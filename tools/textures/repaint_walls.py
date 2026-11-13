"""Crimson Halls-style repaint of the game's painted wall textures (art only; src/ is untouched).

Reads  assets/textures/walls/original/<set>/<name>.png  (made by dump_wall_textures.js)
Writes assets/textures/walls/v2/<set>/<name>.png        at exactly 2x, same name.

Same approach as assets/models/env/crimson_halls (PS2 look):
  * 2x nearest upscale keeps every original shape, colour and motif (no new themes)
  * bevelled blocks: 1 px highlight under/left of every mortar groove, 1 px shadow above/right
  * edge wear chips on the lit edges, small dark pits, soft mottling
  * ordered (Bayer) dither, then a hard quantize to a limited palette (<=16 colours) built
    from the texture itself plus its accent colours (gold, lava, runes, blood) so mood holds
  * every filter wraps (np.roll / integer-period noise), so tiles stay as seamless as the original
Deterministic: fixed seeds, no time-based randomness.
usage: python3 tools/textures/repaint_walls.py [src_dir] [dst_dir]"""
import os, sys, zlib, glob
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'assets/textures/walls/original')
DST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'assets/textures/walls/v2')
PAL_SIZE = 16
BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0) - 0.47

def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114

def wrap_blur(x, r=2):
    acc = np.zeros_like(x)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            acc += np.roll(np.roll(x, dy, 0), dx, 1)
    return acc / (2 * r + 1) ** 2

def wrap_noise(h, w, rng, periods=((1, 1), (2, 1), (1, 2), (3, 2))):
    """low-frequency mottling with integer periods so it tiles exactly"""
    y, x = np.mgrid[0:h, 0:w]
    n = np.zeros((h, w))
    for py, px in periods:
        ph = rng.random(2) * 6.283
        n += np.sin(y / h * 6.283 * py + ph[0]) * np.cos(x / w * 6.283 * px + ph[1])
    return n / len(periods)

def label_wrap(mask):
    """4-connected labels of mask with wrap-around (so a block cut by the tile edge is one block)"""
    h, w = mask.shape
    lab = -np.ones((h, w), int); n = 0
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or lab[sy, sx] >= 0:
                continue
            stack = [(sy, sx)]; lab[sy, sx] = n
            while stack:
                y, x = stack.pop()
                for ny, nx in ((y - 1) % h, x), ((y + 1) % h, x), (y, (x - 1) % w), (y, (x + 1) % w):
                    if mask[ny, nx] and lab[ny, nx] < 0:
                        lab[ny, nx] = n; stack.append((ny, nx))
            n += 1
    return lab, n

def chroma(a):
    return a.max(-1) - a.min(-1)

def build_palette(proc, orig):
    """12-ish base colours by median cut of the repainted image + up to 4 accents from the original"""
    o = orig.reshape(-1, 3)
    L, C = lum(o), chroma(o)
    medL, medC = np.median(L), np.median(C)
    acc_mask = (C > max(medC * 2.2, medC + 45)) | (L > medL + 70)
    accents = []
    if acc_mask.any():
        cols, counts = np.unique(o[acc_mask].astype(np.uint8), axis=0, return_counts=True)
        order = np.argsort(-counts)
        for i in order:
            c = cols[i].astype(float)
            if all(np.abs(c - a).sum() > 60 for a in accents):
                accents.append(c)
            if len(accents) == 4:
                break
    nbase = PAL_SIZE - len(accents)
    q = Image.fromarray(np.clip(proc, 0, 255).astype(np.uint8)).quantize(nbase, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    base = np.array(q.getpalette()[:nbase * 3], float).reshape(-1, 3)
    return np.vstack([base] + ([np.array(accents)] if accents else []))

def map_to(img, pal):
    w = np.array([0.30, 0.59, 0.11]) * 3
    d = (((img[:, :, None, :] - pal[None, None]) ** 2) * w).sum(-1)
    return pal[d.argmin(-1)]

def repaint(path):
    im = Image.open(path).convert('RGB')
    o = np.array(im, float)
    a = np.array(im.resize((im.width * 2, im.height * 2), Image.NEAREST), float)
    h, w = a.shape[:2]
    rng = np.random.default_rng(zlib.crc32(os.path.relpath(path, SRC).encode()))
    L = lum(a)
    local = wrap_blur(L, 3)
    groove = L < local * 0.62                       # mortar lines, flutes, cracks, frame shadows
    solid = ~groove
    up_g, dn_g = np.roll(groove, 1, 0), np.roll(groove, -1, 0)   # groove above / below this pixel
    lf_g, rt_g = np.roll(groove, 1, 1), np.roll(groove, -1, 1)
    hi = solid & (up_g | lf_g)
    lo = solid & (dn_g | rt_g) & ~hi
    out = a.copy()
    # per-block tone: every stone/plank/tile gets its own slight value shift, like the kit's bricks
    lab, n = label_wrap(solid)
    small = np.bincount(lab[lab >= 0], minlength=n) < h * w * 0.25        # leave big backgrounds alone
    tone = 1.0 + (rng.random(n) - 0.5) * 0.18 * small
    tmap = np.ones((h, w)); tmap[solid] = tone[lab[solid]]
    out *= tmap[..., None]
    # soft mottling (integer-period, tiles exactly)
    out *= 1.0 + 0.08 * wrap_noise(h, w, rng)[..., None]
    # chunky 2 px bevel (1 original pixel) with warm top-left torch light
    warm = np.array([1.0, 0.90, 0.74])
    hi2 = solid & (np.roll(up_g, 1, 0) | np.roll(lf_g, 1, 1)) & ~hi
    lo2 = solid & (np.roll(dn_g, -1, 0) | np.roll(rt_g, -1, 1)) & ~hi & ~hi2 & ~lo
    out[hi] = out[hi] * 1.32 + 22 * warm
    out[hi2] = out[hi2] * 1.12 + 8 * warm
    out[lo] = out[lo] * 0.58
    out[lo2] = out[lo2] * 0.80
    out[groove] = out[groove] * 0.65
    # edge wear chips on lit edges, pits with a lit rim on flat faces
    chips = hi & (rng.random((h, w)) < 0.20)
    out[chips] = out[chips] * 1.12 + 20 * warm
    flat = solid & ~hi & ~lo & ~hi2 & ~lo2
    pits = flat & (rng.random((h, w)) < 0.03)
    out[pits] = out[pits] * 0.55
    pit_lit = np.roll(np.roll(pits, 1, 0), 1, 1) & flat & ~pits
    out[pit_lit] = out[pit_lit] * 1.15 + 8
    # ordered dither so gradients break into PS2-style pixel steps
    by = BAYER4[np.arange(h)[:, None] % 4, np.arange(w)[None, :] % 4]
    out += (by * 14.0)[..., None]
    out = np.clip(out, 0, 255)
    pal = build_palette(out, o)
    res = map_to(out, pal).astype(np.uint8)
    return Image.fromarray(res), len(np.unique(res.reshape(-1, 3), axis=0))

def seam_score(img):
    a = np.array(img, float)
    return np.abs(a[0] - a[-1]).mean(), np.abs(a[:, 0] - a[:, -1]).mean()

if __name__ == '__main__':
    for p in sorted(glob.glob(os.path.join(SRC, '*', '*.png'))):
        rel = os.path.relpath(p, SRC)
        img, ncol = repaint(p)
        dst = os.path.join(DST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        img.save(dst, optimize=True)
        print(f'{rel:28s} {img.width}x{img.height} colours={ncol}')
