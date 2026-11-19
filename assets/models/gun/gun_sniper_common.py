"""Shared helpers for the gothic sniper remakes (bolt, antimat, marksman, rail): scope, scope rings, bolt handle.
Builds on gun_shotgun_common (HD albedo, satin walnut, glossy polymer, horn sweep)."""
import math, os, sys
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_shotgun_common as S
K, C, M, G = S.K, S.C, S.M, S.G


def scope(part, y, z_oc, z_obj, r=0.0125, big=0.0215, rings=(0.30, 0.68), y_base=None, base_w=0.0140, segs=14, turrets=True):
    """Gothic scope on the sight line (axis at height y, z_oc rear/ocular end, z_obj front/objective end).
    Returns nothing; region 'tube' = engraved steel, brass rings/turrets, dark lens caps ('muzzle')."""
    L = z_oc - z_obj
    st = [(z_oc, r * 1.15), (z_oc - 0.012, r * 1.45), (z_oc - 0.034, r * 1.12), (z_oc - 0.052, r),
          (z_obj + 0.075, r), (z_obj + 0.050, r * 1.3), (z_obj + 0.026, big * 0.92), (z_obj + 0.006, big), (z_obj, big)]
    K.revolve(part, st, y, segs=segs, region='tube', cap_f='muzzle', cap_b='muzzle')
    for zz, rr in ((z_oc - 0.0125, r * 1.45), (z_obj + 0.0105, big), (z_oc - 0.056, r), (z_obj + 0.082, r)):
        K.revolve(part, [(zz + 0.0022, rr + 0.0012), (zz - 0.0022, rr + 0.0012)], y, segs=segs, region='brass', cap_f='brass', cap_b='brass')
    zm = z_obj + 0.5 * (L - 0.13) + 0.05
    if turrets:
        part.cyl((0, y + r - 0.001, zm), (0, y + r + 0.0095, zm), 0.0062, 10, 'brass', cap='brass')           # elevation turret
        part.cyl((r - 0.001, y, zm), (r + 0.0095, y, zm), 0.0056, 10, 'brass', cap='brass')                      # windage turret
    for f in rings:
        zc = z_oc - 0.07 - f * (L - 0.2)
        yb = y_base if y_base is not None else y - 0.030
        part.loft([(zc + 0.007, K.hexp(-base_w, base_w, yb, y + r + 0.0030, 0.0075)), (zc - 0.007, K.hexp(-base_w, base_w, yb, y + r + 0.0030, 0.0075))], 'steel', top='steel_top')
        part.box((-base_w - 0.0004, y - 0.002, zc - 0.0062), (base_w + 0.0004, y + 0.002, zc + 0.0062), 'brass')    # brass screw band across the ring
    return zm


def energy_mat(base_mat, strength=1.0):
    """Third glTF material: the crimson energy channel (emissive, same atlas as `base_mat`; the atlas region is painted bright crimson so it still reads red if a loader drops emission)."""
    img = [n.image for n in base_mat.node_tree.nodes if n.type == 'TEX_IMAGE'][0]
    mat = bpy.data.materials.new(base_mat.name.split('_')[0] + '_energy')
    mat.use_nodes = True
    nt = mat.node_tree; b = nt.nodes.get('Principled BSDF')
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = img; node.interpolation = C.TEX_INTERP
    nt.links.new(node.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = 0.0
    b.inputs['Roughness'].default_value = 0.35
    b.inputs['Emission Color'].default_value = (0.95, 0.02, 0.05, 1.0)
    b.inputs['Emission Strength'].default_value = strength
    return mat


def coil(part, cy, r_c, r_w, z0, z1, pitch, pts_per_turn=8, segs=5, region='copper', cx=0.0, cap_region=None):
    """Real wound wire: a helix of round wire (centre radius r_c around the bore axis (cx, cy), wire radius r_w) from z0 down to z1 (z1 < z0)."""
    import bmesh
    from mathutils import Vector
    bm = part.bm
    turns = (z0 - z1) / pitch
    n = max(2, int(round(turns * pts_per_turn)) + 1)
    rings = []
    for i in range(n):
        t = i / (n - 1)
        th = 2 * math.pi * turns * t + math.pi / 2
        z = z0 + (z1 - z0) * t
        c = Vector((cx + r_c * math.cos(th), cy + r_c * math.sin(th), z))
        u = Vector((math.cos(th), math.sin(th), 0)); w = Vector((0, 0, 1))
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs + math.pi / segs
            q = c + r_w * (math.cos(a) * u + math.sin(a) * w)
            ring.append(bm.verts.new(G(q.x, q.y, q.z)))
        rings.append(ring)
    faces = []
    for A, B in zip(rings, rings[1:]):
        for k in range(segs):
            k2 = (k + 1) % segs
            faces.append(bm.faces.new((A[k], A[k2], B[k2], B[k])))
    c0 = bm.faces.new(list(reversed(rings[0]))); c1 = bm.faces.new(rings[-1])
    part._fix_normals(faces + [c0, c1], rings)
    for f in faces:
        part._uv_face(f, region)
    part._uv_face(c0, cap_region or region); part._uv_face(c1, cap_region or region)
