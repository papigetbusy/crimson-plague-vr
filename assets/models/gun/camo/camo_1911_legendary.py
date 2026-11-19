"""LEGENDARY 1911 'reliquary' parts: ribcage dust-cover cage, spired muzzle, pierced-lancet spire hammer, cathedral-arch grip panels,
emissive crimson rune ribbons. Called from camo_1911_shape_build.build()."""
import math
import bmesh
from mathutils import Vector
import camo_1911_runes as RN

SB = None
def init(sb):
    global SB
    SB = sb

def _M(): return SB.M
def _S(): return SB.S

def legendary_frame():
    """rear frame + a short solid dust-cover stub; the rest of the dust cover is the rib cage."""
    M = _M()
    bm = bmesh.new(); M._tex_layer(bm)
    y_bot = M.Y_FRAME_BOT; y_top = M.Y_SLIDE_BOT + 0.0004
    zfs = (M.GRIP_TOP - M.BACK * (M.GRIP_THICK * 0.5)).z
    zrear = M.Z_SLIDE_REAR - 0.002
    M.add_box(bm, center=(0, (y_bot + y_top) * 0.5, (zfs + zrear) * 0.5), size=(M.FRAME_W, y_top - y_bot, zrear - zfs), tex='steel_dark', chamfer=0.0006)
    zst = -0.0780
    M.add_box(bm, center=(0, (y_bot + y_top) * 0.5, (zst + zfs) * 0.5), size=(M.FRAME_W, y_top - y_bot, zfs - zst), tex='steel_dark', chamfer=0.0008)
    return bm

def cage_parts():
    """ribcage handguard: staggered, tapered, curved ribs (aged bone texture) that sweep forward and join a beaded sternum spine.
    returns (bone_bm, gold_bm, core_bm)"""
    M = _M(); S = _S()
    bone = bmesh.new(); M._tex_layer(bone)
    gold = bmesh.new(); M._tex_layer(gold)
    core = bmesh.new(); M._tex_layer(core)
    yc = M.Y_SLIDE_BOT + 0.0008
    b = 0.0138
    ys = yc - b + 0.0004
    zs = [-0.1500, -0.1375, -0.1250, -0.1125, -0.1000, -0.0875]
    amp = [0.0128, 0.0146, 0.0160, 0.0160, 0.0150, 0.0136]
    a_ = 0.0128
    for j in range(7):
        z0 = -0.1500 + 0.0115 * j
        pts = []
        n = 9
        for k in range(n):
            ph = math.pi * k / (n - 1)
            pts.append((a_ * math.cos(ph), yc - b * math.sin(ph), z0 - 0.0085 * math.sin(ph) ** 1.3))
        r = 0.0021
        prof = [0.62, 0.92, 1.0, 1.0, 1.0, 1.0, 1.0, 0.92, 0.62]
        S.tube_path(bone, pts, [r * q for q in prof], [r * 0.85 * q for q in prof], segs=7, tex='bonetex', up=(0, 1, 0), caps=(True, True), phase=math.pi / 7)
    # beaded sternum spine joining the ribs
    zst = [-0.1700 + 0.0050 * i for i in range(17)]
    pts = [(0, ys, z) for z in zst]
    rx = [0.0030 if i % 2 == 0 else 0.0019 for i in range(17)]; ry = [0.0028 if i % 2 == 0 else 0.0018 for i in range(17)]
    S.tube_path(bone, pts, rx, ry, segs=6, tex='bonetex', up=(0, 1, 0), phase=math.pi / 6)
    # gold sternum spire pointing forward under the barrel
    S.tube_path(gold, [(0, ys, -0.1700), (0, ys + 0.0006, -0.1800), (0, ys + 0.0018, -0.1900), (0, ys + 0.0032, -0.1985)],
                [0.0034, 0.0026, 0.0015, 0.00008], [0.0024, 0.0019, 0.0011, 0.00008], segs=8, tex='gold', up=(0, 1, 0))
    S.box(core, (0, M.Y_SLIDE_BOT - 0.0058, -0.1200), (0.0100, 0.0128, 0.0800), bevel=0.0010, segs=1, tex='black')
    return bone, gold, core

