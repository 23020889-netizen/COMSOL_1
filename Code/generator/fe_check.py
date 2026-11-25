"""
Independent plane-stress FE verification of the TFG layouts (gmsh + scikit-fem, P2 triangles).
Not COMSOL: it is used to (1) check that the geometry fed to COMSOL is connected and
physically sensible, (2) tune spring lengths to the paper's frequencies, (3) give the
expected numbers that the COMSOL run must reproduce (3D vs plane stress: ~1-2 %).
"""
import sys, json, math, time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
import gmsh
from skfem import MeshTri, Basis, ElementVector, ElementTriP2, BilinearForm, LinearForm, asm
from skfem.models.elasticity import linear_elasticity, lame_parameters
from skfem.helpers import dot
import tfg_geometry as G
import tfg_physics as PH

UM = 1e-6


def mesh_layout(parts, h_body=40.0, n_across=2.0, verbose=False):
    gmsh.initialize(); gmsh.option.setNumber('General.Terminal', 1 if verbose else 0)
    gmsh.model.add('tfg')
    occ = gmsh.model.occ
    tags = []
    for p in parts:
        if p['kind'] == 'rect':
            t = occ.addRectangle(p['x0'], p['y0'], 0, p['x1'] - p['x0'], p['y1'] - p['y0'])
        else:
            pts = [occ.addPoint(x, y, 0) for x, y in p['pts']]
            ls = [occ.addLine(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
            t = occ.addPlaneSurface([occ.addCurveLoop(ls)])
        tags.append(t)
    out, omap = occ.fragment([(2, t) for t in tags], [])
    occ.synchronize()
    surf_part = {}
    for i, m in enumerate(omap):
        for d, t in m:
            surf_part[t] = i
    # mesh size per part, smallest wins on shared points
    sizes = []
    for i, p in enumerate(parts):
        x0, y0, x1, y1 = G.bbox(p)
        if p['kind'] == 'poly':
            dmin = 8.0 if p['name'].endswith(('_h1', '_h2')) else 30.0
        else:
            dmin = min(x1 - x0, y1 - y0)
        sizes.append(min(h_body, max(dmin / n_across, 2.0)))
    order = sorted(surf_part, key=lambda t: -sizes[surf_part[t]])
    for t in order:
        pts = gmsh.model.getBoundary([(2, t)], recursive=True)
        gmsh.model.mesh.setSize(pts, sizes[surf_part[t]])
    gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary', 0)
    gmsh.option.setNumber('Mesh.MeshSizeMax', h_body)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 0)
    gmsh.option.setNumber('Mesh.MeshSizeFromPoints', 1)
    gmsh.option.setNumber('Mesh.Algorithm', 6)
    gmsh.model.mesh.generate(2)
    nodeTags, coords, _ = gmsh.model.mesh.getNodes()
    xyz = coords.reshape(-1, 3)[:, :2]
    idx = {int(t): i for i, t in enumerate(nodeTags)}
    tris, tri_part = [], []
    for t, i in surf_part.items():
        et, etags, enodes = gmsh.model.mesh.getElements(2, t)
        for k, typ in enumerate(et):
            if typ != 2:
                continue
            nn = np.array([idx[int(n)] for n in enodes[k]]).reshape(-1, 3)
            tris.append(nn); tri_part.append(np.full(len(nn), i))
    gmsh.finalize()
    tris = np.vstack(tris); tri_part = np.concatenate(tri_part)
    used = np.unique(tris)
    remap = -np.ones(len(xyz), int); remap[used] = np.arange(len(used))
    m = MeshTri((xyz[used] * UM).T, remap[tris].T)
    return m, tri_part


class Model:
    def __init__(self, scheme, n_across=2.0, h_body=40.0, **over):
        t0 = time.time()
        self.scheme = scheme
        self.P, self.parts, self.info = G.build(scheme, **over)
        self.mesh, self.tri_part = mesh_layout(self.parts, h_body, n_across)
        self.groups = np.array([self.parts[i]['group'] for i in self.tri_part])
        mat = PH.MATERIAL
        E, nu, rho = mat['E'], mat['nu'], mat['rho']
        lam, mu = lame_parameters(E, nu)
        lam_ps = 2 * lam * mu / (lam + 2 * mu)          # plane stress
        self.e = ElementVector(ElementTriP2())
        self.ib = Basis(self.mesh, self.e)
        h = self.P['h'] * UM
        self.h = h
        self.K = asm(linear_elasticity(lam_ps, mu), self.ib) * h
        self.Mfull = asm(BilinearForm(lambda u, v, w: rho * dot(u, v)), self.ib) * h
        # fixed DOFs: every dof of anchor elements
        anc = np.where(self.groups == 'anchor')[0]
        fixed = np.unique(self.ib.element_dofs[:, anc].ravel())
        self.free = np.setdiff1d(np.arange(self.K.shape[0]), fixed)
        self.ndof = self.K.shape[0]
        self.rho = rho
        # group mass matrices and averaging functionals
        self._gm = {}
        self.avg = {}
        for g in set(self.groups):
            el = np.where(self.groups == g)[0]
            b = Basis(self.mesh, self.e, elements=el)
            area = el.size and float(np.sum(b.dx))
            fx = asm(LinearForm(lambda v, w: v[0]), b)
            fy = asm(LinearForm(lambda v, w: v[1]), b)
            self.avg[g] = (fx / area, fy / area, area)
            self._gm[g] = b
        print(f"[{scheme}] mesh {self.mesh.p.shape[1]} vertices, {self.mesh.t.shape[1]} tris, "
              f"{self.ndof} dofs, {time.time()-t0:.1f}s")

    def group_mass(self, g):
        b = self._gm[g]
        return asm(BilinearForm(lambda u, v, w: self.rho * dot(u, v)), b) * self.h

    def mass_of(self, g):
        return self.avg[g][2] * self.h * self.rho

    def eig(self, n=24, f0=12500.0):
        Kf = self.K[self.free][:, self.free].tocsc(); Mf = self.Mfull[self.free][:, self.free].tocsc()
        sig = (2 * np.pi * f0) ** 2
        w2, V = sla.eigsh(Kf, k=n, M=Mf, sigma=sig, which='LM', tol=1e-9, maxiter=4000, ncv=max(2 * n + 1, 40))
        o = np.argsort(w2); w2 = w2[o]; V = V[:, o]
        Phi = np.zeros((self.ndof, n)); Phi[self.free] = V
        # mass normalise
        for k in range(n):
            Phi[:, k] /= math.sqrt(Phi[:, k] @ (self.Mfull @ Phi[:, k]))
        self.f = np.sqrt(np.abs(w2)) / 2 / np.pi
        self.Phi = Phi
        return self.f, Phi

    def a(self, g, comp, U):
        return self.avg[g][comp] @ U

    def classify(self):
        """Mode identification by mass-normalised participation (same criterion as
        in the COMSOL Java):  P_drive = |vL - vR| / sqrt(modal mass),
        P_sense = |uL - uR| / sqrt(modal mass)  (u,v averaged on the proof masses)."""
        rows = []
        for k in range(self.Phi.shape[1]):
            U = self.Phi[:, k]
            mm = math.sqrt(U @ (self.Mfull @ U))
            uL, vL = self.a('pm_L', 0, U), self.a('pm_L', 1, U)
            uR, vR = self.a('pm_R', 0, U), self.a('pm_R', 1, U)
            rows.append(dict(k=k + 1, f=float(self.f[k]),
                             P_drive=float(abs(vL - vR) / mm), P_drive_in=float(abs(vL + vR) / mm),
                             P_sense=float(abs(uL - uR) / mm), P_sense_in=float(abs(uL + uR) / mm)))
        self.modes = rows
        # contribution of a mode to the anti-phase static compliance ~ P^2/w^2 -> rank by P/f
        self.k_drive = max([r for r in rows if r['P_drive'] > r['P_sense']], key=lambda r: r['P_drive'] / r['f'])['k']
        self.k_sense = max([r for r in rows if r['P_sense'] > r['P_drive']], key=lambda r: r['P_sense'] / r['f'])['k']
        return rows

    # ---- harmonic response by modal superposition (non-proportional C) ----
    def damping_matrix(self):
        d = PH.dashpots(self.scheme)
        C = sp.csr_matrix((self.ndof, self.ndof))
        gmap = {'pm': ['pm_L', 'pm_R'], 'df': ['df_L', 'df_R'], 'sf': ['sf_L', 'sf_R'],
                'af': ['af_T', 'af_B']}
        self.alpha = {}
        for key, c in d.items():
            gs = gmap[key]
            m1 = self.mass_of(gs[0])                 # Table 5 coefficients are per tine / per part
            alpha = (c / 2 if key == 'af' else c) / m1   # c_s2 is shared by the two amplified frames (Eq. 12)
            self.alpha[key] = alpha
            if alpha > 0:
                for g in gs:
                    C = C + alpha * self.group_mass(g)
        return C

    def force_vec(self, g, comp, F):
        fx = self.avg[g][comp]   # = int(phi)/area  -> sum = 1 over the group
        return F * fx            # total force F uniformly distributed

    def frf(self, freqs, F_vec, outputs):
        C = self.damping_matrix()
        Phi = self.Phi
        Cm = Phi.T @ (C @ Phi)
        w2 = (2 * np.pi * self.f) ** 2
        fm = Phi.T @ F_vec
        res = {k: [] for k in outputs}
        for fr in freqs:
            w = 2 * np.pi * fr
            A = np.diag(w2 - w ** 2) + 1j * w * Cm
            q = np.linalg.solve(A, fm)
            U = Phi @ q
            for k, fn in outputs.items():
                res[k].append(fn(U))
        return {k: np.array(v) for k, v in res.items()}


def outputs_for(M):
    a = M.a
    o = {'xL': lambda U: a('pm_L', 0, U), 'xR': lambda U: a('pm_R', 0, U),
         'yL': lambda U: a('pm_L', 1, U), 'yR': lambda U: a('pm_R', 1, U),
         'sfL': lambda U: a('sf_L', 0, U), 'sfR': lambda U: a('sf_R', 0, U)}
    if M.scheme == 'I':
        o.update({'yT': lambda U: a('af_T', 1, U), 'yB': lambda U: a('af_B', 1, U)})
    return o


def run(scheme, n_modes=24, **over):
    M = Model(scheme, **over)
    M.eig(n_modes)
    M.classify()
    return M


if __name__ == '__main__':
    sc = sys.argv[1] if len(sys.argv) > 1 else 'I'
    M = run(sc)
    for r in M.modes:
        tag = ' <== DRIVE' if r['k'] == M.k_drive else (' <== SENSE' if r['k'] == M.k_sense else '')
        print(f"{r['k']:3d} {r['f']:10.1f} Hz  Pd={r['P_drive']:7.1f} Pd_in={r['P_drive_in']:7.1f} "
              f"Ps={r['P_sense']:7.1f} Ps_in={r['P_sense_in']:7.1f}{tag}")
