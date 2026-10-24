import importlib, inspect, bpy

m = importlib.import_module('bl_ext.user_default.molecularnodes')
Mol = m.entities.Molecule
print('MOLECULE_CLASS:', Mol)
print('MOLECULE_METHODS:', [n for n in dir(Mol) if not n.startswith('_')])

op = bpy.ops.mn.import_molecule
try:
    rna = op.get_rna_type()
    props = [(p.identifier, getattr(p, 'default', None)) for p in rna.properties]
    print('IMPORT_MOLECULE_PROPS:', props)
except Exception as e:
    print('OP_RNA_FAIL:', e)

tr = bpy.ops.mn.reload_trajectory
strm = m.entities.StreamingTrajectory
print('TRAJ_METHODS:', [n for n in dir(strm) if not n.startswith('_')])
