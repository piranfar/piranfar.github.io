"""Before/after render of the OmpF + E. coli LPS outer membrane:
frame 0 (as built by CHARMM-GUI) vs 5 ns of MD. Each component is a separate
Molecular Nodes object so it gets its own colour.
Usage: blender -b --python scripts/render_membrane_compare.py -- t0|t5ns
"""
import bpy, sys, math, os
from mathutils import Vector

TAG = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 't0'
BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep01-envelope')
TRAJ = os.path.join(BASE, 'traj', 'ompf_lps')
OUT = os.path.join(EP, 'renders', f'ompf_lps_{TAG}.png')

COMP = {  # name: (file suffix, style, rgba)
    'protein': ('protein', 'cartoon', (0.10, 0.55, 0.60, 1.0)),   # teal
    'lps':     ('lps',     'spheres', (0.95, 0.55, 0.15, 1.0)),   # orange sugars + lipid A
    'lipid':   ('lipid',   'spheres', (0.75, 0.75, 0.78, 1.0)),   # grey phospholipids
}

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def set_material(obj, name, rgba):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = 0.45
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = mat

allv = []
for name, (suf, style, rgba) in COMP.items():
    before = set(bpy.data.objects)
    bpy.ops.mn.import_molecule(method='local', filepath=os.path.join(TRAJ, f'ompf_lps_{TAG}_{suf}.pdb'),
                               file_format='pdb', style=style)
    obj = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
    obj.name = name
    set_material(obj, f'MAT_{name}', rgba)
    allv += [obj.matrix_world @ v.co for v in obj.data.vertices]
    print('IMPORTED', name, len(obj.data.vertices))

lo = Vector((min(v.x for v in allv), min(v.y for v in allv), min(v.z for v in allv)))
hi = Vector((max(v.x for v in allv), max(v.y for v in allv), max(v.z for v in allv)))
c = (lo + hi) / 2; ext = hi - lo
print('EXTENT', [round(e, 2) for e in ext])

# side view, slightly elevated, looking along +Y so membrane normal (Z) is vertical in frame
cam_d = bpy.data.cameras.new('Cam'); cam_d.lens = 50
cam = bpy.data.objects.new('Cam', cam_d); bpy.context.collection.objects.link(cam)
dist = max(ext.x, ext.z) * 2.2
cam.location = c + Vector((0.0, -dist, ext.z * 0.25))
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

sun_d = bpy.data.lights.new('Sun', type='SUN'); sun_d.energy = 3.0; sun_d.angle = 0.5
sun = bpy.data.objects.new('Sun', sun_d); bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
world = bpy.data.worlds.new('World'); world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.08, 0.09, 0.13, 1.0); bg.inputs[1].default_value = 0.8
bpy.context.scene.world = world

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = OUT
sc.view_settings.view_transform = 'Standard'
bpy.ops.render.render(write_still=True)
print('RENDER_DONE', OUT)
