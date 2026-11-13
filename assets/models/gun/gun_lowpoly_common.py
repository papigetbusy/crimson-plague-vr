"""Shared helpers for the PS2 / Snake Eater low-poly long guns and SMGs.

Used by build_ak47_base.py, build_m4_base.py, build_mp5_base.py and
build_uzi_base.py. Follows docs/lowpoly-pipeline.md and the locked look of
pistol_1911_base: dark blued steel (metallic 1, roughness 0.30) with painted
highlights, plus one non-metal furniture material (wood or polymer) that
shares the same 256 px nearest-filtered atlas.

Surface wear follows the owner's PS2 gun reference set (exterior wear only,
no designs copied): scuffed lighter edges, mottled grime on the steel,
weathered reddish-brown wood with grain and rubbed edges.

Game space: +Y up, muzzle toward -Z, +X right, metres, origin at the palm.
Blender is Z up; G() converts (x, y, z)_game -> (x, -z, y)_blender.
"""
import importlib.util, math, os, sys
import bpy, bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
_spec = importlib.util.spec_from_file_location(
    'p1911', os.path.join(REPO, 'tools', 'blender', 'build_pistol_1911.py'))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
G = M.G

S = 256
PAD = 2
STEEL = {
    'recess':      (7, 8, 11),
    'steel_black': (11, 12, 18),
    'steel_dark':  (19, 22, 32),
    'steel_mid':   (30, 35, 49),
    'steel_light': (50, 57, 76),
    'sheen':       (86, 98, 122),
    'steel_edge':  (148, 154, 164),
    'grime':       (40, 36, 31),
    'silver':      (168, 172, 178),
}
WOOD = {   # weathered reddish-brown
    'f_shadow': (36, 18, 12), 'f_dark': (56, 27, 17), 'f_mid': (84, 41, 26),
    'f_light': (108, 58, 36), 'f_high': (146, 100, 70), 'f_grime': (52, 40, 32),
}
POLYMER = {  # worn black polymer
    'f_shadow': (10, 10, 11), 'f_dark': (17, 17, 19), 'f_mid': (29, 29, 32),
    'f_light': (44, 44, 48), 'f_high': (82, 82, 86), 'f_grime': (48, 44, 38),
}
# Atlas regions (x0, y0, x1, y1) in UV pixel space, y up.
REGION = {
    'steel':     (0, 0, 128, 64),     # worn receiver panel
    'steel_top': (128, 0, 192, 64),   # lighter top flats, polish streak
    'muzzle':    (192, 0, 256, 64),
    'furn':      (0, 64, 128, 128),   # wood grain / polymer stipple
    'furn_end':  (128, 64, 192, 128), # end grain / darker edges
    'ribs':      (192, 64, 256, 128), # steel grooves (mag ribs, cover ribs)
    'barrel':    (0, 128, 128, 192),  # long steel, wraps cylinders
    'grip':      (128, 128, 192, 192),# checkered / stippled grip
    'silver':    (192, 128, 224, 160),
    'recess':    (224, 128, 256, 160),
    'vents':     (192, 160, 256, 192),# furniture with dark vent slots
    'mag':       (0, 192, 128, 256),  # magazine steel with painted ribs
    'furn_dark': (128, 192, 192, 256),
    'rail':      (192, 192, 256, 256),# steel with cross slots
}
FURN_REGIONS = {'furn', 'furn_end', 'grip', 'vents', 'furn_dark'}


# ---- texture ---------------------------------------------------------------
def _h(x, y, s=0):
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    return (n ^ (n >> 16)) / 4294967296.0


