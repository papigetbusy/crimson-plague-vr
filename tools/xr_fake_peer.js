// A stand-in for PeerJS (the internet link co-op uses) for the playtest: pages in the same headless Chrome talk through a BroadcastChannel instead of WebRTC.
// Same calls the game makes (new Peer(id), on('open'|'connection'|'error'|'disconnected'), connect(id) -> conn with on('open'|'data'|'close'|'error'), send, close, destroy).
// Messages go through JSON like PeerJS's 'json' serialization. window.__peerStats counts what went each way.
(function () {
  const bc = new BroadcastChannel('cp-fake-peer'), peers = {}; let n = 0;
  const stats = window.__peerStats = { sent: 0, got: 0, bytes: 0 };
  class Em { constructor() { this.h = {}; } on(e, f) { (this.h[e] = this.h[e] || []).push(f); return this; } emit(e, ...a) { for (const f of this.h[e] || []) { try { f(...a); } catch (x) { console.error(x); } } } }
  class Conn extends Em {
    constructor(peer, remote, cid) { super(); this.peer = peer; this.peerId = remote; this.cid = cid; this.open = false; }
    send(m) { if (!this.open) return; const j = JSON.stringify(m); stats.sent++; stats.bytes += j.length; bc.postMessage({ k: 'data', to: this.peerId, cid: this.cid, j }); }
    close() { if (!this.open) return; this.open = false; bc.postMessage({ k: 'close', to: this.peerId, cid: this.cid }); this.emit('close'); }
  }
  class Peer extends Em {
    constructor(id) { super(); this.id = id || ('anon-' + Math.random().toString(36).slice(2)); this.conns = {}; this.destroyed = false; peers[this.id] = this; setTimeout(() => this.emit('open', this.id), 30); }
    connect(id) { const cid = this.id + '>' + id + '#' + (++n), c = new Conn(this, id, cid); this.conns[cid] = c; bc.postMessage({ k: 'conn', to: id, from: this.id, cid }); c.t = setTimeout(() => { if (!c.open) c.emit('error', { type: 'peer-unavailable' }); }, 4000); return c; }
    destroy() { this.destroyed = true; for (const c of Object.values(this.conns)) c.close(); delete peers[this.id]; }
    reconnect() {}
  }
  bc.onmessage = (e) => {
    const d = e.data, p = peers[d.to]; if (!p) return;
    if (d.k === 'conn') { const c = new Conn(p, d.from, d.cid); p.conns[d.cid] = c; p.emit('connection', c); setTimeout(() => { c.open = true; c.emit('open'); bc.postMessage({ k: 'ack', to: d.from, cid: d.cid }); }, 10); }
    else if (d.k === 'ack') { const c = p.conns[d.cid]; if (c) { clearTimeout(c.t); c.open = true; c.emit('open'); } }
    else if (d.k === 'data') { const c = p.conns[d.cid]; if (c && c.open) { stats.got++; c.emit('data', JSON.parse(d.j)); } }
    else if (d.k === 'close') { const c = p.conns[d.cid]; if (c && c.open) { c.open = false; c.emit('close'); } }
  };
  window.Peer = Peer;
})();
