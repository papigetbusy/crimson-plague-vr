"""Crimson Plague VR - pistol_machine_base: the Machine Pistol.

Original low-poly PS2 / Snake Eater style selective-fire machine pistol
(Beretta 93R / Glock 18 proportions: open-top slide over an exposed ported
barrel with compensator, hooked guard with a deployed folding foregrip, long
20-round extended magazine), dressed Gothic: dark blued slide engraved with
scrollwork and lancet arches, stippled black polymer grip scales with carved
bone cross plaques, brass selector, foregrip pivot, comp ring and magazine
baseplate. Steel and brass share the locked 1911 metal material (metallic 1 /
roughness 0.30); polymer + bone share one non-metal material; one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_machine_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/pistol_machine_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/pistol_machine_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_machine_base.py -- --render-glb assets/models/gun/pistol_machine_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: slide (recoils; origin at its bounds), frame (frame + barrel + comp + grip +
guard + foregrip + hammer + trigger), magazine (under mag_well).
Empties: muzzle, mag_well, rear_sight, front_sight. rear/front share X=0 and Y, so
the sight line is exactly parallel to the bore (dir 0,0,-1); bore is 20 mm below it.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_gothic_common as K
C, M, G = K.C, K.M, K.G

NAME = 'pistol_machine_base'
TH = math.radians(19)
YB = 0.0535
Y_SB, Y_ST = 0.037, 0.067          # slide bottom / top
Y_SIGHT = 0.0735
Z_SR, Z_SF = 0.034, -0.138          # slide rear / front
Z_MUZ = -0.190
Z_REAR_SIGHT, Z_FRONT_SIGHT = 0.0285, -0.1330
PH = -math.pi / 12
GRIP_H = -0.050
WELL = K.ah_to_zy([(0.0, GRIP_H)], TH)[0]          # (z, y) of the mag well


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('mag', 40, 96), ('bone_inlay', 40, 64), ('slide_f', 112, 36), ('slide_r', 64, 36),
        ('poly', 48, 48), ('steel', 48, 32), ('steel_top', 48, 24), ('serr', 24, 28), ('muzzle', 28, 28),
        ('brass', 24, 24), ('bone_end', 16, 16), ('poly_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('slide_f', seed=9, lam=22, grime=0.82)
    A.engraved('slide_r', seed=10, lam=20, grime=0.82, cross=False)
    A.serrations('serr')
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.mag('mag'); A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_inlay', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    A.poly('poly', seed=43, checker=True); A.poly('poly_end', seed=45, dark=True)
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    A.save(tex)
    mats = C.make_materials(NAME, tex, furn='polymer')
    mats[1].name = NAME + '_polymer'
    mats[1].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.55
    mats[1].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.22
    C.REGION  # (atlas installed)
    K.FURN.add('poly_end')

    # ---------------- slide ----------------
    sl = C.Part('slide')
    prof = lambda w: K.hexp(-w, w, Y_SB, Y_ST, 0.0030)
    sl.loft([(-0.030, prof(0.0125)), (Z_SR, prof(0.0125))], 'slide_r', top='steel_top', end='steel')
    for sgn in (-1, 1):                                        # front walls (open top), engraved
        sl.box((sgn * 0.0090 if sgn > 0 else -0.0125, Y_SB, Z_SF), (0.0125 if sgn > 0 else -0.0090, Y_ST, -0.030),
               'slide_f', top='steel_top', end='steel')
    sl.box((-0.0090, Y_SB, Z_SF), (0.0090, 0.0470, -0.030), 'steel')                 # floor bar under the barrel
    sl.loft([(Z_SF, K.hexp(-0.0125, 0.0125, Y_SB, Y_ST, 0.0030)), (-0.1255, K.hexp(-0.0125, 0.0125, Y_SB, Y_ST, 0.0030))],
            'steel', top='steel_top')                                                 # front cap
    for sgn in (-1, 1):                                        # rear serrations
        x0, x1 = (0.0124, 0.0129) if sgn > 0 else (-0.0129, -0.0124)
        sl.box((x0, 0.0405, 0.0105), (x1, 0.0635, 0.0315), 'serr')
    # rear sight (notch) + front sight (post, brass bead)
    sl.box((-0.0080, Y_ST - 0.0005, 0.0255), (0.0080, Y_ST + 0.0012, 0.0315), 'steel')
    for sgn in (-1, 1):
        lo, hi = (0.0024, 0.0080) if sgn > 0 else (-0.0080, -0.0024)
        sl.box((lo, Y_ST, 0.0255), (hi, Y_SIGHT, 0.0315), 'steel', top='steel_top')
        sl.box((lo, Y_SIGHT - 0.0009, 0.0255), (hi, Y_SIGHT, 0.0315), 'brass')
    sl.box((-0.0034, Y_ST, -0.1385), (0.0034, Y_SIGHT - 0.0016, -0.1275), 'steel')
    sl.box((-0.0016, Y_SIGHT - 0.0016, -0.1370), (0.0016, Y_SIGHT, -0.1290), 'brass')

    # ---------------- frame ----------------
    fr = C.Part('frame')
    fr.loft([(-0.100, K.hexp(-0.0105, 0.0105, 0.0285, Y_SB + 0.001, 0.0015)), (0.032, K.hexp(-0.0105, 0.0105, 0.0285, Y_SB + 0.001, 0.0015))],
            'steel', top='steel_top')
    # barrel + ported compensator (visible through the open slide)
    K.revolve(fr, [(-0.030, 0.0070), (-0.1275, 0.0070), (-0.1500, 0.0078), (-0.1520, 0.0090), (-0.1860, 0.0090), (Z_MUZ, 0.0080)],
              YB, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    K.revolve(fr, [(-0.1500, 0.0097), (-0.1560, 0.0097)], YB, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    K.revolve(fr, [(-0.1765, 0.0097), (-0.1805, 0.0097)], YB, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for zz in (-0.1620, -0.1680, -0.1740):                      # comp ports (dark slots on top and both flanks)
        fr.box((-0.0036, YB + 0.0082, zz - 0.0022), (0.0036, YB + 0.0096, zz + 0.0022), 'steel')
    # grip: steel core, stippled polymer scales, carved bone cross plaques
    grip = [(-0.0230, 0.034), (-0.0240, 0.012), (-0.0245, -0.015), (-0.0235, -0.040), (-0.0225, GRIP_H),
            (0.0210, GRIP_H), (0.0235, -0.040), (0.0245, -0.012), (0.0245, 0.012), (0.0225, 0.034)]
    gs = K.chaikin(grip, 1)
    K.prism_ah(fr, K.inset(gs, 0.97), TH, -0.0106, 0.0106, 'steel', side='steel')
    gs1 = K.chaikin(grip, 1)
    for sgn in (-1, 1):
        for (a, b, sc, reg) in ((0.0100, 0.0140, 0.995, 'poly'), (0.0140, 0.0160, 0.93, 'poly'), (0.0160, 0.0170, 0.70, 'bone_inlay')):
            lo, hi = (a, b) if sgn > 0 else (-b, -a)
            K.prism_ah(fr, K.inset(gs, sc), TH, lo, hi, reg, side='poly_end' if reg == 'poly' else 'bone_end')
    # brass grip screw, butt cap
    for sgn in (-1, 1):
        zy = K.ah_to_zy([(0.0, 0.020)], TH)[0]
        fr.cyl((sgn * 0.0156, zy[1], zy[0]), (sgn * 0.0172, zy[1], zy[0]), 0.0030, 8, 'brass', cap='brass')
    # trigger guard (squared hook) + trigger + folding foregrip (deployed) with brass pivot
    K.tube(fr, [(-0.0300, 0.0290), (-0.0450, 0.0295), (-0.0680, 0.0310), (-0.0705, 0.0100), (-0.0665, -0.0035), (-0.0450, -0.0075),
                (-0.0300, -0.0070), (-0.0245, -0.0020)], 0.0072, 0.0074, 'steel')
    fr.prism([(-0.0420, 0.0300), (-0.0365, 0.0300), (-0.0370, 0.0170), (-0.0395, 0.0080), (-0.0440, 0.0030), (-0.0478, 0.0035),
              (-0.0455, 0.0100), (-0.0430, 0.0180)], -0.0020, 0.0020, 'brass', side='brass')
    K.tube(fr, [(-0.0665, -0.0035), (-0.0700, -0.0250), (-0.0720, -0.0480), (-0.0680, -0.0560), (-0.0550, -0.0580)],
           0.0100, 0.0140, 'steel_top')
    fr.cyl((-0.0044, -0.0035, -0.0665), (0.0044, -0.0035, -0.0665), 0.0040, 8, 'brass', cap='brass')
    for sgn in (-1, 1):
        fr.cyl((sgn * 0.0040, -0.0035, -0.0665), (sgn * 0.0058, -0.0035, -0.0665), 0.0044, 8, 'brass', cap='brass')
    # hammer (exposed) + brass selector lever on the left
    fr.prism([(0.0230, 0.0400), (0.0310, 0.0400), (0.0365, 0.0455), (0.0380, 0.0530), (0.0355, 0.0600), (0.0310, 0.0615),
              (0.0295, 0.0560), (0.0265, 0.0490)], -0.0034, 0.0034, 'steel_top', side='steel')
    fr.prism([(0.0000, 0.0290), (0.0160, 0.0290), (0.0185, 0.0325), (0.0160, 0.0360), (0.0000, 0.0360)], -0.0140, -0.0102, 'brass', side='brass')
    # ---------------- magazine (extended 20-round) ----------------
    mg = C.Part('magazine')
    mag_poly = [(-0.0198, 0.012), (0.0198, 0.012), (0.0206, GRIP_H - 0.058), (-0.0206, GRIP_H - 0.058)]
    mg_zy = K.ah_to_zy([(a, h) for a, h in mag_poly], TH)
    mg.prism(mg_zy, -0.0098, 0.0098, 'mag', side='steel')
    bp = K.ah_to_zy([(-0.0230, GRIP_H - 0.0570), (0.0222, GRIP_H - 0.0570), (0.0222, GRIP_H - 0.0650), (-0.0230, GRIP_H - 0.0650)], TH)
    mg.prism(bp, -0.0124, 0.0124, 'brass', side='brass')
    objs = {p.name: p.to_object(mats) for p in (sl, fr, mg)}
    return objs, mats


def finish(out_dir):
    objs, mats = build(out_dir)
    C.assemble('pistol_machine', objs, {
        'muzzle': (0, YB, Z_MUZ),
        'mag_well': (0, WELL[1], WELL[0]),
        'rear_sight': (0, Y_SIGHT, Z_REAR_SIGHT),
        'front_sight': (0, Y_SIGHT, Z_FRONT_SIGHT),
    })
    K.write_wiring_dump(NAME)
    C.save_blend(out_dir, NAME)


def render(glb, render_dir, *_):
    K.render_gun(glb, render_dir, 'pistol_machine')


if __name__ == '__main__':
    K.run(finish, render, NAME)
