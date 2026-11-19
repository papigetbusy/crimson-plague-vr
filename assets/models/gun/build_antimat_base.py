"""Crimson Plague VR - sniper_antimat_base: the Anti-Materiel Rifle.

Original low-poly PS2 / Snake Eater style .50 anti-materiel rifle (Barrett M82 proportions, traced from the M82A1
photo in /workspace/gun_brief/refs/sniper_antimat): long slab receiver with a Picatinny rail, skeleton frame stock
with a thick butt pad (shell with a real cut-out), raked pistol grip, boxy 10-round magazine, heavy barrel with a
slotted muzzle brake, folded bipod legs, carry handle and a big gothic scope. Steel + brass on the locked 1911 metal
material, glossy near-black clearcoat polymer (bullpup polish3 recipe) for stock + grip, bone cross badge inset in
the butt pad. One 1024 px smooth albedo, glTF sampler LINEAR.

Meshes: receiver (receiver, plates, barrel, brake, scope, handle, bipod, guard), furniture (frame stock, butt pad, grip),
magazine (box mag under mag_well). Empties: muzzle, mag_well, rear_sight (scope ocular), front_sight (scope objective).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_sniper_common as SN
S, K, C, M, G = SN.S, SN.K, SN.C, SN.M, SN.G

NAME = 'sniper_antimat_base'
BY = 0.060
RAIL_TOP = 0.0985
Y_SIGHT = 0.1285
Z_OC, Z_OBJ = 0.012, -0.352
Z_MUZ = -1.000
PH = -math.pi / 12
MAGW = (0.0, -0.0150, -0.1130)

# skeleton stock frame (outer triangle + cut-out), traced proportions from the M82A1 side photo
FRAME = [(0.362, 0.0450), (0.362, -0.0600), (0.040, 0.0150), (0.040, 0.0450)]
FRAME_HOLE = [(0.340, 0.0330), (0.340, -0.0379), (0.085, 0.0200), (0.085, 0.0330)]
GRIP = [(0.100, -0.0200), (0.095, -0.0480), (0.082, -0.0900), (0.064, -0.1200), (0.034, -0.1180), (0.028, -0.0850), (0.012, -0.0450),
        (0.002, -0.0100), (0.060, -0.0100)]


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('tube', 128, 48), ('panel', 112, 36), ('port', 56, 28), ('poly', 128, 40), ('mag', 96, 32),
        ('bone_stock', 40, 40), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=22, grime=0.84, arches=True)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.wrap('tube', 8, 6, lambda j: 'eng' if j in (0, 4) else 'hi' if j == 2 else 'dark' if j == 6 else 'plain', seed=17, lam=16)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    A.poly('poly', seed=43, fine=True); S.paint_port(A, 'port'); A.mag('mag', holes=True)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_poly_mats(NAME, tex)

    # ---------------- receiver group ----------------
    rc = C.Part('receiver')
    rear = K.hexp(-0.0230, 0.0230, -0.0126, 0.0850, 0.0100)
    rc.loft([(0.040, rear), (-0.300, rear)], 'steel', top='steel_top')
    fore = K.hexp(-0.0210, 0.0210, 0.0120, 0.0850, 0.0090)
    rc.loft([(-0.300, fore), (-0.505, fore)], 'steel', top='steel_top')
    rc.box((-0.0085, 0.0848, -0.500), (0.0085, RAIL_TOP, 0.040), 'steel', top='steel_top')                      # Picatinny rail
    zz = 0.040
    while zz - 0.0120 > -0.500:
        rc.box((-0.0085, RAIL_TOP - 0.0006, zz - 0.0120), (0.0085, RAIL_TOP + 0.0014, zz), 'steel', top='steel_top')   # rail teeth
        zz -= 0.0250
    for sgn in (-1, 1):
        a_, b_ = (0.0226, 0.0246) if sgn > 0 else (-0.0246, -0.0226)
        rc.prism(S.cham(-0.060, 0.025, 0.0080, 0.0700, 0.006), a_, b_, 'panel', side='steel', top='steel_top')
        rc.prism(S.cham(-0.275, -0.115, 0.0300, 0.0700, 0.005), a_, b_, 'port', side='steel', top='steel_top')
        for zc in (0.0330, -0.0950, -0.2900):
            x0, x1 = (0.0224, 0.0250) if sgn > 0 else (-0.0250, -0.0224)
            rc.box((x0, -0.0136, zc - 0.0030), (x1, 0.0860, zc + 0.0030), 'brass')
    # barrel + brake
    K.revolve(rc, [(-0.480, 0.0140), (-0.700, 0.0128), (-0.930, 0.0112)], BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.9300, 0.0112), (-0.9340, 0.0240), (-0.9980, 0.0240), (Z_MUZ, 0.0205)], BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0 in (-0.9340, -0.9640, -0.9900):
        K.revolve(rc, [(z0, 0.0249), (z0 - 0.0050, 0.0249)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for z0 in (-0.5100, -0.7000):
        K.revolve(rc, [(z0, 0.0156), (z0 - 0.0060, 0.0156)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    # scope
    SN.scope(rc, Y_SIGHT, Z_OC, Z_OBJ, r=0.0140, big=0.0245, rings=(0.20, 0.62), y_base=RAIL_TOP - 0.0020, base_w=0.0150)
    # carry handle, folded bipod
    K.tube(rc, [(-0.395, RAIL_TOP), (-0.395, 0.1200), (-0.450, 0.1200), (-0.450, RAIL_TOP)], 0.0100, 0.0070, 'steel')
    rc.box((-0.0150, 0.0000, -0.3150), (0.0150, 0.0130, -0.2950), 'steel', top='steel_top')                      # bipod mount block
    for sgn in (-1, 1):
        rc.cyl((sgn * 0.0240, 0.0060, -0.3050), (sgn * 0.0240, 0.0060, -0.4950), 0.0050, 8, 'steel', cap='brass')
        rc.cyl((sgn * 0.0240, 0.0060, -0.4300), (sgn * 0.0240, 0.0060, -0.4400), 0.0066, 8, 'brass', cap='brass')
    # trigger guard band + trigger
    K.tube(rc, [(0.0200, -0.0100), (0.0170, -0.0350), (-0.0020, -0.0430), (-0.0200, -0.0310), (-0.0230, -0.0100)], 0.0090, 0.0060, 'steel')
    rc.prism([(0.0030, -0.0100), (-0.0030, -0.0100), (-0.0025, -0.0200), (0.0000, -0.0290), (0.0050, -0.0300), (0.0040, -0.0200)], -0.0016, 0.0016, 'brass', side='brass')

    # ---------------- polymer furniture ----------------
    fu = C.Part('furniture')
    K.shell(fu, FRAME, [FRAME_HOLE], 0.0120, region='poly', bevel=0.0045, segs=2, bevel_hole=0.0035, gmap=True)
    K.shell(fu, K.chaikin([(0.4030, 0.0450), (0.4030, -0.0600), (0.3560, -0.0600), (0.3560, 0.0450)], 1), [], 0.0170, region='poly', bevel=0.0070, segs=2, gmap=True)
    K.shell(fu, K.chaikin(GRIP, 1), [], 0.0140, region='poly', bevel=0.0050, segs=2, gmap=True)
    for sgn in (-1, 1):
        x0, x1 = (0.0170 - 0.0005, 0.0170 + 0.0016) if sgn > 0 else (-0.0170 - 0.0016, -0.0170 + 0.0005)
        fu.cyl((x0, -0.0075, 0.3800), (x1, -0.0075, 0.3800), 0.0150, 12, 'brass', cap='bone_stock')               # brass-rimmed bone cross badge
    fu.box((-0.0172, 0.0452, 0.3600), (0.0172, 0.0472, 0.4030), 'brass')                                         # brass heel strap

    # ---------------- box magazine ----------------
    mg = C.Part('magazine')
    mg.prism(S.cham(-0.195, -0.033, -0.1200, -0.0140, 0.006), -0.0200, 0.0200, 'mag', side='steel')
    mg.box((-0.0208, -0.1250, -0.1990), (0.0208, -0.1190, -0.0290), 'brass')
    mg.box((-0.0208, -0.0165, -0.1990), (0.0208, -0.0125, -0.0290), 'brass')

    objs = {}
    for p, ml in ((rc, 0.024), (fu, 0.020), (mg, 0.014)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p is fu else 35))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('sniper_antimat', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_OC),
        'front_sight': (0, Y_SIGHT, Z_OBJ),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'sniper_antimat', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
