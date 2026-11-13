"""Low-poly 3D skulls rendered (baked) into small RGBA sprites for the v2 wall textures.

The skull is real geometry: cranium, cheekbones, maxilla, brow ridge, eye sockets and nose cavity
cut with exact booleans (dark cavity material), a row of upper teeth and an optional jaw with lower
teeth. Cycles renders it orthographic with light from above-front, so the sprite carries the form:
lit crown and brow, dark sockets, cheekbone and tooth shading, ambient occlusion in the cavities.
Variants: front+jaw, tilted+jaw, front no jaw, tilted no jaw, and a gold horned demon (crypt banner).
Bone sprites are neutral ivory; repaint_walls_v3.py tints them per set.

  blender -b --python tools/textures/make_skull_sprites.py -- --out assets/textures/walls/v2_src/skulls
"""
import argparse, math, os, sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--size', type=int, default=160)
A = ap.parse_args(argv)
OUT = os.path.abspath(A.out); os.makedirs(OUT, exist_ok=True)


def mat(name, col, rough=0.75, metal=0.0, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = 3.0
    return m


def sphere(name, loc, scale, seg=16, ring=10, m=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    if m: o.data.materials.append(m)
    return o


def cube(name, loc, scale, m=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    if m: o.data.materials.append(m)
    if bevel:
        bm = o.modifiers.new('bv', 'BEVEL'); bm.width = bevel; bm.segments = 2
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier='bv')
    return o


def boolean(target, other, op):
    md = target.modifiers.new('b', 'BOOLEAN'); md.object = other; md.operation = op; md.solver = 'EXACT'
    md.material_mode = 'TRANSFER'
    bpy.context.view_layer.objects.active = target; bpy.ops.object.modifier_apply(modifier='b')
    bpy.data.objects.remove(other, do_unlink=True)


def build_skull(bone, cav, jaw=True, demon=False, eye=None):
    # +Y is the back of the head; the face looks toward -Y (the camera)
    head = sphere('cranium', (0, 0.1, 0.2), (0.68, 0.84, 0.66), 24, 14, bone)
    for o in (sphere('face', (0, -0.4, -0.28), (0.55, 0.52, 0.5), 16, 10, bone),
              sphere('brow', (0, -0.56, 0.0), (0.54, 0.24, 0.1), 16, 8, bone),
              sphere('cheekL', (0.44, -0.6, -0.26), (0.17, 0.22, 0.14), 12, 8, bone),
              sphere('cheekR', (-0.44, -0.6, -0.26), (0.17, 0.22, 0.14), 12, 8, bone),
              cube('maxilla', (0, -0.62, -0.58), (0.3, 0.2, 0.12), bone, 0.05)):
        boolean(head, o, 'UNION')
    # eye sockets under the brow and the nose cavity: deep cuts with the dark cavity material
    for s in (1, -1):
        so = sphere('socket', (s * 0.25, -0.78, -0.15), (0.2, 0.34, 0.18), 16, 10, cav)
        so.rotation_euler = (0, s * 0.18, 0)
        boolean(head, so, 'DIFFERENCE')
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.11, radius2=0.0, depth=0.5, location=(0, -0.82, -0.4))
    nose = bpy.context.object; nose.data.materials.append(cav)
    nose.rotation_euler = (math.radians(90), 0, 0); nose.scale = (1.0, 1.0, 1.0)
    # point the triangle up: the cone axis runs along Y, one vertex at +Z
    nose.rotation_euler = (math.radians(90), math.radians(90), 0)
    nose.scale = (1.0, 1.35, 1.0)
    boolean(head, nose, 'DIFFERENCE')
    parts = [head]
    # upper teeth
    for i in range(7):
        x = -0.24 + i * 0.08
        t = cube('tooth', (x, -0.78 + abs(x) * 0.35, -0.73), (0.034, 0.04, 0.065), bone, 0.012); parts.append(t)
    if jaw:
        j = sphere('jaw', (0, -0.45, -0.86), (0.4, 0.4, 0.14), 16, 8, bone)
        boolean(j, sphere('jawin', (0, -0.3, -0.84), (0.34, 0.4, 0.3), 12, 8, cav), 'DIFFERENCE')
        parts.append(j)
        chin = cube('chin', (0, -0.76, -0.9), (0.2, 0.08, 0.08), bone, 0.04); parts.append(chin)
        for i in range(6):
            x = -0.2 + i * 0.08
            parts.append(cube('ltooth', (x, -0.76 + abs(x) * 0.35, -0.82), (0.032, 0.035, 0.05), bone, 0.01))
    if demon:
        for s in (1, -1):
            pts = []
            # curved horn: a chain of shrinking spheres sweeping up and out
            for k in range(9):
                f = k / 8
                loc = (s * (0.55 + 0.55 * f), -0.1 - 0.1 * f, 0.55 + 0.75 * f - 0.25 * f * f)
                r = 0.2 * (1 - f) + 0.03
                parts.append(sphere('horn', loc, (r, r, r), 10, 6, bone))
        if eye:
            for s in (1, -1):
                parts.append(sphere('eye', (s * 0.27, -0.66, -0.13), (0.1, 0.1, 0.1), 10, 6, eye))
    return parts


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = A.size
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.03, 0.03, 0.035, 1)
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.35
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0, -6, -0.05); cam.rotation_euler = (math.radians(90), 0, 0)
    key = bpy.data.lights.new('key', 'AREA'); key.energy = 380; key.size = 2.5
    ko = bpy.data.objects.new('key', key); sc.collection.objects.link(ko)
    ko.location = (1.2, -3.2, 4.0); ko.rotation_euler = (Vector((0, 0, 0)) - ko.location).to_track_quat('-Z', 'Y').to_euler()
    rim = bpy.data.lights.new('fill', 'AREA'); rim.energy = 60; rim.size = 3
    ro = bpy.data.objects.new('fill', rim); sc.collection.objects.link(ro)
    ro.location = (-3, -3, 0.2); ro.rotation_euler = (Vector((0, 0, 0)) - ro.location).to_track_quat('-Z', 'Y').to_euler()
    return sc


