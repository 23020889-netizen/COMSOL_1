"""Draw the 2D layout of a scheme (PNG)."""
import sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
import tfg_geometry as G

COL = {'anchor': '#222222', 'pm': '#38d6e8', 'df': '#4caf50', 'sf': '#9e9d24', 'af': '#f2e34c',
       'vb': '#f39c12', 'spring': '#d32f2f', 'amp': '#f39c12', 'lever': '#666666', 'link': '#999999'}

def color(g):
    return COL.get(g.split('_')[0], '#aaaaaa')

def draw(scheme, out, zoom=None):
    P, parts, info = G.build(scheme)
    fig, ax = plt.subplots(figsize=(15, 10))
    for p in parts:
        sh = G.to_shapely(p)
        ax.add_patch(MP(list(sh.exterior.coords), fc=color(p['group']), ec='k', lw=0.15))
    ax.autoscale(); ax.set_aspect('equal')
    if zoom: ax.set_xlim(zoom[0], zoom[1]); ax.set_ylim(zoom[2], zoom[3])
    ax.set_title(f"Scheme {scheme} layout (um) - {'chevron amplifier' if scheme=='I' else 'conventional, diamond coupling'}")
    plt.savefig(out, dpi=130, bbox_inches='tight'); plt.close(fig)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    for sc in ('I', 'II'):
        draw(sc, f'{out}/layout_scheme{sc}.png')
        draw(sc, f'{out}/layout_scheme{sc}_center.png', zoom=(-1300, 1300, -1100, 1100))
