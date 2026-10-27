"""Shared cinematic look, applied at run time by the film scripts (never saved to the base scene).

 apply_look(volume=True, jitter=True)
   - colour management AgX, Medium High Contrast, exposure +0.15
   - three-point light: warm key (sun), soft fill, cyan rim from behind/below the inner membrane
   - lipids: subsurface weight 0.18, warm radius; proteins: AO darkens roughness in cavities
   - world: weak volume scatter (density 0.012, anisotropy 0.3) for a liquid medium
   - EEVEE: raytracing on, shadows on, volumetric samples 32
 jitter(obj, amp_nm, rot_deg, seed)   Brownian noise on location/rotation via f-curve noise modifiers
 ease_camera(cam, target_empty)       smooth in/out on every camera and target key (Bezier, auto-clamped,
                                      with a gentle ease)
exec'd into the film script namespace: exec(open(LOOK).read(), {'__name__': 'look', 'bpy': bpy})
"""
import bpy, math, random, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in globals() else os.path.join('E:' + os.sep, 'Github Project', 'piranfar.github.io', 'youtube-shorts')
from mathutils import Vector

sc = bpy.context.scene
objs = bpy.data.objects
mats = bpy.data.materials


def _principled(m):
    return m.node_tree.nodes.get('Principled BSDF')


def colour_management():
    vs = sc.view_settings
    try:
        vs.view_transform = 'AgX'
        vs.look = 'AgX - Medium High Contrast'
    except Exception:
        vs.view_transform = 'AgX'
    vs.exposure = 0.15
    vs.gamma = 1.0


def lights():
    key = objs.get('Key')
    if key:
        key.data.energy = 3.4
        key.data.color = (1.0, 0.93, 0.84)          # warm key
        key.data.angle = math.radians(4.0)
    fill = objs.get('Fill')
    if fill:
        fill.data.energy = 8000.0
        fill.data.color = (0.85, 0.9, 1.0)
        fill.data.size = 40.0
    rim = objs.get('Rim')
    if not rim:
        d = bpy.data.lights.new('Rim', 'AREA')
        rim = objs.new('Rim', d)
        sc.collection.objects.link(rim)
    rim.data.shape = 'RECTANGLE'
    rim.data.size, rim.data.size_y = 90.0, 30.0
    rim.data.energy = 26000.0
    rim.data.color = (0.45, 0.8, 1.0)               # cyan rim
    rim.location = (6.0, -28.0, -26.0)              # behind the scene (camera is at +y), below the inner membrane
    rim.rotation_euler = (math.radians(-55.0), 0.0, 0.0)   # pointing up-forward toward the camera side
    kick = objs.get('Kick')
    if not kick:
        d = bpy.data.lights.new('Kick', 'AREA')
        kick = objs.new('Kick', d)
        sc.collection.objects.link(kick)
    kick.data.size = 30.0
    kick.data.energy = 9000.0
    kick.data.color = (0.55, 0.85, 1.0)
    kick.location = (40.0, -18.0, 18.0)             # top-back right, outlines the LPS and porins
    kick.rotation_euler = (math.radians(-125.0), 0.0, math.radians(20.0))


def materials():
    for n in ('MAT_lipid', 'MAT_lipid_IM', 'MAT_lps'):
        m = mats.get(n)
        if not m:
            continue
        b = _principled(m)
        b.inputs['Subsurface Weight'].default_value = 0.18
        b.inputs['Subsurface Radius'].default_value = (1.0, 0.45, 0.25)
        b.inputs['Subsurface Scale'].default_value = 0.6
        b.inputs['Roughness'].default_value = 0.55
        b.inputs['Specular IOR Level'].default_value = 0.35
    for n in ('MAT_enzyme_tem1', 'MAT_target_pbp1b', 'MAT_pump_acrb', 'MAT_protein_porin', 'MAT_pg_glycan', 'MAT_pg_peptide'):
        m = mats.get(n)
        if not m:
            continue
        nt = m.node_tree
        b = _principled(m)
        if nt.nodes.get('AO'):
            continue
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
        ao.name = 'AO'
        ao.samples = 8
        ao.inputs['Distance'].default_value = 1.6
        ramp = nt.nodes.new('ShaderNodeMapRange')
        ramp.name = 'AO_rough'
        ramp.inputs['From Min'].default_value = 0.0
        ramp.inputs['From Max'].default_value = 1.0
        ramp.inputs['To Min'].default_value = 0.9        # cavities: rougher, darker
        ramp.inputs['To Max'].default_value = 0.38
        nt.links.new(ao.outputs['AO'], ramp.inputs['Value'])
        nt.links.new(ramp.outputs['Result'], b.inputs['Roughness'])
        # (base colour left unlinked so the film scripts can keyframe it)


