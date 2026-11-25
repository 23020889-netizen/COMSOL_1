"""
Emit COMSOL Multiphysics 6.3 Java (API) model builders for Scheme I and II.

    python make_comsol_java.py            -> ../comsol/TFG_SchemeI_Chevron.java
                                             ../comsol/TFG_SchemeII_Conventional.java
Both files are generated from the SAME geometry module and the SAME physics
parameter set, so the only difference between the two .mph files is the sense
coupling (chevron amplifier + amplified frames  vs  diamond + direct sense frames).
"""
import os, math, textwrap
import tfg_geometry as G
import tfg_physics as PH

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, '..', 'comsol')

CLASS = {'I': 'TFG_SchemeI_Chevron', 'II': 'TFG_SchemeII_Conventional'}
MPH = {'I': 'MEMS_TFG_SchemeI_Chevron_v2.mph', 'II': 'MEMS_TFG_SchemeII_Conventional_v2.mph'}


def jd(x):
    return repr(float(x))


def jstr(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def emit(scheme):
    P, parts, info = G.build(scheme)
    errs, _ = G.validate(parts, verbose=False)
    assert not errs, errs
    E = PH.ELEC
    D = PH.dashpots(scheme)
    cls = CLASS[scheme]
    h = P['h']

    def area(g):
        return G.group_area(parts, g)

    # ---------------- parameters ----------------
    par = []
    def p(name, expr, descr):
        par.append((name, expr, descr))
    p('h_dev', f"{h:g}[um]", 'Device layer thickness (Table 1)')
    p('rho_si', f"{PH.MATERIAL['rho']:g}[kg/m^3]", 'Silicon density (Table 2) - SAME in both schemes')
    p('E_si', f"{PH.MATERIAL['E']/1e9:g}[GPa]", "Silicon Young's modulus (Table 2)")
    p('nu_si', f"{PH.MATERIAL['nu']:g}", "Silicon Poisson's ratio (Table 2)")
    p('w_spring', f"{P['w']:g}[um]", 'Width of all flexures (Table 1) [geometry generator]')
    p('L_drive_spring', f"{P['L_d']:g}[um]", 'Drive folded-spring length (Table 1) [geometry generator]')
    p('L_sense_spring', f"{P['L_s']:g}[um]", 'Sense folded-spring length (Table 1) [geometry generator]')
    if scheme == 'I':
        p('alpha_amp', f"{P['alpha']:g}[deg]", 'Chevron arm angle (Table 1) [geometry generator]')
        p('L_amp_spring', f"{P['L_a']:g}[um]", 'Amplified-frame support spring length [geometry generator]')
    else:
        p('alpha_amp', f"{P['alpha']:g}[deg]", 'Sense-coupling (diamond) arm angle (Table 1) [geometry generator]')
        p('L_cpl_spring', f"{P['L_c']:g}[um]", 'Sense-coupling support spring length (Table 1) [geometry generator]')
    p('R_theory', '0.5*cot(alpha_amp)', 'Kinematic amplification ratio R = cot(alpha)/2 (Eq. 3)')
    # part areas -> masses (exact areas of the generated geometry)
    p('A_pm', f"{area('pm_L'):.6g}[um^2]", 'Area of one Coriolis (proof) mass')
    p('A_df', f"{area('df_L'):.6g}[um^2]", 'Area of the two drive frames of one tine')
    p('A_sf', f"{area('sf_L'):.6g}[um^2]", 'Area of the two sense(-decouple) frames of one tine')
    p('m_pm', 'rho_si*A_pm*h_dev', 'Coriolis mass m_c')
    p('m_df', 'rho_si*A_df*h_dev', 'Drive-frame mass m_d (per tine)')
    p('m_sf', 'rho_si*A_sf*h_dev', 'Sense-frame mass (per tine)')
    if scheme == 'I':
        p('A_af', f"{area('af_T'):.6g}[um^2]", 'Area of one amplified sense frame')
        p('m_af', 'rho_si*A_af*h_dev', 'Amplified sense frame mass (each)')
    # damping (Table 5) -> Rayleigh mass-proportional dashpots on rigid parts
    p('c_d', f"{PH.DAMP['c_d']:g}[N*s/m]", 'Damping coefficient, drive axis (Table 5)')
    p('c_s1', f"{PH.DAMP['c_s1']:g}[N*s/m]", 'Damping coefficient, sense axis Scheme I (Table 5)')
    p('c_s2', f"{PH.DAMP['c_s2']:g}[N*s/m]", 'Damping coefficient, amplified frame Scheme I (Table 5)')
    p('c_s', f"{PH.DAMP['c_s']:g}[N*s/m]", 'Damping coefficient, sense axis Scheme II (Table 5)')
    p('c_pm', 'c_s1', 'Proof-mass slide-film damping (both schemes)')
    p('alpha_pm', 'c_pm/m_pm', 'Rayleigh alpha on each proof mass (c_pm per tine, Table 5)')
    p('alpha_df', '(c_d-c_pm)/m_df', 'Rayleigh alpha on drive frames (drive electrodes)')
    if scheme == 'I':
        p('alpha_af', 'c_s2/(2*m_af)', 'Rayleigh alpha on amplified sense frames (c_s2 shared by the 2 frames, Eq. 12)')
    else:
        p('alpha_sf', '(c_s-c_pm)/m_sf', 'Rayleigh alpha on sense frames (sense electrodes)')
    # drive electrodes
    p('N_d', f"{E['N_d']}", 'Rotor fingers per drive comb (one comb on the outer edge of each drive frame)')
    p('L0_d', f"{E['L0_d']*1e6:g}[um]", 'Drive finger overlap')
    p('g_d', f"{E['g_d']*1e6:g}[um]", 'Drive finger gap (Table 5)')
    p('w_f', '4[um]', 'Comb finger width')
    p('V_DC', f"{E['V_DC']:g}[V]", 'Drive DC polarisation  (|stator-rotor| = V_DC +/- v_ac)')
    p('V_AC', f"{E['V_AC']:g}[V]", 'Drive AC amplitude')
    p('eta_d', '1', 'Fringe-field factor of the drive comb (set automatically from Component 2)')
    p('F_d0', '4*N_d*epsilon0_const*h_dev*V_DC*V_AC/g_d', 'Push-pull drive force amplitude per tine (parallel-overlap model)')
    p('F_drive', 'eta_d*F_d0', 'Drive force amplitude per tine actually applied')
    # sense electrodes
    p('N_s', f"{E['N_s']}", 'Number of sense electrodes (identical in Scheme I and II)')
    p('L_se', f"{E['L_s']*1e6:g}[um]", 'Sense electrode overlap length')
    p('g_s', f"{E['g_s']*1e6:g}[um]", 'Sense gap (Table 5)')
    p('C0_s', 'epsilon0_const*h_dev*L_se/g_s', 'Rest capacitance of one sense electrode')
    p('eta_s', '1', 'Fringe factor of the sense electrode (set automatically from Component 2)')
    p('V_s', f"{E['V_s']:g}[V]", 'DC bias across the sense capacitors (rotor to stator)')
    p('C_f', f"{E['C_f']*1e15:g}[fF]", 'Charge-amplifier feedback capacitor')
    # loads
    p('F_c', f"{PH.F_CORIOLIS_TEST*1e6:g}[uN]", 'Anti-phase harmonic sense-axis force (paper Sec. 5.3, Fig. 9)')
    p('Omega_z', f"{PH.OMEGA_TEST:g}[rad/s]", 'Input angular rate (gyro operation study)')
    p('d_cell', '0[um]', 'Rotor displacement in the electrostatic unit cells (Component 2)')
    p('V_cell_d', 'V_DC+V_AC', 'Stator voltage of the drive cell (peak of V_DC+V_AC*sin(wt))')
    p('V_cell_s', 'V_s', 'Stator voltage of the sense cell')

    # ---------------- java building ----------------
    L = []
    w = L.append
    w(f"// AUTO-GENERATED by Code/generator/make_comsol_java.py -- do not edit by hand.")
    w(f"// MEMS tuning fork gyroscope, Scheme {scheme} ({'chevron amplifier' if scheme=='I' else 'conventional / diamond coupling'})")
    w("// Reference: Hu et al., Micromachines 2025, 16, 195.   COMSOL Multiphysics 6.3, Java API.")
    w("// Build:  comsolcompile " + cls + ".java   then   comsolbatch -inputfile " + cls + ".class -nosave")
    w("import com.comsol.model.*;")
    w("import com.comsol.model.util.*;")
    w("import java.io.*;")
    w("import java.util.*;")
    w("")
    w(f"public class {cls} {{")
    w("")
    w(f"  static final String SCHEME = \"{scheme}\";")
    w(f"  static final String OUT_MPH = \"{MPH[scheme]}\";")
    w("  /** true -> frequency resolution of the paper (0.1 Hz near resonance, ~700 points, slow). */")
    w("  static boolean PAPER_RESOLUTION = false;")
    w("  /** mesh: 1 = coarse (fast check), 2 = normal (default), 3 = fine. */")
    w("  static int MESH_LEVEL = 2;")
    w("  static PrintWriter LOG;")
    w("")
    w("  public static void main(String[] args) {")
    w("    run();")
    w("  }")
    w("")
    w("  static void readOptions() {")
    w("    // environment variables (comsolbatch does not forward command-line arguments)")
    w("    String p = System.getenv(\"TFG_PAPER\"), mm = System.getenv(\"TFG_MESH\");")
    w("    if (p != null && (p.equals(\"1\") || p.equalsIgnoreCase(\"true\"))) PAPER_RESOLUTION = true;")
    w("    if (mm != null) try { MESH_LEVEL = Integer.parseInt(mm.trim()); } catch (NumberFormatException e) { }")
    w("    log(\"Options: PAPER_RESOLUTION=\" + PAPER_RESOLUTION + \", MESH_LEVEL=\" + MESH_LEVEL);")
    w("  }")
    w("")
    w("  static void log(String s) {")
    w("    System.out.println(s);")
    w("    if (LOG != null) { LOG.println(s); LOG.flush(); }")
    w("  }")
    w("")
    # ---- run()
    w("  public static Model run() {")
    w("    try { LOG = new PrintWriter(new FileWriter(OUT_MPH.replace(\".mph\", \"_log.txt\"))); } catch (IOException e) { LOG = null; }")
    w("    readOptions();")
    w("    ModelUtil.showProgress(true);")
    w("    Model model = ModelUtil.create(\"Model\");")
    w("    model.modelPath(new File(\".\").getAbsolutePath());")
    w(f"    model.label(\"{MPH[scheme]}\");")
    w("    try {")
    w("      parameters(model);")
    w("      geometry(model);")
    w("      selections(model);")
    w("      definitions(model);")
    w("      materials(model);")
    w("      physics(model);")
    w("      mesh(model);")
    w("      electrostaticCells(model);")
    w("      studies(model);")
    w("      solveAll(model);")
    w("    } catch (Exception e) {")
    w("      log(\"!! BUILD/SOLVE ERROR: \" + e);")
    w("      StringWriter sw = new StringWriter(); e.printStackTrace(new PrintWriter(sw)); log(sw.toString());")
    w("    } finally {")
    w("      try { model.save(new File(OUT_MPH).getAbsolutePath()); log(\"Saved \" + new File(OUT_MPH).getAbsolutePath()); }")
    w("      catch (Exception e) { log(\"!! could not save: \" + e); }")
    w("      if (LOG != null) LOG.close();")
    w("    }")
    w("    return model;")
    w("  }")
    w("")
    # ---- parameters
    w("  static void parameters(Model model) {")
    for n, e_, d in par:
        w(f"    model.param().set({jstr(n)}, {jstr(e_)}, {jstr(d)});")
    w("  }")
    w("")
    # ---- geometry helpers
    w("  static void rect(Model m, String tag, double x0, double y0, double x1, double y1) {")
    w("    m.component(\"comp1\").geom(\"geom1\").feature(\"wp1\").geom().create(tag, \"Rectangle\");")
    w("    m.component(\"comp1\").geom(\"geom1\").feature(\"wp1\").geom().feature(tag).set(\"pos\", new double[]{x0, y0});")
    w("    m.component(\"comp1\").geom(\"geom1\").feature(\"wp1\").geom().feature(tag).set(\"size\", new double[]{x1 - x0, y1 - y0});")
    w("  }")
    w("  static void poly(Model m, String tag, double[][] pts) {")
    w("    m.component(\"comp1\").geom(\"geom1\").feature(\"wp1\").geom().create(tag, \"Polygon\");")
    w("    m.component(\"comp1\").geom(\"geom1\").feature(\"wp1\").geom().feature(tag).set(\"source\", \"table\");")
    w("    m.component(\"comp1\").geom(\"geom1\").feature(\"wp1\").geom().feature(tag).set(\"table\", pts);")
    w("  }")
    w("")
    # geometry split in chunks of 60 parts to stay far below the 64 kB method limit
    chunks = [parts[i:i + 60] for i in range(0, len(parts), 60)]
    w("  static void geometry(Model model) {")
    w("    model.component().create(\"comp1\", true);")
    w("    model.component(\"comp1\").label(\"Component 1: 3D gyroscope (Solid Mechanics)\");")
    w("    model.component(\"comp1\").geom().create(\"geom1\", 3);")
    w("    model.component(\"comp1\").geom(\"geom1\").lengthUnit(\"\\u00b5m\");")
    w("    model.component(\"comp1\").geom(\"geom1\").create(\"wp1\", \"WorkPlane\");")
    w("    model.component(\"comp1\").geom(\"geom1\").feature(\"wp1\").set(\"unite\", false);")
    for k in range(len(chunks)):
        w(f"    geometryParts{k}(model);")
    w("    model.component(\"comp1\").geom(\"geom1\").create(\"ext1\", \"Extrude\");")
    w("    model.component(\"comp1\").geom(\"geom1\").feature(\"ext1\").set(\"workplane\", \"wp1\");")
    w("    model.component(\"comp1\").geom(\"geom1\").feature(\"ext1\").selection(\"input\").set(\"wp1\");")
    w("    model.component(\"comp1\").geom(\"geom1\").feature(\"ext1\").setIndex(\"distance\", \"h_dev\", 0);")
    w("    model.component(\"comp1\").geom(\"geom1\").run();")
    w(f"    log(\"Geometry built: {len(parts)} primitives (one domain each).\");")
    w("  }")
    for k, ch in enumerate(chunks):
        w(f"  static void geometryParts{k}(Model m) {{")
        for prt in ch:
            if prt['kind'] == 'rect':
                w(f"    rect(m, {jstr(prt['name'])}, {jd(prt['x0'])}, {jd(prt['y0'])}, {jd(prt['x1'])}, {jd(prt['y1'])});")
            else:
                pts = ', '.join('{' + jd(x) + ', ' + jd(y) + '}' for x, y in prt['pts'])
                w(f"    poly(m, {jstr(prt['name'])}, new double[][]{{{pts}}});")
        w("  }")
    w("")
    # ---- selections
    w("  static void box(Model m, String comp, String tag, int dim, double x0, double y0, double x1, double y1, boolean is3d, String label) {")
    w("    m.component(comp).selection().create(tag, \"Box\");")
    w("    m.component(comp).selection(tag).set(\"entitydim\", dim);")
    w("    m.component(comp).selection(tag).set(\"xmin\", x0);")
    w("    m.component(comp).selection(tag).set(\"xmax\", x1);")
    w("    m.component(comp).selection(tag).set(\"ymin\", y0);")
    w("    m.component(comp).selection(tag).set(\"ymax\", y1);")
    w("    if (is3d) {")
    w("      m.component(comp).selection(tag).set(\"zmin\", -0.5);")
    w(f"      m.component(comp).selection(tag).set(\"zmax\", {jd(h + 0.5)});")
    w("    }")
    w("    m.component(comp).selection(tag).set(\"condition\", \"inside\");")
    w("    if (label != null) m.component(comp).selection(tag).label(label);")
    w("  }")
    w("  static void union(Model m, String comp, String tag, int dim, String[] in, String label) {")
    w("    m.component(comp).selection().create(tag, \"Union\");")
    w("    m.component(comp).selection(tag).set(\"entitydim\", dim);")
    w("    m.component(comp).selection(tag).set(\"input\", in);")
    w("    m.component(comp).selection(tag).label(label);")
    w("  }")
    groups = {}
    for prt in parts:
        groups.setdefault(prt['group'], []).append(prt)
    sel_groups = ['anchor', 'pm_L', 'pm_R', 'df_L', 'df_R', 'sf_L', 'sf_R']
    sel_groups += ['af_T', 'af_B'] if scheme == 'I' else ['vb_T', 'vb_B']
    labels = {'anchor': 'Anchors (fixed to substrate, electrical GND of the rotor)',
              'pm_L': 'Coriolis mass - left tine', 'pm_R': 'Coriolis mass - right tine',
              'df_L': 'Drive frames - left tine (drive combs D1/D2)', 'df_R': 'Drive frames - right tine (drive combs D3/D4)',
              'sf_L': 'Sense' + ('-decouple' if scheme == 'I' else '') + ' frames - left tine',
              'sf_R': 'Sense' + ('-decouple' if scheme == 'I' else '') + ' frames - right tine',
              'af_T': 'Amplified sense frame - top (electrodes S+ / S-)', 'af_B': 'Amplified sense frame - bottom (electrodes S+ / S-)',
              'vb_T': 'Diamond vertex block - top', 'vb_B': 'Diamond vertex block - bottom'}
    w("  static void selections(Model model) {")
    for g in sel_groups:
        w(f"    sel_{g}(model);")
    w("    box(model, \"comp1\", \"sel_bottom\", 2, -1e5, -1e5, 1e5, 1e5, false, \"Bottom faces (z=0) - source faces for the swept mesh\");")
    w("    model.component(\"comp1\").selection(\"sel_bottom\").set(\"zmin\", -0.1);")
    w("    model.component(\"comp1\").selection(\"sel_bottom\").set(\"zmax\", 0.1);")
    w("  }")
    for g in sel_groups:
        items = groups[g]
        w(f"  static void sel_{g}(Model m) {{")
        tags = []
        for i, prt in enumerate(items):
            x0, y0, x1, y1 = G.bbox(prt)
            t = f"b_{prt['name']}"
            tags.append(t)
            w(f"    box(m, \"comp1\", {jstr(t)}, 3, {jd(x0-0.5)}, {jd(y0-0.5)}, {jd(x1+0.5)}, {jd(y1+0.5)}, true, {jstr(prt['name'])});")
        arr = ', '.join(jstr(t) for t in tags)
        w(f"    union(m, \"comp1\", \"sel_{g}\", 3, new String[]{{{arr}}}, {jstr(labels[g])});")
        w("  }")
    w("")
    # ---- definitions: couplings & variables
    ave = [('ave_pmL', 'sel_pm_L'), ('ave_pmR', 'sel_pm_R'), ('ave_sfL', 'sel_sf_L'), ('ave_sfR', 'sel_sf_R')]
    if scheme == 'I':
        ave += [('ave_T', 'sel_af_T'), ('ave_B', 'sel_af_B')]
    else:
        ave += [('ave_T', 'sel_vb_T'), ('ave_B', 'sel_vb_B')]
    ints = [('int_dfL', 'sel_df_L'), ('int_dfR', 'sel_df_R'), ('int_pmL', 'sel_pm_L'), ('int_pmR', 'sel_pm_R')]
    w("  static void definitions(Model model) {")
    for t, s in ave:
        w(f"    model.component(\"comp1\").cpl().create(\"{t}\", \"Average\");")
        w(f"    model.component(\"comp1\").cpl(\"{t}\").set(\"opname\", \"{t}\");")
        w(f"    model.component(\"comp1\").cpl(\"{t}\").selection().named(\"{s}\");")
    for t, s in ints:
        w(f"    model.component(\"comp1\").cpl().create(\"{t}\", \"Integration\");")
        w(f"    model.component(\"comp1\").cpl(\"{t}\").set(\"opname\", \"{t}\");")
        w(f"    model.component(\"comp1\").cpl(\"{t}\").selection().named(\"{s}\");")
    w("    model.component(\"comp1\").cpl().create(\"int_all\", \"Integration\");")
    w("    model.component(\"comp1\").cpl(\"int_all\").set(\"opname\", \"int_all\");")
    w("    model.component(\"comp1\").cpl(\"int_all\").selection().all();")
    var = [
        ('uL', 'ave_pmL(u)', 'x-displacement, left Coriolis mass'),
        ('vL', 'ave_pmL(v)', 'y-displacement, left Coriolis mass'),
        ('uR', 'ave_pmR(u)', 'x-displacement, right Coriolis mass'),
        ('vR', 'ave_pmR(v)', 'y-displacement, right Coriolis mass'),
        ('xsL', 'ave_sfL(u)', 'x-displacement, left sense(-decouple) frames'),
        ('xsR', 'ave_sfR(u)', 'x-displacement, right sense(-decouple) frames'),
        ('yT', 'ave_T(v)', 'y-displacement, top ' + ('amplified sense frame' if scheme == 'I' else 'diamond vertex')),
        ('yB', 'ave_B(v)', 'y-displacement, bottom ' + ('amplified sense frame' if scheme == 'I' else 'diamond vertex')),
        ('V_dfL', 'int_dfL(1)', 'Volume, drive frames left'),
        ('V_dfR', 'int_dfR(1)', 'Volume, drive frames right'),
        ('V_pmL', 'int_pmL(1)', 'Volume, left Coriolis mass'),
        ('V_pmR', 'int_pmR(1)', 'Volume, right Coriolis mass'),
        ('m_modal', 'sqrt(int_all(rho_si*(abs(u)^2+abs(v)^2+abs(w)^2)))', 'sqrt of modal mass (mode normalisation)'),
        ('P_drive', 'abs(vL-vR)/m_modal', 'Participation: anti-phase DRIVE (y) of the Coriolis masses'),
        ('P_drive_in', 'abs(vL+vR)/m_modal', 'Participation: in-phase y motion'),
        ('P_sense', 'abs(uL-uR)/m_modal', 'Participation: anti-phase SENSE (x) of the Coriolis masses'),
        ('P_sense_in', 'abs(uL+uR)/m_modal', 'Participation: in-phase x motion'),
        ('y_drive', '(vL-vR)/2', 'Drive amplitude (per tine)'),
        ('x_an', 'xsL-xsR', 'Anti-phase sense input x_l - x_r (paper Eq. 15)'),
        ('R_fem', '(yT-yB)/(2*(xsL-xsR))', 'FEM amplification ratio y_a/(x_l-x_r) (Eq. 9; R\' for the diamond)'),
    ]
    if scheme == 'I':
        var += [('a_out', 'yT', 'Sense-frame amplitude plotted in Fig. 9a (amplified frame, y)'),
                ('d_out', 'yT-yB', 'Differential electrode displacement (both amplified frames)')]
    else:
        var += [('a_out', 'xsL', 'Sense-frame amplitude plotted in Fig. 9b (sense frame, x)'),
                ('d_out', 'xsL-xsR', 'Differential electrode displacement (both sense frames)')]
    var += [
        ('dC_diff', '(N_s/2)*eta_s*C0_s/g_s*d_out', 'Differential sense capacitance C(S+) - C(S-)'),
        ('V_out', 'V_s*dC_diff/C_f', 'Charge-amplifier output amplitude (at the drive frequency)'),
        ('Q_mode', 'real(freq)/(2*imag(freq))', 'Quality factor of an eigenmode (damped eigenfrequency)'),
    ]
    w("    model.component(\"comp1\").variable().create(\"var1\");")
    w("    model.component(\"comp1\").variable(\"var1\").label(\"Read-out variables (displacements, participation, capacitance, voltage)\");")
    for n, e_, d in var:
        w(f"    model.component(\"comp1\").variable(\"var1\").set({jstr(n)}, {jstr(e_)});")
        w(f"    model.component(\"comp1\").variable(\"var1\").descr({jstr(n)}, {jstr(d)});")
    w("  }")
    w("")
    # ---- materials
    w("  static void materials(Model model) {")
    w("    model.component(\"comp1\").material().create(\"mat1\", \"Common\");")
    w("    model.component(\"comp1\").material(\"mat1\").label(\"Silicon (Table 2: rho=2320, E=170 GPa, nu=0.22)\");")
    w("    model.component(\"comp1\").material(\"mat1\").selection().all();")
    w("    model.component(\"comp1\").material(\"mat1\").propertyGroup(\"def\").set(\"density\", \"rho_si\");")
    w("    model.component(\"comp1\").material(\"mat1\").propertyGroup(\"def\").set(\"youngsmodulus\", \"E_si\");")
    w("    model.component(\"comp1\").material(\"mat1\").propertyGroup(\"def\").set(\"poissonsratio\", \"nu_si\");")
    w("    model.component(\"comp1\").material(\"mat1\").propertyGroup().create(\"Enu\", \"Young's modulus and Poisson's ratio\");")
    w("    model.component(\"comp1\").material(\"mat1\").propertyGroup(\"Enu\").set(\"E\", \"E_si\");")
    w("    model.component(\"comp1\").material(\"mat1\").propertyGroup(\"Enu\").set(\"nu\", \"nu_si\");")
    w("  }")
    w("")
    # ---- physics
    damp = [('dmp_pm', 'Proof-mass slide-film damping', ['sel_pm_L', 'sel_pm_R'], 'alpha_pm'),
            ('dmp_df', 'Drive-comb damping', ['sel_df_L', 'sel_df_R'], 'alpha_df')]
    if scheme == 'I':
        damp.append(('dmp_af', 'Sense-electrode damping (amplified frames)', ['sel_af_T', 'sel_af_B'], 'alpha_af'))
    else:
        damp.append(('dmp_sf', 'Sense-electrode damping (sense frames)', ['sel_sf_L', 'sel_sf_R'], 'alpha_sf'))
    w("  static void physics(Model model) {")
    w("    model.component(\"comp1\").physics().create(\"solid\", \"SolidMechanics\", \"geom1\");")
    w("    model.component(\"comp1\").physics(\"solid\").create(\"fix1\", \"Fixed\", 3);")
    w("    model.component(\"comp1\").physics(\"solid\").feature(\"fix1\").label(\"Fixed: anchors bonded to the substrate\");")
    w("    model.component(\"comp1\").physics(\"solid\").feature(\"fix1\").selection().named(\"sel_anchor\");")
    for i, (t, lab, sels, a) in enumerate(damp):
        # union selection for the damping subnode
        arr = ', '.join(jstr(s) for s in sels)
        w(f"    union(model, \"comp1\", \"sel_{t}\", 3, new String[]{{{arr}}}, {jstr(lab)});")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"lemm1\").create(\"{t}\", \"Damping\", 3);")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"lemm1\").feature(\"{t}\").label({jstr('Rayleigh (mass-prop.) damping: ' + lab)});")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"lemm1\").feature(\"{t}\").selection().named(\"sel_{t}\");")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"lemm1\").feature(\"{t}\").set(\"DampingType\", \"RayleighDamping\");")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"lemm1\").feature(\"{t}\").set(\"alpha_dM\", \"{a}\");")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"lemm1\").feature(\"{t}\").set(\"beta_dK\", \"0\");")
    loads = [
        ('bl_drvL', 'Drive force, left tine: combs D1(top,+)/D2(bottom,-) -> +F_drive along y', 'sel_df_L', ['0', 'F_drive/V_dfL', '0']),
        ('bl_drvR', 'Drive force, right tine: combs D3/D4 (swapped AC phase) -> -F_drive along y', 'sel_df_R', ['0', '-F_drive/V_dfR', '0']),
        ('bl_senL', 'Sense test force (Fig. 9): +F_c along x on left Coriolis mass', 'sel_pm_L', ['F_c/V_pmL', '0', '0']),
        ('bl_senR', 'Sense test force (Fig. 9): -F_c along x on right Coriolis mass', 'sel_pm_R', ['-F_c/V_pmR', '0', '0']),
    ]
    for t, lab, s, vec in loads:
        arr = ', '.join(jstr(x) for x in vec)
        w(f"    model.component(\"comp1\").physics(\"solid\").create(\"{t}\", \"BodyLoad\", 3);")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"{t}\").label({jstr(lab)});")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"{t}\").selection().named(\"{s}\");")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"{t}\").set(\"forceReferenceVolume\", new String[]{{{arr}}});")
        w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"{t}\").set(\"forceDeformedVolume\", new String[]{{{arr}}});")
    cor = ['2*rho_si*Omega_z*(j*2*pi*freq*v)', '-2*rho_si*Omega_z*(j*2*pi*freq*u)', '0']
    arr = ', '.join(jstr(x) for x in cor)
    w("    model.component(\"comp1\").physics(\"solid\").create(\"bl_cor\", \"BodyLoad\", 3);")
    w("    model.component(\"comp1\").physics(\"solid\").feature(\"bl_cor\").label(\"Coriolis force -2*rho*Omega x v  (rotation Omega_z about z, frequency domain v = j*w*u)\");")
    w("    model.component(\"comp1\").physics(\"solid\").feature(\"bl_cor\").selection().all();")
    w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"bl_cor\").set(\"forceReferenceVolume\", new String[]{{{arr}}});")
    w(f"    model.component(\"comp1\").physics(\"solid\").feature(\"bl_cor\").set(\"forceDeformedVolume\", new String[]{{{arr}}});")
    w("  }")
    w("")
    # ---- mesh
    w("  static void mesh(Model model) {")
    w("    String[] hmax = {\"60\", \"40\", \"25\"};")
    w("    String[] hnar = {\"1\", \"2\", \"3\"};")
    w("    int k = Math.max(1, Math.min(3, MESH_LEVEL)) - 1;")
    w("    model.component(\"comp1\").mesh().create(\"mesh1\");")
    w("    model.component(\"comp1\").mesh(\"mesh1\").create(\"ftri1\", \"FreeTri\");")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").selection().named(\"sel_bottom\");")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").create(\"size1\", \"Size\");")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").feature(\"size1\").set(\"custom\", \"on\");")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").feature(\"size1\").set(\"hmax\", hmax[k]);")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").feature(\"size1\").set(\"hmaxactive\", true);")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").feature(\"size1\").set(\"hmin\", \"1\");")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").feature(\"size1\").set(\"hminactive\", true);")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").feature(\"size1\").set(\"hnarrow\", hnar[k]);")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").feature(\"size1\").set(\"hnarrowactive\", true);")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").feature(\"size1\").set(\"hgrad\", \"1.3\");")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"ftri1\").feature(\"size1\").set(\"hgradactive\", true);")
    w("    model.component(\"comp1\").mesh(\"mesh1\").create(\"swe1\", \"Sweep\");")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"swe1\").create(\"dis1\", \"Distribution\");")
    w("    model.component(\"comp1\").mesh(\"mesh1\").feature(\"swe1\").feature(\"dis1\").set(\"numelem\", MESH_LEVEL >= 3 ? 2 : 1);")
    w("    model.component(\"comp1\").mesh(\"mesh1\").run();")
    w("    log(\"Mesh 1 built (level \" + MESH_LEVEL + \"): \" + model.component(\"comp1\").mesh(\"mesh1\").getNumElem() + \" elements\");")
    w("  }")
    w("")
    # ---- electrostatic unit cells (component 2)
    w("  static void rect2(Model m, String tag, String x, String y, String wx, String wy) {")
    w("    m.component(\"comp2\").geom(\"geom2\").create(tag, \"Rectangle\");")
    w("    m.component(\"comp2\").geom(\"geom2\").feature(tag).set(\"pos\", new String[]{x, y});")
    w("    m.component(\"comp2\").geom(\"geom2\").feature(tag).set(\"size\", new String[]{wx, wy});")
    w("  }")
    w("  static void electrostaticCells(Model model) {")
    w("    model.component().create(\"comp2\", true);")
    w("    model.component(\"comp2\").label(\"Component 2: electrostatic unit cells - how the electrode voltages are applied\");")
    w("    model.component(\"comp2\").geom().create(\"geom2\", 2);")
    w("    model.component(\"comp2\").geom(\"geom2\").lengthUnit(\"\\u00b5m\");")
    w("    // (a) DRIVE comb cell: 1 rotor finger (GND) between two half stator fingers (V_cell_d); symmetry planes x=+-7 um")
    w("    rect2(model, \"air_d\", \"-7\", \"d_cell\", \"14\", \"70[um]-d_cell\");")
    w("    rect2(model, \"rf_d\", \"-2\", \"d_cell\", \"4\", \"50\");")
    w("    rect2(model, \"sr_d\", \"5\", \"10\", \"2\", \"60\");")
    w("    rect2(model, \"sl_d\", \"-7\", \"10\", \"2\", \"60\");")
    w("    model.component(\"comp2\").geom(\"geom2\").create(\"dif_d\", \"Difference\");")
    w("    model.component(\"comp2\").geom(\"geom2\").feature(\"dif_d\").selection(\"input\").set(\"air_d\");")
    w("    model.component(\"comp2\").geom(\"geom2\").feature(\"dif_d\").selection(\"input2\").set(\"rf_d\", \"sr_d\", \"sl_d\");")
    w("    // (b) SENSE parallel-plate cell: rotor plate (GND) between stator A (V_cell_s, gap g_s-d) and stator B (GND, gap g_s+d)")
    w("    rect2(model, \"air_s\", \"80\", \"-30\", \"40\", \"140\");")
    w("    rect2(model, \"rp_s\", \"98[um]+d_cell\", \"0\", \"4\", \"80\");")
    w("    rect2(model, \"sa_s\", \"105\", \"0\", \"4\", \"80\");")
    w("    rect2(model, \"sb_s\", \"91\", \"0\", \"4\", \"80\");")
    w("    model.component(\"comp2\").geom(\"geom2\").create(\"dif_s\", \"Difference\");")
    w("    model.component(\"comp2\").geom(\"geom2\").feature(\"dif_s\").selection(\"input\").set(\"air_s\");")
    w("    model.component(\"comp2\").geom(\"geom2\").feature(\"dif_s\").selection(\"input2\").set(\"rp_s\", \"sa_s\", \"sb_s\");")
    w("    model.component(\"comp2\").geom(\"geom2\").run();")
    # selections comp2 (boxes valid for |d_cell| <= 1 um)
    sel2 = [
        ('e_gnd_d1', 1, -2.1, -1.2, 2.1, 51.2, 'Drive cell: rotor finger (GND)'),
        ('e_gnd_d2', 1, -7.1, -1.2, 7.1, 1.2, 'Drive cell: rotor base (GND)'),
        ('e_v_d1', 1, 4.9, 9.9, 7.1, 70.1, 'Drive cell: stator finger right (V)'),
        ('e_v_d2', 1, -7.1, 9.9, -4.9, 70.1, 'Drive cell: stator finger left (V)'),
        ('e_v_d3', 1, -7.1, 69.9, 7.1, 70.1, 'Drive cell: stator base (V)'),
        ('e_gnd_s', 1, 79.9, -30.1, 120.1, 110.1, 'Sense cell: all boundaries (GND: rotor, stator B, shield)'),
        ('e_v_s', 1, 104.9, -0.1, 109.1, 80.1, 'Sense cell: stator A (V)'),
        ('e_air_d', 2, -7.1, -1.2, 7.1, 70.1, 'Drive cell air'),
        ('e_air_s', 2, 79.9, -30.1, 120.1, 110.1, 'Sense cell air'),
    ]
    for t, d, x0, y0, x1, y1, lab in sel2:
        w(f"    box(model, \"comp2\", \"{t}\", {d}, {jd(x0)}, {jd(y0)}, {jd(x1)}, {jd(y1)}, false, {jstr(lab)});")
    w("    union(model, \"comp2\", \"e_gnd_d\", 1, new String[]{\"e_gnd_d1\", \"e_gnd_d2\"}, \"Drive cell: rotor = GND (0 V)\");")
    w("    union(model, \"comp2\", \"e_v_d\", 1, new String[]{\"e_v_d1\", \"e_v_d2\", \"e_v_d3\"}, \"Drive cell: stator = V_DC + V_AC (peak)\");")
    w("    model.component(\"comp2\").material().create(\"mat2\", \"Common\");")
    w("    model.component(\"comp2\").material(\"mat2\").label(\"Air (eps_r = 1)\");")
    w("    model.component(\"comp2\").material(\"mat2\").selection().all();")
    w("    model.component(\"comp2\").material(\"mat2\").propertyGroup(\"def\").set(\"relpermittivity\", new String[]{\"1\"});")
    w("    model.component(\"comp2\").physics().create(\"es\", \"Electrostatics\", \"geom2\");")
    for t, lab, s in (('gnd_d', 'Ground: drive rotor finger (proof-mass side) 0 V', 'e_gnd_d'),
                      ('gnd_s', 'Ground: sense rotor plate, stator B and shield 0 V', 'e_gnd_s')):
        w(f"    model.component(\"comp2\").physics(\"es\").create(\"{t}\", \"Ground\", 1);")
        w(f"    model.component(\"comp2\").physics(\"es\").feature(\"{t}\").label({jstr(lab)});")
        w(f"    model.component(\"comp2\").physics(\"es\").feature(\"{t}\").selection().named(\"{s}\");")
    for t, lab, s, v in (('pot_d', 'Electric potential: drive stator D1 = V_DC + V_AC (peak)', 'e_v_d', 'V_cell_d'),
                         ('pot_s', 'Electric potential: sense stator A = V_s', 'e_v_s', 'V_cell_s')):
        w(f"    model.component(\"comp2\").physics(\"es\").create(\"{t}\", \"ElectricPotential\", 1);")
        w(f"    model.component(\"comp2\").physics(\"es\").feature(\"{t}\").label({jstr(lab)});")
        w(f"    model.component(\"comp2\").physics(\"es\").feature(\"{t}\").selection().named(\"{s}\");")
        w(f"    model.component(\"comp2\").physics(\"es\").feature(\"{t}\").set(\"V0\", \"{v}\");")
    for t, s in (('int_d', 'e_air_d'), ('int_s', 'e_air_s')):
        w(f"    model.component(\"comp2\").cpl().create(\"{t}\", \"Integration\");")
        w(f"    model.component(\"comp2\").cpl(\"{t}\").set(\"opname\", \"{t}\");")
        w(f"    model.component(\"comp2\").cpl(\"{t}\").selection().named(\"{s}\");")
    var2 = [('W_d', 'h_dev*int_d(0.5*epsilon0_const*es.normE^2)', 'Electric energy, one drive finger cell'),
            ('C_d', '2*W_d/V_cell_d^2', 'Capacitance of one rotor finger (2 gaps) to the stator'),
            ('F_d1', '0.5*dCd_an*V_cell_d^2', 'Analytic force on one rotor finger at V_cell_d'),
            ('dCd_an', '2*epsilon0_const*h_dev/g_d', 'Analytic dC/dy of one rotor finger'),
            ('W_s', 'h_dev*int_s(0.5*epsilon0_const*es.normE^2)', 'Electric energy, sense cell'),
            ('C_s', '2*W_s/V_cell_s^2', 'Capacitance of stator A (sense electrode)'),
            ('dCs_an', 'epsilon0_const*h_dev*L_se/g_s^2', 'Analytic dC/dx of one sense electrode')]
    w("    model.component(\"comp2\").variable().create(\"var2\");")
    for n, e_, d in var2:
        w(f"    model.component(\"comp2\").variable(\"var2\").set({jstr(n)}, {jstr(e_)});")
        w(f"    model.component(\"comp2\").variable(\"var2\").descr({jstr(n)}, {jstr(d)});")
    w("    model.component(\"comp2\").mesh().create(\"mesh2\");")
    w("    model.component(\"comp2\").mesh(\"mesh2\").autoMeshSize(2);")
    w("    model.component(\"comp2\").mesh(\"mesh2\").run();")
    w("  }")
    w("")
    # ---- studies
    loads_all = ['solid/bl_drvL', 'solid/bl_drvR', 'solid/bl_senL', 'solid/bl_senR', 'solid/bl_cor']
    def disabled(keep):
        return '"' + '", "'.join(x for x in loads_all if x not in keep) + '"'
    w("  static void disable(Model m, String std, String step, String[] feats) {")
    w("    m.study(std).feature(step).set(\"useadvanceddisable\", true);")
    w("    m.study(std).feature(step).set(\"disabledphysics\", feats);")
    w("  }")
    w("  static void studies(Model model) {")
    w("    // std_es: electrostatic unit cells, sweep of the rotor displacement")
    w("    model.study().create(\"std_es\");")
    w("    model.study(\"std_es\").label(\"Study 0: Electrostatic unit cells (C(d), dC/dd, fringe factors)\");")
    w("    model.study(\"std_es\").create(\"stat\", \"Stationary\");")
    w("    model.study(\"std_es\").feature(\"stat\").setEntry(\"activate\", \"solid\", false);")
    w("    model.study(\"std_es\").create(\"param\", \"Parametric\");")
    w("    model.study(\"std_es\").feature(\"param\").setIndex(\"pname\", \"d_cell\", 0);")
    w("    model.study(\"std_es\").feature(\"param\").setIndex(\"plistarr\", \"-0.6 -0.3 0 0.3 0.6\", 0);")
    w("    model.study(\"std_es\").feature(\"param\").setIndex(\"punit\", \"um\", 0);")
    studies = [
        ('std1', 'Study 1: Eigenfrequency - drive & sense modes (automatic identification)', 'eig', 'Eigenfrequency', []),
        ('std2', 'Study 2: Frequency domain - DRIVE response to the push-pull comb voltages', 'freq', 'Frequency', ['solid/bl_drvL', 'solid/bl_drvR']),
        ('std3', 'Study 3: Frequency domain - SENSE response to +/-1 uN (paper Fig. 9)', 'freq', 'Frequency', ['solid/bl_senL', 'solid/bl_senR']),
        ('std4', 'Study 4: Gyroscope operation - drive voltages + Coriolis (Omega_z sweep) -> C, V_out', 'freq', 'Frequency', ['solid/bl_drvL', 'solid/bl_drvR', 'solid/bl_cor']),
        ('std5', 'Study 5: Static - sense stiffness and amplification ratio R (paper Sec. 5.1)', 'stat', 'Stationary', ['solid/bl_senL', 'solid/bl_senR']),
    ]
    for tag, lab, step, typ, keep in studies:
        w(f"    model.study().create(\"{tag}\");")
        w(f"    model.study(\"{tag}\").label({jstr(lab)});")
        w(f"    model.study(\"{tag}\").create(\"{step}\", \"{typ}\");")
        w(f"    model.study(\"{tag}\").feature(\"{step}\").setEntry(\"activate\", \"es\", false);")
        w(f"    disable(model, \"{tag}\", \"{step}\", new String[]{{{disabled(keep)}}});")
    w("    model.study(\"std1\").feature(\"eig\").set(\"neigs\", 24);")
    w("    model.study(\"std1\").feature(\"eig\").set(\"neigsactive\", true);")
    w("    model.study(\"std1\").feature(\"eig\").set(\"shift\", \"12500[Hz]\");")
    w("    model.study(\"std1\").feature(\"eig\").set(\"shiftactive\", true);")
    w("    model.study(\"std4\").create(\"param\", \"Parametric\");")
    w("    model.study(\"std4\").feature(\"param\").setIndex(\"pname\", \"Omega_z\", 0);")
    w("    model.study(\"std4\").feature(\"param\").setIndex(\"plistarr\", \"-1 -0.5 0 0.5 1\", 0);")
    w("    model.study(\"std4\").feature(\"param\").setIndex(\"punit\", \"rad/s\", 0);")
    w("  }")
    w("")
    # ---- solve & post-processing (generic java, scheme-independent)
    w(JAVA_SOLVE.replace('@SCHEME@', scheme))
    w("}")
    src = '\n'.join(L) + '\n'
    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, cls + '.java')
    open(path, 'w').write(src)
    return path, P, parts


