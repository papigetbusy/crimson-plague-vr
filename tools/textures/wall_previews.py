"""Before/after sheets per wall set: original (top) vs v2 (bottom), nearest-neighbour upscaled,
plus a 2x2 tiled strip of each v2 texture to show the seams.
usage: python3 tools/textures/wall_previews.py [out_dir ...]  (default assets/textures/walls/previews)"""
import os, sys, glob
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W = os.path.join(ROOT, 'assets/textures/walls')
OUTS = sys.argv[1:] or [os.path.join(W, 'previews')]
ORDER = ['texStone', 'texPanel', 'texPillar', 'texCeil', 'texFloor', 'texFloor2', 'texFloor3', 'texFloorEdge', 'texBanner', 'texCloth', 'texCarpet', 'texGold']
S = 4          # original px -> 4 screen px; v2 (2x) -> 2 screen px, same on-screen size
GAP, LAB = 10, 18
for setdir in sorted(glob.glob(os.path.join(W, 'original', '*'))):
    s = os.path.basename(setdir)
    names = [n for n in ORDER if os.path.exists(os.path.join(setdir, n + '.png'))]
    cw = 32 * S
    width = GAP + len(names) * (cw + GAP)
    rowh = 64 * S
    height = LAB + (LAB + rowh + GAP) * 3
    sheet = Image.new('RGB', (width, height), (18, 16, 22)); d = ImageDraw.Draw(sheet)
    d.text((GAP, 3), f'{s}: original (row 1) | v2 Crimson Halls repaint (row 2) | v2 tiled 2x2 (row 3)', fill=(232, 216, 160))
    for i, n in enumerate(names):
        x = GAP + i * (cw + GAP)
        o = Image.open(os.path.join(setdir, n + '.png')).convert('RGB')
        v = Image.open(os.path.join(W, 'v2', s, n + '.png')).convert('RGB')
        sc = cw / o.width
        y = LAB
        d.text((x, y + 2), n, fill=(200, 190, 170)); y += LAB
        sheet.paste(o.resize((cw, int(o.height * sc)), Image.NEAREST), (x, y)); y += rowh + GAP
        sheet.paste(v.resize((cw, int(v.height * sc / 2)), Image.NEAREST), (x, y)); y += rowh + GAP
        t = Image.new('RGB', (v.width * 2, v.height * 2))
        for ty in (0, 1):
            for tx in (0, 1): t.paste(v, (tx * v.width, ty * v.height))
        sheet.paste(t.resize((cw, int(t.height * cw / t.width)), Image.NEAREST), (x, y))
    for out in OUTS:
        os.makedirs(out, exist_ok=True)
        sheet.save(os.path.join(out, f'{s}_before_after.png'), optimize=True)
    print(s, sheet.size)