def world_volume(density=0.003, anisotropy=0.3):
    nt = sc.world.node_tree
    out = nt.nodes['World Output']
    vol = nt.nodes.get('Volume Scatter') or nt.nodes.new('ShaderNodeVolumeScatter')
    vol.inputs['Density'].default_value = density
    vol.inputs['Anisotropy'].default_value = anisotropy
    vol.inputs['Color'].default_value = (0.55, 0.7, 0.9, 1.0)
    nt.links.new(vol.outputs['Volume'], out.inputs['Volume'])
    sc.eevee.volumetric_tile_size = '8'
    sc.eevee.volumetric_samples = 32
    sc.eevee.use_volumetric_shadows = False
    sc.eevee.volumetric_start = 2.0
    sc.eevee.volumetric_end = 260.0


def eevee():
    try:
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
        sc.eevee.shadow_ray_count = 2
        sc.eevee.shadow_step_count = 4
    except Exception:
        pass


def apply_look(volume=True):
    colour_management()
    lights()
    materials()
    eevee()
    if volume:
        world_volume()


def jitter(ob, amp_nm=0.25, rot_deg=1.5, seed=0, scale=18.0):
    """Brownian wobble: noise f-modifiers on location and rotation. Keys must exist (adds a static key if none)."""
    if not ob.animation_data or not ob.animation_data.action:
        ob.keyframe_insert('location', frame=1)
        ob.keyframe_insert('rotation_euler', frame=1)
    act = ob.animation_data.action
    try:
        fcs = list(act.fcurves)
    except AttributeError:                       # slotted actions (Blender 4.4+)
        fcs = []
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    fcs += list(cb.fcurves)
    for fc in fcs:
        if fc.data_path not in ('location', 'rotation_euler'):
            continue
        if any(m.type == 'NOISE' for m in fc.modifiers):
            continue
        n = fc.modifiers.new('NOISE')
        n.scale = scale
        n.strength = amp_nm * 2 if fc.data_path == 'location' else math.radians(rot_deg) * 2
        n.phase = seed * 7.3 + fc.array_index * 11.1
        n.depth = 1


def ease_camera(cam, tgt):
    """Smooth in/out: all location keys on the camera and its target get Bezier + AUTO_CLAMPED handles and
    ease-in-out via the easing property; keeps stops crisp but motion continuous."""
    for ob in (cam, tgt, cam.data):
        if not ob.animation_data or not ob.animation_data.action:
            continue
        act = ob.animation_data.action
        try:
            fcs = list(act.fcurves)
        except AttributeError:
            fcs = []
            for layer in act.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        fcs += list(cb.fcurves)
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
                kp.easing = 'EASE_IN_OUT'


