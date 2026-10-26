"""Episode 2b (Two Fates): native landscape shots rendered from the base scene.

Modes (all EEVEE, 30 fps, anchors exported next to the render for the 2D text layer):
  intro   1920x1080, 900 frames (30 s). Wide establishing, push to the outer membrane, descend
          through porin, wall, enzyme, inner membrane, target, pull back out. Matches the
          narration lines 01-04 of NARRATION.md.
  carry   960x1080, 540 frames (18 s). Episode 1's fate: the enzymes are there, the wall keeps
          being built (fresh strands), nothing else happens. Left half of the final shot.
  lysis   960x1080, 540 frames (18 s). Episode 2's fate from the SAME camera: acyl-enzyme on
          PBP1b, growth stops, the wall opens, the inner membrane bulges through. Right half.
  macro1  960x1080, 150 frames (5 s). Close on the TEM-1 active site: ring opens, product released.
  macro2  960x1080, 150 frames (5 s). Close on the PBP1b serine: ring opens, acyl stays.
Usage: blender -b blend/gram_negative_base.blend --python episodes/ep02b-two-fates/scripts/film2b_shots.py -- MODE [PCT] [STILLS]
"""
import bpy, os, sys, json, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep02b-two-fates')
EP2 = os.path.join(BASE, 'episodes', 'ep02-hit-the-wall')
args = sys.argv[sys.argv.index('--') + 1:]
MODE = args[0]
PCT = int(args[1]) if len(args) > 1 else 100
STILLS = [int(x) for x in args[2].split(',')] if len(args) > 2 else None
FPS = 30

