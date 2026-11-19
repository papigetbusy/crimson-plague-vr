"""Shared helpers for the gothic base-gun remakes (cannon, machine pistol, duelist).

Builds on gun_lowpoly_common (Part: loft / box / prism / cyl, assemble, preview
rig). Adds: a shelf-packed 256 px atlas with painters for blued steel, engraved
steel (scrollwork, lancet arches), brass, carved bone and stippled polymer;
revolve / tube / profile-prism mesh helpers; and the export + preview wrappers.

Game space: +Y up, muzzle toward -Z, +X right, metres, origin at the palm.
Look: locked 1911 steel (metallic 1, roughness 0.30) for ALL metal, brass too
(brass is just warm texels on the metal material); one non-metal material for
bone / polymer. Two materials, one 256 px nearest-filtered atlas per gun.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
import numpy as np
from mathutils import Vector
import gun_lowpoly_common as C

M, G = C.M, C.G
S = 256
HD = 1024                      # final albedo size (smooth, anti-aliased); painters still work on the 256 logical grid
C.TEX_INTERP = 'Linear'        # linear filtering for the HD albedo (glTF sampler LINEAR)
C.BEVEL_MINLEN = 0.014          # only long edges get the small bevel (keeps tris down)
C.BEVEL_ANGLE = 50             # the big shell rounding (45 deg steps) is not re-bevelled
C.BEVEL_W = 0.0007             # small bevel on hard edges so the locked steel sheen catches them

PAL = {
    'recess': (7, 8, 11), 'steel_black': (11, 12, 18), 'steel_dark': (19, 22, 32),
    'steel_mid': (30, 35, 49), 'steel_light': (50, 57, 76), 'sheen': (86, 98, 122),
    'steel_edge': (148, 154, 164), 'grime': (30, 30, 36), 'silver': (168, 172, 178),
    'eng': (112, 124, 150), 'eng_dk': (4, 5, 8),
    'brass_shadow': (58, 36, 12), 'brass_dark': (112, 76, 24), 'brass': (176, 132, 48),
    'brass_light': (222, 182, 92), 'brass_hi': (250, 228, 156),
    'bone_shadow': (146, 132, 106), 'bone_dark': (186, 172, 144), 'bone': (222, 212, 186),
    'bone_light': (244, 238, 218), 'bone_cut': (74, 54, 38),
    'p_shadow': (7, 7, 8), 'p_dark': (12, 12, 14), 'p_mid': (21, 21, 24),
    'p_light': (33, 33, 37), 'p_high': (64, 64, 70),
    'pf_dark': (22, 22, 26), 'pf_shadow': (19, 19, 23), 'pf_mid': (27, 27, 32),
}
FURN = {'bone', 'bone_panel', 'bone_inlay', 'poly', 'poly_dark', 'bone_end'}


def _h(x, y, s=0):
    return C._h(x, y, s)


def _vn(x, y, sc, s=0):
    return C._vn(x, y, sc, s)


class Atlas:
    """Shelf-packed regions on a 256 px atlas, painted with palette names."""

    def __init__(self, spec):
        self.buf = [PAL['recess']] * (S * S)
        self.reg = {}
        shelves = []   # [y, height, x_used]
        ytop = 0
        for name, w, h in sorted(spec, key=lambda t: (-t[2], -t[1])):
            for sh in shelves:
                if sh[1] >= h and sh[2] + w <= S:
                    self.reg[name] = (sh[2], sh[0], sh[2] + w, sh[0] + h); sh[2] += w; break
            else:
                shelves.append([ytop, h, w]); self.reg[name] = (0, ytop, w, ytop + h); ytop += h
        assert ytop <= S, f'atlas overflow: {ytop}'
        self.used_px = sum(w * h for _, w, h in spec)
        self.smooth_regions = []     # regions painted as continuous tone (bicubic upscale instead of the crisp label upscale)

    def install(self):
        C.REGION.clear(); C.REGION.update(self.reg)
        C.FURN_REGIONS.clear(); C.FURN_REGIONS.update(r for r in self.reg if r in FURN)

    def put(self, x, y, c):
        if 0 <= x < S and 0 <= y < S:
            self.buf[y * S + x] = PAL[c] if isinstance(c, str) else c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.put(x, y, c)

    def fill(self, r, c):
        self.rect(*self.reg[r], c)

    # ---- steel ---------------------------------------------------------
    def steel(self, r, ramp=('steel_dark', 'steel_mid', 'steel_light', 'sheen'), seed=1,
              grime=0.70, edge=True):
        x0, y0, x1, y1 = self.reg[r]; h = y1 - y0
        for y in range(y0, y1):
            for x in range(x0, x1):
                t = (y - y0) / h
                c = ramp[0] if t < 0.22 else ramp[2] if t > 0.72 else ramp[1]
                if 0.80 < t < 0.85:
                    c = ramp[3]
                n = _vn(x, y, 9, seed) * 0.65 + _vn(x, y, 3, seed + 1) * 0.35
                if n > grime:
                    c = 'grime'
                elif n < 0.22:
                    c = ramp[2]
                hv = _h(x, y, seed + 7)
                if hv > 0.996:
                    c = 'steel_edge'
                elif hv > 0.988:
                    c = 'sheen'
                if edge:
                    d = min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y) - 2
                    if 0 <= d <= 1 and _vn(x, y, 2.5, seed + 3) > 0.42:
                        c = 'steel_edge' if d == 0 else 'sheen'
                self.put(x, y, c)

    def _line(self, pts, c, shadow=True):
        for (x, y) in pts:
            xi, yi = int(round(x)), int(round(y))
            if shadow:
                self.put(xi + 1, yi - 1, 'eng_dk')
        for (x, y) in pts:
            self.put(int(round(x)), int(round(y)), c)

    def _spiral(self, cx, cy, r0, rot, dirn, k=0.27, turns=1.55, c='eng'):
        n = int(turns * 2 * math.pi * r0 * 3) + 8
        pts = []
        for i in range(n + 1):
            th = i / n * turns * 2 * math.pi
            rr = r0 * math.exp(-k * th)
            pts.append((cx + rr * math.cos(rot + dirn * th), cy + rr * math.sin(rot + dirn * th)))
        self._line(pts, c)

    def _arch(self, x, y, w, c='eng'):
        """Pointed (lancet) arch with base left at x, base width w, rising from y."""
        pts = []
        for i in range(0, 41):
            a = math.radians(60) * i / 40
            pts.append((x + w - w * math.cos(a), y + w * math.sin(a)))   # left arc (centre = right base)
            pts.append((x + w * math.cos(a), y + w * math.sin(a)))       # right arc (centre = left base)
        self._line(pts, c)

    def scroll_band(self, r, cy_frac=0.5, amp=None, lam=26, seed=3, rot_off=0.0, c='eng'):
        x0, y0, x1, y1 = self.reg[r]
        h = y1 - y0
        cy = y0 + h * cy_frac
        amp = amp if amp is not None else max(2.0, h * 0.10)
        r0 = max(3.0, min(h * 0.22, 7.0))
        vine = [(x, cy + amp * math.sin(2 * math.pi * (x - x0) / lam)) for x in
                [x0 + 3 + i * 0.5 for i in range(int((x1 - x0 - 6) * 2))]]
        self._line(vine, c)
        k = 0
        xx = x0 + 3 + lam * 0.25
        while xx < x1 - 6:
            y = cy + amp * math.sin(2 * math.pi * (xx - x0) / lam)
            up = 1 if k % 2 == 0 else -1
            self._spiral(xx + 1, y + up * r0 * 0.9, r0, -math.pi / 2 * up + rot_off, up, c=c)
            if k % 2 == 0:   # tiny leaf buds
                self._line([(xx + 2 + i, y + up * (1 + i * 0.5)) for i in range(4)], c, shadow=False)
            xx += lam * 0.5; k += 1

    def engraved(self, r, seed=5, ramp=('steel_dark', 'steel_mid', 'steel_light', 'sheen'),
                 scroll=True, arches=True, border=True, lam=24, grime=0.74, cross=False):
        """Blued steel panel with a rule border, scroll vine and a lancet-arch frieze."""
        self.steel(r, ramp, seed, grime=grime, edge=False)
        x0, y0, x1, y1 = self.reg[r]
        w, h = x1 - x0, y1 - y0
        if border:
            for k, c in ((4, 'eng'), (6, 'eng_dk'), (7, 'eng')):
                if h > 18 and w > 18:
                    for x in range(x0 + k, x1 - k):
                        self.put(x, y0 + k, c); self.put(x, y1 - 1 - k, c)
                    for y in range(y0 + k, y1 - k):
                        self.put(x0 + k, y, c); self.put(x1 - 1 - k, y, c)
        if arches and h >= 34:
            aw = 8
            xx = x0 + 10
            while xx + aw * 2 < x1 - 8:
                self._arch(xx, y0 + 9, aw)
                self._arch(xx + 2, y0 + 9, aw - 4) if aw > 6 else None
                xx += aw * 2 + 1
        if scroll:
            top = 9 + (aw * 0.9 + 2 if arches and h >= 34 else 0)
            sub = (x0, int(y0 + top), x1, y1 - 9)
            tmp = 'tmp_scroll'
            self.reg[tmp] = sub
            self.scroll_band(tmp, 0.5, lam=lam, seed=seed)
            del self.reg[tmp]
        if cross:   # small cross patée mid-panel
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            for d in range(-3, 4):
                self.put(cx + d, cy, 'eng'); self.put(cx, cy + d, 'eng')
            for d in (-3, 3):
                for e in (-1, 0, 1):
                    self.put(cx + d, cy + e, 'eng'); self.put(cx + e, cy + d, 'eng')

    def serrations(self, r, step=5):
        x0, y0, x1, y1 = self.reg[r]
        self.steel(r, ('steel_dark', 'steel_mid', 'steel_light', 'sheen'), 11, grime=0.8, edge=False)
        for x in range(x0 + 3, x1 - 3):
            m = (x - x0) % step
            for y in range(y0 + 3, y1 - 3):
                if m in (0, 1):
                    self.put(x, y, 'recess')
                elif m == 2:
                    self.put(x, y, 'sheen')

    # ---- brass ---------------------------------------------------------
    def brass(self, r, seed=21, engrave=False):
        x0, y0, x1, y1 = self.reg[r]; h = y1 - y0
        for y in range(y0, y1):
            for x in range(x0, x1):
                t = (y - y0) / h
                c = 'brass_shadow' if t < 0.08 else 'brass_dark' if t < 0.22 else 'brass' if t < 0.66 else 'brass_light'
                if 0.78 < t < 0.88:
                    c = 'brass_hi'
                n = _vn(x, y, 6, seed)
                if n > 0.80:
                    c = 'brass_dark'
                elif n < 0.18:
                    c = 'brass_light'
                if _h(x, y, seed + 2) > 0.992:
                    c = 'brass_hi'
                self.put(x, y, c)
        if engrave:   # guilloche: diagonal ticks
            for y in range(y0 + 3, y1 - 3):
                for x in range(x0 + 2, x1 - 2):
                    if (x + y) % 6 == 0:
                        self.put(x, y, 'brass_dark')

    # ---- bone ----------------------------------------------------------
    def bone(self, r, seed=31, motif='skull', rim=True):
        x0, y0, x1, y1 = self.reg[r]
        w, h = x1 - x0, y1 - y0
        for y in range(y0, y1):
            for x in range(x0, x1):
                g = math.sin((x - x0) * 0.33 + 3.0 * _vn(x, y, 11, seed) + 0.02 * y)
                c = 'bone_dark' if g > 0.82 else 'bone_light' if g < -0.86 else 'bone'
                if _vn(x, y, 7, seed + 4) > 0.9:
                    c = 'bone_shadow'
                if _h(x, y, seed + 6) > 0.985:
                    c = 'bone_cut' if _h(x, y, seed + 8) > 0.6 else 'bone_dark'
                self.put(x, y, c)
        # hairline cracks
        for i in range(3):
            px, py = x0 + int(_h(i, 1, seed) * w * 0.8) + 4, y0 + int(_h(i, 2, seed) * h * 0.4) + 2
            for k in range(int(h * 0.25)):
                self.put(px + int(2.2 * math.sin(k * 0.8 + i)), py + k, 'bone_cut' if k % 3 else 'bone_shadow')
        if rim:
            for k in range(3):
                c = 'bone_shadow' if k < 2 else 'bone_dark'
                self.rect(x0 + k, y0 + k, x1 - k, y0 + k + 1, c); self.rect(x0 + k, y1 - k - 1, x1 - k, y1 - k, c)
                self.rect(x0 + k, y0 + k, x0 + k + 1, y1 - k, c); self.rect(x1 - k - 1, y0 + k, x1 - k, y1 - k, c)
        cx, cy = (x0 + x1) // 2, y0 + int(h * 0.60)
        if motif == 'skull':
            self.skull(cx, y0 + int(h * 0.60), 16)
            self.cross_bones(cx, y0 + int(h * 0.17), int(w * 0.30))
        elif motif == 'cross':
            self.big_cross(cx, (y0 + y1) // 2, int(min(w, h) * 0.36))
        elif motif == 'filigree':
            sub = (x0 + 6, y0 + 6, x1 - 6, y1 - 6)
            self.reg['tmp_f'] = sub
            for fy in (0.25, 0.75):
                self.scroll_band('tmp_f', fy, lam=16, amp=2.0, seed=seed, c='bone_cut')
            del self.reg['tmp_f']
            self.big_cross(cx, (y0 + y1) // 2, int(min(w, h) * 0.20))

    SKULL_ROWS = [4, 6, 8, 9, 10, 11, 11, 12, 12, 12, 12, 12, 11, 10, 9, 9, 8, 8, 8, 7, 6]   # half widths, top->chin
    SOCKET = {7: (2, 7), 8: (2, 8), 9: (2, 8), 10: (3, 8), 11: (3, 7), 12: (4, 6)}

    def skull(self, cx, cy, R):
        """Hand-drawn pixel skull, 24 px wide at scale 1 (scale = R // 8, min 1)."""
        sc = max(1, R // 8)
        n = len(self.SKULL_ROWS)
        px = {}
        for r, hw in enumerate(self.SKULL_ROWS):
            for dx in range(-hw, hw):
                c = 'bone_light' if (dx < -hw * 0.35 and r < 14) else 'bone'
                if dx > hw * 0.55 or (r > 12 and dx > hw * 0.3):
                    c = 'bone_dark'
                px[(dx, r)] = c
        for r, (a0, a1) in self.SOCKET.items():
            for dx in range(a0, a1 + 1):
                px[(dx - 1, r)] = 'eng_dk'; px[(-dx, r)] = 'eng_dk'
        for r, hw in ((12, 1), (13, 1), (14, 2), (15, 2)):
            for dx in range(-hw, hw):
                px[(dx, r)] = 'eng_dk'
        for r in range(16, 21):
            hw = self.SKULL_ROWS[r]
            for dx in range(-hw + 1, hw - 1):
                if r == 17:
                    px[(dx, r)] = 'bone_cut'
                elif dx % 2 == 0:
                    px[(dx, r)] = 'bone_cut'
        out = dict(px)
        for (dx, r), c in px.items():
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (dx + a, r + b) not in px:
                    out[(dx + a, r + b)] = 'bone_cut'
        for (dx, r), c in out.items():
            for ix in range(sc):
                for iy in range(sc):
                    self.put(cx + dx * sc + ix, cy + (n // 2 - r) * sc + iy, c)

    def cross_bones(self, cx, cy, L):
        for sgn in (-1, 1):
            for i in range(-L, L + 1):
                x, y = cx + i, cy + int(sgn * i * 0.30)
                for t in (-3, -2, -1, 0, 1, 2, 3):
                    self.put(x, y + t, 'bone_cut' if abs(t) == 3 else 'bone_light' if t == 2 else 'bone_dark')
            for sx in (-1, 1):
                kx, ky = cx + sx * L, cy + int(sgn * sx * L * 0.30)
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        if dx * dx + dy * dy <= 9:
                            self.put(kx + dx, ky + dy, 'bone_cut' if dx * dx + dy * dy > 5 else 'bone')

    def big_cross(self, cx, cy, R):
        """Cross patee: bars with flared ends, outline, light edge, centre boss."""
        w = max(2, R // 5)
        def inside(dx, dy):
            ax, ay = abs(dx), abs(dy)
            bar = (ax <= w and ay <= R) or (ay <= w and ax <= R)
            fl = lambda a, b: (R - 2 * w <= a <= R and b <= w + (a - (R - 2 * w)) * 0.6 + 0.5)
            return bar or fl(ay, ax) or fl(ax, ay)
        px = {}
        for dy in range(-R - 3, R + 4):
            for dx in range(-R - 3, R + 4):
                if inside(dx, dy):
                    px[(dx, dy)] = 'bone_light' if (dx + dy < 0 and abs(dx) < R - 1) else 'bone_dark'
        out = dict(px)
        for (dx, dy) in px:
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (dx + a, dy + b) not in px:
                    out[(dx + a, dy + b)] = 'bone_cut'
        for dy in range(-w, w + 1):                    # centre boss
            for dx in range(-w, w + 1):
                if abs(dx) + abs(dy) <= w + 1:
                    out[(dx, dy)] = 'bone_cut' if abs(dx) + abs(dy) == w + 1 else 'bone_shadow'
        for (dx, dy), c in out.items():
            self.put(cx + dx, cy + dy, c)

    # ---- polymer -------------------------------------------------------
    def poly(self, r, seed=41, dark=False, checker=False, fine=False):
        x0, y0, x1, y1 = self.reg[r]
        if fine:       # HD pass: uniform dark polymer with a fine stipple, no blotches / hatch / edge lines
            for y in range(y0, y1):
                for x in range(x0, x1):
                    hv = _h(x, y, seed)
                    c = 'pf_shadow' if hv < 0.38 else 'pf_mid' if hv > 0.985 else 'pf_dark'
                    self.put(x, y, c)
            return
        for y in range(y0, y1):
            for x in range(x0, x1):
                hv = _h(x, y, seed)
                c = 'p_shadow' if hv < 0.30 else 'p_mid' if hv > 0.93 else 'p_dark'
                if dark and c == 'p_mid':
                    c = 'p_dark'
                if checker and ((x + y) % 5 == 0 or (x - y) % 5 == 0):
                    c = 'p_shadow'
                if checker and (x - y) % 5 == 1 and (x + y) % 2 == 0:
                    c = 'p_mid'
                if _vn(x, y, 8, seed + 5) > 0.86:
                    c = 'p_mid'
                d = min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y) - 2
                if 0 <= d <= 1 and _vn(x, y, 3, seed + 6) > 0.62:
                    c = 'p_light'
                self.put(x, y, c)

    # ---- discs / wraps -------------------------------------------------
    def muzzle(self, r, brass=False):
        x0, y0, x1, y1 = self.reg[r]
        cx, cy = (x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2
        R = (x1 - x0) / 2
        for y in range(y0, y1):
            for x in range(x0, x1):
                d = math.hypot(x - cx, y - cy) / R
                if brass:
                    c = 'brass_shadow' if d > 0.92 else 'brass_light' if d > 0.80 else 'brass' if d > 0.5 else 'brass_dark' if d > 0.34 else 'recess'
                else:
                    c = 'steel_dark' if d > 0.92 else 'steel_edge' if d > 0.80 else 'steel_mid' if d > 0.5 else 'steel_light' if d > 0.40 else 'recess'
                self.put(x, y, c)

    def chambers(self, r, n=6, ring='brass'):
        x0, y0, x1, y1 = self.reg[r]
        cx, cy = (x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2
        R = (x1 - x0) / 2
        for y in range(y0, y1):
            for x in range(x0, x1):
                d = math.hypot(x - cx, y - cy) / R
                c = 'steel_mid' if d < 0.97 else 'steel_dark'
                if d > 0.82:
                    c = 'steel_light' if d < 0.95 else 'steel_dark'
                self.put(x, y, c)
        for i in range(n):
            a = 2 * math.pi * (i + 0.5) / n + math.pi / n
            px, py = cx + R * 0.58 * math.cos(a), cy + R * 0.58 * math.sin(a)
            rr = R * 0.24
            for y in range(int(py - rr - 2), int(py + rr + 3)):
                for x in range(int(px - rr - 2), int(px + rr + 3)):
                    d = math.hypot(x - px, y - py)
                    if d <= rr:
                        self.put(x, y, 'recess' if d < rr * 0.72 else 'brass_dark')
                    elif d <= rr + 1.2:
                        self.put(x, y, 'steel_edge')
        for y in range(y0, y1):          # centre pin / ratchet star
            for x in range(x0, x1):
                if math.hypot(x - cx, y - cy) < R * 0.17:
                    self.put(x, y, 'brass_light' if math.hypot(x - cx, y - cy) < R * 0.10 else 'brass_dark')

    def wrap(self, r, rows, row_px, kinds, seed=51, u_bands=None, lam=22):
        """Texture for a revolve(): `rows` ring segments, each row_px high.
        kinds(j) -> 'hi'|'plain'|'eng'|'dark'|'land'|'wall'|'floor'. u_bands:
        [(u0, u1, 'brass')] columns (fractions) painted as brass bands."""
        x0, y0, x1, y1 = self.reg[r]
        w = x1 - x0
        for j in range(rows):
            ya, yb = y0 + j * row_px, y0 + (j + 1) * row_px
            k = kinds(j)
            for y in range(ya, yb):
                for x in range(x0, x1):
                    n = _vn(x, y, 8, seed) * 0.6 + _vn(x, y, 3, seed + 1) * 0.4
                    t = (y - ya) / max(1, row_px - 1)
                    if k == 'hi':
                        c = 'steel_light' if t < 0.5 else 'sheen'
                        if (x * 3 + j) % 11 == 0: c = 'steel_edge'
                    elif k == 'dark':
                        c = 'steel_black' if n < 0.6 else 'steel_dark'
                    elif k == 'wall':
                        c = 'steel_dark'
                    elif k == 'floor':
                        c = 'steel_black' if n < 0.7 else 'recess'
                    elif k == 'land':
                        c = 'steel_light' if t < 0.45 else 'sheen' if t < 0.62 else 'steel_light'
                        if n > 0.82: c = 'steel_mid'
                    else:
                        c = 'steel_mid' if t > 0.5 else 'steel_dark'
                        if n > 0.74: c = 'grime'
                        elif n < 0.2: c = 'steel_light'
                    self.put(x, y, c)
            if k in ('eng', 'land') and row_px >= 3:        # engraved scroll along this row
                sub = (x0 + 2, ya, x1 - 2, yb)
                self.reg['tmp_w'] = sub
                if row_px >= 6:
                    self.scroll_band('tmp_w', 0.5, lam=lam, amp=max(1.0, row_px * 0.16), seed=seed + j)
                else:
                    for x in range(x0 + 2, x1 - 2):
                        if (x // 3 + j) % 2 == 0:
                            self.put(x, ya + row_px // 2, 'eng')
                del self.reg['tmp_w']
        if u_bands:
            for (ua, ub, kind) in u_bands:
                xa, xb = x0 + int(ua * w), x0 + int(ub * w)
                for y in range(y0, y1):
                    for x in range(xa, xb):
                        t = ((y - y0) % row_px) / max(1, row_px - 1)
                        c = 'brass_shadow' if t < 0.2 else 'brass' if t < 0.7 else 'brass_light'
                        if (x - xa) in (0, xb - xa - 1):
                            c = 'brass_shadow'
                        self.put(x, y, c)

    def mag(self, r, seed=61, holes=True):
        x0, y0, x1, y1 = self.reg[r]
        self.steel(r, ('steel_black', 'steel_dark', 'steel_mid', 'steel_light'), seed, grime=0.78, edge=False)
        w, h = x1 - x0, y1 - y0
        for y in range(y0 + 3, y1 - 3):
            for x in range(x0 + 3, x1 - 3):
                if (x - x0) % 6 == 0:
                    self.put(x, y, 'recess')
                elif (x - x0) % 6 == 1:
                    self.put(x, y, 'steel_light')
        if holes:
            for k in range(1, 8):
                yy = y0 + 4 + k * ((h - 8) // 8)
                self.rect(x0 + w // 2 - 3, yy, x0 + w // 2 + 4, yy + 3, 'brass_dark' if k % 3 == 0 else 'recess')

    def save(self, path):
        used = set(self.buf)
        arr = np.array(self.buf, dtype=np.uint8).reshape(S, S, 3)
        up = hd_upscale(arr)
        if self.smooth_regions:
            cr = arr.astype(np.float32)
            for _ in range(2):
                cr = _cr_up2(_cr_up2(cr, 0), 1)
            for r in self.smooth_regions:
                x0, y0, x1, y1 = self.reg[r]
                up[y0 * 4:y1 * 4, x0 * 4:x1 * 4] = np.clip(cr[y0 * 4:y1 * 4, x0 * 4:x1 * 4] + 0.5, 0, 255).astype(np.uint8)
        M._write_png(path, HD, HD, up.tobytes(), bottom_up=True)
        print('atlas colours', len(used), 'region px', self.used_px, 'hd', HD)
        return len(used)


def paint_wood_smooth(A, r, seed=71, end=False):
    """Walnut with smooth continuous long grain (tone ramp, no palette steps); registered for bicubic upscale."""
    x0, y0, x1, y1 = A.reg[r]
    A.smooth_regions.append(r)
    stops = [(0.0, (14, 8, 5)), (0.35, (36, 20, 11)), (0.65, (58, 32, 17)), (0.88, (84, 50, 26)), (1.0, (104, 66, 36))]
    def ramp(t):
        t = max(0.0, min(1.0, t))
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if t <= b:
                f = (t - a) / (b - a)
                return tuple(int(round(ca[k] + (cb[k] - ca[k]) * f)) for k in range(3))
        return stops[-1][1]
    for y in range(y0, y1):
        for x in range(x0, x1):
            u, v = x - x0, y - y0
            warp = _vn(u * 0.020, v * 0.35, 5, seed) * 2.2
            band = 0.5 + 0.5 * math.sin(v * 0.55 + warp * 3.0 + 0.010 * u)
            fine = _vn(u * 0.06, v * 1.9, 2, seed + 4)
            t = 0.20 + 0.50 * band + 0.30 * (fine - 0.5) + 0.20 * (_vn(u * 0.02, v * 0.2, 9, seed + 2) - 0.5)
            if end:
                t = 0.15 + 0.2 * _h(x, y, seed)
            A.put(x, y, ramp(t))


def _epx(a):
    """Scale2x / EPX pixel-art upscale: smooth diagonals, keeps edges crisp (no blur)."""
    h, w, _ = a.shape
    P = a
    Ap = np.vstack([a[:1], a[:-1]])          # up
    Dp = np.vstack([a[1:], a[-1:]])          # down
    Cp = np.hstack([a[:, :1], a[:, :-1]])    # left
    Bp = np.hstack([a[:, 1:], a[:, -1:]])    # right
    eq = lambda x, y: np.all(x == y, axis=2)
    out = np.zeros((h * 2, w * 2, 3), dtype=a.dtype)
    c_a, a_b, d_c, b_d = eq(Cp, Ap), eq(Ap, Bp), eq(Dp, Cp), eq(Bp, Dp)
    c_d, a_c, b_dd, a_d = eq(Cp, Dp), eq(Ap, Cp), eq(Bp, Dp), eq(Ap, Dp)
    ne = lambda m: ~m
    p1 = c_a & ne(eq(Cp, Dp)) & ne(eq(Ap, Bp))
    p2 = a_b & ne(eq(Ap, Cp)) & ne(eq(Bp, Dp))
    p3 = d_c & ne(eq(Dp, Bp)) & ne(eq(Cp, Ap))
    p4 = b_d & ne(eq(Bp, Ap)) & ne(eq(Dp, Cp))
    out[0::2, 0::2] = np.where(p1[..., None], Ap, P)
    out[0::2, 1::2] = np.where(p2[..., None], Bp, P)
    out[1::2, 0::2] = np.where(p3[..., None], Cp, P)
    out[1::2, 1::2] = np.where(p4[..., None], Dp, P)
    return out


def _cr_up2(a, axis):
    """Catmull-Rom 2x upsample along an axis (edge clamped)."""
    a = a.astype(np.float32)
    n = a.shape[axis]
    idx = np.arange(n)
    def take(off):
        return np.take(a, np.clip(idx + off, 0, n - 1), axis=axis)
    p0, p1, p2, p3 = take(-1), take(0), take(1), take(2)
    def cr(t):
        return (0.5 * (-t ** 3 + 2 * t ** 2 - t) * p0 + 0.5 * (3 * t ** 3 - 5 * t ** 2 + 2) * p1 +
                0.5 * (-3 * t ** 3 + 4 * t ** 2 + t) * p2 + 0.5 * (t ** 3 - t ** 2) * p3)
    lo, hi = cr(0.75), cr(0.25)       # samples at -0.25 / +0.25 of the source pixel (centres)
    # output sample k=2i is at source i-0.25 (between i-1 and i, t=0.75 of p_{i-1}), k=2i+1 at i+0.25
    lo = _shift_cr(a, axis, -1, 0.75)
    hi = _shift_cr(a, axis, 0, 0.25)
    shp = list(a.shape); shp[axis] *= 2
    out = np.empty(shp, dtype=np.float32)
    sl = [slice(None)] * 3
    sl[axis] = slice(0, None, 2); out[tuple(sl)] = lo
    sl[axis] = slice(1, None, 2); out[tuple(sl)] = hi
    return out


def _shift_cr(a, axis, base, t):
    n = a.shape[axis]; idx = np.arange(n)
    g = lambda off: np.take(a, np.clip(idx + base + off, 0, n - 1), axis=axis)
    p0, p1, p2, p3 = g(-1), g(0), g(1), g(2)
    return (0.5 * (-t ** 3 + 2 * t ** 2 - t) * p0 + 0.5 * (3 * t ** 3 - 5 * t ** 2 + 2) * p1 +
            0.5 * (-3 * t ** 3 + 4 * t ** 2 + t) * p2 + 0.5 * (t ** 3 - t ** 2) * p3)


def _gblur(f, sig):
    r = max(1, int(sig * 3))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
    for ax in (0, 1):
        pad = [(r, r) if d == ax else (0, 0) for d in range(f.ndim)]
        p = np.pad(f, pad, mode='edge')
        out = np.zeros_like(f)
        for t, w in enumerate(k):
            sl = [slice(None)] * f.ndim; sl[ax] = slice(t, t + f.shape[ax]); out += w * p[tuple(sl)]
        f = out
    return f


def hd_upscale(arr, sig=0.55, beta=12.0):
    """256 logical painter grid -> 1024 smooth, anti-aliased albedo.
    Smooth-label upscale: every palette colour becomes a soft mask (gaussian + Catmull-Rom x4); each output texel is the
    softmax blend of the colours, so contours become clean curves with a ~1px anti-aliased edge and NO stair-steps,
    thin engraving lines stay crisp. A faint fine grain keeps flat areas from looking like plastic."""
    h, w, _ = arr.shape
    cols, inv = np.unique(arr.reshape(-1, 3), axis=0, return_inverse=True)
    inv = inv.reshape(h, w)
    num = np.zeros((h * 4, w * 4, 3), np.float32); den = np.zeros((h * 4, w * 4), np.float32)
    for k, c in enumerate(cols):
        s = _gblur((inv == k).astype(np.float32), sig)
        s = np.repeat(s[..., None], 3, 2)
        for _ in range(2):
            s = _cr_up2(_cr_up2(s, 0), 1)
        e = np.exp(beta * np.clip(s[..., 0], 0, 1))
        num += e[..., None] * c.astype(np.float32); den += e
    f = num / den[..., None]
    rng = np.random.RandomState(7)
    g = rng.normal(0.0, 1.0, f.shape[:2]).astype(np.float32)[..., None]
    f = f * (1.0 + 0.02 * g)
    return np.clip(f + 0.5, 0, 255).astype(np.uint8)


# ---- mesh helpers ----------------------------------------------------------
def shell(part, outer, holes, hw, region='poly', bevel=0.0055, segs=2, bevel_hole=None):
    """One continuous polymer shell: side profile `outer` (z, y) with closed `holes` (thumbhole, trigger hole ...) extruded
    across X (+-hw), then every rim edge (cap/strip) is rounded with a `segs`-step bevel so the sides read as real
    contoured volume instead of a flat cutout. Caps are filled with holes (triangle_fill)."""
    bm = part.bm
    pre = set(bm.faces)
    loops = [outer] + list(holes)
    Ls = [[bm.verts.new(G(-hw, y, z)) for z, y in lp] for lp in loops]
    Rs = [[bm.verts.new(G(hw, y, z)) for z, y in lp] for lp in loops]
    for L, R in zip(Ls, Rs):
        n = len(L)
        for k in range(n):
            bm.faces.new((L[k], L[(k + 1) % n], R[(k + 1) % n], R[k]))
    rim, rim_h = [], []
    for X in (Ls, Rs):
        edges = []
        for li, r in enumerate(X):
            for k in range(len(r)):
                e = bm.edges.get((r[k], r[(k + 1) % len(r)]))
                edges.append(e); (rim if li == 0 else rim_h).append(e)
        bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    new = [f for f in bm.faces if f not in pre]
    bmesh.ops.recalc_face_normals(bm, faces=new)
    if bevel:
        hb = bevel_hole if bevel_hole is not None else bevel
        bmesh.ops.bevel(bm, geom=rim, offset=bevel, segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
        live = [e for e in rim_h if e.is_valid]
        if live:
            bmesh.ops.bevel(bm, geom=live, offset=hb, segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
    new = [f for f in bm.faces if f not in pre]
    bm.normal_update()
    for f in new:
        part._uv_face(f, region)
    return new


def ah_to_zy(poly, theta):
    """(a = along BACK, h = along UP) grip-space -> (z, y) game space."""
    s, c = math.sin(theta), math.cos(theta)
    return [(a * c - h * s, a * s + h * c) for a, h in poly]


def chaikin(poly, it=1):
    for _ in range(it):
        out = []
        n = len(poly)
        for i in range(n):
            p, q = poly[i], poly[(i + 1) % n]
            out += [(0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]), (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])]
        poly = out
    return poly


def hexp(x0, x1, y0, y1, c):
    return [(x0, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c)]


def inset(poly, k):
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in poly]


def revolve(part, stations, cy, segs=10, region='barrel', cx=0.0, cap_f='steel', cap_b='steel',
            shoulder='steel', phase=0.0):
    """Surface of revolution about the Z axis through (cx, cy).
    stations: [(z, r)] r is a float or f(i)->float. Vertex i sits at angle
    2*pi*i/segs (+phase) from +X toward +Y, so i=0 is the right flank and
    i=segs/4 the top. UV: u = z along the part, v = ring segment."""
    bm = part.bm
    zs = [z for z, _ in stations]
    zmin, zmax = min(zs), max(zs)
    span = max(zmax - zmin, 1e-6)
    rings = []
    for z, r in stations:
        ring = []
        for i in range(segs):
            rr = r(i) if callable(r) else r
            a = 2 * math.pi * i / segs + phase
            ring.append(bm.verts.new(G(cx + rr * math.cos(a), cy + rr * math.sin(a), z)))
        rings.append(ring)
    faces, meta = [], []
    for si, (A, B) in enumerate(zip(rings, rings[1:])):
        for k in range(segs):
            k2 = (k + 1) % segs
            f = bm.faces.new((A[k], A[k2], B[k2], B[k])); faces.append(f); meta.append((si, k))
    cap0 = bm.faces.new(list(reversed(rings[0]))); capN = bm.faces.new(rings[-1])
    part._fix_normals(faces + [cap0, capN], rings)
    x0, y0, x1, y1 = C.REGION[region]
    u0, v0, u1, v1 = (x0 + C.PAD) / S, (y0 + C.PAD) / S, (x1 - C.PAD) / S, (y1 - C.PAD) / S
    for f, (si, k) in zip(faces, meta):
        za, zb = stations[si][0], stations[si + 1][0]
        if abs(za - zb) < 1e-7:
            part._uv_face(f, shoulder); continue
        for l in f.loops:
            vi = rings[si].index(l.vert) if l.vert in rings[si] else rings[si + 1].index(l.vert)
            kk = vi if not (k == segs - 1 and vi == 0) else segs
            z = za if l.vert in rings[si] else zb
            l[part.uv].uv = (u0 + (u1 - u0) * (z - zmin) / span, v0 + (v1 - v0) * kk / segs)
        f.material_index = 1 if region in C.FURN_REGIONS else 0
    part._uv_face(cap0, cap_b); part._uv_face(capN, cap_f)


def tube(part, pts_zy, w, h, region='steel', x=0.0, top=None):
    """Rectangular section (w across X, h in the YZ plane) swept along a
    polyline of (z, y) points. Quad strips + end caps, planar-mapped."""
    bm = part.bm
    n = len(pts_zy)
    rings = []
    for i, (z, y) in enumerate(pts_zy):
        a = pts_zy[max(i - 1, 0)]; b = pts_zy[min(i + 1, n - 1)]
        tz, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tz, ty) or 1.0
        tz, ty = tz / ln, ty / ln
        nz, ny = -ty, tz           # in-plane normal
        ring = []
        for sx, sn in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            ring.append(bm.verts.new(G(x + sx * w * 0.5, y + ny * sn * h * 0.5, z + nz * sn * h * 0.5)))
        rings.append(ring)
    faces = []
    for A, B in zip(rings, rings[1:]):
        for k in range(4):
            faces.append(bm.faces.new((A[k], A[(k + 1) % 4], B[(k + 1) % 4], B[k])))
    caps = [bm.faces.new(list(reversed(rings[0]))), bm.faces.new(rings[-1])]
    part._fix_normals(faces + caps, rings)
    for f in faces + caps:
        part._uv_face(f, region)


def prism_ah(part, poly_ah, theta, x0, x1, region='steel', side=None, top=None):
    part.prism(ah_to_zy(poly_ah, theta), x0, x1, region, side=side, top=top)


def build_objects(parts, mats):
    return {p.name: p.to_object(mats) for p in parts}


def write_wiring_dump(prefix):
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    empties = [o for o in bpy.context.scene.objects if o.type == 'EMPTY']
    print('WIRING', prefix)
    for e in sorted(empties, key=lambda o: o.name):
        g = M.game_of(e.matrix_world.translation)
        print(f'  empty {e.name:14s} game=({g.x:+.4f}, {g.y:+.4f}, {g.z:+.4f}) parent={e.parent.name if e.parent else None}')
    tris = 0
    for m in sorted(meshes, key=lambda o: o.name):
        mn, mx, c, size = M.mesh_bounds_game([m])
        t = sum(len(p.vertices) - 2 for p in m.data.polygons); tris += t
        print(f'  mesh {m.name:14s} tris={t:4d} size=({size.x:.4f},{size.y:.4f},{size.z:.4f}) y[{mn.y:+.4f},{mx.y:+.4f}] z[{mn.z:+.4f},{mx.z:+.4f}]')
    mn, mx, c, size = M.mesh_bounds_game(meshes)
    print(f'  TOTAL tris={tris} size={tuple(round(v, 4) for v in size)}')


# ---- previews ----------------------------------------------------------------
def render_gun(glb, out_dir, gid, relief=0.30, small=False):
    """Sheen-style renders (same rig as the approved 1911 sheen previews) from the
    exported GLB: <gid>_side.png, <gid>_three.png (uncropped, 5% margin) and
    <gid>_sights.png (eye on the sight line at the ADS eye relief)."""
    M.reset_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        for slot in o.material_slots:
            for n in slot.material.node_tree.nodes:
                if n.type == 'TEX_IMAGE':
                    n.interpolation = 'Linear'
    emp = {o.name: M.game_of(o.matrix_world.translation) for o in bpy.context.scene.objects if o.type == 'EMPTY'}
    mn, mx, center, size = M.mesh_bounds_game(meshes)
    L = max(size.z, size.y * 1.6, 0.2)
    k = L / 0.22
    cam, ground = M.setup_preview_scene()
    sc = bpy.context.scene
    quick = bool(os.environ.get('QR'))
    sc.cycles.samples = 12 if quick else 48
    rx, ry = (900, 525) if quick else (1200, 700)
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    ground.location = G(center.x, mn.y - 0.002, center.z); ground.scale = (k * 1.5,) * 3
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.022, 0.024, 0.03, 1)
    gb = ground.data.materials[0].node_tree.nodes['Principled BSDF']
    gb.inputs['Base Color'].default_value = (0.006, 0.006, 0.007, 1)
    for name, e in (('key', 0.5), ('fill', 0.5), ('rim', 1.0)):
        lo = bpy.data.objects[name]
        lo.location = G(center + (M.game_of(lo.location) - Vector((0, 0, 0))) * k)
        lo.data.size *= k; lo.data.energy *= e * k * 1.6
        lo.rotation_euler = (G(center) - lo.location).to_track_quat('-Z', 'Y').to_euler()
    d = bpy.data.lights.new('top_strip', 'AREA'); d.shape = 'RECTANGLE'
    d.size, d.size_y, d.energy, d.color = 0.03 * k, 0.4 * k, 3.0 * k * 1.6, (0.85, 0.92, 1.0)
    o = bpy.data.objects.new('top_strip', d); sc.collection.objects.link(o)
    o.location = G(center.x, mx.y + 0.25 * k, center.z)
    look = G(center.x, center.y, center.z)
    corners = [G(Vector((x, y, z))) for x in (mn.x, mx.x) for y in (mn.y, mx.y) for z in (mn.z, mx.z)]
    os.makedirs(out_dir, exist_ok=True)

    def shoot(path, loc, lookat, lens, up_fit=True):
        cam.data.lens = lens
        M.aim_camera(cam, lookat, loc)
        cam.data.clip_end = max(float(cam.data.clip_end), 5.0)
        cam.data.clip_start = 0.01
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print('rendered', path)

    for name, direction, lens in (('side', Vector((-1.0, 0.04, 0.0)), 60),
                                  ('three', Vector((0.72, 0.24, -0.65)), 60)):
        dirv = G(direction.normalized())
        cam.data.lens = lens
        dist, loc = C.preview_fit_distance(look, look + dirv * 2.0, corners, lens, rx, ry, margin=0.05)
        nx0, nx1, ny0, ny1 = C.preview_ndc_extents(look, loc, corners, lens, rx, ry)
        print(f'FRAME {name} dist={dist:.3f} ndc_x[{nx0:+.3f},{nx1:+.3f}] ndc_y[{ny0:+.3f},{ny1:+.3f}]')
        assert max(abs(nx0), abs(nx1), abs(ny0), abs(ny1)) < 0.999, 'cropped'
        shoot(os.path.join(out_dir, f'{gid}_{name}.png'), loc, look, lens)
    if 'rear_sight' in emp and 'front_sight' in emp:
        r, f = emp['rear_sight'], emp['front_sight']
        dirg = (f - r).normalized()
        eye = r - dirg * relief
        shoot(os.path.join(out_dir, f'{gid}_sights.png'), G(eye), G(r + dirg * 1.0), 38)


def run(build_fn, render_fn, name):
    import argparse
    raw = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--out-dir', default='assets/models/gun')
    p.add_argument('--render-glb', default='')
    p.add_argument('--render-dir', default='/workspace/base_gun_previews')
    p.add_argument('--small-dir', default='')
    a = p.parse_args(raw)
    if a.render_glb:
        render_fn(a.render_glb, a.render_dir)
    else:
        build_fn(os.path.abspath(a.out_dir))
    print('DONE')
