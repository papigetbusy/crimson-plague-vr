"""v2 wall textures, repainted from scratch at Crimson Halls quality (art only; src/ is untouched).

Replaces the first v2 pass (a 2x dither-upscale of the old canvases). The old textures in
assets/textures/walls/original/ are only a guide to each set's colour mood and theme; nothing is copied.

Painting follows assets/models/env/crimson_halls/build_crimson_halls.py (the kit atlas):
  * clean block / brick / plank / facet layouts, flat per-block tone, a lit top-left edge and a
    shadowed bottom-right edge on every block, dark mortar, no speckle and no dither
  * a dark plinth strip with a trim rail along the foot of every wall (like the kit's plinth)
  * sharp drawn details: drips, cracks, runes, icicles, lava veins, moss, roots, fungus, bones
  * skulls are NOT pixel icons: they are low-poly 3D skulls rendered in Blender with light from
    above and occlusion in the sockets (tools/textures/make_skull_sprites.py), tinted per set; the
    crypt banner and cloth carry the kit's gold horned demon, also rendered in 3D
  * painted at 2x then box-filtered down, so edges are crisp but not jagged
  * every layer wraps (9-way offset drawing, wrapped blur), so all tiles stay seamless
Sizes (64 px per metre, the kit's wall is 60): walls / panel / pillar / banner / cloth 128x256
(2 m x 4 m), floors / ceiling / carpet 128x128 (2 m x 2 m), gold trim 64x64.
Deterministic (fixed seeds).
usage: python3 tools/textures/repaint_walls.py [dst_dir]     (default assets/textures/walls/v2)
needs:  assets/textures/walls/v2_src/skulls/*.png  (blender -b --python tools/textures/make_skull_sprites.py -- --out ...)
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'assets/textures/walls/v2')
SKULLS = os.path.join(ROOT, 'assets/textures/walls/v2_src/skulls')
SS = 2          # paint at 2x, box down


def C(c):
    return np.array(c, float)


def mix(a, b, t):
    return C(a) * (1 - t) + C(b) * t


def scl(c, k):
    return tuple(int(max(0, min(255, v * k))) for v in c)


class Tex:
    def __init__(self, w, h, seed):
        self.w, self.h = w, h
        self.W, self.H = w * SS, h * SS
        self.a = np.zeros((self.H, self.W, 3), float)
        self.rng = np.random.default_rng(seed)

    def r(self, a=0.0, b=1.0):
        return a + (b - a) * self.rng.random()

    # ---- wrapped overlay layers (coordinates in final pixels)
    def layer(self):
        return Layer(self)

    def comp(self, L, glow=None, glow_r=3.0, glow_k=0.9):
        rgb = np.asarray(L.img, float)[..., :3]
        al = np.asarray(L.img, float)[..., 3:4] / 255.0
        if glow is not None:
            g = blur_wrap(al[..., 0], glow_r * SS)[..., None]
            self.a = self.a + C(glow) * g * glow_k
        self.a = self.a * (1 - al) + rgb * al

    def sprite(self, name, cx, cy, width, tint=None, alpha=1.0, shadow=0.6):
        """paste a rendered 3D skull sprite, centre (cx, cy), width in final px; wraps"""
        im = Image.open(os.path.join(SKULLS, name + '.png')).convert('RGBA')
        bb = im.getbbox(); im = im.crop(bb)
        w = int(width * SS); h = int(im.height * w / im.width)
        im = im.resize((w, h), Image.LANCZOS)
        rgb = np.asarray(im, float)[..., :3]; al = np.asarray(im, float)[..., 3:4] / 255.0 * alpha
        if tint is not None:
            rgb = rgb / 160.0 * C(tint)
        rgb = np.clip(rgb, 0, 255)
        x0 = int(cx * SS - w / 2); y0 = int(cy * SS - h / 2)
        for ox in (-self.W, 0, self.W):
            for oy in (-self.H, 0, self.H):
                self._paste(rgb, al, x0 + ox, y0 + oy, shadow)
        return h / SS

    def _paste(self, rgb, al, x0, y0, shadow):
        h, w = al.shape[:2]
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(self.W, x0 + w), min(self.H, y0 + h)
        if X0 >= X1 or Y0 >= Y1:
            return
        s = (slice(Y0 - y0, Y1 - y0), slice(X0 - x0, X1 - x0))
        d = (slice(Y0, Y1), slice(X0, X1))
        if shadow:   # contact shadow down-right so it sits in the wall
            sh = np.zeros_like(self.a[..., 0]); sh[d] = al[s][..., 0]
            sh = np.roll(np.roll(sh, 3 * SS, 0), 2 * SS, 1)
            self.a *= (1 - sh * shadow)[..., None]
        self.a[d] = self.a[d] * (1 - al[s]) + rgb[s] * al[s]

    def shade_rect(self, x0, y0, x1, y1, k):
        self.a[int(y0 * SS):int(y1 * SS), int(x0 * SS):int(x1 * SS)] *= k

    def save(self, path):
        im = Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8))
        im = im.reduce(SS)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        im.save(path, optimize=True)
        return im.size


class Layer:
    def __init__(self, t):
        self.t = t
        self.img = Image.new('RGBA', (t.W, t.H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def _offs(self):
        for ox in (-self.t.w, 0, self.t.w):
            for oy in (-self.t.h, 0, self.t.h):
                yield ox, oy

    def poly(self, pts, fill):
        for ox, oy in self._offs():
            self.d.polygon([((x + ox) * SS, (y + oy) * SS) for x, y in pts], fill=fill)

    def line(self, pts, fill, width=1.0):
        for ox, oy in self._offs():
            q = [((x + ox) * SS, (y + oy) * SS) for x, y in pts]
            self.d.line(q, fill=fill, width=max(1, int(round(width * SS))), joint='curve')

    def ellipse(self, cx, cy, rx, ry, fill):
        for ox, oy in self._offs():
            self.d.ellipse([(cx - rx + ox) * SS, (cy - ry + oy) * SS, (cx + rx + ox) * SS, (cy + ry + oy) * SS], fill=fill)

    def rect(self, x0, y0, x1, y1, fill):
        for ox, oy in self._offs():
            self.d.rectangle([(x0 + ox) * SS, (y0 + oy) * SS, (x1 + ox) * SS - 1, (y1 + oy) * SS - 1], fill=fill)


def blur_wrap(a2, r):
    h, w = a2.shape
    big = np.tile(np.clip(a2 * 255, 0, 255).astype(np.uint8), (3, 3))
    big = Image.fromarray(big).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(big, float)[h:2 * h, w:2 * w] / 255.0


def lowfreq(t, amp, periods=((1, 1), (2, 1), (1, 2), (3, 2)), seed=0):
    """smooth tiling variation (integer periods), no speckle"""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:t.H, 0:t.W]
    n = np.zeros((t.H, t.W))
    for py, px in periods:
        ph = rng.random() * 6.283
        n += np.sin(2 * np.pi * (x * px / t.W + y * py / t.H) + ph)
    return n / len(periods) * amp


# =============================================================================
# block renderer: labels (-1 = mortar) -> flat tone per block, lit top-left, shadowed bottom-right
# =============================================================================
def render_blocks(t, lab, base, tones, mortar, hi=1.35, lo=0.62, bev=2, var=6, grad=0.0, seed=1):
    m = lab < 0
    out = np.zeros_like(t.a)
    ids = np.unique(lab[~m])
    tone = {int(i): tones(int(i)) for i in ids}
    k = np.ones(lab.shape)
    for i, v in tone.items():
        k[lab == i] = v
    out[:] = C(base) * k[..., None]
    if grad:
        # lighter toward the top of each block: distance below the mortar above
        up = np.zeros(lab.shape)
        cur = np.zeros(lab.shape)
        dist = np.full(lab.shape, 99.0)
        for d in range(1, 48 * SS):
            hit = np.roll(m, d, 0) & (dist == 99.0)
            dist[hit] = d
        out *= (1 + grad * np.clip(1 - dist / (32 * SS), 0, 1))[..., None]
    out *= (1 + lowfreq(t, var / 100.0, seed=seed))[..., None]
    B = bev * SS
    top = np.zeros(lab.shape, bool); left = np.zeros(lab.shape, bool)
    bot = np.zeros(lab.shape, bool); right = np.zeros(lab.shape, bool)
    for d in range(1, B + 1):
        top |= np.roll(m, d, 0); left |= np.roll(m, d, 1)
        bot |= np.roll(m, -d, 0); right |= np.roll(m, -d, 1)
    for d in range(1, B // 2 + 1):   # shadow rim is thinner but darker at the groove
        pass
    out[(top | left) & ~m] *= hi
    out[(bot | right) & ~m & ~(top | left)] *= lo
    out[m] = C(mortar)
    t.a = np.clip(out, 0, 255)


def bond_labels(t, rh, widths_fn, mortar=2, y0=0, y1=None, offset_fn=None):
    """rows of height rh (final px), each row's block widths sum to the tile width (wraps)"""
    y1 = t.h if y1 is None else y1
    lab = np.full((t.H, t.W), -1, int)
    nid = 0
    for r in range(int((y1 - y0) // rh)):
        ws = widths_fn(r)
        off = offset_fn(r) if offset_fn else 0
        x = off
        for w in ws:
            xs = (np.arange(int(x * SS), int((x + w) * SS) - mortar * SS)) % t.W
            ys = slice(int((y0 + r * rh) * SS), int((y0 + (r + 1) * rh - mortar) * SS))
            lab[ys, xs] = nid
            nid += 1
            x += w
    return lab


def split_widths(rng, total, choices):
    while True:
        ws = []
        while sum(ws) < total:
            ws.append(int(rng.choice(choices)))
        if sum(ws) == total:
            return ws


def carve(L, pts, dark, light, w=1.0):
    """an engraved crack / groove: dark line with a lit lip under it"""
    L.line([(x + 0.6, y + 0.8) for x, y in pts], light, w)
    L.line(pts, dark, w)


def walk(t, x, y, n, step, dx=(-1, 1), dy=(0.6, 1.4), clampx=None):
    pts = [(x, y)]
    for _ in range(n):
        x += t.r(*dx) * step; y += t.r(*dy) * step
        if clampx:
            x = min(max(x, clampx[0]), clampx[1])
        pts.append((x, y))
    return pts


def plinth(t, stone, trim, mortar, h=28, seam=None):
    """dark stone foot strip with a trim rail, blocks every 32 px, like the kit plinth"""
    y0 = t.h - h
    L = t.layer()
    for x in range(0, t.w, 32):
        L.rect(x, y0 + 4, x + 32, t.h - 2, stone)
        L.rect(x, y0 + 4, x + 32, y0 + 6, scl(stone, 1.5))
        L.rect(x + 30, y0 + 4, x + 32, t.h - 2, mortar)
        L.rect(x, t.h - 5, x + 30, t.h - 2, scl(stone, 0.6))
    L.rect(0, t.h - 2, t.w, t.h, mortar)
    L.rect(0, y0, t.w, y0 + 2, scl(trim, 1.15))
    L.rect(0, y0 + 2, t.w, y0 + 4, scl(trim, 0.55))
    t.comp(L)
    if seam:
        G = t.layer(); G.rect(0, y0 + 2, t.w, y0 + 3.5, seam); t.comp(G, glow=seam, glow_r=2.5, glow_k=0.7)


# =============================================================================
# sets: mood colours taken from the old textures (only as a guide)
# =============================================================================
SETS = {
    'crypt': dict(stone=(62, 61, 67), mortar=(16, 14, 18), plinth=(34, 31, 36), trim=(178, 130, 44), inlay=(92, 20, 26),
                  ceil=(40, 38, 44), floor=(58, 57, 63), floor_alt=(46, 44, 50), crack=(14, 12, 16), gem=(200, 40, 30)),
    'blood': dict(stone=(150, 134, 108), back=(40, 9, 11), mortar=(22, 5, 7), plinth=(62, 40, 36), trim=(200, 180, 140),
                  inlay=(120, 14, 20), ceil=(92, 42, 36), floor=(78, 44, 42), floor_alt=(62, 34, 34), crack=(20, 8, 8),
                  gem=(190, 30, 34), bone=(168, 152, 124)),
    'bog': dict(stone=(84, 68, 42), mortar=(14, 16, 10), plinth=(34, 42, 30), trim=(112, 152, 70), inlay=(50, 96, 42),
                ceil=(50, 62, 44), floor=(44, 54, 40), floor_alt=(36, 46, 34), crack=(12, 16, 10), gem=(150, 240, 110),
                bone=(150, 150, 112)),
    'frost': dict(stone=(70, 106, 152), mortar=(22, 30, 46), plinth=(38, 50, 72), trim=(196, 228, 250), inlay=(62, 112, 164),
                  ceil=(62, 84, 116), floor=(78, 94, 116), floor_alt=(66, 82, 104), crack=(150, 220, 255), gem=(150, 225, 255),
                  bone=(214, 226, 238)),
    'ember': dict(stone=(56, 51, 58), mortar=(8, 6, 8), plinth=(28, 18, 15), trim=(210, 100, 36), inlay=(112, 40, 20),
                  ceil=(42, 36, 40), floor=(52, 48, 53), floor_alt=(42, 38, 43), crack=(255, 110, 26), gem=(255, 150, 50)),
    'void': dict(stone=(54, 41, 90), mortar=(10, 6, 20), plinth=(22, 15, 38), trim=(150, 100, 240), inlay=(74, 38, 146),
                 ceil=(42, 31, 68), floor=(50, 40, 84), floor_alt=(40, 32, 70), crack=(150, 90, 255), gem=(180, 120, 255)),
}
WALL = (128, 256)
FLOOR = (128, 128)


# ---------------------------------------------------------------- crypt
def crypt_stone(t, S):
    lab = bond_labels(t, 32, lambda r: split_widths(t.rng, 128, [32, 48, 64]), y1=t.h - 28,
                      offset_fn=lambda r: (r * 23) % 64)
    render_blocks(t, lab, S['stone'], lambda i: t.r(0.82, 1.12), S['mortar'], grad=0.08, seed=11)
    L = t.layer()
    for _ in range(3):
        carve(L, walk(t, t.r(0, 128), t.r(10, 180), 6, 4), S['crack'], scl(S['stone'], 1.3))
    for _ in range(5):   # chipped corners
        x, y = int(t.r(0, 4)) * 32, int(t.r(0, 7)) * 32
        L.poly([(x, y), (x + t.r(3, 6), y), (x, y + t.r(3, 6))], scl(S['mortar'], 1.6))
    t.comp(L)
    plinth(t, S['plinth'], S['trim'], S['mortar'])


def gold_frame(L, x0, y0, x1, y1, trim, w=4):
    L.rect(x0, y0, x1, y1, scl(trim, 0.5))
    L.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, trim)
    L.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 2, scl(trim, 1.35))
    L.rect(x0 + 1, y0 + 1, x0 + 2, y1 - 1, scl(trim, 1.25))
    L.rect(x0 + w - 1, y0 + w - 1, x1 - w + 1, y1 - w + 1, scl(trim, 0.45))


