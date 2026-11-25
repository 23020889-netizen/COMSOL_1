"""
Parametric 2D layout of the MEMS tuning-fork gyroscope (TFG) of
Hu et al., Micromachines 2025, 16, 195 -- Scheme I (chevron amplifier)
and Scheme II (conventional, diamond sense coupling).

This module is the SINGLE SOURCE OF TRUTH for the geometry:
  * make_comsol_java.py turns it into COMSOL 6.3 Java (Work Plane + Extrude)
  * fe_check.py meshes it (gmsh) and solves an independent plane-stress FE
    model (scikit-fem) to verify frequencies / mode shapes before COMSOL.

Units: micrometres.  x = sense axis (horizontal), y = drive axis (vertical),
device centred at the origin, symmetric about x=0 and y=0.

Every primitive is either an axis-aligned rectangle or a polygon. Primitives
only ABUT (share edges), they never overlap, so after "Form Union" each
primitive is exactly one COMSOL domain.  validate() checks this.
"""
import math, copy

# ----------------------------------------------------------------------------
# Shared parameters (identical for both schemes)  -- see README for sources
# ----------------------------------------------------------------------------
BASE = dict(
    h=40.0,          # device layer thickness (Table 1)
    w=8.0,           # width of every flexure (Table 1)
    s=12.0,          # slot between the two beams of a folded (U) spring
    t_tr=20.0,       # truss (fold) length of a U spring
    A_w=60.0, A_h=60.0,   # anchor block
    # Coriolis (proof) mass: 1500 x 1880 x 40 = 0.1128 mm^3 (Table 1: 0.1127)
    W_pm=1500.0, H_pm=1880.0,
    # drive frames (top+bottom): 2 x 1500 x 325 x 40 = 0.039 mm^3 (Table 1)
    W_df=1500.0, H_df=325.0,
    L_d=245.0,       # drive (folded) spring length (Table 1)
    L_pd=300.0,      # proof-mass <-> drive-frame straight connector (sense compliant)
    X_pd=(200.0, 600.0),  # |x| positions of those connectors (4 per edge)
    L_ps=197.5,      # proof-mass <-> sense-frame straight connector (drive compliant); tuned -> f_drive = 12918.7 Hz
    Y_ps=470.0,      # |y| position of those connectors (2 per sense frame)
    H_sf=1700.0,     # sense (decouple) frame height
    L_s=250.0,       # sense (folded) suspension spring length (Table 1)
    Xc=1900.0,       # |x| of each tine centre
    # drive coupling lever (seesaw), top and bottom
    L_lnk=150.0, w_lnk=8.0, w_lev=150.0, L_piv=100.0, w_piv=8.0,
    piv_anchor_w=100.0,
    # amplifier / coupling arms (hinge - rigid body - hinge)
    w_body=30.0, y_arm0=8.0,
    endblk_w=30.0, endblk_h=60.0,
)

SCHEME_I = dict(
    scheme='I',
    W_sf=156.0,      # 2 x 156 x 1700 x 40 = 0.0212 mm^3 (Table 1, sense frame Scheme I)
    alpha=18.0,      # chevron angle (Table 1)
    apex_w=80.0, apex_h=30.0,
    W_af=860.0, H_af=465.0,   # 2 x 860 x 465 x 40 = 0.0320 mm^3 (Table 1)
    L_a=280.0,       # amplified-frame support spring length (Table 1)
    l_hinge=52.0, w_hinge=8.0,   # slender flexure hinges at both ends of each chevron arm (Fig. 6f); tuned -> f_sense = 13043 Hz
)
SCHEME_II = dict(
    scheme='II',
    W_sf=296.0,      # 2 x 296 x 1700 x 40 = 0.0403 mm^3 (Table 1, sense frame Scheme II)
    alpha=38.0,      # sense-coupling (diamond) angle (Table 1)
    vb_w=600.0, vb_h=30.0,    # vertex block of the diamond
    L_c=290.0,       # sense-coupling support spring length (Table 1)
    # diamond arms = uniform beams (Fig. 6g), width tuned -> f_sense = 13106 Hz (paper FEA 13100.6 Hz)
    l_hinge=20.0, w_hinge=21.45, w_body=21.45, y_arm0=16.6,
)


def params(scheme, **over):
    P = dict(BASE)
    P.update(SCHEME_I if scheme == 'I' else SCHEME_II)
    P.update(over)
    return P


