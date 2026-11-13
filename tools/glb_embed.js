// Reads assets/models/manifest.json and turns every gun GLB it lists into one small script: const GlbData = { manifest, files: { path: base64 } }.
// tools/build.js puts that script in the page, so the single-file build (served from raw.githack) needs no extra fetch. Also used by tests/glb.test.js.
const fs = require('fs'), path = require('path');
function load(root) {
  const mf = path.join(root, 'assets', 'models', 'manifest.json');
  const manifest = fs.existsSync(mf) ? JSON.parse(fs.readFileSync(mf, 'utf8')) : {};
  const guns = manifest.guns || {}, files = {};
  for (const id of Object.keys(guns)) for (const file of [guns[id].file, guns[id].fallback].filter(Boolean)) {   // the gun's GLB and its fallback
    const f = path.join(root, 'assets', 'models', file);
    if (!fs.existsSync(f)) { console.warn('glb_embed: ' + id + ' -> missing ' + file + ' (the fallback or voxel gun stays)'); continue; }
    const buf = fs.readFileSync(f);
    if (buf.length < 20 || buf.readUInt32LE(0) !== 0x46546c67) { console.warn('glb_embed: ' + file + ' is not a GLB'); continue; }
    files[file] = buf.toString('base64');
  }
  const env = manifest.env || {};                                   // mesh wall kits (crimson_halls.js): every piece of each kit
  for (const id of Object.keys(env)) for (const f of Object.values(env[id].pieces || {})) {
    const rel = env[id].dir + f, fp = path.join(root, 'assets', 'models', rel);
    if (!fs.existsSync(fp)) { console.warn('glb_embed: kit ' + id + ' -> missing ' + rel + ' (the old walls stay)'); continue; }
    files[rel] = fs.readFileSync(fp).toString('base64');
  }
  return { manifest: { guns, env }, files };
}
const script = (root) => 'const GlbData = ' + JSON.stringify(load(root)) + ';';
module.exports = { load, script };
