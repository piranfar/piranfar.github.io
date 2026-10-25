"""Still check: the transferred acyl ligand sitting in PBP1b's active site.
Run: blender -b blend/gram_negative_base.blend --python episodes/ep02-hit-the-wall/scripts/check_pbp_pose.py
"""
import bpy, os
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep02-hit-the-wall')
sc = bpy.context.scene
objs = bpy.data.objects
for o in objs:
    if o.name.startswith('Drug_') or o.name.startswith('Path_drug'):
        o.hide_render = True
mat = bpy.data.materials.new('MAT_acyl'); mat.use_nodes = True
b = mat.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (1.0, 0.35, 0.2, 1.0)
b.inputs['Emission Color'].default_value = (1.0, 0.4, 0.2, 1.0)
b.inputs['Emission Strength'].default_value = 2.0
before = set(objs)
bpy.ops.mn.import_molecule(method='local', filepath=os.path.join(BASE, 'pdb', 'ligands', 'cefotaxime_acyl_in_pbp1b.pdb'),
                           file_format='pdb', style='ball_and_stick')
lig = next(o for o in objs if o not in before and o.type == 'MESH')
for mod in lig.modifiers:
    if mod.type == 'NODES' and mod.node_group:
        for node in mod.node_group.nodes:
            for inp in node.inputs:
                if inp.name == 'Material' and hasattr(inp, 'default_value'):
                    inp.default_value = mat
site = Vector((36.75, 58.48, -108.99)) * 0.1
cam = objs['Cam_CrossSection']
for c in list(cam.constraints):
    cam.constraints.remove(c)
if cam.animation_data:
    cam.animation_data_clear()
cam.data.dof.use_dof = False
for name, dist, out in (('wide', 16.0, 'check_pbp_pose_wide.png'), ('close', 7.0, 'check_pbp_pose_close.png')):
    cam.location = site + Vector((1.0, dist, 1.5))
    cam.rotation_euler = (site - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for m in sc.timeline_markers:
        m.camera = None
    sc.camera = cam
    sc.render.resolution_percentage = 50
    sc.render.image_settings.media_type = 'IMAGE'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = os.path.join(EP, 'renders', out)
    bpy.ops.render.render(write_still=True)
    print('STILL', out)
