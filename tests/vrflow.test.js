// VR game flow and menus: things the fake-Quest playtest found, pinned down so they cannot come back. Plain sentences. Run: node tests/vrflow.test.js
const fs = require('fs'), path = require('path');
const src = (f) => fs.readFileSync(path.join(__dirname, '..', 'src', f), 'utf8');
let bad = 0;
const t = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) bad++; };
const tpl = src('index.template.html'), screen = src('screen.js'), xrm = src('screen/xr_mode.js');
t('The page says it is UTF-8 in its first 1024 bytes (✔, · and ▼ are not shown as garbage on a server that does not say so)', /<meta charset="utf-8">/i.test(tpl.slice(0, 1024)));
t('Putting the headset on at the title does not skip the start menu (class pick first; a paused run or the test map carries on)', /xr\.on\(\(\) => \{[^}]*if \(!running && \(started \|\| SANDBOX\)\) begin\(true\)/.test(screen));
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
process.exit(bad ? 1 : 0);
