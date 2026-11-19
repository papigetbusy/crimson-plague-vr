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
BY, RB = 0.047, 0.0100           # bore height, barrel radius
TY, RT = 0.0225, 0.0088          # magazine tube centre height, radius
R_Y0, R_Y1 = 0.016, 0.0595
RIB_TOP, Y_SIGHT = 0.0610, 0.0650
Z_MUZ = -0.560
Z_REAR_SIGHT, Z_FRONT_SIGHT = -0.1890, -0.5385
PH = -math.pi / 12
MAGW = (0.0, 0.0050, -0.1275)


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('tube', 128, 48), ('panel', 112, 36), ('panel_s', 48, 36), ('wood', 128, 48), ('bone_stock', 40, 40),
        ('bone_fore', 28, 20), ('port', 56, 28), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24),
        ('bone_end', 16, 16), ('wood_end', 16, 16), ('shell', 32, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=14, grime=0.84, arches=False)
    A.engraved('panel_s', seed=12, lam=13, grime=0.84, arches=False)
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
    prof = K.hexp(-0.0150, 0.0150, R_Y0, R_Y1, 0.0045)
    rc.loft([(-0.175, prof), (0.030, prof)], 'steel', top='steel_top')
    for sgn in (-1, 1):
        a, b_ = (0.0146, 0.0158) if sgn > 0 else (-0.0158, -0.0146)
        if sgn < 0:
            rc.prism(S.cham(-0.1650, -0.0400, 0.0215, 0.0555, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        else:
            rc.prism(S.cham(-0.1650, -0.1090, 0.0215, 0.0555, 0.004), a, b_, 'panel_s', side='steel', top='steel_top')
            rc.prism(S.cham(-0.1010, -0.0400, 0.0255, 0.0535, 0.004), a, b_, 'port', side='steel', top='steel_top')
        for zc in (-0.1720, -0.1050, -0.0370, 0.0270):                      # brass straps over plate joints
            x0, x1 = (0.0144, 0.0162) if sgn > 0 else (-0.0162, -0.0144)
            rc.box((x0, R_Y0 - 0.0005, zc - 0.0012), (x1, R_Y1 + 0.0003, zc + 0.0012), 'brass')
        rc.cyl((sgn * 0.0148, 0.0370, 0.0070), (sgn * 0.0166, 0.0370, 0.0070), 0.0020, 8, 'brass', cap='brass')
    # loading gate plate under the receiver + safety button
    rc.box((-0.0100, 0.0125, -0.1500), (0.0100, 0.0162, -0.1000), 'steel', top='steel_top')
    rc.box((-0.0102, 0.0120, -0.1510), (0.0102, 0.0140, -0.1490), 'brass')
    rc.cyl((-0.0165, 0.0170, -0.0125), (0.0165, 0.0170, -0.0125), 0.0026, 8, 'brass', cap='brass')
    # barrel, tube, bands
    K.revolve(rc, [(-0.170, RB), (-0.545, RB)], BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.5450, RB), (-0.5530, RB - 0.0006), (Z_MUZ, RB - 0.0016)], BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, z1 in ((-0.1700, -0.1740), (-0.3000, -0.3030), (-0.5420, -0.5450)):
        K.revolve(rc, [(z0, RB + 0.0012), (z1, RB + 0.0012)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    K.revolve(rc, [(-0.170, RT), (-0.500, RT)], TY, segs=10, region='tube', cap_f='steel', cap_b='steel')
    K.revolve(rc, [(-0.4960, RT + 0.0016), (-0.5040, RT + 0.0016)], TY, segs=10, region='brass', cap_f='brass', cap_b='brass')
    K.revolve(rc, [(-0.4970, RB + 0.0016), (-0.5030, RB + 0.0016)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    rc.box((-0.0050, TY, -0.5030), (0.0050, BY, -0.4970), 'steel')                 # barrel / tube hanger
    # ventilated rib
    z = -0.1850
    while z - 0.0340 > -0.5450:
        rc.box((-0.0028, BY + RB - 0.0016, z - 0.0340), (0.0028, RIB_TOP, z), 'steel', top='steel_top')
        z -= 0.0395
    # trigger guard + trigger
    K.tube(rc, [(-0.0640, 0.0185), (-0.0680, -0.0100), (-0.0480, -0.0235), (-0.0250, -0.0225), (-0.0080, -0.0100), (0.0020, 0.0000)], 0.0090, 0.0060, 'steel')
    rc.prism([(-0.0370, 0.0110), (-0.0310, 0.0110), (-0.0325, -0.0020), (-0.0350, -0.0110), (-0.0390, -0.0140), (-0.0420, -0.0130),
              (-0.0400, -0.0050), (-0.0385, 0.0020)], -0.0014, 0.0014, 'brass', side='brass')
    S.sight_pair(rc, Y_SIGHT, Z_REAR_SIGHT, Z_FRONT_SIGHT, R_Y1 - 0.0005, RIB_TOP - 0.0005, rear_w=0.0090, rear_len=0.016)

    # ---------------- walnut stock ----------------
    fu = C.Part('furniture')
    # stock side profile traced from the Remington 870 Wingmaster photo (/workspace/gun_brief/refs/shotgun_pump), scaled to this model's stock length
    stock = [(0.3580, -0.0075), (0.3350, -0.0069), (0.3124, -0.0051), (0.2893, -0.0024), (0.2667, -0.0001), (0.2441, 0.0021), (0.2211, 0.0048),
             (0.1985, 0.0071), (0.1759, 0.0093), (0.1529, 0.0112), (0.1303, 0.0139), (0.1077, 0.0166), (0.0847, 0.0184), (0.0620, 0.0190),
             (0.0395, 0.0220), (0.0164, 0.0300), (-0.0062, 0.0400), (-0.0100, 0.0300), (-0.0100, -0.0040), (0.0000, -0.0080), (0.0164, -0.0260),
             (0.0400, -0.0480), (0.0620, -0.0535), (0.0847, -0.0562), (0.1077, -0.0584), (0.1303, -0.0666), (0.1529, -0.0738), (0.1759, -0.0837),
             (0.1985, -0.0941), (0.2211, -0.1032), (0.2441, -0.1122), (0.2667, -0.1217), (0.2893, -0.1289), (0.3124, -0.1366), (0.3350, -0.1411),
             (0.3580, -0.1420)]
    K.shell(fu, stock, [], 0.0138, region='wood', bevel=0.0050, segs=2, gmap=True)
    fu.prism([(0.3575, -0.0075), (0.3650, -0.0075), (0.3650, -0.1420), (0.3575, -0.1420)], -0.0140, 0.0140, 'brass', side='brass')
    for sgn in (-1, 1):
        x0, x1 = (0.0138 - 0.0005, 0.0138 + 0.0016) if sgn > 0 else (-0.0138 - 0.0016, -0.0138 + 0.0005)
        fu.cyl((x0, -0.0480, 0.2200), (x1, -0.0480, 0.2200), 0.0145, 12, 'brass', cap='bone_stock')        # brass-rimmed bone cross badge
        fu.cyl((sgn * 0.0136, 0.0390, 0.050), (sgn * 0.0156, 0.0390, 0.050), 0.0024, 8, 'brass', cap='brass')    # tang bolt
    fu.box((-0.0142, -0.0545, 0.0480), (0.0142, -0.0520, 0.0780), 'brass')                                       # grip cap strap

    # ---------------- pump forend (slides on the tube) ----------------
    pu = C.Part('pump')
    fe = [(-0.200, 0.0340), (-0.200, 0.000), (-0.208, -0.008), (-0.236, -0.010), (-0.240, -0.006), (-0.250, -0.006), (-0.254, -0.010),
          (-0.262, -0.010), (-0.266, -0.006), (-0.276, -0.006), (-0.280, -0.010), (-0.288, -0.010), (-0.292, -0.006), (-0.302, -0.006),
          (-0.306, -0.010), (-0.380, -0.010), (-0.412, -0.004), (-0.420, 0.012), (-0.418, 0.0340)]
    K.shell(pu, fe, [], 0.0150, region='wood', bevel=0.0040, segs=1, gmap=True)
    for zc in (-0.2040, -0.4180):
        pu.box((-0.0154, 0.0040, zc - 0.0020), (0.0154, 0.0380, zc + 0.0020), 'brass')
    for sgn in (-1, 1):
        x0, x1 = (0.0150 - 0.0005, 0.0150 + 0.0014) if sgn > 0 else (-0.0150 - 0.0014, -0.0150 + 0.0005)
        pu.cyl((x0, 0.0215, -0.3400), (x1, 0.0105, -0.3400), 0.0092, 12, 'brass', cap='bone_fore')

    # ---------------- shell at the loading gate (= magazine) ----------------
    mg = C.Part('magazine')
    mg.box((-0.0110, 0.0140, -0.1650), (0.0110, 0.0166, -0.0870), 'brass')            # brass loading gate plate, bolted to the receiver floor
    sy = MAGW[1]
    mg.cyl((0, sy, -0.1520), (0, sy, -0.1060), 0.0090, 8, 'shell', cap='bone_end')
    mg.cyl((0, sy, -0.1060), (0, sy, -0.0930), 0.0096, 8, 'brass', cap='brass')
    mg.cyl((0, sy, -0.1580), (0, sy, -0.1520), 0.0075, 8, 'brass', cap='brass', r1=0.0062)

    objs = {}
    for p, ml in ((rc, 0.024), (fu, 0.020), (pu, 0.020), (mg, 0.014)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p in (fu, pu) else 35))
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
