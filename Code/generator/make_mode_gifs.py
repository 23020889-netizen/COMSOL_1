"""Assemble the 12 PNG phase frames written by COMSOL (…_drive_mode_phase000.png … phase330.png)
into looping GIFs (…_drive_mode_phase.gif).  Usage: python make_mode_gifs.py <folder>"""
import sys, os, glob, re
from PIL import Image

folder = sys.argv[1] if len(sys.argv) > 1 else '.'
bases = sorted({re.sub(r'_phase\d{3}\.png$', '', f) for f in glob.glob(os.path.join(folder, '*_phase[0-9][0-9][0-9].png'))})
for b in bases:
    frames = sorted(glob.glob(b + '_phase[0-9][0-9][0-9].png'))
    imgs = [Image.open(f).convert('RGB').convert('P', palette=Image.ADAPTIVE) for f in frames]
    out = b + '_phase.gif'
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=90, loop=0)
    print(f'{out}: {len(imgs)} frames')