# ---------------------------------------------------------------- scene-level extras (run time only)
def densify_pg(every=1.0, radius=0.12, jitter_nm=0.15, name='PG_peptide_extra'):
    """Extra peptide cross-links between neighbouring glycan strands so the sacculus reads as a mesh.
    Reads PG_glycan's splines (one per strand, ordered along y) and bridges each pair every `every` nm in x."""
    gly = objs.get('PG_glycan')
    if not gly or objs.get(name):
        return None
    sp = [[Vector(p.co[:3]) for p in s.points] for s in gly.data.splines]
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    cu.fill_mode = 'FULL'
    rnd = random.Random(5)
    n = 0
    for a, b in zip(sp, sp[1:]):
        if not a or not b:
            continue
        x0 = max(min(p.x for p in a), min(p.x for p in b))
        x1 = min(max(p.x for p in a), max(p.x for p in b))
        x = x0 + rnd.uniform(0, every)
        while x < x1:
            pa = min(a, key=lambda p: abs(p.x - x))
            pb = min(b, key=lambda p: abs(p.x - x))
            if (pa - pb).length < 4.0:
                s2 = cu.splines.new('POLY')
                s2.points.add(2)
                mid = (pa + pb) / 2 + Vector((rnd.uniform(-jitter_nm, jitter_nm), 0, rnd.uniform(-jitter_nm, jitter_nm) * 2))
                s2.points[0].co = (*pa, 1.0)
                s2.points[1].co = (*mid, 1.0)
                s2.points[2].co = (*pb, 1.0)
                n += 1
            x += every
    ob = objs.new(name, cu)
    gly.users_collection[0].objects.link(ob)
    ob.matrix_world = gly.matrix_world.copy()
    cu.materials.append(mats['MAT_pg_peptide'])
    for m in gly.modifiers:
        if m.type == 'NODES' and m.node_group and m.node_group.name == 'GN_ClipHalfBox':
            mm = ob.modifiers.new('ClipHalfBox', 'NODES')
            mm.node_group = m.node_group
    print('PG_EXTRA_LINKS', n)
    return ob


