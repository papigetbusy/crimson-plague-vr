"""Shared helpers for the batch 3 gothic shotgun remakes (pump, double, combat, blunderbuss).

Same look as the batch 1 / 2 guns (blued steel + brass on the locked 1911 metal material,
dark walnut + bone on one non-metal material, one 256 px atlas). Adds the walnut painter
(promoted from build_drum_base.py), a recessed port painter and a few mesh shortcuts.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_gothic_common as K
C, M, G = K.C, K.M, K.G

K.PAL.update({'w_shadow': (10, 6, 4), 'w_dark': (26, 15, 8), 'w_mid': (42, 24, 13), 'w_light': (64, 38, 20), 'w_hi': (96, 62, 34)})
K.FURN.update({'wood', 'wood_end', 'bone_stock', 'bone_fore', 'bone_butt'})


def cham(z0, z1, y0, y1, c):
    return [(z0 + c, y0), (z1 - c, y0), (z1, y0 + c), (z1, y1 - c), (z1 - c, y1), (z0 + c, y1), (z0, y1 - c), (z0, y0 + c)]


def paint_wood(A, r, seed=71, end=False):
    x0, y0, x1, y1 = A.reg[r]
    for y in range(y0, y1):
        for x in range(x0, x1):
            n = K._vn(x * 0.18, y, 3, seed)
            g = math.sin((y - y0) * 0.62 + 6.0 * n + 0.04 * (x - x0))
            c = 'w_light' if g > 0.78 else 'w_mid' if g > 0.15 else 'w_dark' if g > -0.62 else 'w_shadow'
            if end:
                c = 'w_dark' if K._h(x, y, seed) > 0.3 else 'w_shadow'
            h = K._h(x, y, seed + 3)
            if h > 0.992:
                c = 'w_hi'
            elif h < 0.015:
                c = 'w_shadow'
            A.put(x, y, c)


def paint_port(A, r, seed=81):
    """Dark ejection port / loading window with a bright rim and a brass carrier hint."""
    x0, y0, x1, y1 = A.reg[r]
    A.steel(r, ('steel_dark', 'steel_mid', 'steel_light', 'sheen'), seed, grime=0.8, edge=False)
    for y in range(y0 + 3, y1 - 3):
        for x in range(x0 + 3, x1 - 3):
            A.put(x, y, 'recess' if K._vn(x, y, 5, seed) < 0.8 else 'steel_black')
    for x in range(x0 + 2, x1 - 2):
        A.put(x, y0 + 2, 'steel_edge'); A.put(x, y1 - 3, 'sheen')
    for y in range(y0 + 2, y1 - 2):
        A.put(x0 + 2, y, 'sheen'); A.put(x1 - 3, y, 'steel_edge')
    A.rect(x0 + 5, y0 + 4, x1 - 5, y0 + 7, 'brass_dark')           # carrier lip
    A.rect(x0 + 5, y0 + 4, x1 - 5, y0 + 5, 'brass_light')


def make_mats(name, tex, rough=0.55, spec=0.25):
    mats = C.make_materials(name, tex, furn='wood')
    mats[1].name = name + '_wood'
    b = mats[1].node_tree.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    return mats


def sight_pair(part, y_top, z_rear, z_front, y_base_rear, y_base_front, rear_w=0.0125, rear_len=0.018, bead_h=0.0016, post_in=0.0040):
    """Gothic notch-post rear (two brass-tipped posts) and a blade front with a brass bead."""
    part.box((-rear_w, y_base_rear, z_rear - rear_len * 0.5), (rear_w, y_top - 0.0016, z_rear + rear_len * 0.5), 'steel', top='steel_top')
    for sgn in (-1, 1):
        lo, hi = (post_in, rear_w - 0.0020) if sgn > 0 else (-(rear_w - 0.0020), -post_in)
        part.box((lo, y_top - 0.0016, z_rear - rear_len * 0.35), (hi, y_top, z_rear + rear_len * 0.35), 'steel', top='steel_top')
        part.box((lo, y_top - 0.0008, z_rear - rear_len * 0.35), (hi, y_top, z_rear + rear_len * 0.35), 'brass')
    part.box((-0.0030, y_base_front, z_front - 0.0030), (0.0030, y_top - bead_h, z_front + 0.0030), 'steel', top='steel_top')
    part.box((-0.0018, y_top - bead_h, z_front - 0.0018), (0.0018, y_top, z_front + 0.0018), 'brass')
