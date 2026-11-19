"""Crimson Plague VR - smg_bullpup_base: the Bullpup SMG (v4, traced P90 side profile, real 3D volume).

Original low-poly PS2 / Snake Eater style compact bullpup submachine gun, built from
the FN P90 side silhouette (reference photos in /workspace/bullpup_refs/): a short,
deep, rounded polymer body with the hand on a grip bar near the FRONT, a big
teardrop thumbhole behind the grip, a small trigger hole ahead of it, a flat
butt, a thin top-loaded magazine sunk between two shoulder rails, a short
sight housing at the nose and a stubby barrel with a small slotted hider that
barely clears the body (about 42 cm overall, v2 was 52 cm). Gothic touches are
fine and subtle: thin engraved steel inlays on the butt and sight housing, thin
brass trim and rivets, a small bone cross inlay, brass-ringed visible rounds in the
magazine. Steel and brass share the locked 1911 metal material (metallic 1 /
roughness 0.30); polymer + bone share one non-metal material; one 1024 px smooth albedo (painted on a 256 grid, EPX+bicubic upscaled, linear filtered).

Build (repo root):
  blender -b --python assets/models/gun/build_bullpup_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/smg_bullpup_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/smg_bullpup_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_bullpup_base.py -- --render-glb assets/models/gun/smg_bullpup_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: body (polymer body with thumbhole + trigger hole, steel deck and shoulder rails, sight housing, trigger,
barrel + hider, sight posts), cocking_handle (small brass handle, left, slides back), magazine (top-loaded, under mag_well).
Empties: muzzle, mag_well, rear_sight, front_sight. rear/front share X=0 and Y, so the sight line is exactly parallel
to the bore (dir 0,0,-1); the bore is 49 mm below it (v1 73.5 mm).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_gothic_common as K
C, M, G = K.C, K.M, K.G

def paint_mag_h(A, r):
    """Top magazine: smoked dark body, thin transverse ribs, a row of small dull brass round windows (no tan blocks)."""
    x0, y0, x1, y1 = A.reg[r]
    A.steel(r, ('steel_black', 'steel_dark', 'steel_dark', 'steel_mid'), 61, grime=0.78, edge=False)
    cy = (y0 + y1) // 2
    for x in range(x0 + 3, x1 - 3):
        if (x - x0) % 8 == 0:
            for y in range(y0 + 3, y1 - 3):
                A.put(x, y, 'steel_mid')
    for i in range(0, (x1 - x0 - 8) // 8):
        cx = x0 + 8 + i * 8 + 4
        for y in range(cy - 4, cy + 5):
            for x in range(cx - 4, cx + 5):
                d = math.hypot(x - cx, y - cy)
                if d <= 1.9:
                    A.put(x, y, 'brass_dark')
                elif d <= 3.0:
                    A.put(x, y, 'recess')


NAME = 'smg_bullpup_base'
BY = 0.047                       # bore height
Z_MUZ = -0.168
Y_SIGHT = 0.0960
Z_REAR_SIGHT, Z_FRONT_SIGHT = 0.0500, -0.1120
PH = -math.pi / 12
TOP = 0.0795                     # shell top (rails, butt, nose)
DECK = 0.058                     # mag channel floor
MAG_Y0, MAG_Y1 = 0.058, 0.078
MAGW = (0.0, MAG_Y0, 0.040)
HW = 0.0175                      # shell half width
Z_BUTT, Z_NOSE = 0.285, -0.123
CH_Z0, CH_Z1 = -0.085, 0.148     # magazine channel (rails on both sides)

# Side profile traced from the FN P90 photo (/workspace/bullpup_refs/fn_p90_right_side.jpg), scaled to 0.408 m shell length,
# bore axis at y = 0.047; (z, y), top edge rear -> front, then front face, nose foot, grip, bottom, butt.
OUTER = [(0.2835, 0.0770), (0.2815, 0.0369), (0.2823, 0.0017), (0.2842, -0.0207), (0.2837, -0.0263), (0.1711, -0.0263),
         (0.1690, -0.0221), (0.1594, -0.0221), (0.1082, -0.0381), (0.1045, -0.0439), (0.0847, -0.0439), (0.0618, -0.0429),
         (0.0437, -0.0381), (0.0261, -0.0285), (0.0095, -0.0130), (0.0042, -0.0109), (-0.0086, -0.0109), (-0.0142, -0.0138),
         (-0.0158, -0.0197), (-0.0110, -0.0373), (-0.0110, -0.0415), (-0.0129, -0.0434), (-0.0427, -0.0434), (-0.0502, -0.0418),
         (-0.0641, -0.0349), (-0.0745, -0.0239), (-0.0803, -0.0111), (-0.0819, 0.0054), (-0.0843, 0.0089), (-0.0881, 0.0110),
         (-0.1030, 0.0110), (-0.1075, 0.0081), (-0.1091, 0.0038), (-0.1091, -0.0069), (-0.1121, -0.0087), (-0.1201, -0.0087),
         (-0.1230, 0.0097), (-0.1230, 0.0560), (-0.1190, 0.0640), (-0.1000, 0.0725), (-0.0850, TOP),
         (CH_Z0, DECK), (CH_Z1, DECK), (CH_Z1, TOP), (0.2760, TOP)]
THUMB = [(0.0823, -0.0117), (0.0543, -0.0002), (0.0466, 0.0054), (0.0439, 0.0107), (0.0434, 0.0161), (0.0461, 0.0230),
         (0.0501, 0.0270), (0.0554, 0.0291), (0.0863, 0.0291), (0.0954, 0.0259), (0.1015, 0.0203), (0.1047, 0.0123),
         (0.1047, 0.0049), (0.1026, -0.0010), (0.0954, -0.0087), (0.0890, -0.0114)]
TRIGHOLE = [(-0.0441, -0.0063), (-0.0497, -0.0039), (-0.0542, 0.0022), (-0.0547, 0.0102), (-0.0526, 0.0150), (-0.0454, 0.0201),
            (-0.0395, 0.0265), (-0.0289, 0.0275), (-0.0251, 0.0259), (-0.0217, 0.0230), (-0.0190, 0.0177), (-0.0195, 0.0027),
            (-0.0283, 0.0019), (-0.0297, -0.0010), (-0.0363, -0.0061)]


def cham(z0, z1, y0, y1, c):
    return [(z0 + c, y0), (z1 - c, y0), (z1, y0 + c), (z1, y1 - c), (z1 - c, y1), (z0 + c, y1), (z0, y1 - c), (z0, y0 + c)]


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('mag', 96, 32), ('bone_inlay', 32, 32), ('panel', 112, 36), ('poly', 128, 40),
        ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=14, grime=0.84, arches=False)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    paint_mag_h(A, 'mag'); A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_inlay', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    A.poly('poly', seed=43, fine=True)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = C.make_materials(NAME, tex, furn='polymer')
    mats[1].name = NAME + '_polymer'
    b = mats[1].node_tree.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.42        # satin polymer: visible specular roll-off over the rounded shell
    b.inputs['Specular IOR Level'].default_value = 0.14

    bd = C.Part('body')
    # ---- polymer shell: traced P90 profile with the thumbhole and the trigger-hand hole, rounded sides ----
    K.shell(bd, OUTER, [THUMB, TRIGHOLE], HW, region='poly', bevel=0.0055, segs=2, bevel_hole=0.0032)
    # ---- steel rails either side of the mag channel + engraved steel sight housing ----
    for sgn in (-1, 1):
        lo, hi = (0.0108, HW + 0.0004) if sgn > 0 else (-HW - 0.0004, -0.0108)
        bd.prism(cham(CH_Z0, CH_Z1, 0.0475, TOP - 0.0016, 0.0030), lo, hi, 'poly', side='poly')
        bd.prism(cham(CH_Z0, CH_Z1, TOP - 0.0016, TOP, 0.0008), lo, hi, 'steel', side='steel', top='steel_top')   # steel rail cap
        bd.box((sgn * 0.0128 - 0.0006, TOP - 0.0001, CH_Z0 + 0.004), (sgn * 0.0128 + 0.0006, TOP + 0.0004, CH_Z1 - 0.004), 'brass')
    # steel deck between the rails (the channel floor; the mag sits on it)
    bd.box((-0.0112, DECK - 0.002, CH_Z0 + 0.002), (0.0112, DECK + 0.0004, CH_Z1 - 0.002), 'steel', top='steel_top')
    hous = [(-0.050, 0.0775), (-0.056, 0.088), (-0.066, 0.092), (-0.100, 0.092), (-0.112, 0.086), (-0.119, 0.0745),
            (-0.1195, 0.0580), (CH_Z0, 0.0580), (CH_Z0, 0.0775)]
    bd.prism(hous, -0.0140, 0.0140, 'panel', side='steel', top='steel_top')
    # ---- inlaid engraved plaque + bone cross badge (bezelled, sunk into the side so they are part of the shell) ----
    for sgn in (-1, 1):
        def xs(a, b):
            return (sgn * a, sgn * b) if sgn > 0 else (sgn * b, sgn * a)
        # steel plaque with brass bezel
        bz = K.chaikin(cham(0.1180, 0.1990, 0.0010, 0.0360, 0.0050), 1)
        x0, x1 = xs(HW - 0.0006, HW + 0.0006)
        bd.prism(bz, x0, x1, 'brass', side='brass')
        pl = K.chaikin(cham(0.1210, 0.1960, 0.0040, 0.0330, 0.0045), 1)
        x0, x1 = xs(HW - 0.0006, HW + 0.0012)
        bd.prism(pl, x0, x1, 'panel', side='steel', top='steel_top')
        # bone cross badge: brass ring + bone disc
        cz, cy, R = 0.2330, 0.0170, 0.0135
        x0, x1 = xs(HW - 0.0006, HW + 0.0006)
        bd.cyl((x0, cy, cz), (x1, cy, cz), R + 0.0016, 14, 'brass', cap='brass')
        x0, x1 = xs(HW - 0.0006, HW + 0.0014)
        bd.cyl((x0, cy, cz), (x1, cy, cz), R, 14, 'bone_inlay', cap='bone_inlay')
        for (zz, yy) in ((0.1145, 0.0525), (0.2740, 0.0525), (0.1145, -0.0120)):
            bd.cyl((sgn * HW, yy, zz), (sgn * (HW + 0.0014), yy, zz), 0.0018, 8, 'brass', cap='brass')
        # brass pinstripe along the upper rear block
        x0, x1 = xs(HW - 0.0004, HW + 0.0005)
        bd.box((x0, 0.0640, 0.1520), (x1, 0.0654, 0.2740), 'brass')
    # thin brass butt pad
    bd.box((-0.0128, -0.0235, Z_BUTT - 0.0006), (0.0128, 0.0715, Z_BUTT + 0.0020), 'brass')
    # ---- trigger: steel blade hung from a brass pivot pin, seated inside the trigger-hand hole ----
    trig = [(-0.0200, 0.0300), (-0.0262, 0.0300), (-0.0270, 0.0200), (-0.0298, 0.0100), (-0.0322, 0.0050), (-0.0305, 0.0034),
            (-0.0275, 0.0060), (-0.0243, 0.0120), (-0.0225, 0.0200)]
    bd.prism(trig, -0.0013, 0.0013, 'steel', side='steel', top='steel_top')
    bd.cyl((-0.0150, 0.0238, -0.0235), (0.0150, 0.0238, -0.0235), 0.0024, 8, 'brass', cap='brass')
    bd.cyl((-HW, 0.0238, -0.0235), (-HW - 0.0010, 0.0238, -0.0235), 0.0030, 8, 'brass', cap='brass')
    bd.cyl((HW, 0.0238, -0.0235), (HW + 0.0010, 0.0238, -0.0235), 0.0030, 8, 'brass', cap='brass')
    # ---- sights: front ears + post, rear bridge with two thin posts (same sight line as before) ----
    for sgn in (-1, 1):
        lo, hi = (0.0030, 0.0046) if sgn > 0 else (-0.0046, -0.0030)
        bd.box((lo, 0.0915, -0.1170), (hi, Y_SIGHT - 0.0006, -0.1070), 'steel', top='steel_top')
        x0, x1 = (0.0112, HW) if sgn > 0 else (-HW, -0.0112)
        bd.box((x0, TOP - 0.0005, 0.0440), (x1, 0.0880, 0.0560), 'steel', top='steel_top')
        lo, hi = (0.0035, 0.0058) if sgn > 0 else (-0.0058, -0.0035)
        bd.box((lo, 0.0880, 0.0440), (hi, Y_SIGHT, 0.0560), 'steel', top='steel_top')
        bd.box((lo, Y_SIGHT - 0.0008, 0.0440), (hi, Y_SIGHT, 0.0560), 'brass')
    bd.box((-HW, 0.0840, 0.0440), (HW, 0.0880, 0.0560), 'steel', top='steel_top')
    bd.box((-0.0016, 0.0915, -0.1150), (0.0016, Y_SIGHT - 0.0014, -0.1090), 'steel')
    bd.box((-0.0012, Y_SIGHT - 0.0014, -0.1142), (0.0012, Y_SIGHT, -0.1098), 'brass')
    # ---- barrel + small slotted hider, thin brass rings (barely clears the nose) ----
    K.revolve(bd, [(Z_NOSE + 0.004, 0.0085), (-0.1340, 0.0085), (-0.1350, 0.0070), (-0.1560, 0.0070), (Z_MUZ, 0.0064)],
              BY, segs=10, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, z1, r in ((-0.1300, -0.1335, 0.0098), (-0.1580, -0.1605, 0.0082)):
        K.revolve(bd, [(z0, r), (z1, r)], BY, segs=10, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for zz in (-0.1410, -0.1450, -0.1490):
        bd.box((-0.0022, BY + 0.0062, zz - 0.0013), (0.0022, BY + 0.0074, zz + 0.0013), 'steel')

    # ---------------- cocking handle (small brass, left side, slides back) ----------------
    ch = C.Part('cocking_handle')
    ch.box((-0.0182, 0.0645, 0.1040), (-0.0170, 0.0705, 0.1210), 'brass')
    ch.cyl((-0.0182, 0.0675, 0.1125), (-0.0235, 0.0675, 0.1125), 0.0040, 8, 'brass', cap='brass')

    # ---------------- magazine (top-loaded, sunk between the rails, flush with the rail tops) ----------------
    mg = C.Part('magazine')
    mg.prism(cham(-0.080, 0.142, MAG_Y0, MAG_Y1, 0.003), -0.0098, 0.0098, 'mag', side='steel')
    mg.box((-0.0106, MAG_Y0 + 0.0008, 0.1385), (0.0106, MAG_Y1 - 0.0008, 0.1435), 'brass')
    mg.box((-0.0106, MAG_Y0 + 0.0008, -0.0825), (0.0106, MAG_Y1 - 0.0008, -0.0780), 'brass')

    objs = {p.name: p.to_object(mats, smooth=(50 if p is bd else 35)) for p in (bd, ch, mg)}
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('smg_bullpup', objs, {
        'muzzle': (0, BY, Z_MUZ),
        'mag_well': MAGW,
        'rear_sight': (0, Y_SIGHT, Z_REAR_SIGHT),
        'front_sight': (0, Y_SIGHT, Z_FRONT_SIGHT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'smg_bullpup', relief=0.18)


if __name__ == '__main__':
    K.run(finish, render, NAME)
