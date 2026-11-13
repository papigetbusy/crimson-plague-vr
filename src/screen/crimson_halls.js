/* Crimson Halls wall kit (Wrok's low-poly GLB pieces, assets/models/env/crimson_halls/) dressing one hall of the VR test map (?sandbox) only.
   plan(map) is pure: it picks the start room and says where every piece goes (walls 3 modules high to reach the 11.5 m roof, the top row
   squashed to 0.875; a corner piece in each inner corner; the room's pillar cells as kit pillars scaled to the 2 m cell; a doorway arch on each
   narrow opening; floor tiles; banners; a kit sconce on every torch of the room, its `flame` on the torch light at 2.85 m) and which baked
   faces, floors, cells and pooled torch props to leave out. The gameplay walls are untouched: the referee's cells are still the collision,
   only the look changes. build() merges every placed piece into ONE mesh (one material, one 256 px atlas: one draw call), lit like the
   baked world (torch light per vertex, MeshBasic + vertex colours). Until the GLBs decode, if they fail, or with ?voxelwalls, the old walls stay. */
const CrimsonHalls = (function () {
  const ROW_H = 4, ARCH_MAX = 3;                                          // module height (m); widest opening (cells) that gets an arch
  const open = (c) => c === '.' || c === 'c';
  const solidCh = (c) => !(c === '.' || c === 'c' || c === 'D' || c === 'd');
  const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  const yawOf = (nx, nz) => Math.atan2(nx, nz);                           // turns a piece's +Z (its room side) toward (nx, nz)

  function plan(map) {
    const C = map.CELL, H = map.WALL_H, rows = map.rows;
    const R = (map.rooms || []).find((r) => r.kind === 'start'); if (!R) return null;
    const inR = (cx, cz) => cx >= R.x && cx < R.x + R.w && cz >= R.z && cz < R.z + R.h;
    const at = (cx, cz) => (cz < 0 || cz >= map.H || cx < 0 || cx >= map.W) ? '#' : rows[cz][cx];
    const rowsY = []; for (let y = 0; y < H - 1e-6; y += ROW_H) rowsY.push([y, Math.min(1, (H - y) / ROW_H)]);   // [bottom, y scale]: 0, 4, 8 (x0.875)
    const place = [], skip = { face: new Set(), floor: new Set(), cell: new Set(), torch: new Set() };
    const put = (piece, x, y, z, yaw, sx, sy, sz) => place.push({ piece, x, y, z, yaw, sx: sx || 1, sy: sy || 1, sz: sz || 1 });
    const stack = (piece, x, z, yaw, sx, sz) => { for (const [y, s] of rowsY) put(piece, x, y, z, yaw, sx, s, sz); };
    // pillar cells inside the room: a kit pillar the size of the cell (collision is the whole 2 m cell)
    const pillarCell = (cx, cz) => at(cx, cz) === 'P' && inR(cx, cz) && DIRS.every(([dx, dz]) => inR(cx + dx, cz + dz));
    for (let cz = R.z; cz < R.z + R.h; cz++) for (let cx = R.x; cx < R.x + R.w; cx++) if (pillarCell(cx, cz)) {
      skip.cell.add(cx + ',' + cz); stack('pillar', (cx + 0.5) * C, (cz + 0.5) * C, 0, C / 0.8, C / 0.8);
    }
    // the room's wall edges (an open room cell beside a solid cell) and openings (beside an open cell outside the room)
    const walls = new Map(), opens = [];
    for (let cz = R.z; cz < R.z + R.h; cz++) for (let cx = R.x; cx < R.x + R.w; cx++) {
      if (!open(at(cx, cz))) continue;
      if (at(cx, cz) === '.') { skip.floor.add(cx + ',' + cz); put('floor', (cx + 0.5) * C, 0, (cz + 0.5) * C, 0); }
      for (const [dx, dz] of DIRS) {
        const ncx = cx + dx, ncz = cz + dz, ch = at(ncx, ncz);
        if (pillarCell(ncx, ncz)) continue;
        const e = { cx, cz, dx, dz, nx: -dx, nz: -dz, x: (cx + 0.5 + dx / 2) * C, z: (cz + 0.5 + dz / 2) * C };
        if (solidCh(ch)) { walls.set(cx + ',' + cz + ':' + dx + ',' + dz, e); skip.face.add(ncx + ',' + ncz + ':' + (-dx) + ',' + (-dz)); }
        else if (!inR(ncx, ncz) && open(ch)) opens.push(e);
      }
    }
    // narrow openings get a doorway arch: a run of opening edges along one side, with wall on both ends
    const cut = new Map();                                                // wall edge -> [from, to] of its 2 m left uncovered by an arch (along the wall, -1..1)
    const used = new Set(), key = (e) => e.cx + ',' + e.cz + ':' + e.dx + ',' + e.dz;
    const arches = [];
    for (const e of opens) {
      if (used.has(key(e))) continue;
      const ax = e.dz !== 0 ? [1, 0] : [0, 1];                            // along the wall
      let a = e; while (opens.some((o) => o.cx === a.cx - ax[0] && o.cz === a.cz - ax[1] && o.dx === e.dx && o.dz === e.dz)) a = opens.find((o) => o.cx === a.cx - ax[0] && o.cz === a.cz - ax[1] && o.dx === e.dx && o.dz === e.dz);
      const run = []; let b = a; while (b) { run.push(b); used.add(key(b)); const nb = opens.find((o) => o.cx === b.cx + ax[0] && o.cz === b.cz + ax[1] && o.dx === e.dx && o.dz === e.dz); b = nb; }
      const w = run.length, first = run[0], last = run[w - 1];
      const flankA = walls.get((first.cx - ax[0]) + ',' + (first.cz - ax[1]) + ':' + e.dx + ',' + e.dz), flankB = walls.get((last.cx + ax[0]) + ',' + (last.cz + ax[1]) + ':' + e.dx + ',' + e.dz);
      if (w > ARCH_MAX || !flankA || !flankB) continue;
      const mx = (first.x + last.x) / 2, mz = (first.z + last.z) / 2, yaw = yawOf(first.nx, first.nz);
      put('arch', mx, 0, mz, yaw, w, 1, 1); arches.push({ x: mx, z: mz, w });
      for (const [y, s] of rowsY.slice(1)) for (const o of run) put('straight', o.x, y, o.z, yaw, 1, s, 1);   // the wall goes on above the arch
      // the arch's sides are w metres each: take that off the flanking wall edges (and the next ones if w > 2)
      const along = (p) => (p.x * ax[0] + p.z * ax[1]);
      const s0 = along(first) - C / 2 - w, s1 = along(last) + C / 2 + w;
      for (const [o, side] of [[flankA, -1], [flankB, 1]]) {
        let f = o;
        for (let k = 0; k < 2 && f; k++) {
          const c0 = along(f) - C / 2, c1 = along(f) + C / 2;
          const keep = side < 0 ? [c0, Math.min(c1, s0)] : [Math.max(c0, s1), c1];
          const prev = cut.get(key(f)) || [c0, c1];
          cut.set(key(f), [Math.max(prev[0], keep[0]), Math.min(prev[1], keep[1])].map((v) => v - along(f)));
          f = walls.get((f.cx + side * ax[0]) + ',' + (f.cz + side * ax[1]) + ':' + e.dx + ',' + e.dz);
        }
      }
    }
    // inner corners: one corner piece covers this edge and the edge on its left (the arm's room face is the piece's +X)
    const dropped = new Set(), corners = new Set();
    for (const [k, e] of walls) {
      if (dropped.has(k) || cut.has(k)) continue;
      const yaw = yawOf(e.nx, e.nz), lx = Math.round(Math.cos(yaw)), lz = Math.round(-Math.sin(yaw));
      const k2 = e.cx + ',' + e.cz + ':' + (-lx) + ',' + (-lz);
      if (walls.has(k2) && !dropped.has(k2) && !corners.has(k2) && !cut.has(k2)) { corners.add(k); dropped.add(k2); }
    }
    // the room's sconces become kit sconces, origin on the wall at 2.57 m so the `flame` empty (0.28 out, 0.28 up) sits on the torch light
    const lit = new Set();
    for (const t of map.torches || []) {
      if (t.kind !== 'sconce') continue;
      const cx = Math.floor(t.x / C), cz = Math.floor(t.z / C), k = cx + ',' + cz + ':' + (-t.nx) + ',' + (-t.nz);
      if (!walls.has(k) || dropped.has(k) || (cut.has(k) && cut.get(k)[1] - cut.get(k)[0] < C - 1e-6)) continue;
      skip.torch.add(t); lit.add(k);
      put('sconce', t.x - t.nx * 0.28, t.y - 0.28, t.z - t.nz * 0.28, yawOf(t.nx, t.nz));
    }
    let n = 0;
    for (const [k, e] of walls) {
      if (dropped.has(k)) continue;
      const yaw = yawOf(e.nx, e.nz);
      if (corners.has(k)) { stack('corner', e.x, e.z, yaw); continue; }
      const c = cut.get(k);
      if (c) {                                                            // beside an arch: only the uncovered part in the bottom row
        const len = c[1] - c[0]; if (len > 0.01) { const mid = (c[0] + c[1]) / 2, ax = e.dz !== 0 ? [1, 0] : [0, 1]; put('straight', e.x + ax[0] * mid, 0, e.z + ax[1] * mid, yaw, len / C, 1, 1); }
        for (const [y, s] of rowsY.slice(1)) put('straight', e.x, y, e.z, yaw, 1, s, 1);
        continue;
      }
      stack('straight', e.x, e.z, yaw);
      if (!lit.has(k) && (n++ % 3) === 1) put('banner', e.x, Math.min(H - 1.5, 7.2), e.z, yaw);   // a banner on every third plain wall
    }
    return { room: R, place, skip, arches, count: place.reduce((a, p) => { a[p.piece] = (a[p.piece] || 0) + 1; return a; }, {}) };
  }

  function decode(b64) {
    if (typeof Buffer !== 'undefined' && typeof atob === 'undefined') { const b = Buffer.from(b64, 'base64'); return b.buffer.slice(b.byteOffset, b.byteOffset + b.length); }
    const s = atob(b64), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u.buffer;
  }
  // one merged mesh for every placed piece; light(x, y, z, nx, ny, nz) -> [r, g, b] is the baked world's torch light
  function build(THREE, kit, P, light) {
    const pos = [], nor = [], uv = [], col = [], idx = [];
    const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), S = new THREE.Vector3(), T = new THREE.Vector3(), N3 = new THREE.Matrix3(), v = new THREE.Vector3(), n = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0);
    let tris = 0;
    for (const p of P.place) {
      const g = kit.pieces[p.piece]; if (!g) continue;
      M.compose(T.set(p.x, p.y, p.z), Q.setFromAxisAngle(Y, p.yaw), S.set(p.sx, p.sy, p.sz)); N3.getNormalMatrix(M);
      const gp = g.attributes.position, gn = g.attributes.normal, gu = g.attributes.uv, base = pos.length / 3;
      for (let i = 0; i < gp.count; i++) {
        v.fromBufferAttribute(gp, i).applyMatrix4(M); n.fromBufferAttribute(gn, i).applyMatrix3(N3).normalize();
        pos.push(v.x, v.y, v.z); nor.push(n.x, n.y, n.z); uv.push(gu.getX(i), gu.getY(i));
        const l = light(v.x + n.x * 0.05, v.y, v.z + n.z * 0.05, Math.round(n.x * 2) / 2, Math.round(n.y * 2) / 2, Math.round(n.z * 2) / 2); col.push(l[0], l[1], l[2]);
      }
      const gi = g.index; for (let i = 0; i < gi.count; i++) idx.push(base + gi.getX(i)); tris += gi.count / 3;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    geo.setIndex(pos.length / 3 > 65535 ? new THREE.Uint32BufferAttribute(idx, 1) : new THREE.Uint16BufferAttribute(idx, 1)); geo.computeBoundingSphere();
    const mesh = new THREE.Mesh(geo, kit.mat); mesh.name = 'crimson_halls'; mesh.userData.tris = tris; mesh.userData.pieces = P.count;
    return mesh;
  }

  // one per page: decodes the kit once (base64 GLBs from GlbData), then hands world_view.js a plan and a builder for each new floor
  function create(THREE, o) {
    o = o || {};
    const data = o.data || (typeof GlbData !== 'undefined' ? GlbData : null);
    const spec = data && data.manifest && data.manifest.env && data.manifest.env.crimson_halls;
    const off = /[?&#]voxelwalls\b/.test(o.query || '') || !(o.sandbox === undefined ? /sandbox/.test(o.query || '') : o.sandbox);
    let kit = null, failed = null, started = false;
    const fail = (e) => { failed = String((e && e.message) || e); kit = null; console.warn('Crimson Halls kit could not load, using the old walls: ' + failed); };
    function start(onReady) {
      if (started) return; started = true;
      if (off || !spec) { if (/[?&#]voxelwalls\b/.test(o.query || '')) console.warn('Crimson Halls off (?voxelwalls): using the old walls'); return; }
      if (!THREE.GLTFLoader) { fail('no GLTFLoader in this page'); return; }
      const names = Object.keys(spec.pieces), got = {}; let left = names.length, map = null;
      for (const id of names) {
        const file = spec.dir + spec.pieces[id], b64 = data.files && data.files[file];
        if (!b64) { fail('no embedded file ' + file); return; }
        try {
          new THREE.GLTFLoader().parse(decode(b64), '', (gltf) => {
            if (failed) return;
            try {
              gltf.scene.updateMatrixWorld(true); let mesh = null; gltf.scene.traverse((m) => { if (!mesh && m.isMesh) mesh = m; });
              if (!mesh) throw new Error(file + ' has no mesh');
              const g = mesh.geometry.clone(); g.applyMatrix4(mesh.matrixWorld); if (!g.index) g.setIndex([...Array(g.attributes.position.count).keys()]);
              got[id] = g; if (!map && mesh.material.map) map = mesh.material.map;
              if (--left === 0) {
                if (map) { map.magFilter = THREE.NearestFilter; map.minFilter = THREE.NearestFilter; map.generateMipmaps = false; map.encoding = THREE.LinearEncoding; map.needsUpdate = true; }
                kit = { pieces: got, mat: new THREE.MeshBasicMaterial({ map: map || null, vertexColors: true, fog: true }) };
                if (onReady) onReady();
              }
            } catch (e) { fail(e); }
          }, (e) => fail(e));
        } catch (e) { fail(e); }
      }
    }
    // what world_view.load needs for this map: the plan (what to leave out of the bake) and a builder that takes the baked light
    function forMap(map) {
      if (!kit) return null;
      try { const P = plan(map); if (!P) return null; return { skip: P.skip, plan: P, build: (light) => build(THREE, kit, P, light), mat: kit.mat }; } catch (e) { fail(e); return null; }
    }
    return { start, forMap, ready: () => !!kit, status: () => ({ ready: !!kit, failed, off, pieces: kit ? Object.keys(kit.pieces) : [] }) };
  }
  return { create, plan, build, ROW_H };
})();
if (typeof module !== 'undefined') module.exports = CrimsonHalls;
