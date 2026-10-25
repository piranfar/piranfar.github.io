"""Prepare the S2 porin-passage preview.
 - cut the porin nearest the path open along the cross-section plane so the
   channel interior (and the drug inside it) is visible from the follow camera
 - loosen the follow camera slightly in the passage
 - set the animation output: frames 180-330, 50 % resolution, H.264 MP4
Run: blender -b blend/gram_negative_base.blend --python episodes/ep01-envelope/scripts/prep_preview_s2.py
then: blender -b blend/gram_negative_base.blend -a
"""
import bpy, os
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep01-envelope')
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
sc = bpy.context.scene
objs = bpy.data.objects
clip = bpy.data.node_groups['GN_ClipHalfBox']

por = objs['OM_OmpF']
if not por.modifiers.get('ClipHalfBox'):
    m = por.modifiers.new('ClipHalfBox', 'NODES')
    m.node_group = clip
    with bpy.context.temp_override(object=por):
        bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)
    print('PORIN_CLIPPED')

cam = objs['Cam_S2_follow']
drug = objs['Drug_ceftazidime']
for f, off in {260: Vector((0.8, 7.0, 0.8)), 330: Vector((1.0, 7.5, 1.0))}.items():
    sc.frame_set(f)
    cam.location = drug.matrix_world.translation + off
    cam.keyframe_insert('location', frame=f)
print('CAM_ADJUSTED')

sc.frame_start, sc.frame_end = 180, 330
sc.render.resolution_percentage = 50
# Blender 5 moved video output behind image_settings.media_type
try:
    sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    sc.render.filepath = os.path.join(EP, 'renders', 'preview_S2_porin.mp4')
    print('OUTPUT video')
except Exception as e:   # fall back to a PNG sequence
    sc.render.image_settings.media_type = 'IMAGE'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = os.path.join(EP, 'renders', 'preview_S2', 'f_')
    print('OUTPUT png sequence (video setup failed: %s)' % e)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)
