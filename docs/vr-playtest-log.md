# VR playtest log (simulated Meta Quest 3)

How it is tested: `tools/xr_playtest.js` opens the built page in headless Chrome with a fake Quest (`tools/xr_fake_quest.js`: a WebXR immersive-vr session, a head and two Touch controllers with xr-standard buttons, sticks and haptics). It moves the hands to real items, gates and doors in the level, squeezes grips, pulls triggers, clicks sticks and points the laser at menu buttons, then reads the game's own state to see what really happened. Screenshots go to the folder given with `--shots`.

## Everything you can pick up or use (audit of the code, 2026-11-12)
| Thing | Where it comes from | How it is taken / used | In VR before the fix |
|---|---|---|---|
| Gun on the floor | monster drops, the boss, the gun you swap away, test-map rack | pick up (game: manual only, so nothing is swapped by accident); fades after 60 s | right grip only; took the nearest within 2.6 m of your feet, not the one you reached for |
| Armor (head, chest, boots, charms) | drops, test map | pick up (goes on even if worse, on purpose) | same as guns |
| Gun mod | drops, test map | pick up into the bag (6 places) | same as guns |
| Heart (heal) and flame (frenzy) | drops | walk over them (automatic) | worked |
| Coins and XP orbs | every kill | pulled to you and taken automatically | worked |
| Gold gate (toll) | across corridors on every floor | pay the price at it (5 m reach) | right grip only, no highlight, no reason when short of gold; on the test map all gates were already open |
| Key gate | floor 3+, last gate | use the Key Keeper's key | right grip only |
| Boss door | every floor | opens by itself when the boss is dead and the puzzle is solved | grip did nothing and said nothing; on the test map this was the only closed door, so "doors don't open" |
| Scale / Fortune Wheels | beside the boss door | first action = grip, second (take gold back) = hard push down on the right stick | right grip only |
| Coin Sockets | in the halls | shoot them | worked |
| Safe-room door | after the boss | open; walk through | worked |
| Stash chest | safe room | grip at it opens the stash menu | right grip only |
| Merchant | safe room | walk up: the shop opens | worked |

## Before the fix (build e61a65f), 2026-11-12
26 of 46 checks passed. Notes on the ones that need reading: the "shoulder swap" in the first run only "passed" because the grip grabbed a floor gun near your feet (that is the bug); the stash and merchant rows first failed because the boss's level-up cards were open (the test now picks them with the laser); the safe-room door row failed because of the test's teleport (fixed in the harness, not a game bug).

| # | Area | Check | Result | Seen / why |
|---|---|---|---|---|
| 1 | pickup | Right grip with your hand at your side takes a gun lying at your feet | PASS | pistol -> shotgun |
| 2 | pickup | Reaching a hand to an item highlights it | **FAIL** | no highlight existed |
| 3 | pickup | Light buzz when a hand touches something grabbable | **FAIL** | 0 pulses |
| 4 | pickup | Right hand reaching down + grip takes THAT gun | **FAIL** | took a different gun (nearest to the feet, not the hand) |
| 5 | pickup | Firm buzz when the grab lands | **FAIL** | no haptic on pickup |
| 6 | pickup | Left hand reaching down + left grip takes that gun | **FAIL** | the left grip never grabbed anything |
| 7 | pickup | Pointing at an item 5 m away highlights it | **FAIL** | no distance grab |
| 8 | pickup | Point + grip pulls it from 5 m | **FAIL** | out of the 2.6 m reach; grip took another gun instead |
| 9 | pickup | Grip already held (like a gun), hand reaches an item: taken | **FAIL** | a grab only counted the instant the grip went down |
| 10 | pickup | Gun mod: reach + grip | PASS | (it was the nearest item) |
| 11 | pickup | Left grip on the fore-end = two-handed hold | PASS | |
| 12 | pickup | Right hand over the shoulder + grip swaps to the back gun | **FAIL** | grabbed a floor gun instead |
| 13 | pickup | Test-map guns still there after a minute | **FAIL** | floor loot fades after 60 s, the test map's gifts too (found in code, proved in tests/grab.test.js) |
| 14 | doors | Gold gate without enough gold says why | **FAIL** | nothing happened, no buzz, no message |
| 15 | doors | Gate highlighted when you stand at it | **FAIL** | |
| 16 | doors | LEFT grip at the gate pays and opens it | **FAIL** | left grip unused |
| 17 | doors | RIGHT grip at the gate pays and opens it | PASS | |
| 18 | doors | Walk through the open gate | PASS | |
| 19 | doors | Sealed boss door says what opens it | **FAIL** | grip did nothing, said nothing |
| 20 | doors | Test map: grip opens the boss door | **FAIL** | sealed until the boss dies (the only closed door on the test map) |
| 21 | doors | Walk into the open boss door: safe room | PASS | (opened by killing the boss in the test) |
| 22 | doors | Stash chest: grip opens it | PASS | |
| 23 | doors | Y closes the stash | PASS | |
| 24 | doors | Merchant: walk up, shop opens | PASS | |
| 25 | doors | Y leaves the shop | PASS | |
| 26-45 | controls | Move, sprint (full push and click), A jump, B slide, fire, X reload, ADS, turn, right stick forward does nothing, stick-click swap, Y pause, laser click, Y back, double-tap Y map, Y closes map, hold Y Gear, menu scroll, Y closes Gear, no script errors | PASS | all worked |

