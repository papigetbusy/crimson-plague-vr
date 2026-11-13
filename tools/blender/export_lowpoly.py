"""Headless low-poly glTF export with hard limits for Crimson Plague VR.

Usage:
  blender -b <file.blend> --python tools/blender/export_lowpoly.py -- \\
      --out assets/models/gun/pistol_1911_ps2.glb --type gun

  blender -b --python tools/blender/export_lowpoly.py -- \\
      --blend <file.blend> --out <file.glb> --type enemy

The script never overwrites the source .blend (it works on a copy of the
meshes in memory). It fails with a clear message if the scene is outside
the limits for the asset type.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

# Triangle and texture caps per asset type. Guns stay in the PS2-era band
# the 1911 test established; enemies can be a little heavier; props stay light.
LIMITS = {
    'gun':   {'min_tris': 300, 'max_tris': 1500, 'max_tex': 256},
    'enemy': {'min_tris': 300, 'max_tris': 2000, 'max_tex': 256},
    'prop':  {'min_tris': 0,   'max_tris': 500,  'max_tex': 256},
}


def _argv():
    raw = sys.argv
    return raw[raw.index('--') + 1:] if '--' in raw else []


def _parse():
    p = argparse.ArgumentParser(description='Export a low-poly GLB with enforced limits.')
    p.add_argument('--blend', default=None, help='Open this .blend first (optional if already loaded).')
    p.add_argument('--out', required=True, help='Output .glb path.')
    p.add_argument('--type', choices=sorted(LIMITS), default='gun', help='Asset type (sets limits).')
    p.add_argument('--max-tris', type=int, default=None, help='Override max triangles.')
    p.add_argument('--min-tris', type=int, default=None, help='Override min triangles.')
    p.add_argument('--max-tex', type=int, default=None, help='Override max texture size in pixels.')
    p.add_argument('--allow-multi-material', action='store_true',
                   help='Allow more than one material or more than one texture image.')
    return p.parse_args(_argv())


def _is_pot(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _eval_mesh(obj, depsgraph):
    ev = obj.evaluated_get(depsgraph)
    return ev.to_mesh()


def _tri_vert_counts(objs, depsgraph):
    """Apply modifiers (via evaluated mesh), triangulate a copy, count."""
    total_tris = 0
    total_verts = 0
    per = []
    for obj in objs:
        me = _eval_mesh(obj, depsgraph)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
        tris = len(bm.faces)
        verts = len(bm.verts)
        total_tris += tris
        total_verts += verts
        per.append((obj.name, tris, verts))
        bm.free()
        ev = obj.evaluated_get(depsgraph)
        ev.to_mesh_clear()
    return total_tris, total_verts, per


def _used_materials(objs):
    mats = []
    seen = set()
    for obj in objs:
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat.name not in seen:
                seen.add(mat.name)
                mats.append(mat)
    return mats


def _images_on_material(mat):
    images = []
    if not mat or not mat.use_nodes or not mat.node_tree:
        return images
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            images.append(node.image)
    return images


def _image_size(img):
    # Packed or generated images have size; some file images too.
    w, h = int(img.size[0]), int(img.size[1])
    return w, h


def _fail(msg):
    print('ERROR: ' + msg, file=sys.stderr)
    raise SystemExit(msg)


def _apply_transforms_and_modifiers(objs):
    """Duplicate work is avoided: export_apply=True applies modifiers and
    currently applied transforms on export. We still apply location/rotation/
    scale on the live objects so the counts we print match the file. The
    script is not supposed to save the .blend, so this is safe."""
    bpy.ops.object.select_all(action='DESELECT')
    # Apply in object mode, each mesh by itself so parenting stays intact
    # after location apply... Applying location on a child bakes the parent
    # offset, which we do NOT want. Only apply rotation/scale, and location
    # only on unparented meshes or when delta is already at the origin.
    for obj in objs:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as ex:
                print('warning: could not apply modifier', mod.name, 'on', obj.name, ex)
        obj.select_set(False)


def main():
    args = _parse()
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend))

    limits = dict(LIMITS[args.type])
    if args.max_tris is not None:
        limits['max_tris'] = args.max_tris
    if args.min_tris is not None:
        limits['min_tris'] = args.min_tris
    if args.max_tex is not None:
        limits['max_tex'] = args.max_tex

    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
    other_objs = [o for o in bpy.context.scene.objects if o.type != 'MESH' and not o.hide_render]
    if not mesh_objs:
        _fail('No mesh objects in the scene to export.')

    _apply_transforms_and_modifiers(mesh_objs)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    total_tris, total_verts, per = _tri_vert_counts(mesh_objs, depsgraph)

    mats = _used_materials(mesh_objs)
    images = []
    seen_img = set()
    for mat in mats:
        for img in _images_on_material(mat):
            if img.name not in seen_img:
                seen_img.add(img.name)
                images.append(img)

    errors = []
    if total_tris > limits['max_tris']:
        errors.append(
            f'{total_tris} triangles exceeds the {args.type} limit of {limits["max_tris"]}. '
            f'Simplify the mesh or raise --max-tris if this type should allow more.'
        )
    if total_tris < limits['min_tris']:
        errors.append(
            f'{total_tris} triangles is under the {args.type} minimum of {limits["min_tris"]}. '
            f'The silhouette will read as a blob in VR; add form (or pass --min-tris).'
        )
    if not args.allow_multi_material:
        if len(mats) > 1:
            errors.append(
                f'{len(mats)} materials found ({", ".join(m.name for m in mats)}). '
                f'Default pipeline is one material / one atlas. Fix or pass --allow-multi-material.'
            )
        if len(images) > 1:
            errors.append(
                f'{len(images)} textures found ({", ".join(i.name for i in images)}). '
                f'Default pipeline is a single atlas. Fix or pass --allow-multi-material.'
            )
    if not images:
        errors.append('No image texture found. The pipeline expects one atlas packed into the material.')
    tex_info = []
    for img in images:
        w, h = _image_size(img)
        tex_info.append((img.name, w, h))
        if w > limits['max_tex'] or h > limits['max_tex']:
            errors.append(
                f'Texture {img.name} is {w}x{h}, larger than the {limits["max_tex"]}px cap.'
            )
        if not _is_pot(w) or not _is_pot(h):
            errors.append(
                f'Texture {img.name} is {w}x{h}, not a power of two. Use 128 or 256.'
            )

    print('=== low-poly export check ===')
    print(f'type:      {args.type}')
    print(f'limits:    {limits["min_tris"]}-{limits["max_tris"]} tris, texture <= {limits["max_tex"]} px POT')
    print(f'tris:      {total_tris}')
    print(f'verts:     {total_verts}')
    print('objects:')
    for name, tris, verts in per:
        print(f'  - {name}: {tris} tris, {verts} verts')
    extras = [o.name + f' ({o.type})' for o in other_objs]
    if extras:
        print('empties/other: ' + ', '.join(extras))
    print('materials: ' + (', '.join(m.name for m in mats) or '(none)'))
    print('textures:  ' + (', '.join(f'{n} {w}x{h}' for n, w, h in tex_info) or '(none)'))

    if errors:
        for e in errors:
            print('ERROR: ' + e, file=sys.stderr)
        raise SystemExit(f'Export aborted ({len(errors)} limit error{"s" if len(errors) != 1 else ""}).')

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)

    # Select exportable objects (meshes + empties/armatures, skip cameras/lights).
    bpy.ops.object.select_all(action='DESELECT')
    exportable = []
    for o in bpy.context.scene.objects:
        if o.hide_render:
            continue
        if o.type in {'MESH', 'EMPTY', 'ARMATURE'}:
            o.select_set(True)
            exportable.append(o)
    if exportable:
        bpy.context.view_layer.objects.active = exportable[0]

    bpy.ops.export_scene.gltf(
        filepath=out,
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        # Modifiers and rotation/scale are applied above. Location is left
        # in place so moving parts (a magazine) and anchor empties keep
        # their origins after export.
        export_apply=False,
        export_texcoords=True,
        export_normals=True,
        export_materials='EXPORT',
        export_cameras=False,
        export_lights=False,
        export_extras=True,
        export_draco_mesh_compression_enable=False,
        export_image_format='AUTO',
        export_keep_originals=False,
        export_animations=False,
        export_skins=False,
        export_morph=False,
        export_nla_strips=False,
        export_force_sampling=False,
        export_tangents=False,
    )
    size = os.path.getsize(out)
    print(f'wrote {out} ({size} bytes)')
    print(f'summary: {total_tris} tris, {total_verts} verts, '
          f'{len(mats)} material(s), {len(images)} texture(s), {len(exportable)} objects, Y-up, no Draco')


if __name__ == '__main__':
    main()
