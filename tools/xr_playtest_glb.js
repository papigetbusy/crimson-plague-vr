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
      rec(G, 'The Service Pistol in your hand is the 1911 mesh (GLB), not the voxel pistol', g.st.on && g.st.gun === 'pistol_service' && g.body && g.tris > 1000, JSON.stringify(g).slice(0, 200));
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
      rec(G, 'Draw calls in the Crimson Halls room stay in the Quest budget (under 200 per eye) and the whole kit costs one draw per eye', calls / 2 < 200 && kitCost / 2 <= 1, (calls / 2) + ' per eye worst direction; without the kit ' + (noKit / 2) + ' (kit adds ' + (kitCost / 2) + ')');
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
  return { meshGroup };
};
