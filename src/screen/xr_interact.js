/* VR hands in the world: each hand shows what its grip will take or use (a ring on the floor, a beam, and a label in the world, a light buzz
   when a new thing comes under the hand), and a squeeze turns into one action for the game: take this exact item, use the gate / door /
   chest / puzzle you stand at, or swap to the gun on your back (right hand over the right shoulder). The choosing is XrGrab (pure);
   this file only reads the controllers, draws the highlight and plays the haptics. Presentation and input only: the referee still decides. */
const XrInteract = (function () {
  function create(o) {
    const { THREE, dolly, camera, hands, pulse } = o;
    const ITEM_Y = 0.35;
    const OK = { '.': 1, c: 1, d: 1, P: 1 };
    // a straight line on the map from the player to (x, z) without a wall in between (the referee checks again)
    function los(st, x, z) {
      const m = o.map && o.map(); if (!m) return true;
      const C = m.CELL, px = st.player.x, pz = st.player.z, n = Math.ceil(Math.hypot(x - px, z - pz) / 0.25);
      for (let i = 1; i < n; i++) { const t = i / n, cx = Math.floor((px + (x - px) * t) / C), cz = Math.floor((pz + (z - pz) * t) / C), r = m.rows[cz]; if (!r || !OK[r[cx]]) return false; }
      return true;
    }
    // ---- the highlight, one per hand: a ring on the floor, a soft beam, a label that faces you, and a line from the hand when pulling from afar ----
    function makeLabel() {
      const cv = document.createElement('canvas'); cv.width = 768; cv.height = 160;
      const tex = new THREE.CanvasTexture(cv), sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false, depthWrite: false, fog: false }));
      sp.scale.set(0.96, 0.2, 1); sp.renderOrder = 995; sp.visible = false; dolly.parent ? dolly.parent.add(sp) : dolly.add(sp);
      let last = '';
      function set(a, b, col) {
        const key = a + '|' + b + '|' + col; if (key === last) return; last = key;
        const x = cv.getContext('2d'); x.clearRect(0, 0, cv.width, cv.height);
        x.fillStyle = 'rgba(10,3,5,0.78)'; x.strokeStyle = col; x.lineWidth = 5; const r = 26, w = cv.width - 10, h = cv.height - 10;
        x.beginPath(); x.moveTo(5 + r, 5); x.arcTo(5 + w, 5, 5 + w, 5 + h, r); x.arcTo(5 + w, 5 + h, 5, 5 + h, r); x.arcTo(5, 5 + h, 5, 5, r); x.arcTo(5, 5, 5 + w, 5, r); x.closePath(); x.fill(); x.stroke();
        x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = col; x.font = "700 54px 'Barlow Condensed', 'Arial Narrow', sans-serif"; x.fillText(a, cv.width / 2, 56);
        x.fillStyle = '#ecdfc6'; x.font = "600 40px 'Barlow Condensed', 'Arial Narrow', sans-serif"; x.fillText(b, cv.width / 2, 114);
        tex.needsUpdate = true;
      }
      return { sp, set };
    }
    const world = () => dolly.parent || dolly;
    function makeMark(col) {
      const g = new THREE.Group(); g.visible = false;
      const mat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.9, depthWrite: false, fog: false });
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.34, 0.022, 6, 40), mat); ring.rotation.x = Math.PI / 2; ring.position.y = 0.03; g.add(ring);
      const beamMat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.22, depthWrite: false, fog: false, blending: THREE.AdditiveBlending });
      const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.11, 1.2, 10, 1, true), beamMat); beam.position.y = 0.6; g.add(beam);
      world().add(g);
      const line = new THREE.Mesh(new THREE.BoxGeometry(0.006, 0.006, 1), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.7, depthWrite: false, fog: false }));
      line.visible = false; world().add(line);
      return { g, ring, beam, mat, beamMat, line, label: makeLabel() };
    }
    const COL = { right: 0xffd27a, left: 0x9ee7ff, bad: 0xff5a4a };
    const side = { right: { mark: makeMark(COL.right), grip: XrGrab.createGrip(), tgt: null, key: '' }, left: { mark: makeMark(COL.left), grip: XrGrab.createGrip(), tgt: null, key: '' } };
    // the item's flight to your hand (Alyx-style pull), purely for show: the game has already taken it
    const flyMat = new THREE.MeshBasicMaterial({ color: 0xffe2a0, transparent: true, opacity: 0.9, fog: false, blending: THREE.AdditiveBlending, depthWrite: false });
    const fly = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 8), flyMat); fly.visible = false; world().add(fly);
    let flyT = 1, flyHand = null; const flyFrom = new THREE.Vector3();
    let pending = null, lastAct = null;
    const hp = new THREE.Vector3(), hd = new THREE.Vector3(), q = new THREE.Quaternion(), tmp = new THREE.Vector3(), headL = new THREE.Vector3();
    function itemName(p) { const v = p.gun || p.gear || p.mod; return v ? v.name + (v.rarityName ? '  (' + v.rarityName + ')' : '') : p.kind; }
    function itemColor(p) { const v = p.gun || p.gear || p.mod; return v && v.color !== undefined ? '#' + v.color.toString(16).padStart(6, '0') : '#ffd27a'; }
    // where a use target is, from the snapshot
    function usePos(st, u) {
      const L = st.locks, n = L && L.near;
      if (u.what === 'toll' || u.what === 'key') { const g = n && L.gates[n.i]; return g ? [g.x, g.z, 1.1] : null; }
      if (u.what === 'scale' || u.what === 'wheels') { const s = L.boss && L.boss.station; return s ? [s.x - s.nx * 1.2, s.z - s.nz * 1.2, 0.8] : null; }
      if (u.what === 'door') return [L.door.x, L.door.z, 1.4];
      if (u.what === 'stash') return [u.x, u.z, 0.6];
      return null;
    }
    function hide(s) { s.mark.g.visible = false; s.mark.line.visible = false; s.mark.label.sp.visible = false; }
    // every frame while playing: choose each hand's target, draw it, and turn a squeeze into an action
    function update(st, active, dt, menuOpen) {
      if (fly.visible) { flyT += dt / 0.18; const h = flyHand && hands[flyHand]; if (flyT >= 1 || !h) fly.visible = false; else { h.grip.getWorldPosition(tmp); fly.position.lerpVectors(flyFrom, tmp, flyT * flyT); fly.scale.setScalar(1 - flyT * 0.6); } }
      if (!active || menuOpen || !st || st.over) { for (const k in side) { hide(side[k]); side[k].tgt = null; side[k].key = ''; side[k].grip.step(0, null, dt); } return; }
      const items = (st.pickups || []).filter((p) => (p.grab !== undefined ? p.grab : (p.kind === 'gun' || p.kind === 'gear' || p.kind === 'mod'))).map((p) => ({ id: p.id, x: p.x, y: ITEM_Y, z: p.z, p }));
      const use = XrGrab.useTarget(st), losF = (x, z) => los(st, x, z);
      camera.updateMatrix(); headL.copy(camera.position); tmp.set(0, 0, -1).applyQuaternion(camera.quaternion); const headYaw = Math.atan2(-tmp.x, -tmp.z);
      for (const hand of ['right', 'left']) {
        const s = side[hand], c = hands[hand];
        if (!c || !c.gamepad) { hide(s); s.tgt = null; continue; }
        const gv = c.gamepad.buttons && c.gamepad.buttons[1] ? (c.gamepad.buttons[1].value || (c.gamepad.buttons[1].pressed ? 1 : 0)) : 0;
        // while firing, the gun hand only grabs what it touches (no pull from afar, no nearest-item fallback in a fight)
        const trig = c.gamepad.buttons && c.gamepad.buttons[0] && (c.gamepad.buttons[0].pressed || c.gamepad.buttons[0].value > 0.35);
        s.fireT = trig ? 0.35 : Math.max(0, (s.fireT || 0) - dt);          // and for 0.35 s after letting go: a re-squeeze mid-fight must not pull loot from across the room
        const fighting = hand === 'right' && (trig || s.fireT > 0);
        const support = hand === 'left' && (o.twoHand() || trig);         // left grip on the fore-end, or aiming down sights (left trigger): that hand is on the gun
        let tgt = null;
        if (!support) {
          c.grip.getWorldPosition(hp); c.ray.getWorldQuaternion(q); hd.set(0, 0, -1).applyQuaternion(q);
          if (hand === 'right' && st.player.gun && st.player.gun.other && XrGrab.overShoulder(c.grip.position.toArray(), headL.toArray(), headYaw)) tgt = { mode: 'shoulder', key: 'shoulder', text: 'Swap to ' + (st.player.gun.other.card ? st.player.gun.other.card.name : 'your other gun'), ok: true };
          if (!tgt) { const pk = XrGrab.pick({ p: hp.toArray(), d: hd.toArray() }, items, losF, fighting); if (pk) { const it = items.find((i) => i.id === pk.id); tgt = { mode: pk.mode, id: pk.id, key: pk.mode + pk.id, item: it, text: itemName(it.p), col: itemColor(it.p), ok: true }; } }
          if (!tgt && use) { const at = usePos(st, use); tgt = { mode: 'use', key: 'u' + use.what + use.text, use, at, text: use.text, ok: use.ok }; }
          if (!tgt && hand === 'right' && !fighting) { const bp = XrGrab.bodyPick(items, { x: st.player.x, z: st.player.z, yaw: st.player.yaw }); if (bp) { const it = items.find((i) => i.id === bp.id); tgt = { mode: 'body', id: bp.id, key: 'body' + bp.id, item: it, text: itemName(it.p), col: itemColor(it.p), ok: true }; } }
        }
        const key = tgt ? tgt.key : '';
        if (key !== s.key) { if (tgt && tgt.mode !== 'body') pulse(hand, 0.14, 12); s.key = key; }
        s.tgt = tgt;
        const r = s.grip.step(support ? 0 : gv, tgt ? { id: tgt.key, mode: tgt.mode } : null, dt);
        if (r.grab && tgt) act(hand, tgt, st);
        if (hand === 'left' && tgt && tgt.mode === 'use' && side.right.key === key) hide(s); else draw(hand, s, tgt, hp);   // both hands at the same gate: one highlight
      }
    }
    function act(hand, tgt, st) {
      if (tgt.mode === 'shoulder') { pending = { type: 'swap', hand }; pulse(hand, 0.5, 35); }
      else if (tgt.item) { pending = { type: 'item', id: tgt.id, hand, mode: tgt.mode }; pulse(hand, 0.65, 45); flyFrom.set(tgt.item.x, ITEM_Y, tgt.item.z); flyT = 0; flyHand = hand; fly.visible = true; }
      else if (tgt.use) {
        if (tgt.ok) { pending = { type: 'use', hand, what: tgt.use.what }; pulse(hand, 0.55, 40); }
        else { pulse(hand, 0.9, 70); if (o.toast) o.toast(tgt.text); }             // a firm "no" buzz, and why, so a grip never seems to do nothing
      }
      lastAct = { type: pending ? pending.type : 'denied', hand, mode: tgt.mode, text: tgt.text };
    }
    function draw(hand, s, tgt, hpW) {
      const m = s.mark;
      if (!tgt || tgt.mode === 'shoulder') { hide(s); if (tgt) { m.label.set(hand === 'right' ? 'R GRIP' : 'L GRIP', tgt.text, '#' + COL[hand].toString(16)); hands[hand].grip.getWorldPosition(tmp); m.label.sp.position.copy(tmp).add(new THREE.Vector3(0, 0.18, 0)); m.label.sp.scale.set(0.5, 0.104, 1); m.label.sp.visible = true; } return; }
      const isUse = tgt.mode === 'use', col = !tgt.ok ? COL.bad : COL[hand];
      let x, z, y;
      if (isUse) { if (!tgt.at) { hide(s); return; } [x, z, y] = tgt.at; } else { x = tgt.item.x; z = tgt.item.z; y = ITEM_Y; }
      m.mat.color.setHex(col); m.beamMat.color.setHex(col);
      m.g.position.set(x, 0, z); m.g.scale.setScalar(isUse ? 2.2 : tgt.mode === 'body' ? 0.85 : 1); m.g.visible = true;
      m.beam.visible = !isUse; m.mat.opacity = tgt.mode === 'body' ? 0.45 : 0.9;
      const head = isUse ? (tgt.ok ? 'GRIP: ' : 'LOCKED: ') : (hand === 'right' ? 'R GRIP: take' : 'L GRIP: take');
      m.label.set(isUse ? head + tgt.text : head, isUse ? (tgt.ok ? '' : 'grip for details') : tgt.text, isUse ? '#' + col.toString(16).padStart(6, '0') : tgt.col);
      m.label.sp.position.set(x, (isUse ? y + 0.9 : 1.15) + (hand === 'left' ? 0.24 : 0), z); m.label.sp.scale.set(0.96, 0.2, 1); m.label.sp.visible = true;
      if (tgt.mode === 'ray') {                                          // a line from the hand to what it will pull
        tmp.set(x, y, z); const L = tmp.distanceTo(hpW); m.line.position.copy(hpW).lerp(tmp, 0.5); m.line.lookAt(tmp); m.line.scale.set(1, 1, L); m.line.material.color.setHex(col); m.line.visible = true;
      } else m.line.visible = false;
    }
    function take() { const p = pending; pending = null; return p; }
    function clear() { for (const k in side) { hide(side[k]); side[k].tgt = null; side[k].key = ''; side[k].grip.reset(); } pending = null; fly.visible = false; }
    const view = (t) => (t ? { mode: t.mode, id: t.id, text: t.text, ok: t.ok, what: t.use ? t.use.what : undefined } : null);
    return { update, take, clear, debug: () => ({ right: view(side.right.tgt), left: view(side.left.tgt), last: lastAct }) };
  }
  return { create };
})();
if (typeof module !== 'undefined') module.exports = XrInteract;
