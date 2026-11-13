// Fake-Quest checks for the mesh (GLB) content on the test map: the 1911 is the Service Pistol in your hand (not the voxel one), it fires,
// reloads with its own magazine dropping, aims down sights with one sharp red dot that the shot lands on, and the start room is drawn with
// Wrok's Crimson Halls kit (one merged mesh) without blowing the Quest draw-call budget. ?voxelguns&voxelwalls brings the old look back.
module.exports = function (X) {
  const { open, rest, rec, debug, pointAt, shot } = X;
  async function meshGroup() {
    const G = 'meshes';
    let S = await open('?sandbox');
    try {
      await S.ev(() => { const r = window.__game.ref; r.clearWave(); r.equipGun('pistol_service', 1); }); await S.frames(30);
      const g = await S.ev(() => { const G = window.__game, st = G.glb(), gp = G.xr.debug(); let body = null; G.scene.traverse((o) => { if (o.name === 'glb_body' && o.parent) body = o; }); let tris = 0; if (body) body.traverse((m) => { if (m.isMesh && m.geometry.index) tris += m.geometry.index.count / 3; }); return { st, body: !!body, tris, magVisible: gp.magVisible }; });
      rec(G, 'The Service Pistol in your hand is the 1911 mesh (GLB), not the voxel pistol', g.st.on && g.st.gun === 'pistol_service' && g.body && g.tris >= 600, JSON.stringify(g).slice(0, 200));
      // the room: Crimson Halls kit present, one mesh; draw calls per eye standing in it
      const h = await S.ev(() => window.__game.halls());
      rec(G, 'The test map\'s start room is drawn with the Crimson Halls kit (walls, corners, pillars, floor, banners, sconces)', h.mesh && h.visible && ['straight', 'corner', 'pillar', 'floor', 'banner', 'sconce'].every((k) => h.pieces && h.pieces[k] > 0), JSON.stringify(h).slice(0, 220));
      await S.ev(() => { const r = window.__game.ref, m = r.map, R = m.rooms.find((q) => q.kind === 'start'), C = m.CELL; r.place((R.x + R.w / 2) * C, (R.z + R.h / 2) * C, Math.PI / 2); });
      let calls = 0, noKit = 0, kitCost = Infinity;                // worst of 4 directions, and the same views with the kit mesh hidden (what the kit itself costs)
      for (const yaw of [0, Math.PI / 2, Math.PI, -Math.PI / 2]) {
        await S.ev((y) => window.__game.ref.place(window.__game.ref.snapshot().player.x, window.__game.ref.snapshot().player.z, y), yaw); await S.frames(6);
        const c1 = await S.ev(() => window.__game.renderer.info.render.calls); calls = Math.max(calls, c1);
        const c0 = await S.ev(() => new Promise((res) => { const m = window.__game.scene.getObjectByName('crimson_halls'); m.visible = false; const f0 = window.__fx.frames; const w = () => { if (window.__fx.frames >= f0 + 2) { const c = window.__game.renderer.info.render.calls; m.visible = true; res(c); } else setTimeout(w, 10); }; w(); }));
        noKit = Math.max(noKit, c0); kitCost = Math.min(kitCost, c1 - c0);   // the least over 4 views: other things (shots, pickups) come and go between frames
      }
      X.meshCalls = calls / 2;
      rec(G, 'Draw calls in the Crimson Halls room stay in the Quest budget (under 200 per eye) and the kit costs one draw per visible 24 m block (a handful per eye)', calls / 2 < 200 && kitCost / 2 <= 8, (calls / 2) + ' per eye worst direction; without the kit ' + (noKit / 2) + ' (kit adds ' + (kitCost / 2) + ')');
      await shot(S, 'mesh_halls_room');
      // fire: the 1911 shoots from its muzzle
      await S.ev(() => window.__game.ref.place(window.__game.ref.snapshot().player.x, window.__game.ref.snapshot().player.z, Math.PI / 2)); await rest(S);
      const a0 = await S.ev(() => window.__game.ref.snapshot().player.ammo);
      await S.hold('right', 'trigger', true); await S.frames(4); await S.hold('right', 'trigger', false); await S.frames(6);
      const f = await S.ev(() => { const G = window.__game, sh = G.lastShot && G.lastShot(), gp = G.xr.debug(); return { ammo: G.ref.snapshot().player.ammo, sh: !!sh }; });
      rec(G, 'Trigger fires the 1911 (a shot goes off, one round used)', f.sh && f.ammo < a0, a0 + ' -> ' + f.ammo);
      // reload: X, its own magazine drops and a new one goes in
      const d0 = (await debug(S)).dropN; await S.press('left', 'x', 4);
      let started = false, off = 0, last = true;
      for (let n = 0; n < 400; n++) { await S.frames(1); const r = await S.ev(() => ({ rl: window.__game.ref.snapshot().player.reloading, ...window.__game.rl() })); if (r.rl) started = true; else if (started) break; if (!r.mag && last) off++; last = r.mag; }
      const d1 = (await debug(S)).dropN, a1 = await S.ev(() => { const p = window.__game.ref.snapshot().player; return [p.ammo, p.magSize]; });
      rec(G, 'X reloads the 1911: its magazine drops out and a full one goes in', started && off >= 1 && d1 > d0 && a1[0] === a1[1], 'mag off ' + off + ', drops ' + (d1 - d0) + ', ammo ' + a1.join('/'));
      // ADS: one sharp red dot, on the fire ray, and the shot lands on it
      await S.ev(() => { const r = window.__game.ref, O = window.__pt.openSpot(4, null) || window.__pt.openSpot(3, null); r.clearWave(); r.setCfg({ spread: 0, spreadAds: 0 }); r.place(O[0], O[1], Math.PI / 2); }); await rest(S);   // an open spot, so nothing sits on the edge of the aim line
      const tgt = await S.ev(() => { const p = window.__game.ref.snapshot().player; return [p.x + 10, p.eye, p.z]; });
      await pointAt(S, 'right', tgt); await S.hold('left', 'trigger', true); await S.frames(45);
      const dots = await S.ev(() => {          // every visible red-dot-like thing near the gun or on the fire ray: on-gun dot cubes / glow, the fire-ray sprite
        const G = window.__game, V = G.THREE.Vector3, d = G.xr.feel().dot, cam = G.camera.getWorldPosition(new V()), at = d ? new V(d[0], d[1], d[2]) : null, list = [];
        G.scene.traverse((o) => { if (!o.visible || !o.material || !o.material.color) return; for (let p = o; p; p = p.parent) if (!p.visible) return;
          const c = o.material.color, red = c.r > 0.9 && c.g < 0.3 && c.b < 0.3, w = o.getWorldPosition(new V()), near = w.distanceTo(cam) < 1.5 || (at && w.distanceTo(at) < 0.5);
          const isDot = (o.isSprite && (red || (o.material.map && o.material.map.image && o.material.map.image.width === 128))) || (o.isMesh && o.geometry.type === 'BoxGeometry' && o.geometry.parameters.width < 0.01 && (red || c.g > 0.9));
          if (isDot && near) list.push(o.type + (o.isSprite ? ' ' + o.scale.x.toFixed(3) : '')); });
        return { n: list.length, list, ads: G.ref.snapshot().player.adsT, dot: d };
      });
      await shot(S, 'mesh_1911_ads');
      await S.hold('right', 'trigger', true); await S.frames(3); await S.hold('right', 'trigger', false); await S.frames(2);
      const r = await S.ev(() => { const G = window.__game, sh = G.lastShot(), d = G.xr.feel().dot; if (!sh || !d) return { ok: false }; const V = G.THREE.Vector3, o = new V(sh.ox, sh.oy, sh.oz), e = new V(sh.ex, sh.ey, sh.ez), dir = e.clone().sub(o).normalize(), q = new V(d[0], d[1], d[2]).sub(o), err = q.clone().sub(dir.clone().multiplyScalar(q.dot(dir))).length();   // how far the dot is off the shot's line (along-the-line depth on a grazing wall does not matter to the eye)
        return { ok: err <= 0.06 + 0.01 * (sh.t || 10), err, hit: sh.hit, t: sh.t, o: [sh.ox, sh.oy, sh.oz].map((v) => +v.toFixed(2)), e: [sh.ex, sh.ey, sh.ez].map((v) => +v.toFixed(2)), d: d.map((v) => +v.toFixed(2)), mons: G.ref.snapshot().monsters.length }; });
      await S.hold('left', 'trigger', false);
      rec(G, 'ADS with the 1911 shows exactly one red dot (the sharp one on the fire ray; the old on-gun dot stays hidden)', dots.ads > 0.9 && dots.n === 1 && !!dots.dot, JSON.stringify(dots));
      rec(G, 'The 1911 shot lands on the red dot at 10 m (the dot sits on the shot line)', !!r.ok, r.err !== undefined ? 'err ' + r.err.toFixed(3) + ' m' + (r.ok ? '' : ' ' + JSON.stringify(r)) : 'no shot/dot');
      await S.ev(() => { const r = window.__game.ref; r.setCfg({ spread: r.defaults.spread, spreadAds: r.defaults.spreadAds }); });
      const errs = await S.ev(() => window.__fx.errors.slice(0, 3));
      rec(G, 'No script errors with the mesh gun and walls', errs.length === 0, errs.join(' | ').slice(0, 200));
    } finally { await S.close(); }
    // the old look on request
    S = await open('?sandbox&voxelguns&voxelwalls');
    try {
      await S.ev(() => window.__game.ref.equipGun('pistol_service', 1)); await S.frames(20);
      const o = await S.ev(() => ({ g: window.__game.glb(), h: window.__game.halls() }));
      rec(G, '?voxelguns&voxelwalls brings back the voxel pistol and the old walls', !o.g.on && o.g.forced && !o.h.mesh, JSON.stringify(o).slice(0, 200));
    } finally { await S.close(); }
  }
  // the real game in VR, no test map and no shortcuts in the game: pick a class with the laser, enter the hall, and fight wave after wave
  // until the first boss is out. The harness plays (test-only): it walks up to the nearest monster (a teleport), points the gun hand at it and
  // pulls the trigger, reloads with X, takes a level-up card with the laser, and backs off to the start when hurt. The game rules are untouched.
  async function bossGroup(clickTile) {
    const G = 'boss';
    const S = await open('');
    try {
      if (await S.ev(() => window.__game.xr.menuShown() && !window.__game.running())) { await clickTile(S, '^Witch'); await clickTile(S, 'ENTER THE HALL', { wait: 30 }); }
      if (!(await S.ev(() => window.__game.running()))) await S.ev(() => window.__game.begin && window.__game.begin(true));
      const t0 = Date.now(); let boss = null, deaths = 0, lv = 0, maxWave = 0, steps = 0;
      const LIM = +(process.env.BOSS_MIN || 30) * 60 * 1000;
      while (Date.now() - t0 < LIM) {
        steps++;
        const st = await S.ev(() => { const s = window.__game.ref.snapshot(), p = s.player; const ms = s.monsters.filter((m) => m.hp > 0); let n = null, d = 1e9; for (const m of ms) { const dd = Math.hypot(m.x - p.x, m.z - p.z); if (dd < d) { d = dd; n = m; } }
          return { wave: s.wave.n, phase: s.wave.phase, bossOn: !!s.bossBar, kills: s.kills, lvl: s.level, bossName: s.bossBar && s.bossBar.name, over: !!s.over, hp: p.hp, max: p.maxHp, ammo: p.ammo, rl: p.reloading, n: n && { x: n.x, z: n.z, y: 1.0 * (n.scale || 1) }, d, menu: window.__game.xr.menuShown() && window.__game.xr.debug().menuId, start: window.__game.ref.map.start }; });
        maxWave = Math.max(maxWave, st.wave);
        if (process.env.BOSS_LOG && steps % 15 === 1) console.log('  boss step', steps, JSON.stringify(st), JSON.stringify(await S.ev(() => { const l = window.__game.lastShot(); return l && { hit: l.hit, t: l.t }; })));
        if (st.bossOn) { boss = st; break; }
        if (st.over) { deaths++; if (deaths > 2) break; await S.ev(() => { const b = document.getElementById('restart'); if (b) b.click(); }); await S.frames(30); continue; }
        if (st.menu === 'levelup') { const r = await X.clearLevelUps(S); lv += r.n; continue; }
        if (st.menu) { await S.press('left', 'y', 3); await S.frames(10); continue; }
        if (!st.n) { await S.frames(20); continue; }
        if (st.ammo <= 0 && !st.rl) { await S.press('left', 'x', 4); await S.frames(20); continue; }
        const aim = await S.ev(() => {        // kite like a player would: keep 5-9 m from the pack with a clear line to the nearest monster
          const r = window.__game.ref, s = r.snapshot(), p = s.player, m = r.map, C = m.CELL, open = (x, z) => { const row = m.rows[Math.floor(z / C)]; return !!row && '.c'.includes(row[Math.floor(x / C)] || '#'); };
          const ms = s.monsters.filter((q) => q.hp > 0); if (!ms.length) return null;
          const clear = (ax, az, bx, bz) => { const L = Math.hypot(bx - ax, bz - az), n = Math.ceil(L / 0.5); for (let i = 1; i < n; i++) if (!open(ax + (bx - ax) * i / n, az + (bz - az) * i / n)) return false; return true; };
          const near = (x, z) => ms.reduce((a, q) => Math.min(a, Math.hypot(q.x - x, q.z - z)), 1e9);
          let t = ms.reduce((a, q) => (Math.hypot(q.x - p.x, q.z - p.z) < Math.hypot(a.x - p.x, a.z - p.z) ? q : a));
          const dn = near(p.x, p.z), dt = Math.hypot(t.x - p.x, t.z - p.z);
          if (dn < 4.5 || dt > 10 || !clear(p.x, p.z, t.x, t.z)) {
            let best = null, bs = -1e9;
            for (let k = 0; k < 16; k++) for (const R of [6, 7.5, 9]) { const a = k / 16 * Math.PI * 2, x = t.x + Math.cos(a) * R, z = t.z + Math.sin(a) * R;
              if (!open(x, z) || !open(x + 0.6, z) || !open(x - 0.6, z) || !open(x, z + 0.6) || !open(x, z - 0.6) || !clear(x, z, t.x, t.z)) continue;
              const sc = Math.min(near(x, z), 8) - 0.05 * Math.hypot(x - p.x, z - p.z); if (sc > bs) { bs = sc; best = [x, z]; } }
            if (best) r.place(best[0], best[1], Math.atan2(t.x - best[0], -(t.z - best[1])));
          }
          return [t.x, 0.95 * (t.scale || 1), t.z];
        });
        if (!aim) { await S.frames(10); continue; }
        await pointAt(S, 'right', aim); for (let k = 0; k < 3; k++) { await S.hold('right', 'trigger', true); await S.frames(4); await S.hold('right', 'trigger', false); await S.frames(3); }   // a few pulls per look (semi-auto)
      }
      const why = { maxWave, deaths, lv, steps, minutes: ((Date.now() - t0) / 60000).toFixed(1) };
      rec(G, 'Real game in VR: normal waves and level-ups lead to the first boss (harness plays, the game is unchanged)', !!boss, boss ? 'boss on wave ' + boss.wave + (boss.bossName ? ' (' + boss.bossName + ')' : '') + '; ' + JSON.stringify(why) : JSON.stringify(why));
      if (boss) { await S.frames(30); await shot(S, 'boss_first'); }
      const errs = await S.ev(() => window.__fx.errors.slice(0, 3));
      rec(G, 'No script errors on the way to the boss', errs.length === 0, errs.join(' | ').slice(0, 200));
    } finally { await S.close(); }
  }
  return { meshGroup, bossGroup };
};
