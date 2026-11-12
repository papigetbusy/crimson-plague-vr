// Full simulated Quest 3 playtest: every pickup, door and button in the VR build, driven through the fake headset.
// Run: NODE_PATH=/workspace/xrsim/node_modules node tools/xr_playtest.js [page=site/index.html] [--md out.md] [--shots dir] [--only=pickup,doors,controls]
// Each check prints PASS/FAIL with what was seen. Exit code 1 when anything fails.
const { launch } = require('./xr_sim.js');
const args = process.argv.slice(2), page = args.find((a) => /\.html$/.test(a)) || 'site/index.html';
const mdOut = args.includes('--md') ? args[args.indexOf('--md') + 1] : null, shots = args.includes('--shots') ? args[args.indexOf('--shots') + 1] : null;
const root = require('path').join(__dirname, '..');
const results = [];
const rec = (group, name, pass, detail) => { results.push({ group, name, pass: !!pass, detail: detail || '' }); console.log((pass ? 'PASS ' : 'FAIL ') + '[' + group + '] ' + name + (detail ? '  -- ' + detail : '')); };
const REST = { right: [0.18, -0.42, -0.32], left: [-0.18, -0.42, -0.32] };
const HELPERS = () => {
  const G = window.__game, T = G.THREE;
  const rig = () => { const r = G.xr.rig; r.updateMatrixWorld(true); return r; };
  const toLocal = (x, y, z) => { const v = new T.Vector3(x, y, z); rig().worldToLocal(v); return [v.x, v.y, v.z]; };
  const look = (from, toW) => { const t = toLocal(toW[0], toW[1], toW[2]); const d = new T.Vector3(t[0] - from[0], t[1] - from[1], t[2] - from[2]).normalize(); const q = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 0, -1), d); return [q.x, q.y, q.z, q.w]; };
  const menuMesh = () => { let m = null; rig().traverse((o) => { if (o.isMesh && o.renderOrder === 1001 && o.geometry && o.geometry.type === 'PlaneGeometry' && o.visible) m = o; }); return m; };
  const menuPoint = (u, v) => { const m = menuMesh(); if (!m) return null; const p = new T.Vector3(u - 0.5, v - 0.5, 0); m.updateMatrixWorld(true); m.localToWorld(p); return [p.x, p.y, p.z]; };
  const menuFind = (re) => { const r = new RegExp(re, 'i'); for (let v = 0.97; v > 0.02; v -= 0.015) for (let u = 0.03; u < 0.98; u += 0.015) { const t = G.xr.menuHit(u, v); if (t && r.test(t)) return [u, v, t]; } return null; };
  const titles = () => { const s = new Set(); for (let v = 0.97; v > 0.02; v -= 0.03) for (let u = 0.03; u < 0.98; u += 0.03) { const t = G.xr.menuHit(u, v); if (t) s.add(t); } return [...s]; };
  // an open spot: a floor cell whose neighbours within r cells are all floor, at least 10 m from `avoid`
  const openSpot = (r, avoid) => { const m = G.ref.map, C = m.CELL; const ok = (ch) => ch === '.' || ch === 'c';
    for (let z = r + 1; z < m.H - r - 1; z++) for (let x = r + 1; x < m.W - r - 1; x++) { let good = true; for (let dz = -r; dz <= r && good; dz++) for (let dx = -r; dx <= r; dx++) if (!ok(m.rows[z + dz][x + dx])) { good = false; break; } if (!good) continue; const wx = (x + 0.5) * C, wz = (z + 0.5) * C; if (avoid && Math.hypot(wx - avoid[0], wz - avoid[1]) < 10) continue; return [wx, wz]; }
    return null; };
  const st = () => G.ref.snapshot();
  const grabbable = () => st().pickups.filter((p) => p.kind === 'gun' || p.kind === 'gear' || p.kind === 'mod');
  const place0 = G.ref.place; G.ref.place = (x, z, yaw) => { place0(x, z, yaw); if (yaw !== undefined && G.xr.faceYaw) G.xr.faceYaw(yaw); };   // a teleport also turns the VR body (the harness only)
  // stand k metres in front of the door on the side you can walk (the map's door normal does not always point into the room), facing it
  const atDoor = (k) => { const m = G.ref.map, d = m.door, C = m.CELL; for (const sg of [1, -1]) { const x = d.x + d.nx * k * sg, z = d.z + d.nz * k * sg, r = m.rows[Math.floor(z / C)], ch = r && r[Math.floor(x / C)]; if (ch === '.' || ch === 'c') { const y = Math.atan2(-d.nx * sg, d.nz * sg); G.ref.place(x, z, y); return { x: d.x, z: d.z }; } } return null; };
  window.__pt = { atDoor, toLocal, look, menuMesh, menuPoint, menuFind, titles, openSpot, st, grabbable };
};
async function open(query) {
  const S = await launch({ root, page, query, port: 8765 + Math.floor(Math.random() * 500) });
  await S.page.evaluate(HELPERS);
  await S.enterVR();
  await rest(S);
  return S;
}
async function rest(S) { await S.hand('right', { p: REST.right, q: [0, 0, 0, 1], ax: [0, 0, 0, 0], v: { 0: 0, 1: 0, 3: 0, 4: 0, 5: 0 } }); await S.hand('left', { p: REST.left, q: [0, 0, 0, 1], ax: [0, 0, 0, 0], v: { 0: 0, 1: 0, 3: 0, 4: 0, 5: 0 } }); await S.head({ p: [0, 0, 0], q: [0, 0, 0, 1] }); await S.frames(3); }
const held = (S) => S.ev(() => window.__game.ref.snapshot().player.gun.id);
const debug = (S) => S.ev(() => window.__game.xr.debug());
async function handTo(S, hand, world) { const p = await S.ev((w) => window.__pt.toLocal(w[0], w[1], w[2]), world); await S.hand(hand, { p, q: [-0.38, 0, 0, 0.92] }); await S.frames(3); return p; }   // reached down, pointing at the floor ahead
async function pointAt(S, hand, world) { const q = await S.ev((h, w, f) => window.__pt.look(f, w), hand, world, REST[hand]); await S.hand(hand, { p: REST[hand], q }); await S.frames(3); }
async function shot(S, name) { if (shots) await S.shot(shots + '/' + name + '.png'); }

