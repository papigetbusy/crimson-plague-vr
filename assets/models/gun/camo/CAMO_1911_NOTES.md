# 1911 camo pilot (common / uncommon / rare)

Branch `grok/camo-1911` (off `grok/base-gun-remakes`). Art only; no src/ or game code touched.

Files (all in `assets/models/gun/camo/`):
- `pistol_1911_camo_{common,uncommon,rare}.glb` - game GLBs (1311 tris, 3 meshes, 4 empties, `redDot:false`, one 1024 LINEAR atlas each). Same node table and same triangle geometry as `pistol_1911_base.glb`.
- `pistol_1911_camo_*_albedo.png` - the three 1024x1024 albedo atlases. `.blend` files are the matching sources.
- `camo_1911_layout.py` shared atlas layout, `camo_1911_paint.py` painter (numpy/PIL, 4x supersampled), `camo_1911_build.py` Blender build (reuses `build_1911_base.py` + the tool mesh module, adds a UV re-layout), `compare_glb.py` + `compare_report.txt` mesh/empty equality check.

Rebuild: `python3 camo_1911_paint.py all .` then per tier `blender -b --python camo_1911_build.py -- --tier <t> --out-dir .`, then `tools/blender/export_lowpoly.py --type gun --max-tris 3000 --max-tex 1024 --allow-multi-material`.

