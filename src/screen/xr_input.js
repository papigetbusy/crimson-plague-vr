/* Meta Quest (WebXR) controller input: turns the two Touch controllers into one "standard" gamepad, so the game's existing
   controller code (pad_input.js) drives moving, firing and the rest. Pure logic, no DOM and no clock, so tests can feed it fake controllers.
   The scheme follows Meta's locomotion input map and common VR shooters (Pavlov, Contractors, H3VR), see docs/vr-design.md.

   Quest Touch (xr-standard mapping)       -> game action
     Left stick                            -> move (toward your head's facing), radial deadzone
     Left stick click / stick fully fwd    -> sprint
     Left trigger                          -> aim down sights (xr_mode raises the gun to your eye)
     Left grip near the gun (xr_mode)      -> support hand: steadies and steers the barrel
     Double-tap Y (xr_mode)                -> floor map on / off (a tap of Y also closes it)
     X                                     -> reload
     Y  tap / hold 0.5 s                   -> pause / Gear menu      (in any VR menu: back)
     Right stick left/right (xr_mode)      -> turn (only when sideways is clearly the main direction)
     Right stick up/down                   -> scroll menus; a hard push down = second action at a gold gate / boss door puzzle
     Right stick click                     -> swap guns
     Right trigger                         -> fire (menus: click where the laser points, on release)
     Either grip (xr_interact / xr_grab)   -> grab what the hand reaches or points at, or use the gate / door / chest you stand at
     Right hand over right shoulder + grip -> swap to the gun on your back
     A                                     -> jump   (never from a stick: stick jumps fire by accident)
     B                                     -> slide
   No D-pad on Quest. */
