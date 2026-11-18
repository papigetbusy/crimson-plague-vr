"""Crimson Plague VR - smg_bullpup_base: the Bullpup SMG (v2, sleek).

Original low-poly PS2 / Snake Eater style bullpup submachine gun, FN P90
proportions and a slim, flowing shell: octagonal-section polymer body that tapers
into the muzzle end and sweeps down into a thumbhole butt, a thin top-loaded
magazine under a slotted low-profile rail, a slim realistic-sized grip with a
slender trigger guard, and a short shrouded barrel with a small slotted hider.
Gothic touches kept fine and subtle: two thin engraved steel inlay plates per
side, thin brass trim bands, a tiny bone cross inlay on the butt and brass-ringed
visible rounds in the magazine. Steel and brass share the locked 1911 metal
material (metallic 1 / roughness 0.30); polymer + bone share one non-metal
material; one 256 px atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_bullpup_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/smg_bullpup_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/smg_bullpup_base.glb --type gun --max-tris 3000 --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_bullpup_base.py -- --render-glb assets/models/gun/smg_bullpup_base.glb \
    --render-dir /workspace/base_gun_previews

Meshes: body (shell, inlay plates, grip, guard, shroud + barrel + hider, slotted top rail, sights),
cocking_handle (small brass charging handle on the left, slides back), magazine (top-loaded, under mag_well).
Empties: muzzle, mag_well, rear_sight, front_sight. rear/front share X=0 and Y, so the sight line is exactly
parallel to the bore (dir 0,0,-1); the bore is 47 mm below it (v1 was 73.5 mm).
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_gothic_common as K
C, M, G = K.C, K.M, K.G

NAME = 'smg_bullpup_base'
TH = math.radians(14)
BY = 0.050                       # bore height
Z_MUZ = -0.292
Y_SIGHT = 0.0970
Z_REAR_SIGHT, Z_FRONT_SIGHT = 0.0500, -0.2050
RAIL_Y0, RAIL_Y1 = 0.0820, 0.0895
MAG_Y0, MAG_Y1 = 0.0620, 0.0820
PH = -math.pi / 12
MAGW = (0.0, MAG_Y0, -0.065)      # mag_well (x, y, z): centre of the magazine underside
GRIP_TOP, GRIP_BOT = 0.022, -0.070
# shell stations: (z, half width, bottom y, top y)
ST = [(-0.215, 0.0120, 0.040, 0.058), (-0.190, 0.0145, 0.032, 0.062), (-0.170, 0.0160, 0.028, 0.062), (-0.100, 0.0160, 0.024, 0.062),
      (-0.030, 0.0160, 0.020, 0.062), (0.030, 0.0160, 0.018, 0.062), (0.110, 0.0160, 0.014, 0.062), (0.150, 0.0158, 0.000, 0.062),
      (0.190, 0.0148, -0.030, 0.058), (0.222, 0.0135, -0.044, 0.046), (0.230, 0.0125, -0.046, 0.034)]
CH = 0.0055


def oct_prof(w, y0, y1, c=CH):
    return [(-w + c, y0), (w - c, y0), (w, y0 + c), (w, y1 - c), (w - c, y1), (-w + c, y1), (-w, y1 - c), (-w, y0 + c)]


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


def build(out_dir):
    C.M.reset_scene()
    A = K.Atlas([
        ('barrel', 128, 72), ('mag', 96, 32), ('bone_inlay', 40, 40), ('panel', 112, 36), ('poly', 48, 48),
        ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16), ('poly_end', 16, 16),
    ])
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=14, grime=0.84, arches=False)
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
    bd.loft([(z, oct_prof(w, y0, y1)) for z, w, y0, y1 in ST], 'poly', top='poly', end='poly_end')
    # two thin engraved steel inlay plates per side (flush with the flat of the shell) + thin brass strap between them
    for sgn in (-1, 1):
        a, b_ = (0.0158, 0.0170) if sgn > 0 else (-0.0170, -0.0158)
        bd.prism(K.chaikin(cham(-0.1650, -0.0300, 0.0345, 0.0560, 0.004), 0), a, b_, 'panel', side='steel', top='steel_top')
        bd.prism(cham(-0.0200, 0.0950, 0.0345, 0.0560, 0.004), a, b_, 'panel', side='steel', top='steel_top')
        x0, x1 = (0.0156, 0.0172) if sgn > 0 else (-0.0172, -0.0156)
        bd.box((x0, 0.0330, -0.0272), (x1, 0.0575, -0.0228), 'brass')
        # tiny bone cross inlay on the butt
        lo, hi = (0.0148, 0.0160) if sgn > 0 else (-0.0160, -0.0148)
        bd.prism(K.chaikin(cham(0.1380, 0.1760, 0.0100, 0.0480, 0.006), 1), lo, hi, 'bone_inlay', side='bone_end')
        bd.cyl((sgn * 0.0152, 0.0420, 0.0950 + 0.0200), (sgn * 0.0176, 0.0420, 0.1150), 0.0024, 8, 'brass', cap='brass')
    # thin brass trim bands around the shell
    for zc in (-0.1700,):
        z0, z1 = zc, zc - 0.0030
        def prof_at(z):
            for (za, wa, y0a, y1a), (zb, wb, y0b, y1b) in zip(ST, ST[1:]):
                if zb <= z <= za or za <= z <= zb:
                    t = (z - za) / (zb - za)
                    return wa + (wb - wa) * t + 0.0010, y0a + (y0b - y0a) * t - 0.0010, y1a + (y1b - y1a) * t + 0.0008
        w, y0, y1 = prof_at(z0)
        bd.loft([(z0, oct_prof(w, y0, y1)), (z1, oct_prof(w, y0, y1))], 'brass')
    # slim pistol grip (stippled polymer) + thin brass cap
    grip = [(-0.0170, GRIP_TOP), (-0.0180, 0.005), (-0.0180, -0.030), (-0.0170, GRIP_BOT), (0.0150, GRIP_BOT - 0.002), (0.0185, -0.040),
            (0.0195, -0.005), (0.0190, GRIP_TOP)]
    gs = K.chaikin(grip, 1)
    K.prism_ah(bd, gs, TH, -0.0125, 0.0125, 'poly', side='poly_end')
    zb = K.ah_to_zy([(-0.0170, GRIP_BOT - 0.002), (0.0160, GRIP_BOT - 0.004), (0.0160, GRIP_BOT - 0.0070), (-0.0170, GRIP_BOT - 0.0050)], TH)
    bd.prism(zb, -0.0132, 0.0132, 'brass', side='brass')
    for sgn in (-1, 1):
        zy = K.ah_to_zy([(0.0, 0.006)], TH)[0]
        bd.cyl((sgn * 0.0122, zy[1], zy[0]), (sgn * 0.0138, zy[1], zy[0]), 0.0024, 8, 'brass', cap='brass')
    # slender trigger guard + trigger + tiny brass selector
    K.tube(bd, [(-0.052, 0.0200), (-0.056, 0.0040), (-0.047, -0.0150), (-0.031, -0.0215), (-0.0175, -0.0150)], 0.0050, 0.0054, 'steel')
    bd.prism([(-0.0360, 0.0190), (-0.0320, 0.0190), (-0.0330, 0.0040), (-0.0350, -0.0060), (-0.0385, -0.0110), (-0.0410, -0.0100),
              (-0.0390, -0.0030), (-0.0372, 0.0060)], -0.0014, 0.0014, 'brass', side='brass')
    bd.cyl((-0.0162, 0.0300, 0.0280), (-0.0200, 0.0300, 0.0280), 0.0034, 8, 'brass', cap='brass')
    # shroud + barrel + small slotted hider, thin brass rings
    K.revolve(bd, [(-0.205, 0.0095), (-0.2500, 0.0095), (-0.2520, 0.0070), (-0.2840, 0.0070), (Z_MUZ, 0.0062)],
              BY, segs=12, region='barrel', cap_f='muzzle', cap_b='steel', phase=PH)
    for z0, z1 in ((-0.2500, -0.2535), (-0.2800, -0.2830)):
        K.revolve(bd, [(z0, 0.0102 if z0 > -0.26 and z0 < -0.24 else 0.0080), (z1, 0.0102 if z0 > -0.26 and z0 < -0.24 else 0.0080)],
                  BY, segs=12, region='brass', cap_f='brass', cap_b='brass', phase=PH)
    for zz in (-0.2860, -0.2900):
        bd.box((-0.0024, BY + 0.0066, zz - 0.0013), (0.0024, BY + 0.0078, zz + 0.0013), 'steel')
    # support pylons + slotted top rail
    bd.box((-0.0070, 0.0560, -0.2150), (0.0070, RAIL_Y0 + 0.0005, -0.1650), 'steel', top='steel_top')
    bd.box((-0.0070, 0.0600, 0.0350), (0.0070, RAIL_Y0 + 0.0005, 0.0600), 'steel', top='steel_top')
    z = -0.2130
    while z + 0.0105 < 0.0580:
        bd.box((-0.0115, RAIL_Y0, z), (0.0115, RAIL_Y1, z + 0.0105), 'steel', top='steel_top')
        z += 0.0140
    # rear sight (two thin posts, brass tips) + front sight (slim ears, blade, brass bead)
    for sgn in (-1, 1):
        lo, hi = (0.0035, 0.0058) if sgn > 0 else (-0.0058, -0.0035)
        bd.box((lo, RAIL_Y1 - 0.0005, 0.0440), (hi, Y_SIGHT, 0.0560), 'steel', top='steel_top')
        bd.box((lo, Y_SIGHT - 0.0008, 0.0440), (hi, Y_SIGHT, 0.0560), 'brass')
        lo, hi = (0.0033, 0.0050) if sgn > 0 else (-0.0050, -0.0033)
        bd.box((lo, RAIL_Y1 - 0.0005, -0.2100), (hi, Y_SIGHT - 0.0006, -0.2000), 'steel', top='steel_top')
    bd.box((-0.0016, RAIL_Y1 - 0.0005, -0.2080), (0.0016, Y_SIGHT - 0.0014, -0.2020), 'steel')
    bd.box((-0.0012, Y_SIGHT - 0.0014, -0.2072), (0.0012, Y_SIGHT, -0.2028), 'brass')

    # ---------------- cocking handle (small brass, left side, slides back) ----------------
    ch = C.Part('cocking_handle')
    ch.box((-0.0180, 0.0440, -0.1500), (-0.0155, 0.0500, -0.1340), 'brass')
    ch.cyl((-0.0180, 0.0470, -0.1420), (-0.0235, 0.0470, -0.1420), 0.0042, 8, 'brass', cap='brass')

    # ---------------- magazine (top-loaded, visible rounds) ----------------
    mg = C.Part('magazine')
    mg.prism(cham(-0.165, 0.035, MAG_Y0, MAG_Y1, 0.003), -0.0135, 0.0135, 'mag', side='steel')
    mg.box((-0.0143, MAG_Y0 + 0.0008, -0.1700), (0.0143, MAG_Y1 - 0.0008, -0.1655), 'brass')
    mg.box((-0.0143, MAG_Y0 + 0.0008, 0.0330), (0.0143, MAG_Y1 - 0.0008, 0.0375), 'brass')

    objs = {p.name: p.to_object(mats) for p in (bd, ch, mg)}
    return objs, mats


def cham(z0, z1, y0, y1, c):
    return [(z0 + c, y0), (z1 - c, y0), (z1, y0 + c), (z1, y1 - c), (z1 - c, y1), (z0 + c, y1), (z0, y1 - c), (z0, y0 + c)]


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
