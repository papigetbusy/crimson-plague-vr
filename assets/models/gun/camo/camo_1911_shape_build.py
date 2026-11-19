"""EPIC / LEGENDARY 1911 camo tiers: the gun's SHAPE changes (new smooth, beveled parts) on top of the locked 1911 parts.
  blender -b --python camo_1911_shape_build.py -- --tier epic --out-dir .
Node table, the 4 empties, 3-mesh split (slide / frame / magazine) and redDot:false stay the 1911 format. Atlas 1024 LINEAR."""
import argparse, importlib.util, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import camo_1911_layout as LY
import camo_1911_build as CB
import camo_1911_shapes as S
import bpy, bmesh
from mathutils import Vector
M = CB.M; B = CB.B; G = M.G
S.init(M)

SOFT = dict(slide=(0.0014, 2, 0.006), frame=(0.0013, 2, 0.006), magazine=(0.0008, 1, 0.012))

# ------------------------------------------------------------------ helpers
def cell_uv_center(name):
    x0, y0, x1, y1 = LY.cell64_rect(name)
    return (x0 + x1) / 2.0 / LY.ATLAS, y0 / LY.ATLAS, (y1 - y0) / LY.ATLAS

def unwrap_custom(ob, bm, skull_xy=None):
    """New parts: per-face atlas cell by tag; smooth vertical ramp by world height (point sampled, no per-face re-fit)."""
    me = ob.data
    bm.normal_update()
    layer = bm.faces.layers.string.get('tex')
    uvl = bm.loops.layers.uv.new('UVMap') if not bm.loops.layers.uv else bm.loops.layers.uv[0]
    ys = [M.game_of(v.co).y for v in bm.verts]
    y0, y1 = min(ys), max(ys); span = max(y1 - y0, 1e-6)
    sx0, sy0, sx1, sy1 = LY.SKULL_REGION; A = float(LY.ATLAS)
    for f in bm.faces:
        tag = f[layer].decode() if layer is not None and f[layer] else 'bk_steel'
        for l in f.loops:
            g = M.game_of(l.vert.co)
            if tag == 'skull' and skull_xy is not None:
                cx, cy, sx, sy = skull_xy
                u = 0.5 + (g.x - cx) / sx; v = 0.5 + (g.y - cy) / sy
                u = min(max(u, 0.03), 0.97); v = min(max(v, 0.03), 0.97)
                l[uvl].uv = Vector(((sx0 + (sx1 - sx0) * u) / A, (sy0 + (sy1 - sy0) * v) / A))
            else:
                if tag not in LY.CELLS64: tag = 'bk_steel'
                cu, cv0, ch = cell_uv_center(tag)
                t = (g.y - y0) / span
                l[uvl].uv = Vector((cu, cv0 + ch * (0.16 + 0.68 * t)))
        f.material_index = {'ivory': 1, 'energy': 2}.get(LY.CELL_MATERIAL.get(tag if tag != 'skull' else '', 'steel'), 0)
    bm.to_mesh(me); me.update()

def make_materials3(img_path, name, emit_rgb, emit_strength):
    img = bpy.data.images.load(os.path.abspath(img_path)); img.pack()
    mats = []
    for key, metal, rough in (('steel', 1.0, 0.30), ('ivory', 0.0, 0.42), ('energy', 0.0, 0.35)):
        mat = bpy.data.materials.new(name + ('' if key == 'steel' else '_' + key))
        mat.use_nodes = True
        nt = mat.node_tree; b = nt.nodes.get('Principled BSDF')
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Linear'
        nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Metallic'].default_value = metal
        b.inputs['Roughness'].default_value = rough
        b.inputs['Specular IOR Level'].default_value = 0.5
        if key == 'energy':
            b.inputs['Emission Color'].default_value = (*emit_rgb, 1.0)
            b.inputs['Emission Strength'].default_value = emit_strength
        mats.append(mat)
    return mats