def muzzle_spire():
    """gothic pinnacle muzzle: stepped octagonal tiers, bore through the middle, 4 bone flying-buttress fins. returns (gold_bm, bone_bm, tip_z)"""
    M = _M(); S = _S()
    YB = M.Y_BORE
    gold = bmesh.new(); M._tex_layer(gold)
    st = [(-0.2235, 0.0050), (-0.2215, 0.0040), (-0.2060, 0.0050), (-0.2056, 0.0064), (-0.1990, 0.0064), (-0.1985, 0.0076),
          (-0.1900, 0.0084), (-0.1892, 0.0096), (-0.1800, 0.0096), (-0.1765, 0.0080)]
    S.lathe_z(gold, st, 0.0, YB, segs=16, tex='gold', inner=0.0032, phase=math.pi / 16)
    bone = bmesh.new(); M._tex_layer(bone)
    # pinnacle crown: four slender bone spires rising forward past the muzzle face, plus small gold crockets
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        d = Vector((sx, sy, 0)).normalized()
        r0 = 0.0069
        S.tube_path(bone, [(d.x * r0, YB + d.y * r0, -0.2010), (d.x * r0, YB + d.y * r0, -0.2150), (d.x * r0 * 0.93, YB + d.y * r0 * 0.93, -0.2260), (d.x * r0 * 0.86, YB + d.y * r0 * 0.86, -0.2345)],
                    [0.0019, 0.0016, 0.0010, 0.00008], [0.0019, 0.0016, 0.0010, 0.00008], segs=7, tex='bone', up=(d.x, d.y, 0))
        for zz, sc in ((-0.2150, 1.0), (-0.2250, 0.8)):
            S.tube_path(gold, [(d.x * r0 * 0.96, YB + d.y * r0 * 0.96, zz), (d.x * r0 * 1.40, YB + d.y * r0 * 1.40, zz - 0.0012 * sc)], [0.0007, 0.00006], [0.0007, 0.00006], segs=5, tex='gold', up=(0, 0, 1))
    return gold, bone, -0.2238

def hammer_spire():
    M = _M(); S = _S()
    bm = bmesh.new(); M._tex_layer(bm)
    zc = 0.0278
    outer = S.lancet_up(zc, 0.0498, 0.0598, 0.0716, 0.0072, n=8)
    hole = S.lancet_up(zc, 0.0528, 0.0598, 0.0668, 0.0034, n=8)
    hole = [(z, y) for z, y in hole][::-1]
    S.extrude_zy(bm, outer, -0.0034, 0.0034, tex='gold', bevel=0.0006, segs=1, holes=[hole])
    S.tube_path(bm, [(0, 0.0712, zc), (0, 0.0724, zc), (0, 0.0734, zc)], [0.0016, 0.0009, 0.00008], [0.0016, 0.0009, 0.00008], segs=6, tex='gold', up=(0, 0, 1))
    S.box(bm, (0, 0.0560, M.Z_SLIDE_REAR + 0.0008), (0.0090, 0.0100, 0.0040), bevel=0.0006, segs=1, tex='gold_dark')
    return bm

def panel(side):
    """cathedral-arch grip panel: pointed-arch top, beveled slab; returns bm (ivory material via part key)."""
    M = _M(); S = _S()
    bm = bmesh.new(); M._tex_layer(bm)
    th = math.radians(18.0)
    def zy(c, a):   # grip space (across BACK, along DOWN) -> game (z, y)
        return (c * math.cos(th) + a * math.sin(th), c * math.sin(th) - a * math.cos(th))
    a_top, a_bot = -0.0300, 0.0480
    hw = 0.01766
    ptsca = S.lancet_pts(0.0, a_bot, -0.0105, a_top, hw, n=8)      # (c, a): base-left, arch, base-right
    poly = [zy(c, a) for c, a in ptsca]
    # bottom corners rounded by a small chamfer: cut the two lowest corners
    poly = [zy(c, a) for c, a in _round_bottom(ptsca, 0.0045)]
    x0 = side * (M.GRIP_FRAME_W * 0.5 - 0.0009); x1 = side * (M.GRIP_FRAME_W * 0.5 + 0.0036 - 0.0015 + 0.0018)
    xa, xb = (x0, x1) if side > 0 else (x1, x0)
    # a = along DOWN measured from the palm origin: zy() gives positions relative to the origin (palm), same as build_panel's frame
    S.extrude_zy(bm, poly if side > 0 else poly[::-1], min(xa, xb), max(xa, xb), tex='bone', bevel=0.0008, segs=1)
    return bm

def _round_bottom(pts, r):
    out = []
    n = len(pts)
    for i, (c, a) in enumerate(pts):
        if i == 0:      out += [(c + r, a), (c, a - r)]
        elif i == n - 1: out += [(c, a - r), (c - r, a)]
        else: out.append((c, a))
    return out

def panel_ridge(side):
    """raised gold pointed-arch ridge on the outer face of the grip panel"""
    M = _M(); S = _S()
    bm = bmesh.new(); M._tex_layer(bm)
    th = math.radians(18.0)
    xo = side * (M.GRIP_FRAME_W * 0.5 + 0.0036 - 0.0015 + 0.0018 + 0.0002)
    pts = S.lancet_pts(0.0, 0.0420, -0.0100, -0.0262, 0.0136, n=6)
    path = []
    for c, a in pts:
        z = c * math.cos(th) + a * math.sin(th); y = c * math.sin(th) - a * math.cos(th)
        path.append((xo, y, z))
    r = 0.00062
    S.tube_path(bm, path, [r] * len(path), [r * 0.8] * len(path), segs=3, tex='gold', up=(1, 0, 0), caps=(True, True))
    return bm