// lay out test items in an open room: the player stands at O facing +x; items at known spots around him
async function layout(S) {
  return S.ev(() => {
    const G = window.__game, r = G.ref, s0 = r.snapshot(); const O = window.__pt.openSpot(4, [s0.player.x, s0.player.z]) || window.__pt.openSpot(3, [s0.player.x, s0.player.z]);
    if (!O) return null;
    const at = (dx, dz, fn) => { r.place(O[0] + dx, O[1] + dz); fn(); };
    const before = new Set(r.snapshot().pickups.map((p) => p.id));
    at(1.0, 1.0, () => r.giveGun('sniper_bolt', 2));     // near, front-right (reach down)
    at(1.2, -1.1, () => r.giveGun('smg_compact', 2));    // near, front-left (left hand)
    at(5.0, -1.5, () => r.giveGun('hmg_belt', 2));       // far: distance grab
    at(-1.4, 1.2, () => r.giveGear('chest', 3));         // armor, behind-right
    at(-1.4, -1.2, () => r.giveMod(2));                  // mod, behind-left
    r.place(O[0], O[1], Math.PI / 2);
    const items = r.snapshot().pickups.filter((p) => !before.has(p.id)).map((p) => ({ id: p.id, kind: p.kind, x: p.x, z: p.z, gid: p.gun && p.gun.id }));
    return { O, items };
  });
}
// level-up cards after a boss: pick each with the laser + trigger (also checks the laser on a card menu)
async function clearLevelUps(S) {
  let n = 0;
  for (let k = 0; k < 10; k++) {
    const d = await debug(S); if (!d.menu || d.menuId !== 'levelup') break;
    const t = await S.ev(() => { const ts = window.__pt.titles(); return ts.length ? window.__pt.menuFind(ts[0].replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) : null; });
    if (!t) break;
    const w = await S.ev((t) => window.__pt.menuPoint(t[0], t[1]), t); await pointAt(S, 'right', w); await S.frames(4); await S.press('right', 'trigger', 4); await S.frames(15); n++;
  }
  await rest(S);
  return { n, left: (await debug(S)).menuId === 'levelup' };
}
const exists = (S, id) => S.ev((id) => window.__game.ref.snapshot().pickups.some((p) => p.id === id), id);

