"""Episode 3 v2 beats, exec'd by film3.py after ep3_assets.py, ep3_dna.py and look.py.
Needs from the film namespace: sc, objs, mats, coll (EP3), cut_y, DNA_Y, DX, IM_TOP, IM_BOT, cellB, material(),
_curve(), alpha_keys(), loc_key(), nascent_tem1(), dash(), ss_transfer(), ss_ring(), array_grow(), attr_material(),
to_surface(), bake_static(), jitter(), crowding(), densify_pg().

 add_sec(x, y)                         SecYEG (OPM 5AWW) in the inner membrane at x; returns (object, mouth_cyto, mouth_peri)
 add_ribosome(loc)                     70S ribosome (4V9D assembly 1) as a baked surface; returns object
 express(f_mrna0, f_mrna1, f_chain0, f_chain1, f_fold0, f_fold1, gene_pt, ribo_exit, sec, dest, tem_new)
                                       mRNA dash gene->ribosome, unfolded chain threads through Sec, cartoon folds at dest
 retract(root, pilus, f0, f1, dx)      cell B (parented to root) slides by dx while the pilus shortens to stay attached
 ss_transfer_beat(path_pts, f0, f1, ring_center, f_ring0, f_ring1, f_ds0, f_ds1, pl_ds)
                                       ssDNA threads along path, ss ring grows in B, ds ring fades in (pl_ds) as ss fades
"""
import bpy, os, math
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
MAT_SEC = material('MAT_sec', (0.62, 0.78, 0.70, 1.0), 0.0)
MAT_CHAIN = material('MAT_chain', (0.98, 0.62, 0.70, 1.0), 1.2)          # unfolded TEM-1: same rose, brighter
MAT_MRNA = material('MAT_mrna', (1.0, 0.82, 0.35, 1.0), 2.0)


def _import(path, name, style, mat):
    before = set(objs)
    fmt = 'pdb' if path.endswith('.pdb') else 'cif'
    bpy.ops.mn.import_molecule(method='local', filepath=path, file_format=fmt, style=style)
    ob = next(o for o in objs if o not in before and o.type == 'MESH')
    ob.name = name
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    mod = next(m for m in ob.modifiers if m.type == 'NODES')
    ng = mod.node_group
    st = next(n for n in ng.nodes if n.name.startswith('Style'))
    gi = next(n for n in ng.nodes if n.bl_idname == 'NodeGroupInput')
    for l in list(ng.links):
        if l.to_node == st and l.to_socket.name == 'Atoms':
            ng.links.remove(l)
    ng.links.new(gi.outputs[0], st.inputs['Atoms'])
    for i in st.inputs:
        if i.name == 'Material':
            i.default_value = mat
    return ob, st


def add_sec(x, y):
    ob, st = _import(os.path.join(BASE, 'pdb', 'sec', '5aww_opm_clean.pdb'), 'EP3_SecYEG', 'cartoon', MAT_SEC)
    zc = (IM_TOP + IM_BOT) / 2.0
    ob.location = (x, y, zc + 0.6)                      # OPM frame: z = membrane normal, cytoplasmic loops at -z
    ob.rotation_euler = (0.0, 0.0, math.radians(90.0))   # turn so the lateral gate faces the camera side
    return ob, Vector((x, y, IM_BOT - 1.5)), Vector((x, y, IM_TOP + 1.2))


def add_ribosome(loc):
    ob, st = _import(os.path.join(BASE, 'pdb', 'ribosome', '4v9d_asm1.cif'), 'EP3_ribosome', 'surface',
                     material('MAT_ribosome', (0.26, 0.24, 0.38, 1.0), 0.0, 0.72))
    st.inputs['Quality'].default_value = 2
    st.inputs['Color Source'].default_value = 'Alpha Carbon'
    baked = bake_static(ob)
    baked.name = 'EP3_ribosome_baked'
    baked.location = loc
    baked.rotation_euler = (0.0, math.radians(20.0), math.radians(-30.0))
    baked.scale = (0.85, 0.85, 0.85)
    return baked


def _tube(name, pts, radius, mat):
    ob = _curve(name, pts, radius, mat, kind='NURBS')
    ob.data.bevel_resolution = 4
    ob.data.resolution_u = 16
    ob.data.bevel_factor_start = 0.0
    ob.data.bevel_factor_end = 0.0
    return ob


