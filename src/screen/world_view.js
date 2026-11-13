/* World view: draws the current floor. The floor is baked into chunks of quads (world_bake.js) and only the chunks near you are drawn;
   the torches are a small pool of flame props that follow the nearest torches; the locked door is its own object that lifts when it opens.
   Presentation only: where things are comes from the referee's map. A new floor is built with load(map). */
const WorldView = (function () {
  const SCONCES = 22, BRAZIERS = 6;                                    // how many torch props are drawn at once (the nearest ones)
  function create(THREE, scene, T, glowTex) {
    const TEX = { stone: T.texStone, cloth: T.texCloth, panel: T.texPanel, pillar: T.texPillar, gold: T.texGold, floor: T.texFloor, floor2: T.texFloor2, floor3: T.texFloor3, floorEdge: T.texFloorEdge, carpet: T.texCarpet, ceil: T.texCeil };
    const mats = {}; for (const k in TEX) mats[k] = new THREE.MeshBasicMaterial({ map: TEX[k], vertexColors: true, fog: true });
    const worldMats = Object.values(mats);
    const flameOuter = new THREE.MeshBasicMaterial({ color: 0xff8a26, fog: false });
    const flameInner = new THREE.MeshBasicMaterial({ color: 0xffdc7a, fog: false });
    const ironMat = new THREE.MeshLambertMaterial({ map: T.texDark, emissive: 0x201410 });
    const goldLit = new THREE.MeshLambertMaterial({ map: T.texGold, emissive: 0x3a2a0a });
    const doorGlow = new THREE.MeshBasicMaterial({ color: 0x8a0f14, fog: false });
    const geoCache = {};
    function box(w, h, d, mat, x, y, z, parent) {
      const k = w + '_' + h + '_' + d;
      const geo = geoCache[k] || (geoCache[k] = new THREE.BoxGeometry(w, h, d));
      const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); parent.add(m); return m;
    }

    // the torch pool: a sconce is a bracket, a gold cup and a flame; a brazier a stand, a bowl and a bigger flame
    function makeTorch(big) {
      const grp = new THREE.Group(); scene.add(grp); grp.visible = false;
      const parts = [];
      if (big) { parts.push(box(0.55, 1.2, 0.55, ironMat, 0, 0.6 - 1.75, 0, grp), box(0.85, 0.16, 0.85, goldLit, 0, 1.2 - 1.75, 0, grp), box(0.7, 0.3, 0.7, ironMat, 0, 1.38 - 1.75, 0, grp)); }
      else { parts.push(box(0.2, 0.5, 0.2, ironMat, 0, -0.38, 0, grp), box(0.34, 0.1, 0.34, goldLit, 0, -0.14, 0, grp), box(0.12, 0.12, 0.12, ironMat, 0, -0.5, 0, grp)); }
      const s = big ? 1.6 : 1;
      const outer = box(0.2 * s, 0.34 * s, 0.2 * s, flameOuter, 0, 0.1 * s, 0, grp), inner = box(0.11 * s, 0.22 * s, 0.11 * s, flameInner, 0, 0.06 * s, 0, grp);
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, transparent: true }));
      sp.scale.setScalar(big ? 3.2 : 2.1); sp.position.set(0, 0.15, 0); grp.add(sp);
      return { grp, parts, outer, inner, sp, base: big ? 3.2 : 2.1, ph: Math.random() * 10, big };
    }
    const sconcePool = [], brazierPool = [];
    for (let i = 0; i < SCONCES; i++) sconcePool.push(makeTorch(false));
    for (let i = 0; i < BRAZIERS; i++) brazierPool.push(makeTorch(true));

    // VR (Quest) draw-call saver: the same torch props drawn as one instanced mesh per part (12 draws for every torch in view instead of 6 per torch).
    // The pool above still works out where every part goes; in VR each part's place is copied into its instanced mesh and the pooled meshes are hidden.
    // The glow sprite becomes a camera-facing quad with the same additive glow (its opacity flicker rides the instance colour: with additive blending that is the same thing).
    const glowQuad = new THREE.PlaneGeometry(1, 1);
    function makeInst(pool) {
      const t = pool[0], list = [];
      for (const m of [...t.parts, t.outer, t.inner]) { const im = new THREE.InstancedMesh(m.geometry, m.material, pool.length); im.frustumCulled = false; im.count = 0; im.visible = false; im.instanceMatrix.setUsage(THREE.DynamicDrawUsage); scene.add(im); list.push({ im }); }
      const gm = new THREE.MeshBasicMaterial({ map: glowTex, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, transparent: true, side: THREE.DoubleSide });
      const glow = new THREE.InstancedMesh(glowQuad, gm, pool.length); glow.frustumCulled = false; glow.count = 0; glow.visible = false; glow.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      glow.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(pool.length * 3).fill(1), 3); glow.instanceColor.setUsage(THREE.DynamicDrawUsage); scene.add(glow);   // made by hand: setColorAt would size it by count (0 here)
      return { parts: list.map((e) => e.im), glow };
    }
    const instS = makeInst(sconcePool), instB = makeInst(brazierPool);
    let instOn = false;
    const tmpM = new THREE.Matrix4(), tmpQ = new THREE.Quaternion(), tmpP = new THREE.Vector3(), tmpS = new THREE.Vector3(), tmpC = new THREE.Color(), lookM = new THREE.Matrix4(), UP = new THREE.Vector3(0, 1, 0);
    function setInstanced(on) {
      if (on === instOn) return; instOn = on;
      for (const I of [instS, instB]) { for (const im of I.parts) im.visible = on; I.glow.visible = on; }
      for (const pool of [sconcePool, brazierPool]) for (const o of pool) for (const m of [...o.parts, o.outer, o.inner, o.sp]) m.visible = !on;
    }
    function fillInst(pool, I, eye) {
      let n = 0;
      for (const o of pool) {
        if (!o.grp.visible) continue;
        o.grp.updateMatrixWorld(true);
        const meshes = [...o.parts, o.outer, o.inner];
        for (let j = 0; j < meshes.length; j++) I.parts[j].setMatrixAt(n, meshes[j].matrixWorld);
        o.sp.getWorldPosition(tmpP);                                   // the glow quad faces your eye
        lookM.lookAt(eye, tmpP, UP); tmpQ.setFromRotationMatrix(lookM); tmpS.set(o.sp.scale.x, o.sp.scale.y, 1);
        tmpM.compose(tmpP, tmpQ, tmpS); I.glow.setMatrixAt(n, tmpM);
        const a = o.sp.material.opacity; I.glow.setColorAt(n, tmpC.setRGB(a, a, a));
        n++;
      }
      for (const im of I.parts) { im.count = n; im.instanceMatrix.needsUpdate = true; }
      I.glow.count = n; I.glow.instanceMatrix.needsUpdate = true; if (I.glow.instanceColor) I.glow.instanceColor.needsUpdate = true;
    }

    let kitMesh = null, chunkMeshes = [], bigMeshes = [], bigExtra = 0, torches = [], baked = null, door = null, doorT = 0, doorTarget = 0, doorOpenNow = false, fogFar = 34;
    function dropWorld() {
      for (const c of chunkMeshes) { scene.remove(c.mesh); c.mesh.geometry.dispose(); }
      chunkMeshes = [];
      for (const c of bigMeshes) { scene.remove(c.mesh); c.mesh.geometry.dispose(); }
      bigMeshes = [];
      if (kitMesh) { scene.remove(kitMesh); for (const m of kitMesh.children) m.geometry.dispose(); kitMesh = null; }
      if (door) { scene.remove(door.grp); door = null; }
    }

    function buildDoor(map) {
      const d = map.door, grp = new THREE.Group();
      const alongX = d.nz !== 0;                                       // the door faces up/down the map when its normal runs along z
      const w = map.CELL * 2, h = map.WALL_H, th = 0.5;
      const inner = new THREE.Group(); grp.add(inner);                 // the slab, which lifts
      const add = (mat, bw, bh, bd, x, y, z, p) => box(alongX ? bw : bd, bh, alongX ? bd : bw, mat, alongX ? x : z, y, alongX ? z : x, p || inner);
      add(ironMat, w, h, th, 0, h / 2, 0);                                           // iron slab
      add(goldLit, w + 0.3, 0.35, th + 0.2, 0, h - 0.18, 0);                          // lintel
      add(goldLit, 0.3, h, th + 0.2, -w / 2 + 0.15, h / 2, 0); add(goldLit, 0.3, h, th + 0.2, w / 2 - 0.15, h / 2, 0);   // posts
      add(doorGlow, 0.5, h * 0.7, th + 0.06, 0, h * 0.45, 0);                         // a crimson seam down the middle
      add(goldLit, 1.1, 1.1, th + 0.12, 0, h * 0.55, 0);                              // a gold boss plate
      const lamp = new THREE.PointLight(0xff3a20, 1.2, 14, 2); lamp.position.set(0, 2.6, 0); grp.add(lamp);
      grp.position.set(d.x, 0, d.z);
      scene.add(grp);
      return { grp, inner, lamp, h };
    }

    // build a new floor: bake it, make the chunk meshes, file the torches, stand the door in place.
    // kit (optional, crimson_halls.js forMap): a mesh wall kit drawn over part of the floor; its quads and pooled torches are left out of the bake
    function load(map, far, kit) {
      dropWorld();
      fogFar = far || fogFar;
      baked = WorldBake.bake(map, kit ? kit.skip : null);
      if (kit) { try { kitMesh = kit.build(baked.light); scene.add(kitMesh); } catch (e) { console.warn('Crimson Halls mesh failed, old walls: ' + e.message); kitMesh = null; baked = WorldBake.bake(map); kit = null; } }
      for (const c of baked.chunks) {
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(c.pos, 3));
        geo.setAttribute('uv', new THREE.Float32BufferAttribute(c.uv, 2));
        geo.setAttribute('color', new THREE.Float32BufferAttribute(c.col, 3));
        const mesh = new THREE.Mesh(geo, mats[c.key]); scene.add(mesh);
        chunkMeshes.push({ mesh, x: (c.cx * 12 + 6) * map.CELL, z: (c.cz * 12 + 6) * map.CELL });
      }
      // VR: the same quads merged 2 x 2 chunks at a time (a quarter of the draws; the fog hides the extra reach). Built now, shown only in the headset.
      const big = {};
      for (const c of baked.chunks) { const id = c.key + '@' + (c.cx >> 1) + ',' + (c.cz >> 1); const b = big[id] || (big[id] = { key: c.key, bx: c.cx >> 1, bz: c.cz >> 1, pos: [], uv: [], col: [] }); for (const a of ['pos', 'uv', 'col']) { const src = c[a], dst = b[a]; for (let i = 0; i < src.length; i++) dst.push(src[i]); } }
      for (const id in big) {
        const b = big[id], geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(b.pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(b.uv, 2)); geo.setAttribute('color', new THREE.Float32BufferAttribute(b.col, 3));
        const mesh = new THREE.Mesh(geo, mats[b.key]); mesh.visible = false; scene.add(mesh);
        bigMeshes.push({ mesh, x: (b.bx * 24 + 12) * map.CELL, z: (b.bz * 24 + 12) * map.CELL });
      }
      bigExtra = 6 * map.CELL * Math.SQRT2;
      torches = kit ? map.torches.filter((t) => !kit.skip.torch.has(t)) : map.torches;
      door = buildDoor(map); doorT = 0; doorTarget = 0; doorOpenNow = false;
    }

    // every frame: chunks and torches near the camera, flame flicker, the door's lift
    const near = [];
    function update(time, cam, dt, br, fb, doorOpen, inst, eye) {
      setInstanced(!!inst);
      const reach = fogFar + 18;
      for (const c of chunkMeshes) c.mesh.visible = !instOn && Math.hypot(c.x - cam.x, c.z - cam.z) < reach;
      for (const c of bigMeshes) c.mesh.visible = instOn && Math.hypot(c.x - cam.x, c.z - cam.z) < reach + bigExtra;
      for (const m of worldMats) m.color.setRGB(br * (1 + 0.5 * fb), br * (1 + 0.28 * fb), br * (1 + 0.1 * fb));
      if (kitMesh) {                                                    // the wall kit: one shared material, blocks beyond the fog are skipped
        const kb = kitMesh.children; if (kb.length) kb[0].material.color.setRGB(br * (1 + 0.5 * fb), br * (1 + 0.28 * fb), br * (1 + 0.1 * fb));
        for (const m of kb) { const g = m.geometry; if (!g.boundingBox) g.computeBoundingBox(); const b = g.boundingBox, dx = Math.max(b.min.x - cam.x, 0, cam.x - b.max.x), dz = Math.max(b.min.z - cam.z, 0, cam.z - b.max.z); m.visible = dx * dx + dz * dz < reach * reach; }   // nearest point of the block's square inside the fog
      }
      // the nearest torches of each kind get the pooled props
      for (const kind of ['sconce', 'brazier']) {
        const pool = kind === 'brazier' ? brazierPool : sconcePool; near.length = 0;
        for (const t of torches) { if (t.kind !== kind) continue; const d2 = (t.x - cam.x) * (t.x - cam.x) + (t.z - cam.z) * (t.z - cam.z); if (d2 < reach * reach) near.push([d2, t]); }
        near.sort((a, b) => a[0] - b[0]);
        for (let i = 0; i < pool.length; i++) {
          const o = pool[i], e = near[i];
          if (!e) { o.grp.visible = false; continue; }
          const t = e[1]; o.grp.visible = true; o.grp.position.set(t.x, t.y, t.z);
          if (!o.big) { o.parts[0].position.set(-t.nx * 0.12, -0.38, -t.nz * 0.12); o.parts[2].position.set(-t.nx * 0.22, -0.5, -t.nz * 0.22); }
          const q = 0.85 + 0.25 * Math.sin(time * 14 + o.ph) + 0.12 * Math.sin(time * 29 + o.ph * 2);
          o.outer.scale.set(1, q, 1); o.inner.scale.set(1, q * 1.1, 1);
          o.sp.scale.setScalar(o.base * (0.92 + 0.1 * q)); o.sp.material.opacity = 0.75 + 0.2 * Math.sin(time * 11 + o.ph);
        }
      }
      if (instOn) { fillInst(sconcePool, instS, eye || cam); fillInst(brazierPool, instB, eye || cam); }
      // the door: shut, or lifting out of the way
      if (door) {
        doorTarget = doorOpen ? 1 : 0; doorT += Math.sign(doorTarget - doorT) * Math.min(Math.abs(doorTarget - doorT), dt * 0.8);
        door.inner.position.y = doorT * (door.h + 0.2);
        door.lamp.intensity = doorOpen ? 0 : 1.1 + 0.25 * Math.sin(time * 3);
      }
    }
    return { load, update, light: (x, y, z, nx, ny, nz) => baked.light(x, y, z, nx, ny, nz), setFogFar: (v) => { fogFar = v; }, instanced: () => instOn, kit: () => kitMesh, setFlame: (outer, inner) => { flameOuter.color.setHex(outer); flameInner.color.setHex(inner); }, mats: worldMats };
  }
  return { create };
})();