def soften(bm, key):
    off, segs, ml = SOFT[key]
    S.bevel_all(bm, None, offset=off, segs=segs, angle_deg=24.0, min_len=ml)

# base-part unwrap with point sampling for small (bevel) faces
def unwrap_base(ob, bm, part):
    me = ob.data
    bm.normal_update()
    layer = bm.faces.layers.string.get('tex')
    uvl = bm.loops.layers.uv.new('UVMap') if not bm.loops.layers.uv else bm.loops.layers.uv[0]
    ys = [M.game_of(v.co).y for v in bm.verts]
    py0, py1 = min(ys), max(ys); pspan = max(py1 - py0, 1e-6)
    CB.PENDING.clear()
    for f in bm.faces:
        tag = f[layer].decode() if layer is not None and f[layer] else 'steel_mid'
        verts_g = [M.game_of(l.vert.co) for l in f.loops]
        c = sum(verts_g, Vector((0, 0, 0))) / max(len(verts_g), 1)
        n = Vector((f.normal.x, f.normal.z, -f.normal.y))
        use = tag
        zs = [g.z for g in verts_g]; yv = [g.y for g in verts_g]; xv = [g.x for g in verts_g]
        ext = sorted([max(zs) - min(zs), max(yv) - min(yv), max(xv) - min(xv)])
        small = ext[1] < 0.0030        # a bevel strip: sample one point, never stretch a whole ramp over it
        if part == 'slide' and abs(n.x) > 0.9 and tag.startswith('steel') and not small:
            use = 'slideR' if n.x > 0 else 'slideL'
        elif part == 'frame' and abs(n.x) > 0.9 and tag.startswith('steel') and not small:
            use = 'frameR' if n.x > 0 else 'frameL'
        elif part in ('barrel', 'bushing') and n.z < -0.7 and c.z < M.Z_SLIDE_FRONT + 0.01:
            use = 'muzzle'
        elif part == 'grip_panel_L': use = 'gripL'
        elif part == 'grip_panel_R': use = 'gripR'
        if use in ('slideR', 'slideL', 'frameR', 'frameL'):
            u0, v0, u1, v1 = CB.region_rect(use)
            z0, z1 = LY.SLIDE_Z if use.startswith('slide') else LY.FRAME_Z
            y0, y1 = LY.SLIDE_Y if use.startswith('slide') else LY.FRAME_Y
            for loop, g in zip(f.loops, verts_g):
                uu = (z1 - g.z) / (z1 - z0) if use.endswith('R') else (g.z - z0) / (z1 - z0)
                vv = (g.y - y0) / (y1 - y0)
                loop[uvl].uv = Vector((u0 + (u1 - u0) * M._clamp(uu), v0 + (v1 - v0) * M._clamp(vv)))
        elif use in ('gripL', 'gripR'):
            ext_ = CB.GRIP_EXT.setdefault(use, [1e9, -1e9, 1e9, -1e9])
            for loop, g in zip(f.loops, verts_g):
                a1, a2 = g.dot(M.DOWN), g.dot(M.BACK)
                ext_[0] = min(ext_[0], a1); ext_[1] = max(ext_[1], a1); ext_[2] = min(ext_[2], a2); ext_[3] = max(ext_[3], a2)
            CB.PENDING.append((f, use, [(l, g) for l, g in zip(f.loops, verts_g)]))
        elif use == 'muzzle':
            u0, v0, u1, v1 = CB.region_rect('muzzle')
            for loop, g in zip(f.loops, verts_g):
                uu = 0.5 + g.x / (M.BUSHING_R * 2.2); vv = 0.5 + (g.y - M.Y_BORE) / (M.BUSHING_R * 2.2)
                loop[uvl].uv = Vector((u0 + (u1 - u0) * M._clamp(uu), v0 + (v1 - v0) * M._clamp(vv)))
        elif small:
            u0, v0, u1, v1 = M.uv_rect(use)
            t = M._clamp((c.y - py0) / pspan)
            for loop in f.loops:
                loop[uvl].uv = Vector(((u0 + u1) / 2, v0 + (v1 - v0) * (0.16 + 0.68 * t)))
        else:
            u0, v0, u1, v1 = M.uv_rect(use)
            if abs(n.x) >= abs(n.y) and abs(n.x) >= abs(n.z): uv_of = lambda g: (g.z, g.y)
            elif abs(n.y) >= abs(n.z): uv_of = lambda g: (g.x, g.z)
            else: uv_of = lambda g: (g.x, g.y)
            pts = [uv_of(g) for g in verts_g]
            xs = [p[0] for p in pts]; ysx = [p[1] for p in pts]
            minx, maxx, miny, maxy = min(xs), max(xs), min(ysx), max(ysx)
            dx = max(maxx - minx, 1e-6); dy = max(maxy - miny, 1e-6)
            for loop, p in zip(f.loops, pts):
                loop[uvl].uv = Vector((u0 + (u1 - u0) * (0.15 + 0.7 * (p[0] - minx) / dx), v0 + (v1 - v0) * (0.15 + 0.7 * (p[1] - miny) / dy)))
    for f, use, lg in CB.PENDING:
        u0, v0, u1, v1 = CB.region_rect(use)
        a0, a1, c0, c1 = CB.GRIP_EXT[use]
        for loop, g in lg:
            vv = (g.dot(M.DOWN) - a0) / max(a1 - a0, 1e-9); uu = (g.dot(M.BACK) - c0) / max(c1 - c0, 1e-9)
            loop[uvl].uv = Vector((u0 + (u1 - u0) * M._clamp(uu), v0 + (v1 - v0) * M._clamp(vv)))
    CB.PENDING.clear()
    bm.to_mesh(me); me.update()