const XrInput = (function () {
  const XR = { TRIGGER: 0, GRIP: 1, STICK: 3, LOW: 4, HIGH: 5 };   // xr-standard button order; LOW = A/X, HIGH = B/Y
  const STICK_X = 2, STICK_Y = 3;                                   // xr-standard axes for the thumbstick
  const TURN_DEAD = 0.12, TURN_EXP = 1.3, SNAP_ON = 0.7, SNAP_OFF = 0.35, SNAP_ANGLE = Math.PI / 4, MOVE_DEAD = 0.15, DOMINANCE = 1.3, GATE_PUSH = 0.85, Y_HOLD = 0.5;
  // pause-menu turn speed (Slow / Normal / Fast). A ?turn= or ?snap=N link flag, when present, still wins.
  const TURN_RATE = { slow: 2.5, normal: 4.5, fast: 7 };
  const SNAP_DEG = { slow: 30, normal: 45, fast: 60 };
  const TURN_RATES = ['slow', 'normal', 'fast'];
  const parseTurnRate = (v) => (TURN_RATES.indexOf(v) >= 0 ? v : 'normal');
  const nextTurnRate = (v) => TURN_RATES[(TURN_RATES.indexOf(parseTurnRate(v)) + 1) % 3];
  const smoothTurn = (rate, flag) => (flag != null ? flag : (TURN_RATE[parseTurnRate(rate)]));
  const snapTurnDeg = (rate, flag) => (flag != null ? flag : (SNAP_DEG[parseTurnRate(rate)]));

  const pressed = (gp, i) => { const b = gp && gp.buttons && gp.buttons[i]; return !!b && (b.pressed || b.value > 0.35); };
  const value = (gp, i) => { const b = gp && gp.buttons && gp.buttons[i]; return b ? (b.value || (b.pressed ? 1 : 0)) : 0; };
  const ax = (gp, i) => (gp && gp.axes && typeof gp.axes[i] === 'number' ? gp.axes[i] : 0);
  // Quest reports the stick on axes 2/3; very old runtimes used 0/1
  const stick = (gp, k) => (gp && gp.axes && gp.axes.length >= 4 ? ax(gp, k + 2) : ax(gp, k));

  // left stick with a radial deadzone, rescaled so movement still starts gently just past it (hides worn-stick drift)
  function moveStick(gp) {
    const x = stick(gp, 0), y = stick(gp, 1), m = Math.hypot(x, y);
    if (m <= MOVE_DEAD) return [0, 0];
    const k = Math.min(1, (m - MOVE_DEAD) / (1 - MOVE_DEAD)) / m;
    return [x * k, y * k];
  }
  // right stick split by its main direction: sideways turns, up/down scrolls (never both, so a forward push cannot turn and a turn cannot scroll)
  function rightStick(gp) {
    const x = stick(gp, 0), y = stick(gp, 1), sx = Math.abs(x) > Math.abs(y) * DOMINANCE ? x : 0, sy = Math.abs(y) > Math.abs(x) * DOMINANCE ? y : 0;
    return { x: sx, y: sy };
  }
  // Y: a tap pauses (fires on release), a 0.5 s hold opens Gear (fires once while held). Returns { tap, hold } for this frame.
  // Y: tap = pause, hold 0.5 s = Gear, double-tap = map. A single tap waits DOUBLE_GAP after release to be sure no second tap follows
  // (pausing 0.3 s late is harmless; a map that pops up uninvited is not). `up` is the raw release, used for "back" inside menus.
  const DOUBLE_GAP = 0.3;
  function createY() {
    let t = 0, down = false, held = false, wait = -1, second = false;
    function step(on, dt) {
      let tap = false, hold = false, dbl = false, up = false;
      if (wait >= 0) { wait += dt; if (wait > DOUBLE_GAP && !down) { wait = -1; tap = true; } }
      if (on) {
        if (!down) { down = true; t = 0; held = false; second = wait >= 0 && wait <= DOUBLE_GAP; if (second) wait = -1; }
        t += dt; if (!held && !second && t >= Y_HOLD) { held = true; hold = true; }
      } else if (down) { down = false; if (!held) { up = true; if (second) dbl = true; else wait = 0; } second = false; }
      return { tap, hold, double: dbl, up, holding: down && !held && !second, progress: down && !held && !second ? Math.min(1, t / Y_HOLD) : 0 };
    }
    return { step, reset: () => { down = false; held = false; t = 0; wait = -1; second = false; } };
  }
  // sources: list of { handedness: 'left'|'right', gamepad }. o: { y: createY output for this frame, menu: a VR menu is open }.
  // Returns a Gamepad-shaped object pad_input.js can read, or null.
  function toPad(sources, o) {
    o = o || {};
    let L = null, R = null;
    for (const s of sources || []) { if (!s || !s.gamepad) continue; if (s.handedness === 'left') L = s.gamepad; else if (s.handedness === 'right') R = s.gamepad; }
    if (!L && !R) return null;
    const btn = (on, v) => ({ pressed: !!on, value: v !== undefined ? v : (on ? 1 : 0) });
    const y = o.y || { tap: false, hold: false }, rs = rightStick(R), mv = moveStick(L), menu = !!o.menu;
    const b = new Array(16);
    b[0] = btn(!menu && pressed(R, XR.LOW));        // pad A = jump: A (Meta's locomotion map). Not in menus (the trigger picks there)
    b[1] = btn(!menu && pressed(R, XR.HIGH));       // pad B = slide: B
    b[2] = btn(!menu && pressed(L, XR.LOW));        // pad X = reload: X
    b[3] = btn(!menu && pressed(R, XR.STICK));      // pad Y = swap guns: right stick click
    b[4] = btn(false);                              // LB: the right grip is read as a grab by the VR view instead (pick up / use)
    b[5] = btn(!menu && y.hold);                    // RB (Gear menu): hold Y
    b[6] = btn(!menu && pressed(L, XR.TRIGGER), menu ? 0 : value(L, XR.TRIGGER));   // LT (aim)
    b[7] = btn(!menu && pressed(R, XR.TRIGGER), menu ? 0 : value(R, XR.TRIGGER));   // RT (fire)
    b[8] = btn(false);                              // Back (big map): in VR double-tap Y toggles the map (xr_mode.js)
    b[9] = btn(!menu && y.tap);                     // Start (pause): tap Y. In a menu xr_mode turns Y into "back"
    b[10] = btn(pressed(L, XR.STICK));              // L3 (sprint)
    b[11] = btn(false);                             // R3
    b[12] = btn(false); b[13] = btn(!menu && rs.y > GATE_PUSH);   // D-pad down = a hard push down on the right stick (gate second action)
    b[14] = btn(false); b[15] = btn(false);
    return { id: 'quest-touch', connected: true, mapping: 'standard', axes: [mv[0], mv[1], 0, 0], buttons: b };
  }

  // right-stick turning, done on the XR side so the body turns but your head and hand still aim freely
  function createTurn(snap, snapAngle) {
    const SNAP = snapAngle || SNAP_ANGLE;
    let armed = true;
    // returns radians to add to the body yaw this frame
    function step(gpRight, dt, speed) {
      const x = rightStick(gpRight).x;
      if (!snap) { const m = Math.abs(x); return m <= TURN_DEAD ? 0 : Math.sign(x) * Math.pow((m - TURN_DEAD) / (1 - TURN_DEAD), TURN_EXP) * speed * dt; }   // almost linear: a half push is close to half speed; 0.12 deadzone hides a resting stick
      if (armed && Math.abs(x) >= SNAP_ON) { armed = false; return Math.sign(x) * SNAP; }
      if (Math.abs(x) <= SNAP_OFF) armed = true;
      return 0;
    }
    return { step, reset: () => { armed = true; } };
  }

  // a world direction -> the game's yaw / pitch (yaw 0 looks down -z, positive yaw turns right; pitch up is positive)
  function dirToAngles(x, y, z) {
    const l = Math.hypot(x, y, z) || 1;
    return { yaw: Math.atan2(x / l, -z / l), pitch: Math.asin(Math.max(-1, Math.min(1, y / l))) };
  }
  const wrap = (a) => { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; };
  // the mouse-style look input that moves the player's aim from (yaw, pitch) to the target in one referee step
  function lookToward(cur, target, lookSens, lookMul) {
    const k = lookSens * (lookMul || 1);
    return { lookX: wrap(target.yaw - cur.yaw) / k, lookY: (cur.pitch - Math.max(-1.45, Math.min(1.45, target.pitch))) / k };
  }
  // stick movement turned from the aim's frame into the head's frame (dYaw = head yaw - aim yaw), so you walk where you look
  function headMove(mx, mz, dYaw) {
    const c = Math.cos(dYaw), s = Math.sin(dYaw);
    return { mx: mx * c + mz * s, mz: mz * c - mx * s };
  }
  // auto-sprint: the left stick pushed almost all the way forward runs, like most VR shooters
  const autoSprint = (mz, mx) => mz > 0.85 && Math.abs(mx) < 0.5;
  return { createY, rightStick, moveStick, autoSprint, headMove, toPad, createTurn, dirToAngles, lookToward, wrap, SNAP_ANGLE, TURN_DEAD, TURN_RATE, SNAP_DEG, parseTurnRate, nextTurnRate, smoothTurn, snapTurnDeg };
})();
if (typeof module !== 'undefined') module.exports = XrInput;
