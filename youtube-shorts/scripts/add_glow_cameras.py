"""Glow + multi-angle cameras.
 - drug materials get an emission term (strongest while the drug approaches the
   enzyme) and the compositor adds a soft bloom so the molecule reads as a
   glowing marker even when small in frame
 - S3 orbit re-keyed as far -> near -> far (14 -> 7.5 -> 13 nm)
 - S2 follow arc re-keyed as far -> near -> far
 - two extra S3 cameras for replay angles: Cam_S3_alt (opposite orbit, higher),
   Cam_S3_macro (tight, slow drift on the pocket). They are not bound to markers;
   render them with scripts/render_preview.py ... CAMERA
Run: blender -b blend/gram_negative_base.blend --python scripts/add_glow_cameras.py
"""
import bpy, math, os
from mathutils import Vector

BASE = r'E:\Github Project\piranfar.github.io\youtube-shorts'
BLEND = os.path.join(BASE, 'blend', 'gram_negative_base.blend')
sc = bpy.context.scene
objs = bpy.data.objects
mats = bpy.data.materials
drug = objs['Drug_ceftazidime']
tgt = objs['Target_TEM1_site']
site_w = tgt.matrix_world.translation.copy()


def clear_anim(idb):
    if idb.animation_data:
        idb.animation_data_clear()


def key_fades_and_glow(mat, alpha_keys, glow_keys, glow_rgb):
    tree = mat.node_tree
    clear_anim(tree)
    b = tree.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (*glow_rgb, 1.0)
    a = b.inputs['Alpha']
    for f, v in sorted(alpha_keys.items()):
        a.default_value = v
        a.keyframe_insert('default_value', frame=f)
    e = b.inputs['Emission Strength']
    for f, v in sorted(glow_keys.items()):
        e.default_value = v
        e.keyframe_insert('default_value', frame=f)


red = (1.0, 0.35, 0.2)
key_fades_and_glow(mats['MAT_drug_travel'],
                   {1: 1.0, 470: 1.0, 484: 0.0},
                   {1: 0.6, 150: 0.6, 330: 1.5, 400: 3.0, 470: 3.0, 484: 0.0}, red)
key_fades_and_glow(mats['MAT_drug_docked'],
                   {1: 0.0, 470: 0.0, 484: 1.0, 548: 1.0, 562: 0.0},
                   {1: 0.0, 470: 0.0, 484: 1.2, 548: 1.2, 562: 0.0}, red)
key_fades_and_glow(mats['MAT_drug_product'],
                   {1: 0.0, 548: 0.0, 562: 1.0, 700: 1.0, 730: 0.0},
                   {1: 0.0, 548: 0.0, 562: 0.4, 730: 0.0}, (0.9, 0.6, 0.3))
print('GLOW keyed')

# ---------- compositor bloom ----------
# Blender 5: the compositor is a node-group datablock on scene.compositing_node_group
if hasattr(sc, 'compositing_node_group'):
    nt = bpy.data.node_groups.get('Compositor_Bloom')
    if nt is None:
        nt = bpy.data.node_groups.new('Compositor_Bloom', 'CompositorNodeTree')
    sc.compositing_node_group = nt
else:                                   # Blender 4.x fallback
    sc.use_nodes = True
    nt = sc.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
rl = nt.nodes.new('CompositorNodeRLayers')
gl = nt.nodes.new('CompositorNodeGlare')
# Blender 5.2: every glare option is an input socket; 'Type' is a menu socket
if hasattr(gl, 'glare_type'):
    gl.glare_type = 'BLOOM'
else:
    for ident in ('BLOOM', 'Bloom'):
        try:
            gl.inputs['Type'].default_value = ident
            break
        except Exception:
            pass
for name, val in (('Threshold', 1.0), ('Size', 0.35), ('Strength', 0.6)):
    try:
        gl.inputs[name].default_value = val
    except Exception as e:
        print('   glare option', name, 'skipped:', str(e)[:60])
if hasattr(bpy.types, 'CompositorNodeComposite'):
    out = nt.nodes.new('CompositorNodeComposite')
    out_in = out.inputs['Image']
else:
    if not any(s.in_out == 'OUTPUT' for s in nt.interface.items_tree if s.item_type == 'SOCKET'):
        nt.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    out = nt.nodes.new('NodeGroupOutput')
    out_in = out.inputs[0]
print('   glare type now:', gl.inputs['Type'].default_value if 'Type' in gl.inputs else getattr(gl, 'glare_type', '?'))
nt.links.new(rl.outputs['Image'], gl.inputs['Image'])
nt.links.new(gl.outputs['Image'], out_in)
print('BLOOM compositor set via', 'compositing_node_group' if hasattr(sc, 'compositing_node_group') else 'scene.node_tree')

# ---------- S3 main orbit: far -> near -> far ----------
cam3 = objs['Cam_S3_enzyme']
clear_anim(cam3)
cam3.data.lens = 55
orbit = [(400, 14.0, 188.0, 2.6), (470, 10.5, 174.0, 2.0), (520, 7.5, 162.0, 1.5),
         (600, 7.5, 146.0, 1.5), (680, 10.0, 132.0, 2.2), (740, 13.0, 120.0, 2.8)]
for f, r, a, h in orbit:
    t = math.radians(a)
    cam3.location = site_w + Vector((r * math.cos(t), r * math.sin(t), h))
    cam3.keyframe_insert('location', frame=f)

# ---------- S2: far -> near -> far ----------
cam2 = objs['Cam_S2_follow']
clear_anim(cam2)
arc = {1: (5.0, 20.0, 8.0), 120: (3.5, 14.0, 4.5), 200: (0.5, 9.0, 1.8), 260: (-1.5, 7.5, 0.6),
       330: (-3.0, 10.0, 1.2), 450: (-5.0, 14.0, 2.5)}
for f, off in arc.items():
    sc.frame_set(f)
    cam2.location = drug.matrix_world.translation + Vector(off)
    cam2.keyframe_insert('location', frame=f)
print('CAMERAS re-keyed far-near-far')


# ---------- replay cameras ----------
def make_cam(name, lens):
    old = objs.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    c = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(c)
    trk = c.constraints.new('TRACK_TO')
    trk.target = tgt
    trk.track_axis = 'TRACK_NEGATIVE_Z'
    trk.up_axis = 'UP_Y'
    return c


alt = make_cam('Cam_S3_alt', 50)        # opposite direction, higher, looking down on the pocket
for f, r, a, h in [(400, 12.0, 118.0, 5.0), (520, 8.5, 140.0, 4.0), (620, 8.5, 165.0, 3.5), (740, 12.0, 190.0, 5.0)]:
    t = math.radians(a)
    alt.location = site_w + Vector((r * math.cos(t), r * math.sin(t), h))
    alt.keyframe_insert('location', frame=f)

macro = make_cam('Cam_S3_macro', 70)    # tight on the pocket, slow drift
for f, r, a, h in [(440, 5.5, 170.0, 1.0), (740, 5.0, 150.0, 1.4)]:
    t = math.radians(a)
    macro.location = site_w + Vector((r * math.cos(t), r * math.sin(t), h))
    macro.keyframe_insert('location', frame=f)
print('REPLAY cameras Cam_S3_alt, Cam_S3_macro')

sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('SAVED', BLEND)