# ------------------------------------------------------------------ new parts: shared
YT = M.Y_SLIDE_TOP; YB = M.Y_BORE
PORT_Z0, PORT_Z1 = M.Z_PORT_FRONT, M.Z_PORT_REAR

def _ell(name, c, r, seg=20, rings=11, ydir=1.0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts:
        v.co = G(c[0] + v.co.x * r[0], c[1] + v.co.z * r[1], c[2] + v.co.y * r[2])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

def _cyl(name, c, r, length, segs=20):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=length)
    for v in bm.verts:
        v.co = G(c[0] + v.co.x, c[1] + v.co.y * 0 + v.co.z * 0 + (v.co.x * 0), c[2]) if False else v.co
    for v in bm.verts:   # blender cone axis = z; we want the game z axis (blender -y)
        x, y, z = v.co.x, v.co.y, v.co.z
        v.co = G(c[0] + x, c[1] + y, c[2] + z)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

def _bool(target, tool, op):
    m = target.modifiers.new('b', 'BOOLEAN'); m.operation = op; m.object = tool; m.solver = 'EXACT'
    bpy.ops.object.select_all(action='DESELECT'); target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(tool, do_unlink=True)

def skull_brake(tier):
    """Skull muzzle brake from clean primitives + booleans: cranium, maxilla, cheekbones, deep orbital sockets, nasal cavity = the bore."""
    zf = M.Z_MUZZLE - 0.0240
    br = 0.0034
    cr = _ell('cr', (0, YB + 0.0050, zf + 0.0112), (0.0112, 0.0124, 0.0120), 22, 12)
    mx = _ell('mx', (0, YB - 0.0030, zf + 0.0085), (0.0080, 0.0078, 0.0095), 18, 10)
    _bool(cr, mx, 'UNION')
    for sg in (-1, 1):
        ck = _ell('ck', (sg * 0.0087, YB + 0.0004, zf + 0.0075), (0.0030, 0.0030, 0.0040), 10, 6)
        _bool(cr, ck, 'UNION')
    for sg in (-1, 1):
        ey = _ell('ey', (sg * 0.0058, YB + 0.0078, zf + 0.0003), (0.0036, 0.0040, 0.0034), 14, 8)
        _bool(cr, ey, 'DIFFERENCE')
    nose = _ell('ns', (0, YB - 0.0004, zf + 0.0012), (0.0016, 0.0022, 0.0016), 8, 5)
    # nasal cavity = bore: long cylinder along z through the whole skull
    cyl = _cyl('bore', (0, YB, zf + 0.012), br, 0.034, 20)
    cyl.rotation_euler = (0, 0, 0)
    _bool(cr, cyl, 'DIFFERENCE')
    bpy.data.objects.remove(nose, do_unlink=True)
    bm = bmesh.new(); bm.from_mesh(cr.data)
    bpy.data.objects.remove(cr, do_unlink=True)
    layer = M._tex_layer(bm)
    # (a custom-data layer added after faces exist: re-tag every face)
    for f in bm.faces: f[bm.faces.layers.string.get('tex')] = b'skull'
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    S.lathe_z(bm, [(zf + 0.0200, 0.0072), (M.Z_MUZZLE - 0.0030, 0.0078), (M.Z_MUZZLE + 0.0030, 0.0078)], 0.0, YB, segs=14, tex='bk_steel', inner=0.0032)
    bme = bmesh.new(); M._tex_layer(bme)
    for sg in (-1, 1):
        before = set(bme.faces)
        geo = bmesh.ops.create_icosphere(bme, subdivisions=2, radius=0.00235)
        for v in geo['verts']:
            gx = v.co.x; gy = v.co.z; gz = -v.co.y
            v.co = G(sg * 0.0058 + gx, YB + 0.0078 + gy, zf + 0.0026 + gz)
        S._tag_new(bme, before, 'violet' if tier == 'epic' else 'crimson')
    bmt = bmesh.new(); M._tex_layer(bmt)
    for i in (-1.5, -0.5, 0.5, 1.5):
        S.box(bmt, (i * 0.0024, YB - 0.0072 + (0.0004 if i in (-0.5, 1.5) else 0.0), zf + 0.0010), (0.0020, 0.0034, 0.0030), bevel=0.0004, segs=1, tex='bone')
    mapping = (0.0, YB + 0.0028, 0.0290, 0.0300)
    return bm, bme, bmt, mapping, zf - 0.0004

