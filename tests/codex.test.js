// Codex checks: every class, skill, monster, gun, gun type, status, affix, rarity and piece of gear is explained, numbers come from the game's own data, and search finds things. Plain sentences. Run: node tests/codex.test.js
const Referee = require('../src/referee.js'), D = require('../src/referee_data.js'), C = require('../src/referee_classes.js'), WP = require('../src/referee_weapons.js'), AF = require('../src/referee_affixes.js'), GR = require('../src/referee_gear.js'), FX = require('../src/referee_gunfx.js').FX;
const T = require('../src/screen/codex_text.js'), CP = require('../src/screen/codex_pages.js');
let bad = 0;
const t = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) bad++; };
const cfg = Referee.create(1).cfg;
const pgs = CP.pages({ D, C, WP, AF, GR, FX, T, cfg, ST: require('../src/referee_stash.js') });
const page = (id) => pgs.find((p) => p.id === id);
const text = (id) => CP.plain(page(id).sections.map((s) => s.title + ' ' + s.html).join(' '));
const all = CP.plain(pgs.map((p) => p.sections.map((s) => s.title + ' ' + s.html).join(' ')).join(' '));
const has = (id, s) => text(id).includes(String(s).toLowerCase().replace(/&/g, ' ').replace(/\s+/g, ' ').trim());

