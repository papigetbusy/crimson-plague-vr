/* Playing with friends: the lobby on the start card (host a game, or join with a room code) and the link that runs while you play.
   The rules live in the referee (host = the world, friends = their own gun, loot and level-ups); the talking is in coop_link.js; the internet part is net_peer.js.
   This file only joins them to the buttons. */
const Coop = (function () {
  function create($, ref, hooks) {
    // hooks: { toast(text), playLabel(text, disabled), begin() }
    const btn = $('coopBtn'), panel = $('coopPanel'), hostBtn = $('coopHost'), joinBtn = $('coopJoin'), codeIn = $('coopCode'), nameIn = $('coopName'), info = $('coopInfo'), leaveBtn = $('coopLeave'), menu = $('coopMenu');
    let mode = 'off', net = null, link = null, code = '', went = false, upSince = 0;
    const NAME_KEY = 'crimsonplague.name';
    try { nameIn.value = localStorage.getItem(NAME_KEY) || ('Player' + (10 + Math.floor(Math.random() * 90))); } catch (e) { nameIn.value = 'Player' + (10 + Math.floor(Math.random() * 90)); }
    const myName = () => { const n = nameIn.value.replace(/[<>&]/g, '').trim().slice(0, 12) || 'Player'; try { localStorage.setItem(NAME_KEY, n); } catch (e) { /* not saved */ } return n; };
    // the look you play with: saved if you picked one before, otherwise a random one of the seven; tap a swatch to choose
    const SKIN_KEY = 'crimsonplague.skin', skinsEl = $('coopSkins');
    let skin = ''; try { skin = localStorage.getItem(SKIN_KEY) || ''; } catch (e) { /* not saved */ }
    if (!SkinsLook.valid(skin)) skin = SkinsLook.random();
    const skinBtns = [];
    function chooseSkin(id, save) {
      skin = id; ref.setCfg({ selfSkin: id });
      if (save) { try { localStorage.setItem(SKIN_KEY, id); } catch (e) { /* not saved */ } }
      for (const [sid, b] of skinBtns) b.classList.toggle('sel', sid === id);
      const nm = $('coopSkinName'); if (nm) nm.textContent = 'Your look: ' + SkinsLook.LIST.find((s) => s.id === id).name;
    }
    for (const s of SkinsLook.LIST) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'skinBtn'; b.title = s.name + ': ' + s.blurb; b.setAttribute('aria-label', s.name);
      b.style.setProperty('--tone', s.tone); b.style.setProperty('--glow', s.glow);
      b.addEventListener('click', () => chooseSkin(s.id, true)); skinsEl.appendChild(b); skinBtns.push([s.id, b]);
    }
    const dice = document.createElement('button'); dice.type = 'button'; dice.className = 'skinDice'; dice.textContent = 'Random'; dice.addEventListener('click', () => chooseSkin(SkinsLook.random(), false)); skinsEl.appendChild(dice);
    const nameLine = document.createElement('div'); nameLine.id = 'coopSkinName'; skinsEl.appendChild(nameLine);
    chooseSkin(skin, false);
    const say = (t) => { info.textContent = t; };
    // a headset has no keyboard: on-screen letter keys for the room code (shown only in VR, where the VR menu turns them into tiles)
    const keysEl = $('coopKeys');
    if (keysEl) {
      const shown = document.createElement('div'); shown.id = 'coopKeysShow'; keysEl.appendChild(shown);
      const upd = () => { shown.textContent = 'Room code: ' + (NetPeer.clean(codeIn.value) + '_____').slice(0, 5).split('').join(' '); };
      for (const ch of 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'.split('').concat(['DEL'])) {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'ck'; b.textContent = ch;
        b.addEventListener('click', () => { const v = NetPeer.clean(codeIn.value); codeIn.value = ch === 'DEL' ? v.slice(0, -1) : (v + ch).slice(0, 5); upd(); });
        keysEl.appendChild(b);
      }
      codeIn.addEventListener('input', upd); upd();
    }
    function show() {
      menu.hidden = mode !== 'off'; leaveBtn.hidden = mode === 'off';
      if (mode === 'host') {
        const cs = ref.snapshot().coop, names = cs.peers.map((p) => p.name);
        say(code ? 'ROOM CODE  ' + code + '  -  ' + (names.length + 1) + ' of ' + cs.max + ' players' + (names.length ? ' (joined: ' + names.join(', ') + ')' : ', waiting for friends') + (went ? '' : '. Press ENTER THE HALL when everyone is in.') : 'Opening a room...');
        hooks.playLabel('ENTER THE HALL', false);
      } else if (mode === 'guest') {
        const ready = link && link.ready;
        say(ready ? 'Joined room ' + code + ' (up to ' + ref.snapshot().coop.max + ' players). ' + (went ? 'The host has started!' : 'Waiting for the host to start...') : 'Joining room ' + code + '...');
        hooks.playLabel(!ready ? 'JOINING...' : went ? 'THE HOST STARTED - ENTER' : 'WAITING FOR THE HOST', !ready || !went);
      } else hooks.playLabel('ENTER THE HALL', false);
    }
    function off(text) {
      if (net) { try { net.close(); } catch (e) { /* gone */ } }
      net = null; link = null; mode = 'off'; code = ''; went = false;
      ref.setCfg({ coop: false, guest: false, selfKey: 'host' }); ref.reset();
      if (text) say(text); else say('');
      show(); if (text) info.textContent = text;
    }
    function fail(text) { hooks.toast(text); off(text); }
    function startHost() {
      if (!NetPeer.available()) { say('Playing with friends needs the internet link library, and it did not load. Check your connection and reload.'); return; }
      ref.setCfg({ coop: true, guest: false, selfKey: 'host', selfName: myName(), selfSkin: skin }); ref.reset();
      mode = 'host'; went = false; code = '';
      link = CoopLink.host(ref, (key, msg) => net && net.send(key, msg));
      net = NetPeer.host({
        ready: (c) => { code = c; show(); },
        join: () => show(),
        msg: (key, m) => { link.onMessage(key, m); if (m.t === 'hello' && went) link.start(); show(); },
        leave: (key) => { link.leave(key); hooks.toast('A friend left'); show(); },
        error: (t) => fail(t)
      });
      show();
    }
    function startJoin() {
      const c = NetPeer.clean(codeIn.value);
      if (c.length !== 5) { say('Type the 5 letter room code your friend gave you.'); return; }
      if (!NetPeer.available()) { say('Playing with friends needs the internet link library, and it did not load. Check your connection and reload.'); return; }
      ref.setCfg({ coop: true, guest: true, selfKey: 'pending', selfName: myName(), selfSkin: skin }); ref.reset();
      mode = 'guest'; went = false; code = c;
      link = CoopLink.guest(ref, (m) => net && net.send(m), myName(), (m) => {
        if (m.t === 'welcome') { if (!m.ok) { fail('That room is full (5 players at most).'); return; } ref.setCfg({ selfKey: m.key }); }
        if (m.t === 'go') { went = true; hooks.toast('The host has started - enter the hall!'); }
        show();
      });
      net = NetPeer.join(c, {
        open: () => { link.hello(); show(); },
        msg: (m) => link.onMessage(m),
        close: () => { hooks.toast('The host left the game'); off('The host left the game.'); },
        error: (t) => fail(t)
      });
      show();
    }
    btn.addEventListener('click', () => { panel.hidden = !panel.hidden; if (!panel.hidden) { try { panel.scrollIntoView({ block: 'end' }); } catch (e) { /* older browsers: the card still scrolls by hand */ } } });
    hostBtn.addEventListener('click', startHost);
    joinBtn.addEventListener('click', startJoin);
    codeIn.addEventListener('keydown', (e) => { e.stopPropagation(); if (e.key === 'Enter') startJoin(); });
    nameIn.addEventListener('keydown', (e) => e.stopPropagation());
    leaveBtn.addEventListener('click', () => { if (link && mode === 'guest') { try { link.bye(); } catch (e) { /* closing anyway */ } } off(''); });
    return {
      get mode() { return mode; },
      get blocked() { return mode === 'guest' && !(went && link && link.ready); },     // a friend can not enter the hall until the host has
      onBegin() { if (mode === 'host' && !went) { went = true; link.start(); show(); } },
      tick(dt, events) { if (!link) return; if (mode === 'host') link.tick(dt, events); else if (mode === 'guest' && link.ready) link.tick(dt); },
      off
    };
  }
  return { create };
})();
