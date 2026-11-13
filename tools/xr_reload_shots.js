// Screenshots of the VR reload on each gun type, and the hold-X inspect. Run: NODE_PATH=/workspace/xrsim/node_modules node tools/xr_reload_shots.js outdir
const { launch } = require('./xr_sim.js');
const root = require('path').join(__dirname, '..'), out = process.argv[2] || '/tmp/reload_shots';
require('fs').mkdirSync(out, { recursive: true });
(async () => {
  const S = await launch({ root, page: 'site/index.html', query: '?sandbox', port: 9300 + Math.floor(Math.random() * 300) });
  await S.enterVR();
  await S.head({ p: [0, 0, 0], q: [0, 0, 0, 1] });
  await S.hand('left', { p: [-0.25, -0.5, -0.2], q: [0, 0, 0, 1] });
  await S.hand('right', { p: [0.14, -0.26, -0.5], q: [0, 0, 0, 1] });
  await S.frames(10);
  await S.ev(() => { const G = window.__game, r = G.ref; r.clearWave(); const m = r.map, C = m.CELL; for (let z = 4; z < m.H - 4; z++) for (let x = 4; x < m.W - 4; x++) { let ok = true; for (let dz = -3; dz <= 3 && ok; dz++) for (let dx = -3; dx <= 3; dx++) if (!'.c'.includes(m.rows[z + dz][x + dx])) { ok = false; break; } if (ok) { r.place((x + 0.5) * C, (z + 0.5) * C, Math.PI / 2); if (G.xr.faceYaw) G.xr.faceYaw(Math.PI / 2); return; } } }); await S.frames(5);
  for (const id of ['rifle', 'shotgun_pump', 'sniper_bolt']) {
    await S.ev((id) => window.__game.ref.equipGun(id, 1), id); await S.frames(40);
    await S.hold('right', 'trigger', true); await S.frames(id === 'rifle' ? 8 : 3); await S.hold('right', 'trigger', false); await S.frames(id === 'sniper_bolt' ? 40 : 20);
    await S.press('left', 'x', 4);
    let n = 0, k = 0;
    for (; n < 400; n++) {
      await S.frames(1);
      const r = await S.ev(() => { const p = window.__game.ref.snapshot().player; return { rl: p.reloading, k: p.reloadK, ...window.__game.rl() }; });
      if (!r.rl && n > 5) break;
      if (r.rl && r.k >= [0.2, 0.4, 0.6, 0.85][k]) { await S.shot(out + '/' + id + '_' + k + '_k' + r.k.toFixed(2) + (r.mag ? '' : '_magout') + (r.shell ? '_shell' : '') + '.png'); k++; if (k > 3) k = 3.5; }
    }
  }
  await S.ev(() => window.__game.ref.equipGun('rifle', 1)); await S.frames(30);
  await S.hold('left', 'x', true);
  for (let i = 0; i < 160; i++) { await S.frames(1); if (i === 100 || i === 140) await S.shot(out + '/inspect_' + i + '.png'); }
  await S.hold('left', 'x', false);
  await S.close();
})().catch((e) => { console.error(e); process.exit(1); });
