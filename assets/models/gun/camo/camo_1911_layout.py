"""Shared 1024 atlas layout for the 1911 camo tiers (pure python: imported by the Blender build and by the painter).
All rectangles are (x0, y0, x1, y1) in UV pixel space, origin bottom-left (y up), 1024 x 1024.
Every tier uses this exact layout, so tiers differ only in the albedo image."""
ATLAS = 1024
CELL = 128
PAD = 10          # inset of a mapped face inside its swatch cell (px)
RPAD = 4          # inset inside a special region (px)

SWATCH = {        # same cell grid as the original 256 px 1911 atlas (4x scale)
    'steel_dark': (0, 0), 'steel_mid': (1, 0), 'steel_light': (2, 0), 'steel_edge': (3, 0),
    'recess': (4, 0), 'silver': (5, 0), 'sheen': (6, 0), 'screw': (7, 0),
    'silver_hi': (6, 1), 'ivory': (7, 1), 'silver_dark': (6, 2), 'steel_black': (7, 2),
}
REGION = {
    'slideR': (12, 880, 1012, 1002),     # 1000 x 122, slide side wall, muzzle on the right
    'slideL': (12, 748, 1012, 870),      # muzzle on the left
    'frameR': (12, 664, 1012, 739),      # 1000 x 75
    'frameL': (12, 584, 1012, 659),
    'gripL': (12, 134, 215, 577),        # 203 x 443
    'gripR': (228, 134, 431, 577),
    'muzzle': (444, 134, 700, 390),      # 256 x 256
}
# projection boxes (game metres)
SLIDE_Z = (-0.176, 0.020)
SLIDE_Y = (0.04723803299665451, 0.07123803299665452)
FRAME_Z = (-0.160, 0.018)
FRAME_Y = (0.03423803299665451, 0.04763803299665451)
SERR_LEN = 0.030     # rear serration length (m)

# ---- EPIC / LEGENDARY additions (free block above the muzzle disc: x 440..1020, y 392..580) ----
SKULL_REGION = (448, 396, 576, 524)        # 128 x 128 planar face map for the skull muzzle brake
CELL64 = 64
CELLS64 = ['bk_steel', 'silver_p', 'gold', 'gold_dark', 'bone', 'bone_dark', 'violet', 'crimson', 'black', 'steel_hi']
def cell64_rect(name):
    i = CELLS64.index(name)
    col, row = i % 5, i // 5
    x0 = 600 + 72 * col; y0 = 396 + 72 * row
    return (x0, y0, x0 + CELL64, y0 + CELL64)
CELL_MATERIAL = {'bonetex': 'ivory', 'bone': 'ivory', 'bone_dark': 'ivory', 'violet': 'energy', 'crimson': 'energy'}
