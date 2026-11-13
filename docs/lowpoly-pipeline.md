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

## Putting a GLB in the game (assets/models/manifest.json)
The game loads GLBs through `assets/models/manifest.json`. `node tools/build.js` reads it (`tools/glb_embed.js`) and puts every listed GLB inside the one-file page as base64, with three r128's GLTFLoader (`src/vendor/gltf_loader_r128.js`, no Draco). If a GLB is missing or will not decode, the game warns in the console and keeps the old voxel gun or old walls. Link flags: `?voxelguns` (old guns), `?voxelwalls` (old walls).
- **A gun:** add an entry under `guns`, keyed by the gun id in `src/referee_weapons.js` (e.g. `pistol_service`). `file` is the path under `assets/models/`. The GLB needs a `magazine` mesh parented under an empty `mag_well`, empties `muzzle` and `rear_sight`, optional `slide`; +Y up, muzzle toward -Z, origin at the grip. `grip` (model metres) is the hand spot, moved onto the same grip point as every voxel gun; `redDot`, `slideTravel` and `flatScale` fit the sight, the slide kick and the flat-screen size. `src/screen/glb_guns.js` turns it into the same parts as a voxel gun (body, magazine that drops on reload, slide, muzzle, sight, hands). Material: Phong with nearest-filtered atlas and a little self-light, lit by the torches. Skins do not repaint a mesh gun (ignored).
- **The 1911 now:** `pistol_service` points at Wrok's `gun/pistol_1911_base.glb` (blued steel, silver hammer, ivory grips), with `fallback: gun/pistol_1911_ps2.glb` if it will not decode, then the voxel pistol. To try another model change only `file`, rebuild, run `node tests/glb.test.js`, and nudge `grip`, `redDot` and `slideTravel` if it sits differently. Materials: parts whose GLB material is metallic (steel, hammer) become `MeshStandardMaterial` with a tiny PMREM environment (a 32 px warm hall gradient, made once) so they get a sheen; the rest stay `MeshPhongMaterial` lit by the torches like the voxel guns.
- **A wall kit:** list the pieces under `env.<kit>.pieces` (`straight`, `corner`, `arch`, `pillar`, `floor`, `sconce`, `banner`) with `dir`. `src/screen/crimson_halls.js` now dresses every floor of the real game (not only `?sandbox`): every wall face next to an open cell gets a kit wall stacked 3 modules high (4, 4, 3.5 m) to the 11.5 m roof, inner corners, pillar cells as kit pillars, floor tiles, banners, kit sconces with the flame on the torch light. No arches in the real levels (an arch draws wall above an opening the game treats as open, so there is none: openings stay full height). The trim is squashed to 35 % depth (`TRIM_Z`, about 5 cm proud) so the gun can't clip into it; triangles nobody can see (wall backs, the tops/bottoms hidden by stacking, floor-tile sides) are cut when the GLB is decoded; the baked torch light is passed through a soft curve (`tone`) so walls beside a torch are warm, not blown-out orange. Pieces are merged per 12 x 12 cell block (24 m squares), one draw call each, and blocks whose nearest point is beyond the fog are not drawn. The referee's cells stay the collision. Checks: `node tests/halls.test.js`; headset: the `meshes` group of `tools/xr_playtest.js`; screenshots and draw calls on floor 1 and the biggest floors: `node tools/xr_full_shots.js <dir>`.

