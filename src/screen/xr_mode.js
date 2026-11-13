/* Meta Quest / WebXR mode: an "Enter VR" button (only shown when the browser can do immersive VR), the VR camera rig,
   the two Touch controllers (simple hand meshes and an aim laser), and a floating HUD you can read in the headset.
   Presentation and input only: it never touches the referee's rules. The game reads its input through the same
   controller path as a normal gamepad (XrInput.toPad -> PadInput), and aim is sent as a mouse-style look input. */
const XrMode = (function () {
  function create(o) {
    const { THREE, renderer, scene, camera, gun, $, gunHome } = o;
    const q = location.search + location.hash;
    const opts = { vstock: /[?&#]vstock\b/.test(q), snap: /[?&#]snap\b/.test(q), gaze: /[?&#]gaze\b/.test(q), perf: /[?&#]perf\b/.test(q), vignette: /[?&#]vignette\b/.test(q), aimMove: /[?&#]aimmove\b/.test(q),  rack: /[?&#]rack\b/.test(q),
      turnFlag: (() => { const m = /[?&#]turn=([0-9.]+)/.exec(q); return m ? Math.max(0.5, Math.min(10, +m[1])) : null; })(),
      snapDegFlag: (() => { const m = /[?&#]snap=([0-9]+)/.exec(q); return m ? Math.max(10, Math.min(90, +m[1])) : null; })(),
      scale: (() => { const m = /[?&#]xrscale=([0-9.]+)/.exec(q); return m ? Math.max(0.5, Math.min(1, +m[1])) : 0.8; })() };   // ?xrscale=0.7 trades sharpness for speed
    const dolly = new THREE.Group(); dolly.name = 'xrDolly';
    scene.add(dolly); scene.remove(camera); dolly.add(camera);       // flat screen: the rig sits at 0,0,0 with no turn, so nothing changes
    let session = null, bodyYaw = 0, onStart = null, onEnd = null;
    // Comfort settings (VR pause menu): snap or smooth turn, turn speed, the vignette, slower walking, walk from the head or the left hand.
    // Kept between visits; a link flag (?snap, ?vignette, ?turn=N, ?snap=N) wins for that visit.
    const COMFORT_KEY = 'cp.vrComfort';
    const comfort = (() => { let c = {}; try { c = JSON.parse(localStorage.getItem(COMFORT_KEY) || '{}') || {}; } catch (e) { c = {}; } return { snap: /[?&#]snap\b/.test(q) ? true : !!c.snap, vignette: /[?&#]vignette\b/.test(q) ? true : !!c.vignette, slow: !!c.slow, turnRate: XrInput.parseTurnRate(c.turnRate), walkHand: !!c.walkHand }; })();
    opts.snap = comfort.snap; opts.vignette = comfort.vignette;
    const snapDegOf = () => XrInput.snapTurnDeg(comfort.turnRate, opts.snapDegFlag);
    const turnSpeedOf = () => XrInput.smoothTurn(comfort.turnRate, opts.turnFlag);
    let turn = XrInput.createTurn(opts.snap, snapDegOf() * Math.PI / 180);
    function setComfort(k, v) {
      if (!(k in comfort)) return;
      if (k === 'turnRate') comfort.turnRate = XrInput.parseTurnRate(v);
      else comfort[k] = !!v;
      if (k === 'snap' || k === 'turnRate') { opts.snap = comfort.snap; turn = XrInput.createTurn(opts.snap, snapDegOf() * Math.PI / 180); }
      if (k === 'vignette') { opts.vignette = comfort.vignette; if (!opts.vignette) { moveK = 0; vig.visible = false; vig.material.opacity = 0; } }
      try { localStorage.setItem(COMFORT_KEY, JSON.stringify(comfort)); } catch (e) { /* private mode: just this visit */ }
    }
    const hands = { left: null, right: null };
    const tmpS = new THREE.Vector3(), v3 = new THREE.Vector3(), q4 = new THREE.Quaternion(), fwd = new THREE.Vector3(), aimQ = new THREE.Quaternion(), aimP = new THREE.Vector3(), headQ = new THREE.Quaternion();
    let aimInit = false, fps = 0, fpsN = 0, fpsT = 0, moveK = 0;

    // ---- controllers: rays (aim) and grips (where the hand mesh and the gun sit) ----
    const handMat = new THREE.MeshLambertMaterial({ color: 0x2a1a18, emissive: 0x120806 });
    const laserMat = new THREE.MeshBasicMaterial({ color: 0xff3030, transparent: true, opacity: 0.55, fog: false });
    const ctl = [0, 1].map((i) => {
      const ray = renderer.xr.getController(i), grip = renderer.xr.getControllerGrip(i);
      dolly.add(ray); dolly.add(grip);
      const body = new THREE.Mesh(new THREE.BoxGeometry(0.045, 0.035, 0.11), handMat); body.position.z = 0.01; grip.add(body);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.04, 0.007, 6, 16), handMat); ring.position.set(0, 0.02, -0.05); ring.rotation.x = Math.PI / 3; grip.add(ring);
      const laser = new THREE.Mesh(new THREE.BoxGeometry(0.004, 0.004, 1), laserMat); laser.position.z = -0.5; laser.scale.z = 1; laser.visible = false; ray.add(laser);
      const c = { ray, grip, laser, hand: null };
      ray.addEventListener('connected', (e) => { c.hand = e.data && e.data.handedness; if (c.hand === 'left' || c.hand === 'right') hands[c.hand] = c; });
      ray.addEventListener('disconnected', () => { if (c.hand && hands[c.hand] === c) hands[c.hand] = null; c.hand = null; laser.visible = false; });
      return c;
    });

    // the gun rides in the right hand in VR: an anchor that follows the grip, offset so the gun's usual hip spot lands in the palm
    const gunAnchor = new THREE.Group(); dolly.add(gunAnchor);
    const aimLocal = new THREE.Quaternion(), dollyInv = new THREE.Quaternion();
    // ---- aim down sights (left trigger): the gun leaves the hand and its sight comes up in front of your right eye, at a distance that
    //      suits the gun (eye relief), still pointing where the right controller points (a virtual stock: aim comes from the rear hand only,
    //      smoothed more while aiming). The flat game's own ADS pose (gunAds) already puts the sight on the anchor's centre line, so in VR the
    //      anchor moves from the palm to the eye. The left glove sits at that gun's own hand spot (HOLD: fore-end, pump, cupped under a pistol).
    //      Per gun type (docs/vr-design.md, research round 3):
    // (the voxel guns are drawn bigger than real ones, so the distances are set to give a real-looking sight picture: the sight
    //  housing fills about the same share of your view as a real optic at a real cheek weld; checked per gun in fake-XR screenshots)
    const ADS = {
      pistol: { relief: 0.46, smooth: 16, drop: 0.0 },     // arms out, support hand cupped under the grip (H3VR palm grip)
      smg: { relief: 0.38, smooth: 14, drop: 0.0 },        // compact stock in the shoulder, hand on the fore-grip
      rifle: { relief: 0.34, smooth: 12, drop: 0.0 },      // cheek on the stock, hand on the fore-end
      shotgun: { relief: 0.36, smooth: 12, drop: 0.0 },    // hand on the pump
      sniper: { relief: 0.22, smooth: 8, drop: 0.0, zoom: 4 },   // eye close behind the scope; a 4x picture inside the lens
      hmg: { relief: 0.40, smooth: 10, drop: 0.015 }       // heavy: sits a touch lower, slowest to swing
    };
    const adsOf = () => { const g = o.gunParts && o.gunParts(); return ADS[(g && g.type) || 'rifle'] || ADS.rifle; };
    let adsK = 0;
    const eyeP = new THREE.Vector3(), hipP = new THREE.Vector3(), adsP = new THREE.Vector3();
    // ---- support hand (left grip near the gun's fore-end): the right hand keeps the gun's position, the left one steers the barrel ----
    //      (Contractors / Pavlov style: rotation comes from both hands, position from the trigger hand). Pistols only get a light pull (cupped hand).
    let twoHand = false, gripErr = -1;
    const foreW = new THREE.Vector3(), gripW = new THREE.Vector3(), sh = new THREE.Vector3(), dir2 = new THREE.Vector3(), up2 = new THREE.Vector3(), m4b = new THREE.Matrix4(), q2 = new THREE.Quaternion();
    const ZERO3 = new THREE.Vector3();
    // grabbing and using things in the world (xr_interact.js): what each hand will take, the highlight, the squeeze
    const inter = XrInteract.create({ THREE, dolly, camera, hands, pulse: (h, s, ms) => pulse(h, s, ms), twoHand: () => twoHand, map: o.levelMap, toast: o.toast });
    const STEER = { pistol: 0.3, smg: 0.75, rifle: 0.8, shotgun: 0.8, sniper: 0.85, hmg: 0.85 };
    // ---- feel (xr_feel.js): recoil kicks the gun in the hand and springs back (look and buzz only: bullets go where you point); a hit marker on what you hit ----
    const recRot = XrFeel.createSpring(XrFeel.CAP_ROT), recBack = XrFeel.createSpring(XrFeel.CAP_BACK), recQ = new THREE.Quaternion(), AX_X = new THREE.Vector3(1, 0, 0);
    let shotN = 0, lastKick = null;
    function shotFx() {
      const g = o.gunParts && o.gunParts(), K = XrFeel.kickOf((g && g.type) || 'rifle', twoHand, adsK > 0.5);
      recRot.kick(K.rot, K.w); recBack.kick(K.back, K.w); pulse('right', K.hap, K.ms); if (K.left) pulse('left', K.left, K.ms);
      shotN++; lastKick = K;
    }
    const hmMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, depthTest: false, depthWrite: false, fog: false });
    const hitMk = new THREE.Group(); hitMk.visible = false;
    { const geo = new THREE.PlaneGeometry(0.012, 0.045); for (let i = 0; i < 4; i++) { const a = Math.PI / 4 + i * Math.PI / 2, m = new THREE.Mesh(geo, hmMat); m.position.set(Math.sin(a) * 0.04, Math.cos(a) * 0.04, 0); m.rotation.z = -a; m.renderOrder = 999; hitMk.add(m); } }
    scene.add(hitMk);
    let hmT = 0, hmDur = 0.12, hmS = 1, hitN = 0; const hmQ = new THREE.Quaternion(), hmC = new THREE.Vector3();
    function hitMark(x, y, z, kind) {
      if (!session) return;
      hitMk.position.set(x, y, z); hmDur = hmT = kind === 'kill' ? 0.26 : 0.13; hmS = kind === 'kill' ? 1.6 : kind === 'crit' ? 1.25 : 1;
      hmMat.color.setHex(kind === 'kill' ? 0xff3030 : kind === 'crit' ? 0xffd27a : 0xffffff); hitMk.visible = true; hitN++;
    }
    function hitFx(x, y, z, crit) { hitMark(x, y, z, crit ? 'crit' : 'hit'); pulse('right', crit ? 0.6 : 0.25, crit ? 40 : 20); }
    function hitMarkStep(dt) {
      if (hmT <= 0) return; hmT -= dt; if (hmT <= 0) { hitMk.visible = false; return; }
      camera.getWorldQuaternion(hmQ); camera.getWorldPosition(hmC); hitMk.quaternion.copy(hmQ);
      const k = hmT / hmDur; hitMk.scale.setScalar(hmS * Math.max(0.6, hitMk.position.distanceTo(hmC) * 0.35) * (1.3 - 0.3 * k)); hmMat.opacity = Math.min(1, k * 1.6);
    }
    function supportHand() {
      const L = hands.left, R = hands.right, g = o.gunParts && o.gunParts();
      const held = !!L && btnOn(L.gamepad, 1, 0.35);
      if (!held || !R || !g || !g.gunBody) { if (twoHand) pulse('left', 0.15, 10); twoHand = false; return; }
      if (!twoHand) {                                                  // only grabs when the hand closes near the fore-end (a big, forgiving zone)
        g.gunBody.updateMatrixWorld(true); foreW.copy(g.fore).applyMatrix4(g.gunBody.matrixWorld); dolly.worldToLocal(foreW);
        // anywhere along the gun ahead of the trigger hand counts (the voxel guns are long, a real reach is 30-45 cm), so you never fish for a spot
        const a0 = R.grip.position; dir2.copy(foreW).sub(a0); const len = dir2.length(); dir2.divideScalar(len || 1);
        const t = Math.max(0, Math.min(len, v3.copy(L.grip.position).sub(a0).dot(dir2)));
        if (t > 0.12 && v3.copy(a0).addScaledVector(dir2, t).distanceTo(L.grip.position) < 0.2) { twoHand = true; pulse('left', 0.35, 25); }
      }
    }
    // the aim the hands give this frame (dolly space): the right ray, turned toward the left hand while it holds the fore-end
    function handsAim(out) {
      const R = hands.right; out.copy(R.ray.quaternion);
      if (!twoHand || !hands.left) return out;
      const g = o.gunParts && o.gunParts(), w = STEER[(g && g.type) || 'rifle'] || 0.8;
      let from = R.grip.position;
      if (opts.vstock) {                                               // virtual stock: with the trigger hand near your right shoulder, the gun pivots on the shoulder
        sh.set(0.17, -0.22, 0.05).applyQuaternion(camera.quaternion).add(camera.position);
        if (R.grip.position.distanceTo(sh) < 0.3) from = sh;
      }
      dir2.copy(hands.left.grip.position).sub(from); if (dir2.lengthSq() < 0.01) return out;
      dir2.normalize(); fwd.set(0, 0, -1).applyQuaternion(out);
      dir2.lerp(fwd, 1 - w).normalize();
      up2.set(0, 1, 0).applyQuaternion(out);
      m4b.lookAt(ZERO3, dir2, up2); q2.setFromRotationMatrix(m4b);   // Matrix4.lookAt makes -z face the target (camera style), which is how the gun points
      return out.copy(q2);
    }
    function placeGun(p) {
      const h = hands.right;
      if (!h) { if (gun.parent !== camera) camera.add(gun); return; }
      if (gun.parent !== gunAnchor) gunAnchor.add(gun);
      const q = aimInit ? aimLocal : h.ray.quaternion;
      gunAnchor.quaternion.copy(q);                                    // pointing along the (smoothed) aim
      adsK = p ? Math.max(0, Math.min(1, p.adsT || 0)) : 0;
      // hip: the gun's own grip point (each gun's model says where the hand holds it) sits exactly in the controller grip, so it never floats
      const g = o.gunParts && o.gunParts(), glove = o.arms && o.arms[1];
      gunAnchor.position.copy(h.grip.position); gunAnchor.updateMatrixWorld(true);
      if (glove && g && g.gunBody) { glove.updateMatrixWorld(true); glove.getWorldPosition(gripW); dolly.worldToLocal(gripW); hipP.copy(h.grip.position).sub(gripW).add(h.grip.position); }
      else hipP.set(-gunHome.gunX, -gunHome.gunY + 0.02, -gunHome.gunZ - 0.12).applyQuaternion(q).add(h.grip.position);
      if (adsK > 0) {
        const A = adsOf();
        eyeP.set(0.032, 0, 0).applyQuaternion(camera.quaternion).add(camera.position);   // the right (dominant) eye: half a typical IPD from the head centre
        adsP.set(0, -A.drop, (o.eyeRelief || 0.5) - A.relief).applyQuaternion(q).add(eyeP);   // gunAds puts the sight eyeRelief ahead of the anchor: pull it back to this gun's distance
        gunAnchor.position.lerpVectors(hipP, adsP, adsK * adsK * (3 - 2 * adsK));
      } else gunAnchor.position.copy(hipP);
      if (glove && adsK < 0.01) { gunAnchor.updateMatrixWorld(true); glove.getWorldPosition(gripW); dolly.worldToLocal(gripW); gripErr = gripW.distanceTo(h.grip.position); }   // (checked by the test) the gun's grip is in the hand
      // hands: the game's own gloves at this gun's grip and fore-end spots (no forearms: they crowded the left eye). The right glove is always
      // on the grip; the left one appears on the fore-end while the left grip holds the gun or you aim down sights.
      const kr = recRot.step(lastDt), kb = recBack.step(lastDt);   // recoil: muzzle up and the gun back toward you, springing home
      if (kr || kb) { recQ.setFromAxisAngle(AX_X, kr); gunAnchor.quaternion.multiply(recQ); v3.set(0, 0, kb).applyQuaternion(q); gunAnchor.position.add(v3); }
      const gR = o.arms && o.arms[1], gL = o.arms && o.arms[0], showL = twoHand || adsK > 0.35;
      if (gR) gR.visible = true; if (gL) gL.visible = showL;
      for (const m of h.grip.children) m.visible = false;              // the glove replaces the placeholder controller hand
      const L = hands.left; if (L) for (const m of L.grip.children) if (m !== mapMesh) m.visible = !showL;
      scope(p);
    }
    // ---- sniper scope: while aiming a sniper, a small camera renders a 4x picture into the lens (the whole view never zooms: that makes people sick) ----
    const scopeRT = new THREE.WebGLRenderTarget(384, 384), scopeCam = new THREE.PerspectiveCamera(10, 1, 0.35, 160);
    const lens = new THREE.Mesh(new THREE.CircleGeometry(1, 28), new THREE.MeshBasicMaterial({ map: scopeRT.texture, fog: false }));
    const reticleLens = new THREE.Mesh(new THREE.RingGeometry(0.03, 0.05, 24), new THREE.MeshBasicMaterial({ color: 0x000000, fog: false })); reticleLens.position.z = 0.001; lens.add(reticleLens);
    { const cross = new THREE.MeshBasicMaterial({ color: 0x000000, fog: false }); for (const [w, hh] of [[1.6, 0.02], [0.02, 1.6]]) { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, hh), cross); m.position.z = 0.001; lens.add(m); } }
    lens.visible = false; let scopeOn = false, scopeFrame = 0;
    function scope(p) {
      const g = o.gunParts && o.gunParts(), A = adsOf(), want = !!(session && A.zoom && adsK > 0.85 && p && !p.reloading && g && o.sight);
      if (want && lens.parent !== gun) gun.add(lens);
      lens.visible = want; scopeOn = want;
      if (!want) return;
      const sp = o.sight();                                            // the sight point in the gun's own space (the flat ADS lines it up with the eye)
      lens.position.set(0, sp.y, sp.z + 0.01 / Math.max(0.01, gun.scale.z)); lens.scale.setScalar(0.017 / Math.max(0.01, gun.scale.x));
      scopeCam.fov = 50 / A.zoom; scopeCam.updateProjectionMatrix();
    }
    function renderScope() {                                           // called just before the XR frame renders (screen.js), every other frame
      if (!scopeOn || (scopeFrame++ & 1)) return;
      lens.updateMatrixWorld(true); lens.getWorldPosition(scopeCam.position); scopeCam.quaternion.copy(aimQ);
      const xrOn = renderer.xr.enabled; lens.visible = false;
      renderer.xr.enabled = false; const prev = renderer.getRenderTarget(); renderer.setRenderTarget(scopeRT); renderer.render(scene, scopeCam); renderer.setRenderTarget(prev); renderer.xr.enabled = xrOn;
      lens.visible = true;
    }

    // ---- HUD: a small canvas in front of your eyes, redrawn a few times a second from the page's own HUD text ----
    const hc = document.createElement('canvas'); hc.width = 1024; hc.height = 512;
    const hx = hc.getContext('2d'), hudTex = new THREE.CanvasTexture(hc);
    const hudMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.45), new THREE.MeshBasicMaterial({ map: hudTex, transparent: true, depthTest: false, depthWrite: false, fog: false }));
    hudMesh.position.set(0, -0.12, -1.1); hudMesh.renderOrder = 999; hudMesh.visible = false; camera.add(hudMesh);
    const reticle = new THREE.Mesh(new THREE.RingGeometry(0.008, 0.013, 16), new THREE.MeshBasicMaterial({ color: 0xffe0c0, depthTest: false, fog: false, transparent: true }));
    reticle.renderOrder = 1000; reticle.visible = false; scene.add(reticle);
    // Collimated red-dot sight: a solid red point with a white-hot centre and a soft glow, sitting on the fire ray at the hit (or far along it).
    // From any eye it overlays the impact, the way a real red dot (collimated at infinity) does. Sized in angle, not metres: the sprite is about
    // 44 MOA across, the solid core about 7-8 MOA (3-4 px on a Quest 3 at ~25 px per degree). Smaller than that (the first try, 10 MOA with a
    // sub-pixel core, mipmapped and added on) fades to nothing on the headset. Normal blending so it shows on bright walls; depth-tested so walls hide it.
    const MOA = Math.PI / (180 * 60), DOT_GLOW_MOA = 22, DOT_CORE = 0.17, DOT_MIN_CORE_MOA = 7.2;   // glow radius (MOA), core share of the radius, smallest core (~3 px)
    const fireDotTex = (() => {
      const N = 128, c = document.createElement('canvas'); c.width = c.height = N; const x = c.getContext('2d'), R = N / 2;
      const g = x.createRadialGradient(R, R, 0, R, R, R);
      g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.06, 'rgba(255,235,230,1)'); g.addColorStop(0.1, 'rgba(255,40,32,1)'); g.addColorStop(DOT_CORE, 'rgba(255,24,20,1)');
      g.addColorStop(DOT_CORE + 0.04, 'rgba(255,20,20,0.5)'); g.addColorStop(0.45, 'rgba(255,10,10,0.14)'); g.addColorStop(1, 'rgba(255,0,0,0)');
      x.fillStyle = g; x.fillRect(0, 0, N, N);
      const t = new THREE.CanvasTexture(c); t.minFilter = THREE.LinearFilter; t.magFilter = THREE.LinearFilter; t.generateMipmaps = false; t.needsUpdate = true; return t;
    })();
    const fireDot = new THREE.Sprite(new THREE.SpriteMaterial({ map: fireDotTex, color: 0xffffff, blending: THREE.NormalBlending, depthTest: true, depthWrite: false, fog: false, transparent: true }));
    fireDot.renderOrder = 1002; fireDot.visible = false; scene.add(fireDot);
    const fireDotPos = new THREE.Vector3();
    function placeFireDot(hit, dir, dist, show) {
      fireDot.visible = !!show;
      if (!show) return;
      fireDotPos.copy(hit).addScaledVector(dir, -Math.min(0.03, dist * 0.01));   // a hair toward you, so it does not z-fight the wall or hide inside a monster
      fireDot.position.copy(fireDotPos);
      const moa = Math.max(DOT_GLOW_MOA * 2, DOT_MIN_CORE_MOA / DOT_CORE);        // sprite diameter in MOA: never lets the solid core drop under ~3 px
      const s = Math.max(0.004, dist * moa * MOA);
      fireDot.scale.set(s, s, 1);
    }
    // comfort vignette: a dark ring that closes in a little while you move or turn with the sticks (off with ?novignette)
    const vig = new THREE.Mesh(new THREE.RingGeometry(0.22, 0.6, 32, 1), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0, depthTest: false, depthWrite: false, fog: false }));
    vig.position.z = -0.3; vig.renderOrder = 998; vig.visible = false; camera.add(vig);
    // ---- VR menus: the open menu's data drawn again as a clean VR panel (xr_menu.js), world-locked in front of you ----
    const MENUS = ['codex', 'gearMenu', 'stashMenu', 'levelup', 'gameover', 'start'];   // the big map is held in the left hand instead
    const vm = XrMenu.create(THREE);
    const PANEL_W = 1.5, MENU_DIST = 1.6, RECENTER = 70 * Math.PI / 180;   // metres; ~50 degrees wide at 1.6 m, so no head turning to read the edges
    const menuMat = new THREE.MeshBasicMaterial({ map: vm.tex, transparent: true, depthTest: false, depthWrite: false, fog: false });
    const menuMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), menuMat); menuMesh.scale.set(PANEL_W, PANEL_W * vm.ASPECT, 1);
    menuMesh.renderOrder = 1001; menuMesh.visible = false; dolly.add(menuMesh);
    const cursor = new THREE.Mesh(new THREE.RingGeometry(0.006, 0.011, 20), new THREE.MeshBasicMaterial({ color: 0xffffff, depthTest: false, depthWrite: false, fog: false, transparent: true }));
    cursor.renderOrder = 1003; cursor.visible = false; dolly.add(cursor);
    let menuPlacedFor = '', menuEl = null, modelT = 0, awayT = 0;
    function placeMenu() {
      const hp = camera.position, f = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion); f.y = 0; if (f.lengthSq() < 1e-4) f.set(0, 0, -1); f.normalize();
      menuMesh.position.set(hp.x + f.x * MENU_DIST, hp.y - 0.1, hp.z + f.z * MENU_DIST);
      menuMesh.rotation.set(0, Math.atan2(-f.x, -f.z), 0);
    }
    // the page's controller prompts name Xbox buttons and a D-pad; the Quest Touch controllers have neither, so VR shows Quest names
    const QUEST_WORDS = [[/Press <b>A<\/b> to (begin|resume)/g, 'Point and pull the trigger to $1'], [/Press A to (begin|resume)/g, 'Point and pull the trigger to $1'],
      [/D-pad down/g, 'right stick down'], [/(the )?D-pad( or (the )?left stick)?( to choose)?/g, 'the laser'], [/up and down to change row,?/g, ''],
      [/\bRT\b( \(R2\))?/g, 'right trigger'], [/\bLT\b( \(L2\))?/g, 'left trigger'], [/\bRB\b/g, 'right stick click'], [/\bLB\b/g, 'right grip'],
      [/\bStart\b( \(Options\))?/g, 'Y'], [/\bBack\b( \(View \/ Share\))?/g, 'hold the left grip'], [/Triangle|\bY\b(?= swaps)/g, 'A'], [/\bCross\b/g, 'A'], [/\bSquare\b/g, 'X'], [/\bCircle\b/g, 'B'],
      [/\bA\b to (take|pick|press|confirm)/g, 'the trigger to $1'],
      [/Click the left stick/g, 'Click the left stick (or push it all the way forward)'], [/right stick<\/b> looks/g, 'right stick</b> turns']];
    const questText = (t) => { for (const [re, w] of QUEST_WORDS) t = t.replace(re, w); return t; };
    function openMenu(running) {
      for (const id of MENUS) { const e = $(id); if (e && !e.hidden && (id !== 'start' || !running) && getComputedStyle(e).display !== 'none') return e; }
      return null;
    }
    // the model: what xr_menu.js reads from the page, plus the exits the flat page does not draw as buttons
    function menuModel(el) {
      const root = el.querySelector('.cxwrap, .card, .gbody') || el;
      const m = XrMenu.extract(root, el.id);
      if (el.id === 'levelup' && o.inShop && o.inShop()) { m.sub = 'Spend your gold   ·   ' + txt('goldN').replace(/\s+/g, ' ') ; m.exits.push({ action: 'shopClose', label: 'Leave the merchant' }); }
      if (el.id === 'levelup' && !(o.inShop && o.inShop())) m.sub = 'Take one card from each row';
      if (el.id === 'start' && o.started()) m.title = 'PAUSED';
      return m;
    }
    function hintsFor(el) {
      const exit = vm.layout && vm.layout.exits.length, paused = el.id === 'start' && o.started();
      return { left: 'Trigger: pick    Right stick or drag: scroll', right: exit ? 'Y: ' + vm.layout.exits[0].title.toLowerCase() : paused ? 'Y: resume' : el.id === 'levelup' ? 'Pick to carry on' : '' };
    }
    function menuPanel(running, dt) {
      const el = openMenu(running);
      if (!el) { if (menuPlacedFor) vm.reset(); menuMesh.visible = false; cursor.visible = false; menuPlacedFor = ''; menuEl = null; return false; }
      if (!dt) return menuMesh.visible;
      if (menuPlacedFor !== el.id) { menuPlacedFor = el.id; vm.reset(); placeMenu(); modelT = 0; awayT = 0; }
      menuEl = el;
      modelT -= dt; if (modelT <= 0) { modelT = 0.25; const m = menuModel(el); if (!vm.setModel(m)) vm.refreshEls(m); }
      // turned well away from the panel (or it got left behind)? bring it back in front, so a menu can never be lost
      const hp = camera.position, f = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
      const ang = Math.atan2(f.x * (menuMesh.position.z - hp.z) - f.z * (menuMesh.position.x - hp.x), f.x * (menuMesh.position.x - hp.x) + f.z * (menuMesh.position.z - hp.z));
      awayT = Math.abs(ang) > RECENTER ? awayT + dt : 0; if (awayT > 0.6) { placeMenu(); awayT = 0; }
      vm.draw(hintsFor(el));
      menuMesh.visible = !!vm.layout; return menuMesh.visible;
    }
    // ---- laser pointer: point at a tile (it lights up, a soft tick in that hand), pull and RELEASE the trigger to press it.
    //      Holding the trigger and moving up/down drags the list (and cancels the press); the right stick scrolls too. ----
    const rc = new THREE.Raycaster(), rO = new THREE.Vector3(), rD = new THREE.Vector3();
    const trig = { left: { on: false, t: null, v0: 0, last: 0, drag: false }, right: { on: false, t: null, v0: 0, last: 0, drag: false } };
    let pressN = 0;
    function pressEl(t) {
      pressN++;
      try { t.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true, pointerType: 'pen', isPrimary: true })); t.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerType: 'pen' })); } catch (e) { /* old browser */ }
      t.click();
    }
    function press(t) {
      if (!t) return;
      if (t.action === 'shopClose') { if (o.shopClose) o.shopClose(); pressN++; }
      else if (t.el) {
        if (!t.el.isConnected && menuEl) { const L0 = vm.layout, list = t.exit ? L0.exits : L0.tiles, i = list.indexOf(t); vm.refreshEls(menuModel(menuEl)); t = list[i] || t; }
        if (t.el && t.el.isConnected) pressEl(t.el);
      }
      modelT = 0.05;                                                   // redraw soon: the press usually changes the menu
    }
    function back() {                                                  // Y in a menu: the panel's exit, or resume from pause
      if (!menuEl) return;
      const L0 = vm.layout; if (L0 && L0.exits.length) { press(L0.exits[0]); return; }
      if (menuEl.id === 'start' && o.started()) { const p = $('play'); if (p && !p.disabled) pressEl(p); }
    }
    const laserMatHi = new THREE.MeshBasicMaterial({ color: 0xffd27a, transparent: true, opacity: 0.8, fog: false });
    function laser() {
      let hov = null, hovHand = null;
      cursor.visible = false;
      for (const c of ctl) {
        if (!c.hand) continue;
        const g = c.gamepad, on = btnOn(g, 0, 0.55), T = trig[c.hand];
        if (!menuMesh.visible) { c.laser.visible = false; T.on = on; T.t = null; continue; }
        c.ray.updateMatrixWorld(); rO.setFromMatrixPosition(c.ray.matrixWorld); rD.set(0, 0, -1).transformDirection(c.ray.matrixWorld);
        rc.set(rO, rD); const hit = rc.intersectObject(menuMesh, false)[0];
        c.laser.visible = true; const len = hit ? hit.distance : 1.2; c.laser.scale.z = len; c.laser.position.z = -len / 2;
        const t = hit && hit.uv ? vm.hit(hit.uv.x, hit.uv.y) : null; laserUv[c.hand] = hit && hit.uv ? [+hit.uv.x.toFixed(3), +hit.uv.y.toFixed(3)] : null;
        c.laser.material = t ? laserMatHi : laserMat;
        if (hit && hit.uv) {
          if (on && !T.on) { T.t = t; T.v0 = hit.uv.y; T.last = hit.uv.y; T.drag = false; }
          else if (on && T.on) { if (Math.abs(hit.uv.y - T.v0) > 0.035) T.drag = true; if (T.drag) vm.scrollBy((hit.uv.y - T.last) * XrMenu.H * 1.2); T.last = hit.uv.y; }
          if (c.hand === 'right' || !cursor.visible) { cursor.visible = true; cursor.position.copy(hit.point); dolly.worldToLocal(cursor.position); cursor.quaternion.copy(menuMesh.quaternion); cursor.translateZ(0.004); cursor.scale.setScalar(on ? 0.83 : 1); }
        }
        if (!on && T.on) { if (!T.drag && T.t && t && (T.t === t || (T.t.title === t.title && T.t.x === t.x && T.t.y === t.y))) {   // the same tile, even if the menu was redrawn while the trigger was down
           press(T.t); pulse(c.hand, 0.35, 25); } T.t = null; T.drag = false; }
        T.on = on;
        if (t && (c.hand === 'right' || !hov)) { hov = t; hovHand = c.hand; }
      }
      if (vm.setHover(hov) && hov) pulse(hovHand, 0.1, 8);
      if (menuMesh.visible) { const rs = XrInput.rightStick(hands.right && hands.right.gamepad); if (Math.abs(rs.y) > 0.2) vm.scrollBy(rs.y * 1100 * lastDt); }
    }
    const laserUv = { left: null, right: null };
    let hudT = 0;
    const txt = (id) => { const e = $(id); return e ? (e.textContent || '').replace(/\s+/g, ' ').trim() : ''; };
    const shown = (id) => { const e = $(id); return !!e && !e.hidden && getComputedStyle(e).display !== 'none'; };
    function drawHud(st, running) {
      const W = hc.width, H = hc.height; hx.clearRect(0, 0, W, H);
      hx.textBaseline = 'top'; hx.shadowColor = '#000'; hx.shadowBlur = 8;
      const line = (s, x, y, size, col, align, disp) => { hx.font = (disp ? '' : '700 ') + size + 'px ' + (disp ? "'Pirata One', Georgia, serif" : "'Barlow Condensed', 'Arial Narrow', sans-serif"); hx.fillStyle = col || '#f3e6d8'; hx.textAlign = align || 'left'; hx.fillText(s, x, y); };
      const p = st.player;
      if (opts.perf) line(fps + ' fps', 40, 6, 30, fps >= 70 ? '#7dff7d' : fps >= 55 ? '#ffd060' : '#ff5050');
      // bottom strip: health bar, ammo, wave, kills
      const hpK = Math.max(0, Math.min(1, p.hp / (p.maxHp || 100)));
      hx.fillStyle = 'rgba(0,0,0,0.55)'; hx.fillRect(40, 430, 360, 34); hx.fillStyle = hpK < 0.3 ? '#e23a42' : '#a31d26'; hx.fillRect(44, 434, 352 * hpK, 26);
      line('HP ' + Math.ceil(p.hp), 52, 436, 24);
      line((p.reloading ? 'RELOADING ' : '') + p.ammo + ' / ' + p.magSize, W - 40, 426, 40, p.ammo <= Math.ceil(p.magSize * 0.25) ? '#e23a42' : '#ecdfc6', 'right', true);
      line('Wave ' + txt('waveN') + '   Lvl ' + txt('lvlN') + '   Kills ' + st.kills + '   Gold ' + txt('goldN'), W / 2, 470, 26, '#cfa54a', 'center');
      // middle: banners, menus, prompts
      let y = 40;
      const center = (s, size, col) => { line(s, W / 2, y, size, col, 'center'); y += size + 12; };
      const bn = $('banner');
      if (bn && bn.classList.contains('show')) { center(txt('bannerT'), 52, '#ff4a4a'); center(txt('bannerS'), 28); }
      if (shown('boss')) center(txt('bossName'), 28, '#ff8a60');
      if (menuPanel(running, 0)) { const toastE = $('padToast'); if (toastE && toastE.classList.contains('show')) center(toastE.textContent, 24, '#cfa54a'); return; }   // the real menu is on its own panel
      if (!running) { center(o.started() ? 'PAUSED' : 'CRIMSON PLAGUE', 56, '#ff4a4a'); center('Point and pull the trigger on the menu    Y: pause', 26, '#ecdfc6'); return; }
      if (st.over) { center('YOU FELL', 56, '#ff4a4a'); center(txt('overStats'), 24); center('Point at RISE AGAIN and pull the trigger', 28); return; }
      if (st.choices || st.classChoices || st.shop) {
        center(txt('luTitle') || (st.shop ? 'THE MERCHANT' : 'LEVEL UP'), 40, '#ffcf6a');
        for (const id of ['classCards', 'cards']) {
          const box = $(id); if (!box || !box.children.length || box.offsetParent === null && box.hidden) continue;
          Array.from(box.children).slice(0, 6).forEach((c) => { const sel = c.classList.contains('sel'); center((sel ? '> ' : '') + (c.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60) + (sel ? ' <' : ''), 24, sel ? '#ffe08a' : '#cbb8a8'); });
        }
        center('Point with the laser and pull the trigger to pick' + (st.shop ? '   Y: leave the merchant' : ''), 22, '#a89080');
        return;
      }
      const lb = $('lockBox'); if (lb && getComputedStyle(lb).display !== 'none' && lb.offsetParent !== null) { center(txt('lockTxt'), 24, '#cfa54a'); const b0 = txt('lockB0'), b1 = txt('lockB1'); center((b0 ? 'Grip: ' + b0 : '') + (b1 ? '    Right stick down: ' + b1 : ''), 22); }
      const fc = $('floorCard'); if (fc && fc.offsetParent !== null && txt('floorCard')) center('Grip (reach or point at it): pick up  ' + txt('floorCard').slice(0, 44), 22, '#ecdfc6');
      const sh = $('stashHint'); if (sh && !sh.hidden) center('STASH CHEST: grip', 22, '#cfa54a');
      const mm = o.map && o.map.small;                                // the corner map, bottom left of the view (hold the LEFT GRIP for the whole floor in your hand)
      if (mm && mm.width) { hx.shadowBlur = 0; hx.globalAlpha = 0.9; hx.drawImage(mm, 40, 250, 170, 170); hx.globalAlpha = 1; hx.strokeStyle = '#6a2a2e'; hx.lineWidth = 3; hx.strokeRect(40, 250, 170, 170); hx.shadowBlur = 8; line('Double-tap Y: map', 40, 222, 20, '#cfa54a'); }
      const toastE = $('padToast'); if (toastE && toastE.classList.contains('show')) center(questText(toastE.textContent), 24, '#e8c890');
    }

    let lastDt = 1 / 72;
    function update(st, running, dt) {
      if (!session) return;
      lastDt = dt || lastDt;
      lastSt = st;
      const p = st.player;
      const dYaw = turn.step(hands.right && hands.right.gamepad, dt, opts.snap ? 0 : turnSpeedOf()); bodyYaw += dYaw;
      fpsN++; fpsT += dt; if (fpsT >= 0.5) { fps = Math.round(fpsN / fpsT); fpsN = 0; fpsT = 0; }
      if (opts.vignette) {
        const want = Math.min(1, (Math.hypot(p.vx || 0, p.vz || 0) / 7) + Math.abs(dYaw) / Math.max(dt, 1e-3) / 2.5) * 0.6;
        moveK += (want - moveK) * Math.min(1, dt * 6); vig.material.opacity = moveK; vig.visible = moveK > 0.03;
        vig.scale.setScalar(1.25 - moveK * 0.3);
      }
      dolly.position.set(p.x, p.eye, p.z);
      dolly.rotation.set(0, -bodyYaw, 0);
      dolly.updateMatrixWorld(true);
      fall(dt); mapHand(dt, running);
      placeGun(p);
      hitMarkStep(dt);
      menuPanel(running, dt);
      inter.update(st, running, dt, menuMesh.visible);
      laser(dt);
      hudT -= dt; if (hudT <= 0) { hudT = 0.1; drawHud(st, running); hudTex.needsUpdate = true; }
    }
    // ---- aim: the right controller's ray (smoothed) ----
    const rP = new THREE.Vector3(), magwell = new THREE.Vector3(), tgtQ = new THREE.Quaternion();
    const gl = new THREE.Vector3();
    function toRig(obj, local, out) { gl.copy(local); obj.localToWorld(gl); return dolly.worldToLocal(out.copy(gl)); }
    const convO = [0, 0, 0], convD = [0, 0, 0], WALK = { '.': 1, c: 1, d: 1, P: 1 }; let convDist = 0, lastSt = null;
    const wallAt = (x, z) => { const m = o.levelMap && o.levelMap(); if (!m) return false; const r = m.rows[Math.floor(z / m.CELL)]; return !r || !WALK[r[Math.floor(x / m.CELL)]]; };
    function aim() {
      if (!session) return null;
      const h = !opts.gaze && hands.right;
      if (h) { rP.copy(h.grip.position); supportHand(); handsAim(tgtQ); }
      else { camera.matrixWorld.decompose(v3, q4, tmpS); dollyInv.copy(dolly.quaternion).invert(); tgtQ.copy(dollyInv).multiply(q4); rP.copy(camera.position); }
      if (!aimInit) { aimLocal.copy(tgtQ); aimInit = true; } else { const gp = o.gunParts && o.gunParts(); aimLocal.slerp(tgtQ, Math.min(1, XrFeel.aimRate((gp && gp.type) || 'rifle', twoHand, adsK > 0.5 ? adsOf().smooth : 0) * lastDt)); }   // heavier guns trail the hand a touch; steadier while aiming down sights or with two hands
      aimQ.copy(dolly.quaternion).multiply(aimLocal);                // world aim (the gun in the hand follows this)
      fwd.set(0, 0, -1).applyQuaternion(aimQ);
      v3.copy(rP).applyMatrix4(dolly.matrixWorld);
      // Fire ray: from the muzzle (or the grip) along the aim. Visual recoil is look only, so the direction is the (smoothed) controller, not the kicked barrel — the red dot then stays on the shot.
      // The rules fire from your eye; we aim the eye at the point this line first hits, then put the dot on the eye's fire ray so shot and dot agree even if a wall is in the way.
      const gp = o.gunParts && o.gunParts();
      if (gp && gp.muzzle) { gp.muzzle.updateMatrixWorld(true); gp.muzzle.getWorldPosition(v3); }
      const pl = lastSt && lastSt.player;
      if (pl && h) {
        convO[0] = v3.x; convO[1] = v3.y; convO[2] = v3.z; convD[0] = fwd.x; convD[1] = fwd.y; convD[2] = fwd.z;
        const dBar = XrFeel.converge(convO, convD, lastSt.monsters, wallAt, 40);
        v3.addScaledVector(fwd, dBar);                                 // where the barrel points
        tmpS.set(v3.x - pl.x, v3.y - pl.eye, v3.z - pl.z); const L = tmpS.length() || 1;
        const fire = L > 0.4;                                          // the rules shoot from the eye toward that point
        if (fire) { fwd.copy(tmpS).multiplyScalar(1 / L); v3.set(pl.x, pl.eye, pl.z); }
        convO[0] = v3.x; convO[1] = v3.y; convO[2] = v3.z; convD[0] = fwd.x; convD[1] = fwd.y; convD[2] = fwd.z;
        const d = XrFeel.converge(convO, convD, lastSt.monsters, wallAt, 40); convDist = d;
        v3.addScaledVector(fwd, d);                                    // impact along the actual fire ray (eye -> barrel point), so the dot cannot sit behind a wall the shot would hit
        reticle.visible = !menuMesh.visible; reticle.position.copy(v3); reticle.quaternion.copy(aimQ); reticle.scale.setScalar(Math.max(0.5, d / 6));
        placeFireDot(v3, fwd, d, !menuMesh.visible);
        return XrInput.dirToAngles(fwd.x, fwd.y, fwd.z);
      }
      reticle.visible = !menuMesh.visible; reticle.position.copy(v3).addScaledVector(fwd, 6); reticle.quaternion.copy(aimQ); reticle.scale.setScalar(1);
      placeFireDot(reticle.position, fwd, 6, !menuMesh.visible);
      return XrInput.dirToAngles(fwd.x, fwd.y, fwd.z);
    }
    // ---- reload: the game's own reload animation plays on the gun (screen.js animateReload); here only the old magazine falling away ----
    let dropMag = null, dropV = 0, dropN = 0;
    function dropMagFrom(mag) {                                       // a copy of the gun's own magazine part drops from the magwell and tumbles to the floor
      if (!session || !mag) return;
      if (dropMag) dolly.remove(dropMag);
      mag.updateMatrixWorld(true); dropMag = mag.clone(); dropMag.visible = true; dropMag.matrixAutoUpdate = true;
      mag.matrixWorld.decompose(dropMag.position, dropMag.quaternion, dropMag.scale);
      dolly.worldToLocal(dropMag.position); dropMag.quaternion.premultiply(dollyInv.copy(dolly.quaternion).invert());
      dolly.add(dropMag); dropV = 0.4; dropN++;
      toRig(mag.parent, mag.position, magwell);
    }
    function fall(dt) { if (dropMag) { dropV += 9.8 * dt; dropMag.position.y -= dropV * dt; dropMag.rotation.x += dt * 4; dropMag.rotation.z += dt * 2; if (dropMag.position.y < -2.2) { dolly.remove(dropMag); dropMag = null; } } }
    const btnOn = (g, i, th) => { const b = g && g.buttons && g.buttons[i]; return !!b && (b.pressed || b.value > (th || 0.5)); };
    // ---- map: hold the LEFT GRIP and the floor map appears in your left hand (the game's own big map, live) ----
    const mapCv = o.map && o.map.big, mapTex = mapCv ? new THREE.CanvasTexture(mapCv) : null;
    const mapMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.34), new THREE.MeshBasicMaterial({ map: mapTex, transparent: true, opacity: 0.97, depthTest: false, depthWrite: false, fog: false, side: THREE.DoubleSide }));
    mapMesh.renderOrder = 997; mapMesh.visible = false;
    const mapFrame = new THREE.Mesh(new THREE.PlaneGeometry(0.36, 0.36), new THREE.MeshBasicMaterial({ color: 0x2a0d10, depthTest: false, depthWrite: false, fog: false, side: THREE.DoubleSide }));
    mapFrame.renderOrder = 996; mapFrame.position.z = -0.001; mapMesh.add(mapFrame);
    let mapHeld = false, mapT = 0, mapHost = null;
    // the map: double-tap Y toggles it, a single Y tap (or any menu) closes it. A button and nothing else: the old wrist-glance gesture
    // opened it in the middle of gunfights. It floats above the left controller, turned to face you, so the gun's sight line stays clear.
    let mapOpen = false;
    function mapHand(dt, running) {
      const L = hands.left;
      if (!running || menuMesh.visible || !L || !mapTex) mapOpen = false;
      const show = mapOpen;
      if (show !== mapHeld) { mapHeld = show; if (o.map) o.map.open(show); pulse('left', show ? 0.25 : 0.12, 15); }
      if (mapHost !== dolly) { dolly.add(mapMesh); mapHost = dolly; }
      mapMesh.visible = show;
      if (!show) return;
      mapMesh.position.copy(L.grip.position); mapMesh.position.y += 0.13;                 // just above the hand
      mapMesh.lookAt(v3.copy(camera.position).applyMatrix4(dolly.matrixWorld));           // always turned to face you (lookAt works in world space)
      mapT -= dt; if (mapT <= 0) { mapT = 0.2; mapTex.needsUpdate = true; }
    }
    const canFire = () => true, takeReload = () => false, onReloadStart = () => {}, poseGun = () => {};   // kept so older callers stay harmless
    const srcBuf = [];
    function sources() {
      if (!session) return [];
      srcBuf.length = 0;
      const list = session.inputSources;
      for (let i = 0; i < list.length; i++) { const s = list[i]; if (s && s.gamepad) srcBuf.push(s); }   // XRInputSource already has handedness + gamepad
      for (const c of ctl) { c.gamepad = null; if (c.hand) for (let i = 0; i < srcBuf.length; i++) if (srcBuf[i].handedness === c.hand) c.gamepad = srcBuf[i].gamepad; }
      return srcBuf;
    }
    // the direction your head (or a hand) faces, as the game's yaw, flattened to the floor. Movement goes this way, not where the gun points (?aimmove for the old way).
    function poseYaw(obj) {
      if (!obj) return null;
      obj.updateMatrixWorld(true); obj.matrixWorld.decompose(v3, q4, tmpS); fwd.set(0, 0, -1).applyQuaternion(q4);
      return XrInput.dirToAngles(fwd.x, 0, fwd.z).yaw;
    }
    function headYaw() {
      if (!session || opts.aimMove) return null;
      return poseYaw(camera);
    }
    function handYaw(which) {
      if (!session || opts.aimMove) return null;
      const h = hands[which];
      return poseYaw(h && (h.ray || h.grip));
    }
    function walkYaw() {
      if (comfort.walkHand) { const y = handYaw('left'); if (y !== null) return y; }
      return headYaw();
    }
    // a short buzz in one hand (fire, getting hit). Quest exposes hapticActuators[0].pulse
    function pulse(hand, strength, ms) {
      if (!session) return;
      for (let i = 0; i < session.inputSources.length; i++) {
        const s = session.inputSources[i]; if (s.handedness !== hand || !s.gamepad) continue;
        const a = s.gamepad.hapticActuators && s.gamepad.hapticActuators[0];
        try { if (a && a.pulse) a.pulse(strength, ms); else if (a && a.playEffect) a.playEffect('dual-rumble', { duration: ms, strongMagnitude: strength, weakMagnitude: strength }); } catch (e) { /* no haptics */ }
      }
    }
    // grips: what a squeeze did this frame (xr_interact.js): { type: 'item', id } take that exact item, { type: 'use' } use the gate / door /
    // chest / puzzle you stand at, { type: 'swap' } the gun on your back. Either hand; the left grip on the gun's fore-end is the support hand instead.
    function grab() { return session ? inter.take() : null; }
    function aimDir(out) { return out.set(0, 0, -1).applyQuaternion(aimQ); }
    const yBtn = XrInput.createY(); let yNow = { tap: false, hold: false, progress: 0 };
    function pad() {
      if (!session) return null;
      const src = sources(), L = hands.left, yOn = btnOn(L && L.gamepad, 5);
      yNow = yBtn.step(yOn, lastDt);
      const menu = menuMesh.visible;
      if (menu) { if (yNow.up) { yBtn.reset(); back(); } yNow = { tap: false, hold: false, double: false, up: false, progress: 0 }; }   // Y in a menu = back at once: no menu can trap you
      else if (yNow.double) mapOpen = !mapOpen;                        // double-tap Y: map on / off
      else if (yNow.tap && mapOpen) { mapOpen = false; yNow = Object.assign({}, yNow, { tap: false }); }   // a tap with the map open just closes it (no pause)
      if (yNow.hold && !menu) pulse('left', 0.4, 30);
      return XrInput.toPad(src, { y: yNow, menu });
    }

    let farWas = 120;
    async function enter() {
      if (session) { session.end(); return; }
      try {
        const s = await navigator.xr.requestSession('immersive-vr', { optionalFeatures: ['local-floor'] });
        renderer.xr.enabled = true; renderer.xr.setReferenceSpaceType('local'); renderer.xr.setFramebufferScaleFactor(opts.scale);   // ~80% resolution: holds 72/90 fps
        await renderer.xr.setSession(s);
        const bl = s.renderState && s.renderState.baseLayer; if (bl && 'fixedFoveation' in bl) bl.fixedFoveation = 1;   // full fixed foveation: edges drawn coarser, centre sharp
        if (renderer.xr.setFoveation) renderer.xr.setFoveation(1);
        session = s; aimInit = false; bodyYaw = o.playerYaw(); turn.reset(); hudMesh.visible = true; btn.textContent = 'EXIT VR'; btn.hidden = true;
        s.addEventListener('end', () => {
          session = null; inter.clear(); renderer.xr.enabled = false; vig.visible = false; hudMesh.visible = false; reticle.visible = false; fireDot.visible = false; menuMesh.visible = false;
          dolly.position.set(0, 0, 0); dolly.rotation.set(0, 0, 0); if (gun.parent !== camera) camera.add(gun);
          for (const m of (o.arms || [])) m.visible = true; if (mapHeld && o.map) o.map.open(false); mapHeld = false; mapMesh.visible = false;
          btn.textContent = 'ENTER VR'; btn.hidden = false; if (onEnd) onEnd();
        });
        for (const m of (o.arms || [])) m.visible = false;          // no viewmodel hands or forearms in VR: just the gun
        if (onStart) onStart();
      } catch (e) { o.toast('Could not start VR: ' + (e && e.message ? e.message : e)); }
    }
    // the button: added to the start card only when this browser can really do immersive VR (Quest Browser can; phones and desktops without a headset do not)
    const btn = document.createElement('button'); btn.type = 'button'; btn.id = 'vrBtn'; btn.textContent = 'ENTER VR'; btn.hidden = true;
    // big, fixed on top of everything (start card, menus, HUD) so it can never be scrolled away or covered
    btn.style.cssText = 'position:fixed;z-index:2147483000;left:50%;top:14px;transform:translateX(-50%);padding:18px 44px;font:800 28px sans-serif;letter-spacing:.14em;color:#fff;background:#b0101e;border:3px solid #ffd27a;border-radius:12px;box-shadow:0 0 24px #ff3040;cursor:pointer';
    btn.addEventListener('click', enter);
    const show = (note) => { if (!btn.isConnected) document.body.appendChild(btn); btn.hidden = false; if (note) btn.title = note; };
    try {
      if (navigator.xr) {
        show();                                                     // shown straight away whenever WebXR exists (the Quest browser), not after a slow check
        if (navigator.xr.isSessionSupported) navigator.xr.isSessionSupported('immersive-vr').then((ok) => { if (!ok) { if (/OculusBrowser|Quest/i.test(navigator.userAgent)) btn.textContent = 'ENTER VR (allow VR in browser settings)'; else btn.hidden = true; } }).catch(() => {});
      } else if (/OculusBrowser|Quest/i.test(navigator.userAgent)) { show(); btn.textContent = 'VR needs https'; }
    } catch (e) { /* no WebXR here */ }

    // in VR, put the camera back at the head pose the headset gave last frame (the game's flat-screen camera code is skipped)
    // in VR three.js already leaves the camera at the head pose after each render. Never read the XR camera's own world pose here:
    // asking it for a world quaternion rebuilds its matrix from its world position, which doubled the player offset and put the view inside the walls
    function headPose() { /* nothing to do: the camera keeps last frame's head pose */ }
    // during a run the button shrinks into the top-left corner so it does not cover the wave counter
    function corner(on) {
      btn.style.left = on ? '10px' : '50%'; btn.style.top = on ? 'auto' : '14px'; btn.style.bottom = on ? '10px' : 'auto';
      btn.style.transform = on ? 'none' : 'translateX(-50%)'; btn.style.padding = on ? '8px 16px' : '18px 44px'; btn.style.fontSize = on ? '15px' : '28px';
    }
    return { comfort: () => Object.assign({}, comfort), setComfort, poseGun, dropMag: dropMagFrom, update, aim, pad, headPose, headYaw, handYaw, walkYaw, turnSpeed: turnSpeedOf, snapDeg: snapDegOf, pulse, aimDir, corner, grab, questText, canFire, takeReload, onReloadStart, menuOpen: () => menuMesh.visible, menuCanvas: () => vm.canvas, renderScope, menuHit: (u, v) => { const t = vm.hit(u, v); return t ? t.title : null; }, shotFx, hitFx, hitMark, feel: () => ({ conv: convDist, shotN, hitN, kick: lastKick, rot: recRot.x, back: recBack.x, marker: hitMk.visible, dot: fireDot.visible ? fireDotPos.toArray() : null }), menuTiles: () => { const L = vm.layout; if (!L) return []; const W = XrMenu.W, H = XrMenu.H, V = XrMenu.VIEW, sc = vm.scroll; return L.tiles.map((t) => ({ title: t.title, disabled: !!t.disabled, u: (t.x + t.w / 2) / W, v: 1 - (t.y - sc + t.h / 2) / H, inView: t.y - sc >= 0 && t.y + t.h - sc <= V })).concat(L.exits.map((t) => ({ title: t.title, exit: true, u: (t.x + t.w / 2) / W, v: 1 - (t.y + t.h / 2) / H, inView: true }))); }, faceYaw: (y) => { bodyYaw = y; }, debug: () => ({ grab: inter.debug(), pressN, menuId: menuPlacedFor, dropN, dropping: !!dropMag, magwell: magwell.toArray(), mapShown: mapMesh.visible, armsHidden: (o.arms || []).every((m) => !m.visible), magVisible: !!(o.gunParts() && o.gunParts().mag.visible), hover: vm.hover ? vm.hover.title : null, laserUv, scroll: vm.scroll, maxScroll: vm.maxScroll, tiles: vm.layout ? vm.layout.tiles.length : 0, exits: vm.layout ? vm.layout.exits.map((e) => e.title) : [], adsK, scopeOn, gloveOn: !!(o.arms && o.arms[0] && o.arms[0].visible), twoHand, gripErr, foreAt: (() => { const g = o.gunParts && o.gunParts(); if (!g || !g.gunBody) return null; g.gunBody.updateMatrixWorld(true); const v = g.fore.clone().applyMatrix4(g.gunBody.matrixWorld); dolly.worldToLocal(v); return [v.x, v.y, v.z].map((n) => +n.toFixed(3)); })(), hit: (u, v) => 0, menu: menuMesh.visible, menuPos: menuMesh.position.toArray(), menuScale: menuMesh.scale.toArray(), aim: aimLocal.toArray() }), menuShown: () => menuMesh.visible, vigOn: () => vig.visible, presenting: () => !!session, on: (start, end) => { onStart = start; onEnd = end; }, rig: dolly };
  }
  return { create };
})();
if (typeof module !== 'undefined') module.exports = XrMode;
