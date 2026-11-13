// v2 wall textures: the six sets are embedded, apply falls back to the painted canvases when they are not decoded,
// and world-projected UVs land inside the packed atlas. Run: node tests/walltex.test.js
const path = require('path'), root = path.join(__dirname, '..');
const Embed = require('../tools/wall_tex_embed.js');
global.WallMaterials = require('../src/screen/wall_materials.js'); const WallSets = require('../src/screen/wall_sets.js');
const WallTexV2 = require('../src/screen/wall_tex_v2.js');
let bad = 0;
const t = (name, ok, seen) => { console.log((ok ? 'ok   ' : 'FAIL ') + name + (seen !== undefined && !ok ? '  (' + seen + ')' : '')); if (!ok) bad++; };
const data = Embed.load(root);
t('The embed lists all six wall sets', data.sets.length === 6 && data.sets.slice().sort().join() === 'blood,bog,crypt,ember,frost,void');
t('Every set has walls, panels, pillars, floors and a ceiling', data.sets.every((s) => ['texStone', 'texPanel', 'texPillar', 'texFloor', 'texFloor2', 'texFloor3', 'texFloorEdge', 'texCeil'].every((n) => data.files[s + '/' + n + '.png'] && data.files[s + '/' + n + '.png'].length > 100)));
t('The Crypt also has the gold demon banner, gold, cloth and carpet', ['texBanner', 'texGold', 'texCloth', 'texCarpet'].every((n) => data.files['crypt/' + n + '.png']));
t('The Crimson Halls atlas is embedded (for sconce iron and flame)', !!(data.files['kit/crimson_halls_atlas.png'] && data.files['kit/crimson_halls_atlas.png'].length > 100));
t('The build script turns it into a WallTexData script', /^const WallTexData = \{/.test(Embed.script(root)));
const build = require('fs').readFileSync(path.join(root, 'tools', 'build.js'), 'utf8');
t('tools/build.js puts the v2 embed and wall_tex_v2.js in the page', /wall_tex_embed/.test(build) && /screen\/wall_tex_v2\.js/.test(build));

// without WallTexData / decoded images, apply keeps the original paint (unit tests and a failed load)
function canvas(w, h) { const px = new Array(w * h).fill('start'); const g = { fillStyle: '', fillRect(x, y, a, b) { for (let j = 0; j < b; j++) for (let i = 0; i < a; i++) if (x + i >= 0 && x + i < w && y + j >= 0 && y + j < h) px[(y + j) * w + x + i] = this.fillStyle; }, getImageData() { return px.slice(); }, putImageData(d) { for (let i = 0; i < d.length; i++) px[i] = d[i]; } }; return { width: w, height: h, px, getContext: () => g }; }
const NAMES = { texStone: [32, 64], texPanel: [32, 64], texPillar: [32, 64], texFloor: [32, 32], texFloor2: [32, 32], texFloor3: [32, 32], texFloorEdge: [32, 32], texCeil: [32, 32] };
const T = {}; for (const n in NAMES) T[n] = { image: canvas(NAMES[n][0], NAMES[n][1]), needsUpdate: false };
const s = WallSets.create(T); s.apply('blood');
t('If v2 has not decoded, apply still paints the Blood set on the old canvases', T.texStone.image.width === 32 && T.texStone.needsUpdate && !T.texStone.image.px.includes('start'));
t('WallTexV2.ready is false until create+start have decoded images', WallTexV2.ready() === false);
t('atlas() is null until then, so the kit keeps its own atlas', WallTexV2.atlas('crypt') === null);

// world UVs: a point on a +Z wall at (1, 1, 0) with a mid-wall atlas UV should land in the packed stone/panel region
const uv = WallTexV2.remapUv('corner', 0.25, 0.7, 1, 1, 0, 0, 0, 1, 'crypt', 2);
const P = WallTexV2.PACK.stone; // corner -> stone
const u0 = (P[0] + 1) / 1024, u1 = (P[0] + P[2] - 1) / 1024, v1 = 1 - (P[1] + 1) / 512, v0 = 1 - (P[1] + P[3] - 1) / 512;
t('A Crypt corner wall samples the packed stone tile', uv[0] >= u0 && uv[0] <= u1 && uv[1] >= v0 && uv[1] <= v1, uv.map((x) => x.toFixed(3)).join(','));
const uf = WallTexV2.remapUv('floor', 0.5, 0.5, 1, 0, 1, 0, 1, 0, 'blood', 2);
const F = WallTexV2.PACK.floor; // cell (0,0) -> floor
const fu0 = (F[0] + 1) / 1024, fu1 = (F[0] + F[2] - 1) / 1024;
t('A floor tile samples a packed floor region', uf[0] >= fu0 && uf[0] <= (WallTexV2.PACK.floor3[0] + WallTexV2.PACK.floor3[2] - 1) / 1024, uf.map((x) => x.toFixed(3)).join(','));
const ua = WallTexV2.remapUv('sconce', 0.8, 0.4, 0, 2.5, 0, 0, 0, 1, 'crypt', 2);
t('A sconce keeps the kit atlas (top-left of the packed sheet)', ua[0] >= 0 && ua[0] <= 256 / 1024 && ua[1] >= 0.5, ua.map((x) => x.toFixed(3)).join(','));
process.exit(bad ? 1 : 0);
