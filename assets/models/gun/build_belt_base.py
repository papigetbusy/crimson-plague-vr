"""Crimson Plague VR - hmg_belt_base: the Belt-Fed LMG (M249 / M60 proportions).

Original low-poly PS2 / Snake Eater style squad automatic: boxy steel receiver with a hinged feed cover + Picatinny rail, a visible belt of brass
rounds running from the steel ammo box into the feed, carry handle with a polymer grip sleeve, vented polymer handguard, long barrel with a
slotted flash hider, deployed bipod, glossy near-black polymer skeleton stock (real cut-out) + raked finger-groove pistol grip (bullpup polish3
recipe). Blued engraved steel on the locked 1911 metal material, brass hinge bands + bone cross badge. One 1024 px smooth albedo, sampler LINEAR.

Meshes: receiver (receiver, cover, rail, barrel, hider, handle, bipod, sights, guard), furniture (stock, butt pad, grip, handguard), magazine (ammo box + belt).
Empties: muzzle, mag_well (feed / box), rear_sight, front_sight (X=0, Y_SIGHT, parallel to the bore).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_hmg_common as H
S, K, C, M, G = H.S, H.K, H.C, H.M, H.G

NAME = 'hmg_belt_base'
BY = 0.062
Y_SIGHT = 0.1340
Z_REAR, Z_FRONT = -0.0200, -0.6000
Z_MUZ = -0.7000
PH = -math.pi / 12
MAGW = (0.0, -0.0120, -0.1250)

STOCK = [(0.055, 0.0820), (0.285, 0.0800), (0.312, 0.0740), (0.318, 0.0400), (0.316, -0.0400), (0.300, -0.0620), (0.270, -0.0620), (0.200, -0.0400),
         (0.130, -0.0200), (0.055, -0.0100)]
HOLE = [(0.285, 0.0620), (0.285, -0.0400), (0.200, -0.0220), (0.115, -0.0040), (0.100, 0.0140), (0.100, 0.0620)]


def build(out_dir):
    A = H.make_atlas(out_dir, NAME, wood=False)
    mats = H.finish_mats(A, out_dir, NAME, wood=False)

    rc = C.Part('receiver')
    rp = K.hexp(-0.0300, 0.0300, -0.0150, 0.0920, 0.0120)
    rc.loft([(0.060, rp), (-0.300, rp)], 'steel', top='steel_top')
    cv = K.hexp(-0.0255, 0.0255, 0.0920, 0.1110, 0.0090)
    rc.loft([(-0.035, cv), (-0.215, cv)], 'steel', top='steel_top')                                         # hinged feed cover
    H.rail(rc, -0.050, -0.300, 0.1108)
    rc.box((-0.0262, 0.0900, -0.0420), (0.0262, 0.1120, -0.0480), 'brass')                                  # cover hinge band
    for sgn in (-1, 1):
        a_, b_ = (0.0296, 0.0316) if sgn > 0 else (-0.0316, -0.0296)
        rc.prism(S.cham(-0.250, -0.060, 0.0120, 0.0700, 0.005), a_, b_, 'panel', side='steel', top='steel_top')
        rc.prism(S.cham(0.030, -0.040, 0.0320, 0.0560, 0.004), a_, b_, 'port', side='steel', top='steel_top')
        x0, x1 = (0.0294, 0.0320) if sgn > 0 else (-0.0320, -0.0294)
        for zc in (0.0580, -0.2980):
            rc.box((x0, -0.0160, zc - 0.0030), (x1, 0.0930, zc + 0.0030), 'brass')
    # barrel, hider, gas block
    K.revolve(rc, [(-0.290, 0.0130), (-0.520, 0.0118), (-0.640, 0.0106)], BY, segs=10, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    H.slotted_hider(rc, BY, -0.6400, Z_MUZ, r=0.0150, n_slots=3, segs=10)
    for z0 in (-0.6420, -0.6950):
        K.revolve(rc, [(z0, 0.0160), (z0 - 0.0040, 0.0160)], BY, segs=10, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    K.revolve(rc, [(-0.520, 0.0200), (-0.560, 0.0200)], BY, segs=10, region='steel', cap_f='steel', cap_b='steel', phase=PH)
    # carry handle (steel arch + polymer grip sleeve)
    K.tube(rc, [(-0.340, 0.0860), (-0.340, 0.1400), (-0.475, 0.1400), (-0.475, 0.0860)], 0.0130, 0.0085, 'steel')
    rc.cyl((0, 0.1400, -0.3800), (0, 0.1400, -0.4400), 0.0125, 10, 'poly', cap='poly')
    S.sight_pair(rc, Y_SIGHT, Z_REAR, Z_FRONT, 0.1105, BY + 0.0090, rear_w=0.0125, rear_len=0.016, post_in=0.0030)
    rc.box((-0.0085, BY + 0.0040, Z_FRONT - 0.0120), (0.0085, BY + 0.0120, Z_FRONT + 0.0120), 'steel', top='steel_top')   # front sight base
    # trigger guard band + trigger
    K.tube(rc, [(0.0440, -0.0100), (0.0420, -0.0300), (0.0200, -0.0400), (-0.0050, -0.0340), (-0.0100, -0.0100)], 0.0090, 0.0060, 'steel')
    rc.prism([(0.0230, -0.0100), (0.0170, -0.0100), (0.0175, -0.0200), (0.0200, -0.0300), (0.0250, -0.0310), (0.0240, -0.0200)], -0.0016, 0.0016, 'brass', side='brass')
    # deployed bipod: mount block + two splayed legs with feet
    rc.box((-0.0230, BY - 0.0210, -0.5350), (0.0230, BY - 0.0050, -0.4850), 'steel', top='steel_top')
    for sgn in (-1, 1):
        rc.cyl((sgn * 0.0190, BY - 0.0150, -0.5100), (sgn * 0.0560, -0.1450, -0.5650), 0.0075, 8, 'steel', cap='steel')
        rc.box((sgn * 0.0560 - 0.0110, -0.1520, -0.5800), (sgn * 0.0560 + 0.0110, -0.1420, -0.5500), 'muzzle')
        rc.cyl((sgn * 0.0430, -0.0450, -0.5470), (sgn * 0.0450, -0.0600, -0.5490), 0.0075, 8, 'brass', cap='brass')

    # polymer furniture
    fu = C.Part('furniture')
    K.shell(fu, K.chaikin(STOCK, 1), [HOLE], 0.0190, region='poly', bevel=0.0050, segs=2, bevel_hole=0.0040, gmap=True)
    K.shell(fu, K.chaikin([(0.3000, 0.0800), (0.3220, 0.0760), (0.3260, 0.0000), (0.3200, -0.0620), (0.3000, -0.0620)], 1), [], 0.0215, region='poly', bevel=0.0060, segs=2, gmap=True)
    K.shell(fu, H.grip_poly(0.0500, -0.0100, length=0.120), [], 0.0150, region='poly', bevel=0.0045, segs=2, gmap=True)
    hg = K.hexp(-0.0255, 0.0255, 0.0050, 0.0840, 0.0120)
    fu.loft([(-0.300, hg), (-0.525, hg)], 'poly', top='poly')
    for sgn in (-1, 1):
        x0, x1 = (0.0250, 0.0262) if sgn > 0 else (-0.0262, -0.0250)
        for zc in (-0.340, -0.390, -0.440, -0.490):
            fu.box((x0, 0.0460, zc - 0.0150), (x1, 0.0540, zc + 0.0150), 'muzzle')                           # heat-shield vents
        xb0, xb1 = (0.0215 - 0.0005, 0.0215 + 0.0016) if sgn > 0 else (-0.0215 - 0.0016, -0.0215 + 0.0005)
        fu.cyl((xb0, 0.0080, 0.3110), (xb1, 0.0080, 0.3110), 0.0140, 12, 'brass', cap='bone_stock')       # brass-rimmed bone cross badge on the stock

    # ammo box + belt of brass rounds into the feed
    mg = C.Part('magazine')
    mg.prism(S.cham(-0.190, -0.060, -0.1050, -0.0100, 0.008), -0.0290, 0.0290, 'mag', side='steel')
    mg.box((-0.0298, -0.0980, -0.1950), (0.0298, -0.0920, -0.0550), 'brass')
    for i in range(8):
        t = i / 7.0
        y = 0.056 - 0.082 * t
        z = -0.126 - 0.060 * math.sin(math.pi * t)
        mg.cyl((0.0270, y, z), (0.0680, y, z), 0.0068, 6, 'brass', cap='brass')
        mg.box((0.0270, y - 0.0050, z - 0.0050), (0.0340, y + 0.0050, z + 0.0050), 'steel')

    objs = {}
    for p, ml in ((rc, 0.030), (fu, 0.030), (mg, 0.9)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p is fu else 35))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('hmg_belt', objs, {
        'muzzle': (0, BY, Z_MUZ), 'mag_well': MAGW, 'rear_sight': (0, Y_SIGHT, Z_REAR), 'front_sight': (0, Y_SIGHT, Z_FRONT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'hmg_belt', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
