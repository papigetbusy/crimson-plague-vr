"""Painter for the EPIC / LEGENDARY atlases (extends camo_1911_paint.py; same 1024 layout, plus the new-part cells + skull face map)."""
import math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camo_1911_layout as LY
import camo_1911_paint as P
from camo_1911_paint import C, Ink, smooth, fbm, noise, over, dilate, blur, shift, vramp, lerp, BRASS, PAL

PAL['epic'] = dict(shadow=C(9, 10, 18), base=C(17, 20, 36), hi=C(36, 42, 74), streak=C(96, 108, 160), edge=C(170, 180, 200),
                   black=C(6, 7, 12), recess=C(5, 6, 9), silver=C(176, 182, 192), silver_hi=C(238, 241, 247), silver_dark=C(104, 108, 120))
PAL['legendary'] = dict(shadow=C(10, 11, 16), base=C(19, 21, 31), hi=C(42, 46, 62), streak=C(116, 122, 142), edge=C(180, 184, 196),
                        black=C(6, 6, 9), recess=C(5, 5, 8), silver=C(176, 182, 192), silver_hi=C(238, 241, 247), silver_dark=C(104, 108, 120))
GOLD = dict(shadow=C(78, 52, 14), base=C(184, 140, 46), hi=C(238, 204, 108), streak=C(255, 238, 176))
GOLD_DARK = dict(shadow=C(40, 26, 8), base=C(112, 80, 26), hi=C(176, 134, 58), streak=C(214, 176, 96))
VIOLET = C(168, 96, 255); VIOLET_HOT = C(236, 200, 255); VIOLET_DEEP = C(70, 20, 150)
CRIMSON = C(255, 22, 40); CRIMSON_HOT = C(255, 150, 130); CRIMSON_DEEP = C(110, 0, 12)
BONE = dict(shadow=C(104, 80, 52), base=C(176, 148, 102), hi=C(210, 186, 140), streak=C(232, 214, 172))
BONE_DARK = dict(shadow=C(36, 26, 18), base=C(86, 66, 44), hi=C(130, 106, 76), streak=C(160, 134, 98))

def ramp_cell(d, T=64):
    return np.repeat(vramp(T, d['shadow'], d['base'], d['hi'], d['streak']), T, axis=1).astype(np.float32)

def flat_glow(deep, mid, hot, T=64):
    v = np.linspace(1, 0, T, dtype=np.float32)[:, None, None]
    img = np.ones((T, T, 1), np.float32) * (deep * (1 - smooth(0, 0.4, v)) + mid * smooth(0, 0.4, v)) 
    img = img * (1 - 0.5 * smooth(0.5, 1.0, v)) + hot * 0.5 * smooth(0.5, 1.0, v)
    return np.repeat(img, T, axis=1) if img.shape[1] == 1 else img

def paint_cells64(tier, atlas):
    P_ = PAL[tier]
    cells = {
        'bk_steel': ramp_cell(dict(shadow=P_['shadow'], base=P_['base'], hi=P_['hi'], streak=P_['streak'])),
        'silver_p': ramp_cell(dict(shadow=P_['silver_dark'], base=P_['silver'], hi=C(222, 226, 232), streak=P_['silver_hi'])),
        'gold': ramp_cell(GOLD), 'gold_dark': ramp_cell(GOLD_DARK),
        'bone': ramp_cell(BONE), 'bone_dark': ramp_cell(BONE_DARK),
        'violet': flat_glow(VIOLET_DEEP, VIOLET, VIOLET_HOT), 'crimson': flat_glow(CRIMSON_DEEP, CRIMSON, CRIMSON_HOT),
        'black': ramp_cell(dict(shadow=C(4, 4, 6), base=C(9, 10, 14), hi=C(18, 20, 28), streak=C(40, 44, 58))),
        'steel_hi': ramp_cell(dict(shadow=P_['hi'], base=P_['streak'], hi=P_['edge'], streak=P_['silver_hi'])),
    }
    if tier == 'legendary': cells['crimson'] = np.tile(C(196, 6, 22), (64, 64, 1)).astype(np.float32)
    for name, img in cells.items():
        x0, y0, x1, y1 = LY.cell64_rect(name)
        atlas[y0:y1, x0:x1] = img[::-1]
        # extend a 4 px gutter so Linear filtering never bleeds a neighbour
        atlas[y0 - 4:y0, x0:x1] = img[::-1][0:1]; atlas[y1:y1 + 4, x0:x1] = img[::-1][-1:]
        atlas[y0:y1, x0 - 4:x0] = img[::-1][:, 0:1]; atlas[y0:y1, x1:x1 + 4] = img[::-1][:, -1:]

