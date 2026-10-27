"""Real DNA for episode 3: B-DNA (PDB 1BNA, 12 bp) imported with Molecular Nodes, atoms coloured by base
(A orange, T blue, G green, C red, backbone pale), tiled with the right helical twist and bent along a curve.
exec'd by film3.py after ep3_assets.py (needs its `coll`, `material`, `_curve`, `MAT_GENE`, `MAT_DNA`).

 dna_ring(center, count, tag)   plasmid: closed ring, count x 3.74 nm long; dict with 'dna','array','ring','gene'
 dna_ring_grow(pl, f0, f1)      recipient's copy appears repeat by repeat (Array count keyed)
 dna_chromosome(box, tag)       long random-walk path carrying the same unit, dimmed
"""
import bpy, os, math, random
import numpy as np
from mathutils import Vector, Matrix

BASE_COL = {'DA': (0.98, 0.55, 0.20, 1.0), 'DT': (0.35, 0.60, 0.98, 1.0), 'DG': (0.30, 0.80, 0.45, 1.0), 'DC': (0.95, 0.35, 0.40, 1.0)}
BACKBONE_COL = (0.86, 0.88, 0.92, 1.0)
DNA_RISE = 3.74                         # nm between repeats of the 12-mer (11 steps x 0.34)
DNA_TWIST = 12 * 34.3 - 360.0           # extra helical twist of one repeat, degrees
objs = bpy.data.objects