def express(f_mrna0, f_mrna1, f_chain0, f_chain1, f_fold0, f_fold1, gene_pt, ribo_exit, sec, dest, tem_new, tag='A'):
    """gene_pt: point on the plasmid; ribo_exit: polypeptide exit; sec: (obj, mouth_cyto, mouth_peri); dest: fold position."""
    sec_ob, m_cyto, m_peri = sec
    # mRNA: a short dash from the gene to the ribosome
    mid = (Vector(gene_pt) + Vector(ribo_exit)) / 2 + Vector((0, 0, 3.0))
    mrna = _tube('EP3_mRNA_%s' % tag, [tuple(gene_pt), tuple(mid), tuple(ribo_exit)], 0.14, MAT_MRNA)
    dash(mrna, f_mrna0, f_mrna1, 0.35)
    # polypeptide: ribosome exit -> Sec cytoplasmic mouth -> channel -> periplasmic mouth -> fold site
    pts = [tuple(ribo_exit), tuple((Vector(ribo_exit) + m_cyto) / 2 + Vector((0, 0, -1.0))), tuple(m_cyto),
           tuple((m_cyto + m_peri) / 2), tuple(m_peri), tuple(Vector(dest) + Vector((0, 0, -2.0))), tuple(dest)]
    chain = _tube('EP3_chain_%s' % tag, pts, 0.17, MAT_CHAIN)
    cu = chain.data
    # head threads through (end 0->1), then the tail follows (start 0->1) as the protein folds at dest
    for f, s, e in ((f_chain0, 0.0, 0.0), (f_chain1, 0.0, 1.0), (f_fold0, 0.0, 1.0), (f_fold1, 1.0, 1.0)):
        cu.bevel_factor_start = s
        cu.bevel_factor_end = e
        cu.keyframe_insert('bevel_factor_start', frame=f)
        cu.keyframe_insert('bevel_factor_end', frame=f)
    # the folded enzyme grows at dest while the chain is drawn in
    loc_key(tem_new, 1, dest, 0.0)
    loc_key(tem_new, f_fold0 - 1, dest, 0.0)
    loc_key(tem_new, f_fold0, dest, 0.15)
    loc_key(tem_new, f_fold1, dest, 1.0)
    return mrna, chain


def retract(root, pilus, f0, f1, dx):
    """Cell B (everything parented to root) slides by dx (negative = toward A); pilus shortens so the tip stays on B."""
    root.location = (0.0, 0.0, 0.0)
    root.keyframe_insert('location', frame=f0)
    root.location = (dx, 0.0, 0.0)
    root.keyframe_insert('location', frame=f1)
    full = pilus.scale.z
    # pilus local z is world +x (rotated 90 about y); its start stays at x0, so scale z shrinks the length
    L0 = 2 * (26.9 - 3.1 - 0.6)
    pilus.scale = (1.0, 1.0, full)
    pilus.keyframe_insert('scale', frame=f0)
    pilus.scale = (1.0, 1.0, full * (L0 + dx) / L0)
    pilus.keyframe_insert('scale', frame=f1)


def ss_transfer_beat(path_pts, f0, f1, ring_center, f_ring0, f_ring1, f_ds0, f_ds1, pl_ds, count=16, tag='B'):
    ss, arr, path = ss_transfer(path_pts, count, tag='T' + tag)
    array_grow(arr, f0, f1, count)
    # the strand is only visible while it is in transit; afterwards it is 'inside' the recipient (ring grows there)
    m = ss.data.materials[0] if ss.data.materials else None
    ring = ss_ring(ring_center, tag=tag)
    array_grow(ring['array'], f_ring0, f_ring1, ring['array'].count)
    # second strand: the full ds ring fades in, the ss ring fades out
    ds_mat = attr_material('MAT_dna_atoms_' + tag)
    ds_st = next(n for n in next(mm for mm in pl_ds['dna'].modifiers if mm.type == 'NODES').node_group.nodes if n.name.startswith('Style'))
    ds_st.inputs['Material'].default_value = ds_mat
    for mm in (ds_mat, ss.data.materials and None):
        pass
    try:
        ds_mat.surface_render_method = 'BLENDED'
    except Exception:
        pass
    alpha_keys(ds_mat, {1: 0.0, f_ds0: 0.0, f_ds1: 1.0})
    ss_mat = attr_material('MAT_dna_atoms_ss_' + tag)
    ss_st = next(n for n in next(mm for mm in ring['dna'].modifiers if mm.type == 'NODES').node_group.nodes if n.name.startswith('Style'))
    ss_st.inputs['Material'].default_value = ss_mat
    try:
        ss_mat.surface_render_method = 'BLENDED'
    except Exception:
        pass
    alpha_keys(ss_mat, {1: 1.0, f_ds0: 1.0, f_ds1: 0.0})
    # transit strand hides once it has arrived
    for f, v in ((1, 1.0), (f1 + 10, 1.0), (f1 + 25, 0.0)):
        ss.hide_render = False
    tr_mat = attr_material('MAT_dna_atoms_bright')
    try:
        tr_mat.surface_render_method = 'BLENDED'
    except Exception:
        pass
    alpha_keys(tr_mat, {1: 0.0, f0 - 5: 0.0, f0: 1.0, f1 + 10: 1.0, f1 + 30: 0.0})
    return ss, path, ring


def head_point(path_pts, frac):
    """Approximate position along the polyline at fraction frac (for the 5' label anchor)."""
    pts = [Vector(p) for p in path_pts]
    segs = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(segs)
    d = max(0.0, min(1.0, frac)) * total
    for i, L in enumerate(segs):
        if d <= L or i == len(segs) - 1:
            return pts[i] + (pts[i + 1] - pts[i]) * (d / L if L else 0)
        d -= L
    return pts[-1]