def skull_face(tier, S=128):
    """planar face map of the skull brake: u=0.5+x/0.0270, v=0.5+(y-yc)/0.0300. returns float image (rows top-first)."""
    sx, sy, cc = 0.0290, 0.0300, 0.0028
    px = lambda x: (0.5 + x / sx) * S
    py = lambda y: (1 - (0.5 + y / sy)) * S             # y relative to the outline centre -> row from top
    # y coords below are relative to the bore axis; convert (bore->centre offset is -cc)
    P_ = PAL[tier]
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    X = ((xx + 0.5) / S - 0.5) * sx
    Y = (0.5 - (yy + 0.5) / S) * sy              # relative to the outline centre; bore centre is at -cc
    v = np.clip(0.5 - (yy / S - 0.5), 0, 1)
    img = np.repeat(vramp(S, P_['silver_dark'] * 0.50, P_['silver'] * 0.58, C(170, 176, 188), P_['silver_hi'] * 0.92), S, axis=1).astype(np.float32)
    # aged darkening in the recesses (edges of the face map)
    r = np.hypot(X / 0.0120, (Y - 0.001) / 0.0150)
    img = img * (1 - 0.35 * smooth(0.75, 1.15, r))[..., None]
    # eye sockets: dark with a rim light (eye orbs are emissive geometry in front)
    # bore-relative y of eyes is +0.0066 -> relative to outline centre = 0.0066 - cc
    for ex, ey in ((-0.0058, 0.0078), (0.0058, 0.0078)):
        d = np.hypot((X - ex) / 0.0040, (Y - (ey - cc)) / 0.0036)
        img = img * (1 - 0.94 * smooth(1.10, 0.60, d))[..., None]
        img = P.over(img, P_['silver_hi'], np.exp(-((d - 1.12) / 0.07) ** 2) * 0.35)
    # nasal cavity / bore surround dark
    d = np.hypot(X / 0.0050, (Y + cc) / 0.0050)
    img = img * (1 - 0.85 * smooth(1.1, 0.7, d))[..., None]
    # brow + cheek hairline etching
    ink = Ink(S, S)
    for sgn in (-1, 1):
        ink.line([(px(sgn * 0.0020), py(0.0080 + 0.0030 - cc)), (px(sgn * 0.0070), py(0.0105 - cc + 0.0012)), (px(sgn * 0.0094), py(0.0060 - cc))], 0.9)
        ink.line([(px(sgn * 0.0094), py(0.0010 - cc)), (px(sgn * 0.0082), py(-0.0040 - cc)), (px(sgn * 0.0066), py(-0.0066 - cc))], 0.8)
    ink.line([(px(-0.0050), py(-0.0066 - cc)), (px(0.0050), py(-0.0066 - cc))], 0.7)    # jaw seam above the teeth
    m = ink.mask()
    img = P.over(img, C(10, 10, 14), blur(m, 0.6) * 0.8)
    return img

