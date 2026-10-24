"""Re-import the three TEM-1 trajectory objects from the MDAnalysis-written
topology (traj/tem1/tem1_top.pdb + tem1_protein.xtc). The GROMACS-written
topology had no chain ID and Molecular Nodes produced no secondary structure
for it, so the cartoon style rendered nothing. Transforms, playback settings
and children (ligands, camera target) are carried over.
Run: blender -b blend/gram_negative_base.blend --python scripts/fix_tem1_traj.py
"""
import bpy, os
from mathutils import Matrix

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
TOP = os.path.join(BASE, 'traj', 'tem1', 'tem1_top.pdb')
XTC = os.path.join(BASE, 'traj', 'tem1', 'tem1_protein.xtc')
sc = bpy.context.scene
objs = bpy.data.objects
clip = bpy.data.node_groups['GN_ClipHalfBox']
coll = bpy.data.collections['Periplasm']
mat = bpy.data.materials['MAT_enzyme_tem1']


def assign_mn_material(obj, mat):
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group and mod.node_group is not clip:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = mat


for name in ('PP_TEM1_a', 'PP_TEM1_b', 'PP_TEM1_c'):
    old = objs[name]
    loc, rot = old.location.copy(), old.rotation_euler.copy()
    sub, off = old.mn.subframes, old.mn.offset
    children = [(c, c.matrix_local.copy()) for c in objs if c.parent is old]
    bpy.data.objects.remove(old, do_unlink=True)
    before = set(objs)
    bpy.ops.mn.import_molecule(method='local', filepath=TOP, trajectory=XTC, file_format='pdb', style='cartoon')
    new = next(o for o in objs if o not in before and o.type == 'MESH')
    new.name = name
    for c in list(new.users_collection):
        c.objects.unlink(new)
    coll.objects.link(new)
    assign_mn_material(new, mat)
    new.mn.subframes, new.mn.offset = sub, off
    new.mn.interpolate = True
    new.mn.update_with_scene = True
    new.location, new.rotation_euler = loc, rot
    # the trajectory importer leaves out 'sec_struct' for this topology, so borrow
    # it from a static import of the same file (identical atom order)
    if 'sec_struct' not in [a.name for a in new.data.attributes]:
        before = set(objs)
        bpy.ops.mn.import_molecule(method='local', filepath=TOP, file_format='pdb', style='cartoon')
        tmp = next(o for o in objs if o not in before and o.type == 'MESH')
        src = tmp.data.attributes.get('sec_struct')
        if src and len(src.data) == len(new.data.vertices):
            dst = new.data.attributes.new('sec_struct', src.data_type, 'POINT')
            vals = [d.value for d in src.data]
            dst.data.foreach_set('value', vals)
            print('   sec_struct copied from static import:', sorted(set(vals)))
        else:
            print('   WARNING: could not copy sec_struct', src and len(src.data), len(new.data.vertices))
        bpy.data.objects.remove(tmp, do_unlink=True)
    for c, ml in children:
        c.parent = new
        c.matrix_parent_inverse = Matrix.Identity(4)
        c.matrix_local = ml
    sc.frame_set(500)
    dg = bpy.context.evaluated_depsgraph_get()
    me = new.evaluated_get(dg).to_mesh()
    print('REIMPORTED', name, 'eval verts @500:', len(me.vertices), 'children:', [c.name for c, _ in children],
          'sec_struct:', 'sec_struct' in [a.name for a in new.data.attributes])
    new.evaluated_get(dg).to_mesh_clear()

sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)
