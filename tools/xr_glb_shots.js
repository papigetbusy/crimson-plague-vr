// Screenshots of the mesh (GLB) Service Pistol: in the VR hand (side, three-quarter, aiming, reload with the magazine out, slide locked back) and
// on a flat screen, plus the old voxel pistol (?voxelguns) to compare. Run: NODE_PATH=/workspace/xrsim/node_modules node tools/xr_glb_shots.js outdir
const { launch, quatYawPitch } = require('./xr_sim.js');
const fs = require('fs'), root = require('path').join(__dirname, '..'), out = process.argv[2] || '/tmp/glb_shots';
fs.mkdirSync(out, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const clearSpot = () => { const G = window.__game, r = G.ref; r.clearWave(); const m = r.map, C = m.CELL; for (let z = 4; z < m.H - 4; z++) for (let x = 4; x < m.W - 4; x++) { let ok = true; for (let dz = -3; dz <= 3 && ok; dz++) for (let dx = -3; dx <= 3; dx++) if (!'.c'.includes(m.rows[z + dz][x + dx])) { ok = false; break; } if (ok) { r.place((x + 0.5) * C, (z + 0.5) * C, Math.PI / 2); if (G.xr.faceYaw) G.xr.faceYaw(Math.PI / 2); return; } } };
async function vr(query, tag) {
  const S = await launch({ root, page: 'site/index.html', query });
  await S.enterVR();
  await S.head({ p: [0, 0, 0], q: [0, 0, 0, 1] });
  await S.hand('left', { p: [-0.25, -0.6, -0.1], q: [0, 0, 0, 1] });
  await S.ev(clearSpot); await S.ev(() => window.__game.ref.equipGun('pistol_service', 0)); await S.frames(30);
  const glb = await S.ev(() => window.__game.glb());
  const poses = [['side', [0.0, -0.08, -0.32], quatYawPitch(1.35, 0)], ['threequarter', [0.04, -0.1, -0.3], quatYawPitch(0.7, -0.15)], ['hip', [0.14, -0.26, -0.42], quatYawPitch(0, 0)]];
  for (const [n, p, q] of poses) { await S.hand('right', { p, q }); await S.frames(25); await S.shot(out + '/vr_' + tag + '_' + n + '.png'); }
  // aim down sights (left trigger) with the hand ahead of the face
  await S.hand('right', { p: [0.06, -0.08, -0.35], q: [0, 0, 0, 1] }); await S.hold('left', 'trigger', true); await S.frames(40);
  await S.shot(out + '/vr_' + tag + '_ads.png'); await S.hold('left', 'trigger', false); await S.frames(15);
  // empty the magazine: the slide locks back; then reload (X) with the gun side-on, catching the magazine out
  await S.hand('right', { p: [0.0, -0.08, -0.32], q: quatYawPitch(1.35, 0) }); await S.frames(10);
  await S.ev(() => { const r = window.__game.ref; if (r.setAmmo) r.setAmmo(0); }); 
  for (let i = 0; i < 40; i++) { const a = await S.ev(() => window.__game.ref.snapshot().player.ammo); if (a <= 0) break; await S.hold('right', 'trigger', true); await S.frames(4); await S.hold('right', 'trigger', false); await S.frames(6); }
  await S.frames(20); await S.shot(out + '/vr_' + tag + '_empty_slide.png');
  await S.press('left', 'x', 4);
  let magOut = false;
  for (let n = 0; n < 300; n++) { await S.frames(1); const r = await S.ev(() => ({ rl: window.__game.ref.snapshot().player.reloading, ...window.__game.rl() })); if (r.rl && !r.mag && !magOut) { magOut = true; await S.frames(3); await S.shot(out + '/vr_' + tag + '_reload_magout.png'); } if (!r.rl && n > 5) break; }
  await S.close();
  return glb;
}
async function flat(query, tag) {
  const S = await launch({ root, page: 'site/index.html', query });
  await sleep(1500); await S.ev(() => window.__game.begin && window.__game.begin()); await sleep(800);
  await S.ev(clearSpot); await S.ev(() => window.__game.ref.equipGun('pistol_service', 0)); await sleep(2500);
  await S.shot(out + '/flat_' + tag + '.png');
  await S.close();
}
(async () => {
  console.log('glb', JSON.stringify(await vr('?sandbox', 'glb')));
  await vr('?sandbox&voxelguns', 'voxel');
  await flat('?sandbox', 'glb'); await flat('?sandbox&voxelguns', 'voxel');
  console.log('shots in ' + out);
})().catch((e) => { console.error(e); process.exit(1); });
