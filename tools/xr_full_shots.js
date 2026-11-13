// The real game in VR (no test map): screenshots of a hall in the Crimson Halls kit, the 1911 in hand (steel sheen), a menu panel, and the
// draw calls / triangles / frame time on floor 1 and on the biggest floors (140 x 140 cells; drawn with __game.viewFloor, a tools-only hook).
// Run: NODE_PATH=/workspace/xrsim/node_modules node tools/xr_full_shots.js outdir
const { launch, quatYawPitch } = require('./xr_sim.js');
const fs = require('fs'), root = require('path').join(__dirname, '..'), out = process.argv[2] || '/tmp/full_shots';
fs.mkdirSync(out, { recursive: true });
(async () => {
  const S = await launch({ root, page: 'site/index.html', query: process.argv[3] || '' });
  await S.enterVR(); await S.head({ p: [0, 0, 0], q: [0, 0, 0, 1] }); await S.frames(30);
  await S.ev(() => { const b = document.getElementById('play'); if (b) b.click(); }); await S.frames(40);
  await S.ev(() => window.__game.begin && !window.__game.running() && window.__game.begin(true)); await S.frames(30);
  console.log('halls', JSON.stringify(await S.ev(() => window.__game.halls())), 'gun', JSON.stringify(await S.ev(() => window.__game.glb())));
  const spot = (r) => S.ev((r) => { const m = window.__game.ref.map, C = m.CELL, ok = (x, z) => m.rows[z] && '.c'.includes(m.rows[z][x]); const out = [];
    for (let z = r; z < m.H - r; z += 3) for (let x = r; x < m.W - r; x += 3) { let g = true; for (let d = -r; d <= r && g; d++) if (!ok(x + d, z) || !ok(x, z + d)) g = false; if (g) out.push([(x + 0.5) * C, (z + 0.5) * C]); } return out; }, r);
  const S1 = await spot(3);
  const p0 = S1[Math.floor(S1.length / 3)] || S1[0];
  await S.ev((p) => { const r = window.__game.ref; r.place(p[0], p[1], 0.6); window.__game.xr.faceYaw && window.__game.xr.faceYaw(0.6); }, p0); await S.frames(30);
  await S.hand('right', { p: [0.2, -0.35, -0.3], q: quatYawPitch(0, 0) }); await S.frames(10); await S.shot(out + '/full_hall.png');
  await S.hand('right', { p: [0.02, -0.05, -0.28], q: quatYawPitch(1.2, -0.05) }); await S.frames(15); await S.shot(out + '/full_1911_side.png');
  await S.hand('right', { p: [0.04, -0.08, -0.3], q: quatYawPitch(0.6, -0.25) }); await S.frames(15); await S.shot(out + '/full_1911_three.png');
  await S.hand('right', { p: [0.2, -0.35, -0.3], q: quatYawPitch(0, 0) });
  await S.press('left', 'y', 3); await S.frames(40); await S.shot(out + '/full_pause_menu.png');
  const url = await S.ev(() => window.__game.xr.menuCanvas().toDataURL('image/png')); fs.writeFileSync(out + '/full_pause_menu_vrpanel.png', Buffer.from(url.split(',')[1], 'base64'));
  await S.press('left', 'y', 3); await S.frames(20);
  // draw calls and frame time: floor 1 as it is, then the biggest floors
  const perf = [];
  async function measure(tag) {
    const spots = (await spot(2)).filter((_, i, a) => i % Math.max(1, Math.floor(a.length / 10)) === 0).slice(0, 10); let worst = { calls: 0 };
    await S.ev(() => window.__game.perfReset());
    for (const p of spots) for (const yaw of [0, Math.PI / 2, Math.PI, -Math.PI / 2]) {
      await S.ev((a) => { const r = window.__game.ref; r.place(a[0], a[1], a[2]); window.__game.xr.faceYaw && window.__game.xr.faceYaw(a[2]); }, [p[0], p[1], yaw]); await S.frames(3);
      const f = await S.ev(() => { const ri = window.__game.renderer.info.render; return { calls: ri.calls / 2, tris: ri.triangles / 2 }; }); if (f.calls > worst.calls) worst = f;
    }
    const pf = await S.ev(() => { const p = window.__game.perf(); return { draw: (p.ms.draw || 0) / p.frames, view: (p.ms.view || 0) / p.frames, n: p.frames }; });
    perf.push({ tag, spots: spots.length, worstPerEye: worst, simDrawMs: +pf.draw.toFixed(2), simViewMs: +pf.view.toFixed(2), halls: await S.ev(() => { const h = window.__game.halls(); return { blocks: h.blocks, tris: h.tris }; }) });
  }
  await measure('floor 1 (the game)');
  for (const n of [7, 10]) { await S.ev((n) => window.__game.viewFloor(n, 11 + n), n); await S.ev((n) => { const m = window.__game.ref.map; }, n); await S.frames(10);
    // the rules still run floor 1, so stand where the drawn floor is open: use the drawn map for the spots
    await S.ev(() => {}); perf.push(await (async () => { const m2 = await S.ev((n) => { const m = window.__game.viewFloor(n, 11 + n); window.__vf = m; return { W: m.W, H: m.H }; }, n); return { tag: 'floor ' + n + ' map ' + m2.W + 'x' + m2.H }; })());
    const spotsB = await S.ev(() => { const m = window.__vf, C = m.CELL, ok = (x, z) => m.rows[z] && '.c'.includes(m.rows[z][x]); const o = []; for (let z = 3; z < m.H - 3; z += 4) for (let x = 3; x < m.W - 3; x += 4) { let g = true; for (let d = -2; d <= 2 && g; d++) if (!ok(x + d, z) || !ok(x, z + d)) g = false; if (g) o.push([(x + 0.5) * C, (z + 0.5) * C]); } return o.filter((_, i, a) => i % Math.max(1, Math.floor(a.length / 12)) === 0).slice(0, 12); });
    let worst = { calls: 0 }; await S.ev(() => window.__game.perfReset());
    for (const p of spotsB) for (const yaw of [0, Math.PI / 2, Math.PI, -Math.PI / 2]) {
      await S.ev((a) => { window.__game.ref.place(a[0], a[1], a[2]); window.__game.xr.faceYaw && window.__game.xr.faceYaw(a[2]); }, [p[0], p[1], yaw]); await S.frames(3);
      const f = await S.ev(() => { const ri = window.__game.renderer.info.render; return { calls: ri.calls / 2, tris: ri.triangles / 2 }; }); if (f.calls > worst.calls) worst = f;
    }
    const pf = await S.ev(() => { const p = window.__game.perf(); return { draw: (p.ms.draw || 0) / p.frames, view: (p.ms.view || 0) / p.frames }; });
    Object.assign(perf[perf.length - 1], { spots: spotsB.length, worstPerEye: worst, simDrawMs: +pf.draw.toFixed(2), simViewMs: +pf.view.toFixed(2), halls: await S.ev(() => { const h = window.__game.halls(); return { blocks: h.blocks, tris: h.tris }; }) });
    if (n === 10) { const p = spotsB[Math.floor(spotsB.length / 2)]; await S.ev((a) => { window.__game.ref.place(a[0], a[1], 0.3); window.__game.xr.faceYaw && window.__game.xr.faceYaw(0.3); }, p); await S.frames(20); await S.shot(out + '/full_floor10_hall.png'); }
  }
  console.log('perf', JSON.stringify(perf, null, 1));
  console.log('errors', JSON.stringify(await S.ev(() => window.__fx.errors.slice(0, 3))), 'logs', JSON.stringify(S.logs.slice(0, 4)));
  await S.close();
})().catch((e) => { console.error(e); process.exit(1); });
