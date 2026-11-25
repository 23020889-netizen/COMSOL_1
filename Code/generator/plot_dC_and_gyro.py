"""Plot differential capacitance ΔC_diff(f) and Gyro output ΔC(Ω), V_out(Ω) comparison from COMSOL 6.3 CSV data."""
import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['mathtext.fontset'] = 'cm'

BASE = r"C:\Users\minht\OneDrive\Máy tính\Study\CNVCDT\COMSOL_1\Code\comsol"
OUT_DC = os.path.join(BASE, "comparison_dC_diff.png")
OUT_GYRO = os.path.join(BASE, "comparison_gyro_dC_Vout.png")


def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        rows = list(r)
    return {k: np.array([float(row[k]) for row in rows]) for k in rows[0].keys()}


def main():
    s1 = read_csv(os.path.join(BASE, "MEMS_TFG_SchemeI_Chevron_v2_sense_FRF_fig9.csv"))
    s2 = read_csv(os.path.join(BASE, "MEMS_TFG_SchemeII_Conventional_v2_sense_FRF_fig9.csv"))

    # 1. Comparison of dC_diff(f)
    fig, ax = plt.subplots(figsize=(9.5, 5.6), dpi=220, facecolor='white')
    ax.plot(s1['f_Hz'] / 1e3, s1['dC_diff_fF'], color='#1D4ED8', lw=2.2,
            label=r"Scheme I (Chevron): đỉnh $\Delta C_{\mathrm{diff}} = 138.07\;\mathrm{fF}$ @ $13.081\;\mathrm{kHz}$")
    ax.plot(s2['f_Hz'] / 1e3, s2['dC_diff_fF'], color='#DC2626', lw=2.2, ls='--',
            label=r"Scheme II (Truyền thống): đỉnh $\Delta C_{\mathrm{diff}} = 55.18\;\mathrm{fF}$ @ $13.116\;\mathrm{kHz}$")

    i1 = int(np.argmax(s1['dC_diff_fF']))
    i2 = int(np.argmax(s2['dC_diff_fF']))
    ax.scatter([s1['f_Hz'][i1] / 1e3], [s1['dC_diff_fF'][i1]], color='#1D4ED8', s=45, zorder=5)
    ax.scatter([s2['f_Hz'][i2] / 1e3], [s2['dC_diff_fF'][i2]], color='#DC2626', s=45, zorder=5)

    ax.annotate(
        r"$\Delta C_{\mathrm{I}} / \Delta C_{\mathrm{II}} = 2.502\times$",
        xy=(s1['f_Hz'][i1] / 1e3, s1['dC_diff_fF'][i1]),
        xytext=(13.65, 118),
        fontsize=12, fontweight='bold', color='#1E3A8A',
        arrowprops=dict(arrowstyle='->', color='#1E3A8A', lw=1.3),
        bbox=dict(boxstyle='round,pad=0.35', fc='#EFF6FF', ec='#93C5FD')
    )

    ax.set_title(r"So sánh biến thiên điện dung vi sai $\Delta C_{\mathrm{diff}}(f)$ dưới lực thử $\pm 1\;\mu\mathrm{N}$",
                 fontsize=13.5, fontweight='bold', pad=12)
    ax.set_xlabel(r"Tần số kích thích $f$ (kHz)", fontsize=11.5)
    ax.set_ylabel(r"Biến thiên điện dung vi sai $|\Delta C_{\mathrm{diff}}|$ (fF)", fontsize=11.5)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', fontsize=10, framealpha=0.95)
    ax.set_xlim(11.0, 15.0)
    ax.set_ylim(0, 155)
    plt.tight_layout()
    plt.savefig(OUT_DC, dpi=220, facecolor='white')
    plt.close(fig)

    # 2. Gyro operation: dC(Omega) & V_out(Omega) across 0..300 deg/s
    g1 = read_csv(os.path.join(BASE, "MEMS_TFG_SchemeI_Chevron_v2_gyro_operation.csv"))
    g2 = read_csv(os.path.join(BASE, "MEMS_TFG_SchemeII_Conventional_v2_gyro_operation.csv"))

    # Use linear sensitivity at 1 rad/s (= 57.2958 deg/s) from COMSOL Study 4
    dC_per_rad_1 = float(g1['dC_diff_aF'][-1])  # aF per rad/s (at 1 rad/s)
    dC_per_rad_2 = float(g2['dC_diff_aF'][-1])
    V_per_rad_1 = float(g1['V_out_mV'][-1])
    V_per_rad_2 = float(g2['V_out_mV'][-1])

    omega_deg = np.linspace(0, 300, 100)
    omega_rad = np.deg2rad(omega_deg)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), dpi=220, facecolor='white')

    ax1.plot(omega_deg, (dC_per_rad_1 * omega_rad) / 1000.0, color='#1D4ED8', lw=2.2,
             label=rf"Scheme I: {dC_per_rad_1/57.2958:.2f} aF/(°/s)")
    ax1.plot(omega_deg, (dC_per_rad_2 * omega_rad) / 1000.0, color='#DC2626', lw=2.2, ls='--',
             label=rf"Scheme II: {dC_per_rad_2/57.2958:.2f} aF/(°/s)")
    ax1.set_title(r"Biến thiên điện dung vi sai $\Delta C_{\mathrm{diff}}$ theo tốc độ góc $\Omega_z$",
                  fontsize=11.5, fontweight='bold')
    ax1.set_xlabel(r"Tốc độ góc đầu vào $\Omega_z$ (°/s)", fontsize=10.5)
    ax1.set_ylabel(r"Biến thiên điện dung $\Delta C_{\mathrm{diff}}$ (fF)", fontsize=10.5)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', fontsize=9.5)

    ax2.plot(omega_deg, V_per_rad_1 * omega_rad, color='#1D4ED8', lw=2.2,
             label=rf"Scheme I: {V_per_rad_1/57.2958:.4f} mV/(°/s)")
    ax2.plot(omega_deg, V_per_rad_2 * omega_rad, color='#DC2626', lw=2.2, ls='--',
             label=rf"Scheme II: {V_per_rad_2/57.2958:.4f} mV/(°/s)")
    ax2.set_title(r"Điện áp đầu ra $V_{\mathrm{out}}$ ($V_{\mathrm{bias}} = 5\;\mathrm{V},\; C_f = 100\;\mathrm{fF}$)",
                  fontsize=11.5, fontweight='bold')
    ax2.set_xlabel(r"Tốc độ góc đầu vào $\Omega_z$ (°/s)", fontsize=10.5)
    ax2.set_ylabel(r"Điện áp đầu ra $V_{\mathrm{out}}$ (mV)", fontsize=10.5)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', fontsize=9.5)

    plt.tight_layout()
    plt.savefig(OUT_GYRO, dpi=220, facecolor='white')
    plt.close(fig)
    print("Saved:", OUT_DC)
    print("Saved:", OUT_GYRO)


if __name__ == "__main__":
    main()
