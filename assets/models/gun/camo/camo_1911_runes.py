"""Rune strokes for the LEGENDARY slide, in slide-panel pixel space (panel = 992 x 114 px, y down, top of slide = row 0).
Used by the painter (engraved channel + painted crimson fallback) AND by the Blender build (emissive ribbon geometry), so both line up exactly."""
GLYPHS = {
    'fehu':  [((0, 0), (0, 1)), ((0, .55), (.7, .92)), ((0, .28), (.7, .65))],
    'uruz':  [((0, 0), (0, 1)), ((0, 1), (.7, .78)), ((.7, .78), (.7, 0))],
    'thur':  [((0, 0), (0, 1)), ((0, .78), (.62, .5)), ((.62, .5), (0, .24))],
    'ansz':  [((0, 0), (0, 1)), ((0, 1), (.62, .78)), ((0, .68), (.62, .46))],
    'raid':  [((0, 0), (0, 1)), ((0, 1), (.62, .8)), ((.62, .8), (0, .55)), ((0, .55), (.66, 0))],
    'kena':  [((.62, 1), (0, .5)), ((0, .5), (.62, 0))],
    'gebo':  [((0, 0), (.7, 1)), ((0, 1), (.7, 0))],
    'wunj':  [((0, 0), (0, 1)), ((0, 1), (.6, .76)), ((.6, .76), (0, .52))],
    'haga':  [((0, 0), (0, 1)), ((.7, 0), (.7, 1)), ((0, .66), (.7, .34))],
    'isa':   [((.3, 0), (.3, 1))],
    'sowi':  [((.55, 1), (.1, .66)), ((.1, .66), (.55, .34)), ((.55, .34), (.1, 0))],
    'tiwa':  [((.35, 0), (.35, 1)), ((.35, 1), (0, .66)), ((.35, 1), (.7, .66))],
}
ORDER = ['fehu', 'uruz', 'ansz', 'kena', 'haga', 'tiwa', 'raid', 'gebo', 'thur', 'wunj']
W, H = 992, 114
ROW_TOP, ROW_BOT = 0.50, 0.80           # rune band (fraction of height from the top): below the ejection port floor (0.44 from top)
GLYPH_H = 26.0                          # px  (~5 mm on the slide)
GLYPH_W = 17.0

def strokes(side):
    """list of ((x0,y0),(x1,y1)) in panel px"""
    out = []
    u_lo, u_hi = (0.20, 0.965) if side == 'R' else (0.035, 0.80)
    n = len(ORDER)
    cy = (ROW_TOP + ROW_BOT) / 2 * H
    for i, g in enumerate(ORDER):
        cx = (u_lo + (u_hi - u_lo) * (i + 0.5) / n) * W
        x_left = cx - GLYPH_W * 0.5
        for (a, b) in GLYPHS[g]:
            out.append(((x_left + a[0] * GLYPH_W, cy + (0.5 - a[1]) * GLYPH_H), (x_left + b[0] * GLYPH_W, cy + (0.5 - b[1]) * GLYPH_H)))
    return out