Honest notes
- Materials are unchanged (steel metal 1.0 / rough 0.30, ivory metal 0.0 / rough 0.42): the tiers are ALBEDO-ONLY swaps. No roughness/metal maps exist in this format.
- UVs: the old 256 px atlas gave every slide/frame flat a shared 32 px swatch cell, which cannot hold inlay or scrimshaw. UV coordinates of the slide side walls, frame side walls, the two grip panels and the muzzle disc were re-laid into dedicated regions of the 1024 atlas, and all swatch cells moved to 4x. This layout is identical for all three tiers, so tier swaps are texture-only against each other. Versus the old `pistol_1911_base.glb`, positions/normals/indices/empties are identical (frame, magazine byte-identical; slide triangle set identical, only the exporter's vertex order differs) but UVs differ, so the new GLBs replace the base as a unit (no mixing old UVs with new textures).
- Texture sampler is Linear (no Closest) for crisp smooth detail.

---

# EPIC and LEGENDARY (shape tiers)

Files: `pistol_1911_camo_{epic,legendary}.glb` (+ `.blend`, `_albedo.png`). Built by `camo_1911_paint_hi.py` (atlas) -> `camo_1911_shape_build.py` (Blender; shapes in `camo_1911_shapes.py`, legendary parts in `camo_1911_legendary.py`, rune glyph strokes in `camo_1911_runes.py`) -> `tools/blender/export_lowpoly.py --type gun --max-tris 5000 --max-tex 1024 --allow-multi-material`.
Rebuild: `python3 camo_1911_paint_hi.py <epic|legendary> .` then `blender -b --python camo_1911_shape_build.py -- --tier <t> --out-dir .` then the export above.
`verify_sightline.py <glb>` ray-casts the sight line (0.3 / 1 / 2 mm offsets) and compares it with the locked base GLB.

| tier | tris | slide / frame / mag | muzzle empty z |
|---|---|---|---|
| epic | 4497 | 1155 / 3242 / 100 | -0.2044 (skull front) |
| legendary | 4929 | 1113 / 3716 / 100 | -0.2238 (bore exit of the spire) |

Format kept: same 3 meshes + `pistol_1911` root + the 4 empties (`muzzle`, `mag_well`, `rear_sight`, `front_sight`) with identical node table to the base GLB EXCEPT the `muzzle` empty z, which moved to the new muzzle tip. `redDot:false`. `verify_ads.js camo/<glb> pistol` passes for both. Sight line: no new geometry on it versus the locked base (the base's own rear-sight block is the only hit; see `verify_sightline.py` output). Highest new geometry between the sights is the hammer (epic <= 0.0724 m, legendary finial <= 0.0734 m) against a sight line at ~0.0767-0.078 m.

## Shapes
EPIC: boolean-built skull muzzle brake (bore = nasal cavity, 4 bone teeth, violet eye orbs), thorned shroud under the dust cover (14 thorns + violet strips), 9-vertebra spine ridge with violet cord (kept narrow over the ejection port), extended beavertail, silver claw hammer. Dark blued steel with the rare silver inlay carried over, violet accent.
LEGENDARY: reliquary. Dust cover replaced by a ribcage (6 bone ribs, sternum bar, dark core, gold sternum spire pointing forward), gold stepped pinnacle muzzle with a crown of 4 bone spires, pierced-lancet gold spire hammer, cathedral-arch ivory grip panels with raised gold arch ridge and painted gold rose window / cross / tracery, gold filigree + border rules on the slide, ten Elder-Futhark rune glyphs on each slide wall (emissive crimson 3D ribbons over an engraved channel). Bone/ivory + gold + crimson.
Base slide/frame edges got a small smoothing bevel (slide 1.4 mm / frame 1.3 mm, 2 segments, only edges longer than 6 mm; magazine untouched). All new parts use rounded tube/lathe/beveled-extrude primitives.

## New third material: `energy` (emissive)
Both tiers add a 3rd glTF material `*_energy` (metal 0, rough 0.35, same atlas, `KHR_materials_emissive_strength`): epic emissive (0.52, 0.16, 1.00) strength 5; legendary (1.00, 0.02, 0.05) strength 6. It is used only on the glowing faces (epic: eye orbs, spine cord, shroud strips; legendary: rune ribbons). The same atlas cells are painted bright violet / crimson, so if the engine ignores emissive the glow still reads as a bright painted colour (same fallback approach as sniper_rail). The ivory material (bone) is also present on both tiers. Stock three-material count on the 1911 is now 3 for these tiers (steel / ivory / energy).

## Tracer trail specs (NO game code exists for this; for Gamez to wire up)
Anchor: spawn at the `muzzle` empty, travel along the fire ray, additive blend, camera-facing ribbon, no shadows.
EPIC "violet plasma tracer": core #ECC8FF (hot), body #A860FF, edge/deep #461496. Width 1.4 cm at the muzzle tapering to 0.4 cm at the tail; length 6 m (capped by distance travelled); lifetime 0.18 s, alpha fades linearly 1 -> 0, hue shifts body -> deep over the lifetime. Optional 0.05 s muzzle flash sprite in #A860FF, radius 6 cm. Skull eyes and spine cord pulse (emissive 5 -> 7) for 0.08 s on each shot.
LEGENDARY "blood-smoke trail": core #FF9682 (hot), body #FF1628, deep #6E000C, smoke #1A0508 (50% alpha). Width 2.0 cm at the muzzle growing to 5 cm at the tail (smoke puffs 3-6 cm, 6-8 puffs per metre), length 8 m, lifetime 0.45 s; the red ribbon fades over 0.2 s, the smoke over 0.45 s with slow upward drift (+0.15 m/s) and noise. Runes pulse (emissive 6 -> 9) for 0.12 s on each shot; muzzle flash gold-white #FFE6A0 radius 8 cm.
These are suggested starting values; I could not tune them in-engine.

## Honest notes / weak spots
- No mock tracer renders were made (no game code to render with); only the specs above.
- Epic spine reads as small domes with spikes, not a convincing vertebral column from the 3/4 angle; the thorn shroud is mostly hidden by the dust cover at the 3/4 angle (visible from the low front view). Violet accent is subtle in the 3/4 render. The skull is faceted at close range (booleans on ~20-segment ellipsoids) and slightly toy-like next to the sleek slide.
- Legendary ribs are plain smooth bone tubes (no vertebral detail), the grip panels are flat slabs with painted tracery (only the arch outline and ridge are geometry), and the muzzle crown reads thin from the front view. The hammer looks like a tombstone arch at close range and is visible in the ADS view below the sight line (does not block it).
- Rune ribbons are about 0.8 mm wide; at the 1200x700 preview they read as red glyphs, at gameplay distance they will be thin.
- Tier meshes differ in shape, so these two GLBs are not texture-only swaps against common/uncommon/rare (those three remain texture-only swaps of each other).
