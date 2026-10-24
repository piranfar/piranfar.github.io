"""Prepare inner-membrane PDBs in scene coordinates (Angstrom; Molecular Nodes
scales by 0.1 so 1 Blender unit = 1 nm).

Sources
  - MemProtMD 4dx5: AcrB efflux pump in a DPPC bilayer (water removed)
  - OPM 3vma: full-length E. coli PBP1b, pre-oriented (membrane normal = z,
    membrane centre at z = 0, periplasm = +z)

Steps
  1. unwrap AcrB atoms that crossed the periodic z boundary
  2. rotate the MemProtMD system 180 deg about x (periplasmic side was -z there;
     a proper rotation, so chirality is preserved) and translate it so the
     bilayer centre sits at IM_CENTER_Z and AcrB sits at ACRB_XY
  3. drop OPM dummy/water/ligand records, translate PBP1b so its TM helix sits
     in the bilayer at PBP_XY, and remove DPPC lipids that would overlap it
Outputs: traj/inner_membrane/im_lipids.pdb, im_acrb.pdb, im_pbp1b.pdb
"""
import os, math

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
SRC_IM = os.path.join(BASE, 'pdb', 'memprotmd', '4dx5_membrane_nowater.pdb')
SRC_PBP = os.path.join(BASE, 'pdb', 'opm', '3vma_opm.pdb')
OUT = os.path.join(BASE, 'traj', 'inner_membrane')
os.makedirs(OUT, exist_ok=True)

BOX_Z = 183.405            # MemProtMD box C (A)
BILAYER_CENTER_LOCAL = 105.0   # DPPC z-centre in the MemProtMD file (A)
ACRB_XY_LOCAL = (73.7, 80.7)   # AcrB xy centroid in the MemProtMD file (A)
DARPIN_FIRST_RES = 3111        # first non-AcrB residue in the MemProtMD numbering

OM_BOTTOM_Z = 36.0         # scene: lowest OM phospholipid atom (A)
PERIPLASM = 210.0          # scene: OM inner leaflet to IM outer leaflet (A)
IM_CENTER_Z = OM_BOTTOM_Z - PERIPLASM - 25.0   # bilayer centre (A) -> -199
CUT_Y = 57.0               # scene cross-section plane (A)
ACRB_XY = (125.0, CUT_Y + 10.0)   # scene placement of AcrB (A)
PBP_XY = (50.0, CUT_Y + 15.0)     # scene placement of PBP1b (A)
PBP_CLEAR_R = 14.0         # remove lipids within this xy radius of the PBP TM helix (A)


def parse(line):
    return (float(line[30:38]), float(line[38:46]), float(line[46:54]))


def fmt(line, x, y, z):
    return line[:30] + '%8.3f%8.3f%8.3f' % (x, y, z) + line[54:]


# ---------- MemProtMD system: lipids + AcrB ----------
lip, prot = [], []
with open(SRC_IM) as fh:
    for line in fh:
        if not line.startswith('ATOM'):
            continue
        x, y, z = parse(line)
        is_lipid = line[17:20] == 'DPP'
        # 4DX5 was crystallised with two DARPin binders (chains D, E); MemProtMD
        # renumbers all protein residues consecutively and the DARPins are
        # residues 3111-3418 (AcrB chains A-C end at 3110). Drop them.
        if not is_lipid and int(line[22:26]) >= DARPIN_FIRST_RES:
            continue
        if not is_lipid and z > 145.0:
            # a single wrapped tail atom (Ser1043) sits beyond the cytoplasmic
            # face; unwrapping it put a 3 nm spike on the periplasmic tip, so drop it
            continue
        # rotate 180 deg about x, then translate
        x2, y2, z2 = x, -y, -z
        x2 += ACRB_XY[0] - ACRB_XY_LOCAL[0]
        y2 += ACRB_XY[1] + ACRB_XY_LOCAL[1]
        z2 += IM_CENTER_Z + BILAYER_CENTER_LOCAL
        (lip if is_lipid else prot).append(fmt(line, x2, y2, z2))

# ---------- PBP1b (OPM) ----------
pbp_raw = []
with open(SRC_PBP) as fh:
    for line in fh:
        if line.startswith('ATOM'):
            pbp_raw.append((line, parse(line)))
tm = [(x, y) for _, (x, y, z) in pbp_raw if abs(z) < 15.0]
tmx = sum(p[0] for p in tm) / len(tm)
tmy = sum(p[1] for p in tm) / len(tm)
dx, dy, dz = PBP_XY[0] - tmx, PBP_XY[1] - tmy, IM_CENTER_Z
pbp = [fmt(line, x + dx, y + dy, z + dz) for line, (x, y, z) in pbp_raw]

# ---------- patched lipid sheet for the tiles that carry no AcrB ----------
# The MemProtMD sheet has a hole where AcrB sits. For the neighbouring tiles we
# fill it with a disk of lipids borrowed from the opposite corner of the periodic
# box (which is pure lipid), so AcrB appears only once in the scene.
BOX_XY = (150.575, 159.290)
HOLE_R = 52.0
donor = (ACRB_XY[0] + BOX_XY[0] / 2, ACRB_XY[1] + BOX_XY[1] / 2)
res_lines, res_xy = {}, {}
for line in lip:
    key = line[21:27]
    x, y, z = parse(line)
    res_lines.setdefault(key, []).append(line)
    res_xy.setdefault(key, []).append((x, y))
disk = []
for key, pts in res_xy.items():
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    best = None
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            d = math.hypot(cx + i * BOX_XY[0] - donor[0], cy + j * BOX_XY[1] - donor[1])
            if best is None or d < best[0]:
                best = (d, i, j)
    if best[0] < HOLE_R:
        sx = best[1] * BOX_XY[0] + ACRB_XY[0] - donor[0]
        sy = best[2] * BOX_XY[1] + ACRB_XY[1] - donor[1]
        for line in res_lines[key]:
            x, y, z = parse(line)
            disk.append(fmt(line, x + sx, y + sy, z))
lip_patched = lip + disk
print('patch disk lipids (atoms):', len(disk))

# remove lipids overlapping the PBP transmembrane helix (whole residues)
keep, drop_res = [], set()
for line in lip:
    x, y, z = parse(line)
    if math.hypot(x - PBP_XY[0], y - PBP_XY[1]) < PBP_CLEAR_R:
        drop_res.add(line[21:27])
lip = [l for l in lip if l[21:27] not in drop_res]

box = 'CRYST1  150.575  159.290  183.405  90.00  90.00  90.00 P 1           1\n'
for name, lines in (('im_lipids.pdb', lip), ('im_lipids_patched.pdb', lip_patched),
                    ('im_acrb.pdb', prot), ('im_pbp1b.pdb', pbp)):
    with open(os.path.join(OUT, name), 'w') as fh:
        fh.write(box)
        fh.writelines(lines)
        fh.write('END\n')
    zs = [parse(l)[2] for l in lines]
    print('%-14s %6d atoms  z %.1f .. %.1f A' % (name, len(lines), min(zs), max(zs)))
print('lipid residues removed for PBP1b:', len(drop_res))
