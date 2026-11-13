# Low-poly asset pipeline (PS2 / Snake Eater)

This is the pipeline the M1911 test (`assets/models/gun/pistol_1911_ps2.glb`) was built with. New guns, enemies and props should follow it. The game does not load these GLB files yet — the current guns are still the code-built voxel models in `src/models`. When a loader is added, it should fall back to those voxels if a file is missing or fails the checks below.

A real Government Model 1911 is about 0.216 m long. Keep guns at 1:1 scale so they sit naturally in VR hands.

## Limits

Enforced by `tools/blender/export_lowpoly.py`. The script refuses to write a GLB that is outside these numbers.

| Type   | Triangles   | Texture            | Materials        |
|--------|-------------|--------------------|------------------|
| gun    | 300–1,500   | one atlas, 128 or 256, power of two | one material |
| enemy  | 300–2,000   | same               | one material     |
| prop   | up to 500   | same               | one material     |

Aim for the middle of the band (about 600–1,000 triangles for a gun), not the ceiling. Slide serrations, wood checkering, screws and wear belong in the texture, not in extra geometry.

## Palette and texture

- One 128×128 or 256×256 albedo atlas, nearest-neighbour friendly (hard edges, 2–3 px of padding between colour regions so they do not bleed).
- About 8–16 colours. For guns: dark / mid / light blued steel, a near-black recess, a thin edge highlight, wood or dark grip colours, one or two silver or brass accents.
- No metal/roughness or normal maps in this pipeline. The single material is mostly diffuse (metallic 0) so wood and steel can share the atlas.
- In Blender, set the image node interpolation to Closest. The exporter writes a nearest `magFilter`.

## Naming, axes, origin

- **Axes (in the GLB, and in the game):** +Y up, muzzle toward −Z, +X to the gun's right, units in metres.
- Blender itself is Z-up. Model with Z up and the muzzle toward +Y; the exporter's `+Y up` option converts this to the game axes.
- **Origin is at the grip / hand position** (the palm, mid-panel), not at the muzzle and not at the world floor. The older voxel guns park the hand at a fixed offset `(0, −0.1365, 0.104)` instead; a future loader can add that offset if this mesh has to sit in the same pose.
- Root empty named after the asset (the 1911 uses `pistol_1911`).
- **Magazine is a separate mesh object named `magazine`**, origin at the mag-well lip, parented to a `mag_well` empty so a reload can drop it. Other moving parts (slide, hammer) can be separate objects too; they are not required.
- Anchor empties, identity rotation: `muzzle` (bore tip), `mag_well` (bottom of the well), `rear_sight` (top of the rear sight, useful later for aim). After export, −Z on these empties points muzzle-forward.

## How to build and export

Blender on this machine: `/workspace/blender-fiend/blender-4.2.3-linux-x64/blender`.

Build the 1911 from scratch (writes the `.blend`, the albedo PNG, and optional preview frames):

```bash
blender -b --python tools/blender/build_pistol_1911.py -- \
  --out-dir assets/models/gun \
  --render-dir /workspace/shots/pistol1911
```

Export any low-poly `.blend` (this is the reusable step for future assets):

```bash
blender -b path/to/asset.blend --python tools/blender/export_lowpoly.py -- \
  --out path/to/asset.glb --type gun
```

`--type` is `gun`, `enemy` or `prop`. The script applies modifiers and rotation/scale, triangulates a copy to count triangles, keeps object locations (so the magazine origin is not baked into the mesh), exports GLB with +Y up, no Draco, texture embedded, and prints a summary (tris, verts, texture size, materials, objects). It stops with a clear error if a limit is broken.

Useful flags: `--max-tris`, `--min-tris`, `--max-tex`, `--allow-multi-material` (off by default), `--blend` if the file is not already open.

## Notes

- `assets/models/gun/gun_rifle_v1.glb` is an old 4-byte stub (just a file header). Leave it alone; it is not a usable rifle.
- `assets/models/manifest.json` still says `"gun": null`. This test does not hook the 1911 into the game.