# ----------------------------------------------------------------------------
class Layout:
    def __init__(self):
        self.parts = []

    def rect(self, name, group, x0, y0, x1, y1):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
        assert x1 - x0 > 1e-9 and y1 - y0 > 1e-9, name
        self.parts.append(dict(name=name, group=group, kind='rect',
                               x0=round(x0, 6), y0=round(y0, 6),
                               x1=round(x1, 6), y1=round(y1, 6)))

    def poly(self, name, group, pts):
        q = []
        for x, y in pts:                       # drop repeated vertices (e.g. hinge width == body width)
            pt = (round(x, 6), round(y, 6))
            if not q or abs(pt[0] - q[-1][0]) + abs(pt[1] - q[-1][1]) > 1e-6:
                q.append(pt)
        if abs(q[0][0] - q[-1][0]) + abs(q[0][1] - q[-1][1]) < 1e-6:
            q.pop()
        self.parts.append(dict(name=name, group=group, kind='poly', pts=q))

    # -- folded U spring, beams along x (compliant in y) -------------------
    def u_spring_x(self, name, grp_anchor, x_root, y_edge, side, dirx, L, P,
                   anchor=True, anchor_w=None):
        """Body Q has its end face at x=x_root and an edge (top if side='above',
        bottom if side='below') at y=y_edge.  Beam B is attached to Q on that
        edge band, beam A to an anchor stacked beside Q with slot P['s']."""
        w, s, t = P['w'], P['s'], P['t_tr']
        aw = anchor_w or P['A_w']
        if side == 'above':
            yB = (y_edge - w, y_edge); yA = (y_edge + s, y_edge + s + w)
            yanc = (y_edge + s, y_edge + s + P['A_h'])
        else:
            yB = (y_edge, y_edge + w); yA = (y_edge - s - w, y_edge - s)
            yanc = (y_edge - s - P['A_h'], y_edge - s)
        xa, xb = (x_root, x_root + dirx * L)
        self.rect(name + '_bB', 'spring', xa, yB[0], xb, yB[1])
        self.rect(name + '_bA', 'spring', xa, yA[0], xb, yA[1])
        ylo, yhi = min(yA[0], yB[0]), max(yA[1], yB[1])
        self.rect(name + '_tr', 'spring', xb, ylo, xb + dirx * t, yhi)
        if anchor:
            self.rect(name + '_anc', grp_anchor, x_root - dirx * aw, yanc[0], x_root, yanc[1])

    # -- folded U spring, beams along y (compliant in x) -------------------
    def u_spring_y(self, name, grp_anchor, y_root, x_edge, side, diry, L, P):
        """Body Q has its end face at y=y_root and a side edge at x=x_edge
        (side='right': Q lies left of x_edge, anchor to the right, etc.)."""
        w, s, t = P['w'], P['s'], P['t_tr']
        if side == 'right':
            xB = (x_edge - w, x_edge); xA = (x_edge + s, x_edge + s + w)
            xanc = (x_edge + s, x_edge + s + P['A_w'])
        else:
            xB = (x_edge, x_edge + w); xA = (x_edge - s - w, x_edge - s)
            xanc = (x_edge - s - P['A_w'], x_edge - s)
        ya, yb = y_root, y_root + diry * L
        self.rect(name + '_bB', 'spring', xB[0], ya, xB[1], yb)
        self.rect(name + '_bA', 'spring', xA[0], ya, xA[1], yb)
        xlo, xhi = min(xA[0], xB[0]), max(xA[1], xB[1])
        self.rect(name + '_tr', 'spring', xlo, yb, xhi, yb + diry * t)
        self.rect(name + '_anc', grp_anchor, xanc[0], y_root - diry * P['A_h'], xanc[1], y_root)

    # -- hinge/body/hinge arm between a vertical face and a horizontal face --
    def arm(self, name, group, p_start, p_end, P):
        """Arm from p_start (lies on a VERTICAL face, cut vertical) to p_end
        (lies on a HORIZONTAL face, cut horizontal).  Centre-line straight."""
        (x0, y0), (x1, y1) = p_start, p_end
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L          # axis
        nx, ny = -uy, ux                                # normal
        lh, wh, wb = P['l_hinge'], P['w_hinge'], P['w_body']

        def P_(t, off):  # point at distance t along axis, offset along normal
            return (x0 + ux * t + nx * off, y0 + uy * t + ny * off)

        # vertical cut at start: points on x=x0 with normal offsets
        def vcut(off):   # intersection of line (offset off) with x = x0
            # line: x0 + nx*off + ux*t = x0  -> t = -nx*off/ux
            t = -nx * off / ux
            return P_(t, off)

        def hcut(off):   # intersection of line (offset off) with y = y1
            t = (y1 - y0 - ny * off) / uy
            return P_(t, off)
        # hinge 1
        self.poly(name + '_h1', 'amp', [vcut(-wh / 2), P_(lh, -wh / 2), P_(lh, wh / 2), vcut(wh / 2)])
        # body
        # body: hinge end points inserted so that the shared edges match exactly
        self.poly(name + '_bd', group, [P_(lh, -wb / 2), P_(L - lh, -wb / 2), P_(L - lh, -wh / 2),
                                        P_(L - lh, wh / 2), P_(L - lh, wb / 2), P_(lh, wb / 2),
                                        P_(lh, wh / 2), P_(lh, -wh / 2)])
        # hinge 2
        self.poly(name + '_h2', 'amp', [P_(L - lh, -wh / 2), hcut(-wh / 2), hcut(wh / 2), P_(L - lh, wh / 2)])


