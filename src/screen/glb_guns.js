/* GLB guns: low-poly mesh guns (Blender exports, listed in assets/models/manifest.json) shown in place of a voxel gun.
   tools/build.js embeds the manifest and each GLB as base64 (GlbData), so the one-file page needs no fetch. The GLB is decoded once with
   three's GLTFLoader (src/vendor/gltf_loader_r128.js); until it is ready, or if it fails, or with ?voxelguns in the link, the voxel gun stays.
   build() hands screen.js the same parts the voxel guns give: a body, a magazine that reloads drop and insert, a moving part (the slide)
   and the anchors in gun units (muzzle, red dot, magazine pivot, slide rest, both hands), with the right hand on the same grip spot as every voxel gun.
   Look-only: no rules, no numbers the referee needs. */
const GlbGuns = (function () {
  const GRIP_TARGET = [0, -21 * 0.0065, 16 * 0.0065];   // where the right hand holds every gun (GunKit.GRIP_TARGET in gun units)

  function decode(b64) {
    if (typeof Buffer !== 'undefined' && typeof atob === 'undefined') { const b = Buffer.from(b64, 'base64'); return b.buffer.slice(b.byteOffset, b.byteOffset + b.length); }
    const s = atob(b64), u = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
    return u.buffer;
  }
  // the game's look for a textured low-poly gun: nearest-filter pixels, lit by the torches like the voxel guns (Phong), with a little of the
  // texture glowing by itself so it never goes black in a dark hall
  function lookMat(THREE, map) {
    if (map) { map.magFilter = THREE.NearestFilter; map.minFilter = THREE.NearestFilter; map.generateMipmaps = false; map.encoding = THREE.LinearEncoding; map.needsUpdate = true; }
    return new THREE.MeshPhongMaterial({ color: 0xffffff, map: map || null, emissive: 0x303030, emissiveMap: map || null, specular: 0x2a2828, shininess: 24, side: THREE.DoubleSide });
  }
  // polished steel (a GLB material with metalness >= 0.5, e.g. Wrok's blued 1911 base: metallic 1, roughness 0.3): a metal needs something to
  // reflect, or it reads black. A tiny warm torch-hall gradient turned into a PMREM once (envFrom) gives it its sheen; a little self-light keeps it readable.
  function steelMat(THREE, src, map) {
    return new THREE.MeshStandardMaterial({ color: 0xffffff, map: map || null, metalness: Math.min(1, src.metalness), roughness: Math.max(0.22, src.roughness), envMapIntensity: 1.25, emissive: 0x161618, emissiveMap: map || null, side: THREE.DoubleSide });
  }
  function envFrom(THREE, renderer) {
    const c = document.createElement('canvas'); c.width = 64; c.height = 32; const x = c.getContext('2d');
    const g = x.createLinearGradient(0, 0, 0, 32);                       // top to bottom: dark vault, warm torch band, bright streak, red-brown floor
    g.addColorStop(0, '#141016'); g.addColorStop(0.32, '#3a2620'); g.addColorStop(0.44, '#d8945a'); g.addColorStop(0.5, '#fff0d8'); g.addColorStop(0.56, '#c06a3a'); g.addColorStop(0.7, '#3a1a16'); g.addColorStop(1, '#100a0a');
    x.fillStyle = g; x.fillRect(0, 0, 64, 32);
    x.fillStyle = 'rgba(255,190,120,0.9)'; for (const px of [8, 30, 52]) x.fillRect(px, 9, 3, 6);   // three torch flames round the room
    const t = new THREE.CanvasTexture(c); t.mapping = THREE.EquirectangularReflectionMapping;
    const pm = new THREE.PMREMGenerator(renderer), env = pm.fromEquirectangular(t).texture; pm.dispose(); t.dispose();
    return env;
  }
  function firstMap(scene) { let m = null; scene.traverse((o) => { if (!m && o.isMesh && o.material && o.material.map) m = o.material.map; }); return m; }

  // take node n out of the model and keep its place, relative to the point pivot (model units)
  function detach(THREE, n, pivot) {
    const M = new THREE.Matrix4().makeTranslation(-pivot.x, -pivot.y, -pivot.z).multiply(n.matrixWorld);
    n.parent.remove(n); M.decompose(n.position, n.quaternion, n.scale); n.updateMatrix();
    return n;
  }
  // a small open red-dot sight on the slide (model metres): base plate, two posts and a top bar round an empty window; returns the dot spot
  function redDot(THREE, parent, r) {
    const mat = r.mat;
    const box = (w, h, d, x, y, z) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); m.name = 'red_dot'; m.frustumCulled = false; parent.add(m); };
    const hw = r.halfW, b = r.base, h = r.height, z = r.z, t = 0.002;
    box(2 * hw + 2 * t, 0.003, 0.02, 0, b + 0.0015, z + 0.009);              // base plate on the slide, running back from the window
    box(t, h - 0.003, t, -hw - t / 2, b + 0.003 + (h - 0.003) / 2, z);       // left and right posts
    box(t, h - 0.003, t, hw + t / 2, b + 0.003 + (h - 0.003) / 2, z);
    box(2 * hw + 2 * t, t, t, 0, b + h - t / 2, z);                          // top bar
    return { dot: new THREE.Vector3(0, b + 0.003 + (h - 0.003 - t) / 2, z), y0: b + 0.003, y1: b + h - t, halfW: hw };
  }

  // the parts of one GLB gun at scale k (gun units per model metre)
  function parts(THREE, scene, spec, k, mat) {
    const src = (spec.root && scene.getObjectByName(spec.root)) || scene;
    const root = src.clone(true);
    root.position.set(0, 0, 0); root.quaternion.set(0, 0, 0, 1); root.scale.set(1, 1, 1); root.updateMatrixWorld(true);
    let tris = 0;
    root.traverse((m) => { if (!m.isMesh) return; m.material = (mat.userData.steel && m.material && m.material.metalness >= 0.5) ? mat.userData.steel : mat; m.frustumCulled = false; const g = m.geometry; tris += (g.index ? g.index.count : g.attributes.position.count) / 3; });
    const V = (a) => new THREE.Vector3(a[0], a[1], a[2]);
    const at = (name) => { const n = name && root.getObjectByName(name); return n ? new THREE.Vector3().setFromMatrixPosition(n.matrixWorld) : null; };
    const grip = V(spec.grip || [0, 0, 0]);
    const off = V(GRIP_TARGET).addScaledVector(grip, -k);
    const P = (v) => [off.x + k * v.x, off.y + k * v.y, off.z + k * v.z];
    const box3 = new THREE.Box3().setFromObject(root);
    // magazine: its own group pivoting at the magazine well (screen.js tilts every magazine 0.1 rad; the inner group takes that back out)
    const magN = root.getObjectByName(spec.magazine || 'magazine');
    if (!magN) throw new Error('GLB gun has no ' + (spec.magazine || 'magazine') + ' node');
    const well = new THREE.Vector3().setFromMatrixPosition(magN.parent.matrixWorld);
    const magBox = new THREE.Box3().setFromObject(magN);
    const mag = new THREE.Group(), magIn = new THREE.Group(); magIn.rotation.x = -0.1; magIn.scale.setScalar(k); mag.add(magIn);
    magIn.add(detach(THREE, magN, well)); mag.position.fromArray(P(well)); mag.name = 'glb_mag';
    // slide: moves back on each shot (and stays back on an empty magazine); pivots at its rear top
    const slideN = root.getObjectByName(spec.slide || 'slide');
    const bolt = new THREE.Group(), boltIn = new THREE.Group(); boltIn.scale.setScalar(k); bolt.add(boltIn); bolt.name = 'glb_slide';
    let rest = new THREE.Vector3(0, well.y, well.z);
    if (slideN) { const sb = new THREE.Box3().setFromObject(slideN); rest = new THREE.Vector3(0, (sb.min.y + sb.max.y) / 2, sb.max.z); boltIn.add(detach(THREE, slideN, rest)); }
    bolt.position.fromArray(P(rest));
    // red dot on top of the slide
    if (!mat.userData.dotMat) mat.userData.dotMat = new THREE.MeshLambertMaterial({ color: 0x1c1c20, emissive: 0x0c0c0e });
    const r = redDot(THREE, root, Object.assign({ base: box3.max.y, z: (box3.min.z + box3.max.z) / 2, halfW: 0.011, height: 0.024 }, spec.redDot || {}, { mat: mat.userData.dotMat }));
    const body = new THREE.Group(); body.name = 'glb_body'; body.position.copy(off); body.scale.setScalar(k); body.add(root);
    const muzzle = at(spec.muzzle || 'muzzle') || new THREE.Vector3(0, r.dot.y - 0.02, box3.min.z);
    const fore = V(spec.fore || [grip.x, grip.y - 0.035, grip.z - 0.018]);
    const anchors = {
      muzzle: P(muzzle), sightDot: P(r.dot), magPivot: P(well), boltRest: P(rest),
      handGrip: P(grip), handFore: P(fore), handMag: P(spec.magHand ? V(spec.magHand) : fore),
      dotWindow: { y0: off.y + k * r.y0, y1: off.y + k * r.y1, halfW: k * r.halfW },
    };
    return {
      name: spec.name || 'GLB gun', glb: true, file: spec.file, k, tris: Math.round(tris),
      groups: { body, mag, bolt }, anchors, hands: { grip: anchors.handGrip, fore: anchors.handFore, mag: anchors.handMag },
      kind: spec.kind || 'pistol', skin: spec.skin, slideTravel: k * (spec.slideTravel || 0),
      size: { length: k * (box3.max.z - box3.min.z), height: k * (box3.max.y - box3.min.y), magDrop: k * (magBox.max.y - magBox.min.y) },
    };
  }

  // one per page: decodes every listed GLB once, then builds fresh parts whenever a gun is put in your hands
  function create(THREE, o) {
    o = o || {};
    const data = o.data || (typeof GlbData !== 'undefined' ? GlbData : null);
    const forced = /[?&#]voxelguns\b/.test(o.query || '');
    const guns = (data && data.manifest && data.manifest.guns) || {};
    const ready = {}, failed = {};
    let started = false;
    const steels = []; let env = null;
    const failOut = (id, e) => { failed[id] = String((e && e.message) || e); delete ready[id]; console.warn('GLB gun ' + id + ' could not load, using the voxel gun: ' + failed[id]); };
    function start(onReady) {
      if (started) return; started = true;
      if (forced) { console.warn('GLB guns off (?voxelguns): using the voxel guns'); return; }
      if (!Object.keys(guns).length) return;
      if (!THREE.GLTFLoader) { console.warn('GLB guns: no GLTFLoader in this page, using the voxel guns'); return; }
      for (const id of Object.keys(guns)) {
        const spec0 = guns[id];
        const tryFile = (file, next) => {
        const spec = Object.assign({}, spec0, file === spec0.file ? {} : (spec0.fallbackSpec || {}), { file }), b64 = data.files && data.files[file];
        const fail = (id, e) => { if (next) { console.warn('GLB gun ' + id + ': ' + file + ' did not load (' + ((e && e.message) || e) + '), trying ' + next); tryFile(next, null); } else failOut(id, e); };
        if (!b64) { fail(id, 'no embedded file ' + file); return; }
        try {
          new THREE.GLTFLoader().parse(decode(b64), '', (gltf) => {
            try {
              const map = firstMap(gltf.scene), r = { scene: gltf.scene, spec, mat: lookMat(THREE, map) };
              let metal = null; gltf.scene.traverse((m) => { if (!metal && m.isMesh && m.material && m.material.metalness >= 0.5) metal = m.material; });
              if (metal) { r.mat.userData.steel = steelMat(THREE, metal, map); if (env) r.mat.userData.steel.envMap = env; steels.push(r.mat.userData.steel); }
              parts(THREE, r.scene, spec, 1, r.mat);              // a dry run: a GLB missing its magazine fails here, not mid-game
              ready[id] = r; if (onReady) onReady(id);
            } catch (e) { fail(id, e); }
          }, (e) => fail(id, e));
        } catch (e) { fail(id, e); }
        };
        tryFile(spec0.file, spec0.fallback || null);                  // the manifest's file, then its fallback (the older 1911), then the voxel gun
      }
    }
    const has = (id) => !forced && !!ready[id];
    const fail = failOut;
    // the steel's reflection: made once from the renderer (screen.js calls this as soon as there is one)
    function setRenderer(renderer) { if (env || !renderer) return; try { env = envFrom(THREE, renderer); for (const m of steels) { m.envMap = env; m.needsUpdate = true; } } catch (e) { console.warn('GLB guns: no steel reflection (' + e.message + ')'); } }
    function build(id, k) { const r = ready[id]; if (!r || forced) return null; try { return parts(THREE, r.scene, r.spec, k, r.mat); } catch (e) { fail(id, e); return null; } }
    // gun units per model metre: true size in a headset (the view scales every gun by gunScale), the voxel gun's size on a flat screen
    const scaleFor = (id, vr, gunScale) => (vr ? 1 / (gunScale || 1) : ((guns[id] && guns[id].flatScale) || 1));
    return { start, has, build, scaleFor, setRenderer, file: (id) => ready[id] && ready[id].spec.file, envReady: () => !!env, ids: Object.keys(guns), status: () => ({ ready: Object.keys(ready), failed: Object.assign({}, failed), forced, loader: !!THREE.GLTFLoader }) };
  }
  return { create, parts, decode, lookMat, GRIP_TARGET };
})();
if (typeof module !== 'undefined') module.exports = GlbGuns;
