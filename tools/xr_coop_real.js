// Co-op over the REAL PeerJS public server (not the fake): two players in two windows of one Chrome on this box, flat pages.
// Checks the real matchmaking + WebRTC link: host gets a code, friend joins, both start, each sees the other move. Usage: NODE_PATH=... node tools/xr_coop_real.js
const { launch } = require('./xr_sim.js'), path = require('path');
const root = path.join(__dirname, '..');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitFor(S, fn, arg, ms) { const t0 = Date.now(); while (Date.now() - t0 < (ms || 30000)) { if (await S.ev(fn, arg)) return true; await sleep(250); } return false; }
(async () => {
  let ok = 0, n = 0; const rec = (name, pass, det) => { n++; if (pass) ok++; console.log((pass ? 'PASS' : 'FAIL') + ' [coop-real] ' + name + (det !== undefined ? '  -- ' + det : '')); };
  const H = await launch({ root, query: '', realPeer: true });
  const F = await launch({ root, query: '', realPeer: true, share: H });
  try {
    rec('PeerJS library loads from unpkg', !(await H.ev(() => window.__peerFailed)) && await H.ev(() => typeof window.Peer === 'function'));
    await H.ev(() => { document.getElementById('coopBtn').click(); document.getElementById('coopHost').click(); });
    const hosted = await waitFor(H, () => /ROOM CODE\s+[A-Z0-9]{5}/.test(document.getElementById('coopInfo').textContent), null, 30000);
    const code = await H.ev(() => (/ROOM CODE\s+([A-Z0-9]{5})/.exec(document.getElementById('coopInfo').textContent) || [])[1]);
    rec('Host gets a room code from the real server', hosted, 'code ' + code + ' / ' + (await H.ev(() => document.getElementById('coopInfo').textContent)).slice(0, 80));
    // can this machine make a WebRTC link at all? (a headless box with no usable network interface gathers zero candidates)
    const cands = await F.ev(() => new Promise((res) => { let n = 0; const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] }); pc.createDataChannel('x'); pc.onicecandidate = (e) => { if (e.candidate) n++; else res(n); }; pc.createOffer().then((o) => pc.setLocalDescription(o)); setTimeout(() => res(n), 8000); }));
    if (!cands) {
      console.log('NOTE this machine cannot make any WebRTC link (0 ICE candidates), so the real link is checked on a headset/PC; here: a failed join must give up with a clear message, not hang');
      await F.ev((c) => { window.__joinTimeoutMs = 6000; document.getElementById('coopBtn').click(); document.getElementById('coopCode').value = c; document.getElementById('coopJoin').click(); }, code);
      const told = await waitFor(F, () => /Could not connect to the host/.test(document.getElementById('coopInfo').textContent + ' ' + document.body.innerText), null, 15000);
      rec('A join that cannot connect gives up with a clear message (no endless "Joining room...")', told, (await F.ev(() => document.getElementById('coopInfo').textContent)).slice(0, 90));
      const again = await F.ev(() => !document.getElementById('coopJoin').disabled && !document.getElementById('coopJoin').hidden && !document.getElementById('coopPanel').hidden);
      rec('After it gives up, JOIN can be pressed again', again);
      const errs = [...H.logs, ...F.logs].filter((l) => /pageerror/.test(l));
      rec('No script errors', errs.length === 0, errs.slice(0, 3).join(' | '));
      throw { done: true };
    }
    await F.ev((c) => { document.getElementById('coopBtn').click(); document.getElementById('coopCode').value = c; document.getElementById('coopJoin').click(); }, code);
    const joined = await waitFor(F, () => /Joined room/.test(document.getElementById('coopInfo').textContent), null, 30000);
    const seen = await waitFor(H, () => window.__game.ref.snapshot().coop.peers.length === 1, null, 30000);
    rec('Friend joins over WebRTC and the host sees them', joined && seen, 'friend: ' + (await F.ev(() => document.getElementById('coopInfo').textContent)).slice(0, 80));
    await H.ev(() => document.getElementById('play').click());
    const fr = await waitFor(F, () => !document.getElementById('play').disabled, null, 15000); await F.ev(() => document.getElementById('play').click());
    const both = await waitFor(H, () => window.__game.running(), null, 10000) && await waitFor(F, () => window.__game.running(), null, 10000);
    rec('Both enter the run', fr && both);
    await sleep(1500);
    const pos = (S) => S.ev(() => { const s = window.__game.ref.snapshot(); return { me: [s.player.x, s.player.z], peers: s.coop.peers.map((p) => [p.x, p.z]) }; });
    const f0 = await pos(F);
    await F.page.keyboard.down('KeyW'); await sleep(1200); await F.page.keyboard.up('KeyW'); await sleep(800);
    const f1 = await pos(F), h1 = await pos(H);
    const moved = Math.hypot(f1.me[0] - f0.me[0], f1.me[1] - f0.me[1]), off = h1.peers[0] ? Math.hypot(h1.peers[0][0] - f1.me[0], h1.peers[0][1] - f1.me[1]) : 99;
    rec('Friend walks; host sees them in the right place over the real link', moved > 0.5 && off < 0.6, 'moved ' + moved.toFixed(2) + ' m, host sees it ' + off.toFixed(2) + ' m off');
    const errs = [...H.logs, ...F.logs].filter((l) => /pageerror|error:/.test(l) && !/favicon|AudioContext/.test(l));
    rec('No script errors', errs.length === 0, errs.slice(0, 3).join(' | '));
  } catch (e) { if (!e.done) rec('ran without crashing', false, e.message); }
  console.log(ok + '/' + n + ' passed');
  await F.close(); await H.close(); process.exit(ok === n ? 0 : 1);
})();
