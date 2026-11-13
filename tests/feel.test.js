// VR gun feel (src/screen/xr_feel.js): recoil kick and spring, two-hand hold, buzz per gun. Plain sentences. Run: node tests/feel.test.js
const F = require('../src/screen/xr_feel.js');
let bad = 0; const t = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) bad++; };
function run(peak, w, secs) { const s = F.createSpring(1); s.kick(peak, w); let max = 0, at = 0, x = 0; for (let i = 0; i < secs * 90; i++) { x = s.step(1 / 90); if (x > max) { max = x; at = i / 90; } } return { max, at, end: x }; }
const r = run(0.1, 30, 1);
t('A kick climbs to about its peak (within 10%)', Math.abs(r.max - 0.1) < 0.01);
t('It peaks fast (about 1/30 s for a pistol-speed spring)', r.at > 0.015 && r.at < 0.06);
t('And is home again within a second (no drift)', Math.abs(r.end) < 1e-4);
const s = F.createSpring(1); s.kick(0.1, 30); for (let i = 0; i < 15; i++) s.step(1 / 90); t('About 0.17 s after a pistol shot the gun is nearly back (under 20% of the kick)', s.x < 0.02);
const s2 = F.createSpring(1); s2.kick(0.1, 30); let ok = true, prev = 0; for (let i = 0; i < 200; i++) { const x = s2.step(1 / 90); if (x < -0.005) ok = false; prev = x; } t('It never swings past home (critically damped, no wobble)', ok);
const s3 = F.createSpring(1); s3.kick(0.1, 30); s3.step(0.2); const s4 = F.createSpring(1); s4.kick(0.1, 30); for (let i = 0; i < 25; i++) s4.step(0.008); t('A long frame gives the same result as many short ones (stable on a slow frame)', Math.abs(s3.x - s4.x) < 0.003);
const cap = F.createSpring(F.CAP_ROT); for (let i = 0; i < 40; i++) { cap.kick(0.2, 20); cap.step(1 / 90); } t('Holding the trigger on a heavy gun never flips the gun up past the cap', cap.x <= F.CAP_ROT + 1e-9);
const one = F.kickOf('rifle', false, false), two = F.kickOf('rifle', true, false), ads = F.kickOf('rifle', true, true);
t('A second hand on the fore-end halves the kick', Math.abs(two.rot - one.rot * 0.5) < 1e-9 && Math.abs(two.back - one.back * 0.5) < 1e-9);
t('Aiming down sights trims it more', ads.rot < two.rot);
t('With two hands the support hand feels the shot too', two.left > 0 && one.left === 0);
const K = F.KICK;
t('Shotgun and sniper kick harder than an SMG', K.shotgun.rot > K.smg.rot * 3 && K.sniper.rot > K.smg.rot * 3);
t('Heavier guns buzz harder and longer', K.shotgun.hap > K.pistol.hap && K.shotgun.ms > K.smg.ms && K.sniper.hap > K.rifle.hap);
t('Heavy guns settle slower than light ones', K.shotgun.w < K.smg.w && K.sniper.w < K.pistol.w);
t('Every gun type has a feel (pistol, smg, rifle, shotgun, sniper, hmg)', ['pistol', 'smg', 'rifle', 'shotgun', 'sniper', 'hmg'].every((k) => K[k] && K[k].hap > 0 && K[k].hap <= 1));
t('An unknown gun type falls back to rifle feel', F.kickOf('blaster', false, false).rot === K.rifle.rot);
// converge: where the gun points
const C = F.converge;
t('Pointing at a monster 2 m away: the aim point is on its body (about 1.6 m along the line)', Math.abs(C([0, 1.2, 0], [0, 0, -1], [{ x: 0, z: -2, scale: 1 }], null, 40) - 1.55) < 0.06);
t('Pointing past a monster (1 m to the side): nothing in the way, the aim point is far', C([0, 1.2, 0], [0, 0, -1], [{ x: 1, z: -2, scale: 1 }], null, 40) === 40);
t('A big monster is easier to hit than a small one at the same miss', C([0, 1.2, 0], [0, 0, -1], [{ x: 0.7, z: -3, scale: 2 }], null, 40) < 40 && C([0, 1.2, 0], [0, 0, -1], [{ x: 0.7, z: -3, scale: 1 }], null, 40) === 40);
t('Pointing over a monster\'s head misses it', C([0, 3.5, 0], [0, 0, -1], [{ x: 0, z: -2, scale: 1 }], null, 40) === 40);
t('A monster behind you never counts', C([0, 1.2, 0], [0, 0, -1], [{ x: 0, z: 2, scale: 1 }], null, 40) === 40);
t('A wall stops the line (aim point on the wall)', Math.abs(C([0, 1.2, 0], [0, 0, -1], [], (x, z) => z < -5, 40) - 5.25) < 0.01);
t('The nearer of a wall and a monster wins', C([0, 1.2, 0], [0, 0, -1], [{ x: 0, z: -8, scale: 1 }], (x, z) => z < -5, 40) < 5.5);
t('Pointing at the floor: the aim point is on the floor', Math.abs(C([0, 1.2, 0], [0, -0.6, -0.8], [], null, 40) - 2.0) < 0.26);
// weight per class
t('Weight: a pistol follows the hand faster than a heavy machine gun', F.aimRate('pistol', false, 0) > F.aimRate('rifle', false, 0) && F.aimRate('rifle', false, 0) > F.aimRate('hmg', false, 0));
t('Weight: two hands use one steady rate for every gun', F.aimRate('pistol', true, 0) === F.aimRate('hmg', true, 0));
t('Weight: aiming down sights uses the gun\'s own sight smoothing', F.aimRate('sniper', true, 8) === 8);
t('Weight: no rate is so low the aim feels laggy (>= 14/s: 63% of a move in 70 ms)', Object.values(F.WEIGHT).every((r) => r >= 14));
process.exit(bad ? 1 : 0);
