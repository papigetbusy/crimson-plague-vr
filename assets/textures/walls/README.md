# Wall textures, v2 (art only: the game does not load these yet)

- `original/<set>/` the game's current painted canvases (dumped by `tools/textures/dump_wall_textures.js`, src painters unchanged).
- `v2/<set>/` a from-scratch repaint at Crimson Halls kit quality (`tools/textures/repaint_walls.py`). Same names as the
  game's textures. The originals were only a guide for each set's colour mood and theme; nothing is copied or upscaled.
- `v2_src/skulls/` low-poly 3D skulls (with or without jaw, tilted, and the gold horned demon) rendered in Blender
  (`tools/textures/make_skull_sprites.py`) and composited into the textures, so skulls carry real form and shading.
- `previews/3d/` 3D wall-section renders (640x480 copies; full size 1280x960 in /workspace/wall_tex_previews/3d) built from the Crimson Halls kit modules (`tools/textures/render_wall_sections.py`),
  plus `contact_sheet_three_quarter.png` (Crimson Halls reference + all six sets, same camera).
- `previews/<set>_before_after.png` flat sheets: original, v2, v2 tiled 2x2 (`tools/textures/wall_previews.py`).

Sizes (64 px per metre): texStone / texPanel / texPillar / texBanner / texCloth 128x256 (one tile = 2 m x 4 m, plinth at
the bottom), texFloor / texFloor2 / texFloor3 / texFloorEdge / texCeil / texCarpet 128x128 (2 m x 2 m), texGold 64x64.
The game's canvases are 32x64 / 32x32 / 16x16, so wiring these in is a code change in `src/` (not part of this art pass).

Sets: crypt (grey ashlar, gold, crimson + demon banner), blood (stacked bones, 3D skulls in niches, drips), bog (rotten planks,
moss, slime, roots, glowing fungus, a sunken skull), frost (ice facets, icicles, rime, a skull frozen under ice), ember
(basalt columns, lava veins, embers, soot), void (polished indigo slabs, glowing runes, carved eye, tendrils). Every tile wraps.

Rebuild: `blender -b --python tools/textures/make_skull_sprites.py -- --out assets/textures/walls/v2_src/skulls`, then
`python3 tools/textures/repaint_walls.py`, `python3 tools/textures/wall_previews.py`, and the 3D renders (see the script header).