def _vn(x, y, sc, s=0):
    fx, fy = x / sc, y / sc
    ix, iy = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a, b = _h(ix, iy, s), _h(ix + 1, iy, s)
    c, d = _h(ix, iy + 1, s), _h(ix + 1, iy + 1, s)
    return (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty


def paint_atlas(path, furn='wood', seed=1):
    pal = dict(STEEL); pal.update(WOOD if furn == 'wood' else POLYMER)
    buf = [pal['recess']] * (S * S)

    def put(x, y, c):
        if 0 <= x < S and 0 <= y < S:
            buf[y * S + x] = pal[c]

    def edge_d(x, y, r):
        x0, y0, x1, y1 = r
        return min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y) - PAD

    def steel_region(r, ramp, grime=0.69, ribs=0, slots=0, wrap=False):
        x0, y0, x1, y1 = r
        h = y1 - y0
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
                if ribs and (x - x0) % ribs in (0, 1):
                    c = 'recess'
                elif ribs and (x - x0) % ribs == 2:
                    c = 'steel_light'
                if slots and (y - y0) % slots in (0, 1, 2) and x0 + 8 < x < x1 - 8:
                    c = 'recess'
                hv = _h(x, y, seed + 7)
                if hv > 0.996:
                    c = 'steel_edge'        # scuff
                elif hv > 0.988:
                    c = 'sheen'
                d = edge_d(x, y, r)
                if not wrap and 0 <= d <= 1 and _vn(x, y, 2.5, seed + 3) > 0.42:
                    c = 'steel_edge' if d == 0 else 'sheen'   # worn edge
                if wrap and (y - y0) % 16 in (13,) and _h(x, 0, 5) > 0.5:
                    c = 'sheen'
                put(x, y, c)

    def furn_region(r, kind, dark=False, vents=0, checker=False):
        x0, y0, x1, y1 = r
        for y in range(y0, y1):
            for x in range(x0, x1):
                if furn == 'wood':
                    g = math.sin(y * 0.55 + 4.0 * _vn(x, y, 14, seed + 2) + 0.03 * x)
                    c = 'f_dark' if g > 0.72 else 'f_light' if g < -0.80 else 'f_mid'
                    if kind == 'end':
                        rr = math.hypot(x - (x0 + x1) / 2, y - (y0 + y1) / 2)
                        c = 'f_dark' if int(rr) % 6 < 2 else 'f_mid'
                else:
                    hv = _h(x, y, seed + 4)
                    c = 'f_dark' if hv < 0.25 else 'f_light' if hv > 0.88 else 'f_mid'
                if dark and c == 'f_mid':
                    c = 'f_dark'
                if checker and ((x + y) % 6 == 0 or (x - y) % 6 == 0):
                    c = 'f_shadow'
                if _vn(x, y, 8, seed + 5) > 0.76:
                    c = 'f_grime'
                if vents and x0 + 8 < x < x1 - 8 and (y - y0) % vents in range(3, 9) \
                        and (x - x0) % 16 < 10:
                    c = 'f_shadow'
                d = edge_d(x, y, r)
                if 0 <= d <= 2 and _vn(x, y, 3, seed + 6) > (0.35 + 0.1 * d):
                    c = 'f_high'                                   # rubbed edge
                put(x, y, c)

    ramp = ('steel_dark', 'steel_mid', 'steel_light', 'sheen')
    steel_region(REGION['steel'], ramp)
    steel_region(REGION['steel_top'], ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), grime=0.70)
    steel_region(REGION['barrel'], ('steel_black', 'steel_dark', 'steel_mid', 'sheen'), grime=0.68, wrap=True)
    steel_region(REGION['ribs'], ramp, ribs=6)
    steel_region(REGION['mag'], ('steel_black', 'steel_dark', 'steel_mid', 'steel_light'), ribs=0)
    x0, y0, x1, y1 = REGION['mag']              # two painted stiffening ribs
    for x in range(x0 + 6, x1 - 6):
        for yy, c in ((y0 + 20, 'recess'), (y0 + 21, 'sheen'), (y0 + 42, 'recess'), (y0 + 43, 'sheen')):
            put(x, yy, c)
    steel_region(REGION['rail'], ramp, slots=8)
    furn_region(REGION['furn'], 'side')
    furn_region(REGION['furn_end'], 'end')
    furn_region(REGION['grip'], 'side', checker=True)
    furn_region(REGION['vents'], 'side', vents=12)
    furn_region(REGION['furn_dark'], 'side', dark=True)
    for name, base, hi in (('silver', 'silver', 'steel_edge'), ('recess', 'recess', 'steel_black')):
        x0, y0, x1, y1 = REGION[name]
        for y in range(y0, y1):
            for x in range(x0, x1):
                put(x, y, hi if _h(x, y, 9) > 0.8 else base)
    # Muzzle crown: steel ring, worn rim, black bore.
    x0, y0, x1, y1 = REGION['muzzle']
    cx, cy = (x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2
    for y in range(y0, y1):
        for x in range(x0, x1):
            r = math.hypot(x - cx, y - cy)
            c = 'steel_dark' if r > 28 else 'steel_edge' if r > 25 else 'steel_mid' if r > 15 else 'steel_light' if r > 13 else 'recess'
            put(x, y, c)
    used = set(buf)
    assert len(used) <= 16, f'palette has {len(used)} colours'
    M._write_png(path, S, S, bytes(v for c in buf for v in c), bottom_up=True)
    print('atlas colours', len(used))
    return path


# ---- mesh builder ----------------------------------------------------------
class Part:
    """One mesh object. Faces get UVs at creation; material 0 steel, 1 furniture."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')

    # map a face's verts (game space) into a region by planar bbox projection
    def _uv_face(self, f, region, pts2d=None, margin=0.0):
        x0, y0, x1, y1 = REGION[region]
        u0, v0, u1, v1 = (x0 + PAD) / S, (y0 + PAD) / S, (x1 - PAD) / S, (y1 - PAD) / S
        if pts2d is None:
            gs = [M.game_of(l.vert.co) for l in f.loops]
            n = f.normal; n = Vector((abs(n.x), abs(n.z), abs(n.y)))
            if n.x >= n.y and n.x >= n.z:
                pts2d = [(-g.z, g.y) for g in gs]
            elif n.y >= n.z:
                pts2d = [(g.x, -g.z) for g in gs]
            else:
                pts2d = [(g.x, g.y) for g in gs]
        xs = [p[0] for p in pts2d]; ys = [p[1] for p in pts2d]
        mnx, mny = min(xs), min(ys)
        dx, dy = max(max(xs) - mnx, 1e-6), max(max(ys) - mny, 1e-6)
        for l, p in zip(f.loops, pts2d):
            uu = margin + (1 - 2 * margin) * (p[0] - mnx) / dx
            vv = margin + (1 - 2 * margin) * (p[1] - mny) / dy
            l[self.uv].uv = (u0 + (u1 - u0) * uu, v0 + (v1 - v0) * vv)
        f.material_index = 1 if region in FURN_REGIONS else 0

    def _faces(self, vs, quads, region, cap_region=None, caps=()):
        out = []
        for q in quads:
            f = self.bm.faces.new([vs[i] for i in q])
            out.append(f)
        self.bm.normal_update()
        for f in out:
            self._uv_face(f, region)
        return out

    def box(self, lo, hi, region='steel', top=None, end=None):
        """Axis-aligned box from game-space min/max corners."""
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        prof = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        self.loft([(z0, prof), (z1, prof)], region, top=top, end=end)

    def loft(self, stations, region='steel', top=None, end=None, cx=0.0):
        """Cross sections [(z, [(x, y), ...]), ...] bridged along Z, capped.
        Faces facing up (+Y) use `top`, end caps use `end` (default region)."""
        bm = self.bm
        rings = [[bm.verts.new(G(x, y, z)) for (x, y) in prof] for z, prof in stations]
        n = len(rings[0]); faces = []
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n
                faces.append(bm.faces.new((a[k], a[k2], b[k2], b[k])))
        caps = [bm.faces.new(list(reversed(rings[0]))), bm.faces.new(rings[-1])]
        self._fix_normals(faces + caps, rings)
        for f in faces:
            ng = Vector((f.normal.x, f.normal.z, -f.normal.y))
            self._uv_face(f, top if (top and ng.y > 0.7) else region)
        for f in caps:
            self._uv_face(f, end or region)

    def prism(self, pts_zy, x0, x1, region='steel', side=None, top=None):
        """Side-profile polygon [(z, y), ...] extruded across X from x0 to x1.
        Big side faces use `region` mapped by the profile bbox (Z along U);
        the thin strip faces use `side` (default region)."""
        bm = self.bm
        L = [bm.verts.new(G(x0, y, z)) for z, y in pts_zy]
        R = [bm.verts.new(G(x1, y, z)) for z, y in pts_zy]
        n = len(pts_zy); strips = []
        for k in range(n):
            k2 = (k + 1) % n
            strips.append(bm.faces.new((L[k], L[k2], R[k2], R[k])))
        caps = [bm.faces.new(list(reversed(L))), bm.faces.new(R)]
        self._fix_normals(strips + caps, [L, R])
        pts = [(-z, y) for z, y in pts_zy]
        for f in caps:
            ordered = [(-M.game_of(l.vert.co).z, M.game_of(l.vert.co).y) for l in f.loops]
            self._uv_face(f, region, pts2d=ordered)
        for f in strips:
            ng = Vector((f.normal.x, f.normal.z, -f.normal.y))
            self._uv_face(f, top if (top and ng.y > 0.6) else (side or region))

    def cyl(self, p0, p1, r, segs=8, region='barrel', cap='steel', cap0=None, r1=None):
        """Cylinder from game p0 to p1. UV wraps continuously around the side."""
        bm = self.bm
        p0, p1 = Vector(p0), Vector(p1)
        ax = (p1 - p0).normalized()
        hlp = Vector((0, 1, 0)) if abs(ax.y) < 0.9 else Vector((1, 0, 0))
        u = ax.cross(hlp).normalized(); v = ax.cross(u).normalized()
        r1 = r if r1 is None else r1
        ring = lambda p, rr: [bm.verts.new(G(p + (u * math.cos(a) + v * math.sin(a)) * rr))
                              for a in (2 * math.pi * (i + 0.5) / segs for i in range(segs))]
        A, B = ring(p0, r), ring(p1, r1)
        sides = []
        for k in range(segs):
            k2 = (k + 1) % segs
            sides.append(bm.faces.new((A[k], A[k2], B[k2], B[k])))
        caps = [bm.faces.new(list(reversed(A))), bm.faces.new(B)]
        self._fix_normals(sides + caps, [A, B])
        x0, y0, x1, y1 = REGION[region]
        u0, v0, u1, v1 = (x0 + PAD) / S, (y0 + PAD) / S, (x1 - PAD) / S, (y1 - PAD) / S
        for k, f in enumerate(sides):
            for l in f.loops:
                i = A.index(l.vert) if l.vert in A else B.index(l.vert)
                along = 0.0 if l.vert in A else 1.0
                kk = i if not (k == segs - 1 and i == 0) else segs
                l[self.uv].uv = (u0 + (u1 - u0) * along, v0 + (v1 - v0) * kk / segs)
            f.material_index = 1 if region in FURN_REGIONS else 0
        self._uv_face(caps[0], cap0 or cap); self._uv_face(caps[1], cap)

    def _fix_normals(self, faces, rings):
        c = Vector((0, 0, 0)); cnt = 0
        for r in rings:
            for vv in r:
                c += vv.co; cnt += 1
        c /= cnt
        for f in faces:
            f.normal_update()
            if f.normal.dot(f.calc_center_median() - c) < 0 and len(f.verts) > 2:
                f.normal_flip()
        # strip/cap orientation for concave prisms is handled by recalc below
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)

    def to_object(self, mats, smooth=35):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me); self.bm.free()
        for m in mats:
            me.materials.append(m)
        used = {p.material_index for p in me.polygons}
        if used == {0} and len(mats) > 1:
            me.materials.pop(index=1)
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.collection.objects.link(ob)
        M.shade(ob, smooth)
        return ob


def make_materials(name, img_path, furn='wood'):
    img = bpy.data.images.load(os.path.abspath(img_path)); img.pack()
    out = []
    furn_vals = (0.0, 0.58, 0.45) if furn == 'wood' else (0.0, 0.62, 0.40)
    for key, (metal, rough, spec) in (('steel', (1.0, 0.30, 0.5)), (furn, furn_vals)):
        mat = bpy.data.materials.new(name + ('' if key == 'steel' else '_' + key))
        mat.use_nodes = True
        nt = mat.node_tree; bsdf = nt.nodes.get('Principled BSDF')
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Closest'
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Specular IOR Level'].default_value = spec
        out.append(mat)
    return out


def assemble(root_name, objs, empties, mag_name='magazine'):
    """objs: {name: object}. empties: {name: game_pos}. mag goes under mag_well."""
    root = M.new_empty(root_name, (0, 0, 0))
    em = {}
    for n, p in empties.items():
        em[n] = M.new_empty(n, Vector(p), parent=root)
    for n, ob in objs.items():
        if n == mag_name:
            M.set_origin_world(ob, G(Vector(empties['mag_well'])))
            mw = ob.matrix_world.copy(); ob.parent = em['mag_well']; ob.matrix_world = mw
        else:
            mw = ob.matrix_world.copy(); ob.parent = root; ob.matrix_world = mw
    return root


def save_blend(out_dir, name):
    mn, mx, c, size = M.mesh_bounds_game([o for o in bpy.context.scene.objects if o.type == 'MESH'])
    print('GAME BOUNDS', tuple(round(v, 4) for v in mn), tuple(round(v, 4) for v in mx),
          'size', tuple(round(v, 4) for v in size))
    blend = os.path.abspath(os.path.join(out_dir, name + '.blend'))
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    print('saved', blend)


def render_glb(glb, render_dir, prefix, small_dir=None):
    M.reset_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        for slot in o.material_slots:
            for n in slot.material.node_tree.nodes:
                if n.type == 'TEX_IMAGE':
                    n.interpolation = 'Closest'
    mn, mx, center, size = M.mesh_bounds_game(meshes)
    L = max(size.z, 0.2)
    k = L / 0.22
    cam, ground = M.setup_preview_scene()
    sc = bpy.context.scene
    sc.cycles.samples = 40
    sc.render.resolution_x, sc.render.resolution_y = 1200, 700
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
    dist = L * 1.75
    views = {
        'front': G(center.x, center.y + 0.03 * k, mn.z - dist * 0.55),
        'side': G(mn.x - dist, center.y + 0.02 * k, center.z),
        'three': G(mx.x + dist * 0.62, center.y + 0.35 * dist, center.z - dist * 0.62),
    }
    os.makedirs(render_dir, exist_ok=True)
    paths = []
    for name, loc in views.items():
        M.aim_camera(cam, look, loc)
        cam.data.lens = 60 if name != 'front' else 75
        p = os.path.join(render_dir, f'{prefix}_{name}.png')
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p); print('rendered', p)
        if small_dir:
            os.makedirs(small_dir, exist_ok=True)
            im = bpy.data.images.load(p)
            im.scale(600, 350)
            sp = os.path.join(small_dir, f'{prefix}_{name}.png')
            im.filepath_raw = sp; im.file_format = 'PNG'; im.save()
            print('small', sp)
    return paths


def main(build_fn, name):
    import argparse
    raw = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--out-dir', default='assets/models/gun')
    p.add_argument('--render-glb', default='')
    p.add_argument('--render-dir', default='/workspace/guns_previews')
    p.add_argument('--small-dir', default='')
    a = p.parse_args(raw)
    if a.render_glb:
        render_glb(a.render_glb, a.render_dir, name, a.small_dir or None)
    else:
        build_fn(os.path.abspath(a.out_dir))
    print('DONE')
