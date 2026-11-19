"""Crimson Plague VR - hmg_chain_base: the Chain Gun (man-portable M230 style).

Original low-poly PS2 / Snake Eater style 30 mm chain gun carried by hand: the real M230 identifiers are a big round rear drive / motor housing,
a boxy receiver with the chain drive housing underneath, a perforated-look barrel shroud with a long thin barrel and a slotted flash suppressor,
a side ammo can with a fat brass 30 mm belt climbing into the feed chute. Added to make it handheld: a raked finger-groove polymer pistol grip
with trigger guard, a vertical polymer front grip under the shroud and a high carry handle with a polymer sleeve (the sights sit under it).
Blued engraved steel on the locked 1911 metal material, glossy near-black polymer, brass bands + bone cross badge. 1024 px smooth albedo, LINEAR.

Meshes: receiver, furniture (pistol grip, front grip), magazine (ammo can + belt).
Empties: muzzle, mag_well (ammo can), rear_sight, front_sight (X=0, Y_SIGHT, parallel to the bore axis).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_hmg_common as H
S, K, C, M, G = H.S, H.K, H.C, H.M, H.G

NAME = 'hmg_chain_base'
BY = 0.0750
Y_SIGHT = 0.1600
Z_REAR, Z_FRONT = 0.1250, -0.5100
Z_MUZ = -0.8600
PH = -math.pi / 12
MAGW = (0.0850, BY - 0.0850, -0.1450)


def build(out_dir):
    A = H.make_atlas(out_dir, NAME, wood=False)
    mats = H.finish_mats(A, out_dir, NAME, wood=False)

    rc = C.Part('receiver')
    # rear drive / motor housing: big round drum with ribs and a rounded cap
    K.revolve(rc, [(0.1700, 0.0300), (0.1650, 0.0480), (0.1500, 0.0560), (0.1100, 0.0570), (0.1050, 0.0520), (0.0800, 0.0520), (0.0750, 0.0570), (0.0300, 0.0570), (0.0200, 0.0500)],
              BY, segs=14, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    for z0 in (0.1350, 0.0550):
        K.revolve(rc, [(z0, 0.0585), (z0 - 0.0060, 0.0585)], BY, segs=14, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    # boxy receiver + cover + chain-drive housing
    rb = K.hexp(-0.0500, 0.0500, BY - 0.0600, BY + 0.0500, 0.0150)
    rc.loft([(0.0300, rb), (-0.2000, rb)], 'steel', top='steel_top')
    for sgn in (-1, 1):
        a_, b_ = (0.0496, 0.0516) if sgn > 0 else (-0.0516, -0.0496)
        rc.prism(S.cham(-0.185, 0.015, BY - 0.0450, BY + 0.0350, 0.008), a_, b_, 'panel', side='steel', top='steel_top')
    K.revolve(rc, [(-0.2000, 0.0310), (-0.2150, 0.0350), (-0.2400, 0.0350)], BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    cd = K.hexp(-0.0400, 0.0400, BY - 0.1000, BY - 0.0550, 0.0120)
    rc.loft([(0.0000, cd), (-0.1950, cd)], 'steel', top='steel_top')
    rc.box((-0.0420, BY - 0.0980, -0.1950), (0.0420, BY - 0.0940, 0.0000), 'brass')
    # shroud + barrel + slotted flash suppressor
    H.slotted_hider(rc, BY, -0.2400, -0.5300, r=0.0270, n_slots=4, segs=12)
    K.revolve(rc, [(-0.4800, 0.0135), (-0.7600, 0.0135)], BY, segs=10, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    H.slotted_hider(rc, BY, -0.7000, Z_MUZ, r=0.0200, n_slots=3, segs=10)
    K.revolve(rc, [(-0.5300, 0.0160), (-0.5600, 0.0160)], BY, segs=10, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    # carry handle (steel arch + polymer sleeve); sights sit under it
    K.tube(rc, [(0.0000, BY + 0.0450), (0.0000, BY + 0.1200), (-0.1650, BY + 0.1200), (-0.1650, BY + 0.0450)], 0.0180, 0.0120, 'steel')
    rc.cyl((0, BY + 0.1200, -0.0300), (0, BY + 0.1200, -0.1350), 0.0140, 10, 'poly', cap='poly')
    S.sight_pair(rc, Y_SIGHT, Z_REAR, Z_FRONT, BY + 0.0540, BY + 0.0260, rear_w=0.0100, rear_len=0.014, post_in=0.0030)
    # feed chute on the right of the receiver
    rc.box((0.0480, BY - 0.0300, -0.1800), (0.0880, BY + 0.0300, -0.0600), 'steel', top='steel_top')
    rc.box((0.0880, BY - 0.0200, -0.1700), (0.0900, BY + 0.0200, -0.0700), 'brass')
    # trigger guard + trigger
    K.tube(rc, [(0.0550, BY - 0.0600), (0.0540, BY - 0.0850), (0.0300, BY - 0.0950), (-0.0150, BY - 0.0900)], 0.0090, 0.0060, 'steel')
    rc.prism([(0.0330, BY - 0.0600), (0.0270, BY - 0.0600), (0.0275, BY - 0.0720), (0.0300, BY - 0.0810), (0.0350, BY - 0.0820), (0.0340, BY - 0.0720)], -0.0016, 0.0016, 'brass', side='brass')

    fu = C.Part('furniture')
    K.shell(fu, H.grip_poly(0.0750, BY - 0.0560, length=0.125), [], 0.0175, region='poly', bevel=0.0045, segs=2, gmap=True)
    fg = K.chaikin([(-0.3300, BY - 0.0200), (-0.3640, BY - 0.0200), (-0.3700, BY - 0.1150), (-0.3580, BY - 0.1400), (-0.3380, BY - 0.1400), (-0.3260, BY - 0.1150)], 1)
    K.shell(fu, fg, [], 0.0170, region='poly', bevel=0.0050, segs=2, gmap=True)
    fu.box((-0.0140, BY - 0.0400, -0.3680), (0.0140, BY - 0.0190, -0.3280), 'steel')
    for sgn in (-1, 1):
        x0, x1 = (0.0170 - 0.0005, 0.0170 + 0.0016) if sgn > 0 else (-0.0170 - 0.0016, -0.0170 + 0.0005)
        fu.cyl((x0, BY - 0.0800, -0.3480), (x1, BY - 0.0800, -0.3480), 0.0130, 12, 'brass', cap='bone_stock')

    # ammo can on the right + fat brass 30 mm belt climbing into the feed chute
    mg = C.Part('magazine')
    mg.prism(S.cham(-0.250, -0.050, BY - 0.1400, BY - 0.0300, 0.008), 0.0480, 0.1220, 'mag', side='steel')
    mg.box((0.0470, BY - 0.0950, -0.2540), (0.1230, BY - 0.0890, -0.0460), 'brass')
    for i in range(5):
        t = i / 4.0
        y = BY - 0.0300 + 0.050 * t
        z = -0.2250 + 0.045 * t
        mg.cyl((0.0520, y, z), (0.0900, y, z), 0.0100, 7, 'brass', cap='brass')
        mg.box((0.0500, y - 0.0075, z - 0.0075), (0.0580, y + 0.0075, z + 0.0075), 'steel')

    objs = {}
    for p, ml in ((rc, 0.030), (fu, 0.030), (mg, 0.9)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p is fu else 35))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('hmg_chain', objs, {
        'muzzle': (0, BY, Z_MUZ), 'mag_well': MAGW, 'rear_sight': (0, Y_SIGHT, Z_REAR), 'front_sight': (0, Y_SIGHT, Z_FRONT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'hmg_chain', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
