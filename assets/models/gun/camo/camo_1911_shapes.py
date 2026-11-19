"""Smooth, beveled shape primitives (bmesh) for the EPIC / LEGENDARY 1911 camo tiers.
All coordinates are GAME space (x right, y up, z forward = negative toward the muzzle); M.G() converts to Blender.
Every face is tagged with an atlas cell name in the 'tex' string layer (same layer the tool mesh module uses)."""
import math
import bmesh
from mathutils import Vector

M = None
def init(mod):
    global M
    M = mod

def V(x, y, z): return M.G(x, y, z)

def _layer(bm): return M._tex_layer(bm)

def _tag_new(bm, before, tex):
    layer = _layer(bm)
    for f in bm.faces:
        if f not in before:
            f[layer] = tex.encode()

def _tag_faces(bm, faces, tex):
    layer = _layer(bm)
    for f in faces:
        if f.is_valid:
            f[layer] = tex.encode()

def _val(a, t, i):
    if callable(a): return a(t)
    if isinstance(a, (list, tuple)): return a[i]
    return a

def tube_path(bm, pts, rx, ry, segs=6, tex='bk_steel', up=(0, 1, 0), caps=(True, True), phase=0.0):
    """Sweep an ellipse (half-width rx along B, half-height ry along N) down a polyline of game-space points."""
    _layer(bm)
    before = set(bm.faces)
    P = [Vector(p) for p in pts]
    n = len(P)
    rings = []
    upv = Vector(up)
    for i, p in enumerate(P):
        a = P[max(i - 1, 0)]; b = P[min(i + 1, n - 1)]
        T = (b - a).normalized()
        N = upv - T * upv.dot(T)
        if N.length < 1e-5:
            N = Vector((1, 0, 0)) - T * T.x
        N.normalize(); B = T.cross(N)
        t = i / max(n - 1, 1)
        x = _val(rx, t, i); y = _val(ry, t, i)
        ring = []
        for k in range(segs):
            ang = 2 * math.pi * k / segs + phase
            q = p + B * (math.cos(ang) * x) + N * (math.sin(ang) * y)
            ring.append(bm.verts.new(V(q.x, q.y, q.z)))
        rings.append(ring)
    for A, Bq in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((A[k], A[(k + 1) % segs], Bq[(k + 1) % segs], Bq[k]))
    if caps[0]: bm.faces.new(list(reversed(rings[0])))
    if caps[1]: bm.faces.new(rings[-1])
    new = [f for f in bm.faces if f not in before]
    bmesh.ops.recalc_face_normals(bm, faces=new)
    _tag_faces(bm, new, tex)
    return new

def lathe_z(bm, stations, cx, cy, segs=12, tex='bk_steel', inner=0.0, tex_inner=None, phase=0.0):
    """Surface of revolution about a z-parallel axis through (cx, cy). stations: (z, r) or (z, rx, ry, dy) front->back."""
    _layer(bm)
    before = set(bm.faces)
    rings = []
    for st in stations:
        if len(st) == 2: z, rx = st; ry = rx; dy = 0.0
        else: z, rx, ry, dy = st
        rings.append([bm.verts.new(V(cx + rx * math.cos(2 * math.pi * k / segs + phase), cy + dy + ry * math.sin(2 * math.pi * k / segs + phase), z)) for k in range(segs)])
    for A, B in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((A[k], A[(k + 1) % segs], B[(k + 1) % segs], B[k]))
    if inner > 0:
        z0, z1 = stations[0][0], stations[-1][0]
        i0 = [bm.verts.new(V(cx + inner * math.cos(2 * math.pi * k / segs + phase), cy + inner * math.sin(2 * math.pi * k / segs + phase), z0)) for k in range(segs)]
        i1 = [bm.verts.new(V(cx + inner * math.cos(2 * math.pi * k / segs + phase), cy + inner * math.sin(2 * math.pi * k / segs + phase), z1)) for k in range(segs)]
        for k in range(segs):
            k2 = (k + 1) % segs
            bm.faces.new((rings[0][k2], rings[0][k], i0[k], i0[k2]))
            bm.faces.new((rings[-1][k], rings[-1][k2], i1[k2], i1[k]))
            bm.faces.new((i0[k], i0[k2], i1[k2], i1[k]))
    else:
        bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    new = [f for f in bm.faces if f not in before]
    bmesh.ops.recalc_face_normals(bm, faces=new)
    _tag_faces(bm, new, tex)
    return new

