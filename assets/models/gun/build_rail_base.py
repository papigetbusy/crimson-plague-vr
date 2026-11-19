"""Crimson Plague VR - sniper_rail_base: the Rail Rifle (original gothic coil-rail sniper, v2 showpiece).

Original design (refs are mood only): a glowing crimson EMISSIVE energy channel runs the full length between twin
parallel steel rails (top and bottom), wrapped in four packs of real helical copper-wire coils (swept round wire, not
rings). Gothic ribbed steel receiver with glowing crimson slits between the ribs, bone/ivory lancet inlays, bone cross
badge in a solid sculpted glossy near-black polymer stock (bullpup polish3 recipe), raked finger-groove pistol grip,
slender scope, glowing battery-cell magazine, bone-ringed emitter muzzle with a crimson core.

Materials (3): locked 1911 steel (metallic 1 / roughness 0.30; also the copper + brass), glossy polymer + bone, and a
crimson emissive energy material (same atlas; region 'energy' is painted hot crimson so it still reads red if a loader
ignores emission). One 1024 px smooth albedo, sampler LINEAR.

Meshes: receiver (body, ribs, rails, channel, coils, emitter, scope, guard), furniture (stock, grip, bone inlays), magazine.
Empties: muzzle, mag_well, rear_sight (scope ocular), front_sight (scope objective), on the scope axis parallel to the bore.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_sniper_common as SN
S, K, C, M, G = SN.S, SN.K, SN.C, SN.M, SN.G

NAME = 'sniper_rail_base'
BY = 0.062
Y_SIGHT = 0.1300
Z_OC, Z_OBJ = 0.035, -0.255
Z_MUZ = -1.000
PH = -math.pi / 12
MAGW = (0.0, 0.0320, -0.1550)

STOCK = [(0.050, 0.0940), (0.170, 0.0940), (0.230, 0.1010), (0.300, 0.1020), (0.360, 0.0950), (0.398, 0.0820), (0.404, 0.0100), (0.398, -0.0380),
         (0.372, -0.0600), (0.330, -0.0540), (0.270, -0.0420), (0.200, -0.0280), (0.130, -0.0150), (0.050, 0.0100)]
RK = math.radians(20)


def _gp(u, v, z0=0.066, y0=0.0340):
    return (round(z0 + u * math.sin(RK) + v * math.cos(RK), 4), round(y0 - u * math.cos(RK) + v * math.sin(RK), 4))


_FRONT = [(0.000, -0.0150), (0.016, -0.0165), (0.030, -0.0165), (0.040, -0.0125), (0.052, -0.0165), (0.064, -0.0165), (0.074, -0.0125),
          (0.086, -0.0165), (0.098, -0.0165), (0.108, -0.0135), (0.118, -0.0140)]
_BACK = [(0.118, 0.0150), (0.104, 0.0178), (0.084, 0.0168), (0.062, 0.0158), (0.040, 0.0168), (0.020, 0.0200), (0.000, 0.0180)]
GRIP = [_gp(u, v) for u, v in _FRONT + _BACK]


def _ov(A):
    import numpy as np
    if not hasattr(A, 'overlay'):
        A.overlay = np.zeros((256, 256, 3), dtype=np.float32); A.overlay_regions = []
    return A.overlay


def paint_copper(A, r):
    import numpy as np
    ov = _ov(A); A.overlay_regions.append(r)
    x0, y0, x1, y1 = A.reg[r]; h = y1 - y0
    ramp = [(88, 44, 20), (150, 82, 40), (194, 112, 58), (214, 128, 70), (246, 178, 120), (200, 116, 60), (150, 82, 40), (96, 50, 24)]
    for y in range(y0, y1):
        t = (y - y0) / max(1, h - 1)
        c = ramp[min(len(ramp) - 1, int(t * len(ramp)))]
        for x in range(x0, x1):
            n = K._vn(x, y, 5, 91)
            ov[y, x] = [max(0, min(255, v * (0.9 + 0.2 * n))) for v in c]


def paint_energy(A, r):
    ov = _ov(A); A.overlay_regions.append(r)
    x0, y0, x1, y1 = A.reg[r]; h = y1 - y0
    for y in range(y0, y1):
        t = abs((y - y0) / max(1, h - 1) - 0.5) * 2
        for x in range(x0, x1):
            n = 0.94 + 0.12 * K._vn(x, y, 4, 93)
            core = 1.0 - min(1.0, t * 1.15)
            ov[y, x] = [min(255, (150 + 74 * core) * n), min(255, (3 + 34 * core * core) * n), min(255, (14 + 30 * core) * n)]


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('tube', 128, 48), ('panel', 112, 36), ('poly', 128, 40), ('mag', 96, 32),
        ('bone_stock', 40, 40), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
        ('copper', 24, 24), ('energy', 24, 24),
    ])
    A.install()
    C.ENERGY_REGIONS.clear(); C.ENERGY_REGIONS.add('energy')
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=12, lam=26, grime=0.84, arches=True)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.wrap('tube', 8, 6, lambda j: 'eng' if j in (0, 4) else 'hi' if j == 2 else 'dark' if j == 6 else 'plain', seed=17, lam=16)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    A.poly('poly', seed=43, fine=True); A.mag('mag', holes=True)
    paint_copper(A, 'copper'); paint_energy(A, 'energy')
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_poly_mats(NAME, tex)
    mats.append(SN.energy_mat(mats[0]))

    # ---------------- receiver: gothic ribbed housing ----------------
    rc = C.Part('receiver')
    rb = K.hexp(-0.0210, 0.0210, 0.0320, 0.0940, 0.0110)
    rc.loft([(0.095, rb), (-0.340, rb)], 'steel', top='steel_top')
    rc.box((-0.0080, 0.0936, -0.320), (0.0080, 0.0962, 0.080), 'steel', top='steel_top')                       # top spine
    for sgn in (-1, 1):
        for i in range(7):
            zc = -0.050 - i * 0.0400
            x0, x1 = (0.0206, 0.0230) if sgn > 0 else (-0.0230, -0.0206)
            rc.box((x0, 0.0390, zc - 0.0040), (x1, 0.0880, zc + 0.0040), 'steel', top='steel_top')            # gothic ribs
        a_, b_ = (0.0207, 0.0216) if sgn > 0 else (-0.0216, -0.0207)
        rc.box((a_, 0.0480, -0.290), (b_, 0.0560, -0.020), 'energy')                                        # crimson glow slit between the ribs
        for zc in (-0.3280, 0.0900):
            x0, x1 = (0.0204, 0.0228) if sgn > 0 else (-0.0228, -0.0204)
            rc.box((x0, 0.0330, zc - 0.0026), (x1, 0.0935, zc + 0.0026), 'brass')
    # twin parallel rails (top / bottom) with the crimson energy channel between them
    for sgn in (-1, 1):
        rr = K.hexp(-0.0110, 0.0110, BY + sgn * 0.0185 - 0.0055, BY + sgn * 0.0185 + 0.0055, 0.0030)
        rc.loft([(-0.340, rr), (-0.945, rr)], 'steel', top='steel_top')
    rc.box((-0.0095, BY - 0.0135, -0.340), (0.0095, BY + 0.0135, -0.9450), 'energy')
    # real wound copper coils (helical wire) in four packs, brass cheeks at the pack ends
    for z0 in (-0.390, -0.545, -0.700, -0.855):
        SN.coil(rc, BY, 0.0310, 0.0058, z0, z0 - 0.0800, 0.0200, pts_per_turn=6, segs=4, region='copper')
    # emitter: steel block, bone ring, glowing crimson core
    eb = K.hexp(-0.0170, 0.0170, BY - 0.0300, BY + 0.0300, 0.0100)
    rc.loft([(-0.9450, eb), (-0.9950, eb)], 'steel', top='steel_top')
    eb2 = K.hexp(-0.0182, 0.0182, BY - 0.0312, BY + 0.0312, 0.0105)
    rc.loft([(-0.9500, eb2), (-0.9570, eb2)], 'bone_end')
    rc.cyl((0, BY, -0.9940), (0, BY, Z_MUZ), 0.0105, 10, 'energy', cap='energy')
    SN.scope(rc, Y_SIGHT, Z_OC, Z_OBJ, r=0.0120, big=0.0200, rings=(0.25, 0.70), y_base=0.0920, base_w=0.0120)
    K.tube(rc, [(0.0500, 0.0300), (0.0480, 0.0080), (0.0400, -0.0190), (0.0150, -0.0250), (-0.0050, -0.0160), (-0.0070, 0.0300)], 0.0090, 0.0060, 'steel')
    rc.prism([(0.0330, 0.0320), (0.0270, 0.0320), (0.0275, 0.0150), (0.0300, 0.0030), (0.0350, 0.0030), (0.0340, 0.0150)], -0.0016, 0.0016, 'brass', side='brass')

    # ---------------- solid sculpted polymer furniture + bone ----------------
    fu = C.Part('furniture')
    K.shell(fu, K.chaikin(STOCK, 1), [], 0.0140, region='poly', bevel=0.0060, segs=2, gmap=True)
    K.shell(fu, GRIP, [], 0.0140, region='poly', bevel=0.0045, segs=2, gmap=True)
    for sgn in (-1, 1):
        x0, x1 = (0.0140 - 0.0005, 0.0140 + 0.0016) if sgn > 0 else (-0.0140 - 0.0016, -0.0140 + 0.0005)
        fu.cyl((x0, 0.0300, 0.3500), (x1, 0.0300, 0.3500), 0.0170, 12, 'brass', cap='bone_stock')              # brass-rimmed bone cross badge
        a_, b_ = (0.0206, 0.0222) if sgn > 0 else (-0.0222, -0.0206)
        fu.prism([(0.0880, 0.0420), (0.0880, 0.0740), (0.0740, 0.0870), (0.0600, 0.0740), (0.0600, 0.0420)], a_, b_, 'bone_end', side='bone_end')   # bone lancet inlay
    fu.box((-0.0150, -0.0740, 0.3500), (0.0150, -0.0690, 0.4000), 'brass')                                       # brass heel strap

    # ---------------- glowing battery cell magazine ----------------
    mg = C.Part('magazine')
    mg.prism(S.cham(-0.185, -0.125, -0.0450, 0.0330, 0.005), -0.0150, 0.0150, 'mag', side='steel')
    mg.box((-0.0158, -0.0470, -0.1880), (0.0158, -0.0420, -0.1220), 'brass')
    mg.box((-0.0158, 0.0020, -0.1880), (0.0158, 0.0070, -0.1220), 'brass')
    for sgn in (-1, 1):
        a_, b_ = (0.0148, 0.0158) if sgn > 0 else (-0.0158, -0.0148)
        mg.box((a_, -0.0300, -0.1760), (b_, 0.0000, -0.1340), 'energy')                                      # glowing cell window

    objs = {}
    for p, ml in ((rc, 0.060), (fu, 0.020), (mg, 0.012)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p is fu else 35))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('sniper_rail', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_OC),
        'front_sight': (0, Y_SIGHT, Z_OBJ),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'sniper_rail', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
