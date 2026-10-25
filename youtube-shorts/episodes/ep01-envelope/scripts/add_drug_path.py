"""Shot scaffold: a ceftazidime molecule travelling along a path on the timeline.
 - imports the drug (ball-and-stick) into collection 'Drugs'
 - builds a Bezier path: outside the cell -> through an OmpF pore -> periplasm
   -> TEM-1 copy 'a'
 - Follow Path constraint, path evaluated over frames 1..450 (S1 approach +
   S2 porin + arrival at the enzyme in S3), with a slow tumble
 - renders four preview stills (frames 1, 150, 300, 450) at half resolution
Run: blender -b blend/gram_negative_base.blend --python episodes/ep01-envelope/scripts/add_drug_path.py
"""
import bpy, math, os
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep01-envelope')
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
DRUG_PDB = os.path.join(BASE, 'pdb', 'ligands', 'ceftazidime_CAZ.pdb')
PREVIEW = os.path.join(EP, 'renders', 'drug_path_f%03d.png')
PATH_FRAMES = (1, 450)
PALETTE = {'drug_cephalosporin': (0.98, 0.30, 0.20, 1.0)}   # vivid red-orange

sc = bpy.context.scene
objs = bpy.data.objects
clip = bpy.data.node_groups['GN_ClipHalfBox']
cut_y = [s.default_value for s in clip.interface.items_tree
         if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y'][0]


def centroid(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return sum(vs, Vector()) / len(vs)


def material(name, rgba):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = 0.35
    return mat


def assign_mn_material(obj, mat):
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group and mod.node_group is not clip:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = mat


coll = bpy.data.collections.get('Drugs')
if not coll:
    coll = bpy.data.collections.new('Drugs')
    sc.collection.children.link(coll)
for name in ('Drug_ceftazidime', 'Path_drug_1'):
    if objs.get(name):
        bpy.data.objects.remove(objs[name], do_unlink=True)

# ---------- landmarks ----------
porin = centroid(objs['OM_OmpF'])                 # trimer centre, scene nm
tem1 = centroid(objs['PP_TEM1_a'])
pore = porin + Vector((1.8, 0.0, 0.0))            # one of the three channels sits ~1.8 nm off-centre
print('PORIN', tuple(round(v, 2) for v in porin), 'TEM1', tuple(round(v, 2) for v in tem1))

# ---------- drug ----------
before = set(objs)
bpy.ops.mn.import_molecule(method='local', filepath=DRUG_PDB, file_format='pdb', style='ball_and_stick')
drug = next(o for o in objs if o not in before and o.type == 'MESH')
drug.name = 'Drug_ceftazidime'
for c in list(drug.users_collection):
    c.objects.unlink(drug)
coll.objects.link(drug)
assign_mn_material(drug, material('MAT_drug_cephalosporin', PALETTE['drug_cephalosporin']))
# centre the molecule on its own origin so the path drives its centre
c0 = sum((v.co for v in drug.data.vertices), Vector()) / len(drug.data.vertices)
for v in drug.data.vertices:
    v.co -= c0
print('DRUG_ATOMS', len(drug.data.vertices))

# ---------- path ----------
cu = bpy.data.curves.new('Path_drug_1', 'CURVE')
cu.dimensions = '3D'
cu.use_path = True
cu.path_duration = PATH_FRAMES[1] - PATH_FRAMES[0]
sp = cu.splines.new('BEZIER')
waypoints = [
    pore + Vector((-6.0, 2.0, 16.0)),    # far outside, above the O-antigen
    pore + Vector((-2.0, 1.0, 9.0)),     # sinking through the LPS brush
    pore + Vector((0.0, 0.3, 3.5)),      # entering the pore (extracellular mouth)
    pore + Vector((0.0, 0.3, -3.5)),     # leaving the pore (periplasmic side)
    tem1 + Vector((3.0, 0.5, 2.5)),      # drifting toward the enzyme
    tem1 + Vector((0.0, 0.0, 0.0)),      # at the enzyme
]
sp.bezier_points.add(len(waypoints) - 1)
for bp, p in zip(sp.bezier_points, waypoints):
    bp.co = p
    bp.handle_left_type = bp.handle_right_type = 'AUTO'
path = bpy.data.objects.new('Path_drug_1', cu)
coll.objects.link(path)
path.hide_render = True

con = drug.constraints.new('FOLLOW_PATH')
con.target = path
con.use_curve_follow = False
con.forward_axis = 'FORWARD_Y'
# animate the curve's evaluation time
cu.eval_time = 0.0
cu.keyframe_insert('eval_time', frame=PATH_FRAMES[0])
cu.eval_time = float(cu.path_duration)
cu.keyframe_insert('eval_time', frame=PATH_FRAMES[1])
# slow tumble (default Bezier easing is fine; Blender 5 actions are slotted, so
# the old action.fcurves access is not available here)
drug.rotation_euler = (0.0, 0.0, 0.0)
drug.keyframe_insert('rotation_euler', frame=PATH_FRAMES[0])
drug.rotation_euler = (math.radians(540), math.radians(360), math.radians(720))
drug.keyframe_insert('rotation_euler', frame=PATH_FRAMES[1])
print('PATH_OK', len(waypoints), 'waypoints, frames', PATH_FRAMES)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)

# ---------- preview stills ----------
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = 'PNG'
for f in (1, 150, 300, 450):
    sc.frame_set(f)
    sc.render.filepath = PREVIEW % f
    bpy.ops.render.render(write_still=True)
    print('RENDERED', f, tuple(round(v, 2) for v in drug.matrix_world.translation))
