"""Test render: TEM-1 beta-lactamase (1XPB) cartoon via Molecular Nodes.
Output: youtube-shorts/render/tem1_test.png
"""
import bpy, math, os, traceback
from mathutils import Vector

OUT = r'E:\Github Project\piranfar.github.io\youtube-shorts\render\tem1_test.png'
PDB_LOCAL = r'E:\Github Project\piranfar.github.io\youtube-shorts\pdb\1XPB.pdb'

os.makedirs(os.path.dirname(OUT), exist_ok=True)

# --- clean scene (avoid read_factory_settings: it reloads addons) ---
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    if c.name != 'Collection':
        bpy.data.collections.remove(c)

before = set(bpy.data.objects)

# --- import molecule: local pdb first, fetch fallback ---
imported = False
try:
    bpy.ops.mn.import_molecule(method='local', filepath=PDB_LOCAL,
                               file_format='pdb', style='cartoon')
    imported = True
    print('IMPORT_LOCAL_OK')
except Exception:
    traceback.print_exc()
    print('IMPORT_LOCAL_FAILED')

if not imported:
    bpy.ops.mn.import_molecule(method='fetch', code='1XPB', style='cartoon')
    print('IMPORT_FETCH_OK')

new_objs = [o for o in bpy.data.objects if o not in before]
print('NEW_OBJECTS:', [(o.name, o.type) for o in new_objs])
mol_obj = next((o for o in new_objs if o.type == 'MESH'), new_objs[0])

# --- override material with bright teal principled (smoke test) ---
mat = bpy.data.materials.new('MOL_TEAL')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.16, 0.55, 0.60, 1.0)
bsdf.inputs['Roughness'].default_value = 0.35
mol_obj.data.materials.clear()
mol_obj.data.materials.append(mat)

# Molecular Nodes assigns its material inside the geometry-nodes style tree,
# so the mesh-level slot above is ignored. Point every Material socket in the
# modifier's node group at our material instead.
mat_sockets = 0
for mod in mol_obj.modifiers:
    if mod.type != 'NODES' or not mod.node_group:
        continue
    for node in mod.node_group.nodes:
        for inp in node.inputs:
            if inp.name == 'Material' and hasattr(inp, 'default_value'):
                inp.default_value = mat
                mat_sockets += 1
                print('MATERIAL_SET_ON:', node.name)
print('MATERIAL_SOCKETS_SET:', mat_sockets)

# --- bounding box / centroid (evaluated, world space) ---
dg = bpy.context.evaluated_depsgraph_get()
ev = mol_obj.evaluated_get(dg)
bb = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
centroid = sum(bb, Vector()) / 8.0
size = max((max(v[i] for v in bb) - min(v[i] for v in bb)) for i in range(3))
print('CENTROID:', tuple(round(x, 2) for x in centroid), 'SIZE:', round(size, 2))

# --- camera ---
dist = size * 2.6
cam_data = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_data)
bpy.context.collection.objects.link(cam)
cam.location = centroid + Vector((dist * 0.85, -dist * 0.85, dist * 0.55))
direction = centroid - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam_data.lens = 50
bpy.context.scene.camera = cam

# --- light: 3-point setup ---
sun_data = bpy.data.lights.new('Sun', type='SUN')
sun_data.energy = 3.5
sun_data.angle = 0.3
sun = bpy.data.objects.new('Sun', sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(35), math.radians(10), math.radians(30))

# fill area from opposite side
fill_data = bpy.data.lights.new('Fill', type='AREA')
fill_data.energy = 800.0
fill_data.size = 5.0
fill = bpy.data.objects.new('Fill', fill_data)
bpy.context.collection.objects.link(fill)
fill.location = centroid + Vector((-dist * 0.7, dist * 0.6, dist * 0.3))
fill_dir = centroid - fill.location
fill.rotation_euler = fill_dir.to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new('World')
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.10, 0.12, 0.17, 1.0)
bg.inputs[1].default_value = 1.6
bpy.context.scene.world = world

# --- render settings ---
scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_WORKBENCH'
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.color_type = 'TEXTURE'
print('ENGINE:', scene.render.engine)
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = OUT
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = 1.2

bpy.ops.render.render(write_still=True)
print('RENDER_DONE:', OUT)
