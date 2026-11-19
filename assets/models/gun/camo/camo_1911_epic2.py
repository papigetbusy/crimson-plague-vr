"""EPIC v2 parts: angular demon-skull compensator, one continuous forged dorsal ridge, flowing barbed dust-cover shroud
(keel + two flared wings), swept spur beavertail. Faceted by construction (convex hulls + exact booleans)."""
import math
import bpy, bmesh
from mathutils import Vector

SB = None
def init(sb):
    global SB
    SB = sb

def _G(x, y, z): return SB.M.G(x, y, z)

def hull_bm(pts, tex, bm=None):
    """convex hull of game-space points -> faceted solid (interior verts removed)"""
    own = bm is None
    if own:
        bm = bmesh.new(); SB.M._tex_layer(bm)
    before = set(bm.faces)
    vs = [bm.verts.new(_G(*p)) for p in pts]
    res = bmesh.ops.convex_hull(bm, input=vs)
    dead = [g for g in res.get('geom_interior', []) if isinstance(g, bmesh.types.BMVert)]
    if dead: bmesh.ops.delete(bm, geom=dead, context='VERTS')
    new = [f for f in bm.faces if f not in before]
    bmesh.ops.recalc_face_normals(bm, faces=new)
    SB.S._tag_faces(bm, new, tex)
    return bm

def _obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

def _sym(rows, s=None):
    """rows of (|x|, dy, z) -> mirrored points around the bore centre"""
    YB = SB.YB; out = []
    for x, dy, z in rows:
        out.append((x, YB + dy, z))
        if x: out.append((-x, YB + dy, z))
    return out

