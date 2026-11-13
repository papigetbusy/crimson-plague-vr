// Meta Quest controller checks: the Touch controllers as one standard pad (VR shooter layout), turning, aim maths.
const XrInput = require('../src/screen/xr_input.js');
const PadInput = require('../src/screen/pad_input.js');
let bad = 0;
const t = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) bad++; };
// a fake Touch controller in xr-standard layout: buttons 0 trigger, 1 grip, 3 stick click, 4 A/X, 5 B/Y; axes 2/3 the stick
const touch = (hand, held, sx, sy) => ({ handedness: hand, gamepad: { axes: [0, 0, sx || 0, sy || 0], buttons: Array.from({ length: 6 }, (_, i) => ({ pressed: (held || []).includes(i), value: (held || []).includes(i) ? 1 : 0 })) } });
const read = (l, r, o) => PadInput.create().read(XrInput.toPad([l, r], o));

t('No controllers gives no pad', XrInput.toPad([]) === null);
t('The made-up pad is one the game accepts as a real controller', !!PadInput.pick([XrInput.toPad([touch('left'), touch('right')])]));
t('Left stick forward walks forward', (() => { const r = read(touch('left', [], 0, -1), touch('right')); return Math.abs(r.mz - 1) < 1e-9 && r.mx === 0; })());
t('Right stick left/right does not turn through the pad (the VR rig turns the body)', (() => { const r = read(touch('left'), touch('right', [], 1, 0)); return r.padX === 0 && r.padY === 0; })());
t('Right trigger fires, left trigger aims down sights', (() => { const a = read(touch('left'), touch('right', [0])), b = read(touch('left', [0]), touch('right')); return a.fire && !a.ads && b.ads && !b.fire; })());
t('A jumps (Meta locomotion map); the right stick never jumps, pushed up, diagonally or forward', (() => { const a = read(touch('left'), touch('right', [4])), u = read(touch('left'), touch('right', [], 0, -1)), d = read(touch('left'), touch('right', [], 0.7, -0.7)); return a.jump && !u.jump && !d.jump; })());
t('Left stick pushed forward (even hard, even with drift) never jumps', (() => { const r = read(touch('left', [], 0.12, -1), touch('right', [], 0.1, 0.1)); return !r.jump; })());
t('Right stick click swaps guns', read(touch('left'), touch('right', [3])).swap);
t('X reloads (the gun plays its reload animation)', read(touch('left', [4]), touch('right')).reload);
t('B slides while moving', read(touch('left', [], 0, -1), touch('right', [5])).slide);
t('Y: a tap pauses (0.3 s after release, in case a second tap follows), a 0.5 s hold opens Gear once and does not pause', (() => { const y = XrInput.createY(); const a = y.step(true, 0.1), b = y.step(false, 0.1); let late = 0; for (let k = 0; k < 4; k++) if (y.step(false, 0.1).tap) late++; const z = XrInput.createY(); let g = 0, tap = 0; for (let i = 0; i < 8; i++) { const s = z.step(true, 0.1); if (s.hold) g++; } if (z.step(false, 0.1).tap) tap++; for (let k = 0; k < 5; k++) if (z.step(false, 0.1).tap) tap++; const ra = read(touch('left'), touch('right'), { y: { tap: true } }), rg = read(touch('left'), touch('right'), { y: { hold: true } }); return !a.tap && !b.tap && b.up && late === 1 && g === 1 && tap === 0 && ra.start && rg.gear && !rg.start; })());
t('Y: a double tap is the map and never also pauses or opens Gear; two slow taps are two pauses', (() => { const y = XrInput.createY(); let d = 0, tap = 0, hold = 0; const seq = [1, 0, 1, 0, 0, 0, 0, 0, 0]; for (const on of seq) { const s = y.step(!!on, 0.08); if (s.double) d++; if (s.tap) tap++; if (s.hold) hold++; } const z = XrInput.createY(); let t2 = 0, d2 = 0; for (const on of [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]) { const s = z.step(!!on, 0.08); if (s.tap) t2++; if (s.double) d2++; } return d === 1 && tap === 0 && hold === 0 && t2 === 2 && d2 === 0; })());
t('In a VR menu the pad goes quiet (no jump, fire, reload or pause): the laser and Y do the work', (() => { const r = read(touch('left', [4, 0]), touch('right', [4, 0]), { menu: true, y: { tap: true } }); return !r.jump && !r.fire && !r.reload && !r.start && !r.ads; })());
t('Grips are not pad buttons (left grip = hold for the map, right grip = pick up / use: both read by the VR view)', (() => { const a = read(touch('left', [1]), touch('right', [1])); return !a.swap && !a.fire && a.lockUse === undefined && !a.start; })());
t('No pad map button in VR (the map is held in the left hand instead)', !read(touch('left', [1]), touch('right')).map);
t('Left stick click sprints; only a hard, mostly-downward push on the right stick is the gate action', (() => { const c = read(touch('left', [3], 0, -1), touch('right')), d = read(touch('left'), touch('right', [], 0, 0.95)), s = read(touch('left'), touch('right', [], 0.6, 0.7)), m = read(touch('left'), touch('right', [], 0, 0.6)); return c.sprint && d.lockUse === 1 && s.lockUse !== 1 && m.lockUse !== 1; })());
t('Left stick: small drift inside the deadzone does not move you; past it movement starts gently', (() => { const a = XrInput.moveStick({ axes: [0, 0, 0.1, -0.08] }), b = XrInput.moveStick({ axes: [0, 0, 0, -0.3] }), c = XrInput.moveStick({ axes: [0, 0, 0, -1] }); return a[0] === 0 && a[1] === 0 && b[1] < 0 && b[1] > -0.3 && Math.abs(c[1] + 1) < 1e-9; })());
t('Right stick: a forward/diagonal push does not turn (axis dominance); sideways does', (() => { const s = XrInput.createTurn(false); const f = s.step({ axes: [0, 0, 0.5, -0.9] }, 0.1, 4.5), x = s.step({ axes: [0, 0, 0.9, -0.3] }, 0.1, 4.5); return f === 0 && x > 0; })());
t('Pushing the left stick fully forward sprints; a half push or a sideways push does not', XrInput.autoSprint(0.95, 0.1) && !XrInput.autoSprint(0.6, 0) && !XrInput.autoSprint(0.9, 0.8));
t('Smooth turn: nothing in the dead zone, a half push is close to half speed, full speed at full tilt', (() => { const s = XrInput.createTurn(false); const z = s.step({ axes: [0, 0, 0.1, 0] }, 0.1, 4.5), d = s.step({ axes: [0, 0, 0.08, 0] }, 0.1, 4.5), h = s.step({ axes: [0, 0, 0.5, 0] }, 0.1, 4.5), f = s.step({ axes: [0, 0, 1, 0] }, 0.1, 4.5); return z === 0 && d === 0 && Math.abs(f - 0.45) < 1e-9 && h > 0.3 * 0.45 && h < 0.7 * 0.45; })());
t('Turn rates: Slow 2.5, Normal 4.5, Fast 7 rad/s; a ?turn= flag still wins', XrInput.smoothTurn('slow') === 2.5 && XrInput.smoothTurn('normal') === 4.5 && XrInput.smoothTurn('fast') === 7 && XrInput.smoothTurn('fast', 6) === 6 && XrInput.smoothTurn('nope') === 4.5);
t('Snap angles follow the same Slow/Normal/Fast tile (30/45/60); a ?snap= flag still wins', XrInput.snapTurnDeg('slow') === 30 && XrInput.snapTurnDeg('normal') === 45 && XrInput.snapTurnDeg('fast') === 60 && XrInput.snapTurnDeg('fast', 20) === 20);
t('Turn speed tile cycles Slow to Normal to Fast and back', XrInput.nextTurnRate('slow') === 'normal' && XrInput.nextTurnRate('normal') === 'fast' && XrInput.nextTurnRate('fast') === 'slow' && XrInput.parseTurnRate('FAST') === 'normal');
t('Snap turn: 45 degrees by default, one step per flick, re-arms after the stick returns', (() => { const s = XrInput.createTurn(true), f = { axes: [0, 0, 1, 0] }, z = { axes: [0, 0, 0, 0] }; const a = s.step(f, 0.016), b = s.step(f, 0.016); s.step(z, 0.016); const c = s.step({ axes: [0, 0, -1, 0] }, 0.016); return Math.abs(a - Math.PI / 4) < 1e-9 && b === 0 && Math.abs(c + Math.PI / 4) < 1e-9; })());
t('Snap turn angle can be changed (?snap=30)', Math.abs(XrInput.createTurn(true, Math.PI / 6).step({ axes: [0, 0, 1, 0] }, 0.016) - Math.PI / 6) < 1e-9);
t('Aim maths: straight ahead is yaw 0, right is +90 degrees, up is positive pitch', (() => { const f = XrInput.dirToAngles(0, 0, -1), r = XrInput.dirToAngles(1, 0, 0), u = XrInput.dirToAngles(0, 1, -1); return Math.abs(f.yaw) < 1e-9 && Math.abs(r.yaw - Math.PI / 2) < 1e-9 && u.pitch > 0.7; })());
t('Look toward: the look input moves the referee aim exactly onto the target (taking the short way round)', (() => {
  const cur = { yaw: 3.0, pitch: 0.1 }, tgt = { yaw: -3.0, pitch: -0.2 }, k = 0.0022;
  const l = XrInput.lookToward(cur, tgt, k, 1), ny = cur.yaw + l.lookX * k, np = cur.pitch - l.lookY * k;
  return Math.abs(XrInput.wrap(ny - tgt.yaw)) < 1e-9 && Math.abs(np - tgt.pitch) < 1e-9 && Math.abs(l.lookX * k) < 0.3;
})());
t('Head-relative walking: head 90 degrees right of the gun turns stick-forward into a right strafe', (() => { const a = XrInput.headMove(0, 1, Math.PI / 2), b = XrInput.headMove(0.3, 0.7, 0); return Math.abs(a.mx - 1) < 1e-9 && Math.abs(a.mz) < 1e-9 && b.mx === 0.3 && b.mz === 0.7; })());
t('A small floor for the VR test map (?sandbox) still connects (floorgen size override)', (() => { const FG = require('../src/floorgen.js'); let ok = 0; for (let k = 1; k <= 12; k++) { let a = k * 977; const m = FG.generate(1, () => { a = (Math.imul(a, 1664525) + 1013904223) >>> 0; return a / 4294967296; }, 1, 44); if (m.W === 44) ok++; } return ok === 12; })());
console.log(bad ? bad + ' failed' : 'all xr checks passed');
process.exit(bad ? 1 : 0);