def rune_ribbons(side):
    """emissive crimson sigil strokes (2.4 mm wide flat ribbons, 0.3 mm proud of the slide wall); side +1 right / -1 left"""
    M = _M(); S = _S()
    import camo_1911_layout as LY
    bm = bmesh.new(); M._tex_layer(bm)
    z0, z1 = LY.SLIDE_Z; y0, y1 = LY.SLIDE_Y
    sd = 'R' if side > 0 else 'L'
    x = side * (M.SLIDE_W * 0.5 + 0.00012)
    hw = 0.00090
    def pos(px, py):
        uu = px / RN.W; vv = 1.0 - py / RN.H
        z = (z1 - uu * (z1 - z0)) if sd == 'R' else (z0 + uu * (z1 - z0))
        return (y0 + vv * (y1 - y0), z)
    for pl in RN.polylines(sd):
        P = [pos(*p) for p in pl]
        before = set(bm.faces)
        nrm = []
        for i in range(len(P)):
            a_ = P[max(i - 1, 0)]; b_ = P[min(i + 1, len(P) - 1)]
            dy, dz = b_[0] - a_[0], b_[1] - a_[1]
            L = math.hypot(dy, dz) or 1.0
            nrm.append((-dz / L, dy / L))
        L_, R_ = [], []
        for (yy, zz), (ny, nz) in zip(P, nrm):
            L_.append(bm.verts.new(M.G(x, yy + ny * hw, zz + nz * hw))); R_.append(bm.verts.new(M.G(x, yy - ny * hw, zz - nz * hw)))
        for i in range(len(P) - 1):
            bm.faces.new((L_[i], L_[i + 1], R_[i + 1], R_[i]))
        new = [f for f in bm.faces if f not in before]
        bmesh.ops.recalc_face_normals(bm, faces=new)
        if sum(f.normal.x for f in new) * side < 0: bmesh.ops.reverse_faces(bm, faces=new)
        S._tag_faces(bm, new, 'crimson')
    return bm

def relic_window(side):
    """sealed reliquary window on the frame: gold lancet bezel + faceted crimson relic crystal (emissive)"""
    M = _M(); S = _S()
    bez = bmesh.new(); M._tex_layer(bez)
    xs = side * (M.FRAME_W * 0.5)
    zc = -0.0560
    outer = S.lancet_up(zc, 0.0358, 0.0420, 0.0470, 0.0070, n=6)
    hole = S.lancet_up(zc, 0.0372, 0.0420, 0.0454, 0.0050, n=6)[::-1]
    x0, x1 = (xs - side * 0.0004, xs + side * 0.0016)
    S.extrude_zy(bez, outer, min(x0, x1), max(x0, x1), tex='gold', bevel=0.0003, segs=1, holes=[hole])
    gem = bmesh.new(); M._tex_layer(gem)
    xo = xs + side * 0.0004; xr = xs + side * 0.0017
    P = [(xo, 0.0380, zc - 0.0030), (xo, 0.0380, zc + 0.0030), (xo, 0.0412, zc - 0.0042), (xo, 0.0412, zc + 0.0042), (xo, 0.0444, zc - 0.0028), (xo, 0.0444, zc + 0.0028),
         (xo, 0.0366, zc), (xo, 0.0458, zc), (xr, 0.0398, zc), (xr, 0.0426, zc)]
    import camo_1911_epic2 as E2
    E2.init(SB); E2.hull_bm(P, 'crimson', gem)
    return bez, gem

def gold_spur():
    """spired gold beavertail: a swept gothic blade rising behind the frame"""
    M = _M(); S = _S()
    bm = bmesh.new(); M._tex_layer(bm)
    poly = [(0.0100, 0.0385), (0.0300, 0.0396), (0.0480, 0.0420), (0.0600, 0.0462), (0.0668, 0.0524), (0.0600, 0.0496), (0.0480, 0.0462), (0.0300, 0.0446), (0.0160, 0.0452), (0.0100, 0.0476)]
    S.extrude_zy(bm, poly, -0.0046, 0.0046, tex='gold', bevel=0.0007, segs=1)
    return bm

def add_legendary(SBm, add_base, add_new, groups):
    bone, gold, core = cage_parts()
    add_new('rib_cage', bone, 'frame'); add_new('sternum_spire', gold, 'frame'); add_new('cage_core', core, 'frame')
    mg, mb, tip = muzzle_spire()
    add_new('spire_muzzle', mg, 'frame'); add_new('spire_fins', mb, 'frame')
    for sd in (1, -1):
        add_new('panel_ridge_%d' % sd, panel_ridge(sd), 'frame')
        add_new('sigils_%d' % sd, rune_ribbons(sd), 'slide')
        bz, gm = relic_window(sd)
        add_new('relic_bezel_%d' % sd, bz, 'frame'); add_new('relic_gem_%d' % sd, gm, 'frame')
    add_new('gold_spur', gold_spur(), 'frame')
    return tip
