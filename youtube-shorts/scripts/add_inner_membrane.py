"""Layer 3 of gram_negative_base.blend: the inner (cytoplasmic) membrane.
 - DPPC bilayer from MemProtMD with the AcrB efflux pump, tiled along X by its
   own periodic box vector
 - full-length PBP1b (OPM-oriented) embedded in the bilayer
 - cross-section clip on the lipids, camera pulled back to frame the whole
   envelope in the vertical Shorts format
Run: blender -b blend/gram_negative_base.blend --python scripts/add_inner_membrane.py
"""
import bpy, os
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
OUT = os.path.join(BASE, 'render', 'base_scene_im_test.png')
IM = os.path.join(BASE, 'traj', 'inner_membrane')
IM_BOX_X = 15.0575         # MemProtMD 4dx5 box A (nm)

PALETTE = {
    'lipid':        (0.78, 0.78, 0.82, 1.0),   # shared with OM lipids
    'pump_acrb':    (0.55, 0.40, 0.75, 1.0),   # violet
    'target_pbp1b': (0.95, 0.78, 0.25, 1.0),   # gold
}
COMP = {
    'IM_lipids': ('im_lipids.pdb', 'spheres', 'lipid'),
    'IM_AcrB':   ('im_acrb.pdb',   'cartoon', 'pump_acrb'),
    'IM_PBP1b':  ('im_pbp1b.pdb',  'cartoon', 'target_pbp1b'),
}

sc = bpy.context.scene
clip = bpy.data.node_groups['GN_ClipHalfBox']
cut_y = [s.default_value for s in clip.interface.items_tree
         if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y'][0]


def material(name, rgba):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = 0.45
    return mat


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


coll = bpy.data.collections.get('InnerMembrane')
if not coll:
    coll = bpy.data.collections.new('InnerMembrane')
    sc.collection.children.link(coll)

for name, (fn, style, pal) in COMP.items():
    before = set(bpy.data.objects)
    bpy.ops.mn.import_molecule(method='local', filepath=os.path.join(IM, fn),
                               file_format='pdb', style=style)
    obj = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    assign_mn_material(obj, material('MAT_' + pal, PALETTE[pal]))
    zs = [v.co.z for v in obj.data.vertices]
    print('IMPORTED', name, len(zs), 'z %.1f..%.1f' % (min(zs), max(zs)))
    if name == 'IM_lipids':
        cl = obj.modifiers.new('ClipHalfBox', 'NODES')
        cl.node_group = clip
        move_first(obj, cl)
    if name in ('IM_lipids', 'IM_AcrB'):
        ar = obj.modifiers.new('TileBox', 'ARRAY')
        ar.count = 3
        ar.use_relative_offset = False
        ar.use_constant_offset = True
        ar.constant_offset_displace = (IM_BOX_X, 0.0, 0.0)
        move_first(obj, ar)
        obj.location.x -= IM_BOX_X

# ---------- camera: whole envelope, vertical ----------
cam = bpy.data.objects['Cam_CrossSection']
target = Vector((5.8, cut_y, -3.5))
cam.location = target + Vector((0.0, 72.0, 12.0))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
fill = bpy.data.objects.get('Fill')
if fill:
    fill.location = target + Vector((-28.0, 45.0, 20.0))
    fill.rotation_euler = (target - fill.location).to_track_quat('-Z', 'Y').to_euler()
    fill.data.energy = 12000
    fill.data.size = 35

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('RENDER_DONE', OUT)
