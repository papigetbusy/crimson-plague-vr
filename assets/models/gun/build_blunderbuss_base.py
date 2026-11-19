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
PH = -math.pi / 14
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
    for xa in (bx0 + 1, bx1 - 9):                         # raised ring bands on the brass bell
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
    K.revolve(rc, [(-0.040, 0.0160), (-0.090, 0.0150), (-0.200, 0.0125), (-0.285, 0.0108)], BY, segs=14, region='barrel',
              cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.2850, 0.0108), (-0.3200, 0.0132), (-0.3600, 0.0178), (-0.3960, 0.0238), (Z_MUZ, 0.0250)], BY, segs=24,
              region='bell', cap_f='bellmouth', cap_b='steel', phase=PH)
    for z0, z1, r in ((-0.0950, -0.1050, 0.0180), (-0.1850, -0.1930, 0.0150), (-0.2800, -0.2880, 0.0128)):     # brass barrel bands
        K.revolve(rc, [(z0, r), (z1, r)], BY, segs=14, region='brass', cap_f='brass', cap_b='brass', phase=PH)
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
    K.tube(rc, [(-0.0750, 0.0350), (-0.0780, 0.0150), (-0.0640, 0.0020), (-0.0440, -0.0010), (-0.0260, 0.0080)], 0.0066, 0.0070, 'brass')
    rc.prism([(-0.0480, 0.0360), (-0.0430, 0.0360), (-0.0440, 0.0250), (-0.0460, 0.0170), (-0.0500, 0.0080), (-0.0530, 0.0060),
              (-0.0555, 0.0100), (-0.0530, 0.0170), (-0.0495, 0.0260)], -0.0018, 0.0018, 'brass', side='brass')
    # sights: two brass-tipped spires on the breech, bead on the bell rim
    rc.box((-0.0095, 0.0860, -0.0750), (0.0095, 0.0905, -0.0550), 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0030, 0.0058) if sgn > 0 else (-0.0058, -0.0030)
        rc.box((lo, 0.0905, -0.0730), (hi, Y_SIGHT, -0.0570), 'steel', top='steel_top')
        rc.box((lo, Y_SIGHT - 0.0010, -0.0730), (hi, Y_SIGHT, -0.0570), 'brass')
    rc.box((-0.0034, 0.0930, -0.3980), (0.0034, Y_SIGHT - 0.0016, -0.3860), 'steel', top='steel_top')
    rc.box((-0.0018, Y_SIGHT - 0.0016, -0.3938), (0.0018, Y_SIGHT, -0.3902), 'brass')

    # ---------------- walnut stock ----------------
    fu = C.Part('furniture')
    # stock side profile traced from the Met flintlock blunderbuss photo (/workspace/gun_brief/refs/shotgun_blunderbuss): raked butt, straight
    # wedge buttstock with a sharp heel drop, belly rising to the lock, slim full-length forestock
    stock = [(0.329, 0.0200), (0.309, 0.0309), (0.289, 0.0347), (0.269, 0.0379), (0.249, 0.0412), (0.228, 0.0445), (0.208, 0.0487),
             (0.188, 0.0538), (0.168, 0.0585), (0.130, 0.0620), (0.090, 0.0640), (0.030, 0.0640), (-0.050, 0.0640), (-0.150, 0.0640),
             (-0.250, 0.0630), (-0.286, 0.0600), (-0.290, 0.0500), (-0.288, 0.0360), (-0.270, 0.0330), (-0.150, 0.0345), (-0.050, 0.0345),
             (0.027, 0.0314), (0.060, 0.0290), (0.088, 0.0262), (0.108, 0.0200), (0.128, 0.0110), (0.148, 0.0030), (0.168, -0.0070),
             (0.188, -0.0170), (0.208, -0.0270), (0.228, -0.0370), (0.249, -0.0465), (0.269, -0.0565), (0.289, -0.0660), (0.305, -0.0700)]
    K.shell(fu, stock, [], 0.0165, region='wood', bevel=0.0050, segs=2, gmap=True)
    fu.prism([(0.3290, 0.0200), (0.3370, 0.0200), (0.3130, -0.0700), (0.3050, -0.0700)], -0.0175, 0.0175, 'brass', side='brass')
    for sgn in (-1, 1):
        if sgn > 0:
            x0, x1 = (0.0165 - 0.0005, 0.0165 + 0.0016)
            fu.cyl((x0, -0.0020, 0.2350), (x1, -0.0020, 0.2350), 0.0145, 12, 'brass', cap='bone_stock')          # brass-rimmed bone cross badge
        fu.cyl((sgn * 0.0162, 0.0320, 0.2900), (sgn * 0.0194, 0.0320, 0.2900), 0.0030, 8, 'brass', cap='brass')
    fu.prism([(0.0100, 0.0600), (0.0460, 0.0600), (0.0560, 0.0620), (0.0560, 0.0645), (0.0100, 0.0645)], -0.0090, 0.0090, 'brass', side='brass')   # brass tang plate
    for zc in (-0.2400, -0.1650):                                              # brass fore bands around barrel + wood
        fu.loft([(zc, K.hexp(-0.0185, 0.0185, 0.0320, 0.0840, 0.0070)), (zc - 0.0070, K.hexp(-0.0185, 0.0185, 0.0320, 0.0840, 0.0070))], 'brass')
    fu.box((-0.0170, 0.0340, -0.2960), (0.0170, 0.0620, -0.2850), 'brass')  # brass fore tip

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
    before = set(mg.bm.verts)
    K.shell(mg, fl, [], 0.0140, region='brass', bevel=0.0045, segs=2)          # real volume: a rounded 28 mm thick flask
    import bmesh as _bm
    _bm.ops.translate(mg.bm, verts=[v for v in mg.bm.verts if v not in before], vec=G(-0.0295, 0, 0))
    for sgn in (1,):
        pass
    mg.box((-0.0322, 0.0500, 0.1660), (-0.0268, 0.0580, 0.1740), 'bone_end')                       # bone stopper
    mg.box((-0.0452, -0.0070, 0.1440), (-0.0138, 0.0000, 0.1960), 'steel')                          # steel strap round the flask belly
    mg.cyl((-0.0450, 0.0200, 0.1700), (-0.0432, 0.0200, 0.1700), 0.0085, 12, 'brass', cap='bone_stock')   # brass-rimmed bone cross badge on the flask

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
