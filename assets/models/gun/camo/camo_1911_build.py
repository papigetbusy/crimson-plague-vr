"""Crimson Plague VR - 1911 camo pilot: build the locked 1911 mesh with a 1024 LINEAR atlas layout for the camo tiers.

Geometry, part split, vertex order, joins and the four empties are the original build_1911_base.py (functions are imported, not copied).
Only UV coordinates of the big side flats change (slide sides, frame sides, grip panels, muzzle disc, swatch cells at 4x) so the inlay /
scrimshaw has unique texture space. The three tiers (common / uncommon / rare) share this exact UV layout and differ only in the albedo.

  blender -b --python assets/models/gun/camo/camo_1911_build.py -- --tier rare --out-dir assets/models/gun/camo
"""
import argparse, importlib.util, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import camo_1911_layout as LY
import bpy
from mathutils import Vector

spec = importlib.util.spec_from_file_location('b1911', os.path.join(os.path.dirname(HERE), 'build_1911_base.py'))
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
M = B.M
G = M.G

# ---- 1024 layout into the shared mesh module (uv_rect reads these globals) --------------------------------
M.TEX_SIZE = LY.ATLAS; M.TILE = LY.CELL; M.PAD = LY.PAD
M.SWATCH = dict(LY.SWATCH)
M.REGION = {k: v for k, v in LY.REGION.items() if k in ('muzzle',)}
M.REGION['wood'] = LY.REGION['gripL']


def region_rect(name):
    s = float(LY.ATLAS)
    x0, y0, x1, y1 = LY.REGION[name]
    p = LY.RPAD
    return ((x0 + p) / s, (y0 + p) / s, (x1 - p) / s, (y1 - p) / s)


GRIP_EXT = {}; PENDING = []


def unwrap(ob, bm, part):
    """Same rules as tools/blender/build_pistol_1911.unwrap_object, plus continuous side-wall mapping for slide / frame and
    separate left / right grip panels."""
    me = ob.data
    bm.normal_update()
    layer = bm.faces.layers.string.get('tex')
    uv_lay = bm.loops.layers.uv.new('UVMap') if not bm.loops.layers.uv else bm.loops.layers.uv[0]
    for f in bm.faces:
        tag = 'steel_mid'
        if layer is not None:
            raw = f[layer]
            if raw:
                tag = raw.decode() if isinstance(raw, (bytes, bytearray)) else str(raw)
        verts_g = [M.game_of(l.vert.co) for l in f.loops]
        c = sum(verts_g, Vector((0, 0, 0))) / max(len(verts_g), 1)
        n_bl = f.normal
        n = Vector((n_bl.x, n_bl.z, -n_bl.y))
        use = tag
        if part == 'slide' and abs(n.x) > 0.9 and tag.startswith('steel'):
            use = 'slideR' if n.x > 0 else 'slideL'
        elif part == 'frame' and abs(n.x) > 0.9 and tag.startswith('steel'):
            use = 'frameR' if n.x > 0 else 'frameL'
        elif part in ('barrel', 'bushing') and n.z < -0.7 and c.z < M.Z_SLIDE_FRONT + 0.01:
            use = 'muzzle'
        elif part == 'grip_panel_L':
            use = 'gripL'
        elif part == 'grip_panel_R':
            use = 'gripR'

        if use in ('slideR', 'slideL', 'frameR', 'frameL'):
            u0, v0, u1, v1 = region_rect(use)
            z0, z1 = LY.SLIDE_Z if use.startswith('slide') else LY.FRAME_Z
            y0, y1 = LY.SLIDE_Y if use.startswith('slide') else LY.FRAME_Y
            for loop, g in zip(f.loops, verts_g):
                uu = (z1 - g.z) / (z1 - z0) if use.endswith('R') else (g.z - z0) / (z1 - z0)
                vv = (g.y - y0) / (y1 - y0)
                loop[uv_lay].uv = Vector((u0 + (u1 - u0) * M._clamp(uu), v0 + (v1 - v0) * M._clamp(vv)))
        elif use in ('gripL', 'gripR'):
            u0, v0, u1, v1 = region_rect(use)
            al = [g.dot(M.DOWN) for g in verts_g]; ac = [g.dot(M.BACK) for g in verts_g]
            ext = GRIP_EXT.setdefault(use, [1e9, -1e9, 1e9, -1e9])
            for loop, g in zip(f.loops, verts_g):
                a1, a2 = g.dot(M.DOWN), g.dot(M.BACK)
                ext[0] = min(ext[0], a1); ext[1] = max(ext[1], a1); ext[2] = min(ext[2], a2); ext[3] = max(ext[3], a2)
            PENDING.append((f, use, [(l, g) for l, g in zip(f.loops, verts_g)]))
        elif use == 'muzzle':
            u0, v0, u1, v1 = region_rect('muzzle')
            for loop, g in zip(f.loops, verts_g):
                uu = 0.5 + g.x / (M.BUSHING_R * 2.2)
                vv = 0.5 + (g.y - M.Y_BORE) / (M.BUSHING_R * 2.2)
                loop[uv_lay].uv = Vector((u0 + (u1 - u0) * M._clamp(uu), v0 + (v1 - v0) * M._clamp(vv)))
        else:
            u0, v0, u1, v1 = M.uv_rect(use)
            if abs(n.x) >= abs(n.y) and abs(n.x) >= abs(n.z):
                uv_of = lambda g: (g.z, g.y)
            elif abs(n.y) >= abs(n.z):
                uv_of = lambda g: (g.x, g.z)
            else:
                uv_of = lambda g: (g.x, g.y)
            pts = [uv_of(g) for g in verts_g]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
            dx = max(maxx - minx, 1e-6); dy = max(maxy - miny, 1e-6)
            for loop, p in zip(f.loops, pts):
                uu = (p[0] - minx) / dx; vv = (p[1] - miny) / dy
                loop[uv_lay].uv = Vector((u0 + (u1 - u0) * (0.15 + 0.7 * uu), v0 + (v1 - v0) * (0.15 + 0.7 * vv)))
    for f, use, lg in PENDING:
        u0, v0, u1, v1 = region_rect(use)
        a0, a1, c0, c1 = GRIP_EXT[use]
        for loop, g in lg:
            vv = (g.dot(M.DOWN) - a0) / max(a1 - a0, 1e-9); uu = (g.dot(M.BACK) - c0) / max(c1 - c0, 1e-9)
            loop[uv_lay].uv = Vector((u0 + (u1 - u0) * M._clamp(uu), v0 + (v1 - v0) * M._clamp(vv)))
    if PENDING:
        print('GRIP EXTENTS (along_min,max, across_min,max)', {k: [round(x, 5) for x in v] for k, v in GRIP_EXT.items()})
    PENDING.clear()
    bm.to_mesh(me); me.update()


