"""Build a PS2-era low-poly M1911 for Crimson Plague VR.

Creates a clean (non-voxel) mesh at real scale (~0.216 m long), origin at the
grip, magazine as its own object, and a single 256x256 nearest-filter atlas.
Saves the .blend, writes the albedo PNG, and optionally renders previews.

Usage:
  blender -b --python tools/blender/build_pistol_1911.py -- \\
      --out-dir assets/models/gun --render-dir /workspace/shots/pistol1911
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# ---------------------------------------------------------------------------
# Game space is +Y up, muzzle toward -Z, metres, origin at the palm / grip.
# Blender is +Z up, Y forward. Convert with G(); game coords from a Blender
# vertex are (x, z, -y).
# ---------------------------------------------------------------------------

def G(x, y=None, z=None):
    if y is None or z is None:
        x, y, z = x
    return Vector((x, -z, y))


def game_of(v):
    return Vector((v.x, v.z, -v.y))


# ---- dimensions (metres), tuned to a Government Model 1911 -----------------
LENGTH = 0.216
ANG = math.radians(18.0)

# Grip (origin is the palm, mid-panel).
GRIP_W = 0.034          # total width with panels
GRIP_FRAME_W = 0.026    # steel frame under the panels
GRIP_THICK = 0.046      # front strap to backstrap
GRIP_UP = 0.036         # origin to underside of the frame, along the grip
GRIP_DOWN = 0.056       # origin to mag-well lip, along the grip

# Slide / frame
SLIDE_W = 0.025
SLIDE_H = 0.024
SLIDE_LEN = 0.196
CH_TOP = 0.0036
CH_BOT = 0.0010
FRAME_W = 0.021
DUST_H = 0.013

# Derived placement: rearmost point (hammer spur) at +Z, muzzle at rear-LENGTH.
# The grip sits under the rear of the frame; the slide rear is just behind the
# backstrap top, the hammer and beavertail take the last 16 mm.
Z_REAR = 0.036
Z_MUZZLE = Z_REAR - LENGTH          # -0.180
Z_SLIDE_FRONT = Z_MUZZLE + 0.004    # barrel sticks out 4 mm
Z_SLIDE_REAR = Z_SLIDE_FRONT + SLIDE_LEN
Z_BUSHING = Z_SLIDE_FRONT
Z_DUST_FRONT = Z_SLIDE_FRONT + 0.016
Z_PORT_FRONT = Z_SLIDE_FRONT + 0.088
Z_PORT_REAR = Z_PORT_FRONT + 0.048

UP = Vector((0.0, math.cos(ANG), -math.sin(ANG)))    # along the grip, toward the slide
DOWN = -UP
BACK = Vector((0.0, math.sin(ANG), math.cos(ANG)))  # front strap -> backstrap
RIGHT = Vector((1.0, 0.0, 0.0))

GRIP_TOP = UP * GRIP_UP          # junction with the frame
GRIP_BOT = DOWN * GRIP_DOWN      # mag-well lip

# Frame top (= slide underside) sits DUST_H above the dust-cover bottom.
# At the grip, the frame underside is GRIP_TOP.
# Dust cover underside is a little above the trigger-guard top; set it so the
# slide sits in a natural place above the hand.
Y_FRAME_BOT = GRIP_TOP.y          # ≈ 0.034
Y_SLIDE_BOT = Y_FRAME_BOT + DUST_H
Y_SLIDE_TOP = Y_SLIDE_BOT + SLIDE_H
Y_SLIDE_CY = (Y_SLIDE_BOT + Y_SLIDE_TOP) * 0.5
Y_BORE = Y_SLIDE_CY               # barrel sits in the middle of the slide

BARREL_R = 0.0064
BUSHING_R = 0.0076
BORE_R = 0.0032


# ---- atlas ----------------------------------------------------------------
TEX_SIZE = 256
TILE = 32
PAD = 3

# Palette (sRGB 8-bit), ~12 colours, blued steel + walnut grips.
PAL = {
    'steel_dark':  (14, 16, 22),
    'steel_mid':   (24, 28, 36),
    'steel_light': (48, 54, 64),
    'steel_edge':  (82, 90, 102),
    'sheen':       (18, 22, 32),
    'recess':      (10, 11, 13),
    'silver':      (154, 160, 166),
    'wood_dark':   (58, 34, 18),
    'wood_mid':    (92, 56, 30),
    'wood_light':  (124, 80, 42),
    'wood_high':   (154, 106, 58),
    'screw':       (72, 64, 54),
    'groove':      (16, 17, 20),
}

# Swatch tiles (tx, ty) in the first row, 32 px cells.
SWATCH = {
    'steel_dark':  (0, 0),
    'steel_mid':   (1, 0),
    'steel_light': (2, 0),
    'steel_edge':  (3, 0),
    'recess':      (4, 0),
    'silver':      (5, 0),
    'sheen':       (6, 0),
    'screw':       (7, 0),
}
# Special regions in pixels (x0, y0, x1, y1), y from the top of the image
# when painting with PIL, but UVs use OpenGL (y up). We paint with y-down
# then flip, OR we treat blender image pixels as bottom-up. We'll paint
# with PIL (y down) and load the file; Blender/glTF use the image as-is
# with UV (0,0) at bottom-left, so we must invert V when assigning, or
# flip the image. We'll flip the image vertically before saving so UV
# (0,0) is the bottom-left of our layout.
# Layout after flip (UV space, y up):
#   y 0-32:   swatches
#   y 32-96:  serrations (x 0-128), muzzle disc (x 128-192)
#   y 96-256: wood panel (x 0-128)
REGION = {
    'serration': (0, 32, 128, 96),
    'muzzle':    (128, 32, 192, 96),
    'wood':      (0, 96, 128, 256),
}


def _argv():
    raw = sys.argv
    return raw[raw.index('--') + 1:] if '--' in raw else []


def _parse():
    p = argparse.ArgumentParser()
    p.add_argument('--out-dir', default='assets/models/gun')
    p.add_argument('--render-dir', default='')
    p.add_argument('--name', default='pistol_1911_ps2')
    return p.parse_args(_argv())


# ---- texture --------------------------------------------------------------
def _write_png(path, w, h, rgb, bottom_up=True):
    """Minimal RGB PNG writer (stdlib only). rgb is w*h*3 bytes.
    If bottom_up, row 0 is UV y=0 (image bottom), which is what we want
    so the saved file matches Blender/glTF UV space after load? Careful:
    PNG row 0 is the TOP of the image. Blender's bpy image load uses the
    PNG as a file, and the glTF/UV convention is (0,0) at bottom-left, so
    row 0 of the PNG is V=1. Therefore we store UV-space rows flipped:
    we write the last UV row first.
    """
    import struct, zlib
    def chunk(tag, data):
        crc = zlib.crc32(tag + data) & 0xffffffff
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', crc)
    raw = bytearray()
    for y in range(h):
        # PNG y=0 is the top = UV v=1 = last UV row if bottom_up
        src_y = (h - 1 - y) if bottom_up else y
        raw.append(0)  # no filter
        raw.extend(rgb[src_y * w * 3:(src_y + 1) * w * 3])
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png)


def paint_atlas(path):
    w = h = TEX_SIZE
    pix = bytearray(w * h * 3)
    rec = PAL['recess']

    def idx(x, y):
        return (y * w + x) * 3

    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h:
            i = idx(x, y)
            pix[i] = c[0]; pix[i + 1] = c[1]; pix[i + 2] = c[2]

    def rect(x0, y0, x1, y1, c):
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(w, x1); y1 = min(h, y1)
        for y in range(y0, y1):
            row = idx(0, y)
            for x in range(x0, x1):
                i = row + x * 3
                pix[i] = c[0]; pix[i + 1] = c[1]; pix[i + 2] = c[2]

    def ellipse(cx, cy, rx, ry, c):
        rx = max(1, int(rx)); ry = max(1, int(ry))
        for y in range(-ry, ry + 1):
            for x in range(-rx, rx + 1):
                if (x / rx) ** 2 + (y / ry) ** 2 <= 1.0:
                    put(int(cx + x), int(cy + y), c)

    # Fill background, then swatches (UV space, y up).
    rect(0, 0, w, h, rec)
    for name, (tx, ty) in SWATCH.items():
        rect(tx * TILE, ty * TILE, (tx + 1) * TILE, (ty + 1) * TILE, PAL[name])

    # Serration trim: vertical grooves along V, repeating along U.
    sx0, sy0, sx1, sy1 = REGION['serration']
    rect(sx0, sy0, sx1, sy1, PAL['steel_mid'])
    pitch = 8
    x = sx0 + 4
    while x < sx1 - 2:
        rect(x, sy0, x + 2, sy1, PAL['groove'])
        if x + 3 < sx1:
            for y in range(sy0, sy1, 2):
                put(x + 3, y, PAL['steel_light'])
        x += pitch

    # Muzzle disc: steel ring, dark bore.
    mx0, my0, mx1, my1 = REGION['muzzle']
    rect(mx0, my0, mx1, my1, PAL['steel_dark'])
    cx = (mx0 + mx1 - 1) / 2
    cy = (my0 + my1 - 1) / 2
    ellipse(cx, cy, 28, 28, PAL['steel_mid'])
    ellipse(cx, cy, 25, 25, PAL['steel_light'])
    ellipse(cx, cy, 22, 22, PAL['steel_mid'])
    ellipse(cx, cy, 12, 12, PAL['recess'])

    # Walnut panel with coarse diamond checkering, hard grain, one screw.
    wx0, wy0, wx1, wy1 = REGION['wood']
    rect(wx0, wy0, wx1, wy1, PAL['wood_mid'])
    for i, col in enumerate((PAL['wood_dark'], PAL['wood_light'], PAL['wood_dark'], PAL['wood_high'], PAL['wood_dark'])):
        x = wx0 + 8 + i * 22
        rect(x, wy0, x + 8, wy1, col)
    step = 12
    for k in range(-20, 30):
        for t in range(-20, 40):
            x1 = wx0 + k * step + t
            y1 = wy0 + t
            if wx0 <= x1 < wx1 and wy0 <= y1 < wy1:
                put(x1, y1, PAL['wood_dark'])
            x2 = wx0 + k * step + t
            y2 = wy1 - 1 - t
            if wx0 <= x2 < wx1 and wy0 <= y2 < wy1:
                put(x2, y2, PAL['wood_dark'])
    scx = (wx0 + wx1) / 2
    scy = wy0 + (wy1 - wy0) * 0.42
    ellipse(scx, scy, 10, 10, PAL['screw'])
    ellipse(scx, scy, 8, 8, PAL['silver'])
    ellipse(scx, scy, 5, 5, PAL['steel_dark'])
    rect(int(scx - 5), int(scy - 1), int(scx + 6), int(scy + 2), PAL['recess'])

    _write_png(path, w, h, bytes(pix), bottom_up=True)
    return path


# ---- mesh helpers ---------------------------------------------------------
def _tex_layer(bm):
    layer = bm.faces.layers.string.get('tex')
    if layer is None:
        layer = bm.faces.layers.string.new('tex')
    return layer


def _tag(bm, faces, name):
    # Custom-data layers must exist BEFORE the faces we tag are created,
    # otherwise the BMFace wrappers go stale. _tex_layer is called at the
    # start of every builder for that reason.
    layer = _tex_layer(bm)
    b = name.encode()
    # Re-resolve from the current bmesh in case a wrapper is stale.
    by_idx = {f.index: f for f in bm.faces}
    for f in faces:
        try:
            idx = f.index
            live = by_idx.get(idx, f)
            live[layer] = b
        except ReferenceError:
            continue


def add_box(bm, center, size, axes=None, chamfer=0.0, tex='steel_mid'):
    """Axis-aligned (or oriented) box in game space. size is full extents."""
    _tex_layer(bm)
    ax, ay, az = axes or (RIGHT, Vector((0, 1, 0)), Vector((0, 0, 1)))
    before = set(bm.faces)
    geo = bmesh.ops.create_cube(bm, size=1.0)
    verts = geo['verts']
    c = Vector(center)
    sx, sy, sz = size
    for v in verts:
        g = c + ax * (v.co.x * sx) + ay * (v.co.y * sy) + az * (v.co.z * sz)
        v.co = G(g)
    if chamfer > 0:
        vset = set(verts)
        edges = [e for e in bm.edges if e.verts[0] in vset and e.verts[1] in vset]
        bmesh.ops.bevel(bm, geom=edges, offset=chamfer, segments=1,
                        profile=0.7, affect='EDGES')
    new_faces = [f for f in bm.faces if f not in before]
    _tag(bm, new_faces, tex)
    return new_faces


def add_cyl(bm, p0, p1, radius, segs=8, tex='steel_mid', cap_ends=True, inner=0.0, cap_tex=None):
    """Cylinder (or tube if inner>0) from game-space p0 to p1."""
    _tex_layer(bm)
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    length = axis.length
    if length < 1e-8:
        return []
    axis.normalize()
    # Orthonormal basis in game space.
    helper = RIGHT if abs(axis.dot(RIGHT)) < 0.9 else Vector((0, 1, 0))
    u = axis.cross(helper)
    if u.length < 1e-8:
        u = axis.cross(Vector((0, 0, 1)))
    u.normalize()
    v = axis.cross(u)
    v.normalize()

    before = set(bm.faces)
    rings = []
    for t, r in ((0.0, radius), (1.0, radius)):
        ring = []
        origin = p0.lerp(p1, t)
        for i in range(segs):
            a = 2 * math.pi * i / segs
            g = origin + u * (math.cos(a) * r) + v * (math.sin(a) * r)
            vert = bm.verts.new(G(g))
            ring.append(vert)
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))

    inner_rings = []
    if inner > 0:
        for t, r in ((0.0, inner), (1.0, inner)):
            ring = []
            origin = p0.lerp(p1, t)
            for i in range(segs):
                a = 2 * math.pi * i / segs
                g = origin + u * (math.cos(a) * r) + v * (math.sin(a) * r)
                vert = bm.verts.new(G(g))
                ring.append(vert)
            inner_rings.append(ring)
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((inner_rings[0][j], inner_rings[0][i], inner_rings[1][i], inner_rings[1][j]))
        # annular caps
        if cap_ends:
            for end, (outer, inn) in enumerate(((rings[0], inner_rings[0]), (rings[1], inner_rings[1]))):
                for i in range(segs):
                    j = (i + 1) % segs
                    if end == 0:
                        bm.faces.new((outer[j], outer[i], inn[i], inn[j]))
                    else:
                        bm.faces.new((outer[i], outer[j], inn[j], inn[i]))
    elif cap_ends:
        if segs >= 3:
            bm.faces.new(list(reversed(rings[0])))
            bm.faces.new(rings[1])

    new_faces = [f for f in bm.faces if f not in before]
    _tag(bm, new_faces, tex)
    if cap_tex and cap_ends:
        # retag caps roughly: faces whose average is near an end
        ends = {G(p0)[:], G(p1)[:]}
        for f in new_faces:
            c = f.calc_center_median()
            if min((c - Vector(e)).length for e in (G(p0), G(p1))) < radius * 0.6 + 0.002:
                # only the outer cap-ish; skip, muzzle tagged separately later
                pass
    return new_faces


def add_sweep(bm, path, width, height, up=None, tex='steel_mid', closed=False):
    """Sweep a rectangular profile along a game-space path (list of Vectors)."""
    _tex_layer(bm)
    path = [Vector(p) for p in path]
    n = len(path)
    if n < 2:
        return []
    if up is None:
        up = Vector((0, 1, 0))
    else:
        up = Vector(up)
    before = set(bm.faces)
    rings = []
    for i, p in enumerate(path):
        if i == 0:
            tang = (path[i + 1] - p).normalized()
        elif i == n - 1:
            tang = (p - path[i - 1]).normalized()
        else:
            tang = (path[i + 1] - path[i - 1]).normalized()
        side = tang.cross(up)
        if side.length < 1e-8:
            side = tang.cross(RIGHT)
        side.normalize()
        local_up = side.cross(tang).normalized()
        hw, hh = width * 0.5, height * 0.5
        corners = [
            p - side * hw - local_up * hh,
            p + side * hw - local_up * hh,
            p + side * hw + local_up * hh,
            p - side * hw + local_up * hh,
        ]
        ring = [bm.verts.new(G(c)) for c in corners]
        rings.append(ring)
    for i in range(n - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(4):
            k2 = (k + 1) % 4
            bm.faces.new((a[k], a[k2], b[k2], b[k]))
    if closed and n > 2:
        a, b = rings[-1], rings[0]
        for k in range(4):
            k2 = (k + 1) % 4
            bm.faces.new((a[k], a[k2], b[k2], b[k]))
    else:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    new_faces = [f for f in bm.faces if f not in before]
    _tag(bm, new_faces, tex)
    return new_faces


def extrude_profiles(bm, stations, tex='steel_mid', cap=True, front_hole=None):
    """stations: list of (z, profile) where profile is list of (x, y) game.

    Optional front_hole = radius to punch a circular hole in the first cap.
    """
    _tex_layer(bm)
    before = set(bm.faces)
    rings = []
    for z, profile in stations:
        ring = [bm.verts.new(G(x, y, z)) for (x, y) in profile]
        rings.append(ring)
    n_st = len(rings)
    segs = len(rings[0])
    for i in range(n_st - 1):
        if len(rings[i]) != len(rings[i + 1]):
            # different vertex counts: skip-bridge not supported
            raise RuntimeError('profile size mismatch between stations')
        for k in range(segs):
            k2 = (k + 1) % segs
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    if cap:
        # rear cap
        bm.faces.new(rings[-1][:])
        # front cap, maybe with a hole
        if front_hole:
            z = stations[0][0]
            cx, cy = 0.0, Y_BORE
            inner = []
            segs_h = segs
            for i in range(segs_h):
                # match the outer profile's angular-ish order: start at bottom-rightish
                # Use even spacing on a circle, starting at the same winding.
                a = 2 * math.pi * i / segs_h - math.pi / 2  # start at -Y
                # Our profile starts at bottom-left, going CCW as viewed from +Z
                # (rear looking forward): that's CCW in XY when looking toward -Z?
                # We'll place inner verts in the same index order as the outer
                # profile by projecting each outer vert onto the circle.
                ox, oy = stations[0][1][i]
                dirxy = Vector((ox - cx, oy - cy))
                if dirxy.length < 1e-8:
                    dirxy = Vector((0, -1))
                dirxy.normalize()
                inner.append(bm.verts.new(G(cx + dirxy.x * front_hole, cy + dirxy.y * front_hole, z)))
            for i in range(segs):
                j = (i + 1) % segs
                bm.faces.new((rings[0][j], rings[0][i], inner[i], inner[j]))
            # close the hole with nothing (open); a disc behind is added by the barrel
        else:
            bm.faces.new(list(reversed(rings[0])))
    new_faces = [f for f in bm.faces if f not in before]
    _tag(bm, new_faces, tex)
    return new_faces, rings


def slide_profile(chamfer_top=CH_TOP, port=False, y_port=None):
    """8-point rounded-rect cross section of the slide, or a port cut."""
    hw = SLIDE_W * 0.5
    y0 = Y_SLIDE_BOT
    y1 = Y_SLIDE_TOP
    ct = chamfer_top
    cb = CH_BOT
    if not port:
        return [
            (-hw + cb, y0),
            (hw - cb, y0),
            (hw, y0 + cb),
            (hw, y1 - ct),
            (hw - ct, y1),
            (-hw + ct, y1),
            (-hw, y1 - ct),
            (-hw, y0 + cb),
        ]
    # Ejection port on the right (+X) and top-right. Left half of the top remains.
    yp = y_port if y_port is not None else Y_SLIDE_CY + 0.001
    x_port = 0.001  # left wall of the port, just right of the centreline
    return [
        (-hw + cb, y0),
        (hw - cb, y0),
        (hw, y0 + cb),
        (hw, yp),             # right side drops at the port floor
        (x_port, yp),         # port floor inner corner
        (x_port, y1),         # port left wall at the top
        (-hw + ct, y1),
        (-hw, y1 - ct),
        (-hw, y0 + cb),
    ]


def finalize_bm(bm):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00015)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    # Do not triangulate here actually — keep quads in the .blend for editing;
    # the exporter triangulates. Let me NOT triangulate in the blend.
    # Wait, I already would have triangulated. I'll skip triangulate and only
    # recalc normals + remove doubles.
    return bm


# Oops: I called triangulate in finalize then said skip. I'll write a correct one.
def clean_bm(bm, triangulate=False):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00015)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    # Make sure normals point outward: if median of volume is wrong, flip.
    try:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    except Exception:
        pass
    return bm


def bm_to_object(name, bm):
    clean_bm(bm, triangulate=False)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    # Keep the bmesh around for UV? We'll UV from the mesh / a new bmesh.
    return ob, bm


# ---- UV -------------------------------------------------------------------
def uv_rect(name):
    """Return (u0, v0, u1, v1) inset of a named swatch or region, in 0-1 UV."""
    s = float(TEX_SIZE)
    if name in SWATCH:
        tx, ty = SWATCH[name]
        x0, y0 = tx * TILE + PAD, ty * TILE + PAD
        x1, y1 = (tx + 1) * TILE - PAD, (ty + 1) * TILE - PAD
        return (x0 / s, y0 / s, x1 / s, y1 / s)
    if name in REGION:
        x0, y0, x1, y1 = REGION[name]
        return ((x0 + PAD) / s, (y0 + PAD) / s, (x1 - PAD) / s, (y1 - PAD) / s)
    # default mid steel
    return uv_rect('steel_mid')


def unwrap_object(ob, bm=None, default='steel_mid', part=None):
    """Project each face into its tex-layer swatch, or a special region.

    Serration: slide left/right faces near the rear.
    Wood: grip panels, projected in grip-space.
    Muzzle: front cap of the barrel/bushing.
    """
    me = ob.data
    if bm is None:
        bm = bmesh.new()
        bm.from_mesh(me)
    layer = bm.faces.layers.string.get('tex')
    uv_lay = bm.loops.layers.uv.new('UVMap') if not bm.loops.layers.uv else bm.loops.layers.uv[0]

    # Slide serration zone in game Z
    z_ser_0 = Z_SLIDE_REAR - 0.030
    z_ser_1 = Z_SLIDE_REAR

    for f in bm.faces:
        tag = default
        if layer is not None:
            raw = f[layer]
            if raw:
                tag = raw.decode() if isinstance(raw, (bytes, bytearray)) else str(raw)
        # Game-space face centre and normal
        verts_g = [game_of(l.vert.co) for l in f.loops]
        c = sum(verts_g, Vector((0, 0, 0))) / max(len(verts_g), 1)
        n_bl = f.normal
        n = Vector((n_bl.x, n_bl.z, -n_bl.y))  # game-space normal

        use = tag
        # Auto-promote slide side faces in the rear to the serration trim.
        if part == 'slide' and abs(n.x) > 0.7 and z_ser_0 <= c.z <= z_ser_1 and tag.startswith('steel'):
            use = 'serration'
        if part in ('barrel', 'bushing') and n.z < -0.7 and c.z < Z_SLIDE_FRONT + 0.01:
            use = 'muzzle'
        if part in ('grip_panel_L', 'grip_panel_R'):
            use = 'wood'

        u0, v0, u1, v1 = uv_rect(use)

        if use == 'serration':
            # U along game Z (fore-aft), V along game Y (up the slide).
            for loop, g in zip(f.loops, verts_g):
                uu = (g.z - z_ser_0) / max(z_ser_1 - z_ser_0, 1e-6)
                vv = (g.y - Y_SLIDE_BOT) / max(SLIDE_H, 1e-6)
                loop[uv_lay].uv = Vector((u0 + (u1 - u0) * _clamp(uu), v0 + (v1 - v0) * _clamp(vv)))
        elif use == 'wood':
            # U across the panel (along BACK), V along the grip (DOWN from top).
            for loop, g in zip(f.loops, verts_g):
                rel = g  # origin is the palm
                along = rel.dot(DOWN)          # 0 at origin, + toward mag
                across = rel.dot(BACK)
                uu = 0.5 + across / (GRIP_THICK * 0.9)
                vv = 0.5 + along / (GRIP_LEN_SPAN())
                loop[uv_lay].uv = Vector((u0 + (u1 - u0) * _clamp(uu), v0 + (v1 - v0) * _clamp(vv)))
        elif use == 'muzzle':
            # Planar X/Y around the bore, mapped to the disc.
            for loop, g in zip(f.loops, verts_g):
                uu = 0.5 + g.x / (BUSHING_R * 2.2)
                vv = 0.5 + (g.y - Y_BORE) / (BUSHING_R * 2.2)
                loop[uv_lay].uv = Vector((u0 + (u1 - u0) * _clamp(uu), v0 + (v1 - v0) * _clamp(vv)))
        else:
            # Solid swatch: a tiny stable projection so the face sits inside
            # the padded cell (no neighbour bleed with nearest filter).
            # Project onto the two largest axes of the face.
            ax = 0 if abs(n.x) < 0.9 else 1
            # Use XY, XZ or YZ depending on normal
            if abs(n.x) >= abs(n.y) and abs(n.x) >= abs(n.z):
                def uv_of(g):
                    return g.z, g.y
            elif abs(n.y) >= abs(n.z):
                def uv_of(g):
                    return g.x, g.z
            else:
                def uv_of(g):
                    return g.x, g.y
            pts = [uv_of(g) for g in verts_g]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)
            dx = max(maxx - minx, 1e-6)
            dy = max(maxy - miny, 1e-6)
            for loop, p in zip(f.loops, pts):
                uu = (p[0] - minx) / dx
                vv = (p[1] - miny) / dy
                # Keep a margin inside the swatch.
                loop[uv_lay].uv = Vector((u0 + (u1 - u0) * (0.15 + 0.7 * uu),
                                          v0 + (v1 - v0) * (0.15 + 0.7 * vv)))

    bm.to_mesh(me)
    me.update()


def _clamp(t, a=0.0, b=1.0):
    return a if t < a else b if t > b else t


def GRIP_LEN_SPAN():
    return GRIP_UP + GRIP_DOWN


# ---- build parts ----------------------------------------------------------
def build_slide():
    bm = bmesh.new()
    _tex_layer(bm)
    # Use 8-point profiles everywhere so rings match. For the port region,
    # we need a 9-point profile — so instead, keep 8-point and represent the
    # port as a later boolean-like cut: two extra stations with a modified
    # 8-point profile that drops the top-right into the port, PLUS a floor
    # face. To keep equal counts, use a 9-point profile on ALL stations
    # (the extra point sits on the top-right chamfer when there is no port).

    def prof(kind='solid'):
        hw = SLIDE_W * 0.5
        y0, y1 = Y_SLIDE_BOT, Y_SLIDE_TOP
        ct, cb = CH_TOP, CH_BOT
        yp = Y_SLIDE_CY + 0.0015
        x_port = 0.0015
        if kind == 'solid':
            # 9 points: same as 8, with the top-right corner split so it
            # matches the port profile's extra vertex.
            return [
                (-hw + cb, y0),       # 0
                (hw - cb, y0),        # 1
                (hw, y0 + cb),        # 2
                (hw, y1 - ct),        # 3
                (hw - ct, y1),        # 4
                (0.0, y1),            # 5 mid-top (becomes port wall)
                (-hw + ct, y1),       # 6
                (-hw, y1 - ct),       # 7
                (-hw, y0 + cb),       # 8
            ]
        # port: right side and right-top open down to yp
        return [
            (-hw + cb, y0),
            (hw - cb, y0),
            (hw, y0 + cb),
            (hw, yp),                 # 3 right at port floor
            (x_port, yp),             # 4 inner corner
            (x_port, y1),             # 5 port wall at top
            (-hw + ct, y1),
            (-hw, y1 - ct),
            (-hw, y0 + cb),
        ]

    zf, zr = Z_SLIDE_FRONT, Z_SLIDE_REAR
    # A slight nose taper: front 2 mm are 4% narrower? Skip, keep a clean block.
    stations = [
        (zf,             prof('solid')),
        (Z_PORT_FRONT,   prof('solid')),
        (Z_PORT_FRONT + 0.003, prof('port')),
        (Z_PORT_REAR - 0.003,  prof('port')),
        (Z_PORT_REAR,    prof('solid')),
        (zr,             prof('solid')),
    ]
    faces, rings = extrude_profiles(bm, stations, tex='steel_mid', cap=True, front_hole=BUSHING_R * 0.92)
    # Tag the port floor / interior as recess.
    layer = _tex_layer(bm)
    for f in bm.faces:
        c = game_of(f.calc_center_median())
        n = f.normal
        ng = Vector((n.x, n.z, -n.y))
        if Z_PORT_FRONT - 0.001 <= c.z <= Z_PORT_REAR + 0.001:
            if c.y < Y_SLIDE_CY + 0.006 and c.y > Y_SLIDE_CY - 0.004 and c.x > -0.002 and ng.y > 0.5:
                f[layer] = b'recess'   # port floor
            elif c.x > 0 and c.y > Y_SLIDE_CY and abs(ng.x) > 0.3:
                f[layer] = b'recess'
    # Rear face slightly darker, bottom faces dark (the seam on the frame).
    for f in bm.faces:
        n = f.normal
        ng = Vector((n.x, n.z, -n.y))
        c = game_of(f.calc_center_median())
        if ng.y < -0.8:
            f[layer] = b'steel_dark'
        if ng.z > 0.8 and c.z > zr - 0.002:
            f[layer] = b'steel_dark'
        if ng.y > 0.8 and c.y > Y_SLIDE_TOP - 0.002:
            f[layer] = b'sheen'
    return bm


def build_frame():
    bm = bmesh.new()
    _tex_layer(bm)
    # Dust cover + mid frame under the slide, from dust front to the front strap.
    # Then a rear block under the slide to the slide rear.
    y_bot = Y_FRAME_BOT
    y_top = Y_SLIDE_BOT + 0.0004  # tiny overlap so no gap
    # Dust cover is slimmer in height at the very front (a slight bevel): skip.
    z_front_strap = (GRIP_TOP - BACK * (GRIP_THICK * 0.5)).z
    add_box(bm,
            center=(0, (y_bot + y_top) * 0.5, (Z_DUST_FRONT + z_front_strap) * 0.5),
            size=(FRAME_W, y_top - y_bot, z_front_strap - Z_DUST_FRONT),
            tex='steel_dark', chamfer=0.0008)
    # Rear frame under the back of the slide (breech / rear tang).
    z_rear_frame = Z_SLIDE_REAR - 0.002
    add_box(bm,
            center=(0, (y_bot + y_top) * 0.5, (z_front_strap + z_rear_frame) * 0.5),
            size=(FRAME_W, y_top - y_bot, max(0.008, z_rear_frame - z_front_strap)),
            tex='steel_dark', chamfer=0.0006)
    # A slightly wider "rail" lip under the slide sides so the slide reads as
    # sitting on something. Skip to save tris — the width difference is enough.
    return bm


def build_grip():
    bm = bmesh.new()
    _tex_layer(bm)
    # Angled box for the steel grip frame, from just under the frame to the
    # mag-well lip, thickness along BACK, width along X.
    # Centre is the midpoint of GRIP_TOP and GRIP_BOT.
    mid = (GRIP_TOP + GRIP_BOT) * 0.5
    length = (GRIP_TOP - GRIP_BOT).length
    # Extend a hair into the frame so they meet cleanly.
    length_ext = length + 0.004
    mid_ext = mid + UP * 0.002
    add_box(bm,
            center=mid_ext,
            size=(GRIP_FRAME_W, length_ext, GRIP_THICK * 0.92),
            axes=(RIGHT, UP, BACK),
            tex='steel_dark', chamfer=0.0012)
    # Mainspring housing: a slightly proud backstrap slab, bottom two-thirds.
    hs_mid = GRIP_BOT + UP * (GRIP_DOWN * 0.45) + BACK * (GRIP_THICK * 0.48)
    add_box(bm,
            center=hs_mid,
            size=(GRIP_FRAME_W * 0.85, GRIP_DOWN * 0.85, 0.005),
            axes=(RIGHT, UP, BACK),
            tex='steel_mid', chamfer=0.0008)
    # Beavertail / grip safety: a short hook up and back from the top of the backstrap.
    tail_root = GRIP_TOP + BACK * (GRIP_THICK * 0.42)
    path = [
        tail_root + DOWN * 0.004,
        tail_root + BACK * 0.004 + UP * 0.006,
        tail_root + BACK * 0.010 + UP * 0.014,
        tail_root + BACK * 0.014 + UP * 0.020,   # hump
        tail_root + BACK * 0.012 + UP * 0.026,   # pad
        tail_root + BACK * 0.006 + UP * 0.028,   # tip, slight forward curl
    ]
    add_sweep(bm, path, width=GRIP_FRAME_W * 0.75, height=0.008, up=RIGHT, tex='steel_dark')
    # Mag-well flare: a thin collar at the bottom, slightly wider.
    flare_c = GRIP_BOT + DOWN * 0.002
    add_box(bm,
            center=flare_c,
            size=(GRIP_FRAME_W + 0.003, 0.006, GRIP_THICK * 0.96),
            axes=(RIGHT, UP, BACK),
            tex='steel_dark', chamfer=0.0008)
    return bm


def build_panel(side):
    """side = +1 (right, +X) or -1 (left)."""
    bm = bmesh.new()
    _tex_layer(bm)
    # Panels sit proud of the steel frame, inset from the front/back straps
    # and from the top/bottom of the grip.
    inset_u, inset_d, inset_fb = 0.008, 0.010, 0.007
    top = GRIP_TOP + DOWN * inset_u
    bot = GRIP_BOT + UP * inset_d
    mid = (top + bot) * 0.5
    length = (top - bot).length
    thick = GRIP_THICK - 2 * inset_fb
    # Centre is offset in X so the outer face is at GRIP_W/2.
    panel_t = 0.0032
    x = side * (GRIP_FRAME_W * 0.5 + panel_t * 0.5 - 0.0004)
    add_box(bm,
            center=(x, mid.y, mid.z),
            size=(panel_t, length, thick),
            axes=(RIGHT, UP, BACK),
            tex='wood', chamfer=0.0007)
    return bm


def build_trigger_guard():
    bm = bmesh.new()
    _tex_layer(bm)
    # Classic 1911 D-loop: nearly straight rear (the front strap), flat
    # bottom, and a half-round front. The frame underside is the roof, so
    # the path is open at the top.
    front_strap = GRIP_TOP - BACK * (GRIP_THICK * 0.5)
    y_top = Y_FRAME_BOT - 0.0035          # centreline just under the frame
    y_bot = Y_FRAME_BOT - 0.027
    z_rear = front_strap.z - 0.003
    z_front = front_strap.z - 0.044
    r_rear = 0.0045
    r_front = (y_top - y_bot) * 0.5

    def arc(cy, cz, r, a0, a1, n):
        pts = []
        for i in range(n):
            a = a0 + (a1 - a0) * (i / (n - 1))
            pts.append(Vector((0.0, cy + r * math.sin(a), cz + r * math.cos(a))))
        return pts

    path = []
    # Start slightly into the front strap so the loop buries into the grip.
    path.append(Vector((0.0, y_top + 0.003, z_rear + 0.003)))
    path.append(Vector((0.0, y_bot + r_rear, z_rear)))
    # Bottom-rear corner (from +Z around to -Y).
    path.extend(arc(y_bot + r_rear, z_rear - r_rear, r_rear, 0.0, -math.pi / 2, 5)[1:])
    # Underside, up to the front arc.
    z_front_c = z_front + r_front
    y_mid = (y_top + y_bot) * 0.5
    path.append(Vector((0.0, y_bot, z_front_c)))
    # Half-circle front: bottom (-pi/2) through the MUZZLE side (-pi) to the top
    # (-3pi/2). Going through 0 would bulge the "front" toward the rear and
    # fold over the trigger.
    path.extend(arc(y_mid, z_front_c, r_front, -math.pi / 2, -3 * math.pi / 2, 11)[1:])
    # Short run back under the dust cover, burying the end into the frame.
    path.append(Vector((0.0, y_top, z_front + r_front + 0.012)))
    add_sweep(bm, path, width=0.016, height=0.006, up=Vector((0, 1, 0)), tex='steel_dark')
    return bm

def build_trigger():
    bm = bmesh.new()
    _tex_layer(bm)
    # A simple curved shoe: a hanging blade and a short forward toe.
    # No swept hairpins — those folded in the first pass.
    front_strap = GRIP_TOP - BACK * (GRIP_THICK * 0.5)
    z = front_strap.z - 0.018
    y_top = Y_FRAME_BOT - 0.001
    # Blade, slightly lean the face by offsetting the bottom forward (-Z).
    add_box(bm,
            center=(0, y_top - 0.009, z - 0.001),
            size=(0.007, 0.016, 0.0055),
            tex='steel_mid', chamfer=0.0004)
    # Toe / shoe, a little lower and forward.
    add_box(bm,
            center=(0, y_top - 0.017, z - 0.005),
            size=(0.007, 0.006, 0.008),
            tex='steel_mid', chamfer=0.0005)
    return bm

def build_hammer():
    bm = bmesh.new()
    _tex_layer(bm)
    # Compact Government spur: a visible hook behind the slide, kept inside
    # the 0.216 m overall length (muzzle at Z_MUZZLE, rearmost ~Z_REAR).
    z_pivot = Z_SLIDE_REAR + 0.005
    y_pivot = Y_SLIDE_BOT + 0.007
    add_box(bm,
            center=(0, y_pivot + 0.002, z_pivot),
            size=(0.010, 0.015, 0.010),
            tex='steel_mid', chamfer=0.0010)
    # Spur goes up and back, but not past Z_REAR.
    tip_z = min(Z_REAR - 0.001, z_pivot + 0.012)
    path = [
        Vector((0, y_pivot + 0.007, z_pivot + 0.002)),
        Vector((0, y_pivot + 0.013, z_pivot + 0.007)),
        Vector((0, y_pivot + 0.017, tip_z)),
    ]
    add_sweep(bm, path, width=0.0075, height=0.0045, up=Vector((0, 0, 1)), tex='steel_light')
    # Striking face toward the slide.
    add_box(bm,
            center=(0, y_pivot + 0.006, z_pivot - 0.006),
            size=(0.009, 0.010, 0.0035),
            tex='steel_light', chamfer=0.0004)
    return bm

def build_barrel():
    bm = bmesh.new()
    _tex_layer(bm)
    # Visible barrel stub + bushing ring at the slide front. The rest of the
    # barrel is hidden in the slide; a hood sits in the ejection port.
    p_muzzle = Vector((0, Y_BORE, Z_MUZZLE))
    p_bush_f = Vector((0, Y_BORE, Z_SLIDE_FRONT - 0.0005))
    p_bush_r = Vector((0, Y_BORE, Z_SLIDE_FRONT + 0.008))
    # Bushing (fatter short ring), tube so the bore reads.
    add_cyl(bm, p_bush_f, p_bush_r, BUSHING_R, segs=8, tex='steel_mid', cap_ends=True, inner=BORE_R)
    # Barrel stub in front of the bushing, flush with the muzzle tip.
    add_cyl(bm, p_muzzle, p_bush_f, BARREL_R, segs=8, tex='steel_dark', cap_ends=True, inner=BORE_R)
    # Barrel hood in the ejection port (the raised hump you see in the port).
    hood_z = (Z_PORT_FRONT + Z_PORT_REAR) * 0.5 - 0.006
    add_box(bm,
            center=(0.001, Y_SLIDE_CY + 0.003, hood_z),
            size=(0.014, 0.008, 0.018),
            tex='steel_dark', chamfer=0.0006)
    return bm


def build_sight_front():
    bm = bmesh.new()
    _tex_layer(bm)
    # Plain blade, slightly tapered, on the slide near the muzzle.
    z = Z_SLIDE_FRONT + 0.010
    y0 = Y_SLIDE_TOP - 0.0002
    add_box(bm,
            center=(0, y0 + 0.0035, z),
            size=(0.0036, 0.007, 0.008),
            tex='steel_dark', chamfer=0.0003)
    return bm


def build_sight_rear():
    bm = bmesh.new()
    _tex_layer(bm)
    # Square notch block at the rear of the slide.
    z = Z_SLIDE_REAR - 0.006
    y0 = Y_SLIDE_TOP - 0.0002
    # Two posts with a gap (the notch). Cheaper: one block and a darker
    # inset — but a real notch reads better in silhouette.
    w_post = 0.004
    gap = 0.0032
    h = 0.0055
    d = 0.010
    for side in (-1, 1):
        x = side * (gap * 0.5 + w_post * 0.5)
        add_box(bm,
                center=(x, y0 + h * 0.5, z),
                size=(w_post, h, d),
                tex='steel_dark', chamfer=0.00025)
    # Base joining them
    add_box(bm,
            center=(0, y0 + 0.001, z),
            size=(gap + 2 * w_post, 0.002, d),
            tex='steel_dark')
    return bm


def build_controls():
    bm = bmesh.new()
    _tex_layer(bm)
    # All on the left side (-X): thumb safety at the rear, slide stop above
    # the trigger, mag release behind the trigger guard.
    x = -FRAME_W * 0.5 - 0.0015
    # Thumb safety
    z_saf = Z_SLIDE_REAR - 0.004
    y_saf = Y_FRAME_BOT + 0.004
    add_box(bm, center=(x, y_saf, z_saf), size=(0.0035, 0.008, 0.014), tex='steel_mid', chamfer=0.0004)
    # Slide stop lever
    z_ss = (Z_PORT_FRONT + Z_PORT_REAR) * 0.5
    y_ss = Y_FRAME_BOT + 0.002
    add_box(bm, center=(x, y_ss, z_ss), size=(0.003, 0.005, 0.022), tex='steel_mid', chamfer=0.0004)
    # Mag release button (left, just behind the trigger guard / front strap)
    front_strap = GRIP_TOP - BACK * (GRIP_THICK * 0.5)
    p = front_strap + DOWN * 0.010 + Vector((-GRIP_FRAME_W * 0.5 - 0.002, 0, 0))
    add_cyl(bm, p + Vector((-0.0005, 0, 0)), p + Vector((0.004, 0, 0)), 0.0032, segs=8, tex='steel_light', cap_ends=True)
    return bm


def build_magazine():
    bm = bmesh.new()
    _tex_layer(bm)
    # Single-stack .45 mag, angled with the grip. The body lives in the well;
    # the base plate sits a few millimetres below the mag-well lip.
    # We'll move the object origin to the mag-well lip later.
    top = GRIP_TOP + DOWN * 0.006          # just below the feed lips / inside the frame
    bot = GRIP_BOT + DOWN * 0.008          # base plate underside
    mid = (top + bot) * 0.5
    length = (top - bot).length
    mag_w = 0.014
    mag_d = 0.026
    add_box(bm,
            center=mid,
            size=(mag_w, length - 0.006, mag_d),
            axes=(RIGHT, UP, BACK),
            tex='steel_dark', chamfer=0.0006)
    # Base plate, slightly wider, at the bottom
    plate = GRIP_BOT + DOWN * 0.004
    add_box(bm,
            center=plate,
            size=(mag_w + 0.006, 0.007, mag_d + 0.006),
            axes=(RIGHT, UP, BACK),
            tex='steel_mid', chamfer=0.0008)
    # Tiny front lip on the base plate (1911 floorplate cue)
    lip = plate - BACK * ((mag_d + 0.006) * 0.5) + DOWN * 0.0005
    # "front" of the mag is toward the muzzle, which is -BACK? Front strap is -BACK.
    # The floorplate often has a little toe at the front (toward the muzzle).
    add_box(bm,
            center=plate - BACK * 0.0 + ( - BACK) * (mag_d * 0.45) + DOWN * 0.001,
            size=(mag_w * 0.8, 0.004, 0.006),
            axes=(RIGHT, UP, BACK),
            tex='steel_mid')
    return bm


# ---- object / scene -------------------------------------------------------
def new_empty(name, loc_game, parent=None):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = 'PLAIN_AXES'
    o.empty_display_size = 0.02
    o.location = G(loc_game)
    bpy.context.collection.objects.link(o)
    if parent is not None:
        o.parent = parent
    return o


def shade(ob, angle=40):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    except Exception:
        bpy.ops.object.shade_smooth()


def make_material(img_path):
    img = bpy.data.images.load(os.path.abspath(img_path))
    img.pack()
    img.colorspace_settings.name = 'sRGB'
    mat = bpy.data.materials.new('pistol_1911')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Closest'
    tex.location = (-300, 0)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    # PS2-style: essentially diffuse. A little specular, no metal, so the
    # wood and the steel share one material without the grips going chrome.
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = 0.0
    if 'Roughness' in bsdf.inputs:
        bsdf.inputs['Roughness'].default_value = 0.55
    spec_key = 'Specular IOR Level' if 'Specular IOR Level' in bsdf.inputs else 'Specular'
    if spec_key in bsdf.inputs:
        bsdf.inputs[spec_key].default_value = 0.35
    return mat, img


def assign_mat(ob, mat):
    if ob.data.materials:
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)


def set_origin_world(ob, world_co):
    """Keep mesh in place, move the object origin to a world-space point."""
    saved = bpy.context.scene.cursor.location.copy()
    bpy.context.scene.cursor.location = Vector(world_co)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.context.scene.cursor.location = saved


# ---- preview render -------------------------------------------------------
def setup_preview_scene():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.cycles.device = 'CPU'
    sc.render.resolution_x = 900
    sc.render.resolution_y = 700
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass

    # Dark warm backdrop, MGS3 briefing-room feel without stealing the silhouette.
    world = bpy.data.worlds.new('preview_world')
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.018, 0.016, 0.015, 1)
    bg.inputs[1].default_value = 1.0

    # Seamless ground a little below the mag.
    bpy.ops.mesh.primitive_plane_add(size=1.2, location=(0, 0, -0.09))
    ground = bpy.context.object
    ground.name = 'preview_ground'
    gmat = bpy.data.materials.new('preview_ground')
    gmat.use_nodes = True
    gbsdf = gmat.node_tree.nodes['Principled BSDF']
    gbsdf.inputs['Base Color'].default_value = (0.04, 0.036, 0.032, 1)
    gbsdf.inputs['Roughness'].default_value = 0.9
    if 'Metallic' in gbsdf.inputs:
        gbsdf.inputs['Metallic'].default_value = 0.0
    ground.data.materials.append(gmat)
    ground.hide_render = False

    def add_light(name, typ, loc, colour, energy, size=0.15, rot=None):
        data = bpy.data.lights.new(name, typ)
        data.color = colour
        data.energy = energy
        if typ == 'AREA':
            data.size = size
        elif typ == 'POINT':
            data.shadow_soft_size = size
        elif typ == 'SPOT':
            data.shadow_soft_size = size
        ob = bpy.data.objects.new(name, data)
        sc.collection.objects.link(ob)
        ob.location = loc
        if rot is not None:
            ob.rotation_euler = rot
        return ob

    # Lights in Blender space. Gun sits near the origin, muzzle toward +Y.
    def aim(ob, target=Vector((0, 0, 0.04))):
        ob.rotation_euler = (target - ob.location).to_track_quat('-Z', 'Y').to_euler()

    key = add_light('key', 'AREA', G(-0.16, 0.14, -0.20), (1.0, 0.95, 0.88), 16, size=0.18)
    fill = add_light('fill', 'AREA', G(0.22, 0.08, 0.06), (0.75, 0.82, 1.0), 5, size=0.28)
    rim = add_light('rim', 'AREA', G(0.04, 0.16, 0.24), (1.0, 0.85, 0.65), 8, size=0.14)
    aim(key); aim(fill); aim(rim)

    cam_data = bpy.data.cameras.new('preview_cam')
    cam_data.lens = 60
    cam_data.clip_start = 0.01
    cam_data.clip_end = 10
    cam = bpy.data.objects.new('preview_cam', cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam, ground


def mesh_bounds_game(mesh_objs):
    pts = []
    for ob in mesh_objs:
        for v in ob.data.vertices:
            pts.append(game_of(ob.matrix_world @ v.co))
    xs, ys, zs = zip(*[(p.x, p.y, p.z) for p in pts])
    mn = Vector((min(xs), min(ys), min(zs)))
    mx = Vector((max(xs), max(ys), max(zs)))
    return mn, mx, (mn + mx) * 0.5, mx - mn


def aim_camera(cam, target, location):
    cam.location = location
    direction = target - location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def render_previews(cam, mesh_objs, render_dir, prefix):
    mn, mx, center, size = mesh_bounds_game(mesh_objs)
    # Look at a point a little above the grip so the slide is in frame.
    look = G(center.x, center.y + 0.008, center.z)
    # 60 mm lens, generous padding so the muzzle and mag stay in frame.
    dist = 0.55

    views = {
        # Muzzle-on.
        'front': G(0.0, center.y + 0.01, mn.z - dist),
        # Left side (controls, classic silhouette).
        'side': G(mn.x - dist, center.y + 0.02, center.z),
        # Three-quarter from the right-front so the ejection port reads.
        'three': G(mx.x + dist * 0.70, center.y + 0.11, mn.z - dist * 0.58),
    }
    os.makedirs(render_dir, exist_ok=True)
    sc = bpy.context.scene
    paths = {}
    for name, loc in views.items():
        aim_camera(cam, look, loc)
        path = os.path.join(render_dir, f'{prefix}_{name}.png')
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths[name] = path
        print('rendered', path)
    return paths, (mn, mx, center, size)


# ---- main -----------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0


def build_all(out_dir, render_dir, name):
    reset_scene()
    os.makedirs(out_dir, exist_ok=True)
    tex_path = os.path.join(out_dir, name + '_albedo.png')
    paint_atlas(tex_path)
    mat, _img = make_material(tex_path)

    root = new_empty('pistol_1911', (0, 0, 0))

    parts = [
        ('slide', build_slide, 'slide'),
        ('frame', build_frame, 'frame'),
        ('grip', build_grip, 'grip'),
        ('grip_panel_L', lambda: build_panel(-1), 'grip_panel_L'),
        ('grip_panel_R', lambda: build_panel(+1), 'grip_panel_R'),
        ('trigger_guard', build_trigger_guard, 'trigger_guard'),
        ('trigger', build_trigger, 'trigger'),
        ('hammer', build_hammer, 'hammer'),
        ('barrel', build_barrel, 'barrel'),
        ('sight_front', build_sight_front, 'sight_front'),
        ('sight_rear', build_sight_rear, 'sight_rear'),
        ('controls', build_controls, 'controls'),
        ('magazine', build_magazine, 'magazine'),
    ]

    objects = []
    bms = {}
    for obj_name, fn, part_key in parts:
        bm = fn()
        ob, bm = bm_to_object(obj_name, bm)
        unwrap_object(ob, bm, part=part_key)
        bm.free()
        assign_mat(ob, mat)
        shade(ob, 35)
        objects.append(ob)

    # Parent body parts to the root. Magazine origin sits on the mag-well
    # empty so a reload can drop it along the grip.
    mag_well_g = Vector(GRIP_BOT)
    muzzle_g = Vector((0, Y_BORE, Z_MUZZLE))
    rear_sight_g = Vector((0, Y_SLIDE_TOP + 0.0055, Z_SLIDE_REAR - 0.006))
    mag_ob = next(o for o in objects if o.name == 'magazine')

    for ob in objects:
        if ob is mag_ob:
            continue
        mw = ob.matrix_world.copy()
        ob.parent = root
        ob.matrix_world = mw

    # Anchors. Identity rotation: after Y-up export, -Z is muzzle-forward.
    new_empty('muzzle', muzzle_g, parent=root)
    well = new_empty('mag_well', mag_well_g, parent=root)
    new_empty('rear_sight', rear_sight_g, parent=root)

    set_origin_world(mag_ob, G(mag_well_g))
    mw = mag_ob.matrix_world.copy()
    mag_ob.parent = well
    mag_ob.matrix_world = mw
    print('magazine loc', tuple(round(c, 4) for c in mag_ob.location),
          'world', tuple(round(c, 4) for c in mag_ob.matrix_world.translation))

    # Print a quick bounds check in game space.
    mesh_objs = [o for o in objects]
    mn, mx, center, size = mesh_bounds_game(mesh_objs)
    print('GAME BOUNDS min', tuple(round(c, 4) for c in mn),
          'max', tuple(round(c, 4) for c in mx),
          'size', tuple(round(c, 4) for c in size))
    print('length (Z) %.4f  (target %.4f)' % (size.z, LENGTH))
    print('muzzle z', round(Z_MUZZLE, 4), 'rear z', round(max(Z_REAR, mx.z), 4))
    print('origin at grip (0,0,0); mag_well', tuple(round(c, 4) for c in mag_well_g))

    blend_path = os.path.abspath(os.path.join(out_dir, name + '.blend'))
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print('saved', blend_path)

    if render_dir:
        cam, ground = setup_preview_scene()
        # Don't include the ground in bounds.
        paths, bounds = render_previews(cam, mesh_objs, render_dir, name)
        # Re-save after the preview objects exist? Better not pollute the asset
        # blend. Remove preview extras and save again, leaving the clean file.
        for extra in (cam, ground):
            bpy.data.objects.remove(extra, do_unlink=True)
        for ob in list(bpy.data.objects):
            if ob.name.startswith('key') or ob.name.startswith('fill') or ob.name.startswith('rim') or ob.name.startswith('preview'):
                bpy.data.objects.remove(ob, do_unlink=True)
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        return blend_path, tex_path, paths, (mn, mx, size)
    return blend_path, tex_path, {}, (mn, mx, size)


def main():
    args = _parse()
    # Resolve paths relative to the current working directory (the repo root
    # when called the usual way).
    out_dir = os.path.abspath(args.out_dir)
    render_dir = os.path.abspath(args.render_dir) if args.render_dir else ''
    build_all(out_dir, render_dir, args.name)
    print('BUILD DONE')


if __name__ == '__main__':
    main()
