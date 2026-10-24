"""Convert an RCSB ideal-coordinate ligand SDF (V2000) to a PDB with CONECT
records, so Molecular Nodes can draw it ball-and-stick with correct bonds.
Usage: python -I sdf_to_pdb.py in.sdf out.pdb RESNAME
"""
import sys

src, dst, resname = sys.argv[1], sys.argv[2], sys.argv[3][:3].upper()
lines = open(src).read().splitlines()
counts = lines[3]
n_atoms, n_bonds = int(counts[0:3]), int(counts[3:6])
atoms = []
for i in range(4, 4 + n_atoms):
    p = lines[i].split()
    atoms.append((float(p[0]), float(p[1]), float(p[2]), p[3]))
bonds = []
for i in range(4 + n_atoms, 4 + n_atoms + n_bonds):
    l = lines[i]
    bonds.append((int(l[0:3]), int(l[3:6])))

elem_count = {}
out = []
for idx, (x, y, z, el) in enumerate(atoms, 1):
    elem_count[el] = elem_count.get(el, 0) + 1
    name = (el + str(elem_count[el]))[:4]
    out.append('HETATM%5d %-4s %3s A   1    %8.3f%8.3f%8.3f  1.00  0.00          %2s'
               % (idx, name, resname, x, y, z, el.rjust(2)))
adj = {}
for a, b in bonds:
    adj.setdefault(a, []).append(b)
    adj.setdefault(b, []).append(a)
for a in sorted(adj):
    for chunk in range(0, len(adj[a]), 4):
        out.append('CONECT%5d' % a + ''.join('%5d' % b for b in adj[a][chunk:chunk + 4]))
out.append('END')
open(dst, 'w').write('\n'.join(out) + '\n')
print('%s: %d atoms, %d bonds -> %s' % (resname, n_atoms, n_bonds, dst))
