"""Crimson Halls modular wall kit (first art-style pass), PS2 / Snake Eater low poly.

Builds, from scratch and headless:
  * crimson_halls_atlas.png  - one 256x256 albedo atlas, 16-colour palette, nearest-friendly
  * crimson_halls_kit.blend  - every piece side by side (source file)
  * <tmp>/ch_<piece>.blend   - one .blend per piece, fed to tools/blender/export_lowpoly.py

Usage (from the repo root):
  blender -b --python assets/models/env/crimson_halls/build_crimson_halls.py -- \
      --out-dir assets/models/env/crimson_halls --piece-dir /tmp/crimson_halls_pieces
Then export each piece with tools/blender/export_lowpoly.py (see export_all.sh).

Blender space: Z up, metres. The room side of every wall faces Blender -Y, which the
exporter's +Y-up conversion turns into glTF +Z. Grid is 2 m (the game's CELL).
"""
from __future__ import annotations

import argparse
import math
import os
import struct
import sys
import zlib

import bpy
import numpy as np
from mathutils import Matrix, Vector

TEX = 256

# ---- palette: 16 colours, nothing else is ever written to the atlas --------
PAL = {
    'mortar':      (22, 6, 8),
    'brick_dark':  (74, 14, 16),
    'brick_mid':   (112, 22, 24),
    'brick_light': (146, 36, 32),
    'brick_hi':    (178, 62, 44),
    'stone_dark':  (38, 24, 26),
    'stone_mid':   (64, 42, 40),
    'stone_light': (92, 66, 58),
    'gold_dark':   (104, 70, 20),
    'gold_mid':    (166, 120, 38),
    'gold_light':  (232, 190, 84),
    'iron':        (30, 26, 26),
    'iron_light':  (74, 66, 62),
    'flame_red':   (208, 64, 22),
    'flame_mid':   (255, 160, 40),
    'flame_core':  (255, 236, 160),
}
BRICK = ['mortar', 'brick_dark', 'brick_mid', 'brick_light', 'brick_hi']
STONE = ['mortar', 'stone_dark', 'stone_mid', 'stone_light']
GOLD = ['gold_dark', 'gold_mid', 'gold_light']

# ---- atlas regions, pixel rects (x0, y0, x1, y1), image rows top-down --------
REG = {
    'wall':    (4, 4, 124, 124),      # seamless red brick, 120 px = 2 m x 2 m
    'floor':   (132, 4, 252, 124),    # seamless flagstones + gold inlay, 2 m x 2 m
    'pillar':  (2, 130, 62, 190),     # fluted red stone, 4 faces x 1 m
    'vouss':   (66, 130, 126, 190),   # alternating arch stones (soffit / reveal)
    'plinth':  (4, 194, 124, 222),    # dark stone trim strip, 2 m long
    'gold':    (4, 226, 124, 254),    # gold frieze with ruby diamonds, 2 m long
    'banner':  (132, 130, 186, 250),  # crimson banner with gold demon sigil
    'flame':   (192, 130, 220, 186),  # flame gradient (bottom = core)
    'skull':   (224, 130, 254, 160),  # gold horned demon skull on dark stone
    'iron':    (224, 164, 236, 176),
    'ironl':   (240, 164, 252, 176),
    'goldd':   (224, 180, 236, 192),
    'dark':    (240, 180, 252, 192),
    'stone':   (194, 194, 254, 254),  # dark capstone blocks, 1 m x 1 m
}
PAD = {'wall': 4, 'floor': 4}  # others get 2 px

SKULL = [
    "H.............H",
    "HH...........HH",
    ".HH.........HH.",
    "..HHH.XXX.HHH..",
    "...HHXXXXXHH...",
    "....XXXXXXX....",
    "...XXXXXXXXX...",
    "...XEEXXXEEX...",
    "...XEEXXXEEX...",
    "...XXXXNXXXX...",
    "....XXXNXXX....",
    "....XXXXXXX....",
    ".....XTXTX.....",
    ".....XTXTX.....",
    "......XXX......",
]


