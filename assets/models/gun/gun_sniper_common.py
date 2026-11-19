"""Shared helpers for the gothic sniper remakes (bolt, antimat, marksman, rail): scope, scope rings, bolt handle.
Builds on gun_shotgun_common (HD albedo, satin walnut, glossy polymer, horn sweep)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_shotgun_common as S
K, C, M, G = S.K, S.C, S.M, S.G


def scope(part, y, z_oc, z_obj, r=0.0125, big=0.0215, rings=(0.30, 0.68), y_base=None, base_w=0.0140, segs=14, turrets=True):
    """Gothic scope on the sight line (axis at height y, z_oc rear/ocular end, z_obj front/objective end).
    Returns nothing; region 'tube' = engraved steel, brass rings/turrets, dark lens caps ('muzzle')."""
    L = z_oc - z_obj
    st = [(z_oc, r * 1.15), (z_oc - 0.012, r * 1.45), (z_oc - 0.034, r * 1.12), (z_oc - 0.052, r),
          (z_obj + 0.075, r), (z_obj + 0.050, r * 1.3), (z_obj + 0.026, big * 0.92), (z_obj + 0.006, big), (z_obj, big)]
    K.revolve(part, st, y, segs=segs, region='tube', cap_f='muzzle', cap_b='muzzle')
    for zz, rr in ((z_oc - 0.0125, r * 1.45), (z_obj + 0.0105, big), (z_oc - 0.056, r), (z_obj + 0.082, r)):
        K.revolve(part, [(zz + 0.0022, rr + 0.0012), (zz - 0.0022, rr + 0.0012)], y, segs=segs, region='brass', cap_f='brass', cap_b='brass')
    zm = z_obj + 0.5 * (L - 0.13) + 0.05
    if turrets:
        part.cyl((0, y + r - 0.001, zm), (0, y + r + 0.0095, zm), 0.0062, 10, 'brass', cap='brass')           # elevation turret
        part.cyl((r - 0.001, y, zm), (r + 0.0095, y, zm), 0.0056, 10, 'brass', cap='brass')                      # windage turret
    for f in rings:
        zc = z_oc - 0.07 - f * (L - 0.2)
        yb = y_base if y_base is not None else y - 0.030
        part.loft([(zc + 0.007, K.hexp(-base_w, base_w, yb, y + r + 0.0030, 0.0075)), (zc - 0.007, K.hexp(-base_w, base_w, yb, y + r + 0.0030, 0.0075))], 'steel', top='steel_top')
        part.box((-base_w - 0.0004, y - 0.002, zc - 0.0062), (base_w + 0.0004, y + 0.002, zc + 0.0062), 'brass')    # brass screw band across the ring
    return zm
