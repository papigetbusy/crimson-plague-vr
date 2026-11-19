"""Crimson Plague VR - sniper_bolt_base: the Bolt Rifle.

Original low-poly PS2 / Snake Eater style bolt-action sniper (Kar98k / Remington 700 proportions): full-length
walnut stock whose side profile is traced from the Kar98k photo (/workspace/gun_brief/refs/sniper_bolt), round
receiver with a swept bolt handle + brass knob, tapered barrel with a steel nose cap, gothic scope on tall rings,
trigger guard band with a brass floorplate. Dressed Gothic in the approved batch style: blued engraved steel on the
locked 1911 metal material (metallic 1 / roughness 0.30), satin walnut + bone on one non-metal material, brass
bands, brass-rimmed bone cross badge inset in the stock. One 1024 px smooth albedo (painted on a 256 grid, EPX +
bicubic upscaled; glTF sampler LINEAR).

Build (repo root):
  blender -b --python assets/models/gun/build_bolt_base.py -- --out-dir assets/models/gun
Export / previews: see /workspace/basegun-scripts/run_gun.sh (export_lowpoly.py --type gun --max-tris 3000 --max-tex 1024).

Meshes: receiver (action, barrel, bolt + handle, scope + rings, guard, sights), furniture (stock, butt plate, badge),
magazine (brass floorplate). Empties: muzzle, mag_well, rear_sight (scope ocular centre), front_sight (scope objective
centre); both share X=0, Y and are parallel to the bore (scope axis 40.5 mm above it).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_sniper_common as SN
S, K, C, M, G = SN.S, SN.K, SN.C, SN.M, SN.G

NAME = 'sniper_bolt_base'
BY = 0.050
RR = 0.0165                        # receiver radius
Y_SIGHT = 0.0905                   # scope axis
Z_OC, Z_OBJ = 0.070, -0.235
Z_MUZ = -0.580
PH = -math.pi / 12
MAGW = (0.0, -0.0090, -0.0375)

# stock side profile traced from the Kar98k photo (wood mask, scaled to 1.1 m rifle), (z, y)
STOCK = [(0.400, 0.0085), (0.377, 0.0120), (0.330, 0.0154), (0.284, 0.0188), (0.236, 0.0222), (0.213, 0.0245), (0.190, 0.0215),
         (0.166, 0.0170), (0.142, 0.0188), (0.118, 0.0268), (0.096, 0.0348), (0.072, 0.0400), (-0.100, 0.0400), (-0.130, 0.0460),
         (-0.470, 0.0460), (-0.478, 0.0400), (-0.480, 0.0150), (-0.470, 0.0085), (-0.400, 0.0028), (-0.300, 0.0000), (-0.200, -0.0017),
         (-0.100, -0.0030), (0.000, -0.0074), (0.072, -0.0097), (0.096, -0.0120), (0.118, -0.0200), (0.142, -0.0371), (0.166, -0.0450),
         (0.189, -0.0473), (0.213, -0.0519), (0.236, -0.0599), (0.2597, -0.0679), (0.2837, -0.0770), (0.3065, -0.0838), (0.330, -0.0930),
         (0.353, -0.0998), (0.385, -0.1080)]


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('tube', 128, 48), ('panel', 112, 36), ('port', 56, 28), ('wood', 128, 48), ('bone_stock', 40, 40),
        ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=14, grime=0.84, arches=False)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.wrap('tube', 8, 6, lambda j: 'eng' if j in (0, 4) else 'hi' if j == 2 else 'dark' if j == 6 else 'plain', seed=17, lam=16)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    S.paint_wood(A, 'wood'); S.paint_port(A, 'port')
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = S.make_mats(NAME, tex)

    # ---------------- receiver, barrel, bolt, scope ----------------
    rc = C.Part('receiver')
    K.revolve(rc, [(-0.115, RR), (0.040, RR)], BY, segs=14, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    for z0 in (-0.1150, 0.0380):
        K.revolve(rc, [(z0, RR + 0.0010), (z0 + 0.0040, RR + 0.0010)], BY, segs=14, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    rc.prism(S.cham(-0.098, -0.040, BY + 0.0010, BY + 0.0125, 0.003), RR - 0.0015, RR + 0.0003, 'port', side='steel', top='steel_top')   # ejection port
    rc.box((-0.0085, BY + 0.0050, 0.0400), (0.0085, BY + 0.0160, 0.0850), 'steel', top='steel_top')                              # rear bridge / tang
    K.revolve(rc, [(0.0400, 0.0095), (0.1000, 0.0095)], BY, segs=10, region='barrel', cap_f='steel', cap_b='steel')                # bolt body
    K.revolve(rc, [(0.0980, 0.0108), (0.1040, 0.0108)], BY, segs=10, region='brass', cap_f='brass', cap_b='brass')                 # bolt shroud ring
    S.horn(rc, [(0.009, 0.0520, 0.0500), (0.030, 0.0500, 0.0520), (0.042, 0.0440, 0.0600), (0.047, 0.0360, 0.0720), (0.0485, 0.0335, 0.0755)],
           [0.0050, 0.0045, 0.0045, 0.0050, 0.0050], segs=8, regions=['steel'] * 4, cap_region='steel')
    S.horn(rc, [(0.0488, 0.0330, 0.0762), (0.0510, 0.0310, 0.0792), (0.0540, 0.0285, 0.0840)], [0.0092, 0.0098, 0.0080], segs=10,
           regions=['brass', 'brass'], cap_region='brass')                                                                         # brass bolt knob
    # barrel + crown + bands + nose cap
    K.revolve(rc, [(-0.115, 0.0125), (-0.200, 0.0105), (-0.400, 0.0086), (-0.560, 0.0076)], BY, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    K.revolve(rc, [(-0.560, 0.0076), (-0.568, 0.0084), (-0.576, 0.0072), (Z_MUZ, 0.0066)], BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for zz in (-0.2400, -0.3600):
        K.revolve(rc, [(zz, 0.0112), (zz - 0.0050, 0.0112)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    rc.loft([(-0.4680, K.hexp(-0.0170, 0.0170, -0.0015, 0.0530, 0.0080)), (-0.4800, K.hexp(-0.0170, 0.0170, -0.0015, 0.0530, 0.0080))], 'steel', top='steel')
    rc.loft([(-0.4560, K.hexp(-0.0166, 0.0166, -0.0010, 0.0525, 0.0070)), (-0.4640, K.hexp(-0.0166, 0.0166, -0.0010, 0.0525, 0.0070))], 'brass')
    rc.loft([(-0.3000, K.hexp(-0.0162, 0.0162, -0.0010, 0.0515, 0.0070)), (-0.3070, K.hexp(-0.0162, 0.0162, -0.0010, 0.0515, 0.0070))], 'brass')
    rc.box((-0.0034, BY + 0.0070, -0.5750), (0.0034, BY + 0.0112, -0.5600), 'steel', top='steel_top')                              # front sight blade
    rc.box((-0.0016, BY + 0.0110, -0.5700), (0.0016, BY + 0.0130, -0.5650), 'brass')
    # scope on tall rings
    SN.scope(rc, Y_SIGHT, Z_OC, Z_OBJ, y_base=BY + RR - 0.0030)
    # trigger guard band + trigger
    K.tube(rc, [(0.0950, -0.0085), (0.0800, -0.0290), (0.0400, -0.0350), (0.0100, -0.0290), (0.0000, -0.0080)], 0.0090, 0.0060, 'steel')
    rc.prism([(0.0400, -0.0090), (0.0340, -0.0090), (0.0345, -0.0180), (0.0375, -0.0260), (0.0425, -0.0270), (0.0410, -0.0180)], -0.0016, 0.0016, 'brass', side='brass')

    # ---------------- walnut stock ----------------
    fu = C.Part('furniture')
    K.shell(fu, STOCK, [], 0.0155, region='wood', bevel=0.0048, segs=2, gmap=True)
    fu.prism([(0.4000, 0.0085), (0.4065, 0.0085), (0.3925, -0.1080), (0.3850, -0.1080)], -0.0162, 0.0162, 'brass', side='brass')       # butt plate
    for sgn in (-1, 1):
        x0, x1 = (0.0155 - 0.0005, 0.0155 + 0.0016) if sgn > 0 else (-0.0155 - 0.0016, -0.0155 + 0.0005)
        fu.cyl((x0, -0.0330, 0.3100), (x1, -0.0330, 0.3100), 0.0130, 12, 'brass', cap='bone_stock')               # brass-rimmed bone cross badge
        fu.cyl((sgn * 0.0152, -0.0090, 0.0750), (sgn * 0.0172, -0.0090, 0.0750), 0.0030, 8, 'brass', cap='brass')   # guard screw
    fu.box((-0.0160, -0.0510, 0.1750), (0.0160, -0.0470, 0.2050), 'brass')                                       # grip cap strap

    # ---------------- floorplate (= magazine) ----------------
    mg = C.Part('magazine')
    mg.box((-0.0125, -0.0130, -0.0750), (0.0125, -0.0060, 0.0000), 'brass')
    mg.cyl((-0.0126, -0.0095, -0.0100), (0.0126, -0.0095, -0.0100), 0.0022, 8, 'steel', cap='steel')

    objs = {}
    for p, ml in ((rc, 0.024), (fu, 0.020), (mg, 0.014)):
        C.BEVEL_MINLEN = ml
        objs[p.name] = p.to_object(mats, smooth=(50 if p is fu else 35))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('sniper_bolt', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_OC),
        'front_sight': (0, Y_SIGHT, Z_OBJ),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'sniper_bolt', relief=0.16)


if __name__ == '__main__':
    K.run(finish, render, NAME)