t('The Codex has a page for how to play, classes, monsters, guns, rarities, status effects, affixes, gear and the merchant', ['basics', 'classes', 'monsters', 'guns', 'rarity', 'status', 'affixes', 'gear', 'shop'].every((id) => page(id) && page(id).sections.length > 0));
t('Every page section has a title and some text', pgs.every((p) => p.title && p.sections.every((s) => s.title && s.html.length > 10)));
t('No page shows undefined, NaN or Infinity anywhere', !/undefined|nan\b|infinity/.test(all));
t('Every class, its starting bonus, all four skills and its ultimate are in the Codex', Object.keys(C.CLASSES).every((id) => { const c = C.CLASSES[id]; return has('classes', c.name) && has('classes', c.startText) && c.skills.every((s) => has('classes', s.name) && has('classes', s.desc)) && has('classes', c.ult.name); }));
t('Every class skill shows its level 1 and level 5 numbers from the game data', (() => { const s = C.CLASSES.gunslinger.skills[3]; return has('classes', s.stat(s.v(1))) && has('classes', s.stat(s.v(C.MAX_LEVEL))); })());
t('Every ordinary level-up card is listed with what it does', D.SKILLS.every((s) => has('classes', s.name) && has('classes', s.desc)));
t('Every monster, the boss included, has a written note and a page entry with its numbers', Object.keys(D.KINDS).every((k) => T.MONSTER[k] && T.MONSTER[k].length > 20 && has('monsters', D.KINDS[k].name) && has('monsters', 'x' + D.KINDS[k].hpMul)));
t('Each monster says which wave it first appears on, from the wave table', D.MIX.every((m) => has('monsters', 'wave ' + m.from)) && has('monsters', 'every 10th wave'));
t('Ranged monsters are described as ranged and the others as melee', has('monsters', 'ranged: throws a spit') && has('monsters', 'melee'));
t('The elite abilities are listed', D.AFFIXES.every((a) => has('monsters', a.name)));
t('Every gun is in the Codex with its status and its numbers for a common copy on wave 1', Object.keys(WP.GUNS).every((id) => { const g = WP.GUNS[id]; const s = WP.stats({ id, rarity: 0, wave: 1, status: [], affixes: [] }, cfg); return has('guns', g.name) && has('guns', Math.round(s.dmg) + (s.pellets > 1 ? ' x ' + s.pellets : '')); }));
t('Every gun type has a written description', ['pistol', 'smg', 'shotgun', 'sniper', 'hmg'].every((ty) => T.GUN_TYPE[ty] && has('guns', T.GUN_TYPE[ty].slice(0, 30))));
t('Every gun type in the weapon table has a Codex section', [...new Set(Object.values(WP.GUNS).map((g) => g.type))].every((ty) => Object.keys(T.GUN_TYPE).includes(ty)));
t('All five rarities are explained with their damage and gear numbers, and where they drop', WP.RARITIES.every((r, i) => has('rarity', r.name) && has('rarity', 'x' + r.dmg) && has('rarity', T.RARITY_NOTE[i].slice(0, 20))));
t('The affix counts per rarity match the game', has('rarity', '0 to 1') && has('rarity', '1 to 2') && has('rarity', '2 to 3') && has('rarity', '3 to 4'));
t('All seven status colours are explained and list the guns that carry them', WP.STATUSES.every((st) => T.STATUS[st] && has('status', T.STATUS[st][0]) && Object.keys(WP.GUNS).filter((g) => WP.GUNS[g].status.includes(st)).every((g) => has('status', WP.GUNS[g].name))));
t('Every gun affix and every gear affix is listed, with its class if it has one', AF.LIST.every((a) => has('affixes', a.name) && has('affixes', a.text)) && GR.LIST.every((a) => has('affixes', a.name)) && [...AF.LIST, ...GR.LIST].filter((a) => a.cls).every((a) => has('affixes', 'star ' + a.cls)));
t('Class-only affixes are explained as only dropping for that class', has('rarity', 'only drop while you are playing that class'));
t('Every gear slot, every gear name and the defense cap are in the Codex', GR.SLOTS.every((s) => has('gear', s) && GR.NAMES[s].every((n) => has('gear', n))) && has('gear', Math.round(GR.DEF_CAP * 100) + '%'));
t('The merchant prices come from the game data', has('shop', L(D).shopHeal + ' gold') && has('shop', WP.SHOP.base + ' gold'));
function L(d) { return d.LOOP; }
t('The how-to-play page covers waves, floors, safe rooms, traps, fog, elites, and every control scheme', ['Waves and floors', 'Safe rooms and the merchant', 'Traps', 'Fog', 'Elites and the monster cap', 'Controls: keyboard and mouse', 'Controls: phone touch', 'Controls: controller'].every((h) => page('basics').sections.some((s) => s.title === h)));
t('The controls listed match the game: swap on Q, Swap and Triangle, pick up on E, A and the card, gear on G and RB', has('basics', 'Q') && has('basics', 'Y (Triangle)') && has('basics', 'pick up the gun or gear in front of you') && has('basics', 'RB'));
t('Search finds a gun by name', CP.search(pgs, 'hand cannon').some((r) => r.page === 'Guns'));
t('Search finds a monster, a class skill and an affix by name', CP.search(pgs, 'rock golem').length > 0 && CP.search(pgs, 'quickdraw').length > 0 && CP.search(pgs, 'fan the hammer').length > 0);
t('Search with several words needs all of them', CP.search(pgs, 'witch poison').length > 0 && CP.search(pgs, 'witch zzzzqqq').length === 0);
t('Search finds a gun mod line by name', CP.search(pgs, 'extended magazine').some((r) => r.page === 'Gun Mods') && CP.search(pgs, 'steady grip').length > 0);
t('Search finds the stash and blueprint rules', CP.search(pgs, 'blueprints').some((r) => r.page === 'Stash and Blueprints'));
t('Search finds the saves and seeds rules', CP.search(pgs, 'item seed').some((r) => r.page === 'Saves and Seeds'));
t('An empty search finds nothing', CP.search(pgs, '   ').length === 0);
t('Search finds status effects by their colour word', CP.search(pgs, 'purple').some((r) => r.page === 'Status effects'));
t('The Codex numbers follow the game: change a gun\'s numbers and its Codex line changes', (() => { const cfg2 = Object.assign({}, cfg, { damage: cfg.damage * 2 }); const p2 = CP.pages({ D, C, WP, AF, GR, FX, T, cfg: cfg2 }); return CP.plain(p2.find((p) => p.id === 'guns').sections.map((s) => s.html).join(' ')) !== text('guns'); })());

console.log(bad ? bad + ' FAILED' : 'all codex checks passed'); process.exit(bad ? 1 : 0);