def box(bm, c, size, bevel=0.0006, segs=1, tex='bk_steel'):
    _layer(bm)
    before = set(bm.faces)
    geo = bmesh.ops.create_cube(bm, size=1.0)
    for v in geo['verts']:
        v.co = V(c[0] + v.co.x * size[0], c[1] + v.co.y * size[1], c[2] + v.co.z * size[2])
    if bevel > 0:
        vs = set(geo['verts'])
        es = [e for e in bm.edges if e.verts[0] in vs and e.verts[1] in vs]
        bmesh.ops.bevel(bm, geom=es, offset=bevel, segments=segs, profile=0.6, affect='EDGES')
    new = [f for f in bm.faces if f not in before]
    _tag_faces(bm, new, tex)
    return new

def extrude_zy(bm, poly, x0, x1, tex='bk_steel', bevel=0.0007, segs=2, holes=()):
    """Extrude a (z, y) polygon across X (x0..x1) with filled caps (and holes), then round every cap rim with a bevel."""
    _layer(bm)
    before = set(bm.faces)
    loops = [poly] + list(holes)
    Ls = [[bm.verts.new(V(x0, y, z)) for z, y in lp] for lp in loops]
    Rs = [[bm.verts.new(V(x1, y, z)) for z, y in lp] for lp in loops]
    rim = []
    for L, R in zip(Ls, Rs):
        k = len(L)
        for i in range(k):
            bm.faces.new((L[i], L[(i + 1) % k], R[(i + 1) % k], R[i]))
    for X in (Ls, Rs):
        edges = []
        for r in X:
            for i in range(len(r)):
                e = bm.edges.get((r[i], r[(i + 1) % len(r)]))
                edges.append(e); rim.append(e)
        bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    new = [f for f in bm.faces if f not in before]
    bmesh.ops.recalc_face_normals(bm, faces=new)
    if bevel:
        bmesh.ops.bevel(bm, geom=rim, offset=bevel, segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
    new = [f for f in bm.faces if f not in before]
    _tag_faces(bm, new, tex)
    return new

def bevel_all(bm, faces_or_none=None, offset=0.0012, segs=2, angle_deg=22.0, profile=0.5, min_len=0.0):
    """Round every edge sharper than angle_deg (within the given faces, or the whole bmesh)."""
    faces = faces_or_none if faces_or_none is not None else list(bm.faces)
    es = set()
    ca = math.cos(math.radians(angle_deg))
    for f in faces:
        for e in f.edges:
            if len(e.link_faces) == 2:
                if e.link_faces[0].normal.dot(e.link_faces[1].normal) < ca and e.calc_length() >= min_len:
                    es.add(e)
    layer = _layer(bm)
    r = bmesh.ops.bevel(bm, geom=list(es), offset=offset, segments=segs, profile=profile, affect='EDGES', clamp_overlap=True)
    return r

def lancet_pts(cx, y_base, y_spring, y_apex, half, n=14):
    """(z,y)-style pointed arch outline (x -> first coord, y second) from left base up the arch and down the right jamb."""
    Hh = y_spring - y_apex
    r = (Hh * Hh + half * half) / (2 * half)
    ccx = cx - half + r
    d = math.atan2(-Hh, half - r)
    left = [(ccx + r * math.cos(t), y_spring + r * math.sin(t)) for t in [(-math.pi) + (d + math.pi) * i / (n - 1) for i in range(n)]]
    right = [(2 * cx - x, y) for x, y in left[::-1]]
    return [(cx - half, y_base)] + left + right[1:] + [(cx + half, y_base)]

def lancet_up(cx, y_base, y_spring, y_apex, half, n=14):
    """same as lancet_pts but for y-UP coordinates (apex above the spring line)."""
    return [(c, -a) for c, a in lancet_pts(cx, -y_base, -y_spring, -y_apex, half, n)]