# ----------------------------------------------------------------------------
def _tine(lay, P, side):
    """Build one tine.  side=-1 -> left tine, +1 -> right tine.
    Local X points towards the device centre:  x = side*(Xc - X)."""
    T = 'L' if side < 0 else 'R'
    Xc = P['Xc']

    def gx(X):
        return (X - Xc) if side < 0 else (Xc - X)

    def R(name, group, X0, Y0, X1, Y1):
        lay.rect(f'{name}_{T}', group, gx(X0), Y0, gx(X1), Y1)

    hw, hh = P['W_pm'] / 2, P['H_pm'] / 2
    w = P['w']
    # proof mass
    R('pm', f'pm_{T}', -hw, -hh, hw, hh)
    # drive frames + PM<->DF straight connectors
    for sy, tag in ((+1, 't'), (-1, 'b')):
        y_in = sy * (hh + P['L_pd'])               # DF inner face
        y_out = sy * (hh + P['L_pd'] + P['H_df'])  # DF outer face
        R(f'df{tag}', f'df_{T}', -P['W_df'] / 2, y_in, P['W_df'] / 2, y_out)
        for X in P['X_pd']:
            for sx in (-1, 1):
                Xm = sx * X
                R(f'cpd{tag}{"p" if sx>0 else "m"}{int(X)}', 'spring', Xm - w / 2, sy * hh, Xm + w / 2, y_in)
        # drive folded springs at both DF ends, anchors on outer and inner side
        for sx, etag in ((+1, 'i'), (-1, 'o')):
            Xend = sx * P['W_df'] / 2
            xr = gx(Xend)
            dirx = (1 if xr > gx(0) else -1)
            y_top, y_bot = max(y_in, y_out), min(y_in, y_out)
            lay.u_spring_x(f'sd{tag}{etag}u_{T}', 'anchor', xr, y_top, 'above', dirx, P['L_d'], P)
            lay.u_spring_x(f'sd{tag}{etag}l_{T}', 'anchor', xr, y_bot, 'below', dirx, P['L_d'], P)
    # sense (decouple) frames on both sides of the PM, straight connectors
    for sx, ftag in ((+1, 'i'), (-1, 'o')):
        Xn = sx * (hw + P['L_ps'])                 # near face (towards PM)
        Xf = sx * (hw + P['L_ps'] + P['W_sf'])     # far face
        R(f'sf{ftag}', f'sf_{T}', Xn, -P['H_sf'] / 2, Xf, P['H_sf'] / 2)
        for sy in (-1, 1):
            R(f'cps{ftag}{"p" if sy>0 else "m"}', 'spring', sx * hw, sy * P['Y_ps'] - w / 2, Xn, sy * P['Y_ps'] + w / 2)
        # suspension U springs at the frame ends, anchors in the PM-SF gap
        xnear = gx(Xn)
        anc_side = 'left' if gx(Xn - sx) < xnear else 'right'
        for sy in (-1, 1):
            lay.u_spring_y(f'ss{ftag}{"t" if sy>0 else "b"}_{T}', 'anchor', sy * P['H_sf'] / 2,
                           xnear, anc_side, sy, P['L_s'], P)
    return gx


