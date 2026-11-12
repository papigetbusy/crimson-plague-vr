# Working on Crimson Plague

Keep the code neat: small focused files and functions in clear folders, never one long tangled monolith (owner, 2026-10-19: no fixed line limit, but no monolith). Read `docs/design-lock.md`, `docs/art-contract.md` and `docs/roadmap.md` before changing anything. They are the rules of this project. **Work only on the current phase in the roadmap**; if the owner asks for something from a later phase, say so and ask before jumping ahead.

- The owner is not a programmer. Explain in plain language, one sentence per choice. He checks work on his iPhone: the green tick on GitHub and the published link (landscape phone).
- **Claude writes code. Grok makes art** (3D models for the gun and monsters). Claude never invents final art once Grok's models are in; Grok never edits `src/`. The handoff is `docs/art-contract.md`.
- `src/referee.js` owns every rule and number: movement, hits, damage, monster AI, ammo, reload timing, kills. It may not use the browser, clock, network, files or unseeded random (`tools/guard.js` enforces this).
- `src/screen.js` only draws the referee's snapshot and sends inputs. No rules, no game state of its own.
- Numbers live in the referee's `cfg` / defaults, never buried in screen code. Look-only numbers (colours, model offsets) live in screen.js.
- Every referee rule gets a test in `tests/` named as a plain sentence.
- Log every finished piece of work as one plain line at the top of `docs/changelog.md`.
- Push only when the owner has asked for the work. Commit messages say what changed in plain words.
- Claude and Grok both touch this repo: follow `docs/working-together.md` (pull first, claim the task, checks before and after pushing).

## If your turn was restarted
- **Start of every turn:** run `git status` and read `.claude-wip.md` if it exists, before changing anything.
- **`.claude-wip.md` exists:** an earlier run of you started this task. Its uncommitted changes are yours. Read them, run the checks, carry on from the steps not ticked.
- **Uncommitted changes but no `.claude-wip.md`:** they may be Grok's or the owner's. Look before touching them, ask if unsure.
- **Before your first edit on a task,** write `.claude-wip.md`: the request in the owner's words, the time, the plan as `- [ ]` steps, the files you expect to touch. Delete it once the push is green.
- **Never commit with `git commit -a` or `-am`.** `git status`, then `git add` only this task's files.

