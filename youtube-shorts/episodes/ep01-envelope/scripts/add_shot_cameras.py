"""Per-shot cameras for gram_negative_base.blend.
 - Cam_S2_follow: a close camera that tracks the drug and keeps a few nm away,
   sampled from the drug's own path so it glides with it (S2 porin + S3 periplasm)
 - timeline markers bound to cameras: S1 wide establishing shot (Cam_CrossSection),
   S2/S3 follow camera, S4 back to the wide shot
Run: blender -b blend/gram_negative_base.blend --python episodes/ep01-envelope/scripts/add_shot_cameras.py
"""
import bpy, os
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep01-envelope')
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
sc = bpy.context.scene
objs = bpy.data.objects
drug = objs['Drug_ceftazidime']
wide = objs['Cam_CrossSection']

old = objs.get('Cam_S2_follow')
if old:
    bpy.data.objects.remove(old, do_unlink=True)
cam_d = bpy.data.cameras.new('Cam_S2_follow')
cam_d.lens = 60
cam = bpy.data.objects.new('Cam_S2_follow', cam_d)
sc.collection.objects.link(cam)
trk = cam.constraints.new('TRACK_TO')
trk.target = drug
trk.track_axis = 'TRACK_NEGATIVE_Z'
trk.up_axis = 'UP_Y'

# camera offset from the drug (nm): far and high at the start, tight in the pore,
# then easing out again as the drug drifts toward the enzyme
offsets = {
    1:   Vector((2.0, 14.0, 6.0)),
    120: Vector((1.5, 10.0, 3.5)),
    200: Vector((1.0, 7.0, 1.5)),
    260: Vector((0.8, 5.5, 0.6)),    # inside the porin passage
    330: Vector((1.0, 6.5, 0.8)),
    450: Vector((2.5, 9.0, 2.0)),
}
for f, off in offsets.items():
    sc.frame_set(f)
    cam.location = drug.matrix_world.translation + off
    cam.keyframe_insert('location', frame=f)
print('FOLLOW_CAM keyframes', sorted(offsets))

# marker -> camera binding
bind = {'S1 approach': wide, 'S2 porin': cam, 'S3 periplasm': cam, 'S4 target': wide}
for m in sc.timeline_markers:
    if m.name in bind:
        m.camera = bind[m.name]
        print('MARKER', m.name, m.frame, '->', m.camera.name)
sc.camera = wide
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)