def attr_material(name, emis=0.0, rough=0.45):
    """Principled BSDF whose base colour is the mesh 'Color' attribute (set per atom)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    at = nt.nodes.get('AttrColor') or nt.nodes.new('ShaderNodeAttribute')
    at.name = 'AttrColor'
    at.attribute_name = 'Color'
    nt.links.new(at.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(at.outputs['Color'], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = emis
    b.inputs['Roughness'].default_value = rough
    return m


def _dna_unit(name, mat, dim=1.0, quality=2):
    pdb = os.path.join(BASE, 'pdb', 'dna', '1bna.pdb')
    before = set(objs)
    bpy.ops.mn.import_molecule(method='local', filepath=pdb, file_format='pdb', style='ball_and_stick')
    ob = next(o for o in objs if o not in before and o.type == 'MESH')
    ob.name = name
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    me = ob.data
    # drop the crystal waters (HETATM HOH) so only the DNA is tiled
    sol = me.attributes.get('is_solvent')
    if sol:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        kill = [bm.verts[i] for i, d in enumerate(sol.data) if d.value]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        bm.to_mesh(me)
        bm.free()
    res, bb = [], []
    for line in open(pdb, encoding='utf-8'):
        if line.startswith('ATOM'):
            res.append(line[17:20].strip())
            an = line[12:16].strip()
            bb.append(("'" in an) or an in ('P', 'OP1', 'OP2', 'O1P', 'O2P'))
    col = me.attributes['Color']
    n = min(len(res), len(col.data))
    for i in range(n):
        c = BACKBONE_COL if bb[i] else BASE_COL.get(res[i], BACKBONE_COL)
        col.data[i].color = tuple(ci * dim for ci in c[:3]) + (1.0,)
    co = np.array([v.co for v in me.vertices])
    cen = co.mean(axis=0)
    axis = np.linalg.svd(co - cen)[2][0]
    if axis[2] < 0:
        axis = -axis
    rot = Vector(axis).rotation_difference(Vector((1, 0, 0))).to_matrix().to_4x4()
    me.transform(Matrix.Translation(-Vector(cen)))
    me.transform(rot)
    mod = next(m for m in ob.modifiers if m.type == 'NODES')
    ng = mod.node_group
    style = next(nd for nd in ng.nodes if nd.name.startswith('Style'))
    gi = next(nd for nd in ng.nodes if nd.bl_idname == 'NodeGroupInput')
    for l in list(ng.links):
        if l.to_node == style and l.to_socket.name == 'Atoms':
            ng.links.remove(l)
    ng.links.new(gi.outputs[0], style.inputs['Atoms'])
    style.inputs['Material'].default_value = mat
    # 'Sphere' is a menu (Instance / Mesh / Point Cloud): instances and point clouds are ignored by the
    # Array and Curve modifiers, so the atoms must be realised as mesh
    style.inputs['Sphere'].default_value = 'Mesh'
    style.inputs['Quality'].default_value = quality
    return ob


def _twist_empty(name, rise, twist_deg):
    e = bpy.data.objects.new(name, None)
    coll.objects.link(e)
    e.location = (rise, 0.0, 0.0)
    e.rotation_euler = (math.radians(twist_deg), 0.0, 0.0)
    return e


def dna_along_curve(name, curve_ob, count, mat, dim=1.0, quality=2):
    ob = _dna_unit(name, mat, dim, quality)
    ob.location = curve_ob.location
    ob.rotation_euler = curve_ob.rotation_euler
    e = _twist_empty(name + '_twist', DNA_RISE, DNA_TWIST)
    e.parent = ob                      # the array's object offset is relative to the DNA object
    arr = ob.modifiers.new('Tile', 'ARRAY')
    arr.use_relative_offset = False
    arr.use_constant_offset = False
    arr.use_object_offset = True
    arr.offset_object = e
    arr.count = count
    bend = ob.modifiers.new('Bend', 'CURVE')
    bend.object = curve_ob
    bend.deform_axis = 'POS_X'
    return ob, arr


def dna_ring(center, count=13, mat=None, tag='A', dim=1.0):
    L = count * DNA_RISE
    R = L / (2 * math.pi)
    cu = bpy.data.curves.new('EP3_ring_%s' % tag, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('NURBS')
    npts = 96
    sp.points.add(npts - 1)
    for i, pp in enumerate(sp.points):
        th = 2 * math.pi * i / npts
        pp.co = (R * math.cos(th), 0.0, R * math.sin(th), 1.0)
    sp.use_cyclic_u = True
    sp.order_u = 4
    cu.resolution_u = 6
    circ = bpy.data.objects.new('EP3_ring_%s' % tag, cu)
    circ.location = center
    coll.objects.link(circ)
    ob, arr = dna_along_curve('EP3_plasmidDNA_%s' % tag, circ, count, mat or attr_material('MAT_dna_atoms'), dim)
    cx, cy, cz = center
    gpts = []
    for i in range(60):
        t = 0.05 + 0.17 * i / 59
        th = 2 * math.pi * t
        gpts.append((cx + R * math.cos(th), cy, cz + R * math.sin(th)))
    gob = _curve('EP3_plasmid%s_gene' % tag, gpts, 1.7, MAT_GENE.copy(), kind='NURBS')
    gm = gob.data.materials[0]
    gm.name = 'MAT_gene_%s' % tag
    gb = gm.node_tree.nodes['Principled BSDF']
    gb.inputs['Alpha'].default_value = 0.0
    gb.inputs['Emission Strength'].default_value = 1.2
    gm.surface_render_method = 'BLENDED'
    gm.use_backface_culling = True
    return {'dna': ob, 'array': arr, 'ring': circ, 'gene': gob, 'center': Vector(center), 'radius': R, 'strands': [], 'rungs': None}


def dna_ring_grow(pl, f0, f1):
    arr = pl['array']
    full = arr.count
    for f, c in ((f0, 1), (f1, full)):
        arr.count = c
        arr.keyframe_insert('count', frame=f)
    arr.count = full


def dna_chromosome(box, n_pts=160, step=2.4, count=60, tag='A'):
    (x0, x1), (y0, y1), (z0, z1) = box
    p = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    d = Vector((1, 0, 0))
    pts = []
    for i in range(n_pts):
        d = (d + Vector((random.uniform(-1, 1), random.uniform(-0.3, 0.3), random.uniform(-1, 1))) * 0.8).normalized()
        q = p + d * step
        for k, (lo, hi) in enumerate(((x0, x1), (y0, y1), (z0, z1))):
            if q[k] < lo or q[k] > hi:
                d[k] = -d[k]
                q[k] = min(max(q[k], lo), hi)
        p = q
        pts.append(tuple(p))
    cu = bpy.data.curves.new('EP3_chrpath_%s' % tag, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('NURBS')
    sp.points.add(len(pts) - 1)
    for pp, v in zip(sp.points, pts):
        pp.co = (*v, 1.0)
    sp.order_u = 4
    sp.use_endpoint_u = True
    cu.resolution_u = 8
    path = bpy.data.objects.new('EP3_chrpath_%s' % tag, cu)
    coll.objects.link(path)
    ob, arr = dna_along_curve('EP3_chromDNA_%s' % tag, path, count, attr_material('MAT_dna_atoms_dim', 0.0, 0.7), dim=0.55, quality=1)
    return ob


# ---------------------------------------------------------------- single strand (chain A of 1BNA) for the transfer
def _keep_chain(ob, chain_index):
    """Delete all atoms not in the given chain (0 = A, 1 = B) so the unit becomes one strand."""
    import bmesh
    me = ob.data
    ch = me.attributes['chain_id']
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    kill = [bm.verts[i] for i, d in enumerate(ch.data) if d.value != chain_index]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(me)
    bm.free()


def ss_along_curve(name, curve_ob, count, mat, chain=0, dim=1.0, quality=2):
    """Real single-stranded DNA (one chain of 1BNA) tiled with the helical twist and bent along the curve."""
    ob = _dna_unit(name, mat, dim, quality)
    _keep_chain(ob, chain)
    ob.location = curve_ob.location
    ob.rotation_euler = curve_ob.rotation_euler
    e = _twist_empty(name + '_twist', DNA_RISE, DNA_TWIST)
    e.parent = ob
    arr = ob.modifiers.new('Tile', 'ARRAY')
    arr.use_relative_offset = False
    arr.use_constant_offset = False
    arr.use_object_offset = True
    arr.offset_object = e
    arr.count = count
    bend = ob.modifiers.new('Bend', 'CURVE')
    bend.object = curve_ob
    bend.deform_axis = 'POS_X'
    return ob, arr


def ss_ring(center, count=13, tag='B', chain=0):
    """A plasmid ring made of one strand only (the recipient's copy before synthesis of the second strand)."""
    L = count * DNA_RISE
    R = L / (2 * math.pi)
    cu = bpy.data.curves.new('EP3_ssring_%s' % tag, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('NURBS')
    npts = 96
    sp.points.add(npts - 1)
    for i, pp in enumerate(sp.points):
        th = 2 * math.pi * i / npts
        pp.co = (R * math.cos(th), 0.0, R * math.sin(th), 1.0)
    sp.use_cyclic_u = True
    sp.order_u = 4
    cu.resolution_u = 6
    circ = bpy.data.objects.new('EP3_ssring_%s' % tag, cu)
    circ.location = center
    coll.objects.link(circ)
    ob, arr = ss_along_curve('EP3_ssDNA_%s' % tag, circ, count, attr_material('MAT_dna_atoms'), chain=chain)
    return {'dna': ob, 'array': arr, 'ring': circ, 'center': Vector(center), 'radius': R}


def ss_transfer(points, count, tag='T'):
    """ssDNA along an open NURBS path from donor plasmid to recipient; Array count keyed to 'thread' it."""
    cu = bpy.data.curves.new('EP3_sspath_%s' % tag, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('NURBS')
    sp.points.add(len(points) - 1)
    for pp, v in zip(sp.points, points):
        pp.co = (*v, 1.0)
    sp.order_u = 4
    sp.use_endpoint_u = True
    cu.resolution_u = 12
    path = bpy.data.objects.new('EP3_sspath_%s' % tag, cu)
    coll.objects.link(path)
    ob, arr = ss_along_curve('EP3_ssDNA_%s' % tag, path, count, attr_material('MAT_dna_atoms_bright', 1.5))
    return ob, arr, path


def array_grow(arr, f0, f1, full):
    for f, c in ((f0, 1), (f1, full)):
        arr.count = c
        arr.keyframe_insert('count', frame=f)
    arr.count = full
