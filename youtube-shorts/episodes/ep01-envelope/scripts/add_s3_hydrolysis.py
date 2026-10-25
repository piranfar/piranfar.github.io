"""S3: arrival at TEM-1 and hydrolysis of the beta-lactam ring.
Ligand poses come from KPC-2/5UJ3 superposed onto the TEM-1 MD frame
(pdb/ligands/*_in_tem1.pdb, TEM-1 local frame):
 - frames 1-450   the travelling ceftazidime follows its path to the pocket entrance
 - 450-480        it slides into the pocket and cross-fades into the docked intact pose
 - 540-580        docked intact pose cross-fades into the hydrolyzed (ring-opened) product
 - 620-700        the product drifts out of the active site and fades
 - Cam_S3_enzyme  tracks the active site (marker 'S3 periplasm' -> this camera)
Run: blender -b blend/gram_negative_base.blend --python episodes/ep01-envelope/scripts/add_s3_hydrolysis.py
"""
import bpy, math, os
from mathutils import Vector, Matrix

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep01-envelope')
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
LIG = os.path.join(BASE, 'pdb', 'ligands')
SITE_A = Vector((48.62, 64.35, 25.55))       # TEM-1 frame, Angstrom (from transfer_pose.py)
ENTR_A = Vector((41.32, 69.23, 20.76))
PREVIEW = (420, 680)

sc = bpy.context.scene
objs = bpy.data.objects
clip = bpy.data.node_groups['GN_ClipHalfBox']
tem = objs['PP_TEM1_a']
drug = objs['Drug_ceftazidime']
path = objs['Path_drug_1']
coll = bpy.data.collections['Drugs']

site_w = tem.matrix_world @ (SITE_A * 0.1)
entr_w = tem.matrix_world @ (ENTR_A * 0.1)
out_dir = (entr_w - site_w).normalized()
print('SITE_W', tuple(round(v, 2) for v in site_w), 'OUT', tuple(round(v, 2) for v in out_dir))


def material(name, rgba):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = 0.35
    try:
        mat.surface_render_method = 'BLENDED'
    except Exception:
        mat.blend_method = 'BLEND'
    return mat


def assign_mn_material(obj, mat):
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group and mod.node_group is not clip:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = mat


def fade(mat, keys):
    """keys: {frame: alpha}"""
    a = mat.node_tree.nodes['Principled BSDF'].inputs['Alpha']
    for f, v in sorted(keys.items()):
        a.default_value = v
        a.keyframe_insert('default_value', frame=f)


def import_ligand(fn, name, mat):
    if objs.get(name):
        bpy.data.objects.remove(objs[name], do_unlink=True)
    before = set(objs)
    bpy.ops.mn.import_molecule(method='local', filepath=os.path.join(LIG, fn),
                               file_format='pdb', style='ball_and_stick')
    o = next(x for x in objs if x not in before and x.type == 'MESH')
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    assign_mn_material(o, mat)
    o.parent = tem                        # same local frame as the TEM-1 MD structure
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.location = (0, 0, 0)
    o.rotation_euler = (0, 0, 0)
    return o


# ---------- materials ----------
red = (0.98, 0.30, 0.20, 1.0)
m_travel = material('MAT_drug_travel', red)
m_docked = material('MAT_drug_docked', red)
m_product = material('MAT_drug_product', (0.75, 0.45, 0.25, 1.0))   # duller: inactive product
assign_mn_material(drug, m_travel)

# ---------- path end -> pocket entrance ----------
bps = path.data.splines[0].bezier_points
bps[-2].co = entr_w + out_dir * 2.5 + Vector((0.0, 0.0, 1.0))
bps[-1].co = entr_w
for bp in (bps[-2], bps[-1]):
    bp.handle_left_type = bp.handle_right_type = 'AUTO'

# ---------- travelling drug: slide in, then hand over ----------
con = drug.constraints['Follow Path']
con.influence = 1.0; con.keyframe_insert('influence', frame=450)
con.influence = 0.0; con.keyframe_insert('influence', frame=480)
drug.location = entr_w; drug.keyframe_insert('location', frame=450)
drug.location = site_w; drug.keyframe_insert('location', frame=480)
fade(m_travel, {1: 1.0, 465: 1.0, 485: 0.0})

docked = import_ligand('ceftazidime_docked_in_tem1.pdb', 'Drug_CAZ_docked', m_docked)
fade(m_docked, {1: 0.0, 465: 0.0, 485: 1.0, 540: 1.0, 580: 0.0})

product = import_ligand('cefotaxime_hydrolyzed_in_tem1.pdb', 'Drug_product_hydrolyzed', m_product)
fade(m_product, {1: 0.0, 540: 0.0, 580: 1.0, 700: 1.0, 730: 0.0})
# release: drift out of the site (local frame of TEM-1, nm)
out_local = (tem.matrix_world.to_3x3().inverted() @ out_dir).normalized()
product.location = (0, 0, 0); product.keyframe_insert('location', frame=620)
product.location = out_local * 3.0 + Vector((0.0, 0.0, 0.8)); product.keyframe_insert('location', frame=730)
product.rotation_euler = (0, 0, 0); product.keyframe_insert('rotation_euler', frame=620)
product.rotation_euler = (0.6, -0.4, 0.9); product.keyframe_insert('rotation_euler', frame=730)
print('LIGANDS', docked.name, len(docked.data.vertices), product.name, len(product.data.vertices))

# ---------- Cam_S3_enzyme ----------
for n in ('Cam_S3_enzyme', 'Target_TEM1_site'):
    if objs.get(n):
        bpy.data.objects.remove(objs[n], do_unlink=True)
tgt = bpy.data.objects.new('Target_TEM1_site', None)
sc.collection.objects.link(tgt)
tgt.parent = tem; tgt.matrix_parent_inverse = Matrix.Identity(4)
tgt.location = SITE_A * 0.1
cam_d = bpy.data.cameras.new('Cam_S3_enzyme'); cam_d.lens = 60
cam = bpy.data.objects.new('Cam_S3_enzyme', cam_d)
sc.collection.objects.link(cam)
trk = cam.constraints.new('TRACK_TO'); trk.target = tgt
trk.track_axis = 'TRACK_NEGATIVE_Z'; trk.up_axis = 'UP_Y'
# camera stays below the outer membrane (z < 3) and in front of the cut plane (+y),
# approaching the pocket from the side it opens toward (-x)
for f, off in ((400, (-9.0, 6.0, 2.0)), (480, (-5.5, 3.5, 1.2)), (600, (-5.0, 3.0, 0.8)), (720, (-7.0, 5.0, 1.5))):
    cam.location = site_w + Vector(off)
    cam.keyframe_insert('location', frame=f)
for m in sc.timeline_markers:
    if m.name == 'S3 periplasm':
        m.camera = cam
print('CAM_S3 bound to marker S3')

# ---------- preview output ----------
sc.frame_start, sc.frame_end = PREVIEW
sc.render.resolution_percentage = 50
sc.render.image_settings.media_type = 'VIDEO'
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
sc.render.filepath = os.path.join(EP, 'renders', 'preview_S3_hydrolysis.mp4')
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)

# quick stills to check framing before the long render
sc.render.image_settings.media_type = 'IMAGE'
sc.render.image_settings.file_format = 'PNG'
for f in (430, 500, 600, 690):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(EP, 'renders', 's3_check_f%03d.png' % f)
    bpy.ops.render.render(write_still=True)
    print('RENDERED', f, sc.camera.name)
