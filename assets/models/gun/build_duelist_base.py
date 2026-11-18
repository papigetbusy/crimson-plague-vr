"""Crimson Plague VR - pistol_duelist_base: the Duelist.

Original low-poly PS2 / Snake Eater style slim single-action revolver (Colt
Single Action Army / Python proportions: 8.5" slender round barrel with an
ejector-rod housing, smooth six-shot cylinder, plow-handle grip, long hammer
spur), dressed Gothic and deliberately the opposite of the Hand Cannon:
slender, long and ornate. Blued steel engraved with scrollwork, lancet arches
and a cross; ivory grips carved with filigree and a cross medallion; brass
front/back straps, trigger guard, trigger, cylinder rings and ejector tip.
Steel and brass share the locked 1911 metal material (metallic 1 / roughness
0.30); ivory has its own non-metal material; one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_duelist_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/pistol_duelist_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/pistol_duelist_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_duelist_base.py -- --render-glb assets/models/gun/pistol_duelist_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: frame (frame + barrel + ejector housing + sights + guard + trigger + grip),
hammer (origin at its pivot), magazine (= the cylinder, origin at mag_well).
Empties: muzzle, mag_well (cylinder centre), rear_sight, front_sight. rear/front
share X=0 and Y, so the sight line is exactly parallel to the bore (dir 0,0,-1);
the bore is 16.5 mm below it.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_gothic_common as K
C, M, G = K.C, K.M, K.G

NAME = 'pistol_duelist_base'
TH = math.radians(20)
YB, YC, RC = 0.0610, 0.0475, 0.0185
ZCR, ZCF, ZMUZ = -0.010, -0.050, -0.264
Y_TOP = 0.0715                     # top strap top
Y_SIGHT = 0.0775
Z_REAR_SIGHT, Z_FRONT_SIGHT = -0.0045, -0.2600
PH = -math.pi / 12
hexp = K.hexp


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('cyl', 48, 120), ('bone_panel', 64, 96), ('barrel', 200, 72), ('frame_side', 36, 56),
        ('bone_plain', 32, 56), ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28),
        ('cyl_face', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=8, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=9, grime=0.74)
    A.engraved('frame_side', seed=12, lam=16, arches=True, cross=False)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=14, lam=17)
    A.wrap('cyl', 20, 6, lambda j: 'eng' if j % 2 == 0 else 'hi' if j % 4 == 1 else 'plain', seed=16,
           u_bands=[(0.0, 0.10, 'brass'), (0.90, 1.0, 'brass')], lam=13)
    A.chambers('cyl_face'); A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_end', motif=None, rim=False)
    A.bone('bone_plain', seed=47, motif=None)
    A.bone('bone_panel', seed=49, motif='filigree')
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = C.make_materials(NAME, tex, furn='bone')
    mats[1].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.42

    fr = C.Part('frame')
    blk = [(ZCR, 0.0275), (0.0105, 0.0275), (0.0170, 0.0360), (0.0215, 0.0560), (0.0195, Y_TOP), (ZCR, Y_TOP)]
    fr.prism(blk, -0.0122, 0.0122, 'steel', side='steel', top='steel_top')
    plate = [(-0.0050, 0.0310), (0.0100, 0.0310), (0.0155, 0.0385), (0.0185, 0.0560), (0.0170, 0.0690), (-0.0050, 0.0690)]
    fr.prism(plate, 0.0122, 0.0134, 'frame_side', side='steel')
    fr.prism(plate, -0.0134, -0.0122, 'frame_side', side='steel')
    # top strap and cylinder-window frame, chamfered
    fr.loft([(ZCF, hexp(-0.0098, 0.0098, 0.0660, Y_TOP, 0.0018)), (ZCR, hexp(-0.0098, 0.0098, 0.0660, Y_TOP, 0.0018))], 'steel', top='steel_top')
    fr.box((-0.0080, 0.0225, ZCF), (0.0080, 0.0290, ZCR), 'steel')
    fr.loft([(-0.0640, hexp(-0.0112, 0.0112, 0.0300, Y_TOP, 0.0024)), (ZCF, hexp(-0.0112, 0.0112, 0.0300, Y_TOP, 0.0024))], 'steel', top='steel_top')
    # slim barrel, flared crown; ejector-rod housing on the right with a brass knob; brass rings
    K.revolve(fr, [(ZCF, 0.0100), (-0.080, 0.0092), (-0.2540, 0.0080), (-0.2585, 0.0090), (ZMUZ, 0.0090)],
              YB, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    K.revolve(fr, [(-0.0540, 0.0050), (-0.2000, 0.0050)], YB - 0.0120, cx=0.0128, segs=8, region='barrel', cap_f='steel', cap_b='steel')
    K.revolve(fr, [(-0.2000, 0.0066), (-0.2100, 0.0066)], YB - 0.0120, cx=0.0128, segs=8, region='brass', cap_f='brass', cap_b='brass')
    for z0 in (-0.1050, -0.1900, -0.0680):
        K.revolve(fr, [(z0, 0.0102), (z0 - 0.0060, 0.0102)], YB, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for z0 in (-0.1050, -0.1900):                          # clamp web joining barrel and housing
        fr.box((0.0030, YB - 0.0140, z0 - 0.0060), (0.0140, YB - 0.0030, z0), 'brass')
    fr.box((-0.0010, Y_TOP, -0.0600), (0.0010, Y_TOP + 0.0006, -0.0150), 'brass')           # brass inlay line on the strap
    # front sight: low ramp, blade, brass bead; rear sight posts with a notch
    fr.prism([(-0.2480, 0.0690), (-0.2570, Y_SIGHT - 0.0030), (-0.2570, 0.0690)], -0.0018, 0.0018, 'steel_top', side='steel')
    fr.box((-0.0018, 0.0690, -0.2620), (0.0018, Y_SIGHT - 0.0014, -0.2575), 'steel')
    fr.box((-0.0020, Y_SIGHT - 0.0014, -0.2620), (0.0020, Y_SIGHT, -0.2575), 'brass')
    fr.box((-0.0072, Y_TOP - 0.0010, -0.0075), (0.0072, Y_TOP + 0.0006, -0.0015), 'steel')
    for sgn in (-1, 1):
        lo, hi = (0.0022, 0.0072) if sgn > 0 else (-0.0072, -0.0022)
        fr.box((lo, Y_TOP, -0.0075), (hi, Y_SIGHT, -0.0015), 'steel', top='steel_top')
        fr.box((lo, Y_SIGHT - 0.0009, -0.0075), (hi, Y_SIGHT, -0.0015), 'brass')
    # sideplate screws
    for (zz, yy) in ((-0.0010, 0.0345), (0.0125, 0.0600)):
        for sgn in (-1, 1):
            fr.cyl((sgn * 0.0134, yy, zz), (sgn * 0.0145, yy, zz), 0.0024, 8, 'brass', cap='brass')
    # brass trigger guard + trigger
    K.tube(fr, [(-0.0200, 0.0285), (-0.0215, 0.0105), (-0.0300, 0.0020), (-0.0420, 0.0000), (-0.0520, 0.0060),
                (-0.0545, 0.0200), (-0.0510, 0.0290)], 0.0050, 0.0056, 'brass')
    fr.prism([(-0.0275, 0.0285), (-0.0225, 0.0285), (-0.0230, 0.0175), (-0.0250, 0.0095), (-0.0290, 0.0055),
              (-0.0330, 0.0050), (-0.0332, 0.0082), (-0.0300, 0.0120), (-0.0285, 0.0190)], -0.0018, 0.0018, 'brass', side='brass')
    # plow-handle grip: brass-strapped core, ivory panels with raised filigree/cross medallion
    grip = [(-0.0185, 0.030), (-0.0210, 0.012), (-0.0200, -0.012), (-0.0160, -0.034), (-0.0090, -0.050), (0.0020, -0.058),
            (0.0140, -0.056), (0.0225, -0.046), (0.0270, -0.030), (0.0265, -0.010), (0.0245, 0.012), (0.0215, 0.030)]
    gs = K.chaikin(grip, 2); gs1 = K.chaikin(grip, 1)
    K.prism_ah(fr, K.inset(gs, 0.96), TH, -0.0072, 0.0072, 'brass', side='brass')
    for sgn in (-1, 1):
        for k, (a, b, sc, reg) in enumerate(((0.0066, 0.0138, 0.985, 'bone_plain'), (0.0138, 0.0152, 0.92, 'bone_plain'),
                                             (0.0152, 0.0162, 0.74, 'bone_panel'))):
            lo, hi = (a, b) if sgn > 0 else (-b, -a)
            K.prism_ah(fr, K.inset(gs if k == 0 else gs1, sc), TH, lo, hi, reg, side='bone_end')
    zy = K.ah_to_zy([(0.0, 0.018)], TH)[0]
    for sgn in (-1, 1):
        fr.cyl((sgn * 0.0160, zy[1], zy[0]), (sgn * 0.0176, zy[1], zy[0]), 0.0034, 8, 'brass', cap='brass')
    # hammer with a long curved spur
    hm = C.Part('hammer')
    hm.prism([(0.0120, 0.0470), (0.0185, 0.0470), (0.0240, 0.0550), (0.0295, 0.0640), (0.0335, 0.0700), (0.0345, 0.0735),
              (0.0290, 0.0745), (0.0245, 0.0700), (0.0200, 0.0630), (0.0150, 0.0555)], -0.0034, 0.0034, 'steel_top', side='steel')
    hm.cyl((-0.0046, 0.0500, 0.0160), (0.0046, 0.0500, 0.0160), 0.0030, 8, 'brass', cap='brass')
    # cylinder (= magazine): smooth, engraved vine rows, brass rings, six chambers
    cy = C.Part('magazine')
    K.revolve(cy, [(ZCR, 0.0170), (ZCR - 0.0020, RC), (ZCF + 0.0020, RC), (ZCF, 0.0170)], YC, segs=20, region='cyl',
              cap_f='cyl_face', cap_b='cyl_face')
    objs = {p.name: p.to_object(mats) for p in (fr, hm, cy)}
    M.set_origin_world(objs['hammer'], G(0.0, 0.0500, 0.0160))
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('pistol_duelist', objs, {
        'muzzle': (0, YB, ZMUZ),
        'mag_well': (0, YC, (ZCR + ZCF) / 2),
        'rear_sight': (0, Y_SIGHT, Z_REAR_SIGHT),
        'front_sight': (0, Y_SIGHT, Z_FRONT_SIGHT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'pistol_duelist')


if __name__ == '__main__':
    K.run(finish, render, NAME)
