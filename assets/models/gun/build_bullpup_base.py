"""Crimson Plague VR - smg_bullpup_base: the Bullpup SMG.

Original low-poly PS2 / Snake Eater style bullpup submachine gun (FN P90
proportions: compact body with the mechanism behind the grip, a long flat
magazine lying along the top, forward finger-grip block, slotted flash hider),
dressed Gothic in the same style as the batch 1 pistols: blued steel upper
plates engraved with scrollwork and lancet arches, stippled black polymer
shell, brass straps, selector, cocking handle and hider rings, carved bone
cross plaques on the butt, brass-ringed visible rounds in the magazine.
Steel and brass share the locked 1911 metal material (metallic 1 / roughness
0.30); polymer + bone share one non-metal material; one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_bullpup_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/smg_bullpup_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/smg_bullpup_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_bullpup_base.py -- --render-glb assets/models/gun/smg_bullpup_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: body (core, plates, shells, grip, guard, barrel + hider, rails, sights),
cocking_handle (brass, slides back), magazine (top-loaded, under mag_well).
Empties: muzzle, mag_well, rear_sight, front_sight. rear/front share X=0 and Y,
so the sight line is exactly parallel to the bore (dir 0,0,-1); bore is 73.5 mm below it.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_gothic_common as K
C, M, G = K.C, K.M, K.G

NAME = 'smg_bullpup_base'
TH = math.radians(14)
BY = 0.050                       # bore height
Z_MUZ = -0.292
Y_SIGHT = 0.1235
Z_REAR_SIGHT, Z_FRONT_SIGHT = 0.0560, -0.2105
PH = -math.pi / 12
MAGW = (0.0, 0.0785, -0.075)      # mag_well (x, y, z): centre of the magazine underside
GRIP_TOP, GRIP_BOT = 0.032, -0.075


def cham(z0, z1, y0, y1, c):
    return [(z0 + c, y0), (z1 - c, y0), (z1, y0 + c), (z1, y1 - c), (z1 - c, y1), (z0 + c, y1), (z0, y1 - c), (z0, y0 + c)]


def paint_mag_h(A, r):
    """Flat horizontal magazine: dark steel, transverse ribs, row of brass-ringed rounds."""
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


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('mag', 96, 32), ('bone_inlay', 48, 48), ('panel', 112, 36), ('poly', 48, 48),
        ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16), ('poly_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=22, grime=0.82)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    paint_mag_h(A, 'mag'); A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_inlay', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    A.poly('poly', seed=43, checker=True); A.poly('poly_end', seed=45, dark=True)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = C.make_materials(NAME, tex, furn='polymer')
    mats[1].name = NAME + '_polymer'
    b = mats[1].node_tree.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Specular IOR Level'].default_value = 0.22
    K.FURN.add('poly_end')

    # ---------------- body ----------------
    bd = C.Part('body')
    core = [(-0.228, 0.034), (-0.228, 0.068), (-0.218, 0.078), (0.150, 0.078), (0.195, 0.074), (0.222, 0.060), (0.226, 0.030),
            (0.224, -0.040), (0.208, -0.046), (0.170, -0.020), (0.120, 0.004), (0.090, 0.012), (-0.200, 0.012)]
    bd.prism(core, -0.0175, 0.0175, 'steel', side='steel', top='steel_top')
    # lower polymer strip and the rear polymer shell (both sides)
    low = [(-0.2275, 0.0345), (-0.2005, 0.0115), (0.0705, 0.0115), (0.0705, 0.0405), (-0.2275, 0.0405)]
    shell = [(0.070, 0.0115), (0.070, 0.0760), (0.150, 0.0800), (0.195, 0.0765), (0.2215, 0.0620), (0.2262, 0.0300), (0.2245, -0.0400),
             (0.2085, -0.0462), (0.170, -0.0200), (0.1200, 0.0045), (0.0900, 0.0125)]
    for sgn in (-1, 1):
        a, b_ = (0.0170, 0.0205) if sgn > 0 else (-0.0205, -0.0170)
        bd.prism(low, a, b_, 'poly_end', side='poly_end')
        a, b_ = (0.0170, 0.0225) if sgn > 0 else (-0.0225, -0.0170)
        bd.prism(shell, a, b_, 'poly', side='poly_end')
        # engraved steel upper plates (two panels split by a brass strap)
        a, b_ = (0.0170, 0.0205) if sgn > 0 else (-0.0205, -0.0170)
        bd.prism(cham(-0.2255, -0.1840, 0.0425, 0.0760, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        bd.prism(cham(-0.174, -0.0585, 0.0425, 0.0760, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        bd.prism(cham(-0.0525, 0.0625, 0.0425, 0.0760, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        # carved bone cross plaque on the butt
        lo, hi = (0.0225, 0.0240) if sgn > 0 else (-0.0240, -0.0225)
        bd.prism(K.chaikin([(0.116, 0.014), (0.116, 0.066), (0.170, 0.066), (0.170, 0.014)], 1), lo, hi, 'bone_inlay', side='bone_end')
        # brass straps over the plate joints and grip screws
        for (zc, y0, y1) in ((-0.0555, 0.0425, 0.0790), (-0.1790, 0.0405, 0.0790), (0.0665, 0.0115, 0.0790)):
            x0, x1 = (0.0168, 0.0212) if sgn > 0 else (-0.0212, -0.0168)
            bd.box((x0, y0, zc - 0.0025), (x1, y1, zc + 0.0025), 'brass')
        bd.cyl((sgn * 0.0228, 0.040, 0.142), (sgn * 0.0252, 0.040, 0.142), 0.0035, 8, 'brass', cap='brass')
    # butt plate (brass) + butt shoulder pad edge
    bd.prism([(0.2235, -0.043), (0.2300, -0.043), (0.2305, 0.058), (0.2225, 0.062)], -0.0215, 0.0215, 'brass', side='brass')
    # pistol grip: steel core + stippled polymer scales + bone end plaque
    grip = [(-0.0230, GRIP_TOP), (-0.0240, 0.012), (-0.0245, -0.015), (-0.0235, -0.040), (-0.0225, GRIP_BOT),
            (0.0210, GRIP_BOT), (0.0235, -0.040), (0.0245, -0.012), (0.0245, 0.012), (0.0225, GRIP_TOP)]
    gs = K.chaikin(grip, 1)
    K.prism_ah(bd, K.inset(gs, 0.97), TH, -0.0100, 0.0100, 'steel', side='steel')
    for sgn in (-1, 1):
        for (a, b_, sc, reg) in ((0.0095, 0.0130, 0.995, 'poly'), (0.0130, 0.0148, 0.93, 'poly')):
            lo, hi = (a, b_) if sgn > 0 else (-b_, -a)
            K.prism_ah(bd, K.inset(gs, sc), TH, lo, hi, reg, side='poly_end')
        zy = K.ah_to_zy([(0.0, 0.018)], TH)[0]
        bd.cyl((sgn * 0.0146, zy[1], zy[0]), (sgn * 0.0162, zy[1], zy[0]), 0.0030, 8, 'brass', cap='brass')
    zb = K.ah_to_zy([(-0.0230, GRIP_BOT), (0.0212, GRIP_BOT), (0.0212, GRIP_BOT - 0.0075), (-0.0230, GRIP_BOT - 0.0075)], TH)
    bd.prism(zb, -0.0148, 0.0148, 'brass', side='brass')                              # brass butt cap on the grip
    # trigger guard + trigger + brass selector
    K.tube(bd, [(-0.058, 0.0140), (-0.063, -0.0080), (-0.055, -0.0290), (-0.032, -0.0365), (-0.0195, -0.0300)], 0.0072, 0.0074, 'steel')
    bd.prism([(-0.040, 0.012), (-0.034, 0.012), (-0.036, -0.010), (-0.040, -0.022), (-0.044, -0.020), (-0.042, -0.008)],
             -0.0020, 0.0020, 'brass', side='brass')
    bd.cyl((-0.0205, 0.030, 0.030), (-0.0245, 0.030, 0.030), 0.0050, 8, 'brass', cap='brass')
    # forward finger-grip block (stippled polymer, brass studs, bone cap)
    fg = K.chaikin([(-0.118, 0.014), (-0.121, -0.020), (-0.113, -0.058), (-0.098, -0.070), (-0.086, -0.058), (-0.082, -0.020), (-0.084, 0.014)], 1)
    bd.prism(fg, -0.0185, 0.0185, 'poly', side='poly_end')
    for sgn in (-1, 1):
        for zz, yy in ((-0.1015, -0.012), (-0.1015, -0.040)):
            bd.cyl((sgn * 0.0183, yy, zz), (sgn * 0.0205, yy, zz), 0.0030, 8, 'brass', cap='brass')
    bd.prism([(-0.1005, -0.0690), (-0.0870, -0.0690), (-0.0880, -0.0745), (-0.0995, -0.0745)], -0.0115, 0.0115, 'bone_end', side='bone_end')
    # barrel + slotted flash hider, brass rings
    K.revolve(bd, [(-0.218, 0.0080), (-0.2475, 0.0080), (-0.2500, 0.0098), (-0.2900, 0.0098), (Z_MUZ, 0.0085)],
              BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, z1 in ((-0.2500, -0.2560), (-0.2840, -0.2890)):
        K.revolve(bd, [(z0, 0.0108), (z1, 0.0108)], BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for zz in (-0.2635, -0.2700, -0.2765):                      # hider slots
        bd.box((-0.0034, BY + 0.0092, zz - 0.0022), (0.0034, BY + 0.0106, zz + 0.0022), 'steel')
    # accessory rails flanking the magazine
    for sgn in (-1, 1):
        x0, x1 = (0.0175, 0.0222) if sgn > 0 else (-0.0222, -0.0175)
        bd.box((x0, 0.0775, -0.195), (x1, 0.0930, 0.0405), 'steel', top='steel_top')
    # rear sight (notch posts, brass tips) + front sight (hooded blade, brass bead)
    bd.box((-0.0125, 0.0775, 0.0455), (0.0125, 0.0860, 0.0665), 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0045, 0.0100) if sgn > 0 else (-0.0100, -0.0045)
        bd.box((lo, 0.0860, 0.0500), (hi, Y_SIGHT, 0.0620), 'steel', top='steel_top')
        bd.box((lo, Y_SIGHT - 0.0009, 0.0500), (hi, Y_SIGHT, 0.0620), 'brass')
    bd.box((-0.0085, 0.0700, -0.2260), (0.0085, 0.1000, -0.1960), 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (0.0045, 0.0075) if sgn > 0 else (-0.0075, -0.0045)
        bd.box((lo, 0.1000, -0.2175), (hi, Y_SIGHT - 0.0006, -0.2035), 'steel', top='steel_top')
    bd.box((-0.0030, 0.1000, -0.2150), (0.0030, Y_SIGHT - 0.0016, -0.2060), 'steel')
    bd.box((-0.0016, Y_SIGHT - 0.0016, -0.2135), (0.0016, Y_SIGHT, -0.2075), 'brass')

    # ---------------- cocking handle (brass, slides back) ----------------
    ch = C.Part('cocking_handle')
    ch.box((-0.0240, 0.0585, -0.1060), (-0.0170, 0.0690, -0.0860), 'brass')
    ch.cyl((-0.0240, 0.0638, -0.0960), (-0.0300, 0.0638, -0.0960), 0.0058, 8, 'brass', cap='brass')

    # ---------------- magazine (top-loaded, visible rounds) ----------------
    mg = C.Part('magazine')
    mg.prism(cham(-0.185, 0.032, 0.0792, 0.0992, 0.003), -0.0155, 0.0155, 'mag', side='steel')
    mg.box((-0.0168, 0.0800, -0.1955), (0.0168, 0.0984, -0.1855), 'brass')
    mg.box((-0.0168, 0.0800, 0.0305), (0.0168, 0.0984, 0.0355), 'brass')

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
    K.render_gun(glb, render_dir, 'smg_bullpup')


if __name__ == '__main__':
    K.run(finish, render, NAME)
