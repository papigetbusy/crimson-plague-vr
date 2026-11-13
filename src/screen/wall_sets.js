/* Wall sets: six looks for the halls, one per floor, cycling (floor 1 is the Gothic Crypt, floor 2 the Blood Catacombs ... floor 7 is the Crypt again).
   Each set repaints the wall stone, the wall panel, the pillar, the floor tiles and the ceiling in place (same little canvases, so nothing else has to change),
   and brings its own fog colour and flame colour. Look only: the referee only says which floor you are on.
   Everything is painted a pixel at a time with a seeded random, so a set looks the same every time. */
const WallSets = (function () {
  const LIST = [
    { id: 'crypt',  name: 'Gothic Crypt',     blurb: 'The original: grey blocks, crimson banners, gold trim',       fog: [12, 4, 6],   flame: [0xff8a26, 0xffdc7a] },
    { id: 'blood',  name: 'Blood Catacombs',  blurb: 'Red-brown brick, dripping blood, skulls in the walls',        fog: [24, 3, 5],   flame: [0xff4a24, 0xffb070] },
    { id: 'bog',    name: 'Rotting Bog Vault', blurb: 'Slimy green stone, moss, roots and glowing fungus',          fog: [4, 14, 6],   flame: [0x7cff5a, 0xe8ffb0] },
    { id: 'frost',  name: 'Frozen Ossuary',   blurb: 'Pale blue ice stone, frost, icicles and frozen bones',        fog: [8, 13, 24],  flame: [0x7fd8ff, 0xeaf8ff] },
    { id: 'ember',  name: 'Ashen Forge',      blurb: 'Black basalt split by glowing lava cracks, soot and embers',  fog: [24, 7, 2],   flame: [0xff5a1a, 0xffd05a] },
    { id: 'void',   name: 'Void Cathedral',   blurb: 'Indigo stone, glowing violet runes and watching eyes',        fog: [11, 4, 22],  flame: [0xb07aff, 0xeadcff] }
  ];
  const IDS = LIST.map((s) => s.id);
  const forFloor = (floor) => LIST[(((floor | 0) - 1) % LIST.length + LIST.length) % LIST.length];
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const rgb = (r, g, b) => 'rgb(' + (clamp(r, 0, 255) | 0) + ',' + (clamp(g, 0, 255) | 0) + ',' + (clamp(b, 0, 255) | 0) + ')';
  function mulberry(seed) {
    let a = seed >>> 0;
    return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  // tiny drawing helpers on a canvas context
  const dot = (g, x, y, c, n) => { if (x < 0 || y < 0) return; const k = n || 0; g.fillStyle = rgb(c[0] + k, c[1] + k, c[2] + k); g.fillRect(x | 0, y | 0, 1, 1); };
  const rect = (g, x, y, w, h, c, r, v) => { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) dot(g, x + i, y + j, c, ((r ? r() : 0.5) - 0.5) * (v || 0)); };
  // masonry: staggered blocks with a dark mortar line, a lit top-left edge and a little tone change per block
  function bricks(g, w, h, r, base, mortar, o) {
    o = o || {}; const bh = o.bh || 8, bw = o.bw || 16;
    for (let by = 0; by * bh < h; by++) {
      const off = (by % 2) * (bw / 2);
      for (let bx = -1; bx * bw < w; bx++) {
        const x0 = bx * bw + off, y0 = by * bh, tone = (r() - 0.5) * (o.tone || 14);
        for (let j = 0; j < bh; j++) for (let i = 0; i < bw; i++) {
          const x = x0 + i, y = y0 + j; if (x < 0 || x >= w || y >= h) continue;
          let k = tone + (r() - 0.5) * (o.grain || 12), c = base;
          if (i === 0 || j === 0) { c = mortar; k = 0; } else if (i === 1 || j === 1) k += 11;
          dot(g, x, y, c, k);
        }
      }
    }
  }
  const plinthOf = (g, w, h, r, c, trim) => { rect(g, 0, h - 7, w, 7, c, r, 8); for (let x = 0; x < w; x += 2) dot(g, x, h - 7, trim); };
  // a drip: a streak running down from (x, y) of length n with a fatter bead at the end
  function drip(g, x, y, n, c, c2) { for (let j = 0; j < n; j++) dot(g, x, y + j, c, -j * 1.5); dot(g, x, y + n, c2 || c); dot(g, x - 1, y + n, c, -10); dot(g, x + 1, y + n, c, -10); }
  // a carved skull, 9 wide, in a dark niche
  function skull(g, x, y, bone, dark) {
    rect(g, x - 1, y - 1, 11, 12, dark); rect(g, x, y, 9, 4, bone); rect(g, x + 1, y + 4, 7, 3, bone); rect(g, x + 2, y + 7, 5, 2, bone);
    rect(g, x + 1, y + 2, 2, 2, dark); rect(g, x + 6, y + 2, 2, 2, dark); dot(g, x + 4, y + 5, dark); rect(g, x + 3, y + 8, 1, 1, dark); rect(g, x + 5, y + 8, 1, 1, dark);
  }

  const SETS = {
    // ---- 2 Blood Catacombs
    blood: {
      stone(g, w, h, r) {
        WallMaterials.bones(g, w, h, r, { back: [36, 8, 10], bone: [160, 146, 120] });
        for (const x of [4, 13, 20, 28]) if (r() < 0.9) drip(g, x, 2 + Math.floor(r() * 18), 8 + Math.floor(r() * 18), [150, 14, 20], [190, 30, 34]);   // blood running down the wall
        skull(g, 11, 22, [220, 208, 176], [14, 6, 8]);
        for (let n = 0; n < 22; n++) dot(g, Math.floor(r() * w), Math.floor(r() * (h - 8)), [120, 14, 18], 10);                              // spatter
        plinthOf(g, w, h, r, [62, 44, 40], [196, 176, 140]);
        for (let x = 1; x < w; x += 4) rect(g, x, h - 6, 2, 3, [214, 200, 168], r, 10);                                                        // a row of bone ends along the foot of the wall
      },
      inlay: [120, 14, 20], trim: [196, 176, 140],
      floor(g, w, h, r, kind) {
        for (let ty = 0; ty < 2; ty++) for (let tx = 0; tx < 2; tx++) { const tone = (r() - 0.5) * 12; for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) { let v = 46 + tone + (r() - 0.5) * 12; if (i === 0 || j === 0) v = 16; else if (i === 1 || j === 1) v += 6; dot(g, tx * 32 / 2 + i, ty * 16 + j, [v + 22, v - 8, v - 6]); } }
        for (let n = 0; n < (kind === 'warm' ? 5 : 2); n++) { const cx = 4 + Math.floor(r() * 24), cy = 4 + Math.floor(r() * 24); for (let j = -2; j <= 2; j++) for (let i = -3; i <= 3; i++) if (i * i / 9 + j * j / 4 < 1) dot(g, cx + i, cy + j, [118, 12, 16], (r() - 0.5) * 18); }   // blood pools
        if (kind === 'cracked') for (let k = 0; k < 2; k++) { let x = 2 + Math.floor(r() * 26), y = 2 + Math.floor(r() * 26); for (let n = 0; n < 11; n++) { dot(g, x, y, [16, 8, 8]); x += r() < 0.6 ? 1 : 0; y += r() < 0.6 ? 1 : 0; } }
      },
      ceil: [0.55, [88, 42, 38]]
    },
    // ---- 3 Rotting Bog Vault
    bog: {
      stone(g, w, h, r) {
        WallMaterials.planks(g, w, h, r, { wood: [74, 62, 40], gap: [14, 16, 10] });
        for (let x = 0; x < w; x++) { const d = 3 + Math.floor(r() * 7); for (let j = 0; j < d; j++) dot(g, x, h - 8 - j, [56 + r() * 20, 108 + r() * 30, 48], -j * 3); }   // moss crawling up from the foot
        for (let n = 0; n < 5; n++) { const x = Math.floor(r() * w), y = 4 + Math.floor(r() * 30); rect(g, x, y, 3 + Math.floor(r() * 4), 2, [64, 118, 50], r, 20); }   // moss patches
        for (const x of [5, 17, 26]) drip(g, x, 3 + Math.floor(r() * 14), 10 + Math.floor(r() * 14), [110, 190, 70], [190, 255, 120]);    // slime
        for (const x of [9, 22]) for (let j = 0; j < 22; j++) dot(g, x + (j % 5 === 0 ? 1 : 0), 14 + j, [40, 28, 18], j);                      // roots creeping down
        for (const [x, y] of [[8, 30], [24, 12], [14, 44], [28, 38]]) { dot(g, x, y, [170, 255, 130]); dot(g, x + 1, y, [110, 220, 90]); dot(g, x, y + 1, [110, 220, 90]); }   // glowing fungus
        plinthOf(g, w, h, r, [30, 38, 28], [110, 150, 70]);
      },
      inlay: [48, 96, 40], trim: [150, 200, 90],
      floor(g, w, h, r, kind) {
        for (let ty = 0; ty < 2; ty++) for (let tx = 0; tx < 2; tx++) { const tone = (r() - 0.5) * 10; for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) { let v = 40 + tone + (r() - 0.5) * 12; if (i === 0 || j === 0) v = 14; else if (i === 1 || j === 1) v += 6; dot(g, tx * 16 + i, ty * 16 + j, [v - 4, v + 8, v - 6]); } }
        for (let n = 0; n < (kind === 'warm' ? 4 : 2); n++) { const cx = 4 + Math.floor(r() * 24), cy = 4 + Math.floor(r() * 24); for (let j = -2; j <= 2; j++) for (let i = -3; i <= 3; i++) if (i * i / 9 + j * j / 4 < 1) dot(g, cx + i, cy + j, [40, 78, 36], (r() - 0.5) * 14); dot(g, cx, cy, [150, 240, 110]); }   // slime puddles with a gleam
      },
      ceil: [0.55, [48, 62, 44]]
    },
    // ---- 4 Frozen Ossuary
    frost: {
      stone(g, w, h, r) {
        WallMaterials.shards(g, w, h, r, { ice: [66, 100, 148], crack: [196, 228, 252] });
        for (let n = 0; n < 60; n++) dot(g, Math.floor(r() * w), Math.floor(r() * (h - 8)), [225, 240, 255], -r() * 30);                         // frost speckles
        for (let by = 0; by * 8 < h; by++) for (let x = 0; x < w; x += 2) if (r() < 0.5) dot(g, x, by * 8 + 1, [200, 228, 250]);                // frost on the top edge of every block
        for (const x of [4, 10, 18, 25, 29]) { const L = 3 + Math.floor(r() * 7); for (let j = 0; j < L; j++) dot(g, x + (j > L - 3 ? 0 : 0), 8 + j, [190, 232, 255], -j * 6); for (let j = 0; j < 2; j++) dot(g, x - 1, 8 + j, [160, 210, 240]); }   // icicles
        for (let j = 0; j < 10; j++) { dot(g, 10 + j, 32 + Math.floor(j * 0.6), [140, 220, 255]); dot(g, 11 + j, 32 + Math.floor(j * 0.6), [90, 170, 230]); }   // a crack of blue ice
        rect(g, 19, 40, 8, 6, [230, 240, 250], r, 12); rect(g, 20, 41, 2, 2, [26, 34, 48]); rect(g, 24, 41, 2, 2, [26, 34, 48]);                  // a skull frozen into the wall
        plinthOf(g, w, h, r, [36, 48, 68], [190, 226, 250]);
      },
      inlay: [60, 110, 160], trim: [190, 226, 250],
      floor(g, w, h, r, kind) {
        for (let ty = 0; ty < 2; ty++) for (let tx = 0; tx < 2; tx++) { const tone = (r() - 0.5) * 10; for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) { let v = 70 + tone + (r() - 0.5) * 12; if (i === 0 || j === 0) v = 26; else if (i === 1 || j === 1) v += 10; dot(g, tx * 16 + i, ty * 16 + j, [v - 8, v + 6, v + 24]); } }
        for (let n = 0; n < 26; n++) dot(g, Math.floor(r() * w), Math.floor(r() * h), [230, 244, 255]);                                          // frost
        if (kind === 'cracked') for (let k = 0; k < 2; k++) { let x = 2 + Math.floor(r() * 26), y = 2 + Math.floor(r() * 26); for (let n = 0; n < 12; n++) { dot(g, x, y, [150, 220, 255]); x += r() < 0.6 ? 1 : 0; y += r() < 0.6 ? 1 : 0; } }
      },
      ceil: [0.6, [62, 82, 112]]
    },
    // ---- 5 Ashen Forge
    ember: {
      stone(g, w, h, r) {
        WallMaterials.columns(g, w, h, r, { rock: [52, 48, 56], gap: [8, 6, 8] });
        for (let n = 0; n < 4; n++) {                                                                                                              // lava cracks: a wandering vein with a bright core
          let x = 2 + Math.floor(r() * 28), y = 2 + Math.floor(r() * 12) + n * 12;
          for (let s = 0; s < 14; s++) { dot(g, x, y, [255, 96, 22]); dot(g, x + 1, y, [255, 170, 60]); dot(g, x - 1, y, [140, 40, 12]); y += 1; x += r() < 0.5 ? 1 : r() < 0.5 ? -1 : 0; x = clamp(x, 2, w - 3); }
        }
        for (let n = 0; n < 30; n++) dot(g, Math.floor(r() * w), Math.floor(r() * (h - 8)), [18, 16, 18], -r() * 10);                              // soot
        for (let n = 0; n < 9; n++) dot(g, Math.floor(r() * w), Math.floor(r() * (h - 8)), [255, 200, 90]);                                        // embers stuck in the stone
        plinthOf(g, w, h, r, [24, 14, 12], [190, 80, 30]);
        for (let x = 0; x < w; x++) dot(g, x, h - 8, [255, 90, 20], (r() - 0.5) * 40);                                                           // a glowing seam along the foot
      },
      inlay: [140, 44, 14], trim: [255, 150, 50],
      floor(g, w, h, r, kind) {
        for (let ty = 0; ty < 2; ty++) for (let tx = 0; tx < 2; tx++) { const tone = (r() - 0.5) * 8; for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) { let v = 30 + tone + (r() - 0.5) * 10; if (i === 0 || j === 0) v = 9; else if (i === 1 || j === 1) v += 5; dot(g, tx * 16 + i, ty * 16 + j, [v, v - 2, v + 1]); } }
        const veins = kind === 'warm' ? 4 : kind === 'cracked' ? 3 : 1;
        for (let k = 0; k < veins; k++) { let x = 2 + Math.floor(r() * 26), y = 2 + Math.floor(r() * 26); for (let n = 0; n < 12; n++) { dot(g, x, y, [255, 110, 26]); dot(g, x + 1, y, [160, 50, 14]); x += r() < 0.6 ? 1 : 0; y += r() < 0.6 ? 1 : 0; } }
      },
      ceil: [0.5, [40, 34, 38]]
    },
    // ---- 6 Void Cathedral
    void: {
      stone(g, w, h, r) {
        WallMaterials.slabs(g, w, h, r, { stone: [50, 38, 84], gap: [10, 6, 20] });
        const RUNES = [[3, 5], [25, 8], [4, 46], [26, 44], [14, 52]];
        for (const [x, y] of RUNES) { dot(g, x, y, [170, 110, 255]); dot(g, x + 1, y + 1, [170, 110, 255]); dot(g, x, y + 2, [170, 110, 255]); dot(g, x + 2, y + 2, [120, 70, 230]); dot(g, x + 1, y + 3, [170, 110, 255]); dot(g, x - 1, y + 1, [120, 70, 230]); }   // glowing runes
        // a carved eye in the middle of the wall: an almond shape, a violet iris and a black pupil
        for (let i = -9; i <= 9; i++) { const hgt = Math.round(4 * (1 - (i * i) / 81)); for (let j = -hgt; j <= hgt; j++) dot(g, 16 + i, 24 + j, Math.abs(j) === hgt ? [10, 6, 20] : [214, 200, 236], -Math.abs(i) * 2); }
        for (let j = -3; j <= 3; j++) for (let i = -3; i <= 3; i++) if (i * i + j * j <= 9) dot(g, 16 + i, 24 + j, [150, 80, 255], -(i * i + j * j) * 4);
        rect(g, 15, 22, 2, 5, [8, 4, 16]); dot(g, 14, 22, [255, 255, 255]);
        for (const x of [8, 23]) for (let j = 0; j < 14; j++) dot(g, x + Math.round(Math.sin(j * 0.8) * 1.5), 34 + j, [90, 50, 170], j);          // violet tendrils
        plinthOf(g, w, h, r, [20, 14, 34], [140, 90, 230]);
      },
      inlay: [70, 36, 140], trim: [160, 110, 255],
      floor(g, w, h, r, kind) {
        for (let ty = 0; ty < 2; ty++) for (let tx = 0; tx < 2; tx++) { const tone = (r() - 0.5) * 8; for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) { let v = 36 + tone + (r() - 0.5) * 10; if (i === 0 || j === 0) v = 12; else if (i === 1 || j === 1) v += 6; dot(g, tx * 16 + i, ty * 16 + j, [v, v - 6, v + 26]); } }
        for (let n = 0; n < (kind === 'warm' ? 8 : 4); n++) dot(g, Math.floor(r() * w), Math.floor(r() * h), [150, 100, 255]);                         // glints in the dark
        if (kind === 'cracked') for (let k = 0; k < 2; k++) { let x = 2 + Math.floor(r() * 26), y = 2 + Math.floor(r() * 26); for (let n = 0; n < 11; n++) { dot(g, x, y, [120, 70, 230]); x += r() < 0.6 ? 1 : 0; y += r() < 0.6 ? 1 : 0; } }
      },
      ceil: [0.5, [40, 30, 64]]
    }
  };

  // the carved panel (a framed inlay) and the pillar (fluted, with rings) are built on the set's own stone, in the set's accent colours
  function panel(set, g, w, h, r) {
    set.stone(g, w, h, r); rect(g, 7, 6, 18, 46, set.inlay, r, 16);
    for (let x = 8; x < 25; x += 5) rect(g, x, 7, 1, 44, [set.inlay[0] * 0.4, set.inlay[1] * 0.4, set.inlay[2] * 0.4]);
    for (let y = 7; y < 52; y += 5) rect(g, 8, y, 16, 1, [set.inlay[0] * 0.4, set.inlay[1] * 0.4, set.inlay[2] * 0.4]);
    for (let i = 0; i < 22; i++) { dot(g, 5 + i, 4, set.trim, (r() - 0.5) * 20); dot(g, 5 + i, 53, set.trim, (r() - 0.5) * 20); }
    for (let j = 0; j < 50; j++) { dot(g, 5, 4 + j, set.trim, (r() - 0.5) * 20); dot(g, 26, 4 + j, set.trim, (r() - 0.5) * 20); }
  }
  function pillar(set, g, w, h, r) {
    set.stone(g, w, h, r); rect(g, 0, 0, w, h, [0, 0, 0], r, 0);
    bricks(g, w, h, r, [set.inlay[0] * 0.5 + 24, set.inlay[1] * 0.5 + 24, set.inlay[2] * 0.5 + 24], [10, 8, 10], { tone: 10, bh: 16, bw: 32 });
    rect(g, 0, 3, w, 3, set.trim, r, 30); rect(g, 0, 56, w, 3, set.trim, r, 30);
    for (const x of [3, 9, 22, 28]) for (let y = 8; y < 54; y++) { dot(g, x, y, [18, 16, 20]); dot(g, x + 1, y, [64, 60, 70], (r() - 0.5) * 8); }
    rect(g, 11, 27, 10, 3, set.trim, r, 30); rect(g, 11, 38, 10, 2, set.trim, r, 30);
    for (let j = -4; j <= 4; j++) for (let i = -4; i <= 4; i++) { const d = Math.abs(i) + Math.abs(j); if (d > 4) continue; dot(g, 16 + i, 33 + j, d === 4 ? set.trim : [set.inlay[0] + 90 - d * 12, set.inlay[1] + 60 - d * 8, set.inlay[2] + 90 - d * 12]); }
  }
  const ceilOf = (set, g, w, h, r) => bricks(g, w, h, r, set.ceil[1], [10, 8, 10], { tone: 10 });

  // repaint a texture's canvas in place; textures here are the ones WorldTex.create made (T.texStone ...)
  const paintOn = (tex, seed, fn) => { const c = tex.image, g = c.getContext('2d'); fn(g, c.width, c.height, mulberry(seed)); tex.needsUpdate = true; };
  function create(T) {
    const names = ['texStone', 'texPanel', 'texPillar', 'texFloor', 'texFloor2', 'texFloor3', 'texFloorEdge', 'texCeil'];
    const extras = ['texBanner', 'texCarpet', 'texCloth', 'texGold'];
    const orig = {}, origCanvas = {};
    for (const n of names.concat(extras)) { if (!T[n]) continue; const c = T[n].image; origCanvas[n] = c; orig[n] = c.getContext && c.getContext('2d') ? c.getContext('2d').getImageData(0, 0, c.width, c.height) : null; }      // the Crypt is the original paint, kept to put back
    let cur = 'crypt';
    function restore(n) {
      if (!T[n] || !origCanvas[n]) return;
      if (T[n].image !== origCanvas[n]) T[n].image = origCanvas[n];
      else if (orig[n]) T[n].image.getContext('2d').putImageData(orig[n], 0, 0);
      T[n].needsUpdate = true;
    }
    function apply(id) {
      // Wrok's v2 textures, when they have decoded: same names, bigger canvases. If they are not ready, the paint below stays.
      if (typeof WallTexV2 !== 'undefined' && WallTexV2.ready() && WallTexV2.apply(T, SETS[id] ? id : 'crypt', origCanvas)) { cur = SETS[id] ? id : 'crypt'; return; }
      const set = SETS[id];
      if (!set) { for (const n of names) restore(n); for (const n of extras) restore(n); cur = 'crypt'; return; }
      for (const n of names) if (T[n] && T[n].image !== origCanvas[n]) T[n].image = origCanvas[n];   // a previous v2 apply may have swapped in a bigger canvas
      for (const n of extras) restore(n);
      paintOn(T.texStone, 101, (g, w, h, r) => set.stone(g, w, h, r));
      paintOn(T.texPanel, 102, (g, w, h, r) => panel(set, g, w, h, r));
      paintOn(T.texPillar, 103, (g, w, h, r) => pillar(set, g, w, h, r));
      paintOn(T.texFloor, 104, (g, w, h, r) => set.floor(g, w, h, r, 'plain'));
      paintOn(T.texFloor2, 105, (g, w, h, r) => set.floor(g, w, h, r, 'cracked'));
      paintOn(T.texFloor3, 106, (g, w, h, r) => set.floor(g, w, h, r, 'warm'));
      paintOn(T.texFloorEdge, 107, (g, w, h, r) => set.floor(g, w, h, r, 'worn'));
      paintOn(T.texCeil, 108, (g, w, h, r) => ceilOf(set, g, w, h, r));
      cur = id;
    }
    return { apply, current: () => cur };
  }
  return { LIST, IDS, forFloor, create, SETS };
})();
if (typeof module !== 'undefined') module.exports = WallSets;
