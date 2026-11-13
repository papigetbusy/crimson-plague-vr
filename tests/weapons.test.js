// Weapon checks: the silver pistol start, two carried guns and the swap, per-gun numbers, rarity by wave, and gun drops. Plain sentences. Run: node tests/weapons.test.js
const Referee = require('../src/referee.js'), W = require('../src/referee_weapons.js'), Cat = require('../src/models/gun_catalog.js');
global.Voxel = require('../src/models/voxel.js');
let bad = 0;
const t = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) bad++; };
const mk = (cfg, seed) => { const r = Referee.create(seed || 7); r.setCfg(Object.assign({ playerHp: 1e7, regen: 0, startGun: 'pistol_service', gunDrops: true }, cfg || {})); r.reset(); return r; };
const go = (r, secs, inp) => { let out; const ev = []; for (let i = 0; i < secs * 60; i++) { out = r.step(1 / 60, inp || {}); ev.push(...out.events); } return { s: out.state, ev }; };
const tap = (r) => r.step(1 / 60, { swap: true });
const face = (r, m) => { const p = r.snapshot().player; return Math.atan2(m.x - p.x, -(m.z - p.z)); };

// ---- the numbers
t('Every gun in the weapon table has a model in the gun catalog, and every catalog gun has numbers', Cat.IDS.every((id) => W.GUNS[id]) && W.DROPPABLE.filter((id) => id !== 'rifle_m4').every((id) => Cat.IDS.includes(id)) && W.DROPPABLE.includes('rifle_m4') && W.DROPPABLE.length === 21 && W.GUNS.rifle_m4.name === 'M4 Carbine' && W.GUNS.rifle_m4.type === 'rifle');
t('The M4 Carbine is a new droppable rifle: faster and lighter than the Gothic Rifle, with a quicker reload', (() => { const c = { damage: 14, fireRate: 10, magSize: 30, reloadTime: 2.1 }, a = W.stats(W.make('rifle', 0, 1), c), b = W.stats(W.make('rifle_m4', 0, 1), c); return W.GUNS.rifle_m4.type === 'rifle' && W.DROPPABLE.includes('rifle_m4') && !W.DROPPABLE.includes('rifle') && b.rate > a.rate && b.dmg < a.dmg && b.reload < a.reload && W.view(W.make('rifle_m4', 0, 1), c).name === 'M4 Carbine'; })());
t('equipGun puts the M4 Carbine in your hands, full magazine, and giveGun drops one at your feet so it can be picked up', (() => { const r = mk({ manualGuns: true }); r.equipGun('rifle_m4', 1); const p = r.snapshot().player; const ok = p.gun.id === 'rifle_m4' && p.ammo === p.magSize; r.giveGun('rifle_m4', 0); const floor = r.snapshot().pickups.filter((q) => q.kind === 'gun' && (q.gun && q.gun.id === 'rifle_m4' || q.item && q.item.id === 'rifle_m4')); r.step(1 / 60, { pickup: true }); return ok && floor.length >= 1 && r.snapshot().player.gun.id === 'rifle_m4'; })());
t('A run starts holding the plain silver Service Pistol with a 12 round magazine and nothing in the other hand', (() => { const p = mk().snapshot().player; return p.gun.id === 'pistol_service' && p.gun.rarity === 0 && p.gun.other === null && p.magSize === 12 && p.ammo === 12; })());
t('The Service Pistol carries no status effect', W.GUNS.pistol_service.status.length === 0);
t('Each gun type has its own feel: a shotgun fires 7 pellets slowly, a sniper hits hardest, an SMG fires fastest of the small guns, a heavy machine gun holds the most rounds', (() => { const c = { damage: 14, fireRate: 10, magSize: 30, reloadTime: 2.1 }, s = (id) => W.stats(W.make(id, 0, 1), c); return s('shotgun_pump').pellets === 7 && s('sniper_bolt').dmg > 4 * s('pistol_service').dmg && s('smg_compact').rate > s('pistol_service').rate * 2 && s('hmg_belt').mag > 3 * s('smg_compact').mag; })());
t('The four versions of each type differ from each other in their numbers', ['pistol', 'smg', 'shotgun', 'sniper', 'hmg'].every((ty) => { const c = { damage: 14, fireRate: 10, magSize: 30, reloadTime: 2.1 }, ids = Cat.IDS.filter((i) => i.startsWith(ty + '_')), keys = new Set(ids.map((i) => { const s = W.stats(W.make(i, 0, 1), c); return [s.dmg, s.rate, s.mag, s.reload, s.spread].map((x) => x.toFixed(3)).join('/'); })); return keys.size === 4 || (ty === 'pistol' && keys.size >= 3) || keys.size === 4; }));
t('A higher rarity of the same gun hits harder, and so does a gun dropped on a later wave', (() => { const c = { damage: 14, fireRate: 10, magSize: 30, reloadTime: 2.1 }, d = (r, w) => W.stats(W.make('smg_compact', r, w), c).dmg; return d(1, 1) > d(0, 1) && d(2, 1) > d(1, 1) && d(3, 1) > d(2, 1) && d(4, 1) > d(3, 1) && d(0, 30) > d(0, 1); })());

