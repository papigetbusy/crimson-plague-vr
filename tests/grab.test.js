// VR grabbing and doors: the exact item a hand grabs, distance grab reach and walls, the test map's door and floor items, and the
// grab logic that picks what each hand is about to take (src/screen/xr_grab.js). Plain sentences. Run: node tests/grab.test.js
const Referee = require('../src/referee.js'), XrGrab = require('../src/screen/xr_grab.js');
let bad = 0;
const t = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) bad++; };
const fresh = (cfg) => { const ref = Referee.create(5); ref.setCfg(Object.assign({ startGun: 'pistol_service', locks: false, playerHp: 1e7, manualGuns: true, monsterCount: 0 }, cfg || {})); ref.reset(); const m = ref.map; ref.place(m.start.x, m.start.z, 0); ref.step(1 / 60, {}); return ref; };
const ok = (ch) => ch === '.' || ch === 'c';
const atDoor = (ref, k) => { const m = ref.map, d = m.door, C = m.CELL; for (const sg of [1, -1]) { const x = d.x + d.nx * k * sg, z = d.z + d.nz * k * sg, r = m.rows[Math.floor(z / C)], ch = r && r[Math.floor(x / C)]; if (ch === '.' || ch === 'c') { ref.place(x, z, Math.atan2(-d.nx * sg, d.nz * sg)); return [-d.nx * sg, -d.nz * sg]; } } return null; };
const openSpot = (m, r) => { for (let z = r + 1; z < m.H - r - 1; z++) for (let x = r + 1; x < m.W - r - 1; x++) { let g = true; for (let dz = -r; dz <= r && g; dz++) for (let dx = -r; dx <= r; dx++) if (!ok(m.rows[z + dz][x + dx])) { g = false; break; } if (g) return [(x + 0.5) * m.CELL, (z + 0.5) * m.CELL]; } return null; };

