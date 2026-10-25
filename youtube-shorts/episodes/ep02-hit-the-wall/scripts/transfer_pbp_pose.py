"""Acyl-enzyme pose for episode 2.
Superposes S. pneumoniae PBP1a (2C5W chain B, cefotaxime covalently bound to
Ser370) onto E. coli PBP1b (3VMA, OPM-oriented) using the three conserved
transpeptidase motifs (SxxK, SxN, KTG) and writes the ligand in SCENE
coordinates (the frame of traj/inner_membrane/im_pbp1b.pdb):
  pdb/ligands/cefotaxime_acyl_in_pbp1b.pdb    the bound, ring-opened form
  pdb/ligands/ceftazidime_docked_in_pbp1b.pdb  intact ceftazidime placed on the same site
Prints the active-site centre and a pocket entrance point for the shot script.
Run: python episodes/ep02-hit-the-wall/scripts/transfer_pbp_pose.py
"""
import numpy as np, os

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
REF = os.path.join(BASE, 'pdb', 'opm', '3vma_opm.pdb')          # PBP1b, OPM frame
MOB = os.path.join(BASE, 'pdb', '2C5W.pdb')                      # PBP1a + CEF
SCENE_PBP = os.path.join(BASE, 'traj', 'inner_membrane', 'im_pbp1b.pdb')
CAZ = os.path.join(BASE, 'pdb', 'ligands', 'ceftazidime_CAZ.pdb')
OUT = os.path.join(BASE, 'pdb', 'ligands')
MOTIFS = {  # (ref residues, mobile residues) with +/-1 neighbours
    'SxxK': ([510, 511, 512, 513], [370, 371, 372, 373]),
    'SxN': ([572, 573, 574], [428, 429, 430]),
    'KTG': ([698, 699, 700], [557, 558, 559]),
}


def atoms(path, chain, names=('CA', 'CB')):
    out = {}
    for l in open(path):
        if l.startswith('ATOM') and l[21] == chain and l[12:16].strip() in names:
            out[(int(l[22:26]), l[12:16].strip())] = np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])])
    return out


ref, mob = atoms(REF, 'A'), atoms(MOB, 'B')
P, Q = [], []
for rr, mr in MOTIFS.values():
    for a, b in zip(rr, mr):
        for n in ('CA', 'CB'):
            if (a, n) in ref and (b, n) in mob:
                P.append(ref[(a, n)]); Q.append(mob[(b, n)])
P, Q = np.array(P), np.array(Q)
Pc, Qc = P.mean(0), Q.mean(0)
H = (Q - Qc).T @ (P - Pc)
U, S, Vt = np.linalg.svd(H)
d = np.sign(np.linalg.det(Vt.T @ U.T))
R = Vt.T @ np.diag([1, 1, d]) @ U.T
rmsd = np.sqrt(((((Q - Qc) @ R.T) + Pc - P) ** 2).sum(1).mean())
print('motif atoms %d, RMSD %.2f A' % (len(P), rmsd))

# scene frame = OPM frame + translation (prep_inner_membrane.py only translated PBP1b)
first_opm = next(np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])]) for l in open(REF) if l.startswith('ATOM'))
first_scene = next(np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])]) for l in open(SCENE_PBP) if l.startswith('ATOM'))
T = first_scene - first_opm
print('OPM -> scene translation (A):', np.round(T, 2))


def xf(v):
    return (R @ (v - Qc)) + Pc + T


def fmt(line, v):
    return line[:30] + '%8.3f%8.3f%8.3f' % tuple(v) + line[54:]


lig = [l for l in open(MOB) if l.startswith('HETATM') and l[17:20] == 'CEF' and l[21] == 'B']
out = [fmt(l, xf(np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])]))) for l in lig]
with open(os.path.join(OUT, 'cefotaxime_acyl_in_pbp1b.pdb'), 'w') as fh:
    fh.writelines(out); fh.write('END\n')
lp = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in out])
site = lp.mean(0)
ser = ref[(510, 'CB')] + T
print('acyl ligand %d atoms; centre (scene A) %s; distance to Ser510 CB %.1f A' % (len(out), np.round(site, 2), np.linalg.norm(site - ser)))

# intact ceftazidime on the same site: centroid + principal axes onto the bound ligand
caz = [l for l in open(CAZ) if l.startswith(('ATOM', 'HETATM'))]
cz = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in caz])


def axes(X):
    u, s, vt = np.linalg.svd(X - X.mean(0), full_matrices=False)
    A = vt
    if np.linalg.det(A) < 0:
        A[2] *= -1
    return A


A_b, A_c = axes(lp), axes(cz)
cz2 = (cz - cz.mean(0)) @ A_c.T @ A_b + site
with open(os.path.join(OUT, 'ceftazidime_docked_in_pbp1b.pdb'), 'w') as fh:
    fh.writelines(fmt(l, v) for l, v in zip(caz, cz2))
    fh.writelines(l for l in open(CAZ) if l.startswith('CONECT'))
    fh.write('END\n')

# pocket entrance: 10 A from the site, away from the protein centre
prot = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in open(SCENE_PBP) if l.startswith('ATOM')])
v = site - prot.mean(0); v /= np.linalg.norm(v)
print('SITE (scene A):', np.round(site, 2), ' ENTRANCE:', np.round(site + 10 * v, 2))
