"""Episode 2: Beta-lactams hit the wall.
Same drug, same door, different ending: no beta-lactamase, so ceftazidime
reaches PBP1b, acylates its active-site serine, wall synthesis stops, the
wall opens, the inner membrane bulges through.

The 'entry' timeline is beat-for-beat aligned with episode 1's entry
(frames 1-450: identical path, camera and timing) so the two can later be cut
side by side as the long comparison film. They diverge after frame 450.

Modes:
  hook   frames 1-90   : wide view, the three TEM-1 copies fade away ("no enzyme this time")
  entry  frames 1-1010 : aligned entry (1-450 identical to ep1), drift to PBP1b, wall build, docking,
                        ring opening, wall stop/gap/bulge, pull-out, end card
Usage: blender -b blend/gram_negative_base.blend --python episodes/ep02-hit-the-wall/scripts/film2.py -- MODE [PCT] [STILLS]
"""
import bpy, os, sys, json, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep02-hit-the-wall')
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

# wall mechanics (run-time geometry, collection EP2)
_wm = {'__name__': 'wall_mechanics', '__file__': os.path.join(EP, 'scripts', 'wall_mechanics.py')}
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
cam.data.dof.aperture_fstop = 2.0
bg = sc.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.012, 0.018, 0.035, 1.0)
bg.inputs[1].default_value = 1.0


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


def key_state(frame, subject_mats, glow):
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
pbp = centroid_world(objs['IM_PBP1b'])
center = Vector((porin.x, cut_y, -3.5))
P = lambda x, z: Vector((x, cut_y + 0.3, z))
SITE = Vector((36.75, 58.48, -108.99)) * 0.1       # from transfer_pbp_pose.py (scene nm)
ENTR = Vector((33.23, 53.80, -100.89)) * 0.1
anchors, headlines, cards, bursts = {}, [], [], []


def register_anchor(key, text, corner, f0, f1, point_fn):
    anchors[key] = {'text': text, 'corner': corner, 'frames': [f0, f1], 'point': point_fn}


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


# episode 1's bound ligands are parented to TEM-1 and must not show
for n in ('Drug_CAZ_docked', 'Drug_product_hydrolyzed', 'Path_drug_1'):
    if objs.get(n):
        objs[n].hide_render = True

if MODE == 'hook':
    # wide view of the whole envelope; the three enzymes fade out
    for o in objs:
        if o.name.startswith('Drug_'):
            o.hide_render = True
    key_normal(1)
    cam_key(1, center, 72.0, el=6)
    cam_key(90, center, 66.0, el=5, az=-4)
    m = mats['MAT_enzyme_tem1']
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    fade(m, {1: 1.0, 35: 1.0, 80: 0.0, 90: 0.0})
    headlines = [(0.3, 2.9, 'LAST TIME, AN ENZYME ATE THE DRUG.')]
    END = 90
    OUT = 'film2_hook'