def panel(t, S, stone_fn):
    stone_fn(t, S)
    L = t.layer()
    x0, y0, x1, y1 = 20, 14, 108, 214
    gold_frame(L, x0, y0, x1, y1, S['trim'], 5)
    ix0, iy0, ix1, iy1 = x0 + 5, y0 + 5, x1 - 5, y1 - 5
    L.rect(ix0, iy0, ix1, iy1, scl(S['inlay'], 0.55))
    cw, ch = (ix1 - ix0) / 3, (iy1 - iy0) / 6
    for i in range(3):
        for j in range(6):
            a0, b0 = ix0 + i * cw + 2, iy0 + j * ch + 2
            a1, b1 = a0 + cw - 4, b0 + ch - 4
            L.rect(a0, b0, a1, b1, scl(S['inlay'], 0.72))
            L.rect(a0, b0, a1, b0 + 1.5, scl(S['inlay'], 1.15))
            L.rect(a0, b0, a0 + 1.5, b1, scl(S['inlay'], 1.3))
            L.rect(a0, b1 - 1.5, a1, b1, scl(S['inlay'], 0.6))
            L.rect(a1 - 1.5, b0, a1, b1, scl(S['inlay'], 0.7))
    for i in range(4):
        for j in range(7):
            cx, cy = ix0 + i * cw, iy0 + j * ch
            L.poly([(cx, cy - 3), (cx + 3, cy), (cx, cy + 3), (cx - 3, cy)], S['trim'])
            L.poly([(cx, cy - 3), (cx + 3, cy), (cx, cy)], scl(S['trim'], 1.35))
    t.comp(L)


