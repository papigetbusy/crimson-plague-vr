"""Crimson Plague VR - shotgun_pump_base: the Pump Shotgun.

Original low-poly PS2 / Snake Eater style pump-action shotgun (Remington 870 /
Ithaca 37 proportions: tubular receiver with ejection port, ribbed barrel over a
magazine tube, grooved pump forend, straight-comb stock), dressed Gothic in the
batch 1 / 2 style: dark blued steel with engraved scrollwork and lancet arches,
brass bands and rings, dark walnut furniture with carved bone cross plaques.
Steel and brass share the locked 1911 metal material (metallic 1 / roughness 0.30);
walnut + bone share one non-metal material; one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_pump_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/shotgun_pump_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/shotgun_pump_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_pump_base.py -- --render-glb assets/models/gun/shotgun_pump_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: receiver (receiver, plates, barrel, vent rib, mag tube, guard, sights), furniture (stock, bone plaques,
brass butt plate), pump (wood forend on the mag tube = the sliding part), magazine (a shell at the loading gate).
Empties: muzzle, mag_well, rear_sight, front_sight. rear/front share X=0 and Y (rear on the rib at the receiver
front, bead at the muzzle), so the sight line is exactly parallel to the bore.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_shotgun_common as S
K, C, M, G = S.K, S.C, S.M, S.G

NAME = 'shotgun_pump_base'
BY, RB = 0.047, 0.0108           # bore height, barrel radius
TY, RT = 0.0225, 0.0098          # magazine tube centre height, radius
R_Y0, R_Y1 = 0.010, 0.0595
RIB_TOP, Y_SIGHT = 0.0620, 0.0650
Z_MUZ = -0.560
Z_REAR_SIGHT, Z_FRONT_SIGHT = -0.1890, -0.5385
PH = -math.pi / 12
MAGW = (0.0, -0.0035, -0.1275)


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('tube', 128, 48), ('panel', 112, 36), ('panel_s', 48, 36), ('wood', 64, 64), ('bone_stock', 48, 48),
        ('bone_fore', 48, 28), ('port', 56, 28), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24),
        ('bone_end', 16, 16), ('wood_end', 16, 16), ('shell', 32, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=22, grime=0.82)
    A.engraved('panel_s', seed=12, lam=20, grime=0.82)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.wrap('tube', 8, 6, lambda j: 'eng' if j in (0, 4) else 'hi' if j == 2 else 'dark' if j == 6 else 'plain', seed=17, lam=16)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_fore', seed=41, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    S.paint_wood(A, 'wood'); S.paint_wood(A, 'wood_end', seed=75, end=True)
    S.paint_port(A, 'port')
    A.bone('shell', seed=45, motif=None, rim=False)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_mats(NAME, tex)

    # ---------------- receiver + barrel group ----------------
    rc = C.Part('receiver')
    prof = K.hexp(-0.0170, 0.0170, R_Y0, R_Y1, 0.0040)
    rc.loft([(-0.175, prof), (0.030, prof)], 'steel', top='steel_top')
    for sgn in (-1, 1):
        a, b_ = (0.0166, 0.0200) if sgn > 0 else (-0.0200, -0.0166)
        if sgn < 0:
            rc.prism(S.cham(-0.1650, -0.0400, 0.0185, 0.0555, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        else:
            rc.prism(S.cham(-0.1650, -0.1090, 0.0185, 0.0555, 0.004), a, b_, 'panel_s', side='steel', top='steel_top')
            rc.prism(S.cham(-0.1010, -0.0400, 0.0235, 0.0535, 0.004), a, b_, 'port', side='steel', top='steel_top')
        for zc in (-0.1720, -0.1050, -0.0370, 0.0270):                      # brass straps over plate joints
            x0, x1 = (0.0164, 0.0204) if sgn > 0 else (-0.0204, -0.0164)
            rc.box((x0, R_Y0 - 0.001, zc - 0.0022), (x1, R_Y1 + 0.0004, zc + 0.0022), 'brass')
        rc.cyl((sgn * 0.0168, 0.0360, 0.0070), (sgn * 0.0204, 0.0360, 0.0070), 0.0030, 8, 'brass', cap='brass')
    # loading gate plate under the receiver + safety button
    rc.box((-0.0125, 0.0070, -0.1500), (0.0125, 0.0102, -0.1000), 'steel', top='steel_top')
    rc.box((-0.0128, 0.0066, -0.1520), (0.0128, 0.0086, -0.1480), 'brass')
    rc.cyl((-0.0200, 0.0100, -0.0125), (0.0200, 0.0100, -0.0125), 0.0036, 8, 'brass', cap='brass')
    # barrel, tube, bands
    K.revolve(rc, [(-0.170, RB), (-0.545, RB)], BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.5450, RB), (-0.5530, RB - 0.0006), (Z_MUZ, RB - 0.0016)], BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, z1 in ((-0.1700, -0.1780), (-0.3000, -0.3050), (-0.5420, -0.5480)):
        K.revolve(rc, [(z0, RB + 0.0020), (z1, RB + 0.0020)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    K.revolve(rc, [(-0.170, RT), (-0.500, RT)], TY, segs=8, region='tube', cap_f='steel', cap_b='steel')
    K.revolve(rc, [(-0.4940, RT + 0.0026), (-0.5060, RT + 0.0026)], TY, segs=8, region='brass', cap_f='brass', cap_b='brass')
    K.revolve(rc, [(-0.4960, RB + 0.0026), (-0.5040, RB + 0.0026)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    rc.box((-0.0065, TY, -0.5040), (0.0065, BY, -0.4960), 'steel')                 # barrel / tube hanger
    # ventilated rib
    z = -0.1850
    while z - 0.0340 > -0.5450:
        rc.box((-0.0035, BY + RB - 0.0016, z - 0.0340), (0.0035, RIB_TOP, z), 'steel', top='steel_top')
        z -= 0.0395
    # trigger guard + trigger
    K.tube(rc, [(-0.0640, 0.0120), (-0.0680, -0.0100), (-0.0480, -0.0235), (-0.0250, -0.0225), (-0.0080, -0.0060)], 0.0072, 0.0074, 'steel')
    rc.prism([(-0.0370, 0.0110), (-0.0310, 0.0110), (-0.0325, -0.0020), (-0.0350, -0.0110), (-0.0390, -0.0140), (-0.0420, -0.0130),
              (-0.0400, -0.0050), (-0.0385, 0.0020)], -0.0020, 0.0020, 'brass', side='brass')
    S.sight_pair(rc, Y_SIGHT, Z_REAR_SIGHT, Z_FRONT_SIGHT, R_Y1 - 0.0005, RIB_TOP - 0.0005, rear_w=0.0120, rear_len=0.016)

    # ---------------- walnut stock ----------------
    fu = C.Part('furniture')
    stock = [(-0.010, 0.030), (0.030, 0.0595), (0.120, 0.0580), (0.230, 0.0540), (0.330, 0.0470), (0.356, 0.0430), (0.362, 0.030),
             (0.362, -0.050), (0.350, -0.074), (0.310, -0.062), (0.230, -0.034), (0.150, -0.022), (0.080, -0.024), (0.030, -0.030),
             (-0.004, -0.026), (-0.014, -0.010)]
    fu.prism(K.chaikin(stock, 1), -0.0175, 0.0175, 'wood', side='wood_end')
    fu.prism([(0.3590, 0.0450), (0.3675, 0.0450), (0.3675, -0.0760), (0.3480, -0.0780), (0.3430, -0.0700), (0.3590, -0.0700)], -0.0185, 0.0185, 'brass', side='brass')
    for sgn in (-1, 1):
        lo, hi = (0.0175, 0.0194) if sgn > 0 else (-0.0194, -0.0175)
        fu.prism(K.chaikin(S.cham(0.168, 0.240, -0.012, 0.042, 0.010), 1), lo, hi, 'bone_stock', side='bone_end')
        fu.cyl((sgn * 0.0172, 0.0400, 0.050), (sgn * 0.0204, 0.0400, 0.050), 0.0036, 8, 'brass', cap='brass')    # tang bolt
        fu.cyl((sgn * 0.0172, 0.0020, 0.060), (sgn * 0.0200, 0.0020, 0.060), 0.0030, 8, 'brass', cap='brass')
    fu.box((-0.0186, -0.0215, 0.0020), (0.0186, -0.0185, 0.0450), 'brass')                                       # grip cap strap
    fu.prism([(0.3280, -0.0640), (0.3560, -0.0740), (0.3560, -0.0840), (0.3300, -0.0700)], -0.0120, 0.0120, 'bone_end', side='bone_end')

    # ---------------- pump forend (slides on the tube) ----------------
    pu = C.Part('pump')
    fe = [(-0.200, 0.0355), (-0.200, 0.012), (-0.208, 0.006), (-0.236, 0.006), (-0.240, 0.010), (-0.250, 0.010), (-0.254, 0.006),
          (-0.262, 0.006), (-0.266, 0.010), (-0.276, 0.010), (-0.280, 0.006), (-0.288, 0.006), (-0.292, 0.010), (-0.302, 0.010),
          (-0.306, 0.006), (-0.352, 0.006), (-0.368, 0.012), (-0.372, 0.030), (-0.366, 0.0355)]
    pu.prism(fe, -0.0185, 0.0185, 'wood', side='wood_end')
    for zc in (-0.2040, -0.3705):
        pu.box((-0.0194, 0.0030, zc - 0.0040), (0.0194, 0.0385, zc + 0.0040), 'brass')
    for sgn in (-1, 1):
        lo, hi = (0.0185, 0.0202) if sgn > 0 else (-0.0202, -0.0185)
        pu.prism(K.chaikin(S.cham(-0.3400, -0.2480, 0.0110, 0.0330, 0.0045), 1), lo, hi, 'bone_fore', side='bone_end')

    # ---------------- shell at the loading gate (= magazine) ----------------
    mg = C.Part('magazine')
    sy = MAGW[1]
    mg.cyl((0, sy, -0.1520), (0, sy, -0.1060), 0.0098, 8, 'shell', cap='bone_end')
    mg.cyl((0, sy, -0.1060), (0, sy, -0.0930), 0.0106, 8, 'brass', cap='brass')
    mg.cyl((0, sy, -0.1580), (0, sy, -0.1520), 0.0075, 8, 'brass', cap='brass', r1=0.0062)

    objs = {p.name: p.to_object(mats) for p in (rc, fu, pu, mg)}
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('shotgun_pump', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_REAR_SIGHT),
        'front_sight': (0, Y_SIGHT, Z_FRONT_SIGHT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'shotgun_pump', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
