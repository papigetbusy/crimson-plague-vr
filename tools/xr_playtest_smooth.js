// Fake-Quest checks for the VR menu smoothing (phase 2), on every VR menu of the REAL game: start + class pick, pause, codex,
// level-up, merchant (shop), stash, gear, the map and game over. For each one: it opens, its 150 ms fade/grow finishes, the time of the
// frame that opens it, the hover frame lands on a whole card or button (never on text) with a light tick, a click still works with a
// firmer tick, long lists scroll with the stick and glide to a stop, Y backs out, the closing copy fades away, and nothing is stuck after.
// Run alone: NODE_PATH=/workspace/xrsim/node_modules node tools/xr_playtest.js --only=smooth --shots dir
module.exports = function (X) {
  const { open, rest, rec, debug, pointAt } = X;
  const G = 'smooth';
  const sm = (S) => S.ev(() => window.__game.xr.smooth ? window.__game.xr.smooth() : null);
  const yTap = async (S) => { await S.press('left', 'y', 4); await S.frames(30); };
  const yHold = async (S) => { await S.hold('left', 'y', true); await S.frames(60); await S.hold('left', 'y', false); await S.frames(10); };
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const frameMs = (S) => S.ev(() => { const p = window.__game.perf(); let t = 0; for (const k in p.ms) t += p.ms[k]; const out = { ms: t / Math.max(1, p.frames), stages: Object.assign({}, p.ms), n: p.frames }; window.__game.perfReset(); return out; });
  async function shot(S, name) {
    await X.shot(S, name); if (!X.shotsDir) return;
    const url = await S.ev(() => { const c = window.__game.xr.menuCanvas && window.__game.xr.menuCanvas(); return window.__game.xr.menuShown() && c ? c.toDataURL('image/png') : null; });
    if (url) require('fs').writeFileSync(X.shotsDir + '/' + name + '_vrpanel.png', Buffer.from(url.split(',')[1], 'base64'));
  }
  // open: run `act`, then step one frame at a time until the panel shows; then follow its fade until it is fully in
  async function watchOpen(S, label, act, want) {
    await S.ev(() => window.__game.perfReset());
    await act();
    let first = null, f = 0, base = [];
    for (; f < 60; f++) {
      const d = await S.ev(() => ({ m: window.__game.xr.menuShown(), id: window.__game.xr.debug().menuId }));
      const fm = await frameMs(S);
      if (d.m && (!want || d.id === want)) { first = { f, id: d.id, ms: fm.ms, stages: fm.stages, s: await sm(S) }; break; }
      base.push(fm.ms); await S.frames(1);
    }
    if (!first) { rec(G, label + ': opens', false, 'no panel after 60 frames'); return null; }
    let k = first.s, n = 0; const ks = [k.menuK.toFixed(2)];
    for (; n < 40 && (k.menuK < 1 || k.opacity < 1 || Math.abs(k.scale - 1) > 1e-3); n++) { await S.frames(1); k = await sm(S); if (n < 8) ks.push(k.menuK.toFixed(2)); }
    const typ = base.length ? base.slice().sort((a, b) => a - b)[Math.floor(base.length / 2)] : 0;
    rec(G, label + ': opens with a fade/grow (starts clear and small, eases to full) and it finishes', first.s.opacity < 0.6 && first.s.scale < 0.99 && k.menuK === 1 && k.opacity === 1 && Math.abs(k.scale - 1) < 1e-3, 'menu ' + first.id + '; first frame opacity ' + first.s.opacity.toFixed(2) + ' scale ' + first.s.scale.toFixed(3) + '; menuK ' + ks.join(' ') + ' ... full after ' + (n + 1) + ' frames');
    const top = Object.entries(first.stages).sort((a, b) => b[1] - a[1]).slice(0, 3).map((e) => e[0] + ' ' + e[1].toFixed(1)).join(', ');
    X.openMs = X.openMs || []; X.openMs.push({ menu: label, ms: +first.ms.toFixed(1), typical: +typ.toFixed(1) });
    rec(G, label + ': the frame that opens it stays short (sim CPU, under 40 ms incl. software rendering)', first.ms < 40, first.ms.toFixed(1) + ' ms (normal frames here ~' + typ.toFixed(1) + ' ms; ' + top + ')');
    return first;
  }
  // hover: a tile gets the gliding frame and a light tick; text (the title) never does
  async function hoverCheck(S, label, re) {
    await S.pulses();
    const t = await S.ev((re) => window.__pt.menuFind(re), re);
    if (!t) { rec(G, label + ': a tile to point at', false, re); return null; }
    const w = await S.ev((t) => window.__pt.menuPoint(t[0], t[1]), t); await pointAt(S, 'right', w); await S.frames(12);
    const h = await sm(S), d = await debug(S), p = await S.pulses();
    const tile = await S.ev((title) => { const T = window.__game.xr.menuTiles().find((q) => q.title === title); return T || null; }, d.hover);
    const cx = h.hiRect ? h.hiRect.x + 0.5 : -1, cy = h.hiRect ? 0.5 + h.hiRect.y : -1;
    rec(G, label + ': pointing at "' + t[2].slice(0, 30) + '" lights the whole tile (gliding frame) with a light tick', d.hover === t[2] && h.hi && h.hiA > 0.8 && tile && Math.abs(cx - tile.u) < 0.02 && Math.abs(cy - tile.v) < 0.03 && p.some((q) => q.hand === 'right' && q.s <= 0.15),
      'hover ' + d.hover + ' a ' + h.hiA.toFixed(2) + ' frame centre ' + cx.toFixed(3) + ',' + cy.toFixed(3) + ' tile ' + (tile ? tile.u.toFixed(3) + ',' + tile.v.toFixed(3) : '-') + ' pulses ' + JSON.stringify(p.map((q) => q.s)));
    // the title area: text only, no highlight
    const wt = await S.ev(() => window.__pt.menuPoint(0.5, 0.95)); await pointAt(S, 'right', wt); await S.frames(14);
    const h2 = await sm(S), d2 = await debug(S);
    rec(G, label + ': pointing at the title text lights nothing (text and labels never highlight)', !d2.hover && h2.hiA < 0.08, 'hover ' + d2.hover + ' a ' + h2.hiA.toFixed(2));
    return t;
  }
  async function click(S, re, wait) {
    const t = await S.ev((re) => window.__pt.menuFind(re), re); if (!t) return null;
    const w = await S.ev((t) => window.__pt.menuPoint(t[0], t[1]), t); await pointAt(S, 'right', w); await S.frames(6); await S.pulses();
    await S.press('right', 'trigger', 4); await S.frames(wait || 14); const p = await S.pulses(); await rest(S); return { title: t[2], pulses: p };
  }
  async function scrollCheck(S, label) {
    const d0 = await debug(S); if (!(d0.maxScroll > 40)) return false;
    await rest(S); await S.hand('right', { ax: [0, 0, 0, 1] }); await S.frames(8); await S.hand('right', { ax: [0, 0, 0, 0] });
    const a = (await debug(S)).scroll, v = (await sm(S)).scrollV; await S.frames(2); const b = (await debug(S)).scroll;
    let n = 0, s = await sm(S); for (; n < 60 && Math.abs(s.scrollV) > 0; n++) { await S.frames(1); s = await sm(S); }
    const c = (await debug(S)).scroll; await S.frames(5); const e = (await debug(S)).scroll;
    rec(G, label + ': the right stick scrolls, then the list glides on a little and comes to rest', a > d0.scroll && (b > a || a >= d0.maxScroll) && c === e && s.scrollV === 0, 'scroll ' + d0.scroll.toFixed(0) + ' -> ' + a.toFixed(0) + ' (speed ' + v.toFixed(0) + ' px/s at release) -> glide ' + b.toFixed(0) + ' -> rest ' + c.toFixed(0) + ' after ' + n + ' frames, of ' + d0.maxScroll.toFixed(0));
    // trigger-drag: the list follows the laser 1:1 and a pull stops a glide
    const p0 = await S.ev(() => window.__pt.menuPoint(0.5, 0.35)), p1 = await S.ev(() => window.__pt.menuPoint(0.5, 0.6));
    await pointAt(S, 'right', p0); await S.frames(6); const s0 = (await debug(S)).scroll; await S.hold('right', 'trigger', true); await S.frames(3);
    for (let i = 1; i <= 6; i++) { await pointAt(S, 'right', p0.map((q, j) => q + (p1[j] - q) * i / 6)); }
    const s1 = (await debug(S)).scroll; await S.hold('right', 'trigger', false); await S.frames(30); const s2 = (await debug(S)).scroll, st = await sm(S), id = (await debug(S)).menuId;
    rec(G, label + ': a trigger-drag moves the list (no click fires), then it settles', s1 !== s0 && !st.dragging && st.scrollV === 0 && id === d0.menuId, 'scroll ' + s0.toFixed(0) + ' -> ' + s1.toFixed(0) + ' -> ' + s2.toFixed(0) + ', menu still ' + id);
    await rest(S); return true;
  }
  // closed: the copy fades away, no highlight, laser off, no input left held
  async function closedCheck(S, label, how) {
    const s0 = await sm(S); let n = 0, s = s0; for (; n < 40 && (s.ghost || s.ghostK > 0); n++) { await S.frames(1); s = await sm(S); }
    const d = await debug(S), las = await S.ev(() => { let v = 0; window.__game.xr.rig.traverse((o) => { if (o.isMesh && o.geometry && o.geometry.type === 'BoxGeometry' && o.geometry.parameters.width === 0.004 && o.visible) { for (let p = o; p; p = p.parent) if (!p.visible) return; v++; } }); return v; });
    rec(G, label + ': ' + how + ' closes it; the closing fade finishes and nothing is left on screen or held', !d.menu && !s.ghost && s.ghostK === 0 && !s.hi && las === 0 && !s.dragging && s.scrollV === 0, 'ghost faded in ' + n + ' frames (started at ' + s0.ghostK.toFixed(2) + '), lasers ' + las + ', menu ' + d.menu);
  }
  async function firesAfter(S, label) {
    await rest(S); const a0 = await S.ev(() => window.__game.ref.snapshot().player.ammo);
    await S.hold('right', 'trigger', true); await S.frames(4); await S.hold('right', 'trigger', false); await S.frames(4);
    const a1 = await S.ev(() => window.__game.ref.snapshot().player.ammo); const run = await S.ev(() => window.__game.running());
    rec(G, label + ': back in play the trigger fires the gun again (no stuck menu input)', run && a1 < a0, 'ammo ' + a0 + ' -> ' + a1 + ', running ' + run);
    if (a1 < a0) { await S.press('left', 'x', 4); await S.frames(60); }
  }

  async function smoothGroup() {
    const S = await open('');
    try {
      // 1. start menu + class pick (the title)
      await S.frames(30);
      const s0 = await sm(S); const d0 = await debug(S);
      rec(G, 'Start menu: shown at the title, fully faded in', d0.menu && d0.menuId === 'start' && s0 && s0.menuK === 1, JSON.stringify(s0 && { k: s0.menuK, o: s0.opacity }));
      await hoverCheck(S, 'Start menu (class pick)', '^Witch');
      const c1 = await click(S, '^Witch');
      const sel = await S.ev(() => document.querySelector('[data-cls="witch"]').classList.contains('sel'));
      rec(G, 'Class pick: laser + trigger still picks the class, with a firmer click tick', !!c1 && sel && c1.pulses.some((q) => q.s >= 0.3), 'selected ' + sel + ' pulses ' + JSON.stringify(c1 && c1.pulses.map((q) => q.s)));
      await shot(S, 'smooth_start_hover');
      const c2 = await click(S, 'ENTER THE HALL', 30);
      await closedCheck(S, 'Start menu', 'ENTER THE HALL');
      if (!(await S.ev(() => window.__game.running()))) await S.ev(() => window.__game.begin && window.__game.begin(true));
      await S.ev(() => { const r = window.__game.ref, O = window.__pt.openSpot(4, null) || window.__pt.openSpot(3, null); r.clearWave(); r.place(O[0], O[1], Math.PI / 2); }); await rest(S);
      await firesAfter(S, 'Start menu');
      // 2. pause, 3. codex (a straight menu-to-menu switch), back to pause, resume
      await watchOpen(S, 'Pause (Y)', () => S.press('left', 'y', 4), 'start');
      await hoverCheck(S, 'Pause', '^RESUME');
      // mid-transition picture for the report
      const cx = await S.ev(() => window.__pt.menuFind('CODEX'));
      if (cx) {
        const w = await S.ev((t) => window.__pt.menuPoint(t[0], t[1]), cx); await pointAt(S, 'right', w); await S.frames(6);
        await S.press('right', 'trigger', 4);
        let dip = false, ids = []; for (let i = 0; i < 40; i++) { await S.frames(1); const s = await sm(S), d = await debug(S); if (s.dip) dip = true; ids.push(d.menuId); if (d.menuId === 'codex' && s.menuK === 1) break; }
        const s = await sm(S), d = await debug(S);
        rec(G, 'Pause -> Codex: the old menu dips out, then the Codex fades in fully (no stuck half-way state)', dip && d.menuId === 'codex' && s.menuK === 1 && s.opacity === 1, 'dip ' + dip + ' ids ' + [...new Set(ids)].join('>') + ' k ' + s.menuK);
        await rest(S);
        await hoverCheck(S, 'Codex', '.');
        await scrollCheck(S, 'Codex');
        await shot(S, 'smooth_codex_scrolled');
        await S.press('left', 'y', 4); let back = null; for (let i = 0; i < 40; i++) { await S.frames(1); const dd = await debug(S), ss = await sm(S); if (dd.menuId === 'start' && ss.menuK === 1) { back = dd; break; } }
        rec(G, 'Codex: Y backs out to the pause menu (dips, then fades in fully)', !!back, back ? 'menu start' : JSON.stringify(await debug(S)).slice(0, 120));
      }
      await S.press('left', 'y', 4); await S.frames(2);
      await closedCheck(S, 'Pause', 'Y');
      await firesAfter(S, 'Pause');
      // 4. map (double-tap Y): fades in, Y fades it out
      await S.press('left', 'y', 3); await S.frames(3); await S.press('left', 'y', 3);
      let mk = [], mOn = false; for (let i = 0; i < 30; i++) { await S.frames(1); const s = await sm(S); mk.push(+s.mapK.toFixed(2)); if (s.mapK === 1) { mOn = true; break; } }
      const md = await debug(S);
      rec(G, 'Map: double-tap Y shows it with a fade/grow that finishes', md.mapShown && mOn && mk[0] < 0.9, 'mapK ' + mk.slice(0, 6).join(' ') + ' ...');
      await S.press('left', 'y', 4); let mOff = false, mn = 0; for (; mn < 30; mn++) { await S.frames(1); const s = await sm(S); if (!s.mapVisible && s.mapK === 0) { mOff = true; break; } }
      const md2 = await debug(S);
      rec(G, 'Map: a Y tap closes it with a fade (gone after it, no pause menu)', mOff && !md2.mapShown && !md2.menu, 'gone after ' + (mn + 1) + ' frames, menu ' + md2.menu);
      // 5. gear (hold Y)
      await S.ev(() => { const r = window.__game.ref; r.giveMod(2); r.giveMod(3); r.giveMod(2); });
      await watchOpen(S, 'Gear (hold Y)', async () => { await S.hold('left', 'y', true); await S.frames(60); await S.hold('left', 'y', false); }, 'gearMenu');
      await hoverCheck(S, 'Gear', 'Fit to gun in hands|Take off|.');
      await scrollCheck(S, 'Gear');
      await shot(S, 'smooth_gear');
      await S.press('left', 'y', 4); await S.frames(2); await closedCheck(S, 'Gear', 'Y'); await firesAfter(S, 'Gear');
      // 6. level-up
      await watchOpen(S, 'Level-up', () => S.ev(() => { const r = window.__game.ref, l = r.snapshot().level; r.giveXp(l.need - l.xp + 1); }), 'levelup');
      const lt = await S.ev(() => window.__pt.titles()); await hoverCheck(S, 'Level-up', esc(lt[0] || '.'));
      await shot(S, 'smooth_levelup_hover');
      const yl = await S.ev(() => window.__game.xr.debug().menuId); await S.press('left', 'y', 4); await S.frames(20); const yl2 = await debug(S);
      rec(G, 'Level-up: Y does what it did before (the original game: a card must be picked; the menu stays and is not stuck)', yl === 'levelup' && (yl2.menuId === 'levelup' || !yl2.menu), 'after Y: ' + (yl2.menu ? yl2.menuId : 'closed'));
      const lu = await X.clearLevelUps(S); const ld = await debug(S);
      rec(G, 'Level-up: laser + trigger picks the cards and play carries on', lu.n >= 1 && !ld.menu, lu.n + ' picked');
      await closedCheck(S, 'Level-up', 'picking the cards');
      await firesAfter(S, 'Level-up');
      // 7. merchant (shop) and 8. stash, in the real safe room
      await S.ev(() => { const r = window.__game.ref; r.setCfg({ startWave: 11, startSafe: true }); r.reset(); r.setCfg({ startWave: 1, startSafe: false }); }); await S.frames(20);
      await X.clearLevelUps(S);
      const sf = await S.ev(() => { const s = window.__game.ref.snapshot(); return { safe: s.safe, m: s.merchant, ch: s.player.stash.chest }; });
      if (sf.safe && sf.m) {
        await S.ev(() => window.__game.ref.giveGold(3000));
        await watchOpen(S, 'Merchant (shop)', () => S.ev((c) => window.__game.ref.place(c.x - 1.2, c.z, Math.PI / 2), sf.m), 'levelup');
        await hoverCheck(S, 'Merchant', '.');
        await scrollCheck(S, 'Merchant');
        await shot(S, 'smooth_shop');
        const g0 = await S.ev(() => window.__game.ref.snapshot().gold);
        const names = await S.ev(() => { const s = window.__game.ref.snapshot(); return s.shop ? s.shop.skills.concat(s.shop.supplies).filter((c) => c.afford && c.id !== 'leave' && c.id !== 'mend').map((c) => c.name) : []; });
        let bought = null; for (const n of names) { bought = await click(S, esc(n), 20); if (bought) break; }
        const g1 = await S.ev(() => window.__game.ref.snapshot().gold);
        rec(G, 'Merchant: laser + trigger still buys (gold spent), with the click tick', !!bought && g1 < g0 && bought.pulses.some((q) => q.s >= 0.3), (bought ? bought.title : 'none') + ': ' + g0 + ' -> ' + g1);
        await S.press('left', 'y', 4); await S.frames(2); await closedCheck(S, 'Merchant', 'Y');
        await S.ev((c) => window.__game.ref.place(c.x - 4, c.z, -Math.PI / 2), sf.m); await S.frames(20);
      } else rec(G, 'Merchant: safe room reached', false, JSON.stringify(sf));
      if (sf.safe && sf.ch) {
        await watchOpen(S, 'Stash', async () => { await S.ev((c) => window.__game.ref.place(c.x - 1.5, c.z, Math.PI / 2), sf.ch); await S.frames(8); await pointAt(S, 'right', [sf.ch.x, 0.6, sf.ch.z]); await S.press('right', 'grip', 6); }, 'stashMenu');
        await rest(S);
        await hoverCheck(S, 'Stash', 'Put in stash|Save game here|.');
        await scrollCheck(S, 'Stash');
        await shot(S, 'smooth_stash');
        const n0 = await S.ev(() => window.__game.ref.stashList ? window.__game.ref.stashList().length : -1);
        const put = await click(S, 'Put in stash', 20); const n1 = await S.ev(() => window.__game.ref.stashList ? window.__game.ref.stashList().length : -1);
        rec(G, 'Stash: laser + trigger still stores an item', !!put && n1 > n0, n0 + ' -> ' + n1);
        await S.press('left', 'y', 4); await S.frames(2); await closedCheck(S, 'Stash', 'Y');
      }
      // 9. game over
      await S.ev(() => window.__game.ref.reset()); await S.frames(10);
      if ((await S.ev(() => window.__game.xr.debug().menuId)) === 'stashMenu') { await S.press('left', 'y', 4); await S.frames(30); }
      await S.ev(() => { const r = window.__game.ref, O = window.__pt.openSpot(4, null) || window.__pt.openSpot(3, null); r.place(O[0], O[1], Math.PI / 2); const k = r.kinds; const kd = Object.keys(k).find((id) => !k[id].boss && !k[id].mini && !k[id].ranged) || 'goblin'; r.setHp(1); for (let i = 0; i < 4; i++) r.spawnAt(kd, O[0] + 0.9 * Math.cos(i * 1.6), O[1] + 0.9 * Math.sin(i * 1.6)); });
      await watchOpen(S, 'Game over', async () => { for (let i = 0; i < 60; i++) { await S.frames(5); if (await S.ev(() => !!window.__game.ref.snapshot().over)) break; } }, 'gameover');
      await hoverCheck(S, 'Game over', 'RISE AGAIN');
      await shot(S, 'smooth_gameover_hover');
      const ra = await click(S, 'RISE AGAIN', 40);
      if ((await S.ev(() => window.__game.xr.debug().menuId)) === 'stashMenu') { await S.press('left', 'y', 4); await S.frames(30); }
      const rr = await S.ev(() => ({ over: !!window.__game.ref.snapshot().over, run: window.__game.running() }));
      rec(G, 'Game over: RISE AGAIN still starts a new run', !!ra && !rr.over && rr.run, JSON.stringify(rr));
      await closedCheck(S, 'Game over', 'RISE AGAIN');
      // 10. the laser: steady while the hand trembles, but a sweep is followed at once
      await watchOpen(S, 'Pause again (laser check)', () => S.press('left', 'y', 4), 'start');
      const pt = await S.ev(() => window.__pt.menuPoint(0.5, 0.5)); await pointAt(S, 'right', pt); await S.frames(10);
      const base = await S.ev((f) => window.__pt.look(f, window.__pt.menuPoint(0.5, 0.5)), [0.18, -0.42, -0.32]);
      const jit = []; for (let i = 0; i < 12; i++) { const a = (i % 2 ? 1 : -1) * 0.006; const q = await S.ev((b, a) => { const T = window.__game.THREE, q = new T.Quaternion(b[0], b[1], b[2], b[3]).multiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), a)); return [q.x, q.y, q.z, q.w]; }, base, a); await S.hand('right', { p: [0.18, -0.42, -0.32], q }); await S.frames(1); jit.push((await sm(S)).laserDir); }
      const spread = (() => { let mx = 0; for (const a of jit) for (const b of jit) if (a && b) mx = Math.max(mx, Math.acos(Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))); return mx; })();
      rec(G, 'Laser: a 0.7 degree hand tremor moves the beam much less (steady)', spread < 0.012 * 0.7, 'beam wobble ' + (spread * 57.3).toFixed(2) + ' deg for a ' + (0.012 * 57.3).toFixed(2) + ' deg hand wobble');
      const tR = await S.ev(() => window.__pt.menuFind('^RESUME')); const wR = await S.ev((t) => window.__pt.menuPoint(t[0], t[1]), tR); await pointAt(S, 'right', wR);
      const hv1 = (await debug(S)).hover;
      rec(G, 'Laser: a quick point at RESUME is followed at once (hover within 3 frames, no lag on the click)', hv1 === tR[2], 'hover ' + hv1);
      await S.press('right', 'trigger', 4); await S.frames(10); const rn = await S.ev(() => window.__game.running());
      rec(G, 'Laser: the pull right after pressing it resumes', rn, 'running ' + rn);
      await closedCheck(S, 'Pause', 'RESUME');
      if (X.openMs) console.log('  open-frame times: ' + JSON.stringify(X.openMs));
      const errs = await S.ev(() => window.__fx.errors.slice(0, 3));
      rec(G, 'No script errors in the menu smoothing run', errs.length === 0, errs.join(' | ').slice(0, 200));
    } finally { await S.close(); }
  }
  return { smoothGroup };
};
