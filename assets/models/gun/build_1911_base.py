"""Crimson Plague VR - pistol_1911_base (blued steel, silver hammer, ivory grips).

Original low-poly PS2 / Snake Eater style M1911 "base skin". Reuses the mesh
helpers in tools/blender/build_pistol_1911.py (the test 1911) and overrides the
palette, atlas, materials, grip panels, trigger guard and hammer.

Build (repo root):
  blender -b --python assets/models/gun/build_1911_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/pistol_1911_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/pistol_1911_base.glb --type gun --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_1911_base.py -- --render-glb assets/models/gun/pistol_1911_base.glb \
    --render-dir /workspace/1911_base_previews

Fixes vs the test 1911: grip panels are seated into the frame (no gap), the
trigger guard sweep uses a fixed side axis (no twisted spike at the front),
and the steel is dark blued with metallic 1 / roughness 0.3.
"""
import argparse, importlib.util, math, os, sys
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
spec = importlib.util.spec_from_file_location(
    'p1911', os.path.join(REPO, 'tools', 'blender', 'build_pistol_1911.py'))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
G, Vector = M.G, Vector

NAME = 'pistol_1911_base'

# Chunkier, flatter-topped slide.
M.SLIDE_W = 0.0265
M.CH_TOP = 0.0022
M.CH_BOT = 0.0010

# 16-colour palette: blued steel, silver, ivory.
PAL = {
    'recess':       (7, 8, 11),
    'steel_black':  (10, 11, 17),
    'steel_dark':   (17, 20, 30),
    'steel_mid':    (27, 32, 46),
    'steel_light':  (46, 54, 74),
    'sheen':        (84, 98, 124),
    'steel_edge':   (150, 160, 176),
    'silver_dark':  (104, 108, 116),
    'silver':       (170, 175, 182),
    'silver_hi':    (228, 231, 236),
    'ivory_shadow': (190, 178, 150),
    'ivory_grain':  (214, 204, 178),
    'ivory':        (232, 224, 202),
    'ivory_light':  (247, 242, 228),
    'groove':       (10, 12, 17),
    'screw':        (124, 128, 136),
}
M.PAL = PAL
SWATCH = {
    'steel_dark': (0, 0), 'steel_mid': (1, 0), 'steel_light': (2, 0), 'steel_edge': (3, 0),
    'recess': (4, 0), 'silver': (5, 0), 'sheen': (6, 0), 'screw': (7, 0),
    'silver_hi': (6, 1), 'ivory': (7, 1), 'silver_dark': (6, 2), 'steel_black': (7, 2),
}
M.SWATCH = SWATCH
STEEL_RAMPS = {   # (shadow, base, highlight, streak) per steel cell
    'steel_black': ('recess', 'steel_black', 'steel_dark', 'steel_light'),
    'steel_dark':  ('steel_black', 'steel_dark', 'steel_mid', 'sheen'),
    'steel_mid':   ('steel_dark', 'steel_mid', 'steel_light', 'sheen'),
    'steel_light': ('steel_mid', 'steel_light', 'sheen', 'steel_edge'),
    'sheen':       ('steel_light', 'sheen', 'steel_edge', 'steel_edge'),
    'steel_edge':  ('sheen', 'steel_edge', 'silver_hi', 'silver_hi'),
    'silver':      ('silver_dark', 'silver', 'silver_hi', 'silver_hi'),
    'silver_hi':   ('silver', 'silver_hi', 'silver_hi', 'silver_hi'),
    'silver_dark': ('steel_light', 'silver_dark', 'silver', 'silver_hi'),
    'screw':       ('silver_dark', 'screw', 'silver', 'silver_hi'),
}


