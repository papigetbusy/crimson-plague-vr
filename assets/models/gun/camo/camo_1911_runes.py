"""Gothic / demonic sigils for the LEGENDARY slide, in slide-panel pixel space (panel = 992 x 114 px, y down).
Polylines are shared by the painter (engraved channel + painted crimson fallback) and the Blender build (emissive flat ribbons)."""
import math
def _circle(cx, cy, r, n=16): return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
def _arc(cx, cy, r, a0, a1, n=8): return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
# unit box: x 0..1, y 0..1 (up)
SIGILS = {
 'cross_thorn': [[(.5, 0), (.5, 1)], [(.14, .32), (.86, .32)], [(.14, .32), (.04, .46)], [(.86, .32), (.96, .46)], [(.5, .74), (.30, .84)], [(.5, .74), (.70, .84)]],
 'seal':        [_circle(.5, .5, .5, 18), [(.22, .74), (.78, .74), (.5, .24), (.22, .74)]],
 'leviathan':   [[(.5, .02), (.5, .98)], [(.18, .74), (.82, .74)], [(.30, .50), (.70, .50)], [(.5, .02), (.28, 0.0)], [(.5, .02), (.72, 0.0)]],
 'horned':      [_arc(.5, .96, .44, math.pi * 0.95, math.pi * 0.05, 8)[::-1], [(.5, .52), (.5, 0)], [(.28, .22), (.72, .22)]],
 'trident':     [[(.5, 0), (.5, 1)], [(.12, .96), (.12, .52), (.88, .52), (.88, .96)], [(.12, .96), (.0, .80)], [(.88, .96), (1.0, .80)]],
 'blackletter': [[(.0, 0), (.22, 0)], [(.78, 0), (1, 0)], [(.1, 0), (.1, 1), (.5, .5), (.9, 1), (.9, 0)], [(.1, 1), (.0, .86)]],
}
W, H = 992, 114
GLYPH_H = 40.0; GLYPH_W = 34.0
FRAME_W, FRAME_H = 54.0, 66.0
CY = 0.52 * H
SLOTS = {   # side -> list of (u centre, sigil)
 'L': [(0.115, 'cross_thorn'), (0.215, 'seal'), (0.315, 'blackletter'), (0.415, 'leviathan'), (0.515, 'horned'), (0.615, 'trident'), (0.715, 'cross_thorn')],
 'R': [(0.245, 'seal'), (0.625, 'blackletter'), (0.715, 'cross_thorn'), (0.805, 'horned'), (0.895, 'leviathan')],
}
STROKE_PX = 9.0

def polylines(side):
    out = []
    for uc, name in SLOTS[side]:
        cx = uc * W
        for pl in SIGILS[name]:
            out.append([(cx - GLYPH_W / 2 + x * GLYPH_W, CY + (0.5 - y) * GLYPH_H) for x, y in pl])
    return out

def frames(side):
    """closed rectangular cartouche outlines (px) around each sigil, with notched corners"""
    out = []
    for uc, name in SLOTS[side]:
        cx = uc * W; x0, x1 = cx - FRAME_W / 2, cx + FRAME_W / 2; y0, y1 = CY - FRAME_H / 2, CY + FRAME_H / 2; k = 6
        out.append([(x0 + k, y0), (x1 - k, y0), (x1, y0 + k), (x1, y1 - k), (x1 - k, y1), (x0 + k, y1), (x0, y1 - k), (x0, y0 + k), (x0 + k, y0)])
    return out
