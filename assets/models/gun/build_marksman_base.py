"""Crimson Plague VR - sniper_marksman_base: the Marksman Rifle (SVD Dragunov silhouette).

Original low-poly PS2 / Snake Eater style designated-marksman rifle. Proportions and the thumbhole stock outline are
traced from the SVD photo in /workspace/gun_brief/refs/sniper_marksman: skeleton thumbhole stock with a real
thumbhole + lightening hole (K.shell with holes, one continuous grain map), slotted wood handguard, black AK-style
receiver with dust-cover ridge, thin barrel with gas tube + slotted flash hider, PSO-style side-mount scope, curved
10-round box magazine. Blued engraved steel on the locked 1911 metal material, satin walnut + bone cross badge on one
non-metal material, brass bands. One 1024 px smooth albedo, sampler LINEAR.

Meshes: receiver, furniture (stock + handguard), magazine. Empties: muzzle, mag_well, rear_sight (scope ocular),
front_sight (scope objective), all on the scope axis X=0 parallel to the bore.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_sniper_common as SN
S, K, C, M, G = SN.S, SN.K, SN.C, SN.M, SN.G

NAME = 'sniper_marksman_base'
BY = 0.052
Y_SIGHT = 0.1205
Z_OC, Z_OBJ = -0.027, -0.323
Z_MUZ = -0.9926
PH = -math.pi / 12
MAGW = (0.0, 0.0200, -0.1960)
KK = 0.000636


def T(xd, yd):
    """photo (left crop display px) -> (z, y) game metres"""
    return (round(0.275 - KK * xd, 4), round(BY + 0.1238 - KK * yd, 4))


STOCK_PX = [(62, 198), (150, 195), (230, 194), (320, 195), (400, 196), (432, 203), (480, 216), (525, 238), (524, 262), (515, 295), (498, 335),
            (480, 365), (462, 376), (440, 372), (425, 345), (400, 327), (330, 323), (250, 332), (180, 350), (120, 366), (70, 368), (60, 330), (58, 260)]
HOLE1_PX = [(262, 230), (330, 227), (410, 232), (412, 262), (380, 290), (330, 312), (290, 318), (262, 314)]
HOLE2_PX = [(100, 236), (170, 230), (180, 262), (178, 292), (125, 298), (92, 270)]


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('tube', 128, 48), ('panel', 112, 36), ('port', 56, 28), ('wood', 128, 48), ('bone_stock', 40, 40),
        ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16), ('mag', 96, 32),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=18, grime=0.84, arches=True)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.wrap('tube', 8, 6, lambda j: 'eng' if j in (0, 4) else 'hi' if j == 2 else 'dark' if j == 6 else 'plain', seed=17, lam=16)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    S.paint_wood(A, 'wood'); S.paint_port(A, 'port'); A.mag('mag', holes=True)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_mats(NAME, tex)

    # ---------------- receiver ----------------
    rc = C.Part('receiver')
    rb = K.hexp(-0.0145, 0.0145, 0.0210, 0.0790, 0.0085)
    rc.loft([(0.000, rb), (-0.300, rb)], 'steel', top='steel_top')
    rc.box((-0.0090, 0.0786, -0.2900), (0.0090, 0.0832, -0.0100), 'steel', top='steel_top')                  # dust cover ridge
    for sgn in (-1, 1):
        a_, b_ = (0.0141, 0.0156) if sgn > 0 else (-0.0156, -0.0141)
        rc.prism(S.cham(-0.250, -0.030, 0.0420, 0.0680, 0.004), a_, b_, 'panel', side='steel', top='steel_top')
        rc.prism(S.cham(-0.140, -0.050, 0.0300, 0.0400, 0.003), a_, b_, 'port', side='steel', top='steel_top')
    for zc in (-0.0050, -0.2960):
        rc.box((-0.0152, 0.0202, zc - 0.0030), (0.0152, 0.0800, zc + 0.0030), 'brass')
    K.revolve(rc, [(-0.296, 0.0150), (-0.304, 0.0150)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    # barrel, gas tube, gas block, front sight, flash hider
    K.revolve(rc, [(-0.296, 0.0095), (-0.560, 0.0080), (-0.820, 0.0070), (-0.9000, 0.0070)], BY, segs=10, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.9000, 0.0090), (-0.9050, 0.0112), (-0.9300, 0.0112), (-0.9350, 0.0095), (-0.9926, 0.0102), (Z_MUZ, 0.0070)], BY, segs=10, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0 in (-0.9060, -0.9340, -0.9900):
        K.revolve(rc, [(z0, 0.0122), (z0 - 0.0050, 0.0122)], BY, segs=10, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    rc.cyl((0, BY + 0.0210, -0.296), (0, BY + 0.0210, -0.640), 0.0058, 8, 'steel', cap='steel')            # gas tube
    rc.box((-0.0085, BY - 0.0130, -0.6750), (0.0085, BY + 0.0260, -0.6400), 'steel', top='steel_top')       # gas block
    rc.box((-0.0100, BY - 0.0100, -0.8900), (0.0100, BY + 0.0150, -0.8720), 'steel', top='steel_top')       # front sight base
    rc.box((-0.0030, BY + 0.0100, -0.8860), (0.0030, BY + 0.0420, -0.8800), 'steel')                       # front post
    K.revolve(rc, [(-0.8860, 0.0100), (-0.8800, 0.0100)], BY + 0.0310, segs=10, region='steel', cap_f='steel', cap_b='steel')
    rc.box((-0.0150, 0.0000, -0.0000), (0.0150, 0.0000, 0.0000), 'steel') if False else None
    # PSO-style scope on a side-mount block
    SN.scope(rc, Y_SIGHT, Z_OC, Z_OBJ, r=0.0140, big=0.0190, rings=(0.30, 0.68), y_base=0.0780, base_w=0.0120)
    rc.loft([(-0.0980, K.hexp(-0.0100, 0.0100, 0.0780, 0.0950, 0.0060)), (-0.2250, K.hexp(-0.0100, 0.0100, 0.0780, 0.0950, 0.0060))], 'steel', top='steel_top')
    # trigger guard band + trigger
    K.tube(rc, [(-0.0560, 0.0250), (-0.0580, 0.0060), (-0.0640, -0.0190), (-0.0780, -0.0240), (-0.1000, -0.0200), (-0.1140, -0.0050), (-0.1150, 0.0250)], 0.0090, 0.0060, 'steel')
    rc.prism([(-0.0900, 0.0210), (-0.0960, 0.0210), (-0.0950, 0.0080), (-0.0920, -0.0030), (-0.0870, -0.0030), (-0.0870, 0.0080)], -0.0016, 0.0016, 'brass', side='brass')

    # ---------------- walnut stock + handguard ----------------
    fu = C.Part('furniture')
    outer = [T(*p) for p in STOCK_PX]
    h1 = [T(*p) for p in HOLE1_PX]; h2 = [T(*p) for p in HOLE2_PX]
    K.shell(fu, outer, [h1, h2], 0.0150, region='wood', bevel=0.0040, segs=2, bevel_hole=0.0040, gmap=True)
    hg = K.hexp(-0.0185, 0.0185, 0.0280, 0.0850, 0.0140)
    fu.loft([(-0.2980, hg), (-0.5800, hg)], 'wood', top='wood')
    for sgn in (-1, 1):
        x0, x1 = (0.0181, 0.0192) if sgn > 0 else (-0.0192, -0.0181)
        for zc in (-0.350, -0.420, -0.490):
            fu.box((x0, 0.0560, zc - 0.0150), (x1, 0.0610, zc + 0.0150), 'muzzle')                               # cooling slots
        xx0, xx1 = (0.0150 - 0.0004, 0.0150 + 0.0016) if sgn > 0 else (-0.0150 - 0.0016, -0.0150 + 0.0004)
        zb, yb = T(455, 262)
        fu.cyl((xx0, yb, zb), (xx1, yb, zb), 0.0125, 12, 'brass', cap='bone_stock')                               # brass-rimmed bone cross badge
    zb0, _ = T(60, 260)
    fu.box((-0.0155, -0.0560, zb0 - 0.0010), (0.0155, 0.0420, zb0 + 0.0020), 'brass')                        # butt plate
    fu.box((-0.0190, 0.0270, -0.5800), (0.0190, 0.0860, -0.5700), 'steel', top='steel_top')                    # handguard end cap
    fu.box((-0.0190, 0.0270, -0.3050), (0.0190, 0.0860, -0.2950), 'steel', top='steel_top')                    # handguard rear ring

    # ---------------- curved box magazine ----------------
    mg = C.Part('magazine')
    mag = K.chaikin([(-0.1600, 0.0260), (-0.2320, 0.0260), (-0.2600, -0.0100), (-0.2830, -0.0500), (-0.2940, -0.0880), (-0.2400, -0.0880),
                     (-0.2220, -0.0520), (-0.1950, -0.0150)], 1)
    mg.prism(mag, -0.0125, 0.0125, 'mag', side='steel')
    mg.box((-0.0132, -0.0900, -0.2960), (0.0132, -0.0840, -0.2380), 'brass')

    objs = {}
    for p, ml in ((rc, 0.022), (fu, 0.020), (mg, 0.012)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p is fu else 35))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('sniper_marksman', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_OC),
        'front_sight': (0, Y_SIGHT, Z_OBJ),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'sniper_marksman', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
