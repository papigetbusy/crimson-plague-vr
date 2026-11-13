/* Wrok's v2 wall textures (assets/textures/walls/v2, 3D skulls and the gold demon banner) on every floor.
   tools/build.js embeds the PNGs as base64 (WallTexData), so the one-file page needs no fetch.
   apply() paints those images onto the world's canvases (stone, floors, the crypt banner ...) at their own size
   (128x256 walls, 128x128 floors). atlas() packs the same images into one 1024x512 sheet so the Crimson Halls
   kit can wear them, with world-projected UVs (64 px per metre, same as the 3D previews). Until the images
   decode, if a set is missing, or with ?voxelwalls (the kit itself is off), the old painted canvases and the
   kit's own atlas stay. */
const WallTexV2 = (function () {
  const SETS = ['crypt', 'blood', 'bog', 'frost', 'ember', 'void'];
  const WORLD = ['texStone', 'texPanel', 'texPillar', 'texFloor', 'texFloor2', 'texFloor3', 'texFloorEdge', 'texCeil', 'texBanner', 'texCarpet', 'texCloth', 'texGold'];
  const ATLAS_W = 1024, ATLAS_H = 512, PAD = 1;
  // packed regions, canvas pixels, rows top-down. The original kit atlas is copied into the top-left 256 for sconces and iron.
  const PACK = {
    kit:    [0, 0, 256, 256],
    stone:  [256, 0, 128, 256],
    panel:  [384, 0, 128, 256],
    pillar: [512, 0, 128, 256],
    banner: [640, 0, 128, 256],
    cloth:  [768, 0, 128, 256],
    floor:  [256, 256, 128, 128],
    floor2: [384, 256, 128, 128],
    floor3: [512, 256, 128, 128],
    floorE: [640, 256, 128, 128],
    ceil:   [768, 256, 128, 128],
    carpet: [896, 256, 128, 128],
    gold:   [256, 384, 64, 64],
  };
  const FILEOF = { stone: 'texStone', panel: 'texPanel', pillar: 'texPillar', floor: 'texFloor', floor2: 'texFloor2',
    floor3: 'texFloor3', floorE: 'texFloorEdge', ceil: 'texCeil', carpet: 'texCarpet', gold: 'texGold', banner: 'texBanner', cloth: 'texCloth' };
  // kit atlas regions (px, rows top-down), from build_crimson_halls.py / render_wall_sections.py
  const REG = {
    wall: [4, 4, 124, 124], floor: [132, 4, 252, 124], pillar: [2, 130, 62, 190], vouss: [66, 130, 126, 190],
    plinth: [4, 194, 124, 222], gold: [4, 226, 124, 254], banner: [132, 130, 186, 250], flame: [192, 130, 220, 186],
    skull: [224, 130, 254, 160], iron: [224, 164, 236, 176], ironl: [240, 164, 252, 176], goldd: [224, 180, 236, 192],
    dark: [240, 180, 252, 192], stone: [194, 194, 254, 254],
  };
  const frac = (x) => x - Math.floor(x);

  function regionOf(u, v) {
    const x = u * 256, y = (1 - v) * 256;
    for (const k in REG) { const r = REG[k]; if (r[0] - 3 <= x && x <= r[2] + 3 && r[1] - 3 <= y && y <= r[3] + 3) return k; }
    return null;
  }
  function keyOf(piece, reg, setId) {
    if (piece === 'floor') return 'floor';                         // variant is chosen from the cell in worldTile
    if (reg === 'banner') return 'banner';
    if (reg === 'pillar') return 'pillar';
    if (reg === 'gold') return (setId === 'crypt') ? 'gold' : (piece === 'straight' ? 'panel' : 'stone');
    if (reg === 'skull') return 'stone';
    if (reg === 'stone' || reg === 'dark') return 'ceil';
    if (reg === 'wall' || reg === 'plinth' || reg === 'vouss') return piece === 'straight' ? 'panel' : 'stone';
    return 'atlas';
  }
  function worldTile(key, piece, wx, wy, wz, nx, ny, nz, u, v, cell) {
    if (key === 'banner') {
      const s = (u * 256 - 132) / 54, tt = ((1 - v) * 256 - 130) / 120;
      return [(18 + s * 92) / 128, 1 - (8 + tt * 192) / 256];
    }
    if (key === 'floor' || key === 'floor2' || key === 'floor3' || key === 'floorE' || key === 'carpet') return [frac(wx / 2), frac(wz / 2)];
    if (key === 'pillar') {
      if (Math.abs(nx) >= Math.abs(nz) && Math.abs(nx) >= Math.abs(ny)) return [frac(wz / 2), frac(wy / 4)];
      if (Math.abs(nz) >= Math.abs(ny)) return [frac(wx / 2), frac(wy / 4)];
      return [frac(wx / 2), frac(wz / 2)];
    }
    if (Math.abs(ny) > 0.7) return [frac(wx / 2), frac(wz / 2)];
    if (key === 'gold') return [frac((Math.abs(nx) > Math.abs(nz) ? wz : wx) / 1), frac(wy / 1)];
    return [frac((Math.abs(nx) > Math.abs(nz) ? wz : wx) / 2), frac(wy / 4)];
  }
  function packUv(key, su, sv) {
    const r = PACK[key]; if (!r) return [0, 0];
    const [x, y, w, h] = r, uu = Math.min(1, Math.max(0, su)), vv = Math.min(1, Math.max(0, sv));
    return [(x + PAD + uu * (w - 2 * PAD)) / ATLAS_W, 1 - (y + PAD + (1 - vv) * (h - 2 * PAD)) / ATLAS_H];
  }
  // public: remap one kit vertex's original atlas UV into the packed v2 atlas (world metres, Y-up)
  function remapUv(piece, u, v, wx, wy, wz, nx, ny, nz, setId, cell) {
    const reg = regionOf(u, v), key0 = keyOf(piece, reg, setId);
    let key = key0;
    if (piece === 'floor') {
      const cx = Math.floor(wx / (cell || 2)), cz = Math.floor(wz / (cell || 2));
      key = ['floor', 'floor2', 'floor3'][((cx + cz) % 3 + 3) % 3];
    }
    if (key === 'atlas') return packUv('kit', u, v);
    return packUv(key, ...worldTile(key, piece, wx, wy, wz, nx, ny, nz, u, v, cell));
  }

  function createInst(THREE) {
    const data = (typeof WallTexData !== 'undefined') ? WallTexData : null;
    const files = (data && data.files) || {};
    const imgs = {}, atlases = {};
    let ready = false, failed = null, started = false, THREE_ = THREE;
    function decode(rel) {
      return new Promise((res, rej) => {
        const b64 = files[rel]; if (!b64) return res(null);
        const im = (typeof document !== 'undefined' && document.createElement) ? document.createElement('img') : null;
        if (!im) return rej(new Error('no document'));
        im.onload = () => res(im); im.onerror = () => rej(new Error('bad image ' + rel));
        im.src = 'data:image/png;base64,' + b64;
      });
    }
    function paintCanvas(img) {
      const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
      const g = c.getContext('2d'); g.imageSmoothingEnabled = false; g.drawImage(img, 0, 0); return c;
    }
    function compose(setId) {
      const c = document.createElement('canvas'); c.width = ATLAS_W; c.height = ATLAS_H;
      const g = c.getContext('2d'); g.imageSmoothingEnabled = false;
      const kit = imgs['kit/crimson_halls_atlas.png']; if (kit) g.drawImage(kit, 0, 0, 256, 256);
      for (const key in FILEOF) {
        const rel = setId + '/' + FILEOF[key] + '.png', im = imgs[rel], r = PACK[key];
        if (!im || !r) continue;
        g.drawImage(im, r[0], r[1], r[2], r[3]);
      }
      // a set with no gold / banner / carpet (every set but the Crypt) keeps the kit's own in those regions
      if (setId !== 'crypt' && kit) {
        const copy = (name, dest) => { const s = REG[name], d = PACK[dest]; if (!s || !d) return;
          g.drawImage(kit, s[0], s[1], s[2] - s[0], s[3] - s[1], d[0], d[1], d[2], d[3]); };
        if (!imgs[setId + '/texGold.png']) copy('gold', 'gold');
        if (!imgs[setId + '/texBanner.png']) copy('banner', 'banner');
        if (!imgs[setId + '/texCarpet.png']) copy('floor', 'carpet');
      }
      const t = new THREE_.CanvasTexture(c);
      t.magFilter = THREE_.NearestFilter; t.minFilter = THREE_.NearestFilter;
      t.generateMipmaps = false; t.wrapS = t.wrapT = THREE_.ClampToEdgeWrapping; t.needsUpdate = true;
      return t;
    }
    function start(onReady) {
      if (started) return; started = true;
      if (!data || !Object.keys(files).length) { failed = 'no WallTexData'; if (onReady) onReady(false); return; }
      if (typeof document === 'undefined') { failed = 'no document'; if (onReady) onReady(false); return; }
      const rels = Object.keys(files);
      Promise.all(rels.map((rel) => decode(rel).then((im) => { if (im) imgs[rel] = im; }).catch((e) => { console.warn('Wall textures v2: ' + e.message); })))
        .then(() => {
          const ok = SETS.some((s) => imgs[s + '/texStone.png']);
          if (!ok) { failed = 'no v2 stone textures decoded'; if (onReady) onReady(false); return; }
          try { for (const s of SETS) if (imgs[s + '/texStone.png']) atlases[s] = compose(s); } catch (e) { failed = String(e && e.message || e); console.warn('Wall textures v2: could not pack an atlas (' + failed + ')'); if (onReady) onReady(false); return; }
          ready = true; if (onReady) onReady(true);
        })
        .catch((e) => { failed = String(e && e.message || e); console.warn('Wall textures v2 could not load, using the old paint: ' + failed); if (onReady) onReady(false); });
    }
    // put v2 images on the world's textures; origCanvases is the Crypt paint (to put back if a set is missing)
    function apply(T, id, origCanvases) {
      if (!ready) return false;
      const set = SETS.indexOf(id) >= 0 ? id : null;
      if (!set) {
        if (origCanvases) for (const n of WORLD) if (T[n] && origCanvases[n]) { T[n].image = origCanvases[n]; T[n].needsUpdate = true; }
        return false;
      }
      let used = 0;
      for (const n of WORLD) {
        const im = imgs[set + '/' + n + '.png'];
        if (im && T[n]) { T[n].image = paintCanvas(im); T[n].needsUpdate = true; used++; }
        else if (origCanvases && origCanvases[n] && T[n]) { T[n].image = origCanvases[n]; T[n].needsUpdate = true; }
      }
      if (!used) return false;
      return true;
    }
    const atlas = (id) => ready && atlases[id] || null;
    return { start, ready: () => ready, apply, atlas, remapUv, status: () => ({ ready, failed, sets: Object.keys(atlases), files: Object.keys(imgs) }) };
  }
  let inst = null;
  const create = (THREE) => { inst = createInst(THREE); return inst; };
  const ready = () => !!(inst && inst.ready());
  const apply = (T, id, orig) => !!(inst && inst.apply(T, id, orig));
  const atlas = (id) => inst && inst.atlas(id) || null;
  const start = (onReady) => inst && inst.start(onReady);
  const status = () => inst ? inst.status() : { ready: false, failed: 'not created' };
  return { create, start, ready, apply, atlas, remapUv, status, SETS, PACK, regionOf, keyOf };
})();
if (typeof module !== 'undefined') module.exports = WallTexV2;
