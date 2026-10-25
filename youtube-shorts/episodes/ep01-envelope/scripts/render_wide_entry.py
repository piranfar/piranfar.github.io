"""Wide establishing clip: whole envelope in frame, static cross-section camera,
the antibiotic approaches from outside, crosses the LPS, passes the porin and
reaches the periplasm / enzyme. Nothing is saved to the .blend.
Usage: blender -b blend/gram_negative_base.blend --python episodes/ep01-envelope/scripts/render_wide_entry.py -- [START END PCT]
"""
import bpy, os, sys

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep01-envelope')
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
start = int(args[0]) if len(args) > 0 else 1
end = int(args[1]) if len(args) > 1 else 480
pct = int(args[2]) if len(args) > 2 else 50
sc = bpy.context.scene
for m in sc.timeline_markers:
    m.camera = None
sc.camera = bpy.data.objects['Cam_CrossSection']

# make the 1.5 nm molecule readable at 70 nm: strong constant glow for this render
for name, strength in (('MAT_drug_travel', 6.0), ('MAT_drug_docked', 4.0), ('MAT_drug_product', 2.0)):
    mat = bpy.data.materials[name]
    b = mat.node_tree.nodes['Principled BSDF']
    e = b.inputs['Emission Strength']
    # drop only the emission keyframes, keep the alpha fades
    ad = mat.node_tree.animation_data
    if ad and ad.action:
        try:
            for fc in list(ad.action.fcurves):
                if 'Emission Strength' in fc.data_path:
                    ad.action.fcurves.remove(fc)
        except AttributeError:   # Blender 5 slotted actions
            for layer in ad.action.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        for fc in list(cb.fcurves):
                            if 'Emission Strength' in fc.data_path:
                                cb.fcurves.remove(fc)
    e.default_value = strength
sc.frame_start, sc.frame_end = start, end
sc.render.resolution_percentage = pct
sc.render.image_settings.media_type = 'VIDEO'
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'
sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'
sc.render.filepath = os.path.join(EP, 'renders', 'wide_entry_%d_%d.mp4' % (start, end))
bpy.ops.render.render(animation=True)
print('RENDER_DONE', sc.render.filepath)
