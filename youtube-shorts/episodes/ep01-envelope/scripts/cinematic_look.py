"""Cinematic look pass, modelled on reference Shorts (HUD labels anchored to the
object with leader lines, cinematic depth of field, dark graded background).
This script only builds the label system and renders two test stills; it does
not save the .blend unless --save is given.
Run: blender -b blend/gram_negative_base.blend --python episodes/ep01-envelope/scripts/cinematic_look.py -- [--save]
"""
import bpy, math, os, sys
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep01-envelope')
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
FONT = 'C:/Windows/Fonts/segoeuib.ttf'
SAVE = '--save' in sys.argv
sc = bpy.context.scene
objs = bpy.data.objects
cam = objs['Cam_CrossSection']
clip = bpy.data.node_groups['GN_ClipHalfBox']
cut_y = [s.default_value for s in clip.interface.items_tree
         if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y'][0]

# ---------- materials for the HUD ----------
def emissive(name, rgb, strength):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Emission Color'].default_value = (*rgb, 1.0)
    b.inputs['Emission Strength'].default_value = strength
    return m

MAT_TEXT = emissive('MAT_hud_text', (1.0, 1.0, 1.0), 2.5)
MAT_LINE = emissive('MAT_hud_line', (0.85, 0.95, 1.0), 2.0)
MAT_DOT = emissive('MAT_hud_dot', (1.0, 1.0, 1.0), 6.0)

coll = bpy.data.collections.get('HUD')
if not coll:
    coll = bpy.data.collections.new('HUD')
    sc.collection.children.link(coll)
for o in list(coll.objects):
    bpy.data.objects.remove(o, do_unlink=True)

font = bpy.data.fonts.load(FONT) if os.path.exists(FONT) else None


def centroid_world(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return sum(vs, Vector()) / len(vs)


def make_label(name, anchor, text, sub, offset, size=1.6):
    """anchor: world point on the object. offset: where the text sits relative to it (nm)."""
    pos = anchor + Vector(offset)
    # text (title + smaller subtitle), billboarded to the camera
    cu = bpy.data.curves.new('T_' + name, 'FONT')
    cu.body = text
    cu.size = size
    cu.align_x = 'LEFT'
    if font:
        cu.font = font
    cu.extrude = 0.0
    t = bpy.data.objects.new('HUD_' + name, cu)
    coll.objects.link(t)
    t.location = pos
    t.data.materials.append(MAT_TEXT)
    trk = t.constraints.new('TRACK_TO')
    trk.target = cam
    trk.track_axis = 'TRACK_Z'
    trk.up_axis = 'UP_Y'
    if sub:
        cu2 = bpy.data.curves.new('S_' + name, 'FONT')
        cu2.body = sub
        cu2.size = size * 0.55
        if font:
            cu2.font = font
        s = bpy.data.objects.new('HUD_' + name + '_sub', cu2)
        coll.objects.link(s)
        s.parent = t
        s.location = (0.0, -size * 0.9, 0.0)
        s.data.materials.append(MAT_LINE)
    # leader line: anchor -> elbow -> text start, as a thin tube
    lc = bpy.data.curves.new('L_' + name, 'CURVE')
    lc.dimensions = '3D'
    lc.bevel_depth = 0.06
    sp = lc.splines.new('POLY')
    elbow = Vector((pos.x - 0.5, pos.y, pos.z - 0.15))
    pts = [anchor, elbow, Vector((pos.x - 0.2, pos.y, pos.z - 0.15))]
    sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts):
        p.co = (*v, 1.0)
    line = bpy.data.objects.new('HUD_' + name + '_line', lc)
    coll.objects.link(line)
    line.data.materials.append(MAT_LINE)
    # anchor dot
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=anchor, segments=16, ring_count=8)
    dot = bpy.context.active_object
    dot.name = 'HUD_' + name + '_dot'
    for c in list(dot.users_collection):
        c.objects.unlink(dot)
    coll.objects.link(dot)
    dot.data.materials.append(MAT_DOT)
    return t


# ---------- anchors (world nm) ----------
porin = centroid_world(objs['OM_OmpF'])
tem = centroid_world(objs['PP_TEM1_a'])
pbp = centroid_world(objs['IM_PBP1b'])
acrb = centroid_world(objs['IM_AcrB'])
lps_anchor = Vector((porin.x - 7.5, cut_y + 0.5, 13.0))
pg_anchor = Vector((porin.x + 6.0, cut_y + 0.3, -2.4))
im_anchor = Vector((porin.x + 9.0, cut_y + 0.5, -20.0))

make_label('lps', lps_anchor, 'OUTER MEMBRANE', 'LPS + PHOSPHOLIPIDS', (-14.0, 0.0, 5.0))
make_label('porin', Vector((porin.x, cut_y + 0.3, porin.z)), 'PORIN  OmpF', 'THE WAY IN', (6.0, 0.0, 6.5))
make_label('pg', pg_anchor, 'PEPTIDOGLYCAN', 'THE THIN WALL', (5.0, 0.0, 3.0))
make_label('tem1', Vector((tem.x, cut_y + 0.3, tem.z)), 'BETA-LACTAMASE  TEM-1', 'DESTROYS THE DRUG', (-18.0, 0.0, -4.0))
make_label('pbp', Vector((pbp.x, cut_y + 0.3, pbp.z + 2.0)), 'PBP1b', 'THE REAL TARGET', (6.0, 0.0, 4.0))
make_label('acrb', Vector((acrb.x, cut_y + 0.3, acrb.z + 3.0)), 'EFFLUX PUMP  AcrB', 'THROWS DRUGS OUT', (-18.0, 0.0, 6.0))
make_label('im', im_anchor, 'INNER MEMBRANE', '', (5.0, 0.0, -5.0))
print('LABELS', len([o for o in coll.objects if o.type == 'FONT' and not o.parent]))

# ---------- cinematic camera: depth of field + a bit closer ----------
cam.data.dof.use_dof = True
cam.data.dof.focus_object = objs['OM_OmpF']
cam.data.dof.aperture_fstop = 1.2
cam.data.lens = 55

# ---------- darker, graded world ----------
world = sc.world
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.012, 0.018, 0.035, 1.0)
bg.inputs[1].default_value = 1.0

if SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print('SAVED', BLEND)

# ---------- test stills: wide with labels, and a pushed-in frame on the porin ----------
sc.render.resolution_percentage = 50
sc.render.image_settings.media_type = 'IMAGE'
sc.render.image_settings.file_format = 'PNG'
for m in sc.timeline_markers:
    m.camera = None
sc.camera = cam
sc.frame_set(200)
sc.render.filepath = os.path.join(EP, 'renders', 'look_test_wide.png')
bpy.ops.render.render(write_still=True)
print('RENDERED wide')
# push-in: move the camera 45 % of the way toward the porin, keep aiming at it
target = Vector((porin.x, cut_y, porin.z))
cam.location = cam.location + (target - cam.location) * 0.45
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = os.path.join(EP, 'renders', 'look_test_push.png')
bpy.ops.render.render(write_still=True)
print('RENDERED push')