def demon_brake():
    """returns (skull_bm, trim_bm(steel_hi: fangs, horns, tusks, crest), eyes_bm(violet), tip_z)"""
    YB = SB.YB; S = SB.S
    def H(rows, tex='bk_steel'): return _obj('h', hull_bm(_sym(rows), tex))
    cr = H([(.0100, .0092, -.1775), (.0104, -.0008, -.1775), (.0070, -.0086, -.1775), (0, .0100, -.1775), (0, -.0092, -.1775),
            (.0108, .0102, -.1900), (.0113, .0015, -.1900), (.0078, -.0076, -.1900), (0, .0118, -.1900), (0, -.0082, -.1900),
            (.0090, .0085, -.2060), (.0092, -.0005, -.2060), (.0064, -.0060, -.2060), (0, .0095, -.2060), (0, -.0064, -.2060)])
    sn = H([(.0086, .0075, -.2040), (.0086, -.0030, -.2040), (.0060, -.0058, -.2040), (0, .0092, -.2040), (0, -.0062, -.2040),
            (.0054, .0054, -.2330), (.0056, -.0030, -.2330), (.0038, -.0056, -.2330), (0, .0062, -.2330), (0, -.0058, -.2330)])
    jaw = H([(.0068, -.0080, -.1900), (.0070, -.0130, -.1900), (0, -.0138, -.1900), (0, -.0082, -.1900),
             (.0066, -.0095, -.1980), (.0068, -.0135, -.1980), (0, -.0148, -.1980), (0, -.0100, -.1980),
             (.0030, -.0092, -.2300), (.0032, -.0115, -.2300), (0, -.0120, -.2300), (0, -.0094, -.2300)])
    brows = []
    for s in (-1, 1):
        pts = [(s * .0122, YB + .0138, -.1905), (s * .0122, YB + .0056, -.1975), (s * .0014, YB + .0135, -.2075), (s * .0014, YB + .0052, -.2112), (s * .0100, YB + .0142, -.1990)]
        brows.append(_obj('br', hull_bm(pts, 'bk_steel')))
    for o in [sn, jaw] + brows:
        SB._bool(cr, o, 'UNION')
    for s in (-1, 1):   # eye sockets carved under the brow
        pk = [(s * .0150, YB + .0054, -.1950), (s * .0150, YB - .0002, -.1950), (s * .0030, YB + .0052, -.2000), (s * .0030, YB - .0004, -.2000),
              (s * .0150, YB + .0054, -.2170), (s * .0150, YB - .0002, -.2170), (s * .0030, YB + .0052, -.2170), (s * .0030, YB - .0004, -.2170)]
        SB._bool(cr, _obj('sock', hull_bm(pk, 'bk_steel')), 'DIFFERENCE')
    SB._bool(cr, SB._cyl('bore', (0, YB, -.2150), 0.0034, 0.1000, 20), 'DIFFERENCE')   # bore through everything
    for zc in (-.2125, -.2205, -.2285):                                                 # real vent ports, cut across the snout through the bore
        bx = [(sx * .0200, YB + dy, zc + dz) for sx in (-1, 1) for dy in (-.0030, .0046) for dz in (-.0013, .0013)]
        SB._bool(cr, _obj('vent', hull_bm(bx, 'bk_steel')), 'DIFFERENCE')
    bm = bmesh.new(); bm.from_mesh(cr.data); bpy.data.objects.remove(cr, do_unlink=True)
    SB.M._tex_layer(bm)
    for f in bm.faces: f[bm.faces.layers.string.get('tex')] = b'bk_steel'
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    # a short steel collar so the brake joins the barrel/slide front
    S.lathe_z(bm, [(-.1800, .0078), (-.1750, .0080), (-.1700, .0080)], 0.0, YB, segs=8, tex='bk_steel', inner=0.0032)
    trim = bmesh.new(); SB.M._tex_layer(trim)
    for s in (-1, 1):
        S.tube_path(trim, [(s * .0048, YB - .0050, -.2075), (s * .0049, YB - .0095, -.2097), (s * .0050, YB - .0140, -.2132)], [.0019, .0012, .00008], [.0019, .0012, .00008], segs=4, tex='steel_hi', up=(0, 0, 1), phase=math.pi / 4)
        for zz in (-.2235, -.2350):
            S.tube_path(trim, [(s * .0038, YB - .0050, zz), (s * .0039, YB - .0082, zz - .0012), (s * .0040, YB - .0108, zz - .0034)], [.0013, .0008, .00007], [.0013, .0008, .00007], segs=4, tex='steel_hi', up=(0, 0, 1), phase=math.pi / 4)
        S.tube_path(trim, [(s * .0060, YB - .0105, -.2200), (s * .0064, YB - .0045, -.2290), (s * .0058, YB + .0015, -.2345)], [.0014, .0010, .00007], [.0014, .0010, .00007], segs=4, tex='steel_hi', up=(1, 0, 0), phase=math.pi / 4)
        S.tube_path(trim, [(s * .0098, YB + .0085, -.1925), (s * .0128, YB + .0112, -.1850), (s * .0152, YB + .0130, -.1785)], [.0017, .0011, .00008], [.0014, .0009, .00008], segs=5, tex='steel_hi', up=(0, 1, 0), phase=math.pi / 5)
    eyes = bmesh.new(); SB.M._tex_layer(eyes)
    for s in (-1, 1):
        c = (s * .0070, YB + .0026, -.2010)
        pts = [(c[0] + dx, c[1] + dy, c[2] + dz) for dx, dy, dz in ((.0022, 0, 0), (-.0022, 0, 0), (0, .0021, 0), (0, -.0021, 0), (0, 0, .0017), (0, 0, -.0017))]
        hull_bm(pts, 'violet', eyes)
    return bm, trim, eyes, -.2332

def _barbed_plate(z0, z1, y_top, y_bot0, y_bot1, depth, n, th, tex, bm):
    """flat forged plate in the z-y plane with a forward-raked barbed lower edge, one polygon"""
    S = SB.S
    pitch = (z0 - z1) / n
    poly = [(z0, y_top)]
    poly.append((z0 - .004, y_bot0))
    for i in range(n):
        za = z0 - .004 - pitch * i
        ya = y_bot0 + (y_bot1 - y_bot0) * (za - z0) / (z1 - z0)
        poly.append((za, ya))                                   # notch
        poly.append((za - pitch * 0.92, ya - depth))             # barb tip (raked forward & down)
        poly.append((za - pitch * 0.62, ya - depth * 0.12))      # curved back up
    poly.append((z1, y_bot1 + .0010))
    poly.append((z1, y_top))
    return S.extrude_zy(bm, poly, -th, th, tex=tex, bevel=.0005, segs=1)