def bone_aged(S=128):
    """aged ivory/bone swatch (v up): warm yellowed, fine grain along u, dark crevices at the top (under the slide) and bottom, hairline cracks"""
    yy = np.linspace(0, 1, S, dtype=np.float32)[:, None] * np.ones((1, S), np.float32)
    base = np.zeros((S, S, 3), np.float32) + C(178, 150, 104)
    gr = noise(S, S, 36, 2, 5) * 0.6 + noise(S, S, 6, 1, 6) * 0.5
    base *= (1 + 0.09 * gr)[..., None]
    base = P.over(base, C(206, 182, 134), 0.35 * smooth(0.2, 1.4, fbm(S, S, 30, 22, 7, 3)))
    base = P.over(base, C(132, 100, 62), 0.40 * smooth(0.3, 1.5, fbm(S, S, 22, 16, 8, 3)))
    cr = Ink(S, S); rng = np.random.default_rng(11)
    for _ in range(14):
        x, y = rng.uniform(0, S), rng.uniform(0.15, 0.85) * S; pts = [(x, y)]
        for k in range(4): x += rng.normal(5, 3); y += rng.normal(0, 3); pts.append((x, y))
        cr.line(pts, 0.7)
    base = P.over(base, C(46, 32, 20), cr.mask() * 0.7)
    shade = 0.25 + 0.75 * smooth(0.0, 0.30, yy) * smooth(1.0, 0.72, yy)
    return np.clip(base * shade[..., None], 0, 255)

def paint(tier):
    P_ = PAL[tier]
    atlas = np.zeros((LY.ATLAS, LY.ATLAS, 3), np.float32) + P_['recess']
    for name, (tx, ty) in LY.SWATCH.items():
        cell = P.paint_cell(tier, name)
        atlas[ty * LY.CELL:(ty + 1) * LY.CELL, tx * LY.CELL:(tx + 1) * LY.CELL] = cell[::-1]
    paint_cells64(tier, atlas)
    sx0, sy0, sx1, sy1 = LY.SKULL_REGION
    atlas[sy0:sy1, sx0:sx1] = (bone_aged(sx1 - sx0) if tier == 'legendary' else skull_face(tier, sx1 - sx0))[::-1]
    return atlas


# ------------------------------------------------------------------ region painters
def glow_line(img, ink_mask, deep, mid, hot):
    img = P.over(img, deep, blur(ink_mask, 2.2) * 0.55)
    img = P.over(img, mid, np.clip(ink_mask * 1.2, 0, 1))
    img = P.over(img, hot, np.clip(ink_mask - blur(ink_mask, 0.9) * 0.35, 0, 1) ** 2 * 0.8)
    return img

def slide_panel_hi(tier, side, w, h):
    R_side = side == 'R'
    img = P.steel_panel(tier, w, h, 3 if R_side else 4)
    ser = (0.0, 0.153) if R_side else (0.847, 1.0)
    img = P.apply_serr(img, tier, w, h, *ser)
    art = P.slide_art_rare(side, w, h)
    if tier == 'epic':
        img = P.silver_inlay(img, art, tier, h)
        # violet accent rule + gem
        ink = Ink(w, h)
        xa, xb = (0.168 * w, 0.975 * w) if R_side else (0.025 * w, 0.832 * w)
        ink.line([(xa, 0.8825 * h), (xb, 0.8825 * h)], 1.3)
        medx = 0.71 * w if R_side else 0.43 * w
        ink.circle(medx, 0.505 * h, 3.6)
        img = glow_line(img, ink.mask(), VIOLET_DEEP, VIOLET, VIOLET_HOT)
    return img

def frame_panel_hi(tier, side, w, h):
    R_side = side == 'R'
    img = P.steel_panel(tier, w, h, 7 if R_side else 8)
    if tier == 'epic':
        img = P.silver_inlay(img, P.frame_art_rare(side, w, h), tier, h)
        ink = Ink(w, h); ink.line([(0.02 * w, 0.5 * h), (0.0 * w + 8, 0.5 * h)], 0.1)
    return img

def grip_panel_epic(flipx):
    w, h = P.GW, P.GH
    seed = 23
    base = np.tile(C(22, 19, 27), (h, w, 1)).astype(np.float32)
    gr = noise(h, w, 80, 3, seed) * 0.6 + noise(h, w, 20, 2, seed + 1) * 0.4
    base *= (1 + 0.16 * gr)[..., None]
    base = P.over(base, C(46, 38, 60), 0.30 * smooth(0.5, 1.8, fbm(h, w, 50, 30, seed + 2, 3)))
    img = P.edge_dark(base, 0.45, 8)
    art = P.grip_art_rare(w, h)
    img = P.silver_inlay(img, art, 'epic', h, groove=1.0)
    img = P.screw_boss(img, w / 2, 0.29 * h, 'rare')
    # violet pin-glints on the border corners
    ink = Ink(w, h)
    for (a, b) in ((13, 13), (w - 13, 13), (13, h - 13), (w - 13, h - 13)): ink.circle(a, b, 2.4)
    img = glow_line(img, ink.mask(), VIOLET_DEEP, VIOLET, VIOLET_HOT)
    if flipx: img = img[:, ::-1]
    return img

