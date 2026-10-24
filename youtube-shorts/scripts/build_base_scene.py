"""Build gram_negative_base.blend: the reusable envelope scene.
Layer 1 (this version): equilibrated E. coli outer membrane with OmpF trimer,
shown as a cross-section (a geometry-nodes clip removes the half of the box
nearest the camera, so the porin is visible in profile). Each component is its
own Molecular Nodes object with a fixed material so colours stay consistent
across videos.
Run: blender -b --python scripts/build_base_scene.py
"""
import bpy, math, os
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
TRAJ = os.path.join(BASE, 'traj', 'ompf_lps')
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
OUT = os.path.join(BASE, 'render', 'base_scene_test.png')
TAG = 't5ns'  # equilibrated frame

PALETTE = {               # one palette for the whole series
    'protein_porin': (0.10, 0.55, 0.60, 1.0),   # teal
    'lps':           (0.93, 0.56, 0.18, 1.0),   # orange
    'lipid':         (0.78, 0.78, 0.82, 1.0),   # light grey
}
COMP = {  # object name: (file suffix, MN style, palette key)
    'OM_OmpF':   ('protein', 'cartoon', 'protein_porin'),
    'OM_LPS':    ('lps',     'spheres', 'lps'),
    'OM_lipids': ('lipid',   'spheres', 'lipid'),
}

# ---------- clean ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)

coll_om = bpy.data.collections.new('OuterMembrane')
bpy.context.scene.collection.children.link(coll_om)


def make_material(name, rgba):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = 0.45
    return mat


def assign_mn_material(obj, mat):
    n = 0
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = mat
                        n += 1
    return n


def make_clip_group(name='GN_ClipHalfBox'):
    """Delete points with position.y > Cut Y (exposes the cross-section face)."""
    g = bpy.data.node_groups.get(name)
    if g:
        return g
    g = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    g.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    cut = g.interface.new_socket('Cut Y', in_out='INPUT', socket_type='NodeSocketFloat')
    cut.default_value = 0.0
    g.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n_in = g.nodes.new('NodeGroupInput')
    n_out = g.nodes.new('NodeGroupOutput')
    pos = g.nodes.new('GeometryNodeInputPosition')
    sep = g.nodes.new('ShaderNodeSeparateXYZ')
    cmp = g.nodes.new('FunctionNodeCompare')
    cmp.operation = 'GREATER_THAN'
    dele = g.nodes.new('GeometryNodeDeleteGeometry')
    dele.domain = 'POINT'
    L = g.links
    L.new(pos.outputs['Position'], sep.inputs['Vector'])
    L.new(sep.outputs['Y'], cmp.inputs[0])
    L.new(n_in.outputs['Cut Y'], cmp.inputs[1])
    L.new(n_in.outputs['Geometry'], dele.inputs['Geometry'])
    L.new(cmp.outputs['Result'], dele.inputs['Selection'])
    L.new(dele.outputs['Geometry'], n_out.inputs['Geometry'])
    return g


# ---------- import components ----------
objs = {}
allv = []
for name, (suf, style, pal) in COMP.items():
    before = set(bpy.data.objects)
    bpy.ops.mn.import_molecule(method='local',
                               filepath=os.path.join(TRAJ, 'ompf_lps_%s_%s.pdb' % (TAG, suf)),
                               file_format='pdb', style=style)
    obj = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll_om.objects.link(obj)
    assign_mn_material(obj, make_material('MAT_' + pal, PALETTE[pal]))
    allv += [obj.matrix_world @ v.co for v in obj.data.vertices]
    objs[name] = obj
    print('IMPORTED', name, len(obj.data.vertices))

lo = Vector((min(v.x for v in allv), min(v.y for v in allv), min(v.z for v in allv)))
hi = Vector((max(v.x for v in allv), max(v.y for v in allv), max(v.z for v in allv)))
center = (lo + hi) / 2
ext = hi - lo
print('CENTER', tuple(round(x, 2) for x in center), 'EXTENT', tuple(round(e, 2) for e in ext))

# ---------- cross-section clip (placed before the MN style modifier) ----------
clip = make_clip_group()
# the cut plane is stored on the shared node group (default of its 'Cut Y' input),
# so moving it later in the UI moves it for every clipped layer at once
for s in clip.interface.items_tree:
    if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y':
        s.default_value = float(center.y)
for name, obj in objs.items():
    if name == 'OM_OmpF':
        continue  # keep the porin whole; only the lipid layers are cut
    mod = obj.modifiers.new('ClipHalfBox', 'NODES')
    mod.node_group = clip
    with bpy.context.temp_override(object=obj):
        bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=0)
    print('CLIP_ADDED', name, 'cut_y=', round(center.y, 2))

# ---------- camera: vertical Shorts format, looking at the cut face ----------
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
cam_d = bpy.data.cameras.new('Cam_CrossSection')
cam_d.lens = 50
cam = bpy.data.objects.new('Cam_CrossSection', cam_d)
sc.collection.objects.link(cam)
dist = max(ext.x, ext.z) * 1.6
cam.location = center + Vector((0.0, dist, ext.z * 0.15))   # on the removed side, looking -Y
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam

# ---------- lights / world ----------
key_d = bpy.data.lights.new('Key', type='SUN')
key_d.energy = 3.0
key_d.angle = 0.5
key = bpy.data.objects.new('Key', key_d)
sc.collection.objects.link(key)
key.rotation_euler = (math.radians(55), math.radians(-15), math.radians(160))
fill_d = bpy.data.lights.new('Fill', type='AREA')
fill_d.energy = 1500
fill_d.size = 12
fill = bpy.data.objects.new('Fill', fill_d)
sc.collection.objects.link(fill)
fill.location = center + Vector((-dist * 0.6, dist * 0.8, dist * 0.4))
fill.rotation_euler = (center - fill.location).to_track_quat('-Z', 'Y').to_euler()
world = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.07, 0.08, 0.12, 1.0)
bg.inputs[1].default_value = 0.8
sc.world = world

sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.fps = 30
sc.frame_start, sc.frame_end = 1, 1800   # 60 s timeline scaffold
for f, label in [(1, 'S1 approach'), (150, 'S2 porin'), (400, 'S3 periplasm'), (700, 'S4 target')]:
    sc.timeline_markers.new(label, frame=f)

# ---------- save + test render (half resolution) ----------
os.makedirs(os.path.dirname(BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('RENDER_DONE', OUT)
