"""Figure: where each voltage is applied (both schemes)."""
import sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Rectangle
import tfg_geometry as G, draw_layout as D

def draw(scheme, out):
    P, parts, info = G.build(scheme)
    fig, ax = plt.subplots(figsize=(15, 10.5))
    for p in parts:
        ax.add_patch(MP(list(G.to_shapely(p).exterior.coords), fc=D.color(p['group']), ec='k', lw=0.1, alpha=0.55))
    Xc, ytop = P['Xc'], P['H_pm'] / 2 + P['L_pd'] + P['H_df']
    comb = dict(D1=(-Xc, ytop, '#d62728', 'V$_{DC}$+V$_{AC}$sin$\\omega$t'), D2=(-Xc, -ytop, '#1f77b4', 'V$_{DC}$-V$_{AC}$sin$\\omega$t'),
                D3=(Xc, ytop, '#1f77b4', 'V$_{DC}$-V$_{AC}$sin$\\omega$t'), D4=(Xc, -ytop, '#d62728', 'V$_{DC}$+V$_{AC}$sin$\\omega$t'))
    for k, (x, y, c, lab) in comb.items():
        sy = 1 if y > 0 else -1
        ax.add_patch(Rectangle((x - 600, y if sy > 0 else y - 45), 1200, 45, fc=c, ec='k', lw=0.8))
        ax.text(x, y + sy * 420, f'{k}: {lab}', ha='center', va='center', fontsize=11, color=c, weight='bold')
    if scheme == 'I':
        W, ya = P['W_af'], info['y_apex'] + P['apex_h']
        for sy in (1, -1):
            y0 = sy * ya; y1 = sy * (ya + P['H_af'])
            ax.add_patch(Rectangle((-W / 2 + 40, min(y0, y1) + 40), W / 2 - 60, P['H_af'] - 80, fc='none', ec='#9467bd', lw=2, hatch='//'))
            ax.add_patch(Rectangle((20, min(y0, y1) + 40), W / 2 - 60, P['H_af'] - 80, fc='none', ec='#ff7f0e', lw=2, hatch='\\\\'))
        ax.text(0, 1150, 'Amplified frames: 36 sense electrodes\nS+ (purple) / S- (orange), bias V$_s$ = 5 V', ha='center', fontsize=11)
    else:
        xi = info['x_sf_far']
        for sx in (-1, 1):
            for xs in (sx * xi, sx * (2 * Xc - xi)):
                ax.add_patch(Rectangle((xs - 60 if sx < 0 else xs - 60, -800), 120, 800, fc='none', ec='#9467bd', lw=2, hatch='//'))
                ax.add_patch(Rectangle((xs - 60, 0), 120, 800, fc='none', ec='#ff7f0e', lw=2, hatch='\\\\'))
        ax.text(0, 1150, 'Sense frames: 36 sense electrodes\nS+ (purple) / S- (orange), bias V$_s$ = 5 V', ha='center', fontsize=11)
    ax.text(0, -2350, 'Rotor = all moving silicon, connected through the anchors = GND (0 V).   '
            'Net drive force per tine: F = 2 (dC/dy) V$_{DC}$ V$_{AC}$ sin$\\omega$t  (DC and 2$\\omega$ terms cancel)',
            ha='center', fontsize=11)
    ax.set_xlim(-3300, 3300); ax.set_ylim(-2550, 2450); ax.set_aspect('equal')
    ax.set_title(f'Scheme {scheme}: electrode voltages (push-pull drive D1-D4, differential sense S+/S-)')
    plt.savefig(out, dpi=120, bbox_inches='tight'); plt.close(fig)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    for sc in ('I', 'II'):
        draw(sc, f'{out}/voltage_scheme_{sc}.png')
