#!/usr/bin/env bash
# Rebuild the Crimson Halls kit, export every piece through the pipeline exporter, render previews.
# Run from the repo root. BLENDER defaults to the shared box install.
set -euo pipefail
BLENDER=${BLENDER:-/workspace/blender-fiend/blender-4.2.3-linux-x64/blender}
KIT=assets/models/env/crimson_halls
TMP=${TMP_PIECES:-/tmp/crimson_halls_pieces}
PREVIEW_DIR=${PREVIEW_DIR:-/workspace/crimson_halls_previews}

"$BLENDER" -b --python "$KIT/build_crimson_halls.py" -- --out-dir "$KIT" --piece-dir "$TMP"
for piece in wall_straight wall_corner doorway_arch pillar floor_tile torch_sconce banner; do
  "$BLENDER" -b "$TMP/ch_$piece.blend" --python tools/blender/export_lowpoly.py -- \
    --out "$KIT/ch_$piece.glb" --type prop
done
"$BLENDER" -b --python "$KIT/render_previews.py" -- --kit-dir "$KIT" --out-dir "$PREVIEW_DIR"
