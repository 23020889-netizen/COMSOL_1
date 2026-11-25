"""
Full independent verification + Scheme I vs Scheme II comparison (plane-stress FE).
Produces Code/verification/*.png|csv|json.  Mirrors the COMSOL studies one-to-one:
  Study 0  electrostatic unit cells -> fringe factors eta_d, eta_s
  Study 1  eigenfrequencies, automatic drive / sense identification
  Study 2  drive FRF to the push-pull comb force
  Study 3  sense FRF to +/-1 uN on the Coriolis masses (paper Fig. 9)
  Study 4  gyro operation: drive force + Coriolis (Omega_z) at f_drive -> dC, V_out
  Study 5  static +/-1 uN -> k_an, amplification ratio R
"""
import os, json, math
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from skfem import MeshTri, Basis, ElementTriP2, ElementVector, BilinearForm, asm, condense, solve
from skfem.helpers import dot, grad
from shapely.geometry import box as sbox
import gmsh
import fe_check as FE, tfg_physics as PH

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'verification')
os.makedirs(OUT, exist_ok=True)
E = PH.ELEC
eps0 = E['eps0']


# ------------------------------------------------------------------ Study 0
def es_cell(kind, d):
    """2D Laplace (P2) on the same unit cells as COMSOL Component 2. Returns C per cell [F]."""
    gmsh.initialize(); gmsh.option.setNumber('General.Terminal', 0)
    occ = gmsh.model.occ
    if kind == 'drive':
        air = occ.addRectangle(-7, d, 0, 14, 70 - d)
        holes = [occ.addRectangle(-2, d, 0, 4, 50), occ.addRectangle(5, 10, 0, 2, 60), occ.addRectangle(-7, 10, 0, 2, 60)]
    else:
        air = occ.addRectangle(80, -30, 0, 40, 140)
        holes = [occ.addRectangle(98 + d, 0, 0, 4, 80), occ.addRectangle(105, 0, 0, 4, 80), occ.addRectangle(91, 0, 0, 4, 80)]
    occ.cut([(2, air)], [(2, h) for h in holes]); occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMax', 1.0 if kind == 'drive' else 1.5)
    gmsh.option.setNumber('Mesh.MeshSizeMin', 0.25)
    gmsh.model.mesh.generate(2)
    tags, xyz, _ = gmsh.model.mesh.getNodes(); xyz = xyz.reshape(-1, 3)[:, :2]
    et, etg, en = gmsh.model.mesh.getElements(2)
    idx = {int(t): i for i, t in enumerate(tags)}
    tri = np.array([idx[int(n)] for n in en[0]]).reshape(-1, 3)
    gmsh.finalize()
    used = np.unique(tri); rm = -np.ones(len(xyz), int); rm[used] = np.arange(len(used))
    m = MeshTri(xyz[used].T * 1e-6, rm[tri].T)
    ib = Basis(m, ElementTriP2())
    A = asm(BilinearForm(lambda u, v, w: eps0 * dot(grad(u), grad(v))), ib)
    x, y = ib.doflocs * 1e6
    tol = 1e-3
    onb = np.zeros(ib.N, bool); onb[ib.get_dofs().all()] = True
    if kind == 'drive':
        rotor = onb & (((abs(x) <= 2 + tol) & (y <= 50 + d + tol)) | (abs(y - d) < tol))
        stat = onb & (((abs(x) >= 5 - tol) & (y >= 10 - tol)) | (abs(y - 70) < tol))
        V0 = E['V_DC'] + E['V_AC']
    else:
        stat = onb & (x >= 105 - tol) & (x <= 109 + tol) & (y >= -tol) & (y <= 80 + tol)
        rotor = onb & ~stat
        V0 = E['V_s']
    u = np.zeros(ib.N); u[stat] = V0
    D = np.where(rotor | stat)[0]
    u = solve(*condense(A, np.zeros(ib.N), x=u, D=D))
    W = 0.5 * u @ (A @ u) * 40e-6
    return 2 * W / V0 ** 2