# =============================================================================
# Atlas
# =============================================================================
def write_png(path, arr):
    h, w, _ = arr.shape
    raw = b''.join(b'\x00' + arr[y].tobytes() for y in range(h))

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def paint_atlas(path):
    rng = np.random.default_rng(1666)
    img = np.zeros((TEX, TEX, 3), np.uint8)
    img[:, :] = PAL['mortar']

    def col(name):
        return np.array(PAL[name], np.uint8)

    def shade(ramp, i):
        return ramp[max(1, min(len(ramp) - 1, i))]

    # ---- wall: 8 rows x 4 bricks of 30x15 px, staggered, wraps at 120 px
    W = 120
    t = np.zeros((W, W, 3), np.uint8)
    for r in range(8):
        off = (r % 2) * 15
        for k in range(-1, 5):
            base = [1, 2, 2, 2, 3, 3][int(rng.integers(0, 6))]
            for ly in range(15):
                for lx in range(30):
                    x = (k * 30 + off + lx) % W
                    y = r * 15 + ly
                    if ly == 14 or lx == 0:
                        c = 'mortar'
                        if ly != 14 and rng.random() < 0.08:
                            c = 'brick_dark'
                    else:
                        i = base
                        if ly == 0:
                            i = base + 1
                        elif ly == 13 or lx == 29:
                            i = base - 1
                        roll = rng.random()
                        if roll < 0.06:
                            i -= 1
                        elif roll < 0.09:
                            i += 1
                        c = shade(BRICK, i)
                        if ly in (6, 7) and lx in range(8, 22) and base == 1 and rng.random() < 0.35:
                            c = 'mortar'  # cracked old brick
                    t[y, x] = PAL[c]
    put_region(img, 'wall', t, wrap=True)

    # ---- floor: 2x2 flags, red-black checker, gold diamond inlays on the joints
    t = np.zeros((W, W, 3), np.uint8)
    for y in range(W):
        for x in range(W):
            fx, fy = x // 60, y // 60
            lx, ly = x % 60, y % 60
            ramp = STONE if (fx + fy) % 2 == 0 else ['mortar', 'brick_dark', 'brick_dark', 'brick_mid']
            if lx < 2 or ly < 2:
                c = 'mortar'
            else:
                i = 2
                if lx == 2 or ly == 2:
                    i = 3
                elif lx == 59 or ly == 59:
                    i = 1
                roll = rng.random()
                if roll < 0.08:
                    i -= 1
                elif roll < 0.11:
                    i += 1
                c = shade(ramp, i)
            # inlays at every flag corner (wraps), plus scratches
            for cx, cy in ((0, 0), (60, 0), (0, 60), (60, 60), (120, 0), (0, 120), (120, 120), (60, 120), (120, 60)):
                d = abs(x - cx) + abs(y - cy)
                if d <= 7:
                    c = 'gold_dark' if d >= 6 else ('gold_light' if d <= 1 else 'gold_mid')
            t[y, x] = PAL[c]
    put_region(img, 'floor', t, wrap=True)

    # ---- pillar: 4 faces of 15 px across, joints every 30 px (0.5 m)
    t = np.zeros((60, 60, 3), np.uint8)
    for y in range(60):
        for x in range(60):
            lx = x % 15
            if y % 30 == 29:
                c = 'mortar'
            elif lx == 0:
                c = 'brick_hi'
            elif lx == 14:
                c = 'brick_dark'
            elif lx in (6, 7, 8):
                c = 'mortar' if lx == 6 else 'brick_dark'
            elif lx == 9:
                c = 'brick_light'
            else:
                c = 'brick_mid'
                if rng.random() < 0.10:
                    c = 'brick_dark'
                elif rng.random() < 0.05:
                    c = 'brick_light'
            if y % 30 == 0 and c not in ('mortar',):
                c = 'brick_hi' if lx not in (6, 7, 8) else c
            t[y, x] = PAL[c]
    put_region(img, 'pillar', t, wrap=True)

    # ---- voussoirs: alternating dark-red and stone blocks along the arch
    t = np.zeros((60, 60, 3), np.uint8)
    for y in range(60):
        for x in range(60):
            blk = y // 10
            ly = y % 10
            ramp = STONE if blk % 2 == 0 else ['mortar', 'brick_dark', 'brick_mid', 'brick_light']
            if ly == 9:
                c = 'mortar'
            else:
                i = 3 if ly == 0 else 2
                if rng.random() < 0.12:
                    i -= 1
                c = shade(ramp, i)
            t[y, x] = PAL[c]
    put_region(img, 'vouss', t, wrap=True)

    # ---- plinth / dark trim strip 120x28 (u wraps at 2 m)
    t = np.zeros((28, 120, 3), np.uint8)
    for y in range(28):
        for x in range(120):
            if y < 2:
                c = 'stone_light'
            elif y == 2:
                c = 'gold_dark'
            elif y >= 26:
                c = 'mortar'
            elif x % 30 == 0:
                c = 'mortar'
            else:
                i = 3 if (x % 30 == 1 or y == 3) else 2
                if rng.random() < 0.15:
                    i -= 1
                c = shade(STONE, i)
            t[y, x] = PAL[c]
    put_region(img, 'plinth', t, wrap=True)

    # ---- gold frieze 120x28: rails + ruby diamonds every 20 px
    t = np.zeros((28, 120, 3), np.uint8)
    for y in range(28):
        for x in range(120):
            if y < 2:
                c = 'gold_light'
            elif y == 2 or y == 25:
                c = 'gold_dark'
            elif y >= 26:
                c = 'mortar'
            else:
                c = 'gold_mid'
                d = abs((x % 20) - 10) + abs(y - 13)
                if d <= 7:
                    c = 'gold_dark' if d >= 6 else ('flame_red' if d <= 2 else 'brick_light')
                    if d == 1 and (x % 20) < 10:
                        c = 'gold_light'
                elif (x % 20) == 0 and y in (12, 13, 14):
                    c = 'gold_light'
                elif rng.random() < 0.06:
                    c = 'gold_dark'
            t[y, x] = PAL[c]
    put_region(img, 'gold', t, wrap=True)

    # ---- banner 54x120
    bw, bh = 54, 120
    t = np.zeros((bh, bw, 3), np.uint8)
    for y in range(bh):
        for x in range(bw):
            c = 'brick_mid'
            if x % 18 in (0, 17) and rng.random() < 0.6:
                c = 'brick_dark'
            elif x % 18 in (8, 9) and rng.random() < 0.25:
                c = 'brick_light'
            if x < 3 or x >= bw - 3:
                c = 'gold_mid' if x in (1, bw - 2) else 'gold_dark'
            if y < 8:
                c = 'gold_mid' if 2 <= y <= 5 else 'gold_dark'
            if y >= bh - 8:
                c = 'gold_mid' if (x + y) % 3 else 'gold_dark'
            if 70 <= y <= 98 and x == bw // 2:
                c = 'gold_mid'
            if 70 <= y <= 98 and abs(x - bw // 2) + abs(y - 84) in (6,):
                c = 'gold_light'
            t[y, x] = PAL[c]
    sk = skull_bitmap(scale=2, bg=None)
    oy, ox = 22, (bw - sk.shape[1]) // 2
    for y in range(sk.shape[0]):
        for x in range(sk.shape[1]):
            if sk[y][x]:
                t[oy + y, ox + x] = PAL[sk[y][x]]
    put_region(img, 'banner', t, wrap=False)

    # ---- flame 28x56: top of the image is the tip
    fw, fh = 28, 56
    t = np.zeros((fh, fw, 3), np.uint8)
    for y in range(fh):
        h = 1.0 - y / (fh - 1)  # 0 at base, 1 at tip
        for x in range(fw):
            j = rng.random() * 0.12
            hh = h + j - 0.06
            if hh < 0.38:
                c = 'flame_core'
            elif hh < 0.70:
                c = 'flame_mid' if (abs(x - fw / 2) > 4 or hh > 0.6) else 'flame_core'
            else:
                c = 'flame_red' if abs(x - fw / 2) > 3 else 'flame_mid'
            t[y, x] = PAL[c]
    put_region(img, 'flame', t, wrap=False)

    # ---- skull plate 30x30
    t = np.zeros((30, 30, 3), np.uint8)
    t[:, :] = PAL['stone_dark']
    t[0, :] = PAL['gold_dark']; t[-1, :] = PAL['gold_dark']; t[:, 0] = PAL['gold_dark']; t[:, -1] = PAL['gold_dark']
    sk = skull_bitmap(scale=2, bg=None)
    for y in range(30):
        for x in range(30):
            if sk[y][x]:
                t[y, x] = PAL[sk[y][x]]
    put_region(img, 'skull', t, wrap=False)

    # ---- solids
    for name, c in (('iron', 'iron'), ('ironl', 'iron_light'), ('goldd', 'gold_dark'), ('dark', 'stone_dark')):
        x0, y0, x1, y1 = REG[name]
        img[y0:y1, x0:x1] = PAL[c]

    # ---- capstone 60x60: 30x15 blocks staggered (1 m period)
    t = np.zeros((60, 60, 3), np.uint8)
    for y in range(60):
        r = y // 15
        for x in range(60):
            lx = (x + (r % 2) * 15) % 30
            ly = y % 15
            if lx == 0 or ly == 14:
                c = 'mortar'
            else:
                i = 3 if ly == 0 else 2
                if rng.random() < 0.18:
                    i -= 1
                c = shade(STONE, i)
            t[y, x] = PAL[c]
    put_region(img, 'stone', t, wrap=True)

    write_png(path, img)
    cols = {tuple(c) for c in img.reshape(-1, 3)}
    print(f'atlas {path}: {TEX}x{TEX}, {len(cols)} colours')
    return path


def skull_bitmap(scale=2, bg=None):
    m = {'H': 'gold_light', 'X': 'gold_mid', 'E': 'flame_red', 'N': 'mortar', 'T': 'mortar'}
    out = []
    for row in SKULL:
        r = []
        for ch in row:
            r += [m.get(ch, bg)] * scale
        for _ in range(scale):
            out.append(list(r))
    # dark outline under the gold so it reads at distance
    h, w = len(out), len(out[0])
    res = [list(r) for r in out]
    for y in range(h):
        for x in range(w):
            if out[y][x] is None:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h and out[yy][xx] in ('gold_mid', 'gold_light'):
                        res[y][x] = 'gold_dark'
                        break
    return np.array(res, dtype=object)


def put_region(img, name, tile, wrap):
    x0, y0, x1, y1 = REG[name]
    assert tile.shape[0] == y1 - y0 and tile.shape[1] == x1 - x0, (name, tile.shape)
    p = PAD.get(name, 2)
    padded = np.pad(tile, ((p, p), (p, p), (0, 0)), mode='wrap' if wrap else 'edge')
    img[y0 - p:y1 + p, x0 - p:x1 + p] = padded


# =============================================================================
# Mesh building
# =============================================================================
class Piece:
    """Collects quads/tris with per-corner UVs into one mesh (one draw call)."""

    def __init__(self, name, origin=(0.0, 0.0, 0.0)):
        self.name = name
        self.O = Vector(origin)  # tiling phase: tile edges sit on O + k * period
        self.verts = []
        self.vidx = {}
        self.faces = []
        self.uvs = []
        self.M = Matrix.Identity(4)
        self.empties = []

    # -- low level
    def _v(self, p):
        key = (round(p.x, 5), round(p.y, 5), round(p.z, 5))
        i = self.vidx.get(key)
        if i is None:
            i = len(self.verts)
            self.verts.append(Vector(key))
            self.vidx[key] = i
        return i

    def face(self, pts, uvs, normal=None):
        pts = [Vector(p) for p in pts]
        if normal is not None:
            n = newell(pts)
            if n.dot(Vector(normal)) < 0:
                pts = pts[::-1]
                uvs = uvs[::-1]
        self.faces.append([self._v(p) for p in pts])
        self.uvs.append([region_uv(r, s, t) for (r, s, t) in uvs])

    # -- mapped faces (pts already in piece space)
    def poly(self, pts, normal, mode, reg, period=2.0, local=None):
        pts = [Vector(p) for p in pts]
        n = Vector(normal).normalized()
        if mode == 'solid':
            uv = [(reg, 0.5, 0.5)] * len(pts)
        elif mode == 'local':
            uv = [(reg, s, t) for (s, t) in local]
        else:
            us, vs = [], []
            for p in pts:
                q = p - self.O
                if abs(n.z) > 0.7:
                    u, v = q.x, (q.y if n.z > 0 else -q.y)
                else:
                    r = Vector((-n.y, n.x, 0)).normalized()
                    u, v = q.dot(r), q.z
                us.append(u)
                vs.append(v)
            su = tile_coords(us, period) if mode in ('tile', 'strip') else None
            if mode == 'tile':
                sv = tile_coords(vs, period)
            elif mode == 'strip':
                lo, hi = min(vs), max(vs)
                sv = [(v - lo) / (hi - lo) for v in vs]
            elif mode == 'fill':
                lo, hi = min(us), max(us)
                su = [(u - lo) / (hi - lo) for u in us]
                lo, hi = min(vs), max(vs)
                sv = [(v - lo) / (hi - lo) for v in vs]
            else:
                raise ValueError(mode)
            uv = [(reg, s, t) for s, t in zip(su, sv)]
        self.face(pts, uv, n)

    def rect(self, axis, c, a, b, normal_sign, mode, reg, period=2.0):
        """Axis-aligned rectangle (in the local frame M), split on tile edges.
        axis: plane normal axis 'x' 'y' 'z'; c: plane coordinate;
        a, b: ranges of the two other axes in (x, y, z) order."""
        corners = []
        for aa, bb in ((a[0], b[0]), (a[1], b[0]), (a[1], b[1]), (a[0], b[1])):
            corners.append(axis_point(axis, c, aa, bb))
        nloc = {'x': Vector((1, 0, 0)), 'y': Vector((0, 1, 0)), 'z': Vector((0, 0, 1))}[axis] * normal_sign
        W = [self.M @ p for p in corners]
        n = (self.M.to_3x3() @ nloc).normalized()
        nax = max(range(3), key=lambda i: abs(n[i]))
        oth = [i for i in range(3) if i != nax]
        lo = [min(p[i] for p in W) for i in oth]
        hi = [max(p[i] for p in W) for i in oth]
        cval = W[0][nax]
        split = mode in ('tile', 'strip')
        cuts = []
        for k, i in enumerate(oth):
            pts = [lo[k], hi[k]]
            per = period
            if split and not (mode == 'strip' and i == 2):
                o = self.O[i]
                j = math.floor((lo[k] - o) / per + 1e-6) + 1
                while o + j * per < hi[k] - 1e-6:
                    pts.insert(-1, o + j * per)
                    j += 1
            cuts.append(pts)
        for i0 in range(len(cuts[0]) - 1):
            for i1 in range(len(cuts[1]) - 1):
                q = []
                for (u, v) in ((cuts[0][i0], cuts[1][i1]), (cuts[0][i0 + 1], cuts[1][i1]),
                               (cuts[0][i0 + 1], cuts[1][i1 + 1]), (cuts[0][i0], cuts[1][i1 + 1])):
                    p = [0.0, 0.0, 0.0]
                    p[nax] = cval
                    p[oth[0]] = u
                    p[oth[1]] = v
                    q.append(Vector(p))
                self.poly(q, n, mode, reg, period)

    def box(self, x, y, z, faces, period=2.0):
        """faces: dict side -> (mode, reg) for sides to emit: '+x' '-x' '+y' '-y' '+z' '-z'."""
        for side, spec in faces.items():
            if spec is None:
                continue
            mode, reg = spec[0], spec[1]
            per = spec[2] if len(spec) > 2 else period
            sgn = 1 if side[0] == '+' else -1
            ax = side[1]
            if ax == 'x':
                self.rect('x', x[1] if sgn > 0 else x[0], y, z, sgn, mode, reg, per)
            elif ax == 'y':
                self.rect('y', y[1] if sgn > 0 else y[0], x, z, sgn, mode, reg, per)
            else:
                self.rect('z', z[1] if sgn > 0 else z[0], x, y, sgn, mode, reg, per)

    def empty(self, name, loc):
        self.empties.append((name, Vector(loc)))

    def tri_count(self):
        return sum(len(f) - 2 for f in self.faces)


def axis_point(axis, c, a, b):
    if axis == 'x':
        return Vector((c, a, b))
    if axis == 'y':
        return Vector((a, c, b))
    return Vector((a, b, c))


def newell(pts):
    n = Vector((0, 0, 0))
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        n.x += (p.y - q.y) * (p.z + q.z)
        n.y += (p.z - q.z) * (p.x + q.x)
        n.z += (p.x - q.x) * (p.y + q.y)
    return n


def tile_coords(vals, period):
    base = math.floor(min(vals) / period + 1e-6) * period
    out = [(v - base) / period for v in vals]
    assert max(out) <= 1.0 + 1e-5, f'face straddles a tile edge: {vals} period {period}'
    return out


def region_uv(reg, s, t):
    x0, y0, x1, y1 = REG[reg]
    inset = 0.25
    px = x0 + inset + s * (x1 - x0 - 2 * inset)
    py = y1 - inset - t * (y1 - y0 - 2 * inset)
    return (px / TEX, 1.0 - py / TEX)


# =============================================================================
# Kit pieces (Blender space, Z up, room side = -Y)
# =============================================================================
H = 4.0          # module height
T = 0.5          # wall thickness behind the room face
PL_H, PL_D = 0.4, 0.12        # plinth height, how far it stands out
BAND = (3.40, 3.55, 0.06)     # gold frieze z0, z1, depth
CAP = (3.55, 4.0, 0.16)       # stone cap z0, z1, depth


def wall_run(p, x0, x1, front=True, end0=True, end1=True, trim0=None, trim1=None, body0=None, body1=None):
    """Straight wall along local X. Front face y=0, back y=T.
    trim0/trim1 clip the plinth/frieze/cap (for corner mitres); body0/body1 extend the body."""
    b0 = x0 if body0 is None else body0
    b1 = x1 if body1 is None else body1
    t0 = x0 if trim0 is None else trim0
    t1 = x1 if trim1 is None else trim1
    if front:
        p.rect('y', 0.0, (x0, x1), (PL_H, BAND[0]), -1, 'tile', 'wall')
    p.rect('y', T, (b0, b1), (0.0, CAP[1]), +1, 'tile', 'wall')
    if end0:
        p.rect('x', b0, (0.0, T), (0.0, CAP[0]), -1, 'tile', 'wall')
    if end1:
        p.rect('x', b1, (0.0, T), (0.0, CAP[0]), +1, 'tile', 'wall')
    trims(p, t0, t1, end0, end1, cap_back=b1 if body1 is not None else None, cap_front0=b0)


def trims(p, t0, t1, end0=True, end1=True, cap_back=None, cap_front0=None):
    e = lambda flag, spec: spec if flag else None
    p.box((t0, t1), (-PL_D, 0.0), (0.0, PL_H), {
        '-y': ('strip', 'plinth'), '+z': ('tile', 'stone', 1.0),
        '-x': e(end0, ('solid', 'dark')), '+x': e(end1, ('solid', 'dark'))})
    p.box((t0, t1), (-BAND[2], 0.0), (BAND[0], BAND[1]), {
        '-y': ('strip', 'gold'), '-z': ('solid', 'goldd'),
        '-x': e(end0, ('solid', 'goldd')), '+x': e(end1, ('solid', 'goldd'))})
    p.box((t0, t1), (-CAP[2], 0.0), (CAP[0], CAP[1]), {
        '-y': ('strip', 'plinth'), '-z': ('solid', 'dark'),
        '-x': e(end0, ('solid', 'dark')), '+x': e(end1, ('solid', 'dark'))})
    # cap top runs over the wall body to the back face
    p.rect('z', CAP[1], (t0, t1), (-CAP[2], T), +1, 'tile', 'stone', 1.0)
    if end0:
        p.rect('x', t0, (0.0, T), (CAP[0], CAP[1]), -1, 'solid', 'dark')
    if end1:
        p.rect('x', t1, (0.0, T), (CAP[0], CAP[1]), +1, 'solid', 'dark')


def build_wall_straight():
    p = Piece('ch_wall_straight', origin=(-1.0, 0.0, 0.0))
    wall_run(p, -1.0, 1.0)
    return p


def build_wall_corner():
    """Inner (room-side) corner: arm A along X (x -1..1), arm B along Y (y -2..0) on the
    plane x = -1 facing +X, with a stone pilaster in the corner."""
    p = Piece('ch_wall_corner', origin=(-1.0, 0.0, 0.0))
    # arm A: no end cap where it meets arm B, trims start at arm B's trims
    wall_run(p, -1.0, 1.0, end0=False, trim0=-1.0 + PL_D * 0)
    # arm B: rotate +90 deg about Z, then shift so its front plane is x = -1, y -2..0
    p.M = Matrix.Translation((-1.0, -1.0, 0.0)) @ Matrix.Rotation(math.radians(90), 4, 'Z')
    # local x -1..1 -> world y -2..0; body runs on to local 1.5 (world y 0.5) to close the back corner
    wall_run(p, -1.0, 1.0, end1=False, body1=1.5, trim1=1.0)
    p.M = Matrix.Identity(4)
    # outer back corner: arm B body end (world y = 0.5) and arm A back are already closed by wall_run;
    # the arm B body end at local 1.5 faces +Y in world.
    p.M = Matrix.Translation((-1.0, -1.0, 0.0)) @ Matrix.Rotation(math.radians(90), 4, 'Z')
    p.rect('x', 1.5, (0.0, T), (0.0, CAP[1]), +1, 'solid', 'dark')
    p.M = Matrix.Identity(4)
    corner_pilaster(p, -1.0, 0.0)
    return p


def corner_pilaster(p, x, y, s=0.36):
    # square pilaster tucked into the inner corner, gold band + capital to match the trims
    xs, ys = (x, x + s), (y - s, y)
    p.box(xs, ys, (0.0, PL_H + 0.05), {'+x': ('fill', 'plinth'), '-y': ('fill', 'plinth'), '+z': ('solid', 'dark')})
    sh = (x + 0.04, x + s - 0.04)
    sy = (y - s + 0.04, y)
    p.box(sh, sy, (PL_H + 0.05, BAND[0]), {'+x': ('local_pillar',), '-y': ('local_pillar',)})
    p.box((x, x + s + 0.02), (y - s - 0.02, y), (BAND[0], CAP[0]), {
        '+x': ('fill', 'gold'), '-y': ('fill', 'gold'), '-z': ('solid', 'goldd')})


def build_doorway_arch():
    """4 m wide (two grid cells, like the game's door), pointed arch 2 m wide, 3.25 m high."""
    p = Piece('ch_doorway_arch', origin=(-2.0, 0.0, 0.0))
    X0, X1 = -2.0, 2.0
    w, zs, h, tb, td = 1.0, 2.0, 1.25, 0.12, 0.06
    cx = (h * h - w * w) / (2 * w)
    R = w + cx
    N = 5

    def curve(rad):
        ta = math.acos(cx / rad)
        pts = []
        for k in range(N + 1):
            th = ta * k / N
            pts.append((cx - rad * math.cos(th), zs + rad * math.sin(th)))
        pts[-1] = (0.0, pts[-1][1])
        return pts
    inner = curve(R)
    outer = curve(R + tb)
    for sgn in (-1, 1):
        I = [(sgn * x, z) for x, z in inner]
        O = [(sgn * x, z) for x, z in outer]
        xe = X0 if sgn < 0 else X1
        xo = -(w + tb) * -sgn * -1 if False else sgn * (w + tb)
        # front wall beside the opening
        p.rect('y', 0.0, tuple(sorted((xe, xo))), (PL_H, BAND[0]), -1, 'tile', 'wall')
        # front wall above the arch: strips from the outer curve to the frieze
        for k in range(N):
            a, b = O[k], O[k + 1]
            q = [Vector((a[0], 0.0, a[1])), Vector((b[0], 0.0, b[1])),
                 Vector((b[0], 0.0, BAND[0])), Vector((a[0], 0.0, BAND[0]))]
            p.poly(q, (0, -1, 0), 'tile', 'wall')
        # back wall beside and above
        xi = sgn * w
        p.rect('y', T, tuple(sorted((xe, xi))), (0.0, CAP[1]), +1, 'tile', 'wall')
        for k in range(N):
            a, b = I[k], I[k + 1]
            q = [Vector((a[0], T, a[1])), Vector((b[0], T, b[1])),
                 Vector((b[0], T, CAP[1])), Vector((a[0], T, CAP[1]))]
            p.poly(q, (0, 1, 0), 'tile', 'wall')
        # gold archivolt ring (front), its outer lip, and the soffit
        for k in range(N):
            ia, ib, oa, ob = I[k], I[k + 1], O[k], O[k + 1]
            s0, s1 = k / N, (k + 1) / N
            q = [Vector((ia[0], -td, ia[1])), Vector((ib[0], -td, ib[1])),
                 Vector((ob[0], -td, ob[1])), Vector((oa[0], -td, oa[1]))]
            p.poly(q, (0, -1, 0), 'local', 'gold', local=[(s0, 0.0), (s1, 0.0), (s1, 1.0), (s0, 1.0)])
            q = [Vector((oa[0], -td, oa[1])), Vector((ob[0], -td, ob[1])),
                 Vector((ob[0], 0.0, ob[1])), Vector((oa[0], 0.0, oa[1]))]
            mid = Vector(((oa[0] + ob[0]) / 2, 0, (oa[1] + ob[1]) / 2))
            p.poly(q, (mid.x - sgn * cx, 0, mid.z - zs), 'solid', 'goldd')
            q = [Vector((ia[0], -td, ia[1])), Vector((ib[0], -td, ib[1])),
                 Vector((ib[0], T, ib[1])), Vector((ia[0], T, ia[1]))]
            mid = Vector(((ia[0] + ib[0]) / 2, 0, (ia[1] + ib[1]) / 2))
            p.poly(q, (sgn * cx - mid.x, 0, zs - mid.z), 'local', 'vouss',
                   local=[(0.0, s0), (0.0, s1), (1.0, s1), (1.0, s0)])
        # jamb: gold band down to the plinth, reveal stones
        jb = tuple(sorted((sgn * w, sgn * (w + tb))))
        p.box(jb, (-td, 0.0), (PL_H, zs), {'-y': ('local_goldv',)})
        p.rect('x', sgn * w, (-td, T), (PL_H, zs), -sgn, 'local_reveal', 'vouss')
        p.rect('x', sgn * w, (0.0, T), (0.0, PL_H), -sgn, 'local_reveal', 'vouss')
        # plinth beside the opening
        xa, xb = sorted((xe, sgn * w))
        p.box((xa, xb), (-PL_D, 0.0), (0.0, PL_H), {
            '-y': ('strip', 'plinth'), '+z': ('tile', 'stone', 1.0),
            ('+x' if sgn < 0 else '-x'): ('solid', 'dark'),
            ('-x' if sgn < 0 else '+x'): ('solid', 'dark')})
        # wall body ends
        p.rect('x', xe, (0.0, T), (0.0, CAP[0]), sgn, 'tile', 'wall')
    # frieze + cap across the whole width
    e = True
    p.box((X0, X1), (-BAND[2], 0.0), (BAND[0], BAND[1]), {
        '-y': ('strip', 'gold'), '-z': ('solid', 'goldd'), '-x': ('solid', 'goldd'), '+x': ('solid', 'goldd')})
    p.box((X0, X1), (-CAP[2], 0.0), (CAP[0], CAP[1]), {
        '-y': ('strip', 'plinth'), '-z': ('solid', 'dark'), '-x': ('solid', 'dark'), '+x': ('solid', 'dark')})
    p.rect('z', CAP[1], (X0, X1), (-CAP[2], T), +1, 'tile', 'stone', 1.0)
    p.rect('x', X0, (0.0, T), (CAP[0], CAP[1]), -1, 'solid', 'dark')
    p.rect('x', X1, (0.0, T), (CAP[0], CAP[1]), +1, 'solid', 'dark')
    # demon-skull keystone
    p.box((-0.15, 0.15), (-0.12, -td), (3.08, BAND[0]), {
        '-y': ('fill', 'skull'), '-x': ('solid', 'goldd'), '+x': ('solid', 'goldd'), '-z': ('solid', 'goldd')})
    return p


def build_pillar():
    """Free-standing octagonal pillar, 4 m, square plinth and capital (0.8 m)."""
    p = Piece('ch_pillar', origin=(-0.4, -0.4, 0.0))
    B = 0.4
    p.box((-B, B), (-B, B), (0.0, PL_H), {
        '-y': ('fill', 'plinth'), '+y': ('fill', 'plinth'), '-x': ('fill', 'plinth'), '+x': ('fill', 'plinth'),
        '+z': ('tile', 'stone', 1.0)})
    ring(p, 0.34, PL_H, PL_H + 0.1, 'gold', top=True)
    r = 0.28
    zc = [PL_H + 0.1, 1.0, 2.0, 3.0, BAND[0] - 0.1]
    for k in range(8):
        a0 = math.radians(22.5 + 45 * k)
        a1 = math.radians(22.5 + 45 * (k + 1))
        p0 = Vector((r * math.cos(a0), r * math.sin(a0), 0))
        p1 = Vector((r * math.cos(a1), r * math.sin(a1), 0))
        n = ((p0 + p1) / 2).normalized()
        s0 = (k % 4) / 4
        s1 = s0 + 0.25
        for j in range(len(zc) - 1):
            z0, z1 = zc[j], zc[j + 1]
            t0 = (z0 % 1.0) if j else 0.0
            t1 = t0 + (z1 - z0)
            q = [Vector((p0.x, p0.y, z0)), Vector((p1.x, p1.y, z0)), Vector((p1.x, p1.y, z1)), Vector((p0.x, p0.y, z1))]
            p.poly(q, n, 'local', 'pillar', local=[(s0, t0), (s1, t0), (s1, t1), (s0, t1)])
    ring(p, 0.34, BAND[0] - 0.1, BAND[1], 'gold', bottom=True)
    p.box((-B, B), (-B, B), (CAP[0], CAP[1]), {
        '-y': ('fill', 'plinth'), '+y': ('fill', 'plinth'), '-x': ('fill', 'plinth'), '+x': ('fill', 'plinth'),
        '+z': ('tile', 'stone', 1.0), '-z': ('solid', 'dark')})
    return p


def ring(p, r, z0, z1, reg, top=False, bottom=False, sides=8, inner=0.28):
    pts = [Vector((r * math.cos(math.radians(22.5 + 45 * k)), r * math.sin(math.radians(22.5 + 45 * k)), 0)) for k in range(sides)]
    ins = [Vector((inner * math.cos(math.radians(22.5 + 45 * k)), inner * math.sin(math.radians(22.5 + 45 * k)), 0)) for k in range(sides)]
    for k in range(sides):
        a, b = pts[k], pts[(k + 1) % sides]
        n = ((a + b) / 2).normalized()
        q = [Vector((a.x, a.y, z0)), Vector((b.x, b.y, z0)), Vector((b.x, b.y, z1)), Vector((a.x, a.y, z1))]
        s0 = (k % 4) / 4
        p.poly(q, n, 'local', reg, local=[(s0, 0.15), (s0 + 0.25, 0.15), (s0 + 0.25, 0.9), (s0, 0.9)])
        for flag, z, nz in ((top, z1, 1), (bottom, z0, -1)):
            if flag:
                ia, ib = ins[k], ins[(k + 1) % sides]
                q = [Vector((a.x, a.y, z)), Vector((b.x, b.y, z)), Vector((ib.x, ib.y, z)), Vector((ia.x, ia.y, z))]
                p.poly(q, (0, 0, nz), 'solid', 'goldd')


def build_floor_tile():
    p = Piece('ch_floor_tile', origin=(-1.0, -1.0, 0.0))
    p.box((-1.0, 1.0), (-1.0, 1.0), (-0.1, 0.0), {
        '+z': ('tile', 'floor'), '-x': ('solid', 'dark'), '+x': ('solid', 'dark'),
        '-y': ('solid', 'dark'), '+y': ('solid', 'dark')})
    return p


def build_torch_sconce():
    """Wall sconce. Origin = where the back plate touches the wall; it reaches out along -Y.
    Flame sits 0.28 m out and 0.28 m up (the game's torch light is 0.28 m off the wall)."""
    p = Piece('ch_torch_sconce')
    # demon-skull back plate
    p.box((-0.09, 0.09), (-0.035, 0.0), (-0.16, 0.06), {
        '-y': ('fill', 'skull'), '-x': ('solid', 'iron'), '+x': ('solid', 'iron'),
        '+z': ('solid', 'iron'), '-z': ('solid', 'iron')})
    # forged arm: square section along a bent path
    path = [Vector((0, -0.035, -0.07)), Vector((0, -0.17, -0.04)), Vector((0, -0.28, 0.05))]
    sq = 0.018
    rings = []
    for i, c in enumerate(path):
        d = (path[min(i + 1, 2)] - path[max(i - 1, 0)]).normalized()
        side = Vector((1, 0, 0))
        up = d.cross(side).normalized()
        rings.append([c + side * sx * sq + up * sy * sq for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for i in range(2):
        for k in range(4):
            a0, a1 = rings[i][k], rings[i][(k + 1) % 4]
            b0, b1 = rings[i + 1][k], rings[i + 1][(k + 1) % 4]
            n = ((a0 + a1) / 2 - path[i]).normalized()
            p.poly([a0, a1, b1, b0], n, 'solid', 'ironl' if k == 2 else 'iron')
    # gold cup (hexagonal frustum) with a spike under it and coals on top
    c = Vector((0, -0.28, 0))
    hexa = lambda r, z, rot=0.0: [c + Vector((r * math.cos(math.radians(60 * k + rot)), r * math.sin(math.radians(60 * k + rot)), z)) for k in range(6)]
    lo, hi = hexa(0.045, 0.05), hexa(0.10, 0.16)
    for k in range(6):
        a0, a1, b0, b1 = lo[k], lo[(k + 1) % 6], hi[k], hi[(k + 1) % 6]
        n = ((a0 + a1 + b0 + b1) / 4 - c - Vector((0, 0, 0.1))).normalized()
        s0 = (k % 3) / 3
        p.poly([a0, a1, b1, b0], n, 'local', 'gold', local=[(s0, 0.1), (s0 + 0.33, 0.1), (s0 + 0.33, 0.95), (s0, 0.95)])
        tip = c + Vector((0, 0, -0.05))
        p.poly([a1, a0, tip], (n.x, n.y, -1), 'solid', 'iron')
    p.poly(hexa(0.095, 0.15), (0, 0, 1), 'solid', 'dark')
    # flame: twisted hexagonal bipyramid, opaque (no alpha sorting on Quest)
    base = c + Vector((0, 0, 0.12))
    r1, r2 = hexa(0.065, 0.21), hexa(0.045, 0.31, 30.0)
    tip = c + Vector((0.01, 0.0, 0.47))
    for k in range(6):
        s0, s1 = k / 6, (k + 1) / 6
        a0, a1 = r1[k], r1[(k + 1) % 6]
        b0, b1 = r2[k], r2[(k + 1) % 6]
        n = ((a0 + a1) / 2 - c).normalized()
        p.poly([a0, a1, base], (n.x, n.y, -0.8), 'local', 'flame', local=[(s0, 0.15), (s1, 0.15), ((s0 + s1) / 2, 0.0)])
        p.poly([a0, a1, b1], n, 'local', 'flame', local=[(s0, 0.15), (s1, 0.15), (s1, 0.45)])
        p.poly([a0, b1, b0], n, 'local', 'flame', local=[(s0, 0.15), (s1, 0.45), (s0, 0.45)])
        p.poly([b0, b1, tip], (n.x, n.y, 0.6), 'local', 'flame', local=[(s0, 0.45), (s1, 0.45), ((s0 + s1) / 2, 1.0)])
    p.empty('flame', c + Vector((0, 0, 0.28)))
    return p


def build_banner():
    """Bonus piece: crimson banner with the demon sigil. Origin = middle of the rod, on the wall."""
    p = Piece('ch_banner')
    W2, L, tail = 0.42, 2.0, 0.3
    p.box((-0.5, 0.5), (-0.07, -0.03), (-0.02, 0.02), {
        '-y': ('solid', 'goldd'), '+z': ('fill', 'gold'), '-z': ('solid', 'goldd'),
        '-x': ('solid', 'goldd'), '+x': ('solid', 'goldd')})
    xs = [-W2, -W2 / 3, W2 / 3, W2]
    ys = [-0.05, -0.08, -0.05, -0.08]
    for side, ny in ((-1, -1), (1, 1)):
        off = 0.0 if side < 0 else 0.004
        for k in range(3):
            x0, x1 = xs[k], xs[k + 1]
            y0, y1 = ys[k] + off, ys[k + 1] + off
            s0, s1 = (x0 + W2) / (2 * W2), (x1 + W2) / (2 * W2)
            if side > 0:
                s0, s1 = 1 - s0, 1 - s1
            tb = tail / (L + tail)
            q = [Vector((x0, y0, -L)), Vector((x1, y1, -L)), Vector((x1, y1, 0)), Vector((x0, y0, 0))]
            p.poly(q, (0, ny, 0), 'local', 'banner', local=[(s0, tb), (s1, tb), (s1, 1), (s0, 1)])
        # pointed tail
        tipz = -L - tail
        for (xa, ya, sa), (xb, yb, sb) in (((xs[0], ys[0], 0.0), (0.0, -0.065, 0.5)), ((0.0, -0.065, 0.5), (xs[3], ys[3], 1.0))):
            if side > 0:
                sa, sb = 1 - sa, 1 - sb
            q = [Vector((xa, ya + off, -L)), Vector((xb, yb + off, -L)), Vector((0.0, -0.065 + off, tipz))]
            p.poly(q, (0, ny, 0), 'local', 'banner', local=[(sa, tb), (sb, tb), (0.5, 0.0)])
    return p


PIECES = [
    ('wall_straight', build_wall_straight),
    ('wall_corner', build_wall_corner),
    ('doorway_arch', build_doorway_arch),
    ('pillar', build_pillar),
    ('floor_tile', build_floor_tile),
    ('torch_sconce', build_torch_sconce),
    ('banner', build_banner),
]


# special face modes resolved by box(): pillar faces and vertical gold / reveal stones
_orig_box = Piece.box


def _box(self, x, y, z, faces, period=2.0):
    plain = {}
    for side, spec in faces.items():
        if spec is None:
            continue
        if spec[0] in ('local_pillar', 'local_goldv'):
            sgn = 1 if side[0] == '+' else -1
            ax = side[1]
            if ax == 'x':
                c = x[1] if sgn > 0 else x[0]
                q = [Vector((c, y[0], z[0])), Vector((c, y[1], z[0])), Vector((c, y[1], z[1])), Vector((c, y[0], z[1]))]
                a = y
            else:
                c = y[1] if sgn > 0 else y[0]
                q = [Vector((x[0], c, z[0])), Vector((x[1], c, z[0])), Vector((x[1], c, z[1])), Vector((x[0], c, z[1]))]
                a = x
            n = Vector((sgn, 0, 0)) if ax == 'x' else Vector((0, sgn, 0))
            q = [self.M @ v for v in q]
            n = self.M.to_3x3() @ n
            if spec[0] == 'local_pillar':
                cuts = [z[0]] + [float(k) for k in range(int(z[0]) + 1, int(math.ceil(z[1]))) if k > z[0] and k < z[1]] + [z[1]]
                for j in range(len(cuts) - 1):
                    z0, z1 = cuts[j], cuts[j + 1]
                    qq = [Vector((v.x, v.y, z0 if i < 2 else z1)) for i, v in enumerate(q)]
                    t0 = z0 % 1.0
                    t1 = t0 + (z1 - z0)
                    p_local = [(0.25, t0), (0.75, t0), (0.75, t1), (0.25, t1)]
                    self.poly(qq, n, 'local', 'pillar', local=p_local)
            else:  # vertical gold band: motif runs up the jamb
                L = z[1] - z[0]
                self.poly(q, n, 'local', 'gold', local=[(0.0, 0.0), (0.0, 1.0), (L / 2.0, 1.0), (L / 2.0, 0.0)])
        else:
            plain[side] = spec
    _orig_box(self, x, y, z, plain, period)


_orig_rect = Piece.rect


def _rect(self, axis, c, a, b, normal_sign, mode, reg, period=2.0):
    if mode != 'local_reveal':
        return _orig_rect(self, axis, c, a, b, normal_sign, mode, reg, period)
    # jamb reveal: stones run up the jamb, depth across
    q = [axis_point(axis, c, a[0], b[0]), axis_point(axis, c, a[1], b[0]),
         axis_point(axis, c, a[1], b[1]), axis_point(axis, c, a[0], b[1])]
    n = {'x': Vector((1, 0, 0)), 'y': Vector((0, 1, 0)), 'z': Vector((0, 0, 1))}[axis] * normal_sign
    d0, d1 = (a[0] + 0.06) / (T + 0.06), (a[1] + 0.06) / (T + 0.06)
    t0, t1 = b[0] / 2.0, b[1] / 2.0
    self.poly([self.M @ v for v in q], self.M.to_3x3() @ n, 'local', reg,
              local=[(d0, t0), (d1, t0), (d1, t1), (d0, t1)])


Piece.box = _box
Piece.rect = _rect


# =============================================================================
# Blender objects
# =============================================================================
def make_material(img_path):
    img = bpy.data.images.load(os.path.abspath(img_path))
    img.pack()
    img.colorspace_settings.name = 'sRGB'
    mat = bpy.data.materials.new('crimson_halls')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Closest'
    tex.location = (-300, 0)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.8
    key = 'Specular IOR Level' if 'Specular IOR Level' in bsdf.inputs else 'Specular'
    bsdf.inputs[key].default_value = 0.2
    return mat


def piece_to_objects(p, mat, offset=Vector((0, 0, 0)), coll=None):
    coll = coll or bpy.context.scene.collection
    me = bpy.data.meshes.new(p.name + '_mesh')
    me.from_pydata([tuple(v) for v in p.verts], [], p.faces)
    me.update()
    uv = me.uv_layers.new(name='UVMap')
    li = 0
    for poly, fuv in zip(me.polygons, p.uvs):
        for k, li in enumerate(poly.loop_indices):
            uv.data[li].uv = fuv[k]
    me.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = False
    root = bpy.data.objects.new(p.name, None)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = 0.3
    root.location = offset
    root['kit'] = 'crimson_halls'
    root['grid_m'] = 2.0
    coll.objects.link(root)
    ob = bpy.data.objects.new(p.name + '_mesh', me)
    coll.objects.link(ob)
    ob.parent = root
    for name, loc in p.empties:
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = 'PLAIN_AXES'
        e.empty_display_size = 0.05
        e.location = loc
        coll.objects.link(e)
        e.parent = root
    # octagons / flame read rounder with smooth-by-angle; boxes stay hard
    if p.name in ('ch_pillar', 'ch_torch_sconce'):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
        except Exception as ex:
            print('smooth-by-angle unavailable:', ex)
    return root, ob


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--piece-dir', required=True)
    a = ap.parse_args(argv)
    out = os.path.abspath(a.out_dir)
    pdir = os.path.abspath(a.piece_dir)
    os.makedirs(out, exist_ok=True)
    os.makedirs(pdir, exist_ok=True)
    atlas = paint_atlas(os.path.join(out, 'crimson_halls_atlas.png'))

    built = [(key, fn()) for key, fn in PIECES]
    for key, p in built:
        print(f'piece {key}: {p.tri_count()} tris (pre-export), {len(p.verts)} verts')

    # one .blend per piece for the exporter
    for key, p in built:
        reset()
        mat = make_material(atlas)
        piece_to_objects(p, mat)
        path = os.path.join(pdir, f'ch_{key}.blend')
        bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
        print('saved', path)

    # kit source file: everything laid out on a line
    reset()
    mat = make_material(atlas)
    x = 0.0
    for key, p in built:
        coll = bpy.data.collections.new(key)
        bpy.context.scene.collection.children.link(coll)
        piece_to_objects(p, mat, Vector((x, 0, 0)), coll)
        x += 5.0
    path = os.path.join(out, 'crimson_halls_kit.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    print('saved', path)


if __name__ == '__main__':
    main()
