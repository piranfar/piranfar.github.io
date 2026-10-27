"""Episode 3 run-time assets (never saved into the base scene). exec'd by film3.py.

 plasmid(center, radius)          stylized double-helix ring (two strands + base-pair rungs) in the x-z plane,
                                  with a highlighted gene arc; returns dict of objects
 chromosome(box, n)               long random-walk tube filling a box, dim material
 pilus(x0, x1, z, y)              F-pilus filament (PDB 5LER) imported with Molecular Nodes, arrayed and laid along x
 duplicate_cell(dx)               copies the envelope collections (OuterMembrane, Periplasm, InnerMembrane) by dx in x
                                  into collection 'CellB' (shared mesh data, same clip); returns {orig_name: copy}
 nascent_tem1(name)               a copy of PP_TEM1_a that can be scaled/moved freely (cytoplasm -> periplasm)
 transfer_strand(points)          a bright single-strand curve whose visible dash is animated with bevel_factor_start/end
All objects go to collection 'EP3' (cleared on re-run) except the duplicated cell ('CellB').
"""
import bpy, os, math, random
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
sc = bpy.context.scene
objs = bpy.data.objects
mats = bpy.data.materials
random.seed(3)


def collection(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


coll = collection('EP3')


def material(name, rgba, emis=0.0, rough=0.4):
    m = mats.get(name) or mats.new(name)
    m.use_nodes = True
    if m.node_tree.animation_data:
        m.node_tree.animation_data_clear()
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Emission Color'].default_value = rgba
    b.inputs['Emission Strength'].default_value = emis
    b.inputs['Roughness'].default_value = rough
    b.inputs['Alpha'].default_value = 1.0
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return m


MAT_DNA = material('MAT_dna', (0.55, 0.70, 0.95, 1.0), 0.0)           # plasmid backbone, pale blue
MAT_RUNG = material('MAT_dna_rung', (0.80, 0.85, 0.95, 1.0), 0.0)
MAT_GENE = material('MAT_gene', (1.0, 0.72, 0.25, 1.0), 0.7)          # bla gene arc, warm glow
MAT_CHROM = material('MAT_chromosome', (0.30, 0.36, 0.52, 1.0), 0.0, 0.7)
MAT_STRAND = material('MAT_strand', (1.0, 0.85, 0.45, 1.0), 4.0)
MAT_PILUS = material('MAT_pilus', (0.80, 0.55, 0.85, 1.0), 0.0)


def _curve(name, pts, bevel, mat, cyclic=False, kind='POLY'):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = bevel
    cu.bevel_resolution = 4
    cu.fill_mode = 'FULL'
    cu.use_fill_caps = True
    sp = cu.splines.new(kind)
    sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts):
        p.co = (v[0], v[1], v[2], 1.0)
    sp.use_cyclic_u = cyclic
    if kind == 'NURBS':
        sp.order_u = 4
        sp.use_endpoint_u = not cyclic
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    cu.materials.append(mat)
    return ob


