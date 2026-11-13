"""Preview renders of a small assembled Crimson Halls section, built from the exported GLBs
(so the renders show exactly what the game would load).

  blender -b --python assets/models/env/crimson_halls/render_previews.py -- \
      --kit-dir assets/models/env/crimson_halls --out-dir /workspace/crimson_halls_previews
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

# (piece, location, z-rotation degrees) in Blender space (Z up, room side = -Y)
LAYOUT = [
    *[('floor_tile', (x, y, 0.0), 0) for x in (-3, -1, 1, 3) for y in (-1, -3)],
    ('floor_tile', (0, 1, 0.0), 0),
    ('wall_corner', (-3, 0, 0), 0),
    ('doorway_arch', (0, 0, 0), 0),
    ('wall_straight', (3, 0, 0), 0),
    ('pillar', (-2, -0.4, 0), 0),
    ('pillar', (2, -0.4, 0), 0),
    ('torch_sconce', (3, 0, 2.4), 0),
    ('torch_sconce', (-3, 0, 2.4), 0),
    ('banner', (-4, -1.0, 3.2), 90),
]
SCONCE_FLAME = Vector((0, -0.28, 0.28))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--kit-dir', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--samples', type=int, default=64)
    a = ap.parse_args(argv)
    kit = os.path.abspath(a.kit_dir)
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    flames = []
    for piece, loc, rz in LAYOUT:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(kit, f'ch_{piece}.glb'))
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            if o.parent is None:
                o.location = Vector(loc)
                o.rotation_mode = 'XYZ'
                o.rotation_euler = (0, 0, math.radians(rz))
        if piece == 'torch_sconce':
            flames.append(Vector(loc) + SCONCE_FLAME)
    # every image nearest, like the game (the importer reads the GLB sampler too)
    for img_node_mat in bpy.data.materials:
        if img_node_mat.node_tree:
            for n in img_node_mat.node_tree.nodes:
                if n.type == 'TEX_IMAGE':
                    print('texture filter in imported material:', n.interpolation)
                    n.interpolation = 'Closest'

    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 960
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = 0.1

    world = bpy.data.worlds.new('crypt')
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.010, 0.003, 0.004, 1)

    def light(name, typ, loc, colour, energy, size=0.1, rot=None):
        d = bpy.data.lights.new(name, typ)
        d.color = colour
        d.energy = energy
        if typ == 'AREA':
            d.size = size
        else:
            d.shadow_soft_size = size
        o = bpy.data.objects.new(name, d)
        sc.collection.objects.link(o)
        o.location = loc
        if rot:
            o.rotation_euler = rot
        return o

    # low gold torchlight: one warm point per sconce, just in front of the flame
    for i, f in enumerate(flames):
        light(f'torch{i}', 'POINT', f + Vector((0, -0.18, 0.05)), (1.0, 0.58, 0.22), 140, 0.08)
    # dim gold bounce from the hall, a red glow from beyond the door
    fill = light('hall_fill', 'AREA', (1.5, -7.0, 1.2), (1.0, 0.66, 0.32), 110, 6.0)
    fill.rotation_euler = (Vector((0, 0, 1.8)) - fill.location).to_track_quat('-Z', 'Y').to_euler()
    light('beyond', 'POINT', (0, 1.6, 1.4), (1.0, 0.18, 0.08), 90, 0.3)

    cam_d = bpy.data.cameras.new('cam')
    cam_d.lens = 28
    cam = bpy.data.objects.new('cam', cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    views = {
        'front': ((0.0, -9.6, 2.0), (0.0, 0.0, 2.0)),
        'three_quarter': ((6.2, -7.2, 2.7), (-0.6, -0.6, 1.9)),
    }
    for name, (loc, tgt) in views.items():
        cam.location = loc
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'crimson_halls_{name}.png')
        bpy.ops.render.render(write_still=True)
        print('rendered', sc.render.filepath)


if __name__ == '__main__':
    main()
