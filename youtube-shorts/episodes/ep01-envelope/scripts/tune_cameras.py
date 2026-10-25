"""Camera pass after reviewing the first previews.
 S3 (enzyme): start wider so the enzyme is seen in context under the membrane,
   then a slow 65-degree orbit around the active site with a push-in during
   docking and a pull-out during release. Shorter cross-fades (less ghosting).
 S2 (porin): follow camera pulled back ~35 % and swung in a gentle arc around
   the drug instead of trailing it from one side.
Run: blender -b blend/gram_negative_base.blend --python episodes/ep01-envelope/scripts/tune_cameras.py
"""
import bpy, math, os
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep01-envelope')
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
sc = bpy.context.scene
objs = bpy.data.objects
drug = objs['Drug_ceftazidime']
tem = objs['PP_TEM1_a']
tgt = objs['Target_TEM1_site']
site_w = tgt.matrix_world.translation.copy()


def clear_anim(idblock):
    if idblock.animation_data:
        idblock.animation_data_clear()


# ---------- S3: orbit around the active site ----------
cam3 = objs['Cam_S3_enzyme']
clear_anim(cam3)
cam3.data.lens = 55
# (frame, radius nm, angle deg in the xy plane, height above site nm)
# angle 162 deg = the direction the pocket opens toward; sweep 185 -> 120
orbit = [(400, 13.0, 185.0, 2.4), (470, 10.0, 172.0, 2.0), (520, 8.0, 160.0, 1.6),
         (600, 8.0, 145.0, 1.6), (680, 9.5, 130.0, 2.2), (740, 12.0, 120.0, 2.8)]
for f, r, a, h in orbit:
    t = math.radians(a)
    cam3.location = site_w + Vector((r * math.cos(t), r * math.sin(t), h))
    cam3.keyframe_insert('location', frame=f)
print('CAM3 orbit', [(f, round(r, 1), a) for f, r, a, h in orbit])

# ---------- S2: wider arc around the drug ----------
cam2 = objs['Cam_S2_follow']
clear_anim(cam2)
cam2.data.lens = 55
arc = {1: (4.0, 18.0, 7.0), 120: (3.5, 13.5, 4.5), 200: (0.5, 9.5, 2.0), 260: (-1.5, 8.5, 0.8),
       330: (-3.0, 9.0, 1.0), 450: (-4.5, 11.0, 2.0)}
for f, off in arc.items():
    sc.frame_set(f)
    cam2.location = drug.matrix_world.translation + Vector(off)
    cam2.keyframe_insert('location', frame=f)
print('CAM2 arc', sorted(arc))

# ---------- shorter cross-fades ----------
def fade(mat, keys):
    a = mat.node_tree.nodes['Principled BSDF'].inputs['Alpha']
    clear_anim(mat.node_tree)
    for f, v in sorted(keys.items()):
        a.default_value = v
        a.keyframe_insert('default_value', frame=f)

mats = bpy.data.materials
fade(mats['MAT_drug_travel'], {1: 1.0, 470: 1.0, 484: 0.0})
fade(mats['MAT_drug_docked'], {1: 0.0, 470: 0.0, 484: 1.0, 548: 1.0, 562: 0.0})
fade(mats['MAT_drug_product'], {1: 0.0, 548: 0.0, 562: 1.0, 700: 1.0, 730: 0.0})
print('FADES shortened')

sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)
