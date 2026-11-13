// Screenshots of the test map's Crimson Halls room (Wrok's wall kit) and the 1911 in the VR hand, with the draw calls per eye.
// Run: NODE_PATH=/workspace/xrsim/node_modules node tools/xr_halls_shots.js outdir [extra query]
const { launch, quatYawPitch } = require('./xr_sim.js');
const fs = require('fs'), root = require('path').join(__dirname, '..'), out = process.argv[2] || '/tmp/halls_shots', extra = process.argv[3] || '';
fs.mkdirSync(out, { recursive: true });
(async () => {
  const S = await launch({ root, page: 'site/index.html', query: '?sandbox' + extra });
  await S.enterVR(); await S.head({ p: [0, 0, 0], q: [0, 0, 0, 1] }); await S.frames(20);
  const info = await S.ev(() => window.__game.halls());
  console.log('halls', JSON.stringify(info));
  const room = await S.ev(() => { const r = window.__game.ref, m = r.map, R = m.rooms.find((q) => q.kind === 'start'), C = m.CELL; r.clearWave(); r.equipGun('pistol_service', 0); return { R, C, W: m.W }; });
  const { R, C } = room;
  const views = [['room_corner', (R.x + 1.5) * C, (R.z + 1.5) * C, Math.atan2(-1, -1) + Math.PI], ['room_center', (R.x + R.w / 2) * C, (R.z + R.h / 2) * C, 0], ['room_back', (R.x + R.w - 1.5) * C, (R.z + R.h - 1.5) * C, Math.atan2(-1, -1)]];
  const calls = [];
  for (const [n, x, z, yaw] of views) {
    await S.ev((a) => { const r = window.__game.ref; r.place(a[0], a[1], a[2]); if (window.__game.xr.faceYaw) window.__game.xr.faceYaw(a[2]); }, [x, z, yaw]); await S.frames(20);
    await S.hand('right', { p: [0.12, -0.2, -0.38], q: quatYawPitch(0, 0) }); await S.frames(10);
    calls.push(await S.ev(() => window.__game.renderer.info.render.calls)); await S.shot(out + '/halls_' + n + '.png');
  }
  await S.hand('right', { p: [0.02, -0.08, -0.3], q: quatYawPitch(0.9, -0.1) }); await S.frames(20); await S.shot(out + '/vr_1911_hand.png');
  await S.hand('right', { p: [0.06, -0.06, -0.3], q: [0, 0, 0, 1] }); await S.hold('left', 'trigger', true); await S.frames(40); await S.shot(out + '/vr_1911_ads.png'); await S.hold('left', 'trigger', false);
  console.log('draw calls (both eyes, one frame) per view', JSON.stringify(calls), 'glb', JSON.stringify(await S.ev(() => window.__game.glb())), 'logs', JSON.stringify(S.logs.slice(0, 5)));
  await S.close();
})().catch((e) => { console.error(e); process.exit(1); });