def pillar(t, S, medal=None):
    base = S.get('pillar', mix(S['stone'], S['inlay'], 0.25))
    lab = bond_labels(t, 32, lambda r: [128])
    render_blocks(t, lab, base, lambda i: t.r(0.9, 1.08), S['mortar'], grad=0.06, seed=13)
    L = t.layer()
    for x in (12, 34, 56, 72, 94, 116):   # fluting
        L.rect(x, 22, x + 3, 228, scl(base, 0.45)); L.rect(x + 3, 22, x + 4.5, 228, scl(base, 1.35))
    for y0 in (8, 230):
        L.rect(0, y0, 128, y0 + 12, S['trim']); L.rect(0, y0, 128, y0 + 2, scl(S['trim'], 1.35))
        L.rect(0, y0 + 10, 128, y0 + 12, scl(S['trim'], 0.5))
    t.comp(L)
    L = t.layer()
    cx, cy = 64, 128
    L.rect(44, 106, 84, 150, scl(S['trim'], 0.5)); L.rect(46, 108, 82, 148, scl(base, 0.55))
    t.comp(L)
    if medal:
        medal(t, cx, cy)
    else:
        G = t.layer()
        G.poly([(cx, cy - 16), (cx + 13, cy), (cx, cy + 16), (cx - 13, cy)], scl(S['trim'], 0.6))
        G.poly([(cx, cy - 13), (cx + 10, cy), (cx, cy + 13), (cx - 10, cy)], S['gem'])
        G.poly([(cx, cy - 13), (cx - 10, cy), (cx, cy)], scl(S['gem'], 1.3))
        G.poly([(cx, cy + 13), (cx + 10, cy), (cx, cy)], scl(S['gem'], 0.6))
        G.ellipse(cx - 3, cy - 5, 1.6, 1.6, (255, 240, 220, 220))
        t.comp(G, glow=S['gem'] if S.get('glow') else None, glow_r=4)


def ceil(t, S):
    lab = bond_labels(t, 32, lambda r: [64, 64], offset_fn=lambda r: (r % 2) * 32)
    render_blocks(t, lab, S['ceil'], lambda i: t.r(0.82, 1.1), S['mortar'], grad=0.05, seed=17)