sc = bpy.context.scene
objs = bpy.data.objects
mats = bpy.data.materials
cam = objs['Cam_CrossSection']
clip = bpy.data.node_groups['GN_ClipHalfBox']
cut_y = [s.default_value for s in clip.interface.items_tree
         if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y'][0]

_wm = {'__name__': 'wall_mechanics', '__file__': os.path.join(EP2, 'scripts', 'wall_mechanics.py')}
exec(open(_wm['__file__'], encoding='utf-8').read(), _wm)
build_wall, stop_wall, open_gap, bulge_membrane = _wm['build_wall'], _wm['stop_wall'], _wm['open_gap'], _wm['bulge_membrane']
WALL_C = _wm['WALL_C']

hud = bpy.data.collections.get('HUD')
if hud:
    for o in list(hud.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    hud = bpy.data.collections.new('HUD')
    sc.collection.children.link(hud)

# ---------- resolution per mode ----------
if MODE == 'intro':
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
else:
    sc.render.resolution_x, sc.render.resolution_y = 960, 1080
cam.data.sensor_fit = 'HORIZONTAL'
cam.data.sensor_width = 36.0

# ---------- camera rig (same as film2.py) ----------
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
cam.data.lens = 55.0
cam.data.dof.use_dof = True
cam.data.dof.focus_object = tgt
cam.data.dof.aperture_fstop = 2.0
bg = sc.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.012, 0.018, 0.035, 1.0)
bg.inputs[1].default_value = 1.0


def lens_key(frame, mm):
    cam.data.lens = mm
    cam.data.keyframe_insert('lens', frame=frame)


def cam_key(frame, target, dist, dx=0.0, dz=0.0, az=0.0, el=0.0):
    tgt.location = target
    tgt.keyframe_insert('location', frame=frame)
    a, e = math.radians(az), math.radians(el)
    cam.location = Vector((target.x - dist * math.sin(a) * math.cos(e) + dx,
                           target.y + dist * math.cos(a) * math.cos(e),
                           target.z + dist * math.sin(e) + dz))
    cam.keyframe_insert('location', frame=frame)


def centroid_world(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return sum(vs, Vector()) / len(vs)


# ---------- dimming ----------
ALL_MATS = ['MAT_lps', 'MAT_lipid', 'MAT_protein_porin', 'MAT_pg_glycan', 'MAT_pg_peptide',
            'MAT_enzyme_tem1', 'MAT_lipid_IM', 'MAT_target_pbp1b', 'MAT_pump_acrb']
GLOW = {'MAT_lps': 0.25, 'MAT_lipid': 0.2, 'MAT_protein_porin': 0.6, 'MAT_pg_glycan': 0.3, 'MAT_pg_peptide': 0.3,
        'MAT_enzyme_tem1': 0.6, 'MAT_lipid_IM': 0.2, 'MAT_target_pbp1b': 0.6, 'MAT_pump_acrb': 0.45}
orig = {}
for n in ALL_MATS:
    b = mats[n].node_tree.nodes['Principled BSDF']
    if mats[n].node_tree.animation_data:
        mats[n].node_tree.animation_data_clear()
    orig[n] = tuple(b.inputs['Base Color'].default_value)
    if n == 'MAT_lps':
        r, g, bb, a = orig[n]
        orig[n] = (r * 0.72, g * 0.70, bb * 0.62, a)
    b.inputs['Emission Color'].default_value = orig[n]
    b.inputs['Emission Strength'].default_value = 0.0
    b.inputs['Alpha'].default_value = 1.0
for o in objs:
    if o.type == 'MESH' and hasattr(o, 'mn'):
        try:
            if o.mn.n_frames and o.mn.n_frames > 1:
                o.mn.average = 2
        except Exception:
            pass


def dim_color(c, amount=0.65):
    r, g, b, a = c
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    grey = (lum * 0.35, lum * 0.37, lum * 0.42)
    return tuple(ci * (1 - amount) + gi * amount for ci, gi in zip((r, g, b), grey)) + (a,)


def key_state(frame, subject_mats, glow, amount=0.65):
    for n in ALL_MATS:
        b = mats[n].node_tree.nodes['Principled BSDF']
        is_sub = n in subject_mats
        b.inputs['Base Color'].default_value = orig[n] if is_sub else dim_color(orig[n], amount)
        b.inputs['Base Color'].keyframe_insert('default_value', frame=frame)
        b.inputs['Emission Strength'].default_value = glow if is_sub else 0.0
        b.inputs['Emission Strength'].keyframe_insert('default_value', frame=frame)


def key_normal(frame):
    key_state(frame, ALL_MATS, 0.0)


def material(name, rgba, emis=0.0):
    m = mats.get(name) or mats.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Emission Color'].default_value = rgba
    b.inputs['Emission Strength'].default_value = emis
    b.inputs['Roughness'].default_value = 0.35
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    if m.node_tree.animation_data:
        m.node_tree.animation_data_clear()
    return m


def fade(mat, keys):
    a = mat.node_tree.nodes['Principled BSDF'].inputs['Alpha']
    for f, v in sorted(keys.items()):
        a.default_value = v
        a.keyframe_insert('default_value', frame=f)


def assign_mn_material(obj, mat):
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group and mod.node_group is not clip:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = mat


def import_ligand(fn, name, mat):
    if objs.get(name):
        bpy.data.objects.remove(objs[name], do_unlink=True)
    before = set(objs)
    bpy.ops.mn.import_molecule(method='local', filepath=os.path.join(BASE, 'pdb', 'ligands', fn),
                               file_format='pdb', style='ball_and_stick')
    o = next(x for x in objs if x not in before and x.type == 'MESH')
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    hud.objects.link(o)
    assign_mn_material(o, mat)
    return o


def flash_sphere(name, at, keys, color=(1.0, 0.85, 0.6, 1.0)):
    fm = material('MAT_' + name, color, 10.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=at, segments=24, ring_count=12)
    fl = bpy.context.active_object
    fl.name = name
    for c in list(fl.users_collection):
        c.objects.unlink(fl)
    hud.objects.link(fl)
    fl.data.materials.append(fm)
    for fr, sz in keys:
        fl.scale = (sz, sz, sz)
        fl.keyframe_insert('scale', frame=fr)
    return fl


porin = centroid_world(objs['OM_OmpF'])
tem = centroid_world(objs['PP_TEM1_a'])
pbp = centroid_world(objs['IM_PBP1b'])
acrb = centroid_world(objs['IM_AcrB'])
center = Vector((porin.x, cut_y, -3.5))
P = lambda x, z: Vector((x, cut_y + 0.3, z))
SITE2 = Vector((36.75, 58.48, -108.99)) * 0.1        # PBP1b serine site (scene nm)
site1 = objs['Target_TEM1_site'].matrix_world.translation.copy()
anchors, headlines, bursts = {}, [], []


def register_anchor(key, text, corner, f0, f1, point_fn):
    anchors[key] = {'text': text, 'corner': corner, 'frames': [f0, f1], 'point': point_fn}


def hide(names, state=True):
    for n in names:
        if objs.get(n):
            objs[n].hide_render = state


EP1_DRUGS = ['Drug_ceftazidime', 'Drug_CAZ_docked', 'Drug_product_hydrolyzed', 'Path_drug_1']
TEM1S = ['PP_TEM1_a', 'PP_TEM1_b', 'PP_TEM1_c']

# ======================================================================================
def widen_tiles():
    """16:9 wide shots see past the 36 nm the vertical films needed: tile the membranes and the wall wider."""
    for name in ('OM_lipids', 'OM_LPS'):
        o = objs[name]
        m = next(m for m in o.modifiers if m.type == 'ARRAY')
        m.count += 4
        o.location.x -= 2 * m.constant_offset_displace[0]
    # inner membrane: holed sheet + fill repeat every 45 nm; the extra AcrB holes land outside the frame
    for name in ('IM_lipids', 'IM_lipids_fill'):
        o = objs[name]
        m = o.modifiers.new('TileWide', 'ARRAY')
        m.use_relative_offset = False
        m.use_constant_offset = True
        m.constant_offset_displace = (45.17, 0.0, 0.0)
        m.count = 3
        o.modifiers.move(o.modifiers.find(m.name), 0)
        o.location.x -= 45.17
    for name in ('PG_glycan', 'PG_peptide'):
        o = objs[name]
        span = 36.1
        m = o.modifiers.new('TileWide', 'ARRAY')
        m.use_relative_offset = False
        m.use_constant_offset = True
        m.constant_offset_displace = (span, 0.0, 0.0)
        m.count = 3
        o.modifiers.move(o.modifiers.find(m.name), 0)
        o.location.x -= span


if MODE == 'intro':
    hide(EP1_DRUGS)
    widen_tiles()
    key_normal(1)
    # a longer lens for the wide shots keeps the layers filling the 16:9 frame
    lens_key(1, 35.0)
    WIDE = Vector((13.0, cut_y, -4.0))
    cam_key(1, WIDE, 60.0, el=7)                         # whole envelope, fade-in under it
    cam_key(140, Vector((11.0, cut_y, -1.0)), 54.0, az=-5, el=6)
    lens_key(140, 35.0)
    lens_key(300, 55.0)
    # arrive, then hold with a slow drift (push-in and a few degrees of arc) while the label is up
    stops = [  # key, arrive, leave, target, dist, az, el, label, corner, anchor point, subject mats, glow
        ('om', 260, 350, P(porin.x - 1, 9.5), 26.0, -16, 20, 'OUTER MEMBRANE', 'bl', P(porin.x - 5, 11.5), ['MAT_lps', 'MAT_lipid'], 0.25),
        ('porin', 400, 480, P(porin.x, porin.z + 0.5), 19.0, 12, 8, 'PORIN', 'tl', P(porin.x + 0.5, porin.z + 0.5), ['MAT_protein_porin'], 0.6),
        ('pg', 530, 600, P(porin.x + 4, -2.4), 21.0, -4, 26, 'PEPTIDOGLYCAN (THE WALL)', 'tl', Vector((porin.x + 1.0, cut_y - 3.0, -2.2)), ['MAT_pg_glycan', 'MAT_pg_peptide'], 0.3),
        ('im', 640, 690, P(porin.x - 1, -19.0), 30.0, -12, 16, 'INNER MEMBRANE', 'tr', Vector((porin.x - 4.5, cut_y + 2.5, -19.6)), ['MAT_lipid_IM'], 0.2),
        ('tem1', 730, 790, P(tem.x, tem.z + 0.5), 17.0, 16, 6, 'BETA-LACTAMASE (THE ENZYME)', 'tl', P(tem.x + 0.5, tem.z + 0.5), ['MAT_enzyme_tem1'], 0.6),
        ('pbp', 825, 870, P(pbp.x - 2.0, pbp.z + 0.5), 27.0, 12, 10, 'PBP (THE TARGET)', 'tr', P(pbp.x, pbp.z + 2.0), ['MAT_target_pbp1b'], 0.6),
    ]
    key_normal(230)
    for key, fa, fl, target, dist, az, el, label, corner, anchor, subj, glow in stops:
        cam_key(fa, target, dist, az=az, el=el)
        cam_key(fl, target, dist * 0.93, az=az + (8 if az < 0 else -8), el=el * 0.85)
        key_state(fa - 8, subj, glow, 0.5)
        key_state(fl, subj, glow, 0.5)
        register_anchor(key, label, corner, fa + 5, fl - 4, (lambda a: (lambda fr: a))(anchor))
    key_normal(890)
    lens_key(870, 55.0)
    lens_key(900, 35.0)
    cam_key(900, WIDE, 58.0, el=7)                       # back out for the title
    END, OUT = 900, 'tf_intro'

elif MODE in ('carry', 'lysis'):
    hide(EP1_DRUGS)
    if os.environ.get('TF_DEBUG_HIDE_OLD'):
        hide(['PG_glycan', 'PG_peptide'])
    # the same camera for both halves: lower envelope (wall, PBP, inner membrane), slow push
    wall_t = Vector((WALL_C.x + 2.0, cut_y - 1.0, -7.5))
    cam_key(1, wall_t, 40.0, az=-6, el=24)
    cam_key(540, Vector((WALL_C.x + 1.0, cut_y - 1.0, -8.5)), 30.0, az=3, el=22)
    key_normal(1)
    if MODE == 'carry':
        # episode 1's world: the enzymes stand guard, the wall keeps growing. Nothing fails.
        grown = build_wall(1, 260, n_strands=4, stagger=70)
        key_state(30, ['MAT_pg_glycan', 'MAT_pg_peptide', 'MAT_target_pbp1b', 'MAT_enzyme_tem1'], 0.3, 0.45)
        key_state(540, ['MAT_pg_glycan', 'MAT_pg_peptide', 'MAT_target_pbp1b', 'MAT_enzyme_tem1'], 0.3, 0.45)
        OUT = 'tf_carry'
    else:
        hide(TEM1S)
        acyl = import_ligand('cefotaxime_acyl_in_pbp1b.pdb', 'Drug_acyl_pbp', material('MAT_drug_acyl', (0.95, 0.45, 0.25, 1.0), 1.2))
        grown = build_wall(1, 170, n_strands=3, stagger=36)
        stop_wall(grown, 120)                           # growth freezes at once: the enzyme is locked
        open_gap(160, 290, radius=5.0)
        bulge_membrane(230, 450, amplitude=5.5, sigma=4.0)
        key_state(30, ['MAT_pg_glycan', 'MAT_pg_peptide', 'MAT_target_pbp1b', 'MAT_lipid_IM'], 0.3, 0.45)
        key_state(540, ['MAT_pg_glycan', 'MAT_pg_peptide', 'MAT_target_pbp1b', 'MAT_lipid_IM'], 0.3, 0.45)
        register_anchor('gap', 'THE WALL FAILS', 'tl', 250, 330, lambda fr: Vector((WALL_C.x, cut_y - 1.2, WALL_C.z)))
        register_anchor('bulge', 'MEMBRANE PUSHES THROUGH', 'tl', 380, 470, lambda fr: Vector((WALL_C.x, cut_y - 1.2, WALL_C.z - 3.0)))
        OUT = 'tf_lysis'
    END = 540

elif MODE == 'macro1':
    # episode 1 chemistry, close: docked ceftazidime -> flash -> hydrolyzed product
    hide(['Drug_ceftazidime', 'Path_drug_1'])
    for name, strength, keys in (('MAT_drug_docked', 1.6, {1: 1.0, 70: 1.0, 95: 0.0}),
                                 ('MAT_drug_product', 0.9, {1: 0.0, 70: 0.0, 95: 1.0})):
        tree = mats[name].node_tree
        if tree.animation_data:
            tree.animation_data_clear()
        b = tree.nodes['Principled BSDF']
        b.inputs['Emission Strength'].default_value = strength
        fade(mats[name], keys)
    flash_sphere('HUD_flash1', site1, ((66, 0.0), (72, 0.30), (80, 0.40), (96, 0.0)))
    st = Vector((site1.x, cut_y, site1.z))
    cam_key(1, st, 8.5, dx=0.4, dz=0.5, az=10, el=10)
    cam_key(150, st, 7.0, dx=0.2, dz=0.4, az=-8, el=12)
    key_state(1, ['MAT_enzyme_tem1'], 0.35)
    register_anchor('bond', '', 'tl', 60, 110, lambda fr: site1)
    bursts = [(68, 104, 'bond')]
    END, OUT = 150, 'tf_macro1'

elif MODE == 'macro2':
    hide(EP1_DRUGS)
    hide(TEM1S)
    red = (0.98, 0.30, 0.20, 1.0)
    import_ligand('ceftazidime_docked_in_pbp1b.pdb', 'Drug_CAZ_docked_pbp', material('MAT_drug_docked2', red, 1.6))
    fade(mats['MAT_drug_docked2'], {1: 1.0, 70: 1.0, 95: 0.0})
    import_ligand('cefotaxime_acyl_in_pbp1b.pdb', 'Drug_acyl_pbp', material('MAT_drug_acyl', (0.95, 0.45, 0.25, 1.0), 0.9))
    fade(mats['MAT_drug_acyl'], {1: 0.0, 70: 0.0, 95: 1.0})
    flash_sphere('HUD_flash2', SITE2, ((66, 0.0), (72, 0.30), (80, 0.40), (96, 0.0)))
    st = Vector((SITE2.x, cut_y, SITE2.z))
    # the serine pocket is covered from the front; look at it from the side (TF_CAM="az,el" overrides for tests)
    az0, el0 = [float(v) for v in os.environ.get('TF_CAM', '-75,20').split(',')]
    cam_key(1, st, 8.5, dx=0.2, dz=0.3, az=az0 + 8, el=el0)
    cam_key(150, st, 7.0, dx=0.1, dz=0.3, az=az0 - 8, el=el0 + 3)
    key_state(1, ['MAT_target_pbp1b'], 0.4)
    register_anchor('bond', '', 'tl', 60, 110, lambda fr: SITE2)
    bursts = [(68, 104, 'bond')]
    END, OUT = 150, 'tf_macro2'
else:
    raise SystemExit('MODE must be intro, carry, lysis, macro1 or macro2')

# ---------- export anchors ----------
W, H = sc.render.resolution_x, sc.render.resolution_y
export = {}
for key, a in anchors.items():
    pos = {}
    for fr in range(a['frames'][0] - 2, a['frames'][1] + 3):
        sc.frame_set(fr)
        p = a['point'](fr)
        sc.frame_set(fr)
        v = world_to_camera_view(sc, cam, p)
        pos[fr] = [round(v.x * W, 1), round((1.0 - v.y) * H, 1)]
    export[key] = {'text': a['text'], 'corner': a['corner'], 'frames': a['frames'], 'pos': pos}
os.makedirs(os.path.join(EP, 'renders'), exist_ok=True)
with open(os.path.join(EP, 'renders', OUT + '_anchors.json'), 'w', encoding='utf-8') as fh:
    json.dump({'fps': FPS, 'size': [W, H], 'labels': export, 'headlines': headlines, 'cards': [], 'bursts': bursts}, fh, indent=0)

for m in sc.timeline_markers:
    m.camera = None
sc.camera = cam
sc.render.resolution_percentage = PCT
if STILLS:
    sc.render.image_settings.media_type = 'IMAGE'
    sc.render.image_settings.file_format = 'PNG'
    for fr in STILLS:
        sc.frame_set(fr)
        sc.render.filepath = os.path.join(EP, 'renders', '%s_f%04d.png' % (OUT, fr))
        bpy.ops.render.render(write_still=True)
        print('STILL', fr)
else:
    sc.frame_start, sc.frame_end = 1, END
    sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = os.path.join(EP, 'renders', OUT + '.mp4')
    bpy.ops.render.render(animation=True)
    print('RENDER_DONE', sc.render.filepath, 'frames', END)
