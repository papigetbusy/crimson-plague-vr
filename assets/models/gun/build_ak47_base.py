"""Crimson Plague VR - rifle_ak47_base (blued steel, weathered wood).

Original low-poly PS2 / Snake Eater style AK-pattern rifle. Chunky, readable
shapes; serrations, ribs, grain and wear are painted into one 256 px atlas.
Locked look from pistol_1911_base: steel metallic 1 / roughness 0.30, wood
on its own non-metal material sharing the atlas.

Build (repo root):
  blender -b --python assets/models/gun/build_ak47_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/rifle_ak47_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/rifle_ak47_base.glb --type gun --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_ak47_base.py -- --render-glb assets/models/gun/rifle_ak47_base.glb \
    --render-dir /workspace/guns_previews --small-dir assets/models/gun/previews

Meshes: receiver (+ barrel, sights, gas tube, trigger group), bolt_carrier
(with charging handle), handguard (wood), stock (wood + pistol grip),
magazine (under mag_well). Empties: muzzle, mag_well, rear_sight, front_sight.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_lowpoly_common as C

NAME = 'rifle_ak47_base'
BORE_Y = 0.086


def build(out_dir):
    C.M.reset_scene()
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    C.paint_atlas(tex, furn='wood', seed=11)
    mats = C.make_materials(NAME, tex, furn='wood')

    # --- receiver: stamped box with a rounded dust-cover top -----------------
    rc = C.Part('receiver')
    w = 0.017
    prof = [(-w, 0.040), (w, 0.040), (w, 0.094), (w - 0.004, 0.102), (-w + 0.004, 0.102), (-w, 0.094)]
    rc.loft([(-0.215, prof), (0.090, prof)], 'steel', top='steel_top')
    dust = [(-0.015, 0.100), (0.015, 0.100), (0.015, 0.106), (0.009, 0.113), (-0.009, 0.113), (-0.015, 0.106)]
    rc.loft([(-0.150, dust), (0.098, dust)], 'ribs', top='steel_top', end='steel')
    rc.box((-0.016, 0.060, -0.260), (0.016, 0.112, -0.215), 'steel', top='steel_top')     # rear sight block
    rc.box((-0.012, 0.112, -0.252), (0.012, 0.121, -0.212), 'steel_top')                 # sight leaf
    rc.cyl((0, BORE_Y, -0.255), (0, BORE_Y, -0.595), 0.0085, 8, 'barrel', cap='steel')
    rc.cyl((0, BORE_Y, -0.595), (0, BORE_Y, -0.630), 0.0115, 8, 'barrel', cap='muzzle', cap0='steel')
    rc.box((-0.013, 0.074, -0.452), (0.013, 0.128, -0.425), 'steel', top='steel_top')     # gas block
    rc.cyl((0, 0.115, -0.395), (0, 0.115, -0.430), 0.0095, 6, 'barrel')                   # exposed gas tube
    rc.box((-0.011, 0.074, -0.565), (0.011, 0.098, -0.540), 'steel')                      # front sight base
    rc.prism([(-0.565, 0.098), (-0.540, 0.098), (-0.546, 0.132), (-0.559, 0.132)], -0.010, 0.010, 'steel', top='steel_top')
    rc.box((-0.004, 0.0, -0.090), (0.004, 0.040, -0.080), 'steel')                        # guard front post
    rc.box((-0.006, -0.012, -0.090), (0.006, -0.003, 0.002), 'steel')                     # guard bottom bar
    rc.prism([(-0.040, 0.040), (-0.030, 0.040), (-0.034, 0.012), (-0.046, -0.002), (-0.048, 0.004), (-0.040, 0.020)],
             -0.0035, 0.0035, 'silver')                                                   # trigger
    rc.box((0.017, 0.076, -0.180), (0.021, 0.084, 0.030), 'steel_top')                    # selector lever (right)
    rc.box((-0.018, 0.000, 0.088), (0.018, 0.100, 0.100), 'steel')                        # stock tang
    rc.box((-0.014, 0.040, -0.136), (0.014, 0.046, -0.080), 'recess')                     # mag well lip
    # --- bolt carrier + charging handle (right side, rides in the port) ------
    bc = C.Part('bolt_carrier')
    bc.box((0.012, 0.084, -0.110), (0.0185, 0.096, 0.010), 'steel_top')
    bc.cyl((0.018, 0.090, -0.050), (0.040, 0.090, -0.050), 0.0055, 6, 'barrel', cap='silver')
    # --- wood handguards -----------------------------------------------------
    hg = C.Part('handguard')
    lo = [(-0.021, 0.064), (0.021, 0.064), (0.023, 0.084), (0.018, 0.103), (-0.018, 0.103), (-0.023, 0.084)]
    lo2 = [(x * 0.92, y + (0.002 if y < 0.07 else 0)) for x, y in lo]
    hg.loft([(-0.390, lo2), (-0.262, lo)], 'furn', end='furn_end')
    up = [(-0.014, 0.104), (0.014, 0.104), (0.016, 0.114), (0.009, 0.124), (-0.009, 0.124), (-0.016, 0.114)]
    hg.loft([(-0.395, up), (-0.262, up)], 'furn', end='furn_end')
    hg.box((-0.024, 0.062, -0.270), (0.024, 0.106, -0.259), 'steel', top='steel_top')     # rear retainer
    hg.box((-0.022, 0.062, -0.402), (0.022, 0.104, -0.390), 'steel', top='steel_top')     # front band
    # --- stock and pistol grip (wood) ---------------------------------------
    st = C.Part('stock')
    st.prism([(0.098, 0.100), (0.330, 0.079), (0.366, 0.081), (0.366, -0.050), (0.338, -0.048),
              (0.200, 0.008), (0.120, 0.032), (0.098, 0.040)], -0.019, 0.019, 'furn', side='furn_end', top='furn')
    st.box((-0.020, -0.052, 0.366), (0.020, 0.083, 0.374), 'steel')                       # butt plate
    st.prism([(-0.024, 0.041), (0.020, 0.041), (0.044, -0.076), (0.004, -0.082), (-0.010, -0.040),
              (-0.016, -0.012)], -0.014, 0.014, 'grip', side='furn')
    # --- curved magazine ------------------------------------------------------
    mg = C.Part('magazine')
    import math
    front, rear = [], []
    for i in range(6):
        t = i / 5
        a = math.radians(4 + 30 * t)
        y = 0.046 - 0.170 * math.sin(math.radians(80 * t)) / math.sin(math.radians(80))
        zc = -0.108 - 0.080 * t * t
        hw = 0.028 + 0.004 * t
        front.append((zc - hw * math.cos(a), y - hw * math.sin(a) * 0.4))
        rear.append((zc + hw * math.cos(a), y + hw * math.sin(a) * 0.4))
    mg.prism(front + list(reversed(rear)), -0.013, 0.013, 'mag', side='steel')
    mg.box((-0.015, -0.134, -0.222), (0.015, -0.122, -0.156), 'steel')                    # floor plate

    objs = {}
    for p in (rc, bc, hg, st, mg):
        objs[p.name] = p.to_object(mats)
    C.assemble('rifle_ak47', objs, {
        'muzzle': (0, BORE_Y, -0.630),
        'mag_well': (0, 0.040, -0.108),
        'rear_sight': (0, 0.121, -0.232),
        'front_sight': (0, 0.132, -0.552),
    })
    C.save_blend(out_dir, NAME)


if __name__ == '__main__':
    C.main(build, NAME)
