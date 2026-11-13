/* VR menus: the open menu's data (title, rows of cards, buttons, short texts) read from the page and drawn again as a clean
   VR layout on a canvas, in the game's own fonts and colours. Nothing is photographed: spacing, centring and hover are ours.
   Layout rules (Meta Horizon design guidelines, see docs/vr-design.md): centred title, even gaps, big whole-tile targets
   (cards 300+ px, buttons 84+ px tall = well over 48dp at 1.6 m), hover lights the whole tile only, content that does not fit
   is cut off at the edge with ▲ / ▼ markers and scrolls (right stick or trigger-drag), and a fixed footer always shows the way out.
   Presentation only: pressing a tile presses the real page button, so the game's own menu code does the work. */
const XrMenu = (function () {
  const W = 1600, H = 1000, FOOT = 128, VIEW = H - FOOT, PAD = 60;
  const C = { bg0: '#1a080c', bg1: '#070304', edge: '#5a1a20', ink: '#ecdfc6', dim: '#a8987c', gold: '#cfa54a', goldHi: '#ffd27a', red: '#ff4a4a', tile0: '#2a0c10', tile1: '#12060a', tileHi0: '#4a141c', tileHi1: '#22090e', line: '#6a4a24' };
  const DISPLAY = "'Pirata One', Georgia, serif", BODY = "'Barlow Condensed', 'Arial Narrow', sans-serif";
  const CLICKABLE = 'button, [data-act], [data-bp], [data-load], [data-del], [data-keep], [role="button"]';
  const EXIT = '.gclose, .cxclose';
  const SKIP = '.kbd, .touchhelp, .keys, .padk, .padhelp, .buildTag, .cheatTag, input, textarea, select, label, .phone, [data-act^="rename"]';   // text boxes need a keyboard: flat screen only
  const norm = (t) => (t || '').replace(/\s+/g, ' ').trim();

  // ---------- reading the page ----------
  function visible(el) {
    if (el.hidden) return false;
    const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    return true;
  }
  function lines(el) { return (el.innerText || el.textContent || '').split('\n').map(norm).filter(Boolean); }
  function tileOf(el) {
    const b = el.querySelector(':scope > b'), sp = el.querySelector(':scope > span'), em = el.querySelector(':scope > em');
    const t = { el, primary: el.id === 'play' || el.id === 'restart', disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true', sel: el.classList.contains('sel') && el.matches('[data-cls]'),   // 'sel' is only a real choice for the class buttons; on cards it is the flat pad's focus, not shown in VR
      act: el.classList.contains('active') || el.getAttribute('aria-selected') === 'true', dim: el.classList.contains('poor') };
    if (b && (sp || em)) { t.style = 'card'; t.title = norm(b.textContent); t.color = b.style.color || ''; t.body = sp ? norm(sp.textContent) : ''; t.foot = em ? norm(em.textContent) : ''; t.ult = el.classList.contains('ult'); }
    else { const l = lines(el); t.style = 'btn'; t.title = l[0] || norm(el.textContent) || norm(el.getAttribute('aria-label') || el.title || '') || '?'; t.body = l.slice(1).join('  ·  ').slice(0, 160); }
    return t;
  }
  // a Gear / stash place: the item's card (name first, then its numbers) with that place's own buttons underneath
  function slotOf(el) {
    const info = [], btns = []; let tag = '';
    for (const c of el.children) {
      if (!visible(c) || c.matches(SKIP)) continue;
      if (c.matches(CLICKABLE)) { btns.push(tileOf(c)); continue; }
      for (const b of c.querySelectorAll(CLICKABLE)) if (!b.matches(SKIP) && visible(b)) btns.push(tileOf(b));
      if (!c.querySelector(CLICKABLE)) { if (!info.length && !tag && c.matches('.sub') && !el.classList.contains('empty')) { tag = norm(c.textContent); continue; } info.push(...lines(c)); }
    }
    btns.forEach((b) => { b.small = true; b.style = 'btn'; b.body = ''; });
    return { tag, color: el.style.borderColor || '', empty: el.classList.contains('empty'), info: info.slice(0, 8), btns };
  }
  function extract(root, id) {
    const m = { title: '', sub: '', blocks: [], exits: [] };
    const add = (blk) => { m.blocks.push(blk); return blk; };
    let tiles = null;
    const pushTile = (t) => { if (!tiles || tiles.style !== t.style) tiles = add({ type: 'tiles', style: t.style, tiles: [] }); tiles.tiles.push(t); };
    const end = () => { tiles = null; };
    (function walk(node) {
      for (const el of node.children) {
        if (!visible(el) || el.matches(SKIP)) continue;
        if (el.matches(EXIT)) { m.exits.push({ el, label: norm(el.textContent) || 'Close' }); continue; }
        if (el.matches(CLICKABLE)) { if (el.id === 'vrBtn') continue; pushTile(tileOf(el)); continue; }
        const tag = el.tagName;
        if (tag === 'H1') { if (!m.title) m.title = norm(el.textContent); else { end(); add({ type: 'head', text: norm(el.textContent) }); } continue; }
        if (tag === 'H2' || tag === 'H3' || el.matches('.gsec, header > b')) { end(); const t = norm(el.textContent); if (t) { if (!m.title && tag === 'H2') m.title = t; else add({ type: 'head', text: t }); } continue; }
        if (el.matches('.ggrid')) { end(); add({ type: 'slots', slots: Array.from(el.children).filter((c) => visible(c)).map(slotOf) }); continue; }
        if (el.querySelector(CLICKABLE) || el.querySelector('h1, h2, h3, .gsec')) { walk(el); continue; }
        const l = lines(el); if (!l.length) continue;
        end();
        let text = l.join('  ·  '); if (text.length > 260) text = text.slice(0, 257) + '...';
        if (!m.sub && !m.blocks.length && tag === 'P') m.sub = text; else add({ type: 'text', text });
      }
    })(root);
    return m;
  }

  // ---------- layout ----------
  let measC = null; const meas = { set font(f) { M().font = f; }, get font() { return M().font; }, measureText: (t) => M().measureText(t) }; const M = () => measC || (measC = document.createElement('canvas').getContext('2d'));
  function wrap(text, font, maxW) {
    meas.font = font; const out = []; let cur = '';
    for (const w of String(text).split(' ')) { const t = cur ? cur + ' ' + w : w; if (meas.measureText(t).width > maxW && cur) { out.push(cur); cur = w; } else cur = t; }
    if (cur) out.push(cur); return out;
  }
  const fit = (t, font, maxW) => { meas.font = font; if (meas.measureText(t).width <= maxW) return t; while (t.length > 3 && meas.measureText(t + '…').width > maxW) t = t.slice(0, -1); return t + '…'; };
  const F = { slotT: '34px ' + DISPLAY, slotB: '26px ' + BODY, smallT: '700 28px ' + BODY, title: '96px ' + DISPLAY, head: '700 34px ' + BODY, sub: '32px ' + BODY, text: '30px ' + BODY, cardT: '42px ' + DISPLAY, cardB: '30px ' + BODY, cardF: '700 24px ' + BODY, btnT: '700 36px ' + BODY, btnB: '26px ' + BODY, foot: '700 34px ' + BODY, hint: '24px ' + BODY };
  function layout(m) {
    const items = [], tiles = [];
    let y = 56;
    const textBlock = (text, font, lh, color, maxW) => { const ls = wrap(text, font, maxW || W - PAD * 2 - 140); items.push({ k: 'text', lines: ls, font, lh, color, y }); y += ls.length * lh; };
    if (m.title) { items.push({ k: 'title', text: m.title, y }); y += 98; }
    if (m.sub) { y += 4; textBlock(m.sub, F.sub, 40, C.dim); y += 8; }
    for (const b of m.blocks) {
      if (b.type === 'head') { y += 20; items.push({ k: 'head', text: b.text.toUpperCase(), y }); y += 48; }
      else if (b.type === 'text') { y += 10; textBlock(b.text, F.text, 38, C.dim); y += 6; }
      else if (b.type === 'slots') {
        y += 16;
        const n = b.slots.length, cols = Math.min(3, n), gap = 26, sw = n === 1 ? 640 : Math.floor((W - PAD * 2 - gap * (cols - 1)) / cols);
        for (let r = 0; r * cols < n; r++) {
          const row = b.slots.slice(r * cols, r * cols + cols);
          const parts = row.map((sl) => {
            const head = sl.info[0] || '', rest = sl.info.slice(1).map((l) => fit(l, F.slotB, sw - 40));
            return { head: fit(head, sl.empty ? F.slotB : F.slotT, sw - 40), rest, h: 26 + (sl.tag ? 30 : 0) + (head ? (sl.empty ? 34 : 44) : 0) + rest.length * 32 + (sl.btns.length ? 14 + sl.btns.length * 74 : 0) + 18 };
          });
          const rh = Math.max(...parts.map((q) => q.h)), rowW = row.length * sw + (row.length - 1) * gap;
          let x = Math.round((W - rowW) / 2);
          row.forEach((sl, i) => {
            items.push({ k: 'slot', tag: sl.tag, x, y, w: sw, h: rh, color: sl.color, empty: sl.empty, head: parts[i].head, rest: parts[i].rest });
            let by = y + rh - 18 - sl.btns.length * 74 + 4;
            for (const bt of sl.btns) { tiles.push(Object.assign({}, bt, { tl: [fit(bt.title, F.smallT, sw - 60)], bl: [], x: x + 20, y: by, w: sw - 40, h: 64, card: false })); by += 74; }
            x += sw + gap;
          });
          y += rh + gap;
        }
        y -= gap - 6;
      }
      else if (b.type === 'tiles') {
        y += 18;
        b.tiles.sort((p, q) => (q.primary ? 1 : 0) - (p.primary ? 1 : 0));   // the main action (Resume / Rise again) comes first
        const n = b.tiles.length, card = b.style === 'card';
        let cols, tw, gap = 28;
        if (card) { cols = n <= 4 ? n : (n % 3 === 0 ? 3 : 4); tw = Math.min(340, Math.floor((W - PAD * 2 - gap * (cols - 1)) / cols)); }
        else { const short = b.tiles.every((t) => t.title.length <= 28 && !t.body), keys = n > 6 && b.tiles.every((t) => t.title.length <= 3 && !t.body); cols = keys ? Math.min(8, n) : short && n > 1 ? Math.min(3, n) : 1; tw = cols === 1 ? 1040 : Math.floor((1240 - gap * (cols - 1)) / cols); }
        for (let r = 0; r * cols < n; r++) {
          const row = b.tiles.slice(r * cols, r * cols + cols);
          // every tile in a row gets the same height (the tallest one's), so rows line up cleanly
          const parts = row.map((t) => {
            if (card) { const tl = wrap(t.title, F.cardT, tw - 36).slice(0, 2), bl = wrap(t.body, F.cardB, tw - 36).slice(0, 5); return { tl, bl, h: 30 + tl.length * 46 + (bl.length ? 8 + bl.length * 34 : 0) + (t.foot ? 46 : 0) + 18 }; }
            const tl = wrap(t.title, F.btnT, tw - 48).slice(0, 2), bl = t.body ? wrap(t.body, F.btnB, tw - 48).slice(0, 2) : []; return { tl, bl, h: Math.max(88, 28 + tl.length * 42 + bl.length * 32 + 18) };
          });
          const rh = Math.max(...parts.map((p) => p.h)), rowW = row.length * tw + (row.length - 1) * gap;
          let x = Math.round((W - rowW) / 2);
          row.forEach((t, i) => { tiles.push(Object.assign({}, t, parts[i], { x, y, w: tw, h: rh, card })); x += tw + gap; });
          y += rh + gap;
        }
        y -= gap - 6;
      }
    }
    y += 40;
    // footer: the way out (Close / Leave / Back) and the controls, always on screen
    const ex = m.exits.slice(0, 3), ew = 360, eg = 30, exW = ex.length * ew + Math.max(0, ex.length - 1) * eg;
    const exits = ex.map((e, i) => ({ el: e.el, action: e.action, title: e.label, x: Math.round((W - exW) / 2) + i * (ew + eg), y: VIEW + 18, w: ew, h: 76, exit: true }));
    return { items, tiles, exits, height: Math.max(VIEW, y) };
  }

  // ---------- drawing ----------
  function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
  function drawTile(ctx, t, hover, dy) {
    const x = t.x, y = t.y - dy, w = t.w, h = t.h, off = t.disabled;
    ctx.save(); ctx.globalAlpha = off || t.dim ? 0.5 : 1;
    const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, hover ? C.tileHi0 : C.tile0); g.addColorStop(1, hover ? C.tileHi1 : C.tile1);
    rr(ctx, x, y, w, h, 10); ctx.fillStyle = g; ctx.fill();
    ctx.lineWidth = hover ? 5 : t.sel || t.ult || t.primary ? 3 : 2; ctx.strokeStyle = hover ? C.goldHi : t.sel || t.ult || t.primary ? C.gold : t.exit ? '#8a2a30' : C.line; ctx.stroke();
    if (hover) { ctx.shadowColor = 'rgba(255,210,122,0.55)'; ctx.shadowBlur = 24; ctx.stroke(); ctx.shadowBlur = 0; }
    ctx.textAlign = 'center'; ctx.textBaseline = 'top'; const cx = x + w / 2;
    if (t.card) {
      let yy = y + 30;
      ctx.font = F.cardT; ctx.fillStyle = t.color || C.ink; for (const l of t.tl) { ctx.fillText(l, cx, yy); yy += 46; }
      yy += 10; ctx.font = F.cardB; ctx.fillStyle = C.ink; for (const l of t.bl) { ctx.fillText(l, cx, yy); yy += 34; }
      if (t.foot) { ctx.font = F.cardF; ctx.fillStyle = C.gold; ctx.fillText(t.foot.toUpperCase(), cx, y + h - 42); }
    } else {
      const total = (t.small ? 32 : t.tl.length * 42) + (t.bl || []).length * 32; let yy = y + (h - total) / 2 + 2;
      ctx.font = t.exit ? F.foot : t.small ? F.smallT : F.btnT; ctx.fillStyle = t.primary ? C.goldHi : C.ink; for (const l of t.tl) { ctx.fillText(t.exit || t.primary ? l.toUpperCase() : l, cx, yy); yy += 42; }
      ctx.font = F.btnB; ctx.fillStyle = C.dim; for (const l of t.bl || []) { ctx.fillText(l, cx, yy); yy += 32; }
    }
    ctx.restore();
  }
  function drawContent(ctx, L) {
    ctx.clearRect(0, 0, W, L.height);
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    for (const it of L.items) {
      if (it.k === 'title') { ctx.font = F.title; ctx.fillStyle = C.ink; ctx.shadowColor = 'rgba(163,29,38,0.9)'; ctx.shadowBlur = 22; ctx.fillText(it.text, W / 2, it.y); ctx.shadowBlur = 0; }
      else if (it.k === 'head') {
        ctx.font = F.head; ctx.fillStyle = C.gold; const tw = meas.measureText ? (meas.font = F.head, meas.measureText(it.text).width) : 200;
        ctx.fillText(it.text, W / 2, it.y); ctx.fillStyle = C.line; ctx.fillRect(W / 2 - tw / 2 - 200, it.y + 18, 170, 2); ctx.fillRect(W / 2 + tw / 2 + 30, it.y + 18, 170, 2);
      } else if (it.k === 'slot') {
        rr(ctx, it.x, it.y, it.w, it.h, 10); ctx.fillStyle = 'rgba(20,8,10,0.92)'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = it.color || C.line; ctx.globalAlpha = it.empty ? 0.5 : 1; ctx.stroke(); ctx.globalAlpha = 1;
        let yy = it.y + 22; if (it.tag) { ctx.font = '700 22px ' + BODY; ctx.fillStyle = C.gold; ctx.fillText(it.tag.toUpperCase(), it.x + it.w / 2, yy); yy += 30; }
        if (it.head) { ctx.font = it.empty ? F.slotB : F.slotT; ctx.fillStyle = it.empty ? C.dim : (it.color || C.ink); ctx.fillText(it.empty ? it.head.toUpperCase() : it.head, it.x + it.w / 2, yy); yy += it.empty ? 34 : 44; }
        ctx.font = F.slotB; ctx.fillStyle = C.dim; for (const l of it.rest) { ctx.fillText(l, it.x + it.w / 2, yy); yy += 32; }
      } else if (it.k === 'text') { ctx.font = it.font; ctx.fillStyle = it.color; it.lines.forEach((l, i) => ctx.fillText(l, W / 2, it.y + i * it.lh)); }
    }
  }
  function create(THREE) {
    const disp = document.createElement('canvas'); disp.width = W; disp.height = H;
    const dctx = disp.getContext('2d');
    const content = document.createElement('canvas'); content.width = W; content.height = VIEW;
    const cctx = content.getContext('2d');
    const tex = new THREE.CanvasTexture(disp); tex.minFilter = THREE.LinearMipmapLinearFilter; tex.magFilter = THREE.LinearFilter; tex.anisotropy = 4;
    let L = null, sig = '', scroll = 0, hover = null, dirty = true, model = null;
    const maxScroll = () => (L ? Math.max(0, L.height - VIEW) : 0);
    function setModel(m) {
      const s = JSON.stringify(m, (k, v) => (k === 'el' ? undefined : v));
      if (s === sig) return false;
      const first = !sig; sig = s; model = m;
      // tile elements change identity when the page redraws; keep them fresh even if the look is unchanged
      L = layout(m); content.height = Math.min(8000, L.height);
      drawContent(cctx, L);
      if (first) scroll = 0; scroll = Math.min(scroll, maxScroll());
      hover = null; dirty = true; return true;
    }
    function refreshEls(m) {               // same look, new DOM nodes: re-point the tiles at the live buttons
      if (!L) return; const fresh = layout(m); L.tiles.forEach((t, i) => { if (fresh.tiles[i]) t.el = fresh.tiles[i].el; }); L.exits.forEach((t, i) => { if (fresh.exits[i]) { t.el = fresh.exits[i].el; t.action = fresh.exits[i].action; } });
    }
    function scrollBy(px) { const s = Math.max(0, Math.min(maxScroll(), scroll + px)); if (s !== scroll) { scroll = s; dirty = true; return true; } return false; }
    function hit(u, v) {
      if (!L) return null; const x = u * W, y = (1 - v) * H;
      if (y >= VIEW) { for (const t of L.exits) if (x >= t.x && x <= t.x + t.w && y >= t.y && y <= t.y + t.h) return t; return null; }
      const cy = y + scroll; for (const t of L.tiles) if (!t.disabled && x >= t.x && x <= t.x + t.w && cy >= t.y && cy <= t.y + t.h && t.y - scroll < VIEW && t.y + t.h - scroll > 0) return t;
      return null;
    }
    function setHover(t) { if (t !== hover) { hover = t; dirty = true; return true; } return false; }
    function draw(hints) {
      if (!dirty || !L) return false; dirty = false;
      const g = dctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, C.bg0); g.addColorStop(1, C.bg1);
      dctx.clearRect(0, 0, W, H); rr(dctx, 4, 4, W - 8, H - 8, 26); dctx.fillStyle = g; dctx.globalAlpha = 0.97; dctx.fill(); dctx.globalAlpha = 1; dctx.lineWidth = 4; dctx.strokeStyle = C.edge; dctx.stroke();
      dctx.save(); dctx.beginPath(); dctx.rect(0, 0, W, VIEW); dctx.clip();
      dctx.drawImage(content, 0, scroll, W, Math.min(VIEW, content.height - scroll), 0, 0, W, Math.min(VIEW, content.height - scroll));
      for (const t of L.tiles) if (t.y + t.h - scroll > 0 && t.y - scroll < VIEW) drawTile(dctx, t, t === hover, scroll);
      // more above / below: a soft fade and an arrow, so the cut-off edge reads as "scroll"
      const fade = (y0, up) => { const f = dctx.createLinearGradient(0, y0, 0, y0 + (up ? 60 : -60)); f.addColorStop(0, 'rgba(7,3,4,0.95)'); f.addColorStop(1, 'rgba(7,3,4,0)'); dctx.fillStyle = f; dctx.fillRect(0, up ? y0 : y0 - 60, W, 60); };
      if (scroll > 2) fade(0, true); if (scroll < maxScroll() - 2) fade(VIEW, false);
      if (maxScroll() > 0) {                                         // a thin track on the right edge: where you are in the list (shows there is more)
        const tx = W - 26, ty = 40, th = VIEW - 80, k = VIEW / L.height, bh = Math.max(50, th * k), by = ty + (th - bh) * (scroll / maxScroll());
        rr(dctx, tx, ty, 8, th, 4); dctx.fillStyle = 'rgba(106,74,36,0.35)'; dctx.fill(); rr(dctx, tx - 2, by, 12, bh, 6); dctx.fillStyle = C.gold; dctx.fill();
      }
      dctx.restore();
      dctx.fillStyle = C.line; dctx.fillRect(PAD, VIEW, W - PAD * 2, 2);
      for (const t of L.exits) drawTile(dctx, Object.assign({ tl: [t.title], bl: [] }, t), t === hover, 0);
      dctx.font = F.hint; dctx.fillStyle = C.dim; dctx.textBaseline = 'middle';
      const more = maxScroll() > 2 ? (scroll < maxScroll() - 2 ? '▼ More below: right stick or drag' : '▲ Top: right stick up') : '';
      dctx.textAlign = 'left'; dctx.fillStyle = more ? C.goldHi : C.dim; dctx.font = more ? '700 26px ' + BODY : F.hint; dctx.fillText(more || hints.left || '', PAD, VIEW + 56); dctx.fillStyle = C.dim; dctx.font = F.hint; dctx.textAlign = 'right'; dctx.fillText(hints.right || '', W - PAD, VIEW + 56);
      tex.needsUpdate = true; return true;
    }
    return { canvas: disp, tex, setModel, refreshEls, scrollBy, hit, setHover, draw, get hover() { return hover; }, get scroll() { return scroll; }, get maxScroll() { return maxScroll(); }, get layout() { return L; }, get model() { return model; }, reset: () => { sig = ''; L = null; hover = null; scroll = 0; }, ASPECT: H / W };
  }
  return { create, extract, layout, W, H, VIEW };
})();
if (typeof module !== 'undefined') module.exports = XrMenu;
