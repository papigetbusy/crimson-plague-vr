/* ============================================================
   SCREEN
   Draws the 3D view and sends inputs. Holds no game rules:
   every position, hit, damage and monster move comes from the
   Referee. Anything here is presentation only.
   ============================================================ */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, t) => a + (b - a) * t;

  if (!window.THREE) { $('fatal').hidden = false; return; }

  const ref = Referee.create((Date.now() & 0xffffff) | 1);
  const SANDBOX = /sandbox/.test(location.hash + location.search);   // ?sandbox: the VR test map (a small floor, a few weak monsters, one of each gun type at your feet). Test link only, the normal game is unchanged
  const GAME_CFG = { startGun: 'pistol_service', gunDrops: true, gearDrops: true, modDrops: true, stashOpen: true, manualGuns: true, bossRandom: true };      // the game's rules: you start with the silver pistol and monsters drop guns, armor and charms (the referee's plain defaults keep the tests steady)
  if (SANDBOX) Object.assign(GAME_CFG, { floorSize: 44, monsterCount: 2, monsterDamage: 2, playerHp: 400, keepDrops: true, doorTest: true });   // test map: the gold gate stays shut so paying at a door can be tried (you get the gold), the boss door opens when you use it, floor guns never fade
  ref.setCfg(GAME_CFG); ref.setStash(StashStore.read());          // what you put in the chest on earlier runs is still there

  // a link can start the run on a later wave, to try the boss: ...#wave10 (or ?wave=10)
  const startWaveFromLink = (() => { const m = /wave=?(\d+)/.exec(location.hash + location.search); return m ? Math.max(1, Math.min(60, +m[1])) : 1; })();
  const safeFromLink = /safe/.test(location.hash + location.search);                        // ...#wave=11&safe starts in the safe room with gold, to try the shop
  if (startWaveFromLink > 1) { ref.setCfg({ startWave: startWaveFromLink, startSafe: safeFromLink }); }
  ref.reset();

  // presentation-only numbers (the tuning panel edits these too)
  const GUN_DEFAULTS = { gunX: 0.29, gunY: -0.36, gunZ: -0.5, gunScale: 1.15 };
  const view = Object.assign({ pixelH: 300, brightness: 1, fogFar: 34, sound: 1, fxPreset: 'auto', fxAuto: 1, wallSkin: 'original', gunSkin: 'crimson' }, GUN_DEFAULTS, TouchLayout.DEFAULTS);
  const LS_KEY = 'crimsonhall.tune.v2';
  try {
    let saved = JSON.parse(localStorage.getItem(LS_KEY) || 'null');
    if (!saved) {   // carry over movement and look tuning from the first build, but not gun position
      saved = JSON.parse(localStorage.getItem('crimsonhall.tune.v1') || 'null');
      if (saved) { for (const k of ['gunX', 'gunY', 'gunZ', 'gunScale']) if (saved.view) delete saved.view[k]; if (saved.ref) { delete saved.ref.fovAds; delete saved.ref.fireRate; } }
    }
    if (saved) { if (saved.ref) ref.setCfg(saved.ref); if (saved.view) { Object.assign(view, saved.view); if (!saved.view.fxAuto) view.fxPreset = 'auto'; } }   // an old saved look (from before shots followed the gun) is dropped once
    view.fxAuto = 1;
  } catch (e) { /* storage can be unavailable */ }

  /* ============ texture painting (small canvases, nearest filter = chunky pixels) ============ */
  const T = WorldTex.create(THREE);
  const { texStone, texBanner, texPanel, texPillar, texGold, texFloor, texFloor2, texFloor3, texFloorEdge, texCarpet, texCeil, texCloth, texSkin, texBone, texDark } = T;

  /* ============ renderer, scene, camera ============ */
  const canvas = $('gl');
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
  } catch (e) { $('fatal').hidden = false; return; }
  renderer.setPixelRatio(1);
  const FOG_COL = 0x0c0406;                                   // a deep, warm crimson-black haze (was almost pure black)
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(FOG_COL);
  scene.fog = new THREE.Fog(FOG_COL, 5, view.fogFar);
  const camera = new THREE.PerspectiveCamera(64, 2, 0.05, 120);
  camera.rotation.order = 'YXZ';
  scene.add(camera);

  function resize() {
    const w = Math.max(1, window.innerWidth), h = Math.max(1, window.innerHeight);
    const ph = Math.min(view.pixelH, h), pw = Math.round(ph * w / h);
    renderer.setSize(pw, ph, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  // lights for the things that move (gun and monsters); the world is lit by baked torch light
  scene.add(new THREE.AmbientLight(0x8a6a70, 0.75));
  const dirLight = new THREE.DirectionalLight(0xffd0a0, 0.55); dirLight.position.set(-0.4, 1, 0.6); scene.add(dirLight);
  const lantern = new THREE.PointLight(0xffb070, 0.8, 20, 2); camera.add(lantern);

  // simple helper for small solid boxes
  const geoCache = {};
  function boxMesh(w, h, d, mat, x, y, z, parent) {
    const k = w + '_' + h + '_' + d;
    const geo = geoCache[k] || (geoCache[k] = new THREE.BoxGeometry(w, h, d));
    const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z);
    if (parent) parent.add(m);
    return m;
  }

  /* ============ world: the floor is baked and drawn by src/screen/world_view.js (rebuilt on every new floor), with the glow texture shared by the flames ============ */
  const glowTex = (function () {
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, 'rgba(255,190,90,0.95)'); gr.addColorStop(0.35, 'rgba(255,120,40,0.35)'); gr.addColorStop(1, 'rgba(255,90,20,0)');
    g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  })();
  const worldView = WorldView.create(THREE, scene, T, glowTex);
  const locksView = LocksView.create(THREE, scene, T, glowTex);   // the gold gates, the boss door's sign and puzzle, the hidden sockets
  let loadedFloor = -1;
  const goldLit = new THREE.MeshLambertMaterial({ map: texGold, emissive: 0x3a2a0a });   // the gun's gold trim (the world's own gold lives in world_view.js)

  /* ============ the gun: gothic AK-pattern rifle, red dot sight, gloved hands ============ */
  const stoneLit = new THREE.MeshLambertMaterial({ map: texStone, emissive: 0x181414 });
  const gemMat = new THREE.MeshBasicMaterial({ color: 0xd8222c });
  const gemHi = new THREE.MeshBasicMaterial({ color: 0xff7a6e });
  const blackMat = new THREE.MeshBasicMaterial({ color: 0x050303 });
  const gloveMat = new THREE.MeshLambertMaterial({ map: texDark, emissive: 0x1a100c });
  const gun = new THREE.Group();
  camera.add(gun);
  const gunBody = new THREE.Group(); gun.add(gunBody);
  const gb = (w, h, d, m, x, y, z, p) => boxMesh(w, h, d, m, x, y, z, p || gunBody);
  // the rifle itself: Grok's gothic assault rifle, built from voxels (src/models/gothic_rifle.js)
  const HIP_DOT = GunList.HIP_DOT;                               // where the rifle's red dot sits in gun space; the hip pose is tuned for it
  const gunLook = GunLook.create(THREE, gunBody);                // smoothed shiny meshes, skins, glow and the little light on the hands (src/screen/gun_look.js)
  const gunRig = new THREE.Group(); gunBody.add(gunRig);        // the voxel parts of whichever gun is in your hands (rebuilt by setGun)
  const rigParts = [];
  const voxelPart = (part, vox, parent) => { const g = new THREE.Group(); parent.add(g); rigParts.push(g); return gunLook.part(part, vox, g); };
  const MAG_BASE = new THREE.Vector3(), SIGHT = { y: 0, z: 0 };
  let charge, mag, CHARGE_Z = 0, muzzle;
  const CHARGE_REST = new THREE.Vector3(), GP = { gunBody: null, magBase: null, chargeRest: CHARGE_REST, fore: null };   // the gun's parts for the VR hand reload
  // the red dot floats between the scope rings; ADS lines it up with the eye
  const EYE_RELIEF = 0.5;
  const dotMat = new THREE.MeshBasicMaterial({ color: 0xff2424, fog: false });
  const dotMesh = gb(0.008, 0.008, 0.004, dotMat, 0, 0, 0);
  const dotGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xff2a2a, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, transparent: true }));
  dotGlow.scale.setScalar(0.035); gunBody.add(dotGlow);

  // gloved hands and forearms (forearms stretch between a fixed elbow and the hand)
  const limbGeo = new THREE.BoxGeometry(1, 1, 1);
  const makeLimb = () => { const m = new THREE.Mesh(limbGeo, gloveMat); gunBody.add(m); return m; };
  const limbL = makeLimb(), limbR = makeLimb();
  const handL = new THREE.Group(); gunBody.add(handL);
  gb(0.13, 0.08, 0.14, gloveMat, 0, 0, 0, handL);
  gb(0.035, 0.1, 0.11, gloveMat, -0.08, 0.05, 0, handL);
  gb(0.035, 0.1, 0.11, gloveMat, 0.08, 0.05, 0, handL);
  gb(0.05, 0.035, 0.09, gloveMat, 0.07, 0.1, -0.03, handL);
  gb(0.15, 0.1, 0.05, goldLit, 0, -0.015, 0.11, handL);
  const handR = new THREE.Group(); gunBody.add(handR);
  gb(0.12, 0.14, 0.07, gloveMat, 0, 0, 0, handR);
  for (const y of [0.045, 0.005, -0.035]) gb(0.11, 0.035, 0.08, gloveMat, 0, y, -0.075, handR);
  gb(0.035, 0.04, 0.1, gloveMat, -0.075, 0.07, -0.03, handR);
  gb(0.14, 0.1, 0.045, goldLit, 0, -0.01, 0.07, handR);
  const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
  const HOLD = V3(0, -0.12, -0.45), MAGH = V3(0, -0.15, -0.13), BELT = V3(-0.15, -0.8, -0.05);   // set per gun by setGun: where the left hand holds, grabs the magazine
  const CH_F = V3(0.1, 0.1, -0.17), CH_B = V3(0.1, 0.1, 0.0);                                   // and pulls the charging handle
  const ELBOW_L = V3(-0.55, -1.0, 0.7), ELBOW_R = V3(0.3, -0.9, 1.0);
  const Zaxis = V3(0, 0, 1), tA = V3(0, 0, 0), tB = V3(0, 0, 0);
  function placeLimb(m, a, b, th) {
    tA.subVectors(b, a); const len = tA.length() || 1;
    m.position.copy(a).addScaledVector(tA, 0.5);
    m.quaternion.setFromUnitVectors(Zaxis, tA.divideScalar(len));
    m.scale.set(th, th * 0.9, len);
  }
  muzzle = new THREE.Object3D(); gunBody.add(muzzle);
  const flashMat = new THREE.MeshBasicMaterial({ color: 0xffc860, transparent: true, opacity: 0.95, depthWrite: false, blending: THREE.AdditiveBlending, fog: false });
  const flashMesh = new THREE.Group(); muzzle.add(flashMesh);
  boxMesh(0.14, 0.14, 0.06, flashMat, 0, 0, -0.04, flashMesh);
  boxMesh(0.04, 0.26, 0.04, flashMat, 0, 0, -0.08, flashMesh);
  boxMesh(0.26, 0.04, 0.04, flashMat, 0, 0, -0.08, flashMesh);
  flashMesh.visible = false;
  const muzzleLight = new THREE.PointLight(0xff9a40, 0, 14, 2); muzzle.add(muzzleLight);
  const fogGlow = new THREE.PointLight(0xffa860, 0, 16, 2); gun.add(fogGlow); fogGlow.position.set(0, 0.1, -0.3);   // the glow of your gun, only lit in fog

  // swap the gun in your hands: rebuilds the parts, moves the sight dot and muzzle, and puts both hands where this gun is held (the hands anchors in gun_kit.js)
  let curGun = null, baseSkin = 'crimson', lookKey = '';
  let gunChanged = () => {};
  function setGun(id, takeSkin) {
    const entry = GunList.find(id); if (!entry) return; curGun = entry.id;
    const G = entry.build(), A = G.anchors, H = entry.hands || G.hands || { grip: A.handGrip || [0, -0.15, 0.15], fore: A.handFore || [0, -0.12, -0.45], mag: A.handMag || [0, -0.15, -0.13] };
    gunLook.release(); rigParts.forEach((g) => gunRig.remove(g)); rigParts.length = 0;
    voxelPart(G.parts.body, G.vox, gunRig);
    charge = voxelPart(G.parts.bolt, G.vox, gunRig); charge.position.set(A.boltRest[0], A.boltRest[1], A.boltRest[2]); CHARGE_Z = A.boltRest[2]; CHARGE_REST.copy(charge.position);
    mag = voxelPart(G.parts.mag, G.vox, gunRig); mag.rotation.x = 0.1; MAG_BASE.set(A.magPivot[0], A.magPivot[1], A.magPivot[2]); mag.position.copy(MAG_BASE);
    SIGHT.y = A.sightDot[1]; SIGHT.z = A.sightDot[2];
    dotMesh.position.set(0, SIGHT.y, SIGHT.z); dotGlow.position.set(0, SIGHT.y, SIGHT.z + 0.004);
    muzzle.position.set(A.muzzle[0], A.muzzle[1], A.muzzle[2]);
    handR.position.set(H.grip[0], H.grip[1], H.grip[2]);
    HOLD.set(H.fore[0], H.fore[1], H.fore[2]); MAGH.set(H.mag[0], H.mag[1], H.mag[2]);
    CH_F.set(A.boltRest[0] + 0.1, A.boltRest[1] + 0.04, A.boltRest[2]); CH_B.copy(CH_F); CH_B.z += 0.17;
    if (entry.hands) { CH_F.set(0.1, 0.1, -0.17); CH_B.set(0.1, 0.1, 0.0); }                          // the rifle keeps its old handle spots
    baseSkin = G.skin || 'crimson'; if (takeSkin) view.gunSkin = baseSkin;
    gunLook.setSkin(view.gunSkin || 'crimson'); view.gun = curGun; gunChanged();
  }
  setGun(ref.snapshot().player.gun.id, true);                                   // the gun the referee says you hold; setGun runs again whenever it changes

  // reload choreography: hand keyframes (k = 0..1 through the reload)
  const RL_NORMAL = { hand: [[0, HOLD], [0.16, MAGH], [0.24, MAGH], [0.38, BELT], [0.46, BELT], [0.64, MAGH], [0.72, MAGH], [0.9, HOLD], [1, HOLD]], grab: 0.24, pullEnd: 0.38, newStart: 0.46, seat: 0.64, tilt: [0.14, 0.8, 1.0], snd: { magout: 0.3, magin: 0.66 }, bolt: null };
  const RL_EMPTY = { hand: [[0, HOLD], [0.12, MAGH], [0.18, MAGH], [0.3, BELT], [0.36, BELT], [0.5, MAGH], [0.55, MAGH], [0.64, CH_F], [0.72, CH_B], [0.78, CH_F], [0.9, HOLD], [1, HOLD]], grab: 0.18, pullEnd: 0.3, newStart: 0.36, seat: 0.5, tilt: [0.1, 0.86, 1.0], snd: { magout: 0.24, magin: 0.52, bolt: 0.72 }, bolt: [0.64, 0.78] };
  // a shotgun has no magazine to swap: the left hand goes to your belt for a shell, feeds it in, three times, then racks the pump
  const RL_SHELLS = { hand: [[0, HOLD], [0.08, BELT], [0.16, MAGH], [0.24, BELT], [0.32, MAGH], [0.4, BELT], [0.48, MAGH], [0.56, BELT], [0.64, MAGH], [0.74, CH_F], [0.84, CH_B], [0.9, CH_F], [0.96, HOLD], [1, HOLD]], grab: 9, pullEnd: 9, newStart: 9, seat: 9, tilt: [0.1, 0.88, 1.0], snd: { magin: 0.16, magin2: 0.32, magin3: 0.48, bolt: 0.84 }, bolt: [0.74, 0.9] };
  // inspect (magazine): the left hand pulls the magazine out, lifts it in front of the eye (MAG_LOOK is the hand spot that puts the magazine
  // top at camera-space (-0.03, 0.02, -0.38) while the gun is tilted away, worked out with the pose from GunMotion.inspect('mag')), then slides it home
  const MAG_LOOK = V3(-0.094, 0.2415, 0.211), MAG_DOWN = V3(-0.04, -0.3, -0.1);
  const INSPECT_MAG = { hand: [[0, HOLD], [0.1, MAGH], [0.17, MAGH], [0.27, MAG_DOWN], [0.4, MAG_LOOK], [0.72, MAG_LOOK], [0.8, MAG_DOWN], [0.86, MAGH], [0.93, HOLD], [1, HOLD]], grab: 0.17, pullEnd: 9, newStart: 9, seat: 0.86, snd: { magout: 0.24, magin: 0.88 }, bolt: null };
  const smooth01 = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
  const handPos = V3(0, 0, 0), kfOut = V3(0, 0, 0);
  function kfLerp(frames, k, out) {
    if (k <= frames[0][0]) return out.copy(frames[0][1]);
    for (let i = 1; i < frames.length; i++) {
      if (k <= frames[i][0]) {
        const a = frames[i - 1], b = frames[i];
        return out.lerpVectors(a[1], b[1], smooth01((k - a[0]) / (b[0] - a[0])));
      }
    }
    return out.copy(frames[frames.length - 1][1]);
  }
  let rlPrev = 0;
  // returns gun offsets for this frame and poses the hands, mag and charging handle
  const NO_RL = { px: 0, py: 0, pz: 0, rx: 0, ry: 0, rz: 0 };
  function animateReload(p) {
    const vr = !!(xr && xr.presenting());                           // VR plays the same reload on the gun (the hands are hidden, so the magazine and shells are what you see)
    const ins = !p.reloading && inspK > 0 && inspKind === 'mag';
    const gtype = RefereeWeapons.GUNS[p.gun.id].type, shells = gtype === 'shotgun';
    const R = ins ? INSPECT_MAG : shells ? RL_SHELLS : (p.reloadEmpty || gtype === 'sniper') ? RL_EMPTY : RL_NORMAL;   // a sniper works its bolt after every magazine
    const k = p.reloading ? p.reloadK : ins ? inspK : 0;
    kfLerp(R.hand, k, handPos);
    handL.position.copy(handPos);
    let magHidden = false;
    mag.position.copy(MAG_BASE);
    if ((p.reloading || ins) && k >= R.grab && k < R.seat) {
      magHidden = k > R.pullEnd && k < R.newStart;
      mag.position.x += handPos.x - MAGH.x; mag.position.y += handPos.y - MAGH.y; mag.position.z += handPos.z - MAGH.z;
    }
    if (vr && magHidden && !magWasHidden && p.reloading) xr.dropMag(mag);   // VR: the old magazine falls away from the gun
    magWasHidden = magHidden;
    mag.visible = !magHidden;
    // VR: a shell rides from the belt into the loading port on each push (the flat game shows it in the glove)
    let sh = false;
    if (vr && shells && p.reloading) for (let i = 0; i < 4; i++) { const a = 0.08 + i * 0.16; if (k > a && k < a + 0.08) sh = true; }
    vrShell.visible = sh; if (sh) vrShell.position.copy(handPos);
    charge.position.z = CHARGE_Z + ((p.reloading && R.bolt && k >= R.bolt[0] && k <= R.bolt[1]) ? (handPos.z - CH_F.z) : 0);
    tB.copy(handPos); tB.y -= 0.02; tB.z += 0.1;
    placeLimb(limbL, ELBOW_L, tB, 0.12);
    tB.copy(handR.position); tB.z += 0.08;
    placeLimb(limbR, ELBOW_R, tB, 0.12);
    // sounds on the way through
    if (p.reloading || ins) {
      for (const n in R.snd) if (rlPrev < R.snd[n] && k >= R.snd[n]) { sfx(n.replace(/\d+$/, '')); if (vr) xr.pulse(/bolt/.test(n) ? 'right' : 'left', /bolt/.test(n) ? 0.55 : 0.35, /bolt/.test(n) ? 40 : 25); }   // VR: a buzz on every magazine seat, shell and rack
    }
    rlPrev = p.reloading || ins ? k : 0;
    mag.rotation.set(0.1 + (ins ? 0.5 * smooth01((k - 0.3) / 0.1) * (1 - smooth01((k - 0.74) / 0.08)) : 0), ins ? GunMotion.magSpin(k) : 0, 0);   // the held magazine turns so you see both faces
    if (!p.reloading) return { px: 0, py: 0, pz: 0, rx: 0, ry: 0, rz: 0 };
    const tilt = smooth01(k / R.tilt[0]) * (1 - smooth01((k - R.tilt[1]) / (R.tilt[2] - R.tilt[1])));
    const bump = Math.exp(-Math.pow((k - R.seat) / 0.025, 2));
    return { px: -0.1 * tilt, py: -0.05 * tilt, pz: 0.03 * tilt + bump * 0.035, rx: 0.28 * tilt + bump * 0.06, ry: -0.12 * tilt, rz: -0.5 * tilt };
  }
  const shellV = V3(0, 0, 0);
  let magWasHidden = false;
  const vrShell = new THREE.Group(); vrShell.visible = false; gunBody.add(vrShell);   // a red shotgun shell with a brass end (VR reload only)
  { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.07, 10), new THREE.MeshLambertMaterial({ color: 0xa8121c, emissive: 0x300406 })); c.rotation.x = Math.PI / 2; vrShell.add(c);
    const r = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.015, 10), new THREE.MeshLambertMaterial({ color: 0xc89a3a, emissive: 0x302008 })); r.rotation.x = Math.PI / 2; r.position.z = 0.035; vrShell.add(r); }

  /* ============ monsters: four voxel kinds, built and posed by src/screen/monster_rigs.js ============ */
  const RIGS = MonsterRigs.create(THREE), MODEL = RIGS.MODEL;
  const shotsView = ShotsView.create(THREE, scene, glowTex);   // spit, bolts and fireballs the monsters throw
  { const q = ['goblin', 'skeleton', 'mushroom', 'eyeball', 'flame', 'bat', 'lich', 'dragon'], warm = () => { if (!q.length) return; if (!RIGS.warmStep(q[0])) q.shift(); setTimeout(warm, 120); }; setTimeout(warm, 3000); }   // cut and smooth the newer kinds a slice at a time in the background, so the first one to appear does not stall a frame
  const mons = new Map();     // id -> entry
  const dying = [];
  const smoothLight = (x, z) => worldView.light(x, 1.5, z, 0, 1, 0);
  const loot = LootView.create(THREE, scene, glowTex);       // XP orbs and pickups
  const bossFx = BossFx.create(THREE, scene);               // floor warnings for the boss attacks
  const peersView = PeersView.create(THREE, scene);         // the friends you play with
  let coopKey = 'host';                                      // which player you are (set every frame), so your own bullets are not drawn twice
  const partyHud = PartyHud.create($);                      // their health, and the message while you are down
  const trapView = TrapView.create(THREE, scene, glowTex);   // spike patches, flame vents, rising spikes
  const fx = FxSprites.create(THREE, camera, scene);          // sprite explosions, sparks and lightning (look presets, see fx_plan.js)
  // the look of shots, hits and kills: it follows the gun in your hands (rarity picks the tier, each status colour adds its element). Only the private cheat build can force another look.
  let gunLookId = 'common';
  const fxId = () => (CHEAT && view.fxPreset !== 'auto' ? view.fxPreset : gunLookId);
  const fxOn = () => fx.art() && fxId() !== 'original';
  let shakeAmp = 0, shakeT = 0;

  /* ============ effects ============ */
  const parts = [];
  const partGeo = new THREE.BoxGeometry(0.1, 0.1, 0.1);
  for (let i = 0; i < 100; i++) {
    const m = new THREE.Mesh(partGeo, new THREE.MeshBasicMaterial({ color: 0xffffff }));
    m.visible = false; scene.add(m);
    parts.push({ m, v: new THREE.Vector3(), life: 0, grav: 0 });
  }
  let partCursor = 0;
  function burst(x, y, z, n, colors, speed, life, grav, size) {
    for (let i = 0; i < n; i++) {
      const p = parts[partCursor++ % parts.length];
      p.m.visible = true; p.m.position.set(x, y, z);
      p.m.material.color.setHex(colors[(Math.random() * colors.length) | 0]);
      const s = (size || 1) * (0.6 + Math.random() * 0.9); p.m.scale.setScalar(s);
      const a = Math.random() * 6.283, e = Math.random() * 1.2 - 0.2, sp = speed * (0.4 + Math.random() * 0.8);
      p.v.set(Math.cos(a) * Math.cos(e) * sp, Math.sin(e) * sp + speed * 0.3, Math.sin(a) * Math.cos(e) * sp);
      p.life = life * (0.6 + Math.random() * 0.6); p.grav = grav;
    }
  }
  const tracers = [];
  const tracerGeo = new THREE.BoxGeometry(1, 1, 1);
  for (let i = 0; i < 8; i++) {
    const m = new THREE.Mesh(tracerGeo, new THREE.MeshBasicMaterial({ color: 0xffd27a, transparent: true, fog: false, blending: THREE.AdditiveBlending, depthWrite: false }));
    m.visible = false; scene.add(m); tracers.push({ m, life: 0 });
  }
  let tracerCursor = 0, shotN = 0;
  const tmpV = new THREE.Vector3(), tmpV2 = new THREE.Vector3();
  // from/look are for a friend's bullet: the start of the streak (their muzzle) and their gun's look; yours starts at your own muzzle with your own look
  function addTracer(ex, ey, ez, from, look) {
    if (from) tmpV.set(from[0], from[1], from[2]); else muzzle.getWorldPosition(tmpV);
    tmpV2.set(ex, ey, ez);
    shotN++;
    const lk = look || fxId(), on = look ? fx.art() && look !== 'original' : fxOn();
    const t = tracers[tracerCursor++ % tracers.length], tr = FxPlan.tracer(on ? lk : 'original', shotN);
    const len = tmpV.distanceTo(tmpV2);
    t.m.position.copy(tmpV).add(tmpV2).multiplyScalar(0.5);
    t.m.lookAt(tmpV2);
    t.m.scale.set(tr.width, tr.width, len);
    t.m.material.color.setHex((look ? 0 : gunLook.skin().tracer) || tr.color);
    t.m.visible = true; t.life = t.dur = tr.life; t.m.material.opacity = 0.9;
    if (on && tr.trail) fx.trail(lk, tmpV, tmpV2, shotN);
  }
  // a friend's bullet (the host sends everyone's): the streak from their gun, a flash at the muzzle, and what it hit
  function friendShot(e) {
    const m = peersView.muzzleOf(e.key), look = FxPlan.lookFor(e.r, e.s), from = m || [e.ox, e.oy - 0.2, e.oz];
    addTracer(e.ex, e.ey, e.ez, from, look);
    if (fx.art() && look !== 'original') fx.play(look, 'muzzle', from[0], from[1], from[2]);
    if (e.hit === 1) { burst(e.ex, e.ey, e.ez, 5, [0xffb347, 0xff7a1a, 0x888078], 4, 0.35, 12, 0.7); if (fx.art() && look !== 'original') fx.play(look, 'wall', e.ex, e.ey, e.ez); }
    else if (e.hit === 2) { burst(e.ex, e.ey, e.ez, 4, [0xb01818, 0x701010, 0xe03030], 3.5, 0.4, 10, 0.8); if (fx.art() && look !== 'original') fx.play(look, 'flesh', e.ex, e.ey, e.ez, {}); }
  }

  /* ---- floating damage numbers ---- */
  const dnLayer = $('dn');
  const dnPool = [];
  for (let i = 0; i < 14; i++) { const d = document.createElement('div'); d.className = 'dn'; d.hidden = true; dnLayer.appendChild(d); dnPool.push({ d, life: 0, x: 0, y: 0, z: 0 }); }
  let dnCursor = 0;
  function damageNumber(x, y, z, text, crit) {
    const n = dnPool[dnCursor++ % dnPool.length];
    n.d.textContent = text; n.d.className = 'dn' + (crit ? ' crit' : ''); n.d.hidden = false;
    n.life = 0.7; n.x = x + (Math.random() - 0.5) * 0.4; n.y = y; n.z = z + (Math.random() - 0.5) * 0.4;
  }

  /* ============ audio (tiny synth, starts after the first tap) ============ */
  let AC = null, noiseBuf = null;
  function audioInit() {
    if (AC) { if (AC.state === 'suspended') AC.resume(); return; }
    try {
      AC = new (window.AudioContext || window.webkitAudioContext)();
      noiseBuf = AC.createBuffer(1, AC.sampleRate * 0.4, AC.sampleRate);
      const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    } catch (e) { AC = null; }
  }
  function sfx(kind) {
    if (!AC || !view.sound) return;
    const t = AC.currentTime, out = AC.createGain(); out.connect(AC.destination);
    const noise = (dur, f0, f1, vol, type) => {
      const s = AC.createBufferSource(); s.buffer = noiseBuf;
      const f = AC.createBiquadFilter(); f.type = type || 'lowpass'; f.frequency.setValueAtTime(f0, t); f.frequency.exponentialRampToValueAtTime(f1, t + dur);
      const g = AC.createGain(); g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.001, t + dur);
      s.connect(f); f.connect(g); g.connect(out); s.start(t, Math.random() * 0.2, dur);
    };
    const tone = (type, f0, f1, dur, vol) => {
      const o = AC.createOscillator(); o.type = type; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + dur);
      const g = AC.createGain(); g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.001, t + dur);
      o.connect(g); g.connect(out); o.start(t); o.stop(t + dur + 0.02);
    };
    if (kind === 'shot') { noise(0.14, 5200, 500, 0.55); tone('square', 170, 45, 0.12, 0.35); }
    else if (kind === 'hit') { tone('sine', 1100, 700, 0.05, 0.22); }
    else if (kind === 'crit') { tone('sine', 1600, 900, 0.08, 0.28); }
    else if (kind === 'kill') { tone('sawtooth', 240, 50, 0.3, 0.3); noise(0.22, 1800, 200, 0.4); }
    else if (kind === 'hurt') { tone('sine', 110, 50, 0.2, 0.6); noise(0.12, 600, 120, 0.3); }
    else if (kind === 'magout') { tone('square', 340, 110, 0.07, 0.22); noise(0.06, 3500, 700, 0.25); }
    else if (kind === 'magin') { tone('square', 210, 80, 0.09, 0.32); noise(0.07, 2500, 500, 0.3); }
    else if (kind === 'bolt') { noise(0.1, 4200, 1100, 0.35); tone('square', 520, 190, 0.06, 0.2); }
    else if (kind === 'slide') { noise(0.5, 900, 3000, 0.22, 'bandpass'); }
    else if (kind === 'dead') { tone('sawtooth', 160, 30, 0.8, 0.35); }
    else if (kind === 'orb') { tone('sine', 900, 1500, 0.07, 0.12); }
    else if (kind === 'pickup') { tone('sine', 520, 1040, 0.16, 0.25); }
    else if (kind === 'levelup') { tone('square', 330, 660, 0.18, 0.22); tone('sine', 660, 1320, 0.3, 0.2); }
    else if (kind === 'wave') { tone('sawtooth', 90, 70, 0.5, 0.3); noise(0.4, 400, 120, 0.18); }
    else if (kind === 'boss') { tone('sawtooth', 70, 38, 1.0, 0.45); noise(0.7, 300, 80, 0.3); }
    else if (kind === 'blast') { noise(0.25, 1500, 150, 0.35); }
    else if (kind === 'cloak') { noise(0.4, 3000, 400, 0.2); tone('sine', 700, 300, 0.3, 0.12); }
    else if (kind === 'spit') { noise(0.12, 900, 300, 0.3, 'bandpass'); tone('sine', 300, 140, 0.1, 0.2); }
    else if (kind === 'zap') { noise(0.14, 6000, 1500, 0.3); tone('sawtooth', 900, 200, 0.1, 0.18); }
    else if (kind === 'fireball') { noise(0.35, 1200, 200, 0.3); tone('sawtooth', 220, 90, 0.3, 0.2); }
  }

  /* ============ input ============ */
  const I = { swap: false, pickup: false, pickupId: undefined, mx: 0, mz: 0, lookX: 0, lookY: 0, touchX: 0, touchY: 0, fire: false, ads: false, sprint: false, slide: false, jump: false, reload: false, pick: undefined, restart: false };
  const keys = {};
  const mouse = { fire: false, ads: false };
  const tch = { fire: false, ads: false, sprint: false, reload: false };
  const joy = { id: null, ox: 0, oy: 0, x: 0, y: 0 };
  const isTouch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
  let running = false, started = false, panelOpen = false, noLock = false;
  if (isTouch) document.body.classList.add('touch');

  // ---- controller: any standard gamepad that is connected is picked up by itself; the touch controls hide while one is ----
  const pad = { on: false, input: PadInput.create(), now: null };
  let xr = null;                                                  // Meta Quest / WebXR mode (src/screen/xr_mode.js), made once the gun and menus exist
  const currentPad = () => { try { return PadInput.pick(navigator.getGamepads ? Array.from(navigator.getGamepads()) : []); } catch (e) { return null; } };
  const toastEl = $('padToast'); let toastT = 0;
  function toast(msg) { toastEl.textContent = msg; toastEl.classList.add('show'); toastT = 2.6; }
  // once a frame: find the pad, switch the touch controls on or off, and read its input (null when there is no pad)
  function pollPad(dt) {
    const p = (xr && xr.pad()) || currentPad();                    // in VR the Quest controllers act as one standard pad
    if (!!p !== pad.on) {
      pad.on = !!p; document.body.classList.toggle('pad', pad.on); pad.input.reset();
      toast(pad.on ? 'Controller connected' : (isTouch ? 'Controller lost. Touch controls are back' : 'Controller disconnected'));
    }
    toastT -= dt; if (toastT <= 0) toastEl.classList.remove('show');
    pad.now = p ? pad.input.read(p) : null;
    if (pad.now && xr && xr.presenting()) { pad.now.nav = 0; pad.now.navY = 0; pad.now.confirm = false;}   // VR menus use the laser pointer, not the sticks
  }

  const locked = () => document.pointerLockElement === canvas;
  function tryLock() {
    if (isTouch || noLock) return;
    try { const r = canvas.requestPointerLock(); if (r && r.catch) r.catch(() => { if (!everLocked) noLock = true; }); } catch (e) { if (!everLocked) noLock = true; }
  }
  // a level-up or the shop needs the mouse pointer: let go of the mouse when one opens (so you can click a card) and take it back when it closes
  let menuUnlocked = false, relocking = 0;
  const wantsPointer = () => !!(state.choices || state.classChoices || state.shop);
  function menuPointer() {
    if (isTouch || !running || noLock) return;
    if (wantsPointer()) { if (locked()) { menuUnlocked = true; mouse.fire = mouse.ads = false; document.exitPointerLock(); } }
    else if (menuUnlocked) {
      menuUnlocked = false;
      if (!locked() && !panelOpen) { relocking = performance.now(); try { const r = canvas.requestPointerLock(); if (r && r.catch) r.catch(() => {}); } catch (e) { /* the next click takes the mouse back */ } }
    }
  }
  // The browser sometimes refuses the mouse for a moment (right after you tab back in, or a few instants after Esc). That must never switch mouse capture off for good:
  // only a browser that has never once given us the mouse (a sandboxed frame) is treated as having none. Otherwise your next click simply asks again.
  let everLocked = false;
  document.addEventListener('pointerlockerror', () => { if (!everLocked && performance.now() - relocking > 1500) noLock = true; });
  document.addEventListener('pointerlockchange', () => {
    if (locked()) everLocked = true;
    if (!locked() && running && !noLock && !panelOpen && !isTouch && !menuUnlocked) setRunning(false);
  });
  document.addEventListener('keydown', (e) => {
    if (e.target && e.target.tagName === 'INPUT' && e.code !== 'Escape') return;            // typing in a box (a gun's name, the codex search) is not a game key
    keys[e.code] = true;
    if (e.code === 'KeyC' || e.code === 'ControlLeft') { if (running) I.slide = true; e.preventDefault(); }
    if (e.code === 'Space' && running && !e.repeat) I.jump = true;
    if (e.code === 'KeyR' && running) I.reload = true;
    if (e.code === 'KeyG' && (running || gearMenu.isOpen)) toggleGear();                  // open or close the Gear menu
    if (e.code === 'KeyE' && running) pressPickup();                                   // pick up the gun on the floor in front of you
    if (e.code === 'KeyZ' && running) I.lockUse = 1;                                    // at the Scale: take gold back off the pan
    if (e.code === 'KeyQ' && running) I.swap = true;                                     // swap to the gun in your other hand
    if (e.code === 'KeyM' && running) minimap.toggle();                                  // open or close the big map
    if (e.code === 'KeyF' && running) startInspect();   // F shows both sides, press again for the magazine
    const dg = /^(?:Digit|Numpad)([0-9])$/.exec(e.code), dn = dg ? +dg[1] : 0;        // number row or number pad
    if (running && dn >= 1 && dn <= 3) I.pick = dn - 1;                                // level-up gift
    if (running && dn >= 4 && dn <= 6) I.pickClass = dn - 4;                            // level-up class skill
    if (running && (e.code === 'Enter' || e.code === 'NumpadEnter')) I.restart = true;                                     // after you fall
    if (e.code === 'Tab') { e.preventDefault(); if (started) togglePanel(); }
    if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) e.preventDefault();
  });
  document.addEventListener('keyup', (e) => { keys[e.code] = false; });
  document.addEventListener('mousemove', (e) => {
    if (!running) return;
    mouseAt.x = e.clientX; mouseAt.y = e.clientY;
    // with the mouse captured every move turns you. A browser that will not hand over the mouse (a page shown inside a frame) turns you on every move too, with no button held,
    // and the edge of the window keeps turning you (see edgeTurn); menus and the game-over card keep their normal pointer.
    if (locked() || (noLock && !wantsPointer() && !state.over && !panelOpen)) { I.lookX += e.movementX || 0; I.lookY += e.movementY || 0; }
  });
  const mouseAt = { x: -1, y: -1 };
  // no captured mouse: a pointer pushed against the left, right, top or bottom edge keeps turning you, so you are never stuck at the edge of the window
  let edgeT = 0;
  function edgeTurn() {
    const now = performance.now(), dt = Math.min(0.05, (now - edgeT) / 1000); edgeT = now;
    if (!noLock || isTouch || locked() || mouseAt.x < 0 || wantsPointer() || state.over || panelOpen) return;
    const w = window.innerWidth, h = window.innerHeight, zone = 0.06, speed = 900 * dt;
    const ex = mouseAt.x < w * zone ? -1 : mouseAt.x > w * (1 - zone) ? 1 : 0, ey = mouseAt.y < h * zone ? -1 : mouseAt.y > h * (1 - zone) ? 1 : 0;
    I.lookX += ex * speed; I.lookY += ey * speed * 0.6;
  }
  document.addEventListener('pointerdown', (e) => {
    if (e.pointerType !== 'mouse' || !running || panelOpen) return;
    if (e.target.closest && e.target.closest('#panel,#gear,.overlay')) return;
    if (state.over) { I.restart = true; return; }
    if (e.button === 0) { mouse.fire = true; if (!locked()) tryLock(); }
    if (e.button === 2) mouse.ads = true;
  });
  document.addEventListener('pointerup', (e) => {
    if (e.pointerType !== 'mouse') return;
    if (e.button === 0) mouse.fire = false;
    if (e.button === 2) mouse.ads = false;
  });
  // both mouse buttons at once (aim with right, shoot with left): the browser sends a pointerdown only for the FIRST button held, so the second one would be missed.
  // The older mousedown / mouseup events fire for every button and say which are held (e.buttons), so we read the held buttons from those.
  function syncButtons(e) {
    if (!running || panelOpen) return;
    const fire = !!(e.buttons & 1), ads = !!(e.buttons & 2);
    if (!fire) mouse.fire = false;
    if (!ads) mouse.ads = false;
    if (e.target.closest && e.target.closest('#panel,#gear,.overlay')) return;
    if (state.over) return;
    if (fire && !mouse.fire) mouse.fire = true;
    if (ads) mouse.ads = true;
    if ((fire || ads) && !locked()) tryLock();                       // any click asks for the mouse back if the browser took it away
  }
  document.addEventListener('mousedown', syncButtons);
  document.addEventListener('mouseup', syncButtons);
  document.addEventListener('contextmenu', (e) => e.preventDefault());
  window.addEventListener('blur', () => { mouse.fire = mouse.ads = false; for (const k in keys) keys[k] = false; });

  // ---- touch: joystick (left), look (right), buttons ----
  const joyZone = $('joyZone'), lookZone = $('lookZone'), joyBase = $('joyBase'), joyKnob = $('joyKnob');
  const joyR = () => Math.max(46, window.innerHeight * 0.14) * (view.tJoy || 1);
  function placeJoy(x, y) {
    joyBase.style.left = x + 'px'; joyBase.style.top = y + 'px'; joyBase.classList.add('on');
  }
  function resetJoy() {
    joy.id = null; joy.x = joy.y = 0; joyBase.classList.remove('on');
    joyBase.style.left = ''; joyBase.style.top = ''; joyKnob.style.transform = 'translate(-50%,-50%)';
  }
  joyZone.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse' || joy.id !== null) return;
    joy.id = e.pointerId; joy.ox = e.clientX; joy.oy = e.clientY; joy.x = joy.y = 0;
    placeJoy(e.clientX, e.clientY);
    try { joyZone.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
  });
  joyZone.addEventListener('pointermove', (e) => {
    if (e.pointerId !== joy.id) return;
    const R = joyR();
    let dx = e.clientX - joy.ox, dy = e.clientY - joy.oy;
    const l = Math.hypot(dx, dy);
    if (l > R) { joy.ox += dx / l * (l - R); joy.oy += dy / l * (l - R); dx = dx / l * R; dy = dy / l * R; placeJoy(joy.ox, joy.oy); }
    joy.x = dx / R; joy.y = dy / R;
    joyKnob.style.transform = 'translate(calc(-50% + ' + dx + 'px),calc(-50% + ' + dy + 'px))';
  });
  const joyEnd = (e) => { if (e.pointerId === joy.id) resetJoy(); };
  joyZone.addEventListener('pointerup', joyEnd);
  joyZone.addEventListener('pointercancel', joyEnd);

  const look = { id: null, x: 0, y: 0 };
  function lookDown(e) { if (e.pointerType === 'mouse') return false; look.id = e.pointerId; look.x = e.clientX; look.y = e.clientY; return true; }
  lookZone.addEventListener('pointerdown', (e) => {
    if (look.id !== null) return;
    if (lookDown(e)) { try { lookZone.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ } }
  });
  lookZone.addEventListener('pointermove', (e) => {
    if (e.pointerId !== look.id) return;
    I.touchX += e.clientX - look.x; I.touchY += e.clientY - look.y; look.x = e.clientX; look.y = e.clientY;
  });
  const lookEnd = (e) => { if (e.pointerId === look.id) look.id = null; };
  lookZone.addEventListener('pointerup', lookEnd);
  lookZone.addEventListener('pointercancel', lookEnd);

  // fire button: hold to shoot, drag the same thumb to aim
  const bFire = $('bFire'), bAds = $('bAds'), bSprint = $('bSprint'), bSlide = $('bSlide'), bReload = $('bReload');
  const fireP = { id: null, x: 0, y: 0 };
  bFire.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse' || fireP.id !== null) return;
    fireP.id = e.pointerId; fireP.x = e.clientX; fireP.y = e.clientY; tch.fire = true; bFire.classList.add('on');
    try { bFire.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    e.preventDefault();
  });
  bFire.addEventListener('pointermove', (e) => {
    if (e.pointerId !== fireP.id) return;
    I.touchX += e.clientX - fireP.x; I.touchY += e.clientY - fireP.y; fireP.x = e.clientX; fireP.y = e.clientY;
  });
  const fireEnd = (e) => { if (e.pointerId === fireP.id) { fireP.id = null; tch.fire = false; bFire.classList.remove('on'); } };
  bFire.addEventListener('pointerup', fireEnd);
  bFire.addEventListener('pointercancel', fireEnd);
  bAds.addEventListener('pointerdown', (e) => { if (e.pointerType === 'mouse') return; tch.ads = !tch.ads; bAds.classList.toggle('on', tch.ads); e.preventDefault(); });
  bSprint.addEventListener('pointerdown', (e) => { if (e.pointerType === 'mouse') return; tch.sprint = !tch.sprint; bSprint.classList.toggle('on', tch.sprint); e.preventDefault(); });
  for (const ev of ['pointerup', 'pointercancel', 'pointerleave']) bReload.addEventListener(ev, () => { tch.reload = false; });
  bReload.addEventListener('pointerdown', (e) => { if (e.pointerType === 'mouse') return; I.reload = true; tch.reload = true; bReload.classList.add('on'); setTimeout(() => bReload.classList.remove('on'), 180); e.preventDefault(); });
  const bSwap = $('bSwap');
  bSwap.addEventListener('pointerdown', (e) => { if (e.pointerType === 'mouse') return; I.swap = true; bSwap.classList.add('on'); setTimeout(() => bSwap.classList.remove('on'), 180); e.preventDefault(); });
  const bJump = $('bJump'); bJump.addEventListener('pointerdown', (e) => { if (e.pointerType === 'mouse') return; I.jump = true; bJump.classList.add('on'); setTimeout(() => bJump.classList.remove('on'), 180); e.preventDefault(); });
  bSlide.addEventListener('pointerdown', (e) => { if (e.pointerType === 'mouse') return; I.slide = true; bSlide.classList.add('on'); setTimeout(() => bSlide.classList.remove('on'), 180); e.preventDefault(); });

  function gatherInput() {
    let mx = 0, mz = 0; edgeTurn();
    if (joy.id !== null) {
      const l = Math.hypot(joy.x, joy.y);
      if (l > 0.1) { const k = (l - 0.1) / 0.9 / l; mx = joy.x * k; mz = -joy.y * k; }
    }
    const kx = (keys.KeyD || keys.ArrowRight ? 1 : 0) - (keys.KeyA || keys.ArrowLeft ? 1 : 0);
    const kz = (keys.KeyW || keys.ArrowUp ? 1 : 0) - (keys.KeyS || keys.ArrowDown ? 1 : 0);
    const pr = pad.now;
    if (pr && (pr.mx || pr.mz)) { mx = pr.mx; mz = pr.mz; }
    if (kx || kz) { mx = kx; mz = kz; }
    if (tch.sprint && joy.id === null && !(kx || kz)) { tch.sprint = false; bSprint.classList.remove('on'); }
    if (tch.sprint && tch.ads) { tch.sprint = false; bSprint.classList.remove('on'); }
    const out = {
      mx, mz, lookX: I.lookX, lookY: I.lookY, touchX: I.touchX, touchY: I.touchY, padX: pr ? pr.padX : 0, padY: pr ? pr.padY : 0,
      fire: mouse.fire || tch.fire || !!(pr && pr.fire), ads: mouse.ads || tch.ads || !!(pr && pr.ads),
      sprint: !!(keys.ShiftLeft || keys.ShiftRight) || tch.sprint || !!(pr && pr.sprint), slide: I.slide || !!(pr && pr.slide), jump: I.jump || !!(pr && pr.jump), reload: I.reload || !!(pr && pr.reload), swap: I.swap || !!(pr && pr.swap), pickup: I.pickup, pickupId: I.pickupId, lockUse: I.lockUse !== undefined ? I.lockUse : pr && pr.lockUse, seeds: I.restart ? { map: rnd(), damage: rnd(), item: rnd() } : undefined, pick: I.pick, pickClass: I.pickClass, shopClose: I.shopClose, restart: I.restart
    };
    if (xr && xr.presenting()) {                                    // VR: aim follows the right controller's ray (or your head), sent like a mouse move
      const a = xr.aim(), pl = state.player, c = ref.cfg;
      if (a) { const lk = XrInput.lookToward(pl, a, c.lookSens, 1 - pl.adsT * (1 - c.adsLookMul)); out.lookX += lk.lookX; out.lookY += lk.lookY; }
      if (XrInput.autoSprint(out.mz, out.mx) && !out.ads) out.sprint = true;   // stick fully forward runs
      if (xr.menuOpen()) out.fire = false;
      const hy = xr.headYaw();                                        // walk where your head faces, not where the gun points
      if (hy !== null && (out.mx || out.mz)) { const mv = XrInput.headMove(out.mx, out.mz, hy - (a ? a.yaw : pl.yaw)); out.mx = mv.mx; out.mz = mv.mz; }
    }
    I.lookX = I.lookY = I.touchX = I.touchY = 0; I.slide = false; I.jump = false; I.reload = false; I.swap = false; I.pickup = false; I.pickupId = undefined; I.lockUse = undefined; I.pick = undefined; I.pickClass = undefined; I.shopClose = false; I.restart = false;
    return out;
  }

  /* ============ HUD, overlays, tuning panel ============ */
  // the gun box above the ammo: the gun in your hands (coloured by rarity) and the one waiting in your other hand; tap it to swap
  const elGun = $('gunBox'), floorCard = GunCard.create($, (x, y, z) => { const v = new THREE.Vector3(x, y, z).project(camera); return { x: (v.x * 0.5 + 0.5) * innerWidth, y: (-v.y * 0.5 + 0.5) * innerHeight, ok: v.z < 1 }; }, () => { I.pickup = true; }); let gunKey = '', gunHide = 0;
  elGun.addEventListener('pointerdown', (e) => { I.swap = true; e.preventDefault(); e.stopPropagation(); });
  function hudGuns(g) {
    const key = g.id + g.rarity + g.card.dmg + (g.other ? g.other.id + g.other.rarity + g.other.card.dmg : '');
    if (key === gunKey) return; gunKey = key;
    elGun.classList.add('show'); clearTimeout(gunHide); gunHide = setTimeout(() => elGun.classList.remove('show'), 2000);   // pops up for two seconds when you take or swap a gun, then gets out of the way
    $('bSwap').classList.toggle('off', !g.other);
    const RW = RefereeWeapons, col = (r) => '#' + RW.RARITIES[r].color.toString(16).padStart(6, '0');
    elGun.innerHTML = '<b style="color:' + col(g.rarity) + '">' + RW.GUNS[g.id].name + '</b>' + (g.status.length ? ' <i>' + g.status.join(' + ') + '</i>' : '') + (g.card.affixes.length ? '<span>' + g.card.affixes.map((a) => a.text).join(' · ') + '</span>' : '') +
      (g.other ? '<span>swap (Q / Triangle): <u style="color:' + col(g.other.rarity) + '">' + RW.GUNS[g.other.id].name + '</u></span>' : '');
  }
  const elAmmo = $('ammo'), elAmmoN = $('ammoN'), elAmmoM = $('ammoM'), elRl = $('rlFill'), elKills = $('kills'), elHpFill = $('hpFill'), elHurt = $('hurt'), elCross = $('cross'), elHit = $('hitmark');
  const overlay = $('start'), playBtn = $('play'), playLabel = $('playLabel'), diedEl = $('died');
  let lastKills = -1, hitT = 0, hitKill = false, diedT = 0;
  const minimap = Minimap.create($, () => ref.map), compass = Compass.create($);
  const hud = Hud.create($, { pick: (i) => { I.pick = i; }, pickClass: (i) => { I.pickClass = i; }, restart: () => { if (coop.mode === 'guest') toast('The host starts the next run'); else I.restart = true; } });

  function setRunning(v) {
    running = v; if (xr) xr.corner(v);
    overlay.hidden = v;
    classPick.hidden = started; $('coopBtn').hidden = started && coop.mode === 'off'; $('vrNewRun').hidden = !started;
    if (!v) {
      mouse.fire = mouse.ads = false; tch.fire = false; bFire.classList.remove('on');
      playLabel.textContent = started ? 'RESUME' : 'ENTER THE HALL';
    }
  }
  // starts or resumes. A controller press is not a click, so it cannot ask for fullscreen or the mouse lock
  function begin(fromPad) {
    if (coop.blocked) { toast('Waiting for the host to start'); return; }
    audioInit();
    if (!started) {
      started = true;
      if (isTouch && !fromPad) { try { const el = document.documentElement; (el.requestFullscreen || el.webkitRequestFullscreen).call(el); } catch (e) { /* ignore */ } try { screen.orientation.lock('landscape').catch(() => {}); } catch (e) { /* ignore */ } }
    }
    setRunning(true); coop.onBegin(); sandboxGifts();
    if (!fromPad) tryLock();
  }
  playBtn.addEventListener('click', () => begin(false));
  { const sb = $('sandboxBtn'); if (sb) { if (SANDBOX) sb.textContent = 'VR TEST MAP IS ON (back to the normal game)'; sb.addEventListener('click', () => { const u = new URL(location.href); if (SANDBOX) u.searchParams.delete('sandbox'); else u.searchParams.set('sandbox', '1'); location.href = u.toString(); }); } }
  let sandboxGiven = -1;
  function sandboxGifts() {                                          // one gun of each type lies at your feet, plus gold and a couple of mods, so every reload and menu can be tried
    if (!SANDBOX || sandboxGiven === state.floorId) return; sandboxGiven = state.floorId;
    // laid out in an arc in front of you like a weapon rack (not in one pile), so each can be reached, pointed at and grabbed on its own
    const p = state.player, m = ref.map, C = m.CELL, free = (x, z) => { const r = m.rows[Math.floor(z / C)]; const ch = r && r[Math.floor(x / C)]; return ch === '.' || ch === 'c'; };
    const spot = (k, n) => { for (const rad of [1.7, 1.2, 0.8]) { const a = p.yaw + (k - (n - 1) / 2) * 0.36, x = p.x + Math.sin(a) * rad, z = p.z - Math.cos(a) * rad; if (free(x, z) && free(x + 0.4, z) && free(x - 0.4, z) && free(x, z + 0.4) && free(x, z - 0.4)) return [x, z]; } return [p.x, p.z]; };
    const gifts = [['gun', 'shotgun_pump'], ['gun', 'rifle'], ['gun', 'smg_compact'], ['gun', 'sniper_bolt'], ['mod', 1], ['gear', 'head'], ['mod', 2], ['gun', 'hmg_belt'], ['gun', 'pistol_cannon']];
    gifts.forEach(([k, v], i) => { const [x, z] = spot(i, gifts.length); if (k === 'gun') ref.giveGun(v, 1, undefined, x, z); else if (k === 'mod') ref.giveMod(v, undefined, x, z); else ref.giveGear(v, 2, undefined, x, z); });
    ref.giveGold(1000); state = ref.snapshot();
  }
  const coop = Coop.create($, ref, { toast: (t) => toast(t), playLabel: (t, off) => { $('playLabel').textContent = t; playBtn.disabled = off; }, begin });
  // controller menus: Start pauses and resumes, A starts, picks the highlighted level-up card, and rises again after a fall
  function padMenus() {
    const r = pad.now; if (!r) return;
    if (r.start) { if (running) setRunning(false); else begin(true); return; }
    if (!running) {
      if (r.nav && !started) chooseClass(classSel + r.nav);
      if (r.navY && !started) bpFocusStart.move(r.navY);                                          // up and down walk over the blueprints, A taps the highlighted one
      if (r.confirm) { if (!started && bpFocusStart.press('click')) return; begin(true); }
      return;
    }
    for (const m of [gearMenu, stashMenu]) if (m.isOpen) {                                          // D-pad moves over the buttons, A presses, RB or Back leaves
      if (r.gear || r.map) m.setOpen(false); else { if (r.nav) m.nav(r.nav); if (r.navY) m.nav(r.navY); if (r.confirm) m.press(); }
      return;
    }
    if (r.gear) { toggleGear(); return; }
    if (minimap.isOpen) { if (r.map || r.confirm) minimap.setOpen(false); return; }               // the big map covers the screen: any pad press that is not a move closes it, so it can never trap a controller
    if (state.shop && r.map) { I.shopClose = true; return; }                                         // Back leaves the shop
    if (r.map) { minimap.toggle(); return; }
    if (state.choices || state.classChoices || state.shop) {
      if (r.nav) hud.moveSel(r.nav);
      if (r.navY) hud.moveRow(r.navY);
      const sel = hud.selected();
      if (r.confirm && sel) { if (sel.row === 'class') I.pickClass = sel.index; else I.pick = sel.index; }
    }
    else if (state.over) { if (r.navY) bpFocusOver.move(r.navY); if (r.confirm && !bpFocusOver.press('click')) I.restart = true; }   // up and down walk over the keep and pick buttons, A with none highlighted rises again
    else if (r.confirm) pressPickup();                                                              // A picks up the gun at your feet, or opens the stash chest
  }

  // class picker on the start card (before the first run; a run keeps its class when you rise again)
  const classPick = $('classPick'), classBtns = Array.from(classPick.querySelectorAll('button')), CLASS_IDS = classBtns.map((b) => b.dataset.cls);
  let classSel = 0;
  function chooseClass(i) {
    classSel = (i + CLASS_IDS.length) % CLASS_IDS.length;
    classBtns.forEach((b, j) => b.classList.toggle('sel', j === classSel));
    ref.setCfg({ classId: CLASS_IDS[classSel] }); ref.reset(); state = ref.snapshot();
  }
  classBtns.forEach((b, i) => b.addEventListener('click', () => chooseClass(i)));

  // blueprints: the saved list (kept in this browser), which ones the next run starts with, and keeping stashed things when a run ends
  const bpDesc = () => ({ WP: RefereeWeapons, GR: RefereeGear, cfg: ref.defaults, entry: (i) => ref.stashEntry(i) });
  let bpLib = Blueprints.read(), bpPicked = Blueprints.readPicked().filter((i) => i < bpLib.length), bpKey = '';
  const bpBox = $('bpBox'), bpOver = $('bpOver');
  const bpLoad = () => ref.setLoadout(bpPicked.map((i) => bpLib[i]).filter(Boolean));
  const bpFocusStart = MenuFocus.create(() => $('startLists'), '[data-bp],[data-load],[data-del]', true), bpFocusOver = MenuFocus.create(() => $('overLists'), '[data-keep],[data-bp],[data-load],[data-del]', true);
  const drawStartBp = () => { bpBox.innerHTML = Blueprints.startHtml(bpLib, bpPicked, bpDesc()); bpFocusStart.apply(); };
  function bpToggle(i, resetNow) {
    bpPicked = RefereeStash.pickToggle(bpLib, bpPicked, i); Blueprints.savePicked(bpPicked); bpLoad();
    if (resetNow) { ref.reset(); state = ref.snapshot(); } drawStartBp(); bpKey = '';
  }
  bpBox.addEventListener('click', (e) => { const b = e.target.closest('[data-bp]'); if (b) bpToggle(+b.dataset.bp, true); });
  bpOver.addEventListener('click', (e) => {
    const k = e.target.closest('[data-keep]'), b = e.target.closest('[data-bp]');
    if (k) { const why = RefereeStash.add(bpLib, ref.stashEntry(+k.dataset.keep), RefereeWeapons.GUNS); if (!why) { Blueprints.save(bpLib); toast('Kept as a blueprint'); } else toast('Cannot keep: ' + why); bpKey = ''; drawStartBp(); }
    if (b) bpToggle(+b.dataset.bp, false);
  });
  const drawOverBp = () => {
    const key = state.over ? state.player.stash.items.map((x) => x.i).join() + '|' + bpLib.length + '|' + bpPicked.join() + '|' + Saves.all().length : '';
    if (key === bpKey) return; const was = bpKey; bpKey = key;
    bpOver.innerHTML = state.over ? Blueprints.overHtml(state.player.stash.items, bpLib, bpDesc(), RefereeStash) + (bpLib.length ? Blueprints.startHtml(bpLib, bpPicked, bpDesc()) : '') : '';
    if (!was || !key) bpFocusOver.reset(); else bpFocusOver.apply();
  };
  // saves: written for you in each safe room; Continue goes back to the same map with brand new damage and item seeds
  const rnd = () => (Math.floor(Math.random() * 0x7fffffff)) | 1, newLuck = () => ({ damage: rnd(), item: rnd() });
  const svBox = $('svBox'), svOver = $('svOver');
  const drawSaves = () => { const h = Saves.html(Saves.all()); svBox.innerHTML = h; svOver.innerHTML = Saves.all().length ? h : ''; bpFocusStart.apply(); bpKey = ''; };
  function continueSave(id) {
    const s = Saves.find(id); if (!s) return;
    if (ref.loadData(s.data, newLuck())) { state = ref.snapshot(); StashStore.write(ref.stashList()); if (!started) begin(true); toast('Back at your save with new luck'); }
  }
  const svClick = (e) => { const l = e.target.closest('[data-load]'), d = e.target.closest('[data-del]'); if (l) continueSave(l.dataset.load); if (d) { Saves.remove(d.dataset.del); drawSaves(); } };
  svBox.addEventListener('click', svClick); svOver.addEventListener('click', svClick);
  // saving happens only when you press Save game at the chest in a safe room (never on its own)
  function saveHere() {
    const d = ref.saveData(); if (!d) return coop.mode !== 'off' ? 'saving is off while playing with friends' : 'finish picking your level-up first';
    Saves.add(d, new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric' })); drawSaves();
    return '✔ Saved: Floor ' + d.floor + ' · Wave ' + d.wave;
  }
  ref.setSeeds({ damage: rnd(), item: rnd() });                          // a fresh run: the map seed is already random, and so are the luck seeds
  bpLoad(); drawStartBp(); drawSaves(); ref.reset();   // the first snapshot is taken further down

  const TUNE = [
    ['Movement', null],
    ['Eye height', 'ref', 'eyeStand', 1.2, 2.4, 0.05],
    ['Walk speed', 'ref', 'walkSpeed', 3, 12, 0.1],
    ['Sprint speed', 'ref', 'sprintSpeed', 5, 16, 0.1],
    ['Slide speed', 'ref', 'slideSpeed', 6, 28, 0.5],
    ['Slide time', 'ref', 'slideTime', 0.3, 1.6, 0.05],
    ['Camera', null],
    ['FOV', 'ref', 'fovBase', 50, 100, 1],
    ['FOV aiming', 'ref', 'fovAds', 20, 70, 1],
    ['Mouse sens', 'ref', 'lookSens', 0.0008, 0.006, 0.0001],
    ['Touch sens', 'ref', 'touchSens', 0.002, 0.012, 0.0002],
    ['Stick turn', 'ref', 'padTurn', 1, 8, 0.1],
    ['Gun', null],
    ['Fire rate', 'ref', 'fireRate', 2, 20, 0.5],
    ['Magazine', 'ref', 'magSize', 5, 60, 1],
    ['Reload time', 'ref', 'reloadTime', 0.6, 4, 0.1],
    ['Damage', 'ref', 'damage', 4, 60, 1],
    ['Spread', 'ref', 'spread', 0, 0.1, 0.002],
    ['Gun left/right', 'view', 'gunX', 0, 0.7, 0.01],
    ['Gun up/down', 'view', 'gunY', -0.6, 0, 0.01],
    ['Gun forward', 'view', 'gunZ', -1.1, -0.3, 0.01],
    ['Gun size', 'view', 'gunScale', 0.5, 1.6, 0.05],
    ['Run', null],
    ['Start wave (next new run)', 'ref', 'startWave', 1, 60, 1],
    ['Monsters', null],
    ['Alive in wave 1 (+1 each wave)', 'ref', 'monsterCount', 1, 16, 1],
    ['Size', 'ref', 'monsterScale', 0.6, 2.2, 0.05],
    ['Speed', 'ref', 'monsterSpeed', 1, 8, 0.1],
    ['Health', 'ref', 'monsterHp', 20, 300, 5],
    ['Damage to you', 'ref', 'monsterDamage', 0, 30, 1],
    ['Look', null],
    ['Brightness', 'view', 'brightness', 0.5, 2.4, 0.05],
    ['View distance', 'view', 'fogFar', 15, 70, 1],
    ['Pixel size (lower = chunkier)', 'view', 'pixelH', 150, 540, 10]
  ];
  const panel = $('panel'), panelBody = $('panelBody');
  const sliderEls = {};
  // touch button sizes and show/hide switches sit at the top of the panel (phones only); a hidden toggle button is switched off so it cannot stay stuck on
  const CHEAT = typeof CHEATS !== 'undefined' && CHEATS, noMenu = { sync() {} };   // the Effects and Gun menus exist only in the private cheat build
  const fxSet = !CHEAT ? noMenu : FxPicker.mount(panelBody, view, { save: () => saveTune(), art: fx.art() });
  const skinSet = !CHEAT ? noMenu : GunSkinPicker.mount(panelBody, view, { save: () => saveTune(), set: (id) => gunLook.setSkin(id), inspect: (kind) => startInspect(kind), guns: GunList.LIST.filter((g) => RefereeWeapons.GUNS[g.id]), setGun: (id) => { ref.equipGun(id, view.cheatRarity || 0); state = ref.snapshot(); }, extras: [{ label: 'Drop 5 random gear', fn: () => { for (const sl of ['head', 'chest', 'boots', 'charm', 'charm']) ref.giveGear(sl, 1 + Math.floor(Math.random() * 4)); state = ref.snapshot(); } }, { label: 'Drop 3 gun mods', fn: () => { for (let q = 1; q <= 3; q++) ref.giveMod(q); state = ref.snapshot(); } }, { label: 'Drop legendary gear', fn: () => { for (const sl of ['head', 'chest', 'boots', 'charm', 'charm']) ref.giveGear(sl, 4); state = ref.snapshot(); } }, { label: '+1000 gold', fn: () => { ref.giveGold(1000); state = ref.snapshot(); } }, { label: 'Safe room (wave 11)', fn: () => { ref.setCfg({ startWave: 11, startSafe: true }); ref.reset(); ref.setCfg({ startWave: startWaveFromLink, startSafe: safeFromLink }); state = ref.snapshot(); } }], setRarity: (r) => { ref.equipGun(ref.snapshot().player.gun.id, r); state = ref.snapshot(); } });
  gunChanged = () => skinSet.sync();
  const wallSet = WallSkin.mount(panelBody, view, WallSkin.create(texStone), { save: () => saveTune() });
  const touchSet = TouchLayout.mount(panelBody, view, { save: () => saveTune(), hid: (id) => {
    if (id === 'ads') { tch.ads = false; bAds.classList.remove('on'); }
    if (id === 'sprint') { tch.sprint = false; bSprint.classList.remove('on'); }
  } });
  function fmt(v, step) { return step < 0.01 ? v.toFixed(4) : step < 0.1 ? v.toFixed(2) : step < 1 ? v.toFixed(1) : String(Math.round(v)); }
  for (const t of TUNE) {
    if (!t[1]) { const h = document.createElement('h3'); h.textContent = t[0]; panelBody.appendChild(h); continue; }
    const [label, tgt, key, mn, mx, st] = t;
    const row = document.createElement('label'); row.className = 'row';
    const name = document.createElement('span'); name.textContent = label;
    const val = document.createElement('output');
    const inp = document.createElement('input'); inp.type = 'range'; inp.min = mn; inp.max = mx; inp.step = st; inp.id = 'tune_' + key;
    const get = () => (tgt === 'ref' ? ref.cfg[key] : view[key]);
    inp.value = get(); val.textContent = fmt(+inp.value, st);
    inp.addEventListener('input', () => {
      const v = parseFloat(inp.value);
      if (tgt === 'ref') ref.setCfg({ [key]: v }); else view[key] = v;
      val.textContent = fmt(v, st);
      if (key === 'pixelH') resize();
      if (key === 'fogFar') { scene.fog.far = v; worldView.setFogFar(v); }
      saveTune();
    });
    row.appendChild(name); row.appendChild(val); row.appendChild(inp); panelBody.appendChild(row);
    sliderEls[key] = { inp, val, tgt, st };
  }
  scene.fog.far = view.fogFar;
  function saveTune() {
    try { localStorage.setItem(LS_KEY, JSON.stringify({ ref: pick(ref.cfg, 'ref'), view })); } catch (e) { /* ignore */ }
  }
  function pick(cfg, tgt) { const o = {}; for (const k in sliderEls) if (sliderEls[k].tgt === tgt && k !== 'startWave') o[k] = cfg[k]; return o; }
  $('tuneReset').addEventListener('click', () => {
    ref.setCfg(Object.assign({}, ref.defaults, GAME_CFG));
    Object.assign(view, { pixelH: 300, brightness: 1, fogFar: 34, sound: 1, fxPreset: 'auto', fxAuto: 1, wallSkin: 'original', gunSkin: 'crimson' }, GUN_DEFAULTS, TouchLayout.DEFAULTS); touchSet.sync(); fxSet.sync(); wallSet.sync(); skinSet.sync();
    for (const k in sliderEls) { const s = sliderEls[k]; s.inp.value = s.tgt === 'ref' ? ref.cfg[k] : view[k]; s.val.textContent = fmt(+s.inp.value, s.st); }
    scene.fog.far = view.fogFar; worldView.setFogFar(view.fogFar); resize(); saveTune();
  });
  $('newRun').addEventListener('click', () => { ref.reset(); togglePanel(); });
  $('tuneCopy').addEventListener('click', () => {
    const txt = JSON.stringify({ ref: pick(ref.cfg, 'ref'), view }, null, 1);
    const ta = $('tuneText'); ta.value = txt; ta.hidden = false; ta.select();
    try { navigator.clipboard.writeText(txt).then(() => { $('tuneCopy').textContent = 'Copied'; setTimeout(() => { $('tuneCopy').textContent = 'Copy settings'; }, 1200); }).catch(() => { /* text is selected instead */ }); } catch (e) { /* text is selected instead */ }
  });
  $('tuneSound').addEventListener('click', () => { view.sound = view.sound ? 0 : 1; $('tuneSound').textContent = view.sound ? 'Sound on' : 'Sound off'; saveTune(); });
  $('tuneSound').textContent = view.sound ? 'Sound on' : 'Sound off';
  // VR has no tuning panel (it needs a mouse): its two useful buttons are on the VR pause menu instead
  const vrSoundLabel = () => { $('vrSound').textContent = 'SOUND: ' + (view.sound ? 'ON' : 'OFF'); };
  $('vrSound').addEventListener('click', () => { $('tuneSound').click(); vrSoundLabel(); }); vrSoundLabel();
  $('vrNewRun').addEventListener('click', () => { if (coop.mode !== 'off') { toast('Leave the room to start over'); return; } ref.reset(); state = ref.snapshot(); if (started) begin(true); });
  function togglePanel() {
    panelOpen = !panelOpen; panel.hidden = !panelOpen;
    if (panelOpen) { if (locked()) document.exitPointerLock(); mouse.fire = mouse.ads = false; }
    else if (started && !isTouch && !noLock) tryLock();
  }
  // the Gear menu: the game pauses while it is open (it borrows the panel's pause flag)
  function menuChange(v) {
    if (v) { if (locked()) document.exitPointerLock(); mouse.fire = mouse.ads = false; panelOpen = true; }
    else { panelOpen = false; if (started && !isTouch && !noLock) tryLock(); }
  }
  const gearMenu = GearMenu.create($, { state: () => state, act: (q) => { const why = q[0] === 'attach' ? ref.attachMod(+q[1], +q[2]) : q[0] === 'detach' ? ref.detachMod(+q[1], +q[2]) : ref.stashItem(q[1], +q[2]); state = ref.snapshot(); return why; }, onChange: (v) => {
    if (v) { if (locked()) document.exitPointerLock(); mouse.fire = mouse.ads = false; panelOpen = true; }
    else { panelOpen = false; if (started && !isTouch && !noLock) tryLock(); }
  } });
  const toggleGear = () => { if (!running || (panelOpen && !gearMenu.isOpen) || stashMenu.isOpen) return; gearMenu.toggle(state); };
  // the stash chest in the safe room: press pick up next to it (when no gun, gear or mod lies in reach) or tap the hint
  const stashMenu = GearMenu.create($, { state: () => state, act: (q) => { if (q[0] === 'save') return saveHere(); const why = q[0] === 'take' ? ref.stashTake(+q[1], +q[2]) : q[0] === 'rename' ? ref.stashRename(+q[1], q[2]) : ref.stashItem(q[1], +q[2], q[3]); state = ref.snapshot(); StashStore.write(ref.stashList()); return why; }, onChange: menuChange }, 'stashMenu', StashMenu.html);
  const stashHint = $('stashHint'); let entryShown = false;
  const openStash = () => { if (running && !panelOpen && state.player.stash.near) stashMenu.setOpen(true, state); };
  stashHint.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); openStash(); });
  // the little box that shows up when you stand at a gold gate or the boss door's puzzle: what it is, and the buttons (the keys E and Z, LB and D-pad down, or a tap)
  const lockBox = $('lockBox'), lockTxt = $('lockTxt'), lockB = [$('lockB0'), $('lockB1')]; let lockKey = '', wasSealed = false;
  lockB.forEach((b, i) => b.addEventListener('pointerdown', (e) => { I.lockUse = i; e.preventDefault(); }));
  function lockHud(lk) {
    const n = lk && lk.near;
    if (lk && lk.sealed !== wasSealed) { wasSealed = lk.sealed; if (wasSealed) toast('The boss door is sealed: solve the puzzle beside it'); }
    if (!n) { if (lockKey) { lockKey = ''; lockBox.classList.remove('show'); } return; }
    const key = n.text + '|' + n.actions.map((a) => a.label + a.afford).join();
    if (key === lockKey) return;
    lockKey = key; lockTxt.textContent = n.text;
    lockB.forEach((b, i) => { const a = n.actions[i]; b.hidden = !a; if (a) { b.textContent = a.label + (isTouch ? '' : i === 0 ? '  [E]' : '  [Z]'); b.classList.toggle('no', !a.afford); } });
    lockBox.classList.add('show');
  }
  // VR grips (xr_interact.js): take that exact item, use what you stand at (gate, door, puzzle, chest), or swap to the gun on your back
  function vrGrab(a) {
    if (!a) return;
    if (a.type === 'item') { I.pickup = true; I.pickupId = a.id; }
    else if (a.type === 'swap') I.swap = true;
    else if (a.type === 'use') { if ((state.locks && state.locks.near) || (state.locks && state.locks.door && state.locks.door.near)) I.lockUse = 0; else if (state.player.stash.near) openStash(); }
  }
  function pressPickup() { if (state.locks && state.locks.near) { I.lockUse = 0; return; } const q = GunCard.nearest(state, 6); if (!(q && q.inReach) && state.player.stash.near) openStash(); else I.pickup = true; }
  $('bGear').addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); toggleGear(); });
  // the Codex: opened from the start card (and so from pause too)
  const codex = Codex.create($, () => ({ D: RefereeData, C: RefereeClasses, WP: RefereeWeapons, AF: RefereeAffixes, GR: RefereeGear, ST: RefereeStash, FX: RefereeGunFx.FX, T: CodexText, cfg: ref.defaults }));
  $('codexBtn').addEventListener('click', () => codex.open());
  $('gear').addEventListener('click', togglePanel);
  $('panelClose').addEventListener('click', togglePanel);
  document.addEventListener('visibilitychange', () => { if (document.hidden && running) setRunning(false); });

  /* ============ per-frame presentation ============ */
  const clock = { last: performance.now() };
  const reloadHold = { t: 0, done: false };
  let equipK = 0, inspK = 0, inspKind = 'sides', kickDir = [0, 0], emberT = 0, flameT = 0, nextInspect = 'sides';
  const startInspect = (kind) => { if (running && inspK === 0 && !state.over && !state.player.reloading) { inspKind = kind || nextInspect; nextInspect = inspKind === 'sides' ? 'mag' : 'sides'; inspK = 0.0001; } };
  let bob = 0, kickG = 0, flashT = 0, sway = 0, roll = 0, lastSlideK = 0;
  const gunHip = new THREE.Vector3(), gunAds = new THREE.Vector3();
  function ejectShell() {
    gunBody.localToWorld(shellV.set(0.09, 0.07, -0.05));
    const q = parts[partCursor++ % parts.length], e = camera.matrixWorld.elements;
    q.m.visible = true; q.m.position.copy(shellV); q.m.material.color.setHex(0xe0b050); q.m.scale.setScalar(0.7);
    q.v.set(e[0] * 2.4 + e[4] * 1.8 + e[8] * 0.4 + (Math.random() - 0.5) * 0.6, e[1] * 2.4 + e[5] * 1.8 + e[9] * 0.4, e[2] * 2.4 + e[6] * 1.8 + e[10] * 0.4 + (Math.random() - 0.5) * 0.6);
    q.life = 0.8; q.grav = 14;
  }

  function bigShake(a) { if (a > shakeAmp * 0.5) { shakeAmp = a; shakeT = 0.22; } }
  function handleEvents(events) {
    for (const e of events) {
      hud.event(e);
      if (e.type === 'shot') {
        if (!e.extra && xr && xr.presenting()) xr.shotFx();   // VR: the gun kicks in your hand and springs back, with a buzz that fits the gun (xr_feel.js)
        if (!e.extra) { flashT = 0.06; kickG = 1; kickDir = [Math.random() * 2 - 1, Math.random() * 2 - 1]; inspK = 0; sfx('shot'); ejectShell(); if (fxOn()) { muzzle.getWorldPosition(tmpV); if (xr && xr.presenting()) xr.aimDir(tmpV2); else camera.getWorldDirection(tmpV2); fx.play(fxId(), 'muzzle', tmpV.x + tmpV2.x * 0.12, tmpV.y + tmpV2.y * 0.12, tmpV.z + tmpV2.z * 0.12); } }
        addTracer(e.ex, e.ey, e.ez);
        if (e.hit === 'wall') { burst(e.ex, e.ey, e.ez, 5, [0xffb347, 0xff7a1a, 0x888078], 4, 0.35, 12, 0.7); if (fxOn()) fx.play(fxId(), 'wall', e.ex, e.ey, e.ez); }
      } else if (e.type === 'peerShot') {
        if (e.key !== coopKey) friendShot(e);
      } else if (e.type === 'hit') {
        if (xr && xr.presenting()) xr.hitFx(e.x, e.y, e.z, e.crit);   // feel the hit land, and a hit marker on it (VR has no screen crosshair)
        burst(e.x, e.y, e.z, e.crit ? 9 : 5, [0xb01818, 0x701010, 0xe03030], 3.5, 0.4, 10, 0.8);
        if (fxOn() && !e.splash) fx.play(fxId(), 'flesh', e.x, e.y, e.z, { crit: e.crit });
        if (!e.splash) damageNumber(e.x, e.y + 0.2, e.z, e.dmg, e.crit);
        hitT = 0.14; hitKill = false; sfx(e.crit ? 'crit' : 'hit');
      } else if (e.type === 'kill') {
        hitT = 0.28; hitKill = true; sfx('kill'); if (xr && xr.presenting()) xr.hitMark(e.x, 1.2 * e.scale, e.z, 'kill');
        const en = mons.get(e.id);
        if (en) { mons.delete(e.id); dropBadges(en); dying.push({ en, t: 0 }); }
        burst(e.x, 1.2 * e.scale, e.z, e.boss ? 40 : 24, [0xb01818, 0x701010, 0x3a0a0a, 0xff6a20], 5, 0.8, 11, e.boss ? 2 : 1.3);
        if (fxOn()) { fx.play(fxId(), 'kill', e.x, 1.2 * e.scale, e.z, { scale: e.scale, boss: e.boss }); bigShake(FxPlan.shake(fxId(), 'kill') * (e.boss ? 1.6 : 1)); }
      } else if (e.type === 'blast') { burst(e.x, e.y, e.z, 10, [0xff9a1c, 0xff4500, 0xffd060], 5, 0.4, 4, 1.1); sfx('blast'); if (fxOn()) { fx.play(fxId(), 'blast', e.x, e.y, e.z, { r: e.r }); bigShake(FxPlan.shake(fxId(), 'blast')); } }
      else if (e.type === 'playerHit') { sfx('hurt'); if (xr && xr.presenting()) { xr.pulse('left', 0.8, 90); xr.pulse('right', 0.8, 90); } }
      else if (e.type === 'slide') { sfx('slide'); }
      else if (e.type === 'jump') { sfx('slide'); }
      else if (e.type === 'hop') { sfx('slide'); }
      else if (e.type === 'secondWind') { sfx('levelup'); toast('Second Wind! You cling to life'); }
      else if (e.type === 'overcharge') { sfx('crit'); }
      else if (e.type === 'bounceSlam') { sfx('blast'); }
      else if (e.type === 'gateOpen') { sfx('levelup'); toast(e.key ? 'Key used: gate unlocked' : 'Gate unlocked'); }
      else if (e.type === 'keyTaken') { sfx('levelup'); toast('You took the Keeper\'s key: find the key gate'); }
      else if (e.type === 'keeperWake') { sfx('hurt'); toast('The Key Keeper wakes!'); }
      else if (e.type === 'lockSolved') { sfx('levelup'); toast('Puzzle solved: the boss door can open'); }
      else if (e.type === 'socket') { sfx('orb'); toast('Gold socket hit'); }
      else if (e.type === 'panAdd' || e.type === 'panTake' || e.type === 'spin') { sfx('pickup'); }
      else if (e.type === 'shoot') { sfx(e.proj === 'bolt' ? 'zap' : e.proj === 'spit' ? 'spit' : 'fireball'); }
      else if (e.type === 'projHit') { burst(e.x, e.y, e.z, e.proj === 'fire' ? 12 : 7, e.proj === 'spit' ? [0x9cff4a, 0x4fd02a, 0x2a6a18] : e.proj === 'bolt' ? [0xeaffff, 0x6fd8ff, 0xffffff] : [0xffe070, 0xff5a14, 0xc8260c], 4, 0.4, 6, 0.8); if (e.onPlayer) sfx('hurt'); }
      else if (e.type === 'status') { const S = STATUS[e.kind]; statusPulse.set(e.id, { kind: e.kind, t: 0.4 }); burst(e.x, e.y + 0.3, e.z, 10, S && S.burst ? S.burst : e.kind === 'poison' ? [0xb45cff, 0x7a2cc8, 0xe0b8ff] : e.kind === 'bleed' ? [0xe23a42, 0x8a1018] : [0xf0c860, 0xfff0b0], 3.5, 0.5, 2, 0.9); }
      else if (e.type === 'cloakStart') { sfx('cloak'); }
      else if (e.type === 'ultStart') { sfx('boss'); bigShake(0.12); }
      else if (e.type === 'skillLevel' || e.type === 'skillNew') { sfx('levelup'); }
      else if (e.type === 'ricochet') { addTracer(e.x1, e.y1, e.z1); burst(e.x1, e.y1, e.z1, 4, [0xffe070, 0xffb347], 3, 0.3, 8, 0.6); }
      else if (e.type === 'arc') { for (let i = 0; i <= 6; i++) { const k = i / 6; burst(e.x1 + (e.x2 - e.x1) * k, e.y1 + (e.y2 - e.y1) * k + (Math.random() - 0.5) * 0.3, e.z1 + (e.z2 - e.z1) * k, 1, [0xffe82a, 0xfff6a0], 1.5, 0.25, 0, 0.5); } sfx('orb'); }
      else if (e.type === 'radPulse') { burst(e.x, 0.6, e.z, 18, [0x5cff3a, 0xb8ff90, 0x2a9a1a], e.r * 1.6, 0.5, 0, 1); }
      else if (e.type === 'freeze') { burst(e.x, 1, e.z, 16, [0xc8ecff, 0x7ac8ff, 0xffffff], 3, 0.6, 2, 0.9); }
      else if (e.type === 'plague') { burst(e.x, 1, e.z, 14, [0xb45cff, 0x7a2cc8, 0xe0b8ff], 4, 0.6, 3, 1); }
      else if (e.type === 'raise') { burst(e.x, 1, e.z, 14, [0x6fe08a, 0x2a6a40, 0xc8ffd8], 4, 0.7, -2, 1); sfx('orb'); }
      else if (e.type === 'eliteBlast') { burst(e.x, 1, e.z, 16, [0x9cff4a, 0xffe070, 0xff5a14], 6, 0.5, 4, 0.9); sfx('fireball'); }
      else if (e.type === 'orb') { sfx('orb'); }
      else if (e.type === 'pickup' || e.type === 'skill') { sfx('pickup'); }
      else if (e.type === 'modPickup') { sfx('pickup'); toast(RefereeWeapons.RARITIES[e.rarity].name + ' gun mod in your bag (G to fit it)'); }
      else if (e.type === 'bagFull') { toast('Mod bag is full (6) - fit or drop one first'); }
      else if (e.type === 'gearPickup') { sfx('pickup'); toast(RefereeWeapons.RARITIES[e.rarity].name + ' ' + e.slot + ' on'); }
      else if (e.type === 'gunPickup' || e.type === 'swap') { sfx('pickup'); equipK = 0; if (e.type === 'gunPickup') toast(RefereeWeapons.RARITIES[e.rarity].name + ' ' + RefereeWeapons.GUNS[e.id].name); }
      else if (e.type === 'levelUp') { sfx('levelup'); }
      else if (e.type === 'waveStart') { sfx(e.boss ? 'boss' : 'wave'); }
      else if (e.type === 'bossSummon') { sfx('boss'); }
      else if (e.type === 'bossBlink') { burst(e.x, 1.5, e.z, 14, [0xa050ff, 0xf0dcff], 5, 0.5, 4, 0.9); burst(e.x2, 1.5, e.z2, 14, [0xa050ff, 0xf0dcff], 5, 0.5, 4, 0.9); sfx('blast'); }
      else if (e.type === 'bossNova' || e.type === 'bossSlam') { burst(e.x, 0.6, e.z, 18, e.type === 'bossNova' ? [0xa050ff, 0xf0dcff] : [0xff8a2a, 0xffe070], 7, 0.5, 4, 0.9); sfx('blast'); }
      else if (e.type === 'bossBreath') { sfx('fireball'); }
      else if (e.type === 'bossStrike') { burst(e.x, 0.5, e.z, 14, VariantLook.BURST[e.fx] || [0xa050ff, 0xf0dcff], 6, 0.5, 3.5, 0.8); sfx('blast'); }
      else if (e.type === 'ailment') { sfx('hurt'); toast(e.kind === 'burn' ? 'You are burning! Slide to put it out' : e.kind === 'freeze' ? 'Frozen! You move slower' : 'Poisoned! No healing until it wears off'); }
      else if (e.type === 'bossDive' || e.type === 'bossDrain') { sfx(e.type === 'bossDive' ? 'boss' : 'pickup'); }
      else if (e.type === 'dead') { diedT = 1.4; sfx('dead'); rlPrev = 0; }
      else if (e.type === 'down') { diedT = 0.9; sfx('dead'); toast('You are down - a friend standing close brings you back'); }
      else if (e.type === 'revived') { sfx('levelup'); toast('Back on your feet'); }
      else if (e.type === 'restart') { sandboxGiven = -1; setTimeout(sandboxGifts, 0); diedT = 0; rlPrev = 0; equipK = 0; inspK = 0; fx.clear(); }
      else if (e.type === 'reloadStart') { rlPrev = 0; }
    }
  }

  const ELITE_GLOW = { armored: [0.12, 0.2, 0.38], swift: [0.4, 0.34, 0.02], brutal: [0.42, 0.06, 0.03], volatile: [0.1, 0.42, 0.06], keeper: [0.5, 0.38, 0.04] };   // look only
  function eliteGlow(list, t) {
    if (!list || !list.length) return [0, 0, 0];
    const k = 0.75 + 0.25 * Math.sin(t * 5), n = list.length, o = [0, 0, 0];
    for (const id of list) { const g = ELITE_GLOW[id]; o[0] += g[0] / n; o[1] += g[1] / n; o[2] += g[2] / n; }
    return [o[0] * k, o[1] * k, o[2] * k];
  }
  // the dead the Witch raised: the monster's own shape, tinted green and a little see-through
  // status effects, shown on the monster the way Crusader Tactics does: a coloured glow on the body and a badge over the head
  const STATUS = {
    poison: { col: [0.36, 0.08, 0.55], css: '#b45cff', flag: 'poisoned', gx: 'toxic' },
    bleed: { col: [0.42, 0.03, 0.04], css: '#e23a42', flag: 'bleeding' },
    hex: { col: [0.42, 0.34, 0.05], css: '#f0c860', flag: 'cursed' },
    // gun statuses (the gun's colour): the referee sends these under m.gx
    burn: { col: [0.55, 0.2, 0.02], css: '#ff6a1a', gx: 'burning', burst: [0xff8a1c, 0xff4500, 0xffd060] },
    chill: { col: [0.05, 0.25, 0.5], css: '#4aa8ff', gx: 'chilled', burst: [0x7ac8ff, 0xc8ecff, 0x3a88e0] },
    shock: { col: [0.5, 0.45, 0.02], css: '#ffe82a', gx: 'shocked', burst: [0xffe82a, 0xfff6a0] },
    rad: { col: [0.12, 0.5, 0.08], css: '#5cff3a', gx: 'irradiated', burst: [0x5cff3a, 0xb8ff90, 0x2a9a1a] },
    wither: { col: [0.05, 0.02, 0.1], css: '#8a6aa8', gx: 'withered', burst: [0x3a2a52, 0x8a6aa8, 0x120818] },
    smite: { col: [0.5, 0.5, 0.45], css: '#fff6d8', gx: 'smitten', burst: [0xfff6d8, 0xffffff, 0xffe8a0] }
  };
  const hasStatus = (m, k) => !!((STATUS[k].flag && m[STATUS[k].flag]) || (STATUS[k].gx && m.gx && m.gx[STATUS[k].gx]));
  const statusPulse = new Map();                                                // monster id -> { kind, t } for the burst when a status first lands
  function statusGlow(m, t) {
    const o = [0, 0, 0], p = statusPulse.get(m.id), br = 0.7 + 0.3 * Math.sin(t * 7 + m.id);
    for (const k in STATUS) if (hasStatus(m, k)) { const c = STATUS[k].col; o[0] += c[0] * br; o[1] += c[1] * br; o[2] += c[2] * br; }
    if (p) { const c = STATUS[p.kind].col, k = p.t / 0.4; o[0] += c[0] * 1.6 * k; o[1] += c[1] * 1.6 * k; o[2] += c[2] * 1.6 * k; }
    return o;
  }
  const badgeTex = {};
  function badgeTexture(kind) {                                                 // a small round icon drawn once: droplet (bleed), skull (poison), rune (hex)
    if (badgeTex[kind]) return badgeTex[kind];
    const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'), col = STATUS[kind].css;
    g.fillStyle = 'rgba(8,4,6,0.85)'; g.beginPath(); g.arc(32, 32, 29, 0, 7); g.fill();
    g.strokeStyle = col; g.lineWidth = 4; g.beginPath(); g.arc(32, 32, 27, 0, 7); g.stroke();
    g.fillStyle = col; g.strokeStyle = col; g.lineWidth = 4; g.lineCap = 'round';
    if (kind === 'bleed') { g.beginPath(); g.moveTo(32, 12); g.bezierCurveTo(46, 30, 46, 46, 32, 50); g.bezierCurveTo(18, 46, 18, 30, 32, 12); g.fill(); }
    else if (kind === 'poison') { g.beginPath(); g.arc(32, 28, 14, 0, 7); g.fill(); g.fillRect(24, 36, 16, 12); g.fillStyle = '#10060c'; g.beginPath(); g.arc(26, 29, 4, 0, 7); g.arc(38, 29, 4, 0, 7); g.fill(); g.fillRect(30, 38, 4, 7); }
    else if (kind === 'burn') { g.beginPath(); g.moveTo(32, 10); g.bezierCurveTo(48, 28, 46, 48, 32, 52); g.bezierCurveTo(18, 48, 16, 30, 28, 22); g.bezierCurveTo(28, 30, 34, 30, 32, 10); g.fill(); }
    else if (kind === 'chill') { for (let i = 0; i < 3; i++) { const a = i * Math.PI / 3; g.beginPath(); g.moveTo(32 + Math.cos(a) * 19, 32 + Math.sin(a) * 19); g.lineTo(32 - Math.cos(a) * 19, 32 - Math.sin(a) * 19); g.stroke(); } }
    else if (kind === 'shock') { g.beginPath(); g.moveTo(36, 10); g.lineTo(20, 35); g.lineTo(30, 35); g.lineTo(26, 54); g.lineTo(44, 27); g.lineTo(34, 27); g.closePath(); g.fill(); }
    else if (kind === 'rad') { g.beginPath(); g.arc(32, 32, 5, 0, 7); g.fill(); for (let i = 0; i < 3; i++) { const a = i * 2 * Math.PI / 3 - Math.PI / 2; g.beginPath(); g.arc(32, 32, 18, a - 0.5, a + 0.5); g.stroke(); } }
    else if (kind === 'wither') { g.beginPath(); g.arc(32, 32, 17, 0.7, 5.6); g.stroke(); g.beginPath(); g.arc(37, 29, 13, 0.9, 5.4); g.stroke(); }
    else if (kind === 'smite') { g.beginPath(); g.arc(32, 32, 8, 0, 7); g.fill(); for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; g.beginPath(); g.moveTo(32 + Math.cos(a) * 13, 32 + Math.sin(a) * 13); g.lineTo(32 + Math.cos(a) * 21, 32 + Math.sin(a) * 21); g.stroke(); } }
    else { g.beginPath(); for (let i = 0; i < 5; i++) { const a = -Math.PI / 2 + i * 4 * Math.PI / 5; g.lineTo(32 + Math.cos(a) * 18, 33 + Math.sin(a) * 18); } g.closePath(); g.stroke(); g.beginPath(); g.arc(32, 33, 4, 0, 7); g.fill(); }
    return (badgeTex[kind] = new THREE.CanvasTexture(c));
  }
  const badgeMats = {}, badgeTop = {};
  function badgeMat(kind) { return badgeMats[kind] || (badgeMats[kind] = new THREE.SpriteMaterial({ map: badgeTexture(kind), transparent: true, fog: false })); }
  function badgeHeight(kind) {                                                  // head top for this monster kind, in model units (cached)
    if (badgeTop[kind] === undefined) { let y = 0; for (const sp of ref.kinds[kind].spheres) y = Math.max(y, sp.y + sp.r); badgeTop[kind] = y + (ref.kinds[kind].hover || 0); }
    return badgeTop[kind];
  }
  function statusBadges(en, m, st) {
    const kinds = Object.keys(STATUS).filter((k) => hasStatus(m, k));
    if (!kinds.length && !en.badges) return;
    if (!en.badges) en.badges = {};
    const yaw = st.player.yaw, rx = Math.cos(yaw), rz = Math.sin(yaw), top = badgeHeight(m.kind) * m.scale + 0.45, sz = Math.max(0.5, m.scale * 0.42);
    let i = 0;
    for (const k in STATUS) {
      let b = en.badges[k];
      const on = kinds.includes(k);
      if (on && !b) { b = en.badges[k] = new THREE.Sprite(badgeMat(k)); scene.add(b); }
      if (!b) continue;
      b.visible = on;
      if (!on) continue;
      const off = (i - (kinds.length - 1) / 2) * sz * 1.05; i++;
      b.position.set(m.x + rx * off, top, m.z + rz * off); b.scale.setScalar(sz * (1 + 0.08 * Math.sin(st.t * 6 + i)));
    }
  }
  // fog waves: monsters show two glowing red eyes (drawn through the fog) so you can tell where they are before you can see them
  const eyeMat = new THREE.SpriteMaterial({ map: glowTex, color: 0xff3a2a, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, transparent: true });
  function monsterEyes(en, m, st) {
    const k = st.fog.k;
    if (k < 0.02 && !en.eyes) return;
    if (!en.eyes) { en.eyes = [new THREE.Sprite(eyeMat), new THREE.Sprite(eyeMat)]; for (const e of en.eyes) scene.add(e); }
    const dist = Math.hypot(m.x - st.player.x, m.z - st.player.z), on = k >= 0.02 && dist < 46;
    const fx = Math.sin(m.yaw), fz = -Math.cos(m.yaw), rx = Math.cos(m.yaw), rz = Math.sin(m.yaw), y = badgeHeight(m.kind) * 0.8 * m.scale, sz = Math.max(0.28, 0.24 * m.scale);
    en.eyes.forEach((e, i) => {
      e.visible = on; if (!on) return;
      const side = i ? 1 : -1;
      e.position.set(m.x + fx * 0.3 * m.scale + rx * side * 0.13 * m.scale, y, m.z + fz * 0.3 * m.scale + rz * side * 0.13 * m.scale);
      e.scale.setScalar(sz * (0.85 + 0.15 * Math.sin(st.t * 5 + m.id)));
    });
    if (on) eyeMat.opacity = Math.min(1, k * 1.3);
  }
  function dropBadges(en) {
    if (en.badges) { for (const k in en.badges) scene.remove(en.badges[k]); en.badges = null; }
    if (en.eyes) { for (const e of en.eyes) scene.remove(e); en.eyes = null; }
  }
  const thrallMons = new Map();
  function syncThralls(st) {
    const seen = new Set();
    for (const th of (st.cls && st.cls.thralls) || []) {
      seen.add(th.id);
      let en = thrallMons.get(th.id);
      if (!en) { en = RIGS.build(th.kind); en.skin.transparent = true; en.skin.opacity = 0.7; thrallMons.set(th.id, en); scene.add(en.root); }
      en.root.position.set(th.x, (ref.kinds[th.kind].hover || 0) * th.scale, th.z); en.root.rotation.y = -th.yaw; en.root.scale.setScalar(th.scale * MODEL);
      RIGS.animate(en, { id: th.id, state: 'chase', phase: st.t * 7 + th.id, atkK: 0, castK: 0 }, st.t);
      const pulse = 0.28 + 0.1 * Math.sin(st.t * 6 + th.id);
      en.skin.emissive.setRGB(0.05, pulse, 0.12); en.skin.opacity = 0.35 + 0.4 * Math.min(1, th.k * 4);
    }
    for (const [id, en] of thrallMons) if (!seen.has(id)) { scene.remove(en.root); thrallMons.delete(id); }
  }
  function syncMonsters(st, dt) {
    const seen = new Set();
    for (const m of st.monsters) {
      seen.add(m.id);
      let en = mons.get(m.id);
      if (!en) { en = RIGS.build(m.kind); mons.set(m.id, en); scene.add(en.root); }
      en.root.position.set(m.x, (ref.kinds[m.kind].hover || 0) * m.scale, m.z); en.root.rotation.y = -m.yaw; en.root.scale.setScalar(m.scale * MODEL);
      RIGS.animate(en, m, st.t);
      const lt = smoothLight(m.x, m.z), f = clamp(m.flash / 0.12, 0, 1), warn = m.state === 'windup' ? 0.35 + 0.25 * Math.sin(st.t * 30) : (m.castK > 0 ? 0.12 + 0.3 * m.castK : m.atkK > 0.4 ? 0.2 * m.atkK : 0) + (m.enraged ? 0.14 + 0.08 * Math.sin(st.t * 9) : 0);   // an enraged boss glows red
      const ge = eliteGlow(m.elite, st.t);                                    // elites glow the colour of their abilities
      const sf = statusGlow(m, st.t), vg = VariantLook.glow(m, st.t);          // poison glows purple, bleed red, hex gold; a fresh hit pulses; variants glow their element, an open boss glows gold
      sf[0] += vg[0]; sf[1] += vg[1]; sf[2] += vg[2];
      en.skin.emissive.setRGB(Math.max(0, (lt[0] - 0.14)) * 0.22 + f * 0.7 + warn + ge[0] + sf[0], Math.max(0, (lt[1] - 0.1)) * 0.12 + f * 0.35 + ge[1] + sf[1], f * 0.3 + ge[2] + sf[2]);
      statusBadges(en, m, st); monsterEyes(en, m, st);
    }
    for (const [id, en] of mons) if (!seen.has(id)) { scene.remove(en.root); dropBadges(en); mons.delete(id); }
    for (const [id, p] of statusPulse) { p.t -= dt; if (p.t <= 0) statusPulse.delete(id); }
    for (let i = dying.length - 1; i >= 0; i--) {
      const d = dying[i]; d.t += dt;
      const k = d.t / 0.55;
      if (k >= 1) { scene.remove(d.en.root); dying.splice(i, 1); continue; }
      d.en.root.rotation.x = k * 1.5; d.en.root.position.y = -k * 0.4;
      d.en.skin.emissive.setRGB(0.6 * (1 - k), 0.15 * (1 - k), 0.05 * (1 - k));
    }
  }

  // the Assassin's cloak: gun and hands glow white (the same white glow as Crusader Tactics) so you can tell monsters cannot see you
  let cloakK = 0;
  const WHITE = new THREE.Color(1, 1, 1), GUN_EM = new THREE.Color(0x1c0c0c), GLOVE_EM = new THREE.Color(0x1a100c);
  function cloakGlow(st, dt) {
    const c = st.cls && st.cls.cloak, want = c ? (c.k < 0.5 ? 0.45 + 0.55 * (Math.sin(st.t * 24) > 0 ? 1 : 0.2) * c.k * 2 : 1) : 0;   // blinks in the last half second
    cloakK += (want - cloakK) * Math.min(1, dt * 10 + 0.0001);
    const k = Math.min(1, cloakK * 0.85);
    gunLook.gunMat.emissive.copy(GUN_EM).lerp(WHITE, k);
    gloveMat.emissive.copy(GLOVE_EM).lerp(WHITE, k);
    gunLook.glowMat.color.lerp(WHITE, k);
    cloakVeil.classList.toggle('on', cloakK > 0.3);
  }
  const cloakVeil = $('cloakVeil');
  const camWorld = new THREE.Vector3(); const camEye = new THREE.Vector3();
  function updateView(st, dt, time) {
    const p = st.player;
    const inVr = !!(xr && xr.presenting());
    if (inVr) xr.headPose(); else camera.position.set(p.x, p.eye, p.z);   // in VR the headset places the camera
    const planar = clamp(p.speed / 6, 0, 1.6);
    bob += dt * (p.sprinting ? 13 : 9) * (p.speed > 0.5 ? 1 : 0) * (p.sliding ? 0 : 1);
    const bobAmt = (p.sliding ? 0 : planar) * (1 - p.adsT * 0.7);
    const strafe = (p.vx * Math.cos(p.yaw) + p.vz * Math.sin(p.yaw)) / 8;
    roll += ((p.sliding ? 0.09 : -strafe * 0.025) - roll) * Math.min(1, dt * 10);
    if (!inVr) camera.rotation.set(p.pitch + Math.sin(bob * 2) * 0.0035 * bobAmt, -p.yaw, roll);
    if (!inVr) camera.position.y += Math.abs(Math.sin(bob)) * 0.05 * bobAmt;
    if (shakeT > 0 && inVr) shakeT = 0;                            // no camera shake or bob in a headset (sickness)
    if (shakeT > 0) { shakeT = Math.max(0, shakeT - dt); const k = shakeAmp * (shakeT / 0.22); camera.position.x += (Math.random() - 0.5) * k; camera.position.y += (Math.random() - 0.5) * k; if (shakeT === 0) shakeAmp = 0; }
    if (Math.abs(camera.fov - p.fov) > 0.01) { camera.fov = p.fov; camera.updateProjectionMatrix(); }

    // gun pose
    kickG = Math.max(0, kickG - dt * 14);
    const sp = p.sprintK, ad = p.adsT, sl = p.sliding ? 1 : 0;
    const rl = animateReload(p);
    const gs = view.gunScale;
    gunHip.set(view.gunX, view.gunY + (HIP_DOT.y - SIGHT.y) * gs, view.gunZ + (HIP_DOT.z - SIGHT.z) * gs);   // every gun rests with its sight where the rifle's sits, so short guns are not lost below the screen
    gunAds.set(0, -SIGHT.y * gs, -EYE_RELIEF - SIGHT.z * gs);   // puts the sight window dead centre
    const still = clamp(1 - planar, 0, 1) * (1 - sp) * (1 - sl);
    // hold Reload for 2 seconds with a full magazine: gun inspect (keyboard R, the touch Reload button, or the controller X button)
    const pr = currentPad(), rHeld = !!keys.KeyR || tch.reload || !!(pr && pr.reloadHeld);
    if (GunMotion.holdStep(reloadHold, dt, rHeld, running && p.ammo >= p.magSize && !p.reloading && !state.over && inspK === 0)) startInspect();
    if (equipK < 1) equipK = Math.min(1, equipK + dt / 0.7);
    if (inspK > 0) { inspK += dt / GunMotion.LENGTH[inspKind]; if (inspK >= 1 || p.reloading || p.sprintK > 0.2 || p.adsT > 0.15 || flashT > 0.04) inspK = 0; }
    if (gunLook.skin().flame && running) {      // fire licks along the gun and streams back past you the faster you run
      flameT -= dt; const rate = GunSkins.flameRate(gunLook.skin(), planar);
      if (flameT <= 0) {
        flameT = 1 / rate; camera.getWorldDirection(tmpV2); tmpV.set(0, 0.02, -0.15 - Math.random() * 0.55); gunBody.localToWorld(tmpV);
        const p0 = parts[partCursor++ % parts.length], back = 0.4 + planar * 2.4;
        p0.m.visible = true; p0.m.position.copy(tmpV); p0.m.material.color.setHex([0xff2a10, 0xff6a1a, 0xffb040][(Math.random() * 3) | 0]);
        p0.m.scale.setScalar(0.3 + Math.random() * 0.5); p0.v.set(-tmpV2.x * back + (Math.random() - 0.5) * 0.4, 0.5 + Math.random() * 0.7, -tmpV2.z * back + (Math.random() - 0.5) * 0.4);
        p0.life = 0.3 + Math.random() * 0.25 + planar * 0.15; p0.grav = -0.8;
      }
    }
    if (gunLook.skin().embers && running) { emberT -= dt; if (emberT <= 0) { emberT = 0.07; muzzle.getWorldPosition(tmpV); burst(tmpV.x + (Math.random() - 0.5) * 0.5, tmpV.y + (Math.random() - 0.3) * 0.1, tmpV.z + (Math.random() - 0.5) * 0.5, 1, [0xff6a1a, 0xff3a10, 0xffb040], 0.5, 0.7, -1.5, 0.35); } }
    const mo = GunMotion.add(GunMotion.add(GunMotion.kick(kickG, ad, kickDir), GunMotion.idle(time, still, ad)), GunMotion.add(GunMotion.equip(equipK), GunMotion.inspect(inspKind, inspK)));
    charge.position.z += GunMotion.bolt(kickG, 0.04);
    const gx = lerp(gunHip.x, gunAds.x, ad) - sp * 0.1 - sl * 0.05 + Math.sin(bob) * 0.012 * bobAmt + rl.px + mo.px;
    const gy = lerp(gunHip.y, gunAds.y, ad) - sp * 0.07 + Math.abs(Math.cos(bob)) * 0.012 * bobAmt - sl * 0.06 + rl.py + mo.py;
    const gz = lerp(gunHip.z, gunAds.z, ad) + sp * 0.05 + rl.pz + mo.pz;
    gun.position.set(gx, gy, gz);
    gun.scale.setScalar(gs);
    gun.rotation.set(
      -sp * 0.42 + sl * 0.08 + rl.rx + mo.rx,
      lerp(0.05, 0, ad) + sp * 0.5 + sl * 0.12 + rl.ry + mo.ry,
      sp * 0.22 + sl * 0.3 + Math.sin(bob) * 0.012 * bobAmt + rl.rz + mo.rz
    );
    gunLook.update(time, flashT / 0.06, running ? planar : 0);
    cloakGlow(st, dt);
    // muzzle flash
    flashT = Math.max(0, flashT - dt);
    flashMesh.visible = flashT > 0;
    if (flashT > 0) { flashMesh.rotation.z = Math.random() * 3; flashMesh.scale.setScalar(0.8 + Math.random() * 0.6); }
    muzzleLight.intensity = flashT > 0 ? 2.2 : 0;

    // world brightness: flicker + muzzle flash
    const fl = 1 + 0.035 * Math.sin(time * 17) + 0.025 * Math.sin(time * 31 + 1.3), fb = flashT / 0.06;
    const br = view.brightness * fl;
    const vrNow = !!(xr && xr.presenting()); if (vrNow) camEye.set(st.player.x, st.player.eye, st.player.z);   // the glow quads face your eye (the player's eye point; the head is within a step of it)
    worldView.update(time, camera.getWorldPosition(camWorld), dt, br, fb, st.door.open, vrNow && !window.__noInst, vrNow ? camEye : null);   // VR: torches drawn instanced (Quest draw calls); window.__noInst = true turns it off (to compare)
    locksView.sync(st.locks, ref.map, time, dt); lockHud(st.locks);
    scene.fog.far = view.fogFar * st.fog.mul; fogGlow.intensity = 1.7 * st.fog.k;   // a fog wave shrinks the view, and your gun lights a small circle around you

    // particles, tracers, damage numbers
    for (const q of parts) {
      if (!q.m.visible) continue;
      q.life -= dt; if (q.life <= 0) { q.m.visible = false; continue; }
      q.v.y -= q.grav * dt; q.m.position.addScaledVector(q.v, dt);
      if (q.m.position.y < 0.05) { q.m.position.y = 0.05; q.v.y *= -0.3; q.v.x *= 0.6; q.v.z *= 0.6; }
    }
    for (const t of tracers) { if (!t.m.visible) continue; t.life -= dt; if (t.life <= 0) t.m.visible = false; else t.m.material.opacity = t.life / t.dur * 0.9; }
    camera.updateMatrixWorld(true);
    fx.update(dt);
    for (const n of dnPool) {
      if (n.d.hidden) continue;
      n.life -= dt; if (n.life <= 0) { n.d.hidden = true; continue; }
      n.y += dt * 0.9;
      tmpV.set(n.x, n.y, n.z).project(camera);
      if (tmpV.z > 1) { n.d.hidden = true; continue; }
      n.d.style.transform = 'translate(' + ((tmpV.x * 0.5 + 0.5) * window.innerWidth) + 'px,' + ((-tmpV.y * 0.5 + 0.5) * window.innerHeight) + 'px) translate(-50%,-50%)';
      n.d.style.opacity = clamp(n.life / 0.3, 0, 1);
    }

    // HUD
    if (st.kills !== lastKills) { elKills.textContent = st.kills; lastKills = st.kills; elKills.classList.remove('pop'); void elKills.offsetWidth; elKills.classList.add('pop'); }
    elHpFill.style.width = (clamp(p.hp / p.maxHp, 0, 1) * 100) + '%';
    elHurt.style.opacity = clamp(p.hurt / 0.3, 0, 1) * 0.85 + (p.hp < p.maxHp * 0.3 ? 0.18 : 0);
    elCross.style.opacity = (1 - clamp(p.adsT * 1.8, 0, 1)) * (p.reloading ? 0.25 : 1);
    elAmmoN.textContent = p.ammo; elAmmoM.textContent = '/ ' + p.magSize;
    const lk = p.gun.id + ':' + p.gun.rarity + ':' + p.gun.status.join();
    if (lk !== lookKey) {
      lookKey = lk;
      if (p.gun.id !== curGun) { setGun(p.gun.id, true); equipK = 0; }
      gunLookId = FxPlan.lookFor(p.gun.rarity, p.gun.status);                            // shots, hits and kills now look like this gun
      view.gunSkin = GunSkins.forGun(baseSkin, p.gun.status, p.gun.rarity); gunLook.setSkin(view.gunSkin);   // a legendary wears both its statuses' colours
    }
    hudGuns(p.gun); floorCard.update(st);
    elAmmo.classList.toggle('low', p.ammo <= Math.ceil(p.magSize * 0.25));
    elAmmo.classList.toggle('rl', p.reloading);
    elRl.style.width = (p.reloading ? p.reloadK * 100 : 0) + '%';
    elCross.style.setProperty('--gap', (6 + planar * 5 + (1 - p.adsT) * 4) + 'px');
    hitT = Math.max(0, hitT - dt);
    elHit.style.opacity = hitT > 0 ? Math.min(1, hitT / 0.1) : 0;
    elHit.classList.toggle('kill', hitKill);
    diedT = Math.max(0, diedT - dt); diedEl.style.opacity = clamp(diedT / 0.6, 0, 1);
    shotsView.update(st.shots, st.t);
    hud.update(st, dt); minimap.update(st, dt); compass.update(st); loot.update(st, time); trapView.update(st, ref.map, time); bossFx.update(st, time);
    coopKey = st.coop.key; peersView.update(st.coop.peers, dt); partyHud.update(st);
  }

  /* ============ main loop ============ */
  let state = ref.snapshot(), frameErr = '';
  const wallSets = WallSets.create(T);
  function ensureFloor(st) {
    if (st.floorId !== loadedFloor) {
      const set = WallSets.forFloor(st.floor);                                    // every floor wears the next wall set (6 looks, then round again)
      wallSets.apply(set.id); scene.background.setRGB(set.fog[0] / 255, set.fog[1] / 255, set.fog[2] / 255); scene.fog.color.copy(scene.background); worldView.setFlame(set.flame[0], set.flame[1]);
      worldView.load(ref.map, view.fogFar); loadedFloor = st.floorId;
    }
  }   // a new floor (or a new run) is baked and drawn here
  ensureFloor(state);
  chooseClass(0);
  GP.gunBody = gunBody; GP.magBase = MAG_BASE; GP.fore = HOLD;
  const VR_ACCEL = 240;   // in VR you reach full speed and stop in about 0.04 s: Meta's comfort guides say speeding up and slowing down the view is what makes people sick (docs/vr-design.md, round 5)
  xr = XrMode.create({ THREE, renderer, scene, camera, gun, $, gunHome: GUN_DEFAULTS, toast: (t) => toast(t), started: () => started, menuOpen: () => gearMenu.isOpen || stashMenu.isOpen,
    turnSpeed: () => ref.cfg.padTurn, arms: [handL, handR, limbL, limbR], sight: () => SIGHT, eyeRelief: EYE_RELIEF, inShop: () => !!state.shop, shopClose: () => { I.shopClose = true; }, map: { open: (v) => minimap.setOpen(v), big: $('bigMap'), small: $('miniMap') },
    gunParts: () => { if (!mag || !charge) return null; GP.id = curGun; GP.type = (RefereeWeapons.GUNS[state.player.gun.id] || {}).type; GP.mag = mag; GP.charge = charge; GP.gunScale = view.gunScale; return GP; }, playerYaw: () => state.player.yaw, levelMap: () => ref.map });
  xr.on(() => { renderer.setAnimationLoop(frame); document.body.classList.add('xr'); ref.setCfg({ accel: VR_ACCEL }); if (!running && (started || SANDBOX)) begin(true); }   // a new game shows the start menu in VR first (pick a class, then Enter the hall); a paused run or the test map carries straight on
  , () => { renderer.setAnimationLoop(null); document.body.classList.remove('xr'); ref.setCfg({ accel: ref.defaults.accel }); requestAnimationFrame(frame); });   // a headset drives the frames while in VR
  function frame(now) {
    if (!(xr && xr.presenting())) requestAnimationFrame(frame);
    const dt = Math.min((now - clock.last) / 1000, 0.05); clock.last = now;
    try { pollPad(dt); padMenus(); if (xr && xr.presenting()) { const ga = xr.grab(); if (ga && running && !panelOpen && !state.choices && !state.classChoices && !state.over) vrGrab(ga); } } catch (e) { /* a controller hiccup must not stop the frame */ }
    // each stage guards itself: one bad frame in the drawing code must never freeze the rules or the controller, and the first error is shown on screen so it can be read off a phone
    perfN++;
    const stage = (name, fn) => { const t0 = performance.now(); try { fn(); } catch (e) { if (!frameErr) { frameErr = name + ': ' + (e && e.message ? e.message : e); toastEl.textContent = 'Error in ' + frameErr; toastEl.classList.add('show'); toastT = 1e9; if (window.console) console.error(e); } } perfT[name] = (perfT[name] || 0) + performance.now() - t0; };
    if (running && !panelOpen) {
      stage('rules', () => { const out = ref.step(dt, gatherInput()); state = out.state; stage('events', () => handleEvents(out.events)); coop.tick(dt, out.events); });
    } else {
      I.lookX = I.lookY = I.touchX = I.touchY = 0; I.slide = false; I.jump = false; I.reload = false;
    }
    stage('menuPointer', menuPointer);
    stage('blueprints', drawOverBp);
    stage('stashEntry', () => {          // at the door of the hall: if the stash holds anything, open it so you can take one gun and any mods
      const st = state.player.stash; if (!st.entry) { entryShown = false; return; }
      if (running && !panelOpen && !entryShown && !st.near && st.take && st.items.length && !state.over && !state.choices && !state.classChoices) { entryShown = true; stashMenu.setOpen(true, state); }
    });
    stage('stashHint', () => { const near = running && !panelOpen && state.player.stash.near; stashHint.hidden = !near; });
    stage('floor', () => ensureFloor(state));
    stage('monsters', () => { syncMonsters(state, dt); syncThralls(state); });
    stage('xr', () => xr.update(state, running && !panelOpen, dt));
    stage('view', () => updateView(state, running && !panelOpen ? dt : 0, now / 1000));
    stage('draw', () => { if (xr && xr.presenting()) xr.renderScope(); renderer.render(scene, camera); });
  }
  const perfT = {}; let perfN = 0;                                  // milliseconds spent in each stage of the frame (the playtest reads it to keep the frame Quest-friendly)
  requestAnimationFrame((t) => { clock.last = t; frame(t); });
  setRunning(false);
  window.__game = { ref, view, THREE, fx, mouse, xr, vrShell, running: () => running, begin, perf: () => ({ ms: Object.assign({}, perfT), frames: perfN, reset: () => { for (const k in perfT) delete perfT[k]; perfN = 0; } }), perfReset: () => { for (const k in perfT) delete perfT[k]; perfN = 0; }, renderer, scene, camera };   // handy for poking at numbers from the console
})();
