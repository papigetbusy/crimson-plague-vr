"""Crimson Plague VR - smg_mp5_base (blued steel, worn black polymer).

Original low-poly PS2 / Snake Eater style MP5-pattern SMG with a fixed
stock. Chunky, readable shapes; stipple, ribs and wear are painted into
one 256 px atlas. Locked look from pistol_1911_base: steel metallic 1 /
roughness 0.30; polymer furniture on its own non-metal material.

Build (repo root):
  blender -b --python assets/models/gun/build_mp5_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/smg_mp5_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/smg_mp5_base.glb --type gun --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_mp5_base.py -- --render-glb assets/models/gun/smg_mp5_base.glb \
    --render-dir /workspace/guns_previews --small-dir assets/models/gun/previews

Meshes: receiver (+ barrel, cocking tube, sights, mag well), cocking_handle,
trigger_group (polymer housing + pistol grip), handguard, stock, magazine
(under mag_well). Empties: muzzle, mag_well, rear_sight, front_sight.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_lowpoly_common as C

NAME = 'smg_mp5_base'
BORE_Y = 0.078


def build(out_dir):
    C.M.reset_scene()
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    C.paint_atlas(tex, furn='polymer', seed=37, furn_grime=0.84)
    mats = C.make_materials(NAME, tex, furn='polymer')

    rc = C.Part('receiver')
    w = 0.017
    prof = [(-w + 0.003, 0.045), (w - 0.003, 0.045), (w, 0.052), (w, 0.088), (0.011, 0.100),
            (-0.011, 0.100), (-w, 0.088), (-w, 0.052)]
    rc.loft([(-0.190, prof), (0.060, prof)], 'steel', top='steel_top')
    rc.cyl((0, 0.104, -0.300), (0, 0.104, -0.150), 0.0105, 8, 'barrel')                   # cocking tube
    rc.cyl((0, BORE_Y, -0.190), (0, BORE_Y, -0.345), 0.0085, 8, 'barrel')
    rc.cyl((0, BORE_Y, -0.345), (0, BORE_Y, -0.365), 0.0115, 8, 'ribs', cap='muzzle', cap0='steel')
    rc.box((-0.008, 0.100, -0.302), (0.008, 0.118, -0.286), 'steel')                      # front sight base
    rc.cyl((0, 0.128, -0.302), (0, 0.128, -0.286), 0.012, 8, 'barrel', cap='muzzle')      # hooded post
    rc.box((-0.010, 0.100, 0.026), (0.010, 0.106, 0.054), 'steel')                        # drum sight base
    rc.cyl((-0.012, 0.115, 0.040), (0.012, 0.115, 0.040), 0.011, 8, 'barrel', cap='steel_top')
    rc.box((-0.017, 0.008, -0.168), (0.017, 0.045, -0.112), 'steel')                      # mag well
    rc.box((-0.020, 0.058, -0.012), (-0.017, 0.068, 0.012), 'silver')                     # selector (left)
    cc = C.Part('cocking_handle')
    cc.box((-0.040, 0.099, -0.262), (-0.010, 0.107, -0.252), 'steel_top')
    cc.cyl((-0.040, 0.103, -0.270), (-0.040, 0.103, -0.244), 0.0055, 6, 'barrel', cap='silver')
    tg = C.Part('trigger_group')
    tg.box((-0.016, 0.020, -0.068), (0.016, 0.046, 0.058), 'furn_dark')
    tg.box((-0.006, -0.012, -0.072), (0.006, -0.002, 0.004), 'furn_dark')                 # guard bar
    tg.box((-0.006, -0.002, -0.072), (0.006, 0.020, -0.060), 'furn_dark')
    tg.prism([(-0.030, 0.020), (-0.022, 0.020), (-0.025, 0.006), (-0.036, -0.002), (-0.038, 0.004), (-0.031, 0.012)],
             -0.003, 0.003, 'silver')                                                       # trigger
    tg.prism([(-0.020, 0.022), (0.022, 0.022), (0.042, -0.080), (0.006, -0.086), (-0.006, -0.050),
              (-0.012, -0.034), (-0.008, -0.010)], -0.0145, 0.0145, 'grip', side='furn')
    hg = C.Part('handguard')
    hp = [(-0.019, 0.040), (0.019, 0.040), (0.025, 0.054), (0.024, 0.080), (0.016, 0.092),
          (-0.016, 0.092), (-0.024, 0.080), (-0.025, 0.054)]
    hp2 = [(x * 0.9, y + (0.004 if y < 0.05 else 0)) for x, y in hp]
    hg.loft([(-0.300, hp2), (-0.192, hp)], 'furn', end='furn_dark')
    st = C.Part('stock')
    st.prism([(0.060, 0.098), (0.140, 0.096), (0.290, 0.090), (0.300, 0.086), (0.300, -0.036), (0.280, -0.036),
              (0.150, 0.034), (0.060, 0.046)], -0.017, 0.017, 'furn', side='furn_dark')
    st.box((-0.018, -0.038, 0.300), (0.018, 0.092, 0.310), 'furn_dark')
    mg = C.Part('magazine')
    front, rear = [], []
    for i in range(5):
        t = i / 4
        y = 0.046 - 0.166 * t
        dz = -0.050 * t * t
        front.append((-0.158 + dz, y)); rear.append((-0.122 + dz * 0.9, y + 0.004 * t))
    mg.prism(front + list(reversed(rear)), -0.0115, 0.0115, 'mag', side='steel')
    mg.box((-0.0135, -0.130, -0.212), (0.0135, -0.118, -0.164), 'steel')

    objs = {}
    for p in (rc, cc, tg, hg, st, mg):
        objs[p.name] = p.to_object(mats)
    C.assemble('smg_mp5', objs, {
        'muzzle': (0, BORE_Y, -0.365),
        'mag_well': (0, 0.008, -0.140),
        'rear_sight': (0, 0.126, 0.040),
        'front_sight': (0, 0.140, -0.294),
    })
    C.save_blend(out_dir, NAME)


if __name__ == '__main__':
    C.main(build, NAME)
