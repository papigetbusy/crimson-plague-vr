/* VR grabbing: which item, gate, door or chest each hand is about to take or use, and when a grip squeeze counts as a grab.
   Pure logic (no DOM, no three.js, no clock), so tests can feed it hands and items. The VR view (xr_mode.js) draws the highlight
   and sends the grab to the game. How the top VR shooters do it and why these numbers: docs/vr-design.md, "Grabbing and doors".
     1. NEAR   a hand within 45 cm of an item (anywhere from the floor up to just above it) takes it       (Alyx / Pavlov hand grab, generous)
     2. RAY    a hand pointed at an item up to 7 m away (within ~13 degrees) pulls it to you              (Contractors / Alyx distance grab)
     3. USE    standing at a gold gate, the boss door, a puzzle or the stash chest: the grip uses it      (Pavlov / Contractors "interact")
     4. BODY   nothing pointed at: the nearest item within 2.6 m in front of you (the old flat-game rule, so a grip never does nothing)
   A grab is a fresh squeeze of the grip (with hysteresis, so a half-relaxed grip re-arms). If the grip is already squeezed (players hold it
   like a gun), resting the hand on an item for 0.2 s also takes it, but only a NEAR item: gold is never spent without a fresh squeeze. */
const XrGrab = (function () {
  const R = { NEAR: 0.45, ITEM_TOP: 0.6, CONE: 0.23, CONE_CLOSE: 0.4, FAR: 7, BODY: 2.6, DWELL: 0.2, ON: 0.55, OFF: 0.3, SHOULDER: 0.26 };
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const len = (a) => Math.hypot(a[0], a[1], a[2]);
  // how far a hand is from an item: the item is a short upright post from the floor to ITEM_TOP, so a hand reaching low or just above counts
  function nearDist(p, it) { const y = Math.max(0, Math.min(R.ITEM_TOP, p[1])); return Math.hypot(p[0] - it.x, p[1] - y, p[2] - it.z); }
  // the best target for one hand. hand = { p: [x, y, z], d: unit direction it points } in world space; items = [{ id, x, y, z }];
  // los(x, z) says whether the item can be seen from the player (no grabbing through walls); nearOnly skips pointing (used while firing). Returns { id, mode, d } or null.
  function pick(hand, items, los, nearOnly) {
    if (!hand || !items || !items.length) return null;
    let best = null;
    for (const it of items) { const d = nearDist(hand.p, it); if (d < R.NEAR && (!best || d < best.d)) best = { id: it.id, mode: 'near', d }; }
    if (best || nearOnly) return best;
    let bs = Infinity;
    for (const it of items) {
      const v = sub([it.x, it.y, it.z], hand.p), L = len(v), t = dot(v, hand.d); if (t <= 0 || L > R.FAR || L < 1e-6) continue;
      const ang = Math.acos(Math.max(-1, Math.min(1, t / L))), lim = Math.max(R.CONE, Math.min(R.CONE_CLOSE, Math.atan(0.45 / L)));   // close items get a wider cone (they look big)
      if (ang > lim) continue;
      if (los && !los(it.x, it.z)) continue;
      const score = ang / lim + L / R.FAR * 0.35; if (score < bs) { bs = score; best = { id: it.id, mode: 'ray', d: L }; }
    }
    return best;
  }
  // the old rule as the last fallback: the nearest item within reach, the one in front of you winning (yaw 0 looks down -z)
  function bodyPick(items, body) {
    let best = null, bs = Infinity; const fx = Math.sin(body.yaw), fz = -Math.cos(body.yaw);
    for (const it of items || []) {
      const d = Math.hypot(it.x - body.x, it.z - body.z); if (d >= R.BODY) continue;
      const ahead = d < 0.01 ? 1 : ((it.x - body.x) * fx + (it.z - body.z) * fz) / d, s = d * (1.6 - 0.6 * ahead);
      if (s < bs) { bs = s; best = { id: it.id, mode: 'body', d }; }
    }
    return best;
  }
  // one hand's grip. step(value 0..1, target, dt) -> { grab, squeezed }. grab is true on a fresh squeeze, or (grip held) after the hand rests DWELL s on a NEAR item.
  function createGrip() {
    let down = false, dwellId = null, dwell = 0; const tried = new Set();
    function step(v, target, dt) {
      let grab = false;
      if (!down && v >= R.ON) { down = true; grab = true; dwellId = target ? target.id : null; dwell = 0; if (target) tried.add(target.id); }
      else if (down && v <= R.OFF) { down = false; tried.clear(); dwellId = null; }
      else if (down && target && target.mode === 'near' && !tried.has(target.id)) {
        if (dwellId !== target.id) { dwellId = target.id; dwell = 0; }
        dwell += dt || 0; if (dwell >= R.DWELL) { grab = true; tried.add(target.id); }
      } else if (down && (!target || target.mode !== 'near')) { dwellId = null; dwell = 0; }
      return { grab, squeezed: down };
    }
    return { step, reset: () => { down = false; tried.clear(); dwellId = null; dwell = 0; } };
  }
  // the gun on your back: the right hand reaching over the right shoulder (rig space: head position + yaw only). Returns true when there.
  function overShoulder(hand, head, headYaw) {
    const c = Math.cos(headYaw), s = Math.sin(headYaw), ox = 0.16, oy = -0.08, oz = 0.12;   // right of, a bit below and behind the head
    const sx = head[0] + ox * c + oz * s, sz = head[2] - ox * s + oz * c;   // rig-space yaw (three.js: positive turns left), offset turned with it
    return Math.hypot(hand[0] - sx, hand[1] - (head[1] + oy), hand[2] - sz) < R.SHOULDER;
  }
  // what a grip on a gate / door / puzzle / chest would do, from the game's snapshot: { what, text, ok } or null
  function useTarget(st) {
    const L = st && st.locks, n = L && L.near;
    if (n) { const a = n.actions && n.actions[0]; return { what: n.what, text: a ? (a.afford ? a.label : n.what === 'key' ? 'Needs the Key Keeper\'s key' : n.price ? 'Need ' + n.price + ' gold' : 'Not enough gold') : n.text, ok: !!(a && a.afford), x: n.x, z: n.z }; }
    const d = L && L.door;
    if (d && d.near && !d.open) return { what: 'door', text: d.canOpen ? 'Open the door' : (d.text || 'Sealed'), ok: !!d.canOpen, x: d.x, z: d.z };
    const s = st && st.player && st.player.stash;
    if (s && s.near && s.chest) return { what: 'stash', text: 'Open the stash', ok: true, x: s.chest.x, z: s.chest.z };
    return null;
  }
  return { R, pick, bodyPick, nearDist, createGrip, overShoulder, useTarget };
})();
if (typeof module !== 'undefined') module.exports = XrGrab;
