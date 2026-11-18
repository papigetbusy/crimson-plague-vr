"""Crimson Plague VR - smg_drum_base: the Drum SMG.

Original low-poly PS2 / Snake Eater style drum-magazine submachine gun
(Thompson M1928 / Tommy-gun proportions: finned barrel with Cutts-style
compensator, walnut forend with vertical foregrip, walnut pistol grip and
buttstock, side-mounted cocking knob, round 50-shot drum), dressed Gothic in
the same style as the batch 1 pistols: dark blued receiver with engraved
scrollwork and lancet-arch plates, dark walnut furniture with carved bone
cross plaques and bone foregrip cap, brass straps, fin ring collars,
compensator rings, cocking knob and drum band. Steel and brass share the
locked 1911 metal material (metallic 1 / roughness 0.30); walnut + bone share
one non-metal material; one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_drum_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/smg_drum_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/smg_drum_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_drum_base.py -- --render-glb assets/models/gun/smg_drum_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: receiver (receiver, plates, barrel + fins + compensator, trigger guard, sights),
furniture (walnut stock, grip, forend, vertical foregrip, bone plaques, brass plates),
cocking_handle (brass knob, slides back), magazine (50-round drum, under mag_well).
Empties: muzzle, mag_well, rear_sight, front_sight. rear/front share X=0 and Y, so
the sight line is exactly parallel to the bore (dir 0,0,-1); bore is 46 mm below it.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_gothic_common as K
C, M, G = K.C, K.M, K.G

NAME = 'smg_drum_base'
TH = math.radians(17)
BY = 0.060                       # bore height
Z_MUZ = -0.400
Y_SIGHT = 0.1060
Z_REAR_SIGHT, Z_FRONT_SIGHT = -0.0288, -0.3800
PH = -math.pi / 12
R_Y0, R_Y1 = 0.035, 0.086        # receiver bottom / top
DRUM_C = (0.0, -0.015, -0.105)   # drum axis (x, y, z)
DRUM_R = 0.048
MAGW = (0.0, R_Y0, DRUM_C[2])    # mag_well: top of the drum neck at the receiver floor
GRIP_TOP, GRIP_BOT = 0.050, -0.062

K.PAL.update({'w_shadow': (10, 6, 4), 'w_dark': (26, 15, 8), 'w_mid': (42, 24, 13), 'w_light': (64, 38, 20), 'w_hi': (96, 62, 34)})
K.FURN.update({'wood', 'wood_end'})


def cham(z0, z1, y0, y1, c):
    return [(z0 + c, y0), (z1 - c, y0), (z1, y0 + c), (z1, y1 - c), (z1 - c, y1), (z0 + c, y1), (z0, y1 - c), (z0, y0 + c)]


def paint_wood(A, r, seed=71, end=False):
    x0, y0, x1, y1 = A.reg[r]
    for y in range(y0, y1):
        for x in range(x0, x1):
            n = K._vn(x * 0.18, y, 3, seed)
            g = math.sin((y - y0) * 0.62 + 6.0 * n + 0.04 * (x - x0))
            c = 'w_light' if g > 0.78 else 'w_mid' if g > 0.15 else 'w_dark' if g > -0.62 else 'w_shadow'
            if end:
                c = 'w_dark' if K._h(x, y, seed) > 0.3 else 'w_shadow'
            h = K._h(x, y, seed + 3)
            if h > 0.992:
                c = 'w_hi'
            elif h < 0.015:
                c = 'w_shadow'
            A.put(x, y, c)


def paint_drum_rim(A, r):
    x0, y0, x1, y1 = A.reg[r]
    A.steel(r, ('steel_black', 'steel_dark', 'steel_mid', 'steel_light'), 73, grime=0.80, edge=False)
    for x in range(x0 + 2, x1 - 2):
        if (x - x0) % 4 == 0:
            for y in range(y0 + 2, y1 - 2):
                A.put(x, y, 'steel_light' if (x - x0) % 8 else 'recess')


def paint_drum_face(A, r):
    x0, y0, x1, y1 = A.reg[r]
    cx, cy = (x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2
    R = (x1 - x0) / 2
    for y in range(y0, y1):
        for x in range(x0, x1):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy) / R
            a = math.atan2(dy, dx)
            sec = int(((a + math.pi) / (2 * math.pi)) * 16) % 16
            if d > 0.94:
                c = 'steel_black'
            elif d > 0.84:
                c = 'steel_light' if d < 0.90 else 'steel_edge'
            elif d > 0.42:
                c = 'steel_dark' if sec % 2 == 0 else 'steel_mid'
                if abs(math.sin(a * 8)) < 0.10:
                    c = 'recess'
            elif d > 0.36:
                c = 'brass_shadow'
            elif d > 0.12:
                c = 'brass_light' if (dy < 0 and d < 0.30) else 'brass'
            else:
                c = 'brass_dark'
            A.put(x, y, c)
    for d in range(-8, 9):                                  # small engraved cross on the brass hub
        A.put(int(cx) + d, int(cy), 'brass_shadow'); A.put(int(cx), int(cy) + d, 'brass_shadow')


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('fins', 32, 32), ('panel', 112, 36), ('wood', 64, 64), ('drum_face', 64, 64), ('bone_inlay', 48, 48),
        ('drum_rim', 48, 16), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24),
        ('bone_end', 16, 16), ('wood_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=22, grime=0.82)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.wrap('fins', 8, 4, lambda j: 'hi' if j in (1, 2) else 'plain', seed=15)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_inlay', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    paint_wood(A, 'wood'); paint_wood(A, 'wood_end', seed=75, end=True)
    paint_drum_rim(A, 'drum_rim'); paint_drum_face(A, 'drum_face')
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = C.make_materials(NAME, tex, furn='wood')
    mats[1].name = NAME + '_wood'
    b = mats[1].node_tree.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Specular IOR Level'].default_value = 0.25

    # ---------------- receiver + barrel group ----------------
    rc = C.Part('receiver')
    prof = K.hexp(-0.0185, 0.0185, R_Y0, R_Y1, 0.0040)
    rc.loft([(-0.155, prof), (0.050, prof)], 'steel', top='steel_top')
    for sgn in (-1, 1):
        a, b_ = (0.0180, 0.0215) if sgn > 0 else (-0.0215, -0.0180)
        rc.prism(cham(-0.1445, -0.0475, 0.0425, 0.0790, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        rc.prism(cham(-0.0385, 0.0445, 0.0425, 0.0790, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        for zc in (-0.1500, -0.0430, 0.0480):                              # brass straps over plate joints
            x0, x1 = (0.0178, 0.0220) if sgn > 0 else (-0.0220, -0.0178)
            rc.box((x0, R_Y0 - 0.001, zc - 0.0025), (x1, R_Y1 + 0.0015, zc + 0.0025), 'brass')
        rc.cyl((sgn * 0.0190, 0.0620, 0.0130), (sgn * 0.0225, 0.0620, 0.0130), 0.0032, 8, 'brass', cap='brass')
    # barrel, cooling fins, ring collars, Cutts-style compensator
    K.revolve(rc, [(-0.150, 0.0095), (-0.352, 0.0095)], BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    for i in range(11):
        z0 = -0.170 - i * 0.0165
        K.revolve(rc, [(z0, 0.0140), (z0 - 0.0045, 0.0140)], BY, segs=8, region='fins', cap_f='steel', cap_b='steel')
    K.revolve(rc, [(-0.1550, 0.0128), (-0.1630, 0.0128)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    K.revolve(rc, [(-0.3500, 0.0118), (-0.3930, 0.0118), (Z_MUZ, 0.0092)], BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, z1 in ((-0.3500, -0.3560), (-0.3860, -0.3910)):
        K.revolve(rc, [(z0, 0.0130), (z1, 0.0130)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for zz in (-0.3660, -0.3720, -0.3790):                                  # compensator slots
        rc.box((-0.0040, BY + 0.0104, zz - 0.0020), (0.0040, BY + 0.0118, zz + 0.0020), 'steel')
    # trigger guard + trigger
    K.tube(rc, [(-0.0520, 0.0345), (-0.0560, 0.0120), (-0.0480, -0.0140), (-0.0300, -0.0225), (-0.0185, -0.0160)], 0.0072, 0.0074, 'steel')
    rc.prism([(-0.0330, 0.0340), (-0.0270, 0.0340), (-0.0285, 0.0170), (-0.0310, 0.0070), (-0.0350, 0.0030), (-0.0385, 0.0035),
              (-0.0365, 0.0110), (-0.0345, 0.0190)], -0.0020, 0.0020, 'brass', side='brass')
    # rear sight (ladder posts, brass tips) + front sight (blade between ears, brass bead)
    rc.box((-0.0125, R_Y1 - 0.0005, -0.0385), (0.0125, 0.0905, -0.0185), 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0045, 0.0100) if sgn > 0 else (-0.0100, -0.0045)
        rc.box((lo, 0.0905, -0.0350), (hi, Y_SIGHT, -0.0225), 'steel', top='steel_top')
        rc.box((lo, Y_SIGHT - 0.0009, -0.0350), (hi, Y_SIGHT, -0.0225), 'brass')
    rc.box((-0.0070, 0.0700, -0.3865), (0.0070, 0.0800, -0.3735), 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0040, 0.0065) if sgn > 0 else (-0.0065, -0.0040)
        rc.box((lo, 0.0800, -0.3865), (hi, 0.0965, -0.3735), 'steel', top='steel_top')
    rc.box((-0.0028, 0.0800, -0.3825), (0.0028, Y_SIGHT - 0.0016, -0.3775), 'steel')
    rc.box((-0.0016, Y_SIGHT - 0.0016, -0.3818), (0.0016, Y_SIGHT, -0.3782), 'brass')

    # ---------------- walnut furniture ----------------
    fu = C.Part('furniture')
    stock = [(0.048, 0.082), (0.200, 0.078), (0.312, 0.068), (0.332, 0.062), (0.338, -0.046), (0.322, -0.052), (0.300, -0.030),
             (0.200, 0.020), (0.130, 0.028), (0.048, 0.036)]
    fu.prism(stock, -0.0175, 0.0175, 'wood', side='wood_end')
    fu.prism([(0.3365, -0.0490), (0.3440, -0.0490), (0.3440, 0.0630), (0.3300, 0.0630)], -0.0185, 0.0185, 'brass', side='brass')
    for sgn in (-1, 1):
        lo, hi = (0.0175, 0.0192) if sgn > 0 else (-0.0192, -0.0175)
        fu.prism(K.chaikin([(0.212, 0.012), (0.212, 0.066), (0.274, 0.066), (0.274, 0.012)], 1), lo, hi, 'bone_inlay', side='bone_end')
        fu.cyl((sgn * 0.0172, 0.0560, 0.082), (sgn * 0.0200, 0.0560, 0.082), 0.0034, 8, 'brass', cap='brass')   # stock bolt
    # pistol grip
    grip = [(-0.0225, GRIP_TOP), (-0.0235, 0.020), (-0.0240, -0.015), (-0.0225, GRIP_BOT), (0.0205, GRIP_BOT), (0.0235, -0.030),
            (0.0245, 0.000), (0.0240, 0.030), (0.0220, GRIP_TOP)]
    K.prism_ah(fu, K.chaikin(grip, 1), TH, -0.0135, 0.0135, 'wood', side='wood_end')
    zb = K.ah_to_zy([(-0.0235, GRIP_BOT), (0.0212, GRIP_BOT), (0.0212, GRIP_BOT - 0.0070), (-0.0235, GRIP_BOT - 0.0070)], TH)
    fu.prism(zb, -0.0148, 0.0148, 'brass', side='brass')
    for sgn in (-1, 1):
        zy = K.ah_to_zy([(0.0, 0.012)], TH)[0]
        fu.cyl((sgn * 0.0132, zy[1], zy[0]), (sgn * 0.0152, zy[1], zy[0]), 0.0030, 8, 'brass', cap='brass')
    # forend (under the barrel) + bone plaque, vertical foregrip with brass collar and bone cap
    fe = K.chaikin([(-0.158, 0.046), (-0.160, 0.014), (-0.172, 0.004), (-0.255, 0.004), (-0.264, 0.016), (-0.264, 0.044)], 1)
    fu.prism(fe, -0.0165, 0.0165, 'wood', side='wood_end')
    fu.box((-0.0172, 0.0020, -0.1660), (0.0172, 0.0480, -0.1610), 'brass')
    for sgn in (-1, 1):
        lo, hi = (0.0165, 0.0180) if sgn > 0 else (-0.0180, -0.0165)
        fu.prism(K.chaikin([(-0.250, 0.0085), (-0.250, 0.0405), (-0.218, 0.0405), (-0.218, 0.0085)], 1), lo, hi, 'bone_inlay', side='bone_end')
    vg = K.chaikin([(-0.2335, 0.006), (-0.2380, -0.030), (-0.2320, -0.070), (-0.2200, -0.0925), (-0.2000, -0.0925), (-0.1920, -0.070),
                    (-0.1960, -0.030), (-0.1975, 0.006)], 1)
    fu.prism(vg, -0.0125, 0.0125, 'wood', side='wood_end')
    fu.box((-0.0133, -0.0040, -0.2385), (0.0133, 0.0060, -0.1925), 'brass')
    fu.prism([(-0.2185, -0.0925), (-0.2015, -0.0925), (-0.2030, -0.0985), (-0.2170, -0.0985)], -0.0105, 0.0105, 'bone_end', side='bone_end')

    # ---------------- cocking knob (brass, slides back along the right side) ----------------
    ch = C.Part('cocking_handle')
    ch.box((0.0205, 0.0575, -0.0400), (0.0250, 0.0685, -0.0100), 'brass')
    ch.cyl((0.0250, 0.0630, -0.0250), (0.0320, 0.0630, -0.0250), 0.0062, 8, 'brass', cap='brass')

    # ---------------- 50-round drum magazine ----------------
    mg = C.Part('magazine')
    cx, cy, cz = DRUM_C[0], DRUM_C[1], DRUM_C[2]
    mg.cyl((-0.0235, cy, cz), (0.0235, cy, cz), DRUM_R, 16, 'drum_rim', cap='drum_rim')
    for sgn in (-1, 1):
        a, b_ = (0.0235, 0.0270) if sgn > 0 else (-0.0270, -0.0235)
        mg.cyl((a, cy, cz), (b_, cy, cz), 0.0400, 16, 'drum_rim', cap='drum_face')
    mg.cyl((-0.0045, cy, cz), (0.0045, cy, cz), 0.0520, 16, 'brass', cap='brass')
    mg.box((-0.0150, 0.0300, cz - 0.0200), (0.0150, 0.0400, cz + 0.0200), 'steel')           # neck into the well

    objs = {p.name: p.to_object(mats) for p in (rc, fu, ch, mg)}
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('smg_drum', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_REAR_SIGHT),
        'front_sight': (0, Y_SIGHT, Z_FRONT_SIGHT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'smg_drum')


if __name__ == '__main__':
    K.run(finish, render, NAME)