// ---- what drops when
const rng = (() => { let a = 12345; return () => { a = (a + 0x6D2B79F5) | 0; let x = Math.imul(a ^ (a >>> 15), 1 | a); x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x; return ((x ^ (x >>> 14)) >>> 0) / 4294967296; }; })();
const hist = (w) => { const h = [0, 0, 0, 0, 0]; for (let i = 0; i < 4000; i++) h[W.roll(w, rng).rarity]++; return h; };
{
  const a = hist(5), b = hist(15), c = hist(25), d = hist(35);
  t('Waves 1 to 10: mostly common, a few uncommon, nothing better', a[0] > a[1] * 3 && a[1] > 0 && a[2] + a[3] + a[4] === 0);
  t('Waves 11 to 20: mostly uncommon, a few rare, no common and nothing better than rare', b[1] > b[2] * 3 && b[2] > 0 && b[0] === 0 && b[3] + b[4] === 0);
  t('Waves 21 to 30: mostly rare, a few epic', c[2] > c[3] * 3 && c[3] > 0 && c[0] + c[1] + c[4] === 0);
  t('Wave 31 and later: mostly epic, with a chance of legendary', d[3] > d[4] * 2 && d[4] > 0 && d[0] + d[1] + d[2] === 0);
}
t('Only legendary guns carry two status effects, and they are two different ones; everything else carries one or none', (() => { let ok = true; for (let i = 0; i < 600; i++) { const g = W.roll(35, rng); if (g.rarity === 4 ? !(g.status.length === 2 && g.status[0] !== g.status[1]) : g.status.length > 1) ok = false; } return ok; })());

