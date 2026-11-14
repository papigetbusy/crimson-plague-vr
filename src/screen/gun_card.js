/* The gun card: a small window with a gun's name, rarity colour, numbers, status and affix lines. One is shown for the nearest gun lying on the floor
   (with arrows against the gun in your hands), and the gun box on the HUD uses the same lines for the gun you hold. Presentation only: the numbers come from
   the referee's snapshot (a gun's `card`). html() is pure so a test can check it. */
const GunCard = (function () {
  const hex = (c) => '#' + c.toString(16).padStart(6, '0');
  const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  // arrow against the gun you hold: green up if better, red down if worse (for reload, lower is better)
  const arrow = (v, mine, lowerBetter) => { if (!mine || v === mine.v) return ''; const better = lowerBetter ? v < mine.v : v > mine.v; return ' <em class="' + (better ? 'up' : 'dn') + '">' + (better ? '▲' : '▼') + '</em>'; };
  // a gear card: name, rarity and slot, defense and health, affix lines, and whether it beats what you wear there
  const VS = { better: '<em class="up">▲ better than yours</em>', worse: '<em class="dn">▼ worse than yours</em>', empty: '<em class="up">▲ fills an empty place</em>' };
  function gearHtml(c) {
    const aff = c.affixes.length ? c.affixes.map((a) => '<li' + (a.cls ? ' class="cls" title="' + esc(a.cls) + ' only"' : '') + '>' + (a.cls ? '★ ' : '') + esc(a.text) + ' <i>' + esc(a.name) + '</i></li>').join('') : '<li class="none">no affixes</li>';
    const base = (c.def > 0 || c.hp > 0) ? '<span>Defense <b>' + c.def + '%</b></span><span>Health <b>+' + c.hp + '</b></span>' : '<span class="none">gives nothing until its affixes</span>';
    return '<h4 style="color:' + hex(c.color) + '">' + esc(c.name) + '</h4><div class="sub">' + esc(c.rarityName) + ' ' + esc(c.slot) + '</div><div class="nums">' + base + '</div><ul>' + aff + '</ul>' + (VS[c.vs] ? '<div class="vs">' + VS[c.vs] + '</div>' : '');
  }
  // a mod card: name, rarity, its lines, and (when a gun is in hand) why it will not fit
  function modHtml(c) {
    const aff = c.affixes.map((a) => '<li>' + esc(a.text) + ' <i>' + esc(a.name) + '</i></li>').join('');
    return '<h4 style="color:' + hex(c.color) + '">' + esc(c.name) + ' Mod</h4><div class="sub">' + esc(c.rarityName) + ' gun mod</div><ul>' + aff + '</ul>' + (c.why ? '<div class="vs"><em class="dn">✖ ' + esc(c.why) + ' in your hands</em></div>' : '<div class="vs"><em class="up">▲ fits the gun in your hands</em></div>');
  }
  // the mod places of a gun: each fitted mod's lines, then empty places
  function modsHtml(c) {
    if (!c.slots) return '';
    const used = c.mods.map((m) => '<li class="mod" style="color:' + hex(m.color) + '">' + esc(m.name) + ' <i>' + m.affixes.map((a) => esc(a.text)).join(', ') + '</i></li>').join('');
    const empty = Array.from({ length: Math.max(0, c.slots - c.mods.length) }, () => '<li class="none">empty mod place</li>').join('');
    return '<div class="sub">Mods ' + c.mods.length + '/' + c.slots + '</div><ul>' + used + empty + '</ul>';
  }
  function html(c, held, withMods) {
    if (c.gear) return gearHtml(c);
    if (c.affixes && !c.type) return modHtml(c);
    const h = held || {};
    const nums = '<span>Dmg <b>' + c.dmg + (c.pellets > 1 ? '×' + c.pellets : '') + '</b>' + arrow(c.dmg, h.dmg !== undefined ? { v: h.dmg } : null) + '</span>' +
      '<span>Rate <b>' + (c.burst ? c.burst + '-round burst' : c.rate + '/s') + '</b>' + arrow(c.rate, h.rate !== undefined ? { v: h.rate } : null) + '</span>' +
      '<span>Mag <b>' + c.mag + '</b>' + arrow(c.mag, h.mag !== undefined ? { v: h.mag } : null) + '</span>' +
      '<span>Reload <b>' + c.reload + 's</b>' + arrow(c.reload, h.reload !== undefined ? { v: h.reload } : null, true) + '</span>';
    const aff = c.affixes.length ? c.affixes.map((a) => '<li' + (a.cls ? ' class="cls" title="' + esc(a.cls) + ' only"' : '') + '>' + (a.cls ? '★ ' : '') + esc(a.text) + ' <i>' + esc(a.name) + '</i></li>').join('') : '<li class="none">no affixes</li>';
    return '<h4 style="color:' + hex(c.color) + '">' + esc(c.name) + '</h4><div class="sub">' + esc(c.rarityName) + ' ' + esc(c.type) + (c.status.length ? ' · ' + esc(c.status.join(' + ')) : '') + '</div>' +
      '<div class="nums">' + nums + '</div><ul>' + aff + '</ul>' + (withMods ? modsHtml(c) : (c.slots ? '<div class="sub">Mod places ' + c.slots + '</div>' : ''));
  }
  // the nearest gun on the floor within reach of the eye, or null
  function nearest(state, range) {
    const p = state.player, fx = Math.sin(p.yaw || 0), fz = -Math.cos(p.yaw || 0); let best = null, bs = Infinity, reachBest = null, rs = Infinity;
    for (const q of state.pickups) {
      if (!q.gun && !q.gear && !q.mod) continue;
      const d = Math.hypot(q.x - p.x, q.z - p.z); if (d >= range) continue;
      const ahead = d < 0.01 ? 1 : ((q.x - p.x) * fx + (q.z - p.z) * fz) / d, score = d * (1.6 - 0.6 * ahead);   // the same rule the referee uses to pick: the one you look at wins
      if (score < bs) { bs = score; best = q; }
      if (q.inReach && score < rs) { rs = score; reachBest = q; }
    }
    return reachBest || best;
  }
  // project(x, y, z) gives the screen spot of a world point ({ x, y, ok }); tap() is what a tap on the card does (pick the gun up)
  function create($, project, tap) {
    const el = $('floorCard'); let key = '', reach = false;
    el.addEventListener('pointerdown', (e) => { if (reach && tap) tap(); e.preventDefault(); e.stopPropagation(); });
    function update(state) {
      const q = state.player.gun && nearest(state, 6);
      if (!q) { if (key) { key = ''; el.style.display = 'none'; } return; }
      const c = q.gun || q.gear || q.mod, k = q.id + ':' + c.name + c.rarity + (c.dmg || c.hp) + c.vs + c.why + ':' + state.player.gun.card.dmg + (q.inReach ? 'r' : '');
      reach = !!q.inReach;
      if (k !== key) {
        key = k; el.innerHTML = html(c, state.player.gun.card) + '<div class="tap">' + (reach ? 'TAP / E / A to pick up' : 'come closer to pick up') + '</div>'; el.style.borderColor = hex(c.color);
        el.classList.toggle('reach', reach);
      }
      const at = project(q.x, 1.1, q.z);
      if (!at.ok) { el.style.display = 'none'; return; }
      el.style.display = 'block';
      const w = el.offsetWidth || 190, h = el.offsetHeight || 120, W = innerWidth, H = innerHeight;
      el.style.left = Math.max(8, Math.min(W - w - 8, at.x - w / 2)) + 'px';
      el.style.top = Math.max(8, Math.min(H - h - 8, at.y - h - 10)) + 'px';             // floats just above the gun
    }
    return { update };
  }
  return { html, gearHtml, modHtml, modsHtml, nearest, create };
})();
if (typeof module !== 'undefined') module.exports = GunCard;
