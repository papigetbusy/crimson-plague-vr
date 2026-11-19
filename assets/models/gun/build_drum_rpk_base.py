"""Crimson Plague VR - hmg_drum_base: the Drum LMG (RPK with a 75-round drum).

Original low-poly PS2 / Snake Eater style light machine gun, proportions traced from the RPK side photo (/workspace/gun_brief/refs/hmg_drum,
photo de-rotated, 913 px/m, ~1.0 m long): long thin barrel with a folded bipod + slant brake + hooded front post, wooden fore-end over
a gas tube, stamped steel receiver, fish-belly wooden stock with a raked wooden pistol grip, and a big round DRUM magazine
(smooth 24-sided disc, ribbed steel face, brass rim, bone cross badge on the hub) hanging under the receiver.
Blued engraved steel on the locked 1911 metal material, satin walnut + bone on one non-metal material, brass bands.
One 1024 px smooth albedo, sampler LINEAR.

Meshes: receiver (receiver, barrel, gas tube, sights, guard, bipod), furniture (stock, grip, fore-end), magazine (drum).
Empties: muzzle, mag_well, rear_sight, front_sight (X=0, Y_SIGHT, parallel to the bore).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_hmg_common as H
from build_bullpup_base import dome_shell
S, K, C, M, G = H.S, H.K, H.C, H.M, H.G

NAME = 'hmg_drum_base'
BY = 0.060
Z_MUZ = -0.8000
Y_SIGHT = 0.1340
Z_REAR, Z_FRONT = -0.2700, -0.7650
PH = -math.pi / 12
DR, DHW, DC = 0.0820, 0.0330, (-0.100, -0.1650)     # drum radius, half width, centre (y, z)
MAGW = (0.0, -0.0040, DC[1])


def Z(x):
    return round((x - 800) / 913.0, 4)


def Y(y):
    return round(BY + (287 - y) / 913.0, 4)


def P(pts):
    return [(Z(x), Y(y)) for x, y in pts]


# RPK club-foot stock traced from rpk_boxmag_side.png (963 px/m, receiver rear at px 812): thumb-rest dip on top, deep drop at the wrist,
# thick belly sweeping down to a tall butt with a steel plate
def SZ(x):
    return round(0.0055 + (x - 812) / 963.0, 4)


def SY(y):
    return round(0.118 - (y - 207) * 1.12 / 963.0, 4)


STOCK_PX = [(786, 207), (812, 207), (835, 216), (860, 228), (890, 236), (930, 244), (970, 252), (995, 259), (1005, 266), (1008, 290), (1005, 330), (996, 352), (980, 362),
            (952, 360), (920, 348), (894, 330), (880, 308), (866, 286), (846, 266), (822, 252), (786, 244)]
STOCK = [(SZ(x), SY(y)) for x, y in STOCK_PX]
GRIP_PX = [(724, 336), (790, 336), (793, 376), (790, 416), (781, 441), (758, 441), (749, 420), (745, 378)]
FORE_PX = [(415, 262), (566, 262), (570, 312), (528, 316), (440, 292), (415, 282)]


def build(out_dir):
    A = H.make_atlas(out_dir, NAME, wood=True)
    mats = H.finish_mats(A, out_dir, NAME, wood=True)

    # ---------------- receiver group ----------------
    rc = C.Part('receiver')
    rp = K.hexp(-0.0185, 0.0185, Y(345), Y(246), 0.0100)
    rc.loft([(Z(805), rp), (Z(560), rp)], 'steel', top='steel_top')
    rc.loft([(Z(800), K.hexp(-0.0140, 0.0140, Y(246), Y(236), 0.0060)), (Z(600), K.hexp(-0.0140, 0.0140, Y(246), Y(236), 0.0060))], 'steel', top='steel_top')  # dust-cover ridge
    for sgn in (-1, 1):
        a_, b_ = (0.0181, 0.0198) if sgn > 0 else (-0.0198, -0.0181)
        rc.prism(S.cham(Z(790), Z(640), Y(330), Y(262), 0.004), a_, b_, 'panel', side='steel', top='steel_top')
        x0, x1 = (0.0180, 0.0202) if sgn > 0 else (-0.0202, -0.0180)
        for zc in (Z(803), Z(562)):
            rc.box((x0, Y(346), zc - 0.0030), (x1, Y(245), zc + 0.0030), 'brass')
    # barrel, brake, gas tube, gas block
    K.revolve(rc, [(Z(570), 0.0108), (Z(410), 0.0098), (Z(110), 0.0092), (Z(86), 0.0092)], BY, segs=10, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(Z(86), 0.0092), (Z(82), 0.0120), (Z(58), 0.0120), (Z_MUZ, 0.0100)], BY, segs=10, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0 in (Z(84), Z(60)):
        K.revolve(rc, [(z0, 0.0132), (z0 - 0.0050, 0.0132)], BY, segs=10, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    rc.cyl((0, BY + 0.0420, Z(570)), (0, BY + 0.0420, Z(360)), 0.0085, 8, 'steel', cap='steel')
    K.revolve(rc, [(Z(372), 0.0220), (Z(330), 0.0220)], BY + 0.0200, segs=10, region='steel', cap_f='steel', cap_b='steel', phase=PH)   # gas block
    # rear tangent sight + hooded front post
    rc.box((-0.0100, Y(248), Z(590)), (0.0100, Y_SIGHT - 0.0030, Z(560)), 'steel', top='steel_top')
    rc.box((-0.0090, Y_SIGHT - 0.0030, Z(588)), (0.0090, Y_SIGHT, Z(574)), 'steel', top='steel_top')
    rc.box((-0.0070, Y_SIGHT - 0.0006, Z(586)), (-0.0020, Y_SIGHT + 0.0000, Z(576)), 'brass')
    K.revolve(rc, [(Z_FRONT - 0.0090, 0.0140), (Z_FRONT + 0.0090, 0.0140)], BY, segs=10, region='steel', cap_f='steel', cap_b='steel', phase=PH)
    rc.box((-0.0022, BY + 0.0100, Z_FRONT - 0.0030), (0.0022, Y_SIGHT, Z_FRONT + 0.0030), 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0042, 0.0062) if sgn > 0 else (-0.0062, -0.0042)
        rc.box((lo, BY + 0.0100, Z_FRONT - 0.0090), (hi, Y_SIGHT - 0.0050, Z_FRONT + 0.0090), 'steel', top='steel_top')
    rc.box((-0.0014, Y_SIGHT - 0.0010, Z_FRONT - 0.0014), (0.0014, Y_SIGHT + 0.0010, Z_FRONT + 0.0014), 'brass')
    # trigger guard band + trigger
    K.tube(rc, [(-0.1500, 0.0000), (-0.1480, -0.0190), (-0.1200, -0.0280), (-0.0900, -0.0220), (-0.0810, 0.0000)], 0.0090, 0.0060, 'steel')
    rc.prism([(-0.1180, 0.0000), (-0.1240, 0.0000), (-0.1235, -0.0110), (-0.1210, -0.0200), (-0.1160, -0.0210), (-0.1170, -0.0100)], -0.0016, 0.0016, 'brass', side='brass')
    # folded bipod under the barrel: hinge block + clamp ring, two thick legs back along the barrel, big feet, cross brace, rear catch
    K.revolve(rc, [(-0.7300, 0.0180), (-0.7520, 0.0180)], BY, segs=10, region='steel', cap_f='steel', cap_b='steel', phase=PH)
    rc.box((-0.0230, BY - 0.0330, -0.7500), (0.0230, BY - 0.0150, -0.7280), 'steel', top='steel_top')
    for sgn in (-1, 1):
        rc.cyl((sgn * 0.0190, BY - 0.0260, -0.7400), (sgn * 0.0190, BY - 0.0260, -0.4400), 0.0075, 8, 'steel', cap='steel')
        rc.cyl((sgn * 0.0190, BY - 0.0260, -0.4400), (sgn * 0.0190, BY - 0.0260, -0.4150), 0.0110, 8, 'muzzle', cap='muzzle')
        rc.box((sgn * 0.0190 - 0.0040, BY - 0.0350, -0.7300), (sgn * 0.0190 + 0.0040, BY - 0.0150, -0.7050), 'steel', top='steel_top')
    rc.cyl((-0.0190, BY - 0.0260, -0.5600), (0.0190, BY - 0.0260, -0.5600), 0.0050, 6, 'steel', cap='steel')

    # ---------------- walnut furniture ----------------
    fu = C.Part('furniture')
    dome_shell(fu, K.chaikin(STOCK, 1), [], 0.0215, bevel=0.0090, bevel_hole=0.0060, crown=0.0055, D=0.040, region='wood')
    K.shell(fu, K.chaikin(P(GRIP_PX), 1), [], 0.0150, region='wood', bevel=0.0045, segs=2, gmap=True)
    K.shell(fu, K.chaikin(P(FORE_PX), 1), [], 0.0215, region='wood', bevel=0.0045, segs=2, gmap=True)
    up = K.hexp(-0.0165, 0.0165, Y(268), Y(234), 0.0075)
    fu.loft([(Z(520), up), (Z(418), up)], 'wood', top='wood')                       # upper handguard over the gas tube
    zb, yb = SZ(930), SY(298)
    fu.prism([(Z(992), Y(250)), (Z(998), Y(250)), (Z(986), Y(348)), (Z(980), Y(348))], -0.0178, 0.0178, 'brass', side='brass') if False else None
    z0b, z1b, z2b, z3b = SZ(1008), SZ(1005), SZ(996), SZ(980)
    fu.prism([(z0b, SY(266)), (z0b + 0.0030, SY(290)), (z1b + 0.0030, SY(330)), (z2b + 0.0030, SY(352)), (z3b + 0.0010, SY(362)),
              (z3b - 0.0050, SY(362)), (z2b - 0.0050, SY(352)), (z1b - 0.0050, SY(330)), (z0b - 0.0050, SY(290)), (z0b - 0.0050, SY(266))],
             -0.0220, 0.0220, 'steel', side='steel', top='steel_top')                                                    # steel butt plate
    for sgn in (-1, 1):
        x0, x1 = (0.0268, 0.0290) if sgn > 0 else (-0.0290, -0.0268)
        fu.cyl((x0, yb, zb), (x1, yb, zb), 0.0140, 12, 'brass', cap='bone_stock')                         # brass-rimmed bone cross badge
        fu.cyl((sgn * 0.0212, Y(284), Z(470)), (sgn * 0.0226, Y(284), Z(470)), 0.0075, 10, 'brass', cap='bone_end')

    # ---------------- drum magazine (axis across X) ----------------
    mg = C.Part('magazine')
    dy, dz = DC
    mg.cyl((-DHW, dy, dz), (DHW, dy, dz), DR, 24, 'mag', cap='mag')
    mg.cyl((DHW, dy, dz), (DHW + 0.0050, dy, dz), DR * 0.55, 20, 'steel', cap='steel')           # raised face plate
    mg.cyl((-DHW - 0.0050, dy, dz), (-DHW, dy, dz), DR * 0.55, 20, 'steel', cap='steel')
    mg.cyl((-DHW - 0.0010, dy, dz), (DHW + 0.0010, dy, dz), DR + 0.0030, 24, 'brass', cap='brass', r1=DR + 0.0030) if False else None
    for sgn in (-1, 1):
        mg.cyl((sgn * (DHW + 0.0050), dy, dz), (sgn * (DHW + 0.0090), dy, dz), 0.0220, 12, 'brass', cap='bone_stock')   # hub with bone cross badge
    mg.box((-0.0125, dy + DR - 0.0100, dz - 0.0300), (0.0125, -0.0030, dz + 0.0300), 'steel', top='steel_top')    # drum neck into the mag well
    objs = {}
    for p, ml in ((rc, 0.024), (fu, 0.020), (mg, 0.9)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p is fu else 35))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('hmg_drum', objs, {
        'muzzle': (0, BY, Z_MUZ), 'mag_well': MAGW, 'rear_sight': (0, Y_SIGHT, Z_REAR), 'front_sight': (0, Y_SIGHT, Z_FRONT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'hmg_drum', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