def muzzle_disc_hi(tier, S=256):
    img = P.muzzle_disc('rare', S)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    r = np.hypot(xx - (S - 1) / 2, yy - (S - 1) / 2) / (S / 2 - 4)
    if tier == 'epic':
        img = P.over(img, VIOLET, np.exp(-((r - 0.575) / 0.014) ** 2) * 0.95)
    return img

def paint_full(tier):
    atlas = paint(tier)
    x0, y0, x1, y1 = LY.REGION['slideR']; wi, hi_ = (x1 - x0) - 8, (y1 - y0) - 8
    P.put(atlas, 'slideR', slide_panel_hi(tier, 'R', wi, hi_)); P.put(atlas, 'slideL', slide_panel_hi(tier, 'L', wi, hi_))
    x0, y0, x1, y1 = LY.REGION['frameR']; wi, hi_ = (x1 - x0) - 8, (y1 - y0) - 8
    P.put(atlas, 'frameR', frame_panel_hi(tier, 'R', wi, hi_)); P.put(atlas, 'frameL', frame_panel_hi(tier, 'L', wi, hi_))
    for nm, fl in (('gripL', False), ('gripR', True)):
        g = grip_panel_epic(fl) if tier == 'epic' else grip_panel_legendary(fl)
        x0, y0, x1, y1 = LY.REGION[nm]; p = LY.RPAD
        atlas[y0:y1, x0:x1] = np.pad(g, ((p, p), (p, p), (0, 0)), mode='edge')
    x0, y0, x1, y1 = LY.REGION['muzzle']
    atlas[y0:y1, x0:x1] = muzzle_disc_hi(tier, x1 - x0)
    out = np.clip(atlas + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(out[::-1])


# ---------------------------------------------------------------- LEGENDARY painters
import camo_1911_runes as RN

def metal_inlay(img, mask, tier, h, ramp, groove=1.3):
    P_ = PAL[tier]; hh, w = mask.shape
    g = np.clip(dilate(mask, groove) - mask, 0, 1)
    img = P.over(img, P_['black'], np.clip(g * 1.3, 0, 1) * 0.9)
    fillc = np.repeat(vramp(hh, ramp['shadow'], ramp['base'], ramp['hi'], ramp['streak']), w, axis=1)
    img = img * (1 - mask[..., None]) + fillc * mask[..., None]
    up = np.clip(mask - shift(mask, 0, 1), 0, 1); dn = np.clip(mask - shift(mask, 0, -1), 0, 1)
    img = P.over(img, ramp['streak'], up * 0.8); img = P.over(img, ramp['shadow'] * 0.8, dn * 0.5)
    return img

def slide_art_legendary(side, w, h):
    ink = Ink(w, h); R_side = side == 'R'
    xa, xb = (0.168 * w, 0.975 * w) if R_side else (0.025 * w, 0.832 * w)
    for y in (0.90, 0.935): ink.line([(xa, y * h), (xb, y * h)], 1.5)
    if not R_side:
        for y in (0.07, 0.10): ink.line([(xa, y * h), (xb, y * h)], 1.5)
    xd = 0.153 * w + 6 if R_side else 0.847 * w - 6
    ink.line([(xd, 0.09 * h), (xd, 0.91 * h)], 1.4); ink.line([(xd + (5 if R_side else -5), 0.12 * h), (xd + (5 if R_side else -5), 0.88 * h)], 1.0)
    return ink.mask()

def rune_channel(side, w, h):
    """dark engraved channel + painted crimson fallback line under the emissive ribbons (sigil polylines)"""
    chan = Ink(w, h); core = Ink(w, h)
    for pl in RN.polylines(side):
        chan.line(pl, RN.STROKE_PX + 4.5); core.line(pl, RN.STROKE_PX)
    return chan.mask(), core.mask()

def slide_panel_legendary(side, w, h):
    R_side = side == 'R'
    img = P.steel_panel('legendary', w, h, 3 if R_side else 4)
    ser = (0.0, 0.153) if R_side else (0.847, 1.0)
    img = P.apply_serr(img, 'legendary', w, h, *ser)
    img = metal_inlay(img, slide_art_legendary(side, w, h), 'legendary', h, GOLD)
    chan, core = rune_channel(side, w, h)
    img = P.over(img, C(4, 3, 5), chan * 0.92)
    img = P.over(img, CRIMSON, core)
    return img

def frame_panel_legendary(side, w, h):
    img = P.steel_panel('legendary', w, h, 7 if side == 'R' else 8)
    ink = Ink(w, h)
    for y in (0.10, 0.90): ink.line([(0.02 * w, y * h), (0.98 * w, y * h)], 1.4)
    return metal_inlay(img, ink.mask(), 'legendary', h, GOLD)

def grip_art_legendary(w, h):
    ink = Ink(w, h); cx = w / 2; sy = 0.29 * h
    spr = 0.25 * h
    for half, base, apex, wd in ((88, h - 13, 12, 1.7), (76, h - 19, 24, 0.9)):
        ink.line(P.lancet(cx, base, spr + (12 - apex) * 0.2 + 8, apex, half), wd)
    ink.line([(cx - 88, h - 13), (cx + 88, h - 13)], 1.7); ink.line([(cx - 76, h - 19), (cx + 76, h - 19)], 0.9)
    P.rose_window(ink, cx, sy + 8, 50, 1.3, 9.5)
    P.cross_fleury(ink, cx, 0.64 * h, 70, 2.8)
    P.quatrefoil(ink, cx, 0.50 * h, 16, 1.3)
    for sg in (-1, 1):
        path = P.scroll_S(ink, cx + sg * 40, 0.90 * h - 6, 15, flip=(sg > 0), wmax=2.1, wmin=0.9)
        P.decorate_scroll(ink, path, 8, 9, sg)
    ink.circle(cx, 0.90 * h - 6, 3.2)
    return ink.mask()

def grip_panel_legendary(flipx):
    w, h = P.GW, P.GH
    img = P.ivory_base(w, h, 61, 'legendary')
    img = P.edge_dark(img, 0.26, 8)
    art = grip_art_legendary(w, h)
    # fine dark scrimshaw hairline halo around the gold, then the gold inlay
    img = P.scrim_etch(img, np.clip(dilate(art, 1.6) - art, 0, 1) * 0.6, tone=C(60, 40, 22), halo=0.0)
    img = metal_inlay(img, art, 'legendary', h, GOLD, groove=0.9)
    img = P.screw_boss(img, w / 2, 0.29 * h, 'rare')
    img = img * np.array([0.93, 0.85, 0.70], np.float32)[None, None]
    if flipx: img = img[:, ::-1]
    return img

_muz_old = muzzle_disc_hi
def muzzle_disc_hi(tier, S=256):
    img = _muz_old(tier, S)
    if tier == 'legendary':
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
        r = np.hypot(xx - (S - 1) / 2, yy - (S - 1) / 2) / (S / 2 - 4)
        gcol = np.array(GOLD['base'])[None, None] * (0.8 + 0.4 * np.clip(-(yy - (S - 1) / 2) / (S / 2), -1, 1))[..., None]
        img = P.over(img, gcol, np.exp(-((r - 0.63) / 0.07) ** 4))
    return img

_slide_old = slide_panel_hi
def slide_panel_hi(tier, side, w, h):
    return slide_panel_legendary(side, w, h) if tier == 'legendary' else _slide_old(tier, side, w, h)
_frame_old = frame_panel_hi
def frame_panel_hi(tier, side, w, h):
    return frame_panel_legendary(side, w, h) if tier == 'legendary' else _frame_old(tier, side, w, h)

if __name__ == '__main__':
    tiers = [sys.argv[1]] if len(sys.argv) > 1 else ['epic', 'legendary']
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
    for t in tiers:
        im = paint_full(t); p = os.path.join(out, f'pistol_1911_camo_{t}_albedo.png'); im.save(p); print('wrote', p)
