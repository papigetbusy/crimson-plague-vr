"""3D wall-section previews for the v2 wall texture sets, in the style of the Crimson Halls kit previews.

Builds the same small section as assets/models/env/crimson_halls/render_previews.py from the kit GLBs
(corner, doorway arch, straight wall, two pillars, floor tiles, two torch sconces, crypt banner) and adds a
ceiling (floor tiles flipped at 4 m). Same candle / torch lighting, cameras, 1280x960, nearest filtering.
Then, per set, every face is re-textured by what the kit atlas put on it:
  brick / plinth / arch stones / frieze -> texStone (texPanel on the straight wall, the inset panel wall)
  pillar -> texPillar (64 px/m, medallion centred on each face), capstones -> texCeil, ceiling -> texCeil,
  floor tiles -> texFloor / texFloor2 / texFloor3 / texFloorEdge, crypt banner -> texBanner's banner,
  crypt doorway tile -> texCarpet, crypt gold frieze -> texGold; sconce iron and flame keep the kit atlas.
UVs are world-projected at the texture's own scale: walls 128x256 = 2 m x 4 m (plinth at the floor),
floors and ceiling 128 px = 2 m. Set 'crimson_halls' renders the untouched kit atlas as the reference.

  blender -b --python tools/textures/render_wall_sections.py -- --kit-dir <crimson_halls kit dir> \
      --tex-dir assets/textures/walls/v2 --out-dir /workspace/wall_tex_previews/3d [--sets crypt,blood]
"""
import argparse, math, os, sys
import bpy
from mathutils import Vector

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
    *[('ceiling', (x, y, 4.0), 0) for x in (-3, -1, 1, 3) for y in (-1, -3)],
]
SCONCE_FLAME = Vector((0, -0.28, 0.28))
REG = {   # kit atlas regions (px, rows top-down), from build_crimson_halls.py
    'wall': (4, 4, 124, 124), 'floor': (132, 4, 252, 124), 'pillar': (2, 130, 62, 190), 'vouss': (66, 130, 126, 190),
    'plinth': (4, 194, 124, 222), 'gold': (4, 226, 124, 254), 'banner': (132, 130, 186, 250), 'flame': (192, 130, 220, 186),
    'skull': (224, 130, 254, 160), 'iron': (224, 164, 236, 176), 'ironl': (240, 164, 252, 176), 'goldd': (224, 180, 236, 192),
    'dark': (240, 180, 252, 192), 'stone': (194, 194, 254, 254)}
KEYS = ['atlas', 'stone', 'panel', 'pillar', 'floorA', 'floorB', 'floorC', 'floorE', 'carpet', 'ceil', 'gold', 'banner']
TEXOF = {'stone': 'texStone', 'panel': 'texPanel', 'pillar': 'texPillar', 'floorA': 'texFloor', 'floorB': 'texFloor2',
         'floorC': 'texFloor3', 'floorE': 'texFloorEdge', 'carpet': 'texCarpet', 'ceil': 'texCeil', 'gold': 'texGold',
         'banner': 'texBanner'}
SETS = ['crimson_halls', 'crypt', 'blood', 'bog', 'frost', 'ember', 'void']
VIEWS = {
    'front': ((0.0, -9.6, 2.0), (0.0, 0.0, 2.0)),
    'three_quarter': ((6.2, -7.2, 2.7), (-0.6, -0.6, 1.9)),
    'close': ((-1.15, -3.0, 2.05), (-3.05, 0.0, 1.95)),     # the corner wall up close, to judge texel density and skull depth
}


