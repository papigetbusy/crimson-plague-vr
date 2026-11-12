// More fake-Quest playtest groups for tools/xr_playtest.js: a full run of the real game (no test map), every menu (gun mods and the stash in depth),
// and the boss-door puzzles. Each step drives the game the way a player would: laser + trigger on menu tiles, grips, sticks and buttons.
module.exports = function (X) {
  const { open, rest, rec, debug, pointAt, shot } = X;
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const menuOn = (S) => S.ev(() => window.__game.xr.menuShown());
  const running = (S) => S.ev(() => window.__game.running());
  async function scrollTop(S) { for (let k = 0; k < 12; k++) { const d = await debug(S); if (!d.menu || d.scroll <= 0) return; await S.hand('right', { ax: [0, 0, 0, -1] }); await S.frames(8); await S.hand('right', { ax: [0, 0, 0, 0] }); await S.frames(2); } }
  // find a tile whose title matches (scrolling down through a long menu), point the laser at it and pull the trigger. Returns the tile's title, or null.
  async function clickTile(S, re, o) {
    o = o || {}; if (!o.noTop) await scrollTop(S);
    for (let k = 0; k < 14; k++) {
      const t = await S.ev((re) => window.__pt.menuFind(re), re);
      if (t) {
        const w = await S.ev((t) => window.__pt.menuPoint(t[0], t[1]), t); await pointAt(S, 'right', w); await S.frames(4);
        let hv = (await debug(S)).hover;
        if (!hv) { await S.frames(8); hv = (await debug(S)).hover; }
        if (!hv && o.why) o.why.push(JSON.stringify({ t, w, d: await debug(S).then((d) => ({ pos: d.menuPos, sc: d.menuScale, scroll: d.scroll, id: d.menuId })) }));
        await S.press('right', 'trigger', 4); await S.frames(o.wait || 14); await rest(S); return { title: t[2], hover: hv };
      }
      const d = await debug(S); if (!d.menu || d.scroll >= d.maxScroll) break;
      await S.hand('right', { ax: [0, 0, 0, 1] }); await S.frames(6); await S.hand('right', { ax: [0, 0, 0, 0] }); await S.frames(2);
    }
    return null;
  }
  const tilesNow = (S) => S.ev(() => window.__pt.titles());
  async function allTiles(S) { await scrollTop(S); const seen = new Set(); for (let k = 0; k < 14; k++) { (await tilesNow(S)).forEach((t) => seen.add(t)); const d = await debug(S); if (!d.menu || d.scroll >= d.maxScroll) break; await S.hand('right', { ax: [0, 0, 0, 1] }); await S.frames(6); await S.hand('right', { ax: [0, 0, 0, 0] }); await S.frames(2); } await scrollTop(S); return [...seen]; }
  const yTap = async (S) => { await S.press('left', 'y', 4); await S.frames(30); };
  const yHold = async (S) => { await S.hold('left', 'y', true); await S.frames(60); await S.hold('left', 'y', false); await S.frames(10); };
  const P = (S, f) => S.ev(f);
  const errsOf = (S) => S.ev(() => window.__fx.errors.slice(0, 3));
  const toOpen = (S) => S.ev(() => { const r = window.__game.ref, O = window.__pt.openSpot(4, null) || window.__pt.openSpot(3, null); r.place(O[0], O[1], Math.PI / 2); return O; });
  const mob = (S) => S.ev(() => { const k = window.__game.ref.kinds; return Object.keys(k).find((id) => !k[id].boss && !k[id].mini && !k[id].ranged) || 'goblin'; });

  // ---------------- the real game, start to death and back ----------------
  async function gameGroup() {
    const G = 'game';
    const S = await open('');
    try {
      const st0 = await P(S, () => ({ run: window.__game.running(), id: window.__game.xr.debug().menuId, menu: window.__game.xr.menuShown() }));
      const tl0 = await tilesNow(S);
      rec(G, 'Putting the headset on at the title shows the start menu first (pick a class, then enter)', !st0.run && st0.menu && tl0.some((t) => /Witch/.test(t)), JSON.stringify(st0) + ' tiles: ' + tl0.slice(0, 6).join(', '));
      await shot(S, 'start_menu');
      if (st0.menu && !st0.run) {
        await clickTile(S, '^Witch');
        const sel = await P(S, () => document.querySelector('[data-cls="witch"]').classList.contains('sel'));
        rec(G, 'Laser + trigger picks a class (Witch)', sel, 'witch selected=' + sel);
        await clickTile(S, 'ENTER THE HALL', { wait: 30 });
      }
      const st1 = await P(S, () => ({ run: window.__game.running(), cls: window.__game.ref.cfg.classId, menu: window.__game.xr.menuShown() }));
      rec(G, 'Laser + trigger on Enter the hall starts the run with that class', st1.run && !st1.menu && st1.cls === 'witch', JSON.stringify(st1));
      if (!st1.run) await P(S, () => window.__game.begin && window.__game.begin(true));
      // shooting: a monster in front, the gun hand's laser on it, trigger held
      const O = await toOpen(S); const kind = await mob(S);
      await S.ev((O, k) => { const r = window.__game.ref; r.clearWave(); r.spawnAt(k, O[0] + 4.5, O[1]); }, O, kind); await S.frames(4);
      const m0 = await S.ev(() => window.__game.ref.snapshot().monsters.map((m) => ({ id: m.id, hp: m.hp, x: m.x, z: m.z }))[0]);
      const k0 = await S.ev(() => ({ kills: window.__game.ref.snapshot().kills, ammo: window.__game.ref.snapshot().player.ammo }));
      await S.pulses();
      let dead = false, hit = false;
      for (let i = 0; i < 40 && !dead; i++) {
        const m = await S.ev((id) => window.__game.ref.snapshot().monsters.find((q) => q.id === id) || null, m0.id);
        if (!m) { dead = true; break; } if (m.hp < m0.hp) hit = true;
        await pointAt(S, 'right', [m.x, 1.1, m.z]); await S.hold('right', 'trigger', true); await S.frames(6); await S.hold('right', 'trigger', false); await S.frames(2);
        if ((await S.ev(() => window.__game.ref.snapshot().player.ammo)) === 0) { await S.press('left', 'x', 4); await S.frames(90); }
      }
      const k1 = await S.ev(() => ({ kills: window.__game.ref.snapshot().kills, ammo: window.__game.ref.snapshot().player.ammo }));
      const pf = await S.pulses();
      rec(G, 'Pointing the gun at a monster and pulling the trigger hurts it', hit || dead, 'hp ' + m0.hp + ' -> ' + (dead ? 'dead' : 'hit'));
      rec(G, 'Shooting kills it (kill counted)', dead && k1.kills > k0.kills, 'kills ' + k0.kills + ' -> ' + k1.kills);
      rec(G, 'Fire and hits buzz the gun hand', pf.filter((p) => p.hand === 'right').length >= 2, pf.length + ' pulses');
      await rest(S);
      // ammo + reload
      const a0 = await S.ev(() => window.__game.ref.snapshot().player); await S.hold('right', 'trigger', true); await S.frames(12); await S.hold('right', 'trigger', false); await S.frames(3);
      const a1 = await S.ev(() => window.__game.ref.snapshot().player.ammo);
      rec(G, 'Firing uses ammo', a1 < a0.ammo, a0.ammo + ' -> ' + a1);
      await S.press('left', 'x', 4); let full = false; for (let i = 0; i < 40 && !full; i++) { await S.frames(10); const p = await S.ev(() => window.__game.ref.snapshot().player); full = !p.reloading && p.ammo === p.magSize; }
      rec(G, 'X reloads to a full magazine', full, '');
      // level-up
      await S.ev(() => { const r = window.__game.ref, l = r.snapshot().level; r.giveXp(l.need - l.xp + 1); }); await S.frames(20);
      const lu = await debug(S);
      rec(G, 'A level-up opens the cards in front of you', lu.menu && lu.menuId === 'levelup', 'menu=' + lu.menuId);
      await shot(S, 'levelup');
      const lv0 = await S.ev(() => window.__game.ref.snapshot().skills.length + (window.__game.ref.snapshot().cls.picked || []).length);
      const lr = await X.clearLevelUps(S);
      rec(G, 'Laser + trigger picks the level-up cards and play carries on', lr.n > 0 && !lr.left && (await running(S)), lr.n + ' picked');
      // map, pause, codex from pause
      await S.seq('left', 'y', [[1, 3], [0, 3], [1, 3], [0, 1]]); await S.frames(10);
      const mp = (await debug(S)).mapShown; rec(G, 'Double-tap Y shows the map in the real game', mp, '');
      if (mp) { await S.press('left', 'y', 4); await S.frames(30); }
      await yTap(S);
      const pz = await P(S, () => ({ run: window.__game.running(), id: window.__game.xr.debug().menuId, menu: window.__game.xr.menuShown() }));
      rec(G, 'Tap Y pauses (PAUSED menu)', !pz.run && pz.menu, JSON.stringify(pz));
      const pt = await tilesNow(S); await shot(S, 'pause');
      rec(G, 'Pause menu has Resume and the Codex, and no class buttons mid-run', pt.some((t) => /RESUME/i.test(t)) && pt.some((t) => /Codex/i.test(t)) && !pt.some((t) => /^Witch|^Assassin/.test(t)), pt.join(', ').slice(0, 140));
      const cx = await clickTile(S, 'Codex', { wait: 30 });
      const cxd = await debug(S);
      rec(G, 'Codex opens from pause in VR', cx && cxd.menu && cxd.menuId === 'codex', 'menu=' + cxd.menuId);
      if (cxd.menuId === 'codex') { await shot(S, 'codex'); const c0 = cxd.scroll; await S.hand('right', { ax: [0, 0, 0, 1] }); await S.frames(15); await S.hand('right', { ax: [0, 0, 0, 0] }); await S.frames(3); const c1 = (await debug(S)).scroll; rec(G, 'Codex scrolls with the right stick', cxd.maxScroll === 0 || c1 > c0, c0 + ' -> ' + c1 + ' of ' + cxd.maxScroll); await yTap(S); }
      const bk = await debug(S); rec(G, 'Y leaves the Codex back to the pause menu', bk.menuId === 'start', 'menu=' + bk.menuId);
      await yTap(S);
      rec(G, 'Y resumes from pause', await running(S), '');
      // the safe room of the real game (floor 2's), the merchant and the stash
      await S.ev(() => { const r = window.__game.ref; r.setCfg({ startWave: 11, startSafe: true }); r.reset(); r.setCfg({ startWave: 1, startSafe: false }); }); await S.frames(20);
      await X.clearLevelUps(S);
      const sf = await S.ev(() => { const s = window.__game.ref.snapshot(); return { safe: s.safe, m: s.merchant, ch: s.player.stash.chest }; });
      rec(G, 'Safe room reached (test jump: wave 11)', sf.safe && sf.m && sf.ch, JSON.stringify(sf).slice(0, 100));
      if (sf.safe) {
        await S.ev(() => window.__game.ref.giveGold(3000));
        await S.ev((c) => window.__game.ref.place(c.x - 1.2, c.z, Math.PI / 2), sf.m); await S.frames(30);
        const shop = await S.ev(() => { const s = window.__game.ref.snapshot(); return s.shop ? { gold: s.gold, names: s.shop.skills.concat(s.shop.supplies).filter((c) => c.afford && c.id !== 'leave' && c.id !== 'mend').map((c) => c.name) } : null; });
        const shm = await debug(S);
        rec(G, 'Merchant opens in VR in the real game', !!shop && shm.menu, 'menu=' + shm.menuId);
        if (shop && shop.names.length) {
          const all = await allTiles(S);
          const want = shop.names.find((n) => all.some((t) => t.indexOf(n) >= 0)) || shop.names[0];
          await shot(S, 'shop');
          const c = await clickTile(S, '^' + esc(want), { wait: 20 });
          const g1 = await S.ev(() => window.__game.ref.snapshot().gold);
          rec(G, 'Laser + trigger buys from the merchant (gold spent)', !!c && g1 < shop.gold, 'bought ' + want + ': gold ' + shop.gold + ' -> ' + g1);
          const still = await debug(S); rec(G, 'The shop stays open after a buy (to buy more)', still.menu, 'menu=' + still.menuId);
          if (still.menu) await yTap(S);
          rec(G, 'Y leaves the merchant', !(await menuOn(S)), '');
          await S.ev((c) => window.__game.ref.place(c.x - 4, c.z, -Math.PI / 2), sf.m); await S.frames(20);
        }
      }
      // death and RISE AGAIN
      await S.ev(() => window.__game.ref.reset()); await S.frames(10);
      const O2 = await toOpen(S); const kind2 = await mob(S);
      await S.ev((O, k) => { const r = window.__game.ref; r.setHp(1); for (let i = 0; i < 4; i++) r.spawnAt(k, O[0] + 0.9 * Math.cos(i * 1.6), O[1] + 0.9 * Math.sin(i * 1.6)); }, O2, kind2);
      let over = false; for (let i = 0; i < 60 && !over; i++) { await S.frames(10); over = await S.ev(() => window.__game.ref.snapshot().over); }
      await S.frames(80);
      const go = await debug(S); const gt = await tilesNow(S);
      rec(G, 'Falling shows YOU FELL in front of you', over && go.menu && go.menuId === 'gameover', 'over=' + over + ' menu=' + go.menuId + ' tiles: ' + gt.join(', ').slice(0, 80));
      await shot(S, 'gameover');
      const ra = await clickTile(S, 'RISE AGAIN', { wait: 40 });
      const af = await S.ev(() => { const s = window.__game.ref.snapshot(); return { over: s.over, hp: s.player.hp, max: s.player.maxHp, wave: s.wave.n, run: window.__game.running(), menu: window.__game.xr.menuShown() }; });
      rec(G, 'Laser + trigger on RISE AGAIN starts a new run', !!ra && !af.over && af.hp === af.max && af.run && !af.menu, JSON.stringify(af));
      const errs = await errsOf(S); rec(G, 'No script errors in the full run', errs.length === 0, errs.join(' | ').slice(0, 200));
    } finally { if (S.logs.length) console.log('  page log:', S.logs.slice(0, 4).join(' | ')); await S.close(); }
  }

  // ---------------- Gear menu: gun mods; stash chest: put in / take out ----------------
  async function menusGroup() {
    const G = 'menus';
    const S = await open('?sandbox');
    try {
      await S.frames(10);
      await S.ev(() => { const r = window.__game.ref; r.giveMod(2); r.giveMod(3); });
      await S.ev(() => { const r = window.__game.ref, s = r.snapshot(); for (const p of s.pickups.filter((q) => q.kind === 'mod')) { r.place(p.x, p.z); r.step(0.016, { pickupId: p.id, pickup: true }); } });
      const mods0 = await S.ev(() => window.__game.ref.snapshot().player.mods.length);
      if (!mods0) { await S.ev(() => { const r = window.__game.ref; for (let q = 2; q <= 3; q++) { r.giveMod(q); } }); }
      const s0 = await S.ev(() => { const p = window.__game.ref.snapshot().player; return { bag: p.mods.length, on: p.gun.card.mods.length, slots: p.gun.card.slots, names: p.mods.map((m) => m.name) }; });
      await yHold(S);
      const gm = await debug(S);
      rec(G, 'Hold Y opens the Gear menu (guns, armor, mod bag)', gm.menu && gm.menuId === 'gearMenu', 'menu=' + gm.menuId);
      const gt = await allTiles(S);
      await shot(S, 'gear_menu');
      rec(G, 'Gear menu shows the mod bag with a Fit button for each mod', s0.bag > 0 && gt.some((t) => /Fit to gun/i.test(t)), 'bag ' + s0.bag + '; tiles: ' + gt.filter((t) => /Fit|Take off|Not this/.test(t)).join(', ').slice(0, 120));
      const f = await clickTile(S, '^Fit to gun in hands');
      const s1 = await S.ev(() => { const p = window.__game.ref.snapshot().player; return { bag: p.mods.length, on: p.gun.card.mods.length }; });
      rec(G, 'Laser + trigger on "Fit to gun in hands" puts the mod on the gun', !!f && s1.on === s0.on + 1 && s1.bag === s0.bag - 1, 'on gun ' + s0.on + ' -> ' + s1.on + ', bag ' + s0.bag + ' -> ' + s1.bag + (f ? '' : ' (no tile)'));
      const still = await debug(S); rec(G, 'Gear menu stays open after fitting (so you can do more)', still.menu && still.menuId === 'gearMenu', 'menu=' + still.menuId);
      await shot(S, 'gear_mod_fitted');
      const gt2 = await allTiles(S);
      rec(G, 'The fitted mod shows on the gun card with a Take off button', gt2.some((t) => /^Take off/i.test(t)), gt2.filter((t) => /Take off/.test(t)).join(', '));
      const d = await clickTile(S, '^Take off');
      const s2 = await S.ev(() => { const p = window.__game.ref.snapshot().player; return { bag: p.mods.length, on: p.gun.card.mods.length }; });
      rec(G, 'Laser + trigger on "Take off" puts the mod back in the bag', !!d && s2.on === s1.on - 1 && s2.bag === s1.bag + 1, 'on gun ' + s1.on + ' -> ' + s2.on + ', bag ' + s1.bag + ' -> ' + s2.bag);
      // fit to the back gun too (needs a second gun)
      await yTap(S); rec(G, 'Y closes the Gear menu', !(await menuOn(S)), '');
      await S.ev(() => { const r = window.__game.ref; const s = r.snapshot(); if (!s.player.gun.other) { r.giveGun('rifle', 1); const q = r.snapshot().pickups.slice(-1)[0]; r.step(0.016, { pickupId: q.id, pickup: true }); } }); await S.frames(5);
      const hasBack = await S.ev(() => !!window.__game.ref.snapshot().player.gun.other);
      if (hasBack) {
        await yHold(S);
        const b0 = await S.ev(() => window.__game.ref.snapshot().player.gun.other.card.mods.length);
        const fb = await clickTile(S, '^Fit to gun in back');
        const b1 = await S.ev(() => window.__game.ref.snapshot().player.gun.other.card.mods.length);
        rec(G, 'Laser + trigger on "Fit to gun in back" mods the gun on your back', !!fb && b1 === b0 + 1, b0 + ' -> ' + b1);
        await yTap(S);
      }
      const paused = await S.ev(() => window.__game.running());
      rec(G, 'Play resumes after closing the Gear menu', paused, '');
      // the stash chest: go to the safe room of the test map
      await S.ev(() => { const r = window.__game.ref; r.setCfg({ startWave: 11, startSafe: true }); r.reset(); r.setCfg({ startWave: 1, startSafe: false }); }); await S.frames(20);
      await X.clearLevelUps(S);
      await S.ev(() => { const r = window.__game.ref; r.giveMod(2); r.giveGun('smg_compact', 2); const s = r.snapshot(); for (const q of s.pickups.filter((p) => p.kind === 'mod' || p.kind === 'gun')) { r.place(q.x, q.z); r.step(0.016, { pickupId: q.id, pickup: true }); } }); await S.frames(5);
      const ch = await S.ev(() => window.__game.ref.snapshot().player.stash.chest);
      await S.ev((c) => window.__game.ref.place(c.x - 1.5, c.z, Math.PI / 2), ch); await S.frames(8);
      await pointAt(S, 'right', [ch.x, 0.6, ch.z]); await S.press('right', 'grip', 6); await S.frames(20); await rest(S);
      const sm = await debug(S);
      rec(G, 'Stash chest: grip opens the stash menu', sm.menu && sm.menuId === 'stashMenu', 'menu=' + sm.menuId);
      const stt = await allTiles(S); await shot(S, 'stash_menu');
      rec(G, 'Stash menu shows Put in stash buttons and the save button (no text boxes)', stt.some((t) => /Put in stash/i.test(t)) && stt.some((t) => /Save game/i.test(t)), stt.filter((t) => /Put in|Save|Take|Rename/.test(t)).join(', ').slice(0, 140));
      const n0 = await S.ev(() => { const s = window.__game.ref.snapshot().player; return { items: s.stash.items.length, mods: s.mods.length, gun: s.gun.id, back: s.gun.other && s.gun.other.id }; });
      // deposit the mod (the last "Put in stash" belongs to the mod bag, the first to the gun in your hands)
      const putMod = await S.ev(() => { let best = null; for (let v = 0.97; v > 0.02; v -= 0.01) for (let u = 0.03; u < 0.98; u += 0.02) { const t = window.__game.xr.menuHit(u, v); if (t && /Put in stash/.test(t)) best = 1; } return best; });
      const pm = await clickTile(S, 'Put in stash');
      const n1 = await S.ev(() => { const s = window.__game.ref.snapshot().player; return { items: s.stash.items.length, mods: s.mods.length, gun: s.gun.id, back: s.gun.other && s.gun.other.id }; });
      rec(G, 'Laser + trigger on "Put in stash" stores it', !!pm && n1.items === n0.items + 1, 'stash ' + n0.items + ' -> ' + n1.items + ' (' + JSON.stringify(n1) + ')');
      await shot(S, 'stash_deposited');
      const sm2 = await debug(S); rec(G, 'Stash menu stays open after putting something in', sm2.menu && sm2.menuId === 'stashMenu', 'menu=' + sm2.menuId);
      const tk = await clickTile(S, '^Take (into my hands|to my back|to my mod bag|this gun)|^Swap with');
      const n2 = await S.ev(() => { const s = window.__game.ref.snapshot().player; return { items: s.stash.items.length, mods: s.mods.length, gun: s.gun.id, back: s.gun.other && s.gun.other.id }; });
      rec(G, 'Laser + trigger on "Take ..." takes it back out', !!tk && (n2.items < n1.items || n2.gun !== n1.gun || n2.back !== n1.back || n2.mods > n1.mods), (tk ? tk.title : 'no tile') + ': ' + JSON.stringify(n1) + ' -> ' + JSON.stringify(n2));
      const why = []; const sv = await clickTile(S, '^Save game here', { why }); if (why.length) console.log('  save tile debug:', why.join(' '));
      const saved = await S.ev(() => { try { const a = JSON.parse(localStorage.getItem('cp_saves_v1') || '[]'); return a.length; } catch (e) { return -1; } });
      const smsg = await S.ev(() => { const m = document.querySelector('#stashMenu .gmsg'); return m ? m.textContent : ''; });
      rec(G, 'Save game here works from VR', !!sv && saved > 0, 'saves ' + saved + ' msg: ' + smsg + (sv ? ' tile ' + JSON.stringify(sv) : ' (no tile)'));
      await yTap(S);
      rec(G, 'Y closes the stash and play resumes', !(await menuOn(S)) && (await running(S)), '');
      // the stash at the door of a new run (take one gun + mods) after you fall
      const errs = await errsOf(S); rec(G, 'No script errors in the menus run', errs.length === 0, errs.join(' | ').slice(0, 200));
    } finally { if (S.logs.length) console.log('  page log:', S.logs.slice(0, 4).join(' | ')); await S.close(); }
  }
  return { gameGroup, menusGroup, clickTile, allTiles };
};
