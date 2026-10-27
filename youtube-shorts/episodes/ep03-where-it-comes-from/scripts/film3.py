"""Episode 3: Where the enzyme comes from. One continuous vertical film (1080x1920, 30 fps).

Timeline (frames):
    1- 150  hook: the periplasm enzyme of episode 1, then the camera drops through the inner membrane
  150- 420  cytoplasm: chromosome (dim) and the plasmid; the bla gene arc lights up
  420- 720  expression: a new TEM-1 forms by the plasmid, crosses the inner membrane, settles in the periplasm
  720-1140  conjugation: wide on two cells, the F-pilus bridges them, a single strand runs across,
            the recipient completes its ring and the gene lights there too
 1140-1500  the recipient makes the enzyme; ceftazidime enters its porin; ring broken, cell carries on
 1500-1740  pull out: both cells, both plasmids glowing; end card
Usage: blender -b blend/gram_negative_base.blend --python episodes/ep03-where-it-comes-from/scripts/film3.py -- short [PCT] [STILLS]
"""
import bpy, os, sys, json, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep03-where-it-comes-from')
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

_a = {'__name__': 'ep3_assets', '__file__': os.path.join(EP, 'scripts', 'ep3_assets.py')}
exec(open(_a['__file__'], encoding='utf-8').read(), _a)
_a['__file__'] = os.path.join(EP, 'scripts', 'ep3_dna.py')
exec(open(_a['__file__'], encoding='utf-8').read(), _a)
pilus, duplicate_cell = _a['pilus'], _a['duplicate_cell']
nascent_tem1, transfer_strand, dash, gene_glow = _a['nascent_tem1'], _a['transfer_strand'], _a['dash'], _a['gene_glow']
plasmid, chromosome, ring_grow = _a['dna_ring'], _a['dna_chromosome'], _a['dna_ring_grow']

hud = bpy.data.collections.get('HUD')
if hud:
    for o in list(hud.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    hud = bpy.data.collections.new('HUD')
    sc.collection.children.link(hud)
sc.render.resolution_x, sc.render.resolution_y = (1920, 1080) if MODE == 'wide' else (1080, 1920)
cam.data.sensor_fit = 'HORIZONTAL'
cam.data.sensor_width = 36.0

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
cam.data.lens = 55.0
cam.data.dof.use_dof = True
cam.data.dof.focus_object = tgt
cam.data.dof.aperture_fstop = 2.2
bg = sc.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.012, 0.018, 0.035, 1.0)


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


TEM_OFF = None   # centroid - origin of PP_TEM1_a, so nascent copies are placed by their centroid


def loc_key(ob, frame, loc, scale=None):
    ob.location = Vector(loc) - TEM_OFF
    ob.keyframe_insert('location', frame=frame)
    if scale is not None:
        ob.scale = (scale, scale, scale)
        ob.keyframe_insert('scale', frame=frame)


# ---------- dimming (as in the other films) ----------
ALL_MATS = ['MAT_lps', 'MAT_lipid', 'MAT_protein_porin', 'MAT_pg_glycan', 'MAT_pg_peptide',
            'MAT_enzyme_tem1', 'MAT_lipid_IM', 'MAT_target_pbp1b', 'MAT_pump_acrb', 'MAT_pilus']
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


def alpha_keys(mat, keys):
    a = mat.node_tree.nodes['Principled BSDF'].inputs['Alpha']
    for f, v in sorted(keys.items()):
        a.default_value = v
        a.keyframe_insert('default_value', frame=f)


# ---------- scene layout ----------
porin = centroid_world(objs['OM_OmpF'])
tem = centroid_world(objs['PP_TEM1_a'])
TEM_OFF = tem - objs['PP_TEM1_a'].matrix_world.translation
pbp = centroid_world(objs['IM_PBP1b'])
P = lambda x, z: Vector((x, cut_y + 0.3, z))
DX = 72.0                                   # cell B offset along x
DNA_Y = cut_y - 2.2                         # just behind the cut plane
PLASMID_A = Vector((24.0, DNA_Y, -40.0))
PLASMID_B = PLASMID_A + Vector((DX, 0, 0))
IM_TOP, IM_BOT = -17.0, -23.5

for n in ('Drug_ceftazidime', 'Drug_CAZ_docked', 'Drug_product_hydrolyzed', 'Path_drug_1'):
    objs[n].hide_render = True