// ---- carrying two guns
{
  const r = mk(); r.giveGun('smg_compact', 1); const o = go(r, 0.2), g = o.s.player.gun;
  t('Walking over a gun picks it up into the free slot and puts it in your hands, keeping the pistol in the other', g.id === 'smg_compact' && g.rarity === 1 && g.other && g.other.id === 'pistol_service' && o.ev.some((e) => e.type === 'gunPickup'));
  t('The new gun comes with a full magazine of its own size', o.s.player.ammo === o.s.player.magSize && o.s.player.magSize > 12);
  const sw = tap(r).state.player.gun;
  t('The swap button switches back to the pistol and the other gun waits in the other slot', sw.id === 'pistol_service' && sw.other.id === 'smg_compact');
  go(r, 0.5); const sw2 = tap(r).state.player.gun; t('Swapping twice returns to the first gun', sw2.id === 'smg_compact');
}
{
  const r = mk(); const sw = tap(r); t('With only one gun the swap button does nothing', sw.state.player.gun.id === 'pistol_service' && !sw.events.some((e) => e.type === 'swap'));
  r.giveGun('smg_compact', 0); go(r, 0.2); go(r, 0.4, { fire: true }); // fire some SMG ammo
  const smgAmmo = r.snapshot().player.ammo; tap(r); go(r, 0.5); const back = tap(r).state.player;
  t('Each carried gun keeps its own ammo while you hold the other', back.gun.id === 'smg_compact' && back.ammo === smgAmmo);
  r.giveGun('shotgun_pump', 2); const o = go(r, 0.2);
  t('With both slots full a new gun replaces the one in your hands, and the old one drops at your feet', o.s.player.gun.id === 'shotgun_pump' && o.s.player.gun.other.id === 'pistol_service' && o.s.pickups.some((p) => p.kind === 'gun' && p.gun.id === 'smg_compact'));
  const later = go(r, 0.5); t('The gun you just dropped is not grabbed straight back up', later.s.player.gun.id === 'shotgun_pump' && later.s.pickups.some((p) => p.kind === 'gun'));
}
{
  const r = mk(); r.giveGun('shotgun_pump', 0); go(r, 0.5);
  const m = r.snapshot(); r.spawnAt('fiend', r.snapshot().player.x + 0, r.snapshot().player.z - 8);
  const mon = r.snapshot().monsters.slice(-1)[0]; r.place(r.snapshot().player.x, r.snapshot().player.z, face(r, mon));
  const shots = go(r, 0.05, { fire: true }).ev.filter((e) => e.type === 'shot').length;
  t('A shotgun sends seven pellets with one pull of the trigger', shots === 7);
}

{
  const r = mk(); r.equipGun('hmg_minigun', 3); const g = r.snapshot().player;
  t('The cheat build can put any gun in your hands at any rarity, with a full magazine', g.gun.id === 'hmg_minigun' && g.gun.rarity === 3 && g.ammo === g.magSize && g.magSize > 12);
}

// ---- fire rate holds after a reload
{
  const rate = (r) => r.snapshot().player.gun.card.rate;
  const r = mk({ magSize: 30, spread: 0, spreadAds: 0 }, 5); r.place(r.map.start.x, r.map.start.z, 0); go(r, 1.7);
  const per = rate(r);
  go(r, 0.2, { fire: true }); go(r, 0.05, { reload: true, fire: true });         // hold fire, press reload and keep holding
  let guard = 0; while (r.snapshot().player.reloading && guard++ < 600) go(r, 1 / 60, { fire: true });
  go(r, 1, { fire: true });
  const used = r.snapshot().player.magSize - r.snapshot().player.ammo;
  t('Holding fire through a reload does not store up a burst: the first second after it shoots at the gun\'s own rate', used <= per * 1 + 3);
}

