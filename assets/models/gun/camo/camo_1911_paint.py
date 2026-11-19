"""Procedural 1024 LINEAR albedo painter for the 1911 camo tiers (numpy + PIL, 4x supersampled vector art, smooth gradients).
usage: python3 camo_1911_paint.py [common|uncommon|rare|all] [out_dir]
Layout comes from camo_1911_layout.py (identical for all tiers)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camo_1911_layout as LY

SS = 4
A = LY.ATLAS
def C(r, g, b): return np.array([r, g, b], np.float32)

# ------------------------------------------------------------------ helpers
def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

def noise(h, w, sy, sx, seed):
    rng = np.random.default_rng(seed)
    gh, gw = int(math.ceil(h / sy)) + 4, int(math.ceil(w / sx)) + 4
    g = rng.standard_normal((gh, gw)).astype(np.float32)
    im = Image.fromarray(g, 'F').resize((gw * sx, gh * sy), Image.BICUBIC)
    a = np.asarray(im)[sy:sy + h, sx:sx + w]
    return a

def fbm(h, w, sy, sx, seed, octs=3):
    tot = np.zeros((h, w), np.float32); amp = 1.0; norm = 0
    for o in range(octs):
        tot += amp * noise(h, w, max(1, int(sy / 2 ** o)), max(1, int(sx / 2 ** o)), seed + 17 * o); norm += amp; amp *= 0.5
    tot /= norm
    return (tot - tot.mean()) / (tot.std() + 1e-6)

def lerp(a, b, t): return a + (b - a) * t

class Ink:
    """Supersampled mask canvas. coords are in final pixels (float), y down."""
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.im = Image.new('L', (w * SS, h * SS), 0); s.d = ImageDraw.Draw(s.im)
    def circle(s, x, y, r, v=255):
        s.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=v)
    def ring(s, x, y, r, wd, v=255):
        s.d.ellipse([(x - r - wd / 2) * SS, (y - r - wd / 2) * SS, (x + r + wd / 2) * SS, (y + r + wd / 2) * SS], outline=v, width=max(1, int(wd * SS)))
    def poly(s, pts, v=255):
        s.d.polygon([(px * SS, py * SS) for px, py in pts], fill=v)
    def line(s, pts, w0, w1=None, v=255):
        """polyline stamped with circles, width tapering w0 -> w1 (diameter in px)."""
        w1 = w0 if w1 is None else w1
        P = np.array(pts, np.float32)
        seg = np.hypot(*(np.diff(P, axis=0).T)); L = float(seg.sum())
        if L <= 0: return
        cum = np.concatenate([[0], np.cumsum(seg)])
        n = max(2, int(L * SS / max(0.35, min(w0, w1) * 0.18)) + 2)
        for t in np.linspace(0, L, n):
            i = min(np.searchsorted(cum, t, side='right') - 1, len(seg) - 1)
            f = (t - cum[i]) / max(seg[i], 1e-6)
            p = P[i] + (P[i + 1] - P[i]) * f
            wd = lerp(w0, w1, t / L)
            s.circle(p[0], p[1], max(wd, 0.2) / 2, v)
    def mask(s):
        im = s.im.resize((s.w, s.h), Image.LANCZOS)
        return np.clip(np.asarray(im, np.float32) / 255.0, 0, 1)

def dilate(m, r):
    if r <= 0: return m
    from PIL import ImageFilter
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * int(math.ceil(r)) + 1))
    im = im.filter(ImageFilter.GaussianBlur(0.5))
    return np.asarray(im, np.float32) / 255.0

def blur(m, r):
    from PIL import ImageFilter
    im = Image.fromarray(np.clip(m * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, np.float32) / 255.0

def shift(m, dx, dy):
    return np.roll(np.roll(m, dy, 0), dx, 1)

def over(img, color, alpha):
    a = alpha[..., None]
    return img * (1 - a) + np.asarray(color, np.float32) * a

# ---------------------------------------------------------------- palettes per tier
PAL = {
 'common': dict(
    shadow=C(17, 20, 30), base=C(27, 32, 46), hi=C(46, 54, 74), streak=C(84, 98, 124), edge=C(150, 160, 176),
    black=C(10, 11, 17), recess=C(7, 8, 11), silver=C(170, 175, 182), silver_hi=C(228, 231, 236), silver_dark=C(104, 108, 116)),
 'uncommon': dict(
    shadow=C(16, 17, 23), base=C(29, 30, 38), hi=C(50, 52, 64), streak=C(88, 94, 110), edge=C(160, 164, 172),
    black=C(10, 10, 14), recess=C(7, 8, 11), silver=C(170, 175, 182), silver_hi=C(228, 231, 236), silver_dark=C(104, 108, 116)),
 'rare': dict(
    shadow=C(11, 13, 21), base=C(21, 26, 42), hi=C(44, 56, 86), streak=C(100, 118, 152), edge=C(170, 180, 196),
    black=C(8, 9, 14), recess=C(6, 7, 10), silver=C(176, 182, 190), silver_hi=C(236, 239, 244), silver_dark=C(108, 113, 122)),
}
BRASS = dict(dark=C(46, 33, 14), base=C(112, 84, 36), hi=C(176, 140, 70))

# cell -> (shadow, base, hi, streak) as keys into a palette-derived dict
def cell_ramp(P, name):
    steel = {
        'steel_black': (P['recess'], P['black'], P['shadow'], P['hi']),
        'steel_dark': (P['black'], P['shadow'], P['base'], P['streak']),
        'steel_mid': (P['shadow'], P['base'], P['hi'], P['streak']),
        'steel_light': (P['base'], P['hi'], P['streak'], P['edge']),
        'sheen': (P['hi'], P['streak'], P['edge'], P['edge']),
        'steel_edge': (P['streak'], P['edge'], P['silver_hi'], P['silver_hi']),
        'silver': (P['silver_dark'], P['silver'], P['silver_hi'], P['silver_hi']),
        'silver_hi': (P['silver'], P['silver_hi'], P['silver_hi'], P['silver_hi']),
        'silver_dark': (P['hi'], P['silver_dark'], P['silver'], P['silver_hi']),
        'screw': (P['silver_dark'], C(124, 128, 136), P['silver'], P['silver_hi']),
    }
    return steel[name]

def vramp(h, sh, base, hi, streak, v0=None):
    """smooth shadow/base/highlight ramp with a thin bright streak, returns (h,1,3); v up."""
    v = np.linspace(1, 0, h, dtype=np.float32)[:, None]
    t1 = smooth(0.02, 0.36, v); t2 = smooth(0.36, 0.60, v)
    col = sh[None, None, :] * (1 - t1[..., None]) + base[None, None, :] * t1[..., None]
    col = col * (1 - t2[..., None]) + hi[None, None, :] * t2[..., None]
    st = np.exp(-((v - 0.655) / 0.016) ** 2)[..., None] * 0.9
    col = col * (1 - st) + streak[None, None, :] * st
    return col

def paint_cell(tier, name):
    P = PAL[tier]; T = LY.CELL
    if name == 'recess':
        return np.tile(P['recess'], (T, T, 1)).astype(np.float32)
    if name == 'ivory':
        return np.tile(C(232, 224, 202), (T, T, 1)).astype(np.float32)
    sh, base, hi, st = cell_ramp(P, name)
    img = np.repeat(vramp(T, sh, base, hi, st), T, axis=1).astype(np.float32)
    # polish line along the mapped border (15%/85% of the cell, + pad) : continuous, anti-aliased
    lo, hp = LY.PAD + (T - 2 * LY.PAD) * 0.15, LY.PAD + (T - 2 * LY.PAD) * 0.85
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    ytop = T - 1 - yy  # y up -> rows are top-first in array
    def band(c, wdt): return np.exp(-((c) / wdt) ** 2)
    wear = name.startswith('steel') or name == 'sheen'
    wc = P['edge'] if wear else P['silver_hi']
    ring = np.maximum.reduce([band(ytop - (T - 1 - hp), 1.1) * (xx > lo - 3) * (xx < hp + 3),
                              band(xx - lo, 1.0) * 0.35, band(xx - hp, 1.0) * 0.35])
    a = ring * (0.55 if tier == 'common' else 0.65)
    if tier == 'uncommon' and wear and name.startswith('steel'):
        n = fbm(T, T, 10, 10, 40 + sum(map(ord, name)) % 50, 2)
        a = a * smooth(-0.3, 0.9, n)
        mott = fbm(T, T, 40, 40, 7, 2)
        img = img * (1 + 0.0 * mott[..., None])
    img = over(img, wc, a)
    # mipmap bleed guard: outside the mapped region just extend (already smooth)
    return img

# ---------------------------------------------------------------- slide / frame bare steel
def steel_panel(tier, w, h, seed, hmax_wear=True):
    """base blued steel for a long side flat (w x h px), v-up ramp. returns float rgb."""
    P = PAL[tier]
    img = np.repeat(vramp(h, P['shadow'], P['base'], P['hi'], P['streak']), w, axis=1).astype(np.float32)
    # very fine linear polish grain (low amplitude, smooth)
    g = noise(h, w, 1, 40, seed) * 0.8 + noise(h, w, 2, 90, seed + 1) * 0.5
    img *= (1 + 0.018 * g)[..., None]
    return img

def serrations(w, h, u0, u1, v0=0.14, v1=0.86, n=20):
    ink = Ink(w, h); hi = Ink(w, h)
    xs = np.linspace(u0 * w, u1 * w, n + 2)[1:-1]
    for x in xs:
        ink.line([(x, v0 * h), (x, v1 * h)], 2.2)
        hi.line([(x + 2.0, v0 * h + 1), (x + 2.0, v1 * h - 1)], 1.1)
    return ink.mask(), hi.mask()

def apply_serr(img, tier, w, h, u0, u1):
    P = PAL[tier]
    g, hl = serrations(w, h, u0, u1)
    img = over(img, P['black'], g * 0.95)
    img = over(img, P['edge'] if tier != 'common' else P['streak'], np.clip(hl - g * 0.5, 0, 1) * 0.75)
    return img

# ------------------------------------------------------------------ ornament primitives (all px, y down)
def spiral(cx, cy, R, th0, turns, rtip=0.07, n=90, direction=-1):
    t = np.linspace(0, 1, n)
    th = th0 + direction * 2 * math.pi * turns * t
    r = R * (1 - (1 - rtip) * t ** 0.85)
    return np.stack([cx + r * np.cos(th), cy + r * np.sin(th)], 1)

def scroll_S(ink, xc, yc, R, phi=35, turns=1.15, wmax=2.6, wmin=0.9, flip=False, leaves=True, cut=None):
    """point-symmetric S scroll centred at (xc,yc); outer spiral radius R; returns stem points."""
    th0 = math.radians(-phi)
    cA = np.array([-R * math.cos(th0), -R * math.sin(th0)])
    sp = spiral(cA[0], cA[1], R, th0, turns)           # outer -> inner (t 0..1)
    half = sp                                           # starts at origin
    full = np.concatenate([half[::-1], -half[1:]])
    if flip: full = full * np.array([1, -1])
    full = full + np.array([xc, yc])
    n = len(full)
    s = np.linspace(0, 1, n)
    wd = wmin + (wmax - wmin) * np.sin(math.pi * np.clip(s * 1.0, 0, 1)) ** 0.6   # thick in the middle, thin tips
    wd = np.maximum(wd, wmin)
    for i in range(n - 1):
        ink.line([tuple(full[i]), tuple(full[i + 1])], wd[i], wd[i + 1])
    # bead at both tips
    ink.circle(full[0][0], full[0][1], wmax * 0.75); ink.circle(full[-1][0], full[-1][1], wmax * 0.75)
    return full

def leaf(ink, x, y, ang, L, Wd, cutline=True):
    """lancet leaf from base (x,y) pointing at angle ang (rad, y-down coords)."""
    s = np.linspace(0, 1, 18)
    off = Wd * np.sin(np.pi * s ** 0.8) * (1 - 0.25 * s)
    ca, sa = math.cos(ang), math.sin(ang)
    pts_u = [(x + ca * L * a - sa * o, y + sa * L * a + ca * o) for a, o in zip(s, off)]
    pts_d = [(x + ca * L * a + sa * o, y + sa * L * a - ca * o) for a, o in zip(s[::-1], off[::-1])]
    ink.poly(pts_u + pts_d)
    return (x + ca * L, y + sa * L)

def leaf_cut(ink, x, y, ang, L, w=0.8):
    ink.line([(x + math.cos(ang) * L * 0.12, y + math.sin(ang) * L * 0.12), (x + math.cos(ang) * L * 0.78, y + math.sin(ang) * L * 0.78)], w, w, v=0)

def decorate_scroll(ink, path, every, size, side=1, rng=None, cut=True):
    """leaves along a stem path, alternating sides, plus tiny berries."""
    P = np.asarray(path)
    d = np.diff(P, axis=0); seg = np.hypot(d[:, 0], d[:, 1]); cum = np.concatenate([[0], np.cumsum(seg)])
    L = cum[-1]
    k = 0
    for t in np.arange(every * 0.6, L - every * 0.4, every):
        i = min(np.searchsorted(cum, t) - 1, len(d) - 1); i = max(i, 0)
        tx, ty = d[i] / max(seg[i], 1e-6)
        nx, ny = -ty, tx
        sg = side if k % 2 == 0 else -side
        ang = math.atan2(ty * 0.55 + ny * sg, tx * 0.55 + nx * sg)
        x, y = P[i]
        # skip leaves near the tight spiral cores (path too curved): only where cum is within [0.12,0.88] L
        if 0.1 * L < t < 0.9 * L:
            leaf(ink, x, y, ang, size, size * 0.30)
            if cut: leaf_cut(ink, x, y, ang, size)
        k += 1

def lancet(cx, y_base, y_spring, y_apex, half, n=40):
    """pointed (two-centred) arch outline: straight jambs from y_base to y_spring, two arcs to the apex. y down."""
    Hh = y_spring - y_apex
    r = (Hh * Hh + half * half) / (2 * half)
    ccx = cx - half + r
    d = math.atan2(-Hh, half - r)
    left = [(ccx + r * math.cos(t), y_spring + r * math.sin(t)) for t in np.linspace(-math.pi, d, n)]
    right = [(2 * cx - x, y) for x, y in left[::-1]]
    return [(cx - half, y_base)] + left + right[1:] + [(cx + half, y_base)]

def rose_window(ink, cx, cy, R, w=1.2, boss=9):
    ink.ring(cx, cy, R, w * 1.5); ink.ring(cx, cy, R - 4.5, w * 0.9)
    ink.ring(cx, cy, R * 0.46, w); ink.ring(cx, cy, boss + 5, w * 0.9)
    r1, r2 = R * 0.50, R - 8
    for k in range(8):
        a = k * math.pi / 4
        da = math.pi / 8 * 0.85
        s_ = np.linspace(0, 1, 18)
        env = (1 - s_ ** 2.2) ** 0.8 * da
        left = [(cx + (r1 + (r2 - r1) * t) * math.cos(a - e), cy + (r1 + (r2 - r1) * t) * math.sin(a - e)) for t, e in zip(s_, env)]
        right = [(cx + (r1 + (r2 - r1) * t) * math.cos(a + e), cy + (r1 + (r2 - r1) * t) * math.sin(a + e)) for t, e in zip(s_, env)]
        ink.line(left + right[::-1], w, w)
        ink.circle(cx + (R * 0.5 + 3) * math.cos(a + math.pi / 8), cy + (R * 0.5 + 3) * math.sin(a + math.pi / 8), 1.2)
        ink.circle(cx + (R - 2.3) * math.cos(a + math.pi / 8), cy + (R - 2.3) * math.sin(a + math.pi / 8), 0.01)
    for k in range(16):
        a = k * math.pi / 8
        ink.line([(cx + (boss + 5) * math.cos(a), cy + (boss + 5) * math.sin(a)), (cx + R * 0.46 * math.cos(a), cy + R * 0.46 * math.sin(a))], 0.8, 0.8)
    ink.circle(cx, cy, boss)

def cross_fleury(ink, cx, cy, h, w=3.0):
    """Latin cross with trefoil flared ends (filled)."""
    arm = h * 0.30; yb = cy - h * 0.16
    ink.line([(cx, cy - h * 0.5), (cx, cy + h * 0.5)], w, w)
    ink.line([(cx - arm, yb), (cx + arm, yb)], w, w)
    for (x, y, dx, dy) in ((cx, cy - h * 0.5, 0, -1), (cx, cy + h * 0.5, 0, 1), (cx - arm, yb, -1, 0), (cx + arm, yb, 1, 0)):
        ink.circle(x + dx * w * 0.5, y + dy * w * 0.5, w * 0.95)
        ink.circle(x + dy * w * 1.5 + dx * w * 0.2, y + dx * w * 1.5 + dy * w * 0.2, w * 0.7)
        ink.circle(x - dy * w * 1.5 + dx * w * 0.2, y - dx * w * 1.5 + dy * w * 0.2, w * 0.7)

def quatrefoil(ink, cx, cy, r, t=1.7):
    """quatrefoil outline of thickness t"""
    o = r * 0.52; rho = r * 0.50
    for dx, dy in ((o, 0), (-o, 0), (0, o), (0, -o)):
        ink.circle(cx + dx, cy + dy, rho)
    for dx, dy in ((o, 0), (-o, 0), (0, o), (0, -o)):
        ink.circle(cx + dx, cy + dy, rho - t, v=0)
    ink.circle(cx, cy, r * 0.30, v=0)

# ---------------------------------------------------------------- inlay / etch renderers
def silver_inlay(img, mask, tier, h_region, groove=1.3):
    P = PAL[tier]; h, w = mask.shape
    g = np.clip(dilate(mask, groove) - mask * 1.0, 0, 1)
    img = over(img, P['black'], np.clip(g * 1.3, 0, 1) * 0.9)
    fillc = np.repeat(vramp(h, P['silver_dark'] * 0.92, P['silver'], C(218, 222, 228), P['silver_hi']), w, axis=1)
    img = img * (1 - mask[..., None]) + fillc * mask[..., None]
    up = np.clip(mask - shift(mask, 0, 1), 0, 1)
    dn = np.clip(mask - shift(mask, 0, -1), 0, 1)
    img = over(img, P['silver_hi'], up * 0.85)
    img = over(img, P['silver_dark'] * 0.8, dn * 0.5)
    return img

# ---------------------------------------------------------------- slide
def slide_art_rare(side, w, h):
    """returns ink mask (silver inlay) for the slide side. y down; top of slide = row 0."""
    ink = Ink(w, h)
    R_side = side == 'R'
    # horizontal axis: u increases to the right; muzzle right (R) / muzzle left (L)
    ser0, ser1 = (0.0, 0.153) if R_side else (0.847, 1.0)
    # border rules
    yb, yt = 0.905 * h, 0.115 * h     # bottom / top rule (row from top) : top rule near row 0.115h
    def rule(y, x0, x1):
        ink.line([(x0, y), (x1, y)], 1.5)
    xa, xb = (0.168 * w, 0.975 * w) if R_side else (0.025 * w, 0.832 * w)
    rule(0.90 * h, xa, xb)
    rule(0.865 * h, xa, xb)
    port_x0, port_x1 = 0.306 * w, 0.551 * w
    if R_side:
        rule(0.115 * h, 0.551 * w + 12, xb); rule(0.150 * h, 0.551 * w + 12, xb)
        rule(0.115 * h, xa, 0.306 * w - 12); rule(0.150 * h, xa, 0.306 * w - 12)
    else:
        rule(0.115 * h, xa, xb); rule(0.150 * h, xa, xb)
    # divider next to the serrations (vertical double line with beads)
    xd = ser1 * w + 6 if R_side else ser0 * w - 6
    ink.line([(xd, 0.11 * h), (xd, 0.91 * h)], 1.4)
    ink.line([(xd + (5 if R_side else -5), 0.15 * h), (xd + (5 if R_side else -5), 0.865 * h)], 1.0)
    # --- scroll fields
    rng = np.random.default_rng(3)
    cut = []
    def field(x0, x1, y0, y1, R, flip0=False):
        """tile S-scrolls between x0..x1 in the band y0..y1 (centre line). alternate flips, leaves on stems."""
        yc = (y0 + y1) / 2
        step = R * 2.0 * 1.35
        n = max(1, int(round((x1 - x0) / step)))
        stp = (x1 - x0) / n
        for i in range(n):
            xc = x0 + stp * (i + 0.5)
            fl = (i % 2 == 1) ^ flip0
            path = scroll_S(ink, xc, yc, R * stp / step * 0.9, flip=fl, wmax=min(3.2, R * 0.12 + 1.4), wmin=1.0)
            decorate_scroll(ink, path, R * 0.55, R * 0.42, 1 if not fl else -1)
    if R_side:
        # rear field (full height), front field (full height), under-port band
        field(xa + 12, port_x0 - 18, 0.18 * h, 0.84 * h, 26)
        field(port_x1 + 20, 0.71 * w - 54, 0.18 * h, 0.84 * h, 28)
        field(0.71 * w + 54, xb - 8, 0.18 * h, 0.84 * h, 28, True)
        medx = 0.71 * w
        under_band_y = (0.52 * h, 0.86 * h)
        field(port_x0 + 8, port_x1 - 8, under_band_y[0], under_band_y[1], 21)
    else:
        medx = 0.43 * w
        field(xa + 8, medx - 70, 0.18 * h, 0.84 * h, 28)
        field(medx + 70, xb - 8, 0.18 * h, 0.84 * h, 28, True)
    # --- central medallion: quatrefoil + beaded ring + cross
    cy = 0.505 * h
    Rm = 0.30 * h
    ink.ring(medx, cy, Rm * 1.45, 1.8); ink.ring(medx, cy, Rm * 1.45 + 4.5, 1.0)
    for k in range(20):
        a = k * math.pi / 10
        ink.circle(medx + (Rm * 1.45 + 9.5) * math.cos(a), cy + (Rm * 1.45 + 9.5) * math.sin(a), 1.25)
    quatrefoil(ink, medx, cy, Rm * 1.22, 2.0)
    cross_fleury(ink, medx, cy, Rm * 1.05, 2.2)
    return ink.mask()

def frame_art_rare(side, w, h):
    ink = Ink(w, h)
    ink.line([(0.02 * w, 0.10 * h), (0.98 * w, 0.10 * h)], 1.4)
    ink.line([(0.02 * w, 0.90 * h), (0.98 * w, 0.90 * h)], 1.4)
    R = 0.24 * h
    n = int(0.62 * w / (R * 2.7))
    x0, x1 = 0.04 * w, 0.66 * w
    stp = (x1 - x0) / n
    for i in range(n):
        path = scroll_S(ink, x0 + stp * (i + 0.5), 0.5 * h, R, flip=(i % 2 == 1), wmax=2.0, wmin=0.8)
        decorate_scroll(ink, path, R * 0.7, R * 0.45, -1 if i % 2 else 1)
    return ink.mask()

# ---------------------------------------------------------------- wear (uncommon)
def wear_alpha(w, h, seed, ends=(), strength=1.0):
    """worn-bluing mask: heavy on the top/bottom edges, ends, scattered nicks. 1 = bare steel."""
    n1 = fbm(h, w, 10, 60, seed, 3)          # long streaks along the slide
    n2 = fbm(h, w, 5, 9, seed + 5, 2)
    rows = np.arange(h, dtype=np.float32)[:, None] / (h - 1)
    cols = np.arange(w, dtype=np.float32)[None, :] / (w - 1)
    top = np.exp(-(rows - 0.0) / 0.045) + np.exp(-(rows - 0.0) / 0.012) * 0.6
    bot = np.exp(-(1 - rows) / 0.05)
    e = np.zeros((1, w), np.float32)
    for x0, wid in ends: e = np.maximum(e, 0.30 * np.exp(-np.abs(cols - x0) / wid))
    rpx = np.arange(h, dtype=np.float32)[:, None]
    force = (np.exp(-rpx / 1.2) + np.exp(-(h - 1 - rpx) / 1.2)) * 0.6
    prox = np.clip(top * 1.0 + bot * 0.9 + e * 0.9 + force, 0, 1.6)
    m = prox * 0.98 + 0.07 * n1 + 0.02 * n2 - 0.80
    a = smooth(0.0, 0.16, m) * strength * 0.5
    # tiny crisp nicks / scratches
    rng = np.random.default_rng(seed + 9)
    nk = Ink(w, h)
    for _ in range(0):
        x, y = rng.uniform(0, w), rng.uniform(0.05, 0.95) * h
        L = rng.uniform(2, 9); ang = rng.normal(0, 0.35) + (0 if rng.random() < 0.7 else math.pi / 2)
        nk.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], rng.uniform(0.7, 1.4))
    return np.clip(a, 0, 1), n1

def worn_steel(tier, w, h, seed, ends=()):
    img = steel_panel(tier, w, h, seed)
    P = PAL[tier]
    mott = fbm(h, w, 14, 70, seed + 21, 3)
    img *= (1 + 0.0 * mott)[..., None]                          # mottled blue-black
    brown = smooth(0.4, 1.6, fbm(h, w, 9, 45, seed + 31, 3))
    img = over(img, C(46, 36, 34), brown * 0.0)                 # plum/brown fade where the bluing thinned
    a, n1 = wear_alpha(w, h, seed, ends)
    bare = np.repeat(vramp(h, C(92, 100, 114), C(128, 137, 150), C(164, 172, 184), C(204, 210, 220)), w, axis=1)
    grain = 1 + 0.06 * noise(h, w, 1, 30, seed + 3)[..., None]
    bare = bare * grain * (1 - 0.08 * smooth(0.5, 1.5, n1))[..., None]
    img = img * (1 - a[..., None]) + bare * a[..., None]
    return img, a

# ---------------------------------------------------------------- grips (natural orientation: top of grip = row 0)
GW, GH = 195, 435   # inner usable size after RPAD (region is 203 x 443)

def ivory_base(w, h, seed, tier):
    base = np.tile(C(212, 199, 170), (h, w, 1)).astype(np.float32)
    # long soft grain along the grip, fine growth lines
    gr = noise(h, w, 70, 3, seed) * 0.6 + noise(h, w, 24, 2, seed + 1) * 0.4
    base *= (1 + 0.028 * gr)[..., None]
    base = over(base, C(186, 160, 118), 0.28 * smooth(0.3, 1.5, fbm(h, w, 60, 40, seed + 2, 3)))   # warm patina
    base = over(base, C(232, 222, 196), 0.18 * smooth(0.4, 1.6, fbm(h, w, 40, 30, seed + 3, 2)))
    return base

def dark_grip_base(w, h, seed):
    base = np.tile(C(44, 29, 19), (h, w, 1)).astype(np.float32)
    streak = noise(h, w, 90, 3, seed) * 0.7 + noise(h, w, 30, 2, seed + 1) * 0.5 + noise(h, w, 8, 1, seed + 2) * 0.25
    base *= (1 + 0.20 * streak)[..., None]
    base = over(base, C(86, 56, 34), 0.22 * smooth(0.6, 2.0, noise(h, w, 50, 4, seed + 5)))   # lighter figure
    base = over(base, C(26, 17, 12), 0.45 * smooth(0.2, 1.8, fbm(h, w, 40, 30, seed + 6, 3)))   # oil stain
    return base

def edge_dark(img, amount, px=8):
    h, w, _ = img.shape
    r = np.minimum.reduce([np.arange(h)[:, None] * np.ones((1, w)), (h - 1 - np.arange(h))[:, None] * np.ones((1, w)),
                           np.ones((h, 1)) * np.arange(w)[None, :], np.ones((h, 1)) * (w - 1 - np.arange(w))[None, :]])
    return img * (1 - amount * np.exp(-r / px))[..., None]

def screw_boss(img, cx, cy, tier):
    h, w, _ = img.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xx - cx, yy - cy)
    if tier == 'uncommon':
        rim, face, hi = BRASS['dark'], BRASS['base'], BRASS['hi']
    else:
        rim, face, hi = C(104, 108, 116), C(160, 165, 172), C(228, 231, 236)
    cov = np.clip(10.5 - r, 0, 1)
    img = over(img, C(15, 12, 10), np.clip(12.5 - r, 0, 1) * 0.7 * (r > 8))
    col = face[None, None] + (hi - face)[None, None] * np.clip(1 - (r / 8.5), 0, 1)[..., None] * (0.7 + 0.5 * np.clip(-(yy - cy) / 8, -1, 1))[..., None]
    col = col * (1 - 0.35 * smooth(6.5, 9.0, r))[..., None] + rim * (0.35 * smooth(6.5, 9.0, r))[..., None]
    img = over(img, col, np.clip(9.2 - r, 0, 1))
    slot = np.clip(1.0 - np.abs((yy - cy - 0.5 * (xx - cx) * 0.25)) / 1.1, 0, 1) * (np.abs(xx - cx) < 6.2) * (r < 8.5)
    img = over(img, C(30, 24, 18), slot * 0.85)
    return img

def scrim_etch(img, mask, tone=C(34, 22, 14), halo=0.22):
    mask = np.clip(dilate(mask, 0.6) * 0.5 + mask * 0.75, 0, 1)
    img = over(img, tone, blur(mask, 1.4) * halo)
    img = over(img, tone, mask * 0.97)
    return img

def grip_art_rare(w, h):
    ink = Ink(w, h)
    cx = w / 2
    sy = 0.29 * h
    # double border with corner trefoils
    def rrect(inset, wd):
        x0, y0, x1, y1 = inset, inset, w - inset, h - inset
        ink.line([(x0 + 8, y0), (x1 - 8, y0)], wd); ink.line([(x0 + 8, y1), (x1 - 8, y1)], wd)
        ink.line([(x0, y0 + 8), (x0, y1 - 8)], wd); ink.line([(x1, y0 + 8), (x1, y1 - 8)], wd)
        for (a, b, sx_, sy_) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            pts = [(a + sx_ * 8 * (1 - math.sin(t)), b + sy_ * 8 * (1 - math.cos(t))) for t in np.linspace(0, math.pi / 2, 12)]
            ink.line(pts, wd)
    rrect(13, 1.6); rrect(19, 0.9)
    for (a, b) in ((13, 13), (w - 13, 13), (13, h - 13), (w - 13, h - 13)):
        ink.circle(a, b, 3.2)
    # rose window around the screw
    rose_window(ink, cx, sy, 58, 1.3, 9.5)
    # little pointed arches row above the window
    for i in range(-2, 3):
        x = cx + i * 22
        ink.line(lancet(x, 38, 31, 22, 8), 1.0)
    # tall lancet window with cross
    top, base = 0.585 * h, 0.80 * h
    spr = top + 52
    ink.line(lancet(cx, base, spr, top, 52), 1.7)
    ink.line(lancet(cx, base - 5, spr, top + 10, 43), 0.9)
    ink.line([(cx - 52, base), (cx + 52, base)], 1.7)
    ink.line([(cx - 43, base - 5), (cx + 43, base - 5)], 0.9)
    cross_fleury(ink, cx, (top + base) / 2 + 10, 66, 2.6)
    for k in range(-2, 3):      # vertical tracery strokes either side of cross
        if k:
            ink.line([(cx + k * 17, base - 8), (cx + k * 17, base - 8 - 38 + abs(k) * 6)], 0.8)
    # quatrefoil in the arch head
    quatrefoil(ink, cx, top + 30, 15, 1.2)
    # thorny vine along the bottom
    vy = 0.905 * h
    path = scroll_S(ink, cx - 38, vy, 15, flip=False, wmax=2.2, wmin=0.9)
    decorate_scroll(ink, path, 8, 9, 1)
    path = scroll_S(ink, cx + 38, vy, 15, flip=True, wmax=2.2, wmin=0.9)
    decorate_scroll(ink, path, 8, 9, -1)
    ink.circle(cx, vy, 3.2)
    # stipple (pin-prick) shading in the arch spandrels
    rng = np.random.default_rng(5)
    for _ in range(170):
        x = rng.uniform(cx - 50, cx + 50); y = rng.uniform(top + 52, base - 12)
        if abs(x - cx) > 36 and rng.random() < 0.85: ink.circle(x, y, rng.uniform(0.55, 0.95))
    return ink.mask()

def grip_panel(tier, flipx):
    w, h = GW, GH
    seed = 11
    if tier == 'common':
        img = ivory_base(w, h, seed, tier)
        img = edge_dark(img, 0.18, 7)
        mk = Ink(w, h); mk.line([(14, 14), (w - 14, 14), (w - 14, h - 14), (14, h - 14), (14, 14)], 1.0)
        img = over(img, C(176, 160, 128), mk.mask() * 0.55)
        img = screw_boss(img, w / 2, 0.29 * h, tier)
    elif tier == 'uncommon':
        img = dark_grip_base(w, h, seed)
        img = edge_dark(img, 0.40, 8)
        mk = Ink(w, h)
        mk.line([(15, 15), (w - 15, 15), (w - 15, h - 15), (15, h - 15), (15, 15)], 1.8)
        for (a, b) in ((15, 15), (w - 15, 15), (15, h - 15), (w - 15, h - 15)):
            mk.circle(a, b, 4.2)
        m = mk.mask()
        brass = np.zeros_like(img) + BRASS['base']
        vr = np.linspace(1, 0, h, dtype=np.float32)[:, None, None]
        brass = lerp(BRASS['dark'], BRASS['hi'], 0.25 + 0.5 * vr) * np.ones((1, w, 1))
        img = over(img, C(12, 8, 6), dilate(m, 1.3) * 0.7)
        img = img * (1 - m[..., None]) + brass * m[..., None]
        img = over(img, BRASS['hi'], np.clip(m - shift(m, 0, 1), 0, 1) * 0.5)
        img = screw_boss(img, w / 2, 0.29 * h, tier)
    else:
        img = ivory_base(w, h, seed + 40, tier)
        img = edge_dark(img, 0.22, 7)
        art = grip_art_rare(w, h)
        img = scrim_etch(img, art)
        # screw boss sits in the rose-window centre
        img = screw_boss(img, w / 2, 0.29 * h, tier)
    if flipx: img = img[:, ::-1]
    return img                # atlas rows are v-up and v runs DOWN the grip, so natural (top-first) rows go in unflipped

# ---------------------------------------------------------------- muzzle disc
def muzzle_disc(tier, S=256):
    P = PAL[tier]
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    r = np.hypot(xx - (S - 1) / 2, yy - (S - 1) / 2) / (S / 2 - 4)       # 1.0 at the edge of the usable disc
    img = np.tile(P['shadow'], (S, S, 1)).astype(np.float32)
    ring_face = lerp(P['base'][None, None], P['hi'][None, None], smooth(0.4, 0.9, r)[..., None])
    img = over(img, ring_face, smooth(0.395, 0.405, r) * (1 - smooth(0.875, 0.885, r)))
    img = over(img, P['edge'], np.exp(-((r - 0.80) / 0.012) ** 2) * 0.8)
    img = over(img, P['streak'], np.exp(-((r - 0.47) / 0.012) ** 2) * 0.7)
    bore = np.clip(1 - r / 0.395, 0, 1)
    img = over(img, P['recess'][None, None] * (0.6 + 0.4 * (1 - bore))[..., None], 1 - smooth(0.375, 0.395, r))
    img = over(img, P['edge'], np.exp(-((r - 0.385) / 0.01) ** 2) * 0.65)
    if tier == 'uncommon':
        ring = np.exp(-((r - 0.63) / 0.055) ** 4)
        bc = BRASS['base'][None, None] * (0.8 + 0.4 * np.clip(-(yy - (S - 1) / 2) / (S / 2), -1, 1))[..., None]
        img = over(img, bc, ring); img = over(img, BRASS['dark'], np.exp(-((r - 0.575) / 0.012) ** 2) * 0.8)
    if tier == 'rare':
        ring = np.exp(-((r - 0.63) / 0.05) ** 4)
        sv = P['silver'][None, None] * (0.85 + 0.3 * np.clip(-(yy - (S - 1) / 2) / (S / 2), -1, 1))[..., None]
        img = over(img, sv, ring)
        ang = np.arctan2(yy - (S - 1) / 2, xx - (S - 1) / 2)
        ticks = (np.cos(ang * 48) > 0.9) * np.exp(-((r - 0.74) / 0.035) ** 4)
        img = over(img, P['silver_hi'], ticks * 0.9)
        img = over(img, P['black'], np.exp(-((r - 0.575) / 0.01) ** 2) * 0.9)
    return img

# ---------------------------------------------------------------- slide / frame per tier
def slide_panel(tier, side, w=1000, h=122):
    R_side = side == 'R'
    if tier == 'common':
        img = steel_panel(tier, w, h, 3 if R_side else 4)
        ser = (0.0, 0.153) if R_side else (0.847, 1.0)
        img = apply_serr(img, tier, w, h, *ser)
    elif tier == 'uncommon':
        ends = [(0.0, 0.03), (1.0, 0.03)]
        img, a = worn_steel(tier, w, h, 5 if R_side else 6, ends)
        ser = (0.0, 0.153) if R_side else (0.847, 1.0)
        img = apply_serr(img, tier, w, h, *ser)
        img = brass_slide_inlay(img, side, w, h)
    else:
        img = steel_panel(tier, w, h, 3 if R_side else 4)
        ser = (0.0, 0.153) if R_side else (0.847, 1.0)
        img = apply_serr(img, tier, w, h, *ser)
        img = silver_inlay(img, slide_art_rare(side, w, h), tier, h)
    return img

def brass_slide_inlay(img, side, w, h):
    """a slim aged-brass rule + medallion pin: darkened brass inlay."""
    ink = Ink(w, h)
    medx = 0.71 * w if side == 'R' else 0.43 * w
    cy = 0.505 * h
    ink.ring(medx, cy, 23, 2.8); ink.ring(medx, cy, 12, 1.6); ink.circle(medx, cy, 5.6)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        ink.circle(medx + 23 * math.cos(a), cy + 23 * math.sin(a), 3.4)
    xa, xb = (0.168 * w, 0.975 * w) if side == 'R' else (0.025 * w, 0.832 * w)
    ink.line([(xa, 0.885 * h), (xb, 0.885 * h)], 2.0)
    m = ink.mask()
    vr = np.linspace(1, 0, h, dtype=np.float32)[:, None, None]
    brass = lerp(BRASS['dark'], BRASS['hi'], 0.18 + 0.55 * vr) * np.ones((1, w, 1))
    img = over(img, C(8, 8, 10), dilate(m, 1.2) * 0.8)
    img = img * (1 - m[..., None]) + brass * m[..., None]
    img = over(img, BRASS['hi'], np.clip(m - shift(m, 0, 1), 0, 1) * 0.55)
    return img

def frame_panel(tier, side, w=1000, h=75):
    R_side = side == 'R'
    if tier == 'common':
        return steel_panel(tier, w, h, 7 if R_side else 8)
    if tier == 'uncommon':
        img, a = worn_steel(tier, w, h, 9 if R_side else 10, [(0.0, 0.02), (1.0, 0.02)])
        return img
    img = steel_panel(tier, w, h, 7 if R_side else 8)
    return silver_inlay(img, frame_art_rare(side, w, h), tier, h)

# ---------------------------------------------------------------- atlas assembly
def put(atlas, rect_name, img, pad_extend=True):
    x0, y0, x1, y1 = LY.REGION[rect_name]
    ih, iw = img.shape[:2]
    p = LY.RPAD
    # img covers the inner (x0+p..x1-p) box; fill the pad border by edge extension
    inner_w, inner_h = (x1 - x0) - 2 * p, (y1 - y0) - 2 * p
    assert (iw, ih) == (inner_w, inner_h), (rect_name, (iw, ih), (inner_w, inner_h))
    full = np.pad(img, ((p, p), (p, p), (0, 0)), mode='edge')            # image rows are top-first
    atlas[y0:y1, x0:x1] = full[::-1]                                       # atlas rows are y-up

def paint(tier):
    atlas = np.zeros((A, A, 3), np.float32) + PAL[tier]['recess']
    for name, (tx, ty) in LY.SWATCH.items():
        cell = paint_cell(tier, name)                                     # rows top-first
        atlas[ty * LY.CELL:(ty + 1) * LY.CELL, tx * LY.CELL:(tx + 1) * LY.CELL] = cell[::-1]
    x0, y0, x1, y1 = LY.REGION['slideR']; wi, hi_ = (x1 - x0) - 8, (y1 - y0) - 8
    put(atlas, 'slideR', slide_panel(tier, 'R', wi, hi_))
    put(atlas, 'slideL', slide_panel(tier, 'L', wi, hi_))
    x0, y0, x1, y1 = LY.REGION['frameR']; wi, hi_ = (x1 - x0) - 8, (y1 - y0) - 8
    put(atlas, 'frameR', frame_panel(tier, 'R', wi, hi_))
    put(atlas, 'frameL', frame_panel(tier, 'L', wi, hi_))
    # grip panels: image rows are top-first in 'natural' orientation, grip_panel() already flipped to UV (v-up) order
    gl = grip_panel(tier, False); gr = grip_panel(tier, True)
    for nm, g in (('gripL', gl), ('gripR', gr)):
        x0, y0, x1, y1 = LY.REGION[nm]; p = LY.RPAD
        full = np.pad(g, ((p, p), (p, p), (0, 0)), mode='edge')
        atlas[y0:y1, x0:x1] = full
    x0, y0, x1, y1 = LY.REGION['muzzle']
    atlas[y0:y1, x0:x1] = muzzle_disc(tier, x1 - x0)
    out = np.clip(atlas + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(out[::-1])                                      # PNG top row = v 1

if __name__ == '__main__':
    tiers = ['common', 'uncommon', 'rare'] if len(sys.argv) < 2 or sys.argv[1] == 'all' else [sys.argv[1]]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
    for t in tiers:
        im = paint(t)
        p = os.path.join(out, f'pistol_1911_camo_{t}_albedo.png')
        im.save(p); print('wrote', p, im.size)