def flags(t, S):
    lab = bond_labels(t, 64, lambda r: [64, 64], mortar=2)
    alt = {}
    for i in range(4):
        alt[i] = S['floor'] if (i + i // 2) % 2 == 0 else S['floor_alt']
    # per-flag colour by drawing two passes
    render_blocks(t, lab, (100, 100, 100), lambda i: 1.0, S['mortar'], seed=19, var=5)
    k = t.a / 100.0
    col = np.zeros_like(t.a)
    for i, c in alt.items():
        col[lab == i] = C(c) * t.r(0.92, 1.06)
    col[lab < 0] = C(S['mortar'])
    t.a = np.where((lab < 0)[..., None], col, col * k)


def floor_kind(t, S, kind, set_id):
    flags(t, S)
    L = t.layer()
    glow = None
    if kind in ('cracked',) or (kind == 'warm' and set_id in ('ember',)):
        n = 3 if kind == 'cracked' else 4
        for _ in range(n):
            pts = walk(t, t.r(4, 124), t.r(4, 124), 7, 4, dx=(-0.4, 1.2), dy=(-0.4, 1.2))
            if set_id in ('ember', 'void', 'frost'):
                L.line(pts, S['crack'] + (255,), 1.6 if set_id == 'ember' else 1.2)
                L.line(pts, (255, 230, 150, 255) if set_id == 'ember' else (235, 230, 255, 255), 0.6)
                glow = S['crack']
            else:
                carve(L, pts, S['crack'], scl(S['floor'], 1.45), 1.2)
    if kind == 'warm':
        if set_id == 'crypt':
            for cx in (0, 64, 128):
                for cy in (0, 64, 128):
                    L.poly([(cx, cy - 8), (cx + 8, cy), (cx, cy + 8), (cx - 8, cy)], scl(S['trim'], 0.55))
                    L.poly([(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)], S['trim'])
                    L.poly([(cx, cy - 6), (cx - 6, cy), (cx, cy)], scl(S['trim'], 1.35))
                    L.poly([(cx, cy - 2), (cx + 2, cy), (cx, cy + 2), (cx - 2, cy)], S['gem'])
        elif set_id == 'blood':
            for _ in range(4):
                pool(L, t.r(10, 118), t.r(10, 118), t.r(6, 12), S)
        elif set_id == 'bog':
            for _ in range(4):
                cx, cy, r = t.r(0, 128), t.r(0, 128), t.r(6, 11)
                L.ellipse(cx, cy, r, r * 0.6, (40, 78, 36, 255)); L.ellipse(cx - 1, cy - 1, r * 0.7, r * 0.4, (64, 120, 50, 255))
                L.ellipse(cx - r * 0.3, cy - r * 0.25, r * 0.25, r * 0.12, (150, 210, 110, 255))
        elif set_id == 'frost':
            for _ in range(4):
                rime(L, t.r(0, 128), t.r(0, 128), t.r(7, 12))
        elif set_id == 'void':
            rune_circle(L, 64, 64, 22, S)
            glow = S['crack']
    if kind == 'worn':
        t.a *= (1 + 0.10 * np.clip(1 - np.hypot(*(np.mgrid[0:t.H, 0:t.W] - np.array([t.H / 2, t.W / 2])[:, None, None])) / (t.W * 0.55), 0, 1))[..., None]
        for _ in range(6):
            x, y = int(t.r(0, 2)) * 64 + t.r(0, 1) * 60, int(t.r(0, 2)) * 64
            L.poly([(x, y + 2), (x + t.r(4, 8), y + 2), (x + t.r(1, 3), y + t.r(3, 6))], scl(S['mortar'], 1.5))
    # each set's small signature on every floor
    if set_id == 'void':
        for _ in range(4 if kind != 'warm' else 7):
            glint(L, t.r(0, 128), t.r(0, 128), t.r(2, 3.5), (200, 160, 255, 255))
        glow = S['crack']
    if set_id == 'frost':
        for _ in range(3):
            glint(L, t.r(0, 128), t.r(0, 128), 2.5, (235, 248, 255, 255))
    if set_id == 'blood' and kind != 'warm':
        for _ in range(2 if kind == 'plain' else 1):
            pool(L, t.r(10, 118), t.r(10, 118), t.r(4, 7), S)
    if set_id == 'bog':
        for x in (0, 64):   # moss in the joints
            for y in range(0, 128, 6):
                if t.r() < 0.5:
                    L.ellipse(x + t.r(-1, 1), y, t.r(1.5, 3), t.r(1.5, 3), (60, 108, 46, 255))
    t.comp(L, glow=glow, glow_r=2.5)


def pool(L, cx, cy, r, S):
    L.ellipse(cx, cy, r, r * 0.65, scl(S['inlay'], 0.6) + (255,))
    L.ellipse(cx, cy - 0.5, r * 0.85, r * 0.52, S['inlay'] + (255,))
    L.ellipse(cx - r * 0.35, cy - r * 0.25, r * 0.3, r * 0.12, (220, 90, 90, 255))


def glint(L, cx, cy, r, c):
    L.poly([(cx, cy - r), (cx + r * 0.25, cy), (cx, cy + r), (cx - r * 0.25, cy)], c)
    L.poly([(cx - r, cy), (cx, cy - r * 0.25), (cx + r, cy), (cx, cy + r * 0.25)], c)


def rime(L, cx, cy, r):
    L.ellipse(cx, cy, r, r * 0.6, (150, 180, 214, 150))
    L.ellipse(cx - 1, cy - 1, r * 0.7, r * 0.4, (200, 226, 246, 200))
    L.ellipse(cx - r * 0.3, cy - r * 0.2, r * 0.25, r * 0.12, (245, 252, 255, 255))


RUNES = [  # stroke glyphs in a 10 x 14 box
    [[(5, 0), (5, 14)], [(5, 4), (10, 0)], [(5, 8), (0, 4)]],
    [[(0, 0), (5, 14), (10, 0)], [(2, 7), (8, 7)]],
    [[(0, 14), (0, 0), (10, 5), (0, 9)], [(5, 9), (10, 14)]],
    [[(5, 0), (10, 7), (5, 14), (0, 7), (5, 0)], [(5, 4), (5, 10)]],
    [[(0, 0), (10, 14)], [(10, 0), (0, 14)], [(0, 7), (10, 7)]],
    [[(2, 0), (2, 14)], [(8, 0), (8, 14)], [(2, 3), (8, 11)]],
]


def rune(L, x, y, k, S, s=1.0):
    for st in RUNES[k % len(RUNES)]:
        pts = [(x + px * s, y + py * s) for px, py in st]
        L.line(pts, scl(S['crack'], 0.55) + (255,), 2.4 * s)
    for st in RUNES[k % len(RUNES)]:
        pts = [(x + px * s, y + py * s) for px, py in st]
        L.line(pts, (225, 200, 255, 255), 0.9 * s)


def rune_circle(L, cx, cy, r, S):
    L.ellipse(cx, cy, r + 1.5, r + 1.5, scl(S['crack'], 0.55) + (255,))
    L.ellipse(cx, cy, r, r, (0, 0, 0, 0))
    L.ellipse(cx, cy, r - 0.1, r - 0.1, S['floor'] + (255,))
    for i in range(6):
        a = i * math.pi / 3
        rune(L, cx + math.cos(a) * (r - 8) - 3.5, cy + math.sin(a) * (r - 8) - 5, i, S, 0.7)


def crypt_banner(t, S):
    crypt_stone(t, S)
    L = t.layer()
    x0, x1, y0, y1 = 18, 110, 8, 200
    L.rect(x0 + 3, y0 + 3, x1 + 3, y1 + 3, (0, 0, 0, 110))
    t.comp(L)
    cloth(t, S, x0, x1, y0, y1, banner=True)


def cloth(t, S, x0, x1, y0, y1, banner=False, emblem_w=60):
    red = (120, 22, 26)
    L = t.layer()
    if banner:   # swallow-tail bottom
        mid = (x0 + x1) / 2
        L.poly([(x0, y0), (x1, y0), (x1, y1 + 14), (mid, y1 - 6), (x0, y1 + 14)], red + (255,))
    else:
        L.rect(x0, y0, x1, y1, red + (255,))
    t.comp(L)
    # folds: smooth vertical light/dark bands inside the cloth
    yy, xx = np.mgrid[0:t.H, 0:t.W] / SS
    inside = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1 + 16)
    fold = 1 + 0.16 * np.sin((xx - x0) / (x1 - x0) * 2 * np.pi * 3)
    t.a[inside] = np.minimum(t.a[inside], 255)
    sel = inside & (np.abs(t.a - C(red)).sum(-1) < 40)
    t.a[sel] *= fold[sel][..., None]
    L = t.layer()
    gold = S['trim']
    for xa in (x0, x1 - 5):
        L.rect(xa, y0, xa + 5, y1 if not banner else y1 + 6, gold); L.rect(xa, y0, xa + 1.5, y1 if not banner else y1 + 6, scl(gold, 1.35))
        L.rect(xa + 4, y0, xa + 5, y1 if not banner else y1 + 6, scl(gold, 0.55))
    if banner:
        L.rect(x0 - 6, y0 - 2, x1 + 6, y0 + 8, scl(gold, 0.55)); L.rect(x0 - 6, y0 - 2, x1 + 6, y0 + 1, scl(gold, 1.4))
        L.rect(x0 - 6, y0 + 1, x1 + 6, y0 + 6, gold)
        for ex in (x0 - 9, x1 + 9):
            L.ellipse(ex, y0 + 3, 4, 4, scl(gold, 0.6)); L.ellipse(ex - 0.8, y0 + 2.2, 2.6, 2.6, scl(gold, 1.3))
        mid = (x0 + x1) / 2
        L.line([(x0 + 2, y1 + 12), (mid, y1 - 8), (x1 - 2, y1 + 12)], gold, 3)
        # gold rod and diamond under the demon, like the kit banner
        L.rect(mid - 1.5, 128, mid + 1.5, 176, gold)
        L.poly([(mid, 140), (mid + 12, 152), (mid, 164), (mid - 12, 152)], scl(gold, 0.55))
        L.poly([(mid, 143), (mid + 9, 152), (mid, 161), (mid - 9, 152)], S['gem'])
        L.poly([(mid, 143), (mid - 9, 152), (mid, 152)], scl(S['gem'], 1.35))
    t.comp(L)
    cy = 76 if banner else (y0 + y1) / 2
    t.sprite('demon_gold', (x0 + x1) / 2, cy, emblem_w, shadow=0.5)