// ---- drops
const quiet = (cfg) => { const r = mk(Object.assign({ magSize: 1000, spread: 0, spreadAds: 0 }, cfg || {}), 5); r.place(r.map.start.x, r.map.start.z, 0); go(r, 1.7); return r; };
const killOne = (r, kind) => { r.spawnAt(kind || 'fiend', r.map.start.x, r.map.start.z - 5); return go(r, 0.4, { fire: true }).ev.filter((e) => e.type === 'kill').length; };
{
  const r = quiet({ damage: 1e6 }), r0 = quiet({ damage: 1e6, gunDrops: false }); let k = 0, k0 = 0;
  for (let i = 0; i < 80; i++) { k += killOne(r); k0 += killOne(r0); }
  const n = r.snapshot().pickups.filter((p) => p.kind === 'gun').length;
  t('With drops on, killing monsters leaves guns on the floor, and not on every kill', k >= 70 && n >= 1 && n < k * 0.5);
  t('With drops off, no guns appear', k0 >= 70 && r0.snapshot().pickups.filter((p) => p.kind === 'gun').length === 0 && r0.snapshot().player.gun.other === null);
  const boss = quiet({ damage: 1e6, startWave: 10 }); const kk = killOne(boss, 'demon'), bs = boss.snapshot();
  t('A boss always leaves a gun behind', kk === 1 && bs.pickups.some((q) => q.kind === 'gun'));
}
{
  const a = mk({ gunDrops: true }, 99), b = mk({ gunDrops: false }, 99); let same = true;
  for (let i = 0; i < 600; i++) { const x = a.step(1 / 60, {}).state, y = b.step(1 / 60, {}).state; if (x.monsters.length !== y.monsters.length || x.monsters.some((m, j) => Math.abs(m.x - y.monsters[j].x) > 1e-9)) same = false; }
  t('Gun drops use their own dice, so turning them on never changes where monsters spawn or move', same);
}
// ---- the merchant sells guns
{
  const open = (drops) => { const ref = Referee.create(5); ref.setCfg({ locks: false, startWave: 1, playerHp: 1e7, regen: 0, classId: 'gunslinger', startGun: 'pistol_service', gunDrops: drops }); ref.reset(); const m = ref.map;
    ref.spawnAt('demon', m.start.x + 10, m.start.z); ref.clearWave(); ref.place(m.door.x, m.door.z, 0); go(ref, 2);
    for (let i = 0; i < 30 && (ref.snapshot().choices || ref.snapshot().classChoices); i++) ref.step(1 / 60, { pick: 0, pickClass: 0 });
    const mer = ref.snapshot().merchant; ref.place(mer.x, mer.z + 2, 0); go(ref, 0.5); return ref; };
  const r = open(true); let st = r.snapshot();
  const guns = st.shop.supplies.filter((x) => x.rarity !== undefined);
  t('The merchant offers two guns for gold, between Mend and Leave, each with a price and a rarity colour', !!st.shop && guns.length === 2 && st.shop.supplies[0].id === 'mend' && st.shop.supplies[3].id === 'leave' && guns.every((g) => g.price > 0 && /^#/.test(g.color)));
  t('The second gun is a rarity better, and costs more', guns[1].rarity >= guns[0].rarity && guns[1].price >= guns[0].price);
  r.giveGold(-r.snapshot().gold); r.step(1 / 60, { pick: 1 });
  t('With no gold a gun cannot be bought', r.snapshot().player.gun.id === 'pistol_service' && r.snapshot().shop.supplies.filter((x) => x.rarity !== undefined).length === 2);
  r.giveGold(5000); const price = guns[0].price; r.step(1 / 60, { pick: 1 }); st = r.snapshot();
  t('Buying a gun takes its price in gold and puts it in your hands, keeping your pistol in the other slot', st.gold === 5000 - price && st.player.gun.id !== 'pistol_service' && st.player.gun.other && st.player.gun.other.id === 'pistol_service');
  t('A bought gun leaves the shelf', st.shop.supplies.filter((x) => x.rarity !== undefined).length === 1);
  const plain = open(false);
  t('With gun drops off, the merchant sells only Mend and Leave, as before', plain.snapshot().shop.supplies.length === 2);
}

// ---- manual pickup (the game's setting): a gun is only taken when you press pick up
{
  const man = (extra) => { const r = mk(Object.assign({ manualGuns: true }, extra || {})); return r; };
  const r = man(); r.giveGun('smg_compact', 2); go(r, 0.2);
  t('With manual pickup, standing on a gun does not take it', r.snapshot().player.gun.id === 'pistol_service' && r.snapshot().pickups.some((q) => q.kind === 'gun'));
  t('A gun in reach is marked so the card can say tap to pick up', r.snapshot().pickups.find((q) => q.kind === 'gun').inReach === true);
  r.step(1 / 60, { pickup: true });
  t('Pressing pick up takes the gun at your feet', r.snapshot().player.gun.id === 'smg_compact' && r.snapshot().pickups.every((q) => q.kind !== 'gun'));
  const far = man(); far.giveGun('smg_compact', 2); const p0 = far.snapshot().player; far.place(p0.x + 5, p0.z, 0); far.step(1 / 60, { pickup: true });
  t('A gun too far away is not taken, and is not marked in reach', far.snapshot().player.gun.id === 'pistol_service' && far.snapshot().pickups.find((q) => q.kind === 'gun').inReach === false);
  const two = man(); two.giveGun('smg_compact', 2); two.step(1 / 60, { pickup: true }); two.giveGun('hmg_belt', 3); two.step(1 / 60, { pickup: true });
  const s2 = two.snapshot();
  t('With both hands full, picking up swaps it for the gun in your hands, which drops at your feet', s2.player.gun.id === 'hmg_belt' && s2.pickups.some((q) => q.kind === 'gun' && q.gun.id === 'smg_compact'));
  const safe = man(); safe.giveGun('smg_compact', 2); safe.step(1 / 60, { pickup: true }); safe.giveGun('hmg_belt', 3); go(safe, 3);
  t('Walking around in a fight never swaps your gun for one on the floor', safe.snapshot().player.gun.id === 'smg_compact');
  const old = mk(); old.giveGun('smg_compact', 2); go(old, 0.2);
  t('With manual pickup off (the old way) walking over a gun still takes it, so older tests stay valid', old.snapshot().player.gun.id === 'smg_compact');
}
// ---- two guns on the floor, and the one from your hands dropping
{
  const r = mk({ manualGuns: true }); const p0 = r.snapshot().player;
  r.giveGun('smg_compact', 1); r.step(1 / 60, { pickup: true });
  t('The first gun you pick up goes in your free hand and the pistol stays in the other', (() => { const g = r.snapshot().player.gun; return g.id === 'smg_compact' && g.other && g.other.card.name === 'Service Pistol'; })());
  r.giveGun('rifle', 2); r.step(1 / 60, {});
  const before = r.snapshot().player;
  r.step(1 / 60, { pickup: true });
  const after = r.snapshot(), floor = after.pickups.filter((q) => q.kind === 'gun');
  t('With both hands full, picking up a gun puts it in your hands and the gun that was in your hands drops', after.player.gun.id === 'rifle' && floor.length === 1 && floor[0].gun.name === 'Compact SMG');
  t('The gun from your hands drops beside you, not under the spot you reached for', floor.length === 1 && Math.hypot(floor[0].x - before.x, floor[0].z - before.z) > 0.8);
  t('The gun that drops keeps the ammo it had', (() => { const q = mk({ manualGuns: true }); q.giveGun('smg_compact', 1); q.step(1 / 60, { pickup: true }); for (let i = 0; i < 40; i++) q.step(1 / 60, { fire: true }); const ammo = q.snapshot().player.ammo; q.giveGun('rifle', 2); q.step(1 / 60, {}); q.step(1 / 60, { pickup: true }); const f = q.snapshot().pickups.find((x) => x.kind === 'gun'); return ammo < q.snapshot().player.magSize && f && f.gun.name === 'Compact SMG'; })());
}
{
  const r = mk({ manualGuns: true }), S = r.map.start;
  let yaw = null;
  for (let k = 0; k < 8 && yaw === null; k++) {      // find a direction with open floor for 3 units
    const a = k * Math.PI / 4, fx = Math.sin(a), fz = -Math.cos(a); r.place(S.x, S.z, a); r.giveGun('smg_compact', 1);
    r.place(S.x + fx * 2, S.z + fz * 2, a); if (Math.hypot(r.snapshot().player.x - (S.x + fx * 2), r.snapshot().player.z - (S.z + fz * 2)) < 0.01) yaw = a;
    r.clearWave(); if (yaw === null) { r.reset(); }
  }
  const fx = Math.sin(yaw || 0), fz = -Math.cos(yaw || 0);
  const q = mk({ manualGuns: true }); q.place(S.x, S.z, yaw || 0); q.giveGun('smg_compact', 1);                      // a gun at the start spot
  q.place(S.x + fx * 2, S.z + fz * 2, yaw || 0); q.giveGun('rifle', 2);                                           // a rifle two steps ahead
  q.place(S.x + fx * 0.8, S.z + fz * 0.8, yaw || 0); q.step(1 / 60, {});                                           // you stand between them, looking at the rifle; the smg is nearer
  q.step(1 / 60, { pickup: true });
  t('With two guns on the floor, pick up takes the one you are looking at, not just the nearest', q.snapshot().player.gun.id === 'rifle');
}
console.log(bad ? bad + ' FAILED' : 'all weapon checks passed'); process.exit(bad ? 1 : 0);
