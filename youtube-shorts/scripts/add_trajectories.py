"""Wire the MD trajectories to the timeline.
 - outer membrane: the three static component objects are replaced by Molecular
   Nodes trajectory objects (protein / LPS / lipids, 251 frames, 20 ps apart)
   stretched over the 60 s timeline with interpolation
 - TEM-1: the three static copies are replaced by trajectory objects (1001
   frames, 10 ps apart) with different frame offsets so they do not move in sync
 - clip and tiling modifiers are re-applied exactly as before
 - renders two stills from the follow camera to check motion
Run: blender -b blend/gram_negative_base.blend --python scripts/add_trajectories.py
"""
import bpy, math, os
from mathutils import Vector, Euler

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
TR = os.path.join(BASE, 'traj')
PREVIEW = os.path.join(BASE, 'render', 'traj_check_f%03d.png')
OM_BOX_X = 11.3615
OM_SUBFRAMES = 6      # 251 MD frames x 7 = 1757 timeline frames (~60 s)
TEM_SUBFRAMES = 1     # 1001 MD frames x 2 = 2002 timeline frames

sc = bpy.context.scene
objs = bpy.data.objects
clip = bpy.data.node_groups['GN_ClipHalfBox']


def assign_mn_material(obj, mat):
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group and mod.node_group is not clip:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = mat


def move_first(obj, mod):
    with bpy.context.temp_override(object=obj):
        bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=0)


def import_traj(top, xtc, style, name, coll):
    before = set(bpy.data.objects)
    bpy.ops.mn.import_molecule(method='local', filepath=top, trajectory=xtc,
                               file_format='pdb', style=style)
    obj = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


def set_playback(obj, subframes, offset=0):
    obj.mn.subframes = subframes
    obj.mn.offset = offset
    obj.mn.interpolate = True
    obj.mn.update_with_scene = True


def add_clip(obj):
    m = obj.modifiers.new('ClipHalfBox', 'NODES')
    m.node_group = clip
    move_first(obj, m)


def add_tile(obj):
    ar = obj.modifiers.new('TileBox', 'ARRAY')
    ar.count = 3
    ar.use_relative_offset = False
    ar.use_constant_offset = True
    ar.constant_offset_displace = (OM_BOX_X, 0.0, 0.0)
    move_first(obj, ar)
    obj.location.x -= OM_BOX_X


# ---------- remember transforms of the objects we replace ----------
tem_xf = {n: (objs[n].location.copy(), objs[n].rotation_euler.copy())
          for n in ('PP_TEM1_a', 'PP_TEM1_b', 'PP_TEM1_c') if objs.get(n)}
ompf_xf = {n: (objs[n].location.copy(), objs[n].rotation_euler.copy())
           for n in ('OM_OmpF', 'OM_OmpF_b', 'OM_OmpF_c') if objs.get(n)}
for n in list(tem_xf) + list(ompf_xf) + ['OM_LPS', 'OM_lipids']:
    if objs.get(n):
        bpy.data.objects.remove(objs[n], do_unlink=True)

coll_om = bpy.data.collections['OuterMembrane']
coll_pp = bpy.data.collections['Periplasm']
mats = bpy.data.materials

# ---------- outer membrane ----------
om = os.path.join(TR, 'ompf_lps')
lps = import_traj(os.path.join(om, 'ompf_lps_lps_top.pdb'), os.path.join(om, 'ompf_lps_lps.xtc'),
                  'spheres', 'OM_LPS', coll_om)
assign_mn_material(lps, mats['MAT_lps']); add_clip(lps); add_tile(lps); set_playback(lps, OM_SUBFRAMES)
lip = import_traj(os.path.join(om, 'ompf_lps_lipid_top.pdb'), os.path.join(om, 'ompf_lps_lipid.xtc'),
                  'spheres', 'OM_lipids', coll_om)
assign_mn_material(lip, mats['MAT_lipid']); add_clip(lip); add_tile(lip); set_playback(lip, OM_SUBFRAMES)
por = import_traj(os.path.join(om, 'ompf_lps_protein_top.pdb'), os.path.join(om, 'ompf_lps_protein.xtc'),
                  'cartoon', 'OM_OmpF', coll_om)
assign_mn_material(por, mats['MAT_protein_porin']); set_playback(por, OM_SUBFRAMES)
por.location, por.rotation_euler = ompf_xf['OM_OmpF']
for n in ('OM_OmpF_b', 'OM_OmpF_c'):
    o = por.copy()             # shares the animated mesh, own transform
    o.name = n
    coll_om.objects.link(o)
    o.location, o.rotation_euler = ompf_xf[n]
print('OM_TRAJ frames', por.mn.n_frames if hasattr(por.mn, 'n_frames') else '?')

# ---------- TEM-1 ----------
t1 = os.path.join(TR, 'tem1')
for i, n in enumerate(('PP_TEM1_a', 'PP_TEM1_b', 'PP_TEM1_c')):
    o = import_traj(os.path.join(t1, 'tem1_t10ns.pdb'), os.path.join(t1, 'tem1_nowater.xtc'),
                    'cartoon', n, coll_pp)
    assign_mn_material(o, mats['MAT_enzyme_tem1'])
    set_playback(o, TEM_SUBFRAMES, offset=-300 * i)
    o.location, o.rotation_euler = tem_xf[n]
print('TEM1_TRAJ 3 copies')

sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)

# ---------- motion check from the follow camera ----------
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = 'PNG'
for f in (200, 280):
    sc.frame_set(f)
    sc.render.filepath = PREVIEW % f
    bpy.ops.render.render(write_still=True)
    print('RENDERED', f, 'camera', sc.camera.name)
