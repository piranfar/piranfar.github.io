"""Test render: OmpF trimer in an E. coli LPS outer membrane (CHARMM-GUI build)
via Molecular Nodes, space-filling spheres. Output: render/ompf_membrane_test.png
"""
import bpy, math, os, traceback
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
PDB = os.path.join(BASE, 'pdb', 'charmm-gui', 'ompf_lps_membrane.pdb')
OUT = os.path.join(BASE, 'render', 'ompf_membrane_test.png')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

before = set(bpy.data.objects)
bpy.ops.mn.import_molecule(method='local', filepath=PDB, file_format='pdb', style='spheres')
new_objs = [o for o in bpy.data.objects if o not in before]
print('NEW_OBJECTS:', [(o.name, o.type) for o in new_objs])
mol = next(o for o in new_objs if o.type == 'MESH')

# bounding box from the raw atom positions (the spheres style is instanced,
# so the evaluated bound_box can come back empty in background mode)
xs = [mol.matrix_world @ v.co for v in mol.data.vertices]
lo = Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs)))
hi = Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
centroid = (lo + hi) / 2.0
ext = [hi[i] - lo[i] for i in range(3)]
print('NVERTS:', len(xs))
print('CENTROID:', tuple(round(x, 2) for x in centroid), 'EXTENT:', [round(e, 2) for e in ext])

# camera: oblique side view so both the LPS brush and the porin are visible
dist = max(ext) * 1.9
cam_data = bpy.data.cameras.new('Cam'); cam_data.lens = 45
cam = bpy.data.objects.new('Cam', cam_data); bpy.context.collection.objects.link(cam)
cam.location = centroid + Vector((dist * 0.75, -dist * 0.75, dist * 0.45))
cam.rotation_euler = (centroid - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

sun_d = bpy.data.lights.new('Sun', type='SUN'); sun_d.energy = 3.0; sun_d.angle = 0.4
sun = bpy.data.objects.new('Sun', sun_d); bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(35))
world = bpy.data.worlds.new('World'); world.use_nodes = True
bgn = world.node_tree.nodes['Background']
bgn.inputs[0].default_value = (0.10, 0.12, 0.17, 1.0); bgn.inputs[1].default_value = 1.0
bpy.context.scene.world = world

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = OUT
sc.view_settings.view_transform = 'Standard'
bpy.ops.render.render(write_still=True)
print('RENDER_DONE:', OUT)