VARIANTS = [
    # name, jaw, rot (x tilt, z turn) degrees, demon
    ('skull_front_jaw', True, (0, 0, 0), False),
    ('skull_tilt_jaw', True, (-8, 0, 24), False),
    ('skull_front_nojaw', False, (6, 0, 0), False),
    ('skull_tilt_nojaw', False, (-4, 12, -28), False),
    ('demon_gold', True, (0, 0, 0), True),
]
for name, jaw, rot, demon in VARIANTS:
    sc = setup()
    if demon:
        bone = mat('gold', (0.95, 0.62, 0.2), 0.32, 1.0)
        cav = mat('cav', (0.05, 0.02, 0.015), 0.9)
        eye = mat('eye', (0.8, 0.05, 0.02), 0.5, 0.0, (1.0, 0.08, 0.02))
        sc.camera.data.ortho_scale = 3.3; sc.camera.location.z = 0.12
    else:
        bone = mat('bone', (0.62, 0.57, 0.47), 0.7)
        cav = mat('cav', (0.04, 0.035, 0.03), 0.95)
        eye = None
    parts = build_skull(bone, cav, jaw, demon, eye)
    for p in parts:
        p.data.polygons.foreach_set('use_smooth', [True] * len(p.data.polygons))
    root = bpy.data.objects.new('root', None); sc.collection.objects.link(root)
    for p in parts:
        p.parent = root
    root.rotation_euler = tuple(math.radians(a) for a in rot)
    tris = sum(sum(len(f.vertices) - 2 for f in p.data.polygons) for p in parts)
    sc.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('skull sprite', name, 'tris', tris)
