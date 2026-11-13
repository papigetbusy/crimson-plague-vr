// Crimson Halls wall kit on every floor: the plan (walls 3 modules high to the roof, corners, pillars the size of their cells, nothing across
// openings, floor tiles, sconces whose flame sits on the torch light), the bake leaving out only what the kit replaces,
// collision unchanged, and the kit's GLBs decoding into one merged mesh. Run: node tests/halls.test.js
const fs = require('fs'), path = require('path');
const Referee = require('../src/referee.js'), WorldBake = require('../src/screen/world_bake.js'), CH = require('../src/screen/crimson_halls.js');
let fails = 0;
const t = (name, ok, seen) => { if (!ok) fails++; console.log((ok ? 'ok   ' : 'FAIL ') + name + (seen !== undefined && !ok ? '  (' + seen + ')' : '')); };
const sandbox = (seed) => { const r = Referee.create(seed); r.setCfg({ floorSize: 44, monsterCount: 2, doorTest: true, keepDrops: true }); r.reset(); return r; };
const FG = require('../src/floorgen.js');
const mk = (seed) => { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
const ref = Referee.create(1); ref.reset(); const map = ref.map, P = CH.plan(map), C = map.CELL;
t('Floor 1 of the real game gets a Crimson Halls plan for the whole floor', !!P && P.count.straight > 1000, JSON.stringify(P && P.count));
t('It uses straight walls, corners, pillars, floor tiles, banners and sconces', ['straight', 'corner', 'pillar', 'floor', 'banner', 'sconce'].every((k) => P.count[k] > 0), JSON.stringify(P.count));
t('No arch and no wall is drawn across an opening (the referee has openings open to the roof)', !P.count.arch);
const wallYs = [...new Set(P.place.filter((p) => p.piece === 'straight' || p.piece === 'corner').map((p) => p.y + ':' + p.sy))].sort();
t('Walls stack three 4 m modules up to the 11.5 m roof (the top one at 0.875)', JSON.stringify(wallYs) === JSON.stringify(['0:1', '4:1', '8:0.875']), JSON.stringify(wallYs));
const top = Math.max(...P.place.filter((p) => p.piece === 'straight').map((p) => p.y + p.sy * CH.ROW_H));
t('The top row meets the roof exactly', Math.abs(top - map.WALL_H) < 1e-9, top);
t('The brick trim is squashed so it stands only ~5 cm proud of the wall (a gun at the wall does not sink into it)', P.place.filter((p) => p.piece === 'straight').every((p) => p.sz === CH.TRIM_Z) && 0.16 * CH.TRIM_Z < 0.06);
const solidAt = (x, z) => { const ch = map.rows[Math.floor(z / C)] && map.rows[Math.floor(z / C)][Math.floor(x / C)]; return !(ch === '.' || ch === 'c' || ch === 'D' || ch === 'd'); };
const across = P.place.filter((p) => p.piece === 'straight').every((p) => { const nx = Math.sin(p.yaw), nz = Math.cos(p.yaw); return !solidAt(p.x + nx * 0.5, p.z + nz * 0.5) && solidAt(p.x - nx * 0.5, p.z - nz * 0.5); });
t('Every wall module stands on a real wall: open floor in front, a solid cell behind (none in a doorway)', across);
const pil = P.place.filter((p) => p.piece === 'pillar');
t('Kit pillars stand on pillar cells, scaled to the 2 m cell (so they match the collision)', pil.length > 0 && pil.every((p) => map.rows[Math.floor(p.z / C)][Math.floor(p.x / C)] === 'P' && Math.abs(p.sx * 0.8 - C) < 1e-9));
const sc = P.place.filter((p) => p.piece === 'sconce'), tor = map.torches.filter((x) => P.skip.torch.has(x));
const flameAt = (p) => [p.x + Math.sin(p.yaw) * 0.28, p.y + 0.28, p.z + Math.cos(p.yaw) * 0.28];
t('Each kit sconce\'s flame lands on its torch light (2.85 m up, 0.28 m off the wall)', sc.length === tor.length && sc.length > 50 && sc.every((p, i) => { const f = flameAt(p), q = tor[i]; return Math.hypot(f[0] - q.x, f[1] - q.y, f[2] - q.z) < 1e-6; }) && sc.every((p) => Math.abs(p.y - 2.57) < 1e-9));
t('Beside a torch the kit\'s light rolls off (no flat blown-out orange), the dark halls stay as they were', CH.tone(1.64) < 1.1 && Math.abs(CH.tone(0.15) - 0.15) < 0.03);
const plain = WorldBake.bake(map), kit = WorldBake.bake(map, P.skip);
const n = (b) => b.chunks.reduce((a, c) => a + c.pos.length, 0);
t('The bake leaves out the quads the kit replaces (the ceiling and door frames stay)', n(kit) < n(plain) && n(kit) > n(plain) * 0.2);
t('The torch light is the same with or without the kit', JSON.stringify(kit.light(5, 2, 5, 0, 1, 0)) === JSON.stringify(plain.light(5, 2, 5, 0, 1, 0)));
t('The gameplay walls do not change (the referee map is the collision)', (() => { const r2 = Referee.create(1); r2.reset(); return JSON.stringify(map.rows) === JSON.stringify(r2.map.rows); })());
let allFloors = true; for (const f of [1, 3, 6, 10]) { const m = FG.generate(f, mk(9 + f), f); m.WALL_H = 11.5; const Q = CH.plan(m); if (!Q || !Q.count.straight || !Q.count.floor) allFloors = false; }
const sr = FG.safeRoom(1); sr.WALL_H = 11.5;
t('Every floor size (80 to 140 cells), the safe room and the test map get the kit', allFloors && CH.plan(sr).count.straight > 0 && CH.plan(sandbox(3).map).count.straight > 0);
t('?voxelwalls keeps the old walls', CH.create({}, { query: '?voxelwalls' }).status().off === true && CH.create({}, { query: '' }).status().off === false);

const threePath = [process.env.THREE_JS, '/workspace/three128.js', path.join(__dirname, '..', 'node_modules', 'three', 'build', 'three.js')].find((p) => p && fs.existsSync(p));
(async () => {
  if (!threePath) { console.log('skip: no three.js r128 here, kit decode checks did not run'); return; }
  global.window = global; global.self = global;
  global.document = { createElementNS: () => { const img = { listeners: {}, addEventListener(k, f) { this.listeners[k] = f; }, removeEventListener() {}, set src(v) { this._src = v; setTimeout(() => this.listeners.load && this.listeners.load.call(img), 0); }, get src() { return this._src; }, width: 256, height: 256 }; return img; } };
  global.THREE = require(threePath); require('../src/vendor/gltf_loader_r128.js');
  const data = require('../tools/glb_embed.js').load(path.join(__dirname, '..'));
  t('The manifest lists the 7 kit pieces and the build embeds them', Object.keys(data.manifest.env.crimson_halls.pieces).length === 7 && Object.keys(data.files).filter((f) => /^env\//.test(f)).length === 7);
  const H = CH.create(THREE, { data, query: '' });
  await new Promise((res) => { H.start(res); setTimeout(res, 8000); });
  t('The kit decodes with the vendored GLTFLoader', H.ready(), JSON.stringify(H.status()));
  if (!H.ready()) return;
  const K = H.forMap(map), grp = K.build(plain.light), m0 = grp.children[0];
  t('The floor is a few merged blocks (one per 12 x 12 cells: one draw each) sharing one nearest-filtered atlas material, lit like the baked world', grp.children.length >= 4 && grp.children.length <= 196 && grp.children.every((m) => m.material === m0.material) && m0.material.type === 'MeshBasicMaterial' && m0.material.vertexColors && m0.material.map.magFilter === THREE.NearestFilter, grp.children.length);
  t('Hidden triangles are dropped (wall backs, row caps, floor tile sides): floor 1 under 200,000 triangles (was 281,000)', grp.userData.tris > 50000 && grp.userData.tris < 200000, grp.userData.tris);
  let mx = 0; for (const m of grp.children) for (const v of m.geometry.attributes.color.array) mx = Math.max(mx, v);
  t('It is torch-lit, not black and not blown out (vertex light under 1.1)', mx > 0.5 && mx < 1.1, mx);
  let topY = 0; for (const m of grp.children) { m.geometry.computeBoundingBox(); topY = Math.max(topY, m.geometry.boundingBox.max.y); }
  t('Nothing pokes through the roof', topY <= map.WALL_H + 0.05, topY);
  const broken = CH.create(THREE, { data: { manifest: data.manifest, files: Object.assign({}, data.files, { 'env/crimson_halls/ch_pillar.glb': Buffer.from('nope').toString('base64') }) }, query: '' });
  const cw = console.warn; let w = 0; console.warn = () => { w++; };
  await new Promise((res) => { broken.start(res); setTimeout(res, 1500); }); console.warn = cw;
  t('A kit GLB that will not decode keeps the old walls, with a console warning', !broken.ready() && broken.forMap(map) === null && w > 0);
})().catch((e) => { fails++; console.log('FAIL threw ' + (e && e.stack || e)); }).then(() => { console.log(fails ? fails + ' failed' : 'all Crimson Halls checks passed'); process.exit(fails ? 1 : 0); });
