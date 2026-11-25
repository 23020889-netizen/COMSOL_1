"""Audit of the ORIGINAL .mph files (no COMSOL needed): parameters, materials, loads,
plot-group mode indices, the expressions behind the plotted curves and the eigenfrequencies
actually stored in the solution (decoded from solution1.mphbin).
Usage: python analyze_old_mph.py ../MEMS_Tuning_Fork_Gyroscope_*.mph"""
import sys, zipfile, struct, re, math
import xml.etree.ElementTree as ET


def eigvals(binblob):
    """complex eigenvalues lambda (rad/s) stored as consecutive little-endian doubles (re, im)."""
    out = []
    for i in range(len(binblob) - 16):
        re_, im_ = struct.unpack('<dd', binblob[i:i + 16])
        if 1.0 < re_ < 1e5 and -1e8 < im_ < -1e3 and 50 < -im_ / (2 * re_) < 1e5:
            out.append((i, re_, -im_))
    # keep the regular stride-21 table
    vals, last = [], -100
    for i, r, w in out:
        if i - last >= 16:
            vals.append((w / 2 / math.pi, w / (2 * r))); last = i
    return vals


def audit(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read('dmodel.xml'))
    print('=' * 100); print(path)
    smodel = z.read('smodel.json').decode('utf8', 'ignore')
    for m in re.finditer(r'"description":"([^"]*)","name":"([^"]*)","scalarImag":"[^"]*","scalarReal":"[^"]*","value":"([^"]*)"', smodel):
        print(f'  param {m.group(2):18s} = {m.group(3):14s}  # {m.group(1)}')
    phys = [e for e in root.iter() if e.get('op') in ('Electrostatics', 'ElectromechanicalForces', 'Electromechanics')]
    print('  Electrostatics / electromechanics physics present:', bool(phys))
    for e in root.iter():
        if e.get('op') == 'BodyLoad':
            for c in e:
                if c.tag == 'param' and c.get('param') == 'forceReferenceVolume':
                    print(f"  BodyLoad {e.get('tag')}: {c.get('value')}")
        if e.get('op') == 'Damping':
            for c in e:
                if c.tag == 'param' and c.get('param') == 'eta_s':
                    print(f"  Damping loss factor eta_s = {c.get('value')}  (Q forced = 1/eta)")
        if e.get('op') == 'Roller':
            print('  Roller constraint present (w = 0 on the whole bottom face)')
        if e.get('op') == 'PlotGroup3D':
            ll = [c.get('valueMatrix') for c in e if c.tag == 'propertyValue' and c.get('name') == 'p:looplevel']
            print(f"  3D plot {e.get('tag'):22s} eigen-solution index {ll}  '{e.get('name')[:70]}'")
        if e.get('op') in ('Global', 'Surface') and e.get('tag', '').startswith(('glob', 'surf_v')):
            ex = [c.get('valueMatrix') or c.get('value') for c in e if c.tag == 'propertyValue' and c.get('name') == 'p:expr']
            print(f"  plotted expression {e.get('tag')}: {ex[0][:160] if ex else ''}")
    for n in z.namelist():
        if n == 'solution1.mphbin':
            ev = eigvals(z.read(n))
            print('  stored eigenfrequencies (Hz, Q):', ', '.join(f'{f:.0f} ({q:.0f})' for f, q in ev))


if __name__ == '__main__':
    for p in sys.argv[1:]:
        audit(p)
