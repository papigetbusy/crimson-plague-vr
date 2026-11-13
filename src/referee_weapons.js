/* Weapons: the guns' numbers, the five rarities, and what drops when. Pure data and pure functions (no browser, no clock, no random of their own:
   the referee hands in its seeded rng). Every number is a multiplier on the referee's cfg gun (damage, fireRate, magSize, reloadTime, spread),
   so the starting rifle ('rifle', all ones) is the baseline that older tests and tuning use. A gun item is { id, rarity, wave, status[], affixes[] }. */
const RefereeWeapons = (function () {
  const AF = typeof RefereeAffixes !== 'undefined' ? RefereeAffixes : require('./referee_affixes.js');   // bonus lines a gun can carry
  const MD = typeof RefereeMods !== 'undefined' ? RefereeMods : require('./referee_mods.js');          // parts bolted onto a gun
  const RARITIES = [
    { id: 'common', name: 'Common', color: 0xc8ccd4, dmg: 1.0 },
    { id: 'uncommon', name: 'Uncommon', color: 0x4fd65a, dmg: 1.3 },
    { id: 'rare', name: 'Rare', color: 0x4a9bff, dmg: 1.65 },
    { id: 'epic', name: 'Epic', color: 0xb05cff, dmg: 2.1 },
    { id: 'legendary', name: 'Legendary', color: 0xffa21a, dmg: 2.8 }
  ];
  // what each kind of gun is like (multipliers on cfg.damage, fireRate, magSize, reloadTime and spread; pellets = bullets per shot)
  const TYPES = {
    rifle:   { dmg: 1,    rate: 1,    mag: 1,    reload: 1,    spread: 1,   pellets: 1 },
    pistol:  { dmg: 1.5,  rate: 0.55, mag: 0.4,  reload: 0.65, spread: 0.6, pellets: 1 },
    smg:     { dmg: 0.7,  rate: 1.4,  mag: 1.1,  reload: 0.85, spread: 1.5, pellets: 1 },
    shotgun: { dmg: 0.75, rate: 0.15, mag: 0.2,  reload: 1.1,  spread: 2.5, pellets: 7 },
    sniper:  { dmg: 7,    rate: 0.1,  mag: 0.17, reload: 1.25, spread: 0.1, pellets: 1 },
    hmg:     { dmg: 1.1,  rate: 1.2,  mag: 3.4,  reload: 1.9,  spread: 1.8, pellets: 1 }
  };
  // the guns: its type, how this version differs from the type's plain numbers, and its status effect (what Phase 6 will make each shot do; legendaries get a second one).
  // The starting rifle stays the all-ones baseline. The M4 Carbine is a second rifle: a bit faster and lighter, obtainable like the other droppable guns.
  const GUNS = {
    rifle:               { name: 'Gothic Rifle',   type: 'rifle', status: [] },
    rifle_m4:            { name: 'M4 Carbine',     type: 'rifle', v: { dmg: 0.9, rate: 1.2, reload: 0.85, spread: 1.05 }, status: [] },
    pistol_service:      { name: 'Service Pistol', type: 'pistol', status: [] },
    pistol_cannon:       { name: 'Hand Cannon',    type: 'pistol', v: { dmg: 1.6, rate: 0.7, mag: 0.6 }, status: ['fire'] },
    pistol_machine:      { name: 'Machine Pistol', type: 'pistol', v: { dmg: 0.55, rate: 2.3, mag: 1.7, reload: 1.1 }, status: ['electric'] },
    pistol_duelist:      { name: 'Duelist',        type: 'pistol', v: { dmg: 1.25, rate: 0.85, mag: 0.7, spread: 0.5 }, status: ['ice'] },
    smg_compact:         { name: 'Compact SMG',    type: 'smg', status: ['radiation'] },
    smg_tactical:        { name: 'Tactical SMG',   type: 'smg', v: { dmg: 1.15, rate: 0.85, spread: 0.7 }, status: ['dark'] },
    smg_bullpup:         { name: 'Bullpup SMG',    type: 'smg', v: { dmg: 1.2, rate: 0.95, mag: 0.9, spread: 0.8 }, status: ['poison'] },
    smg_drum:            { name: 'Drum SMG',       type: 'smg', v: { dmg: 0.9, rate: 1.05, mag: 2.1, reload: 1.3 }, status: ['fire'] },
    shotgun_pump:        { name: 'Pump Shotgun',   type: 'shotgun', status: ['electric'] },
    shotgun_double:      { name: 'Double Barrel',  type: 'shotgun', v: { dmg: 1.4, rate: 0.9, mag: 0.4, spread: 1.15 }, status: ['ice'] },
    shotgun_combat:      { name: 'Combat Shotgun', type: 'shotgun', v: { dmg: 0.8, rate: 2.2, mag: 1.7, spread: 1.1 }, status: ['radiation'] },
    shotgun_blunderbuss: { name: 'Blunderbuss',    type: 'shotgun', v: { dmg: 1.25, rate: 0.7, mag: 0.5, spread: 1.6 }, status: ['fire'] },
    sniper_bolt:         { name: 'Bolt Rifle',     type: 'sniper', status: ['light'] },
    sniper_antimat:      { name: 'Anti-Materiel',  type: 'sniper', v: { dmg: 1.8, rate: 0.7, mag: 0.6, reload: 1.3 }, status: ['fire'] },
    sniper_marksman:     { name: 'Marksman Rifle', type: 'sniper', v: { dmg: 0.45, rate: 2.6, mag: 2, reload: 0.9, spread: 1.6 }, status: ['radiation'] },
    sniper_rail:         { name: 'Rail Rifle',     type: 'sniper', v: { dmg: 1.4, rate: 1.1, mag: 0.8 }, status: ['electric'] },
    hmg_belt:            { name: 'Belt MG',        type: 'hmg', status: ['poison'] },
    hmg_minigun:         { name: 'Minigun',        type: 'hmg', v: { dmg: 0.6, rate: 2.2, mag: 1.5, reload: 1.2, spread: 1.2 }, status: ['electric'] },
    hmg_drum:            { name: 'Drum LMG',       type: 'hmg', v: { dmg: 1.25, rate: 0.8, mag: 0.7, spread: 0.8 }, status: ['dark'] },
    hmg_chain:           { name: 'Chaingun',       type: 'hmg', v: { dmg: 0.85, rate: 1.4, mag: 1.2, reload: 1.1 }, status: ['ice'] }
  };
  const DROPPABLE = Object.keys(GUNS).filter((id) => id !== 'rifle');
  const STATUSES = ['radiation', 'poison', 'electric', 'ice', 'fire', 'dark', 'light'];
  const DROP = {
    chance: 0.07, eliteChance: 0.4,          // the chance an ordinary monster, an elite, drops a gun (a boss always does, one rarity band higher)
    band: 10, minorBase: 0.12, minorPer: 0.015, legendBase: 0.06, legendPer: 0.01, legendMax: 0.3,   // ten waves to a rarity band; the next rarity up shows up more often as the band goes on
    waveGrowth: 0.04, life: 60, noPick: 1.5   // every wave adds this to a gun's damage when it drops (until the cap, chosen later); how long a gun lies there; seconds before a gun you just dropped can be picked up again
  };

  const SHOP = { offers: 2, base: 100, perRarity: 1.2, perWave: 0.05, betterBand: 10 };   // the merchant's guns: how many, and the price (base, times more per rarity step, times more every wave); the last one is a band better
  const price = (item) => Math.round(SHOP.base * (1 + SHOP.perRarity * item.rarity) * (1 + SHOP.perWave * ((item.wave || 1) - 1)));
  // which rarity (0..4) drops on wave w: waves 1-10 mostly common with a few uncommon, 11-20 mostly uncommon with a few rare, 21-30 mostly rare with a few epic, 31+ mostly epic with a chance of legendary
  function rarityFor(w, rng) {
    const band = Math.floor((w - 1) / DROP.band), at = (w - 1) % DROP.band;
    if (band >= 3) { const p = Math.min(DROP.legendMax, DROP.legendBase + DROP.legendPer * (w - 31)); return rng() < p ? 4 : 3; }
    return rng() < DROP.minorBase + DROP.minorPer * at ? band + 1 : band;
  }
  const make = (id, rarity, wave, rng, cls) => {
    const g = GUNS[id] || GUNS.pistol_service, status = rarity >= 1 ? g.status.slice() : [];      // a common gun is plain: no status effect (uncommon and better carry the gun's own, legendaries a second)
    while (rarity >= 4 && rng && status.length < 2) { const rest = STATUSES.filter((s) => !status.includes(s)); status.push(rest[Math.floor(rng() * rest.length)]); }   // only legendaries carry two
    return { id: GUNS[id] ? id : 'pistol_service', rarity, wave: wave || 1, status, affixes: rng ? AF.roll(rarity, rng, cls || '') : [] };
  };
  const roll = (w, rng, extra, cls) => make(DROPPABLE[Math.floor(rng() * DROPPABLE.length)], Math.min(4, rarityFor(w + (extra || 0), rng)), w, rng, cls);
  // the numbers of a gun item, against cfg
  function stats(item, cfg) {
    const g = GUNS[item.id] || GUNS.pistol_service, t = TYPES[g.type], v = g.v || {};
    const k = (key) => t[key] * (v[key] || 1);
    const grow = 1 + DROP.waveGrowth * ((item.wave || 1) - 1);
    const a = (stat) => AF.sum(item, stat) + MD.sum(item, stat);     // the gun's own lines plus its mods' lines
    return {
      dmg: cfg.damage * k('dmg') * RARITIES[item.rarity].dmg * grow * (1 + a('dmg')), rate: cfg.fireRate * k('rate') * (1 + a('rate')), mag: Math.max(1, Math.round(cfg.magSize * k('mag') * (1 + a('mag')))),
      reload: cfg.reloadTime * k('reload') * Math.max(0.3, 1 - a('reload')), spread: k('spread') * Math.max(0.1, 1 - a('spread')), pellets: t.pellets,
      crit: a('crit'), critDmg: a('critdmg'), head: a('head'), leech: a('leech'), status: a('status'),    // extras the referee reads when a shot lands
      ads: a('ads'), adsMove: a('adsmove')                                                              // from mods: faster aiming, faster walking while aiming
    };
  }
  // a mod as a card: name, colour and its lines (and the reason it will not fit a gun, when a gun is given)
  const modView = (m, gun) => ({ name: MD.nameOf(m), rarity: m.rarity, rarityName: RARITIES[m.rarity].name, color: RARITIES[m.rarity].color, affixes: m.affixes.map(MD.describe), why: gun ? MD.why(gun, m) : '' });
  // everything the screen needs to show a gun in a card: name, colour, numbers, status and affix lines
  function view(item, cfg) {
    const st = stats(item, cfg), g = GUNS[item.id] || GUNS.pistol_service, r = RARITIES[item.rarity];
    return { id: item.id, name: item.label || g.name, baseName: g.name, label: item.label || '', type: g.type, rarity: item.rarity, rarityName: r.name, color: r.color, status: item.status.slice(),
      dmg: Math.round(st.dmg), rate: Math.round(st.rate * 10) / 10, mag: st.mag, reload: Math.round(st.reload * 10) / 10, pellets: st.pellets,
      affixes: (item.affixes || []).map(AF.describe), slots: MD.slotsFor(item.rarity), mods: (item.mods || []).map((m) => modView(m)) };
  }
  // the name you give a gun: letters, numbers and a few marks, 24 at most; empty means the regular name
  const cleanLabel = (s) => String(s == null ? '' : s).replace(/[^\w .,'!?&+-]/g, '').replace(/\s+/g, ' ').trim().slice(0, 24);
  return { cleanLabel, RARITIES, TYPES, GUNS, DROPPABLE, STATUSES, DROP, SHOP, price, rarityFor, make, roll, stats, view, modView, AF, MD };
})();
if (typeof module !== 'undefined') module.exports = RefereeWeapons;