JAVA_SOLVE = r'''
  // ======================================================================
  //  Solving, automatic mode identification, post-processing
  // ======================================================================
  static Set<String> dsets(Model m) {
    return new LinkedHashSet<String>(Arrays.asList(m.result().dataset().tags()));
  }

  /** Runs a study and returns the tag of the dataset it created. */
  static String runStudy(Model m, String std) {
    Set<String> before = dsets(m);
    Set<String> solBefore = new LinkedHashSet<String>(Arrays.asList(m.sol().tags()));
    long t0 = System.currentTimeMillis();
    log(">> running " + std + " : " + m.study(std).label());
    m.study(std).run();
    String ds = null;
    for (String t : dsets(m)) if (!before.contains(t)) { ds = t; break; }
    if (ds == null) {   // no dataset generated automatically -> create one on the first new solution
      String sol = null;
      for (String t : m.sol().tags()) if (!solBefore.contains(t)) { sol = t; break; }
      ds = "dset_" + std;
      m.result().dataset().create(ds, "Solution");
      m.result().dataset(ds).set("solution", sol);
    }
    log("   done in " + (System.currentTimeMillis() - t0) / 1000 + " s, dataset " + ds);
    return ds;
  }

  static double[][] transpose(double[][] a) {
    double[][] b = new double[a[0].length][a.length];
    for (int i = 0; i < a.length; i++) for (int j = 0; j < a[0].length; j++) b[j][i] = a[i][j];
    return b;
  }

  /** Global evaluation -> result[expr][solution]. */
  static double[][] evalGlobal(Model m, String tag, String ds, String[] expr, String[] unit, String tbl) {
    m.result().numerical().create(tag, "EvalGlobal");
    m.result().numerical(tag).set("data", ds);
    m.result().numerical(tag).set("expr", expr);
    if (unit != null) m.result().numerical(tag).set("unit", unit);
    if (tbl != null) {
      m.result().table().create(tbl, "Table");
      m.result().numerical(tag).set("table", tbl);
      m.result().numerical(tag).setResult();
    }
    double[][] r = m.result().numerical(tag).getReal();
    if (r.length != expr.length && r.length > 0 && r[0].length == expr.length) r = transpose(r);
    return r;
  }

  static void writeCsv(String file, String header, double[][] cols) {
    try {
      PrintWriter pw = new PrintWriter(new FileWriter(file));
      pw.println(header);
      for (int i = 0; i < cols[0].length; i++) {
        StringBuilder sb = new StringBuilder();
        for (int c = 0; c < cols.length; c++) { if (c > 0) sb.append(','); sb.append(String.format(Locale.US, "%.9g", cols[c][i])); }
        pw.println(sb);
      }
      pw.close();
      log("   wrote " + file);
    } catch (IOException e) { log("!! csv " + e); }
  }

  static double slope(double[] x, double[] y) {
    double mx = 0, my = 0; int n = x.length;
    for (int i = 0; i < n; i++) { mx += x[i] / n; my += y[i] / n; }
    double sxy = 0, sxx = 0;
    for (int i = 0; i < n; i++) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) * (x[i] - mx); }
    return sxy / sxx;
  }

  /** frequency list: coarse span + finer bands around the resonance f0 */
  static String plist(double f0, double fd, double fs, boolean wide) {
    TreeSet<Double> s = new TreeSet<Double>();
    if (PAPER_RESOLUTION) {
      for (double f = 11000; f <= 15000 + 1e-9; f += 10) s.add(f);
      for (double f = f0 - 50; f <= f0 + 50 + 1e-9; f += 1) s.add(f);
      for (double f = f0 - 10; f <= f0 + 10 + 1e-9; f += 0.1) s.add(f);
    } else {
      if (wide) for (double f = 11000; f <= 15000 + 1e-9; f += 200) s.add(f);
      for (double f = f0 - 400; f <= f0 + 400 + 1e-9; f += 40) s.add(f);
      for (double f = f0 - 40; f <= f0 + 40 + 1e-9; f += 4) s.add(f);
      for (double f = f0 - 8; f <= f0 + 8 + 1e-9; f += 0.4) s.add(f);
    }
    s.add(fd); s.add(fs);
    StringBuilder sb = new StringBuilder();
    double last = -1;
    for (double f : s) {
      double r = Math.round(f * 100) / 100.0;
      if (r == last || r <= 0) continue;
      if (sb.length() > 0) sb.append(' ');
      sb.append(String.format(Locale.US, "%.2f", r));
      last = r;
    }
    return sb.toString();
  }

  static void plot3d(Model m, String tag, String label, String ds, int level, String expr, String title) {
    m.result().create(tag, "PlotGroup3D");
    m.result(tag).label(label);
    m.result(tag).set("data", ds);
    m.result(tag).set("looplevel", new int[]{level});
    m.result(tag).create("surf1", "Surface");
    m.result(tag).feature("surf1").set("expr", expr);
    m.result(tag).feature("surf1").create("def1", "Deform");
    try { m.result(tag).set("titletype", "manual"); m.result(tag).set("title", title); } catch (Exception e) { }
  }

  static void plot1d(Model m, String tag, String label, String ds, String[] expr, String[] descr, String ylabel, boolean ylog) {
    m.result().create(tag, "PlotGroup1D");
    m.result(tag).label(label);
    m.result(tag).set("data", ds);
    m.result(tag).create("glob1", "Global");
    m.result(tag).feature("glob1").set("expr", expr);
    m.result(tag).feature("glob1").set("descr", descr);
    try {
      m.result(tag).set("ylabelactive", true); m.result(tag).set("ylabel", ylabel);
      if (ylog) m.result(tag).set("ylog", true);
    } catch (Exception e) { }
  }

  static void image(Model m, String plot, String file) {
    try {
      String t = "img_" + plot;
      m.result().export().create(t, "Image");
      m.result().export(t).set("sourceobject", plot);
      m.result().export(t).set("pngfilename", new File(file).getAbsolutePath());
      m.result().export(t).run();
    } catch (Exception e) { log("   (image export skipped: " + e + ")"); }
  }

  static void solveAll(Model model) {
    String pre = OUT_MPH.replace(".mph", "");
    // ---------------- 0) electrostatic cells -> fringe factors ----------------
    try {
      String ds = runStudy(model, "std_es");
      double[][] r = evalGlobal(model, "gev_es", ds,
          new String[]{"d_cell", "comp2.C_d", "comp2.C_s", "comp2.dCd_an", "comp2.dCs_an", "comp2.W_d"},
          new String[]{"um", "fF", "fF", "fF/um", "fF/um", "J"}, "tbl_es");
      double sd = slope(r[0], r[1]), ss = slope(r[0], r[2]);
      double etaD = sd / r[3][0], etaS = ss / r[4][0];
      log(String.format(Locale.US, "   drive cell: C(0)=%.4f fF/finger, dC/dy=%.5f fF/um (analytic %.5f) -> eta_d=%.4f", r[1][r[1].length / 2], sd, r[3][0], etaD));
      log(String.format(Locale.US, "   sense cell: C(0)=%.4f fF/electrode, dC/dx=%.5f fF/um (analytic %.5f) -> eta_s=%.4f", r[2][r[2].length / 2], ss, r[4][0], etaS));
      if (etaD > 0.5 && etaD < 2) model.param().set("eta_d", String.format(Locale.US, "%.5f", etaD), "Drive comb fringe factor (from Study 0)");
      if (etaS > 0.5 && etaS < 2) model.param().set("eta_s", String.format(Locale.US, "%.5f", etaS), "Sense electrode fringe factor (from Study 0)");
      writeCsv(pre + "_electrostatic_cells.csv", "d_um,C_drive_finger_fF,C_sense_electrode_fF", new double[][]{r[0], r[1], r[2]});
      model.result().create("pg_es", "PlotGroup2D");
      model.result("pg_es").label("0. Electrostatic cells: potential V (drive comb left, sense plates right)");
      model.result("pg_es").set("data", ds);
      model.result("pg_es").create("surf1", "Surface");
      model.result("pg_es").feature("surf1").set("expr", "V");
      model.result("pg_es").create("con1", "Contour");
      model.result("pg_es").feature("con1").set("expr", "V");
      image(model, "pg_es", pre + "_electrostatic_cells.png");
    } catch (Exception e) { log("!! Study 0 failed: " + e + "  (eta_d = eta_s = 1 kept)"); }

    // ---------------- 1) eigenfrequencies + automatic drive/sense identification ----------------
    String dsEig = runStudy(model, "std1");
    String[] ex = new String[]{"real(freq)", "comp1.Q_mode", "comp1.P_drive", "comp1.P_drive_in", "comp1.P_sense", "comp1.P_sense_in", "comp1.R_fem"};
    double[][] e = evalGlobal(model, "gev_modes", dsEig, ex, new String[]{"Hz", "1", "1", "1", "1", "1", "1"}, "tbl_modes");
    model.result().table("tbl_modes").label("Eigenmodes: frequency, Q, participation (drive / sense, anti- / in-phase)");
    int n = e[0].length, kd = 0, ks = 0;
    // a mode's contribution to the anti-phase static compliance is ~ (P/f)^2 -> rank by P/f
    // drive candidates: P_drive > P_sense ; sense candidates: P_sense > P_drive  (never the same mode)
    double bd = -1, bs = -1;
    for (int i = 0; i < n; i++) {
      if (e[2][i] > e[4][i] && e[2][i] / e[0][i] > bd) { bd = e[2][i] / e[0][i]; kd = i; }
      if (e[4][i] > e[2][i] && e[4][i] / e[0][i] > bs) { bs = e[4][i] / e[0][i]; ks = i; }
    }
    double fd = e[0][kd], fs = e[0][ks];
    log("   mode table (k, f[Hz], Q, P_drive, P_drive_in, P_sense, P_sense_in):");
    for (int i = 0; i < n; i++)
      log(String.format(Locale.US, "   %2d %10.2f %8.1f %9.3g %9.3g %9.3g %9.3g%s", i + 1, e[0][i], e[1][i], e[2][i], e[3][i], e[4][i], e[5][i],
          (i == kd ? "  <== DRIVE (anti-phase y)" : (i == ks ? "  <== SENSE (anti-phase x)" : ""))));
    if (kd == ks) log("!! drive and sense identified as the same mode - check the model!");
    log(String.format(Locale.US, "   DRIVE mode #%d f=%.2f Hz | SENSE mode #%d f=%.2f Hz | df = %.2f Hz | R_fem(sense mode) = %.4f",
        kd + 1, fd, ks + 1, fs, fs - fd, e[6][ks]));
    writeCsv(pre + "_modes.csv", "f_Hz,Q,P_drive,P_drive_in,P_sense,P_sense_in,R_fem", e);
    model.param().set("f_drive", String.format(Locale.US, "%.3f[Hz]", fd), "Drive-mode frequency (Study 1, mode " + (kd + 1) + ")");
    model.param().set("f_sense", String.format(Locale.US, "%.3f[Hz]", fs), "Sense-mode frequency (Study 1, mode " + (ks + 1) + ")");
    plot3d(model, "pg_drive", "1. DRIVE mode (anti-phase y, mode " + (kd + 1) + ")", dsEig, kd + 1, "v",
        String.format(Locale.US, "Drive mode #%d: f = %.1f Hz (colour: y-displacement v)", kd + 1, fd));
    plot3d(model, "pg_sense", "2. SENSE mode (anti-phase x, mode " + (ks + 1) + ")", dsEig, ks + 1, "@SCHEME@".equals("I") ? "v" : "u",
        String.format(Locale.US, "Sense mode #%d: f = %.1f Hz (colour: %s)", ks + 1, fs, "@SCHEME@".equals("I") ? "y-displacement v - amplified frames" : "x-displacement u"));
    image(model, "pg_drive", pre + "_drive_mode.png");
    image(model, "pg_sense", pre + "_sense_mode.png");

    // ---------------- 2) drive frequency response ----------------
    model.study("std2").feature("freq").set("plist", plist(fd, fd, fs, false));
    model.study("std2").feature("freq").set("punit", "Hz");
    String dsD = runStudy(model, "std2");
    double[][] d = evalGlobal(model, "gev_drv", dsD, new String[]{"freq", "abs(comp1.y_drive)", "abs(comp1.uL-comp1.uR)/2"},
        new String[]{"Hz", "um", "um"}, null);
    writeCsv(pre + "_drive_FRF.csv", "f_Hz,drive_amplitude_um,parasitic_sense_um", d);
    plot1d(model, "pg_drvfrf", "3. Drive response to the push-pull comb voltages", dsD,
        new String[]{"abs(comp1.y_drive)"}, new String[]{"Drive amplitude |y_d| (per tine)"}, "Drive amplitude (um)", false);
    image(model, "pg_drvfrf", pre + "_drive_FRF.png");

    // ---------------- 3) sense frequency response (Fig. 9) ----------------
    model.study("std3").feature("freq").set("plist", plist(fs, fd, fs, true));
    model.study("std3").feature("freq").set("punit", "Hz");
    String dsS = runStudy(model, "std3");
    double[][] s = evalGlobal(model, "gev_sen", dsS, new String[]{"freq", "abs(comp1.a_out)", "abs(comp1.d_out)", "abs(comp1.dC_diff)", "abs(comp1.x_an)", "abs(comp1.R_fem)"},
        new String[]{"Hz", "um", "um", "fF", "um", "1"}, null);
    int ip = 0;
    for (int i = 0; i < s[0].length; i++) if (s[1][i] > s[1][ip]) ip = i;
    int j1 = ip, j2 = ip;
    while (j1 > 0 && s[1][j1] > s[1][ip] / Math.sqrt(2)) j1--;
    while (j2 < s[0].length - 1 && s[1][j2] > s[1][ip] / Math.sqrt(2)) j2++;
    double Q = s[0][ip] / Math.max(1e-9, (s[0][j2] - s[0][j1]));
    log(String.format(Locale.US, "   FIG.9: peak sense-frame amplitude %.4f um at %.2f Hz, Q(-3dB) ~ %.0f, dC_diff = %.3f fF, R_fem = %.4f",
        s[1][ip], s[0][ip], Q, s[3][ip], s[5][ip]));
    writeCsv(pre + "_sense_FRF_fig9.csv", "f_Hz,sense_frame_amplitude_um,differential_disp_um,dC_diff_fF,x_l_minus_x_r_um,R_fem", s);
    plot1d(model, "pg_fig9", "4. Fig. 9: sense-frame amplitude under +/-1 uN", dsS,
        new String[]{"abs(comp1.a_out)"}, new String[]{"@SCHEME@".equals("I") ? "Amplified sense frame |y_a1|" : "Sense frame |x_l|"}, "Amplitude (um)", false);
    plot1d(model, "pg_dC", "5. Differential sense capacitance under +/-1 uN", dsS,
        new String[]{"abs(comp1.dC_diff)"}, new String[]{"|C(S+) - C(S-)|"}, "dC (F)", false);
    image(model, "pg_fig9", pre + "_fig9.png");

    // ---------------- 4) gyroscope operation (drive + Coriolis) ----------------
    model.study("std4").feature("freq").set("plist", String.format(Locale.US, "%.3f", fd));
    model.study("std4").feature("freq").set("punit", "Hz");
    String dsG = runStudy(model, "std4");
    double[][] g = evalGlobal(model, "gev_gyro", dsG, new String[]{"Omega_z", "abs(comp1.y_drive)", "abs(comp1.a_out)", "abs(comp1.d_out)", "abs(comp1.dC_diff)", "abs(comp1.V_out)", "comp1.F_drive"},
        new String[]{"rad/s", "um", "nm", "nm", "aF", "mV", "uN"}, "tbl_gyro");
    model.result().table("tbl_gyro").label("Gyro operation at f_drive: Omega, drive amp., sense amp., dC, V_out");
    writeCsv(pre + "_gyro_operation.csv", "Omega_rad_s,drive_amp_um,sense_frame_amp_nm,differential_disp_nm,dC_diff_aF,V_out_mV,F_drive_uN", g);
    int last = g[0].length - 1;
    log(String.format(Locale.US, "   GYRO @ f_drive: F_drive=%.3f uN, drive amp %.3f um; at Omega=%.2f rad/s: sense frame %.4f nm, dC=%.3f aF, V_out=%.4f mV  -> %.4f mV/(rad/s) = %.5f mV/(deg/s)",
        g[6][last], g[1][last], g[0][last], g[2][last], g[4][last], g[5][last], g[5][last] / Math.abs(g[0][last]), g[5][last] / Math.abs(g[0][last]) * Math.PI / 180));
    plot1d(model, "pg_gyro", "6. Gyro output: V_out vs input rate", dsG,
        new String[]{"abs(comp1.V_out)"}, new String[]{"|V_out| (charge amplifier)"}, "V_out (V)", false);
    try { model.result("pg_gyro").feature("glob1").set("xdata", "expr"); model.result("pg_gyro").feature("glob1").set("xdataexpr", "Omega_z"); } catch (Exception ex2) { }

    // ---------------- 5) static stiffness / amplification ----------------
    String dsT = runStudy(model, "std5");
    double[][] t = evalGlobal(model, "gev_stat", dsT, new String[]{"comp1.uL-comp1.uR", "comp1.xsL-comp1.xsR", "comp1.yT-comp1.yB", "comp1.R_fem", "2*F_c/(comp1.uL-comp1.uR)", "R_theory"},
        new String[]{"um", "um", "um", "1", "N/m", "1"}, "tbl_static");
    model.result().table("tbl_static").label("Static: x_l-x_r, y_T-y_B, R_fem, k_an = 2F/x_an, R_theory");
    log(String.format(Locale.US, "   STATIC (+/-%s): x_l-x_r = %.5f um, y_T-y_B = %.5f um, R_fem = %.4f (theory %.4f), k_an = %.1f N/m",
        "1 uN", t[0][0], t[2][0], t[3][0], t[5][0], t[4][0]));
    plot3d(model, "pg_static", "7. Static deformation under +/-1 uN (sense axis)", dsT, 1, "solid.disp", "Static deformation, anti-phase 1 uN on the Coriolis masses");

    // ---------------- summary ----------------
    try {
      PrintWriter pw = new PrintWriter(new FileWriter(pre + "_summary.txt"));
      pw.println("Scheme @SCHEME@ summary");
      pw.println(String.format(Locale.US, "f_drive_Hz=%.3f%nf_sense_Hz=%.3f%ndf_Hz=%.3f%nfig9_peak_um=%.5f%nfig9_peak_f_Hz=%.3f%nQ_sense=%.1f%ndC_peak_fF=%.4f%n",
          fd, fs, fs - fd, s[1][ip], s[0][ip], Q, s[3][ip]));
      pw.println(String.format(Locale.US, "R_fem_static=%.5f%nk_an_N_per_m=%.2f%nV_out_per_rad_s_mV=%.5f%ndC_per_rad_s_aF=%.5f%ndrive_amp_um=%.4f%n",
          t[3][0], t[4][0], g[5][last] / Math.abs(g[0][last]), g[4][last] / Math.abs(g[0][last]), g[1][last]));
      pw.close();
    } catch (IOException ex3) { log("!! summary " + ex3); }
  }
'''

if __name__ == '__main__':
    for sc in ('I', 'II'):
        path, P, parts = emit(sc)
        print('wrote', os.path.relpath(path), len(parts), 'parts')