async function pickupGroup() {
  const G = 'pickup';
  const S = await open('?sandbox');
  try {
    const g0 = await held(S), n0 = await S.ev(() => window.__pt.grabbable().length);
    await S.press('right', 'grip', 6); await S.frames(10);
    const g1 = await held(S), n1 = await S.ev(() => window.__pt.grabbable().length);
    rec(G, 'Right grip with your hand at your side takes a gun lying at your feet', g1 !== g0 || n1 < n0, g0 + ' -> ' + g1 + ', floor items ' + n0 + ' -> ' + n1);
    const L = await layout(S); if (!L) { rec(G, 'Test room found', false, 'no open spot'); return; }
    await S.frames(15); await S.pulses();
    const item = (gid, kind) => L.items.find((i) => (gid ? i.gid === gid : i.kind === kind));
    const sn = item('sniper_bolt');
    await handTo(S, 'right', [sn.x, 0.35, sn.z]); await S.frames(8);
    const d2 = await debug(S), pz = await S.pulses();
    rec(G, 'Reaching a hand to an item highlights it (you can see what you will grab)', d2.grab && d2.grab.right && d2.grab.right.id === sn.id, 'hover=' + JSON.stringify(d2.grab ? d2.grab.right : undefined));
    rec(G, 'A light buzz in that hand when it touches something you can grab', pz.some((p) => p.hand === 'right'), pz.length + ' pulses');
    await shot(S, 'grab_hover_near');
    await S.press('right', 'grip', 6); await S.frames(10);
    const pg = await S.pulses();
    rec(G, 'Right hand reaching down + grip takes THAT gun (sniper)', !(await exists(S, sn.id)) && (await held(S)) === 'sniper_bolt', 'held ' + (await held(S)));
    rec(G, 'A firm buzz when the grab lands', pg.some((p) => p.hand === 'right' && p.s >= 0.3), JSON.stringify(pg.slice(0, 3)));
    await rest(S);
    const sm = item('smg_compact');
    await handTo(S, 'left', [sm.x, 0.35, sm.z]); await S.frames(6);
    await S.press('left', 'grip', 6); await S.frames(10);
    rec(G, 'Left hand reaching down + left grip takes THAT gun (it lands in your gun hand)', !(await exists(S, sm.id)), 'held ' + (await held(S)));
    await rest(S);
    const hm = item('hmg_belt');
    await pointAt(S, 'right', [hm.x, 0.35, hm.z]); await S.frames(8);
    const d4 = await debug(S);
    await shot(S, 'grab_hover_far');
    rec(G, 'Pointing a hand at an item 5 m away highlights it (distance grab)', d4.grab && d4.grab.right && d4.grab.right.id === hm.id, 'hover=' + JSON.stringify(d4.grab ? d4.grab.right : undefined));
    await S.press('right', 'grip', 6); await S.frames(14);
    rec(G, 'Point + grip pulls that item from 5 m away (distance grab)', !(await exists(S, hm.id)), 'held ' + (await held(S)));
    await rest(S);
    // grip already squeezed BEFORE the armor is there (you walked up holding the grip like a gun), then the hand reaches it
    await S.hold('right', 'grip', true); await S.frames(10);
    const ge = await S.ev((O) => { const r = window.__game.ref, ids = new Set(r.snapshot().pickups.map((p) => p.id)); r.place(O[0] - 1.4, O[1] + 1.2); r.giveGear('chest', 3); r.place(O[0], O[1]); const q = r.snapshot().pickups.find((p) => !ids.has(p.id)); return { id: q.id, x: q.x, z: q.z }; }, L.O);
    await S.frames(4);
    await handTo(S, 'right', [ge.x, 0.35, ge.z]); await S.frames(25);
    const gone5 = !(await exists(S, ge.id));
    await S.hold('right', 'grip', false); await S.frames(4);
    rec(G, 'Grip already squeezed (held like a gun) and hand reaches an item: it is still taken (armor)', gone5, gone5 ? 'taken' : 'still on the floor');
    if (!gone5) { await S.press('right', 'grip', 6); await S.frames(8); rec(G, 'Armor: reach + fresh grip takes it', !(await exists(S, ge.id)), ''); }
    const ge0 = item(null, 'gear'); if (await exists(S, ge0.id)) { await rest(S); await handTo(S, 'right', [ge0.x, 0.35, ge0.z]); await S.frames(4); await S.press('right', 'grip', 6); await S.frames(8); }
    await rest(S);
    const md = item(null, 'mod');
    await handTo(S, 'right', [md.x, 0.35, md.z]); await S.frames(5);
    await S.press('right', 'grip', 6); await S.frames(8);
    rec(G, 'Gun mod: reach + grip puts it in your bag', !(await exists(S, md.id)), '');
    await rest(S);
    const fore = (await debug(S)).foreAt;
    if (fore) { await S.hand('left', { p: fore }); await S.hold('left', 'grip', true); await S.frames(10); }
    const d7 = await debug(S);
    rec(G, 'Left grip on the gun\'s fore-end = two-handed hold', d7.twoHand === true, 'twoHand=' + d7.twoHand);
    await S.hold('left', 'grip', false); await rest(S);
    // firing while pointing at a far item: no pull-from-afar highlight (nothing grabbed by accident in a fight)
    await S.ev((O) => { const r = window.__game.ref; r.giveGun('shotgun_pump', 1, 1, O[0] + 5, O[1] + 1.5); }, L.O); await S.frames(3);
    const far9 = await S.ev((O) => window.__game.ref.snapshot().pickups.find((p) => p.gun && p.gun.id === 'shotgun_pump' && Math.abs(p.x - O[0] - 5) < 0.1), L.O);
    await pointAt(S, 'right', [far9.x, 0.35, far9.z]); await S.hold('right', 'trigger', true); await S.frames(6);
    const d9 = await debug(S); await S.hold('right', 'trigger', false); await S.frames(6);
    const d9b = await debug(S);
    rec(G, 'While firing, the gun hand does not light up far items; let go and it does', !(d9.grab.right && d9.grab.right.mode === 'ray') && d9b.grab.right && d9b.grab.right.mode === 'ray', 'firing: ' + JSON.stringify(d9.grab.right) + ' / after: ' + (d9b.grab.right && d9b.grab.right.mode));
    await rest(S);
    // coins: walk over them (no button)
    const g10 = (await S.state()).gold;
    await S.ev((O) => { const r = window.__game.ref; r.spawnAt('goblin', O[0] + 1.5, O[1]); r.clearWave(); }, L.O); await S.frames(40);
    rec(G, 'Coins: walking near them picks them up by themselves', (await S.state()).gold > g10, 'gold ' + g10 + ' -> ' + (await S.state()).gold);
    const s8 = await S.state(), before8 = s8.player.gun.id, back8 = s8.player.gun.other && s8.player.gun.other.id, n8 = s8.pickups.length;
    await S.hand('right', { p: [0.16, -0.05, 0.14] }); await S.frames(4);
    await S.press('right', 'grip', 6); await S.frames(10);
    const s8b = await S.state();
    rec(G, 'Right hand over your right shoulder + grip swaps to the gun on your back (picks nothing up)', s8b.player.gun.id === back8 && s8b.pickups.length === n8, before8 + ' (back ' + back8 + ') -> ' + s8b.player.gun.id + ', floor items ' + n8 + ' -> ' + s8b.pickups.length);
    await rest(S);
  } finally { if (S.logs.length) console.log('  page log:', S.logs.slice(0, 4).join(' | ')); await S.close(); }
}

