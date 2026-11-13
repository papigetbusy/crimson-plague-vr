// Tonight's playtest shots: the 1911, AK, MP5, Uzi and M4 in the VR hand, and v2 Crimson Halls walls on two floors.
// Run: NODE_PATH=/workspace/xrsim/node_modules node tools/xr_tonight_shots.js /workspace/fp_shots/tonight
const { launch, quatYawPitch } = require('./xr_sim.js');
const fs = require('fs'), root = require('path').join(__dirname, '..'), out = process.argv[2] || '/workspace/fp_shots/tonight';
fs.mkdirSync(out, { recursive: true });
const GUNS = [
  ['pistol_service', '1911'],
  ['rifle', 'ak'],
  ['smg_tactical', 'mp5'],
  ['smg_compact', 'uzi'],
  ['rifle_m4', 'm4'],
];
const poses = [
  ['side', [0.0, -0.08, -0.32], quatYawPitch(1.35, 0)],
  ['threequarter', [0.04, -0.1, -0.3], quatYawPitch(0.7, -0.15)],
];
async function waitReady(S, ms) {
  const t0 = Date.now();
  while (Date.now() - t0 < (ms || 8000)) {
    const st = await S.ev(() => ({ w: window.__game.walltex && window.__game.walltex(), h: window.__game.halls && window.__game.halls(), g: window.__game.glb && window.__game.glb() }));
    if (st.w && st.w.ready && st.h && st.h.ready && st.g && st.g.ready && st.g.ready.length >= 5) return st;
    await S.frames(10);
  }
  return S.ev(() => ({ w: window.__game.walltex && window.__game.walltex(), h: window.__game.halls && window.__game.halls(), g: window.__game.glb && window.__game.glb() }));
}
(async () => {
  const S = await launch({ root, page: 'site/index.html', query: '?sandbox' });
  await S.enterVR(); await S.head({ p: [0, 0, 0], q: [0, 0, 0, 1] });
  const ready = await waitReady(S, 10000);
  console.log('ready', JSON.stringify(ready));
  await S.ev(() => { const r = window.__game.ref; r.clearWave(); const m = r.map, R = m.rooms.find((q) => q.kind === 'start'), C = m.CELL; r.place((R.x + R.w / 2) * C, (R.z + R.h / 2) * C, Math.PI / 2); if (window.__game.xr.faceYaw) window.__game.xr.faceYaw(Math.PI / 2); });
  await S.frames(20);
  const gunStatus = {};
  for (const [id, tag] of GUNS) {
    await S.ev((id) => window.__game.ref.equipGun(id, 0), id); await S.frames(25);
    const st = await S.ev(() => window.__game.glb());
    gunStatus[id] = { on: st.on, gun: st.gun, file: st.ready && st.ready.includes(id), ready: st.ready };
    for (const [n, p, q] of poses) { await S.hand('right', { p, q }); await S.frames(18); await S.shot(out + '/gun_' + tag + '_' + n + '.png'); }
  }
  console.log('guns', JSON.stringify(gunStatus));
  // Crypt halls (sandbox start room, floor 1)
  await S.ev(() => { const r = window.__game.ref, m = r.map, R = m.rooms.find((q) => q.kind === 'start'), C = m.CELL; r.place((R.x + 1.5) * C, (R.z + 1.5) * C, Math.atan2(-1, -1) + Math.PI); if (window.__game.xr.faceYaw) window.__game.xr.faceYaw(Math.atan2(-1, -1) + Math.PI); });
  await S.hand('right', { p: [0.18, -0.28, -0.4], q: quatYawPitch(0, 0) }); await S.frames(20);
  const crypt = await S.ev(() => ({ halls: window.__game.halls(), walltex: window.__game.walltex(), floor: window.__game.ref.snapshot().floor }));
  await S.shot(out + '/walls_crypt_floor1.png');
  console.log('crypt', JSON.stringify(crypt));
  // Blood Catacombs (floor 2) via the tools hook
  const blood = await S.ev(() => { const m = window.__game.viewFloor(2, 13); window.__vf = m; return { W: m.W, H: m.H, halls: window.__game.halls(), walltex: window.__game.walltex() }; });
  const spot = await S.ev(() => { const m = window.__vf, C = m.CELL, ok = (x, z) => m.rows[z] && '.c'.includes(m.rows[z][x]);
    for (let z = 4; z < m.H - 4; z++) for (let x = 4; x < m.W - 4; x++) { let g = true; for (let d = -2; d <= 2 && g; d++) if (!ok(x + d, z) || !ok(x, z + d)) g = false; if (g) return [(x + 0.5) * C, (z + 0.5) * C]; } return [10, 10]; });
  await S.ev((a) => { window.__game.ref.place(a[0], a[1], 0.4); if (window.__game.xr.faceYaw) window.__game.xr.faceYaw(0.4); }, spot); await S.frames(25);
  await S.shot(out + '/walls_blood_floor2.png');
  console.log('blood', JSON.stringify(blood), 'spot', spot, 'logs', JSON.stringify(S.logs.slice(0, 8)));
  await S.close();
  console.log('shots in ' + out);
})().catch((e) => { console.error(e); process.exit(1); });