def thorn(bm, side, z0, scale=1.0, tex='bk_steel'):
    base = (side * 0.0046, 0.0320, z0)
    mid = (side * (0.0046 + 0.0032 * scale), 0.0320 - 0.0028 * scale, z0 + 0.0022 * scale)
    tip = (side * (0.0046 + 0.0062 * scale), 0.0320 - 0.0060 * scale, z0 + 0.0078 * scale)
    r0 = 0.0022 * scale
    S.tube_path(bm, [base, mid, tip], [r0, r0 * 0.62, 0.00008], [r0, r0 * 0.62, 0.00008], segs=5, tex=tex, up=(0, 0, 1))

def epic_frame_parts():
    """thorned shroud/rail under the dust cover, violet accent strips."""
    bm = bmesh.new(); M._tex_layer(bm)
    zA, zB = -0.1770, -0.0860
    S.tube_path(bm, [(0, 0.0322, zA), (0, 0.0322, zA + 0.0050), (0, 0.0322, zB - 0.0060), (0, 0.0322, zB)],
                [0.0030, 0.0050, 0.0050, 0.0034], [0.0022, 0.0030, 0.0030, 0.0022], segs=10, tex='bk_steel', up=(0, 1, 0))
    for side in (-1, 1):
        for i in range(7):
            thorn(bm, side, -0.1665 + i * 0.0118, scale=1.0 if i % 2 == 0 else 0.78)
    bms = bmesh.new(); M._tex_layer(bms)
    for side in (-1, 1):
        S.tube_path(bms, [(side * 0.0052, 0.0328, -0.1690), (side * 0.0054, 0.0328, -0.0930)], 0.0005, 0.0007, segs=4, tex='violet', up=(0, 1, 0))
    return bm, bms