async function doorGroup() {
  const G = 'doors';
  let S = await open('');
  try {
    const gate = await S.ev(() => { const s = window.__game.ref.snapshot(); return s.locks.gates.find((g) => !g.open) || null; });
    if (!gate) { rec(G, 'A closed gold gate on floor 1', false, 'none'); } else {
      const side = await S.ev((g) => { const r = window.__game.ref; for (const s of [1, -1]) { r.place(g.x + g.nx * 2.2 * s, g.z + g.nz * 2.2 * s); if (r.snapshot().locks.near) return s; } return 1; }, gate);
      await S.ev((g, s) => { const r = window.__game.ref; r.place(g.x + g.nx * 2.2 * s, g.z + g.nz * 2.2 * s, Math.atan2(-g.nx * s, g.nz * s)); }, gate, side);
      await S.frames(6); await S.pulses();
      const gold0 = (await S.state()).gold;
      await S.press('right', 'grip', 6); await S.frames(8);
      const s2 = await S.state(), pd = await S.pulses(), dd = await debug(S);
      rec(G, 'Gold gate with too little gold stays shut, and tells you why (buzz + message)', !s2.locks.gates[gate.i].open && pd.length > 0 && /gold/i.test(JSON.stringify(dd.grab || '')), 'gold ' + gold0 + ', pulses ' + pd.length + ', hint ' + JSON.stringify(dd.grab || null).slice(0, 80));
      await S.ev(() => window.__game.ref.giveGold(300)); await S.frames(4);
      const gw = [gate.x, 1.2, gate.z];
      await pointAt(S, 'left', gw); await S.frames(6);
      const dg = await debug(S);
      rec(G, 'Gate is highlighted when you stand at it (shows the price)', dg.grab && (dg.grab.left || dg.grab.right) && /gate|toll|gold/i.test(JSON.stringify(dg.grab)), JSON.stringify(dg.grab || null).slice(0, 120));
      await shot(S, 'gate_hover');
      await S.press('left', 'grip', 6); await S.frames(8);
      let open1 = (await S.state()).locks.gates[gate.i].open; const pl = await S.pulses();
      rec(G, 'LEFT grip at the gate pays and opens it', open1, 'open=' + open1);
      if (!open1) { await S.press('right', 'grip', 6); await S.frames(8); open1 = (await S.state()).locks.gates[gate.i].open; rec(G, 'RIGHT grip at the gate pays and opens it', open1, 'open=' + open1); }
      else rec(G, 'Opening a gate gives a buzz', pl.length > 0, pl.length + ' pulses');
      await rest(S); await S.frames(20); await shot(S, 'gate_open');
      const p0 = await S.state();
      const sgn = (q) => (q.player.x - gate.x) * gate.nx + (q.player.z - gate.z) * gate.nz;
      await S.hand('left', { ax: [0, 0, 0, -1] }); await S.frames(70); await S.hand('left', { ax: [0, 0, 0, 0] });
      const p1 = await S.state();
      rec(G, 'Walk through the open gate (left stick forward)', Math.sign(sgn(p0)) !== Math.sign(sgn(p1)), 'side ' + sgn(p0).toFixed(1) + ' -> ' + sgn(p1).toFixed(1));
    }
    const door = await S.ev(() => { const m = window.__game.ref.map; return { x: m.door.x, z: m.door.z, nx: m.door.nx, nz: m.door.nz }; });
    await S.ev(() => window.__pt.atDoor(2.2)); await S.frames(6); await S.pulses();
    await pointAt(S, 'right', [door.x, 1.5, door.z]);
    await S.press('right', 'grip', 6); await S.frames(6);
    const sd = await S.state(), pd2 = await S.pulses(), dd2 = await debug(S);
    rec(G, 'Sealed boss door: grip tells you what opens it (buzz + message; it stays shut until the boss is down)', !sd.door.open && pd2.length > 0 && /boss|seal/i.test(JSON.stringify(dd2.grab || '') + JSON.stringify(sd.locks.door || '')), 'open=' + sd.door.open + ' pulses=' + pd2.length + ' hint=' + JSON.stringify((dd2.grab && (dd2.grab.right || dd2.grab.left)) || sd.locks.door || null).slice(0, 100));
    await shot(S, 'door_sealed');
  } finally { if (S.logs.length) console.log('  page log:', S.logs.slice(0, 4).join(' | ')); await S.close(); }

  S = await open('?sandbox');
  try {
    const door = await S.ev(() => { const m = window.__game.ref.map; return { x: m.door.x, z: m.door.z, nx: m.door.nx, nz: m.door.nz }; });
    await S.ev(() => window.__pt.atDoor(2.2)); await S.frames(6);
    await pointAt(S, 'right', [door.x, 1.5, door.z]); await S.frames(4);
    await shot(S, 'door_testmap_hover');
    await S.press('right', 'grip', 6); await S.frames(10);
    const open = (await S.state()).door.open;
    rec(G, 'Test map: grip at the boss door opens it', open, 'open=' + open);
    await shot(S, 'door_testmap_open');
    if (!open) { await S.ev((d) => { const r = window.__game.ref; r.spawnAt('demon', d.x - d.nx * 6, d.z - d.nz * 6); r.clearWave(); }, door); await S.frames(10); }
    await S.ev(() => window.__pt.atDoor(2.2)); await S.frames(3);
    rec(G, 'Standing in front of the door is not already through it (test setup)', !(await S.state()).safe, '');
    await S.hand('left', { ax: [0, 0, 0, -1] }); await S.frames(60); await S.hand('left', { ax: [0, 0, 0, 0] }); await S.frames(10);
    const s3 = await S.state();
    rec(G, 'Walk into the open boss door: the safe room', s3.safe === true, 'safe=' + s3.safe);
    if (s3.safe) {
      const lu = await clearLevelUps(S);
      if (lu.n) rec(G, 'Level-up cards after the boss: laser + trigger picks each one', !lu.left, lu.n + ' picked');
      const ch = s3.player.stash.chest;
      await S.ev((c) => window.__game.ref.place(c.x - 1.5, c.z, Math.PI / 2), ch); await S.frames(8);
      const near = (await S.state()).player.stash.near;
      await pointAt(S, 'right', [ch.x, 0.6, ch.z]);
      await S.press('right', 'grip', 6); await S.frames(20);
      const m1 = await S.ev(() => window.__game.xr.menuShown());
      rec(G, 'Stash chest: stand at it, grip opens it (menu in front of you)', m1, 'near=' + near + ' menu=' + m1);
      await shot(S, 'stash_open');
      if (m1) { await S.press('left', 'y', 4); await S.frames(20); }
      rec(G, 'Y closes the stash', !(await S.ev(() => window.__game.xr.menuShown())), '');
      await rest(S);
      const mc = (await S.state()).merchant;
      await S.ev((c) => window.__game.ref.place(c.x - 1.2, c.z, Math.PI / 2), mc); await S.frames(30);
      const sh = await S.ev(() => ({ shop: !!window.__game.ref.snapshot().shop, menu: window.__game.xr.menuShown() }));
      rec(G, 'Merchant: walk up and the shop opens in VR', sh.shop && sh.menu, JSON.stringify(sh));
      if (sh.menu) { await S.press('left', 'y', 4); await S.frames(20); }
      rec(G, 'Y leaves the shop', !(await S.ev(() => window.__game.xr.menuShown())), '');
      const d2 = (await S.state()).door;
      const m = await S.ev(() => { const m = window.__game.ref.map; return { nx: m.door.nx, nz: m.door.nz }; });
      await S.ev(() => window.__pt.atDoor(2.2)); await S.frames(3);
      await S.hand('left', { ax: [0, 0, 0, -1] }); await S.frames(60); await S.hand('left', { ax: [0, 0, 0, 0] }); await S.frames(10);
      const s4 = await S.state();
      rec(G, 'Safe room door: walk through to the next floor', !s4.safe && s4.floor === 2, 'safe=' + s4.safe + ' floor=' + s4.floor);
    }
  } finally { if (S.logs.length) console.log('  page log:', S.logs.slice(0, 4).join(' | ')); await S.close(); }
}

