"""Crimson Plague VR - smg_uzi_base (blued steel, worn black polymer).

Original low-poly PS2 / Snake Eater style Uzi-pattern SMG (stock folded off;
only the rear hinge block is modelled). The magazine loads through the
pistol grip. Ribs, stipple and wear are painted into one 256 px atlas.
Locked look from pistol_1911_base: steel metallic 1 / roughness 0.30;
polymer furniture on its own non-metal material.

Build (repo root):
  blender -b --python assets/models/gun/build_uzi_base.py -- --out-dir assets/models/gun
Export:
  blender -b assets/models/gun/smg_uzi_base.blend --python tools/blender/export_lowpoly.py -- \
    --out assets/models/gun/smg_uzi_base.glb --type gun --allow-multi-material
Previews (from the GLB):
  blender -b --python assets/models/gun/build_uzi_base.py -- --render-glb assets/models/gun/smg_uzi_base.glb \
    --render-dir /workspace/guns_previews --small-dir assets/models/gun/previews

Meshes: receiver (+ barrel, sights, trigger guard, lower frame), top_cover
(with the cocking knob / bolt), grip (polymer + grip safety), handguard,
magazine (under mag_well). Empties: muzzle, mag_well, rear_sight, front_sight.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_lowpoly_common as C

NAME = 'smg_uzi_base'
BORE_Y = 0.068


def build(out_dir):
    C.M.reset_scene()
    tex = os.path.join(out_dir, NAME + '_albedo.png')
    C.paint_atlas(tex, furn='polymer', seed=53, furn_grime=0.84)
    mats = C.make_materials(NAME, tex, furn='polymer')

    rc = C.Part('receiver')
    w = 0.020
    prof = [(-w + 0.003, 0.035), (w - 0.003, 0.035), (w, 0.040), (w, 0.092), (-w, 0.092), (-w, 0.040)]
    rc.loft([(-0.170, prof), (0.110, prof)], 'steel', top='steel_top')
    rc.box((-0.012, 0.092, -0.166), (0.012, 0.118, -0.150), 'steel', top='steel_top')     # front sight ears
    rc.box((-0.010, 0.092, 0.090), (0.010, 0.112, 0.105), 'steel', top='steel_top')       # rear sight
    rc.cyl((0, BORE_Y, -0.170), (0, BORE_Y, -0.186), 0.0165, 12, 'ribs', cap='steel')      # barrel nut
    rc.cyl((0, BORE_Y, -0.186), (0, BORE_Y, -0.226), 0.0080, 10, 'barrel', cap='muzzle')
    rc.box((-0.016, 0.022, -0.092), (0.016, 0.035, 0.060), 'steel')                       # lower frame
    rc.box((-0.006, -0.014, -0.082), (0.006, -0.005, -0.018), 'steel')                    # guard bar
    rc.box((-0.005, -0.005, -0.084), (0.005, 0.022, -0.075), 'steel')
    rc.prism([(-0.046, 0.022), (-0.038, 0.022), (-0.041, 0.004), (-0.051, -0.006), (-0.053, 0.000), (-0.046, 0.012)],
             -0.003, 0.003, 'silver')                                                       # trigger
    rc.box((-0.016, 0.042, 0.110), (0.016, 0.084, 0.126), 'steel')                        # stock hinge block
    rc.box((-0.023, 0.050, 0.020), (-0.020, 0.060, 0.040), 'silver')                      # selector (left)
    for sx in (-1, 1):                                                                    # stamped side ribs
        rc.box((sx * 0.020 - 0.0015, 0.070, -0.140), (sx * 0.020 + 0.0015, 0.078, 0.080), 'steel_top')
    tc = C.Part('top_cover')
    tp = [(-0.0185, 0.092), (0.0185, 0.092), (0.0185, 0.099), (0.013, 0.105), (-0.013, 0.105), (-0.0185, 0.099)]
    tc.loft([(-0.135, tp), (0.088, tp)], 'steel', top='ribs')
    tc.cyl((0, 0.104, -0.066), (0, 0.117, -0.066), 0.0075, 8, 'barrel', cap='silver')     # cocking knob
    gp = C.Part('grip')
    gp.prism([(-0.022, 0.024), (0.030, 0.024), (0.038, -0.020), (0.039, -0.060), (0.037, -0.090), (-0.017, -0.090),
              (-0.021, -0.040)], -0.0175, 0.0175, 'grip', side='furn')
    gp.box((-0.010, -0.052, 0.031), (0.010, 0.020, 0.040), 'steel')                       # grip safety
    gp.box((-0.0185, -0.096, -0.019), (0.0185, -0.088, 0.039), 'steel')                   # well heel
    hg = C.Part('handguard')
    hg.box((-0.023, 0.018, -0.166), (0.023, 0.046, -0.098), 'furn', top='furn_dark')
    mg = C.Part('magazine')
    mg.prism([(-0.010, 0.030), (0.020, 0.030), (0.027, -0.170), (-0.003, -0.170)], -0.0125, 0.0125, 'mag', side='steel')
    mg.box((-0.0145, -0.180, -0.006), (0.0145, -0.168, 0.030), 'steel')

    objs = {}
    for p in (rc, tc, gp, hg, mg):
        objs[p.name] = p.to_object(mats)
    C.assemble('smg_uzi', objs, {
        'muzzle': (0, BORE_Y, -0.226),
        'mag_well': (0, -0.096, 0.010),
        'rear_sight': (0, 0.112, 0.0975),
        'front_sight': (0, 0.118, -0.158),
    })
    C.save_blend(out_dir, NAME)


if __name__ == '__main__':
    C.main(build, NAME)
