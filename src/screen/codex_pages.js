/* The Codex pages: every class, skill, monster, gun, gun type, status, affix, rarity and piece of gear explained. Pure: it builds plain html strings from the referee's own
   data (so numbers can never drift from the rules) plus the written notes in codex_text.js. pages(data) returns [{ id, title, sections: [{ title, html }] }]. */
const CodexPages = (function () {
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const hex = (c) => '#' + c.toString(16).padStart(6, '0');
  const pct = (v, d) => (v * 100).toFixed(d || 0).replace(/\.0+$/, '') + '%';
  const num = (v, d) => String(Math.round(v * Math.pow(10, d || 0)) / Math.pow(10, d || 0));
  const table = (head, rows) => '<table><tr>' + head.map((h) => '<th>' + esc(h) + '</th>').join('') + '</tr>' + rows.map((r) => '<tr>' + r.map((c) => '<td>' + c + '</td>').join('') + '</tr>').join('') + '</table>';
  const p = (t) => '<p>' + t + '</p>';
  const sec = (title, html) => ({ title, html });
  const CLASS_IDS = ['gunslinger', 'assassin', 'witch'];

  function pages(d) {
    const { D, C, WP, AF, GR, FX, T, cfg } = d, L = D.LOOP, RAR = WP.RARITIES, out = [];

    out.push({ id: 'basics', title: 'How to play', sections: T.WORLD.map(([t, x]) => sec(t, p(esc(x)))).concat([
      sec('Controls: keyboard and mouse', table(['Input', 'Does'], T.CONTROLS.keyboard.map(([a, b]) => [esc(a), esc(b)]))),
      sec('Controls: phone touch', table(['Input', 'Does'], T.CONTROLS.touch.map(([a, b]) => [esc(a), esc(b)]))),
      sec('Controls: controller', table(['Input', 'Does'], T.CONTROLS.pad.map(([a, b]) => [esc(a), esc(b)]))),
      sec('The numbers behind the rules', table(['Rule', 'Value'], [['Starting health', num(cfg.playerHp)], ['Walk / sprint / slide speed', num(cfg.walkSpeed, 1) + ' / ' + num(cfg.sprintSpeed, 1) + ' / ' + num(cfg.slideSpeed, 1)], ['Headshot damage', 'x' + cfg.headMul], ['Waves per floor', L.bossEvery], ['Most monsters alive at once', L.aliveCap], ['Health restored after a wave', L.waveClearHeal], ['Heart pickup heals', L.healAmount], ['Fog starts at wave', L.fogFrom], ['Elite abilities added every', L.eliteAffixEvery + ' waves past the cap']]))
    ]) });

    out.push({ id: 'classes', title: 'Classes', sections: CLASS_IDS.map((id) => {
      const c = C.CLASSES[id];
      const skill = (s) => '<li><b>' + esc(s.name) + '</b>: ' + esc(s.desc) + '<br><i>Level 1: ' + esc(s.stat(s.v(1))) + '. Level ' + C.MAX_LEVEL + ': ' + esc(s.stat(s.v(C.MAX_LEVEL))) + '</i></li>';
      return sec(c.name, p('<b>' + esc(c.blurb) + '.</b> Starting bonus: ' + esc(c.startText) + '.') + '<ul>' + c.skills.map(skill).join('') + '</ul>' +
        p('<b>Ultimate, ' + esc(c.ult.name) + ':</b> ' + esc(c.ult.desc) + '. Offered from player level ' + C.ULT_LEVEL + '. <i>Level 1: ' + esc(c.ult.stat(c.ult.v(1))) + '. Level ' + C.MAX_LEVEL + ': ' + esc(c.ult.stat(c.ult.v(C.MAX_LEVEL))) + '.</i>') +
        p('Class skills are passive (no new buttons). Each has ' + C.MAX_LEVEL + ' levels and levels up from use as well as from picking it again. Gear and gun affixes marked with a star only drop while you play ' + esc(c.name) + '.'));
    }).concat([sec('Ordinary level-up cards', table(['Card', 'Does', 'Most you can take'], D.SKILLS.map((s) => [esc(s.name), esc(s.desc), s.max])))]) });

    const unlock = (kind) => { const m = D.MIX.find((x) => x.kind === kind); return D.KINDS[kind].boss ? 'every 10th wave (boss, one of four at random)' : kind === 'fiend' ? 'wave 1 (fills every wave)' : 'wave ' + m.from; };
    out.push({ id: 'monsters', title: 'Monsters', sections: Object.keys(D.KINDS).map((k) => {
      const m = D.KINDS[k], sh = m.shoot, style = (m.boss ? 'Boss. ' : '') + (sh ? 'Ranged: throws a ' + esc(sh.proj) + ' from up to ' + sh.range + ' away. ' : 'Melee. ') + (m.hover ? 'Floats above the ground. ' : '') + (m.charge ? 'Charges at you every ' + m.charge.every + 's. ' : '');
      return sec(m.name, p(esc(T.MONSTER[k] || '')) + table(['Health', 'Speed', 'Damage', 'Attack rate', 'XP', 'Appears'], [['x' + m.hpMul, 'x' + m.speedMul, 'x' + m.dmgMul, 'x' + m.rate, m.xp, unlock(k)]]) + p(style + 'All numbers are multiples of the base monster, and grow every wave (+' + pct(L.hpPerWave) + ' health, +' + pct(L.dmgPerWave) + ' damage per wave).'));
    }).concat([
      sec('Elites', p('Past the monster cap, some spawns are elites: bigger (x' + L.eliteScale + '), x' + L.eliteHp + ' health, ' + L.eliteXp + 'x XP and ' + L.goldElite + 'x gold, and they drop guns and gear far more often.') + table(['Ability', 'Unlocks after', 'Does'], D.AFFIXES.map((a) => [esc(a.name), a.from + ' waves past the cap', a.hp ? 'x' + a.hp + ' health' : a.speed ? 'x' + a.speed + ' speed' : a.dmg ? 'x' + a.dmg + ' damage' : 'explodes when it dies, hurting you within ' + L.volatileRadius + ' for its full damage']))),
      sec('Wave size', p('Wave w brings about 6 + 2w + w/3 monsters (half that plus the boss on boss waves). Unlocked kinds share up to 85% of a wave; the Horned Fiend fills the rest.'))
    ]) });

    // a gun at common, wave 1, against the base numbers
    const gunStats = (id) => WP.stats({ id, rarity: 0, wave: 1, status: [], affixes: [] }, cfg);
    const types = ['rifle', 'pistol', 'smg', 'shotgun', 'sniper', 'hmg'];
    out.push({ id: 'guns', title: 'Guns', sections: types.map((ty) => {
      const ids = Object.keys(WP.GUNS).filter((g) => WP.GUNS[g].type === ty);
      return sec({ rifle: 'Rifles', pistol: 'Pistols', smg: 'SMGs', shotgun: 'Shotguns', sniper: 'Sniper rifles', hmg: 'Heavy machine guns' }[ty], p(esc(T.GUN_TYPE[ty])) + table(['Gun', 'Status', 'Damage', 'Fire rate', 'Magazine', 'Reload'], ids.map((g) => { const s = gunStats(g), gg = WP.GUNS[g]; return [esc(gg.name), gg.status.length ? esc(gg.status.join(', ')) : 'none', num(s.dmg) + (s.pellets > 1 ? ' x ' + s.pellets : ''), num(s.rate, 1) + '/s', s.mag, num(s.reload, 1) + 's']; })) + p('Numbers shown are for a Common copy dropped on wave 1. Rarity, wave and affixes raise them.'));
    }).concat([
      sec('Gun and gear rules', p('You carry two guns and swap with Q, the Swap button or Triangle. Pick a gun up with E, A or by tapping its card (gear works the same way); with both hands full it replaces the gun in your hands and that one drops at your feet. Every wave a gun drops it gets +' + pct(WP.DROP.waveGrowth) + ' damage until the damage cap (chosen later). Guns lie on the floor for ' + WP.DROP.life + ' seconds.'))
    ]) });

    out.push({ id: 'rarity', title: 'Rarities', sections: [
      sec('The five rarities', table(['Rarity', 'Gun damage', 'Gear strength', 'Affixes (gun / charm / armor)', 'Price', 'Where it drops'], RAR.map((r, i) => [ '<b style="color:' + hex(r.color) + '">' + esc(r.name) + '</b>', 'x' + r.dmg, 'x' + GR.RARITY_K[i], AF.COUNT[i][0] === AF.COUNT[i][1] ? AF.COUNT[i][0] : AF.COUNT[i][0] + ' to ' + AF.COUNT[i][1], 'x' + num(1 + WP.SHOP.perRarity * i, 1) + ' base', esc(T.RARITY_NOTE[i])]))),
      sec('Drops', p('An ordinary monster drops a gun ' + pct(WP.DROP.chance) + ' of the time, an elite ' + pct(WP.DROP.eliteChance) + ', a boss always (one rarity band better). Gear drops ' + pct(GR.DROP.chance) + ' / ' + pct(GR.DROP.eliteChance) + ' / always. The chance of the next rarity up grows through each band of ten waves; legendaries start at ' + pct(WP.DROP.legendBase) + ' on wave 31 and gain ' + pct(WP.DROP.legendPer) + ' a wave up to ' + pct(WP.DROP.legendMax) + '.')),
      sec('Class-only rule', p('Affixes marked with a star belong to one class. They only drop while you are playing that class, so a Witch never finds a Gunslinger line, and the other way round.'))
    ] });

    out.push({ id: 'status', title: 'Status effects', sections: WP.STATUSES.map((st) => {
      const t = T.STATUS[st]; return sec(t[0] + ' (' + t[1] + ')', p(esc(t[2])) + p('Guns with this status: ' + Object.keys(WP.GUNS).filter((g) => WP.GUNS[g].status.includes(st)).map((g) => esc(WP.GUNS[g].name)).join(', ') + '. Strength grows +' + pct(FX.power) + ' per rarity step, and by status affixes.'));
    }).concat([sec('How statuses work', p('A normal gun carries one status; a legendary carries two. A status triggers on every hit. The Service Pistol has none. The shot effects (muzzle flash, bullet streak, hits and kills) take their colour from the gun in your hands: a legendary alternates between its two colours.'))]) });

    const affRows = (list, scaleFn) => table(['Affix', 'Does', 'Common', 'Legendary', 'Class'], list.map((a) => { const lo = scaleFn(a, 0), hi = scaleFn(a, 4); return [esc(a.name), esc(a.text), lo, hi, a.cls ? '&#9733; ' + esc(a.cls) : 'any']; }));
    const fmt = (a, r) => { const v = a.base * (1 + 0.25 * r); return a.unit === '' ? '+' + num(v * 0.8, 1) + ' to ' + num(v * 1.2, 1) : '+' + pct(v * 0.8, a.flat && v < 0.1 ? 1 : 0) + ' to ' + pct(v * 1.2, a.flat && v < 0.1 ? 1 : 0); };
    out.push({ id: 'affixes', title: 'Affixes', sections: [
      sec('Gun affixes', p('A gun gets 0 to 4 of these depending on its rarity (see Rarities). Each value rolls between 80% and 120% of the shown range.') + affRows(AF.LIST, fmt)),
      sec('Gear affixes', p('Gear affixes only roll on the pieces that suit them (shown under Gear).') + affRows(GR.LIST, fmt))
    ] });

    out.push({ id: 'saves', title: 'Saves and Seeds', sections: [
      sec('Saves', p('The game never saves by itself. In a safe room, stand at the stash chest, press pick up and choose Save game here (the newest 8 are kept, and you can delete any). A save holds your wave, level, gold, class, skills, guns, gear, mods and stash. After a fall, or from the start card, press Continue to go back to one.')),
      sec('Seeds', p('A run has three seeds. The MAP seed decides the floors, traps and fog, and a save keeps it, so going back gives you the very same floors. The DAMAGE seed (the fight dice) and the ITEM seed (drops and the merchant\'s stock) are never saved: they are rolled fresh every time you start a run or go back to a save. So you can return to the same map as often as you like and chase better luck.')),
      sec('Starting over', p('Rising again after a fall starts a brand new run with a new map seed too.'))
    ] });
    const MD = WP.MD;
    const ST = d.ST;
    if (ST) out.push({ id: 'stash', title: 'Stash and Blueprints', sections: [
      sec('The stash chest', p('Every safe room has a stash chest a few steps from the merchant. Stand next to it and press pick up (E, A or tap the hint) to open it. You can put a gun, a worn piece of gear or a mod in it (' + ST.RULES.stashSize + ' places). Things in the chest cannot be used for the rest of that run, but they are safe. You always keep at least one gun in your hands.')),
      sec('Blueprints', p('After you fall, anything you stashed can be kept as a blueprint: a saved copy with all its lines (and the mods fitted on a gun), back at wave 1. Pick blueprints on the start card or the game over card. A run starts with ONE gun and one piece of each gear place (head, chest, boots, one charm). Picking a second of the same place swaps it in. You can keep ' + ST.RULES.perType + ' blueprints of each type. Loose mods cannot be blueprints: fit them to a gun first.')),
      sec('Blueprint types', table(['Type', 'Kept'], Object.keys(ST.TYPE_NAMES).filter((k) => k !== 'mod').map((k) => [esc(ST.TYPE_NAMES[k]), ST.RULES.perType + ' blueprints']))),
      sec('Coming later', p('The stash is open from the start while the game is being built. Later it opens for solo play after you beat the wave 100 boss, and online play can use it from the start.'))
    ] });
    const VR = d.VR || (typeof RefereeVariants !== 'undefined' ? RefereeVariants : require('../referee_variants.js')), RA = d.RA || (typeof RefereeAilments !== 'undefined' ? RefereeAilments : require('../referee_ailments.js'));
    out.push({ id: 'variants', title: 'Variants and Ailments', sections: [
      sec('Ember, Frost and Venom', p('From floor ' + VR.RULES.from + ' on, some monsters come as an Ember, Frost or Venom version. They have ' + pct(VR.VARIANTS.ember.hp - 1) + ' more health, hit harder, glow their colour, and every blow that lands puts an ailment on you. Deeper floors bring more of them (up to ' + pct(VR.RULES.max) + ' of the monsters). Bosses can be variants from floor ' + VR.RULES.bossFrom + ', and a variant boss also rains marked blasts of its element.')),
      sec('The three variants', table(['Variant', 'Puts on you', 'Weak to (gun status)', 'Barely hurt by'], VR.IDS.map((id) => { const v = VR.VARIANTS[id]; return [esc(v.name), esc(v.ail), esc(v.weak), esc(v.resist)]; }))),
      sec('Weak spots', p('A gun carrying the weak status does ' + pct(VR.RULES.weakMul - 1) + ' extra damage to that variant. A gun carrying its own status does ' + pct(1 - VR.RULES.resistMul) + ' less. Common guns carry no status, so look for a better rarity.')),
      sec('Burning', p('You lose ' + pct(RA.RULES.burn.dps, 1) + ' of your top health every second for ' + RA.RULES.burn.dur + ' seconds. Slide on the ground to put it out. Fireballs from Flame Spirits, the Demon Lord and the Elder Dragon set you burning too.')),
      sec('Frozen', p('You walk ' + pct(RA.RULES.freeze.slow) + ' slower for ' + RA.RULES.freeze.dur + ' seconds.')),
      sec('Poison', p('You lose ' + pct(RA.RULES.poison.dps, 1) + ' of your top health every second for ' + RA.RULES.poison.dur + ' seconds, and cannot heal until it wears off. Poison alone never kills you; it leaves you on 1 health.')),
      sec('Bosses open to your shots', p('After a big move a boss is left open for a moment: his bar says OPEN and your shots do ' + pct(VR.RULES.exposedMul - 1) + ' extra damage. Save your big hits for it. Deeper floors make a boss quicker (' + pct(VR.RULES.tempoPerFloor) + ' faster per floor).'))
    ] });
    out.push({ id: 'mods', title: 'Gun Mods', sections: [
      sec('What they are', p('Mods are small parts that bolt onto a gun. They have their own lines and never carry the ordinary gun or gear lines. Pick one up with E, A or by tapping its card, then open the Gear menu (G) to fit it. Taking one off puts it back in your bag (' + MD.BAG + ' places). Mods drop ' + pct(MD.DROP.chance) + ' of the time from monsters, ' + pct(MD.DROP.eliteChance) + ' from elites, and a boss always leaves one.')),
      sec('Lines by rarity', table(['Rarity', 'Lines on a mod', 'Mod places on a gun of that rarity', 'Fits a gun of'], RAR.map((r, i) => ['<b style="color:' + hex(r.color) + '">' + esc(r.name) + '</b>', String(MD.COUNT[i]), String(MD.SLOTS[i]), esc(RAR[MD.window(i)[0]].name + (MD.window(i)[0] === MD.window(i)[1] ? '' : ' to ' + RAR[MD.window(i)[1]].name))]))),
      sec('Any mod on any gun', p('A mod of any rarity fits any gun that has a free mod place. Take a mod off one gun and bolt it on another whenever you like: a weaker gun with a mod line you love can be the better build for you. The only limit is the number of places on the gun.')),
      sec('Mod lines', table(['Line', 'Does', 'Common', 'Legendary'], MD.LIST.map((a) => [esc(a.name), esc(a.text), '+' + pct(a.base * 0.8) + ' to ' + pct(a.base * 1.2), '+' + pct(a.base * 2 * 0.8) + ' to ' + pct(a.base * 2 * 1.2)])))
    ] });

    out.push({ id: 'gear', title: 'Gear', sections: [
      sec('Where you wear it', p('Five places: head, chest, boots and two charms. Gear on the floor is only picked up when you press pick up (E, A or tap its card). It goes on in its place and the old piece drops at your feet; the card says if it is better or worse. The merchant sells gear too. Defense stops at ' + pct(GR.DEF_CAP) + '.')),
      sec('Armor and charms by rarity', table(['Piece', 'Base (Common)', 'Names, Common to Legendary'], GR.SLOTS.map((s) => [esc(s[0].toUpperCase() + s.slice(1)), GR.BASE[s].def || GR.BASE[s].hp ? pct(GR.BASE[s].def, 1) + ' defense, +' + GR.BASE[s].hp + ' health' : 'nothing until its affixes (always at least one)', esc(GR.NAMES[s].join(', '))]))),
      sec('Which affixes fit which piece', table(['Piece', 'Can roll'], GR.SLOTS.map((s) => [esc(s), GR.pool(s, '').filter((a) => !a.cls).map((a) => esc(a.name)).join(', ')]))),
      sec('Class-only gear lines', table(['Class', 'Line', 'Does', 'On'], GR.LIST.filter((a) => a.cls).map((a) => [esc(a.cls), esc(a.name), esc(a.text), esc(a.slots.join(', '))])))
    ] });

    out.push({ id: 'shop', title: 'Merchant and gold', sections: [
      sec('The safe room', p('After each boss the door opens to a safe room with a merchant. You can leave any time; the next floor starts when you walk through the door.')),
      sec('Prices', table(['Item', 'Cost'], [['Mend (full heal)', L.shopHeal + ' gold'], ['Class skill level', L.shopSkill + ' gold + ' + L.shopSkillPer + ' per level the skill already has'], ['Gun or gear', WP.SHOP.base + ' gold x (1 + ' + WP.SHOP.perRarity + ' per rarity step) x (1 + ' + pct(WP.SHOP.perWave) + ' per wave)']])),
      sec('Gold', p('Monsters drop coins: ' + L.goldPerXp + ' gold per XP point of the monster, a bit more every wave, x' + L.goldElite + ' from elites.'))
    ] });
    return out;
  }
  // every section as plain text for the search box
  const plain = (html) => html.replace(/<[^>]+>/g, ' ').replace(/&#9733;/g, 'star').replace(/&[a-z]+;/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
  function search(pgs, q) {
    const w = String(q || '').toLowerCase().split(/\s+/).filter(Boolean); if (!w.length) return [];
    const out = [];
    for (const pg of pgs) for (const s of pg.sections) { const hay = plain(s.title + ' ' + s.html); if (w.every((x) => hay.includes(x))) out.push({ page: pg.title, title: s.title, html: s.html }); }
    return out;
  }
  return { pages, search, plain };
})();
if (typeof module !== 'undefined') module.exports = CodexPages;
