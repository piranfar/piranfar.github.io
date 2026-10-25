"""Film 1 v2, pass 1 (visual pointing instead of text):
 - no 3D labels in the render; instead each anchor's screen position is exported
   per frame (render/<out>_anchors.json) and the pointing (ring, drawn leader,
   one-word label) is added in 2D afterwards by overlay_hud.py, so text can
   never sit behind geometry
 - while a component is introduced, every other material is dimmed and
   desaturated and the subject gets a gentle glow
 - same camera work as film1_cinematic.py (tour / entry)
Usage: blender -b blend/gram_negative_base.blend --python scripts/film1_v2.py -- MODE [PCT] [STILLS]
"""
import bpy, os, sys, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
args = sys.argv[sys.argv.index('--') + 1:]
MODE = args[0]
PCT = int(args[1]) if len(args) > 1 else 100
STILLS = [int(x) for x in args[2].split(',')] if len(args) > 2 else None
FPS = 30
LENS = 55.0

sc = bpy.context.scene
objs = bpy.data.objects
mats = bpy.data.materials
cam = objs['Cam_CrossSection']
clip = bpy.data.node_groups['GN_ClipHalfBox']
cut_y = [s.default_value for s in clip.interface.items_tree
         if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y'][0]

# remove any HUD objects left from earlier scripts (not saved anyway)
hud = bpy.data.collections.get('HUD')
if hud:
    for o in list(hud.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    hud = bpy.data.collections.new('HUD')
    sc.collection.children.link(hud)

# ---------- camera rig ----------
for c in list(cam.constraints):
    cam.constraints.remove(c)
if cam.animation_data:
    cam.animation_data_clear()
if cam.data.animation_data:
    cam.data.animation_data_clear()
tgt = bpy.data.objects.new('CamTarget', None)
hud.objects.link(tgt)
trk = cam.constraints.new('TRACK_TO')
trk.target = tgt
trk.track_axis = 'TRACK_NEGATIVE_Z'
trk.up_axis = 'UP_Y'
cam.data.lens = LENS
cam.data.dof.use_dof = True
cam.data.dof.focus_object = tgt
cam.data.dof.aperture_fstop = 2.0          # a little less blur than v1
bg = sc.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.012, 0.018, 0.035, 1.0)
bg.inputs[1].default_value = 1.0


def cam_key(frame, target, dist, dx=0.0, dz=0.0):
    tgt.location = target
    tgt.keyframe_insert('location', frame=frame)
    cam.location = Vector((target.x + dx, target.y + dist, target.z + dz))
    cam.keyframe_insert('location', frame=frame)


def centroid_world(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return sum(vs, Vector()) / len(vs)


# ---------- dimming system ----------
ALL_MATS = ['MAT_lps', 'MAT_lipid', 'MAT_protein_porin', 'MAT_pg_glycan', 'MAT_pg_peptide',
            'MAT_enzyme_tem1', 'MAT_lipid_IM', 'MAT_target_pbp1b', 'MAT_pump_acrb']
orig = {}
for n in ALL_MATS:
    b = mats[n].node_tree.nodes['Principled BSDF']
    if mats[n].node_tree.animation_data:
        mats[n].node_tree.animation_data_clear()
    orig[n] = tuple(b.inputs['Base Color'].default_value)
    b.inputs['Emission Color'].default_value = orig[n]
    b.inputs['Emission Strength'].default_value = 0.0


def dim_color(c, amount=0.65):
    r, g, b, a = c
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    grey = (lum * 0.35, lum * 0.37, lum * 0.42)   # dark, slightly cool
    return tuple(ci * (1 - amount) + gi * amount for ci, gi in zip((r, g, b), grey)) + (a,)


def key_state(frame, subject_mats, glow):
    """keyframe every material: subjects at full colour (+glow), the rest dimmed."""
    for n in ALL_MATS:
        b = mats[n].node_tree.nodes['Principled BSDF']
        is_sub = n in subject_mats
        b.inputs['Base Color'].default_value = orig[n] if is_sub else dim_color(orig[n])
        b.inputs['Base Color'].keyframe_insert('default_value', frame=frame)
        b.inputs['Emission Strength'].default_value = glow if is_sub else 0.0
        b.inputs['Emission Strength'].keyframe_insert('default_value', frame=frame)


def key_normal(frame):
    for n in ALL_MATS:
        b = mats[n].node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = orig[n]
        b.inputs['Base Color'].keyframe_insert('default_value', frame=frame)
        b.inputs['Emission Strength'].default_value = 0.0
        b.inputs['Emission Strength'].keyframe_insert('default_value', frame=frame)


porin = centroid_world(objs['OM_OmpF'])
tem = centroid_world(objs['PP_TEM1_a'])
pbp = centroid_world(objs['IM_PBP1b'])
acrb = centroid_world(objs['IM_AcrB'])
center = Vector((porin.x, cut_y, -3.5))
P = lambda x, z: Vector((x, cut_y + 0.3, z))
GLOW = {'MAT_lps': 0.25, 'MAT_lipid': 0.2, 'MAT_protein_porin': 0.6, 'MAT_pg_glycan': 0.3, 'MAT_pg_peptide': 0.3,
        'MAT_enzyme_tem1': 0.6, 'MAT_lipid_IM': 0.2, 'MAT_target_pbp1b': 0.6, 'MAT_pump_acrb': 0.45}
anchors = {}      # label key -> {"frames": [f0, f1], "pos": {frame: [x, y]}, "text": ..., "corner": ...}
headlines = []


def register_anchor(key, text, corner, f0, f1, point_fn):
    anchors[key] = {'text': text, 'corner': corner, 'frames': [f0, f1], 'point': point_fn}


if MODE == 'tour':
    for o in objs:
        if o.name.startswith('Drug_') or o.name.startswith('Path_drug'):
            o.hide_render = True
    LEAD, HOLD = 3 * FPS, 5 * FPS
    segs = [  # key, target, dist, anchor point, label, screen corner for the text, subject materials
        ('om', P(porin.x - 2, 9.5), 34.0, P(porin.x - 7, 12.5), 'OUTER MEMBRANE', 'bl', ['MAT_lps', 'MAT_lipid']),
        ('porin', P(porin.x, porin.z + 1.0), 22.0, P(porin.x + 0.5, porin.z + 0.5), 'PORIN', 'tl', ['MAT_protein_porin']),
        ('pg', P(porin.x + 2, -1.5), 22.0, P(porin.x + 5.0, -2.4), 'PEPTIDOGLYCAN', 'tl', ['MAT_pg_glycan', 'MAT_pg_peptide']),
        ('tem1', P(tem.x, tem.z + 0.5), 19.0, P(tem.x + 0.5, tem.z + 0.5), 'BETA-LACTAMASE', 'tl', ['MAT_enzyme_tem1']),
        ('im', P(porin.x + 4, -19.0), 34.0, P(porin.x + 9, -19.8), 'INNER MEMBRANE', 'tr', ['MAT_lipid_IM']),
        ('pbp', P(pbp.x - 2.5, pbp.z - 1.0), 30.0, P(pbp.x, pbp.z + 2.0), 'PBP (THE TARGET)', 'tr', ['MAT_target_pbp1b']),
        ('acrb', P(acrb.x, acrb.z), 38.0, P(acrb.x, acrb.z + 3.0), 'EFFLUX PUMP', 'tl', ['MAT_pump_acrb']),
    ]
    cam_key(1, center, 72.0, dz=6.0)
    cam_key(LEAD, center, 62.0, dz=5.0)
    key_normal(1)
    key_normal(LEAD)
    f = LEAD + 1
    for key, target, dist, anchor, label, corner, subj in segs:
        cam_key(f + 25, target, dist)
        cam_key(f + HOLD, target, dist * 0.94, dx=0.4)
        key_state(f + 12, subj, max(GLOW[m] for m in subj))
        key_state(f + HOLD - 12, subj, max(GLOW[m] for m in subj))
        register_anchor(key, label, corner, f + 14, f + HOLD - 8, (lambda a: (lambda fr: a))(anchor))
        f += HOLD
    key_normal(f + 12)
    cam_key(f + 40, center, 72.0, dz=6.0)
    END = f + 40
    OUT = 'film1_v2_tour'
    headlines = []

elif MODE == 'entry':
    for o in objs:
        if o.name.startswith('Drug_') or o.name.startswith('Path_drug'):
            o.hide_render = o.name.startswith('Path_drug')
    fades = {'MAT_drug_travel': {1: 1.0, 470: 1.0, 484: 0.0},
             'MAT_drug_docked': {1: 0.0, 470: 0.0, 484: 1.0, 548: 1.0, 562: 0.0},
             'MAT_drug_product': {1: 0.0, 548: 0.0, 562: 1.0, 700: 1.0, 730: 0.0}}
    for name, strength in (('MAT_drug_travel', 6.0), ('MAT_drug_docked', 1.6), ('MAT_drug_product', 0.9)):
        tree = mats[name].node_tree
        if tree.animation_data:
            tree.animation_data_clear()
        b = tree.nodes['Principled BSDF']
        b.inputs['Emission Strength'].default_value = strength
        a = b.inputs['Alpha']
        for fr, v in sorted(fades[name].items()):
            a.default_value = v
            a.keyframe_insert('default_value', frame=fr)
    drug = objs['Drug_ceftazidime']
    site = objs['Target_TEM1_site'].matrix_world.translation.copy()
    key_normal(1)
    DIST = 26.0
    cam_key(1, center, 72.0, dz=6.0)
    cam_key(90, Vector((porin.x, cut_y, 12.0)), 40.0, dz=6.0)
    for fr in (150, 220, 300, 380, 450):
        sc.frame_set(fr)
        d = drug.matrix_world.translation
        cam_key(fr, Vector((d.x, cut_y, d.z)), DIST, dx=1.5, dz=2.0)
    site_t = Vector((site.x, cut_y, site.z))
    cam_key(520, site_t, 17.0, dx=0.8, dz=1.0)
    cam_key(600, site_t, 15.0, dx=0.4, dz=0.8)
    cam_key(690, site_t, 16.0, dx=-0.3, dz=1.2)
    cam_key(740, site_t, 24.0, dx=-1.0, dz=2.5)
    # subject emphasis during the reaction: dim everything but the enzyme
    key_normal(495)
    key_state(515, ['MAT_enzyme_tem1'], 0.35)
    key_state(700, ['MAT_enzyme_tem1'], 0.35)
    key_normal(725)
    register_anchor('drug', 'CEFTAZIDIME', 'bl', 100, 205, lambda fr: (sc.frame_set(fr), drug.matrix_world.translation.copy())[1])
    register_anchor('porin', 'PORIN', 'tl', 215, 330, lambda fr: P(porin.x + 0.5, porin.z + 0.5))
    register_anchor('tem1', 'BETA-LACTAMASE', 'br', 385, 475, lambda fr: P(tem.x + 0.5, tem.z + 0.5))
    headlines = [(20 / FPS, 110 / FPS, 'A BETA-LACTAM ARRIVES'), (215 / FPS, 300 / FPS, 'THROUGH THE PORIN'),
                 (565 / FPS, 650 / FPS, 'THE BETA-LACTAM RING IS BROKEN')]
    END = 740
    OUT = 'film1_v2_entry'
else:
    raise SystemExit('MODE must be tour or entry')

# ---------- export anchor screen positions (pixels, full-res frame) ----------
W, H = sc.render.resolution_x, sc.render.resolution_y
export = {}
for key, a in anchors.items():
    pos = {}
    for fr in range(a['frames'][0] - 2, a['frames'][1] + 3):
        sc.frame_set(fr)
        p = a['point'](fr)
        sc.frame_set(fr)            # point_fn may have moved the frame
        v = world_to_camera_view(sc, cam, p)
        pos[fr] = [round(v.x * W, 1), round((1.0 - v.y) * H, 1)]
    export[key] = {'text': a['text'], 'corner': a['corner'], 'frames': a['frames'], 'pos': pos}
with open(os.path.join(BASE, 'render', OUT + '_anchors.json'), 'w', encoding='utf-8') as fh:
    json.dump({'fps': FPS, 'size': [W, H], 'labels': export, 'headlines': headlines}, fh, indent=0)
print('ANCHORS', {k: (v['frames'], list(v['pos'].values())[len(v['pos']) // 2]) for k, v in export.items()})

for m in sc.timeline_markers:
    m.camera = None
sc.camera = cam
sc.render.resolution_percentage = PCT
if STILLS:
    sc.render.image_settings.media_type = 'IMAGE'
    sc.render.image_settings.file_format = 'PNG'
    for fr in STILLS:
        sc.frame_set(fr)
        sc.render.filepath = os.path.join(BASE, 'render', '%s_f%04d.png' % (OUT, fr))
        bpy.ops.render.render(write_still=True)
        print('STILL', fr)
else:
    sc.frame_start, sc.frame_end = 1, END
    sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = os.path.join(BASE, 'render', OUT + '.mp4')
    bpy.ops.render.render(animation=True)
    print('RENDER_DONE', sc.render.filepath, 'frames', END)
