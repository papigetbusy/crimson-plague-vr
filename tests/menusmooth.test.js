// VR menu smoothing (phase 2): the laser's steadying filter at Quest frame rates, and the fixed numbers of the transitions.
// The full behaviour (fades, hover frame, ticks, scroll glide, Y, no stuck input) is checked in the fake Quest: tools/xr_playtest.js --only=smooth
// Run: node tests/menusmooth.test.js
const fs = require('fs'), path = require('path');
const XrMode = require('../src/screen/xr_mode.js');
let fails = 0;
const t = (name, ok, seen) => { if (!ok) fails++; console.log((ok ? 'ok   ' : 'FAIL ') + name + (seen !== undefined ? '  (' + seen + ')' : '')); };
// the same filter as laser() in xr_mode.js, on one angle
function run(hz, input) {
  const dt = 1 / hz; let y = input(0), spd = 0; const out = [];
  for (let i = 1; i < hz * 2; i++) { const x = input(i), py = y; if (Math.abs(x - y) > XrMode.LASER_SNAP) { y = x; spd = 0; } else { y += (x - y) * (1 - Math.exp(-dt * XrMode.laserRate(spd))); spd += (Math.abs(y - py) / dt - spd) * (1 - Math.exp(-dt * 20)); } out.push(y); }
  return out;
}
for (const hz of [72, 90, 120]) {
  const a = 0.006, y = run(hz, (i) => (i % 2 ? a : -a)), tail = y.slice(-hz / 2), amp = (Math.max(...tail) - Math.min(...tail)) / (2 * a);
  t('At ' + hz + ' Hz a 0.7 degree hand tremor moves the menu beam at most a third as much', amp < 0.34, 'beam ' + (amp * 100).toFixed(0) + '% of the hand');
}
{ const hz = 72, w = 2, y = run(hz, (i) => w * i / hz), lag = (w * (hz * 2 - 1) / hz - y[y.length - 1]);
  t('A quick 2 rad/s sweep is followed closely (beam within 1.5 degrees of the hand)', lag < 1.5 / 57.3, (lag * 57.3).toFixed(2) + ' deg behind'); }
{ const hz = 72, y = run(hz, (i) => (i < 10 ? 0 : 0.2)); const k = y.findIndex((v, i) => i >= 9 && Math.abs(0.2 - v) < 0.2 * 0.05);
  t('After the hand stops, the beam settles on the new spot within ~100 ms (no long lag before a click)', k >= 0 && (k - 9) / hz < 0.11, ((k - 9) / hz * 1000).toFixed(0) + ' ms'); }
{ const hz = 72, y = run(hz, (i) => (i < 5 ? 0 : 0.5)); t('A 29 degree jump is taken at once (no swinging beam)', y[4] === 0.5, y[4]); }
const src = fs.readFileSync(path.join(__dirname, '../src/screen/xr_mode.js'), 'utf8'), menu = fs.readFileSync(path.join(__dirname, '../src/screen/xr_menu.js'), 'utf8');
t('Menus open and close in 150 ms; a menu-to-menu switch dips out in 75 ms', /MENU_FADE = 0\.15, MENU_DIP = 0\.075/.test(src));
t('Hover does not redraw the menu canvas (no texture upload on hover)', /function setHover\(t\) \{ if \(t !== hover\) \{ hover = t; return true; \}/.test(menu));
t('The menu texture has no mipmap rebuild on each upload', /tex\.generateMipmaps = false/.test(menu));
t('Y still backs out of every menu (back() presses the panel exit or resumes)', /function back\(\)/.test(src) && /if \(!menuEl \|\| dipT > 0\) return;/.test(src));
console.log(fails ? fails + ' FAILED' : 'all menu smoothing checks passed');
process.exit(fails ? 1 : 0);
