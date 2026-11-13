# Crimson Plague in VR (Meta Quest 3): how other VR shooters do it, and what we copied

Grok's research notes, 2026-11-04 (sources: Half-Life: Alyx guides, the Half-Life 2: VR mod manual, Lambda1VR's Quest controls, Pavlov player tips; Contractors, Onward, H3VR, Into the Radius, Pistol Whip and Arizona Sunshine follow the same patterns).

## Conventions most VR shooters share
- **Move with the left stick, turn with the right stick.** Snap turn (30 or 45 degrees) is the comfort default; smooth turn is offered, usually with a speed setting. Movement can follow the head or the off hand (Pavlov, HL2VR let you pick).
- **Sprint = click the left stick** (HL2VR: stays on until the stick returns to centre). Pavlov's "auto sprint" adds running without the click.
- **Jump = right stick up, crouch = right stick down** (HL2VR) or B/Y (Lambda1VR). Physically ducking also works.
- **Triggers fire, grips grab.** The gun hand's grip holds the gun; the off hand's grip holds the foregrip.
- **Two-handed aim:** put the off hand at the gun's front and hold its grip; the barrel then runs from the back hand through the front hand, which is far steadier. Lambda1VR only turns it on when the hands are 15cm+ apart, so one-handed pistols are not spoiled.
- **Hand reload (Alyx, Pavlov, HL2VR "manual"):** press A on the gun hand to drop the magazine, reach to the hip / behind the shoulder and grip to take a new one, push it into the magwell, then rack the slide (pull it back) **only if the chamber was empty**. Haptic ticks confirm each step.
- **Easy reload option:** HL2VR's "quick reload" and Pavlov settings let players skip the hand steps; we keep that as `?easyreload` (A reloads).
- **Menus:** a laser from the controller, point and pull the trigger. Panels float in the world (not stuck to your face), big enough to read, so you can turn your head to look around them.
- **Comfort:** a vignette while moving is optional; no camera shake or head bob.

## Reloading in other VR shooters, per weapon type

| Weapon type | Pavlov / Onward / Contractors | Half-Life: Alyx | H3VR / Into the Radius | Arizona Sunshine |
|---|---|---|---|---|
| Pistol | A (or a button) drops the mag; grab one from the belt or chest; push it into the grip; rack the slide if the gun was empty | Flick the hand to drop, grab from over the shoulder, push in, rack | The same, but you must find, seat and rack by hand | Grab from the hip, touch the gun |
| SMG / rifle | Mag release, new mag from the chest pouch, seat, pull the charging handle only if empty | Mag into the well, pull the bolt | Fully manual: every step, including slide lock | Auto chamber |
| Sniper (bolt) | Mag or rounds, then work the bolt after each shot | n/a | Bolt up, back, forward, down | Simplified |
| Shotgun (pump) | Shells one at a time into the loading port, then pump | Shells one at a time (up to 6), then pump | Shells by hand, pump | One shell per touch |
| HMG / LMG | Box mag, open the top cover, seat the belt | n/a | Fully manual | Auto |

What they agree on: big, forgiving snap zones; the magazine visibly drops out; a haptic click on every step; the gun will not fire while empty (dry click). Casual games (Arizona Sunshine, Contractors casual mode) also offer a one-button or touch reload. We follow the casual path: everything is optional and forgiving.

## Crimson Plague reload, per weapon (animation on the gun)

The hand reload (grabbing magazines and shells, racking, two-handed support grip) was **removed** at the owner's request. Now the reload works like Arizona Sunshine's or a flat shooter's: you press X, or empty the gun, and the gun model plays the reload itself. The timing follows the game's own reload duration (`reloadK` from the referee), so the rules don't change. Each gun uses the anchors from its own model: magazine pivot `magPivot`, bolt or slide `boltRest`, and the loading port.

- **Pistol, SMG, rifle, HMG:** the gun tips toward you, the magazine slides out of the magwell, and a copy drops from the gun and tumbles to the floor. Then the new magazine slides up into the real magwell and seats with a click and a left-hand buzz. On an empty reload the slide or bolt racks, with a right-hand buzz.
- **Sniper:** same as above, and the bolt is worked after every magazine.
- **Shotgun (all four):** a red shell rides from the belt into the loading port four times, with a buzz per shell. Then the pump racks.
- An empty gun still reloads by itself, as in the flat game. Arms and hands stay hidden: you see only the gun.

