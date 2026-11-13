/* VR gun feel, pure numbers (no THREE, no DOM) so tests can check them. Research and choices: docs/vr-design.md, "Feel (research round 5)".
   Recoil: every shot kicks the gun in your hand (muzzle up and back toward you) and a spring brings it home, like Pavlov / Contractors / Alyx.
   It is only the look and the buzz: the bullets still go exactly where the controller points (no surprise misses), so it never fights the aim.
   Heavier guns kick harder and settle slower; a second hand on the fore-end halves the kick (the reason to hold a rifle with two hands);
   aiming down sights trims it a little more. The trigger hand buzzes harder for heavier guns; the support hand feels it too. */
const XrFeel = (function () {
  // rot: peak muzzle climb (radians), back: peak push toward you (metres), w: spring speed (higher = settles faster), hap/ms: trigger-hand buzz
  const KICK = {
    pistol: { rot: 0.10, back: 0.022, w: 30, hap: 0.40, ms: 28 },
    smg: { rot: 0.040, back: 0.012, w: 34, hap: 0.26, ms: 16 },
    rifle: { rot: 0.060, back: 0.018, w: 30, hap: 0.45, ms: 26 },
    shotgun: { rot: 0.20, back: 0.050, w: 20, hap: 0.95, ms: 70 },
    sniper: { rot: 0.17, back: 0.045, w: 18, hap: 0.85, ms: 60 },
    hmg: { rot: 0.045, back: 0.016, w: 32, hap: 0.50, ms: 22 }
  };
  const TWO_HAND = 0.5, ADS = 0.8, CAP_ROT = 0.32, CAP_BACK = 0.07;
  function kickOf(type, twoHand, ads) {
    const K = KICK[type] || KICK.rifle, k = (twoHand ? TWO_HAND : 1) * (ads ? ADS : 1);
    return { rot: K.rot * k, back: K.back * k, w: K.w, hap: K.hap, ms: K.ms, left: twoHand ? +(K.hap * 0.6).toFixed(3) : 0 };
  }
  // a critically damped spring: a kick of `peak` reaches about that far after 1/w seconds and is home (under 5%) after about 5/w
  function createSpring(cap) {
    let x = 0, v = 0, w = 30;
    return {
      kick(peak, wi) { w = wi || w; v += peak * w * Math.E; },
      step(dt) {
        const e = Math.exp(-w * dt), c = v + w * x;                 // the exact answer for any frame length: x(t) = (x0 + (v0 + w x0) t) e^-wt
        const nx = (x + c * dt) * e, nv = (v - w * c * dt) * e; x = nx; v = nv;
        if (x > cap) { x = cap; if (v > 0) v = 0; }
        if (Math.abs(x) < 1e-5 && Math.abs(v) < 1e-4) { x = 0; v = 0; }
        return x;
      },
      get x() { return x; }, reset() { x = 0; v = 0; }
    };
  }
  // Where the gun points: the distance along the gun's line to the first monster or wall (or maxD). The game's bullets start at your eye, a hand's
  // width away from the gun, so the screen aims the eye at THIS point: then the shot lands where the barrel points at any range (close-range
  // shotgun blasts no longer sail over a monster's head). o = [x, y, z], d = unit [x, y, z], mons = [{ x, z, scale }], wall(x, z) = true in a wall.
  function converge(o, d, mons, wall, maxD) {
    maxD = maxD || 40; let best = maxD;
    for (let i = 0; i < mons.length; i++) {                         // each monster as an upright cylinder about its size
      const m = mons[i], sc = m.scale || 1, r = 0.45 * sc, top = 2.0 * sc;
      const ex = m.x - o[0], ez = m.z - o[2], a = d[0] * d[0] + d[2] * d[2]; if (a < 1e-6) continue;
      const t = (ex * d[0] + ez * d[2]) / a; if (t <= 0.05 || t >= best) continue;
      const cx = o[0] + d[0] * t - m.x, cz = o[2] + d[2] * t - m.z, miss = cx * cx + cz * cz; if (miss > r * r) continue;
      const tIn = Math.max(0.05, t - Math.sqrt(r * r - miss) / Math.sqrt(a)), y = o[1] + d[1] * tIn; if (y < -0.1 || y > top) continue;
      best = tIn;
    }
    for (let t = 0.25; t < best; t += 0.25) { if ((wall && wall(o[0] + d[0] * t, o[2] + d[2] * t)) || o[1] + d[1] * t <= 0) { best = t; break; } }   // walls (if a map is given) and the floor
    return best;
  }
  // weight: how fast the aim follows the hand when holding the gun in one hand at the hip (per second; lower = heavier, the gun trails the hand a touch).
  // The gun model and the laser both ride this same aim, so they never disagree; two hands and aiming down sights use their own steadier rates.
  const WEIGHT = { pistol: 34, smg: 30, rifle: 26, shotgun: 22, sniper: 22, hmg: 16 }, WEIGHT_TWO = 18;
  function aimRate(type, twoHand, adsSmooth) { if (adsSmooth) return adsSmooth; if (twoHand) return WEIGHT_TWO; return WEIGHT[type] || WEIGHT.rifle; }
  return { KICK, kickOf, createSpring, converge, TWO_HAND, ADS, CAP_ROT, CAP_BACK, WEIGHT, aimRate };
})();
if (typeof module !== 'undefined') module.exports = XrFeel;