def study0():
    ds = np.array([-0.6, -0.3, 0.0, 0.3, 0.6])
    Cd = np.array([es_cell('drive', d) for d in ds]); Cs = np.array([es_cell('sense', d) for d in ds])
    sd = np.polyfit(ds * 1e-6, Cd, 1)[0]; ss = np.polyfit(ds * 1e-6, Cs, 1)[0]
    an_d = 2 * eps0 * 40e-6 / E['g_d']; an_s = eps0 * 40e-6 * E['L_s'] / E['g_s'] ** 2
    r = dict(C_drive_finger_fF=Cd[2] * 1e15, dCdy_drive=sd, dCdy_drive_analytic=an_d, eta_d=sd / an_d,
             C_sense_el_fF=Cs[2] * 1e15, dCdx_sense=ss, dCdx_sense_analytic=an_s, eta_s=ss / an_s)
    print('Study 0:', {k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    return r


# ------------------------------------------------------------------ mechanics helpers
def coriolis_matrix(M):
    """Gc(u,w) = int 2 rho h (u_y w_x - u_x w_y):  Coriolis load = j*w*Omega*Gc*U."""
    rho, h = M.rho, M.h
    return asm(BilinearForm(lambda u, v, w: 2 * rho * (u[1] * v[0] - u[0] * v[1])), M.ib) * h


def analyse(scheme, tuned, es):
    M = FE.Model(scheme, **tuned)
    M.eig(30, 12500.0); M.classify()
    kd, ks = M.k_drive - 1, M.k_sense - 1
    fd, fs = M.f[kd], M.f[ks]
    C = M.damping_matrix()
    Phi = M.Phi; Cm = Phi.T @ (C @ Phi); w2 = (2 * np.pi * M.f) ** 2
    Gm = Phi.T @ (coriolis_matrix(M) @ Phi)
    a = lambda g, c, U: M.avg[g][c] @ U
    if scheme == 'I':
        a_out = lambda U: a('af_T', 1, U); d_out = lambda U: a('af_T', 1, U) - a('af_B', 1, U)
    else:
        a_out = lambda U: a('sf_L', 0, U); d_out = lambda U: a('sf_L', 0, U) - a('sf_R', 0, U)
    x_an = lambda U: a('sf_L', 0, U) - a('sf_R', 0, U)
    C0 = eps0 * 40e-6 * E['L_s'] / E['g_s']
    dCfac = E['N_s'] / 2 * es['eta_s'] * C0 / E['g_s']
    F_drive = es['eta_d'] * 4 * E['N_d'] * eps0 * 40e-6 * E['V_DC'] * E['V_AC'] / E['g_d']
    F_sen = M.force_vec('pm_L', 0, PH.F_CORIOLIS_TEST) - M.force_vec('pm_R', 0, PH.F_CORIOLIS_TEST)
    F_drv = M.force_vec('df_L', 1, F_drive) - M.force_vec('df_R', 1, F_drive)

    def resp(freq, F, Om=0.0):
        w = 2 * np.pi * freq
        q = np.linalg.solve(np.diag(w2 - w ** 2) + 1j * w * (Cm - Om * Gm), Phi.T @ F)
        return Phi @ q
    # Study 3 - Fig. 9 sweep
    fr = np.unique(np.concatenate([np.arange(11000, 15001, 20), np.arange(fs - 60, fs + 60, 0.5),
                                   np.arange(fs - 8, fs + 8, 0.05), [fd, fs]]))
    A = np.array([abs(a_out(resp(f, F_sen))) for f in fr])
    Dd = np.array([abs(d_out(resp(f, F_sen))) for f in fr])
    ip = int(np.argmax(A)); half = A[ip] / math.sqrt(2)
    lo = fr[:ip][A[:ip] < half][-1]; hi = fr[ip:][A[ip:] < half][0]
    # Study 2 - drive FRF
    frd = np.unique(np.concatenate([np.arange(fd - 400, fd + 400, 5), np.arange(fd - 10, fd + 10, 0.05)]))
    Yd = np.array([abs((a('pm_L', 1, resp(f, F_drv)) - a('pm_R', 1, resp(f, F_drv))) / 2) for f in frd])
    # Study 4 - gyro operation at f_drive
    U0 = resp(fd, F_drv, 0.0); U1 = resp(fd, F_drv, PH.OMEGA_TEST)
    gyro = dict(F_drive_uN=F_drive * 1e6, drive_amp_um=abs(a('pm_L', 1, U1) - a('pm_R', 1, U1)) / 2 * 1e6,
                sense_frame_nm_per_rad_s=abs(a_out(U1) - a_out(U0)) * 1e9,
                dC_aF_per_rad_s=abs(dCfac * (d_out(U1) - d_out(U0))) * 1e18)
    gyro['V_out_mV_per_rad_s'] = E['V_s'] * gyro['dC_aF_per_rad_s'] * 1e-18 / E['C_f'] * 1e3
    gyro['V_out_mV_per_deg_s'] = gyro['V_out_mV_per_rad_s'] * math.pi / 180
    # Study 5 - static
    Kf = M.K[M.free][:, M.free].tocsc()
    Us = np.zeros(M.ndof); Us[M.free] = sla.spsolve(Kf, F_sen[M.free])
    R_fem = (a('af_T' if scheme == 'I' else 'vb_T', 1, Us) - a('af_B' if scheme == 'I' else 'vb_B', 1, Us)) / (2 * x_an(Us))
    k_an = 2 * PH.F_CORIOLIS_TEST / (a('pm_L', 0, Us) - a('pm_R', 0, Us))
    res = dict(scheme=scheme, f_drive=float(fd), f_sense=float(fs), df=float(fs - fd),
               mode_drive=M.k_drive, mode_sense=M.k_sense,
               fig9_peak_um=float(A[ip] * 1e6), fig9_peak_f=float(fr[ip]), Q_sense=float(fr[ip] / (hi - lo)),
               fig9_dC_peak_fF=float(Dd[ip] * dCfac * 1e15),
               fig9_Vout_peak_mV=float(E['V_s'] * Dd[ip] * dCfac / E['C_f'] * 1e3),
               drive_peak_um=float(Yd.max() * 1e6), R_fem_static=float(R_fem), k_an_static=float(k_an),
               masses=dict(pm=M.mass_of('pm_L'), df=M.mass_of('df_L'), sf=M.mass_of('sf_L'),
                           **({'af': M.mass_of('af_T')} if scheme == 'I' else {})),
               alpha=M.alpha, gyro=gyro,
               modes=[dict(k=r['k'], f=r['f'], P_drive=r['P_drive'], P_sense=r['P_sense'],
                           P_drive_in=r['P_drive_in'], P_sense_in=r['P_sense_in']) for r in M.modes])
    np.savetxt(os.path.join(OUT, f'scheme{scheme}_fig9_FRF.csv'), np.c_[fr, A * 1e6, Dd * dCfac * 1e15],
               delimiter=',', header='f_Hz,sense_frame_amp_um,dC_diff_fF', comments='')
    np.savetxt(os.path.join(OUT, f'scheme{scheme}_drive_FRF.csv'), np.c_[frd, Yd * 1e6], delimiter=',',
               header='f_Hz,drive_amp_um', comments='')
    # mode-shape figures
    for k, nm in ((kd, 'drive'), (ks, 'sense')):
        plot_mode(M, k, os.path.join(OUT, f'scheme{scheme}_{nm}_mode.png'),
                  f"Scheme {scheme} - {nm.upper()} mode #{k+1}: {M.f[k]:.1f} Hz")
    return res, (fr, A, Dd * dCfac), (frd, Yd)


def plot_mode(M, k, path, title):
    U = M.Phi[:, k]
    ux = U[M.ib.nodal_dofs[0]]; uy = U[M.ib.nodal_dofs[1]]
    nv = M.mesh.p.shape[1]
    ux, uy = ux[:nv], uy[:nv]
    s = 150e-6 / max(np.abs(ux).max(), np.abs(uy).max())
    xy = M.mesh.p + s * np.vstack([ux, uy])
    mag = np.hypot(ux, uy)
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.tripcolor(xy[0] * 1e6, xy[1] * 1e6, M.mesh.t.T, mag / mag.max(), shading='gouraud', cmap='viridis')
    ax.set_aspect('equal'); ax.set_title(title + '  (colour: |u| normalised, deformation exaggerated)')
    ax.set_xlabel('x (um) - sense axis'); ax.set_ylabel('y (um) - drive axis')
    plt.savefig(path, dpi=110, bbox_inches='tight'); plt.close(fig)


if __name__ == '__main__':
    tuned = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tuned.json')))
    es = study0()
    allres = {'electrostatics': es, 'tuned': tuned}
    curves = {}
    for sc in ('I', 'II'):
        r, c9, cd = analyse(sc, tuned, es)
        allres['scheme' + sc] = r; curves[sc] = (c9, cd)
        print(json.dumps({k: v for k, v in r.items() if k not in ('modes', 'masses', 'alpha')}, indent=1), flush=True)
    I, II = allres['schemeI'], allres['schemeII']
    allres['ratios'] = dict(fig9_amplitude=I['fig9_peak_um'] / II['fig9_peak_um'],
                            fig9_dC=I['fig9_dC_peak_fF'] / II['fig9_dC_peak_fF'],
                            gyro_V_out=I['gyro']['V_out_mV_per_rad_s'] / II['gyro']['V_out_mV_per_rad_s'])
    print('RATIOS', allres['ratios'])
    json.dump(allres, open(os.path.join(OUT, 'results.json'), 'w'), indent=1)
    # comparison plots
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    for sc, col in (('I', '#c0392b'), ('II', '#2471a3')):
        (fr, A, dC), _ = curves[sc]
        lab = 'Scheme I (chevron): amplified frame |y_a1|' if sc == 'I' else 'Scheme II (conventional): sense frame |x_l|'
        ax[0].plot(fr, A * 1e6, color=col, label=lab)
        ax[1].plot(fr, dC * 1e15, color=col, label=f'Scheme {sc}')
    ax[0].set_xlabel('Frequency (Hz)'); ax[0].set_ylabel('Amplitude (um)'); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[0].set_title('Fig. 9 equivalent: +/-1 uN anti-phase sense force')
    ax[1].set_xlabel('Frequency (Hz)'); ax[1].set_ylabel('|C(S+) - C(S-)| (fF)'); ax[1].legend(); ax[1].grid(alpha=.3)
    ax[1].set_title(f"Differential sense capacitance ({E['N_s']} electrodes in both)")
    for a_ in ax: a_.set_xlim(12500, 13600)
    plt.savefig(os.path.join(OUT, 'compare_fig9_and_capacitance.png'), dpi=120, bbox_inches='tight'); plt.close(fig)