def paint_atlas(path):
    S, T, P = M.TEX_SIZE, M.TILE, M.PAD
    buf = [PAL['recess']] * (S * S)   # row 0 = UV v=0 (bottom)

    def put(x, y, c):  # UV space, y up
        if 0 <= x < S and 0 <= y < S:
            buf[y * S + x] = PAL[c] if isinstance(c, str) else c

    def rect(x0, y0, x1, y1, c):
        for y in range(y0, y1):
            for x in range(x0, x1):
                put(x, y, c)

    # Swatch cells. Each solid face maps to 15-85% of its cell, so a vertical
    # ramp + a bright streak reads as painted polish on every face, and a
    # dotted light rim at the mapped border reads as edge wear.
    for name, (tx, ty) in SWATCH.items():
        x0, y0 = tx * T, ty * T
        if name == 'recess':
            rect(x0, y0, x0 + T, y0 + T, 'recess'); continue
        if name == 'ivory':
            rect(x0, y0, x0 + T, y0 + T, 'ivory')
            rect(x0, y0, x0 + T, y0 + 12, 'ivory_grain')
            rect(x0, y0 + 20, x0 + T, y0 + 23, 'ivory_light'); continue
        sh, base, hi, streak = STEEL_RAMPS[name]
        rect(x0, y0, x0 + T, y0 + T, base)
        rect(x0, y0, x0 + T, y0 + 12, sh)
        rect(x0, y0 + 18, x0 + T, y0 + T, hi)
        rect(x0, y0 + 20, x0 + T, y0 + 22, streak)
        wear = 'steel_edge' if name.startswith('steel') or name == 'sheen' else 'silver_hi'
        lo, hi_px = P + 4, T - P - 4          # ~ the 15% / 85% mapped border
        for i in range(lo, hi_px + 1):
            if (i * 7) % 5 < 2:
                put(x0 + i, y0 + hi_px, wear)      # top edge wear
            if (i * 3) % 7 == 0:
                put(x0 + lo, y0 + i, wear)
                put(x0 + hi_px, y0 + i, wear)

    # Slide serrations: dark grooves with a polished ridge highlight each,
    # bright wear along the top and bottom of the panel.
    sx0, sy0, sx1, sy1 = M.REGION['serration']
    rect(sx0, sy0, sx1, sy1, 'steel_mid')
    rect(sx0, sy0, sx1, sy0 + 20, 'steel_dark')
    rect(sx0, sy0 + 40, sx1, sy0 + 46, 'steel_light')
    x = sx0 + 4
    while x < sx1 - 3:
        rect(x, sy0 + 6, x + 3, sy1 - 6, 'groove')
        rect(x + 3, sy0 + 6, x + 4, sy1 - 6, 'sheen')
        x += 8
    for xx in range(sx0, sx1):
        if xx % 3:
            put(xx, sy1 - P - 1, 'steel_edge')
        if xx % 5 == 0:
            put(xx, sy0 + P, 'sheen')

    # Muzzle disc.
    mx0, my0, mx1, my1 = M.REGION['muzzle']
    rect(mx0, my0, mx1, my1, 'steel_dark')
    cx, cy = (mx0 + mx1 - 1) / 2, (my0 + my1 - 1) / 2
    for r, c in ((28, 'steel_mid'), (25, 'steel_edge'), (23, 'steel_light'), (21, 'steel_mid'), (12, 'recess')):
        for y in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + y * y <= r * r:
                    put(int(cx + xx), int(cy + y), c)

    # Ivory grip panel (in the old 'wood' region): smooth, faint grain,
    # darker rim so it seats visually, a silver screw.
    wx0, wy0, wx1, wy1 = M.REGION['wood']
    rect(wx0, wy0, wx1, wy1, 'ivory')
    for i, c in enumerate(('ivory_grain', 'ivory_light', 'ivory_grain', 'ivory_light', 'ivory_grain')):
        gx = wx0 + 14 + i * 22
        for y in range(wy0, wy1):
            put(gx + int(2 * math.sin(y * 0.09 + i)), y, c)
            put(gx + 1 + int(2 * math.sin(y * 0.09 + i)), y, c)
    rect(wx0 + 30, wy0 + 100, wx0 + 60, wy0 + 140, 'ivory_light')
    for k in range(6):
        rect(wx0 + k, wy0 + k, wx1 - k, wy0 + k + 1, 'ivory_shadow' if k < 4 else 'ivory_grain')
        rect(wx0 + k, wy1 - k - 1, wx1 - k, wy1 - k, 'ivory_shadow' if k < 4 else 'ivory_grain')
        rect(wx0 + k, wy0 + k, wx0 + k + 1, wy1 - k, 'ivory_shadow' if k < 4 else 'ivory_grain')
        rect(wx1 - k - 1, wy0 + k, wx1 - k, wy1 - k, 'ivory_shadow' if k < 4 else 'ivory_grain')
    scx, scy = (wx0 + wx1) // 2, wy0 + int((wy1 - wy0) * 0.42)
    for r, c in ((9, 'ivory_shadow'), (7, 'silver'), (4, 'silver_hi')):
        for y in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + y * y <= r * r:
                    put(scx + xx, scy + y, c)
    rect(scx - 6, scy - 1, scx + 7, scy + 1, 'silver_dark')

    used = set(buf)
    assert len(used) <= 16, f'palette has {len(used)} colours'
    M._write_png(path, S, S, bytes(v for c in buf for v in c), bottom_up=True)
    print('atlas colours', len(used))
    return path


