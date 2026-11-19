"""Crimson Plague VR - hmg_minigun_base: the Handheld Minigun (M134 style, man-portable).

Original low-poly PS2 / Snake Eater style six-barrel rotary gun in a hand-carried build: the real M134 barrel cluster (six smooth barrels around a hub,
three steel clamp rings with brass bands, dark muzzle holes), a round gear / motor housing with a rounded rear cap, a chassis with a raked
finger-groove polymer pistol grip, a vertical polymer foregrip under the middle clamp, a carry handle with a polymer grip sleeve, an ammo box with a
brass belt feeding the housing. Blued engraved steel on the locked 1911 metal material, glossy near-black polymer (bullpup polish3 recipe), brass
bands + bone cross badge. One 1024 px smooth albedo, sampler LINEAR.

Meshes: receiver (barrels, clamps, housing, chassis, handle, sights, guard), furniture (pistol grip, foregrip), magazine (ammo box + belt).
Empties: muzzle, mag_well (ammo box), rear_sight, front_sight (X=0, Y_SIGHT, parallel to the bore axis).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_hmg_common as H
S, K, C, M, G = H.S, H.K, H.C, H.M, H.G

NAME = 'hmg_minigun_base'
BY = 0.080
Y_SIGHT = 0.1620
Z_REAR, Z_FRONT = 0.0850, -0.7550
Z_MUZ = -0.8000
PH = -math.pi / 12
MAGW = (0.0, BY - 0.0600, -0.0800)
RING_R = 0.0215


def build(out_dir):
    A = H.make_atlas(out_dir, NAME, wood=False)
    mats = H.finish_mats(A, out_dir, NAME, wood=False)

    rc = C.Part('receiver')
    # six barrels around the hub + muzzle holes
    K.revolve(rc, [(-0.120, 0.0150), (-0.760, 0.0150)], BY, segs=10, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    for k in range(6):
        a = math.radians(60 * k + 30)
        cx, cy = RING_R * math.cos(a), BY + RING_R * math.sin(a)
        K.revolve(rc, [(-0.120, 0.0078), (-0.8000, 0.0078)], cy, segs=8, region='barrel', cx=cx, cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, r, w in ((-0.190, 0.0390, 0.0260), (-0.420, 0.0340, 0.0220), (-0.740, 0.0350, 0.0220)):
        K.revolve(rc, [(z0, r * 0.94), (z0 - 0.003, r), (z0 - w + 0.003, r), (z0 - w, r * 0.94)], BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
        K.revolve(rc, [(z0 - 0.0045, r + 0.0010), (z0 - w + 0.0045, r + 0.0010)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    # rear gear / motor housing, rounded cap
    K.revolve(rc, [(0.1200, 0.0350), (0.1150, 0.0500), (0.0600, 0.0525), (0.0500, 0.0555), (-0.0200, 0.0555), (-0.0300, 0.0510), (-0.1200, 0.0480), (-0.1300, 0.0400)],
              BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    for z0 in (0.0000, -0.0800):
        K.revolve(rc, [(z0, 0.0570), (z0 - 0.0050, 0.0570)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    # chassis under the housing (grip mount)
    ch = K.hexp(-0.0380, 0.0380, BY - 0.0680, BY - 0.0300, 0.0140)
    rc.loft([(0.090, ch), (-0.140, ch)], 'steel', top='steel_top')
    for sgn in (-1, 1):
        a_, b_ = (0.0376, 0.0394) if sgn > 0 else (-0.0394, -0.0376)
        rc.prism(S.cham(-0.120, 0.060, BY - 0.0600, BY - 0.0360, 0.004), a_, b_, 'panel', side='steel', top='steel_top')
    # carry handle (steel arch + polymer grip sleeve)
    K.tube(rc, [(0.0500, BY + 0.0500), (0.0500, BY + 0.1050), (-0.1100, BY + 0.1050), (-0.1100, BY + 0.0500)], 0.0180, 0.0120, 'steel')
    rc.cyl((0, BY + 0.1050, 0.0000), (0, BY + 0.1050, -0.0900), 0.0135, 10, 'poly', cap='poly')
    # sights on the housing top / front clamp
    S.sight_pair(rc, Y_SIGHT, Z_REAR, Z_FRONT, BY + 0.0540, BY + 0.0330, rear_w=0.0100, rear_len=0.014, post_in=0.0030)
    # trigger guard band + trigger
    K.tube(rc, [(0.0580, BY - 0.0600), (0.0560, BY - 0.0800), (0.0320, BY - 0.0900), (0.0060, BY - 0.0850), (0.0020, BY - 0.0600)], 0.0090, 0.0060, 'steel')
    rc.prism([(0.0350, BY - 0.0600), (0.0290, BY - 0.0600), (0.0295, BY - 0.0700), (0.0320, BY - 0.0790), (0.0370, BY - 0.0800), (0.0360, BY - 0.0700)], -0.0016, 0.0016, 'brass', side='brass')

    # polymer furniture
    fu = C.Part('furniture')
    K.shell(fu, H.grip_poly(0.0780, BY - 0.0560, length=0.125), [], 0.0175, region='poly', bevel=0.0045, segs=2, gmap=True)
    fg = K.chaikin([(-0.4040, BY - 0.0300), (-0.4360, BY - 0.0300), (-0.4420, BY - 0.1150), (-0.4300, BY - 0.1400), (-0.4100, BY - 0.1400), (-0.3980, BY - 0.1150)], 1)
    K.shell(fu, fg, [], 0.0170, region='poly', bevel=0.0050, segs=2, gmap=True)
    fu.box((-0.0140, BY - 0.0460, -0.4400), (0.0140, BY - 0.0280, -0.4000), 'steel')
    for sgn in (-1, 1):
        x0, x1 = (0.0170 - 0.0005, 0.0170 + 0.0016) if sgn > 0 else (-0.0170 - 0.0016, -0.0170 + 0.0005)
        fu.cyl((x0, BY - 0.0800, -0.4200), (x1, BY - 0.0800, -0.4200), 0.0130, 12, 'brass', cap='bone_stock')       # brass-rimmed bone cross badge

    # ammo box under the chassis + brass belt up the right side into the housing
    mg = C.Part('magazine')
    mg.prism(S.cham(-0.135, -0.025, BY - 0.1450, BY - 0.0650, 0.008), -0.0340, 0.0340, 'mag', side='steel')
    mg.box((-0.0348, BY - 0.1000, -0.1380), (0.0348, BY - 0.0940, -0.0220), 'brass')
    for i in range(7):
        t = i / 6.0
        y = BY - 0.075 + 0.085 * t
        z = -0.080 + 0.050 * math.sin(math.pi * t)
        mg.cyl((0.0300, y, z), (0.0700, y, z), 0.0066, 6, 'brass', cap='brass')
        mg.box((0.0300, y - 0.0048, z - 0.0048), (0.0370, y + 0.0048, z + 0.0048), 'steel')

    objs = {}
    for p, ml in ((rc, 0.030), (fu, 0.030), (mg, 0.9)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p is fu else 35))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('hmg_minigun', objs, {
        'muzzle': (0, BY, Z_MUZ), 'mag_well': MAGW, 'rear_sight': (0, Y_SIGHT, Z_REAR), 'front_sight': (0, Y_SIGHT, Z_FRONT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'hmg_minigun', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