# second cell (no enzyme): copy the envelope, hide its TEM-1s; the drug objects are copied separately below
cellB = duplicate_cell(DX, names=('OuterMembrane', 'Periplasm', 'InnerMembrane', 'Drugs'))
for n in ('PP_TEM1_a', 'PP_TEM1_b', 'PP_TEM1_c'):
    cellB[n].hide_render = True

chrA = chromosome(((-11.0, 14.0), (DNA_Y - 1.5, DNA_Y + 1.5), (-66.0, -28.0)), tag='A')
chrB = chromosome(((-11.0 + DX, 14.0 + DX), (DNA_Y - 1.5, DNA_Y + 1.5), (-66.0, -28.0)), tag='B')
plA = plasmid(PLASMID_A, tag='A')
plB = plasmid(PLASMID_B, tag='B')
for n in ('MAT_dna_atoms', 'MAT_dna_atoms_dim'):          # attribute-coloured: only emission is keyable
    ALL_MATS.append(n)
    orig[n] = tuple(mats[n].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)
pil = pilus(14.0, 62.0, 7.5, cut_y - 1.5, copies=2)
anchors, headlines, cards, bursts = {}, [], [], []


def register_anchor(key, text, corner, f0, f1, point_fn):
    anchors[key] = {'text': text, 'corner': corner, 'frames': [f0, f1], 'point': point_fn}


