"""Crimson Plague VR - pistol_cannon_base: the Hand Cannon.

Original low-poly PS2 / Snake Eater style heavy .44 magnum revolver (S&W
N-frame proportions: 6.5" ribbed barrel with full underlug, fluted cylinder,
round-butt grips) dressed Gothic: dark blued steel with engraved scrollwork and
lancet arches on the side plates and barrel, carved bone grips with a skull
medallion, brass cylinder bands, barrel rings, trigger and sight-ramp accents.
Locked look from pistol_1911_base: steel (and brass) on a metallic 1 / rough
0.30 material, bone on its own non-metal material, one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_cannon_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/pistol_cannon_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/pistol_cannon_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_cannon_base.py -- --render-glb assets/models/gun/pistol_cannon_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: frame (frame + barrel + underlug + sights + guard + trigger + bone grips),
hammer (origin at its pivot), magazine (= the cylinder, origin at mag_well).
Empties: muzzle, mag_well (cylinder centre), rear_sight, front_sight.
Sight line: rear and front empties share X=0 and Y, so it is exactly parallel
to the bore (dir 0,0,-1); the bore is 23 mm below it.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_gothic_common as K
C, M, G = K.C, K.M, K.G

NAME = 'pistol_cannon_base'
TH = math.radians(16)
YB, YC, RC = 0.0655, 0.049, 0.0225        # bore height, cylinder centre height, cylinder radius
ZCR, ZCF, ZMUZ = -0.012, -0.058, -0.222   # cylinder rear/front face, muzzle
Y_TOP = 0.0795                             # top strap / rib top
Y_SIGHT = 0.0885                           # sight line height (rear notch top = front blade top)
Z_REAR_SIGHT, Z_FRONT_SIGHT = -0.007, -0.2170


hexp = K.hexp
PH = -math.pi / 12      # ring phase: segment 0 is centred on the right flank, 3 on top, 6 on the left


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('cyl', 56, 144), ('bone_panel', 64, 96), ('barrel', 160, 72), ('frame_side', 44, 60),
        ('bone_plain', 32, 56), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28),
        ('cyl_face', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=3, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=4, grime=0.72)
    A.engraved('frame_side', seed=7, lam=18, cross=False)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j in (3,) else 'dark' if j in (9,) else 'plain',
           seed=9, lam=20)
    A.wrap('cyl', 24, 6, lambda j: ('land', 'wall', 'floor', 'wall')[j % 4], seed=13,
           u_bands=[(0.0, 0.16, 'brass'), (0.86, 1.0, 'brass')], lam=15)
    A.chambers('cyl_face'); A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_end', motif=None, rim=False)
    A.bone('bone_plain', seed=33, motif=None)
    A.bone('bone_panel', seed=35, motif='skull')
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = C.make_materials(NAME, tex, furn='bone')
    mats[1].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.42

    # ---------------- frame ----------------
    fr = C.Part('frame')
    # rear block: plain body + engraved side plates
    blk = [(ZCR, 0.0275), (0.016, 0.0275), (0.022, 0.040), (0.0235, 0.062), (0.0205, Y_TOP), (ZCR, Y_TOP)]
    fr.prism(blk, -0.0158, 0.0158, 'steel', side='steel', top='steel_top')
    plate = [(-0.0095, 0.033), (0.0145, 0.033), (0.0195, 0.042), (0.0205, 0.062), (0.0185, 0.0765), (-0.0095, 0.0765)]
    fr.prism(plate, 0.0158, 0.0172, 'frame_side', side='steel')
    fr.prism(plate, -0.0172, -0.0158, 'frame_side', side='steel')
    # top strap over the cylinder (chamfered)
    fr.loft([(ZCF, hexp(-0.0128, 0.0128, 0.0705, Y_TOP, 0.0022)), (ZCR, hexp(-0.0128, 0.0128, 0.0705, Y_TOP, 0.0022))],
            'steel', top='steel_top')
    # floor under the cylinder + crane / yoke + barrel root block
    fr.box((-0.0105, 0.0215, ZCF), (0.0105, 0.0270, ZCR), 'steel')
    fr.loft([(-0.0825, hexp(-0.0138, 0.0138, 0.030, Y_TOP, 0.0030)), (ZCF, hexp(-0.0138, 0.0138, 0.030, Y_TOP, 0.0030))],
            'steel', top='steel_top')
    # barrel: shrouded root, taper, crown; underlug; vent rib; brass rings
    br = K.revolve
    br(fr, [(ZCF, 0.0128), (-0.084, 0.0128), (-0.098, 0.0106), (-0.2125, 0.0106), (-0.2150, 0.0112), (-0.2190, 0.0112), (ZMUZ, 0.0098)],
       YB, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    br(fr, [(-0.064, 0.0098), (-0.186, 0.0098)], 0.0450, segs=12, region='barrel', cap_f='steel', cap_b='steel', phase=PH)
    RECT = lambda w, y0, y1: [(-w, y0), (w, y0), (w, y1), (-w, y1)]
    fr.loft([(-0.070, RECT(0.0046, 0.0440, 0.0660)), (-0.182, RECT(0.0046, 0.0440, 0.0660))], 'steel')
    fr.loft([(-0.074, RECT(0.0042, 0.0742, 0.0805)), (-0.2165, RECT(0.0042, 0.0742, 0.0805))], 'steel', top='steel_top')
    for z0, z1, r, cyy in ((-0.1930, -0.2000, 0.0116, YB), (-0.1000, -0.1060, 0.0116, YB), (-0.1840, -0.1900, 0.0102, 0.0450),
                           (-0.0700, -0.0760, 0.0102, 0.0450)):
        br(fr, [(z0, r), (z1, r)], cyy, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    # lug tip: brass ejector-rod knob
    br(fr, [(-0.1860, 0.0076), (-0.1930, 0.0070)], 0.0450, segs=10, region='brass', cap_f='brass', cap_b='brass')
    # front sight: low ramp, steel blade, brass bead (top = sight line); rear sight posts with a notch
    fr.prism([(-0.2000, 0.0805), (-0.2145, 0.0850), (-0.2145, 0.0805)], -0.0020, 0.0020, 'steel_top', side='steel')
    fr.box((-0.0020, 0.0805, -0.2190), (0.0020, Y_SIGHT - 0.0016, -0.2145), 'steel')
    fr.box((-0.0022, Y_SIGHT - 0.0016, -0.2190), (0.0022, Y_SIGHT, -0.2145), 'brass')
    fr.box((-0.0095, 0.0790, -0.0100), (0.0095, 0.0810, -0.0040), 'steel')
    fr.box((-0.0095, 0.0805, -0.0100), (-0.0025, Y_SIGHT, -0.0040), 'steel', top='steel_top')
    fr.box((0.0025, 0.0805, -0.0100), (0.0095, Y_SIGHT, -0.0040), 'steel', top='steel_top')
    fr.box((-0.0095, Y_SIGHT - 0.0010, -0.0100), (-0.0025, Y_SIGHT, -0.0040), 'brass')   # brass sight-line edges
    fr.box((0.0025, Y_SIGHT - 0.0010, -0.0100), (0.0095, Y_SIGHT, -0.0040), 'brass')
    # sideplate screws + brass cylinder latch (left)
    for (zz, yy) in ((-0.0045, 0.0360), (0.0150, 0.0690)):
        for sgn in (-1, 1):
            fr.cyl((sgn * 0.0172, yy, zz), (sgn * 0.0184, yy, zz), 0.0026, 8, 'brass', cap='brass')
    fr.box((-0.0215, 0.0455, -0.0090), (-0.0172, 0.0520, 0.0105), 'brass')
    # trigger guard + trigger
    K.tube(fr, [(-0.0245, 0.0285), (-0.0265, 0.0105), (-0.0340, 0.0025), (-0.0490, 0.0000), (-0.0615, 0.0065),
                (-0.0655, 0.0215), (-0.0620, 0.0305)], 0.0056, 0.0060, 'steel')
    fr.prism([(-0.0345, 0.0285), (-0.0285, 0.0285), (-0.0285, 0.0185), (-0.0305, 0.0095), (-0.0345, 0.0055),
              (-0.0385, 0.0050), (-0.0388, 0.0085), (-0.0352, 0.0125), (-0.0338, 0.0190)], -0.0022, 0.0022, 'brass', side='brass')
    # grip: steel core + stepped bone panels (plain base, raised border, inset skull medallion)
    grip = [(-0.021, 0.034), (-0.0250, 0.018), (-0.0275, 0.000), (-0.0270, -0.020), (-0.0235, -0.040), (-0.0165, -0.056),
            (-0.0050, -0.064), (0.0110, -0.064), (0.0210, -0.056), (0.0262, -0.038), (0.0270, -0.015), (0.0258, 0.008), (0.0225, 0.032)]
    grip = [(a * 0.94, h * 0.93 - 0.002) for a, h in grip]
    gs = K.chaikin(grip, 2); gs1 = K.chaikin(grip, 1)
    K.prism_ah(fr, K.inset(gs, 0.95), TH, -0.0070, 0.0070, 'steel_top', side='steel_top')
    for sgn in (-1, 1):
        for k, (a, b, sc, reg) in enumerate(((0.0065, 0.0158, 0.995, 'bone_plain'), (0.0158, 0.0182, 0.94, 'bone_plain'),
                                             (0.0182, 0.0196, 0.78, 'bone_panel'))):
            lo, hi = (a, b) if sgn > 0 else (-b, -a)
            K.prism_ah(fr, K.inset(gs if k == 0 else gs1, sc), TH, lo, hi, reg, side='bone_end')
    zy = K.ah_to_zy([(0.0, 0.020)], TH)[0]
    for sgn in (-1, 1):                                          # brass escutcheon screws on the panels
        fr.cyl((sgn * 0.0194, zy[1], zy[0]), (sgn * 0.0212, zy[1], zy[0]), 0.0040, 8, 'brass', cap='brass')
    bz = K.ah_to_zy([(-0.0150, -0.0625), (0.0100, -0.0625)], TH)  # brass butt plate
    fr.prism([(bz[0][0], bz[0][1] - 0.0050), (bz[1][0], bz[1][1] - 0.0050), (bz[1][0] + 0.0010, bz[1][1] + 0.0010), (bz[0][0] - 0.0010, bz[0][1] + 0.0010)],
             -0.0108, 0.0108, 'brass', side='brass')
    # ---------------- hammer ----------------
    hm = C.Part('hammer')
    hm.prism([(0.0150, 0.0520), (0.0225, 0.0520), (0.0290, 0.0620), (0.0345, 0.0725), (0.0348, 0.0775), (0.0278, 0.0795),
              (0.0250, 0.0735), (0.0190, 0.0640)], -0.0042, 0.0042, 'steel_top', side='steel')
    hm.cyl((-0.0058, 0.0525, 0.0200), (0.0058, 0.0525, 0.0200), 0.0036, 8, 'brass', cap='brass')
    # ---------------- cylinder (= magazine) ----------------
    cy = C.Part('magazine')
    fl = lambda i: 0.0225 if i % 4 in (0, 1) else 0.0194
    K.revolve(cy, [(ZCR, 0.0225), (-0.0185, 0.0225), (-0.0235, fl), (-0.0465, fl), (-0.0505, 0.0225), (ZCF, 0.0225)],
              YC, segs=24, region='cyl', cap_f='cyl_face', cap_b='cyl_face')
    objs = {p.name: p.to_object(mats) for p in (fr, hm, cy)}
    M.set_origin_world(objs['hammer'], G(0.0, 0.0525, 0.0200))  # hammer pivot
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('pistol_cannon', objs, {
        'muzzle': (0, YB, ZMUZ),
        'mag_well': (0, YC, (ZCR + ZCF) / 2),
        'rear_sight': (0, Y_SIGHT, Z_REAR_SIGHT),
        'front_sight': (0, Y_SIGHT, Z_FRONT_SIGHT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'pistol_cannon')


if __name__ == '__main__':
    K.run(finish, render, NAME)
