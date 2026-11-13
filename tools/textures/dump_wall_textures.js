/* Renders every wall set's painted canvases to PNGs (art baseline, nothing in src/ is changed).
   usage: NODE_PATH=/workspace/xrsim/node_modules node tools/textures/dump_wall_textures.js [outDir]
   Default out: assets/textures/walls/original/<set>/<name>.png */
const fs = require('fs'), path = require('path');
const puppeteer = require('puppeteer-core');
const ROOT = path.resolve(__dirname, '..', '..');
const OUT = path.resolve(process.argv[2] || path.join(ROOT, 'assets/textures/walls/original'));
const src = (p) => fs.readFileSync(path.join(ROOT, 'src/screen', p), 'utf8');
const SET_NAMES = ['texStone', 'texPanel', 'texPillar', 'texFloor', 'texFloor2', 'texFloor3', 'texFloorEdge', 'texCeil'];
const CRYPT_EXTRA = ['texBanner', 'texGold', 'texCarpet', 'texCloth'];
(async () => {
  const b = await puppeteer.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const pg = await b.newPage();
  await pg.setContent('<body></body>');
  await pg.addScriptTag({ content: 'const THREE = { CanvasTexture: function (c) { this.image = c; }, NearestFilter: 1, RepeatWrapping: 2 };\n' + src('world_tex.js') + src('wall_materials.js') + src('wall_sets.js') });
  const data = await pg.evaluate((SET_NAMES, CRYPT_EXTRA) => {
    const out = {};
    for (const set of WallSets.LIST) {
      const T = WorldTex.create(THREE); WallSets.create(T).apply(set.id);
      const names = set.id === 'crypt' ? SET_NAMES.concat(CRYPT_EXTRA) : SET_NAMES;
      out[set.id] = {};
      for (const n of names) out[set.id][n] = T[n].image.toDataURL('image/png');
    }
    return out;
  }, SET_NAMES, CRYPT_EXTRA);
  for (const [set, texs] of Object.entries(data)) {
    fs.mkdirSync(path.join(OUT, set), { recursive: true });
    for (const [n, url] of Object.entries(texs)) fs.writeFileSync(path.join(OUT, set, n + '.png'), Buffer.from(url.split(',')[1], 'base64'));
    console.log(set, Object.keys(texs).length);
  }
  await b.close();
})();
