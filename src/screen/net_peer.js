/* The real link between phones: PeerJS (WebRTC) with its free public matchmaking server, so a room code is all anyone needs (no server of ours, no accounts).
   The library is loaded from a CDN in the page head; if it did not load, available() is false and the lobby says so. Everything above this file talks only through
   host(handlers) and join(code, handlers), so a test can swap in a fake. */
const NetPeer = (function () {
  const PREFIX = 'cplague-1-', ALPHA = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';   // no 0/O/1/I: a code read out loud or typed on a phone must be hard to get wrong
  const ICE = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }, { urls: 'stun:global.stun.twilio.com:3478' },
    { urls: 'turn:openrelay.metered.ca:80', username: 'openrelayproject', credential: 'openrelayproject' }, { urls: 'turn:openrelay.metered.ca:443', username: 'openrelayproject', credential: 'openrelayproject' }] };   // a public relay for phones whose networks block a direct link
  const available = () => typeof Peer !== 'undefined';
  const makeCode = () => { let s = ''; for (let i = 0; i < 5; i++) s += ALPHA[Math.floor(Math.random() * ALPHA.length)]; return s; };
  const clean = (c) => String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
  const friendly = (err) => {
    const t = err && err.type;
    if (t === 'peer-unavailable') return 'No game with that code. Check the letters and that the host is waiting.';
    if (t === 'network' || t === 'server-error' || t === 'socket-error' || t === 'socket-closed') return 'Could not reach the matchmaking server. Check your connection and try again.';
    if (t === 'browser-incompatible') return 'This browser can not play with friends.';
    return 'Connection problem' + (t ? ' (' + t + ')' : '') + '.';
  };
  // host: handlers = { ready(code), join(key), msg(key, msg), leave(key), error(text) }
  function host(h) {
    let peer = null, tries = 0, n = 0, closed = false; const conns = new Map();
    function open() {
      const code = makeCode();
      peer = new Peer(PREFIX + code, { config: ICE });
      peer.on('open', () => h.ready(code));
      peer.on('error', (err) => { if (err && err.type === 'unavailable-id' && tries++ < 6) { try { peer.destroy(); } catch (e) { /* gone */ } open(); } else h.error(friendly(err)); });
      peer.on('connection', (conn) => {
        const key = 'p' + (++n);
        conn.on('open', () => { conns.set(key, conn); h.join(key); });
        conn.on('data', (m) => h.msg(key, m));
        conn.on('close', () => { if (conns.delete(key)) h.leave(key); });
        conn.on('error', () => { if (conns.delete(key)) h.leave(key); });
      });
      peer.on('disconnected', () => { if (!closed) { try { peer.reconnect(); } catch (e) { /* the server link will come back or the lobby says so */ } } });
    }
    open();
    return { send(key, msg) { const c = conns.get(key); if (c && c.open) c.send(msg); }, close() { closed = true; try { peer.destroy(); } catch (e) { /* gone */ } }, count: () => conns.size };
  }
  // friend: handlers = { open(), msg(msg), close(), error(text) }
  function join(code, h) {
    let conn = null, up = false, done = false;
    const peer = new Peer(undefined, { config: ICE });
    const failOnce = (t) => { if (done || up) return; done = true; clearTimeout(timer); try { peer.destroy(); } catch (e) { /* gone */ } h.error(t); };
    // a link that never opens (a network that blocks the direct link and the relay) must not leave you on "Joining room..." forever
    const timer = setTimeout(() => failOnce('Could not connect to the host after 20 seconds. Check the code, make sure the host is still waiting, and try again (being on the same Wi-Fi helps).'), (typeof window !== 'undefined' && window.__joinTimeoutMs) || 20000);
    peer.on('open', () => {
      conn = peer.connect(PREFIX + clean(code), { reliable: true, serialization: 'json' });
      conn.on('open', () => { if (done) return; up = true; clearTimeout(timer); h.open(); });
      conn.on('data', (m) => h.msg(m));
      conn.on('close', () => { if (up) { up = false; h.close(); } });
      conn.on('error', (e) => { if (up) h.error(friendly(e)); else failOnce(friendly(e)); });
    });
    peer.on('error', (err) => { if (up) h.error(friendly(err)); else failOnce(friendly(err)); });
    return { send(msg) { if (conn && conn.open) conn.send(msg); }, close() { up = false; done = true; clearTimeout(timer); try { peer.destroy(); } catch (e) { /* gone */ } } };
  }
  return { available, host, join, clean, makeCode };
})();