def crypt_cloth(t, S):
    t.a[:] = C((120, 22, 26))
    cloth(t, S, 10, 118, -2, 258, emblem_w=54)


def crypt_carpet(t, S):
    red = C((110, 20, 24))
    t.a[:] = red
    t.a *= (1 + lowfreq(t, 0.04, seed=5))[..., None]
    L = t.layer(); g = S['trim']
    for xa in (6, 112):
        L.rect(xa, 0, xa + 10, 128, scl(g, 0.55)); L.rect(xa + 1, 0, xa + 9, 128, g)
        L.rect(xa + 1, 0, xa + 2.5, 128, scl(g, 1.35)); L.rect(xa + 4, 0, xa + 6, 128, scl(red, 0.6))
    L.rect(0, 0, 6, 128, scl(red, 0.55)); L.rect(122, 0, 128, 128, scl(red, 0.55))
    for cy in (0, 64, 128):
        L.poly([(64, cy - 26), (92, cy), (64, cy + 26), (36, cy)], scl(g, 0.55))
        L.poly([(64, cy - 22), (88, cy), (64, cy + 22), (40, cy)], scl(red, 0.62))
        L.poly([(64, cy - 9), (73, cy), (64, cy + 9), (55, cy)], g)
        L.poly([(64, cy - 9), (55, cy), (64, cy)], scl(g, 1.35))
    for cy in (32, 96):
        L.ellipse(64, cy, 4, 4, scl(g, 0.6)); L.ellipse(63.3, cy - 0.7, 2.5, 2.5, scl(g, 1.2))
    t.comp(L)


def crypt_gold(t, S):
    g = S['trim']
    t.a[:] = C(g)
    L = t.layer()
    L.rect(0, 0, 64, 6, scl(g, 1.35)); L.rect(0, 6, 64, 8, scl(g, 0.5))
    L.rect(0, 56, 64, 58, scl(g, 1.2)); L.rect(0, 58, 64, 64, scl(g, 0.5))
    for cx in (0, 32, 64):
        L.poly([(cx, 14), (cx + 17, 32), (cx, 50), (cx - 17, 32)], scl(g, 0.5))
        L.poly([(cx, 18), (cx + 13, 32), (cx, 46), (cx - 13, 32)], S['gem'])
        L.poly([(cx, 18), (cx - 13, 32), (cx, 32)], scl(S['gem'], 1.35))
        L.poly([(cx, 46), (cx + 13, 32), (cx, 32)], scl(S['gem'], 0.6))
        L.ellipse(cx - 3, 26, 1.6, 1.6, (255, 230, 210))
    for cx in (16, 48):
        L.ellipse(cx, 32, 3, 3, scl(g, 0.55)); L.ellipse(cx - 0.6, 31.4, 1.8, 1.8, scl(g, 1.4))
    t.comp(L)