def make_materials(img_path, name):
    img = bpy.data.images.load(os.path.abspath(img_path)); img.pack()
    mats = {}
    for key, metal, rough, spec in (('steel', 1.0, 0.30, 0.5), ('ivory', 0.0, 0.42, 0.5)):
        mat = bpy.data.materials.new(name if key == 'steel' else name + '_ivory')
        mat.use_nodes = True
        nt = mat.node_tree; bsdf = nt.nodes.get('Principled BSDF')
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Linear'
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Specular IOR Level'].default_value = spec
        mats[key] = mat
    return mats


def build(tier, out_dir):
    name = f'pistol_1911_camo_{tier}'
    M.reset_scene()
    tex_path = os.path.join(out_dir, f'{name}_albedo.png')
    assert os.path.exists(tex_path), 'paint the albedo first: ' + tex_path
    mats = make_materials(tex_path, name)
    parts = [
        ('slide', M.build_slide, 'slide', 'slide'),
        ('sight_front', M.build_sight_front, 'sight_front', 'slide'),
        ('sight_rear', M.build_sight_rear, 'sight_rear', 'slide'),
        ('frame', M.build_frame, 'frame', 'frame'),
        ('grip', M.build_grip, 'grip', 'frame'),
        ('grip_panel_L', lambda: B.build_panel(-1), 'grip_panel_L', 'frame'),
        ('grip_panel_R', lambda: B.build_panel(+1), 'grip_panel_R', 'frame'),
        ('trigger_guard', B.build_trigger_guard, 'trigger_guard', 'frame'),
        ('trigger', M.build_trigger, 'trigger', 'frame'),
        ('hammer', B.build_hammer, 'hammer', 'frame'),
        ('barrel', M.build_barrel, 'barrel', 'frame'),
        ('controls', M.build_controls, 'controls', 'frame'),
        ('magazine', M.build_magazine, 'magazine', 'magazine'),
    ]
    groups = {}
    for obj_name, fn, key, group in parts:
        ob, bm = M.bm_to_object(obj_name, fn())
        unwrap(ob, bm, key)
        bm.free()
        ob.data.materials.append(mats['ivory' if key.startswith('grip_panel') else 'steel'])
        groups.setdefault(group, []).append(ob)
    objs = {g: B.join(lst, g) if len(lst) > 1 else lst[0] for g, lst in groups.items()}
    for ob in objs.values():
        M.shade(ob, 35)
    root = M.new_empty('pistol_1911', (0, 0, 0))
    mag_well_g = Vector(M.GRIP_BOT)
    for g in ('slide', 'frame'):
        mw = objs[g].matrix_world.copy(); objs[g].parent = root; objs[g].matrix_world = mw
    M.new_empty('muzzle', Vector((0, M.Y_BORE, M.Z_MUZZLE)), parent=root)
    well = M.new_empty('mag_well', mag_well_g, parent=root)
    M.new_empty('rear_sight', Vector((0, M.Y_SLIDE_TOP + 0.0055, M.Z_SLIDE_REAR - 0.006)), parent=root)
    M.new_empty('front_sight', Vector((0, M.Y_SLIDE_TOP - 0.0002 + 0.007, M.Z_SLIDE_FRONT + 0.010)), parent=root)
    mag = objs['magazine']
    M.set_origin_world(mag, G(mag_well_g))
    mw = mag.matrix_world.copy(); mag.parent = well; mag.matrix_world = mw
    blend = os.path.abspath(os.path.join(out_dir, name + '.blend'))
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print('saved', blend)


def render(glb, render_dir, gid):
    sys.path.insert(0, os.path.dirname(HERE))
    import gun_gothic_common as K
    K.render_gun(glb, render_dir, gid)


def main():
    raw = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--tier', default='common')
    p.add_argument('--out-dir', default='assets/models/gun/camo')
    p.add_argument('--render-glb', default='')
    p.add_argument('--render-dir', default='/workspace/camo_previews/work')
    a = p.parse_args(raw)
    if a.render_glb:
        render(a.render_glb, a.render_dir, f'pistol_1911_camo_{a.tier}')
    else:
        build(a.tier, os.path.abspath(a.out_dir))
    print('DONE')


if __name__ == '__main__':
    main()