## Menus: what each one is for, and how VR handles it

In VR every menu is a copy of the game's own panel, hung in front of you on a world-locked board. Point the right controller's laser at it and pull the trigger. **Only real buttons light up.** That means buttons, whole cards (a level-up or shop card is one button, so it lights up as one tile), gear and stash actions, blueprints, and save entries. Headings, descriptions and other words are never highlighted, and the trigger does nothing on them. When buttons sit inside other buttons, the smallest one under the laser wins.

| Menu | What it is for | Elements | In VR |
|---|---|---|---|
| Start | Pick a class and begin | Class buttons, Play, Codex, Co-op | Laser and trigger on a class, then Play |
| Codex | Reading about enemies and items | Text and a close button | Laser on the close button |
| Level-up | Choose upgrades on level-up | A class card row and a gift row (take one of each) | Each card is one tile; trigger picks it |
| Merchant (shop) | Spend gold on class training and supplies | Cards and your gold; the flat game leaves with Back | Laser picks cards; **Y leaves the merchant** (the hint is shown under the board) |
| Gear | Fit or remove weapon mods and see your gear | Fit / Remove / Close buttons (`data-act`) | Laser on the buttons; hold Y to open, Y to close |
| Stash chest | Store items between runs | Put in, Take, Rename, Save game, "Enter the hall" | Laser on the buttons. Renaming needs the Quest keyboard (untested) |
| Game over | See the run summary, keep stash items as blueprints, load or delete saves, rise again | Keep, blueprint and save buttons, and RISE AGAIN | Laser on any of them |
| Pause | Stop the game | Resume, Codex | Tap Y; Y again resumes |
| Map | Overview of the floor | Flat overlay (M / Back) | Double-tap Y: the map opens above your left hand, facing you. Double-tap again, or tap Y once, to close it |

## Research round 3 (Nov 2026): what real VR shooters and Meta's own guidelines do, and the decisions we took

### The owner's target (Nov 2026, authoritative)
A polished, mid-spectrum VR shooter: **Contractors / Pavlov handling with Half-Life: Alyx polish** (not Onward milsim, not H3VR hyper-sim). His list:
1. ADS / two hands: left trigger reliably brings the gun to the dominant eye with per-gun offsets (pistol high and close, rifles longer, shotgun different, sniper with zoom). The support hand (left grip on the fore-end) stabilises and steers the barrel: the primary hand owns position, the support hand influences rotation. Optional virtual-stock blend near the shoulder, as a toggle.
2. Per-gun grab points and hand poses so the model sits correctly in the hand: no floating, no arm models.
3. Sticks: pure move + turn. Jump off the stick (A). Sprint on stick click or full forward. Smooth and snap turn. No accidental jumps.
4. Menus: world-locked, laser point-and-click only, whole cards/buttons highlight only, scroll by stick or laser, a clear exit everywhere (Y backs out), clean, centred, readable, no lock-in.
5. Keep: X instant reload, the reload animation on the gun, the test map.
Because the left grip is the support hand again, the map moved off it: first to a wrist glance, then (owner, after playing: "the map keeps randomly popping up... causing problems in gun fights") to a double-tap of Y (row 16).