## Commands
- `node tests/referee.test.js` : referee tests
- `node tests/loop.test.js` : core loop checks (waves, xp, skills, boss, game over)
- `python3 tools/smoke_loop.py` : level-up / game over / boss HUD on a phone-sized page
- `node tests/models.test.js` : model checks (sight clear, anchors, face budget)
- `node tests/pad.test.js` : controller checks (Hypershot layout, dead zones, right-stick turn)
- `node tests/xr.test.js` : Meta Quest controller checks (Touch controllers become one standard pad, snap/smooth turn, aim maths)
- `node tests/grab.test.js` : VR grabbing and doors (the exact item a hand grabs, 7 m distance grab and walls, test-map door and loot, what each hand targets, grip held like a gun, shoulder swap)
- `NODE_PATH=<dir with puppeteer-core> node tools/xr_playtest.js [--md out.md] [--shots dir]` : full simulated Meta Quest playtest in headless Chrome (fake headset tools/xr_fake_quest.js): every pickup, door, button and menu, PASS/FAIL per check
- `node tests/touch.test.js` : touch button settings checks (size range, what can be hidden)
- `node tests/fx.test.js` : effect checks (look presets escalate common to legendary, sprite pool)
- `node tests/gun.test.js` : gun look checks (smoothed shape, skins, motion)
- `node tests/ember.test.js` : Ember Rifle checks (code-built gun: sight window clear, anchors, face budget)
- `node tests/revolver.test.js` : Revolver checks (picture silhouette, open trigger guard, sight clear, glow, face budget)
- `node tests/movement.test.js` : jump and slides in any direction, the 11.5 high roof
- `node tests/locks.test.js` : gold gates, the Key Keeper and key gate, and the boss door puzzle (toll, Scale, Coin Sockets, Fortune Wheels, sealed door, gold keeps coming, gates stop you until paid)
- `node tests/wallsets.test.js` : wall sets (6 looks cycling by floor, own colours, same paint every time, Crypt restores)
- `node tests/skins.test.js` : player skins (7 looks, box budget, fallbacks) and the real gun in a friend's hand
- `node tests/weapons.test.js` : weapons (silver pistol start, two carried guns and swap, per-gun numbers, rarity by wave, drops)
- `node tests/affixes.test.js` : gun affixes (count by rarity, class-only lines, what each does, the floor gun card)
- `node tests/gear.test.js` : gear (armor and charms: affix counts and fit, class-only lines, drops, pickup rules, defense/health/speed in a run, the Gear menu and floor card)
- `node tests/codex.test.js` : Codex (every class, skill, monster, gun, status, affix, rarity and gear piece explained from the game's own data; search)
- `node tests/mods.test.js` : gun mods (lines by rarity, which guns each fits, mod places by gun rarity, bag of 6, fitting and removing, drops, the Gear menu bag)
- `node tests/stash.test.js` : stash and blueprints (3 gun + 3 mod places, put in / take out / swap at the chest, the hall-door menu that lets you take one gun and any mods, stash kept between runs, 3 blueprints per type, starting a run from blueprints, the menus)
- `node tests/gifts.test.js` : the six newer level-up gifts (Lucky Drops, Thick Skin, Gold Rush, Overcharge, Bounce Pad, Second Wind)
- `node tests/variants.test.js` : Ember/Frost/Venom monsters, burn/freeze/poison on you, weak spots
- `node tests/bossmoves.test.js` : the extra boss moves, the open moment, variant bosses, deeper-floor speed
- `node tests/saves.test.js` : seeds and saves (map seed kept in a save, damage and item seeds fresh every time, what a save holds, the saves list)
- `node tests/stuck.test.js` : never stuck (a level-up can always be picked, at the merchant, at the chest, after a save; random play never throws or stalls)
- `node tests/floorguns.test.js` : floor guns (one default pickup model per gun type, told apart by size and shape, shaded in the rarity colour)
- `node tests/trail.test.js` : gold trail (the walking route from you to the Demon Lord that the minimap draws: starts at him, ends at you, stays on floor)
- `node tests/bosses.test.js` : bosses (random pick per floor, tougher each floor, the Bat Lord dives and drains, the Lich King rings, fans, blinks and raises the dead, the Elder Dragon breathes and slams)
- `node tests/coop.test.js` : co-op (a host and two friends over an in-memory link: join, shared monsters, own loot/gold/level-ups, scaling, down and revive, everyone down, shared doors and floors, menus do not stop the world)
- `node tests/gunfx.test.js` : gun status effects (fire burns, poison, ice slows and freezes, electric arcs, radiation pulse, dark drains and withers, light smites, legendaries carry two)
- `node tests/guns.test.js` : the 20 catalog guns (5 types x 4 versions: sight clear, hands on grip and fore-end, skin exists, face budget)
- `node tests/world.test.js` : hall look checks (banners, floors, ribs, baked light)
- `node tests/monsters.test.js` : monster checks (wind-up and reach, ranged attackers, projectiles, slide, unlock waves)
- `node tests/rigs.test.js` : every monster builds into a rig and every pose runs
- `node tests/elites.test.js` : past the monster cap (more health and damage forever, elites with abilities, volatile blast)
- `node tests/classes.test.js` : classes (Gunslinger, Assassin, Witch: start bonuses, two-row level-ups, every skill and ultimate, cloak, skill levels)
- `node tests/fog.test.js` : fog waves (which waves, thickening and lifting, announced)
- `node tests/shop.test.js` : gold, coin drops, the safe room after a boss, the merchant (buy class skill levels and a full heal)
- `node tests/traps.test.js` : traps (spikes, flame vents, rising spikes; where they sit, when they hurt you and monsters, deeper tiers hit harder)
- `node tests/floor.test.js` : floor checks (sizes, connected rooms, far-corner door, short carpet)
- `python3 tools/floor_map.py out.png [floor ...]` : draws top-down pictures of generated floors
- `python3 tools/hall_shot.py out_dir [view ...]` : draws pictures of the hall the way the game does, with no GPU (corridor, hall, torch, banner, ceiling, carpet, or x,z,yaw,pitch)
- `python3 tools/extract_ct_assets.py` then `python3 tools/pack_fx.py` : pull the owner's free art packs out of the CT page into git-ignored `assets-private/` (full packs never go in the repo), and pack the effect sheets into `src/screen/fx_data.js` (committed, credited in `docs/credits.md`) (without it the build just shows the plain voxel effects)
- `python3 tools/smoke_mouse.py` : desktop mouse check (mouse captured while playing, released for a level-up so a click works, number keys pick, mouse taken back, aim and shoot buttons held together in either order)
- `python3 tools/smoke_pad.py` : fake-controller run on phone and desktop sizes (connect, play, level-up, pause, unplug)
- `python3 tools/smoke_stash.py seed.json` : stash at the hall door (opens by itself when the browser stash holds something, take one gun and mods; seed.json is a list of stash entries)
- `python3 tools/smoke_coop.py` : two browser windows with a fake matchmaker: host a room, join by code, start together, see each other's monsters, revive a downed friend (needs the cheat build)
- `node tools/preview_models.js rifle|fiend out.json` then `python3 tools/preview_models.py out.json out.png side|front|back|three|top` : draws a model with no GPU
- `node tools/skin_dump.js out.json [gun]` then `python3 tools/skin_sheet.py out.json out.png front|three|back` : draws the 7 player skins holding a real gun with no GPU
- `python3 tools/wall_sets_sheet.py out.png` : draws every wall set's textures large; `WALLSET=<id> python3 tools/hall_shot.py ...` draws the hall in one set; `FLOOR=<n> python3 tools/hall_shot.py out gate sign station both socket` draws the gold gate, boss door sign and puzzle with the game's own code
- `node tools/gun_sheet.js out.png ext cy id [id ...]` : draws catalog guns side and three-quarter with no GPU; `node tools/pack_guns.js <Quaternius OBJ dir>` rebuilds `src/models/guns_packed_data.js` from the CC0 pack
- `node tools/guard.js` : architecture guard
- `node tools/build.js` : builds `site/index.html` (one playable page, the real game: no Effects or Gun menu)
- `node tools/build.js x --cheat` : builds the private cheat page `cheat/index.html` (git-ignored, never published) with the Effects and Gun menus; the owner tests on this one
- `python3 tools/smoke.py` : phone/desktop smoke test (needs Playwright)
