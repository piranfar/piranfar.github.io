"""Layer 2 of gram_negative_base.blend: the periplasm.
 - tiles the outer membrane 3x along X using the periodic box vector (seamless)
 - adds a stylized single-layer peptidoglycan mesh (glycan strands + peptide
   cross-links, curve tubes) ~6 nm below the OM inner leaflet
 - adds three copies of the MD-equilibrated TEM-1 beta-lactamase floating in
   the periplasm
 - applies the same cross-section clip to the new layers and re-frames the camera
Run: blender -b blend/gram_negative_base.blend --python scripts/add_periplasm.py
Units: 1 Blender unit = 1 nm (Molecular Nodes default).
"""
import bpy, math, os, random
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
OUT = os.path.join(BASE, 'render', 'base_scene_periplasm_test.png')
TEM1_PDB = os.path.join(BASE, 'traj', 'tem1', 'tem1_t10ns.pdb')

BOX_X = 11.3615            # CHARMM-GUI box vector A (nm): periodic tiling offset
OM_BOTTOM_Z = 3.6          # lowest phospholipid atom of the OM (nm, from the t5ns frame)
PG_Z = OM_BOTTOM_Z - 6.0   # peptidoglycan plane (Lpp tether is ~8 nm; PG sits just under it)
PALETTE = {
    'enzyme_tem1': (0.85, 0.27, 0.38, 1.0),   # rose red
    'pg_glycan':   (0.55, 0.72, 0.40, 1.0),   # green
    'pg_peptide':  (0.80, 0.86, 0.65, 1.0),   # pale green
}
random.seed(7)

sc = bpy.context.scene
clip = bpy.data.node_groups['GN_ClipHalfBox']
cut_y = [s.default_value for s in clip.interface.items_tree
         if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y'][0]


def material(name, rgba, rough=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = rough
    return mat


def assign_mn_material(obj, mat):
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group and mod.node_group is not clip:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = mat


def add_clip(obj, index=None):
    mod = obj.modifiers.new('ClipHalfBox', 'NODES')
    mod.node_group = clip
    if index is not None:
        with bpy.context.temp_override(object=obj):
            bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=index)
    return mod


def add_tiling(obj):
    """Array along X by the periodic box vector; placed first in the stack."""
    mod = obj.modifiers.new('TileBox', 'ARRAY')
    mod.count = 3
    mod.use_relative_offset = False
    mod.use_constant_offset = True
    mod.constant_offset_displace = (BOX_X, 0.0, 0.0)
    with bpy.context.temp_override(object=obj):
        bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=0)
    obj.location.x -= BOX_X          # tiles at -1, 0, +1 so the original stays centred


def collection(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
    return c


# ---------- 1) tile the outer membrane ----------
for name in ('OM_OmpF', 'OM_LPS', 'OM_lipids'):
    add_tiling(bpy.data.objects[name])
    print('TILED', name)

# ---------- 2) peptidoglycan ----------
coll_pp = collection('Periplasm')
x0, x1 = -1.0 - BOX_X, 12.7 + BOX_X      # span the tiled membrane
y0, y1 = -1.0, 12.7
STRAND_GAP = 2.0      # nm between glycan strands (along Y)
XLINK_GAP = 2.0       # nm between peptide cross-links (along X)


def new_curve(name, radius, mat):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.fill_mode = 'FULL'
    ob = bpy.data.objects.new(name, cu)
    coll_pp.objects.link(ob)
    cu.materials.append(mat)
    return ob, cu


def poly(cu, pts):
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, (x, y, z) in zip(sp.points, pts):
        p.co = (x, y, z, 1.0)


gly_ob, gly = new_curve('PG_glycan', 0.30, material('MAT_pg_glycan', PALETTE['pg_glycan']))
pep_ob, pep = new_curve('PG_peptide', 0.13, material('MAT_pg_peptide', PALETTE['pg_peptide']))

ys = []
y = y0
while y <= y1:
    ys.append(y)
    y += STRAND_GAP * random.uniform(0.85, 1.15)

strands = []
for yi in ys:
    pts = []
    x = x0
    phase = random.uniform(0, 6.28)
    while x <= x1:
        # gentle waviness in Y and Z so strands read as organic, not drawn with a ruler
        pts.append((x, yi + 0.25 * math.sin(0.9 * x + phase), PG_Z + 0.2 * math.sin(1.3 * x + phase)))
        x += 0.5
    # occasional strand breaks (real sacculi have gaps)
    if random.random() < 0.25:
        cut = random.randint(6, len(pts) - 6)
        poly(gly, pts[:cut]); poly(gly, pts[cut + 3:])
    else:
        poly(gly, pts)
    strands.append(pts)

# peptide cross-links between neighbouring strands
for i in range(len(strands) - 1):
    a, b = strands[i], strands[i + 1]
    x = x0 + random.uniform(0, XLINK_GAP)
    while x <= x1:
        k = min(range(len(a)), key=lambda j: abs(a[j][0] - x))
        if random.random() < 0.7:   # ~70 % of possible sites are cross-linked
            pa, pb = a[k], b[min(k, len(b) - 1)]
            poly(pep, [pa, ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, PG_Z + 0.35), pb])
        x += XLINK_GAP
for ob in (gly_ob, pep_ob):
    add_clip(ob)
print('PG_STRANDS', len(strands), 'XLINKS', len(pep.splines))

# ---------- 3) TEM-1 copies ----------
before = set(bpy.data.objects)
bpy.ops.mn.import_molecule(method='local', filepath=TEM1_PDB, file_format='pdb', style='cartoon')
tem = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
tem.name = 'PP_TEM1_a'
for c in list(tem.users_collection):
    c.objects.unlink(tem)
coll_pp.objects.link(tem)
assign_mn_material(tem, material('MAT_enzyme_tem1', PALETTE['enzyme_tem1']))
vs = [v.co for v in tem.data.vertices]
c0 = sum(vs, Vector()) / len(vs)
print('TEM1_ATOMS', len(vs), 'centroid', tuple(round(x, 2) for x in c0))

# positions (nm): in front of the cut face so they are visible, at different depths
placements = [
    ((2.5, cut_y + 2.0, OM_BOTTOM_Z - 2.8), (0.3, 0.9, 0.4)),
    ((9.0, cut_y + 3.5, PG_Z - 3.2),        (1.4, 0.2, 2.1)),
    ((15.5, cut_y + 1.5, OM_BOTTOM_Z - 3.5), (2.2, 1.1, 0.8)),
]
copies = [tem]
for i, (pos, rot) in enumerate(placements):
    ob = tem if i == 0 else tem.copy()
    if ob is not tem:
        ob.name = 'PP_TEM1_%s' % 'abc'[i]
        coll_pp.objects.link(ob)
    ob.rotation_euler = rot
    # rotate about the molecule centroid, then place the centroid at pos
    from mathutils import Euler
    R = Euler(rot).to_matrix()
    ob.location = Vector(pos) - R @ c0
    copies.append(ob)
print('TEM1_COPIES', [o.name for o in copies[1:]])

# ---------- 4) camera re-frame (vertical) ----------
cam = bpy.data.objects['Cam_CrossSection']
target = Vector((5.8, cut_y, 3.0))
dist = 46.0
cam.location = target + Vector((0.0, dist, 9.0))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
fill = bpy.data.objects.get('Fill')
if fill:
    fill.location = target + Vector((-20.0, 30.0, 18.0))
    fill.rotation_euler = (target - fill.location).to_track_quat('-Z', 'Y').to_euler()
    fill.data.energy = 6000
    fill.data.size = 25

# ---------- save + test render ----------
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('RENDER_DONE', OUT)
