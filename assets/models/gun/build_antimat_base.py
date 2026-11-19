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
Y_SIGHT = 0.1400
Z_OC, Z_OBJ = 0.050, -0.500
Z_MUZ = -1.000
PH = -math.pi / 12
MAGW = (0.0, -0.0150, -0.1130)

# skeleton stock frame (outer triangle + cut-out), traced proportions from the M82A1 side photo
FRAME = [(0.362, 0.0450), (0.362, -0.0600), (0.040, 0.0150), (0.040, 0.0450)]
FRAME_HOLE = [(0.340, 0.0330), (0.340, -0.0379), (0.085, 0.0200), (0.085, 0.0330)]
RK = math.radians(20)


def _gp(u, v, z0=0.060, y0=0.0000):
    return (round(z0 + u * math.sin(RK) + v * math.cos(RK), 4), round(y0 - u * math.cos(RK) + v * math.sin(RK), 4))


_FRONT = [(0.000, -0.0150), (0.016, -0.0165), (0.030, -0.0165), (0.040, -0.0125), (0.052, -0.0165), (0.064, -0.0165), (0.074, -0.0125),
          (0.086, -0.0165), (0.098, -0.0165), (0.108, -0.0135), (0.118, -0.0140)]
_BACK = [(0.118, 0.0150), (0.104, 0.0178), (0.084, 0.0168), (0.062, 0.0158), (0.040, 0.0168), (0.020, 0.0200), (0.000, 0.0180)]
GRIP = [_gp(u, v) for u, v in _FRONT + _BACK]


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
    low = K.hexp(-0.0205, 0.0205, -0.0126, 0.0300, 0.0080)
    rc.loft([(0.105, low), (0.038, low)], 'steel', top='steel_top')                                          # lower receiver block the grip hangs from
    fore = K.hexp(-0.0210, 0.0210, 0.0120, 0.0850, 0.0090)
    rc.loft([(-0.300, fore), (-0.505, fore)], 'steel', top='steel_top')
    rc.box((-0.0085, 0.0848, -0.500), (0.0085, RAIL_TOP, 0.040), 'steel', top='steel_top')                      # Picatinny rail
    zz = 0.040
    while zz - 0.0120 > -0.500:
        rc.box((-0.0085, RAIL_TOP - 0.0006, zz - 0.0120), (0.0085, RAIL_TOP + 0.0014, zz), 'steel', top='steel_top')   # rail teeth
        zz -= 0.0400
    for sgn in (-1, 1):
        a_, b_ = (0.0226, 0.0246) if sgn > 0 else (-0.0246, -0.0226)
        rc.prism(S.cham(-0.060, 0.025, 0.0080, 0.0700, 0.006), a_, b_, 'panel', side='steel', top='steel_top')
        rc.prism(S.cham(-0.275, -0.115, 0.0300, 0.0700, 0.005), a_, b_, 'port', side='steel', top='steel_top')
        for zc in (0.0330, -0.0950, -0.2900):
            x0, x1 = (0.0224, 0.0250) if sgn > 0 else (-0.0250, -0.0224)
            rc.box((x0, -0.0136, zc - 0.0030), (x1, 0.0860, zc + 0.0030), 'brass')
    # barrel + M82 chevron brake (arrowhead nose, three angled side ports each side)
    K.revolve(rc, [(-0.480, 0.0140), (-0.700, 0.0128), (-0.930, 0.0118)], BY, segs=10, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    for z0 in (-0.5100, -0.7000):
        K.revolve(rc, [(z0, 0.0156), (z0 - 0.0060, 0.0156)], BY, segs=10, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    bk = K.hexp(-0.0250, 0.0250, BY - 0.0235, BY + 0.0235, 0.0085)
    bn = K.hexp(-0.0170, 0.0170, BY - 0.0195, BY + 0.0195, 0.0085)
    rc.loft([(-0.9250, bk), (-0.9780, bk), (Z_MUZ, bn)], 'steel', top='steel_top')
    rc.cyl((0, BY, Z_MUZ + 0.0004), (0, BY, Z_MUZ - 0.0006), 0.0090, 8, 'muzzle', cap='muzzle')
    rc.box((-0.0262, BY - 0.0245, -0.9270), (0.0262, BY + 0.0245, -0.9330), 'brass')                       # brass collar at the brake rear
    for sgn in (-1, 1):
        xa, xb = (0.0248, 0.0256) if sgn > 0 else (-0.0256, -0.0248)
        for z0 in (-0.9420, -0.9590):
            rc.prism([(z0, BY - 0.0165), (z0 - 0.0048, BY - 0.0165), (z0 - 0.0090, BY), (z0 - 0.0042, BY)], xa, xb, 'muzzle', side='muzzle')
            rc.prism([(z0 - 0.0042, BY), (z0 - 0.0090, BY), (z0 - 0.0048, BY + 0.0165), (z0, BY + 0.0165)], xa, xb, 'muzzle', side='muzzle')
    # scope
    SN.scope(rc, Y_SIGHT, Z_OC, Z_OBJ, r=0.0140, big=0.0340, rings=(0.12, 0.66), y_base=RAIL_TOP - 0.0020, base_w=0.0150)
    # bipod folded under the barrel: clamp on the barrel, two legs with rubber feet, brace plate
    rc.loft([(-0.600, K.hexp(-0.0190, 0.0190, BY - 0.0275, BY + 0.0150, 0.0090)), (-0.632, K.hexp(-0.0190, 0.0190, BY - 0.0275, BY + 0.0150, 0.0090))], 'steel', top='steel_top')
    rc.box((-0.0196, BY - 0.0040, -0.6120), (0.0196, BY + 0.0020, -0.6200), 'brass')
    for sgn in (-1, 1):
        rc.cyl((sgn * 0.0120, BY - 0.0225, -0.6200), (sgn * 0.0120, BY - 0.0225, -0.8950), 0.0050, 8, 'steel', cap='steel')
        rc.cyl((sgn * 0.0120, BY - 0.0225, -0.8950), (sgn * 0.0120, BY - 0.0225, -0.9100), 0.0068, 8, 'muzzle', cap='muzzle')   # rubber foot
        rc.cyl((sgn * 0.0120, BY - 0.0225, -0.7600), (sgn * 0.0120, BY - 0.0225, -0.7700), 0.0064, 8, 'brass', cap='brass')
    rc.loft([(-0.8000, K.hexp(-0.0185, 0.0185, BY - 0.0290, BY - 0.0100, 0.0070)), (-0.8100, K.hexp(-0.0185, 0.0185, BY - 0.0290, BY - 0.0100, 0.0070))], 'steel', top='steel_top')
    # trigger guard band + trigger
    K.tube(rc, [(0.0480, -0.0100), (0.0450, -0.0340), (0.0200, -0.0440), (-0.0040, -0.0420), (-0.0200, -0.0300), (-0.0230, -0.0100)], 0.0090, 0.0060, 'steel')
    rc.prism([(0.0030, -0.0100), (-0.0030, -0.0100), (-0.0025, -0.0200), (0.0000, -0.0290), (0.0050, -0.0300), (0.0040, -0.0200)], -0.0016, 0.0016, 'brass', side='brass')

    # ---------------- polymer furniture ----------------
    fu = C.Part('furniture')
    K.shell(fu, FRAME, [FRAME_HOLE], 0.0120, region='poly', bevel=0.0045, segs=2, bevel_hole=0.0035, gmap=True)
    K.shell(fu, K.chaikin([(0.4030, 0.0450), (0.4030, -0.0600), (0.3560, -0.0600), (0.3560, 0.0450)], 1), [], 0.0170, region='poly', bevel=0.0070, segs=2, gmap=True)
    K.shell(fu, GRIP, [], 0.0140, region='poly', bevel=0.0045, segs=2, gmap=True)
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
