// Floor gun checks: every gun type has its own default pickup model you can tell apart at a glance, sized sensibly, shaded in its rarity colour. Plain sentences. Run: node tests/floorguns.test.js
const S = require('../src/screen/floor_gun_shapes.js'), W = require('../src/referee_weapons.js');
const fs = require('fs'), path = require('path');
let bad = 0;
const t = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) bad++; };
const types = Object.keys(W.TYPES), e = (ty) => S.extent(ty);

t('Every gun type in the game has its own floor model', types.every((ty) => S.SHAPES[ty] && S.SHAPES[ty].length >= 3));
t('Every gun in the weapon table lands on a floor model through its type', Object.values(W.GUNS).every((g) => S.SHAPES[g.type]));
t('Every part is a real box with sizes and a position', types.every((ty) => S.SHAPES[ty].every((p) => p.length >= 6 && p.slice(0, 6).every((n) => typeof n === 'number' && isFinite(n)) && p[0] > 0 && p[1] > 0 && p[2] > 0)));
t('No two types have the same silhouette (length, height and part count)', (() => { const sig = types.map((ty) => [e(ty).len.toFixed(2), e(ty).height.toFixed(2), e(ty).parts].join()); return new Set(sig).size === types.length; })());
t('The pistol is the smallest and the sniper is the longest, so size alone tells them apart', types.every((ty) => ty === 'pistol' || e('pistol').len < e(ty).len) && types.every((ty) => ty === 'sniper' || e('sniper').len > e(ty).len));
t('A rifle is longer than an SMG, and an SMG longer than a pistol', e('rifle').len > e('smg').len && e('smg').len > e('pistol').len);
t('The heavy machine gun is the tallest and the thickest', types.every((ty) => ty === 'hmg' || (e('hmg').height > e(ty).height && e('hmg').width >= e(ty).width)));
t('The sniper has a scope: a part standing above its body', S.SHAPES.sniper.some((p) => p[4] - p[1] / 2 > 0.2));
t('The shotgun has a barrel that is long and thin compared with its body', (() => { const b = S.SHAPES.shotgun[0]; return b[0] > 0.7 && b[1] <= 0.08; })());
t('Every model fits a sensible size on the floor (about 0.4 to 1.4 long, under 0.6 tall)', types.every((ty) => e(ty).len >= 0.4 && e(ty).len <= 1.4 && e(ty).height < 0.6));
t('The darker shade really is darker than the rarity colour, whatever the rarity', W.RARITIES.every((r) => { const c = r.color, d = S.darker(c), lum = (x) => ((x >> 16) & 255) + ((x >> 8) & 255) + (x & 255); return lum(d) < lum(c) && d >= 0 && d <= 0xffffff; }));
t('The pickup view uses these models, not one generic shape', (() => { const src = fs.readFileSync(path.join(__dirname, '../src/screen/loot_view.js'), 'utf8'); return src.includes('setShape(p, d.gun.type)') && src.includes('FloorGunShapes.SHAPES'); })());
t('The build includes the floor model file before the loot view', (() => { const b = fs.readFileSync(path.join(__dirname, '../tools/build.js'), 'utf8'); return b.indexOf('floor_gun_shapes.js') > 0 && b.indexOf('floor_gun_shapes.js') < b.indexOf('loot_view.js'); })());

console.log(bad ? bad + ' FAILED' : 'all floor gun checks passed'); process.exit(bad ? 1 : 0);
