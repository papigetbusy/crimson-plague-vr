// Reads Wrok's v2 wall textures (assets/textures/walls/v2/<set>/*.png) and the Crimson Halls atlas
// and turns them into one small script: const WallTexData = { files: { path: base64 } }.
// tools/build.js puts that script in the page, so the one-file build (served from raw.githack) needs no extra fetch.
const fs = require('fs'), path = require('path');
const SETS = ['crypt', 'blood', 'bog', 'frost', 'ember', 'void'];
const NAMES = ['texStone', 'texPanel', 'texPillar', 'texFloor', 'texFloor2', 'texFloor3', 'texFloorEdge', 'texCeil', 'texBanner', 'texCarpet', 'texCloth', 'texGold'];
function load(root) {
  const files = {};
  const kit = path.join(root, 'assets', 'models', 'env', 'crimson_halls', 'crimson_halls_atlas.png');
  if (fs.existsSync(kit)) files['kit/crimson_halls_atlas.png'] = fs.readFileSync(kit).toString('base64');
  else console.warn('wall_tex_embed: missing Crimson Halls atlas (kit details stay on the GLB map)');
  for (const set of SETS) for (const name of NAMES) {
    const rel = set + '/' + name + '.png', fp = path.join(root, 'assets', 'textures', 'walls', 'v2', rel);
    if (!fs.existsSync(fp)) continue;
    const buf = fs.readFileSync(fp);
    if (buf.length < 8 || buf[0] !== 0x89 || buf[1] !== 0x50) { console.warn('wall_tex_embed: ' + rel + ' is not a PNG'); continue; }
    files[rel] = buf.toString('base64');
  }
  return { sets: SETS, files };
}
const script = (root) => 'const WallTexData = ' + JSON.stringify(load(root)) + ';';
module.exports = { load, script, SETS, NAMES };
