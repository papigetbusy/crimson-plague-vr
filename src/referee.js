/* ============================================================
   REFEREE
   Owns every rule and number: map, positions, movement, slide,
   aim-down-sights, shooting, hit detection, damage, monster
   behavior, respawns, kill counter.

   No DOM. No 3D library. Plain data in, plain data out, so it
   can be ported to Go later without touching the screen.

   step(dt, input) -> { state, events }
     input:  { mx, mz, lookX, lookY, touchX, touchY, padX, padY,
               fire, ads, sprint, slide, reload, swap }
               (padX / padY: the controller's right stick, -1..1, already past its dead zone)
     state:  everything the screen needs to draw one frame
     events: one-shot things that happened this step
   ============================================================ */
const Referee = (function () {
  'use strict';

  const CELL = 2;       // world units per grid cell
  const WALL_H = 11.5;   // wall height

  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, t) => a + (b - a) * t;
  const D = typeof RefereeData !== 'undefined' ? RefereeData : require('./referee_data.js');   // monster kinds, skills, wave plan
  const CL = typeof RefereeClass !== 'undefined' ? RefereeClass : require('./referee_class.js');   // the Gunslinger, Assassin and Witch rules
  const RL = typeof RefereeLocks !== 'undefined' ? RefereeLocks : require('./referee_locks.js');           // the gold gates and the boss door's puzzle
  const TR = typeof RefereeTrail !== 'undefined' ? RefereeTrail : require('./referee_trail.js');         // the gold trail to the boss
  const RB = typeof RefereeBosses !== 'undefined' ? RefereeBosses : require('./referee_bosses.js');       // the Bat Lord, Lich King and Elder Dragon moves
  const ST = typeof RefereeStash !== 'undefined' ? RefereeStash : require('./referee_stash.js');         // the run stash and blueprints
  const WP = typeof RefereeWeapons !== 'undefined' ? RefereeWeapons : require('./referee_weapons.js');   // the 20 guns, rarities and drops
  const GR = typeof RefereeGear !== 'undefined' ? RefereeGear : require('./referee_gear.js');             // armor pieces and charms
  const GX = typeof RefereeGunFx !== 'undefined' ? RefereeGunFx : require('./referee_gunfx.js');         // what a gun's status colour does to a monster
  const RA = typeof RefereeAilments !== 'undefined' ? RefereeAilments : require('./referee_ailments.js');   // burn, freeze and poison on you
  const VR = typeof RefereeVariants !== 'undefined' ? RefereeVariants : require('./referee_variants.js');   // Ember, Frost and Venom monsters and bosses
  const SH = typeof RefereeShots !== 'undefined' ? RefereeShots : require('./referee_shots.js');   // monster projectiles
  const RC = typeof RefereeCoop !== 'undefined' ? RefereeCoop : require('./referee_coop.js');       // playing with friends: the numbers and the small helpers
const FG = typeof FloorGen !== 'undefined' ? FloorGen : require('./floorgen.js');              // the floors: rooms and winding corridors from a seed

  function makeRng(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // Every tunable number lives here.
  const DEFAULT_CFG = {
    trapTier: 0,                                       // 0 = traps get more advanced with the floor; a number forces that tier (test links)
    locks: true,               // gold gates across the corridors and a puzzle on the boss door (tests can turn them off)
    startSafe: false, startGold: 600,                  // test links: start in the safe room (#safe) with this much gold
    // body
    eyeStand: 1.7,
    eyeSlide: 0.85,
    walkSpeed: 6.2,
    sprintSpeed: 10.0,
    adsSpeedMul: 0.55,
    accel: 60,
    // slide
    slideSpeed: 15,
    slideTime: 0.75,
    slideCooldown: 0.35,
    // jump: straight up with the speed you already have (so it goes any direction you were moving), and a slide goes any direction you hold
    jumpSpeed: 9,                 // about twice as high as before (peak = speed squared over twice the gravity): high enough to hop over small monsters
    gravity: 18,
    // camera
    fovBase: 64,
    fovAds: 44,
    sprintFovAdd: 6,
    adsTime: 0.12,
    lookSens: 0.0022,     // radians per mouse pixel
    touchSens: 0.0055,    // radians per touch pixel
    padTurn: 3.4,         // radians per second the right stick turns you at full tilt
    padPitchMul: 0.7,     // looking up and down is slower than turning, so the aim stays easy to hold
    adsLookMul: 0.55,
    // gun
    fireRate: 10,
    damage: 14,
    headMul: 2,
    spread: 0.03,
    spreadAds: 0.004,
    range: 70,
    magSize: 30,
    reloadTime: 2.1,
    reloadEmptyExtra: 0.45,
    recoilKick: 0.012,
    startGun: 'rifle',        // the gun a run starts with: the plain rifle (all-ones baseline) here; the game screen starts you with 'pistol_service'
    manualGuns: false,        // true = guns and gear on the floor are only taken when you press pick up (the game does this so a good gun is never swapped away by accident); tests keep the old walk-over
    gunReach: 2.6,            // how close you must be to take a gun or piece of gear with pick up
    grabReach: 7,             // VR: how far away a gun or piece of gear you point at and grab can be (you must see it: never through a wall)
    keepDrops: false,         // the VR test map only: guns, armor and mods on the floor never fade (normally they go after 60 s)
    doorTest: false,          // the VR test map only: the boss door opens when you use it, so doors can be tried without fighting the boss
    stashReach: 3,            // how close you stand to the stash chest to use it
    bossRandom: false,        // a random boss on each boss floor (the game screen turns it on; tests keep the Demon Lord unless they ask)
    bossKind: '',             // force one boss: demon, bat, lich or dragon
    coop: false,              // playing with friends (see referee_coop.js): a level-up or the shop does not stop the world, and a downed player can be revived
    guest: false,             // this is a friend's copy: monsters, waves and doors come from the host (applyWorld); only what is personal is played here
    selfKey: 'host',          // this player's name on the net
    selfName: 'Host',
    selfSkin: '',                       // the look you picked in the lobby (the referee only carries the name of it; the screen draws it)
    stashOpen: false,         // can you put things in the safe-room stash? off here so tests stay steady; the game screen turns it on (later: only after the wave 100 boss when playing alone)
    modDrops: false,          // do monsters drop gun mods? off here so tests stay steady; the game screen turns it on
    gearDrops: false,         // do monsters drop armor and charms? off here so tests stay steady; the game screen turns it on
    gunDrops: false,          // do monsters drop guns? off here so tests stay steady; the game screen turns it on
    // monsters (base = the horned fiend; every kind multiplies these, see referee_data.js)
    monsterCount: 6,          // how many may be alive in wave 1; one more each wave, up to the cap in referee_data.js
    startWave: 1,
    classId: '',              // '' = no class; the screen picks gunslinger, assassin or witch before a run
    monsterHp: 70,
    monsterSpeed: 3.6,
    monsterDamage: 7,
    monsterAttackRate: 1.0,
    monsterScale: 1.0,
    // player
    playerHp: 100,
    regenDelay: 3,
    regen: 14
  };

  // (hit spheres now live with each monster kind, in referee_data.js)
  const MONSTER_RADIUS = 0.5;

  // seed = the MAP seed (floors, traps, fog): a save keeps it. luck = { damage, item }: the dice for fights and for drops, which a save does NOT keep (they are rolled fresh every time you enter)
  function create(seed, luck) {
    let seed0 = seed || 1337, rng = makeRng(luck && luck.damage ? luck.damage | 1 : seed0);
    const SEEDS = { map: seed0, damage: luck && luck.damage ? luck.damage | 1 : seed0, item: luck && luck.item ? luck.item | 1 : ((seed0 ^ 0x5bd1e995) | 1) };
    const cfg = Object.assign({}, DEFAULT_CFG);

    /* ---------- the floor you are on (a new one is generated when you go through the door) ---------- */
    let M0, G, GW, GH, floorNo = 0, mapId = 0, doorOpen = false, floorCells = [], explored = null, exploredCell = -1;
    let flow = null, queue = null, flowCell = -1, flowTimer = 0;
    let gateSet = new Set(), tflow = null, LK = null, bossDown = false, lockOut = [], sealedT = 0;     // the floor's locks (referee_locks.js), whether the boss has fallen, and what a friend's copy tells the host
    const solid = (cx, cz) => {
      if (cx < 0 || cz < 0 || cx >= GW || cz >= GH) return true;
      const c = G[cz][cx];
      return c !== '.' && c !== 'c' && c !== 'd';      // 'D' is the locked door (or a locked gate), 'd' the same once it is open
    };
    const AIL = RA.create({ maxHp: () => maxHp(), dot: (d, k) => dotPlayer(d, k) });       // burn, freeze and poison on you
    function loadFloor(n) {
      AIL.clear();
      R.windUsed = 0;                                                  // Second Wind comes back on every floor
      floorNo = n;
      setMap(FG.generate(n, makeRng((seed0 * 2654435761 + n * 40503) >>> 0), cfg.trapTier || n, cfg.floorSize));   // floorSize: unset in the game; only the ?sandbox test link sets a small one   // its own random stream, so a floor never depends on how the fight went
    }
    function setMap(map) {
      M0 = map;
      M0.WALL_H = WALL_H; M0.id = ++mapId;
      G = M0.rows.map((r) => r.split('')); GW = M0.W; GH = M0.H; doorOpen = false;
      floorCells = [];
      for (let z = 0; z < GH; z++) for (let x = 0; x < GW; x++) if (!solid(x, z)) floorCells.push([x, z]);
      flow = new Int16Array(GW * GH); queue = new Int16Array(GW * GH); flowCell = -1; flowTimer = 0;
      explored = new Uint8Array(GW * GH); exploredCell = -1;
      LK = RL.create(RL.layout(M0, floorNo)); bossDown = false; sealedT = 0; gateSet = new Set(); for (const g of M0.gates || []) for (const [x, z] of g.cells) gateSet.add(z * GW + x);
      R.keys = 0; if (cfg.locks === false) LK.load({ o: LK.layout.gates.map(() => 1), s: 1 }); syncGates();
      if (LK.layout.keeper && cfg.locks !== false && !cfg.guest) spawnKeeper(LK.layout.keeper);
      for (const a of peers.values()) { a.flow = new Int16Array(GW * GH); a.flowCell = -1; a.flowTimer = 0; }
    }

    // the Key Keeper: a big tough monster asleep in a room on your side of the key gate; every player's game hands them a key when he dies (see rewardDrops)
    function spawnKeeper(kp) {
      addMonster(kp.kind, kp.x, kp.z); const m = monsters[monsters.length - 1];
      m.mini = true; m.elite = ['keeper']; m.hp = m.maxHp = m.hp * L.keeperHp; m.dmg *= L.keeperDmg; m.scale *= L.keeperScale; m.state = 'guard'; m.yaw = m.yawT = rng() * Math.PI * 2;
    }
    const waveCount = () => monsters.reduce((n, m) => n + (m.mini ? 0 : 1), 0);      // the Key Keeper is not part of any wave: waves end and fill up without counting him
    // every gate that has been paid for stands open
    function syncGates() {
      for (const g of M0.gates || []) if (LK.S.open[g.id] && G[g.cells[0][1]][g.cells[0][0]] !== 'd') { for (const [x, z] of g.cells) G[z][x] = 'd'; flowCell = -1; for (const a of peers.values()) a.flowCell = -1; }
    }
    // the boss door opens when the boss is down and the puzzle is solved
    function tryOpenDoor() { if (bossDown && LK.solved() && !doorOpen && !R.safe) openDoor(); }
    // use what is near you (0: first action, 1: second). A friend's copy does it here and tells the host; the host and a solo game do it for real.
    const nearDoor = () => !!M0.door && Math.hypot(P.x - M0.door.x, P.z - M0.door.z) < RL.RULES.reach + 1;
    function useLock(idx) {
      const a = LK.use(P.x, P.z, R.gold, idx, R.keys);
      if (!a) { if (idx === 0 && cfg.doorTest && !cfg.guest && !doorOpen && !R.safe && nearDoor()) { openDoor(); R.phase = 'intermission'; spawnQ = []; monsters = []; } return; }   // test map: the door opens and the hall goes quiet so you can walk through
      const r = LK.act(a, R.gold, R.keys); if (!r) return;
      R.gold -= r.cost; R.keys -= r.key || 0; events.push(r.ev); if (cfg.guest) lockOut.push(a); else { syncGates(); tryOpenDoor(); }
    }
    function hitSocket(i) {
      const a = { k: 'sock', i }, r = LK.act(a, 0, 0); if (!r) return;
      events.push(r.ev); if (cfg.guest) lockOut.push(a); else tryOpenDoor();
    }
    const locksOut = () => { const o = lockOut; lockOut = []; return o; };
    // a friend did something at a lock (they paid with their own gold): the host makes it so
    function remoteLocks(key, list) {
      if (cfg.guest) return;
      between(() => { for (const a of (list || []).slice(0, 6)) { const r = LK.act({ k: String(a && a.k), i: a && a.i | 0, d: a && a.d > 0 ? 1 : -1 }, Infinity, 1); if (r) events.push(r.ev); } syncGates(); tryOpenDoor(); });
    }

    function collides(x, z, r) {
      const cx0 = Math.floor((x - r) / CELL), cx1 = Math.floor((x + r) / CELL);
      const cz0 = Math.floor((z - r) / CELL), cz1 = Math.floor((z + r) / CELL);
      for (let cz = cz0; cz <= cz1; cz++) for (let cx = cx0; cx <= cx1; cx++) {
        if (!solid(cx, cz)) continue;
        const nx = clamp(x, cx * CELL, (cx + 1) * CELL);
        const nz = clamp(z, cz * CELL, (cz + 1) * CELL);
        const dx = x - nx, dz = z - nz;
        if (dx * dx + dz * dz < r * r) return true;
      }
      return false;
    }
    // Axis-separated move so bodies slide along walls. Returns which axes were blocked.
    function tryMove(o, dx, dz, r) {
      const n = Math.max(1, Math.ceil(Math.max(Math.abs(dx), Math.abs(dz)) / 0.3));
      const sx = dx / n, sz = dz / n;
      let bx = false, bz = false;
      for (let i = 0; i < n; i++) {
        if (sx !== 0) { if (!collides(o.x + sx, o.z, r)) o.x += sx; else bx = true; }
        if (sz !== 0) { if (!collides(o.x, o.z + sz, r)) o.z += sz; else bz = true; }
      }
      return { bx, bz };
    }
    function hasLOS(ax, az, bx, bz) {
      const dx = bx - ax, dz = bz - az;
      const d = Math.hypot(dx, dz);
      const n = Math.ceil(d / 0.4);
      for (let i = 1; i < n; i++) {
        const t = i / n;
        if (solid(Math.floor((ax + dx * t) / CELL), Math.floor((az + dz * t) / CELL))) return false;
      }
      return true;
    }
    function hasWideLOS(ax, az, bx, bz) {
      if (!hasLOS(ax, az, bx, bz)) return false;
      const dx = bx - ax, dz = bz - az, d = Math.hypot(dx, dz) || 1;
      const px = -dz / d * 0.45, pz = dx / d * 0.45;
      return hasLOS(ax + px, az + pz, bx + px, bz + pz) && hasLOS(ax - px, az - pz, bx - px, bz - pz);
    }

    /* ---------- flow field toward the player ---------- */
    const NB = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]];
    function buildFlow(px, pz) {
      const pcx = clamp(Math.floor(px / CELL), 0, GW - 1), pcz = clamp(Math.floor(pz / CELL), 0, GH - 1);
      flow.fill(-1);
      let qh = 0, qt = 0;
      flow[pcz * GW + pcx] = 0; queue[qt++] = pcz * GW + pcx;
      while (qh < qt) {
        const cur = queue[qh++], cx = cur % GW, cz = (cur / GW) | 0, cd = flow[cur];
        for (const [ox, oz] of NB) {
          const nx = cx + ox, nz = cz + oz;
          if (solid(nx, nz)) continue;
          if (ox !== 0 && oz !== 0 && (solid(cx + ox, cz) || solid(cx, cz + oz))) continue;
          const ni = nz * GW + nx;
          if (flow[ni] !== -1) continue;
          flow[ni] = cd + 1; queue[qt++] = ni;
        }
      }
      flowCell = pcz * GW + pcx;
    }
    let trailKey = '', trailPts = [];
    function trailTo(b) {                                       // cached: only worked out again when you or the boss change cell
      const key = M0.id + ':' + flowCell + ':' + Math.floor(b.x / CELL) + ':' + Math.floor(b.z / CELL) + ':' + LK.gateOpenIds().length;
      if (key !== trailKey) {                                   // the line leads through the gold gates too (you have to pay your way along it)
        trailKey = key;
        const blocked = (x, z) => solid(x, z) && !gateSet.has(z * GW + x);
        if (!tflow || tflow.length !== GW * GH) tflow = new Int16Array(GW * GH);
        tflow.fill(-1); const pc = clamp(Math.floor(P.z / CELL), 0, GH - 1) * GW + clamp(Math.floor(P.x / CELL), 0, GW - 1), q = [pc]; tflow[pc] = 0;
        for (let i = 0; i < q.length; i++) { const cx = q[i] % GW, cz = (q[i] / GW) | 0; for (const [ox, oz] of NB) { const nx = cx + ox, nz = cz + oz; if (blocked(nx, nz)) continue; if (ox !== 0 && oz !== 0 && (blocked(cx + ox, cz) || blocked(cx, cz + oz))) continue; const ni = nz * GW + nx; if (tflow[ni] !== -1) continue; tflow[ni] = tflow[q[i]] + 1; q.push(ni); } }
        trailPts = TR.walk(tflow, GW, GH, CELL, blocked, b.x, b.z);
      }
      return trailPts;
    }
    function flowDir(x, z) {
      const cx = Math.floor(x / CELL), cz = Math.floor(z / CELL);
      let best = flow[cz * GW + cx], bx = -1, bz = -1;
      if (best < 0) return null;
      for (const [ox, oz] of NB) {
        const nx = cx + ox, nz = cz + oz;
        if (solid(nx, nz)) continue;
        if (ox !== 0 && oz !== 0 && (solid(cx + ox, cz) || solid(cx, cz + oz))) continue;
        const v = flow[nz * GW + nx];
        if (v >= 0 && v < best) { best = v; bx = nx; bz = nz; }
      }
      if (bx < 0) return null;
      const tx = (bx + 0.5) * CELL - x, tz = (bz + 0.5) * CELL - z;
      const l = Math.hypot(tx, tz) || 1;
      return [tx / l, tz / l];
    }

    /* ---------------- state ---------------- */
    const L = D.LOOP;
    const floorOf = (w) => Math.floor((w - 1) / L.bossEvery) + 1;   // ten waves to a floor
    const SELF = {
      get key() { return cfg.selfKey; }, get down() { return !!R.down; }, x: 0, z: 0, yaw: 0, pitch: 0,                       // set by placePlayer, once the floor exists
      vx: 0, vz: 0, eye: cfg.eyeStand,
      sliding: false, slideT: 0, slideCd: 0, sdx: 0, sdz: 0, jumpH: 0, jumpV: 0,
      sprinting: false, sprintK: 0, adsT: 0, kick: 0,
      hp: cfg.playerHp, hurt: 0, sinceHit: 0, invuln: 0, fireCd: 0,
      ammo: cfg.magSize, reloading: false, reloadT: 0, reloadDur: 0, reloadEmpty: false
    };
    let P = SELF;                                        // whoever the monsters are looking at right now (always SELF, except inside aim(), see the co-op section)
    const peers = new Map();                             // host: the friends joined to this game, as plain positions (their own games play the rest)
    let pendingEv = [], runNo = 0, paused = false, outbox = [];
    let monsters = [], orbs = [], pickups = [], coins = [], spawnQ = [];
    let rngW = makeRng(SEEDS.item);                     // its own dice for gun drops, so drops never change what the main dice roll
    const GEAR = { worn: [null, null, null, null, null] };   // head, chest, boots and two charms (see referee_gear.js)
    const W = { slots: [null, null], held: 0, mods: [] };         // the two guns you carry, and which one is in your hands (the held gun's ammo lives in P.ammo)
    let nextId = 1, kills = 0, deaths = 0, time = 0, spawnTimer = 0.4, events = [];

    /* ---------------- the run: waves, xp, level-ups, skills ---------------- */
    const taken = new Set();      // stash places already copied at the hall door this run
    const R = { stash: [] };      // wave, phase ('intermission' | 'fight'), timer, level, xp, stacks, choices, frenzy, over
    let M = null;      // the skill bonuses, worked out from the stacks
    const skillOf = (id) => D.SKILLS.find((s) => s.id === id);
    const stackOf = (id) => R.stacks[id] || 0;
    function computeMods() {
      const per = (id) => skillOf(id).per * stackOf(id), gt = GR.total(GEAR.worn);       // level-up skills plus everything you wear
      return {
        dmg: (1 + per('dmg')) * (1 + gt.dmg), rate: (1 + per('rate')) * (1 + gt.rate), speed: (1 + per('speed')) * (1 + gt.speed), multi: per('multi'), hp: per('hp') + gt.hp, steal: per('steal') + gt.leech,
        reloadMul: Math.max(0.25, (1 - per('reload')) * (1 - Math.min(0.6, gt.reload))), blast: per('blast'), magnet: (1 + per('magnet')) * (1 + gt.magnet), regen: per('regen') + gt.regen, mag: per('mag'),
        vit: gt.vit, def: gt.def, crit: gt.crit, critDmg: gt.critdmg,
        luck: per('luck'), thick: per('thick'), goldMul: per('gold'), over: per('over'), bounce: stackOf('bounce'), wind: stackOf('wind')
      };
    }
    const maxHp = () => Math.round((cfg.playerHp + M.hp) * (1 + M.vit));
    const gunStats = () => WP.stats(W.slots[W.held], cfg);
    const maxMag = () => Math.max(1, Math.round(gunStats().mag * (1 + M.mag / cfg.magSize)));      // Deep Magazine adds its share of the gun's magazine

    function newRun() {
      R.wave = cfg.startWave; R.phase = 'intermission'; R.timer = L.firstDelay; R.level = 1; R.xp = 0;
      R.stacks = {}; R.choices = null; R.classChoices = null; R.pending = 0; R.fogOn = false; R.fogK = 0; R.frenzy = 0; R.over = null; R.down = false; R.reviveT = 0; R.time = 0; R.hold = null; R.gold = 0; R.keys = 0; R.safe = false; R.shop = null; R.shopShut = false;
      kit.reset(cfg.classId);
      W.slots = [WP.make(cfg.startGun, 0, 1), null]; W.held = 0; W.mods = []; R.entry = true; R.entryGun = false; taken.clear(); GEAR.worn = [null, null, null, null, null]; applyLoadout();
      grantStartKit();
      M = computeMods();
    }
    // blueprints chosen on the start card: they join the run as fresh items (a gun replaces the starting pistol)
    let loadout = [];
    function applyLoadout() {
      const copy = (e) => JSON.parse(JSON.stringify(e.item)); let g = 0;
      for (const e of loadout) {
        if (e.kind === 'gun' && g < 1) { const it = copy(e); it.ammo = WP.stats(it, cfg).mag; W.slots[g++] = it; }
        else if (e.kind === 'gear') { const it = copy(e), at = GR.WEAR.indexOf(it.slot); if (at >= 0 && !GEAR.worn[at]) GEAR.worn[at] = it; }   // one piece of each place: the first charm place only
      }
    }
    // starting a run on a later wave (the #wave=N test link) hands out the upgrades you would have earned, picked at random, so you are not too weak
    function grantStartKit() {
      const n = Math.floor((cfg.startWave - 1) * L.kitPerWave);
      for (let i = 0; i < n; i++) {
        const open = D.SKILLS.filter((s) => stackOf(s.id) < s.max); if (!open.length) break;
        const s = open[Math.floor(rng() * open.length)]; R.stacks[s.id] = stackOf(s.id) + 1;
      }
      R.level = 1 + n;
      kit.grantKit(n, R.level);
    }
    function placePlayer() {
      P.x = M0.start.x; P.z = M0.start.z; P.yaw = M0.start.yaw; P.pitch = 0;
      P.vx = P.vz = 0; P.sliding = false; P.slideT = 0; P.kick = 0; P.jumpH = P.jumpV = 0;
      P.hp = maxHp(); P.invuln = 1.5; P.hurt = 0; P.sinceHit = 0; AIL.clear();
      P.ammo = maxMag(); P.reloading = false; P.reloadT = 0; P.fireCd = 0;
      if (explored) reveal(P);
    }
    // a normal run starts on the floor its wave belongs to; a test link (#safe) starts in the safe room before that floor, with some gold in hand
    function startFloor() {
      if (cfg.startSafe && R.wave > 1) { loadFloor(floorOf(R.wave - 1)); enterSafe(); R.gold = cfg.startGold; } else loadFloor(floorOf(R.wave));
    }
    function restartRun() {
      kills = 0; runNo++; monsters = []; orbs = []; pickups = []; coins = []; spawnQ = []; spawnTimer = 0.4; mshots.clear();
      newRun(); startFloor(); placePlayer(); R.windUsed = 0;
      events.push({ type: 'restart' });
    }
    function startWave() {
      spawnQ = D.waveKinds(R.wave, rng, bossKindFor(R.wave));
      if (coopN() > 1) spawnQ = RC.scaleQueue(spawnQ, coopN(), rng, (kd) => !!D.KINDS[kd].boss);      // more friends, more monsters
      R.phase = 'fight'; spawnTimer = 0.2; R.fogOn = D.fogWave(R.wave, seed0); R.entry = false;      // the hall's door closes behind you: the entry stash menu is over
      events.push({ type: 'waveStart', n: R.wave, boss: spawnQ.some((k) => D.KINDS[k].boss), bossName: (() => { const bk = spawnQ.find((k) => D.KINDS[k].boss); return bk ? titleOf(bk, VR.forBoss(floorOf(R.wave), seed0)) : undefined; })(), count: spawnQ.length, fog: R.fogOn });
    }
    function endWave() {
      events.push({ type: 'waveClear', n: R.wave });
      waveReward();
      R.wave++; R.phase = 'intermission'; R.timer = L.intermission;
    }
    function waveReward() {                                  // a clear wave leaves a heal in front of you (in co-op every player gets their own)
      const a = P.yaw, hx = P.x + Math.sin(a) * 2, hz = P.z - Math.cos(a) * 2;
      pickups.push({ id: nextId++, kind: 'heal', x: collides(hx, hz, 0.3) ? P.x : hx, z: collides(hx, hz, 0.3) ? P.z : hz, life: L.pickupLife });
    }
    const aliveMax = () => Math.round(Math.min(L.aliveCap, cfg.monsterCount + R.wave - 1) * RC.countMul(coopN()));
    let forceElite = false;
    const overCap = () => Math.max(0, cfg.monsterCount + R.wave - 1 - L.aliveCap);     // how many waves past the point where the screen is full

    function gainXp(v) {
      R.xp += v;
      while (R.xp >= D.xpNeed(R.level)) { R.xp -= D.xpNeed(R.level); R.level++; R.pending++; events.push({ type: 'levelUp', level: R.level }); }
      if (!R.choices && !R.classChoices && R.pending > 0) rollChoices();
    }
    function rollChoices() {
      const open = D.SKILLS.filter((s) => stackOf(s.id) < s.max);
      R.pending--;
      R.classChoices = kit.choices(R.level);                // a class skill row comes with every level-up
      if (!open.length) { if (!R.classChoices) { P.hp = Math.min(maxHp(), P.hp + 25); if (R.pending > 0) rollChoices(); } return; }
      for (let i = open.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); const t = open[i]; open[i] = open[j]; open[j] = t; }
      R.choices = open.slice(0, 3).map((s) => s.id);
    }
    function pickSkill(i) {
      const id = R.choices && R.choices[i];
      if (!id) return;
      R.stacks[id] = stackOf(id) + 1;
      M = computeMods();
      if (id === 'hp') P.hp = Math.min(maxHp(), P.hp + skillOf('hp').per);
      events.push({ type: 'skill', id });
      R.choices = null;
      if (!R.classChoices && R.pending > 0) rollChoices();
    }
    function pickClass(i) {
      const id = R.classChoices && R.classChoices[i];
      if (!id) return;
      kit.pick(id);
      R.classChoices = null;
      if (!R.choices && R.pending > 0) rollChoices();
    }

    /* ---------------- monsters: stats, spawning, loot ---------------- */
    const bossKindFor = (wave) => cfg.bossRandom || cfg.bossKind ? RB.pick(floorOf(wave), seed0, cfg.bossKind) : 'demon';
    function statsFor(kind, wave) {
      const k = D.KINDS[kind], w = wave - 1, bf = k.boss ? floorOf(wave) - 1 : 0;      // a boss gets tougher and hits harder on every floor after the first, on top of the wave growth
      return {
        hp: cfg.monsterHp * k.hpMul * RC.hpMul(coopN()) * (1 + L.hpPerWave * w) * (1 + L.capHp * overCap()) * (1 + L.bossHpFloor * bf),
        dmg: cfg.monsterDamage * k.dmgMul * (1 + L.dmgPerWave * w) * (1 + L.capDmg * overCap()) * (1 + L.bossDmgFloor * bf),
        spd: cfg.monsterSpeed * k.speedMul * Math.min(L.speedMax, 1 + L.speedPerWave * w)
      };
    }
    function angleDiff(a, b) {
      let d = a - b;
      while (d > Math.PI) d -= Math.PI * 2;
      while (d < -Math.PI) d += Math.PI * 2;
      return d;
    }
    function spawnMonster(kind) {
      const k = D.KINDS[kind];
      let best = null, bestScore = -1;
      if (k.boss) {                                         // the boss spawns at the door and guards it
        const d = M0.door;
        best = [d.x + d.nx * 3.2, d.z + d.nz * 3.2];
      } else {
        // on a big floor monsters appear a walk away from you (not across the whole map): cells whose path to you is 8 to 26 cells long, out of sight if possible
        for (let i = 0; i < 70; i++) {
          const c = floorCells[(rng() * floorCells.length) | 0], fd = flow[c[1] * GW + c[0]];
          if (fd < L.spawnPathMin || fd > L.spawnPathMax) continue;
          const x = (c[0] + 0.3 + rng() * 0.4) * CELL, z = (c[1] + 0.3 + rng() * 0.4) * CELL;
          const d = Math.hypot(x - P.x, z - P.z);
          if (d < 10) continue;
          const seen = hasLOS(x, z, P.x, P.z);
          const score = (seen ? 0 : 100) + Math.min(d, 40);
          if (score > bestScore) { bestScore = score; best = [x, z]; }
          if (!seen && d > 14) break;
        }
      }
      if (!best) return false;
      addMonster(kind, best[0], best[1]);
      return true;
    }
    // elites only appear once the waves are past the cap; no random is used before that, so early runs play out exactly as before
    function rollElite() {
      const over = overCap(); if (over <= 0 && !forceElite) return [];
      if (!forceElite && rng() >= Math.min(L.eliteMax, L.eliteBase + L.elitePer * over)) return [];
      const open = D.AFFIXES.filter((a) => over >= a.from), n = Math.min(L.eliteAffixMax, open.length, 1 + Math.floor(over / L.eliteAffixEvery)), pool = open.slice(), got = [];
      while (got.length < n) got.push(pool.splice((rng() * pool.length) | 0, 1)[0]);
      return got;
    }
    function addMonster(kind, x, z) {
      const k = D.KINDS[kind];
      const sv = k.boss ? 1 : 0.92 + rng() * 0.18, st = statsFor(kind, R.wave), elite = k.boss ? [] : rollElite();
      const variant = forceVariant || (k.boss ? VR.forBoss(floorOf(R.wave), seed0) : VR.roll(floorOf(R.wave), rng)), vv = variant && VR.VARIANTS[variant];
      if (vv) { st.hp *= k.boss ? VR.RULES.bossHp : vv.hp; st.dmg *= k.boss ? VR.RULES.bossDmg : vv.dmg; }
      if (elite.length) { st.hp *= L.eliteHp; for (const a of elite) { st.hp *= a.hp || 1; st.dmg *= a.dmg || 1; st.spd *= a.speed || 1; } }
      monsters.push({
        id: nextId++, kind, x, z, hp: st.hp, maxHp: st.hp, dmg: st.dmg, spd0: st.spd,
        elite: elite.map((a) => a.id), variant, tempo: k.boss ? 1 + VR.RULES.tempoPerFloor * (floorOf(R.wave) - 1) : 1, sv, scale: cfg.monsterScale * sv * k.size * (elite.length ? L.eliteScale : 1), spd: 0.85 + rng() * 0.3, yaw: k.guard ? Math.atan2(M0.door.nx, -M0.door.nz) : 0, yawT: k.guard ? Math.atan2(M0.door.nx, -M0.door.nz) : 0, phase: rng() * 6, atk: k.wind || 0.4, shT: 0.8 + rng() * 1.6, shW: 0,
        flash: 0, stun: 0, state: k.guard ? 'guard' : 'chase', chT: k.charge ? 1.5 : 0, wT: 0, cT: 0, cdx: 0, cdz: 0, summoned: false
      });
      events.push({ type: 'spawn', kind, boss: !!k.boss });
    }
    function dropLoot(m, k) {
      orbs.push({ id: nextId++, x: m.x, z: m.z, v: k.xp, life: L.orbLife });
      if (orbs.length > 80) { gainXp(orbs.shift().v); }
      const gv = Math.max(1, Math.round(k.xp * L.goldPerXp * (1 + L.goldWave * (R.wave - 1)) * (m.elite.length ? L.goldElite : 1)));
      coins.push({ id: nextId++, x: m.x, z: m.z, v: gv, life: L.coinLife });
      const r = rng();
      if (cfg.gunDrops && (k.boss || rngW() < (m.elite.length ? WP.DROP.eliteChance : WP.DROP.chance))) dropGun(m.x, m.z, k.boss ? 10 : 0);   // a boss always leaves a gun, a rarity band better
      if (cfg.gearDrops && (k.boss || rngW() < (m.elite.length ? GR.DROP.eliteChance : GR.DROP.chance))) dropGear(m.x, m.z, k.boss ? 10 : 0);
      if (cfg.modDrops && (k.boss || rngW() < (m.elite.length ? WP.MD.DROP.eliteChance : WP.MD.DROP.chance))) dropMod(m.x, m.z);
      if (k.boss || r < L.healChance) pickups.push({ id: nextId++, kind: 'heal', x: m.x, z: m.z, life: L.pickupLife });
      else if (r < L.healChance + L.frenzyChance) pickups.push({ id: nextId++, kind: 'frenzy', x: m.x, z: m.z, life: L.pickupLife });
    }
    function dropGear(x, z, extra, item) {
      pickups.push({ id: nextId++, kind: 'gear', x, z, life: WP.DROP.life, noPick: 0, gear: item || GR.roll(Math.min(4, WP.rarityFor(R.wave + (extra || 0) + luckWaves(), rngW)), R.wave, rngW, cfg.classId) });
    }
    const luckWaves = () => M.luck * L.luckWaves;                         // Lucky Drops: better rarities for guns, gear and mods
    function dropMod(x, z, item) {
      pickups.push({ id: nextId++, kind: 'mod', x, z, life: WP.DROP.life, noPick: 0, mod: item || WP.MD.make(Math.min(4, WP.rarityFor(R.wave + luckWaves(), rngW)), R.wave, rngW) });
    }
    function dropGun(x, z, extra, item) {
      pickups.push({ id: nextId++, kind: 'gun', x, z, life: WP.DROP.life, noPick: 0, item: item || WP.roll(R.wave, rngW, (extra || 0) + luckWaves(), cfg.classId) });
    }
    function killMonster(m) {
      const k = D.KINDS[m.kind];
      kills++; kit.onKill(m);
      events.push({ type: 'kill', id: m.id, kind: m.kind, boss: !!k.boss, x: m.x, z: m.z, scale: m.scale, yaw: m.yaw, elite: m.elite });
      rewardDrops(m, k);
      if (m.elite.includes('volatile')) {                                 // a volatile elite blows up when it dies
        events.push({ type: 'eliteBlast', x: m.x, z: m.z, r: L.volatileRadius });
        for (const t of targets()) aim(t, () => { if (Math.hypot(P.x - m.x, P.z - m.z) < L.volatileRadius) hurtPlayer(m.dmg * L.volatileDmg, m.id); });
      }
      monsters = monsters.filter((o) => o !== m);
      if (k.boss) { bossDown = true; tryOpenDoor(); if (!doorOpen) R.hold = 'door'; }     // the door stays sealed until the puzzle is solved too: waves of ordinary monsters keep coming meanwhile (see worldStep)
    }
    // what a kill leaves for YOU: loot, coins, xp (in co-op every player rolls their own when a monster dies)
    function rewardDrops(m, k) {
      dropLoot(m, k);
      if (m.elite.includes('keeper')) { R.keys++; events.push({ type: 'keyTaken' }); }
      if (m.elite.length) for (let i = 1; i < L.eliteXp; i++) orbs.push({ id: nextId++, x: m.x + (rng() - 0.5), z: m.z + (rng() - 0.5), v: k.xp, life: L.orbLife });
    }
    // the boss is down: the door he guarded opens right there, and the next wave waits until you step through
    function openDoor() {
      for (const [x, z] of M0.door.cells) G[z][x] = 'd';
      doorOpen = true; R.hold = 'door'; flowCell = -1;
      events.push({ type: 'doorOpen', x: M0.door.x, z: M0.door.z });
    }
    // through the door: a new, bigger floor; what you carry (health, ammo, level, skills) comes with you
    // the boss's door leads first into the safe room (a calm hall with a merchant); its own door leads on to the next floor
    function enterSafe() {
      for (const o of orbs) gainXp(o.v);
      for (const c of coins) R.gold += Math.round(c.v * (1 + M.goldMul));
      monsters = []; orbs = []; pickups = []; coins = []; spawnQ = []; mshots.clear();
      setMap(FG.safeRoom(floorNo));
      for (const [x, z] of M0.door.cells) G[z][x] = 'd';
      AIL.clear(); doorOpen = true; R.safe = true; R.hold = 'door'; R.phase = 'intermission'; R.shop = null; R.shopShut = false; R.fogOn = false;
      R.stock = kit.choices(R.level) || [];
      R.gearStock = cfg.gearDrops ? [GR.roll(Math.min(4, WP.rarityFor(R.wave, rngW)), R.wave, rngW, cfg.classId), GR.roll(Math.min(4, WP.rarityFor(R.wave + WP.SHOP.betterBand, rngW)), R.wave, rngW, cfg.classId)] : [];   // the merchant's armor and charms, for your class; the second is a rarity band better
      R.gunStock = cfg.gunDrops ? [WP.roll(R.wave, rngW, 0, cfg.classId), WP.roll(R.wave, rngW, WP.SHOP.betterBand, cfg.classId)] : [];     // the merchant's guns; the second is a rarity band better
      P.x = M0.start.x; P.z = M0.start.z; P.yaw = M0.start.yaw; P.vx = P.vz = 0; P.sliding = false; P.slideT = 0; P.invuln = 1.5;
      placePeers(); reveal(P);
      events.push({ type: 'safeRoom', floor: floorNo });
    }
    const skillPrice = (sid) => L.shopSkill + L.shopSkillPer * kit.lvl(sid);
    function shopBuy(i) {
      const slot = R.stock.map((x, k) => (x ? k : -1)).filter((k) => k >= 0)[i], sid = R.stock[slot];   // i counts the cards still on show
      if (!sid || R.gold < skillPrice(sid)) return;
      R.gold -= skillPrice(sid); kit.pick(sid); R.stock[slot] = null;
      events.push({ type: 'bought', what: sid });
    }
    // the supplies row: Mend, then the guns still on the shelf, then Leave
    const supplyList = () => [{ kind: 'mend' }].concat((R.gunStock || []).map((g, k) => (g ? { kind: 'gun', slot: k, item: g } : null)).filter(Boolean), (R.gearStock || []).map((g, k) => (g ? { kind: 'gear', slot: k, item: g } : null)).filter(Boolean), [{ kind: 'leave' }]);
    function shopSupply(i) {
      const e = supplyList()[i]; if (!e) return;
      if (e.kind === 'leave') { R.shop = null; R.shopShut = true; return; }
      if (e.kind === 'mend' && R.gold >= L.shopHeal && P.hp < maxHp()) { R.gold -= L.shopHeal; P.hp = maxHp(); events.push({ type: 'bought', what: 'mend' }); }
      if (e.kind === 'gear' && R.gold >= gearPrice(e.item)) { R.gold -= gearPrice(e.item); R.gearStock[e.slot] = null; wearBought(e.item); events.push({ type: 'bought', what: e.item.slot }); }
      if (e.kind === 'gun' && R.gold >= WP.price(e.item)) { R.gold -= WP.price(e.item); R.gunStock[e.slot] = null; takeGun({ item: e.item, life: 1 }); events.push({ type: 'bought', what: e.item.id }); }
    }
    const gearPrice = (item) => WP.price({ rarity: item.rarity, wave: item.wave });
    const gearCard = (item, k) => {
      const v = GR.view(item, GEAR.worn), pr = gearPrice(item), bits = [v.slot[0].toUpperCase() + v.slot.slice(1)];
      if (v.def > 0) bits.push('Def ' + v.def + '%'); if (v.hp > 0) bits.push('+' + v.hp + ' hp');
      for (const a of v.affixes) bits.push((a.cls ? '★ ' : '') + a.text);
      return { id: 'gear' + k + item.slot + item.rarity, name: v.rarityName + ' ' + v.name, desc: bits.join('  ·  ') + (v.vs === 'worse' ? '  ·  worse than yours' : ''), price: pr, afford: R.gold >= pr, color: '#' + v.color.toString(16).padStart(6, '0'), rarity: item.rarity };
    };
    const gunCard = (item, k) => {
      const st = WP.stats(item, cfg), r = WP.RARITIES[item.rarity], pr = WP.price(item);
      return { id: 'gun' + k + item.id + item.rarity, name: r.name + ' ' + WP.GUNS[item.id].name, desc: (item.status.length ? item.status.join(' + ') + '  ·  ' : '') + (item.affixes && item.affixes.length ? item.affixes.length + ' affix' + (item.affixes.length > 1 ? 'es' : '') + '  ·  ' : '') + Math.round(st.dmg) + ' dmg  ·  ' + st.rate.toFixed(1) + '/s  ·  ' + st.mag + ' rounds', price: pr, afford: R.gold >= pr, color: '#' + r.color.toString(16).padStart(6, '0'), rarity: item.rarity };
    };
    function nextFloor() {
      for (const o of orbs) gainXp(o.v);
      monsters = []; orbs = []; pickups = []; coins = []; spawnQ = []; mshots.clear();
      R.safe = false; R.shop = null; R.stock = null; R.gunStock = null; R.gearStock = null;
      loadFloor(floorNo + 1);
      P.x = M0.start.x; P.z = M0.start.z; P.yaw = M0.start.yaw; P.vx = P.vz = 0; P.sliding = false; P.slideT = 0; P.invuln = 1.5;
      R.hold = null; R.phase = 'intermission'; R.timer = L.intermission; spawnTimer = 0.4;
      placePeers(); reveal(P);
      events.push({ type: 'floorChange', floor: floorNo });
    }
    // a variant takes more from the gun status it is weak to and less from its own; a boss left open after a big move takes extra
    function weakSpot(m) {
      let f = m.exposed ? VR.RULES.exposedMul : 1;
      const vv = m.variant && VR.VARIANTS[m.variant], st = (W.slots[W.held] && W.slots[W.held].status) || [];
      if (vv) f *= st.includes(vv.weak) ? VR.RULES.weakMul : st.includes(vv.resist) ? VR.RULES.resistMul : 1;
      return f;
    }
    function damageMonster(m, dmg, crit, x, y, z, splash, quiet) {
      if (m.hp <= 0) return;
      dmg *= kit.takenMul(m) * gfx.takenMul(m);                               // a hexed monster takes extra
      dmg *= weakSpot(m);
      m.hp -= dmg;
      const died = m.hp <= 0 && !m.lifeTaken;                                    // the killing blow: you heal a flat amount of life for each kill (once per monster)
      if (died) { m.lifeTaken = true; const gain = M.steal + gunStats().leech; if (gain > 0) P.hp = Math.min(maxHp(), P.hp + gain); }
      if (cfg.guest) { outbox.push([m.id, dmg]); if (m.hp <= 0) m.hp = 0.001; }       // a friend's copy tells the host; the host decides when it dies
      if (!quiet) { m.flash = 0.12; if (!splash) m.stun = Math.max(m.stun || 0, 0.08); events.push({ type: 'hit', id: m.id, dmg: Math.round(dmg), crit, x, y, z, splash: !!splash }); }
      if (m.hp <= 0) killMonster(m);
    }

    function hurtPlayer(d, id, ail) {
      if (P !== SELF) return remoteHurt(d, id);          // co-op: the blow was meant for a friend; the host tells their game
      if (P.invuln > 0 || R.over || R.down || paused || P.sliding) return;   // a slide is untouchable from start to finish (and so is a level-up or shop menu in co-op, and a downed player)
      d *= (1 - M.def) * (1 - Math.min(0.6, M.thick));    // armor and Thick Skin block a share of every hit
      P.hp -= d; P.hurt = 0.3; P.sinceHit = 0;
      events.push({ type: 'playerHit', dmg: d, id });
      const src = monsters.find((q) => q.id === id), kind = ail || (src && src.variant && VR.VARIANTS[src.variant].ail);   // a variant monster burns, freezes or poisons with every blow that lands
      if (kind) { AIL.inflict(kind, src && src.variant ? VR.VARIANTS[src.variant].power : 1); events.push({ type: 'ailment', kind }); }
      return checkDeath();
    }
    // a steady loss from burn or poison (poison never kills you)
    function dotPlayer(d, canKill) {
      if (P !== SELF || P.invuln > 0 || R.over || R.down || paused) return;
      P.hp -= d; P.sinceHit = 0;
      if (!canKill && P.hp < 1) P.hp = 1;
      if (P.hp <= 0) checkDeath();
    }
    function checkDeath() {
      if (P.hp <= 0 && M.wind > (R.windUsed || 0)) {           // Second Wind: once per floor (per stack) a killing blow leaves you standing
        R.windUsed = (R.windUsed || 0) + 1; P.hp = Math.max(1, maxHp() * L.windHp); P.invuln = L.windGrace; events.push({ type: 'secondWind' });
      }
      if (P.hp <= 0) {
        P.hp = 0; deaths++;
        if (cfg.coop) { R.down = true; R.reviveT = 0; events.push({ type: 'down' }); }      // with friends you go down; a friend standing close brings you back
        else {
          R.over = { wave: R.wave, kills, level: R.level, time: R.time };
          events.push({ type: 'dead' });
        }
      }
      return true;                                       // the blow landed (a slide, an invulnerable moment or a finished run returns nothing)
    }

    const mshots = SH.create({
      nextId: () => nextId++, solidAt: (x, z) => solid(Math.floor(x / CELL), Math.floor(z / CELL)),
      player: () => ({ x: P.x, z: P.z, eye: P.eye, sliding: P.sliding }), hurt: (d, id, key, ail) => aimKey(key, () => hurtPlayer(d, id, ail)), event: (e) => events.push(e),
      players: () => targets().filter((t) => !isDown(t)).map((t) => ({ x: t.x, z: t.z, eye: t.eye, sliding: t.sliding, key: t.key }))
    });

    // the boss moves (bat, lich, dragon); see referee_bosses.js
    const BO = RB.create({
      player: () => P, rng: () => rng(), los: (ax, az, bx, bz) => hasLOS(ax, az, bx, bz), hurt: (d, id) => hurtPlayer(d, id), fire: (s) => mshots.fire(s.proj === 'fire' && !s.ail ? Object.assign({ ail: 'burn' }, s) : s), event: (e) => events.push(e),
      speed: (m) => m.spd0 * m.spd * gfx.slowOf(m),
      spot: (ax, az, bx, bz, min, max) => {                                    // a floor spot a walk away from you, in sight of you if it can be found
        let any = null;
        for (let i = 0; i < 60; i++) {
          const c = floorCells[(rng() * floorCells.length) | 0], x = (c[0] + 0.5) * CELL, z = (c[1] + 0.5) * CELL, d = Math.hypot(x - bx, z - bz);
          if (d < min || d > max) continue;
          if (hasLOS(x, z, bx, bz)) return [x, z];
          if (!any) any = [x, z];
        }
        return any;
      }
    });
    const kit = CL.create({
      rng: () => rng(), P, monsters: () => monsters, damage: (m, d, c, x, y, z, sp, q) => damageMonster(m, d, c, x, y, z, sp, q),
      heal: (v) => { P.hp = Math.min(maxHp(), P.hp + v); }, maxHp: () => maxHp(), baseDmg: () => gunStats().dmg * M.dmg, isBoss: (m) => !!D.KINDS[m.kind].boss,
      event: (e) => events.push(e), tryMove: (o, dx, dz, r) => tryMove(o, dx, dz, r), nextId: () => nextId++
    });

    const gfx = GX.create({
      monsters: () => monsters, damage: (m, d, c, x, y, z, sp, q) => damageMonster(m, d, c, x, y, z, sp, q),
      heal: (v) => { P.hp = Math.min(maxHp(), P.hp + v); }, event: (e) => events.push(e), boss: (m) => !!(D.KINDS[m.kind] && D.KINDS[m.kind].boss)
    });


    /* ---------------- playing with friends (numbers in referee_coop.js) ----------------
       The host's referee is the world. Each friend's own referee (cfg.guest) plays only what is personal: gun, gear, level, gold, drops, shop.
       Monsters on a friend's screen are copies fed by the host; a friend's shots are reported to the host as damage. */
    const coopN = () => cfg.coop ? (cfg.guest ? (R.coopN || 1) : 1 + peers.size) : 1;
    const targets = () => [SELF].concat(Array.from(peers.values()));
    const isDown = (t) => !!t.down;
    // look through someone else's eyes for one job (a monster picking who to chase, a hit landing): P and the flow field are swapped, then put back
    function aim(t, fn) {
      const sP = P, sF = flow, sC = flowCell;
      P = t; if (t !== SELF) { flow = t.flow; flowCell = t.flowCell; }
      try { return fn(); } finally { if (t !== SELF) t.flowCell = flowCell; P = sP; flow = sF; flowCell = sC; }
    }
    const aimKey = (key, fn) => { const t = !key || key === SELF.key ? SELF : peers.get(key); return t ? aim(t, fn) : undefined; };
    function remoteHurt(d, id) {
      if (P.down || P.sliding || R.over) return;
      events.push({ type: 'remoteHurt', to: P.key, dmg: d, id });          // the host does not apply it: the friend's own game does (their armor, their invulnerable moments)
      return true;
    }
    const pickTarget = (m) => RC.nearest(targets(), m.x, m.z);
    function spawnFor(kind) {
      if (!peers.size) return spawnMonster(kind);
      const up = targets().filter((t) => !t.down), t = up.length ? up[(rng() * up.length) | 0] : SELF;       // a new monster appears a walk away from one of you, picked by chance
      let ok = false; aim(t, () => { ok = spawnMonster(kind); }); return ok;
    }
    function placePeers() { for (const a of peers.values()) { a.x = M0.start.x; a.z = M0.start.z; a.flowCell = -1; } }
    const friends = () => cfg.guest ? (R.others || []) : Array.from(peers.values());
    // downed: a standing friend close by brings you back, slowly
    function reviveStep(dt) {
      const near = RC.helpers(friends(), P.x, P.z) > 0;
      R.reviveT = near ? R.reviveT + dt : Math.max(0, R.reviveT - dt * 0.5);
      if (R.reviveT >= RC.RULES.reviveTime) {
        R.down = false; R.reviveT = 0; P.hp = Math.max(1, Math.round(maxHp() * RC.RULES.reviveHp)); P.invuln = RC.RULES.reviveInvuln; P.hurt = 0; P.sinceHit = 0;
        events.push({ type: 'revived' });
      }
    }
    const between = (fn) => { events = pendingEv; try { return fn(); } finally { pendingEv = events; } };     // things that happen between steps are reported with the next step
    const reviveK = () => clamp((R.reviveT || 0) / RC.RULES.reviveTime, 0, 1);
    const peerSnap = (a) => ({ key: a.key, name: a.name, x: a.x, z: a.z, yaw: a.yaw, eye: a.eye, sliding: !!a.sliding, hp: a.hp, maxHp: a.maxHp, down: !!a.down, rk: a.rk || 0, gun: a.gun, gr: a.gr, gs: a.gs || [], cls: a.cls, skin: a.skin || '' });
    const playerView = (a) => ({ key: a.key, name: a.name, x: a.x, z: a.z, yaw: a.yaw, eye: a.eye, sl: !!a.sliding, hp: a.hp, mhp: a.maxHp, dn: !!a.down, rk: a.rk || 0, gun: a.gun, gr: a.gr, gs: a.gs || [], cls: a.cls, skn: a.skin || '' });
    // host side
    const cleanSkin = (s) => String(s || '').replace(/[^a-z]/g, '').slice(0, 12);
    function remoteJoin(key, name, skin) {
      if (cfg.guest || peers.has(key)) return peers.has(key);
      if (peers.size >= RC.RULES.maxPlayers - 1) return false;
      peers.set(key, { key, name: name || 'Friend', skin: cleanSkin(skin), x: M0.start.x, z: M0.start.z, yaw: 0, eye: cfg.eyeStand, sliding: false, hp: cfg.playerHp, maxHp: cfg.playerHp, down: false, flow: new Int16Array(GW * GH), flowCell: -1, flowTimer: 0 });
      return true;
    }
    const remoteLeave = (key) => { peers.delete(key); };
    function remoteState(key, st) {
      const a = peers.get(key); if (!a) return;
      a.x = st.x; a.z = st.z; a.yaw = st.yaw; a.eye = st.eye; a.sliding = !!st.sl; a.hp = st.hp; a.maxHp = st.mhp; a.down = !!st.dn; a.rk = st.rk; a.gun = st.gun; a.gr = st.gr; a.gs = Array.isArray(st.gs) ? st.gs.slice(0, 2) : []; a.cls = st.cls; if (st.skn) a.skin = cleanSkin(st.skn);
    }
    // a friend's bullets, as their game saw them: the host passes them on to everyone so each screen can draw the streaks, flashes and hits
    function remoteShots(key, list) {
      const ok = (v) => typeof v === 'number' && isFinite(v);
      between(() => {
        for (const s of (list || []).slice(0, 12)) {
          if (![s.ox, s.oy, s.oz, s.ex, s.ey, s.ez].every(ok)) continue;
          events.push({ type: 'peerShot', key, ox: s.ox, oy: s.oy, oz: s.oz, ex: s.ex, ey: s.ey, ez: s.ez, hit: s.hit | 0, g: String(s.g || '').slice(0, 24), r: s.r | 0, s: Array.isArray(s.s) ? s.s.slice(0, 2) : [] });
        }
      });
    }
    // a friend's hit on a monster: their game worked out the damage; here it only lowers the monster's health (and the host sees the number)
    function remoteDamage(key, list) {
      between(() => {
        for (const [id, dmg] of list) {
          const m = monsters.find((o) => o.id === id); if (!m || m.hp <= 0) continue;
          m.hp -= dmg; m.flash = 0.12; events.push({ type: 'hit', id: m.id, dmg: Math.round(dmg), crit: false, x: m.x, y: 1.2 * m.scale, z: m.z, splash: true });
          if (m.hp <= 0) killMonster(m);
        }
      });
    }
    const playersView = () => [playerView({ key: SELF.key, name: cfg.selfName, x: P.x, z: P.z, yaw: P.yaw, eye: P.eye, sliding: P.sliding, hp: P.hp, maxHp: maxHp(), down: R.down, rk: reviveK(), gun: W.slots[W.held].id, gr: W.slots[W.held].rarity, gs: W.slots[W.held].status || [], cls: cfg.classId, skin: cfg.selfSkin })].concat(Array.from(peers.values()).map(playerView));
    function worldView() {
      const boss = monsters.find((m) => D.KINDS[m.kind].boss);
      return {
        t: time, run: runNo, seed: SEEDS.map, floor: floorNo, safe: R.safe, door: doorOpen, hold: R.hold, n: coopN(),
        wave: { n: R.wave, phase: R.phase, timer: R.timer, fogOn: R.fogOn, left: spawnQ.length + waveCount() },
        over: R.over ? { wave: R.over.wave, time: R.over.time } : null,
        monsters: monsters.map((m) => { const k = D.KINDS[m.kind]; return RC.compact(m, m.state === 'attack' ? clamp(1 - m.atk / k.wind, 0, 1) : 0, castOf(m, k)); }),
        shots: mshots.view(), bossFx: boss && (D.KINDS[boss.kind].moves || D.KINDS[boss.kind].extra) ? BO.view(boss, D.KINDS[boss.kind]).warn : [],
        players: playersView(), lk: LK.state()
      };
    }
    // friend side
    function selfState() { const g = W.slots[W.held]; return { x: P.x, z: P.z, yaw: P.yaw, eye: P.eye, sl: P.sliding, hp: P.hp, mhp: maxHp(), dn: !!R.down, rk: reviveK(), gun: g.id, gr: g.rarity, gs: g.status || [], cls: cfg.classId, skn: cfg.selfSkin }; }
    let shotOut = [];
    const shotsOut = () => { const o = shotOut; shotOut = []; return o; };           // the bullets to tell the host about
    function guestOut() {                                       // what to tell the host: damage dealt, added up per monster
      const sum = new Map(); for (const [id, d] of outbox) sum.set(id, (sum.get(id) || 0) + d);
      outbox = []; return Array.from(sum.entries());
    }
    function applyWorld(w, evs) {
      if (!cfg.guest) return;
      between(() => {
        if (w.seed !== SEEDS.map || (R.netRun !== undefined && w.run !== R.netRun)) { seed0 = SEEDS.map = w.seed; restartRun(); }      // a new run, or the host's map: start over on it
        R.netRun = w.run;
        syncFloor(w);
        time = w.t; R.wave = w.wave.n; R.phase = w.wave.phase; R.timer = w.wave.timer; R.fogOn = w.wave.fogOn; R.hold = w.hold; R.netLeft = w.wave.left; R.coopN = w.n;
        if (w.lk) { LK.load(w.lk); syncGates(); }
        if (w.door && !doorOpen) openDoor();
        for (const e of evs || []) worldEvent(e);
        monsters = RC.merge(monsters, w.monsters);
        R.netShots = w.shots; R.netBossFx = w.bossFx; R.others = w.players.filter((q) => q.key !== SELF.key).map((q) => ({ key: q.key, name: q.name, x: q.x, z: q.z, yaw: q.yaw, eye: q.eye, sliding: q.sl, hp: q.hp, maxHp: q.mhp, down: q.dn, rk: q.rk, gun: q.gun, gr: q.gr, gs: q.gs || [], cls: q.cls, skin: q.skn || '' }));
        if (w.over && !R.over) { R.over = { wave: w.over.wave, kills, level: R.level, time: R.time }; events.push({ type: 'dead' }); }
      });
    }
    // the host says which floor (and whether the safe room) everyone is in; a friend's copy goes there too (the same map seed gives the same floors)
    function syncFloor(w) {
      if (w.safe) { if (!(R.safe && floorNo === w.floor)) { if (floorNo !== w.floor) loadFloor(w.floor); enterSafe(); } }
      else if (R.safe || floorNo !== w.floor) { if (R.safe && floorNo + 1 === w.floor) nextFloor(); else { loadFloor(w.floor); R.safe = false; monsters = []; placePlayer(); } }
    }
    function worldEvent(e) {
      if (e.type === 'remoteHurt') { if (e.to === SELF.key) hurtPlayer(e.dmg, e.id); return; }
      if (e.type === 'dead') return;
      if (e.type === 'peerShot') { if (e.key !== SELF.key) events.push(e); return; }          // your own bullets came back from the host: you already drew them
      if (e.type === 'kill') {                                  // every friend gets their own loot and xp for a kill
        const k = D.KINDS[e.kind], m = monsters.find((o) => o.id === e.id) || { id: e.id, kind: e.kind, x: e.x, z: e.z, scale: e.scale, yaw: e.yaw, elite: e.elite || [], dmg: 0 };
        kills++; kit.onKill(m); events.push(e); rewardDrops(m, k);
        monsters = monsters.filter((o) => o.id !== e.id); return;
      }
      if (e.type === 'waveClear') waveReward();
      events.push(e);
    }

    /* ---------------- the two guns you carry ---------------- */
    // walking over a gun: it goes in your free hand-slot and you hold it; with both slots full it replaces the gun in your hands, and that one drops at your feet
    function takeGun(p) {
      const it = p.item; it.ammo = WP.stats(it, cfg).mag;
      p.life = -1;
      const other = 1 - W.held;
      if (!W.slots[other]) {
        W.slots[W.held].ammo = P.ammo; W.held = other; W.slots[other] = it;
      } else {
        const sx = P.x + Math.cos(P.yaw) * 1.1, sz = P.z + Math.sin(P.yaw) * 1.1, ok = !collides(sx, sz, 0.3);      // the gun from your hands drops beside you (to your right), not under the one you reach for
        W.slots[W.held].ammo = P.ammo;
        dropGun(ok ? sx : P.x, ok ? sz : P.z, 0, W.slots[W.held]); pickups[pickups.length - 1].noPick = WP.DROP.noPick;
        W.slots[W.held] = it;
      }
      P.ammo = it.ammo; P.reloading = false; P.reloadT = 0; P.fireCd = 0.3;
      events.push({ type: 'gunPickup', id: it.id, rarity: it.rarity });
    }
    // walking over gear: it goes on if the place is empty or it beats what you wear there (the old piece drops at your feet); worse gear stays on the floor
    function takeGear(p) {
      const at = GR.place(GEAR.worn, p.gear); if (at < 0) return;
      p.life = -1; wearAt(p.gear, at);
    }
    function wearAt(item, at) {
      const old = GEAR.worn[at]; GEAR.worn[at] = item;
      if (old) { dropGear(P.x, P.z, 0, old); pickups[pickups.length - 1].noPick = WP.DROP.noPick; }
      const hpBefore = maxHp(); M = computeMods(); P.hp = Math.min(maxHp(), P.hp + Math.max(0, maxHp() - hpBefore));   // new health comes in full
      events.push({ type: 'gearPickup', slot: item.slot, rarity: item.rarity });
    }
    // something you bought goes on even when it is not better (the shop card warns you): into the empty place, else over your weakest piece of that kind
    function wearBought(item) {
      let at = GR.place(GEAR.worn, item);
      if (at < 0) at = GR.WEAR.map((w, i) => (w === item.slot ? i : -1)).filter((i) => i >= 0).sort((a, b) => GR.score(GEAR.worn[a]) - GR.score(GEAR.worn[b]))[0];
      wearAt(item, at);
    }
    // pick up: take the nearest gun or piece of gear lying within reach (with manualGuns on, only this press picks things up, so nothing is ever taken by accident; hearts and flames are still automatic)
    function pickUpGun(id) {
      if (Number.isInteger(id)) {                       // VR: the exact item your hand grabbed or pointed at, or nothing (never a different one)
        const q = pickups.find((o) => o.id === id);
        if (!q || (q.kind !== 'gun' && q.kind !== 'gear' && q.kind !== 'mod') || q.noPick > 0 || q.life <= 0) return;
        const d = Math.hypot(P.x - q.x, P.z - q.z); if (d >= cfg.grabReach || (d >= cfg.gunReach && !hasLOS(P.x, P.z, q.x, q.z))) return;
        if (q.kind === 'gun') takeGun(q); else if (q.kind === 'mod') takeMod(q); else { q.life = -1; wearBought(q.gear); }
        return;
      }
      let best = null, bd = cfg.gunReach;
      let bs = Infinity; const fx = Math.sin(P.yaw), fz = -Math.cos(P.yaw);
      for (const q of pickups) {
        if ((q.kind !== 'gun' && q.kind !== 'gear' && q.kind !== 'mod') || q.noPick > 0 || q.life <= 0) continue;
        const d = Math.hypot(P.x - q.x, P.z - q.z); if (d >= bd) continue;
        const ahead = d < 0.01 ? 1 : ((q.x - P.x) * fx + (q.z - P.z) * fz) / d;      // 1 = straight ahead of you, -1 = behind: with several on the floor, the one you are looking at wins
        const score = d * (1.6 - 0.6 * ahead); if (score < bs) { bs = score; best = q; }
      }
      if (!best) return;
      if (best.kind === 'gun') takeGun(best); else if (best.kind === 'mod') takeMod(best); else { best.life = -1; wearBought(best.gear); }   // a piece you picked up on purpose goes on, even over a better one
    }
    // a mod goes into the bag (six places); with a full bag it stays on the floor
    function takeMod(p) {
      if (W.mods.length >= WP.MD.BAG) { events.push({ type: 'bagFull' }); return; }
      p.life = -1; W.mods.push(p.mod); events.push({ type: 'modPickup', rarity: p.mod.rarity });
    }
    // bolt a mod from the bag onto the gun in a hand (0 or 1), or take one off and back into the bag. Returns '' when it worked, else the reason.
    function attachMod(bag, hand) {
      const gun = W.slots[hand], mod = W.mods[bag], why = WP.MD.why(gun, mod); if (why) return why;
      W.mods.splice(bag, 1); (gun.mods = gun.mods || []).push(mod); if (hand === W.held) P.ammo = Math.min(P.ammo, maxMag()); return '';
    }
    function detachMod(hand, at) {
      const gun = W.slots[hand]; if (!gun || !gun.mods || !gun.mods[at]) return 'nothing there';
      if (W.mods.length >= WP.MD.BAG) return 'bag full';
      W.mods.push(gun.mods.splice(at, 1)[0]); if (hand === W.held) P.ammo = Math.min(P.ammo, maxMag()); return '';
    }
    // put something away in the safe-room stash (kind 'gun' = a hand 0/1, 'gear' = a worn place 0-4, 'mod' = a bag place). Returns '' when done, else the reason.
    function stashItem(kind, at, label) {
      if (!cfg.stashOpen) return 'the stash is not open yet';
      if (!nearChest()) return 'stand next to the stash chest in the safe room';
      if (kind !== 'gun' && kind !== 'mod') return 'the stash holds guns and mods only';
      const have = R.stash.filter((e) => e.kind === kind).length, cap = kind === 'gun' ? ST.RULES.gunSlots : ST.RULES.modSlots;
      if (have >= cap) return kind === 'gun' ? 'the stash gun places are full (take one out first)' : 'the stash mod places are full (take one out first)';
      let item = null;
      if (kind === 'gun') {
        if (!W.slots[at]) return 'nothing there'; if (!W.slots[1 - at]) return 'keep at least one gun';
        if (at === W.held) swapGun();
        item = W.slots[at]; W.slots[at] = null; delete item.ammo; const nm = WP.cleanLabel(label); if (nm) item.label = nm; else if (label !== undefined) delete item.label;     // you may name the gun as you put it away; leave the name empty for its regular one
      } else if (kind === 'mod') {
        if (!W.mods[at]) return 'nothing there'; item = W.mods.splice(at, 1)[0];
      } else return 'unknown item';
      R.stash.push({ kind, item }); return '';
    }
    // take a stashed gun or mod back out (edit your stash as often as you like at the chest). A gun goes into the hand you name; if that hand holds a gun, the two swap places.
    function stashTake(i, hand) {
      if (!cfg.stashOpen) return 'the stash is not open yet';
      if (!nearChest() && !R.entry) return 'stand next to the stash chest in the safe room';
      const e = R.stash[i]; if (!e) return 'nothing there';
      const door = R.entry && !nearChest();                      // at the hall door you take a COPY and the stash keeps the original; at the chest you move the real thing
      const copy = (x) => JSON.parse(JSON.stringify(x));
      if (door && taken.has(i)) return 'you already took that';
      if (e.kind === 'mod') { if (W.mods.length >= 6) return 'your mod bag is full'; if (door) { W.mods.push(copy(e.item)); taken.add(i); } else { W.mods.push(e.item); R.stash.splice(i, 1); } return ''; }
      if (e.kind !== 'gun') return 'unknown item';
      if (R.entry && R.entryGun) return 'you can only take one gun into the hall';
      const h = hand === 1 ? 1 : 0, cur = W.slots[h];
      if (h === W.held && cur) cur.ammo = P.ammo;
      const it = door ? copy(e.item) : e.item; it.ammo = WP.stats(it, cfg).mag; W.slots[h] = it;
      if (door) { taken.add(i); if (cur && !W.slots[1 - h]) W.slots[1 - h] = cur; }          // at the hall's door your starting gun just moves to your back; the stash keeps its gun
      else if (cur && R.entry && !W.slots[1 - h]) { W.slots[1 - h] = cur; R.stash.splice(i, 1); }
      else if (cur) { delete cur.ammo; R.stash[i] = { kind: 'gun', item: cur }; } else R.stash.splice(i, 1);
      if (h === W.held) { P.ammo = maxMag(); P.reloading = false; P.reloadT = 0; P.fireCd = 0.35; }
      if (R.entry) R.entryGun = true;
      return '';
    }
    const nearChest = () => !!(R.safe && M0.chest && Math.hypot(P.x - M0.chest.x, P.z - M0.chest.z) < cfg.stashReach);
    // rename a gun that sits in the stash (an empty name goes back to the regular one)
    function stashRename(i, label) {
      const e = R.stash[i]; if (!e || e.kind !== 'gun') return 'nothing there'; if (!cfg.stashOpen) return 'the stash is not open yet'; if (!nearChest()) return 'stand next to the stash chest in the safe room';
      const nm = WP.cleanLabel(label); if (nm) e.item.label = nm; else delete e.item.label; return '';
    }
    // the stash outlives a run: the screen keeps it in the browser and hands it back with setStash; the live copy stays through every new run
    function setStash(list) { R.stash = (list || []).filter((e) => e && (e.kind === 'gun' || e.kind === 'mod') && e.item).map((e) => JSON.parse(JSON.stringify(e))); }
    const stashList = () => R.stash.map((e) => JSON.parse(JSON.stringify(e)));
    const stashView = () => ({ entry: !!R.entry, entryGun: !!R.entryGun, take: !!cfg.stashOpen && (nearChest() || !!R.entry), near: nearChest(), open: !!cfg.stashOpen && nearChest(), chest: R.safe && M0.chest ? { x: M0.chest.x, z: M0.chest.z } : null, size: ST.RULES.stashSize, gunSlots: ST.RULES.gunSlots, modSlots: ST.RULES.modSlots, items: R.stash.map((e, i) => ({ i, kind: e.kind, taken: taken.has(i), card: e.kind === 'gun' ? WP.view(e.item, cfg) : e.kind === 'gear' ? GR.view(e.item, null) : WP.modView(e.item) })) });
    function swapGun() {
      const other = 1 - W.held; if (!W.slots[other]) return;
      W.slots[W.held].ammo = P.ammo; W.held = other; P.ammo = W.slots[other].ammo;
      P.reloading = false; P.reloadT = 0; P.fireCd = 0.35;
      events.push({ type: 'swap', id: W.slots[W.held].id, rarity: W.slots[W.held].rarity });
    }

    /* ---------------- reload ---------------- */
    function startReload() {
      if (P.reloading || P.ammo >= maxMag() || kit.mods().freeAmmo) return;
      P.reloading = true; P.reloadT = 0; P.reloadEmpty = P.ammo <= 0;
      P.reloadDur = (gunStats().reload + (P.reloadEmpty ? cfg.reloadEmptyExtra : 0)) * M.reloadMul * kit.reloadMul(); kit.onReload();
      events.push({ type: 'reloadStart', dur: P.reloadDur, empty: P.reloadEmpty });
    }

    /* ---------------- shooting ---------------- */
    function castWall(ox, oy, oz, dx, dy, dz, maxT) {
      const stepLen = 0.12;
      for (let t = stepLen; t < maxT; t += stepLen) {
        const x = ox + dx * t, y = oy + dy * t, z = oz + dz * t;
        if (y < 0 || y > WALL_H || solid(Math.floor(x / CELL), Math.floor(z / CELL))) return t;
      }
      return maxT;
    }
    function raySphere(ox, oy, oz, dx, dy, dz, cx, cy, cz, r) {
      const lx = cx - ox, ly = cy - oy, lz = cz - oz;
      const tca = lx * dx + ly * dy + lz * dz;
      if (tca < 0) return -1;
      const d2 = lx * lx + ly * ly + lz * lz - tca * tca;
      if (d2 > r * r) return -1;
      return tca - Math.sqrt(r * r - d2);
    }

    function shoot() {
      const pe = clamp(P.pitch + P.kick, -1.5, 1.5);
      const speed = Math.hypot(P.vx, P.vz);
      const GS = gunStats();
      let s0 = lerp(cfg.spread, cfg.spreadAds, P.adsT) * GS.spread * (1 + speed / cfg.walkSpeed * 0.5);
      if (P.sliding) s0 *= 0.8;
      const sy = Math.sin(P.yaw), cy = Math.cos(P.yaw), sp = Math.sin(pe), cp = Math.cos(pe);
      const fx = sy * cp, fy = sp, fz = -cy * cp;
      const rx = cy, rz = sy;                              // right
      const ux = -sy * sp, uy = cp, uz = cy * sp;          // up
      const ex = P.x, ey = P.eye, ez = P.z;
      P.shotN = (P.shotN || 0) + 1; const charged = M.over > 0 && P.shotN % L.overEvery === 0; if (charged) events.push({ type: 'overcharge' });      // Overcharge: every 5th shot hits harder
      const vol = kit.beginShot(), bullets = GS.pellets + M.multi + vol.extra, dmgOne = GS.dmg * M.dmg * (R.frenzy > 0 ? L.frenzyDmg : 1) * (charged ? 1 + M.over : 1);
      for (let b = 0; b < bullets; b++) {
        const s = s0 + (b > 0 ? 0.02 : 0);
        const a = rng() * Math.PI * 2, rr = Math.sqrt(rng()) * s;
        const ox = Math.cos(a) * rr, oy = Math.sin(a) * rr;
        let dx = fx + rx * ox + ux * oy, dy = fy + uy * oy, dz = fz + rz * ox + uz * oy;
        const dl = Math.hypot(dx, dy, dz); dx /= dl; dy /= dl; dz /= dl;

        const wallT = castWall(ex, ey, ez, dx, dy, dz, cfg.range);
        let bestT = wallT, bestM = null, bestHead = false, sock = null;
        for (const m of monsters) {
          const k = D.KINDS[m.kind], sc = m.scale, mfx = Math.sin(m.yaw), mfz = -Math.cos(m.yaw);
          for (const sph of k.spheres) {
            const t = raySphere(ex, ey, ez, dx, dy, dz, m.x + mfx * sph.f * sc, sph.y * sc, m.z + mfz * sph.f * sc, sph.r * sc);
            if (t >= 0 && t < bestT) { bestT = t; bestM = m; bestHead = !!sph.head; }
          }
        }
        sock = LK.socketHit(ex, ey, ez, dx, dy, dz, bestT); if (sock) { bestT = sock.t; bestM = null; }      // a gold socket on the wall is in the way of this bullet
        const endx = ex + dx * bestT, endy = ey + dy * bestT, endz = ez + dz * bestT;
        events.push({
          type: 'shot', extra: b > 0, ox: ex, oy: ey, oz: ez, dx, dy, dz, t: bestT,
          ex: endx, ey: endy, ez: endz, hit: bestM ? 'monster' : (bestT >= cfg.range - 0.2 ? 'none' : 'wall')
        });
        if (cfg.coop) {                                                         // friends see this bullet too: where it started, where it ended, what it hit, and the gun look it came from
          const q2 = (v) => Math.round(v * 100) / 100, gn = W.slots[W.held], hit = bestM ? 2 : (bestT >= cfg.range - 0.2 ? 0 : 1);
          const rec = { ox: q2(ex), oy: q2(ey), oz: q2(ez), ex: q2(endx), ey: q2(endy), ez: q2(endz), hit, g: gn.id, r: gn.rarity, s: gn.status || [] };
          if (cfg.guest) { if (shotOut.length < 12) shotOut.push(rec); } else events.push(Object.assign({ type: 'peerShot', key: SELF.key }, rec));
        }
        if (sock) hitSocket(sock.i);
        if (bestM) {
          const crit = kit.rollCrit(vol.force) || (GS.crit + M.crit > 0 && rngW() < GS.crit + M.crit); if (crit) events.push({ type: 'crit' });
          const dmg = dmgOne * (bestHead ? cfg.headMul * (1 + GS.head) : 1) * (crit ? kit.critMul() + GS.critDmg + M.critDmg : 1);
          damageMonster(bestM, dmg, bestHead || crit, endx, endy, endz, false);
          kit.onHit(bestM, dmg, crit, endx, endy, endz);
          gfx.hit(bestM, dmg, W.slots[W.held]);
          if (M.blast > 0) {
            events.push({ type: 'blast', x: endx, y: endy, z: endz, r: L.blastRadius });
            for (const o of monsters.slice()) if (o !== bestM && Math.hypot(o.x - endx, o.z - endz) < L.blastRadius + 0.5 * o.scale) damageMonster(o, dmg * M.blast, false, o.x, 1.2 * o.scale, o.z, true);
          }
        }
      }
      P.kick += cfg.recoilKick;
      if (!kit.mods().freeAmmo) P.ammo--;
      if (P.ammo <= 0) startReload();
    }

    /* ---------------- monster behaviour ---------------- */
    // a ranged attacker (mushroom, eyeball, flame spirit, and the Demon Lord's fireball). Returns true when it is busy shooting, so the melee and chase code is skipped.
    // It keeps its distance (backs off when you are inside `keep`), stops while it has a clear shot, rears back for `wind` seconds, then throws; the throw is aimed where you stand
    // at that moment, so moving or sliding dodges it.
    function shooterStep(m, k, dt, dist, dx, dz) {
      const S = k.shoot;
      m.shMx = m.shMz = 0;
      if (m.state === 'cast') {
        m.shW -= dt; m.yawT = Math.atan2(dx, -dz);
        if (m.shW <= 0) {
          const sc = m.scale, ux = dx / (dist || 1), uz = dz / (dist || 1);
          mshots.fire({ ail: S.proj === 'fire' ? 'burn' : undefined, proj: S.proj, owner: m.id, x: m.x + ux * 0.6 * sc, y: S.y * sc, z: m.z + uz * 0.6 * sc, tx: P.x, tz: P.z, ty: P.eye - 0.35, speed: S.speed, r: S.r * Math.max(1, sc * 0.8), dmg: m.dmg * S.dmg });
          events.push({ type: 'shoot', proj: S.proj, id: m.id, x: m.x, z: m.z });
          m.state = 'chase'; m.shT = S.cd * (0.8 + rng() * 0.4) * (m.enraged ? k.enrage.pace : 1);
        }
        return true;
      }
      m.shT -= dt;
      const clear = dist < S.range && dist > (S.min || 0) && hasLOS(m.x, m.z, P.x, P.z);
      if (!clear) return false;
      if (m.shT <= 0) { m.state = 'cast'; m.shW = S.wind; return true; }
      if (S.keep && dist < S.keep) {                      // too close: back away while it waits to throw again
        const sp = m.spd0 * m.spd * gfx.slowOf(m) * 0.6; m.shMx = -dx / dist * sp; m.shMz = -dz / dist * sp; m.state = 'chase'; m.yawT = Math.atan2(dx, -dz);
        return true;
      }
      if (S.keep && dist < S.range) { m.state = 'chase'; m.yawT = Math.atan2(dx, -dz); return true; }   // in range with a clear shot: hold still and wait for the throw
      return false;
    }
    // Bounce Pad: landing from a good jump slams every monster around you (a share of your shot damage per stack) and rocks them for a moment
    function bounceSlam(p) {
      const dmg = gunStats().dmg * M.dmg * L.bounceDmg * M.bounce;
      events.push({ type: 'bounceSlam', x: p.x, z: p.z, r: L.bounceRadius });
      for (const o of monsters.slice()) if (Math.hypot(o.x - p.x, o.z - p.z) < L.bounceRadius + 0.4 * o.scale) { damageMonster(o, dmg, false, o.x, 1.2 * o.scale, o.z, true, false); if (o.hp > 0 && !D.KINDS[o.kind].boss) o.stun = Math.max(o.stun || 0, L.bounceStun); }
    }
    // hopping over a small monster: while your feet are high enough above its back, its blow passes under you (bosses and tall monsters cannot be hopped)
    const bodyTop = (k, sc) => k.spheres.reduce((h, s) => Math.max(h, s.y + s.r), 0) * sc;
    const hopped = (m, k) => { if (k.boss) return false; const top = bodyTop(k, m.scale); return top < L.hopMax && (P.jumpH || 0) >= top * L.hopFrac; };
    function updateMonster(m, dt) {
      const k = D.KINDS[m.kind], sc = m.scale;
      m.flash = Math.max(0, m.flash - dt);
      m.stun = Math.max(0, m.stun - dt);
      const dx = P.x - m.x, dz = P.z - m.z;
      const dist = Math.hypot(dx, dz) || 0.0001;
      const reach = L.meleeReachMul * sc + L.meleeReachAdd;
      let mvx = 0, mvz = 0;
      const was = m.state;
      if (m.state === 'guard') {                          // asleep on his feet at the door until you come into sight or hurt him
        if (m.hp < m.maxHp || (dist < (k.guard ? k.guard.wake : L.keeperWake) && hasLOS(m.x, m.z, P.x, P.z))) { m.state = 'chase'; m.shT = 0.4; events.push(m.mini ? { type: 'keeperWake' } : { type: 'bossWake', name: k.name }); }   // he opens the fight with a fireball
        else { m.yaw += clamp(angleDiff(m.yawT, m.yaw), -dt * 9, dt * 9); return; }
      }
      if (!k.boss && (gfx.frozen(m) || m.stun > 0.1)) { m.state = 'chase'; m.atk = k.wind; return; }     // frozen solid or smitten: it stands there and cannot swing, throw or walk (bosses shrug it off)
      if (k.summonAt && !m.summoned && m.hp <= m.maxHp * k.summonAt) {
        m.summoned = true;
        for (let i = 0; i < k.summonN; i++) spawnQ.unshift(k.summonKind);
        spawnTimer = 0;
        events.push({ type: 'bossSummon', x: m.x, z: m.z, text: k.summonText || 'HOUNDS CALLED' });
      }
      if (k.enrage && !m.enraged && m.hp <= m.maxHp * k.enrage.below) { m.enraged = true; m.spd0 *= k.enrage.speed; events.push({ type: 'bossEnrage', x: m.x, z: m.z, name: k.name }); }
      if (k.charge) m.chT -= dt * (m.enraged ? 1 / k.enrage.pace : 1);
      if ((k.moves || k.extra) && BO.step(m, k, dt, dist, dx, dz, reach)) {      // the Bat Lord, Lich King and Elder Dragon play their own moves
        mvx = m.bmx; mvz = m.bmz;
      } else if (m.state === 'windup') {                         // the boss rears back where it stands, then lunges
        m.wT -= dt; m.yawT = Math.atan2(dx, -dz);
        if (m.wT <= 0) { m.state = 'charge'; m.cT = k.charge.dur; m.cdx = dx / dist; m.cdz = dz / dist; }
      } else if (m.state === 'charge') {
        m.cT -= dt;
        const sp = m.spd0 * m.spd * gfx.slowOf(m) * k.charge.mult;
        mvx = m.cdx * sp; mvz = m.cdz * sp; m.yawT = Math.atan2(m.cdx, -m.cdz);
        if (dist < reach) { if (hopped(m, k)) { events.push({ type: 'hop', id: m.id }); } else hurtPlayer(m.dmg * k.charge.hit, m.id); m.cT = 0; }
        if (m.cT <= 0) { m.state = 'chase'; m.chT = k.charge.every; }
      } else if (k.charge && m.state !== 'cast' && m.chT <= 0 && dist > 3.5 && dist < 22 && hasLOS(m.x, m.z, P.x, P.z)) {
        m.state = 'windup'; m.wT = k.charge.windup;
      } else if (P === SELF && kit.cloaked() && !k.boss && m.state !== 'cast' && m.state !== 'attack') {
        m.state = 'lost'; m.yawT = m.yaw + Math.sin(time * 1.3 + m.phase) * 0.9;     // an Assassin's cloak: it cannot see you, so it stops and looks around
      } else if (k.shoot && shooterStep(m, k, dt, dist, dx, dz)) {
        // a ranged attacker: it stopped, or is stepping back, or is rearing back to throw (see shooterStep)
        mvx = m.shMx; mvz = m.shMz;
      } else {
        m.state = dist < (was === 'attack' ? reach * 1.2 : reach) ? 'attack' : 'chase';   // a little give, so a monster pushed by its friends keeps swinging
        if (m.state === 'attack') {
          if (was !== 'attack') m.atk = k.wind;                                          // the blow lands this long after it reaches you, no longer
          m.atk -= dt;
          if (m.atk <= 0) { m.atk = 1 / (cfg.monsterAttackRate * k.rate); if (dist < reach * 1.25) { if (hopped(m, k)) events.push({ type: 'hop', id: m.id }); else hurtPlayer(m.dmg, m.id); } }   // you can still step out of reach in the wind-up, or hop over a small monster
          m.yawT = Math.atan2(dx, -dz);
        } else {
          let dirx, dirz;
          const los = hasWideLOS(m.x, m.z, P.x, P.z);
          if (los) { dirx = dx / dist; dirz = dz / dist; }
          else {
            const d = flowDir(m.x, m.z);
            if (d) { dirx = d[0]; dirz = d[1]; } else { dirx = dx / dist; dirz = dz / dist; }
          }
          const sp = m.spd0 * m.spd * gfx.slowOf(m) * (m.stun > 0 ? 0.25 : 1);
          mvx = dirx * sp; mvz = dirz * sp;
          m.yawT = los ? Math.atan2(dx, -dz) : Math.atan2(dirx, -dirz);
        }
      }
      let sx = 0, sz = 0;
      const minD = MONSTER_RADIUS * 2 * Math.max(0.8, sc);
      for (const o of monsters) {
        if (o === m) continue;
        const ox = m.x - o.x, oz = m.z - o.z, dd = Math.hypot(ox, oz);
        if (dd > 0.001 && dd < minD) { const kk = (minD - dd) * 5 / dd; sx += ox * kk; sz += oz * kk; }
      }
      const mv = tryMove(m, (mvx + sx) * dt, (mvz + sz) * dt, MONSTER_RADIUS * Math.min(Math.max(sc, 0.8), 1.4));
      if (m.state === 'dash' && (mv.bx || mv.bz)) m.bm.t = 0;                             // a dive ends against a wall
      if (m.state === 'charge' && (mv.bx || mv.bz)) { m.cT = 0; m.state = 'chase'; m.chT = k.charge.every; }
      m.yaw += clamp(angleDiff(m.yawT, m.yaw), -dt * 9, dt * 9);
      m.phase += Math.hypot(mvx, mvz) * dt * 2.4 / Math.max(0.7, sc * 0.8);
    }

    /* ---------------- orbs and pickups ---------------- */
    // traps: 0 = harmless right now, 1 = warning, 2 = dangerous. Spikes are always up; a vent glows then fires; pulse spikes rise and sink.
    function trapState(t) {
      if (t.kind === 'spike') return 2;
      if (t.kind === 'pulse') { const u = (time + t.phase) % L.pulseEvery; return u < L.pulseUp - 0.25 ? 2 : u < L.pulseUp ? 1 : u > L.pulseEvery - 0.25 ? 1 : 0; }
      const u = (time + t.phase) % L.ventEvery;
      return u >= L.ventEvery - L.ventFire ? 2 : u >= L.ventEvery - L.ventFire - L.ventWarn ? 1 : 0;
    }
    const onTrap = (t, x, z) => x >= t.x * CELL - 0.2 && x <= (t.x + t.w) * CELL + 0.2 && z >= t.z * CELL - 0.2 && z <= (t.z + t.h) * CELL + 0.2;
    function updateTraps(dt) {
      const traps = M0.traps || [];
      if (!traps.length) return;
      P.trapCd = Math.max(0, (P.trapCd || 0) - dt);
      for (const m of monsters) if (m.trapCd > 0) m.trapCd = Math.max(0, m.trapCd - dt);
      const tier = cfg.trapTier || floorNo, pct = Math.min(L.trapMax, L.trapPct * (1 + L.trapScale * (tier - 1)));
      for (const t of traps) {
        if (trapState(t) !== 2) continue;
        if (!P.trapCd && !P.sliding && P.jumpH < 0.4 && onTrap(t, P.x, P.z)) { P.trapCd = L.trapTick; hurtPlayer(Math.max(1, Math.round(maxHp() * pct)), 'trap'); }
        if (!cfg.guest) for (const m of monsters.slice()) {
          if (m.trapCd || m.hp <= 0 || D.KINDS[m.kind].hover || !onTrap(t, m.x, m.z)) continue;
          m.trapCd = L.trapTick;
          damageMonster(m, Math.max(5, m.maxHp * L.trapMonsterPct * (D.KINDS[m.kind].boss ? L.trapBoss : 1)), false, m.x, 1, m.z, false, false);
        }
      }
    }
    function updateLoot(dt) {
      const reachMag = L.orbMagnet * M.magnet;
      for (const o of orbs) {
        o.life -= dt;
        const dx = P.x - o.x, dz = P.z - o.z, d = Math.hypot(dx, dz) || 0.001;
        if (d < reachMag) { const sp = (6 + (1 - d / reachMag) * 14) * dt; o.x += dx / d * Math.min(sp, d); o.z += dz / d * Math.min(sp, d); }
        if (d < L.orbPickup) { o.life = -1; events.push({ type: 'orb', v: o.v }); gainXp(o.v); }
      }
      orbs = orbs.filter((o) => o.life > 0);
      for (const c of coins) {
        c.life -= dt;
        const dx = P.x - c.x, dz = P.z - c.z, d = Math.hypot(dx, dz) || 0.001;
        if (d < L.coinMagnet * M.magnet) { const sp = (6 + (1 - d / (L.coinMagnet * M.magnet)) * 14) * dt; c.x += dx / d * Math.min(sp, d); c.z += dz / d * Math.min(sp, d); }
        if (d < L.coinPickup) { c.life = -1; const v = Math.round(c.v * (1 + M.goldMul)); R.gold += v; events.push({ type: 'coin', v }); }
      }
      coins = coins.filter((c) => c.life > 0);
      const reachPick = L.pickupRadius * (1 + (M.magnet - 1) * 0.5);
      for (const p of pickups) {
        if (!(cfg.keepDrops && (p.kind === 'gun' || p.kind === 'gear' || p.kind === 'mod'))) p.life -= dt; if (p.noPick > 0) p.noPick -= dt;   // (the test map keeps guns and gear on the floor until you take them)
        if (Math.hypot(P.x - p.x, P.z - p.z) < reachPick) {
          if (p.kind === 'gun') { if (p.noPick > 0 || cfg.manualGuns) continue; takeGun(p); continue; }
          if (p.kind === 'gear') { if (p.noPick > 0 || cfg.manualGuns) continue; takeGear(p); continue; }
          if (p.kind === 'mod') { if (p.noPick > 0 || cfg.manualGuns) continue; takeMod(p); continue; }
          p.life = -1;
          if (p.kind === 'heal') P.hp = Math.min(maxHp(), P.hp + L.healAmount); else R.frenzy = L.frenzyTime;
          events.push({ type: 'pickup', kind: p.kind });
        }
      }
      pickups = pickups.filter((p) => p.life > 0);
    }

    // what you have seen of this floor, for the minimap: every cell in line of sight within a few cells of you
    function reveal(p) {
      const pcx = clamp(Math.floor(p.x / CELL), 0, GW - 1), pcz = clamp(Math.floor(p.z / CELL), 0, GH - 1), pc = pcz * GW + pcx;
      if (pc === exploredCell) return;
      exploredCell = pc;
      const r = L.exploreRadius;
      for (let z = Math.max(0, pcz - r); z <= Math.min(GH - 1, pcz + r); z++) for (let x = Math.max(0, pcx - r); x <= Math.min(GW - 1, pcx + r); x++) {
        if (explored[z * GW + x] || (x - pcx) * (x - pcx) + (z - pcz) * (z - pcz) > r * r) continue;
        if (hasLOS(p.x, p.z, (x + 0.5) * CELL, (z + 0.5) * CELL)) explored[z * GW + x] = 1;
      }
    }

    /* ---------------- step ---------------- */
    function step(dt, inp) {
      dt = Math.min(Math.max(dt, 0), 0.05);
      events = pendingEv; pendingEv = [];                // (what happened between steps, like a friend's hit, is reported with this one)
      inp = inp || {};
      if (Number.isInteger(inp.lockUse) && !R.over && !R.down && !(R.choices || R.classChoices)) useLock(inp.lockUse);
      if (R.over) { if (inp.restart && !cfg.guest) { if (inp.seeds) setSeeds(inp.seeds); restartRun(); } return { state: snapshot(), events }; }
      let frozen = false;                                // co-op: a menu is open; your body stands still and can not be hurt, but the world keeps going
      const levelPending = !!(R.choices || R.classChoices);       // a level-up always comes first: the shop waits behind it, so a pick can never be eaten by the shop
      if (R.safe && M0.merchant && !levelPending) {                          // walk up to the merchant and the shop opens; step away and it can open again
        const md = Math.hypot(P.x - M0.merchant.x, P.z - M0.merchant.z);
        if (R.shop) {
          if (Number.isInteger(inp.pickClass)) shopBuy(inp.pickClass);
          if (Number.isInteger(inp.pick)) shopSupply(inp.pick);
          if (inp.shopClose) { R.shop = null; R.shopShut = true; }
          if (R.shop) { if (!cfg.coop) return { state: snapshot(), events }; frozen = true; }
        } else if (md > L.shopRadius + 1.5) R.shopShut = false;
        else if (md < L.shopRadius && !R.shopShut) { R.shop = true; if (!cfg.coop) return { state: snapshot(), events }; frozen = true; }
      }
      if (R.choices || R.classChoices) {                 // the level-up pause: nothing moves until a skill (and a class skill) is picked
        if (Number.isInteger(inp.pick)) pickSkill(inp.pick);
        if (Number.isInteger(inp.pickClass)) pickClass(inp.pickClass);
        if (!cfg.coop) return { state: snapshot(), events };
        if (R.choices || R.classChoices) frozen = true;
      }
      paused = frozen;
      time += dt; R.time += dt;
      R.fogK = clamp(R.fogK + (R.phase === 'fight' && R.fogOn ? dt : -dt) / L.fogRamp, 0, 1);   // fog thickens while a fog wave is on and lifts when it is cleared
      R.frenzy = Math.max(0, R.frenzy - dt);
      if (R.down) reviveStep(dt);
      personal(dt, frozen || R.down ? {} : inp);
      if (cfg.guest) guestStep(dt); else worldStep(dt);
      updateTraps(dt);
      updateLoot(dt);
      reveal(P);
      if (cfg.coop && !cfg.guest && R.down && ![...peers.values()].some((a) => !a.down) && !R.over) { R.over = { wave: R.wave, kills, level: R.level, time: R.time }; events.push({ type: 'dead' }); }   // everyone is down: the run is over

      return { state: snapshot(), events };
    }

    // you: look, move, slide, reload and fire
    function personal(dt, inp) {
      const p = SELF;
      // look
      const lookMul = 1 - p.adsT * (1 - cfg.adsLookMul);
      const padX = clamp(inp.padX || 0, -1, 1), padY = clamp(inp.padY || 0, -1, 1);
      p.yaw += ((inp.lookX || 0) * cfg.lookSens + (inp.touchX || 0) * cfg.touchSens + padX * cfg.padTurn * dt) * lookMul;
      p.pitch = clamp(p.pitch - ((inp.lookY || 0) * cfg.lookSens + (inp.touchY || 0) * cfg.touchSens + padY * cfg.padTurn * cfg.padPitchMul * dt) * lookMul, -1.45, 1.45);

      // move
      const fx = Math.sin(p.yaw), fz = -Math.cos(p.yaw), rx = Math.cos(p.yaw), rz = Math.sin(p.yaw);
      let mx = clamp(inp.mx || 0, -1, 1), mz = clamp(inp.mz || 0, -1, 1);
      const mag = Math.hypot(mx, mz);
      if (mag > 1) { mx /= mag; mz /= mag; }
      const wx = rx * mx + fx * mz, wz = rz * mx + fz * mz;
      const ads = !!inp.ads && !p.reloading;   // aiming drops while reloading
      p.sprinting = !!inp.sprint && mz > 0.25 && !ads && !p.sliding;
      const CM = kit.mods();                                       // the class bonuses (and a running ultimate)
      let top = (p.sprinting ? cfg.sprintSpeed : cfg.walkSpeed) * M.speed * CM.speed * AIL.speedMul();
      if (ads) top *= Math.min(1, cfg.adsSpeedMul * (1 + gunStats().adsMove));

      p.slideCd -= dt;
      // jump: leave the ground with a push up; you keep the sideways speed you had, and gravity brings you down
      if (inp.jump && !p.sliding && p.jumpH <= 0 && !R.down) { p.jumpV = cfg.jumpSpeed * (1 + L.bounceJump * M.bounce); p.peak = 0; events.push({ type: 'jump' }); }
      if (p.jumpV !== 0 || p.jumpH > 0) {
        p.jumpH += p.jumpV * dt; p.jumpV -= cfg.gravity * dt; p.peak = Math.max(p.peak || 0, p.jumpH);
        if (p.jumpH <= 0) { p.jumpH = 0; p.jumpV = 0; events.push({ type: 'land' }); if (M.bounce > 0 && p.peak >= L.bounceMin) bounceSlam(p); }
      }
      if (inp.slide && !p.sliding && p.slideCd <= 0 && p.jumpH <= 0) {
        const sp = Math.hypot(p.vx, p.vz), want = Math.hypot(wx, wz);       // a slide goes the way you hold the stick (forward, back or sideways), or the way you were already moving
        if (want > 0.3 || sp > cfg.walkSpeed * 0.5) {
          p.sliding = true; p.slideT = cfg.slideTime;
          p.sdx = want > 0.3 ? wx / want : p.vx / sp; p.sdz = want > 0.3 ? wz / want : p.vz / sp;
          p.slideCd = cfg.slideTime + cfg.slideCooldown;
          events.push({ type: 'slide' }); kit.slideStart();
        }
      }
      if (p.sliding) {
        p.slideT -= dt;
        const k = Math.max(p.slideT, 0) / cfg.slideTime;
        const sp = cfg.slideSpeed * (0.25 + 0.75 * k);
        p.vx = p.sdx * sp; p.vz = p.sdz * sp;
        if (p.slideT <= 0) p.sliding = false;
      } else {
        const tvx = wx * top, tvz = wz * top;
        const dvx = tvx - p.vx, dvz = tvz - p.vz, dl = Math.hypot(dvx, dvz), md = cfg.accel * dt;
        if (dl <= md) { p.vx = tvx; p.vz = tvz; } else { p.vx += dvx / dl * md; p.vz += dvz / dl * md; }
      }
      const mv = tryMove(p, p.vx * dt, p.vz * dt, 0.4);
      if (mv.bx) p.vx = 0;
      if (mv.bz) p.vz = 0;
      if (p.sliding && (mv.bx || mv.bz)) p.slideT = Math.min(p.slideT, 0.05);

      p.eye += ((p.sliding ? cfg.eyeSlide : cfg.eyeStand) + p.jumpH - p.eye) * Math.min(1, dt * 16);
      const ar = dt / (cfg.adsTime / (1 + gunStats().ads));
      p.adsT += clamp((ads ? 1 : 0) - p.adsT, -ar, ar);
      p.sprintK += ((p.sprinting ? 1 : 0) - p.sprintK) * Math.min(1, dt * 7);
      p.kick -= p.kick * Math.min(1, dt * 9);
      p.invuln = Math.max(0, p.invuln - dt);
      p.hurt = Math.max(0, p.hurt - dt);
      p.sinceHit += dt; AIL.update(dt, p.sliding);
      if (p.sinceHit > cfg.regenDelay && p.hp < maxHp() && !AIL.blocksHealing()) p.hp = Math.min(maxHp(), p.hp + (cfg.regen + M.regen) * dt);

      // reload, then fire
      if (p.ammo > maxMag()) p.ammo = maxMag();
      if (inp.swap) swapGun();
      if (inp.pickup && !R.over) pickUpGun(inp.pickupId);
      if (CM.freeAmmo) {                                         // Bullet Storm means no reloading: a reload already under way stops and the magazine is full, so the fire never stalls
        if (p.reloading) { p.reloading = false; p.reloadT = 0; events.push({ type: 'reloadEnd' }); }
        p.ammo = maxMag();
      } else if (inp.reload) startReload();
      if (p.reloading) {
        p.reloadT += dt;
        if (p.reloadT >= p.reloadDur) { p.reloading = false; p.ammo = maxMag(); events.push({ type: 'reloadEnd' }); }
      }
      p.fireCd = Math.max(p.fireCd - dt, -dt);                  // the leftover of a frame carries over (so the rate stays exact), but never more than one frame: a long reload must not store up a burst
      if (p.fireCd < 0 && !inp.fire) p.fireCd = 0;
      const interval = 1 / (gunStats().rate * M.rate * CM.rate * (R.frenzy > 0 ? L.frenzyRate : 1));
      let shots = 0;
      if (inp.fire && !p.reloading && p.ammo <= 0) startReload();
      while (inp.fire && !p.reloading && p.ammo > 0 && p.fireCd <= 0 && shots < 3) { shoot(); p.fireCd += interval; shots++; }

    }

    // the world, played by the host (or by a single player): monsters, waves, doors
    function worldStep(dt) {
      const p = SELF;
      // monsters, waves, loot
      flowTimer -= dt;
      const pc = clamp(Math.floor(p.z / CELL), 0, GH - 1) * GW + clamp(Math.floor(p.x / CELL), 0, GW - 1);
      if (pc !== flowCell || flowTimer <= 0) { buildFlow(p.x, p.z); flowTimer = 0.4; }
      for (const a of peers.values()) {                                        // co-op: every friend has their own flow field, so monsters find the nearest one
        a.flowTimer -= dt;
        const ac = clamp(Math.floor(a.z / CELL), 0, GH - 1) * GW + clamp(Math.floor(a.x / CELL), 0, GW - 1);
        if (ac !== a.flowCell || a.flowTimer <= 0) { aim(a, () => buildFlow(a.x, a.z)); a.flowTimer = 0.4; }
      }
      for (const m of monsters.slice()) if (!R.over) { if (peers.size) aim(pickTarget(m), () => updateMonster(m, dt)); else updateMonster(m, dt); }
      mshots.update(dt); kit.update(dt); gfx.update(dt);
      if (R.phase === 'fight') {
        spawnTimer -= dt;
        if (spawnTimer <= 0 && spawnQ.length && waveCount() < aliveMax()) {
          const heavyN = monsters.filter((m) => D.KINDS[m.kind].heavy).length;
          const shootN = monsters.filter((m) => D.KINDS[m.kind].shoot && !D.KINDS[m.kind].boss).length;
          const i = spawnQ.findIndex((kd) => (!D.KINDS[kd].heavy || D.KINDS[kd].boss || heavyN < L.heavyCap * RC.countMul(coopN())) && (!D.KINDS[kd].shoot || D.KINDS[kd].boss || shootN < L.shooterCap * RC.countMul(coopN())));
          if (i >= 0 && spawnFor(spawnQ[i])) { spawnQ.splice(i, 1); spawnTimer = L.spawnGap; } else spawnTimer = 0.3;
        }
        if (!spawnQ.length && !waveCount()) endWave();
      } else if (R.hold === 'door' && !doorOpen && !R.safe) {   // the boss is down but the door is still sealed by its puzzle: a few ordinary monsters keep coming, so there is always gold to earn
        sealedT -= dt;
        if (sealedT <= 0 && waveCount() < L.sealedAlive) { const kd = D.waveKinds(Math.max(1, R.wave - 1), rng, null).find((q) => !D.KINDS[q].boss && !D.KINDS[q].heavy); if (kd) spawnFor(kd); sealedT = L.sealedGap; }
      } else if (R.hold === 'door') {                     // the boss is down and the door is open: the next wave waits until you step through
        if (targets().some((t) => !t.down && G[clamp(Math.floor(t.z / CELL), 0, GH - 1)][clamp(Math.floor(t.x / CELL), 0, GW - 1)] === 'd')) { if (R.safe) nextFloor(); else enterSafe(); }
      } else {
        R.timer -= dt;
        if (R.timer <= 0) startWave();
      }
    }
    // a friend's copy has no world of its own: the monsters are the host's, so only your own effects tick here (the flow is for the gold trail to the boss)
    function guestStep(dt) {
      for (const m of monsters) {
        m.x += (m.tx - m.x) * Math.min(1, dt * 14); m.z += (m.tz - m.z) * Math.min(1, dt * 14);
        m.yaw += angleDiff(m.tyaw, m.yaw) * Math.min(1, dt * 14);
        m.flash = Math.max(0, m.flash - dt); m.stun = Math.max(0, m.stun - dt);
      }
      if (monsters.some((m) => m.state === 'guard')) {
        flowTimer -= dt;
        const pc = clamp(Math.floor(P.z / CELL), 0, GH - 1) * GW + clamp(Math.floor(P.x / CELL), 0, GW - 1);
        if (pc !== flowCell || flowTimer <= 0) { buildFlow(P.x, P.z); flowTimer = 0.4; }
      }
      kit.update(dt); gfx.update(dt);
    }

    // how far a monster's wind-up has got: the boss's own moves, or a ranged monster rearing back
    const titleOf = (kind, v) => (v ? VR.VARIANTS[v].name + ' ' : '') + D.KINDS[kind].name;       // 'Frost Lich King'
    function castOf(m, k) {
      const v = k.moves || k.extra ? BO.view(m, k).k : 0;
      return v > 0 || k.moves ? v : (m.state === 'cast' && k.shoot ? clamp(1 - m.shW / k.shoot.wind, 0, 1) : 0);
    }
    function snapshot() {
      const p = P;
      const ease = p.adsT * p.adsT * (3 - 2 * p.adsT);
      const boss = monsters.find((m) => D.KINDS[m.kind].boss);
      return {
        t: time, kills, deaths,
        player: {
          x: p.x, z: p.z, yaw: p.yaw, pitch: clamp(p.pitch + p.kick, -1.5, 1.5), eye: p.eye,
          fov: lerp(cfg.fovBase, cfg.fovAds, ease) + cfg.sprintFovAdd * p.sprintK,
          adsT: p.adsT, sprintK: p.sprintK, sprinting: p.sprinting, sliding: p.sliding,
          slideK: p.sliding ? p.slideT / cfg.slideTime : 0,
          vx: p.vx, vz: p.vz, speed: Math.hypot(p.vx, p.vz),
          hp: p.hp, maxHp: maxHp(), hurt: p.hurt, kick: p.kick, ail: AIL.view(),
          ammo: p.ammo, magSize: maxMag(), reloading: p.reloading,
          stash: stashView(), gear: gearView(), mods: W.mods.map((m) => WP.modView(m, W.slots[W.held])),
          gun: { id: W.slots[W.held].id, rarity: W.slots[W.held].rarity, name: W.slots[W.held].label || WP.GUNS[W.slots[W.held].id].name, status: W.slots[W.held].status, held: W.held, card: WP.view(W.slots[W.held], cfg), other: W.slots[1 - W.held] ? { card: WP.view(W.slots[1 - W.held], cfg), id: W.slots[1 - W.held].id, rarity: W.slots[1 - W.held].rarity, ammo: W.slots[1 - W.held].ammo } : null },
          reloadK: p.reloading ? clamp(p.reloadT / p.reloadDur, 0, 1) : 0,
          reloadEmpty: p.reloadEmpty, reloadDur: p.reloadDur
        },
        monsters: monsters.map((m) => ({
          id: m.id, kind: m.kind, x: m.x, z: m.z, yaw: m.yaw, hp: m.hp, maxHp: m.maxHp,
          flash: m.flash, state: m.state, phase: m.phase, scale: m.scale, elite: m.elite,
          enraged: !!m.enraged, variant: m.variant || null, exposed: !!m.exposed, poisoned: !!(m.fx && m.fx.poison), bleeding: !!(m.fx && m.fx.bleed), cursed: !!(m.fx && m.fx.hexT > 0), gx: gfx.view(m),
          atkK: m.net ? m.atkKv : m.state === 'attack' ? clamp(1 - m.atk / D.KINDS[m.kind].wind, 0, 1) : 0,              // 0 to 1 as a melee blow winds up; resets when it lands (the screen raises the weapon with it)
          castK: m.net ? m.castKv : castOf(m, D.KINDS[m.kind])           // the same for a ranged monster rearing back to throw
        })),
        floor: floorNo, floorId: M0.id,
        door: { x: M0.door.x, z: M0.door.z, open: doorOpen },
        locks: locksView(),
        traps: (M0.traps || []).map(trapState),
        gold: R.gold, coins: coins.map((c) => ({ id: c.id, x: c.x, z: c.z, v: c.v })),
        safe: R.safe, merchant: R.safe && M0.merchant ? { x: M0.merchant.x, z: M0.merchant.z } : null,
        shop: R.shop && !(R.choices || R.classChoices) ? {
          skills: R.stock.map((sid, i) => sid ? Object.assign(kit.card(sid, R.level), { price: skillPrice(sid), afford: R.gold >= skillPrice(sid), slot: i }) : null).filter(Boolean),
          supplies: supplyList().map((e) => e.kind === 'mend' ? { id: 'mend', name: 'Mend', desc: 'Heal to full health', price: L.shopHeal, afford: R.gold >= L.shopHeal && P.hp < maxHp() } : e.kind === 'leave' ? { id: 'leave', name: 'Leave', desc: 'Back to the room', price: 0, afford: true } : e.kind === 'gear' ? gearCard(e.item, e.slot) : gunCard(e.item, e.slot))
        } : null,
        bossFx: cfg.guest ? (R.netBossFx || []) : boss && (D.KINDS[boss.kind].moves || D.KINDS[boss.kind].extra) ? BO.view(boss, D.KINDS[boss.kind]).warn : [],      // floor warnings the screen draws (rings, lanes) so each attack can be dodged
        trail: boss && boss.state === 'guard' ? trailTo(boss) : null,      // the walking route from you to him, for the gold line on the map
        compass: boss && boss.state === 'guard' ? { x: boss.x, z: boss.z } : null,      // points at the boss from the moment he spawns until the fight with him starts
        explored,
        fog: { k: R.fogK, mul: 1 + (L.fogMul - 1) * R.fogK },      // how thick the fog is, and the fraction of the normal view distance you can see
        shots: cfg.guest ? (R.netShots || []) : mshots.view(),
        coop: { on: !!cfg.coop, n: coopN(), max: RC.RULES.maxPlayers, down: !!R.down, reviveK: reviveK(), key: SELF.key, peers: cfg.guest ? (R.others || []) : Array.from(peers.values()).map(peerSnap) },
        wave: { n: R.wave, phase: R.phase, timer: Math.max(0, R.timer), left: cfg.guest ? (R.netLeft || 0) : spawnQ.length + waveCount(), boss: R.phase === 'fight' ? !!boss || spawnQ.some((kd) => D.KINDS[kd].boss) : R.wave % L.bossEvery === 0 },
        bossBar: boss ? { name: titleOf(boss.kind, boss.variant), variant: boss.variant || null, exposed: !!boss.exposed, hp: boss.hp, maxHp: boss.maxHp, state: boss.state } : null,
        level: { n: R.level, xp: R.xp, need: D.xpNeed(R.level) },
        orbs: orbs.map((o) => ({ id: o.id, x: o.x, z: o.z, v: o.v })),
        pickups: pickups.map((q) => ({ id: q.id, kind: q.kind, x: q.x, z: q.z, life: q.life, gun: q.item ? WP.view(q.item, cfg) : undefined, grab: (q.kind === 'gun' || q.kind === 'gear' || q.kind === 'mod') && q.noPick <= 0, inReach: (q.kind === 'gun' || q.kind === 'gear' || q.kind === 'mod') && q.noPick <= 0 && Math.hypot(P.x - q.x, P.z - q.z) < cfg.gunReach, gear: q.gear ? GR.view(q.gear, GEAR.worn) : undefined, mod: q.mod ? WP.modView(q.mod, W.slots[W.held]) : undefined })),
        classChoices: R.classChoices ? R.classChoices.map((id) => kit.card(id, R.level)) : null,
        cls: kit.view(R.level),
        choices: R.choices ? R.choices.map((id) => { const s = skillOf(id); return { id, name: s.name, desc: s.desc, stack: stackOf(id), max: s.max }; }) : null,
        skills: D.SKILLS.filter((s) => stackOf(s.id) > 0).map((s) => ({ id: s.id, name: s.name, n: stackOf(s.id) })),
        frenzy: R.frenzy,
        over: R.over
      };
    }

    // what the screen needs to draw the gold gates, the boss door's sign and puzzle, and the prompt when you stand at one
    function locksView() {
      const lay = LK.layout, S = LK.S, b = lay.boss, n = R.over || R.down ? null : LK.near(P.x, P.z, R.gold, R.keys);
      return {
        gates: lay.gates.map((g) => ({ i: g.id, x: g.x, z: g.z, nx: g.nx, nz: g.nz, open: !!S.open[g.id], price: g.price, type: g.type })),
        boss: b ? { kind: b.kind, solved: S.solved, sign: b.sign, station: b.station, text: RL.signText(b), target: b.target, pan: S.pan, spin: b.spin, sym: b.sym, wheels: S.wheels.slice(), locked: S.locked.slice(), sockets: b.sockets.map((q, i) => ({ x: q.x, y: q.y, z: q.z, nx: q.nx, nz: q.nz, hit: !!S.hit[i] })) } : null,
        keys: R.keys, keeper: (() => { const q = monsters.find((o) => o.mini); return q ? { x: q.x, z: q.z, asleep: q.state === 'guard' } : null; })(),
        near: n, sealed: bossDown && !doorOpen && !R.safe,
        door: M0.door ? { x: M0.door.x, z: M0.door.z, nx: M0.door.nx, nz: M0.door.nz, open: doorOpen, near: !doorOpen && !R.safe && nearDoor(), canOpen: !!cfg.doorTest && !doorOpen && !R.safe,
          text: doorOpen ? 'Open' : cfg.doorTest ? 'Test map: grip opens it' : !bossDown ? 'Sealed: kill the boss to open it' : 'Sealed: solve the puzzle beside it' } : null
      };
    }
    // put the player somewhere (tests and tools only: the game never teleports you)
    function place(x, z, yaw) { P.x = x; P.z = z; if (yaw !== undefined) P.yaw = yaw; P.vx = P.vz = 0; flowCell = -1; }
    // put a monster somewhere (tests and tools only)
    function spawnAt(kind, x, z) { addMonster(kind, x, z); }
    let forceVariant = null;
    function spawnVariant(kind, x, z, v) { forceVariant = v; addMonster(kind, x, z); forceVariant = null; }   // for tests: a monster of this variant right here
    function spawnElite(kind, x, z) { forceElite = true; addMonster(kind, x, z); forceElite = false; }   // for tests: an elite right here
    function setCfg(o) { Object.assign(cfg, o); }
    function clearWave() { spawnQ = []; for (const m of monsters.slice()) killMonster(m); }   // tests: the wave is over right now
    function solveLocks() { LK.load({ o: LK.layout.gates.map(() => 1), s: 1 }); syncGates(); tryOpenDoor(); }   // tests: every gate stands open and the boss door's puzzle is solved
    const lockState = () => LK;                                                       // tests: the floor's locks
    function giveGold(v) { R.gold += v; }                                               // tests: some gold right now
    function giveXp(v) { gainXp(v); }                                                  // tests: some experience right now
    function giveGun(id, rarity, wave, x, z) { dropGun(x === undefined ? P.x : x, z === undefined ? P.z : z, 0, WP.make(id, rarity, wave || R.wave, rngW, cfg.classId)); }   // tests: a gun lies at your feet
    function equipGun(id, rarity) {                                                     // cheat build and tests: the gun in your hands becomes this one, full magazine
      const it = WP.make(id, rarity || 0, R.wave, rngW, cfg.classId); it.ammo = WP.stats(it, cfg).mag; W.slots[W.held] = it; P.ammo = maxMag(); P.reloading = false; P.reloadT = 0; P.fireCd = 0.3;
    }
    function gearView() { const t = GR.total(GEAR.worn); return { worn: GEAR.worn.map((it, i) => it ? GR.view(it, null) : { slot: GR.WEAR[i], empty: true }), def: Math.round(t.def * 1000) / 10, hp: Math.round(t.hp), vit: Math.round(t.vit * 100), regen: Math.round(t.regen * 10) / 10, speed: Math.round(t.speed * 100), magnet: Math.round(t.magnet * 100), dmg: Math.round(t.dmg * 100), rate: Math.round(t.rate * 100), crit: Math.round(t.crit * 1000) / 10, critdmg: Math.round(t.critdmg * 100), leech: Math.round(t.leech * 10) / 10, reload: Math.round(t.reload * 100) }; }
    function giveGear(slot, rarity, wave, x, z) { dropGear(x === undefined ? P.x : x, z === undefined ? P.z : z, 0, GR.make(slot, rarity, wave || R.wave, rngW, cfg.classId)); }   // tests: a piece of gear lies at your feet
    function wearGear(item, at) { GEAR.worn[at === undefined ? GR.WEAR.indexOf(item.slot) : at] = item; M = computeMods(); P.hp = Math.min(P.hp, maxHp()); }   // tests: wear exactly this piece
    function equipItem(item) { const it = Object.assign({}, item); it.ammo = WP.stats(it, cfg).mag; W.slots[W.held] = it; P.ammo = maxMag(); P.reloading = false; P.reloadT = 0; P.fireCd = 0; }   // tests: hold exactly this gun item (with the affixes it carries)
    function giveMod(rarity, wave, x, z) { dropMod(x === undefined ? P.x : x, z === undefined ? P.z : z, WP.MD.make(rarity, wave || R.wave, rngW)); }   // tests: a mod lies at your feet
    function addMod(item) { W.mods.push(item); }                                       // tests: this exact mod goes straight in the bag
    function setLoadout(list) { loadout = (list || []).map((e) => JSON.parse(JSON.stringify(e))); }   // blueprints for the next run (applied on reset)
    function stashEntry(i) { return R.stash[i] ? JSON.parse(JSON.stringify(R.stash[i])) : null; }   // a copy of a stashed entry, for making a blueprint
    function setHp(v) { P.hp = v; }                                                    // tests: set the player's health
    function giveGift(id, n) { R.stacks[id] = n === undefined ? stackOf(id) + 1 : n; M = computeMods(); }          // tests: this level-up gift, this many times
    function giveSkill(id) { kit.pick(id); }                                           // tests: hand the player a class skill
    function monsterFx(i) { return monsters[i] && monsters[i].fx; }                     // tests: statuses on a monster
    // the three seeds: map (floors and fog), damage (fight dice) and item (drops and the merchant's stock). Any of them can be replaced; the run restarts on the next reset.
    function setSeeds(s) {
      if (s.map) { seed0 = SEEDS.map = s.map | 1; }
      if (s.damage) { SEEDS.damage = s.damage | 1; rng = makeRng(SEEDS.damage); }
      if (s.item) { SEEDS.item = s.item | 1; rngW = makeRng(SEEDS.item); }
    }
    // a save, written in a safe room (null anywhere else, or while a level-up is waiting): everything that makes the run yours, plus the MAP seed. It never holds the damage or item seeds.
    function saveData() {
      if (cfg.coop || !R.safe || R.over || R.choices || R.classChoices || R.pending) return null;
      const held = W.slots[W.held]; if (held) held.ammo = P.ammo;
      return JSON.parse(JSON.stringify({ v: 1, mapSeed: SEEDS.map, classId: cfg.classId, wave: R.wave, floor: floorNo, level: R.level, xp: R.xp, stacks: R.stacks, gold: R.gold, hp: P.hp, kills, time: R.time,
        kit: kit.save(), guns: W.slots, held: W.held, mods: W.mods, gear: GEAR.worn, stash: R.stash }));
    }
    // go back to a save: the same map seed, so the same floors; fresh damage and item seeds (pass them in), so the luck is new. The merchant's stock is rolled again too.
    function loadData(d, luck) {
      if (!d || d.v !== 1) return false;
      setSeeds({ map: d.mapSeed, damage: luck && luck.damage, item: luck && luck.item });
      cfg.classId = d.classId; restartRun(); const c = (x) => JSON.parse(JSON.stringify(x));
      R.wave = d.wave; R.level = d.level; R.xp = d.xp; R.stacks = c(d.stacks); R.time = d.time; kills = d.kills; kit.load(d.kit);
      W.slots = c(d.guns); W.held = d.held; W.mods = c(d.mods); GEAR.worn = c(d.gear); R.stash = c(d.stash);
      M = computeMods(); loadFloor(d.floor); enterSafe(); R.gold = d.gold;
      P.hp = Math.min(d.hp, maxHp()); const g = W.slots[W.held]; P.ammo = g && g.ammo !== undefined ? g.ammo : maxMag();
      events.push({ type: 'loaded' }); return true;
    }
    function reset() { deaths = 0; restartRun(); events = []; }

    newRun(); startFloor(); placePlayer();
    // first state, so the screen can draw before the first step
    return { get map() { return M0; }, cfg, setCfg, place, spawnAt, spawnElite, spawnVariant, clearWave, giveSkill, giveGold, giveXp, setHp, giveGun, equipGun, equipItem, giveGift, stashTake, stashRename, setStash, stashList, giveGear, wearGear, seeds: () => Object.assign({}, SEEDS), setSeeds, saveData, loadData, giveMod, addMod, attachMod, detachMod, stashItem, setLoadout, stashEntry, monsterFx, step, snapshot, reset, remoteJoin, remoteLeave, remoteState, remoteDamage, worldView, remoteShots, shotsOut, remoteLocks, locksOut, solveLocks, lockState, selfState, guestOut, applyWorld, kinds: D.KINDS, defaults: Object.assign({}, DEFAULT_CFG) };
  }

  return { create };
})();

if (typeof module !== 'undefined') module.exports = Referee;
