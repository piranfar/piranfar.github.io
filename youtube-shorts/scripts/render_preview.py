"""Render a frame range of the base scene to an H.264 preview.
Usage: blender -b blend/gram_negative_base.blend --python scripts/render_preview.py -- START END NAME [PERCENT] [CAMERA]
With CAMERA given, the marker-bound camera switching is disabled for this render
(not saved) and that camera is used for the whole range.
"""
import bpy, os, sys

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
args = sys.argv[sys.argv.index('--') + 1:]
start, end, name = int(args[0]), int(args[1]), args[2]
pct = int(args[3]) if len(args) > 3 else 50
camera = args[4] if len(args) > 4 else None
sc = bpy.context.scene
if camera:
    for m in sc.timeline_markers:
        m.camera = None
    sc.camera = bpy.data.objects[camera]
sc.frame_start, sc.frame_end = start, end
sc.render.resolution_percentage = pct
sc.render.image_settings.media_type = 'VIDEO'
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'
sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'
sc.render.filepath = os.path.join(BASE, 'render', name + '.mp4')
bpy.ops.render.render(animation=True)
print('RENDER_DONE', sc.render.filepath, 'camera', sc.camera.name)
