"""Film 1, cinematic version (reference style: HUD labels anchored to the object,
moving camera with depth of field, dark graded look). Headlines and the title
are burned in afterwards with ffmpeg (assemble_cinematic.py), because
camera-parented 3D text is destroyed by the depth of field.
Two modes, rendered separately and concatenated afterwards:
  tour   : 3 s establishing + 7 components x 5 s + pull-out, drug hidden
  entry  : frames 1-480, the beta-lactam arrives, passes the porin, reaches TEM-1
Usage: blender -b blend/gram_negative_base.blend --python scripts/film1_cinematic.py -- MODE [PCT] [STILLS]
"""
import bpy, os, sys, json, math
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
FONT = 'C:/Windows/Fonts/segoeuib.ttf'
args = sys.argv[sys.argv.index('--') + 1:]
MODE = args[0]
PCT = int(args[1]) if len(args) > 1 else 50
STILLS = [int(x) for x in args[2].split(',')] if len(args) > 2 else None
FPS = 30
LENS = 55.0

sc = bpy.context.scene
objs = bpy.data.objects
cam = objs['Cam_CrossSection']
clip = bpy.data.node_groups['GN_ClipHalfBox']
cut_y = [s.default_value for s in clip.interface.items_tree
         if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y'][0]
font = bpy.data.fonts.load(FONT) if os.path.exists(FONT) else None


def emissive(name, rgb, strength):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Emission Color'].default_value = (*rgb, 1.0)
    b.inputs['Emission Strength'].default_value = strength
    return m


MAT_TEXT = emissive('MAT_hud_text', (1.0, 1.0, 1.0), 2.5)
MAT_SUB = emissive('MAT_hud_sub', (0.75, 0.9, 1.0), 2.2)
MAT_LINE = emissive('MAT_hud_line', (0.85, 0.95, 1.0), 2.0)
MAT_DOT = emissive('MAT_hud_dot', (1.0, 1.0, 1.0), 6.0)

coll = bpy.data.collections.get('HUD')
if not coll:
    coll = bpy.data.collections.new('HUD')
    sc.collection.children.link(coll)
for o in list(coll.objects):
    bpy.data.objects.remove(o, do_unlink=True)


def centroid_world(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return sum(vs, Vector()) / len(vs)


def frame_size(dist):
    """visible height/width (nm) at 'dist' for a 9:16 frame, 36 mm sensor on the long side."""
    H = 2.0 * dist * (18.0 / LENS)
    return H, H * 9.0 / 16.0


def text_obj(name, body, size, mat):
    cu = bpy.data.curves.new('F_' + name, 'FONT')
    cu.body = body
    cu.size = size
    if font:
        cu.font = font
    t = bpy.data.objects.new(name, cu)
    coll.objects.link(t)
    t.data.materials.append(mat)
    return t


def pop(obj, f_in, f_out, rise=10):
    """scale 0 -> 1 at f_in, 1 -> 0 at f_out, applied to the label and its leader/dot."""
    for o in [obj] + list(obj.get('_hud_parts', []) and [objs[n] for n in obj['_hud_parts']]):
        for f, s in ((f_in - 1, 0.0), (f_in + rise, 1.0), (f_out - rise, 1.0), (f_out, 0.0)):
            o.scale = (s, s, s)
            o.keyframe_insert('scale', frame=f)


def make_label(name, anchor, title, sub, target, dist, side='top', align='left', follow=None):
    """Label placed in a free corner of the frame (relative to the camera target at
    distance 'dist'), sized to span <= 80 % of the frame width, with a leader to 'anchor'.
    With follow=<object>, the whole label rides along with that object (world offset kept)."""
    H, W = frame_size(dist)
    if follow is not None:
        # a tag riding on a moving molecule. The molecule travels well in front of the cut
        # plane (closer to the camera than the camera target), so the visible frame around
        # it is small: keep the tag small and centred just below it
        size = 0.55
        pos = anchor + Vector((0.62 * size * len(title) / 2.0, 0.0, -1.6))
    else:
        longest = max(len(title), int(len(sub) * 0.6) if sub else 0)
        size = min(0.80 * W / (0.62 * max(longest, 1)), 0.075 * H)
        tw = 0.62 * size * len(title)
        # the camera sits on +Y looking toward -Y, so screen-right is world -X:
        # text starts at the screen-left edge and runs toward decreasing world x
        x = target.x + 0.44 * W if align == 'left' else target.x - 0.44 * W + tw
        z = target.z + 0.30 * H if side == 'top' else target.z - 0.30 * H
        pos = Vector((x, cut_y + 0.3, z))
    tw = 0.62 * size * len(title)
    t = text_obj('HUD_' + name, title, size, MAT_TEXT)
    t.location = pos
    trk = t.constraints.new('TRACK_TO')
    trk.target = cam
    trk.track_axis = 'TRACK_Z'
    trk.up_axis = 'UP_Y'
    if sub:
        s = text_obj('HUD_' + name + '_sub', sub, size * 0.6, MAT_SUB)
        s.parent = t
        s.location = (0.0, -size * 0.95, 0.0)
    # anchor dot (no rotation of its own, so the leader parented to it stays put)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size * 0.18, location=anchor, segments=16, ring_count=8)
    dot = bpy.context.active_object
    dot.name = 'HUD_' + name + '_dot'
    for c in list(dot.users_collection):
        c.objects.unlink(dot)
    coll.objects.link(dot)
    dot.data.materials.append(MAT_DOT)
    # leader: from the dot to the nearer end of the text baseline, in dot-local coordinates
    if follow is not None:
        end = Vector((0.0, 0.0, pos.z - anchor.z + size * 1.15))      # straight down to the tag
    else:
        end_x = pos.x + size * 0.25 if abs(anchor.x - pos.x) < abs(anchor.x - (pos.x - tw)) else pos.x - tw - size * 0.25
        end = Vector((end_x, pos.y, pos.z - size * 0.15)) - anchor
    lc = bpy.data.curves.new('L_' + name, 'CURVE')
    lc.dimensions = '3D'
    lc.bevel_depth = size * 0.05
    sp = lc.splines.new('POLY')
    sp.points.add(1)
    sp.points[0].co = (0.0, 0.0, 0.0, 1.0)
    sp.points[1].co = (*end, 1.0)
    line = bpy.data.objects.new('HUD_' + name + '_line', lc)
    coll.objects.link(line)
    line.data.materials.append(MAT_LINE)
    line.parent = dot
    if follow is not None:
        for o, off in ((t, pos - anchor), (dot, Vector((0.0, 0.0, 0.0)))):
            cl = o.constraints.new('COPY_LOCATION')
            cl.target = follow
            cl.use_offset = True
            o.location = off
    t['_hud_parts'] = [dot.name, line.name]
    return t


# ---------- camera rig: location keys + Track To an animated target ----------
for c in list(cam.constraints):
    cam.constraints.remove(c)
if cam.animation_data:
    cam.animation_data_clear()
if cam.data.animation_data:
    cam.data.animation_data_clear()
tgt = bpy.data.objects.new('CamTarget', None)
coll.objects.link(tgt)
trk = cam.constraints.new('TRACK_TO')
trk.target = tgt
trk.track_axis = 'TRACK_NEGATIVE_Z'
trk.up_axis = 'UP_Y'
cam.data.lens = LENS
cam.data.dof.use_dof = True
cam.data.dof.focus_object = tgt
cam.data.dof.aperture_fstop = 1.6
bg = sc.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.012, 0.018, 0.035, 1.0)
bg.inputs[1].default_value = 1.0


def cam_key(frame, target, dist, dx=0.0, dz=0.0):
    tgt.location = target
    tgt.keyframe_insert('location', frame=frame)
    cam.location = Vector((target.x + dx, target.y + dist, target.z + dz))
    cam.keyframe_insert('location', frame=frame)


porin = centroid_world(objs['OM_OmpF'])
tem = centroid_world(objs['PP_TEM1_a'])
pbp = centroid_world(objs['IM_PBP1b'])
acrb = centroid_world(objs['IM_AcrB'])
center = Vector((porin.x, cut_y, -3.5))
P = lambda x, z: Vector((x, cut_y + 0.3, z))
headlines = []

if MODE == 'tour':
    for o in objs:
        if o.name.startswith('Drug_') or o.name.startswith('Path_drug'):
            o.hide_render = True
    LEAD, HOLD = 3 * FPS, 5 * FPS
    segs = [  # key, camera target, dist, anchor, title, sub, side, align, headline
        ('om', P(porin.x - 2, 10.5), 32.0, P(porin.x - 7, 13.0), 'OUTER MEMBRANE', 'LPS + PHOSPHOLIPIDS', 'bottom', 'left', None),
        ('porin', P(porin.x, porin.z + 1.5), 21.0, P(porin.x + 0.5, porin.z + 0.5), 'PORIN  OmpF', 'THE WAY IN', 'top', 'left', 'THE ONLY WAY IN'),
        ('pg', P(porin.x + 2, -1.5), 22.0, P(porin.x + 5.0, -2.4), 'PEPTIDOGLYCAN', 'THE THIN WALL', 'top', 'left', None),
        ('tem1', P(tem.x, tem.z + 0.5), 19.0, P(tem.x + 0.5, tem.z + 0.5), 'TEM-1', 'BETA-LACTAMASE', 'top', 'left', 'THIS ENZYME DESTROYS ANTIBIOTICS'),
        ('im', P(porin.x + 4, -19.0), 34.0, P(porin.x + 9, -19.8), 'INNER MEMBRANE', '', 'top', 'right', None),
        # PBP sits screen-left of centre so the label has clear space on the screen-right side
        ('pbp', P(pbp.x - 2.5, pbp.z - 1.0), 30.0, P(pbp.x, pbp.z + 2.0), 'PBP1b', 'THE REAL TARGET', 'top', 'right', 'THE REAL TARGET'),
        ('acrb', P(acrb.x, acrb.z), 38.0, P(acrb.x, acrb.z + 3.0), 'EFFLUX PUMP  AcrB', 'THROWS DRUGS OUT', 'top', 'left', 'AND THIS ONE THROWS THEM OUT'),
    ]
    cam_key(1, center, 72.0, dz=6.0)
    cam_key(LEAD, center, 62.0, dz=5.0)
    f = LEAD + 1
    for key, target, dist, anchor, ttl, sub, side, align, head in segs:
        lab = make_label(key, anchor, ttl, sub, target, dist, side, align)
        pop(lab, f + 8, f + HOLD - 6)
        cam_key(f + 25, target, dist)
        cam_key(f + HOLD, target, dist * 0.94, dx=0.4)
        if head:
            headlines.append(((f + 45) / FPS, (f + HOLD - 8) / FPS, head))
        f += HOLD
    cam_key(f + 40, center, 72.0, dz=6.0)
    END = f + 40
    OUT = 'film1_cin_tour'

elif MODE == 'entry':
    for o in objs:
        if o.name.startswith('Drug_') or o.name.startswith('Path_drug'):
            o.hide_render = o.name.startswith('Path_drug')
    # constant glow, but keep the cross-fades (travel -> docked -> hydrolyzed product)
    fades = {'MAT_drug_travel': {1: 1.0, 470: 1.0, 484: 0.0},
             'MAT_drug_docked': {1: 0.0, 470: 0.0, 484: 1.0, 548: 1.0, 562: 0.0},
             'MAT_drug_product': {1: 0.0, 548: 0.0, 562: 1.0, 700: 1.0, 730: 0.0}}
    # the reaction is filmed close, so the bound forms glow gently and keep their structure visible
    for name, strength in (('MAT_drug_travel', 6.0), ('MAT_drug_docked', 1.6), ('MAT_drug_product', 0.9)):
        mat = bpy.data.materials[name]
        tree = mat.node_tree
        if tree.animation_data:
            tree.animation_data_clear()
        b = tree.nodes['Principled BSDF']
        b.inputs['Emission Strength'].default_value = strength
        a = b.inputs['Alpha']
        for f, v in sorted(fades[name].items()):
            a.default_value = v
            a.keyframe_insert('default_value', frame=f)
    drug = objs['Drug_ceftazidime']
    site = objs['Target_TEM1_site'].matrix_world.translation.copy()
    DIST = 26.0
    cam_key(1, center, 72.0, dz=6.0)
    cam_key(90, Vector((porin.x, cut_y, 12.0)), 40.0, dz=6.0)
    targets = {}
    for fr in (150, 220, 300, 380, 450):
        sc.frame_set(fr)
        d = drug.matrix_world.translation
        targets[fr] = Vector((d.x, cut_y, d.z))
        cam_key(fr, targets[fr], DIST, dx=1.5, dz=2.0)
    # reaction close-up: push in on the active site while the ring is opened, then ease out
    site_t = Vector((site.x, cut_y, site.z))
    cam_key(520, site_t, 17.0, dx=0.8, dz=1.0)
    cam_key(600, site_t, 15.0, dx=0.4, dz=0.8)
    cam_key(690, site_t, 16.0, dx=-0.3, dz=1.2)
    cam_key(740, site_t, 24.0, dx=-1.0, dz=2.5)
    # labels (camera keeps moving: place each for the mid-point of its window)
    sc.frame_set(165)
    lab_d = make_label('drug', drug.matrix_world.translation.copy(), 'CEFTAZIDIME', 'A BETA-LACTAM ANTIBIOTIC',
                       (targets[150] + targets[220]) / 2, DIST, 'bottom', 'right', follow=drug)
    pop(lab_d, 100, 205)       # ends before the porin label's leader crosses it
    mid_p = (targets[220] + targets[300]) / 2
    mid_t = (targets[380] + targets[450]) / 2
    lab_p = make_label('porin', P(porin.x + 0.5, porin.z + 0.5), 'PORIN  OmpF', 'THE WAY IN', mid_p, DIST, 'top', 'left')
    pop(lab_p, 150, 320)
    lab_t = make_label('tem1', P(tem.x + 0.5, tem.z + 0.5), 'TEM-1', 'BETA-LACTAMASE', mid_t, DIST, 'bottom', 'right')
    pop(lab_t, 380, 500)
    headlines = [(20 / FPS, 110 / FPS, 'A BETA-LACTAM ARRIVES'), (200 / FPS, 300 / FPS, 'THROUGH THE PORIN'),
                 (330 / FPS, 450 / FPS, 'INTO THE PERIPLASM'), (500 / FPS, 560 / FPS, 'CAUGHT BY THE ENZYME'),
                 (570 / FPS, 650 / FPS, 'THE BETA-LACTAM RING IS BROKEN'), (660 / FPS, 735 / FPS, 'DESTROYED. NOW HARMLESS.')]
    END = 740
    OUT = 'film1_cin_entry'
else:
    raise SystemExit('MODE must be tour or entry')

with open(os.path.join(BASE, 'render', OUT + '_headlines.json'), 'w', encoding='utf-8') as fh:
    json.dump(headlines, fh, ensure_ascii=False, indent=1)

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
    sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    sc.render.filepath = os.path.join(BASE, 'render', OUT + '.mp4')
    bpy.ops.render.render(animation=True)
    print('RENDER_DONE', sc.render.filepath, 'frames', END)
