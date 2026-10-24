"""Film 1 opening: component tour on the static wide camera.
 - drug objects hidden (nothing enters yet)
 - 3 s establishing, then each envelope component glows for 3 s in turn so a
   caption can name it in the edit: outer membrane (LPS + phospholipids),
   porin, peptidoglycan, beta-lactamase, inner membrane, PBP, efflux pump
 - nothing is saved to the .blend except the IM lipid material split
Usage: blender -b blend/gram_negative_base.blend --python scripts/render_intro_tour.py -- [PCT]
"""
import bpy, os, sys

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
pct = int(args[0]) if args else 50
FPS = 30
HOLD = int(float(args[1]) * FPS) if len(args) > 1 else 5 * FPS   # seconds per component
LEAD = int(float(args[2]) * FPS) if len(args) > 2 else 3 * FPS   # establishing shot

sc = bpy.context.scene
objs = bpy.data.objects
mats = bpy.data.materials
clip = bpy.data.node_groups['GN_ClipHalfBox']


def assign_mn_material(obj, mat):
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group and mod.node_group is not clip:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = mat


# ---------- one-time: give the inner membrane its own lipid material ----------
if 'MAT_lipid_IM' not in mats:
    m = mats['MAT_lipid'].copy()
    m.name = 'MAT_lipid_IM'
    for n in ('IM_lipids', 'IM_lipids_fill'):
        if objs.get(n):
            assign_mn_material(objs[n], m)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print('SAVED material split')

# ---------- hide the drug for the tour ----------
for o in objs:
    if o.name.startswith('Drug_') or o.name.startswith('Path_drug'):
        o.hide_render = True

# ---------- sequential glow pulses ----------
TOUR = [  # (caption key, materials, glow strength)
    # pale, dense materials (spheres, tubes) blow out quickly; keep them low
    ('outer_membrane', ['MAT_lps', 'MAT_lipid'], 0.35),
    ('porin_OmpF', ['MAT_protein_porin'], 1.2),
    ('peptidoglycan', ['MAT_pg_glycan', 'MAT_pg_peptide'], 0.4),
    ('beta_lactamase_TEM1', ['MAT_enzyme_tem1'], 1.3),
    ('inner_membrane', ['MAT_lipid_IM'], 0.3),
    ('PBP1b_target', ['MAT_target_pbp1b'], 1.2),
    ('efflux_pump_AcrB', ['MAT_pump_acrb'], 0.7),
]


def pulse(mat, f0, f1, strength):
    tree = mat.node_tree
    b = tree.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = b.inputs['Base Color'].default_value
    e = b.inputs['Emission Strength']
    for f, v in ((f0, 0.0), (f0 + 12, strength), (f1 - 12, strength), (f1, 0.0)):
        e.default_value = v
        e.keyframe_insert('default_value', frame=f)


timing = []
f = LEAD + 1
for key, mnames, strength in TOUR:
    for mn in mnames:
        pulse(mats[mn], f, f + HOLD, strength)
    timing.append((key, f, f + HOLD))
    f += HOLD
end = f
for key, a, b in timing:
    print('CAPTION %-22s frames %4d-%4d   %5.1f-%5.1f s' % (key, a, b, a / FPS, b / FPS))

sc.frame_start, sc.frame_end = 1, end
for m in sc.timeline_markers:
    m.camera = None
sc.camera = objs['Cam_CrossSection']
sc.render.resolution_percentage = pct
sc.render.image_settings.media_type = 'VIDEO'
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'
sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'
sc.render.filepath = os.path.join(BASE, 'render', 'film1_intro_tour.mp4')
bpy.ops.render.render(animation=True)
print('RENDER_DONE', sc.render.filepath, 'frames', end)
