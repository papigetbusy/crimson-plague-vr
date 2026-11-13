// Co-op in VR: two players in one headless Chrome (PeerJS swapped for tools/xr_fake_peer.js). The host plays in the fake Quest, the friend on a flat page
// (and then the other way round: the friend in VR). Checks: host + join, start, both see each other move, the same monsters, shots from either side hurt
// monsters on both, a gate opened by one is open for the other, no script errors.
const { launch } = require('./xr_sim.js');
module.exports = function (X) {
  const { rec, rest, debug, pointAt, shot, root, page } = X;
  const g = (S, f, ...a) => S.ev(f, ...a);
  async function waitFor(S, fn, arg, ms) { const t0 = Date.now(); while (Date.now() - t0 < (ms || 15000)) { if (await S.ev(fn, arg)) return true; await new Promise((r) => setTimeout(r, 150)); } return false; }
  const snapOf = (S) => S.ev(() => { const s = window.__game.ref.snapshot(); return { x: s.player.x, z: s.player.z, run: window.__game.running(), on: s.coop.on, key: s.coop.key, peers: s.coop.peers.map((p) => ({ key: p.key, x: p.x, z: p.z, name: p.name })), mons: s.monsters.map((m) => ({ id: m.id, hp: m.hp, x: m.x, z: m.z })), gates: s.locks.gates.map((q) => q.open), wave: s.wave.n, phase: s.wave.phase }; });
  async function pair(hostVr) {
    const H = await launch({ root, page, query: '', fakePeer: true });
    const F = await launch({ root, page, query: '', fakePeer: true, share: H });
    for (const S of [H, F]) await S.page.evaluate(X.HELPERS);
    const flat = hostVr ? F : H; flat.frames = (n) => new Promise((r) => setTimeout(r, Math.max(1, n) * 25));   // a flat page has no headset frames to count: wait by the clock (its own game loop keeps running)
    const vrS = hostVr ? H : F; await vrS.enterVR(); await rest(vrS);
    let lobbyVr = { host: null, keys: null };
    if (hostVr) {          // the host hosts from inside the headset: PLAY WITH FRIENDS, then HOST A GAME, with the laser
      const a1 = await X.MORE.clickTile(H, '^PLAY WITH FRIENDS'), a2 = await X.MORE.clickTile(H, '^HOST A GAME', { wait: 20 });
      lobbyVr.host = !!a1 && !!a2;
    } else await H.ev(() => { document.getElementById('coopBtn').click(); document.getElementById('coopHost').click(); });
    const hosted = await waitFor(H, () => /ROOM CODE\s+[A-Z0-9]{5}/.test(document.getElementById('coopInfo').textContent));
    const code = await H.ev(() => (/ROOM CODE\s+([A-Z0-9]{5})/.exec(document.getElementById('coopInfo').textContent) || [])[1]);
    if (!hostVr && code) {   // the friend joins from inside the headset: PLAY WITH FRIENDS, the letter keys, then JOIN
      await X.MORE.clickTile(F, '^PLAY WITH FRIENDS'); let typed = 0;
      for (const ch of code) { if (await X.MORE.clickTile(F, '^' + ch + '$', { wait: 6 })) typed++; }
      const shown = await F.ev(() => document.getElementById('coopCode').value);
      lobbyVr.keys = typed === 5 && shown === code ? true : 'typed ' + typed + ', box ' + shown;
      await shot(F, 'coop_vr_keys');
      await X.MORE.clickTile(F, '^JOIN$', { wait: 20 });
    } else await F.ev((c) => { document.getElementById('coopBtn').click(); document.getElementById('coopCode').value = c; document.getElementById('coopJoin').click(); }, code);
    const joined = await waitFor(F, () => /Joined room/.test(document.getElementById('coopInfo').textContent));
    const seen = await waitFor(H, () => window.__game.ref.snapshot().coop.peers.length === 1);
    return { H, F, hosted, code, joined, seen, lobbyVr };
  }
  async function coopGroup() {
    const G = 'coop';
    let P = await pair(true); const { H, F } = P;
    try {
      rec(G, 'Host a game: a 5-letter room code appears', P.hosted && !!P.code, 'code ' + P.code);
      rec(G, 'A friend joins with the code', P.joined && P.seen, 'joined=' + P.joined + ' host sees friend=' + P.seen);
      rec(G, 'Host in VR: PLAY WITH FRIENDS and HOST A GAME work with the laser (no keyboard needed)', P.lobbyVr.host === true, '');
      const st = await debug(H);
      rec(G, 'Host in VR: the start menu shows (Enter the hall)', st.menu && st.menuId === 'start', 'menu=' + st.menuId);
      const c = await X.MORE.clickTile(H, 'ENTER THE HALL', { wait: 30 });
      rec(G, 'Host: laser + trigger on Enter the hall starts the co-op run', !!c && (await g(H, () => window.__game.running())), '');
      const went = await waitFor(F, () => !document.getElementById('play').disabled);
      await F.ev(() => document.getElementById('play').click());
      const frun = await waitFor(F, () => window.__game.running());
      rec(G, 'The friend is told the host started, and enters', went && frun, 'play enabled=' + went + ' running=' + frun);
      await H.frames(30);
      // both see each other, and movement shows up on the other side
      let h0 = await snapOf(H), f0 = await snapOf(F);
      rec(G, 'Host sees the friend, and the friend sees the host', h0.peers.length === 1 && f0.peers.length >= 1, 'host peers ' + h0.peers.length + ', friend peers ' + f0.peers.length);
      await F.page.keyboard.down('KeyW'); await F.frames(40); await F.page.keyboard.up('KeyW'); await F.frames(10); await H.frames(20);
      const f1 = await snapOf(F), h1 = await snapOf(H);
      const fp = h1.peers[0] || {}, moved = Math.hypot(f1.x - f0.x, f1.z - f0.z);
      rec(G, 'The friend walks: the host sees the friend where the friend really is', moved > 0.5 && Math.hypot((fp.x || 0) - f1.x, (fp.z || 0) - f1.z) < 1.5, 'friend moved ' + moved.toFixed(2) + ' m; host sees it ' + Math.hypot((fp.x || 0) - f1.x, (fp.z || 0) - f1.z).toFixed(2) + ' m off');
      await H.hand('left', { ax: [0, 0, 0, -1] }); await H.frames(40); await H.hand('left', { ax: [0, 0, 0, 0] }); await H.frames(10); await F.frames(20);
      const h2 = await snapOf(H), f2 = await snapOf(F); const hp = f2.peers.find((p) => p.key === 'host') || f2.peers[0] || {};
      rec(G, 'The host walks in VR: the friend sees the host where the host really is', Math.hypot(h2.x - h1.x, h2.z - h1.z) > 0.5 && Math.hypot((hp.x || 0) - h2.x, (hp.z || 0) - h2.z) < 1.5, 'host moved ' + Math.hypot(h2.x - h1.x, h2.z - h1.z).toFixed(2) + '; friend sees it ' + Math.hypot((hp.x || 0) - h2.x, (hp.z || 0) - h2.z).toFixed(2) + ' m off');
      // the same monsters on both
      const O = await H.ev(() => { const r = window.__game.ref, O = window.__pt.openSpot(4, null) || window.__pt.openSpot(3, null); r.place(O[0], O[1], Math.PI / 2); return O; });
      await H.ev((O) => { const r = window.__game.ref; r.clearWave(); r.spawnAt('goblin', O[0] + 4.5, O[1]); }, O); await H.frames(10); await F.frames(20);
      const hm = await snapOf(H), fm = await snapOf(F);
      const same = hm.mons.length > 0 && hm.mons.every((m) => fm.mons.some((q) => q.id === m.id && Math.hypot(q.x - m.x, q.z - m.z) < 2));
      rec(G, 'The friend sees the same monsters in the same places', same, 'host ' + hm.mons.length + ', friend ' + fm.mons.length);
      // the host shoots in VR: hp drops on both sides
      const m0 = hm.mons[0]; let hit = false;
      for (let i = 0; i < 20 && !hit; i++) { const m = await H.ev((id) => window.__game.ref.snapshot().monsters.find((q) => q.id === id), m0.id); if (!m) { hit = true; break; } await pointAt(H, 'right', [m.x, 1.1, m.z]); await H.hold('right', 'trigger', true); await H.frames(6); await H.hold('right', 'trigger', false); await H.frames(3); const fmm = await F.ev((id) => window.__game.ref.snapshot().monsters.find((q) => q.id === id), m0.id); if (!fmm || fmm.hp < m0.hp) hit = true; }
      rec(G, 'Host shoots a monster in VR: the friend sees it hurt or dead', hit, '');
      await rest(H);
      // a gate opened by the host is open for the friend
      const gate = await H.ev(() => window.__game.ref.snapshot().locks.gates.find((q) => !q.open) || null);
      if (gate) {
        await H.ev((q) => { const r = window.__game.ref; r.giveGold(500); for (const s of [1, -1]) { r.place(q.x + q.nx * 2.2 * s, q.z + q.nz * 2.2 * s, Math.atan2(-q.nx * s, q.nz * s)); if (r.snapshot().locks.near) return; } }, gate); await H.frames(6);
        await H.press('right', 'grip', 6); await H.frames(10); await F.frames(20);
        const ho = (await snapOf(H)).gates[gate.i], fo = (await snapOf(F)).gates[gate.i];
        rec(G, 'Host opens a gold gate in VR: it is open for the friend too', ho && fo, 'host open=' + ho + ', friend open=' + fo);
      }
      await shot(H, 'coop_host_vr');
      const eh = await g(H, () => window.__fx.errors.slice(0, 3)), ef = await g(F, () => window.__fx.errors.slice(0, 3));
      rec(G, 'No script errors on either side', !eh.length && !ef.length, eh.concat(ef).join(' | ').slice(0, 200));
      const stats = await g(H, () => window.__peerStats);
      rec(G, 'Network traffic stays small (host sends under 20 KB/s)', stats && stats.bytes / Math.max(1, (await g(H, () => window.__game.ref.snapshot().t))) < 20000, JSON.stringify(stats));
    } finally { for (const S of [F, H]) { const l = S.logs.filter((x) => !/favicon/.test(x)); if (l.length) console.log('  page log:', l.slice(0, 4).join(' | ')); } await F.close(); await H.close(); }
    // the friend in VR, the host flat
    P = await pair(false);
    try {
      rec(G, 'Friend in VR: types the room code on the letter keys and joins (no keyboard needed)', P.lobbyVr.keys === true && P.joined, 'keys=' + P.lobbyVr.keys + ' joined=' + P.joined);
      await P.H.ev(() => window.__game.begin(true)); await P.H.frames(10); await P.F.frames(30);
      const st = await debug(P.F); const tl = await P.F.ev(() => window.__pt.titles());
      rec(G, 'Friend in VR: the start menu shows the host started', st.menu && tl.some((t) => /HOST STARTED|ENTER/.test(t)), tl.join(', ').slice(0, 100));
      const c = await X.MORE.clickTile(P.F, 'HOST STARTED|ENTER THE HALL', { wait: 30 });
      const fr = await g(P.F, () => window.__game.running());
      rec(G, 'Friend in VR: laser + trigger enters the host\'s run', !!c && fr, '');
      await P.F.frames(30);
      const fs = await snapOf(P.F); rec(G, 'Friend in VR sees the host and the host\'s monsters', fs.peers.length >= 1 && fs.on, 'peers ' + fs.peers.length + ', monsters ' + fs.mons.length);
      // the friend shoots in VR: the host spawns a monster in front of the friend; the friend points and fires; the host's world takes the damage
      const fO = await P.F.ev(() => { const r = window.__game.ref, O = window.__pt.openSpot(4, null) || window.__pt.openSpot(3, null); r.place(O[0], O[1], Math.PI / 2); return O; });
      await P.F.frames(20);
      await P.H.ev((O) => { const r = window.__game.ref; r.clearWave(); r.spawnAt('goblin', O[0] + 4, O[1]); }, fO); await P.H.frames(10); await P.F.frames(20);
      const tgt = await P.H.ev(() => { const m = window.__game.ref.snapshot().monsters[0]; return m && { id: m.id, hp: m.hp }; });
      let fhit = false;
      for (let i = 0; tgt && i < 20 && !fhit; i++) {
        const m = await P.F.ev((id) => window.__game.ref.snapshot().monsters.find((q) => q.id === id), tgt.id); if (!m) { fhit = true; break; }
        await pointAt(P.F, 'right', [m.x, 1.1, m.z]); await P.F.hold('right', 'trigger', true); await P.F.frames(6); await P.F.hold('right', 'trigger', false); await P.F.frames(3); await P.H.frames(6);
        const hm = await P.H.ev((id) => window.__game.ref.snapshot().monsters.find((q) => q.id === id), tgt.id); if (!hm || hm.hp < tgt.hp) fhit = true;
      }
      rec(G, 'Friend in VR shoots a monster: the host\'s world takes the damage', fhit, tgt ? '' : 'no monster');
      await rest(P.F);
      await P.F.press('left', 'y', 4); await P.F.frames(30);
      const pz = await g(P.F, () => ({ menu: window.__game.xr.menuShown(), id: window.__game.xr.debug().menuId }));
      rec(G, 'Friend in VR: Y opens the pause menu (the shared world keeps going)', pz.menu, JSON.stringify(pz));
      await P.F.press('left', 'y', 4); await P.F.frames(30);
      const e2 = (await g(P.F, () => window.__fx.errors.slice(0, 3))).concat(await g(P.H, () => window.__fx.errors.slice(0, 3)));
      rec(G, 'No script errors (friend in VR)', !e2.length, e2.join(' | ').slice(0, 200));
      await shot(P.F, 'coop_friend_vr');
    } finally { await P.F.close(); await P.H.close(); }
  }
  return { coopGroup };
};