def drug_entry_B(f0, f1):
    """Cell B's ceftazidime: the episode-1 path (frames 1-450) replayed shifted by one cell over f0..f1."""
    drugB = cellB['Drug_ceftazidime']
    drugB.hide_render = False
    for c in list(drugB.constraints):
        drugB.constraints.remove(c)
    drugB.animation_data_clear()
    drugB.parent = None
    srcd = objs['Drug_ceftazidime']
    for f in range(f0, f1 + 1, 4):
        fo = 1 + int((f - f0) / float(f1 - f0) * 449)
        sc.frame_set(fo)
        mw = srcd.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
        drugB.location = mw.translation + Vector((DX, 0, 0))
        drugB.keyframe_insert('location', frame=f)
        drugB.rotation_euler = mw.to_euler()
        drugB.keyframe_insert('rotation_euler', frame=f)
    drugB.keyframe_insert('location', frame=1)
    alpha_keys(mats['MAT_drug_travel'], {1: 0.0, f0 - 5: 0.0, f0 + 5: 1.0, f1 + 5: 1.0, f1 + 20: 0.0})
    mats['MAT_drug_travel'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 4.0
    return drugB


def ligands_B(f_dock, f_flash, f_fade):
    """Docked drug appears on the new enzyme, flash, product released (cell B copies placed by world matrix)."""
    for n in ('Drug_CAZ_docked', 'Drug_product_hydrolyzed'):
        c = cellB[n]
        c.hide_render = False
        c.parent = None
        c.matrix_world = objs[n].matrix_world.copy()
        c.location.x += DX
    for name in ('MAT_drug_docked', 'MAT_drug_product'):
        if mats[name].node_tree.animation_data:
            mats[name].node_tree.animation_data_clear()
    alpha_keys(mats['MAT_drug_docked'], {1: 0.0, f_dock - 15: 0.0, f_dock: 1.0, f_flash + 2: 1.0, f_flash + 18: 0.0})
    alpha_keys(mats['MAT_drug_product'], {1: 0.0, f_flash + 2: 0.0, f_flash + 18: 1.0, f_fade: 1.0, f_fade + 40: 0.0})
    mats['MAT_drug_docked'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.6
    mats['MAT_drug_product'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.9
    siteB = Vector((tem.x + DX, cut_y, tem.z + 0.5))
    fm = bpy.data.materials.new('MAT_flash3')
    fm.use_nodes = True
    fb = fm.node_tree.nodes['Principled BSDF']
    fb.inputs['Emission Color'].default_value = (1.0, 0.8, 0.5, 1.0)
    fb.inputs['Emission Strength'].default_value = 10.0
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=siteB, segments=24, ring_count=12)
    flash = bpy.context.active_object
    flash.name = 'HUD_flash'
    for c in list(flash.users_collection):
        c.objects.unlink(flash)
    hud.objects.link(flash)
    flash.data.materials.append(fm)
    for fr, sz in ((f_flash, 0.0), (f_flash + 6, 0.3), (f_flash + 14, 0.4), (f_flash + 30, 0.0)):
        flash.scale = (sz, sz, sz)
        flash.keyframe_insert('scale', frame=fr)
    return siteB


if MODE == 'short':
    # ---- hook: episode-1 enzyme, then down through the inner membrane ----
    key_normal(1)
    cam_key(1, P(tem.x, tem.z + 0.5), 18.0, az=12, el=6)
    cam_key(60, P(tem.x, tem.z + 0.5), 17.0, az=6, el=4)
    cam_key(150, Vector((12.0, cut_y, -44.0)), 46.0, az=-4, el=4)
    key_state(40, ['MAT_enzyme_tem1'], 0.5, 0.5)
    key_state(90, ['MAT_enzyme_tem1'], 0.5, 0.5)
    key_normal(140)
    register_anchor('tem1', 'THE ENZYME', 'tl', 20, 100, lambda fr: P(tem.x + 0.5, tem.z + 0.5))
    # ---- cytoplasm ----
    cam_key(230, Vector((10.0, cut_y, -44.0)), 44.0, az=4, el=6)
    key_state(170, ['MAT_dna_atoms_dim'], 0.15, 0.55)
    key_state(230, ['MAT_dna_atoms_dim'], 0.15, 0.55)
    register_anchor('chrom', 'CHROMOSOME', 'bl', 175, 250, lambda fr: Vector((2.0, DNA_Y, -48.0)))
    cam_key(300, Vector((PLASMID_A.x, cut_y, PLASMID_A.z)), 24.0, az=-8, el=8)
    cam_key(420, Vector((PLASMID_A.x, cut_y, PLASMID_A.z)), 22.0, az=6, el=10)
    key_state(270, ['MAT_dna_atoms'], 0.25, 0.6)
    key_state(420, ['MAT_dna_atoms'], 0.25, 0.6)
    register_anchor('plasmid', 'PLASMID', 'tr', 300, 370, lambda fr: PLASMID_A + Vector((-plA['radius'], 0, 0)))
    gene_glow(plA, {1: 0.0, 335: 0.0, 360: 0.3})
    register_anchor('gene', 'THE bla GENE', 'bl', 365, 440, lambda fr: PLASMID_A + Vector((plA['radius'] * math.cos(2 * math.pi * 0.135), 0, plA['radius'] * math.sin(2 * math.pi * 0.135))))
    # ---- expression: new TEM-1 from the plasmid, through the IM, into the periplasm ----
    newA = nascent_tem1('EP3_tem1_newA')
    start = PLASMID_A + Vector((plA['radius'] + 3.0, 0, 2.0))
    under_im = Vector((30.0, DNA_Y, IM_BOT - 2.5))
    in_im = Vector((30.0, DNA_Y, (IM_TOP + IM_BOT) / 2))
    peri = Vector((30.0, DNA_Y, -12.5))
    loc_key(newA, 1, start, 0.0)
    loc_key(newA, 430, start, 0.0)
    loc_key(newA, 470, start, 1.0)
    loc_key(newA, 560, under_im, 1.0)
    loc_key(newA, 620, in_im, 1.0)
    loc_key(newA, 680, peri, 1.0)
    loc_key(newA, 1740, peri, 1.0)
    cam_key(470, Vector((start.x, cut_y, start.z)), 20.0, az=-6, el=8)
    cam_key(560, Vector((under_im.x, cut_y, under_im.z + 2)), 22.0, az=-4, el=10)
    cam_key(640, Vector((in_im.x, cut_y, in_im.z + 3)), 20.0, az=4, el=12)
    cam_key(720, Vector((peri.x, cut_y, peri.z)), 22.0, az=8, el=8)
    key_state(450, ['MAT_enzyme_tem1', 'MAT_dna_atoms'], 0.4, 0.6)
    key_state(600, ['MAT_enzyme_tem1', 'MAT_lipid_IM'], 0.4, 0.6)
    key_state(700, ['MAT_enzyme_tem1'], 0.4, 0.6)
    register_anchor('new', 'NEW ENZYME', 'tl', 480, 545, lambda fr: (sc.frame_set(fr), newA.matrix_world.translation.copy())[1])
    register_anchor('im', 'INNER MEMBRANE', 'tr', 590, 650, lambda fr: Vector((36.0, cut_y + 1.5, -19.5)))
    register_anchor('peri', 'PERIPLASM', 'tl', 690, 750, lambda fr: Vector((30.0, DNA_Y, -10.0)))
    # ---- conjugation ----
    key_normal(760)
    lens_key(720, 55.0)
    lens_key(800, 40.0)
    cam_key(800, Vector((36.0, cut_y, -12.0)), 92.0, el=5)
    cam_key(880, Vector((38.0, cut_y, 4.0)), 50.0, az=-5, el=6)
    cam_key(1000, Vector((44.0, cut_y, 4.0)), 44.0, az=5, el=4)
    alpha_keys(mats['MAT_pilus'], {1: 0.0, 820: 0.0, 860: 1.0})
    key_state(850, ['MAT_pilus'], 0.3, 0.5)
    key_state(1000, ['MAT_pilus'], 0.3, 0.5)
    register_anchor('pilus', 'PILUS', 'bl', 870, 960, lambda fr: Vector((44.0, cut_y - 1.5, 9.5)))
    # a single strand: from plasmid A up through the cell, along the pilus, down into cell B's cytoplasm
    path = [tuple(PLASMID_A + Vector((plA['radius'], 0, 0))), (30.0, DNA_Y, -30.0), (27.0, DNA_Y, -6.0), (26.0, DNA_Y, 7.5),
            (40.0, DNA_Y, 7.5), (56.0, DNA_Y, 7.5), (64.0, DNA_Y, 0.0), (74.0, DNA_Y, -20.0), tuple(PLASMID_B + Vector((-plB['radius'], 0, 4.0)))]
    strand = transfer_strand(path)
    dash(strand, 960, 1100, 0.10)
    lens_key(1040, 40.0)
    lens_key(1100, 55.0)
    cam_key(1100, Vector((PLASMID_B.x, cut_y, PLASMID_B.z)), 24.0, az=-6, el=8)
    cam_key(1140, Vector((PLASMID_B.x, cut_y, PLASMID_B.z)), 22.0, az=4, el=10)
    ring_grow(plB, 1060, 1120)
    gene_glow(plB, {1: 0.0, 1115: 0.0, 1140: 0.3})
    key_state(1060, ['MAT_dna_atoms'], 0.25, 0.6)
    key_state(1140, ['MAT_dna_atoms'], 0.25, 0.6)
    register_anchor('copy', 'A COPY', 'tr', 1100, 1150, lambda fr: PLASMID_B + Vector((-plB['radius'], 0, 0)))
    # ---- the recipient makes the enzyme, the drug arrives, the ring breaks ----
    newB = nascent_tem1('EP3_tem1_newB')
    startB = start + Vector((DX, 0, 0))
    periB = Vector((tem.x + DX, DNA_Y, tem.z + 0.5))
    loc_key(newB, 1, startB, 0.0)
    loc_key(newB, 1150, startB, 0.0)
    loc_key(newB, 1180, startB, 1.0)
    loc_key(newB, 1250, under_im + Vector((DX, 0, 0)), 1.0)
    loc_key(newB, 1290, in_im + Vector((DX, 0, 0)), 1.0)
    loc_key(newB, 1340, periB, 1.0)
    loc_key(newB, 1740, periB, 1.0)
    cam_key(1250, Vector((startB.x - 2, cut_y, startB.z + 8)), 30.0, az=-4, el=8)
    cam_key(1340, Vector((periB.x, cut_y, periB.z + 4)), 24.0, az=6, el=8)
    key_state(1170, ['MAT_enzyme_tem1', 'MAT_dna_atoms'], 0.4, 0.6)
    key_state(1340, ['MAT_enzyme_tem1'], 0.4, 0.6)
    # drug for cell B: copy the path and the drug, re-time the entry to 1330-1470
    # drug for cell B: sample the episode-1 path (frames 1-450) and replay it shifted by one cell over 1330-1470
    drugB = cellB['Drug_ceftazidime']
    drugB.hide_render = False
    for c in list(drugB.constraints):
        drugB.constraints.remove(c)
    drugB.animation_data_clear()
    drugB.parent = None
    srcd = objs['Drug_ceftazidime']
    for f in range(1330, 1471, 4):
        fo = 1 + int((f - 1330) / 140.0 * 449)
        sc.frame_set(fo)
        mw = srcd.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
        drugB.location = mw.translation + Vector((DX, 0, 0))
        drugB.keyframe_insert('location', frame=f)
        drugB.rotation_euler = mw.to_euler()
        drugB.keyframe_insert('rotation_euler', frame=f)
    drugB.keyframe_insert('location', frame=1)
    alpha_keys(mats['MAT_drug_travel'], {1: 0.0, 1325: 0.0, 1335: 1.0, 1475: 1.0, 1490: 0.0})
    mats['MAT_drug_travel'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 4.0
    for fr in (1360, 1420, 1470):
        sc.frame_set(fr)
        d = drugB.matrix_world.translation
        cam_key(fr, Vector((d.x, cut_y, d.z)), 26.0, dx=1.5, dz=2.0)
    register_anchor('drug', 'CEFTAZIDIME', 'bl', 1345, 1420, lambda fr: (sc.frame_set(fr), drugB.matrix_world.translation.copy())[1])
    # docked / product on the new enzyme in B (ligands parented to PP_TEM1_a copy; use cell B's hidden copy positions)
    # cell B's copied ligands sit on the hidden PP_TEM1_a_B, exactly where newB settles: key their materials
    for n in ('Drug_CAZ_docked', 'Drug_product_hydrolyzed'):
        c = cellB[n]
        c.hide_render = False
        c.parent = None
        c.matrix_world = objs[n].matrix_world.copy()
        c.location.x += DX
    for name in ('MAT_drug_docked', 'MAT_drug_product'):
        if mats[name].node_tree.animation_data:
            mats[name].node_tree.animation_data_clear()
    alpha_keys(mats['MAT_drug_docked'], {1: 0.0, 1480: 0.0, 1495: 1.0, 1532: 1.0, 1548: 0.0})
    alpha_keys(mats['MAT_drug_product'], {1: 0.0, 1532: 0.0, 1548: 1.0, 1600: 1.0, 1640: 0.0})
    mats['MAT_drug_docked'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.6
    mats['MAT_drug_product'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.9
    siteB = Vector((tem.x + DX, cut_y, tem.z + 0.5))
    cam_key(1520, siteB, 14.0, az=6, el=8)
    cam_key(1580, siteB, 12.0, az=-4, el=10)
    fm = bpy.data.materials.new('MAT_flash3')
    fm.use_nodes = True
    fb = fm.node_tree.nodes['Principled BSDF']
    fb.inputs['Emission Color'].default_value = (1.0, 0.8, 0.5, 1.0)
    fb.inputs['Emission Strength'].default_value = 10.0
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=siteB, segments=24, ring_count=12)
    flash = bpy.context.active_object
    flash.name = 'HUD_flash'
    for c in list(flash.users_collection):
        c.objects.unlink(flash)
    hud.objects.link(flash)
    flash.data.materials.append(fm)
    for fr, sz in ((1530, 0.0), (1536, 0.3), (1544, 0.4), (1560, 0.0)):
        flash.scale = (sz, sz, sz)
        flash.keyframe_insert('scale', frame=fr)
    register_anchor('bond', '', 'tl', 1525, 1570, lambda fr: siteB)
    bursts = [(1532, 1566, 'bond')]
    # ---- pull out: both cells, both plasmids ----
    lens_key(1600, 55.0)
    lens_key(1680, 40.0)
    cam_key(1680, Vector((36.0, cut_y, -16.0)), 100.0, el=5)
    cam_key(1740, Vector((36.0, cut_y, -16.0)), 100.0, el=5)
    key_state(1620, ['MAT_dna_atoms', 'MAT_enzyme_tem1'], 0.35, 0.5)
    key_state(1700, ['MAT_dna_atoms', 'MAT_enzyme_tem1'], 0.35, 0.5)
    headlines = [(0.5, 3.5, 'THIS ENZYME HAS A NAME'), (4.0, 9.5, 'TEM. ATHENS, 1963.'), (10.5, 12.5, 'NOT FROM THE CHROMOSOME'), (13.5, 17.0, 'A SPARE RING OF DNA. A PASSENGER.'), (20.0, 22.5, 'THE GENE IS READ'), (23.5, 26.0, 'SHIPPED TO THE PERIPLASM'), (27.5, 30.5, 'BACTERIA HAVE SEX'), (32.0, 35.0, 'ONE STRAND CROSSES'), (38.5, 42.0, 'HANDED IT. IN MINUTES.'), (46.5, 49.0, 'SAME DRUG. SAME DOOR.'), (49.5, 52.0, 'RING BROKEN.'), (53.0, 56.5, 'IT NEEDS A GENE THAT TRAVELS')]
    cards = [(1690 / FPS, 1740 / FPS, 'EPISODE 3  -  WHERE IT COMES FROM', 'NEXT: HOW WE FIGHT BACK')]
    END = 1740
    OUT = 'film3_short'
elif MODE == 'wide':
    # extra envelope-only cells left and right so the final pull-back shows a population
    cellC = duplicate_cell(-DX, cname='CellC')
    cellD = duplicate_cell(2 * DX, cname='CellD')
    for n in ('PP_TEM1_a', 'PP_TEM1_b', 'PP_TEM1_c'):
        cellC[n].hide_render = n != 'PP_TEM1_a'           # one enzyme in C (it has the plasmid), none in D
        cellD[n].hide_render = True
    lens_key(1, 35.0)
    WIDE_A = Vector((13.0, cut_y, -4.0))
    # A: cold open on the envelope (ATHENS 1963 drawn by the text layer)
    key_normal(1)
    cam_key(1, WIDE_A, 62.0, el=6)
    cam_key(300, WIDE_A, 54.0, az=-4, el=5)
    # B: the enzyme, then the drop through the inner membrane
    cam_key(360, P(tem.x, tem.z + 0.5), 19.0, az=10, el=6)
    cam_key(520, P(tem.x, tem.z + 0.5), 17.5, az=2, el=4)
    key_state(345, ['MAT_enzyme_tem1'], 0.5, 0.5)
    key_state(520, ['MAT_enzyme_tem1'], 0.5, 0.5)
    key_normal(560)
    register_anchor('tem1', 'TEM-1 BETA-LACTAMASE', 'tl', 370, 505, lambda fr: P(tem.x + 0.5, tem.z + 0.5))
    cam_key(620, Vector((12.0, cut_y, -44.0)), 62.0, az=-3, el=4)
    # C: cytoplasm: chromosome, plasmid, gene
    cam_key(720, Vector((10.0, cut_y, -44.0)), 58.0, az=3, el=5)
    key_state(640, ['MAT_dna_atoms_dim'], 0.1, 0.5)
    key_state(720, ['MAT_dna_atoms_dim'], 0.1, 0.5)
    register_anchor('chrom', 'CHROMOSOME', 'bl', 650, 730, lambda fr: Vector((0.0, DNA_Y, -46.0)))
    cam_key(780, Vector((PLASMID_A.x, cut_y, PLASMID_A.z)), 32.0, az=-6, el=6)
    cam_key(900, Vector((PLASMID_A.x, cut_y, PLASMID_A.z)), 30.0, az=4, el=8)
    key_state(770, ['MAT_dna_atoms'], 0.2, 0.55)
    key_state(900, ['MAT_dna_atoms'], 0.2, 0.55)
    register_anchor('plasmid', 'PLASMID', 'tr', 790, 870, lambda fr: PLASMID_A + Vector((-plA['radius'], 0, 0)))
    gene_glow(plA, {1: 0.0, 860: 0.0, 890: 0.3})
    GENE_PT = PLASMID_A + Vector((plA['radius'] * math.cos(2 * math.pi * 0.135), 0, plA['radius'] * math.sin(2 * math.pi * 0.135)))
    cam_key(960, Vector((GENE_PT.x, cut_y, GENE_PT.z)), 14.0, az=-8, el=10)
    cam_key(1020, Vector((GENE_PT.x, cut_y, GENE_PT.z)), 13.0, az=4, el=12)
    register_anchor('gene', 'THE bla GENE', 'bl', 965, 1015, lambda fr: GENE_PT)
    # D: expression
    newA = nascent_tem1('EP3_tem1_newA')
    start = PLASMID_A + Vector((plA['radius'] + 3.5, 0, 2.0))
    under_im = Vector((30.0, DNA_Y, IM_BOT - 2.5))
    in_im = Vector((30.0, DNA_Y, (IM_TOP + IM_BOT) / 2))
    peri = Vector((30.0, DNA_Y, -12.5))
    loc_key(newA, 1, start, 0.0)
    loc_key(newA, 1040, start, 0.0)
    loc_key(newA, 1080, start, 1.0)
    loc_key(newA, 1110, start, 1.0)
    loc_key(newA, 1230, under_im, 1.0)
    loc_key(newA, 1300, in_im, 1.0)
    loc_key(newA, 1380, peri, 1.0)
    loc_key(newA, 3690, peri, 1.0)
    cam_key(1080, Vector((start.x, cut_y, start.z)), 24.0, az=-6, el=8)
    cam_key(1160, Vector((start.x, cut_y, start.z)), 23.0, az=2, el=8)
    cam_key(1230, Vector((under_im.x, cut_y, under_im.z + 2)), 24.0, az=-4, el=10)
    cam_key(1310, Vector((in_im.x, cut_y, in_im.z + 3)), 22.0, az=4, el=12)
    cam_key(1390, Vector((peri.x, cut_y, peri.z)), 24.0, az=8, el=8)
    cam_key(1470, Vector((peri.x - 2, cut_y, peri.z)), 26.0, az=2, el=8)
    key_state(1060, ['MAT_enzyme_tem1', 'MAT_dna_atoms'], 0.4, 0.6)
    key_state(1290, ['MAT_enzyme_tem1', 'MAT_lipid_IM'], 0.4, 0.6)
    key_state(1400, ['MAT_enzyme_tem1'], 0.4, 0.6)
    register_anchor('new', 'NEW ENZYME', 'tl', 1095, 1165, lambda fr: (sc.frame_set(fr), newA.matrix_world.translation.copy() + TEM_OFF)[1])
    register_anchor('im', 'INNER MEMBRANE', 'tr', 1255, 1325, lambda fr: Vector((36.0, cut_y + 1.5, -19.5)))
    register_anchor('peri', 'PERIPLASM', 'tl', 1395, 1465, lambda fr: Vector((30.0, DNA_Y, -10.0)))
    # E: a neighbour with no enzyme (wide on both cells)
    key_normal(1500)
    cam_key(1540, Vector((42.0, cut_y, -8.0)), 112.0, el=5)
    cam_key(1620, Vector((42.0, cut_y, -6.0)), 108.0, az=-3, el=5)
    register_anchor('cellb', 'NO ENZYME', 'tr', 1560, 1620, lambda fr: Vector((tem.x + DX + 0.5, cut_y, tem.z + 0.5)))
    # F: the pilus, the strand, the copy
    alpha_keys(mats['MAT_pilus'], {1: 0.0, 1640: 0.0, 1680: 1.0})
    cam_key(1700, Vector((38.0, cut_y, 3.0)), 62.0, az=-5, el=6)
    cam_key(1820, Vector((44.0, cut_y, 4.0)), 56.0, az=4, el=4)
    key_state(1690, ['MAT_pilus'], 0.3, 0.5)
    key_state(1820, ['MAT_pilus'], 0.3, 0.5)
    register_anchor('pilus', 'F PILUS (THE SEX PILUS)', 'bl', 1700, 1800, lambda fr: Vector((44.0, cut_y - 1.5, 9.5)))
    path = [tuple(PLASMID_A + Vector((plA['radius'], 0, 0))), (30.0, DNA_Y, -30.0), (27.0, DNA_Y, -6.0), (26.0, DNA_Y, 7.5),
            (40.0, DNA_Y, 7.5), (56.0, DNA_Y, 7.5), (64.0, DNA_Y, 0.0), (74.0, DNA_Y, -20.0), tuple(PLASMID_B + Vector((-plB['radius'], 0, 4.0)))]
    strand = transfer_strand(path)
    dash(strand, 1800, 1960, 0.10)
    cam_key(1900, Vector((60.0, cut_y, -10.0)), 70.0, az=2, el=6)
    cam_key(1980, Vector((PLASMID_B.x, cut_y, PLASMID_B.z)), 32.0, az=-6, el=8)
    cam_key(2080, Vector((PLASMID_B.x, cut_y, PLASMID_B.z)), 30.0, az=4, el=10)
    ring_grow(plB, 1940, 2020)
    gene_glow(plB, {1: 0.0, 2050: 0.0, 2080: 0.3})
    key_state(1940, ['MAT_dna_atoms'], 0.2, 0.55)
    key_state(2080, ['MAT_dna_atoms'], 0.2, 0.55)
    register_anchor('copy', 'THE COPY', 'tr', 1990, 2070, lambda fr: PLASMID_B + Vector((-plB['radius'], 0, 0)))
    # G: handed it: the enzyme is made in B
    newB = nascent_tem1('EP3_tem1_newB')
    startB = start + Vector((DX, 0, 0))
    periB = Vector((tem.x + DX, DNA_Y, tem.z + 0.5))
    loc_key(newB, 1, startB, 0.0)
    loc_key(newB, 2090, startB, 0.0)
    loc_key(newB, 2130, startB, 1.0)
    loc_key(newB, 2200, under_im + Vector((DX, 0, 0)), 1.0)
    loc_key(newB, 2250, in_im + Vector((DX, 0, 0)), 1.0)
    loc_key(newB, 2320, periB, 1.0)
    loc_key(newB, 3690, periB, 1.0)
    cam_key(2200, Vector((startB.x - 2, cut_y, startB.z + 6)), 34.0, az=-4, el=8)
    cam_key(2330, Vector((periB.x, cut_y, periB.z + 3)), 26.0, az=6, el=8)
    cam_key(2380, Vector((periB.x, cut_y, periB.z + 3)), 26.0, az=2, el=8)
    key_state(2110, ['MAT_enzyme_tem1', 'MAT_dna_atoms'], 0.4, 0.6)
    key_state(2330, ['MAT_enzyme_tem1'], 0.4, 0.6)
    # H: same drug, same door, ring broken
    drugB = drug_entry_B(2380, 2520)
    for fr in (2410, 2470, 2520):
        sc.frame_set(fr)
        d = drugB.matrix_world.translation
        cam_key(fr, Vector((d.x, cut_y, d.z)), 26.0, dx=1.5, dz=2.0)
    register_anchor('drug', 'CEFTAZIDIME', 'bl', 2395, 2470, lambda fr: (sc.frame_set(fr), drugB.matrix_world.translation.copy())[1])
    siteB = ligands_B(2530, 2560, 2620)
    cam_key(2560, siteB, 14.0, az=6, el=8)
    cam_key(2640, siteB, 12.5, az=-4, el=10)
    register_anchor('bond', '', 'tl', 2555, 2600, lambda fr: siteB)
    bursts = [(2562, 2596, 'bond')]
    # I: both cells, then the population
    cam_key(2700, Vector((42.0, cut_y, -8.0)), 112.0, el=5)
    cam_key(2900, Vector((42.0, cut_y, -8.0)), 108.0, az=2, el=5)
    lens_key(2900, 35.0)
    lens_key(3200, 30.0)
    cam_key(3200, Vector((42.0, cut_y, -12.0)), 175.0, el=4)
    cam_key(3360, Vector((42.0, cut_y, -12.0)), 180.0, az=-2, el=4)
    cam_key(3690, Vector((42.0, cut_y, -12.0)), 180.0, az=-2, el=4)
    key_state(2660, ['MAT_dna_atoms', 'MAT_enzyme_tem1'], 0.35, 0.45)
    key_state(3360, ['MAT_dna_atoms', 'MAT_enzyme_tem1'], 0.35, 0.45)
    key_state(3400, [], 0.0)
    headlines = [(1.0, 9.5, 'ATHENS, 1963'), (21.5, 24.0, 'NOT FROM THE CHROMOSOME'), (28.0, 33.0, 'A SPARE RING OF DNA'),
                 (34.8, 37.5, 'THE GENE IS READ'), (46.0, 49.0, 'ONE RING, AND THE CELL IS COVERED'),
                 (50.0, 53.5, 'BACTERIA HAVE SEX'), (61.0, 66.0, 'ONE STRAND CROSSES'), (68.0, 72.0, 'HANDED IT. IN MINUTES.'),
                 (79.0, 81.0, 'SAME DRUG. SAME DOOR.'), (83.0, 85.5, 'RING BROKEN. CELL CARRIES ON.'),
                 (88.5, 98.5, 'GONORRHOEA 1976   HAEMOPHILUS 1974   SAME GENE'), (100.5, 111.5, 'ONE SPECIES, ONE COUNTRY: EVERY SPECIES, EVERY COUNTRY'),
                 (113.0, 118.0, 'IT NEEDS A GENE THAT TRAVELS')]
    cards = [(118.5, 127.0, 'EPISODE 3  -  WHERE IT COMES FROM', 'NEXT: HOW WE FIGHT BACK')]   # assembler pads 4 s
    END = 3690
    OUT = 'film3_wide'

else:
    raise SystemExit('MODE must be short or wide')

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
        if os.environ.get('TF_DEBUG'):
            for n in ('Cam_CrossSection', 'CamTarget', 'EP3_tem1_newB', 'Drug_ceftazidime_B', 'EP3_pilus', 'IM_AcrB_B', 'PP_TEM1_b_B', 'Drug_CAZ_docked_B'):
                o = objs.get(n)
                print('POS', fr, n, tuple(round(v, 1) for v in o.matrix_world.translation), 'hide' if o.hide_render else 'show', tuple(round(v, 2) for v in o.scale))
            continue
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
