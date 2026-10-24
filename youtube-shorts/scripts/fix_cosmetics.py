"""Cosmetic pass on gram_negative_base.blend
 1. AcrB appears once: the holed lipid sheet stays in the centre tile, the two
    neighbouring tiles use the patched (hole-filled) sheet; AcrB is re-imported
    from the DARPin-free file and no longer tiled
 2. OmpF: one copy per tile, each rotated about its own axis so the three porins
    do not look stamped
 3. camera raised a little so the peptidoglycan reads as a net, not a line
Run: blender -b blend/gram_negative_base.blend --python scripts/fix_cosmetics.py
"""
import bpy, math, os
from mathutils import Vector, Euler

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
OUT = os.path.join(BASE, 'render', 'base_scene_v2_test.png')
IM = os.path.join(BASE, 'traj', 'inner_membrane')
IM_BOX_X = 15.0575
OM_BOX_X = 11.3615

sc = bpy.context.scene
clip = bpy.data.node_groups['GN_ClipHalfBox']
cut_y = [s.default_value for s in clip.interface.items_tree
         if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y'][0]
objs = bpy.data.objects


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


def untile(obj):
    ar = obj.modifiers.get('TileBox')
    if ar:
        obj.modifiers.remove(ar)
        obj.location.x = 0.0


def centroid(obj):
    vs = [v.co for v in obj.data.vertices]
    return sum(vs, Vector()) / len(vs)


def place_rotated(obj, c0, pos, rot_z):
    R = Euler((0.0, 0.0, rot_z)).to_matrix()
    obj.rotation_euler = (0.0, 0.0, rot_z)
    obj.location = Vector(pos) - R @ c0


# ---------- 1) inner membrane: single AcrB ----------
coll_im = bpy.data.collections['InnerMembrane']
untile(objs['IM_lipids'])                      # holed sheet, centre tile only

old = objs.get('IM_AcrB')
mat_pump = bpy.data.materials['MAT_pump_acrb']
if old:
    bpy.data.objects.remove(old, do_unlink=True)
before = set(bpy.data.objects)
bpy.ops.mn.import_molecule(method='local', filepath=os.path.join(IM, 'im_acrb.pdb'),
                           file_format='pdb', style='cartoon')
acrb = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
acrb.name = 'IM_AcrB'
for c in list(acrb.users_collection):
    c.objects.unlink(acrb)
coll_im.objects.link(acrb)
assign_mn_material(acrb, mat_pump)
zs = [v.co.z for v in acrb.data.vertices]
print('ACRB_REIMPORTED', len(zs), 'height_nm %.1f' % (max(zs) - min(zs)))

if not objs.get('IM_lipids_fill'):
    before = set(bpy.data.objects)
    bpy.ops.mn.import_molecule(method='local', filepath=os.path.join(IM, 'im_lipids_patched.pdb'),
                               file_format='pdb', style='spheres')
    fill = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
    fill.name = 'IM_lipids_fill'
    for c in list(fill.users_collection):
        c.objects.unlink(fill)
    coll_im.objects.link(fill)
    assign_mn_material(fill, bpy.data.materials['MAT_lipid'])
    cl = fill.modifiers.new('ClipHalfBox', 'NODES'); cl.node_group = clip; move_first(fill, cl)
    ar = fill.modifiers.new('TileBox', 'ARRAY')
    ar.count = 2
    ar.use_relative_offset = False
    ar.use_constant_offset = True
    ar.constant_offset_displace = (2 * IM_BOX_X, 0.0, 0.0)   # tiles -1 and +1 only
    move_first(fill, ar)
    fill.location.x = -IM_BOX_X
    print('FILL_ADDED', len(fill.data.vertices))

# ---------- 2) OmpF: three individually rotated copies ----------
ompf = objs['OM_OmpF']
untile(ompf)
c0 = centroid(ompf)
for name in ('OM_OmpF_b', 'OM_OmpF_c'):
    o = objs.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
place_rotated(ompf, c0, c0, math.radians(0))
for name, dx, deg in (('OM_OmpF_b', -OM_BOX_X, 47.0), ('OM_OmpF_c', OM_BOX_X, -38.0)):
    o = ompf.copy()
    o.name = name
    bpy.data.collections['OuterMembrane'].objects.link(o)
    place_rotated(o, c0, c0 + Vector((dx, 0.0, 0.0)), math.radians(deg))
print('OMPF_COPIES', 'rotated 47 / -38 deg')

# ---------- 3) camera ----------
cam = objs['Cam_CrossSection']
target = Vector((5.8, cut_y, -3.5))
cam.location = target + Vector((0.0, 72.0, 20.0))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('RENDER_DONE', OUT)