def barbed_shroud():
    S = SB.S
    keel = bmesh.new(); SB.M._tex_layer(keel)
    _barbed_plate(-.040, -.2300, .0450, .0342, .0290, .0105, 7, .0036, 'bk_steel', keel)
    wings = bmesh.new(); SB.M._tex_layer(wings)
    for s in (-1, 1):
        before = set(wings.verts)
        _barbed_plate(-.085, -.1960, .0472, .0334, .0300, .0075, 5, .0014, 'bk_steel', wings)
        vs = [v for v in wings.verts if v not in before]
        px, py = 0.0, .0472                                           # flare outward ~24 deg about the slide underside
        ang = math.radians(24.0) * s
        for v in vs:
            g = SB.M.game_of(v.co); x = g[0] + s * .0100 - px; y = g[1] - py
            xr = x * math.cos(ang) - y * math.sin(ang); yr = x * math.sin(ang) + y * math.cos(ang)
            v.co = _G(px + xr, py + yr, g[2])
    strips = bmesh.new(); SB.M._tex_layer(strips)
    for s in (-1, 1):
        S.tube_path(strips, [(s * .0041, .0392, -.0950), (s * .0041, .0372, -.1350), (s * .0041, .0372, -.2050)], .0005, .0007, segs=4, tex='violet', up=(0, 1, 0))
    return keel, wings, strips

def forged_ridge():
    """ONE continuous ridge: broad bevelled forged base rail + a raked-tooth dorsal blade, all clear of the sights"""
    S = SB.S; YT = SB.YT
    base = bmesh.new(); SB.M._tex_layer(base)
    S.box(base, (0, YT + .0004, -.0850), (.0084, .0014, .1330), bevel=.0005, segs=1, tex='bk_steel')
    blade = bmesh.new(); SB.M._tex_layer(blade)
    n = 10; zr, zf = -.0185, -.1500; pitch = (zr - zf) / n
    poly = [(zr, YT), (zr - .0010, YT + .0017)]
    for i in range(n):
        za = zr - .0010 - pitch * i
        poly.append((za, YT + .0014))
        poly.append((za - pitch * 0.94, YT + .0036 + .0002 * (i % 2)))
    poly.append((zf - .0010, YT + .0014)); poly.append((zf, YT))
    # remove consecutive duplicates
    P = [poly[0]]
    for p in poly[1:]:
        if abs(p[0] - P[-1][0]) + abs(p[1] - P[-1][1]) > 1e-6: P.append(p)
    S.extrude_zy(blade, P, -.0011, .0011, tex='steel_hi', bevel=.00035, segs=1)
    cord = bmesh.new(); SB.M._tex_layer(cord)
    for s in (-1, 1):
        S.tube_path(cord, [(s * .0036, YT + .0013, -.0220), (s * .0036, YT + .0013, -.1470)], .0004, .0003, segs=4, tex='violet', up=(0, 1, 0))
    return base, blade, cord

def spur():
    S = SB.S
    bm = bmesh.new(); SB.M._tex_layer(bm)
    pts = [(0, .0383, .0095), (0, .0395, .0200), (0, .0420, .0320), (0, .0470, .0430), (0, .0540, .0515), (0, .0625, .0565)]
    S.tube_path(bm, pts, [.0112, .0112, .0102, .0078, .0042, .00012], [.0034, .0036, .0034, .0028, .0018, .0001], segs=8, tex='bk_steel', up=(0, 1, 0), phase=math.pi / 8)
    return bm

def add_epic(add_new, objs):
    sk, trim, eyes, tip = demon_brake()
    add_new('demon_brake', sk, 'frame'); add_new('demon_trim', trim, 'frame'); add_new('demon_eyes', eyes, 'frame')
    keel, wings, strips = barbed_shroud()
    add_new('shroud_keel', keel, 'frame'); add_new('shroud_wings', wings, 'frame'); add_new('shroud_strips', strips, 'frame')
    base, blade, cord = forged_ridge()
    add_new('ridge_base', base, 'slide'); add_new('ridge_blade', blade, 'slide'); add_new('ridge_cord', cord, 'slide')
    add_new('spur', spur(), 'frame')
    return tip