## After the fix, 2026-11-12 (run twice, same result)
| # | Area | Check | Result | Seen |
|---|---|---|---|---|
| 1 | pickup | Right grip with your hand at your side takes a gun lying at your feet | PASS | pistol_service -> pistol_service, floor items 9 -> 8 |
| 2 | pickup | Reaching a hand to an item highlights it (you can see what you will grab) | PASS | hover={"mode":"near","id":10,"text":"Bolt Rifle  (Rare)","ok":true} |
| 3 | pickup | A light buzz in that hand when it touches something you can grab | PASS | 1 pulses |
| 4 | pickup | Right hand reaching down + grip takes THAT gun (sniper) | PASS | held sniper_bolt |
| 5 | pickup | A firm buzz when the grab lands | PASS | [{"hand":"right","s":0.65,"ms":45,"f":75}] |
| 6 | pickup | Left hand reaching down + left grip takes THAT gun (it lands in your gun hand) | PASS | held smg_compact |
| 7 | pickup | Pointing a hand at an item 5 m away highlights it (distance grab) | PASS | hover={"mode":"ray","id":12,"text":"Belt MG  (Rare)","ok":true} |
| 8 | pickup | Point + grip pulls that item from 5 m away (distance grab) | PASS | held hmg_belt |
| 9 | pickup | Grip already squeezed (held like a gun) and hand reaches an item: it is still taken (armor) | PASS | taken |
| 10 | pickup | Gun mod: reach + grip puts it in your bag | PASS |  |
| 11 | pickup | Left grip on the gun's fore-end = two-handed hold | PASS | twoHand=true |
| 12 | pickup | While firing, the gun hand does not light up far items; let go and it does | PASS | firing: {"mode":"body","id":21,"text":"Bloodforged Cuirass  (Epic)","ok":true} / after: ray |
| 13 | pickup | Coins: walking near them picks them up by themselves | PASS | gold 1000 -> 1008 |
| 14 | pickup | Right hand over your right shoulder + grip swaps to the gun on your back (picks nothing up) | PASS | sniper_bolt (back pistol_service) -> pistol_service, floor items 15 -> 15 |
| 15 | doors | Gold gate with too little gold stays shut, and tells you why (buzz + message) | PASS | gold 0, pulses 1, hint {"right":{"mode":"use","text":"Need 80 gold","ok":false,"what":"toll"},"left":{" |
| 16 | doors | Gate is highlighted when you stand at it (shows the price) | PASS | {"right":{"mode":"use","text":"Pay 80 gold","ok":true,"what":"toll"},"left":{"mode":"use","text":"Pay 80 gold","ok":true |
| 17 | doors | LEFT grip at the gate pays and opens it | PASS | open=true |
| 18 | doors | Opening a gate gives a buzz | PASS | 3 pulses |
| 19 | doors | Walk through the open gate (left stick forward) | PASS | side 2.2 -> -6.6 |
| 20 | doors | Sealed boss door: grip tells you what opens it (buzz + message; it stays shut until the boss is down) | PASS | open=false pulses=1 hint={"mode":"use","text":"Sealed: kill the boss to open it","ok":false,"what":"door"} |
| 21 | doors | Test map: grip at the boss door opens it | PASS | open=true |
| 22 | doors | Standing in front of the door is not already through it (test setup) | PASS |  |
| 23 | doors | Walk into the open boss door: the safe room | PASS | safe=true |
| 24 | doors | Stash chest: stand at it, grip opens it (menu in front of you) | PASS | near=true menu=true |
| 25 | doors | Y closes the stash | PASS |  |
| 26 | doors | Merchant: walk up and the shop opens in VR | PASS | {"shop":true,"menu":true} |
| 27 | doors | Y leaves the shop | PASS |  |
| 28 | doors | Safe room door: walk through to the next floor | PASS | safe=false floor=2 |
| 29 | controls | Left stick forward walks | PASS | 1.87 m |
| 30 | controls | Left stick all the way forward sprints | PASS | sprinting=true |
| 31 | controls | Left stick click sprints | PASS | sprinting=true |
| 32 | controls | A jumps | PASS | eye 1.70 -> max 3.81 |
| 33 | controls | B slides | PASS | sliding=true |
| 34 | controls | Right trigger fires | PASS | ammo 12 -> 9 |
| 35 | controls | X reloads (animation on the gun) | PASS | reloading=true |
| 36 | controls | Left trigger aims down sights | PASS | adsT=1.00 |
| 37 | controls | Right stick sideways turns | PASS | yaw 1.57 -> 3.52 |
| 38 | controls | Right stick forward does nothing in play (no surprise jump or turn) | PASS |  |
| 39 | controls | Right stick click swaps guns | PASS | rifle -> pistol_service |
| 40 | controls | Tap Y pauses (menu in front of you) | PASS | menu=true |
| 41 | controls | Laser + trigger presses a menu button (RESUME) | PASS | hover=RESUME, menu after=false |
| 42 | controls | Y backs out of the pause menu | PASS |  |
| 43 | controls | Double-tap Y shows the map | PASS | map=true |
| 44 | controls | Tap Y closes the map without pausing | PASS |  |
| 45 | controls | Hold Y opens the Gear menu | PASS | menu=true |
| 46 | controls | Right stick scrolls a long menu | PASS | scroll 0 -> 180 of 180 |
| 47 | controls | Y closes the Gear menu | PASS |  |
| 48 | controls | No script errors during the run | PASS |  |

48/48 passed

Unit checks: `node tests/grab.test.js` (32 checks) and every other test in tests/ pass.

## Final check on the committed build

`sh tools/xr_check_all.sh` (guard, build, every unit test, full fake-Quest run): **48/48**. One earlier run showed "B slides" failing 1 time in 4. Cause: the test pressed B while the player was still in the air from the jump test, and the game doesn't allow a slide in mid-air (that's correct). The test now waits for the player to land. After that it passed 4/4 controls-only runs plus the full run. It also shows a jump lasts a long time (about half a second or more in the air), which ties into the jump-height comfort item below.

## Overnight round, 2026-11-12 evening (owner: "all mechanics, all menus, gun mods, stashes")

New playtest groups (in `tools/xr_playtest_more.js`, run by `tools/xr_playtest.js`):
- **game**: the real game (not the test map). Start menu → pick a class with the laser → Enter the hall → shoot a monster dead → ammo and X reload → level-up cards → double-tap Y map → Y pause → Codex from pause (scroll, Y back) → Y resume → safe room → merchant buy → Y leave → die → YOU FELL → RISE AGAIN.
- **menus**: the Gear menu and gun mods (fit to the gun in your hands, take off, fit to the gun on your back), and the stash chest (open with grip, put in, take out, save game, Y close).

### Before (first run of the new groups, before any fixes): 31 of 40 passed
| Found | Why | Fix |
|---|---|---|
| Putting the headset on at the title skipped the start menu and started a Gunslinger run straight away (no class pick in VR) | entering VR always called "begin" | VR now opens on the start menu (class buttons + Enter the hall, laser + trigger). A paused run and the test map still carry straight on |
| "Save game here" in the stash did nothing when the laser was on the tile's edge | the playtest aimed at tile edges (rounding put the laser 1 pixel outside); also a press failed if the menu redrew while the trigger was down | the playtest now aims at the middle of each tile; a press now counts for the same tile even after a redraw |
| ✔, · and ▼ showed as garbage letters (e.g. "Cannot: âœ” Saved") on a server that doesn't say the page is UTF-8 | the page had no `<meta charset>` | added `<meta charset="utf-8">` |
| Level-up "still open" after 10 picks, map/pause/codex checks after it | test gave 5000 XP = many level-ups at once | test now gives exactly one level |
| Double-tap Y flaky in the game group | the slow fake headset took longer than the 0.3 s double-tap window between taps | test uses the same tight tap pattern as the controls group |

### After batch 1: 90 of 90 (guard, build, all unit tests incl. new tests/vrflow.test.js, full fake-Quest run)
Gun mods in VR: **work** (open Gear with hold Y, fit to the gun in hands, take off, fit to the gun on your back, Y closes, play resumes).
Stash in VR: **works** (grip at the chest, put in, take out into your hands, Save game here, Y closes).

### Batch 2: multiplayer (co-op) and feel
New groups:
- **coop**: two players, each in their own browser window, linked by a fake PeerJS (same messages as the real one, carried over a BroadcastChannel). Pair 1: the host is in VR and opens a room with the laser on the VR menu; a flat friend joins with the code. Pair 2: a flat host; the friend is in VR and types the room code on new VR letter keys. Checks: both see each other move, the same monsters, the host's VR shot and the VR friend's shot hurt monsters on both screens, gold gates open for both, pause, no errors, sane traffic. **21/21.**
- **feel**: recoil kicks and settles, shotgun kicks and buzzes harder than an SMG, two hands halve the kick and buzz the left hand too, a hit marker shows at close range, walking reaches full speed and stops within 0.1 s, frame time. **12/12.**

| Found | Why | Fix |
|---|---|---|
| A friend in VR could not join a co-op room | the room-code box needs a keyboard, and the VR panel hid the co-op panel | VR letter keys (the code's own alphabet + DEL) on the co-op panel, shown only in VR; the VR menu lays them out 8 per row |
| Shots at monsters closer than ~3 m missed even with the gun pointed right at them | bullets start at the eye, not at the gun, so up close the eye's line and the gun's line miss each other | the eye now aims at the point the gun's line meets first (monster, wall or floor), so whatever the gun points at is what gets hit; the reticle sits on that point |
| No recoil or hit feedback in VR | not built | per-gun recoil (spring that kicks and settles, capped so it never pulls the gun off your hand), right-hand buzz per shot (stronger for heavy guns), left-hand buzz when two-handed, hit marker (red cross for crits, bigger for kills) |
| Walking took 0.15 s to reach speed (felt like ice-skating; motion sickness risk) | flat game's acceleration | VR uses near-instant start/stop (0.04 s); flat unchanged |
| (test tool) the second player's background tab froze | browsers slow background tabs | each player gets its own window |

### Batch 3: the boss door's puzzles, stash at the door of the hall, flat-vs-VR gaps
New group **mechanics**: **11/11.** The Scale (grip pays gold onto the pan; a hard push down on the right stick takes it back, the flat game's Z), Fortune Wheels (grip spins), Coin Sockets (point the gun at the socket and shoot it), a new run with a stashed gun (the stash opens at the door of the hall, "Take this gun" with the laser, Y enters the hall), and the two new pause-menu buttons.

| Found | Why | Fix |
|---|---|---|
| In VR there was no way to turn the sound off or start over | those buttons live on the flat Tuning panel (Tab, mouse only) | SOUND: ON/OFF and NEW RUN tiles on the VR pause menu (NEW RUN is refused in a co-op room) |
| Every gun felt the same weight in your hand | one aim smoothing for all guns | per-class weight: a pistol follows the hand fastest, rifle, shotgun/sniper, the heavy machine gun trails it a touch; two hands and aiming down sights keep their steadier rates. Gun and laser ride the same aim, so they never disagree |

### Flat controls vs VR (every flat key has a VR way)
| Flat | VR | Tested in the sim |
|---|---|---|
| WASD move, Shift sprint | left stick (click or push all the way to sprint) | yes |
| Mouse look | head + right stick snap/smooth turn | yes |
| Left mouse fire | right trigger | yes |
| Right mouse aim down sights | left trigger (the gun comes up to your eye; sniper shows a 4x scope) | yes |
| Space jump | A | yes |
| C / Ctrl slide | B | yes |
| R reload | X (or drop the mag) | yes |
| Hold R / F inspect | hold X with a full magazine | not checked (look only) |
| E pick up / use / stash | grip | yes |
| Z take back from the Scale | hard push down on the right stick | yes |
| Q swap gun | right stick click, or reach over your right shoulder + grip | yes |
| G gear | hold Y | yes |
| M map | double-tap Y | yes |
| 1-6 level-up picks | laser + trigger on the card | yes |
| Enter restart | RISE AGAIN tile | yes |
| Tab Tuning panel | SOUND / NEW RUN on the Y pause menu (the dev sliders stay flat-only) | yes |

### Batch 4: co-op over the real internet
New tool `tools/xr_coop_real.js`: two windows on the real PeerJS server (no fake). On this box the PeerJS library loads and the host gets a real room code, but this machine cannot make any WebRTC link at all (0 ICE candidates even for a bare RTCPeerConnection), so the actual friend-to-host link must be checked on a headset + phone/PC.

| Found | Why | Fix |
|---|---|---|
| A friend whose link never connects sat on "Joining room..." forever | the join had no time limit | gives up after 20 s with a clear message (check the code, host still waiting, same Wi-Fi helps); JOIN works again right away. Checked with the real server: 5/5 |
| The backup relay (openrelay.metered.ca, user "openrelayproject") no longer works | Metered retired the shared public login; it now needs a free account + API key | not fixed (needs an account the owner signs up for). Co-op still works whenever the two devices can link directly (same Wi-Fi, most home internet); it can fail on some phone networks |

### Batch 5: Quest draw calls (VR only; the flat game is unchanged)
| Found | Why | Fix |
|---|---|---|
| 263 draw calls per eye mid-fight (Quest 3 wants well under ~200) | every torch was 6 separate meshes (22 sconces + 6 braziers), and the floor was cut into 12 x 12-cell chunks per texture (about 55 in view) | in VR the torches are drawn as 12 instanced meshes in all (glow becomes a camera-facing additive quad, same look: checked side by side at 2 m, `torch_compare.png`), and the floor uses merged 2 x 2-chunk meshes (same quads, fog hides the extra reach). Mid-fight test: **263 -> 133 per eye**; standing in the full game ~110 -> ~75. `window.__noInst = true` switches back to compare |
| (found while doing it) calling `renderer.xr.getCamera()` mid-frame broke sprinting and laser clicks | in three r128 it moves the camera to the headset pose as a side effect | not used; the glow faces the player's eye point |

### Batch 6: Comfort settings on the VR pause menu
Three new tiles on the Y pause menu, saved on the headset between visits (a link flag like `?snap` or `?vignette` still wins): **SPEED: NORMAL / COMFORT (slower)** (4.5 m/s walk, 7 m/s sprint instead of 6.2 / 10; only in VR, put back on leaving VR), **TURN: SMOOTH / SNAP** (45 degree steps), **VIGNETTE: OFF / ON**. Defaults unchanged. Mechanics group: 16/16 (toggles, saved, walk tops out at 7 m/s, one snap push = 46 degrees, all back off).

### Batch 8: turn speed, walk-from-the-left-hand, and a small collimated red dot
Two new tiles on the Y pause menu, saved with the other comfort settings (a `?turn=` or `?snap=30` link still wins for that visit): **TURN SPEED: SLOW / NORMAL / FAST** (smooth: 2.5 / 4.5 / 7 rad/s; snap: 30 / 45 / 60 degrees), and **WALK: HEAD / LEFT HAND** (Onward-style: the left stick moves you the way the left controller points, or the way your head faces; falls back to the head if the left controller is missing). Default is still Normal and Head. Light pushes on the right stick are closer to linear (a half push is about a third of full speed, not a fifth), with a 0.12 deadzone so a resting stick does not drift. Mechanics group: turn-speed and walk tiles toggle and save, half-push ~1.6 vs full ~4.7 rad/s, Fast vs Slow about 8 vs 2.6 rad/s, walk-from-left-hand ~90 degrees off the head.

The pistol's red-dot sight is no longer an 8 mm cube with a 35 mm glow. In the flat game it is a small crisp point (about 1 mm, white-hot core, faint halo). In VR the on-gun blob is hidden and a collimated point sits on the actual fire ray (from the eye, toward the point the muzzle aims at, including walls in the way), about 1.5–2 MOA, so it overlays the impact from any eye position. Referee kick is off in VR so shots do not climb off the dot. Feel group: pistol ADS at 3, 10 and 30 m, plus the rifle and sniper at 10 m, all land within about 0.10 m of the dot. Full simulated Quest check: **161/161**.

## Red dot visible on Quest, 2026-11-13
The owner could not see the e410342 red dot on a real Quest 3: the sprite was 10 MOA (about 4 px) with a sub-pixel core, mipmapped and additive, so it faded out. Now the sprite is about 44 MOA with a solid red core and white-hot centre filling the inner 17 % of its radius (about 7-8 MOA, 3-4 px on a Quest 3), never smaller than ~3 px, no mipmaps, normal blending (shows on bright walls), still depth-tested (walls hide it). The old on-gun dot stays hidden in VR. Sim: exactly one dot renders while aiming (44 MOA sprite), shots still land on it at 3, 10 and 30 m; full suite 161/161.

## Mesh 1911 and Crimson Halls on the test map, 2026-11-13
- The game now loads GLB models (three r128 GLTFLoader, embedded in the page through `assets/models/manifest.json`). The Service Pistol is the PS2-style 1911 (`gun/pistol_1911_ps2.glb`): true size (22 cm) in VR, the voxel pistol's size on a flat screen, the right hand on the same grip spot as every voxel gun (0, -0.1365, 0.104), its own magazine drops on reload, the slide kicks and locks back when empty. `?voxelguns` brings back the voxel guns.
- The test map's start room (`?sandbox`) is drawn with Wrok's Crimson Halls kit: walls 3 modules high to the 11.5 m roof, inner corners, the room's pillar cells as kit pillars, a doorway arch on openings up to 3 cells wide, floor tiles, banners, and kit sconces whose flame sits on the torch light. All merged into one mesh (one draw call per eye), lit with the same baked torch light; the referee's cells stay the collision. `?voxelwalls` brings back the old walls. The full game's floors are unchanged.
- Sim (new `meshes` group): the 1911 mesh is in hand, fires, reloads with its magazine dropping, ADS shows exactly one red dot and the shot lands on it, the kit is present, draw calls in the room 126-141 per eye (the kit adds 1), and the flags bring the old look back. Full suite: 161 earlier checks pass, `meshes` 9/9 (one flaky dot-depth check reworked to measure distance from the shot line, then re-run alone).

## Full-game VR build, 2026-11-13 (walls in every level, 1911 base; phase 1)
- The real game, unchanged rules: original floors and progression, class pick, level-ups, shop, gear, stash, map, the rotating boss cast. Nothing added for convenience.
- Crimson Halls in every level (not only `?sandbox`): no arches (no wall drawn above an opening the game treats as open), trim squashed so the gun does not sink into it, a soft curve on the torch light so walls beside torches are warm, not blown-out orange. Merged per 24 m block, blocks beyond the fog skipped, hidden triangles cut at decode.
- The Service Pistol is Wrok's `pistol_1911_base.glb` (blued steel with a small env-map sheen, silver hammer, ivory grips; the PS2 1911 is its fallback). In VR only the gun shows: no hands, gloves or forearms. The red dot is unchanged from eb83e87 (one small sharp dot).
- Menus are unchanged from Papi's original in this phase (menu smoothing is phase 2).
- Draw calls / triangles per eye, worst of 4 directions at 10-12 spots (sim): floor 1 130 calls, 332k tris; biggest floors (7 and 10, 140 x 140 cells) 125-126 calls, 332-343k tris; a boss arena on floor 1 (Elder Dragon / Demon Lord at the boss door) 85-115 calls. The kit adds 1-2 draws per eye (one per visible 24 m block). Frame time can't be measured on a real Quest GPU here (software renderer); the sim CPU draw step stayed at 1.3-1.4 ms and game logic under 1 ms.
- The 1911 base's steel: metalness 1 / roughness 0.30 kept; its very dark blued atlas is lifted (tint 1.3) and the tiny PMREM hall gradient reflects at 1.7, so edges catch warm highlights instead of reading black. The ivory grips are toned down and cooled (they blew out to a skin-coloured block that read as a hand). No glove, forearm or controller placeholder is drawn in VR, also while aiming with both hands (new check in the `meshes` group).
- Sim: unit tests all pass (1,078 checks), full fake-Quest run 171/171. The mid-fight draw-call check is noisy (one frame: 63-259 per eye across runs; the base build 22e4dfe also swings 182-217).
- Harness fixes: the 1911 base is 1,000 triangles (check lowered to 600); the kit costs one draw per visible block (check: up to 8 per eye).

## Menu smoothing in VR, 2026-11-13 (phase 2)
- Every VR menu (start/class pick, pause, codex, level-up, shop, gear, stash, game over, and the hand-held map) now fades and grows in over about 150 ms, and fades out the same way when closed. Switching from one menu to another dips out and back in, so old and new content never show together.
- Hover: a gold frame glides to the card or button the laser points at (cards and real buttons only, never titles, text or labels) and fades in; a light haptic tick on every hover change, the usual stronger tick on a click. The hover frame floats above the page, so pointing never redraws the menu.
- Laser: lightly smoothed (one-euro style: steady when the hand is still, quick when it moves, big jumps taken at once, the trigger never waits for the smoothing).
- Scrolling: the stick scrolls with a soft speed curve and glides to a stop; dragging the list with the trigger held lets it coast gently after release.
- No hitch on open: the cards are drawn once when a menu's content changes, the menu texture has no mipmaps to rebuild. Open-frame cost in the sim 1-5 ms (normal frames 0-4 ms).
- Layout, content and what every button does are exactly the original game's. Menus stay world-locked, laser point-and-click, and Y backs out of every menu (level-up still needs a pick, as in the original).
- Sim (new `smooth` group, real game): 65/65 - every menu opens, closes, backs out with Y, scrolls, clicks still work, nothing stays stuck, the fades finish, open-frame time under 40 ms. Pickup, doors, controls, feel (red dot), meshes and menus re-checked: 94/94. New unit test tests/menusmooth.test.js (laser filter at 72/90/120 Hz, settle time, snap, source checks).
- Known: scrolling still redraws the menu texture each scrolling frame (as before); without mipmaps small text may shimmer slightly at a distance; the sim's frames are 17-50 ms, so its laser steadiness number is looser than on a 72-120 Hz headset.

## Still needs a real Quest
- Frame rate of the full-game kit on the Quest 3 GPU (about 690k triangles per frame, both eyes, at the worst spot in the biggest floors), and how the ivory grips read under orange torchlight (from above they can look skin-toned).
- The 1911 mesh and Crimson Halls on the Quest's own GPU: grip feel, size in the hand, brightness of the kit next to the old walls.
- How the 45 cm hand reach and the 13° pointing cone feel with real hands (the fake hands are perfectly still).
- Whether the floor labels are readable at arm's length on the Quest 3 lenses, and whether the gold beam/ring is too much in a fight.
- How the menu fades, hover frame, laser smoothing and scroll glide feel on the headset, and whether the hover tick is too light or too strong.
- Haptic strength on real Touch Plus controllers (the browser may ignore very short pulses).
- The over-the-shoulder swap spot (16 cm right, 12 cm behind the head) on a real body.
- Jumping: A lifts the view by about 2 m (the game's own jump); check it is comfortable in a headset.
- Recoil size and buzz strength per gun, the gun weight rates, and the aim-at-what-the-gun-points feel up close.
- Typing a room code on the VR letter keys.
- Walk 6.2 m/s and sprint 10 m/s are fast for VR (Meta suggests 4-6 m/s); left for the owner to decide.
- Draw calls (~210-260 per eye in the sim) and frame time on the Quest's own GPU.
- Co-op over real networks (the sim checks the game logic; real WebRTC links, NAT and lag need two headsets or a headset and a PC).
- Co-op between two real devices; on mobile data the link can fail until a relay (TURN) account is set up.