# ---------------------------------------------------------------- blood: stacked bones and skulls
def bone(L, x, y, length, th, c, back):
    """a horizontal leg bone, drawn as a shaded rounded form (shadow, body, lit top, outline)"""
    r = th * 0.75
    def shape(dy, k, shrink=0.0):
        col = scl(c, k) + (255,)
        L.rect(x + r, y - th / 2 + dy + shrink, x + length - r, y + th / 2 + dy - shrink, col)
        for ex in (x + r * 0.9, x + length - r * 0.9):
            L.ellipse(ex, y - th * 0.35 + dy, r - shrink, r - shrink, col)
            L.ellipse(ex, y + th * 0.35 + dy, r - shrink, r - shrink, col)
    shape(1.0, 0.0)
    L_ = L
    col = back + (255,)
    shape(0.6, 0.42)          # dark rim / underside
    shape(-0.2, 0.86, 0.8)    # body
    L.rect(x + r, y - th / 2 + 1.4, x + length - r, y - th / 2 + 2.6, scl(c, 1.18) + (255,))   # lit top of the shaft
    for ex in (x + r * 0.9, x + length - r * 0.9):
        L.ellipse(ex - 0.6, y - th * 0.45, r * 0.45, r * 0.4, scl(c, 1.2) + (255,))


