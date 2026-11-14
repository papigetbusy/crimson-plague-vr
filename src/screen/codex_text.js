/* The Codex's written explanations: what each monster does, what each status colour does, how the world works, the controls. Words only (look and help text):
   every number in the Codex comes from the referee's own data, so it cannot drift. tests/codex.test.js fails if a monster, class skill, gun, status, affix or gear piece has no entry here. */
const CodexText = (function () {
  const MONSTER = {
    fiend: 'The standard monster. A horned brute that walks straight at you and hits hard in melee. Fills every wave that is not taken by something else.',
    hound: 'Fast and fragile. Runs you down quickly and bites twice as often, but dies to one or two good hits.',
    golem: 'A slow wall of stone with a huge pile of health and a heavy blow. Slide away from it and keep shooting.',
    goblin: 'Small, quick and weak. Comes in numbers early on; easy kills that fill your XP bar.',
    skeleton: 'Tough bones and a slow, heavy swing with a long wind-up: you can step out of reach before it lands.',
    mushroom: 'Stays back and spits slow globs of spore at you. Dodge the glob, then shoot it.',
    eyeball: 'Floats above the ground and fires fast bolts from long range. Hard to hit while you run; stop and aim.',
    flame: 'A floating fire spirit that hurls slow fireballs and hits harder than most. Keep moving sideways.',
    bat: 'The Bat Lord, one of the four bosses at the end of a floor (picked at random). A fast flyer that circles you, rears up, then dives through the spot where you stood: a lane glows on the floor first, so step aside or slide through. A dive that lands drains your health into his. Calls bats at half health and enrages under a third.',
    lich: 'The Lich King, one of the four bosses. He keeps his distance, fires a fan of soul bolts and a ring of bolts with gaps (find a gap, or slide), blinks away when you get close and raises the dead at 60% health.',
    dragon: 'The Elder Dragon, one of the four bosses. He stands his ground: a sweeping cone of fire (lanes show where it will go; step out of it) and a tail slam that shocks everything close (a ring shows its reach). Slow, huge and very tough.',
    demon: 'The Demon Lord, one of the four bosses at the end of a floor (picked at random). He sleeps at the door until you come close or hurt him, then charges, throws fireballs, calls hounds at half health and goes into a rage under about a third of his health. He always drops a gun and a piece of gear, a rarity band better than normal.'
  };
  const STATUS = {
    fire: ['Fire', 'red', 'Burns the monster: a share of the hit lands again over a few seconds.'],
    poison: ['Poison', 'purple', 'A toxin that deals damage over time. Stacks with other hits by keeping the strongest dose going.'],
    ice: ['Ice', 'blue', 'Chills monsters to half speed. The fifth chill in a row freezes them solid for a moment.'],
    electric: ['Electric', 'yellow', 'Each hit arcs lightning to the nearest other monsters for part of the damage.'],
    radiation: ['Radiation', 'green', 'Each hit sends out a pulse that hurts every monster around the target, and leaves them irradiated, taking damage for a few seconds.'],
    dark: ['Dark magic', 'black', 'Drains health back to you from each hit, and withers the target so it takes extra damage for a while.'],
    light: ['Light magic', 'white', 'Smites: each hit stuns the monster for a moment.']
  };
  const GUN_TYPE = {
    rifle: 'Rifles: a balanced automatic, the hall\'s baseline. The M4 Carbine is a 3-round burst rifle: one trigger pull fires a tight, accurate burst, then you have to let go and pull again. Each shot hits a little harder than the Gothic Rifle, with a short delay between bursts and a quicker reload.',
    pistol: 'Light and steady. Good damage per shot, small magazine, quick reload, very accurate. Your first gun is a plain silver pistol.',
    smg: 'Fast and spraying. Lower damage per bullet but a high fire rate and a big magazine.',
    shotgun: 'Seven pellets per shot, strong up close and weak at range. Reloads one shell at a time.',
    sniper: 'Huge damage in one slow, accurate shot. Tiny magazine; reloads by working the bolt.',
    hmg: 'Heavy machine guns: a huge magazine and steady fire, with a long reload and a wider spray.'
  };
  const RARITY_NOTE = [
    'Mostly drops on waves 1 to 10.', 'Green. Mostly waves 11 to 20, with a few earlier.', 'Blue. Mostly waves 21 to 30, with a few earlier.',
    'Purple. Mostly wave 31 on, with a few earlier.', 'Orange. Only from wave 31 on, with a chance that grows each wave. Bosses drop one rarity band higher than normal, so they can drop these first.'
  ];
  const WORLD = [
    ['The goal', 'Survive. There is no win condition yet: waves keep coming and the monsters grow stronger forever. How far you get is your score.'],
    ['Waves and floors', 'Each wave is a pack of monsters. Ten waves make a floor. Every tenth wave brings the floor\'s boss, the Demon Lord, who guards the door to the next floor in the far corner. Each floor is bigger than the last, up to a limit.'],
    ['Safe rooms and the merchant', 'Beating a boss opens the door to a safe room before the next floor. The merchant there sells a full heal, class skill levels, two guns and two pieces of gear for gold. Gold drops from monsters as coins.'],
    ['Levels and skills', 'Killing monsters drops XP. Each level-up gives you two picks: one class skill and one ordinary stat card. Class skills level up from use as well as from picking them again.'],
    ['Guns', 'You start with a silver pistol. Guns drop from monsters (more from elites, a sure drop from bosses). You carry two and swap between them. A gun lying on the floor is only picked up when you press pick up, so a good gun is never lost by accident. Hearts and flames are still picked up by walking over them.'],
    ['Gear', 'Armor (head, chest, boots) and two charms drop too. Armor gives defense and health, charms give nothing until their affixes roll. Like guns, gear on the floor is only picked up when you press pick up, and a piece you pick up goes on in its place, with the old piece dropping at your feet. The floor card tells you if it is better or worse than what you wear.'],
    ['Traps', 'Spikes, flame vents and rising spikes hurt you for a share of your health, and hurt monsters too. They get nastier on deeper floors.'],
    ['Fog', 'From wave 3 some ordinary waves roll in fog that cuts how far you can see. It thickens and lifts slowly, and the game announces it.'],
    ['Elites and the monster cap', 'Only so many monsters can be alive at once. Once waves pass that cap they stop getting more numerous and get stronger instead, forever. Elites are bigger, tougher monsters carrying abilities (armored, swift, brutal, volatile).'],
    ['Statuses on monsters', 'Gun status colours, poison, bleed and curses show on the monster: a coloured glow and a small badge above its head.']
  ];
  const CONTROLS = {
    keyboard: [['W A S D', 'move'], ['Mouse', 'look'], ['Left click', 'fire'], ['Right click', 'aim'], ['Shift', 'sprint'], ['C', 'slide while sprinting'], ['R', 'reload (hold with a full magazine to inspect)'], ['Q', 'swap guns'], ['E', 'pick up the gun or gear in front of you'], ['G', 'gear menu'], ['M', 'big map'], ['F', 'inspect the gun'], ['1 2 3 / 4 5 6', 'level-up and shop picks'], ['Tab', 'tuning panel']],
    touch: [['Left thumb', 'move stick'], ['Fire button', 'fire; drag on it to look'], ['Aim', 'toggle aim'], ['Run', 'toggle sprint'], ['Slide', 'slide while running'], ['Reload', 'reload'], ['Swap', 'swap guns'], ['Tap a gun or gear card', 'pick it up'], ['GEAR', 'gear menu'], ['Minimap', 'tap for the big map']],
    pad: [['Left stick', 'move'], ['Right stick', 'look'], ['RT / LT', 'fire / aim'], ['L3', 'sprint'], ['B (Circle)', 'slide'], ['X (Square)', 'reload'], ['Y (Triangle)', 'swap guns'], ['A (Cross)', 'pick up a gun; confirm in menus'], ['RB', 'gear menu'], ['Back / View', 'big map'], ['Start', 'pause']]
  };
  return { MONSTER, STATUS, GUN_TYPE, RARITY_NOTE, WORLD, CONTROLS };
})();
if (typeof module !== 'undefined') module.exports = CodexText;