def _lever(lay, P):
    """Seesaw drive-coupling levers (top and bottom)."""
    Xc = P['Xc']
    for sy, tag in ((+1, 't'), (-1, 'b')):
        y_df = sy * (P['H_pm'] / 2 + P['L_pd'] + P['H_df'])
        y_l0 = y_df + sy * P['L_lnk']
        y_l1 = y_l0 + sy * P['w_lev']
        for sx in (-1, 1):
            lay.rect(f'lnk{tag}{"R" if sx>0 else "L"}', 'link', sx * Xc - P['w_lnk'] / 2, y_df,
                     sx * Xc + P['w_lnk'] / 2, y_l0)
        half = Xc + 30.0
        lay.rect(f'lev{tag}', 'lever', -half, y_l0, half, y_l1)
        y_p = y_l1 + sy * P['L_piv']
        lay.rect(f'piv{tag}', 'spring', -P['w_piv'] / 2, y_l1, P['w_piv'] / 2, y_p)
        lay.rect(f'pivanc{tag}', 'anchor', -P['piv_anchor_w'] / 2, y_p, P['piv_anchor_w'] / 2,
                 y_p + sy * P['A_h'])


def _center_scheme1(lay, P):
    """Chevron displacement amplifier + two amplified sense frames."""
    xi = P['Xc'] - (P['W_pm'] / 2 + P['L_ps'] + P['W_sf'])   # |x| of inner SF far face
    ta = math.tan(math.radians(P['alpha']))
    xe = xi - P['endblk_w']                                    # |x| of arm start face
    for sx in (-1, 1):
        lay.rect(f'endblk_{"R" if sx>0 else "L"}', 'amp', sx * xi, -P['endblk_h'] / 2,
                 sx * xe, P['endblk_h'] / 2)
    xa = 24.0                                                  # |x| of arm end at apex
    dy = (xe - xa) * ta
    y_apex = P['y_arm0'] + dy
    for sy, tag in ((+1, 'T'), (-1, 'B')):
        for sx in (-1, 1):
            p0 = (sx * xe, sy * P['y_arm0'])
            p1 = (sx * xa, sy * y_apex)
            lay.arm(f'chv{tag}{"R" if sx>0 else "L"}', 'amp', p0, p1, P)
        # apex block, attached directly to the amplified frame
        y0 = sy * y_apex
        y1 = sy * (y_apex + P['apex_h'])
        lay.rect(f'apex{tag}', 'amp', -P['apex_w'] / 2, y0, P['apex_w'] / 2, y1)
        ya0 = y1
        ya1 = y1 + sy * P['H_af']
        lay.rect(f'af{tag}', f'af_{tag}', -P['W_af'] / 2, ya0, P['W_af'] / 2, ya1)
        # 4 folded support springs per frame (beams along x, compliant in y)
        for sx in (-1, 1):
            xr = sx * P['W_af'] / 2
            ytop, ybot = max(ya0, ya1), min(ya0, ya1)
            lay.u_spring_x(f'sa{tag}{"R" if sx>0 else "L"}u', 'anchor', xr, ytop, 'above', sx, P['L_a'], P)
            lay.u_spring_x(f'sa{tag}{"R" if sx>0 else "L"}l', 'anchor', xr, ybot, 'below', sx, P['L_a'], P)
    return dict(y_apex=y_apex, x_endface=xe, x_sf_far=xi)


def _center_scheme2(lay, P):
    """Diamond sense-coupling mechanism with anchored vertex springs."""
    xi = P['Xc'] - (P['W_pm'] / 2 + P['L_ps'] + P['W_sf'])
    ta = math.tan(math.radians(P['alpha']))
    xe = xi - P['endblk_w']
    for sx in (-1, 1):
        lay.rect(f'endblk_{"R" if sx>0 else "L"}', 'amp', sx * xi, -P['endblk_h'] / 2,
                 sx * xe, P['endblk_h'] / 2)
    xa = 24.0
    y_v = P['y_arm0'] + (xe - xa) * ta
    for sy, tag in ((+1, 'T'), (-1, 'B')):
        for sx in (-1, 1):
            lay.arm(f'dia{tag}{"R" if sx>0 else "L"}', 'amp', (sx * xe, sy * P['y_arm0']),
                    (sx * xa, sy * y_v), P)
        y0, y1 = sy * y_v, sy * (y_v + P['vb_h'])
        lay.rect(f'vb{tag}', f'vb_{tag}', -P['vb_w'] / 2, y0, P['vb_w'] / 2, y1)
        for sx in (-1, 1):
            xr = sx * P['vb_w'] / 2
            ytop, ybot = max(y0, y1), min(y0, y1)
            lay.u_spring_x(f'sc{tag}{"R" if sx>0 else "L"}u', 'anchor', xr, ytop, 'above', sx, P['L_c'], P)
            lay.u_spring_x(f'sc{tag}{"R" if sx>0 else "L"}l', 'anchor', xr, ybot, 'below', sx, P['L_c'], P)
    return dict(y_vertex=y_v, x_endface=xe, x_sf_far=xi)


