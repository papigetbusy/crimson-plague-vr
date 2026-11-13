// VR game flow and menus: things the fake-Quest playtest found, pinned down so they cannot come back. Plain sentences. Run: node tests/vrflow.test.js
const fs = require('fs'), path = require('path');
const src = (f) => fs.readFileSync(path.join(__dirname, '..', 'src', f), 'utf8');
let bad = 0;
const t = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) bad++; };
const tpl = src('index.template.html'), screen = src('screen.js'), xrm = src('screen/xr_mode.js');
t('The page says it is UTF-8 in its first 1024 bytes (✔, · and ▼ are not shown as garbage on a server that does not say so)', /<meta charset="utf-8">/i.test(tpl.slice(0, 1024)));
t('Putting the headset on at the title does not skip the start menu (class pick first; a paused run or the test map carries on)', /xr\.on\(\(\) => \{.{0,200}?if \(!running && \(started \|\| SANDBOX\)\) begin\(true\)/.test(screen));
t('A menu press still counts if the menu was redrawn while the trigger was down (same tile by title and place)', /T\.t\.title === t\.title && T\.t\.x === t\.x && T\.t\.y === t\.y/.test(xrm));
t('The playtest can find the middle of every menu tile (menuTiles)', /menuTiles: \(\) =>/.test(xrm));
// the Gear menu's mod buttons and the stash menu's buttons are real page buttons the VR panel can press (not text boxes)
global.GunCard = require('../src/screen/gun_card.js');
const GearMenu = require('../src/screen/gear_menu.js'), StashMenu = require('../src/screen/stash_menu.js');
const Referee = require('../src/referee.js'); const ref = Referee.create(7); ref.setCfg({ startGun: 'pistol_service', monsterCount: 0 }); ref.reset(); ref.giveMod(2); { const q = ref.snapshot().pickups.find((p) => p.kind === 'mod'); ref.place(q.x, q.z); ref.step(1 / 60, { pickup: true, pickupId: q.id }); }
const p = ref.snapshot().player, gh = GearMenu.html(p);
t('Gear menu: every loose mod has a "Fit to gun in hands" button', p.mods.length > 0 && (gh.match(/data-act="attach:/g) || []).length >= p.mods.length && /Fit to gun in hands/.test(gh));
ref.attachMod(0, 0); const gh2 = GearMenu.html(ref.snapshot().player);
t('Gear menu: a fitted mod has a "Take off" button', /data-act="detach:0:0"/.test(gh2));
t('Gear menu has a Close the VR panel turns into its Y exit', /class="gclose" data-act="close"/.test(gh));
{ // the stash chest in a safe room: put in, take out, save; text boxes are skipped by the VR panel (no keyboard in a headset)
  const r = Referee.create(9); r.setCfg({ startGun: 'pistol_service', monsterCount: 0, startWave: 11, startSafe: true }); r.reset();
  const s = r.snapshot(), pl = s.player;
  const sh = StashMenu.html(Object.assign({}, pl, { stash: Object.assign({}, pl.stash, { open: true, take: true, near: true }) }));
  t('Stash menu: the gun in your hands has a "Put in stash" button', /data-act="stash:gun:/.test(sh));
  t('Stash menu: a Save game here button', /data-act="save"/.test(sh));
  const XrMenuSrc = src('screen/xr_menu.js');
  t('The VR panel skips text boxes (gun names) but keeps the buttons next to them', /SKIP = '[^']*input/.test(XrMenuSrc));
  t('Safe room at wave 11 has a stash chest and a merchant (the playtest goes there)', s.safe && !!pl.stash.chest && !!s.merchant);
}
{ // batch 2: co-op lobby in VR, instant start/stop in VR, aim converges where the barrel points
  const coop = src('screen/coop.js'), xm = src('screen/xr_menu.js'), tplS = src('index.template.html');
  t('Co-op: PLAY WITH FRIENDS and HOST are no longer hidden from the VR menu', !/#coopPanel, #coopBtn/.test(xm));
  t('Co-op: letter keys for the room code exist and show only in VR', /coopKeys/.test(coop) && /body\.xr #coopKeys/.test(tplS) && /id="coopKeys" class="vrOnly"/.test(tplS));
  t('Co-op: the keys cover every letter a room code can use, plus delete', /ABCDEFGHJKMNPQRSTUVWXYZ23456789/.test(coop) && /'DEL'/.test(coop));
  t('VR menu: a key board lays out 8 keys a row (not 3)', /Math\.min\(8, n\)/.test(xm));
  t('VR: instant start and stop while in the headset, normal again after', /ref.setCfg\(\{ accel: VR_ACCEL/.test(screen) && /ref.setCfg\(\{ accel: ref.defaults.accel/.test(screen));
  t('VR: the eye aims at the point the barrel points at (converge), so shots land where the gun points', /XrFeel\.converge\(/.test(xrm));
  t('VR: every shot uses the per-gun kick and buzz (shotFx), every hit the hit marker (hitFx)', /xr\.shotFx\(\)/.test(screen) && /xr\.hitFx\(/.test(screen));
}
// batch 3
t('VR pause menu has SOUND and NEW RUN (the flat Tuning panel needs a mouse)', /id="vrSound"/.test(tpl) && /id="vrNewRun"/.test(tpl) && /\$\('vrNewRun'\)\.addEventListener/.test(screen));
t('NEW RUN is refused in a co-op room (the host owns the run)', /vrNewRun'\)\.addEventListener\('click', \(\) => \{ if \(coop\.mode !== 'off'\)/.test(screen));
t('Gun weight: the aim follows the hand at a per-class rate (XrFeel.aimRate)', /XrFeel.aimRate\(/.test(xrm));
t('VR pause menu has TURN SPEED (Slow/Normal/Fast) and WALK (Head / Left hand), saved with the other comfort tiles', /id="vrTurnSpeed"/.test(tpl) && /id="vrWalk"/.test(tpl) && /setComfort\('turnRate'/.test(screen) && /setComfort\('walkHand'/.test(screen) && /turnRate: XrInput.parseTurnRate/.test(xrm) && /walkHand: !!c.walkHand/.test(xrm));
t('A ?turn= link flag still wins over the saved turn speed', /turnFlag/.test(xrm) && /smoothTurn\(comfort.turnRate, opts.turnFlag\)/.test(xrm));
t('Walking can follow the left hand, and falls back to the head if that hand is missing', /walkYaw\(\)/.test(screen) && /handYaw\('left'\)/.test(xrm) && /if \(y !== null\) return y/.test(xrm));
t('VR red dot is big enough to see on a Quest: a ~44 MOA sprite with a solid core of at least ~7 MOA (3 px), no mipmaps, normal blending, depth-tested', /DOT_GLOW_MOA = 22/.test(xrm) && /DOT_MIN_CORE_MOA = 7\.2/.test(xrm) && /generateMipmaps = false/.test(xrm) && /blending: THREE\.NormalBlending, depthTest: true/.test(xrm));
t('VR red dot is a collimated point on the fire ray (the old 8 mm on-gun cube is gone)', /placeFireDot\(/.test(xrm) && /gb\(0\.001, 0\.001, 0\.0005/.test(screen) && !/gb\(0\.008, 0\.008, 0\.004/.test(screen));
t('VR shots start from the eye aimed where the barrel points, with no referee kick fighting the sight', /gp\.muzzle.getWorldPosition/.test(xrm) && /recoilKick: 0/.test(screen));
process.exit(bad ? 1 : 0);
