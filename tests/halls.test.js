// Crimson Halls wall kit on the VR test map: the plan for the start room (walls 3 modules high to the roof, corners, pillars the size of their
// cells, arches on narrow openings, floor tiles, sconces whose flame sits on the torch light), the bake leaving out only what the kit replaces,
// collision unchanged, and the kit's GLBs decoding into one merged mesh. Run: node tests/halls.test.js
const fs = require('fs'), path = require('path');
const Referee = require('../src/referee.js'), WorldBake = require('../src/screen/world_bake.js'), CH = require('../src/screen/crimson_halls.js');
let fails = 0;
const t = (name, ok, seen) => { if (!ok) fails++; console.log((ok ? 'ok   ' : 'FAIL ') + name + (seen !== undefined && !ok ? '  (' + seen + ')' : '')); };
const sandbox = (seed) => { const r = Referee.create(seed); r.setCfg({ floorSize: 44, monsterCount: 2, doorTest: true, keepDrops: true }); r.reset(); return r; };
const ref = sandbox(1), map = ref.map, P = CH.plan(map), C = map.CELL;
t('The test map\'s start room gets a Crimson Halls plan', !!P && P.room.kind === 'start');
t('It uses straight walls, corners, pillars, floor tiles, banners and sconces', ['straight', 'corner', 'pillar', 'floor', 'banner', 'sconce'].every((k) => P.count[k] > 0), JSON.stringify(P.count));
t('A narrow opening gets a doorway arch (seed 1 has one)', P.count.arch === 1 && P.arches.length === 1);
const wallYs = [...new Set(P.place.filter((p) => p.piece === 'straight' || p.piece === 'corner').map((p) => p.y + ':' + p.sy))].sort();
t('Walls stack three 4 m modules up to the 11.5 m roof (the top one at 0.875)', JSON.stringify(wallYs) === JSON.stringify(['0:1', '4:1', '8:0.875']), JSON.stringify(wallYs));
const top = Math.max(...P.place.filter((p) => p.piece === 'straight').map((p) => p.y + p.sy * CH.ROW_H));
t('The top row meets the roof exactly', Math.abs(top - map.WALL_H) < 1e-9, top);
const pil = P.place.filter((p) => p.piece === 'pillar');
t('Kit pillars stand on the room\'s pillar cells, scaled to the 2 m cell (so they match the collision)', pil.length > 0 && pil.every((p) => map.rows[Math.floor(p.z / C)][Math.floor(p.x / C)] === 'P' && Math.abs(p.sx * 0.8 - C) < 1e-9));
const onEdge = P.place.filter((p) => p.piece === 'straight' && p.sx === 1).every((p) => { const fx = p.x / C - Math.floor(p.x / C), fz = p.z / C - Math.floor(p.z / C); return (Math.abs(fx) < 1e-9 && Math.abs(fz - 0.5) < 1e-9) || (Math.abs(fz) < 1e-9 && Math.abs(fx - 0.5) < 1e-9); });
t('Every full wall module sits on a cell edge (the gameplay wall plane), centred on the cell', onEdge);
const sc = P.place.filter((p) => p.piece === 'sconce'), tor = map.torches.filter((x) => P.skip.torch.has(x));
const flameAt = (p) => [p.x + Math.sin(p.yaw) * 0.28, p.y + 0.28, p.z + Math.cos(p.yaw) * 0.28];
t('Each kit sconce\'s flame lands on its torch light (2.85 m up, 0.28 m off the wall)', sc.length === tor.length && sc.every((p, i) => { const f = flameAt(p), q = tor[i]; return Math.hypot(f[0] - q.x, f[1] - q.y, f[2] - q.z) < 1e-6; }) && sc.every((p) => Math.abs(p.y - 2.57) < 1e-9));
const plain = WorldBake.bake(map), kit = WorldBake.bake(map, P.skip);
const n = (b) => b.chunks.reduce((a, c) => a + c.pos.length, 0);
t('The bake leaves out the quads the kit replaces, and only those', n(kit) < n(plain) && n(kit) > n(plain) * 0.5);
t('The torch light is the same with or without the kit', JSON.stringify(kit.light(5, 2, 5, 0, 1, 0)) === JSON.stringify(plain.light(5, 2, 5, 0, 1, 0)));
t('The gameplay walls do not change (the referee map is the collision)', JSON.stringify(map.rows) === JSON.stringify(sandbox(1).map.rows));
let allSeeds = true; for (const s of [2, 3, 5, 7, 11, 13]) { const Q = CH.plan(sandbox(s).map); if (!Q || !Q.count.straight || !Q.count.floor) allSeeds = false; }
t('Every test map seed gets a Crimson Halls room', allSeeds);
t('The full game\'s floors get nothing (only ?sandbox turns it on)', CH.create({}, { query: '', data: { manifest: { env: { crimson_halls: { dir: '', pieces: {} } } }, files: {} } }).status().off === true);
t('?voxelwalls keeps the old walls on the test map', CH.create({}, { query: '?sandbox&voxelwalls' }).status().off === true);