### Sources read
- Meta Horizon OS design docs: *Locomotion input maps* (developers.meta.com/horizon/design/locomotion-input-maps), *Locomotion user preferences*, *Controllers best practices*, *Ray casting specs* (developers.meta.com/vr/design/raycasting_specs), *Hands UI best practices* (sizing, scrolling, feedback), *Panels*, and the IWSDK *Locomotion Slide* doc.
- Pavlov: the UploadVR review (jump and crouch are physical, no buttons), the r/PSVR tips thread (auto sprint, virtual stock, "right controller at the chin, left hand straight out" ADS stance), and a Quest control list (B ejects the mag, right stick click opens the buy menu, left stick click sprints).
- H3VR wiki *Gun Stabilization*: virtual stock, two-handed grip on the fore-end, palm grip for pistols, hand smoothing.
- Contractors dev post *Inside the new weapon and damage model*: when aiming down sights, rifles pivot around the stock and shoulder contact, and pistols pivot around the wrist. Its Quest binds: jump on the right stick, crouch on left stick click, slide = sprint + crouch, weapons pulled from holsters, wrist menu.
- Onward forum (*DIY gunstock*): players want the point of aim to come from the rear (trigger) hand only. A front hand that changes the aim "jerks the point of aim off".
- Ghosts of Tabor and Into the Radius threads: jump on a stick press or flick, and players complain about it. Tabor moved jump to right stick up in 2025, and Into the Radius players ask for different bindings.
- Reddit drift threads: worn Quest sticks drift and fire stick-based actions unasked, and Meta's help page tells people to enlarge the deadzone.

