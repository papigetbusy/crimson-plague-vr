#!/bin/sh
# Everything for the VR build in one go: build, every unit test, then the full fake-Quest playtest. Writes a markdown report.
# Usage: PUPPETEER_DIR=/workspace/xrsim/node_modules sh tools/xr_check_all.sh [report.md] [shots_dir]
cd "$(dirname "$0")/.." || exit 1
REPORT=${1:-/tmp/xr_report.md}; SHOTS=${2:-/tmp/xr_shots}; mkdir -p "$SHOTS"
node tools/guard.js || exit 1
node tools/build.js || exit 1
FAIL=0
for f in tests/*.test.js; do node "$f" > /tmp/xr_unit.txt 2>&1 || { echo "UNIT FAIL: $f"; grep FAIL /tmp/xr_unit.txt | head -5; FAIL=1; }; done
NODE_PATH=${PUPPETEER_DIR:-/workspace/xrsim/node_modules} node tools/xr_playtest.js --md "$REPORT" --shots "$SHOTS" || FAIL=1
echo "report: $REPORT  shots: $SHOTS"
exit $FAIL
