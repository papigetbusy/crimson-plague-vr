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
R_Y0, R_Y1 = 0.030, 0.080
TY, RT = 0.0395, 0.0100            # magazine tube centre height / radius (tube under the barrel, Benelli M4)
Y_SIGHT = 0.1020
Z_MUZ = -0.580
Z_REAR_SIGHT, Z_FRONT_SIGHT = -0.0300, -0.4500
GRIP_TOP, GRIP_BOT = 0.045, -0.062
PH = -math.pi / 12
MAGW = (0.0, 0.0205, -0.1100)


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('tube', 96, 32), ('panel', 112, 36), ('wood', 64, 64), ('bone_stock', 48, 48), ('bone_fore', 48, 24),
        ('shell', 32, 16), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
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
    A.bone('shell', seed=45, motif=None, rim=False)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_mats(NAME, tex)

    # ---------------- receiver + barrel group (Benelli M4: slim rounded flat-top receiver, tube mag under the barrel) ----------------
    rc = C.Part('receiver')
    prof = [(-0.0200, R_Y0 + 0.007), (-0.0168, R_Y0), (0.0168, R_Y0), (0.0200, R_Y0 + 0.007), (0.0200, R_Y1 - 0.011), (0.0158, R_Y1),
            (-0.0158, R_Y1), (-0.0200, R_Y1 - 0.011)]
    rc.loft([(-0.200, prof), (0.040, prof)], 'steel', top='steel_top')
    rc.box((-0.0085, R_Y1 - 0.0004, -0.1900), (0.0085, R_Y1 + 0.0028, 0.0300), 'steel', top='steel_top')       # flat-top rail
    rc.box((-0.0012, R_Y1 + 0.0026, -0.1800), (0.0012, R_Y1 + 0.0033, 0.0200), 'brass')                       # brass inlay down the rail
    for sgn in (-1, 1):
        a_, b_ = (0.0196, 0.0228) if sgn > 0 else (-0.0228, -0.0196)
        rc.prism(S.cham(-0.1750, -0.0450, 0.0345, 0.0725, 0.004), a_, b_, 'panel', side='steel', top='steel_top')
        for zc in (-0.1950, 0.0360):                                          # brass straps over the receiver joints
            x0, x1 = (0.0194, 0.0232) if sgn > 0 else (-0.0232, -0.0194)
            rc.box((x0, R_Y0 - 0.001, zc - 0.0024), (x1, R_Y1 + 0.0004, zc + 0.0024), 'brass')
        rc.cyl((sgn * 0.0197, 0.0560, 0.0200), (sgn * 0.0236, 0.0560, 0.0200), 0.0030, 8, 'brass', cap='brass')
    # loading gate on the underside
    rc.box((-0.0125, R_Y0 - 0.0030, -0.1450), (0.0125, R_Y0 + 0.0004, -0.0750), 'steel', top='steel_top')
    # barrel + brake + rings
    K.revolve(rc, [(-0.190, RB), (-0.525, RB)], BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.5250, 0.0125), (-0.5750, 0.0140), (Z_MUZ, 0.0120)], BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, z1 in ((-0.5250, -0.5320), (-0.5700, -0.5760)):
        K.revolve(rc, [(z0, 0.0152), (z1, 0.0152)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for zz in (-0.5400, -0.5480, -0.5560):                                      # brake slots (top)
        rc.box((-0.0040, BY + 0.0128, zz - 0.0022), (0.0040, BY + 0.0150, zz + 0.0022), 'steel')
    # magazine tube under the barrel, running to near the muzzle, brass cap + barrel hanger
    K.revolve(rc, [(-0.200, RT), (-0.505, RT)], TY, segs=12, region='tube', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.4940, RT + 0.0022), (-0.5060, RT + 0.0022)], TY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    rc.box((-0.0060, TY + 0.0040, -0.5000), (0.0060, BY - RB + 0.0030, -0.4920), 'steel')
    # front sight block on the barrel
    rc.box((-0.0100, BY - RB + 0.0010, -0.4700), (0.0100, 0.0975, -0.4300), 'steel', top='steel_top')
    # trigger guard + trigger
    K.tube(rc, [(-0.0560, 0.0310), (-0.0600, 0.0110), (-0.0480, -0.0100), (-0.0300, -0.0180), (-0.0190, -0.0120)], 0.0072, 0.0074, 'steel')
    rc.prism([(-0.0320, 0.0300), (-0.0260, 0.0300), (-0.0275, 0.0140), (-0.0300, 0.0040), (-0.0340, 0.0000), (-0.0375, 0.0005),
              (-0.0355, 0.0080), (-0.0335, 0.0160)], -0.0020, 0.0020, 'brass', side='brass')
    # ghost-ring rear sight (octagonal aperture ring on twin posts, centred on the sight line) and front sight ears + blade + bead
    ro, ri, rz0, rz1 = 0.0100, 0.0058, -0.0360, -0.0240
    for k in range(8):
        a0, a1 = math.radians(22.5 + 45 * k), math.radians(22.5 + 45 * (k + 1))
        quad = [(ro * math.cos(a0), Y_SIGHT + ro * math.sin(a0)), (ro * math.cos(a1), Y_SIGHT + ro * math.sin(a1)),
                (ri * math.cos(a1), Y_SIGHT + ri * math.sin(a1)), (ri * math.cos(a0), Y_SIGHT + ri * math.sin(a0))]
        rc.loft([(rz0, quad), (rz1, quad)], 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0060, 0.0100) if sgn > 0 else (-0.0100, -0.0060)
        rc.box((lo, R_Y1 + 0.0020, -0.0350), (hi, Y_SIGHT - 0.0050, -0.0250), 'steel', top='steel_top')
        lo, hi = (0.0042, 0.0068) if sgn > 0 else (-0.0068, -0.0042)
        rc.box((lo, 0.0975, -0.4650), (hi, Y_SIGHT - 0.0005, -0.4350), 'steel', top='steel_top')
    rc.box((-0.0028, 0.0975, -0.4560), (0.0028, Y_SIGHT - 0.0016, -0.4440), 'steel')
    rc.box((-0.0016, Y_SIGHT - 0.0016, -0.4530), (0.0016, Y_SIGHT, -0.4470), 'brass')

    # ---------------- walnut furniture ----------------
    fu = C.Part('furniture')
    # stock side profile traced from the Benelli M4 / L128A1 photo (/workspace/gun_brief/refs/shotgun_combat): tall butt pad, slim dropped neck
    # rising into the receiver; scaled to this model's stock length
    stock = [(0.040, 0.0700), (0.100, 0.0600), (0.160, 0.0470), (0.220, 0.0330), (0.262, 0.0260), (0.292, 0.0300), (0.312, 0.0390),
             (0.330, 0.0430), (0.344, 0.0400), (0.344, -0.0800), (0.330, -0.0830), (0.314, -0.0760), (0.296, -0.0560), (0.262, -0.0440),
             (0.220, -0.0380), (0.160, -0.0230), (0.100, -0.0040), (0.040, 0.0200)]
    K.shell(fu, K.chaikin(stock, 1), [], 0.0165, region='wood', bevel=0.0050, segs=2, gmap=True)
    fu.prism([(0.3430, -0.0800), (0.3500, -0.0800), (0.3500, 0.0400), (0.3430, 0.0400)], -0.0170, 0.0170, 'brass', side='brass')
    for sgn in (-1, 1):
        x0, x1 = (0.0160 - 0.0005, 0.0160 + 0.0016) if sgn > 0 else (-0.0160 - 0.0016, -0.0160 + 0.0005)
        fu.cyl((x0, -0.0180, 0.3250), (x1, -0.0180, 0.3250), 0.0150, 12, 'brass', cap='bone_stock')          # brass-rimmed bone cross badge
    grip = [(-0.0225, GRIP_TOP), (-0.0235, 0.020), (-0.0240, -0.015), (-0.0225, GRIP_BOT), (0.0205, GRIP_BOT), (0.0235, -0.030),
            (0.0245, 0.000), (0.0240, 0.030), (0.0220, GRIP_TOP)]
    K.shell(fu, K.ah_to_zy(K.chaikin(grip, 1), TH), [], 0.0135, region='wood', bevel=0.0045, segs=1, gmap=True)
    zb = K.ah_to_zy([(-0.0235, GRIP_BOT), (0.0212, GRIP_BOT), (0.0212, GRIP_BOT - 0.0070), (-0.0235, GRIP_BOT - 0.0070)], TH)
    fu.prism(zb, -0.0148, 0.0148, 'brass', side='brass')
    # slim rounded polymer-style handguard wrapped around the barrel + tube (Benelli M4 forend)
    fg = [(-0.205, 0.0700), (-0.205, 0.0300), (-0.214, 0.0255), (-0.372, 0.0255), (-0.384, 0.0300), (-0.384, 0.0700)]
    K.shell(fu, K.chaikin(fg, 1), [], 0.0155, region='wood', bevel=0.0050, segs=2, gmap=True)
    fu.loft([(-0.3840, K.hexp(-0.0160, 0.0160, 0.0245, 0.0712, 0.0060)), (-0.3910, K.hexp(-0.0160, 0.0160, 0.0245, 0.0712, 0.0060))], 'brass')
    for sgn in (-1, 1):
        x0, x1 = (0.0155 - 0.0005, 0.0155 + 0.0014) if sgn > 0 else (-0.0155 - 0.0014, -0.0155 + 0.0005)
        fu.cyl((x0, 0.0480, -0.2950), (x1, 0.0480, -0.2950), 0.0085, 12, 'brass', cap='bone_fore')

    # ---------------- cocking knob (brass, right side, slides back) ----------------
    ch = C.Part('cocking_handle')
    ch.box((0.0206, 0.0600, -0.0780), (0.0250, 0.0680, -0.0580), 'brass')
    ch.cyl((0.0250, 0.0640, -0.0680), (0.0330, 0.0640, -0.0680), 0.0072, 8, 'brass', cap='brass')

    # ---------------- loading-gate shell (= magazine node; the real magazine is the tube under the barrel) ----------------
    mg = C.Part('magazine')
    mg.box((-0.0115, 0.0275, -0.1400), (0.0115, 0.0302, -0.0800), 'brass')
    sy = MAGW[1]
    mg.cyl((0, sy, -0.1300), (0, sy, -0.0950), 0.0072, 8, 'shell', cap='bone_end')
    mg.cyl((0, sy, -0.0950), (0, sy, -0.0860), 0.0078, 8, 'brass', cap='brass')

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
