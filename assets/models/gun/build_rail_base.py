"""Crimson Plague VR - sniper_rail_base: the Rail Rifle (original gothic coil-rail sniper).

Original design (refs are mood only: hand-built coilgun photos): slab steel receiver with engraved gothic panels and
exposed brass capacitor tubes, two long parallel steel rails with brass accelerator coils wrapped around them, a thin
bore line between the rails and a dark emitter cap at the muzzle, glossy near-black clearcoat polymer skeleton stock
(real cut-out, one grain map) + raked pistol grip (bullpup polish3 recipe), slender gothic scope, battery cell
magazine. Blued steel on the locked 1911 metal material, brass coils/bands, bone cross badge in the butt.
One 1024 px smooth albedo, sampler LINEAR.

Meshes: receiver (body, rails, coils, emitter, scope, capacitors, guard), furniture (stock, grip), magazine (battery cell).
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

STOCK = [(0.050, 0.0940), (0.200, 0.0940), (0.255, 0.1010), (0.320, 0.0990), (0.375, 0.0840), (0.397, 0.0000), (0.392, -0.0420), (0.362, -0.0640),
         (0.300, -0.0450), (0.220, -0.0180), (0.140, 0.0000), (0.050, 0.0320)]
HOLE = [(0.335, 0.0780), (0.170, 0.0790), (0.108, 0.0600), (0.140, 0.0170), (0.220, -0.0020), (0.300, -0.0290), (0.345, -0.0290)]
GRIP = [(0.112, 0.0400), (0.104, 0.0100), (0.090, -0.0300), (0.070, -0.0700), (0.040, -0.0680), (0.043, -0.0350), (0.030, -0.0050), (0.016, 0.0400)]


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('tube', 128, 48), ('panel', 112, 36), ('port', 56, 28), ('poly', 128, 40), ('mag', 96, 32),
        ('bone_stock', 40, 40), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=12, lam=26, grime=0.84, arches=True)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.wrap('tube', 8, 6, lambda j: 'eng' if j in (0, 4) else 'hi' if j == 2 else 'dark' if j == 6 else 'plain', seed=17, lam=16)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    A.poly('poly', seed=43, fine=True); S.paint_port(A, 'port'); A.mag('mag', holes=True)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_poly_mats(NAME, tex)

    # ---------------- receiver ----------------
    rc = C.Part('receiver')
    rb = K.hexp(-0.0210, 0.0210, 0.0320, 0.0940, 0.0110)
    rc.loft([(0.050, rb), (-0.340, rb)], 'steel', top='steel_top')
    rc.box((-0.0080, 0.0936, -0.320), (0.0080, 0.0960, 0.040), 'steel', top='steel_top')                       # top spine
    for sgn in (-1, 1):
        a_, b_ = (0.0206, 0.0222) if sgn > 0 else (-0.0222, -0.0206)
        rc.prism(S.cham(-0.300, -0.060, 0.0560, 0.0850, 0.005), a_, b_, 'panel', side='steel', top='steel_top')
        rc.prism(S.cham(-0.050, 0.020, 0.0460, 0.0720, 0.004), a_, b_, 'port', side='steel', top='steel_top')
        for zc in (-0.3250, 0.0300):
            x0, x1 = (0.0204, 0.0228) if sgn > 0 else (-0.0228, -0.0204)
            rc.box((x0, 0.0330, zc - 0.0030), (x1, 0.0950, zc + 0.0030), 'brass')
        rc.cyl((sgn * 0.0262, 0.0520, -0.285), (sgn * 0.0262, 0.0520, -0.005), 0.0075, 10, 'tube', cap='brass')   # exposed capacitor tubes
        rc.cyl((sgn * 0.0262, 0.0700, -0.285), (sgn * 0.0262, 0.0700, -0.005), 0.0075, 10, 'tube', cap='brass')
    # twin accelerator rails + bore line + coils + emitter
    for sgn in (-1, 1):
        rr = K.hexp(sgn * 0.0125 - 0.0045, sgn * 0.0125 + 0.0045, BY - 0.0110, BY + 0.0150, 0.0035)
        rc.loft([(-0.340, rr), (-0.960, rr)], 'steel', top='steel_top')
    K.revolve(rc, [(-0.340, 0.0060), (-0.980, 0.0060)], BY, segs=8, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    for i in range(8):
        z0 = -0.385 - i * 0.0700
        K.revolve(rc, [(z0, 0.0245), (z0 - 0.0300, 0.0245)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    K.revolve(rc, [(-0.9500, 0.0170), (-0.9560, 0.0235), (-0.9940, 0.0235), (Z_MUZ, 0.0170)], BY, segs=12, region='steel', cap_f='muzzle', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.9580, 0.0242), (-0.9620, 0.0242)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    SN.scope(rc, Y_SIGHT, Z_OC, Z_OBJ, r=0.0120, big=0.0200, rings=(0.25, 0.70), y_base=0.0920, base_w=0.0120)
    K.tube(rc, [(0.0560, 0.0300), (0.0540, 0.0080), (0.0450, -0.0200), (0.0200, -0.0250), (-0.0050, -0.0160), (-0.0070, 0.0300)], 0.0090, 0.0060, 'steel')
    rc.prism([(0.0330, 0.0320), (0.0270, 0.0320), (0.0275, 0.0150), (0.0300, 0.0030), (0.0350, 0.0030), (0.0340, 0.0150)], -0.0016, 0.0016, 'brass', side='brass')

    # ---------------- polymer furniture ----------------
    fu = C.Part('furniture')
    K.shell(fu, K.chaikin(STOCK, 1), [HOLE], 0.0120, region='poly', bevel=0.0045, segs=2, bevel_hole=0.0035, gmap=True)
    K.shell(fu, K.chaikin(GRIP, 1), [], 0.0135, region='poly', bevel=0.0050, segs=2, gmap=True)
    for sgn in (-1, 1):
        x0, x1 = (0.0120 - 0.0005, 0.0120 + 0.0016) if sgn > 0 else (-0.0120 - 0.0016, -0.0120 + 0.0005)
        fu.cyl((x0, 0.0200, 0.3700), (x1, 0.0200, 0.3700), 0.0150, 12, 'brass', cap='bone_stock')
    fu.box((-0.0125, -0.0660, 0.3600), (0.0125, -0.0630, 0.3980), 'brass')                                       # brass heel strap

    # ---------------- battery cell magazine ----------------
    mg = C.Part('magazine')
    mg.prism(S.cham(-0.185, -0.125, -0.0450, 0.0330, 0.005), -0.0150, 0.0150, 'mag', side='steel')
    mg.box((-0.0158, -0.0470, -0.1880), (0.0158, -0.0420, -0.1220), 'brass')
    mg.box((-0.0158, 0.0020, -0.1880), (0.0158, 0.0070, -0.1220), 'brass')

    objs = {}
    for p, ml in ((rc, 0.022), (fu, 0.020), (mg, 0.012)):
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
