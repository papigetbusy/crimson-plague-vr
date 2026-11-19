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
    """ribcage: 6 bone hoops sweeping forward at the bottom, bone sternum bar, dark core, gold sternum spire; returns (bone_bm, gold_bm, core_bm)"""
    M = _M(); S = _S()
    bone = bmesh.new(); M._tex_layer(bone)
    gold = bmesh.new(); M._tex_layer(gold)
    core = bmesh.new(); M._tex_layer(core)
    yc = M.Y_SLIDE_BOT + 0.0008
    a, b = 0.0111, 0.0138
    zs = [-0.1515 + i * 0.0134 for i in range(6)]
    for z0 in zs:
        pts = []
        n = 9
        for k in range(n):
            t = k / (n - 1)
            ang = math.pi * t                       # 0 .. pi : right attach -> bottom -> left attach
            x = a * math.cos(ang); depth = math.sin(ang)
            y = yc - b * depth
            z = z0 - 0.0085 * depth ** 1.3        # ribs bow forward toward the sternum
            pts.append((x, y, z))
        r = 0.00165
        S.tube_path(bone, pts, [r * 0.55, r * 0.9, r, r, r, r, r, r * 0.9, r * 0.55], [r * 0.55, r * 0.9, r, r, r, r, r, r * 0.9, r * 0.55], segs=7, tex='bone', up=(0, 1, 0), caps=(True, True))
    # sternum bar
    S.tube_path(bone, [(0, yc - b + 0.0004, -0.1700), (0, yc - b + 0.0004, -0.1560), (0, yc - b + 0.0004, -0.0900), (0, yc - b + 0.0004, -0.0820)],
                [0.0020, 0.0033, 0.0033, 0.0022], [0.0020, 0.0030, 0.0030, 0.0020], segs=10, tex='bone', up=(0, 1, 0))
    # gold sternum spire (points forward under the barrel)
    S.tube_path(gold, [(0, yc - b + 0.0004, -0.1650), (0, yc - b + 0.0010, -0.1780), (0, yc - b + 0.0022, -0.1900), (0, yc - b + 0.0035, -0.1985)],
                [0.0034, 0.0026, 0.0015, 0.00008], [0.0024, 0.0019, 0.0011, 0.00008], segs=8, tex='gold', up=(0, 1, 0))
    # dark core so the cage is not see-through
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
    outer = S.lancet_up(zc, 0.0498, 0.0598, 0.0716, 0.0072)
    hole = S.lancet_up(zc, 0.0528, 0.0598, 0.0668, 0.0034)
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
    ptsca = S.lancet_pts(0.0, a_bot, -0.0105, a_top, hw, n=12)      # (c, a): base-left, arch, base-right
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
    pts = S.lancet_pts(0.0, 0.0420, -0.0100, -0.0262, 0.0136, n=10)
    path = []
    for c, a in pts:
        z = c * math.cos(th) + a * math.sin(th); y = c * math.sin(th) - a * math.cos(th)
        path.append((xo, y, z))
    r = 0.00062
    S.tube_path(bm, path, [r] * len(path), [r * 0.8] * len(path), segs=4, tex='gold', up=(1, 0, 0), caps=(True, True))
    return bm

def rune_ribbons(side):
    """emissive crimson rune strokes on the slide wall (side +1 right / -1 left)"""
    M = _M(); S = _S()
    import camo_1911_layout as LY
    bm = bmesh.new(); M._tex_layer(bm)
    z0, z1 = LY.SLIDE_Z; y0, y1 = LY.SLIDE_Y
    sd = 'R' if side > 0 else 'L'
    x = side * (M.SLIDE_W * 0.5 + 0.00018)
    def pos(px, py):
        uu = px / RN.W; vv = 1.0 - py / RN.H
        z = (z1 - uu * (z1 - z0)) if sd == 'R' else (z0 + uu * (z1 - z0))
        return (x, y0 + vv * (y1 - y0), z)
    for (a, b) in RN.strokes(sd):
        S.tube_path(bm, [pos(*a), pos(*b)], 0.00042, 0.00030, segs=4, tex='crimson', up=(1, 0, 0), caps=(False, False), phase=math.pi / 4)
    return bm

def add_legendary(SBm, add_base, add_new, groups):
    bone, gold, core = cage_parts()
    add_new('rib_cage', bone, 'frame'); add_new('sternum_spire', gold, 'frame'); add_new('cage_core', core, 'frame')
    mg, mb, tip = muzzle_spire()
    add_new('spire_muzzle', mg, 'frame'); add_new('spire_fins', mb, 'frame')
    for sd in (1, -1):
        add_new('panel_ridge_%d' % sd, panel_ridge(sd), 'frame')
        add_new('runes_%d' % sd, rune_ribbons(sd), 'slide')
    return tip
