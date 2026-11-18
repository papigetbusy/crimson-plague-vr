"""Crimson Plague VR - shotgun_combat_base: the Combat Shotgun.

Original low-poly PS2 / Snake Eater style semi-auto combat shotgun (Saiga-12 /
AA-12 proportions: fat boxy receiver with a raised top cover, long gas tube
under a walnut upper handguard, front-sight block with sight ears, finned
muzzle brake, curved 8-round box magazine, pistol grip, solid stock), dressed
Gothic in the batch 1 / 2 style: dark blued steel with engraved scrollwork and
lancet arches, brass straps / rings / cocking knob / mag band, dark walnut
furniture with carved bone cross plaques. Steel and brass share the locked 1911
metal material (metallic 1 / roughness 0.30); walnut + bone share one non-metal
material; one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_combat_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/shotgun_combat_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/shotgun_combat_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_combat_base.py -- --render-glb assets/models/gun/shotgun_combat_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: receiver (receiver, plates, barrel, gas tube + block, brake, guard, sights), furniture (stock, pistol grip,
upper + lower handguards, bone plaques, brass plates), cocking_handle (brass knob on the right, slides back),
magazine (curved 8-round box under mag_well).
Empties: muzzle, mag_well, rear_sight, front_sight. rear/front share X=0 and Y (rear ear posts on the top cover,
front ears on the sight block), so the sight line is exactly parallel to the bore (bore 40 mm below it).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_shotgun_common as S
K, C, M, G = S.K, S.C, S.M, S.G

NAME = 'shotgun_combat_base'
TH = math.radians(17)
BY, RB = 0.062, 0.0115
GY, RG = 0.0865, 0.0075            # gas tube centre height, radius
R_Y0, R_Y1 = 0.030, 0.082
COVER_TOP = 0.085
Y_SIGHT = 0.1020
Z_MUZ = -0.580
Z_REAR_SIGHT, Z_FRONT_SIGHT = -0.0300, -0.4500
GRIP_TOP, GRIP_BOT = 0.045, -0.062
PH = -math.pi / 12
MAGW = (0.0, R_Y0, -0.1100)


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('tube', 96, 32), ('panel', 112, 36), ('wood', 64, 64), ('bone_stock', 48, 48), ('bone_fore', 48, 24),
        ('mag', 64, 48), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
        ('wood_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=22, grime=0.82)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.wrap('tube', 8, 4, lambda j: 'hi' if j == 2 else 'dark' if j == 6 else 'plain', seed=17, lam=16)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_fore', seed=41, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    S.paint_wood(A, 'wood'); S.paint_wood(A, 'wood_end', seed=75, end=True)
    A.mag('mag', holes=True)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_mats(NAME, tex)

    # ---------------- receiver + barrel group ----------------
    rc = C.Part('receiver')
    prof = K.hexp(-0.0210, 0.0210, R_Y0, R_Y1, 0.0040)
    rc.loft([(-0.200, prof), (0.040, prof)], 'steel', top='steel_top')
    rc.box((-0.0150, R_Y1 - 0.0005, -0.1930), (0.0150, COVER_TOP, 0.0320), 'steel', top='steel_top')       # raised top cover
    for sgn in (-1, 1):
        a, b_ = (0.0206, 0.0240) if sgn > 0 else (-0.0240, -0.0206)
        rc.prism(S.cham(-0.1850, -0.0400, 0.0345, 0.0765, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        for zc in (-0.1950, -0.0300, 0.0360):                                 # brass straps over plate joints
            x0, x1 = (0.0204, 0.0244) if sgn > 0 else (-0.0244, -0.0204)
            rc.box((x0, R_Y0 - 0.001, zc - 0.0024), (x1, R_Y1 + 0.0004, zc + 0.0024), 'brass')
        rc.cyl((sgn * 0.0208, 0.0560, 0.0200), (sgn * 0.0246, 0.0560, 0.0200), 0.0032, 8, 'brass', cap='brass')
        rc.cyl((sgn * 0.0208, 0.0380, -0.1700), (sgn * 0.0246, 0.0380, -0.1700), 0.0030, 8, 'brass', cap='brass')
    # magazine well collar
    rc.box((-0.0185, 0.0270, -0.1480), (0.0185, 0.0310, -0.0720), 'steel', top='steel_top')
    # barrel, brake, rings
    K.revolve(rc, [(-0.190, RB), (-0.525, RB)], BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.5250, 0.0125), (-0.5750, 0.0140), (Z_MUZ, 0.0120)], BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, z1 in ((-0.5250, -0.5320), (-0.5700, -0.5760)):
        K.revolve(rc, [(z0, 0.0152), (z1, 0.0152)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for zz in (-0.5400, -0.5480, -0.5560):                                      # brake slots (top)
        rc.box((-0.0040, BY + 0.0128, zz - 0.0022), (0.0040, BY + 0.0150, zz + 0.0022), 'steel')
    # gas tube, cap and gas / front-sight block
    K.revolve(rc, [(-0.200, RG), (-0.400, RG)], GY, segs=8, region='tube', cap_f='steel', cap_b='steel')
    K.revolve(rc, [(-0.3960, RG + 0.0022), (-0.4040, RG + 0.0022)], GY, segs=8, region='brass', cap_f='brass', cap_b='brass')
    rc.box((-0.0100, BY - RB + 0.0010, -0.4700), (0.0100, 0.0975, -0.4300), 'steel', top='steel_top')
    # trigger guard + trigger
    K.tube(rc, [(-0.0560, 0.0310), (-0.0600, 0.0110), (-0.0480, -0.0100), (-0.0300, -0.0180), (-0.0190, -0.0120)], 0.0072, 0.0074, 'steel')
    rc.prism([(-0.0320, 0.0300), (-0.0260, 0.0300), (-0.0275, 0.0140), (-0.0300, 0.0040), (-0.0340, 0.0000), (-0.0375, 0.0005),
              (-0.0355, 0.0080), (-0.0335, 0.0160)], -0.0020, 0.0020, 'brass', side='brass')
    # rear sight (base + two tall brass-topped posts) and front sight (ears + blade + brass bead)
    rc.box((-0.0125, COVER_TOP - 0.0005, -0.0390), (0.0125, 0.0905, -0.0210), 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0045, 0.0085) if sgn > 0 else (-0.0085, -0.0045)
        rc.box((lo, 0.0905, -0.0360), (hi, Y_SIGHT, -0.0240), 'steel', top='steel_top')
        rc.box((lo, Y_SIGHT - 0.0009, -0.0360), (hi, Y_SIGHT, -0.0240), 'brass')
        lo, hi = (0.0042, 0.0068) if sgn > 0 else (-0.0068, -0.0042)
        rc.box((lo, 0.0975, -0.4650), (hi, Y_SIGHT - 0.0005, -0.4350), 'steel', top='steel_top')
    rc.box((-0.0028, 0.0975, -0.4560), (0.0028, Y_SIGHT - 0.0016, -0.4440), 'steel')
    rc.box((-0.0016, Y_SIGHT - 0.0016, -0.4530), (0.0016, Y_SIGHT, -0.4470), 'brass')

    # ---------------- walnut furniture ----------------
    fu = C.Part('furniture')
    stock = [(0.040, 0.0795), (0.200, 0.0770), (0.312, 0.0680), (0.332, 0.0620), (0.338, -0.046), (0.322, -0.052), (0.300, -0.030),
             (0.200, 0.020), (0.130, 0.028), (0.040, 0.036)]
    fu.prism(stock, -0.0175, 0.0175, 'wood', side='wood_end')
    fu.prism([(0.3365, -0.0490), (0.3440, -0.0490), (0.3440, 0.0630), (0.3300, 0.0630)], -0.0185, 0.0185, 'brass', side='brass')
    for sgn in (-1, 1):
        lo, hi = (0.0175, 0.0194) if sgn > 0 else (-0.0194, -0.0175)
        fu.prism(K.chaikin(S.cham(0.190, 0.262, 0.012, 0.066, 0.010), 1), lo, hi, 'bone_stock', side='bone_end')
        fu.cyl((sgn * 0.0172, 0.0600, 0.0820), (sgn * 0.0204, 0.0600, 0.0820), 0.0034, 8, 'brass', cap='brass')
    grip = [(-0.0225, GRIP_TOP), (-0.0235, 0.020), (-0.0240, -0.015), (-0.0225, GRIP_BOT), (0.0205, GRIP_BOT), (0.0235, -0.030),
            (0.0245, 0.000), (0.0240, 0.030), (0.0220, GRIP_TOP)]
    K.prism_ah(fu, K.chaikin(grip, 1), TH, -0.0135, 0.0135, 'wood', side='wood_end')
    zb = K.ah_to_zy([(-0.0235, GRIP_BOT), (0.0212, GRIP_BOT), (0.0212, GRIP_BOT - 0.0070), (-0.0235, GRIP_BOT - 0.0070)], TH)
    fu.prism(zb, -0.0148, 0.0148, 'brass', side='brass')
    for sgn in (-1, 1):
        zy = K.ah_to_zy([(0.0, 0.012)], TH)[0]
        fu.cyl((sgn * 0.0132, zy[1], zy[0]), (sgn * 0.0152, zy[1], zy[0]), 0.0030, 8, 'brass', cap='brass')
    # upper handguard over the gas tube (below the sight line) and lower handguard under the barrel
    fu.loft([(-0.2050, K.hexp(-0.0128, 0.0128, 0.0785, 0.0950, 0.0045)), (-0.3900, K.hexp(-0.0128, 0.0128, 0.0785, 0.0950, 0.0045))],
            'wood', top='wood', end='wood_end')
    fu.box((-0.0136, 0.0770, -0.3950), (0.0136, 0.0958, -0.3880), 'brass')
    fu.box((-0.0136, 0.0770, -0.2090), (0.0136, 0.0958, -0.2030), 'brass')
    lg = K.chaikin([(-0.200, 0.0560), (-0.200, 0.0300), (-0.215, 0.0260), (-0.360, 0.0290), (-0.395, 0.0380), (-0.395, 0.0560)], 1)
    fu.prism(lg, -0.0172, 0.0172, 'wood', side='wood_end')
    fu.box((-0.0180, 0.0240, -0.4010), (0.0180, 0.0585, -0.3945), 'brass')
    for sgn in (-1, 1):
        lo, hi = (0.0172, 0.0189) if sgn > 0 else (-0.0189, -0.0172)
        fu.prism(K.chaikin(S.cham(-0.338, -0.256, 0.0310, 0.0525, 0.0045), 1), lo, hi, 'bone_fore', side='bone_end')

    # ---------------- cocking knob (brass, right side, slides back) ----------------
    ch = C.Part('cocking_handle')
    ch.box((0.0206, 0.0600, -0.0780), (0.0250, 0.0680, -0.0580), 'brass')
    ch.cyl((0.0250, 0.0640, -0.0680), (0.0330, 0.0640, -0.0680), 0.0072, 8, 'brass', cap='brass')

    # ---------------- curved 8-round box magazine ----------------
    mg = C.Part('magazine')
    mp = K.chaikin([(-0.0780, 0.0340), (-0.1420, 0.0340), (-0.1480, -0.0200), (-0.1800, -0.0860), (-0.1220, -0.0860), (-0.1100, -0.0220)], 1)
    mg.prism(mp, -0.0158, 0.0158, 'mag', side='steel')
    mg.prism([(-0.1235, -0.0850), (-0.1830, -0.0850), (-0.1830, -0.0950), (-0.1235, -0.0950)], -0.0170, 0.0170, 'brass', side='brass')
    mg.box((-0.0163, -0.0030, -0.1480), (0.0163, 0.0050, -0.1000), 'brass')

    objs = {p.name: p.to_object(mats) for p in (rc, fu, ch, mg)}
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('shotgun_combat', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_REAR_SIGHT),
        'front_sight': (0, Y_SIGHT, Z_FRONT_SIGHT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'shotgun_combat', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
