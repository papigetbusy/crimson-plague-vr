/* World bake: turns the referee's map (rows of cells, torches) into merged quads with torch light baked into the vertex colours.
   Pure: no THREE, no browser, so a tool can draw the same floor offline.
   Returns { chunks: [{ key, cx, cz, pos, uv, col }] (the quads, one list per texture kind per 12 x 12 cell chunk, so the screen can skip what is out of sight),
             buckets: the same merged by texture kind (for tools and tests), light(x, y, z, nx, ny, nz) -> [r, g, b] the same torch light for things that move }.
   skip (optional, from crimson_halls.js): { face: Set('cx,cz:dx,dz'), floor: Set('cx,cz'), cell: Set('cx,cz') } leaves those quads out where a mesh kit is drawn instead
   (the light still counts every wall, so the kit is lit the same). */
const WorldBake = (function () {
  const DIM = 0.82;                                                       // overall light level, a touch darker (owner, 2026-10-19)
  function bake(map, skip) {
    const CELL = map.CELL, WALL_H = map.WALL_H, GW = map.W, GH = map.H, rows = map.rows, torches = map.torches;
    const solidC = (cx, cz) => {
      if (cx < 0 || cz < 0 || cx >= GW || cz >= GH) return true;
      const c = rows[cz][cx];
      return c !== '.' && c !== 'c' && c !== 'D' && c !== 'd';   // the door cells are doorways here: the door itself is its own object (world_view.js)
    };
    function losV(ax, az, bx, bz) {
      const dx = bx - ax, dz = bz - az, d = Math.hypot(dx, dz);
      for (let s = 0.35; s < d - 0.1; s += 0.5) {
        if (solidC(Math.floor((ax + dx / d * s) / CELL), Math.floor((az + dz / d * s) / CELL))) return false;
      }
      return true;
    }
    const TB = 20, tgrid = new Map();                                   // torches filed by 20-unit square, so a point only looks at the ones near it
    for (const t of torches) { const k = Math.floor(t.x / TB) * 4096 + Math.floor(t.z / TB); (tgrid.get(k) || tgrid.set(k, []).get(k)).push(t); }
    const lightCache = new Map();                                       // the same corner is asked for by up to four quads
    function bakeLight(px, py, pz, nx, ny, nz) {
      const ni = nx > 0 ? 0 : nx < 0 ? 1 : ny > 0 ? 2 : ny < 0 ? 3 : nz > 0 ? 4 : 5;
      const ck = ((Math.round(px * 16) * 8192 + Math.round(pz * 16)) * 128 + Math.round(py * 16)) * 8 + ni;
      const hit = lightCache.get(ck); if (hit) return hit;
      let r = 0.17, g = 0.125, b = 0.15;
      const bx = Math.floor(px / TB), bz = Math.floor(pz / TB);
      for (let ox = -1; ox <= 1; ox++) for (let oz = -1; oz <= 1; oz++) {
        const list = tgrid.get((bx + ox) * 4096 + bz + oz); if (!list) continue;
        for (const t of list) {
          const dx = t.x - px, dy = t.y - py, dz = t.z - pz;
          const d2 = dx * dx + dy * dy + dz * dz;
          if (d2 > 420) continue;
          const d = Math.sqrt(d2) || 0.001;
          const nd = (nx * dx + ny * dy + nz * dz) / d;
          if (nd < 0.02) continue;
          if (!losV(px + nx * 0.06, pz + nz * 0.06, t.x, t.z)) continue;
          const f = (t.kind === 'brazier' ? 3.3 : 2.5) / (1 + d2 / 12) * (0.3 + 0.7 * nd);
          r += f; g += f * 0.56; b += f * 0.24;
        }
      }
      const out = [Math.min(r, 2.0) * DIM, Math.min(g, 2.0) * DIM, Math.min(b, 2.0) * DIM];
      lightCache.set(ck, out); return out;
    }
    const CHUNK = 12, chunkMap = {};
    let curChunk = '0,0', curCx = 0, curCz = 0;
    const B = (k) => { const id = k + '@' + curChunk; return chunkMap[id] || (chunkMap[id] = { key: k, cx: curCx, cz: curCz, pos: [], uv: [], col: [] }); };
    function addFace(key, O, U, V, nu, nv, n) {
      const b = B(key);
      const vert = (a, c) => {
        const p = [O[0] + U[0] * a + V[0] * c, O[1] + U[1] * a + V[1] * c, O[2] + U[2] * a + V[2] * c];
        return { p, a, c, l: bakeLight(p[0], p[1], p[2], n[0], n[1], n[2]) };
      };
      const push = (v) => { b.pos.push(v.p[0], v.p[1], v.p[2]); b.uv.push(v.a, v.c); b.col.push(v.l[0], v.l[1], v.l[2]); };
      for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) {
        const v00 = vert(i / nu, j / nv), v10 = vert((i + 1) / nu, j / nv), v11 = vert((i + 1) / nu, (j + 1) / nv), v01 = vert(i / nu, (j + 1) / nv);
        push(v00); push(v10); push(v11); push(v00); push(v11); push(v01);
      }
    }
    function addBox(key, x0, y0, z0, x1, y1, z1) {
      const dx = x1 - x0, dy = y1 - y0, dz = z1 - z0;
      addFace(key, [x1, y0, z1], [0, 0, -dz], [0, dy, 0], 1, 1, [1, 0, 0]);
      addFace(key, [x0, y0, z0], [0, 0, dz], [0, dy, 0], 1, 1, [-1, 0, 0]);
      addFace(key, [x0, y0, z1], [dx, 0, 0], [0, dy, 0], 1, 1, [0, 0, 1]);
      addFace(key, [x1, y0, z0], [-dx, 0, 0], [0, dy, 0], 1, 1, [0, 0, -1]);
      addFace(key, [x0, y1, z1], [dx, 0, 0], [0, 0, -dz], 1, 1, [0, 1, 0]);
      addFace(key, [x0, y0, z0], [dx, 0, 0], [0, 0, dz], 1, 1, [0, -1, 0]);
    }
    const VREP = Math.max(3, Math.round(3 * WALL_H / 5.5));          // the wall texture repeats up the taller walls instead of stretching
    const KIND = { '#': 'stone', 'B': 'stone', 'W': 'panel', 'P': 'pillar' };
    // the floor tile set for a cell: worn beside the carpet, otherwise a plain, cracked or warm-stained set mixed by position
    function floorKey(cx, cz) {
      if (rows[cz][cx - 1] === 'c' || rows[cz][cx + 1] === 'c') return 'floorEdge';
      const h = (cx * 7 + cz * 13 + cx * cz) % 7;
      return h === 0 || h === 3 ? 'floor2' : h === 5 ? 'floor3' : 'floor';
    }
    // a banner: a cloth slab and a gold rod standing a hand's width off the wall (the wall behind stays plain stone)
    function hangBanner(nx, nz, plane, mid) {
      const slab = (key, half, d0, d1, y0, y1) => {
        const a = nx ? [plane + nx * d0, plane + nx * d1] : [mid - half, mid + half], b = nz ? [plane + nz * d0, plane + nz * d1] : [mid - half, mid + half];
        addBox(key, Math.min(a[0], a[1]), y0, Math.min(b[0], b[1]), Math.max(a[0], a[1]), y1, Math.max(b[0], b[1]));
      };
      const top = Math.min(WALL_H - 1.0, 8.6);                         // banners hang from a rod no higher than 8.6, so they stay banners when the roof is high
      slab('cloth', 0.78, 0.04, 0.14, 0.8, top);
      slab('gold', 0.92, 0.0, 0.2, top, top + 0.16);
    }
    for (let cz = 0; cz < GH; cz++) for (let cx = 0; cx < GW; cx++) {
      const ch = rows[cz][cx], x0 = cx * CELL, x1 = x0 + CELL, z0 = cz * CELL, z1 = z0 + CELL;
      curCx = Math.floor(cx / CHUNK); curCz = Math.floor(cz / CHUNK); curChunk = curCx + ',' + curCz;
      if (ch === '.' || ch === 'c' || ch === 'D' || ch === 'd') {
        if (!(skip && skip.floor.has(cx + ',' + cz))) addFace(ch === 'c' ? 'carpet' : floorKey(cx, cz), [x0, 0, z1], [CELL, 0, 0], [0, 0, -CELL], 2, 2, [0, 1, 0]);
        addFace('ceil', [x0, WALL_H, z0], [CELL, 0, 0], [0, 0, CELL], 2, 2, [0, -1, 0]);
        if (cz % 4 === 0 && cz > 0 && cz < GH - 1) {                    // a stone rib across the ceiling every fourth cell, with a gold edge: depth and rhythm overhead
          addBox('stone', x0, WALL_H - 0.6, z0, x1, WALL_H, z0 + 0.6);
          addBox('gold', x0, WALL_H - 0.72, z0, x1, WALL_H - 0.6, z0 + 0.6);
        }
        continue;
      }
      const key = KIND[ch];
      if (skip && skip.cell.has(cx + ',' + cz)) continue;
      const shown = (dx, dz) => !solidC(cx + dx, cz + dz) && !(skip && skip.face.has(cx + ',' + cz + ':' + dx + ',' + dz));
      if (ch === 'B') {
        if (shown(1, 0)) hangBanner(1, 0, x1, z0 + CELL / 2);
        if (shown(-1, 0)) hangBanner(-1, 0, x0, z0 + CELL / 2);
        if (shown(0, 1)) hangBanner(0, 1, z1, x0 + CELL / 2);
        if (shown(0, -1)) hangBanner(0, -1, z0, x0 + CELL / 2);
      }
      if (shown(1, 0)) addFace(key, [x1, 0, z1], [0, 0, -CELL], [0, WALL_H, 0], 2, VREP, [1, 0, 0]);
      if (shown(-1, 0)) addFace(key, [x0, 0, z0], [0, 0, CELL], [0, WALL_H, 0], 2, VREP, [-1, 0, 0]);
      if (shown(0, 1)) addFace(key, [x0, 0, z1], [CELL, 0, 0], [0, WALL_H, 0], 2, VREP, [0, 0, 1]);
      if (shown(0, -1)) addFace(key, [x1, 0, z0], [-CELL, 0, 0], [0, WALL_H, 0], 2, VREP, [0, 0, -1]);
      if (ch === 'P') {
        addBox('gold', x0 - 0.14, 0, z0 - 0.14, x1 + 0.14, 0.38, z1 + 0.14);
        addBox('gold', x0 - 0.14, WALL_H - 0.7, z0 - 0.14, x1 + 0.14, WALL_H - 0.3, z1 + 0.14);
        addBox('stone', x0 - 0.06, WALL_H - 0.3, z0 - 0.06, x1 + 0.06, WALL_H, z1 + 0.06);
      }
    }

    const chunks = Object.values(chunkMap);
    for (const c of chunks) if (c.key === 'gold') for (let i = 0; i < c.col.length; i++) c.col[i] *= 0.55;   // gold trim catches the torch light but must not blow out to flat orange
    let merged = null;
    return {
      chunks, light: bakeLight,
      get buckets() {                                                    // all chunks of one kind joined (tools and tests)
        if (merged) return merged;
        merged = {};
        for (const c of chunks) { const m = merged[c.key] || (merged[c.key] = { pos: [], uv: [], col: [] }); for (const k of ['pos', 'uv', 'col']) for (const v of c[k]) m[k].push(v); }
        return merged;
      }
    };
  }
  return { bake };
})();
if (typeof module !== 'undefined') module.exports = WorldBake;