### Decisions (with why)
| # | Decision | Why |
|---|---|---|
| 1 | **A = jump.** Nothing on any stick ever jumps. | Meta's input map puts jump on the right A button, standing or moving. Stick-flick jumps fire by accident when the thumb drifts diagonally, the stick is worn, or you push the right stick while turning. That is the owner's "random jumping when I move forward". |
| 2 | **Right stick click = swap guns** | A single, deliberate press, next to where the thumb already is. Pavlov puts its weapon or buy menu on the same click. |
| 3 | **B = slide** (crouch-slide), as before | B is the usual crouch or back button, and Contractors makes the slide out of the crouch. |
| 4 | **Tap Y = pause, hold Y (0.5 s) = Gear. In any menu, Y = back.** | Meta asks for one consistent menu button. The left ≡ button belongs to the browser in WebXR, so Y takes that role. There must always be one button that backs out, so no menu can trap you. |
| 5 | **Left stick: radial deadzone 0.15** with rescale. **Right stick turns only when sideways is clearly the main direction** (axis dominance 1.3:1); up/down on the right stick only scrolls menus, or a hard push down (0.85+) works the gate puzzle. | Stops crosstalk: pushing forward on one stick no longer turns, jumps or scrolls. The deadzone hides small drift (Meta's own advice). |
| 6 | **Left trigger = aim down sights, emulated.** The gun eases (smoothstep) from the hand onto your right eye's sight line, at a per-gun distance. Aim comes from the right controller, smoothed more while aiming; if the left grip also holds the gun, it steers too (row 15). The left glove is shown on the gun's fore-end. | The owner wants the trigger to bring the gun to the eye reliably. Physical ADS (Pavlov, H3VR) needs a stock and practice; an emulated snap with per-gun offsets is reliable from the first minute. |
| 7 | **Per-gun ADS data** (distance from the eye, support-hand spot, smoothing, zoom) | Pistol: arms out at 46 cm, support hand cupped under the grip (H3VR palm grip), lightest smoothing. SMG: 38 cm, hand on the fore-grip. Rifle: 34 cm, hand on the fore-end. Shotgun: 36 cm, hand on the pump. Sniper: 22 cm behind the scope, with a 4x picture in the lens and the most smoothing. HMG: 40 cm, sits 1.5 cm lower and swings slowest. The voxel guns are drawn bigger than real guns, so these distances were tuned on fake-XR screenshots until each sight takes up about as much of the view as a real optic at a real cheek weld. |
| 8 | **Sniper scope = magnified picture inside the lens** (a small 4x camera rendered only while aiming the sniper) | VR can't zoom the whole view without making you sick, so H3VR-style scopes show the zoom in the glass only. |
| 9 | **Menus are drawn by the game for VR, not photographed.** A clean layout built from the same menu data, with the same fonts and colours: centred title, even spacing, whole-tile buttons in a centred grid, and a fixed footer with the exit. | Photographing the flat page (html2canvas) carried over flat-screen spacing, clipped rows and stray boxes. Meta: 48 dp hit targets with 12 mm gaps, a clear hover state on the whole target, no hover-driven layout changes, and content filling the panel. |
| 10 | **Scrolling: right stick up/down, or hold the trigger and drag.** Content cut off at the edge plus ▲/▼ markers show there is more. No scroll bars. | Meta says users fail with ray-and-drag scroll bars and should get swipe or drag on the content instead, with visible clipping as the cue. The owner got locked out of a menu he could not scroll. |
| 11 | **Click on release, not on press**, and a drag cancels the click | Lets you drag to scroll without pressing whatever was under the laser. This is how Quest system panels behave. |
| 12 | **Laser:** white beam, gold when over a button, a cursor dot on the panel, and a buzz when you hover a new button | Meta's raycast spec uses distinct hover and select colours and a constant-size cursor. Haptics confirm the target. |
| 13 | **Panel placement:** 1.6 m away, centred at eye height (−10 cm), about 1.5 m × 0.95 m. It re-centres itself if you turn more than 70° away from it. | Meta says ray UI is comfortable from 0.46 to 3 m and panels should not make you turn your head to see the edges. Re-centring means a menu can never get lost behind you. |
| 15 | **Left grip near the gun = support hand.** Close the left grip anywhere along the gun ahead of the trigger hand (within 20 cm of that line; a buzz confirms). The right hand keeps the position; the barrel turns toward the left hand (pull: pistol 30% (a cupped hand), SMG 75%, rifle/shotgun 80%, sniper/HMG 85%), with extra smoothing. Release the grip to let go. | Pavlov and Contractors: two-hand rotation is what makes long guns steady. A whole-line grab zone because the voxel guns are long and a real reach is 30–45 cm, so you never fish for a spot. Position stays on the primary hand (the owner's rule), so the gun never pulls out of your hand. |
| 16 | **Map = double-tap Y** (toggle). A single tap of Y while the map is open closes it instead of pausing. Menus close it. It never opens by itself, not even when your hand passes your face. A single Y tap now pauses 0.3 s after release (the wait for a possible second tap); in menus Y still backs out at once. | The wrist glance (Contractors/Alyx style) fired by accident in gunfights, because a support hand on a long gun sits right in front of your face. Options weighed: **hold X** would delay or misfire the instant reload the owner wants kept, and X is a combat button. **Left stick click** is sprint. **Right stick click** is swap. Y is already the non-combat "system" button (pause, Gear, back), so a double tap there conflicts with nothing in a fight; the only cost is the 0.3 s later pause. Toggle instead of hold, so you can walk and turn while reading it. |
| 17 | **Per-gun grab point.** Every gun model already has a hand spot (its grip); the gun is placed so that spot sits exactly in the controller grip (the test measures a 0 mm gap on all six guns). The game's own right glove is drawn there and the left glove on the fore-end while supporting or aiming. No forearms. | The owner: "no floating, no arm models". Alyx and Contractors show hands only. |
| 18 | **Virtual stock (option, `?vstock`).** While two-handing, if your right hand is within 30 cm of your right shoulder the gun pivots on the shoulder instead of the hand. Off by default. | H3VR and Pavlov offer it as a setting; some players love it, some hate it, so it's opt-in. |
| 14 | Text inputs (stash rename, codex search, co-op name) are left out of the VR panel | The Quest keyboard over WebXR is unreliable, and an input you can't finish is a trap. Renaming stays a flat-screen feature. |

## What Crimson Plague does in VR
| Control | Action |
|---|---|
| Left stick | Move (toward where your head faces; `?aimmove` = toward the gun) |
| Left stick click / stick fully forward | Sprint |
| Left trigger | Aim down sights (per gun; the sniper shows a 4x picture in its scope) |
| Left grip near the gun | Support hand: steady and steer the barrel with both hands |
| Double-tap Y | Map on / off (a tap of Y also closes it). A small corner map is always in the HUD |
| X | Reload (animation on the gun) |
| Tap Y | Pause / resume (0.3 s after release). In any menu: back / close (at the merchant: leave) |
| Hold Y (0.5 s) | Gear menu |
| Right stick left/right | Smooth turn, 4.5 rad/s with a curve (`?turn=6`), or snap (`?snap` = 45 degrees, `?snap=30`) |
| Right stick up/down | Scrolls menus only. A hard push down works a gold gate / boss door puzzle |
| Right stick click | Swap guns |
| Right trigger | Fire. In menus: point and release on a button |
| Either grip | **Grab / use** (see "Grabbing and doors" below): reach a hand to a gun, armor or mod and squeeze to take that exact one; or point a hand at it (up to 7 m) and squeeze to pull it to you; at a gold gate, the boss door, a puzzle or the stash chest, squeeze to use it. A ring, a beam and a label show what the squeeze will do, with a light buzz when a new thing comes under your hand. The left grip on the gun's fore-end is still the support hand |
| Right hand over your right shoulder + grip | Swap to the gun on your back (same as right stick click) |
| A | Jump |
| B | Slide |

Why this layout: see rows 1–5 and 15–18 above. Jump is on a button so a drifting or diagonal stick can never jump; the left grip is the support hand like in Pavlov and Contractors; the map is on a double tap of Y, the non-combat system button, so it can never pop up in a fight. There is no D-pad anywhere.

**VR test map:** open the game with `?sandbox`, or press **VR TEST MAP** on the start card. You get a small 44x44 floor (the normal first floor is 80x80) with all the normal systems, only 2 weak monsters at a time, 400 HP and the gold gates open. One of each gun type lies at your feet (pump shotgun, rifle, SMG, bolt sniper, belt HMG, hand cannon), along with 500 gold, two mods and a helmet. Press the button again to go back to the normal game.

Reload: see "Crimson Plague reload, per weapon" above. An empty gun dry-clicks until you reload (by hand, or with X). Ammo still comes back on the game's own timer, so the rules and numbers do not change.

Other options: `?perf` (fps counter), `?xrscale=0.6..1` (render resolution, default 0.8), `?vignette`, `?gaze` (aim with the head).

## Grabbing and doors (research round 4, 2026-11-12)
The owner's playtest of e61a65f: "can't pick stuff up, can't open doors, the buttons don't feel like Pavlov, Contractors, Onward or Alyx". What those games actually do:

- **Half-Life: Alyx.** Grip = grab, hand-sized forgiving zones. The gravity gloves are the famous part: point at an item until it glows, lock on, flick the wrist, catch it. Valve's own notes: the item glows so "both the player and the game are on the same page"; each stage has its own sound; the flight is corrected toward your hand so you can look away. Doors open **both ways** (push or pull from either side) because "getting through a barrier matters more than real door mechanics". Sources: Road to VR "VR Design Unpacked", DigiPen interview with Kerry Davis, Engadget interview.
- **Pavlov.** Grip grabs weapons, items and doors; holding the grip keeps the gun (Quest default "Hold" grip mode; a "Toggle grip" setting exists). Items under your hand highlight blue before you grab. Holsters on the body; auto sprint. Sources: Pavlov wiki Game Settings, r/PavlovGame, Steam discussions.
- **Contractors.** Point your hand at an item, a white circle appears on it, press grip and it flies to your hand (distance grab is the normal way to loot the floor in Showdown). Players' advice: stand about a metre away, palm toward it; complaints are about the selection being unclear without a laser, so a visible marker matters. Mags can be moved to the trigger so the grip never takes the wrong thing. Sources: r/ContractorsVR, UploadVR beginner's guide.
- **Onward.** Milsim: grip grabs guns, trigger grabs small items (grenades, mags); a "grip/trigger" setting exists because players grabbed the wrong item. Doors: reach the handle and squeeze. Grip mode: proximity (snaps when near) or click. Sources: r/OnwardVR, UploadVR field guide, Ready VR One guide.
- **H3VR.** Everything by hand: grab the doorknob and turn it, from either side. Too fiddly for us (the owner said not H3VR hyper-sim).
- **Meta's guidelines** (Interaction SDK, "Grab" best practices): always show which object is targeted before the grab (hover state), confirm a grab with sound/haptics, use magnetism for distance grabs, and do not rely on distance grab alone; combine it with direct hand grab. Distance-grab selection uses a cone from the wrist and picks the most centred object; a short detection delay avoids false picks.

**What was wrong in our build (tested with the fake headset, see docs/vr-playtest-log.md):**
1. Only the right grip did anything, and it ignored where your hand was: it took whichever gun was nearest your feet within 2.6 m. Reaching for a gun with either hand, or pointing at one, did nothing (or took a different one).
2. A grab only counted on the exact moment the grip went down. Players hold the right grip all the time (it's how you hold a gun in Pavlov), so after the first squeeze nothing could ever be picked up.
3. No highlight, no buzz, no message: you could not tell what a squeeze would do, or why it did nothing.
4. On the test map, the guns at your feet **disappeared after 60 seconds** (the game's normal rule for floor loot), so by the time you had looked around there was nothing left to pick up. They were also all in one pile.
5. Doors: on the test map every gold gate was already open, and the only closed door was the boss door, which by the game's rules stays sealed until the boss is dead. Nothing told you that. The left grip did nothing at a gate.

**What we built (Alyx/Contractors-style, forgiving, with an always-works fallback):**
| Step | What happens | Numbers |
|---|---|---|
| Near grab | Reach either hand to an item (anywhere from the floor to just above it) and squeeze: you take that exact item | 45 cm from your hand |
| Distance grab | Point either hand at an item and squeeze: it flies to your hand (a gold line shows what you are pointing at) | up to 7 m, within about 13° (wider for close items); never through walls |
| Use | Standing at a gold gate, the boss door, the Scale/Wheels or the stash chest: squeeze either grip to pay / open / spin / open the stash | the game's own reach (5 m from a gate) |
| Fallback | Nothing pointed at: the right grip takes the nearest item within 2.6 m in front of you (the old rule), so a squeeze never does nothing | 2.6 m |
| Grip held like a gun | If the grip is already squeezed, resting the hand on an item for 0.2 s takes it. Only near items: gold is never spent and nothing is pulled from afar without a fresh squeeze | 0.2 s |
| Highlight | A ring on the floor, a soft beam and a label in the world ("R GRIP: take / Bolt Rifle (Rare)", "GRIP: Pay 80 gold", "LOCKED: Sealed: kill the boss to open it"). Red when it can't be done | |
| Haptics | Light tick when a new thing comes under your hand, firm pulse on a grab, strong buzz + message when it can't be done (not enough gold, sealed door) | 0.14 / 0.65 / 0.9 strength |
| Fights | While you hold the trigger the gun hand only grabs what it touches (no pulling from afar mid-fight); while aiming down sights the left hand never grabs | |
| Holster swap | Right hand over your right shoulder + grip: swap to the gun on your back (Pavlov/Onward-style back slot); right stick click still works | 26 cm zone |
| Grip hysteresis | A squeeze counts at 55% and re-arms when you ease off below 30%, so a loose grip never flickers | |

**Doors:** gates and the boss door open with the grip from wherever you stand at them (like Alyx's "doors open both ways": no handle to find, no push/pull to guess). The boss door in the real game still needs the boss dead (and its puzzle solved); the grip now tells you that instead of doing nothing. **On the VR test map only** (`?sandbox`): the gold gate is shut again (you get 1000 gold to pay it), the boss door opens when you grip it so you can walk to the safe room (stash chest and merchant) and on to floor 2, and floor loot never fades. The test map's guns lie in an arc in front of you like a weapon rack.

## Feel and co-op (research round 5, 2026-11-12 overnight)
The owner asked for shooting and moving that feel like a real VR shooter (Pavlov, Contractors, Onward, Alyx), and for co-op to work in VR. Here is what those games and Meta's guides do, and what we chose.

**Moving (Meta comfort guides: "Locomotion comfort and usability", "Locomotion best practices", the Horizon comfort checklist; Pavlov / Onward / Contractors all use smooth stick movement).**
- Meta: speeding up and slowing down the camera is what makes people sick. Fixed speeds that switch on and off at once are better than slow ramps. A vignette (darkened edges) helps sensitive players. Snap turn should be offered.
- Pavlov, Onward and Contractors all move at a steady speed the moment you push the stick, and stop the moment you let go.
- **Our choice:** in VR the run speeds up and stops almost at once: full speed in about 0.04 s, a dead stop in about 0.04 s. On the flat screen it is unchanged (0.15 s). Walk 6.2 m/s and sprint 10 m/s are the game's own speeds. They are fast next to Meta's suggested 4–6 m/s, but changing them would change the whole game's balance, so that is the owner's call. Smooth turn stays the default because shooter players expect it; `?snap` gives snap turn, `?vignette` gives the comfort vignette.

**Recoil (Pavlov, Contractors, Alyx).**
- Pavlov and Contractors kick the gun up and back on every shot, with a fixed pattern per gun. Contractors pivots a pistol's kick at the wrist and a long gun's at the shoulder when aiming. Both have settings to steady the gun (Pavlov's virtual stock and hand smoothing, Contractors' scope stabiliser).
- Players complain when recoil pulls the gun out of your hand so that your hand and the gun stop matching (Steam "Pavlov vs Contractors" thread).
- **Our choice (src/screen/xr_feel.js):**
  - Every shot kicks the gun model up and back, and a spring brings it home in 0.1–0.25 s. It is the look and the buzz only: the bullets still go where the controller points, so the gun never leaves your hand and there are no surprise misses.
  - Heavier guns kick harder and settle slower:

| Gun | Kick up | Kick back | Settles in about | Buzz |
|---|---|---|---|---|
| Pistol | 0.10 rad | 2.2 cm | 0.17 s | 0.40 / 28 ms |
| SMG | 0.04 | 1.2 cm | 0.15 s | 0.26 / 16 ms |
| Rifle | 0.06 | 1.8 cm | 0.17 s | 0.45 / 26 ms |
| Shotgun | 0.20 | 5 cm | 0.25 s | 0.95 / 70 ms |
| Sniper | 0.17 | 4.5 cm | 0.28 s | 0.85 / 60 ms |
| HMG | 0.045 | 1.6 cm | 0.16 s | 0.50 / 22 ms |

  - **Two hands:** with the left hand on the fore-end the kick is halved and the left hand feels every shot too (60% strength). That is the Pavlov/Onward reason to hold a rifle with both hands.
  - **Aiming down sights:** trims the kick by a further 20%.
  - Full auto can never flip the gun past 0.32 rad.

**Hits.** Contractors and Pavlov rely on hit sounds; flat shooters use a crosshair hit marker, and VR has no crosshair. **Our choice:** a small white X flashes on the spot you hit (gold for a crit, a bigger red one for a kill). It always faces you and is sized for its distance. It comes with the game's hit sound, the damage number and a buzz in the gun hand.

**Aim down sights and the scope (already in the build, checked tonight).** The left trigger brings each gun's own sight to the right eye at that gun's eye relief. The sniper shows a zoomed picture inside the scope only (the whole view never zooms; that makes people sick). Two hands steer the barrel like Contractors and Pavlov, and `?vstock` adds a virtual stock.

**Not done, on purpose:** gun sway or lag for heavy guns. In H3VR and Pavlov a heavy gun held one-handed turns slowly. Here that would put the gun model and the laser out of line with your hand, which is the exact complaint players have about Pavlov's recoil. Worth trying on a real Quest later as an option.

**Frame budget.** A Quest 3 has 11–14 ms per frame (72–90 Hz).
- In the fake headset, the game's own work (rules, screen, VR) takes about 1 ms per frame in a fight with 4 monsters and the trigger held. Drawing is about 230–260 draw calls per eye.
- The per-shot effects (recoil, hit marker) reuse the same few objects and make no new ones per frame.
- The game still builds a fresh state snapshot every frame (that is how the rules talk to the screen). That is fine at 1 ms, but it is the first thing to look at if a real Quest stutters.

**Co-op in VR.** The flat lobby needed a keyboard (room code, name). **Our choice:**
- PLAY WITH FRIENDS and HOST A GAME are now on the VR start menu.
- There are on-screen letter keys for the room code (only shown in VR), then JOIN, so a player in the headset can host or join with the laser alone.
- The name box stays flat-only; the saved name or a random one is used.
- The playtest runs two players in one headless Chrome with a stand-in for PeerJS (tools/xr_fake_peer.js) and checks both ways round (host in VR with a flat friend, and a friend in VR with a flat host): join, start, movement both ways, the same monsters, shots from either side, gates, pause, errors and traffic.
