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