elif MODE == 'entry':
    for n in ('PP_TEM1_a', 'PP_TEM1_b', 'PP_TEM1_c'):
        objs[n].hide_render = True
    drug = objs['Drug_ceftazidime']
    objs['Path_drug_1'].hide_render = True
    # ---- the drug: frames 1-450 are episode 1 exactly (untouched path), then it travels to PBP1b ----
    # keep every key the base scene has (identical to episode 1 through frame 480: path, tumble,
    # influence hand-over, arrival at the now-invisible TEM-1); add the onward journey to PBP1b
    drug.location = ENTR + Vector((0.0, 0.0, 3.0)); drug.keyframe_insert('location', frame=520)
    drug.location = ENTR; drug.keyframe_insert('location', frame=545)
    drug.location = SITE; drug.keyframe_insert('location', frame=565)
    red = (0.98, 0.30, 0.20, 1.0)
    m_travel = material('MAT_drug_travel', red, 6.0)
    assign_mn_material(drug, m_travel)
    fade(m_travel, {1: 1.0, 555: 1.0, 569: 0.0})
    docked = import_ligand('ceftazidime_docked_in_pbp1b.pdb', 'Drug_CAZ_docked_pbp', material('MAT_drug_docked2', red, 1.6))
    fade(mats['MAT_drug_docked2'], {1: 0.0, 555: 0.0, 569: 1.0, 656: 1.0, 684: 0.0})
    acyl = import_ligand('cefotaxime_acyl_in_pbp1b.pdb', 'Drug_acyl_pbp', material('MAT_drug_acyl', (0.95, 0.45, 0.25, 1.0), 0.9))
    fade(mats['MAT_drug_acyl'], {1: 0.0, 656: 0.0, 684: 1.0})       # stays: the acyl-enzyme does not leave
    fm = material('MAT_flash2', (1.0, 0.85, 0.6, 1.0), 10.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=SITE, segments=24, ring_count=12)
    flash = bpy.context.active_object
    flash.name = 'HUD_flash'
    for c in list(flash.users_collection):
        c.objects.unlink(flash)
    hud.objects.link(flash)
    flash.data.materials.append(fm)
    for fr, sz in ((660, 0.0), (665, 0.28), (672, 0.38), (686, 0.0)):
        flash.scale = (sz, sz, sz)
        flash.keyframe_insert('scale', frame=fr)

    # ---- wall mechanics ----
    grown = build_wall(470, 590)          # the wall grows while the drug drifts toward PBP1b
    stop_wall(grown, 680)                 # growth freezes as the ring opens on the serine
    open_gap(750, 840, radius=5.0)
    bulge_membrane(790, 900, amplitude=5.0, sigma=4.0)

    # ---- camera: identical to episode 1 for frames 1-450 ----
    key_normal(1)
    DIST = 26.0
    cam_key(1, Vector((porin.x, cut_y, 13.0)), 44.0, az=-8, el=10)
    cam_key(90, Vector((porin.x, cut_y, 12.0)), 36.0, az=-4, el=6)
    for fr in (150, 220, 300, 380, 450):
        sc.frame_set(fr)
        d = drug.matrix_world.translation
        cam_key(fr, Vector((d.x, cut_y, d.z)), DIST, dx=1.5, dz=2.0)
    wall_t = Vector((WALL_C.x + 3.0, cut_y - 1.0, -5.5))
    site_t = Vector((SITE.x, cut_y, SITE.z))
    cam_key(500, wall_t, 26.0, az=-6, el=24)
    cam_key(600, wall_t, 23.0, az=3, el=22)
    cam_key(640, site_t, 16.0, az=8, el=8)
    cam_key(660, site_t, 13.0, dx=0.5, dz=0.6, az=6, el=10)
    cam_key(710, site_t, 12.0, dx=0.3, dz=0.5, az=-4, el=10)
    cam_key(745, site_t, 12.0, dx=0.2, dz=0.5, az=-6, el=10)   # hold the macro through the headline
    cam_key(800, wall_t, 23.0, az=-4, el=26)
    cam_key(880, wall_t, 24.0, az=2, el=24)
    cam_key(920, Vector((WALL_C.x, cut_y, -9.0)), 30.0, az=-8, el=14)
    cam_key(970, center, 72.0, el=6)
    cam_key(1010, center, 72.0, el=6)
    # emphasis
    key_state(485, ['MAT_target_pbp1b', 'MAT_pg_glycan', 'MAT_pg_peptide'], 0.35)
    key_state(610, ['MAT_target_pbp1b', 'MAT_pg_glycan', 'MAT_pg_peptide'], 0.35)
    key_state(640, ['MAT_target_pbp1b'], 0.4)
    key_state(760, ['MAT_target_pbp1b'], 0.4)
    key_state(800, ['MAT_target_pbp1b', 'MAT_pg_glycan', 'MAT_pg_peptide', 'MAT_lipid_IM'], 0.3)
    key_state(905, ['MAT_target_pbp1b', 'MAT_pg_glycan', 'MAT_pg_peptide', 'MAT_lipid_IM'], 0.3)
    key_normal(940)
    key_state(975, [], 0.0)

    # ---- labels, headlines, bursts, card ----
    register_anchor('drug', 'CEFTAZIDIME', 'bl', 100, 205, lambda fr: (sc.frame_set(fr), drug.matrix_world.translation.copy())[1])
    register_anchor('porin', 'PORIN', 'tl', 215, 300, lambda fr: P(porin.x + 0.5, porin.z + 0.5))
    register_anchor('pbp', 'PBP: BUILDS THE WALL', 'bl', 490, 595, lambda fr: P(pbp.x, pbp.z + 2.0))
    register_anchor('bond', '', 'tl', 660, 700, lambda fr: SITE)
    register_anchor('gap', 'THE WALL FAILS', 'tl', 815, 875, lambda fr: Vector((WALL_C.x, cut_y - 1.2, WALL_C.z)))
    bursts = [(662, 696, 'bond')]
    headlines = [(20 / FPS, 110 / FPS, 'SAME DRUG. SAME DOOR.'), (215 / FPS, 300 / FPS, 'THROUGH THE PORIN'),
                 (340 / FPS, 440 / FPS, 'NO ENZYME THIS TIME'), (600 / FPS, 652 / FPS, 'IT REACHES THE TARGET'),
                 (690 / FPS, 748 / FPS, 'THE RING OPENS... AND STAYS'), (815 / FPS, 885 / FPS, 'THE WALL STOPS GROWING'),
                 (898 / FPS, 945 / FPS, 'LYSIS')]
    cards = [(960 / FPS, 1010 / FPS, 'EPISODE 2  -  HITTING THE WALL', 'NEXT: HOW BACTERIA FIGHT BACK')]
    END = 1010
    OUT = 'film2_entry'
else:
    raise SystemExit('MODE must be hook or entry')

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
    json.dump({'fps': FPS, 'size': [W, H], 'labels': export, 'headlines': headlines, 'cards': cards, 'bursts': bursts}, fh, indent=0)

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
