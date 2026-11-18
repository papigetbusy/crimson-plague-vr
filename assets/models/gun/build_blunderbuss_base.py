"""Crimson Plague VR - shotgun_blunderbuss_base: the Blunderbuss.

Original low-poly PS2 / Snake Eater style flintlock blunderbuss (late-1700s
coaching blunderbuss proportions: short octagonal barrel swelling into a flared
brass bell mouth, side-mounted flintlock with cock, frizzen and pan, full walnut
stock with a deep wrist and a curved butt, brass furniture), dressed Gothic in
the batch 1 / 2 style: dark blued steel with engraved scrollwork, a fluted brass
bell with a dark mouth, engraved lock plate, brass guard / tang / bands / butt
plate, dark walnut stock with carved bone cross plaques, and a brass powder
flask on the left of the stock (= the magazine node). Steel and brass share the
locked 1911 metal material (metallic 1 / roughness 0.30); walnut + bone share
one non-metal material; one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_blunderbuss_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/shotgun_blunderbuss_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/shotgun_blunderbuss_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_blunderbuss_base.py -- --render-glb assets/models/gun/shotgun_blunderbuss_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: receiver (octagonal barrel, brass bell, lock plate, frizzen, pan, guard, trigger, sights), furniture (walnut stock,
bone plaques, brass butt plate and bands), hammer (the flint cock, origin at its pivot), magazine (brass powder flask).
Empties: muzzle (centre of the bell mouth), mag_well (flask centre), rear_sight, front_sight. rear/front share X=0 and Y
(rear = two brass-tipped spires on the breech, front = a bead on the rim of the bell), so the sight line is exactly
parallel to the bore (bore 38 mm below it).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_shotgun_common as S
K, C, M, G = S.K, S.C, S.M, S.G

NAME = 'shotgun_blunderbuss_base'
BY = 0.070
Y_SIGHT = 0.1060
Z_MUZ = -0.404
Z_REAR_SIGHT, Z_FRONT_SIGHT = -0.0650, -0.3920
PH = -math.pi / 8
HAM_PIVOT = (0.0, 0.0460, 0.0100)
FLASK_C = (-0.0235, -0.0020, 0.1700)
MAGW = FLASK_C


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('bell', 64, 64), ('lock', 64, 40), ('wood', 64, 64), ('bone_stock', 48, 48),
        ('steel', 48, 32), ('steel_top', 48, 24), ('bellmouth', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16), ('wood_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('lock', seed=14, lam=18, grime=0.82, cross=True)
    A.wrap('barrel', 8, 9, lambda j: 'eng' if j in (0, 4) else 'hi' if j == 2 else 'dark' if j == 6 else 'plain', seed=11, lam=16)
    A.wrap('bell', 8, 8, lambda j: 'plain', seed=23, u_bands=[(0.0, 1.0, 'brass')])
    bx0, by0, bx1, by1 = A.reg['bell']
    for j in range(8):                                   # engraved flutes + rings on the brass bell
        ya = by0 + j * 8
        for x in range(bx0 + 3, bx1 - 10):
            if ((x - bx0) // 5) % 2 == 0:
                A.rect(x, ya + 2, x + 1, ya + 6, 'brass_dark')
    for xa in (bx0 + 1, bx1 - 9):
        A.rect(xa, by0, xa + 2, by1, 'brass_shadow')
    A.rect(bx1 - 7, by0, bx1, by1, 'brass_light')
    A.rect(bx1 - 3, by0, bx1, by1, 'brass_dark')
    A.muzzle('bellmouth', brass=True); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    S.paint_wood(A, 'wood'); S.paint_wood(A, 'wood_end', seed=75, end=True)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_mats(NAME, tex)

    # ---------------- barrel, bell, lock hardware ----------------
    rc = C.Part('receiver')
    K.revolve(rc, [(-0.040, 0.0185), (-0.090, 0.0176), (-0.200, 0.0150), (-0.285, 0.0130)], BY, segs=8, region='barrel',
              cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.2850, 0.0130), (-0.3200, 0.0172), (-0.3600, 0.0238), (-0.3960, 0.0305), (Z_MUZ, 0.0312)], BY, segs=8,
              region='bell', cap_f='bellmouth', cap_b='steel', phase=PH)
    for z0, z1, r in ((-0.0950, -0.1050, 0.0206), (-0.1850, -0.1930, 0.0178), (-0.2800, -0.2880, 0.0160)):     # brass barrel bands
        K.revolve(rc, [(z0, r), (z1, r)], BY, segs=8, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    rc.box((-0.0100, BY - 0.0040, -0.0420), (0.0100, BY + 0.0210, -0.0300), 'steel', top='steel_top')            # breech plug / touch-hole block
    # lock plate (right), brass pan, frizzen, tail screws; blank steel counter plate on the left
    plate = K.chaikin([(-0.0800, 0.0400), (-0.0640, 0.0580), (-0.0320, 0.0650), (0.0100, 0.0660), (0.0360, 0.0560), (0.0420, 0.0440),
                       (0.0260, 0.0350), (-0.0300, 0.0340)], 1)
    rc.prism(plate, 0.0162, 0.0196, 'lock', side='steel', top='steel_top')
    rc.prism(K.chaikin([(-0.0200, 0.0400), (0.0000, 0.0560), (0.0250, 0.0540), (0.0280, 0.0420), (0.0100, 0.0360)], 1), -0.0194, -0.0162, 'steel', side='steel', top='steel_top')
    rc.box((0.0170, 0.0560, -0.0680), (0.0262, 0.0625, -0.0400), 'brass')                                         # flash pan
    rc.prism([(-0.0700, 0.0620), (-0.0640, 0.0620), (-0.0620, 0.0880), (-0.0760, 0.0925), (-0.0760, 0.0865), (-0.0690, 0.0845)],
             0.0188, 0.0214, 'steel_top', side='steel')                                                          # frizzen
    rc.box((0.0186, 0.0868, -0.0770), (0.0216, 0.0925, -0.0690), 'brass')                                         # frizzen face
    for (zz, yy) in ((-0.0560, 0.0450), (0.0240, 0.0590)):
        rc.cyl((0.0196, yy, zz), (0.0226, yy, zz), 0.0030, 8, 'brass', cap='brass')
        rc.cyl((-0.0194, yy, zz), (-0.0224, yy, zz), 0.0030, 8, 'brass', cap='brass')
    # trigger guard (brass bow) + trigger
    K.tube(rc, [(-0.0750, 0.0120), (-0.0780, -0.0140), (-0.0620, -0.0360), (-0.0420, -0.0400), (-0.0240, -0.0340)], 0.0066, 0.0070, 'brass')
    rc.prism([(-0.0480, 0.0300), (-0.0430, 0.0300), (-0.0440, 0.0140), (-0.0460, 0.0000), (-0.0500, -0.0140), (-0.0530, -0.0170),
              (-0.0555, -0.0120), (-0.0530, 0.0000), (-0.0495, 0.0150)], -0.0018, 0.0018, 'brass', side='brass')
    # sights: two brass-tipped spires on the breech, bead on the bell rim
    rc.box((-0.0095, 0.0860, -0.0750), (0.0095, 0.0905, -0.0550), 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0030, 0.0058) if sgn > 0 else (-0.0058, -0.0030)
        rc.box((lo, 0.0905, -0.0730), (hi, Y_SIGHT, -0.0570), 'steel', top='steel_top')
        rc.box((lo, Y_SIGHT - 0.0010, -0.0730), (hi, Y_SIGHT, -0.0570), 'brass')
    rc.box((-0.0034, 0.0950, -0.3980), (0.0034, Y_SIGHT - 0.0016, -0.3860), 'steel', top='steel_top')
    rc.box((-0.0018, Y_SIGHT - 0.0016, -0.3938), (0.0018, Y_SIGHT, -0.3902), 'brass')

    # ---------------- walnut stock ----------------
    fu = C.Part('furniture')
    stock = [(-0.230, 0.0560), (-0.230, 0.0260), (-0.215, 0.0200), (-0.090, 0.0200), (-0.060, 0.0100), (-0.040, -0.0120), (-0.026, -0.0380),
             (0.004, -0.0540), (0.044, -0.0460), (0.082, -0.0240), (0.170, -0.0300), (0.260, -0.0600), (0.300, -0.0880), (0.322, -0.0740),
             (0.326, 0.0300), (0.322, 0.0460), (0.250, 0.0520), (0.150, 0.0580), (0.060, 0.0620), (0.030, 0.0600), (-0.030, 0.0560)]
    fu.prism(stock, -0.0165, 0.0165, 'wood', side='wood_end')
    fu.prism([(0.3225, 0.0480), (0.3310, 0.0480), (0.3310, -0.0720), (0.3010, -0.0930), (0.2960, -0.0850), (0.3225, -0.0690)], -0.0175, 0.0175, 'brass', side='brass')
    for sgn in (-1, 1):
        if sgn > 0:
            lo, hi = 0.0165, 0.0184
            fu.prism(K.chaikin(S.cham(0.152, 0.226, -0.020, 0.044, 0.010), 1), lo, hi, 'bone_stock', side='bone_end')
        fu.cyl((sgn * 0.0162, 0.0480, 0.2900), (sgn * 0.0194, 0.0480, 0.2900), 0.0030, 8, 'brass', cap='brass')
    fu.prism([(0.0100, 0.0600), (0.0460, 0.0600), (0.0560, 0.0620), (0.0560, 0.0645), (0.0100, 0.0645)], -0.0090, 0.0090, 'brass', side='brass')   # brass tang plate
    fu.prism([(-0.0050, -0.0520), (0.0220, -0.0600), (0.0420, -0.0500), (0.0400, -0.0440), (0.0000, -0.0430)], -0.0090, 0.0090, 'brass', side='brass')  # wrist cap
    for zc in (-0.2250, -0.1650):                                              # brass fore bands around barrel + wood
        fu.loft([(zc, K.hexp(-0.0185, 0.0185, 0.0180, 0.0860, 0.0070)), (zc - 0.0070, K.hexp(-0.0185, 0.0185, 0.0180, 0.0860, 0.0070))], 'brass')
    fu.box((-0.0170, 0.0170, -0.2420), (0.0170, 0.0540, -0.2300), 'bone_end')  # bone fore tip

    # ---------------- flint cock (hammer; pivots at HAM_PIVOT) ----------------
    hm = C.Part('hammer')
    cock = K.chaikin([(0.0160, 0.0400), (0.0245, 0.0400), (0.0270, 0.0560), (0.0130, 0.0760), (-0.0100, 0.0870), (-0.0300, 0.0920),
                      (-0.0340, 0.0860), (-0.0240, 0.0800), (-0.0120, 0.0720), (0.0040, 0.0580), (0.0060, 0.0440)], 1)
    hm.prism(cock, 0.0188, 0.0224, 'steel_top', side='steel')
    hm.box((0.0190, 0.0820, -0.0400), (0.0222, 0.0900, -0.0300), 'bone_end')                            # flint
    hm.cyl((0.0186, 0.0460, 0.0100), (0.0236, 0.0460, 0.0100), 0.0036, 8, 'brass', cap='brass')

    # ---------------- brass powder flask on the left of the stock (= magazine) ----------------
    mg = C.Part('magazine')
    fl = K.chaikin([(0.1680, 0.0500), (0.1720, 0.0500), (0.1760, 0.0360), (0.2060, 0.0120), (0.2120, -0.0200), (0.1960, -0.0460),
                    (0.1440, -0.0460), (0.1280, -0.0200), (0.1340, 0.0120), (0.1640, 0.0360)], 1)
    mg.prism(fl, -0.0300, -0.0170, 'brass', side='brass')
    mg.box((-0.0262, 0.0500, 0.1660), (-0.0208, 0.0580, 0.1740), 'bone_end')
    mg.box((-0.0306, -0.0060, 0.1440), (-0.0164, 0.0000, 0.1960), 'steel')

    objs = {p.name: p.to_object(mats) for p in (rc, fu, hm, mg)}
    M.set_origin_world(objs['hammer'], G(*HAM_PIVOT))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('shotgun_blunderbuss', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_REAR_SIGHT),
        'front_sight': (0, Y_SIGHT, Z_FRONT_SIGHT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'shotgun_blunderbuss', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