def epic_beavertail():
    bm = bmesh.new(); M._tex_layer(bm)
    pts = [(0, 0.0383, 0.0090), (0, 0.0396, 0.0190), (0, 0.0414, 0.0290), (0, 0.0445, 0.0372), (0, 0.0486, 0.0430), (0, 0.0512, 0.0458)]
    S.tube_path(bm, pts, [0.0118, 0.0120, 0.0121, 0.0119, 0.0112, 0.0090], [0.0026, 0.0026, 0.0024, 0.0021, 0.0018, 0.0013], segs=14, tex='bk_steel', up=(0, 1, 0))
    return bm

def epic_hammer():
    bm = bmesh.new(); M._tex_layer(bm)
    zp = M.Z_SLIDE_REAR + 0.005; yp = M.Y_SLIDE_BOT + 0.007
    S.box(bm, (0, yp + 0.002, zp), (0.0100, 0.0150, 0.0100), bevel=0.0012, segs=2, tex='bk_steel')
    claw = [(0, yp + 0.0040, zp + 0.0010), (0, yp + 0.0105, zp + 0.0045), (0, yp + 0.0148, zp + 0.0115), (0, yp + 0.0160, zp + 0.0205), (0, yp + 0.0142, zp + 0.0290)]
    S.tube_path(bm, claw, [0.0040, 0.0043, 0.0034, 0.0022, 0.0006], [0.0034, 0.0034, 0.0026, 0.0017, 0.0005], segs=8, tex='steel_hi', up=(1, 0, 0))
    S.box(bm, (0, yp + 0.006, zp - 0.006), (0.0090, 0.0100, 0.0035), bevel=0.0005, segs=1, tex='bk_steel')
    return bm

def epic_spine():
    """vertebra-like ridge along the slide top; max 2.9 mm above the slide, sight line is >= 5.3 mm above."""
    bm = bmesh.new(); M._tex_layer(bm)
    n = 9; z_first, z_last = -0.1520, -0.0150
    for i in range(n):
        zc = z_first + (z_last - z_first) * i / (n - 1)
        s = 0.72 + 0.28 * i / (n - 1)
        over_port = (PORT_Z0 - 0.006) < zc < (PORT_Z1 + 0.006)
        hw = 0.0013 if over_port else 0.0046 * s
        l = 0.0122 * s
        yc = YT + 0.0004
        S.tube_path(bm, [(0, yc, zc - l / 2), (0, yc, zc - l * 0.22), (0, yc, zc + l * 0.22), (0, yc, zc + l / 2)],
                    [hw * 0.55, hw, hw, hw * 0.55], [0.0011, 0.0017, 0.0017, 0.0011], segs=6, tex='bk_steel', up=(0, 1, 0))
        S.tube_path(bm, [(0, YT + 0.0012, zc), (0, YT + 0.0031 * (0.85 + 0.15 * s), zc)], [0.0026 * s, 0.00012], [0.0010, 0.00012], segs=5, tex='silver_p', up=(1, 0, 0))
    bmc = bmesh.new(); M._tex_layer(bmc)
    S.tube_path(bmc, [(0, YT + 0.0010, z_first - 0.004), (0, YT + 0.0010, z_last + 0.004)], 0.00072, 0.00072, segs=6, tex='violet', up=(0, 1, 0))
    return bm, bmc

# ------------------------------------------------------------------ build
EMIT = {'epic': ((0.52, 0.16, 1.0), 5.0), 'legendary': ((1.0, 0.02, 0.05), 6.0)}