def build(scheme='I', **over):
    P = params(scheme, **over)
    lay = Layout()
    _tine(lay, P, -1)
    _tine(lay, P, +1)
    _lever(lay, P)
    info = _center_scheme1(lay, P) if scheme == 'I' else _center_scheme2(lay, P)
    return P, lay.parts, info


# ----------------------------------------------------------------------------
def to_shapely(p):
    from shapely.geometry import Polygon, box
    if p['kind'] == 'rect':
        return box(p['x0'], p['y0'], p['x1'], p['y1'])
    return Polygon(p['pts'])


def bbox(p):
    if p['kind'] == 'rect':
        return p['x0'], p['y0'], p['x1'], p['y1']
    xs = [q[0] for q in p['pts']]; ys = [q[1] for q in p['pts']]
    return min(xs), min(ys), max(xs), max(ys)


def group_area(parts, group):
    return sum(to_shapely(p).area for p in parts if p['group'] == group)


def validate(parts, verbose=True):
    """No overlaps, everything connected, every anchor touches the structure,
    every group-box selection (bbox +0.5 um, 'inside') catches only its part."""
    from shapely.strtree import STRtree
    from shapely.ops import unary_union
    geoms = [to_shapely(p) for p in parts]
    for g, p in zip(geoms, parts):
        assert g.is_valid and g.area > 0, p['name']
    tree = STRtree(geoms)
    errs = []
    adj = {i: set() for i in range(len(parts))}
    for i, g in enumerate(geoms):
        for j in tree.query(g.buffer(1e-4)):
            j = int(j)
            if j <= i:
                continue
            inter = g.intersection(geoms[j])
            if inter.area > 1e-3:
                errs.append(f"OVERLAP {parts[i]['name']} / {parts[j]['name']} area={inter.area:.3g}")
            if g.buffer(0.01).intersection(geoms[j].buffer(0.01)).area > 0.01:
                adj[i].add(j); adj[j].add(i)
    # connectivity: BFS over shared-edge adjacency
    seen = {0}; stack = [0]
    while stack:
        k = stack.pop()
        for n in adj[k]:
            if n not in seen:
                seen.add(n); stack.append(n)
    if len(seen) != len(parts):
        miss = [parts[k]['name'] for k in range(len(parts)) if k not in seen]
        errs.append(f"DISCONNECTED parts: {miss[:20]} ... ({len(miss)})")
    # parts that touch only by a corner or tiny edge
    for i in range(len(parts)):
        if not adj[i]:
            errs.append(f"ISOLATED {parts[i]['name']}")
    # box-selection uniqueness
    for i, p in enumerate(parts):
        x0, y0, x1, y1 = bbox(p)
        bx = (x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5)
        inside = [parts[j]['name'] for j in range(len(parts))
                  if bbox(parts[j])[0] >= bx[0] and bbox(parts[j])[1] >= bx[1]
                  and bbox(parts[j])[2] <= bx[2] and bbox(parts[j])[3] <= bx[3]]
        if p['group'] not in ('spring', 'amp') and inside != [p['name']]:
            errs.append(f"BOX {p['name']} catches {inside}")
    # minimum clearance between non-adjacent parts
    clear = []
    for i, g in enumerate(geoms):
        for j in tree.query(g.buffer(6.0)):
            j = int(j)
            if j <= i or j in adj[i] or (adj[i] & adj[j]):
                continue   # adjacent, or both attached to the same part (acute joint wedge) -> fine
            d = g.distance(geoms[j])
            if d < 5.0:
                clear.append((d, parts[i]['name'], parts[j]['name']))
    for d, a, b in sorted(clear)[:30]:
        if d < 1e-6:
            # corner touching
            errs.append(f"CORNER-TOUCH {a}/{b}")
        else:
            errs.append(f"CLEARANCE {d:.2f}um {a}/{b}")
    if verbose:
        print(f"{len(parts)} parts, union area {unary_union(geoms).area:.1f} um^2")
        for e in errs:
            print('  !!', e)
        if not errs:
            print('  geometry OK: no overlaps, connected, unique box selections, clearance >= 5 um')
    return errs, adj


if __name__ == '__main__':
    for sc in ('I', 'II'):
        P, parts, info = build(sc)
        print('Scheme', sc, info)
        validate(parts)
        for g in ('pm_L', 'df_L', 'sf_L', 'af_T', 'vb_T'):
            a = group_area(parts, g)
            if a:
                print(f'   {g}: area {a:.0f} um^2 -> volume {a*P["h"]*1e-9:.4f} mm^3')