def region_of(uvs):
    u = sum(p[0] for p in uvs) / len(uvs); v = sum(p[1] for p in uvs) / len(uvs)
    x, y = u * 256, (1 - v) * 256
    for k, (x0, y0, x1, y1) in REG.items():
        if x0 - 3 <= x <= x1 + 3 and y0 - 3 <= y <= y1 + 3:
            return k
    return None


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--kit-dir', required=True); ap.add_argument('--tex-dir', required=True)
    ap.add_argument('--out-dir', required=True); ap.add_argument('--samples', type=int, default=64)
    ap.add_argument('--sets', default=','.join(SETS)); ap.add_argument('--views', default=','.join(VIEWS))
    a = ap.parse_args(argv)
    kit, texd, out = map(os.path.abspath, (a.kit_dir, a.tex_dir, a.out_dir))
    os.makedirs(out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    flames, meshes = [], []   # (obj, piece, tile location)
    for piece, loc, rz in LAYOUT:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(kit, 'ch_%s.glb' % ('floor_tile' if piece == 'ceiling' else piece)))
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            if o.parent is None:
                o.location = Vector(loc); o.rotation_mode = 'XYZ'
                o.rotation_euler = (math.pi if piece == 'ceiling' else 0, 0, math.radians(rz))
        for o in new:
            if o.type == 'MESH':
                meshes.append((o, piece, loc))
        if piece == 'torch_sconce':
            flames.append(Vector(loc) + SCONCE_FLAME)
    bpy.context.view_layer.update()
    for m in bpy.data.materials:
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE':
                    n.interpolation = 'Closest'

    # ---- per face: key + world-projected UVs (layer 'world'); slots = KEYS on every mesh
    for o, piece, tloc in meshes:
        me = o.data
        atlas_mat = me.materials[0]
        o['atlas_mat'] = atlas_mat.name
        src = me.uv_layers[0]
        me.uv_layers[0].active_render = True
        wl = me.uv_layers.new(name='world')
        me.materials.clear()
        for k in KEYS:
            me.materials.append(atlas_mat)
        M = o.matrix_world; R = M.to_3x3()
        for p in me.polygons:
            uvs = [src.data[li].uv.copy() for li in p.loop_indices]
            reg = region_of(uvs)
            n = (R @ p.normal).normalized()
            if piece == 'floor_tile':
                fx, fy = tloc[0], tloc[1]
                key = {(0, 1): 'carpet'}.get((fx, fy)) or ('floorE' if fy == -1 and abs(fx) == 3 else
                                                         ['floorA', 'floorB', 'floorC'][int((fx + 3) / 2 + (fy + 3) / 2) % 3])
            elif piece == 'ceiling':
                key = 'ceil'
            elif reg in ('wall', 'plinth', 'vouss'):
                key = 'panel' if piece == 'wall_straight' else 'stone'
            elif reg == 'gold':
                key = 'gold'
            elif reg == 'pillar':
                key = 'pillar'
            elif reg in ('stone', 'dark'):
                key = 'ceil'
            elif reg == 'banner':
                key = 'banner'
            elif reg == 'skull':
                key = 'skull'
            else:
                key = 'atlas'
            o.data.polygons[p.index].material_index = KEYS.index(key) if key in KEYS else 0
            if key == 'skull':
                o.data.polygons[p.index].material_index = KEYS.index('stone')
                key = 'stone_skull'
            for li, vi in zip(p.loop_indices, p.vertices):
                w = M @ me.vertices[vi].co
                if key in ('floorA', 'floorB', 'floorC', 'floorE', 'carpet'):
                    uv = ((w.x - tloc[0]) / 2 + 0.5, (w.y - tloc[1]) / 2 + 0.5)
                elif key == 'banner':
                    su, sv = src.data[li].uv
                    s = (su * 256 - 132) / 54; tt = ((1 - sv) * 256 - 130) / 120
                    uv = ((18 + s * 92) / 128, 1 - (8 + tt * 192) / 256)
                elif key == 'pillar':
                    if abs(n.x) > abs(n.y) and abs(n.x) > abs(n.z):
                        uv = ((w.y - tloc[1]) / 2 + 0.5, w.z / 4)
                    elif abs(n.y) >= abs(n.z):
                        uv = ((w.x - tloc[0]) / 2 + 0.5, w.z / 4)
                    else:
                        uv = (w.x / 2, w.y / 2)
                elif abs(n.z) > 0.7:
                    uv = (w.x / 2, w.y / 2)
                elif key == 'gold':
                    uv = ((w.y if abs(n.x) > abs(n.y) else w.x) / 1.0, w.z / 1.0)
                else:
                    uv = ((w.y if abs(n.x) > abs(n.y) else w.x) / 2, w.z / 4)
                wl.data[li].uv = uv

    def tex_mat(sid, key):
        name = f'{sid}_{key}'
        if name in bpy.data.materials:
            return bpy.data.materials[name]
        path = os.path.join(texd, sid, TEXOF[key] + '.png')
        if not os.path.exists(path):
            return None
        m = bpy.data.materials.new(name); m.use_nodes = True
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        b.inputs['Roughness'].default_value = 0.85; b.inputs['Metallic'].default_value = 0.0
        b.inputs['Specular IOR Level'].default_value = 0.25
        im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(path, check_existing=True)
        im.interpolation = 'Closest'; im.extension = 'REPEAT'
        uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'world'
        nt.links.new(uvn.outputs['UV'], im.inputs['Vector']); nt.links.new(im.outputs['Color'], b.inputs['Base Color'])
        return m

    # ---- render setup, identical to the kit previews
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = a.samples; sc.cycles.use_denoising = True
    sc.render.resolution_x = 1280; sc.render.resolution_y = 960
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0.1
    world = bpy.data.worlds.new('crypt'); sc.world = world; world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.010, 0.003, 0.004, 1)

    def light(name, typ, loc, colour, energy, size=0.1):
        d = bpy.data.lights.new(name, typ); d.color = colour; d.energy = energy
        if typ == 'AREA':
            d.size = size
        else:
            d.shadow_soft_size = size
        ob = bpy.data.objects.new(name, d); sc.collection.objects.link(ob); ob.location = loc
        return ob
    for i, f in enumerate(flames):
        light(f'torch{i}', 'POINT', f + Vector((0, -0.18, 0.05)), (1.0, 0.58, 0.22), 140, 0.08)
    fill = light('hall_fill', 'AREA', (1.5, -7.0, 1.2), (1.0, 0.66, 0.32), 110, 6.0)
    fill.rotation_euler = (Vector((0, 0, 1.8)) - fill.location).to_track_quat('-Z', 'Y').to_euler()
    light('beyond', 'POINT', (0, 1.6, 1.4), (1.0, 0.18, 0.08), 90, 0.3)
    cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 28
    cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam

    for sid in a.sets.split(','):
        for o, piece, tloc in meshes:
            atlas_mat = bpy.data.materials[o['atlas_mat']]
            o.hide_render = (piece == 'banner' and sid not in ('crimson_halls', 'crypt'))
            for i, k in enumerate(KEYS):
                m = None
                if sid != 'crimson_halls' and k != 'atlas':
                    kk = k
                    if k == 'gold' and sid != 'crypt':
                        kk = 'panel' if piece == 'wall_straight' else 'stone'
                    if k == 'carpet' and sid != 'crypt':
                        kk = 'floorA'
                    m = tex_mat(sid, kk)
                o.data.materials[i] = m or atlas_mat
        for vname in a.views.split(','):
            loc, tgt = VIEWS[vname]
            cam.location = loc
            cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(out, f'{sid}_{vname}.png')
            bpy.ops.render.render(write_still=True)
            print('rendered', sc.render.filepath, flush=True)


if __name__ == '__main__':
    main()