def crowding(box, n=50, r=(0.45, 1.1), seed=1, name='Crowd', color=(0.30, 0.34, 0.46, 1.0), alpha=0.28):
    """Out-of-focus 'molecular crowding': low-poly blobs instanced in a box behind the cut plane,
    dim and translucent, never in the hero plane. box = ((x0,x1),(y0,y1),(z0,z1))."""
    if objs.get(name):
        return objs[name]
    rnd = random.Random(seed)
    m = mats.get('MAT_crowd') or mats.new('MAT_crowd')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = 0.7
    b.inputs['Alpha'].default_value = alpha
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
    proto = bpy.context.active_object
    proto.name = name + '_proto'
    proto.data.materials.append(m)
    # displace for lumpy blobs
    tex = bpy.data.textures.new(name + '_tex', 'CLOUDS')
    tex.noise_scale = 0.6
    dm = proto.modifiers.new('Lump', 'DISPLACE')
    dm.texture = tex
    dm.strength = 0.45
    proto.hide_render = True
    proto.hide_viewport = True
    (x0, x1), (y0, y1), (z0, z1) = box
    me = bpy.data.meshes.new(name + '_pts')
    pts = [(rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(z0, z1)) for _ in range(n)]
    me.from_pydata(pts, [], [])
    ob = objs.new(name, me)
    sc.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(name + '_gn', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')
    inst = ng.nodes.new('GeometryNodeInstanceOnPoints')
    oi = ng.nodes.new('GeometryNodeObjectInfo')
    oi.inputs[0].default_value = proto
    rv = ng.nodes.new('FunctionNodeRandomValue')
    rv.data_type = 'FLOAT'
    # socket layout: 0/1 vector min/max, 2/3 float min/max, 4/5 int min/max, ...
    fl = [i for i in rv.inputs if i.bl_idname == 'NodeSocketFloat']
    fl[0].default_value = r[0]
    fl[1].default_value = r[1]
    rv.inputs['Seed'].default_value = seed
    rr = ng.nodes.new('FunctionNodeRandomValue')
    rr.data_type = 'FLOAT_VECTOR'
    vc = [i for i in rr.inputs if i.bl_idname == 'NodeSocketVector']
    vc[0].default_value = (0, 0, 0)
    vc[1].default_value = (6.28, 6.28, 6.28)
    rr.inputs['Seed'].default_value = seed + 1
    ng.links.new(gi.outputs[0], inst.inputs['Points'])
    ng.links.new(oi.outputs['Geometry'], inst.inputs['Instance'])
    out_f = next(o for o in rv.outputs if o.enabled)
    out_v = next(o for o in rr.outputs if o.enabled)
    ng.links.new(out_f, inst.inputs['Scale'])
    ng.links.new(out_v, inst.inputs['Rotation'])
    ng.links.new(inst.outputs[0], go.inputs[0])
    mod = ob.modifiers.new('Crowd', 'NODES')
    mod.node_group = ng
    return ob


# ---------------------------------------------------------------- Molecular Nodes style helpers
SURFACE_DEFAULTS = {'Quality': 3, 'Scale': 1.25, 'Relax': 5, 'Offset': 0.15, 'Fillet': 0, 'Mean Width': 1, 'Mean Iterations': 1,
                    'Color Blur': 2, 'Shade Smooth': True, 'Separate By': 'chain_id'}


def ensure_surface_group():
    """MN appends 'Style Surface' on first use; import a tiny molecule as surface once to get it."""
    if bpy.data.node_groups.get('Style Surface'):
        return bpy.data.node_groups['Style Surface']
    import os
    before = set(objs)
    bpy.ops.mn.import_molecule(method='local', filepath=os.path.join(BASE, 'pdb', 'dna', '1bna.pdb'), file_format='pdb', style='surface')
    tmp = next(o for o in objs if o not in before and o.type == 'MESH')
    bpy.data.objects.remove(tmp, do_unlink=True)
    return bpy.data.node_groups['Style Surface']


def to_surface(ob, mat=None, quality=3, scale=1.25):
    """Switch a static MN object from cartoon/spheres to the Gaussian surface style, keeping its material."""
    grp = ensure_surface_group()
    mod = next(m for m in ob.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name != 'GN_ClipHalfBox')
    style = next(n for n in mod.node_group.nodes if n.name.startswith('Style'))
    old_mat = None
    for i in style.inputs:
        if i.name == 'Material' and hasattr(i, 'default_value'):
            old_mat = i.default_value
    # remember what feeds 'Atoms' and where 'Geometry' goes: links are dropped when the tree changes
    ng = mod.node_group
    src = next((l.from_socket for l in ng.links if l.to_node == style and l.to_socket.name == 'Atoms'), None)
    dsts = [l.to_socket for l in ng.links if l.from_node == style]
    style.node_tree = grp
    gi = next(nd for nd in ng.nodes if nd.bl_idname == 'NodeGroupInput')
    ng.links.new(src or gi.outputs[0], style.inputs['Atoms'])
    for d in dsts:
        ng.links.new(style.outputs[0], d)
    for i in style.inputs:
        if i.name in SURFACE_DEFAULTS and hasattr(i, 'default_value'):
            try:
                i.default_value = SURFACE_DEFAULTS[i.name]
            except Exception:
                pass
        if i.name == 'Quality':
            i.default_value = quality
        if i.name == 'Scale':
            i.default_value = scale
        if i.name == 'Material':
            i.default_value = mat or old_mat
    return ob


def bake_static(ob, keep_clip=True):
    """Evaluate a static object's modifiers once into a plain mesh (geometry nodes surfaces are expensive to
    re-evaluate every frame). Keeps the clip modifier by re-adding it if asked. Returns the baked object."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    nb = objs.new(ob.name + '_baked', me)
    # material: the style node's Material socket is what the evaluated mesh should carry
    try:
        mod = next(m for m in ob.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name != 'GN_ClipHalfBox')
        st = next(n for n in mod.node_group.nodes if n.name.startswith('Style'))
        mat = next(i.default_value for i in st.inputs if i.name == 'Material')
        me.materials.clear()
        me.materials.append(mat)
    except StopIteration:
        pass
    for c in ob.users_collection:
        c.objects.link(nb)
    nb.matrix_world = ob.matrix_world.copy()
    # materials come from the evaluated geometry; make sure slots exist
    if not me.materials:
        for m in ev.data.materials:
            me.materials.append(m)
    ob.hide_render = True
    ob.hide_viewport = True
    return nb
