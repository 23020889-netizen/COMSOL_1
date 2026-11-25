"""Material, damping and electrical parameters shared by BOTH schemes.
Sources: Hu et al., Micromachines 2025, 16, 195 (Tables 2 and 5)."""

MATERIAL = dict(rho=2320.0, E=170e9, nu=0.22)      # Table 2 (single value for both files!)

# Viscous damping coefficients, Table 5 [N s/m]
DAMP = dict(
    c_d=2.61e-5,   # drive axis (proof-mass slide film + drive electrodes)
    c_s1=2.42e-5,  # sense axis, Scheme I (proof-mass slide film)
    c_s2=1.35e-6,  # amplified sense frame, Scheme I (sense electrodes)
    c_s=2.49e-5,   # sense axis, Scheme II (proof mass + sense electrodes)
)
# Split into mass-proportional (Rayleigh alpha) dashpots on each rigid part:
#   proof mass      : c_pm  = c_s1            (slide-film under the Coriolis mass, isotropic)
#   drive frames    : c_df  = c_d  - c_pm     (drive comb electrodes)
#   Scheme I  AF    : c_af  = c_s2            (sense electrodes on amplified frames)
#   Scheme II SF    : c_sf  = c_s  - c_pm     (sense electrodes on sense frames)
#   Scheme I  SF    : 0                       (decouple frames carry no electrodes)
def dashpots(scheme):
    c_pm = DAMP['c_s1']
    d = dict(pm=c_pm, df=DAMP['c_d'] - c_pm)
    if scheme == 'I':
        d.update(af=DAMP['c_s2'], sf=0.0)
    else:
        d.update(sf=DAMP['c_s'] - c_pm)
    return d

# Electrodes (lumped, omitted from the 3D geometry exactly like in the paper)
ELEC = dict(
    eps0=8.854187817e-12,
    # drive: lateral comb drives, one comb on the outer edge of every drive frame
    N_d=50,          # rotor fingers per comb  (A_de = 2 combs x 50 x 2 sides x 40 um x 40 um = 3.2e5 um^2, Table 5)
    L0_d=40e-6,      # finger overlap
    g_d=3e-6,        # finger gap (Table 5, d_e)
    V_DC=20.0,       # DC polarisation of the drive combs
    V_AC=5.0,        # AC drive amplitude
    # sense: differential parallel-plate electrodes, SAME number in both schemes
    N_s=36,          # electrodes in total (A_se = 36 x 80 um x 40 um = 1.152e5 um^2, Table 5)
    L_s=80e-6,       # electrode overlap length
    g_s=3e-6,        # sense gap
    V_s=5.0,         # DC sense bias across the sense capacitors
    C_f=100e-15,     # feedback capacitor of the charge amplifier
)

F_CORIOLIS_TEST = 1e-6   # 1 uN anti-phase harmonic force for the Fig.9 comparison (paper Sec. 5.3)
OMEGA_TEST = 1.0         # rad/s input rate for the full gyro-operation study