def plasmid(center, radius=7.0, turns=22, r_helix=0.75, gene=(0.05, 0.22), tag='A'):
    """Double helix wound around a ring in the x-z plane (camera looks along -y). Returns dict."""
    cx, cy, cz = center
    N = 720
    strands = []
    for k, phase in enumerate((0.0, math.pi)):
        pts = []
        for i in range(N):
            t = i / N
            th = 2 * math.pi * t
            ph = 2 * math.pi * turns * t + phase
            rr = radius + r_helix * math.cos(ph)
            pts.append((cx + rr * math.cos(th), cy + r_helix * math.sin(ph), cz + rr * math.sin(th)))
        strands.append(_curve('EP3_plasmid%s_strand%d' % (tag, k), pts, 0.28, MAT_DNA, cyclic=True))
    rungs = []
    for i in range(0, N, 10):
        t = i / N
        th = 2 * math.pi * t
        ph = 2 * math.pi * turns * t
        a = (cx + (radius + r_helix * math.cos(ph)) * math.cos(th), cy + r_helix * math.sin(ph), cz + (radius + r_helix * math.cos(ph)) * math.sin(th))
        b = (cx + (radius - r_helix * math.cos(ph)) * math.cos(th), cy - r_helix * math.sin(ph), cz + (radius - r_helix * math.cos(ph)) * math.sin(th))
        rungs.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2, a, b))
    # all rungs as one curve object with many splines (fast)
    cu = bpy.data.curves.new('EP3_plasmid%s_rungs' % tag, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.12
    cu.bevel_resolution = 2
    cu.fill_mode = 'FULL'
    for _, _, _, a, b in rungs:
        sp = cu.splines.new('POLY')
        sp.points.add(1)
        sp.points[0].co = (*a, 1.0)
        sp.points[1].co = (*b, 1.0)
    rob = bpy.data.objects.new('EP3_plasmid%s_rungs' % tag, cu)
    coll.objects.link(rob)
    cu.materials.append(MAT_RUNG)
    # gene arc: a thicker glowing tube along the ring between gene[0] and gene[1] of the circumference
    g0, g1 = gene
    gpts = []
    for i in range(60):
        t = g0 + (g1 - g0) * i / 59
        th = 2 * math.pi * t
        gpts.append((cx + radius * math.cos(th), cy, cz + radius * math.sin(th)))
    gob = _curve('EP3_plasmid%s_gene' % tag, gpts, 1.0, MAT_GENE.copy(), kind='NURBS')
    gob.data.materials[0].name = 'MAT_gene_%s' % tag
    gob.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.0
    return {'strands': strands, 'rungs': rob, 'gene': gob, 'center': Vector(center), 'radius': radius}


def ring_grow(pl, f0, f1):
    """Draw the plasmid ring progressively (used when the recipient completes its copy)."""
    for ob in pl['strands']:
        cu = ob.data
        cu.use_fill_caps = True
        # bevel factor animation needs a non-cyclic spline: re-create as open
        sp = cu.splines[0]
        sp.use_cyclic_u = False
        for f, v in ((f0, 0.0), (f1, 1.0)):
            cu.bevel_factor_end = v
            cu.keyframe_insert('bevel_factor_end', frame=f)
    rob = pl['rungs']
    for f, s in ((f0, 0.0), (f1 - 1, 0.0), (f1, 1.0)):
        rob.scale = (s, s, s)
        rob.keyframe_insert('scale', frame=f)
    # rungs appear with the ring: scale from the ring centre is wrong, so instead fade them in at the end
    rob.location = (0, 0, 0)


def gene_glow(pl, keys):
    """keys: {frame: alpha} for the gene arc (0 hidden .. 1 bright)."""
    a = pl['gene'].data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Alpha']
    for f, v in sorted(keys.items()):
        a.default_value = v
        a.keyframe_insert('default_value', frame=f)


def chromosome(box, n=420, step=1.6, bevel=0.55, tag='A'):
    """Random walk confined to box=((x0,x1),(y0,y1),(z0,z1)); smoothed NURBS tube."""
    (x0, x1), (y0, y1), (z0, z1) = box
    p = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    d = Vector((1, 0, 0))
    pts = []
    for i in range(n):
        d = (d + Vector((random.uniform(-1, 1), random.uniform(-0.35, 0.35), random.uniform(-1, 1))) * 0.9).normalized()
        q = p + d * step
        # bounce off the walls
        for k, (lo, hi) in enumerate(((x0, x1), (y0, y1), (z0, z1))):
            if q[k] < lo or q[k] > hi:
                d[k] = -d[k]
                q[k] = min(max(q[k], lo), hi)
        p = q
        pts.append(tuple(p))
    return _curve('EP3_chromosome_%s' % tag, pts, bevel, MAT_CHROM, kind='NURBS')


def pilus(x0, x1, z, y, copies=None):
    """Import the F-pilus (5LER), lay it along +x from x0 to x1 at height z, depth y. Returns the object."""
    before = set(objs)
    bpy.ops.mn.import_molecule(method='local', filepath=os.path.join(BASE, 'pdb', 'pilus', '5LER.cif'),
                               file_format='cif', style='cartoon')
    ob = next(o for o in objs if o not in before and o.type == 'MESH')
    ob.name = 'EP3_pilus'
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    # the filament axis is z (3.1..26.9), centred at x,y ~ 7: rotate so the axis lies along +x
    seg = 26.9 - 3.1 - 0.6                                     # slight overlap hides the joint
    ob.rotation_euler = (0.0, math.radians(90.0), 0.0)          # z -> +x
    n = copies or int(math.ceil((x1 - x0) / seg))
    arr = ob.modifiers.new('Along', 'ARRAY')
    arr.use_relative_offset = False
    arr.use_constant_offset = True
    arr.constant_offset_displace = (0.0, 0.0, seg)        # local z = world +x after the rotation
    arr.count = n
    ob.modifiers.move(ob.modifiers.find(arr.name), 0)
    # after rotation the local z axis points to +x and local x to -z; place the start at x0
    ob.location = (x0 - 3.1, y - 7.05, z + 7.0)
    m = MAT_PILUS
    for mod in ob.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            for node in mod.node_group.nodes:
                for inp in node.inputs:
                    if inp.name == 'Material' and hasattr(inp, 'default_value'):
                        inp.default_value = m
    return ob


def duplicate_cell(dx, names=('OuterMembrane', 'Periplasm', 'InnerMembrane'), cname='CellB'):
    cb = collection(cname)
    mapping = {}
    for cname in names:
        for o in list(bpy.data.collections[cname].objects):
            c = o.copy()
            c.name = o.name + '_' + cname[-1]
            c.location.x += dx
            cb.objects.link(c)
            mapping[o.name] = c
    # parented children (ligands on TEM-1) keep their parent: re-point to the copies
    for o, c in mapping.items():
        if c.parent and c.parent.name in mapping:
            c.parent = mapping[c.parent.name]
            c.location.x -= dx                      # the parent already carries the offset
    return mapping


def nascent_tem1(name='EP3_tem1_new', src='PP_TEM1_a'):
    o = objs[src].copy()
    o.name = name
    o.animation_data_clear()
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    o.parent = None
    return o


def transfer_strand(points, bevel=0.35):
    ob = _curve('EP3_transfer', points, bevel, MAT_STRAND, kind='NURBS')
    ob.data.bevel_factor_start = 0.0
    ob.data.bevel_factor_end = 0.0
    return ob


def dash(ob, f0, f1, length=0.12):
    """A short bright dash runs from start to end of the curve between f0 and f1."""
    cu = ob.data
    for f, s, e in ((f0, 0.0, 0.0), (f0 + int((f1 - f0) * length), 0.0, length), (f1 - int((f1 - f0) * length), 1.0 - length, 1.0), (f1, 1.0, 1.0)):
        cu.bevel_factor_start = s
        cu.bevel_factor_end = e
        cu.keyframe_insert('bevel_factor_start', frame=f)
        cu.keyframe_insert('bevel_factor_end', frame=f)