def build(tier, out_dir):
    name = f'pistol_1911_camo_{tier}'
    M.reset_scene()
    tex_path = os.path.join(out_dir, f'{name}_albedo.png')
    assert os.path.exists(tex_path), 'paint first: ' + tex_path
    mats = make_materials3(tex_path, name, *EMIT[tier])
    CB.GRIP_EXT.clear(); CB.PENDING.clear()
    objs_by_group = {'slide': [], 'frame': [], 'magazine': []}
    def add_base(obname, fn, key, group, mat_idx=0, soft=None):
        bm = fn()
        if soft: soften(bm, soft)
        ob, bm = M.bm_to_object(obname, bm)
        unwrap_base(ob, bm, key); bm.free()
        for m in mats: ob.data.materials.append(m)
        for p in ob.data.polygons: p.material_index = mat_idx
        print('PART', obname, sum(len(p.vertices) - 2 for p in ob.data.polygons)); objs_by_group[group].append(ob); return ob
    def add_new(obname, bm, group, skull_xy=None):
        ob, bm = M.bm_to_object(obname, bm)
        unwrap_custom(ob, bm, skull_xy); bm.free()
        for m in mats: ob.data.materials.append(m)
        print('PART', obname, sum(len(p.vertices) - 2 for p in ob.data.polygons)); objs_by_group[group].append(ob); return ob
    muzzle_tip = M.Z_MUZZLE
    add_base('slide', M.build_slide, 'slide', 'slide', soft='slide')
    add_base('sight_front', M.build_sight_front, 'sight_front', 'slide')
    add_base('sight_rear', M.build_sight_rear, 'sight_rear', 'slide')
    if tier == 'legendary':
        import camo_1911_legendary as LG
        LG.init(sys.modules[__name__])
    add_base('frame', M.build_frame if tier == 'epic' else LG.legendary_frame, 'frame', 'frame', soft='frame')
    add_base('grip', M.build_grip, 'grip', 'frame')
    if tier == 'epic':
        add_base('grip_panel_L', lambda: B.build_panel(-1), 'grip_panel_L', 'frame', 1)
        add_base('grip_panel_R', lambda: B.build_panel(+1), 'grip_panel_R', 'frame', 1)
    else:
        add_base('grip_panel_L', lambda: LG.panel(-1), 'grip_panel_L', 'frame', 1)
        add_base('grip_panel_R', lambda: LG.panel(+1), 'grip_panel_R', 'frame', 1)
    add_base('trigger_guard', B.build_trigger_guard, 'trigger_guard', 'frame')
    add_base('trigger', M.build_trigger, 'trigger', 'frame')
    add_new('hammer', epic_hammer() if tier == 'epic' else LG.hammer_spire(), 'frame')
    add_base('barrel', M.build_barrel, 'barrel', 'frame')
    add_base('controls', M.build_controls, 'controls', 'frame')
    add_base('magazine', M.build_magazine, 'magazine', 'magazine')
    if tier == 'epic':
        sk, eyes, teeth, mp, tip = skull_brake('epic')
        add_new('skull', sk, 'frame', mp); add_new('skull_eyes', eyes, 'frame'); add_new('skull_teeth', teeth, 'frame')
        muzzle_tip = tip
        rail, strips = epic_frame_parts()
        add_new('thorn_shroud', rail, 'frame'); add_new('shroud_strip', strips, 'frame')
        add_new('beavertail', epic_beavertail(), 'frame')
        sp, cord = epic_spine()
        add_new('spine', sp, 'slide'); add_new('spine_cord', cord, 'slide')
    else:
        muzzle_tip = LG.add_legendary(sys.modules[__name__], add_base, add_new, objs_by_group)
    objs = {g: B.join(lst, g) if len(lst) > 1 else lst[0] for g, lst in objs_by_group.items()}
    for ob in objs.values(): M.shade(ob, 35)
    root = M.new_empty('pistol_1911', (0, 0, 0))
    mag_well_g = Vector(M.GRIP_BOT)
    for g in ('slide', 'frame'):
        mw = objs[g].matrix_world.copy(); objs[g].parent = root; objs[g].matrix_world = mw
    M.new_empty('muzzle', Vector((0, M.Y_BORE, muzzle_tip)), parent=root)
    well = M.new_empty('mag_well', mag_well_g, parent=root)
    M.new_empty('rear_sight', Vector((0, M.Y_SLIDE_TOP + 0.0055, M.Z_SLIDE_REAR - 0.006)), parent=root)
    M.new_empty('front_sight', Vector((0, M.Y_SLIDE_TOP - 0.0002 + 0.007, M.Z_SLIDE_FRONT + 0.010)), parent=root)
    mag = objs['magazine']
    M.set_origin_world(mag, G(mag_well_g))
    mw = mag.matrix_world.copy(); mag.parent = well; mag.matrix_world = mw
    blend = os.path.abspath(os.path.join(out_dir, name + '.blend'))
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    tris = sum(len(p.vertices) - 2 for o in objs.values() for p in o.data.polygons)
    print('TRIS', tris, 'saved', blend)