# ---- part overrides -----------------------------------------------------
def build_panel(side):
    import bmesh
    bm = bmesh.new(); M._tex_layer(bm)
    # Panels cover nearly the full grip side and are sunk 1.5 mm into the
    # steel frame so there is never a visible gap; ~2 mm stands proud.
    inset_u, inset_d, inset_fb = 0.006, 0.008, 0.0035
    top = M.GRIP_TOP + M.DOWN * inset_u
    bot = M.GRIP_BOT + M.UP * inset_d
    mid = (top + bot) * 0.5
    panel_t = 0.0036
    x = side * (M.GRIP_FRAME_W * 0.5 + panel_t * 0.5 - 0.0015)
    M.add_box(bm, center=(x, mid.y, mid.z),
              size=(panel_t, (top - bot).length, M.GRIP_THICK * 0.92 - 2 * inset_fb),
              axes=(M.RIGHT, M.UP, M.BACK), tex='wood', chamfer=0.0009)
    return bm


def build_trigger_guard():
    import bmesh
    bm = bmesh.new(); M._tex_layer(bm)
    front_strap = M.GRIP_TOP - M.BACK * (M.GRIP_THICK * 0.5)
    y_top = M.Y_FRAME_BOT - 0.0020           # top face buried ~0.8 mm in the frame
    y_bot = M.Y_FRAME_BOT - 0.027
    z_rear = front_strap.z - 0.002
    z_front = front_strap.z - 0.044
    r_rear = 0.005
    r_front = (y_top - y_bot) * 0.5

    def arc(cy, cz, r, a0, a1, n):
        return [Vector((0.0, cy + r * math.sin(a0 + (a1 - a0) * i / (n - 1)),
                        cz + r * math.cos(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]
    path = [Vector((0.0, y_top + 0.002, z_rear)), Vector((0.0, y_bot + r_rear, z_rear))]
    path += arc(y_bot + r_rear, z_rear - r_rear, r_rear, 0.0, -math.pi / 2, 4)[1:]
    z_front_c = z_front + r_front
    path.append(Vector((0.0, y_bot, z_front_c)))
    path += arc((y_top + y_bot) * 0.5, z_front_c, r_front, -math.pi / 2, -3 * math.pi / 2, 9)[1:]
    path.append(Vector((0.0, y_top, z_front_c + 0.010)))
    # The path lies in the game YZ plane, so a fixed +X 'up' keeps the
    # profile frame stable all the way round (the old Y-up frame flipped
    # where the loop went vertical and threw a spike at the front).
    M.add_sweep(bm, path, width=0.0055, height=0.0115, up=M.RIGHT, tex='steel_dark')
    return bm


def build_hammer():
    import bmesh
    bm = bmesh.new(); M._tex_layer(bm)
    z_pivot = M.Z_SLIDE_REAR + 0.005
    y_pivot = M.Y_SLIDE_BOT + 0.007
    M.add_box(bm, center=(0, y_pivot + 0.002, z_pivot), size=(0.010, 0.015, 0.010),
              tex='silver', chamfer=0.0010)
    tip_z = min(M.Z_REAR - 0.001, z_pivot + 0.012)
    path = [Vector((0, y_pivot + 0.007, z_pivot + 0.002)),
            Vector((0, y_pivot + 0.013, z_pivot + 0.007)),
            Vector((0, y_pivot + 0.017, tip_z))]
    M.add_sweep(bm, path, width=0.0078, height=0.0048, up=Vector((0, 0, 1)), tex='silver_hi')
    M.add_box(bm, center=(0, y_pivot + 0.006, z_pivot - 0.006), size=(0.009, 0.010, 0.0035),
              tex='silver', chamfer=0.0004)
    return bm


def make_materials(img_path):
    img = bpy.data.images.load(os.path.abspath(img_path))
    img.pack()
    mats = {}
    for key, metal, rough, spec in (('steel', 1.0, 0.30, 0.5), ('ivory', 0.0, 0.42, 0.5)):
        mat = bpy.data.materials.new(NAME if key == 'steel' else NAME + '_ivory')
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes.get('Principled BSDF')
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = img
        tex.interpolation = 'Closest'
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Specular IOR Level'].default_value = spec
        mats[key] = mat
    return mats


def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name; ob.data.name = name
    return ob


def build(out_dir):
    M.reset_scene()
    tex_path = os.path.join(out_dir, NAME + '_albedo.png')
    paint_atlas(tex_path)
    mats = make_materials(tex_path)
    parts = [
        ('slide', M.build_slide, 'slide', 'slide'),
        ('sight_front', M.build_sight_front, 'sight_front', 'slide'),
        ('sight_rear', M.build_sight_rear, 'sight_rear', 'slide'),
        ('frame', M.build_frame, 'frame', 'frame'),
        ('grip', M.build_grip, 'grip', 'frame'),
        ('grip_panel_L', lambda: build_panel(-1), 'grip_panel_L', 'frame'),
        ('grip_panel_R', lambda: build_panel(+1), 'grip_panel_R', 'frame'),
        ('trigger_guard', build_trigger_guard, 'trigger_guard', 'frame'),
        ('trigger', M.build_trigger, 'trigger', 'frame'),
        ('hammer', build_hammer, 'hammer', 'frame'),
        ('barrel', M.build_barrel, 'barrel', 'frame'),
        ('controls', M.build_controls, 'controls', 'frame'),
        ('magazine', M.build_magazine, 'magazine', 'magazine'),
    ]
    groups = {}
    for obj_name, fn, key, group in parts:
        ob, bm = M.bm_to_object(obj_name, fn())
        M.unwrap_object(ob, bm, part=key)
        bm.free()
        ob.data.materials.append(mats['ivory' if key.startswith('grip_panel') else 'steel'])
        groups.setdefault(group, []).append(ob)
    # 3 meshes / 4 draw calls: slide (can recoil), frame (+ivory primitive), magazine.
    objs = {g: join(lst, g) if len(lst) > 1 else lst[0] for g, lst in groups.items()}
    for ob in objs.values():
        M.shade(ob, 35)

    root = M.new_empty('pistol_1911', (0, 0, 0))
    mag_well_g = Vector(M.GRIP_BOT)
    for g in ('slide', 'frame'):
        mw = objs[g].matrix_world.copy(); objs[g].parent = root; objs[g].matrix_world = mw
    M.new_empty('muzzle', Vector((0, M.Y_BORE, M.Z_MUZZLE)), parent=root)
    well = M.new_empty('mag_well', mag_well_g, parent=root)
    M.new_empty('rear_sight', Vector((0, M.Y_SLIDE_TOP + 0.0055, M.Z_SLIDE_REAR - 0.006)), parent=root)
    mag = objs['magazine']
    M.set_origin_world(mag, G(mag_well_g))
    mw = mag.matrix_world.copy(); mag.parent = well; mag.matrix_world = mw

    mn, mx, c, size = M.mesh_bounds_game(list(objs.values()))
    print('GAME BOUNDS', tuple(round(v, 4) for v in mn), tuple(round(v, 4) for v in mx), 'size', tuple(round(v, 4) for v in size))
    blend = os.path.abspath(os.path.join(out_dir, NAME + '.blend'))
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print('saved', blend)


def render_glb(glb, render_dir):
    M.reset_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:   # importer sets Linear; match Closest like the game
        for slot in o.material_slots:
            for n in slot.material.node_tree.nodes:
                if n.type == 'TEX_IMAGE':
                    n.interpolation = 'Closest'
    cam, ground = M.setup_preview_scene()
    sc = bpy.context.scene
    sc.cycles.samples = 48
    sc.render.resolution_x, sc.render.resolution_y = 1000, 760
    # Cool-grey studio sky so polished steel has something to reflect,
    # plus a long overhead softbox for a streak down the flat slide top.
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.022, 0.024, 0.03, 1)
    bg.inputs[1].default_value = 1.0
    gb = ground.data.materials[0].node_tree.nodes['Principled BSDF']
    gb.inputs['Base Color'].default_value = (0.006, 0.006, 0.007, 1)
    d = bpy.data.lights.new('top_strip', 'AREA'); d.shape = 'RECTANGLE'
    d.size, d.size_y, d.energy, d.color = 0.03, 0.4, 3.0, (0.85, 0.92, 1.0)
    o = bpy.data.objects.new('top_strip', d); sc.collection.objects.link(o)
    o.location = G(0.0, 0.30, -0.05)
    for name, k in (('key', 0.4), ('fill', 0.4), ('rim', 0.9)):
        bpy.data.objects[name].data.energy *= k
    M.render_previews(cam, meshes, render_dir, NAME)


def main():
    raw = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--out-dir', default='assets/models/gun')
    p.add_argument('--render-glb', default='')
    p.add_argument('--render-dir', default='/workspace/1911_base_previews')
    a = p.parse_args(raw)
    if a.render_glb:
        render_glb(a.render_glb, a.render_dir)
    else:
        build(os.path.abspath(a.out_dir))
    print('DONE')


if __name__ == '__main__':
    main()
