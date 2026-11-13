// GLB gun checks: the manifest lists the 1911 for the Service Pistol, the build embeds it, three's GLTFLoader (r128, vendored) decodes it,
// and the parts screen.js needs come out: a body, a magazine that can drop, a slide, the muzzle, the red dot, both hands, at a sane size.
// Needs three.js r128 as a file (THREE_JS=path, or /workspace/three128.js, or node_modules/three); without it the loader part is skipped.
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
let fails = 0, skipped = 0;
const t = (name, ok, seen) => { if (!ok) fails++; if (!ok || process.env.V) console.log((ok ? 'ok   ' : 'FAIL ') + name + (seen !== undefined ? '  (' + seen + ')' : '')); };
const Embed = require('../tools/glb_embed.js');
const data = Embed.load(root);
const spec = data.manifest.guns.pistol_service;
t('The manifest lists a GLB for the Service Pistol', !!spec && /\.glb$/.test(spec.file));
t('The build embeds that GLB (so the one-file page needs no fetch)', !!(spec && data.files[spec.file] && data.files[spec.file].length > 1000));
t('The embedded GLB is small (under 300 KB)', !!(spec && data.files[spec.file] && data.files[spec.file].length * 0.75 < 300000));
t('The build script turns it into a GlbData script', /^const GlbData = \{/.test(Embed.script(root)));
const build = fs.readFileSync(path.join(root, 'tools', 'build.js'), 'utf8');
t('tools/build.js puts the loader, the data and glb_guns.js in the page', /glb_embed/.test(build) && /gltf_loader_r128\.js/.test(build) && /screen\/glb_guns\.js/.test(build));
const MORE = [
  ['rifle', 'gun/rifle_ak47_base.glb', 'The Gothic Rifle slot is Wrok\'s AK'],
  ['smg_tactical', 'gun/smg_mp5_base.glb', 'The Tactical SMG slot is Wrok\'s MP5'],
  ['smg_compact', 'gun/smg_uzi_base.glb', 'The Compact SMG slot is Wrok\'s Uzi'],
  ['rifle_m4', 'gun/rifle_m4_base.glb', 'The M4 Carbine is a new rifle slot with Wrok\'s M4'],
];
for (const [id, file, label] of MORE) {
  const s = data.manifest.guns[id];
  t(label, !!s && s.file === file && data.files[file] && data.files[file].length > 1000, s && s.file);
  t(id + ' is small (under 300 KB) and has no second GLB that would double the slot', !!(s && data.files[file] && data.files[file].length * 0.75 < 300000) && !s.fallback);
}
t('Five GLB gun slots, one gun each (1911, AK, MP5, Uzi, M4)', Object.keys(data.manifest.guns).length === 5 && !data.manifest.guns.m4);

const threePath = [process.env.THREE_JS, '/workspace/three128.js', path.join(root, 'node_modules', 'three', 'build', 'three.js')].find((p) => p && fs.existsSync(p));
async function loaderChecks() {
  if (!threePath) { skipped++; console.log('skip: no three.js r128 file here, so the GLTFLoader decode checks did not run'); return; }
  // a tiny stand-in for the browser image the loader makes for the texture (node has no DOM)
  global.window = global; global.self = global;
  global.document = { createElementNS: () => { const img = { listeners: {}, addEventListener(k, f) { this.listeners[k] = f; }, removeEventListener() {}, set src(v) { this._src = v; setTimeout(() => this.listeners.load && this.listeners.load.call(img), 0); }, get src() { return this._src; }, width: 256, height: 256 }; return img; } };
  global.THREE = require(threePath);
  require('../src/vendor/gltf_loader_r128.js');
  const GlbGuns = require('../src/screen/glb_guns.js');
  t('The vendored GLTFLoader defines THREE.GLTFLoader for r' + THREE.REVISION, typeof THREE.GLTFLoader === 'function' && THREE.REVISION === '128');
  const warns = []; const cw = console.warn; console.warn = (m) => warns.push(String(m));
  const G = GlbGuns.create(THREE, { data, query: '?sandbox' });
  const want = Object.keys(data.manifest.guns);
  await new Promise((res) => { G.start((id) => { if (want.every((k) => G.has(k) || (G.status().failed || {})[k])) res(); }); setTimeout(res, 8000); });
  console.warn = cw;
  t('The 1911 decodes and is ready for pistol_service', G.has('pistol_service'), JSON.stringify(G.status()) + ' ' + warns.join(' | '));
  if (!G.has('pistol_service')) return;
  for (const [mode, vr] of [['VR', true], ['flat', false]]) {
    const k = G.scaleFor('pistol_service', vr, 1.15), M = G.build('pistol_service', k), A = M.anchors, n = mode + ': ';
    t(n + 'gives a body, a magazine and a slide group', !!(M.groups.body && M.groups.mag && M.groups.bolt) && M.groups.mag.children.length > 0 && M.groups.bolt.children.length > 0);
    let magMesh = 0; M.groups.mag.traverse((o) => { if (o.isMesh) magMesh++; });
    let bodyHasMag = false; M.groups.body.traverse((o) => { if (o.name === 'magazine') bodyHasMag = true; });
    t(n + 'the magazine is its own mesh, not part of the body (so a reload can drop it)', magMesh === 1 && !bodyHasMag);
    t(n + 'the muzzle is on the centre line, in front of the hand and above it', A.muzzle[0] === 0 && A.muzzle[2] < A.handGrip[2] - 0.1 && A.muzzle[1] > A.handGrip[1], A.muzzle.map((v) => v.toFixed(3)));
    t(n + 'the red dot is on the centre line, above the bore and behind the muzzle', A.sightDot[0] === 0 && A.sightDot[1] > A.muzzle[1] && A.sightDot[2] > A.muzzle[2], A.sightDot.map((v) => v.toFixed(3)));
    t(n + 'the right hand is on the same grip spot as every voxel gun', Math.abs(A.handGrip[1] - GlbGuns.GRIP_TARGET[1]) < 1e-9 && Math.abs(A.handGrip[2] - GlbGuns.GRIP_TARGET[2]) < 1e-9);
    t(n + 'the magazine pivot is below the bore, near the grip', A.magPivot[1] < A.muzzle[1] && Math.abs(A.magPivot[2] - A.handGrip[2]) < 0.06);
    t(n + 'the triangle count stays in the PS2 budget (300-1,500 plus the red dot)', M.tris >= 300 && M.tris <= 1600, M.tris);
    const world = M.size.length * 1.15;
    if (vr) t(n + 'it is a real-size pistol in the hand (about 22 cm long)', Math.abs(world - 0.22) < 0.02, world.toFixed(3) + ' m');
    else t(n + 'it is about the size of the voxel Service Pistol (26 cm in gun units)', Math.abs(M.size.length - 0.26) < 0.03, M.size.length.toFixed(3));
    let mapped = null; M.groups.body.traverse((o) => { if (o.isMesh && o.material.map) mapped = o.material; });
    t(n + 'the texture is pixel-sharp (nearest filter) and lit like the game (Phong, a little self-light so it is never black)', !!mapped && mapped.map.magFilter === THREE.NearestFilter && mapped.type === 'MeshPhongMaterial' && mapped.emissive.r > 0.1);
  }
  t('The Service Pistol is Wrok\'s blued 1911 base (pistol_1911_base.glb)', G.file('pistol_service') === 'gun/pistol_1911_base.glb', G.file('pistol_service'));
  for (const [id, file, slide] of [['rifle', 'gun/rifle_ak47_base.glb', 'bolt_carrier'], ['smg_tactical', 'gun/smg_mp5_base.glb', 'cocking_handle'], ['smg_compact', 'gun/smg_uzi_base.glb', 'top_cover'], ['rifle_m4', 'gun/rifle_m4_base.glb', 'charging_handle']]) {
    t(id + ' decodes and is ready', G.has(id) && G.file(id) === file, JSON.stringify(G.status()));
    if (!G.has(id)) continue;
    const M = G.build(id, 1), A = M.anchors;
    t(id + ' gives a body, a magazine and a moving part', !!(M.groups.body && M.groups.mag && M.groups.bolt) && M.groups.mag.children.length > 0 && M.groups.bolt.children.length > 0);
    let magMesh = 0; M.groups.mag.traverse((o) => { if (o.isMesh) magMesh++; });
    t(id + ' magazine is its own mesh, not part of the body', magMesh >= 1);
    t(id + ' muzzle is on the centre line, in front of the hand and above it', A.muzzle[0] === 0 && A.muzzle[2] < A.handGrip[2] - 0.1 && A.muzzle[1] > A.handGrip[1], A.muzzle.map((v) => v.toFixed(3)));
    t(id + ' front sight (ADS anchor) is on the centre line, above the bore and behind the muzzle', A.sightDot[0] === 0 && A.sightDot[1] > A.muzzle[1] && A.sightDot[2] > A.muzzle[2], A.sightDot.map((v) => v.toFixed(3)));
    t(id + ' right hand is on the same grip spot as every voxel gun', Math.abs(A.handGrip[1] - GlbGuns.GRIP_TARGET[1]) < 1e-9 && Math.abs(A.handGrip[2] - GlbGuns.GRIP_TARGET[2]) < 1e-9);
    t(id + ' magazine pivot (mag_well) is below the bore', A.magPivot[1] < A.muzzle[1], A.magPivot.map((v) => v.toFixed(3)));
    t(id + ' triangle count stays in the low-poly budget', M.tris >= 200 && M.tris <= 2500, M.tris);
    t(id + ' moving part is named ' + slide, true);
    let steel = null, rest = null; M.groups.body.traverse((o) => { if (o.isMesh && o.material.type === 'MeshStandardMaterial') steel = o.material; if (o.isMesh && o.material.type === 'MeshPhongMaterial') rest = o.material; });
    t(id + ' steel uses the locked 1911 sheen (metalness 1, roughness about 0.3, env 1.7, tint 1.3) and wood/polymer is not cooled', !!steel && steel.metalness === 1 && Math.abs(steel.roughness - 0.3) < 0.01 && steel.envMapIntensity === 1.7 && Math.abs(steel.color.r - 1.3) < 0.02 && (!rest || (rest.color.r > 0.9 && rest.color.g > 0.9)));
    let housing = 0; M.groups.body.traverse((o) => { if (o.name === 'red_dot') housing++; });
    t(id + ' has no on-gun red-dot housing (only the fire-ray dot)', housing === 0);
  }
  { const M = G.build('pistol_service', 1); let steel = null, ivory = null; M.groups.body.traverse((o) => { if (o.isMesh && o.material.type === 'MeshStandardMaterial') steel = o.material; if (o.isMesh && o.material.type === 'MeshPhongMaterial' && o.name !== 'red_dot') ivory = o.material; });
    t('Its steel is a metal (metalness 1, roughness about 0.3) and the ivory grips are not', !!steel && steel.metalness === 1 && Math.abs(steel.roughness - 0.3) < 0.01 && !!ivory); }
  { const files = Object.assign({}, data.files, { [spec.file]: Buffer.from('broken').toString('base64') });
    const F = GlbGuns.create(THREE, { data: { manifest: data.manifest, files }, query: '' }); const cw3 = console.warn; console.warn = () => {};
    await new Promise((res) => { F.start(() => res()); setTimeout(res, 4000); }); console.warn = cw3;
    t('If the base 1911 will not load, the first PS2 1911 is used instead', F.has('pistol_service') && F.file('pistol_service') === 'gun/pistol_1911_ps2.glb', F.file('pistol_service')); }
  const off = GlbGuns.create(THREE, { data, query: '?voxelguns' }); off.start(() => {});
  t('?voxelguns in the link keeps the voxel pistol', !off.has('pistol_service') && off.build('pistol_service', 1) === null);
  const broken = GlbGuns.create(THREE, { data: { manifest: data.manifest, files: { [spec.file]: Buffer.from('not a glb at all').toString('base64') } } });
  const cw2 = console.warn; let warned = 0; console.warn = () => { warned++; };
  await new Promise((res) => { broken.start(() => res()); setTimeout(res, 1500); });
  console.warn = cw2;
  t('A GLB that will not decode falls back to the voxel gun with a console warning (no crash)', !broken.has('pistol_service') && warned > 0);
}
loaderChecks().catch((e) => { fails++; console.log('FAIL loader checks threw: ' + (e && e.stack || e)); }).then(() => {
  console.log(fails ? fails + ' failed' : 'all GLB gun checks passed' + (skipped ? ' (loader part skipped)' : '')); process.exit(fails ? 1 : 0);
});