def main():
    raw = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--tier', default='epic'); p.add_argument('--out-dir', default='assets/models/gun/camo')
    p.add_argument('--render-glb', default=''); p.add_argument('--render-dir', default='/workspace/camo_previews/work')
    a = p.parse_args(raw)
    if a.render_glb and os.environ.get('SHOTS'):
        shots = []
        for spec in os.environ['SHOTS'].split(';'):
            nm, *v = spec.split(','); v = [float(x) for x in v]
            shots.append((nm, v[0:3], v[3:6], v[6]))
        render_extra(a.render_glb, a.render_dir, f'pistol_1911_camo_{a.tier}', shots)
    elif a.render_glb: CB.render(a.render_glb, a.render_dir, f'pistol_1911_camo_{a.tier}')
    else: build(a.tier, os.path.abspath(a.out_dir))
    print('DONE')


# ---------------------------------------------------------------- debug close-ups (same lights/world as K.render_gun, own cameras)
def render_extra(glb, out_dir, gid, shots):
    sys.path.insert(0, os.path.dirname(HERE))
    import gun_gothic_common as K
    M.reset_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        for slot in o.material_slots:
            for n in slot.material.node_tree.nodes:
                if n.type == 'TEX_IMAGE': n.interpolation = 'Linear'
    mn, mx, center, size = M.mesh_bounds_game(meshes)
    L = max(size.z, size.y * 1.6, 0.2); k = L / 0.22
    cam, ground = M.setup_preview_scene()
    sc = bpy.context.scene
    sc.cycles.samples = 48; sc.render.resolution_x, sc.render.resolution_y = 1200, 800
    ground.location = G(center.x, mn.y - 0.002, center.z); ground.scale = (k * 1.5,) * 3
    bg = sc.world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.022, 0.024, 0.03, 1)
    gb = ground.data.materials[0].node_tree.nodes['Principled BSDF']; gb.inputs['Base Color'].default_value = (0.006, 0.006, 0.007, 1)
    for name, e in (('key', 0.5), ('fill', 0.5), ('rim', 1.0)):
        lo = bpy.data.objects[name]
        lo.location = G(center + (M.game_of(lo.location) - Vector((0, 0, 0))) * k)
        lo.data.size *= k; lo.data.energy *= e * k * 1.6
        lo.rotation_euler = (G(center) - lo.location).to_track_quat('-Z', 'Y').to_euler()
    d = bpy.data.lights.new('top_strip', 'AREA'); d.shape = 'RECTANGLE'
    d.size, d.size_y, d.energy, d.color = 0.03 * k, 0.4 * k, 3.0 * k * 1.6, (0.85, 0.92, 1.0)
    o = bpy.data.objects.new('top_strip', d); sc.collection.objects.link(o); o.location = G(center.x, mx.y + 0.25 * k, center.z)
    os.makedirs(out_dir, exist_ok=True)
    for name, loc, look, lens in shots:
        cam.data.lens = lens; M.aim_camera(cam, G(*look), G(*loc)); cam.data.clip_end = 5.0; cam.data.clip_start = 0.005
        sc.render.filepath = os.path.join(out_dir, f'{gid}_{name}.png'); bpy.ops.render.render(write_still=True)
        print('rendered', sc.render.filepath)


if __name__ == '__main__':
    main()