const threePath = [process.env.THREE_JS, '/workspace/three128.js', path.join(__dirname, '..', 'node_modules', 'three', 'build', 'three.js')].find((p) => p && fs.existsSync(p));
(async () => {
  if (!threePath) { console.log('skip: no three.js r128 here, kit decode checks did not run'); return; }
  global.window = global; global.self = global;
  global.document = { createElementNS: () => { const img = { listeners: {}, addEventListener(k, f) { this.listeners[k] = f; }, removeEventListener() {}, set src(v) { this._src = v; setTimeout(() => this.listeners.load && this.listeners.load.call(img), 0); }, get src() { return this._src; }, width: 256, height: 256 }; return img; } };
  global.THREE = require(threePath); require('../src/vendor/gltf_loader_r128.js');
  const data = require('../tools/glb_embed.js').load(path.join(__dirname, '..'));
  t('The manifest lists the 7 kit pieces and the build embeds them', Object.keys(data.manifest.env.crimson_halls.pieces).length === 7 && Object.keys(data.files).filter((f) => /^env\//.test(f)).length === 7);
  const H = CH.create(THREE, { data, query: '?sandbox' });
  await new Promise((res) => { H.start(res); setTimeout(res, 8000); });
  t('The kit decodes with the vendored GLTFLoader', H.ready(), JSON.stringify(H.status()));
  if (!H.ready()) return;
  const K = H.forMap(map), mesh = K.build(plain.light);
  t('The whole room is ONE mesh (one draw call) with the nearest-filtered atlas, lit like the baked world', mesh.isMesh && mesh.material.type === 'MeshBasicMaterial' && mesh.material.vertexColors && mesh.material.map && mesh.material.map.magFilter === THREE.NearestFilter);
  t('It stays light for a Quest (under 20,000 triangles)', mesh.userData.tris > 2000 && mesh.userData.tris < 20000, mesh.userData.tris);
  const col = mesh.geometry.attributes.color.array; let mx = 0; for (const v of col) mx = Math.max(mx, v);
  t('It is torch-lit, not black and not blown out (vertex light 0.1-1.7)', mx > 0.5 && mx < 1.7, mx);
  mesh.geometry.computeBoundingBox(); const bb = mesh.geometry.boundingBox;
  t('It stays inside the room and under the roof', bb.min.y > -0.2 && bb.max.y <= map.WALL_H + 0.2 && bb.min.x >= (P.room.x - 1) * C - 0.1 && bb.max.x <= (P.room.x + P.room.w + 1) * C + 0.1);
  const broken = CH.create(THREE, { data: { manifest: data.manifest, files: Object.assign({}, data.files, { 'env/crimson_halls/ch_pillar.glb': Buffer.from('nope').toString('base64') }) }, query: '?sandbox' });
  const cw = console.warn; let w = 0; console.warn = () => { w++; };
  await new Promise((res) => { broken.start(res); setTimeout(res, 1500); }); console.warn = cw;
  t('A kit GLB that will not decode keeps the old walls, with a console warning', !broken.ready() && broken.forMap(map) === null && w > 0);
})().catch((e) => { fails++; console.log('FAIL threw ' + (e && e.stack || e)); }).then(() => { console.log(fails ? fails + ' failed' : 'all Crimson Halls checks passed'); process.exit(fails ? 1 : 0); });