{ // the exact item
  const ref = fresh(), m = ref.map, O = openSpot(m, 4);
  ref.place(O[0], O[1], 0); ref.giveGun('rifle', 1, 1, O[0] + 1, O[1]); ref.giveGun('smg_compact', 1, 1, O[0] - 1, O[1]);
  const s = ref.snapshot(), far = s.pickups.find((p) => p.gun.id === 'smg_compact');
  ref.step(1 / 60, { pickup: true, pickupId: far.id });
  t('A grab names the exact item: you get that gun, not the nearest one', ref.snapshot().player.gun.id === 'smg_compact');
  t('Floor items say when they can be grabbed', s.pickups.every((p) => p.grab === true));
  const ref2 = fresh(), O2 = openSpot(ref2.map, 4); ref2.place(O2[0], O2[1], 0); ref2.giveGun('hmg_belt', 1, 1, O2[0] + 5, O2[1]);
  const id2 = ref2.snapshot().pickups.find((p) => p.gun && p.gun.id === 'hmg_belt').id;
  ref2.step(1 / 60, { pickup: true });
  t('The old pick up (no item named) still only reaches 2.6 m', ref2.snapshot().player.gun.id !== 'hmg_belt');
  ref2.step(1 / 60, { pickup: true, pickupId: id2 });
  t('A pointed grab reaches 5 m when you can see the item', ref2.snapshot().player.gun.id === 'hmg_belt');
  const ref3 = fresh(), O3 = openSpot(ref3.map, 4); ref3.place(O3[0], O3[1], 0); ref3.giveGun('shotgun_pump', 1, 1, O3[0] + 7.5, O3[1]);
  const id3 = ref3.snapshot().pickups[ref3.snapshot().pickups.length - 1].id; ref3.step(1 / 60, { pickup: true, pickupId: id3 });
  t('Nothing past 7 m can be grabbed', ref3.snapshot().player.gun.id !== 'shotgun_pump');
  // through a wall: find a floor cell with a wall cell between it and a floor cell 2 cells away
  const ref4 = fresh(), M = ref4.map; let pair = null;
  for (let z = 2; z < M.H - 2 && !pair; z++) for (let x = 2; x < M.W - 3 && !pair; x++) if (ok(M.rows[z][x]) && !ok(M.rows[z][x + 1]) && !ok(M.rows[z][x + 2]) && ok(M.rows[z][x + 3])) pair = [x, z];
  if (pair) { const C = M.CELL; ref4.place((pair[0] + 0.5) * C, (pair[1] + 0.5) * C, 0); ref4.giveGun('sniper_bolt', 1, 1, (pair[0] + 3.5) * C, (pair[1] + 0.5) * C);
    const id4 = ref4.snapshot().pickups[ref4.snapshot().pickups.length - 1].id; ref4.step(1 / 60, { pickup: true, pickupId: id4 });
    t('A gun behind a wall can not be grabbed', ref4.snapshot().player.gun.id !== 'sniper_bolt'); }
  const ref5 = fresh(), O5 = openSpot(ref5.map, 4); ref5.place(O5[0], O5[1], 0); ref5.giveGun('shotgun_pump', 1, 1, O5[0] + 1, O5[1]);
  ref5.step(1 / 60, { pickup: true, pickupId: 99999 });
  t('A grab of an item that is gone takes nothing else', ref5.snapshot().player.gun.id !== 'shotgun_pump');
  const ref6 = fresh(), O6 = openSpot(ref6.map, 4); ref6.place(O6[0], O6[1], 0); ref6.giveGear('chest', 3, 1, O6[0] + 1, O6[1]); ref6.giveMod(2, 1, O6[0] - 1, O6[1]);
  const p6 = ref6.snapshot().pickups; ref6.step(1 / 60, { pickup: true, pickupId: p6.find((p) => p.kind === 'gear').id }); ref6.step(1 / 60, { pickup: true, pickupId: p6.find((p) => p.kind === 'mod').id });
  t('Armor and mods can be grabbed by name too', ref6.snapshot().pickups.length === 0 && ref6.snapshot().player.mods.length === 1);
}
{ // floor items on the test map
  const a = fresh({ keepDrops: true }), b = fresh();
  a.giveGun('rifle', 1); b.giveGun('rifle', 1);
  for (let i = 0; i < 61 * 20; i++) { a.step(0.05, {}); b.step(0.05, {}); }
  t('Guns on the floor fade after 60 s in the game', b.snapshot().pickups.filter((p) => p.kind === 'gun').length === 0);
  t('On the VR test map guns on the floor stay until you take them', a.snapshot().pickups.filter((p) => p.kind === 'gun').length === 1);
}
{ // doors
  const ref = fresh({ locks: true }), d = ref.map.door;
  atDoor(ref, 2.2); ref.step(1 / 60, {});
  let L = ref.snapshot().locks;
  t('Standing at the sealed boss door, the game says what opens it', L.door && L.door.near && !L.door.open && /boss/i.test(L.door.text) && !L.door.canOpen);
  ref.step(1 / 60, { lockUse: 0 });
  t('Using the sealed boss door in the game does nothing (the boss must fall)', !ref.snapshot().door.open);
  const tm = fresh({ locks: true, doorTest: true }), d2 = tm.map.door;
  const toward = atDoor(tm, 2.2); tm.step(1 / 60, {});
  t('Standing in front of the door is not already through it', !tm.snapshot().safe);
  t('On the test map the boss door can be opened', tm.snapshot().locks.door.canOpen);
  tm.step(1 / 60, { lockUse: 0 });
  t('On the test map using the boss door opens it', tm.snapshot().door.open);
  let safe = false; for (let i = 0; i < 240 && !safe; i++) { tm.step(1 / 60, { mz: 1 }); safe = tm.snapshot().safe; }
  t('Walking through the opened test-map door takes you to the safe room', safe);
  const far = fresh({ locks: true, doorTest: true }); far.step(1 / 60, { lockUse: 0 });
  t('The test-map door only opens when you stand at it', !far.snapshot().door.open);
}
{ // the grab logic
  const items = [{ id: 1, x: 1, y: 0.3, z: 0 }, { id: 2, x: 0, y: 0.3, z: -5 }, { id: 3, x: 3, y: 0.3, z: 3 }];
  const near = XrGrab.pick({ p: [1.1, 0.4, 0.1], d: [0, -1, 0] }, items);
  t('A hand within reach of an item picks it (near grab)', near && near.id === 1 && near.mode === 'near');
  t('Reaching low counts: a hand on the floor beside the item', (XrGrab.pick({ p: [1.3, 0.05, 0.2], d: [0, -1, 0] }, items) || {}).id === 1);
  t('A hand at your side does not grab what lies at your feet', XrGrab.pick({ p: [1.0, 1.3, 0], d: [0, 0, -1] }, [{ id: 9, x: 1, y: 0.3, z: 0 }]) === null || XrGrab.pick({ p: [1.0, 1.3, 0], d: [0, 0, -1] }, [{ id: 9, x: 1, y: 0.3, z: 0 }]).mode !== 'near');
  const dir = (a, b) => { const v = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], l = Math.hypot(...v); return v.map((x) => x / l); };
  const ray = XrGrab.pick({ p: [0, 1.2, 0], d: dir([0, 1.2, 0], [0.2, 0.3, -5]) }, items);
  t('Pointing at an item 5 m away picks it (distance grab), even a little off', ray && ray.id === 2 && ray.mode === 'ray');
  t('Pointing well away from everything picks nothing', XrGrab.pick({ p: [0, 1.2, 0], d: [-1, 0, 0] }, items) === null);
  t('While firing, the gun hand does not pull things from afar (only what it touches)', XrGrab.pick({ p: [0, 1.2, 0], d: dir([0, 1.2, 0], [0.2, 0.3, -5]) }, items, null, true) === null && (XrGrab.pick({ p: [1.1, 0.4, 0.1], d: [0, -1, 0] }, items, null, true) || {}).id === 1);
  t('Nothing is picked through a wall', XrGrab.pick({ p: [0, 1.2, 0], d: dir([0, 1.2, 0], [0, 0.3, -5]) }, items, () => false) === null);
  const body = XrGrab.bodyPick([{ id: 5, x: 0, z: -1 }, { id: 6, x: 0, z: 1 }], { x: 0, z: 0, yaw: 0 });
  t('With nothing pointed at, the item in front of you within 2.6 m is the fallback', body && body.id === 5);
  const g = XrGrab.createGrip(), tgt = { id: 1, mode: 'ray' };
  const a1 = g.step(0.2, tgt, 0.016), a2 = g.step(0.9, tgt, 0.016), a3 = g.step(0.9, tgt, 0.016), a4 = g.step(0.5, tgt, 0.016), a5 = g.step(0.2, tgt, 0.016), a6 = g.step(0.7, tgt, 0.016);
  t('A grip grabs once per squeeze; easing off to 0.3 re-arms it (hysteresis, no flicker)', !a1.grab && a2.grab && !a3.grab && !a4.grab && !a5.grab && a6.grab);
  const h = XrGrab.createGrip(); h.step(1, null, 0.016); let got = false, n = 0;
  for (let i = 0; i < 30; i++) { const r = h.step(1, { id: 7, mode: 'near' }, 0.016); if (r.grab) { got = true; n++; } }
  t('Grip held like a gun: resting the hand on an item for a moment takes it, once', got && n === 1);
  const k = XrGrab.createGrip(); k.step(1, null, 0.016); let farGot = false; for (let i = 0; i < 30; i++) if (k.step(1, { id: 8, mode: 'ray' }, 0.016).grab) farGot = true;
  t('Grip held: pointing at something far away does not grab it (needs a fresh squeeze)', !farGot);
  t('Over the right shoulder counts as the back gun; in front of you does not', XrGrab.overShoulder([0.16, -0.06, 0.13], [0, 0, 0], 0) && !XrGrab.overShoulder([0.15, -0.3, -0.35], [0, 0, 0], 0));
  t('The shoulder spot turns with your head', XrGrab.overShoulder([0.12, -0.08, -0.16], [0, 0, 0], Math.PI / 2) && !XrGrab.overShoulder([0.16, -0.08, 0.12], [0, 0, 0], Math.PI / 2));
  const u = XrGrab.useTarget({ locks: { near: { what: 'toll', i: 0, price: 80, actions: [{ label: 'Pay 80 gold', afford: false }] } }, player: {} });
  t('At a gold gate without the gold, the grip says how much you need', u && !u.ok && /80 gold/.test(u.text));
  const dz = XrGrab.useTarget({ locks: { near: null, door: { near: true, open: false, canOpen: false, text: 'Sealed: kill the boss to open it', x: 1, z: 1 } }, player: {} });
  t('At the sealed boss door, the grip says why it will not open', dz && dz.what === 'door' && !dz.ok && /boss/.test(dz.text));
}
console.log(bad ? bad + ' failed' : 'all grab checks passed');
process.exit(bad ? 1 : 0);
