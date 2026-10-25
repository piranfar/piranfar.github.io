"""Episode 2 wall mechanics, added at run time (never saved to the base scene).

 build_wall(f0, f1)      new glycan strands grow out of PBP1b and cross-link into
                         the existing mesh (curve bevel_factor_end keyed 0 -> 1,
                         peptide stubs pop in behind the growing tip)
 stop_wall(f)            growth freezes at frame f (keys are clamped)
 open_gap(f0, f1, r)     a sphere around the PBP's patch of wall deletes glycan and
                         peptide geometry with radius keyed 0 -> r  (geometry nodes,
                         driven by an empty so no modifier properties are keyed)
 bulge_membrane(f0, f1, a) inner-membrane lipids are pushed upward through the gap
                         with a gaussian bump of amplitude keyed 0 -> a nm

All geometry lives in collection 'EP2' and is removed on re-run.
Standalone test:  blender -b blend/gram_negative_base.blend --python episodes/ep02-hit-the-wall/scripts/wall_mechanics.py -- 100,220,330,430
"""
import bpy, sys, os, math, random
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
EP = os.path.join(BASE, 'episodes', 'ep02-hit-the-wall')
sc = bpy.context.scene
objs = bpy.data.objects
PG_Z = -2.4
random.seed(11)


def centroid_world(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return sum(vs, Vector()) / len(vs)


def collection(name='EP2'):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


coll = collection()
pbp = objs['IM_PBP1b']
pbp_c = centroid_world(pbp)
clip = bpy.data.node_groups['GN_ClipHalfBox']
cut_y = [s.default_value for s in clip.interface.items_tree
         if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Cut Y'][0]
# the TP domain top of PBP1b, where new wall is handed to the mesh
pbp_top = Vector((pbp_c.x, cut_y - 1.0, max((pbp.matrix_world @ v.co).z for v in pbp.data.vertices) - 1.0))


def mat_of(name):
    return bpy.data.materials[name]


def fresh_material(i, f_grow_start, f_grow_end):
    """new wall material: brighter, slightly emissive while growing, settling to the old wall colour."""
    old = bpy.data.materials['MAT_pg_glycan']
    m = old.copy()
    m.name = 'MAT_pg_fresh_%d' % i
    b = m.node_tree.nodes['Principled BSDF']
    base = tuple(old.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)
    bright = (min(1.0, base[0] * 0.9), min(1.0, base[1] * 1.25), min(1.0, base[2] * 0.6), 1.0)
    b.inputs['Emission Color'].default_value = bright
    for f, col, em in ((f_grow_start, bright, 0.9), (f_grow_end, bright, 0.9), (f_grow_end + 40, base, 0.0)):
        b.inputs['Base Color'].default_value = col
        b.inputs['Base Color'].keyframe_insert('default_value', frame=f)
        b.inputs['Emission Strength'].default_value = em
        b.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
    return m


# ---------------------------------------------------------------- 1) building
STRAND_LEN = 11.0
X0 = pbp_c.x - 1.2                      # new material leaves the PBP on its screen-right side
STOP_FRAC = 0.42                        # the last strand is frozen at this fraction of its length
WALL_C = Vector((X0 - STRAND_LEN * STOP_FRAC, cut_y - 1.2, PG_Z))   # where growth stops = where the wall fails


def build_wall(f0, f1, n_strands=3, stagger=36):
    """Horizontal strands in the wall plane, growing from the PBP toward screen-right,
    each cross-linked to the older strand behind it with visible peptide bridges."""
    grown = []
    for i in range(n_strands):
        y = cut_y - 0.4 - 1.5 * i          # in front of the old mesh, behind the cut plane
        z = PG_Z + 0.15 * i
        cu = bpy.data.curves.new('EP2_newstrand_%d' % i, 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = 0.30
        cu.bevel_resolution = 3
        cu.fill_mode = 'FULL'
        cu.use_fill_caps = True
        sp = cu.splines.new('NURBS')
        pts = []
        for k in range(24):
            t = k / 23.0
            pts.append((X0 - STRAND_LEN * t, y + 0.18 * math.sin(2.2 * STRAND_LEN * t + i), z + 0.15 * math.sin(1.7 * STRAND_LEN * t + 2 * i)))
        sp.points.add(len(pts) - 1)
        for p, v in zip(sp.points, pts):
            p.co = (*v, 1.0)
        sp.use_endpoint_u = True
        sp.order_u = 4
        ob = bpy.data.objects.new('EP2_newstrand_%d' % i, cu)
        coll.objects.link(ob)
        fa = f0 + stagger * i
        cu.materials.append(fresh_material(i, fa, f1 + stagger * i))
        for f, v in ((fa, 0.0), (f1 + stagger * i, 1.0)):
            cu.bevel_factor_end = v
            cu.keyframe_insert('bevel_factor_end', frame=f)
        grown.append((ob, pts, fa, f1 + stagger * i))
        # peptide bridges to the strand behind (old mesh for i == 0), popping in behind the tip
        for k in range(3, len(pts) - 1, 4):
            x, yy, zz = pts[k]
            lc = bpy.data.curves.new('EP2_pep_%d_%d' % (i, k), 'CURVE')
            lc.dimensions = '3D'
            lc.bevel_depth = 0.17
            lc.use_fill_caps = True
            s2 = lc.splines.new('POLY')
            s2.points.add(2)
            s2.points[0].co = (x, yy, zz, 1.0)
            s2.points[1].co = (x + 0.15, yy - 0.75, zz + 0.45, 1.0)
            s2.points[2].co = (x + 0.3, yy - 1.5, zz, 1.0)
            pob = bpy.data.objects.new('EP2_pep_%d_%d' % (i, k), lc)
            coll.objects.link(pob)
            lc.materials.append(mat_of('MAT_pg_peptide'))
            t_k = k / (len(pts) - 1)
            fk = fa + int((f1 - f0) * t_k) + 8
            for f, sc_ in ((fk - 1, 0.0), (fk + 7, 1.0)):
                pob.scale = (sc_, sc_, sc_)
                pob.keyframe_insert('scale', frame=f)
    return grown


def stop_wall(grown, f_stop):
    """freeze growth at f_stop; bridges scheduled after it never appear."""
    for ob, pts, fa, fb in grown:
        cu = ob.data
        if not cu.animation_data:
            continue
        sc.frame_set(f_stop)
        v = cu.bevel_factor_end
        cu.animation_data_clear()
        cu.bevel_factor_end = 0.0
        cu.keyframe_insert('bevel_factor_end', frame=fa)
        cu.bevel_factor_end = v
        cu.keyframe_insert('bevel_factor_end', frame=min(f_stop, fb))
        cu.keyframe_insert('bevel_factor_end', frame=f_stop + 600)
        if fb > f_stop:                      # interrupted strand: stays bright, never settles
            m = cu.materials[0]
            m.node_tree.animation_data_clear()
            b = m.node_tree.nodes['Principled BSDF']
            b.inputs['Base Color'].default_value = tuple(b.inputs['Emission Color'].default_value)
            b.inputs['Emission Strength'].default_value = 0.9
    for ob in coll.objects:
        if ob.name.startswith('EP2_pep_') and ob.animation_data:
            sc.frame_set(f_stop)
            if ob.scale.x < 0.99:
                ob.animation_data_clear()
                ob.scale = (0, 0, 0)


# ---------------------------------------------------------------- 2) gap
def _ctl(name, loc):
    e = bpy.data.objects.new(name, None)
    coll.objects.link(e)
    e.location = loc
    e.scale = (0.001, 0.001, 0.001)
    return e


def _gap_group(ctl):
    g = bpy.data.node_groups.get('GN_EP2_Gap')
    if g:
        bpy.data.node_groups.remove(g)
    g = bpy.data.node_groups.new('GN_EP2_Gap', 'GeometryNodeTree')
    g.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    g.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n_in, n_out = g.nodes.new('NodeGroupInput'), g.nodes.new('NodeGroupOutput')
    info = g.nodes.new('GeometryNodeObjectInfo')
    info.transform_space = 'RELATIVE'
    info.inputs['Object'].default_value = ctl        # Blender 5.2: modifier inputs cannot be set from Python, so the control object is wired inside the group
    pos = g.nodes.new('GeometryNodeInputPosition')
    dist = g.nodes.new('ShaderNodeVectorMath'); dist.operation = 'DISTANCE'
    sep = g.nodes.new('ShaderNodeSeparateXYZ')
    cmp = g.nodes.new('FunctionNodeCompare'); cmp.operation = 'LESS_THAN'
    dele = g.nodes.new('GeometryNodeDeleteGeometry'); dele.domain = 'POINT'
    L = g.links
    L.new(pos.outputs['Position'], dist.inputs[0])
    L.new(info.outputs['Location'], dist.inputs[1])
    L.new(info.outputs['Scale'], sep.inputs['Vector'])
    L.new(dist.outputs['Value'], cmp.inputs[0])
    L.new(sep.outputs['X'], cmp.inputs[1])           # radius = control scale.x
    L.new(n_in.outputs['Geometry'], dele.inputs['Geometry'])
    L.new(cmp.outputs['Result'], dele.inputs['Selection'])
    L.new(dele.outputs['Geometry'], n_out.inputs['Geometry'])
    return g


def open_gap(f0, f1, radius=5.0, targets=('PG_glycan', 'PG_peptide')):
    ctl = _ctl('EP2_GapCtl', WALL_C)
    for f, r in ((f0, 0.001), (f1, radius)):
        ctl.scale = (r, r, r)
        ctl.keyframe_insert('scale', frame=f)
    g = _gap_group(ctl)
    for name in targets + tuple(o.name for o in coll.objects if o.name.startswith('EP2_newstrand') or o.name.startswith('EP2_pep')):
        ob = objs.get(name)
        if not ob:
            continue
        m = ob.modifiers.new('EP2_Gap', 'NODES')
        m.node_group = g
        with bpy.context.temp_override(object=ob):
            bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)
    return ctl


# ---------------------------------------------------------------- 3) bulge
def _bulge_group(ctl):
    g = bpy.data.node_groups.get('GN_EP2_Bulge')
    if g:
        bpy.data.node_groups.remove(g)
    g = bpy.data.node_groups.new('GN_EP2_Bulge', 'GeometryNodeTree')
    g.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    g.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n_in, n_out = g.nodes.new('NodeGroupInput'), g.nodes.new('NodeGroupOutput')
    info = g.nodes.new('GeometryNodeObjectInfo'); info.transform_space = 'RELATIVE'
    info.inputs['Object'].default_value = ctl
    pos = g.nodes.new('GeometryNodeInputPosition')
    # horizontal distance only (x, y) so the whole column of lipids rises together
    sep_p = g.nodes.new('ShaderNodeSeparateXYZ'); sep_c = g.nodes.new('ShaderNodeSeparateXYZ')
    sep_s = g.nodes.new('ShaderNodeSeparateXYZ')
    dx = g.nodes.new('ShaderNodeMath'); dx.operation = 'SUBTRACT'
    dy = g.nodes.new('ShaderNodeMath'); dy.operation = 'SUBTRACT'
    dx2 = g.nodes.new('ShaderNodeMath'); dx2.operation = 'MULTIPLY'
    dy2 = g.nodes.new('ShaderNodeMath'); dy2.operation = 'MULTIPLY'
    add = g.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
    sig2 = g.nodes.new('ShaderNodeMath'); sig2.operation = 'MULTIPLY'      # sigma^2 = scale.y^2
    div = g.nodes.new('ShaderNodeMath'); div.operation = 'DIVIDE'
    neg = g.nodes.new('ShaderNodeMath'); neg.operation = 'MULTIPLY'; neg.inputs[1].default_value = -1.0
    ex = g.nodes.new('ShaderNodeMath'); ex.operation = 'EXPONENT'
    amp = g.nodes.new('ShaderNodeMath'); amp.operation = 'MULTIPLY'       # * scale.z (amplitude)
    comb = g.nodes.new('ShaderNodeCombineXYZ')
    setp = g.nodes.new('GeometryNodeSetPosition')
    L = g.links
    L.new(pos.outputs['Position'], sep_p.inputs['Vector'])
    L.new(info.outputs['Location'], sep_c.inputs['Vector'])
    L.new(info.outputs['Scale'], sep_s.inputs['Vector'])
    L.new(sep_p.outputs['X'], dx.inputs[0]); L.new(sep_c.outputs['X'], dx.inputs[1])
    L.new(sep_p.outputs['Y'], dy.inputs[0]); L.new(sep_c.outputs['Y'], dy.inputs[1])
    L.new(dx.outputs[0], dx2.inputs[0]); L.new(dx.outputs[0], dx2.inputs[1])
    L.new(dy.outputs[0], dy2.inputs[0]); L.new(dy.outputs[0], dy2.inputs[1])
    L.new(dx2.outputs[0], add.inputs[0]); L.new(dy2.outputs[0], add.inputs[1])
    L.new(sep_s.outputs['Y'], sig2.inputs[0]); L.new(sep_s.outputs['Y'], sig2.inputs[1])
    L.new(add.outputs[0], div.inputs[0]); L.new(sig2.outputs[0], div.inputs[1])
    L.new(div.outputs[0], neg.inputs[0])
    L.new(neg.outputs[0], ex.inputs[0])
    L.new(ex.outputs[0], amp.inputs[0]); L.new(sep_s.outputs['Z'], amp.inputs[1])
    L.new(amp.outputs[0], comb.inputs['Z'])
    L.new(n_in.outputs['Geometry'], setp.inputs['Geometry'])
    L.new(comb.outputs['Vector'], setp.inputs['Offset'])
    L.new(setp.outputs['Geometry'], n_out.inputs['Geometry'])
    return g


def bulge_membrane(f0, f1, amplitude=3.5, sigma=4.5, targets=('IM_lipids', 'IM_lipids_fill')):
    ctl = _ctl('EP2_BulgeCtl', Vector((WALL_C.x, WALL_C.y, -19.9)))
    for f, a in ((f0, 0.001), (f1, amplitude)):
        ctl.scale = (1.0, sigma, a)
        ctl.keyframe_insert('scale', frame=f)
    g = _bulge_group(ctl)
    for name in targets:
        ob = objs.get(name)
        if not ob:
            continue
        m = ob.modifiers.new('EP2_Bulge', 'NODES')
        m.node_group = g
        # after the tiling/clip, before the Molecular Nodes style
        idx = [i for i, mm in enumerate(ob.modifiers) if mm.name == 'Molecular Nodes']
        if idx:
            with bpy.context.temp_override(object=ob):
                bpy.ops.object.modifier_move_to_index(modifier=m.name, index=idx[0])
    return ctl


# ---------------------------------------------------------------- standalone test
if __name__ == '__main__' and '--' in sys.argv:
    arg = sys.argv[sys.argv.index('--') + 1]
    stills = None if arg == 'anim' else [int(x) for x in arg.split(',')]
    grown = build_wall(30, 130)          # strands start at 30, 66, 102; each takes 100 frames
    stop_wall(grown, 150)                # the third strand freezes less than half-way
    open_gap(170, 260, radius=5.0)
    bulge_membrane(200, 290, amplitude=5.0, sigma=4.0)
    for o in objs:
        if o.name.startswith('Drug_') or o.name.startswith('Path_drug') or o.name.startswith('PP_TEM1'):
            o.hide_render = True             # episode 2: no beta-lactamase in this cell
    cam = objs['Cam_CrossSection']
    for c in list(cam.constraints):
        cam.constraints.remove(c)
    if cam.animation_data:
        cam.animation_data_clear()
    cam.data.dof.use_dof = False
    # the wall is a plane: look down on it (~28 deg) or it is edge-on and unreadable
    target = Vector((WALL_C.x + 1.5, cut_y - 1.0, PG_Z - 4.0))
    cam.location = target + Vector((2.0, 24.0, 13.0))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for m in sc.timeline_markers:
        m.camera = None
    sc.camera = cam
    sc.render.resolution_percentage = 50
    sc.render.image_settings.media_type = 'IMAGE'
    sc.render.image_settings.file_format = 'PNG'
    os.makedirs(os.path.join(EP, 'renders'), exist_ok=True)
    if stills:
        for fr in stills:
            sc.frame_set(fr)
            sc.render.filepath = os.path.join(EP, 'renders', 'wall_f%04d.png' % fr)
            bpy.ops.render.render(write_still=True)
            print('STILL', fr)
    else:
        sc.frame_start, sc.frame_end = 20, 300
        sc.render.image_settings.media_type = 'VIDEO'
        sc.render.image_settings.file_format = 'FFMPEG'
        sc.render.ffmpeg.format = 'MPEG4'
        sc.render.ffmpeg.codec = 'H264'
        sc.render.filepath = os.path.join(EP, 'renders', 'wall_mechanics_preview.mp4')
        bpy.ops.render.render(animation=True)
        print('RENDER_DONE')