def blood_stone(t, S, panel_mode=False):
    t.a[:] = C(S['back'])
    t.a *= (1 + lowfreq(t, 0.08, seed=3))[..., None]
    L = t.layer()
    rh = 12
    for r in range(int((t.h - 28) // rh)):
        y = r * rh + rh / 2
        x = t.r(0, 40)
        while x < 128 + t.r(0, 4):
            ln = t.r(34, 52)
            bone(L, x, y, ln, 7.5, S['bone'], S['back'])
            x += ln + t.r(1, 4)
    t.comp(L)
    # dark niches with real 3D skulls
    for i, (cx, cy, v, w) in enumerate([(32, 60, 'skull_front_jaw', 34), (96, 132, 'skull_tilt_nojaw', 32), (40, 186, 'skull_tilt_jaw', 30)]):
        if panel_mode and i == 1:
            continue
        N = t.layer()
        N.ellipse(cx, cy + 2, w * 0.66, w * 0.72, scl(S['back'], 0.9) + (255,))
        N.ellipse(cx, cy + 2, w * 0.6, w * 0.66, (14, 4, 6, 255))
        t.comp(N)
        t.sprite(v, cx, cy + 1, w, tint=scl(S['bone'], 1.12), shadow=0.0)
    drips(t, S, [(10, 4), (52, 0), (74, 30), (114, 10), (88, 150)])
    L = t.layer()
    for _ in range(8):   # a few clean spatters
        cx, cy, r = t.r(0, 128), t.r(0, 220), t.r(0.8, 1.8)
        L.ellipse(cx, cy, r, r, S['inlay'] + (255,))
    t.comp(L)
    plinth(t, S['plinth'], S['trim'], S['mortar'])
    L = t.layer()
    for x in range(2, 128, 8):   # bone ends along the foot
        L.ellipse(x + 2, t.h - 14, 3.2, 3.2, scl(S['bone'], 0.45) + (255,))
        L.ellipse(x + 1.6, t.h - 14.4, 2.6, 2.6, S['bone'] + (255,))
        L.ellipse(x + 1.2, t.h - 15.2, 1.1, 1.1, scl(S['bone'], 1.25) + (255,))
    t.comp(L)


def drips(t, S, starts, col=None, hi=None, glow=None):
    col = col or S['inlay']; hi = hi or (200, 40, 44)
    L = t.layer()
    for x, y in starts:
        n = t.r(30, 70)
        L.poly([(x - 2.2, y), (x + 2.2, y), (x + 1.2, y + n), (x - 1.2, y + n)], scl(col, 0.8) + (255,))
        L.ellipse(x, y + n + 1, 2.6, 3.4, scl(col, 0.8) + (255,))
        L.line([(x - 0.6, y + 2), (x - 0.4, y + n)], hi + (255,), 0.8)
        L.ellipse(x - 0.8, y + n, 0.9, 1.2, (255, 200, 190, 255) if glow is None else (240, 255, 220, 255))
        L.rect(x - 4, y - 1, x + 4, y + 2, scl(col, 0.8) + (255,))
    t.comp(L, glow=glow, glow_r=2.5, glow_k=0.6)


def blood_medal(t, cx, cy):
    t.sprite('skull_front_jaw', cx, cy, 30, tint=scl(SETS['blood']['bone'], 1.12), shadow=0.4)


# ---------------------------------------------------------------- bog: rotten planks, moss, slime
def bog_stone(t, S):
    ws = [22, 18, 24, 20, 26, 18]
    lab = np.full((t.H, t.W), -1, int)
    x = 0; nid = 0
    for i, w in enumerate(ws):
        cut = t.r(60, 200)
        xs = slice(int(x * SS), int((x + w - 2) * SS))
        lab[:int(cut * SS) - 2 * SS, xs] = nid; lab[int(cut * SS):, xs] = nid + 1
        nid += 2; x += w
    lab[:, :] = np.where(np.arange(t.H)[:, None] >= (t.h - 28) * SS, -1, lab)
    render_blocks(t, lab, S['stone'], lambda i: t.r(0.78, 1.1), S['mortar'], hi=1.3, lo=0.6, seed=23)
    # rot: darker toward the foot
    yy = np.arange(t.H)[:, None] / t.H
    t.a *= (1 - 0.35 * np.clip((yy - 0.4) / 0.6, 0, 1))[..., None]
    L = t.layer()
    x = 0
    for w in ws:   # grain lines and knots
        for k in range(3):
            gx = x + 3 + k * (w - 6) / 2
            pts = [(gx + math.sin(y * 0.05 + k) * 1.5, y) for y in range(0, 230, 10)]
            L.line(pts, scl(S['stone'], 0.62) + (255,), 0.8)
        ky = t.r(20, 200)
        L.ellipse(x + w / 2, ky, 3.5, 5, scl(S['stone'], 0.45) + (255,)); L.ellipse(x + w / 2 - 0.5, ky - 0.5, 1.8, 3, scl(S['stone'], 0.85) + (255,))
        x += w
    t.comp(L)
    # roots creeping down
    L = t.layer()
    for rx in (44, 100):
        pts = [(rx, -2)]
        for _ in range(9):
            px, py = pts[-1]; pts.append((px + t.r(-4, 4), py + t.r(9, 14)))
        L.line(pts, (30, 20, 12, 255), 3); L.line([(p[0] - 0.7, p[1]) for p in pts], (82, 60, 36, 255), 1)
        bx, by = pts[4]; br = [(bx, by), (bx + 8, by + 10), (bx + 10, by + 22)]
        L.line(br, (30, 20, 12, 255), 2); L.line([(p[0] - 0.5, p[1]) for p in br], (82, 60, 36, 255), 0.7)
    t.comp(L)
    drips(t, S, [(12, 30), (66, 12), (114, 50)], col=(96, 176, 62), hi=(200, 255, 140), glow=(110, 220, 70))
    # moss crawling up from the foot (clean blobby edge with a lit rim)
    L = t.layer()
    xs = np.arange(0, 129, 2)
    hgt = 16 + 9 * np.sin(xs / 128 * 2 * np.pi * 3 + 1) + 5 * np.sin(xs / 128 * 2 * np.pi * 7)
    y0 = t.h - 28
    top = [(x, y0 - h) for x, h in zip(xs, hgt)]
    L.poly([(0, y0 + 6)] + top + [(128, y0 + 6)], (40, 78, 34, 255))
    L.line(top, (92, 150, 62, 255), 2.2)
    L.line([(x, y - 1.4) for x, y in top], (150, 206, 96, 255), 0.8)
    for _ in range(4):   # moss patches higher up
        cx, cy = t.r(0, 128), t.r(20, 150)
        for k in range(4):
            L.ellipse(cx + t.r(-6, 6), cy + t.r(-3, 3), t.r(3, 6), t.r(2, 4), (48, 92, 40, 255))
        L.ellipse(cx - 1, cy - 2, 3, 1.5, (120, 180, 80, 255))
    t.comp(L)
    plinth(t, S['plinth'], S['trim'], S['mortar'])
    # a skull and bones half sunk in the moss
    L = t.layer()
    bone(L, 70, y0 - 6, 34, 6, S['bone'], (30, 40, 26))
    t.comp(L)
    t.sprite('skull_tilt_nojaw', 30, y0 - 10, 26, tint=S['bone'], shadow=0.3)
    L = t.layer()
    L.poly([(14, y0 + 2)] + [(x, y0 - 4 - 3 * math.sin(x * 0.4)) for x in range(14, 48, 3)] + [(48, y0 + 2)], (40, 78, 34, 255))
    t.comp(L)
    # glowing fungus caps
    G = t.layer()
    for fx, fy in [(8, y0 - 18), (16, y0 - 22), (92, y0 - 14), (100, y0 - 20), (58, 90), (63, 94), (120, 150)]:
        G.rect(fx - 0.6, fy, fx + 0.6, fy + 4, (200, 230, 170, 255))
        G.poly([(fx - 4, fy + 0.5), (fx, fy - 3), (fx + 4, fy + 0.5)], (110, 220, 90, 255))
        G.ellipse(fx - 1.2, fy - 1, 1.2, 0.8, (210, 255, 170, 255))
    t.comp(G, glow=(110, 230, 80), glow_r=3)


# ---------------------------------------------------------------- frost: ice facets, icicles, frozen skull
def frost_stone(t, S):
    rng = t.rng
    pts = np.array([[rng.random() * 128, rng.random() * 228, rng.random()] for _ in range(16)])
    yy, xx = np.mgrid[0:t.H, 0:t.W] / SS
    best = np.full(xx.shape, 1e9); second = np.full(xx.shape, 1e9); lab = np.zeros(xx.shape, int)
    for i, (px, py, _) in enumerate(pts):
        for ox in (-128, 0, 128):
            for oy in (-256, 0, 256):
                d = np.hypot(xx - px - ox, (yy - py - oy) * 0.8)
                upd = d < best
                second = np.where(upd, best, np.minimum(second, d)); best = np.where(upd, d, best)
                lab = np.where(upd, i, lab)
    edge = (second - best) < 1.6
    lab = np.where(edge, -1, lab)
    render_blocks(t, lab, S['stone'], lambda i: 0.85 + 0.3 * pts[i, 2], S['mortar'], hi=1.55, lo=0.7, bev=1, seed=29)
    # soft diagonal sheen across each facet
    sheen = 1 + 0.12 * np.sin((xx + yy * 1.6) * 0.06)
    t.a *= sheen[..., None]
    t.a[edge] = C(S['trim']) * 0.95   # cracks between facets read bright
    L = t.layer()
    # a long blue crack
    crack = walk(t, 70, 150, 9, 5, dx=(0.2, 1.2), dy=(0.0, 0.8))
    L.line(crack, (90, 170, 230, 255), 2.4); L.line(crack, (200, 240, 255, 255), 0.9)
    t.comp(L, glow=(120, 200, 255), glow_r=2.5, glow_k=0.6)
    # frozen skull: 3D skull under a pane of ice
    t.sprite('skull_front_jaw', 40, 120, 34, tint=S['bone'], shadow=0.4)
    L = t.layer()
    L.poly([(18, 94), (64, 98), (60, 150), (20, 146)], (150, 200, 240, 80))
    L.line([(26, 100), (54, 140)], (240, 250, 255, 150), 1.4); L.line([(30, 100), (40, 112)], (240, 250, 255, 120), 0.8)
    t.comp(L)
    # frost rime under the cap and icicles hanging from it
    L = t.layer()
    L.rect(0, 0, 128, 5, (215, 236, 252, 255)); L.rect(0, 5, 128, 6, (130, 170, 210, 255))
    x = 2
    while x < 126:
        ln = t.r(8, 30); w = t.r(3, 6)
        L.poly([(x, 5), (x + w, 5), (x + w * 0.45, 5 + ln)], (150, 200, 240, 255))
        L.poly([(x + 0.5, 5), (x + w * 0.45, 5), (x + w * 0.4, 5 + ln * 0.9)], (235, 248, 255, 255))
        x += w + t.r(2, 9)
    for _ in range(8):
        glint(L, t.r(0, 128), t.r(20, 220), t.r(1.8, 3), (240, 250, 255, 255))
    t.comp(L)
    plinth(t, S['plinth'], S['trim'], S['mortar'])
    L = t.layer()
    for _ in range(5):
        rime(L, t.r(0, 128), t.h - 26, t.r(6, 12))
    t.comp(L)


# ---------------------------------------------------------------- ember: basalt columns, lava veins
def ember_stone(t, S):
    lab = np.full((t.H, t.W), -1, int)
    nid = 0
    for c in range(4):
        x0, x1 = c * 32, c * 32 + 30
        y = 0
        joints = sorted(t.r(10, 220) for _ in range(3))
        edges = [0] + [int(j) for j in joints] + [t.h - 28]
        for a, b in zip(edges[:-1], edges[1:]):
            lab[int(a * SS):int((b - 2) * SS), int(x0 * SS):int(x1 * SS)] = nid; nid += 1
    render_blocks(t, lab, S['stone'], lambda i: t.r(0.8, 1.1), S['mortar'], hi=1.45, lo=0.6, seed=31)
    xx = (np.arange(t.W) / SS) % 32
    cyl = 0.62 + 0.55 * np.sin(np.clip(xx / 30, 0, 1) * np.pi) ** 0.7 * (1.05 - 0.25 * xx / 30)
    m = lab >= 0
    t.a[m] *= cyl[None, :].repeat(t.H, 0)[m][..., None]
    # soot: soft dark smears from the top
    L = t.layer()
    for _ in range(4):
        cx = t.r(0, 128)
        L.ellipse(cx, t.r(0, 30), t.r(10, 18), t.r(25, 50), (10, 8, 10, 90))
    L.img = L.img.filter(ImageFilter.GaussianBlur(6 * SS))
    t.comp(L)
    # lava veins: glowing core, bright centre line
    L = t.layer()
    for n in range(4):
        pts = walk(t, t.r(4, 124), t.r(0, 60) + n * 40, 10, 5, dx=(-0.8, 0.8), dy=(0.6, 1.2))
        L.line(pts, (200, 50, 14, 255), 3.2)
        L.line(pts, (255, 120, 30, 255), 1.8)
        L.line(pts, (255, 220, 120, 255), 0.7)
    for _ in range(9):   # embers stuck in the stone
        cx, cy = t.r(0, 128), t.r(0, 220)
        L.ellipse(cx, cy, 1.4, 1.4, (255, 190, 80, 255)); L.ellipse(cx, cy, 0.6, 0.6, (255, 250, 210, 255))
    t.comp(L, glow=(255, 90, 20), glow_r=4, glow_k=1.1)
    plinth(t, S['plinth'], S['trim'], S['mortar'], seam=(255, 110, 30))


# ---------------------------------------------------------------- void: polished slabs, runes, the eye
def void_stone(t, S):
    lab = bond_labels(t, 76, lambda r: [64, 64], y1=t.h - 28, offset_fn=lambda r: (r % 2) * 32, mortar=2)
    render_blocks(t, lab, S['stone'], lambda i: t.r(0.88, 1.1), S['mortar'], hi=1.5, lo=0.6, seed=37)
    yy, xx = np.mgrid[0:t.H, 0:t.W] / SS
    band = np.exp(-((((xx - yy * 0.55) % 64) - 32) / 10) ** 2) * 0.22   # polished sheen across the slabs
    m = lab >= 0
    t.a[m] *= (1 + band[m])[..., None]
    L = t.layer()
    for i, (x, y) in enumerate([(8, 10), (106, 20), (10, 170), (108, 160), (60, 192)]):
        rune(L, x, y, i, S)
    # violet tendrils from the eye
    for sx in (44, 84):
        pts = [(sx + math.sin(j * 0.45) * 4, 96 + j * 4) for j in range(18)]
        L.line(pts, (90, 50, 170, 255), 2.2); L.line(pts, (170, 120, 255, 255), 0.7)
    t.comp(L, glow=S['crack'], glow_r=3, glow_k=1.0)
    # the carved eye
    cx, cy = 64, 84
    L = t.layer()
    L.rect(34, 64, 94, 104, scl(S['stone'], 0.5) + (255,)); L.rect(36, 66, 92, 102, scl(S['stone'], 0.75) + (255,))
    t.comp(L)
    L = t.layer()
    almond = [(cx + 24 * math.cos(a), cy + 11 * math.sin(a) * (1 - 0.25 * math.cos(a) ** 2)) for a in np.linspace(0, 2 * math.pi, 40)]
    L.poly(almond, (12, 6, 22, 255))
    inner = [(cx + 21 * math.cos(a), cy + 8.6 * math.sin(a) * (1 - 0.25 * math.cos(a) ** 2)) for a in np.linspace(0, 2 * math.pi, 40)]
    L.poly(inner, (206, 192, 230, 255))
    L.ellipse(cx, cy, 8, 8, (90, 40, 180, 255)); L.ellipse(cx, cy, 6.5, 6.5, (150, 80, 255, 255))
    L.ellipse(cx - 1, cy - 1, 4.5, 4.5, (190, 130, 255, 255))
    L.rect(cx - 1.2, cy - 6, cx + 1.2, cy + 6, (8, 4, 16, 255))
    L.ellipse(cx - 3, cy - 3, 1.5, 1.5, (255, 255, 255, 255))
    L.line([(cx - 21, cy - 6), (cx, cy - 9.5), (cx + 21, cy - 6)], (110, 90, 140, 255), 1.2)   # lid shadow
    t.comp(L)
    t.a[int((cy - 9) * SS):int((cy - 6) * SS), int((cx - 18) * SS):int((cx + 18) * SS)] *= 0.85
    plinth(t, S['plinth'], S['trim'], S['mortar'], seam=(150, 90, 255))


STONE = {'crypt': crypt_stone, 'blood': blood_stone, 'bog': bog_stone, 'frost': frost_stone, 'ember': ember_stone, 'void': void_stone}
SEED = {'crypt': 100, 'blood': 200, 'bog': 300, 'frost': 400, 'ember': 500, 'void': 600}


def main():
    sizes = {}
    for sid, S in SETS.items():
        S.setdefault('glow', sid in ('ember', 'void', 'bog', 'frost'))
        out = os.path.join(DST, sid)
        base = SEED[sid]
        jobs = [('texStone', WALL, lambda t: STONE[sid](t, S)),
                ('texPanel', WALL, lambda t: panel(t, S, (lambda tt, SS_: blood_stone(tt, SS_, True)) if sid == 'blood' else STONE[sid])),
                ('texPillar', WALL, lambda t: pillar(t, S, blood_medal if sid == 'blood' else None)),
                ('texCeil', FLOOR, lambda t: ceil(t, S)),
                ('texFloor', FLOOR, lambda t: floor_kind(t, S, 'plain', sid)),
                ('texFloor2', FLOOR, lambda t: floor_kind(t, S, 'cracked', sid)),
                ('texFloor3', FLOOR, lambda t: floor_kind(t, S, 'warm', sid)),
                ('texFloorEdge', FLOOR, lambda t: floor_kind(t, S, 'worn', sid))]
        if sid == 'crypt':
            jobs += [('texBanner', WALL, lambda t: crypt_banner(t, S)),
                     ('texCloth', WALL, lambda t: crypt_cloth(t, S)),
                     ('texCarpet', FLOOR, lambda t: crypt_carpet(t, S)),
                     ('texGold', (64, 64), lambda t: crypt_gold(t, S))]
        for k, (name, (w, h), fn) in enumerate(jobs):
            t = Tex(w, h, base + k)
            fn(t)
            sizes[f'{sid}/{name}'] = t.save(os.path.join(out, name + '.png'))
    for k, v in sizes.items():
        print(k, '%dx%d' % v)


if __name__ == '__main__':
    main()
