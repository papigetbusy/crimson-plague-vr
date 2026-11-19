"""Crimson Plague VR - smg_bullpup_base: the Bullpup SMG (v5 SHAPE REBUILD, FN P90).

Original low-poly PS2 / Snake Eater style personal-defence bullpup, rebuilt from the FN P90 side photos in
/workspace/bullpup_refs/ (outline traced, 1653 px/m = 0.505 m long). The P90 tells:
  1. translucent smoked-glass magazine lying flat along the whole top, brass rounds visible inside (3rd glTF material 'glass',
     alpha-blended; the atlas region is also painted smoked + brass rounds so it still reads if a loader ignores alpha);
  2. one smooth bulbous polymer lower shell with a rounded teardrop thumbhole and a rounded trigger hole, rounded butt,
     no flat faces: big rim bevels + a REAL geometric crown (cap faces subdivided and domed, not just normals);
  3. steel sight housing arching over the magazine with a hollow window, round brass-rimmed ring-sight caps on the sides,
     a ring sight + front bead on top, short barrel with a slotted flash hider, charging handles / rods on both sides;
  4. ~50 cm long, stubby.
Glossy near-black polymer (polish3 recipe) + the locked 1911 steel (metallic 1 / roughness 0.30). Only two small brass
accents (trigger blade, ring-cap rims). One 1024 px smooth albedo, sampler LINEAR.

Meshes: body (polymer shell + trigger), receiver (housing, ring sight, deck, barrel + hider, rods, tabs), magazine (glass mag + brass rounds).
Empties: muzzle, mag_well (mag centre), rear_sight (ring centre), front_sight (bead) - both at X=0 on the sight axis parallel to the bore.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
import bpy
import gun_sniper_common as SN
S, K, C, M, G = SN.S, SN.K, SN.C, SN.M, SN.G

NAME = 'smg_bullpup_base'
BY = 0.050
HW = 0.0215
CROWN = 0.0085
Z_MUZ = -0.2086
Y_SIGHT = 0.1571
Z_RING = -0.0568
Z_BEAD = -0.1300
PH = -math.pi / 12
MAGW = (0.0, 0.0751, 0.0045)


def T(xp, yp):
    """P90 side photo px -> (z, y) metres (bore on yp 268, butt at z +0.296)."""
    return (round((560 - xp) / 1653.0, 4), round(BY + (268 - yp) / 1653.0, 4))


def P(pts):
    return [T(x, y) for x, y in pts]


SHELL_PX = [(70, 226), (74, 214), (86, 208), (95, 207), (322, 207), (334, 222), (342, 245), (780, 245), (834, 262), (836, 332), (820, 372),
            (790, 372), (768, 372), (752, 395), (730, 422), (700, 436), (660, 438), (632, 432), (624, 412), (600, 408), (560, 415),
            (520, 428), (470, 440), (425, 440), (395, 426), (345, 410), (292, 405), (95, 405), (86, 404), (74, 399), (70, 388)]
THUMB_PX = [(445, 320), (520, 312), (542, 330), (535, 352), (500, 372), (450, 380), (415, 375), (406, 358), (420, 335)]
TRIG_PX = [(645, 305), (690, 302), (715, 318), (722, 345), (700, 368), (668, 372), (640, 366), (622, 350), (618, 325)]
HOUSE_PX = [(545, 262), (550, 222), (562, 182), (590, 152), (632, 142), (640, 106), (832, 106), (836, 262), (780, 262), (780, 212), (600, 212), (594, 262)]
WINDOW_PX = [(658, 158), (764, 158), (764, 198), (658, 198)]


def _dist_poly(pt, poly):
    best = 1e9
    px, py = pt
    for i in range(len(poly)):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % len(poly)]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-12)))
        best = min(best, math.hypot(px - (ax + t * dx), py - (ay + t * dy)))
    return best


def dome_shell(part, outer, holes, hw, bevel, bevel_hole, crown, D):
    """K.shell + a real geometric crown: interior cap edges are split once and every cap vertex is pushed outward by
    crown * ease(distance from the outline), so the big side faces are convex domes instead of flat planes."""
    new = K.shell(part, outer, holes, hw, region='poly', bevel=bevel, segs=2, bevel_hole=bevel_hole, gmap=True)
    bm = part.bm
    def on_cap(v):
        return abs(abs(M.game_of(v.co).x) - hw) < 1e-5
    caps = [f for f in new if f.is_valid and all(on_cap(v) for v in f.verts)]
    capset = set(caps)
    inner = [e for f in caps for e in f.edges if all(lf in capset for lf in e.link_faces) and len(e.link_faces) == 2]
    inner = list(set(inner))
    if inner:
        bmesh.ops.subdivide_edges(bm, edges=inner, cuts=2, use_grid_fill=True)
    loops = [outer] + list(holes)
    for v in bm.verts:
        g = M.game_of(v.co)
        if abs(abs(g.x) - hw) > 1e-5:
            continue
        d = min(_dist_poly((g.z, g.y), lp) for lp in loops)
        t = max(0.0, min(1.0, (d - bevel) / D))
        f = 1 - (1 - t) ** 2
        g2 = (g.x + math.copysign(crown * f, g.x), g.y, g.z)
        v.co = G(*g2)
    bm.normal_update()


def paint_glass(A, r):
    """Smoked translucent magazine side: dark smoke, faint ribs, a row of brass round discs."""
    x0, y0, x1, y1 = A.reg[r]
    A.steel(r, ('steel_black', 'steel_dark', 'steel_dark', 'steel_mid'), 61, grime=0.78, edge=False)
    cy = (y0 + y1) // 2
    n = 12
    step = (x1 - x0 - 8) / n
    for i in range(n):
        cx = x0 + 4 + step * (i + 0.5)
        for y in range(cy - 7, cy + 8):
            for x in range(int(cx) - 7, int(cx) + 8):
                d = math.hypot(x - cx, y - cy)
                if d <= 4.6:
                    A.put(x, y, 'brass_light' if d < 2.0 else 'brass')
                elif d <= 5.8:
                    A.put(x, y, 'brass_dark')


def glass_mat(base_mat):
    img = [n.image for n in base_mat.node_tree.nodes if n.type == 'TEX_IMAGE'][0]
    mat = bpy.data.materials.new(NAME + '_glass')
    mat.use_nodes = True
    nt = mat.node_tree; b = nt.nodes.get('Principled BSDF')
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = img; node.interpolation = C.TEX_INTERP
    nt.links.new(node.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = 0.0
    b.inputs['Roughness'].default_value = 0.10
    b.inputs['Specular IOR Level'].default_value = 0.6
    b.inputs['Alpha'].default_value = 0.80
    try:
        mat.blend_method = 'BLEND'
    except Exception:
        pass
    try:
        mat.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return mat


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('glass', 128, 32), ('poly', 128, 40), ('steel', 48, 32), ('steel_top', 48, 24),
        ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
    ])
    A.install()
    C.ENERGY_REGIONS.clear(); C.ENERGY_REGIONS.add('glass')
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.muzzle('muzzle'); A.brass('brass', engrave=True); A.bone('bone_end', motif=None, rim=False)
    A.poly('poly', seed=43, fine=True)
    paint_glass(A, 'glass')
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_poly_mats(NAME, tex)
    mats.append(glass_mat(mats[0]))

    # ---------------- lower shell: one smooth bulbous polymer moulding (thumbhole + trigger hole) ----------------
    bd = C.Part('body')
    dome_shell(bd, P(SHELL_PX), [P(THUMB_PX), P(TRIG_PX)], HW, bevel=0.0125, bevel_hole=0.0080, crown=CROWN, D=0.040)
    bd.prism(P([(655, 296), (668, 296), (671, 338), (665, 356), (654, 354), (656, 335)]), -0.0018, 0.0018, 'brass', side='brass')   # brass trigger blade

    # ---------------- steel receiver group ----------------
    rc = C.Part('receiver')
    K.shell(rc, P(HOUSE_PX), [P(WINDOW_PX)], 0.0215, region='steel', bevel=0.0055, segs=1, bevel_hole=0.0035)
    zd0, yd0 = T(780, 262); zd1, yd1 = T(600, 243)
    rc.box((-0.0150, yd0, zd0), (0.0150, yd1 + 0.0004, zd1), 'steel', top='steel_top')                                  # deck under the magazine
    # ring sight on the top plate (octagon ring centred on the sight line) + front post with brass bead
    ro, ri, rz0, rz1 = 0.0095, 0.0050, Z_RING - 0.0043, Z_RING + 0.0043
    for k in range(8):
        a0, a1 = math.radians(22.5 + 45 * k), math.radians(22.5 + 45 * (k + 1))
        quad = [(ro * math.cos(a0), Y_SIGHT + ro * math.sin(a0)), (ro * math.cos(a1), Y_SIGHT + ro * math.sin(a1)),
                (ri * math.cos(a1), Y_SIGHT + ri * math.sin(a1)), (ri * math.cos(a0), Y_SIGHT + ri * math.sin(a0))]
        rc.loft([(rz1, quad), (rz0, quad)], 'steel', top='steel_top')
    rc.box((-0.0022, 0.1470, Z_BEAD - 0.0030), (0.0022, Y_SIGHT - 0.0008, Z_BEAD + 0.0030), 'steel', top='steel_top')
    rc.box((-0.0014, Y_SIGHT - 0.0008, Z_BEAD - 0.0016), (0.0014, Y_SIGHT + 0.0004, Z_BEAD + 0.0016), 'brass')
    # round ring-sight caps on both sides of the front block (brass rim, dark centre)
    zc, yc = T(795, 160)
    for sgn in (-1, 1):
        rc.cyl((sgn * 0.0212, yc, zc), (sgn * 0.0229, yc, zc), 0.0115, 12, 'brass', cap='brass')
        rc.cyl((sgn * 0.0228, yc, zc), (sgn * 0.0233, yc, zc), 0.0085, 12, 'muzzle', cap='muzzle')
    # barrel + slotted flash hider
    K.revolve(rc, [(-0.150, 0.0078), (-0.1760, 0.0078)], BY, segs=10, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.1760, 0.0078), (-0.1775, 0.0108), (-0.1860, 0.0108), (-0.1870, 0.0094), (-0.1920, 0.0094), (-0.1930, 0.0108),
                   (-0.2000, 0.0108), (-0.2010, 0.0094), (Z_MUZ, 0.0094)], BY, segs=10, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    # charging handles / rods on both sides under the magazine, rear tabs
    for sgn in (-1, 1):
        rc.cyl((sgn * 0.0262, 0.0440, T(600, 0)[0]), (sgn * 0.0262, 0.0440, T(780, 0)[0]), 0.0044, 8, 'steel', cap='steel')
        zt0, zt1 = T(290, 0)[0], T(335, 0)[0]
        x0, x1 = (0.0200, 0.0318) if sgn > 0 else (-0.0318, -0.0200)
        rc.box((x0, 0.0610, zt1), (x1, 0.0790, zt0), 'steel', top='steel_top')
        rc.cyl((sgn * 0.0262, 0.0440, T(780, 0)[0]), (sgn * 0.0262, 0.0440, T(790, 0)[0]), 0.0066, 8, 'steel', cap='steel')

    # ---------------- translucent top magazine ----------------
    mg = C.Part('magazine')
    zm0, ym1 = T(335, 210); zm1, ym0 = T(770, 243)
    mg.box((-0.0185, ym0, zm1), (0.0185, ym1, zm0), 'glass')
    for i in range(12):
        zr = zm0 - 0.0105 - i * 0.0210
        mg.cyl((-0.0160, (ym0 + ym1) / 2, zr), (0.0160, (ym0 + ym1) / 2, zr), 0.0050, 5, 'brass', cap='brass')

    objs = {}
    for p, ml in ((bd, 0.9), (rc, 0.020), (mg, 0.9)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p is bd else 35))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('smg_bullpup', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_RING),
        'front_sight': (0, Y_SIGHT, Z_BEAD),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'smg_bullpup', relief=0.14)


if __name__ == '__main__':
    K.run(finish, render, NAME)
