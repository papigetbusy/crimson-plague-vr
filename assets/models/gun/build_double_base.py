"""Crimson Plague VR - shotgun_double_base: the Double Barrel.

Original low-poly PS2 / Snake Eater style side-by-side break-action shotgun
(coach-gun / English sidelock proportions: two blued barrels joined by a vent
rib, hinged action with engraved sideplates and brass hinge pin, top lever,
two triggers, splinter forend, pistol-grip stock), dressed Gothic in the batch
1 / 2 style: dark blued steel with engraved scrollwork and lancet arches, brass
barrel bands / rings / lever, dark walnut furniture with carved bone cross
plaques, brass butt plate, and a brass-strapped stock cuff holding two spare
shells (= the magazine node). Steel and brass share the locked 1911 metal
material (metallic 1 / roughness 0.30); walnut + bone share one non-metal
material; one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_double_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/shotgun_double_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/shotgun_double_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_double_base.py -- --render-glb assets/models/gun/shotgun_double_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: receiver (action, sideplates, hinge pin, top lever, guard, triggers), hammers (two exposed hammers), barrels (two barrels, vent rib, bands,
sights; a separate mesh so the break can be animated later), furniture (stock, pistol grip, forend, bone plaques,
brass plates and cuff straps), magazine (two spare shells in the stock cuff).
Empties: muzzle (between the barrels), mag_well (cuff), rear_sight, front_sight. rear/front share X=0 and Y
(rear posts on the rib at the breech, bead at the muzzle), so the sight line is exactly parallel to the bores.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_shotgun_common as S
K, C, M, G = S.K, S.C, S.M, S.G

NAME = 'shotgun_double_base'
BY, RB, BX = 0.052, 0.0112, 0.0118        # bore height, barrel radius, barrel x offset
RIB_TOP, Y_SIGHT = 0.0662, 0.0690
A_Y0, A_Y1 = 0.020, 0.0600
Z_MUZ = -0.520
Z_REAR_SIGHT, Z_FRONT_SIGHT = -0.1350, -0.4975
TH = math.radians(14)
GRIP_TOP, GRIP_BOT = 0.040, -0.062
PH = -math.pi / 12
SHELL_X, SHELL_Y0, SHELL_Y1, SHELL_Z0, SHELL_Z1 = -0.0275, 0.0395, 0.0190, 0.140, 0.208
MAGW = (SHELL_X, 0.0292, (SHELL_Z0 + SHELL_Z1) / 2)


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('panel', 112, 36), ('lock', 64, 40), ('wood', 64, 64), ('bone_stock', 48, 48), ('bone_fore', 40, 28),
        ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16), ('wood_end', 16, 16),
        ('shell', 32, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=22, grime=0.82)
    A.engraved('lock', seed=14, lam=18, grime=0.82, cross=True)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_fore', seed=41, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    S.paint_wood(A, 'wood'); S.paint_wood(A, 'wood_end', seed=75, end=True)
    A.bone('shell', seed=45, motif=None, rim=False)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_mats(NAME, tex)

    # ---------------- action ----------------
    rc = C.Part('receiver')
    prof = K.hexp(-0.0245, 0.0245, A_Y0, A_Y1, 0.0050)
    rc.loft([(-0.118, prof), (0.030, prof)], 'steel', top='steel_top')
    lock = K.chaikin([(-0.088, 0.032), (-0.062, 0.052), (-0.012, 0.0545), (0.018, 0.0500), (0.024, 0.0400), (0.010, 0.0300), (-0.040, 0.0265)], 1)
    for sgn in (-1, 1):
        a, b_ = (0.0242, 0.0272) if sgn > 0 else (-0.0272, -0.0242)
        rc.prism(lock, a, b_, 'lock', side='steel', top='steel_top')
        xa, xb = (0.0240, 0.0276) if sgn > 0 else (-0.0276, -0.0240)
        rc.box((xa, A_Y0 - 0.001, -0.1155), (xb, A_Y1 + 0.0004, -0.1100), 'brass')               # brass strap at the action front
        rc.box((xa, A_Y0 - 0.001, 0.0260), (xb, A_Y1 + 0.0004, 0.0305), 'brass')
        rc.cyl((sgn * 0.0240, 0.0300, -0.0950), (sgn * 0.0285, 0.0300, -0.0950), 0.0046, 8, 'brass', cap='brass')   # hinge pin heads
        rc.cyl((sgn * 0.0240, 0.0465, 0.0050), (sgn * 0.0282, 0.0465, 0.0050), 0.0030, 8, 'brass', cap='brass')
    rc.cyl((-0.0245, 0.0300, -0.0950), (0.0245, 0.0300, -0.0950), 0.0036, 8, 'brass', cap='brass')
    # short brass top lever on the top strap (opens the break)
    rc.prism([(-0.0750, 0.0596), (-0.0570, 0.0596), (-0.0510, 0.0610), (-0.0500, 0.0624), (-0.0570, 0.0622), (-0.0750, 0.0614)], -0.0030, 0.0030, 'brass', side='brass')
    # trigger guard + two triggers
    K.tube(rc, [(-0.0840, 0.0210), (-0.0870, 0.0000), (-0.0680, -0.0200), (-0.0400, -0.0250), (-0.0220, -0.0140)], 0.0072, 0.0074, 'steel')
    for zc in (-0.0300, -0.0520):
        rc.prism([(zc - 0.003, 0.0210), (zc + 0.003, 0.0210), (zc + 0.0015, 0.0040), (zc - 0.0030, -0.0070), (zc - 0.0065, -0.0060), (zc - 0.0040, 0.0030)],
                 -0.0018, 0.0018, 'brass', side='brass')

    # exposed hammers (coach-gun style), one each side, outside the sideplates
    hm = C.Part('hammers')
    hamp = K.chaikin([(-0.0040, 0.0440), (0.0060, 0.0440), (0.0150, 0.0520), (0.0260, 0.0600), (0.0310, 0.0640), (0.0315, 0.0668),
                      (0.0230, 0.0670), (0.0160, 0.0620), (0.0070, 0.0560), (-0.0040, 0.0510)], 1)
    for sgn in (-1, 1):
        lo, hi = (0.0272, 0.0304) if sgn > 0 else (-0.0304, -0.0272)
        hm.prism(hamp, lo, hi, 'steel_top', side='steel')
        hm.cyl((sgn * 0.0272, 0.0455, 0.0030), (sgn * 0.0316, 0.0455, 0.0030), 0.0032, 8, 'brass', cap='brass')

    # ---------------- barrels ----------------
    br = C.Part('barrels')
    for sgn in (-1, 1):
        cx = sgn * BX
        K.revolve(br, [(-0.100, RB), (-0.505, RB)], BY, segs=12, region='barrel', cx=cx, cap_f='steel', cap_b='steel', phase=PH)
        K.revolve(br, [(-0.5050, RB), (-0.5130, RB - 0.0006), (Z_MUZ, RB - 0.0016)], BY, segs=12, region='barrel', cx=cx, cap_f='muzzle', cap_b='steel', phase=PH)
        K.revolve(br, [(-0.5000, RB + 0.0018), (-0.5080, RB + 0.0018)], BY, segs=12, region='brass', cx=cx, cap_f='brass', cap_b='brass', phase=PH)
    br.box((-0.0075, BY - 0.0090, -0.118), (0.0075, BY + 0.0060, -0.513), 'steel', top='steel_top')   # fills the V between the bores
    z = -0.118
    while z - 0.0340 > -0.5000:
        br.box((-0.0075, BY + RB - 0.0030, z - 0.0340), (0.0075, RIB_TOP, z), 'steel', top='steel_top')
        z -= 0.0395
    for z0, w in ((-0.1700, 0.0070), (-0.3050, 0.0060)):          # brass bands across both barrels
        br.loft([(z0, K.hexp(-0.0262, 0.0262, BY - 0.0130, BY + 0.0130, 0.0060)), (z0 - w, K.hexp(-0.0262, 0.0262, BY - 0.0130, BY + 0.0130, 0.0060))], 'brass')
    S.sight_pair(br, Y_SIGHT, Z_REAR_SIGHT, Z_FRONT_SIGHT, RIB_TOP - 0.0005, RIB_TOP - 0.0005, rear_w=0.0075, rear_len=0.016, post_in=0.0026)

    # ---------------- walnut furniture ----------------
    fu = C.Part('furniture')
    stock = [(0.030, 0.0600), (0.200, 0.0560), (0.310, 0.0480), (0.345, 0.0440), (0.352, -0.045), (0.336, -0.062), (0.300, -0.040),
             (0.200, 0.010), (0.130, 0.020), (0.030, 0.025)]
    fu.prism(stock, -0.0175, 0.0175, 'wood', side='wood_end')
    fu.prism([(0.3500, 0.0460), (0.3585, 0.0460), (0.3585, -0.0560), (0.3380, -0.0660), (0.3330, -0.0580), (0.3500, -0.0540)], -0.0185, 0.0185, 'brass', side='brass')
    grip = [(-0.0225, GRIP_TOP), (-0.0235, 0.020), (-0.0240, -0.015), (-0.0225, GRIP_BOT), (0.0205, GRIP_BOT), (0.0235, -0.030),
            (0.0245, 0.000), (0.0240, 0.030), (0.0220, GRIP_TOP)]
    K.prism_ah(fu, K.chaikin(grip, 1), TH, -0.0140, 0.0140, 'wood', side='wood_end')
    zb = K.ah_to_zy([(-0.0235, GRIP_BOT), (0.0212, GRIP_BOT), (0.0212, GRIP_BOT - 0.0070), (-0.0235, GRIP_BOT - 0.0070)], TH)
    fu.prism(zb, -0.0152, 0.0152, 'brass', side='brass')
    zb2 = K.ah_to_zy([(-0.0150, GRIP_BOT - 0.0070), (0.0100, GRIP_BOT - 0.0070), (0.0090, GRIP_BOT - 0.0130), (-0.0140, GRIP_BOT - 0.0130)], TH)
    fu.prism(zb2, -0.0105, 0.0105, 'bone_end', side='bone_end')
    for sgn in (-1, 1):
        lo, hi = (0.0175, 0.0194) if sgn > 0 else (-0.0194, -0.0175)
        fu.prism(K.chaikin(S.cham(0.052, 0.124, -0.002, 0.050, 0.010), 1), lo, hi, 'bone_stock', side='bone_end')
        fu.cyl((sgn * 0.0172, 0.0480, 0.0300), (sgn * 0.0204, 0.0480, 0.0300), 0.0034, 8, 'brass', cap='brass')    # tang bolt
        zy = K.ah_to_zy([(0.0, 0.012)], TH)[0]
        fu.cyl((sgn * 0.0138, zy[1], zy[0]), (sgn * 0.0160, zy[1], zy[0]), 0.0030, 8, 'brass', cap='brass')
    # splinter forend under the barrels + brass tip + bone plaques
    fe = K.chaikin([(-0.118, 0.0420), (-0.118, 0.0200), (-0.180, 0.0190), (-0.250, 0.0235), (-0.286, 0.0300), (-0.290, 0.0420)], 1)
    fu.prism(fe, -0.0235, 0.0235, 'wood', side='wood_end')
    fu.box((-0.0243, 0.0285, -0.2960), (0.0243, 0.0438, -0.2860), 'brass')
    fu.box((-0.0243, 0.0170, -0.1250), (0.0243, 0.0430, -0.1180), 'brass')
    for sgn in (-1, 1):
        lo, hi = (0.0235, 0.0252) if sgn > 0 else (-0.0252, -0.0235)
        fu.prism(K.chaikin(S.cham(-0.236, -0.164, 0.0225, 0.0405, 0.0040), 1), lo, hi, 'bone_fore', side='bone_end')
    # shell cuff straps on the left of the buttstock (the shells are the magazine node)
    for zc in (0.1500, 0.2020):
        fu.box((-0.0388, 0.0090, zc - 0.0030), (-0.0170, 0.0500, zc + 0.0030), 'brass')

    # ---------------- two spare shells in the cuff (= magazine) ----------------
    mg = C.Part('magazine')
    for sy in (SHELL_Y0, SHELL_Y1):
        mg.cyl((SHELL_X, sy, SHELL_Z0 + 0.012), (SHELL_X, sy, SHELL_Z1), 0.0092, 8, 'shell', cap='bone_end')
        mg.cyl((SHELL_X, sy, SHELL_Z0), (SHELL_X, sy, SHELL_Z0 + 0.012), 0.0098, 8, 'brass', cap='brass')
        mg.cyl((SHELL_X, sy, SHELL_Z1), (SHELL_X, sy, SHELL_Z1 + 0.005), 0.0070, 8, 'brass', cap='brass', r1=0.0058)

    objs = {p.name: p.to_object(mats) for p in (rc, hm, br, fu, mg)}
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('shotgun_double', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_REAR_SIGHT),
        'front_sight': (0, Y_SIGHT, Z_FRONT_SIGHT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'shotgun_double', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
