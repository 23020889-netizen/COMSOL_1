"""After running both COMSOL builders: compare Scheme I vs Scheme II from the exported files.
Usage: python compare_comsol_runs.py <folder with *_summary.txt and *_sense_FRF_fig9.csv>"""
import sys, os, csv

def summary(path):
    d = {}
    for line in open(path):
        if '=' in line:
            k, v = line.strip().split('=', 1)
            try: d[k] = float(v)
            except ValueError: pass
    return d

def frf(path):
    rows = list(csv.reader(open(path)))[1:]
    return [float(r[0]) for r in rows], [float(r[1]) for r in rows], [float(r[3]) for r in rows]

folder = sys.argv[1] if len(sys.argv) > 1 else '.'
I = summary(os.path.join(folder, 'MEMS_TFG_SchemeI_Chevron_v2_summary.txt'))
II = summary(os.path.join(folder, 'MEMS_TFG_SchemeII_Conventional_v2_summary.txt'))
rows = [('f_drive_Hz', 'Tan so Drive (Hz)'), ('f_sense_Hz', 'Tan so Sense (Hz)'), ('df_Hz', 'Do lech f_s - f_d (Hz)'),
        ('fig9_peak_um', 'Bien do dinh Fig.9 (um)'), ('Q_sense', 'Q sense'), ('dC_peak_fF', 'dC vi sai tai dinh (fF)'),
        ('R_fem_static', 'He so khuech dai R (FEM)'), ('k_an_N_per_m', 'k anti-phase (N/m)'),
        ('drive_amp_um', 'Bien do drive tai f_d (um)'), ('dC_per_rad_s_aF', 'dC / Omega (aF per rad/s)'),
        ('V_out_per_rad_s_mV', 'V_out / Omega (mV per rad/s)')]
lines = ['| Dai luong | Scheme I (Chevron) | Scheme II (Truyen thong) | I / II |', '|---|---|---|---|']
for k, lab in rows:
    a, b = I.get(k), II.get(k)
    ratio = f'{a/b:.3f}' if a and b else '-'
    lines.append(f'| {lab} | {a:.5g} | {b:.5g} | {ratio} |' if a is not None and b is not None else f'| {lab} | {a} | {b} | - |')
txt = '\n'.join(lines)
print(txt)
open(os.path.join(folder, 'comparison_SchemeI_vs_SchemeII.md'), 'w').write(txt + '\n')
try:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
    for tag, lab, col in (('SchemeI_Chevron', 'Scheme I (chevron) - amplified frame', '#c0392b'),
                          ('SchemeII_Conventional', 'Scheme II (conventional) - sense frame', '#2471a3')):
        f, a, dc = frf(os.path.join(folder, f'MEMS_TFG_{tag}_v2_sense_FRF_fig9.csv'))
        ax[0].plot(f, a, color=col, label=lab); ax[1].plot(f, dc, color=col, label=lab)
    ax[0].set_ylabel('Amplitude (um)'); ax[1].set_ylabel('|dC_diff| (fF)')
    for x in ax: x.set_xlabel('Frequency (Hz)'); x.grid(alpha=.3); x.legend()
    plt.savefig(os.path.join(folder, 'comparison_fig9.png'), dpi=130, bbox_inches='tight')
    print('wrote comparison_fig9.png')
except Exception as e:
    print('plot skipped:', e)
