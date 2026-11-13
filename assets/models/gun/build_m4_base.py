"""Crimson Plague VR - rifle_m4_base (blued steel, worn black polymer).

Original low-poly PS2 / Snake Eater style M4-pattern carbine. Chunky,
readable shapes; rail slots, vents, stipple and wear are painted into one
256 px atlas. Locked look from pistol_1911_base: steel metallic 1 /
roughness 0.30; polymer furniture on its own non-metal material.

Build (repo root):
  blender -b --python assets/models/gun/build_m4_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/rifle_m4_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/rifle_m4_base.glb --type gun --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_m4_base.py -- --render-glb assets/models/gun/rifle_m4_base.glb \
    --render-dir /workspace/guns_previews --small-dir assets/models/gun/previews

Meshes: upper (+ barrel, sights, rail), lower (+ pistol grip, buffer tube,
trigger group), charging_handle, handguard, stock, magazine (under mag_well).
Empties: muzzle, mag_well, rear_sight, front_sight, optic_mount.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_lowpoly_common as C

NAME = 'rifle_m4_base'
BORE_Y = 0.095


def build(out_dir):
    C.M.reset_scene()
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    C.paint_atlas(tex, furn='polymer', seed=23)
    mats = C.make_materials(NAME, tex, furn='polymer')

    up = C.Part('upper')
    prof = [(-0.013, 0.072), (0.013, 0.072), (0.015, 0.076), (0.015, 0.108), (0.012, 0.112),
            (-0.012, 0.112), (-0.015, 0.108), (-0.015, 0.076)]
    up.loft([(-0.105, prof), (0.105, prof)], 'steel', top='steel_top')
    up.box((-0.011, 0.112, -0.105), (0.011, 0.121, 0.105), 'rail', top='rail')
    up.cyl((0, BORE_Y, -0.105), (0, BORE_Y, -0.400), 0.0075, 8, 'barrel')
    up.cyl((0, BORE_Y, -0.400), (0, BORE_Y, -0.438), 0.0105, 8, 'barrel', cap='muzzle')
    up.box((-0.011, 0.083, -0.348), (0.011, 0.105, -0.318), 'steel', top='steel_top')
    up.prism([(-0.322, 0.105), (-0.345, 0.105), (-0.338, 0.143), (-0.329, 0.143)], -0.008, 0.008, 'steel', top='steel_top')
    up.box((-0.010, 0.121, 0.078), (0.010, 0.140, 0.100), 'steel', top='steel_top')       # flip-up rear sight
    up.cyl((0.013, 0.100, 0.048), (0.026, 0.093, 0.074), 0.0058, 6, 'barrel', cap='silver')  # forward assist
    lo = C.Part('lower')
    lo.box((-0.015, 0.040, -0.112), (0.015, 0.072, 0.072), 'steel')
    lo.box((-0.016, 0.008, -0.118), (0.016, 0.040, -0.056), 'steel')                      # flared mag well
    lo.box((-0.006, -0.006, -0.056), (0.006, 0.002, 0.004), 'steel')                      # guard bar
    lo.box((-0.004, 0.002, -0.058), (0.004, 0.040, -0.050), 'steel')
    lo.prism([(-0.030, 0.040), (-0.022, 0.040), (-0.025, 0.014), (-0.036, 0.002), (-0.038, 0.008), (-0.031, 0.022)],
             -0.003, 0.003, 'silver')                                                       # trigger
    lo.box((-0.019, 0.054, -0.010), (-0.015, 0.064, 0.012), 'steel_top')                  # selector (left)
    lo.cyl((0, BORE_Y, 0.072), (0, BORE_Y, 0.255), 0.0150, 8, 'barrel')                  # buffer tube
    lo.prism([(-0.022, 0.040), (0.018, 0.040), (0.040, -0.074), (0.004, -0.080), (-0.012, -0.032)],
             -0.0135, 0.0135, 'grip', side='furn')
    ch = C.Part('charging_handle')
    ch.box((-0.012, 0.112, 0.098), (0.012, 0.119, 0.124), 'steel_top')
    ch.box((-0.022, 0.111, 0.124), (0.022, 0.121, 0.134), 'steel', top='steel_top')
    hg = C.Part('handguard')
    import math
    def octa(r, sq=1.0):
        return [(r * math.cos(math.radians(22.5 + 45 * i)), BORE_Y + sq * r * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
    hg.loft([(-0.285, octa(0.0235)), (-0.120, octa(0.0260))], 'vents', end='furn_dark')
    hg.cyl((0, BORE_Y, -0.105), (0, BORE_Y, -0.120), 0.029, 8, 'barrel')                   # delta ring
    hg.cyl((0, BORE_Y, -0.285), (0, BORE_Y, -0.292), 0.022, 8, 'barrel')                   # handguard cap
    st = C.Part('stock')
    st.prism([(0.150, 0.118), (0.300, 0.123), (0.306, 0.120), (0.306, -0.015), (0.282, -0.015),
              (0.205, 0.062), (0.150, 0.076)], -0.020, 0.020, 'furn', side='furn_dark')
    st.box((-0.021, -0.017, 0.306), (0.021, 0.124, 0.316), 'furn_dark')                   # butt pad
    mg = C.Part('magazine')
    front = [(-0.113, 0.046), (-0.118, -0.010), (-0.128, -0.065), (-0.142, -0.112)]
    rear = [(-0.061, 0.046), (-0.064, -0.010), (-0.073, -0.065), (-0.086, -0.108)]
    mg.prism(front + list(reversed(rear)), -0.0115, 0.0115, 'mag', side='steel')
    mg.box((-0.0135, -0.122, -0.146), (0.0135, -0.110, -0.082), 'steel')

    objs = {}
    for p in (up, lo, ch, hg, st, mg):
        objs[p.name] = p.to_object(mats)
    C.assemble('rifle_m4', objs, {
        'muzzle': (0, BORE_Y, -0.438),
        'mag_well': (0, 0.008, -0.087),
        'rear_sight': (0, 0.140, 0.089),
        'front_sight': (0, 0.143, -0.3335),
        'optic_mount': (0, 0.121, 0.0),
    })
    C.save_blend(out_dir, NAME)


if __name__ == '__main__':
    C.main(build, NAME)