async function controlsGroup() {
  const G = 'controls';
  const S = await open('?sandbox');
  try {
    const p = async () => (await S.state()).player;
    const toOpen = () => S.ev(() => { const r = window.__game.ref, O = window.__pt.openSpot(4, null) || window.__pt.openSpot(3, null); r.place(O[0], O[1], Math.PI / 2); });
    await toOpen(); await S.frames(5);
    let a = await p(); await S.hand('left', { ax: [0, 0, 0, -0.6] }); await S.frames(20); let b = await p(); await S.hand('left', { ax: [0, 0, 0, 0] }); await S.frames(5);
    rec(G, 'Left stick forward walks', Math.hypot(b.x - a.x, b.z - a.z) > 0.5, Math.hypot(b.x - a.x, b.z - a.z).toFixed(2) + ' m');
    await toOpen(); await S.frames(3);
    await S.hand('left', { ax: [0, 0, 0, -1] }); await S.frames(12); b = await p(); await S.hand('left', { ax: [0, 0, 0, 0] }); await S.frames(5);
    rec(G, 'Left stick all the way forward sprints', b.sprinting, 'sprinting=' + b.sprinting);
    await toOpen(); await S.frames(3);
    await S.hand('left', { ax: [0, 0, 0, -0.6], v: { 3: 1 } }); await S.frames(12); b = await p(); await S.hand('left', { ax: [0, 0, 0, 0], v: { 3: 0 } }); await S.frames(5);
    rec(G, 'Left stick click sprints', b.sprinting, 'sprinting=' + b.sprinting);
    a = await p(); let maxEye = a.eye; await S.hold('right', 'a', true); for (let i = 0; i < 10; i++) { await S.frames(1); maxEye = Math.max(maxEye, (await p()).eye); } await S.hold('right', 'a', false); await S.frames(20);
    rec(G, 'A jumps', maxEye > a.eye + 0.1, 'eye ' + a.eye.toFixed(2) + ' -> max ' + maxEye.toFixed(2));
    for (let i = 0; i < 180 && (await p()).eye > a.eye + 0.02; i++) await S.frames(1);   // land first: the game (rightly) won't start a slide in mid-air
    await toOpen(); await S.frames(3);
    await S.hand('left', { ax: [0, 0, 0, -1] }); await S.frames(5); await S.hold('right', 'b', true); let sl = false; for (let i = 0; i < 8; i++) { await S.frames(1); if ((await p()).sliding) sl = true; } await S.hold('right', 'b', false); await S.hand('left', { ax: [0, 0, 0, 0] }); await S.frames(20);
    rec(G, 'B slides', sl, 'sliding=' + sl);
    a = await p(); await S.hold('right', 'trigger', true); await S.frames(10); await S.hold('right', 'trigger', false); await S.frames(3); b = await p();
    rec(G, 'Right trigger fires', b.ammo < a.ammo, 'ammo ' + a.ammo + ' -> ' + b.ammo);
    await S.press('left', 'x', 4); await S.frames(2); b = await p();
    rec(G, 'X reloads (animation on the gun)', b.reloading || b.ammo === b.magSize, 'reloading=' + b.reloading);
    await S.frames(80);
    await S.hold('left', 'trigger', true); await S.frames(20); b = await p(); const dA = await debug(S); await shot(S, 'ads'); await S.hold('left', 'trigger', false); await S.frames(15);
    rec(G, 'Left trigger aims down sights', b.adsT > 0.5 && dA.adsK > 0.5, 'adsT=' + b.adsT.toFixed(2));
    a = await p(); await S.hand('right', { ax: [0, 0, 1, 0] }); await S.frames(10); await S.hand('right', { ax: [0, 0, 0, 0] }); await S.frames(6); b = await p();
    rec(G, 'Right stick sideways turns', Math.abs(b.yaw - a.yaw) > 0.2, 'yaw ' + a.yaw.toFixed(2) + ' -> ' + b.yaw.toFixed(2));
    a = await p(); await S.hand('right', { ax: [0, 0, 0, -1] }); await S.frames(10); await S.hand('right', { ax: [0, 0, 0, 0] }); await S.frames(10); b = await p();
    rec(G, 'Right stick forward does nothing in play (no surprise jump or turn)', Math.abs(b.eye - a.eye) < 0.05 && Math.abs(b.yaw - a.yaw) < 0.05, '');
    await S.ev(() => { const r = window.__game.ref; r.giveGun('rifle', 1); }); await S.frames(2); await S.press('right', 'grip', 6); await S.frames(10);   // a second gun for the swap
    const g0 = await held(S);
    await S.press('right', 'stick', 4); await S.frames(10);
    const g1 = await held(S);
    rec(G, 'Right stick click swaps guns', g0 !== g1, g0 + ' -> ' + g1);
    await S.press('left', 'y', 3); await S.frames(30);
    const m1 = await S.ev(() => window.__game.xr.menuShown());
    rec(G, 'Tap Y pauses (menu in front of you)', m1, 'menu=' + m1);
    await shot(S, 'menu_pause');
    const tiles = await S.ev(() => window.__pt.titles());
    const target = await S.ev(() => window.__pt.menuFind('resume|play|continue'));
    if (target) { const w = await S.ev((t) => window.__pt.menuPoint(t[0], t[1]), target); await pointAt(S, 'right', w); await S.frames(6); const hv = (await debug(S)).hover; await S.press('right', 'trigger', 4); await S.frames(20);
      const m2 = await S.ev(() => window.__game.xr.menuShown());
      rec(G, 'Laser + trigger presses a menu button (' + target[2] + ')', !m2, 'hover=' + hv + ', menu after=' + m2);
    } else rec(G, 'Laser + trigger presses a menu button', false, 'no resume tile; tiles=' + tiles.join(','));
    await rest(S);
    if (!(await S.ev(() => window.__game.xr.menuShown()))) { await S.press('left', 'y', 3); await S.frames(30); }
    await S.press('left', 'y', 3); await S.frames(20);
    rec(G, 'Y backs out of the pause menu', !(await S.ev(() => window.__game.xr.menuShown())), '');
    await S.frames(20);
    await S.seq('left', 'y', [[1, 3], [0, 3], [1, 3], [0, 1]]); await S.frames(10);
    const mp = (await debug(S)).mapShown; await shot(S, 'map');
    rec(G, 'Double-tap Y shows the map', mp, 'map=' + mp);
    await S.press('left', 'y', 3); await S.frames(20);
    rec(G, 'Tap Y closes the map without pausing', !(await debug(S)).mapShown && !(await S.ev(() => window.__game.xr.menuShown())), '');
    await S.frames(20);
    await S.hold('left', 'y', true); await S.frames(30); await S.hold('left', 'y', false); await S.frames(20);
    const mg = await S.ev(() => window.__game.xr.menuShown());
    rec(G, 'Hold Y opens the Gear menu', mg, 'menu=' + mg);
    if (mg) { const d0 = await debug(S); await S.hand('right', { ax: [0, 0, 0, 1] }); await S.frames(15); await S.hand('right', { ax: [0, 0, 0, 0] }); await S.frames(3); const d1 = await debug(S);
      rec(G, 'Right stick scrolls a long menu', d0.maxScroll === 0 || d1.scroll > d0.scroll, 'scroll ' + d0.scroll + ' -> ' + d1.scroll + ' of ' + d0.maxScroll);
      await S.press('left', 'y', 3); await S.frames(20);
      rec(G, 'Y closes the Gear menu', !(await S.ev(() => window.__game.xr.menuShown())), ''); }
    const errs = await S.ev(() => window.__fx.errors.slice(0, 3));
    rec(G, 'No script errors during the run', errs.length === 0, errs.join(' | ').slice(0, 200));
  } finally { if (S.logs.length) console.log('  page log:', S.logs.slice(0, 4).join(' | ')); await S.close(); }
}

(async () => {
  const only = args.find((a) => /^--only=/.test(a)); const want = only ? only.slice(7).split(',') : ['pickup', 'doors', 'controls'];
  for (const [n, f] of [['pickup', pickupGroup], ['doors', doorGroup], ['controls', controlsGroup]]) if (want.includes(n)) { try { await f(); } catch (e) { rec(n, 'group ran to the end', false, String(e && e.message || e).slice(0, 200)); } }
  const bad = results.filter((r) => !r.pass);
  console.log('\n' + (results.length - bad.length) + '/' + results.length + ' passed');
  if (mdOut) {
    const md = ['| # | Area | Check | Result | Seen |', '|---|---|---|---|---|'].concat(results.map((r, i) => '| ' + (i + 1) + ' | ' + r.group + ' | ' + r.name + ' | ' + (r.pass ? 'PASS' : '**FAIL**') + ' | ' + r.detail.replace(/\|/g, '/').slice(0, 140) + ' |')).join('\n');
    require('fs').writeFileSync(mdOut, md + '\n\n' + (results.length - bad.length) + '/' + results.length + ' passed\n');
  }
  process.exit(bad.length ? 1 : 0);
})();
