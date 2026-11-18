"""Crimson Plague VR - smg_bullpup_base: the Bullpup SMG (v3, compact P90 silhouette).

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
    """Flat horizontal magazine: dark steel, thin transverse ribs, row of brass-ringed rounds."""
    x0, y0, x1, y1 = A.reg[r]
    A.steel(r, ('steel_black', 'steel_dark', 'steel_mid', 'steel_light'), 61, grime=0.78, edge=False)
    cy = (y0 + y1) // 2
    for x in range(x0 + 3, x1 - 3):
        if (x - x0) % 8 == 0:
            for y in range(y0 + 3, y1 - 3):
                A.put(x, y, 'steel_light')
    for i in range(0, (x1 - x0 - 8) // 8):
        cx = x0 + 8 + i * 8 + 4
        for y in range(cy - 5, cy + 6):
            for x in range(cx - 5, cx + 6):
                d = math.hypot(x - cx, y - cy)
                if d <= 3.2:
                    A.put(x, y, 'brass_light' if d < 1.6 else 'brass')
                elif d <= 4.4:
                    A.put(x, y, 'recess')


NAME = 'smg_bullpup_base'
BY = 0.047                       # bore height
Z_MUZ = -0.168
Y_SIGHT = 0.0960
Z_REAR_SIGHT, Z_FRONT_SIGHT = 0.0500, -0.1120
PH = -math.pi / 12
SLAB_TOP, DECK_TOP = 0.076, 0.058
MAG_Y0, MAG_Y1 = 0.058, 0.078
MAGW = (0.0, MAG_Y0, 0.040)
HW = 0.0170                      # body half width
Z_BUTT, Z_NOSE = 0.285, -0.123


def cham(z0, z1, y0, y1, c):
    return [(z0 + c, y0), (z1 - c, y0), (z1, y0 + c), (z1, y1 - c), (z1 - c, y1), (z0 + c, y1), (z0, y1 - c), (z0, y0 + c)]


# lower body outline (rear block + wall under the thumbhole + grip bar + front arm): thumbhole and trigger hole are the
# notches between this outline and the top slab. (z, y), rear -> front along the hole edges, front -> rear along the bottom.
LOWER = [(0.285, 0.034), (0.104, 0.034), (0.104, 0.002), (0.092, -0.011), (0.060, -0.017), (0.032, -0.013), (0.021, -0.005),
         (0.021, 0.034), (-0.019, 0.034), (-0.019, 0.001), (-0.030, 0.0), (-0.050, 0.0), (-0.056, 0.008), (-0.056, 0.034),
         (-0.123, 0.034), (-0.123, -0.010), (-0.115, -0.016), (-0.100, -0.015), (-0.085, -0.030), (-0.060, -0.044), (-0.035, -0.054),
         (-0.020, -0.061), (0.000, -0.065), (0.020, -0.060), (0.060, -0.050), (0.110, -0.040), (0.150, -0.029), (0.285, -0.029)]


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('mag', 96, 32), ('bone_inlay', 32, 32), ('panel', 112, 36), ('poly', 128, 40),
        ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16), ('poly_end', 16, 16),
    ])
    K.FURN.add('poly_end')
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=14, grime=0.84, arches=False)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    paint_mag_h(A, 'mag'); A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_inlay', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    A.poly('poly', seed=43, fine=True); A.poly('poly_end', seed=45, dark=True, fine=True)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = C.make_materials(NAME, tex, furn='polymer')
    mats[1].name = NAME + '_polymer'
    b = mats[1].node_tree.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.68
    b.inputs['Specular IOR Level'].default_value = 0.14

    bd = C.Part('body')
    # ---- polymer: lower body (thumbhole + grip bar + trigger hole), shoulder rails, deck ----
    bd.prism(K.chaikin(LOWER, 1), -HW, HW, 'poly', side='poly_end')
    slab = [(Z_BUTT, SLAB_TOP - 0.008), (Z_BUTT - 0.008, SLAB_TOP), (Z_NOSE + 0.008, SLAB_TOP), (Z_NOSE, SLAB_TOP - 0.008),
            (Z_NOSE, 0.034), (Z_BUTT, 0.034)]
    for sgn in (-1, 1):
        lo, hi = (0.0105, HW) if sgn > 0 else (-HW, -0.0105)
        bd.prism(slab, lo, hi, 'poly', side='poly_end')
    bd.prism([(Z_BUTT, DECK_TOP), (Z_NOSE, DECK_TOP), (Z_NOSE, 0.034), (Z_BUTT, 0.034)], -0.0108, 0.0108, 'steel', side='steel', top='steel_top')
    # ---- thin engraved steel inlays (butt sides) + small bone cross inlay + brass rivets ----
    for sgn in (-1, 1):
        a, b_ = (HW, HW + 0.0010) if sgn > 0 else (-HW - 0.0010, -HW)
        bd.prism(cham(0.118, 0.200, -0.020, 0.024, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        a, b_ = (HW, HW + 0.0012) if sgn > 0 else (-HW - 0.0012, -HW)
        bd.prism(K.chaikin(cham(0.222, 0.258, -0.014, 0.022, 0.006), 1), a, b_, 'bone_inlay', side='bone_end')
        for (zz, yy) in ((0.268, 0.058), (0.268, -0.018), (0.112, 0.060)):
            bd.cyl((sgn * HW, yy, zz), (sgn * (HW + 0.0016), yy, zz), 0.0020, 8, 'brass', cap='brass')
        # brass selector stud at the foot of the trigger hole
        bd.cyl((sgn * HW, 0.0045, -0.0215), (sgn * (HW + 0.0030), 0.0045, -0.0215), 0.0032, 8, 'brass', cap='brass')
    # thin brass pinstripes along the upper slab sides (gothic trim, breaks up the flat polymer)
    for sgn in (-1, 1):
        x0, x1 = (HW, HW + 0.0006) if sgn > 0 else (-HW - 0.0006, -HW)
        bd.box((x0, 0.0515, Z_NOSE + 0.012), (x1, 0.0530, 0.120), 'brass')
        bd.box((x0, 0.0515, 0.134), (x1, 0.0530, Z_BUTT - 0.012), 'brass')
    # thin brass trim: butt edge strip and grip-bar foot pad
    bd.box((-0.0150, -0.0275, Z_BUTT - 0.0004), (0.0150, SLAB_TOP - 0.010, Z_BUTT + 0.0016), 'brass')
    bd.prism([(-0.017, -0.0625), (0.017, -0.0610), (0.017, -0.0660), (-0.017, -0.0670)], -0.0125, 0.0125, 'brass', side='brass')
    # ---- trigger (thin brass blade in the trigger hole) ----
    bd.prism([(-0.0360, 0.0340), (-0.0310, 0.0340), (-0.0322, 0.0190), (-0.0345, 0.0100), (-0.0385, 0.0075), (-0.0410, 0.0085),
              (-0.0392, 0.0140), (-0.0372, 0.0220)], -0.0012, 0.0012, 'brass', side='brass')
    # ---- sight housing at the nose (steel, engraved sides) + front sight + hinged rear sight bridge ----
    hous = [(-0.050, SLAB_TOP - 0.002), (-0.056, 0.086), (-0.064, 0.090), (-0.108, 0.090), (-0.119, 0.084), (-0.119, SLAB_TOP - 0.002)]
    bd.prism(hous, -0.0140, 0.0140, 'panel', side='steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0030, 0.0046) if sgn > 0 else (-0.0046, -0.0030)
        bd.box((lo, 0.0895, -0.1170), (hi, Y_SIGHT - 0.0006, -0.1070), 'steel', top='steel_top')          # front ears
        # rear sight: uprights on the shoulder rails, cross bridge, two thin brass-tipped posts
        x0, x1 = (0.0112, HW) if sgn > 0 else (-HW, -0.0112)
        bd.box((x0, SLAB_TOP - 0.0005, 0.0440), (x1, 0.0880, 0.0560), 'steel', top='steel_top')
        lo, hi = (0.0035, 0.0058) if sgn > 0 else (-0.0058, -0.0035)
        bd.box((lo, 0.0880, 0.0440), (hi, Y_SIGHT, 0.0560), 'steel', top='steel_top')
        bd.box((lo, Y_SIGHT - 0.0008, 0.0440), (hi, Y_SIGHT, 0.0560), 'brass')
    bd.box((-HW, 0.0840, 0.0440), (HW, 0.0880, 0.0560), 'steel', top='steel_top')
    bd.box((-0.0016, 0.0895, -0.1150), (0.0016, Y_SIGHT - 0.0014, -0.1090), 'steel')
    bd.box((-0.0012, Y_SIGHT - 0.0014, -0.1142), (0.0012, Y_SIGHT, -0.1098), 'brass')
    # ---- barrel + small slotted hider, thin brass rings (barely clears the nose) ----
    K.revolve(bd, [(Z_NOSE + 0.004, 0.0085), (-0.1340, 0.0085), (-0.1350, 0.0070), (-0.1560, 0.0070), (Z_MUZ, 0.0064)],
              BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, z1, r in ((-0.1300, -0.1335, 0.0098), (-0.1580, -0.1605, 0.0082)):
        K.revolve(bd, [(z0, r), (z1, r)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for zz in (-0.1410, -0.1450, -0.1490):
        bd.box((-0.0022, BY + 0.0062, zz - 0.0013), (0.0022, BY + 0.0074, zz + 0.0013), 'steel')

    # ---------------- cocking handle (small brass, left side, slides back) ----------------
    ch = C.Part('cocking_handle')
    ch.box((-0.0180, 0.0640, 0.1040), (-0.0155, 0.0700, 0.1210), 'brass')
    ch.cyl((-0.0180, 0.0670, 0.1125), (-0.0235, 0.0670, 0.1125), 0.0040, 8, 'brass', cap='brass')

    # ---------------- magazine (top-loaded, visible rounds, sunk between the rails) ----------------
    mg = C.Part('magazine')
    mg.prism(cham(-0.056, 0.142, MAG_Y0, MAG_Y1, 0.003), -0.0098, 0.0098, 'mag', side='steel')
    mg.box((-0.0106, MAG_Y0 + 0.0008, 0.1385), (0.0106, MAG_Y1 - 0.0008, 0.1435), 'brass')
    mg.box((-0.0106, MAG_Y0 + 0.0008, -0.0585), (0.0106, MAG_Y1 - 0.0008, -0.0540), 'brass')

    objs = {p.name: p.to_object(mats) for p in (bd, ch, mg)}
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
