/* Crimson Halls wall kit (Wrok's low-poly GLB pieces, assets/models/env/crimson_halls/) dressing every floor of the game.
   plan(map) is pure: walls on every open/solid cell edge, 3 modules high to the 11.5 m roof (top row squashed to 0.875), a corner piece in each
   inner corner, free-standing pillar cells as kit pillars scaled to the 2 m cell, floor tiles, banners on banner walls, a kit sconce on every wall
   torch (its `flame` on the torch light at 2.85 m), and which baked faces, floors, cells and pooled torch props to leave out. Openings stay open to
   the roof, as the referee has them. The referee's cells are still the collision: only the look changes. build() merges the pieces into one mesh
   per 12 x 12 cell block (one material, one 256 px atlas), lit like the baked world (torch light per vertex, MeshBasic + vertex colours).
   Until the GLBs decode, if they fail, or with ?voxelwalls, the old walls stay. */
const CrimsonHalls = (function () {
  const ROW_H = 4, ARCH_MAX = 3;                                          // module height (m); widest opening (cells) that gets an arch
  const open = (c) => c === '.' || c === 'c';
  const solidCh = (c) => !(c === '.' || c === 'c' || c === 'D' || c === 'd');
  const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  const yawOf = (nx, nz) => Math.atan2(nx, nz);                           // turns a piece's +Z (its room side) toward (nx, nz)

  // plan(map): every hall of the floor. Walls go on every edge between an open cell and a solid one; nothing is drawn across an opening
  // (the referee treats a doorway as open all the way to the 11.5 m roof, so a wall or arch above it would hide shots that really pass).
  const TRIM_Z = 0.35;                                                    // the kit's brick trim stands 0.16 m proud of the wall; squashed to ~5 cm so a gun held at a wall does not sink into it
  function plan(map) {
    const C = map.CELL, H = map.WALL_H, rows = map.rows;
    const at = (cx, cz) => (cz < 0 || cz >= map.H || cx < 0 || cx >= map.W) ? '#' : rows[cz][cx];
    const rowsY = []; for (let y = 0; y < H - 1e-6; y += ROW_H) rowsY.push([y, Math.min(1, (H - y) / ROW_H)]);   // [bottom, y scale]: 0, 4, 8 (x0.875)
    const place = [], skip = { face: new Set(), floor: new Set(), cell: new Set(), torch: new Set() };
    const put = (piece, x, y, z, yaw, sx, sy, sz) => place.push({ piece, x, y, z, yaw, sx: sx || 1, sy: sy || 1, sz: sz || 1 });
    const stack = (piece, x, z, yaw, sx, sz) => { for (const [y, s] of rowsY) put(piece, x, y, z, yaw, sx, s, sz); };
    // free-standing pillar cells (open all round): a kit pillar the size of the cell (collision is the whole 2 m cell)
    const pillarCell = (cx, cz) => at(cx, cz) === 'P' && DIRS.every(([dx, dz]) => open(at(cx + dx, cz + dz)));
    const walls = new Map();
    for (let cz = 0; cz < map.H; cz++) for (let cx = 0; cx < map.W; cx++) {
      if (pillarCell(cx, cz)) { skip.cell.add(cx + ',' + cz); stack('pillar', (cx + 0.5) * C, (cz + 0.5) * C, 0, C / 0.8, C / 0.8); continue; }
      if (!open(at(cx, cz))) continue;
      if (at(cx, cz) === '.') { skip.floor.add(cx + ',' + cz); put('floor', (cx + 0.5) * C, 0, (cz + 0.5) * C, 0); }
      for (const [dx, dz] of DIRS) {
        const ncx = cx + dx, ncz = cz + dz, ch = at(ncx, ncz);
        if (!solidCh(ch) || pillarCell(ncx, ncz)) continue;
        walls.set(cx + ',' + cz + ':' + dx + ',' + dz, { cx, cz, dx, dz, nx: -dx, nz: -dz, x: (cx + 0.5 + dx / 2) * C, z: (cz + 0.5 + dz / 2) * C, banner: ch === 'B' });
        skip.face.add(ncx + ',' + ncz + ':' + (-dx) + ',' + (-dz));
      }
    }
    // inner corners: one corner piece covers this edge and the edge on its left (the arm's room face is the piece's +X)
    const dropped = new Set(), corners = new Set();
    for (const [k, e] of walls) {
      if (dropped.has(k) || corners.has(k)) continue;
      const yaw = yawOf(e.nx, e.nz), lx = Math.round(Math.cos(yaw)), lz = Math.round(-Math.sin(yaw));
      const k2 = e.cx + ',' + e.cz + ':' + (-lx) + ',' + (-lz);
      if (walls.has(k2) && !dropped.has(k2) && !corners.has(k2)) { corners.add(k); dropped.add(k2); }
    }
    // every wall sconce becomes a kit sconce, origin on the wall at 2.57 m so the `flame` empty (0.28 out, 0.28 up) sits on the torch light
    const lit = new Set();
    for (const t of map.torches || []) {
      if (t.kind !== 'sconce') continue;
      const cx = Math.floor(t.x / C), cz = Math.floor(t.z / C), k = cx + ',' + cz + ':' + (-t.nx) + ',' + (-t.nz);
      if (!walls.has(k)) continue;
      skip.torch.add(t); lit.add(k);
      put('sconce', t.x - t.nx * 0.28, t.y - 0.28, t.z - t.nz * 0.28, yawOf(t.nx, t.nz));
    }
    for (const [k, e] of walls) {
      if (dropped.has(k)) continue;
      const yaw = yawOf(e.nx, e.nz);
      if (corners.has(k)) { for (const [y, s] of rowsY) put('corner', e.x, y, e.z, yaw, 1, s, 1); continue; }
      for (const [y, s] of rowsY) put('straight', e.x, y, e.z, yaw, 1, s, TRIM_Z);
      if (e.banner && !lit.has(k)) put('banner', e.x, Math.min(H - 1.5, 7.2), e.z, yaw);   // banner walls ('B') keep their banner
    }
    return { place, skip, count: place.reduce((a, p) => { a[p.piece] = (a[p.piece] || 0) + 1; return a; }, {}) };
  }

  // drop the triangles nobody can see once the pieces stand in a level (less for the Quest to draw): wall backs and the thick ends inside the
  // solid cell (they would also z-fight the next wall at an outside corner), the caps between stacked rows and under the roof, a floor tile's sides
  function hidden(THREE, id, g) {
    const p = g.attributes.position, I = g.index, keep = [], a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), n = new THREE.Vector3(), e = new THREE.Vector3();
    for (let i = 0; i < I.count; i += 3) {
      a.fromBufferAttribute(p, I.getX(i)); b.fromBufferAttribute(p, I.getX(i + 1)); c.fromBufferAttribute(p, I.getX(i + 2));
      n.subVectors(b, a).cross(e.subVectors(c, a)).normalize(); const cy = (a.y + b.y + c.y) / 3, cz = (a.z + b.z + c.z) / 3;
      let drop = false;
      if (id === 'floor') drop = n.y < 0.5;
      else if (id === 'straight' || id === 'corner') drop = n.z < -0.5 || (n.y > 0.5 && cy > ROW_H - 0.02) || (Math.abs(n.x) > 0.5 && cz < -0.01 && (id === 'straight' || cz > -0.6));
      else if (id === 'pillar') drop = Math.abs(n.y) > 0.5 && (cy > ROW_H - 0.02 || cy < 0.02);
      if (!drop) keep.push(I.getX(i), I.getX(i + 1), I.getX(i + 2));
    }
    g.setIndex(keep); return g;
  }
  function decode(b64) {
    if (typeof Buffer !== 'undefined' && typeof atob === 'undefined') { const b = Buffer.from(b64, 'base64'); return b.buffer.slice(b.byteOffset, b.byteOffset + b.length); }
    const s = atob(b64), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u.buffer;
  }
  // the kit's bright red brick under the baked torch light (up to ~1.6) blew out to flat orange beside a torch: a soft shoulder keeps the
  // dark halls as they were and rolls the hot spots off (1.6 -> ~1.0)
  const tone = (c) => 1.25 * c / (1 + 0.6 * c);
  // every placed piece merged into one mesh per 12 x 12 cell block (the same blocks the VR world uses): one material, a handful of draws,
  // and blocks out of reach are skipped. light(x, y, z, nx, ny, nz) -> [r, g, b] is the baked world's torch light
  const BLOCK = 12;                                                  // 24 m squares: the fog and the view cone skip most of them (fewer triangles on Quest)
  function build(THREE, kit, P, light, cell) {
    const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), S = new THREE.Vector3(), T = new THREE.Vector3(), N3 = new THREE.Matrix3(), v = new THREE.Vector3(), n = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0);
    const blocks = {}, span = BLOCK * (cell || 2);
    for (const p of P.place) { const id = Math.floor(p.x / span) + ',' + Math.floor(p.z / span); (blocks[id] || (blocks[id] = [])).push(p); }
    const group = new THREE.Group(); group.name = 'crimson_halls'; let tris = 0;
    for (const id in blocks) {
      const pos = [], uv = [], col = [], idx = [];
      for (const p of blocks[id]) {
        const g = kit.pieces[p.piece]; if (!g) continue;
        M.compose(T.set(p.x, p.y, p.z), Q.setFromAxisAngle(Y, p.yaw), S.set(p.sx, p.sy, p.sz)); N3.getNormalMatrix(M);
        const gp = g.attributes.position, gn = g.attributes.normal, gu = g.attributes.uv, base = pos.length / 3;
        for (let i = 0; i < gp.count; i++) {
          v.fromBufferAttribute(gp, i).applyMatrix4(M); n.fromBufferAttribute(gn, i).applyMatrix3(N3).normalize();
          pos.push(v.x, v.y, v.z); uv.push(gu.getX(i), gu.getY(i));
          const l = light(v.x + n.x * 0.05, v.y, v.z + n.z * 0.05, Math.round(n.x * 2) / 2, Math.round(n.y * 2) / 2, Math.round(n.z * 2) / 2); col.push(tone(l[0]), tone(l[1]), tone(l[2]));
        }
        const gi = g.index; for (let i = 0; i < gi.count; i++) idx.push(base + gi.getX(i)); tris += gi.count / 3;
      }
      if (!idx.length) continue;
      const geo = new THREE.BufferGeometry();       // no normals kept: the material is unlit (light is in the vertex colours), so the GPU reads less
      geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
      geo.setIndex(pos.length / 3 > 65535 ? new THREE.Uint32BufferAttribute(idx, 1) : new THREE.Uint16BufferAttribute(idx, 1)); geo.computeBoundingSphere();
      const mesh = new THREE.Mesh(geo, kit.mat); mesh.name = 'crimson_halls_block'; mesh.userData.block = id; group.add(mesh);
    }
    group.userData.tris = tris; group.userData.pieces = P.count; group.userData.blocks = group.children.length;
    return group;
  }

  // one per page: decodes the kit once (base64 GLBs from GlbData), then hands world_view.js a plan and a builder for each new floor
  function create(THREE, o) {
    o = o || {};
    const data = o.data || (typeof GlbData !== 'undefined' ? GlbData : null);
    const spec = data && data.manifest && data.manifest.env && data.manifest.env.crimson_halls;
    const off = /[?&#]voxelwalls\b/.test(o.query || '');
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
              got[id] = hidden(THREE, id, g); if (!map && mesh.material.map) map = mesh.material.map;
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
      try { const P = plan(map); if (!P) return null; return { skip: P.skip, plan: P, build: (light) => build(THREE, kit, P, light, map.CELL), mat: kit.mat }; } catch (e) { fail(e); return null; }
    }
    return { start, forMap, ready: () => !!kit, status: () => ({ ready: !!kit, failed, off, pieces: kit ? Object.keys(kit.pieces) : [] }) };
  }
  return { create, plan, build, tone, ROW_H, TRIM_Z };
})();
if (typeof module !== 'undefined') module.exports = CrimsonHalls;
