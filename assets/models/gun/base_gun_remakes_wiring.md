# Base-gun remakes, batch 1 (pistols): wiring notes

Art only. Nothing here changes `src/` or `manifest.json`; these are the entries to paste in
when the owner approves. Each model REPLACES its slot (one gun per slot):

| slot id          | file                              | root node         | tris  |
|------------------|-----------------------------------|-------------------|-------|
| `pistol_cannon`  | `gun/pistol_cannon_base.glb`      | `pistol_cannon`   | 2,276 |
| `pistol_machine` | `gun/pistol_machine_base.glb`     | `pistol_machine`  | 1,332 |
| `pistol_duelist` | `gun/pistol_duelist_base.glb`     | `pistol_duelist`  | 1,948 |

Format = the approved 1911: Y-up, muzzle toward -Z, metres, origin at the palm; one 256 px
nearest-filtered albedo; two embedded materials (metal = steel AND brass at metallic 1 /
roughness 0.30 so the locked 1911 sheen applies; one non-metal for bone or polymer).
Empties under the root: `muzzle`, `mag_well`, `rear_sight`, `front_sight`.

## Sight line (xr_ads.js on grok/full-playtest-tonight @c3d56a6)

`glb_guns.js` takes `rear_sight` as the ADS point and `normalize(front_sight - rear_sight)` as the sight
direction **only when the entry has `"redDot": false`**. (With a `redDot` object it uses the red-dot
housing instead, as the 1911 entry does.) So every entry below sets `"redDot": false`.
`XrAds.localAdsPose` then puts `rear_sight` at (0,0,-relief) on the eye axis (pistol relief 0.30 m) and
rotates the sight line onto -Z. In all three guns rear and front share X = 0 and Y, so the sight direction is
exactly (0,0,-1), the pose rotation is the identity, and the bore sits a fixed distance directly below the
sight line (the 25 m zero in `XrAds.fire` then converges the ray by atan(offset / 25 m)).

| gun    | rear_sight (x,y,z)      | front_sight (x,y,z)     | muzzle (x,y,z)          | sight radius | bore below line |
|--------|-------------------------|-------------------------|-------------------------|--------------|-----------------|
| cannon | 0, 0.0885, -0.0070      | 0, 0.0885, -0.2170      | 0, 0.0655, -0.2220      | 0.210 m      | 23.0 mm         |
| machine| 0, 0.0735, +0.0285      | 0, 0.0735, -0.1330      | 0, 0.0535, -0.1900      | 0.1615 m     | 20.0 mm         |
| duelist| 0, 0.0775, -0.0045      | 0, 0.0775, -0.2600      | 0, 0.0610, -0.2640      | 0.2555 m     | 16.5 mm         |

Each empty sits on the TOP of its sight (rear = top of the notch posts, front = top of the blade/bead),
same convention as the 1911's `rear_sight` / `front_sight`. `/workspace/basegun-scripts/verify_ads.js`
re-runs the check against the real `xr_ads.js` from the exported GLB.

## manifest.json `guns` entries (not applied)

Following `pistol_service -> gun/pistol_1911_base.glb`. `grip` is the hand spot on the grip axis
(same spot as the 1911's, re-derived for each grip tilt); `fore` is a suggested support-hand spot.
Revolvers have no slide, so no `slide`/`slideTravel`. The cylinder is the `magazine` node.

```json
"pistol_cannon": {
  "file": "gun/pistol_cannon_base.glb",
  "root": "pistol_cannon",
  "grip": [0, -0.0365, 0.0105],
  "fore": [0, -0.075, 0.010],
  "magazine": "magazine",
  "muzzle": "muzzle",
  "redDot": false,
  "flatScale": 1.0,
  "coolNonMetal": true,
  "kind": "pistol"
},
"pistol_machine": {
  "file": "gun/pistol_machine_base.glb",
  "root": "pistol_machine",
  "grip": [0, -0.036, 0.0125],
  "fore": [0, -0.040, -0.070],
  "slide": "slide",
  "slideTravel": 0.024,
  "magazine": "magazine",
  "muzzle": "muzzle",
  "redDot": false,
  "flatScale": 1.1,
  "coolNonMetal": true,
  "kind": "pistol"
},
"pistol_duelist": {
  "file": "gun/pistol_duelist_base.glb",
  "root": "pistol_duelist",
  "grip": [0, -0.0357, 0.0130],
  "fore": [0, -0.070, 0.010],
  "magazine": "magazine",
  "muzzle": "muzzle",
  "redDot": false,
  "flatScale": 1.0,
  "coolNonMetal": true,
  "kind": "pistol"
}
```

## Things to know when wiring

* **Revolver reload:** `glb_guns.js` detaches the `magazine` node and drops it on reload. On the cannon and
  duelist that node is the cylinder, so it falls out and leaves the open cylinder window. If that looks wrong in
  playtest, the cheap fix is a tiny `magazine` stand-in (e.g. a speedloader) with the cylinder left in the frame;
  say so and I will split it.
* `hammer` is its own mesh on both revolvers, origin at its pivot, so a cock/fall animation can be added later.
  It is not animated by the current `glb_guns.js` (only `slide` and `magazine` move). 4 draw calls per revolver,
  4 for the machine pistol (slide, frame metal + polymer primitive, magazine).
* Slide on the machine pistol is the only recoiling part; its barrel and compensator stay in `frame`.
* Atlas colours: 20 / 25 / 20 (the 1911 is 16): brass, bone and engraving need a few more.

---

# Batch 2 (SMGs): wiring notes

Same rules and format as batch 1. Art only; nothing here changes `src/` or `manifest.json`. Each model
REPLACES its slot (one gun per slot):

| slot id       | file                          | root node     | tris  | meshes                                              |
|---------------|-------------------------------|---------------|-------|-----------------------------------------------------|
| `smg_bullpup` | `gun/smg_bullpup_base.glb`    | `smg_bullpup` | 1,708 | `body`, `cocking_handle`, `magazine`                |
| `smg_drum`    | `gun/smg_drum_base.glb`       | `smg_drum`    | 1,816 | `receiver`, `furniture`, `cocking_handle`, `magazine` |

Empties under the root: `muzzle`, `mag_well`, `rear_sight`, `front_sight`. One 256 px albedo each; two embedded
materials (metal = steel AND brass at metallic 1 / roughness 0.30 so the locked 1911 sheen applies; one non-metal:
stippled polymer + bone on the bullpup, walnut + bone on the drum gun).

## Sight line (xr_ads.js on grok/full-playtest-tonight @c3d56a6, `kind: "smg"`, relief 0.18 m)

Both entries need `"redDot": false` (rear/front empties drive ADS). Rear and front share X = 0 and Y, so the sight
direction is exactly (0,0,-1) (0.0000 deg off), the ADS pose rotation is the identity, and the bore sits a fixed
distance below the sight line. `verify_ads.js <glb> smg`: rear on the eye axis, rear z == -relief, front ahead of rear,
scale-invariant at gs = 1 and 2.2, `fire()` ray starts on the sight line (0.0000 deg).

| gun     | rear_sight (x,y,z)     | front_sight (x,y,z)    | muzzle (x,y,z)         | sight radius | bore below line | 25 m zero convergence |
|---------|------------------------|------------------------|------------------------|--------------|-----------------|-----------------------|
| bullpup | 0, 0.1235, +0.0560     | 0, 0.1235, -0.2105     | 0, 0.0500, -0.2920     | 0.2665 m     | 73.5 mm         | 0.171 deg             |
| drum    | 0, 0.1060, -0.0288     | 0, 0.1060, -0.3800     | 0, 0.0600, -0.4000     | 0.3512 m     | 46.0 mm         | 0.107 deg             |

Empties sit on the TOP of each sight (rear = top of the notch posts, front = top of the blade bead), same convention
as the 1911 and batch 1.

## manifest.json `guns` entries (not applied)

Following `smg_tactical -> gun/smg_mp5_base.glb`: `grip` [0,0,0] (the pistol grip is built around the origin),
`slide` = the moving part (the brass cocking handle), `magazine` = the node dropped on reload.

```json
"smg_bullpup": {
  "file": "gun/smg_bullpup_base.glb",
  "root": "smg_bullpup",
  "grip": [0, 0, 0],
  "fore": [0, -0.028, -0.100],
  "slide": "cocking_handle",
  "slideTravel": 0.05,
  "magazine": "magazine",
  "muzzle": "muzzle",
  "sight": "front_sight",
  "redDot": false,
  "kind": "smg",
  "flatScale": 1
},
"smg_drum": {
  "file": "gun/smg_drum_base.glb",
  "root": "smg_drum",
  "grip": [0, 0, 0],
  "fore": [0, -0.045, -0.215],
  "slide": "cocking_handle",
  "slideTravel": 0.06,
  "magazine": "magazine",
  "muzzle": "muzzle",
  "sight": "front_sight",
  "redDot": false,
  "kind": "smg",
  "flatScale": 1
}
```

## Things to know when wiring batch 2

* **Bullpup magazine is top-loaded** (P90 style): `mag_well` is at (0, 0.0785, -0.075) on top of the body, so a
  reload that drops the `magazine` node leaves an empty flat tray with the engraved rails; the sights stand clear of
  it (the sight line is 24 mm above the magazine top). It is 0.231 m long, so it is the biggest `magazine` node of
  any gun so far.
* **Drum magazine** is a 96 mm round drum on an X axis; `mag_well` is the top of its neck at the receiver floor.
  Dropping it leaves the open mag-well slot under the receiver. The brass ring and both hub faces ride with it.
* `cocking_handle` is a small brass part in both guns (bullpup on the left side, drum on the right side); only it moves
  with `slide` / `slideTravel`.
* Draw calls: bullpup 3 meshes (5 primitives), drum 4 meshes (7 primitives).
* Atlas colours: 24 (bullpup) / 25 (drum).

---

# Batch 3 (shotguns): wiring notes

Same rules and format as batches 1 and 2 (art only; nothing here changes `src/` or `manifest.json`). Each model
REPLACES its slot. Empties under every root: `muzzle`, `mag_well`, `rear_sight`, `front_sight`. One 256 px albedo each;
two embedded materials (metal = steel AND brass at metallic 1 / roughness 0.30, locked 1911 sheen; one non-metal for
walnut + bone). Sight line verified with `verify_ads.js <glb> shotgun` against xr_ads.js @c3d56a6 (`kind: "shotgun"`,
relief 0.16 m), all entries need `"redDot": false`. These are bead-only guns: the rear reference is a pair of low brass-tipped
posts on the vent rib / top strap (rear and front share X = 0 and Y, so the sight line is exactly (0,0,-1)).
Sight-view previews are rendered with the real shotgun relief (0.16 m).

## shotgun_pump (Remington 870 / Ithaca build)

File `gun/shotgun_pump_base.glb`, root `shotgun_pump`, 1,620 tris. Meshes: `receiver` (receiver, plates, barrel, vent rib,
mag tube, guard, sights), `furniture` (walnut stock, bone cross plaques, brass butt plate), `pump` (walnut forend, the sliding
part), `magazine` (a shell at the loading gate, bone hull + brass head).

| rear_sight (x,y,z) | front_sight (x,y,z) | muzzle (x,y,z) | mag_well (x,y,z) | sight radius | bore below line | 25 m zero convergence |
|--------------------|---------------------|----------------|------------------|--------------|-----------------|-----------------------|
| 0, 0.0650, -0.1890 | 0, 0.0650, -0.5385  | 0, 0.0470, -0.5600 | 0, -0.0035, -0.1275 | 0.3495 m | 18.0 mm | 0.042 deg |

```json
"shotgun_pump": {
  "file": "gun/shotgun_pump_base.glb",
  "root": "shotgun_pump",
  "grip": [0, 0, 0],
  "fore": [0, -0.010, -0.287],
  "slide": "pump",
  "slideTravel": 0.08,
  "magazine": "magazine",
  "muzzle": "muzzle",
  "sight": "front_sight",
  "redDot": false,
  "kind": "shotgun",
  "flatScale": 1
}
```

* The pump forend is the only moving part (`slide` / `slideTravel`, it rides back along +Z). The `magazine` node is just the shell at the
  loading gate; dropping it leaves the brass-edged gate plate.
* Hand spot `grip` is the stock wrist (z = 0, just behind the trigger guard); the receiver sits directly in front of it.

## shotgun_double (side-by-side coach / English sidelock build)

File `gun/shotgun_double_base.glb`, root `shotgun_double`, 1,932 tris. Meshes: `receiver` (action, engraved sideplates, hinge pin,
short brass top lever, guard, two triggers), `hammers` (two exposed hammers), `barrels` (two blued barrels, vent rib, brass bands,
sights; its own mesh so a break animation can be added later), `furniture` (walnut stock + pistol grip + splinter forend, bone cross
plaques, brass plates and cuff straps), `magazine` (two spare shells in the left stock cuff).

| rear_sight (x,y,z) | front_sight (x,y,z) | muzzle (x,y,z) | mag_well (x,y,z) | sight radius | bore below line | 25 m zero convergence |
|--------------------|---------------------|----------------|------------------|--------------|-----------------|-----------------------|
| 0, 0.0690, -0.1350 | 0, 0.0690, -0.4975  | 0, 0.0520, -0.5200 | -0.0275, 0.0292, +0.1760 | 0.3625 m | 17.0 mm | 0.040 deg |

```json
"shotgun_double": {
  "file": "gun/shotgun_double_base.glb",
  "root": "shotgun_double",
  "grip": [0, 0, 0],
  "fore": [0, 0.005, -0.200],
  "magazine": "magazine",
  "muzzle": "muzzle",
  "sight": "front_sight",
  "redDot": false,
  "kind": "shotgun",
  "flatScale": 1
}
```

* No `slide`: break-action, nothing recoils. `muzzle` sits between the two barrels (x = 0), so a pellet spread fires from the centre.
* `magazine` is the pair of spare shells carried in the brass-strapped cuff on the LEFT of the buttstock; dropping it on reload leaves
  the empty cuff straps. `mag_well` is the middle of that pair.
* The brass top lever sits on the top strap in front of the eye in ADS (6 mm under the sight line, see the `_sights` render).

## shotgun_combat (Saiga-12 / AA-12 style box-mag semi-auto)

File `gun/shotgun_combat_base.glb`, root `shotgun_combat`, 1,448 tris. Meshes: `receiver` (receiver + raised top cover, engraved plates, barrel,
gas tube + front-sight block, finned brake, guard, sights), `furniture` (walnut stock, pistol grip, upper + lower handguards, bone cross plaques,
brass plates), `cocking_handle` (brass knob on the right, the moving part), `magazine` (curved 8-round box, brass base plate and band).

| rear_sight (x,y,z) | front_sight (x,y,z) | muzzle (x,y,z) | mag_well (x,y,z) | sight radius | bore below line | 25 m zero convergence |
|--------------------|---------------------|----------------|------------------|--------------|-----------------|-----------------------|
| 0, 0.1020, -0.0300 | 0, 0.1020, -0.4500  | 0, 0.0620, -0.5800 | 0, 0.0300, -0.1100 | 0.4200 m | 40.0 mm | 0.094 deg |

```json
"shotgun_combat": {
  "file": "gun/shotgun_combat_base.glb",
  "root": "shotgun_combat",
  "grip": [0, 0, 0],
  "fore": [0, 0.005, -0.300],
  "slide": "cocking_handle",
  "slideTravel": 0.05,
  "magazine": "magazine",
  "muzzle": "muzzle",
  "sight": "front_sight",
  "redDot": false,
  "kind": "shotgun",
  "flatScale": 1
}
```

* The sights are AK-style (tall rear ear posts on the top cover, front ears on the sight block), so the sight line is 40 mm above the bore.
  The upper handguard and brass bands stay 6 mm under the line.
* `magazine` is the curved box under the well collar: dropping it leaves the open collar. It is 0.129 m tall, hanging in front of the trigger guard.

## shotgun_blunderbuss (flintlock coaching blunderbuss)

File `gun/shotgun_blunderbuss_base.glb`, root `shotgun_blunderbuss`, 1,160 tris. Meshes: `receiver` (octagonal blued barrel, fluted brass bell, engraved lock
plate, brass pan, frizzen, brass guard + trigger, sights), `furniture` (walnut stock, bone cross plaque, brass tang / wrist cap / butt plate / fore bands,
bone fore tip), `hammer` (the flint cock, origin at its pivot, 4 draw-call mesh like the revolvers' hammers), `magazine` (brass powder flask on the left of
the stock).

| rear_sight (x,y,z) | front_sight (x,y,z) | muzzle (x,y,z) | mag_well (x,y,z) | sight radius | bore below line | 25 m zero convergence |
|--------------------|---------------------|----------------|------------------|--------------|-----------------|-----------------------|
| 0, 0.1060, -0.0650 | 0, 0.1060, -0.3920  | 0, 0.0700, -0.4040 | -0.0235, -0.0020, +0.1700 | 0.3270 m | 36.0 mm | 0.084 deg |

```json
"shotgun_blunderbuss": {
  "file": "gun/shotgun_blunderbuss_base.glb",
  "root": "shotgun_blunderbuss",
  "grip": [0, 0, 0],
  "fore": [0, 0.005, -0.150],
  "magazine": "magazine",
  "muzzle": "muzzle",
  "sight": "front_sight",
  "redDot": false,
  "kind": "shotgun",
  "flatScale": 1
}
```

* Rear reference = two thin brass-tipped spires on the breech; front reference = a bead on the rim of the bell (a blunderbuss has no real sights, so the
  line is 36 mm above the bore to clear the bell). `muzzle` is the centre of the bell mouth.
* `hammer` is its own mesh (pivot at its origin) for a later cock / fall animation; `glb_guns.js` does not animate it. No `slide`.
* `magazine` is the brass powder flask on the LEFT of the buttstock; dropping it on reload leaves a clean stock side.

---

# Batch 2 revision: `smg_bullpup` v2 (sleek P90 redo, supersedes the batch 2 bullpup numbers above)

Papi found the first bullpup chunky, so `gun/smg_bullpup_base.glb` was rebuilt: slim octagonal-section polymer shell (31-32 mm wide,
tapering into the muzzle end and sweeping into a thumbhole butt), thin top-loaded magazine (20 mm) under a slotted low-profile rail,
realistic-size grip (25 mm thick) and slender guard / trigger, shrouded 14 mm barrel with a small hider. Gothic detail kept fine: two thin
engraved inlay plates per side, thin brass trim, tiny bone cross inlay on the butt. Same file name, root `smg_bullpup`, same empties and the same
three meshes (`body`, `cocking_handle`, `magazine`), 1,400 tris (was 1,708). The old v1 builder is saved outside the repo only.

| rear_sight (x,y,z) | front_sight (x,y,z) | muzzle (x,y,z) | mag_well (x,y,z) | sight radius | bore below line | 25 m zero convergence |
|--------------------|---------------------|----------------|------------------|--------------|-----------------|-----------------------|
| 0, 0.0970, +0.0500 | 0, 0.0970, -0.2050  | 0, 0.0500, -0.2920 | 0, 0.0620, -0.0650 | 0.2550 m | 47.0 mm (was 73.5) | 0.109 deg |

`verify_ads.js smg`: sight dir exactly (0,0,-1), rear on the eye axis at z = -0.18, front ahead, scale-invariant at gs 1 / 2.2, `fire()` ray starts on
the sight line. The manifest entry for `smg_bullpup` above stays valid, with two changes: `"fore": [0, -0.028, -0.100]` can drop to `[0, 0.030, -0.100]`
(the finger-grip block is gone, the hand now holds the shell front) and `slideTravel` 0.05 is fine for the smaller left-side handle.
* The top-loaded magazine is now 0.2075 m long and 20 mm thick (`mag_well` moved to y = 0.062); dropping it leaves the slotted rail bridge on the shell.

## Batch 3 revision: `shotgun_pump` v2 (sleek pass)

Same file name, root, meshes, empties and sight numbers as above. Slimmer receiver (30 mm wide), 28 mm stock with a thinner wrist and butt, 30 mm forend with
thin brass ferrules, thinner barrel / tube, small bone cross inlays, thin brass straps, finer engraving. 1,564 tris (was 1,620). `verify_ads.js shotgun` unchanged:
rear (0, 0.0650, -0.1890), front (0, 0.0650, -0.5385), bore 18 mm below the line, 0.042 deg. Rib top is now 0.0610 (was 0.0620); sight tops did not move.

## Batch 2 revision: `smg_bullpup` v3 (compact P90-style SMG, supersedes the v2 numbers above)

Papi: v2 still read as a long AR rifle. `gun/smg_bullpup_base.glb` is now a COMPACT SMG: 0.455 m overall (v2 was ~0.55 m), rounded P90-style polymer body with an
integrated thumbhole butt, grip bar and trigger hole, stubby 12 mm barrel with a small hider barely past the shell (muzzle at z = -0.168), thin top-loaded mag
(20 mm) between low shoulder rails, engraved steel sight housing, two thin engraved butt plates, tiny bone cross inlay, brass pinstripes and trim. Same file,
root `smg_bullpup`, same empties, meshes `body`, `cocking_handle`, `magazine`, 2,488 tris (bevelled edges).

| rear_sight (x,y,z) | front_sight (x,y,z) | muzzle (x,y,z) | mag_well (x,y,z) | sight radius | bore below line | 25 m zero convergence |
|--------------------|---------------------|----------------|------------------|--------------|-----------------|-----------------------|
| 0, 0.0960, +0.0500 | 0, 0.0960, -0.1120  | 0, 0.0470, -0.1680 | 0, 0.0580, +0.0400 | 0.1620 m | 49 mm | 0.113 deg |

`verify_ads.js smg`: sight dir exactly (0,0,-1), rear on the eye axis at z = -0.18, front ahead, scale-invariant at gs 1 / 2.2, `fire()` ray starts on the sight
line. The manifest entry's `fore` should be about `[0, 0.0, -0.040]` (hand on the grip bar) and the front sight is short (0.162 m radius), which is normal for a P90.

# HD albedo + linear filtering (applies to every gun built from now on, starting with `smg_bullpup` v3)

Papi's quality bar: crisp, shiny, no pixelated textures. What changed in the art pipeline (assets only, nothing in `src/` touched):

* Albedo is now **1024 x 1024** (was 256 x 256). Painters still work on a 256 grid, then `gun_gothic_common.hd_upscale` does a smooth-label x4 upscale: every palette
  colour becomes a soft mask, the result is blended with a steep softmax, so contours are clean anti-aliased curves with no stair-steps and thin engraving lines stay crisp,
  plus a faint (2 %) fine grain. File size is ~0.4-0.5 MB per gun (GLB ~0.6 MB), so it stays at 1024 rather than being cut to 512.
* The GLB sampler is now **LINEAR** (glTF magFilter 9729 / minFilter 9987 mip-linear), not NEAREST. If the loader overrides filters on gun textures (the old pixel-art
  convention `tex.magFilter = tex.minFilter = THREE.NearestFilter`), remove that override for the guns built from now on, and keep `tex.generateMipmaps = true`, `tex.anisotropy = 4..8`,
  `tex.colorSpace = THREE.SRGBColorSpace`, `flipY = false` (glTF default). Old pistols / SMG GLBs that were not rebuilt are still 256 px NEAREST; set the filter per gun if the loader
  is global (or rebuild them with the same scripts, which is now a one-liner each).
* Key hard edges (> 40 deg, longer than 4 mm) get a 0.7 mm bevel so the locked 1911 steel sheen (metallic 1, roughness 0.30) catches them; this is what adds triangles (still < 3,000).
* Polymer is now a matte material (roughness 0.68, specular 0.14) with a fine stipple instead of a blotchy hatch; steel, brass and bone are unchanged.
* `export_lowpoly.py --max-tex 1024` is needed (the default cap for guns is 256 px); `--max-tris 3000 --allow-multi-material` as before.

## Batch 2 revision: `smg_bullpup` v4 (traced P90 profile, real volume; supersedes v3 body numbers)

Papi: "closer to the P90 shape, less bulky". The shell is now one continuous polymer body traced from the P90 side photo (thumbhole loop, forward trigger-hand hole, sloped nose over the short barrel,
clear top-mag channel between steel-capped rails), extruded 35 mm and rounded with a 5.5 mm two-step bevel (3.2 mm on the hole rims) so there are no flat slab sides. Trigger is a steel blade hung from a brass pivot pin inside the hole;
the engraved steel plaque and the bone-cross badge sit in brass bezels flush with the shell. 2,852 tris. Sight empties unchanged: rear (0, 0.0960, 0.0500), front (0, 0.0960, -0.1120), muzzle (0, 0.047, -0.168),
mag_well (0, 0.058, 0.040); `verify_ads.js smg` passes (dir (0,0,-1), rear on the eye axis at z = -0.18, bore 49 mm below the line, 0.113 deg). Polymer material: metallic 0, roughness 0.42, specular 0.14 (satin);
metal: the locked 1911 material. The mag is now 0.226 m (z -0.0825..0.1435) and sits in the channel.

## Batch 2 revision: `smg_drum` v2 (Thompson M1928, same bar as the bullpup v4)

Rebuilt to the locked brief: 1024 px smooth albedo with LINEAR filtering, bevelled steel edges, and real rounded walnut furniture (slim curved stock, raked pistol grip, short forend, vertical foregrip are
all `K.shell` bodies with rounded rims instead of flat extrusions), satin walnut (roughness 0.40, specular 0.35), brass-rimmed bone cross badges flush with the stock and forend, finer engraved receiver plates,
steel trigger on a brass pivot. Same file, root `smg_drum`, meshes `receiver`, `furniture`, `cocking_handle`, `magazine`, same empties and sight line (rear (0, 0.1060, -0.0288), front (0, 0.1060, -0.3800), muzzle z -0.400,
mag_well (0, 0.035, -0.105)). 2,992 tris. `verify_ads.js smg` passes. The notes above (smg_drum entry, `fore`, `slideTravel`) stay valid.

## Shotguns v3 (HD bar + traced profiles) - pump, double, combat, blunderbuss

All four rebuilt to /workspace/gun_brief/LOCKED_BRIEF.md: 1024x1024 smooth albedo (glTF sampler LINEAR; no src/ change, loader must not force
NEAREST), bevelled steel on the locked 1911 sheen, satin walnut (roughness 0.40, spec 0.35) on `K.shell` rounded furniture with one continuous
side UV projection (`K.shell(..., gmap=True)`, grain runs along the gun), brass-rimmed bone cross badges inset in the furniture, thin brass straps.
Furniture side profiles are traced from the Wikimedia refs in /workspace/gun_brief/refs/ (silhouette mask -> top/bottom profile, scaled to the
model's stock length). Format unchanged: 4 empties (muzzle, mag_well, rear_sight, front_sight), redDot:false, verify_ads pass on every gun.

| slot | node (slot id) | traced from | tris |
|---|---|---|---|
| shotgun_pump | shotgun_pump_base.glb | Remington 870 Wingmaster side (stock + deeper forend with finger ridges) | 2,392 |
| shotgun_double | shotgun_double_base.glb | side-by-side coach gun side (one-piece stock with drop + semi-pistol wrist, grip part removed) | 2,760 |
| shotgun_combat | shotgun_combat_base.glb | Benelli M4 / L128A1 side (tall butt pad, slim dropped neck, pistol grip, deeper lower handguard) | 2,404 |
| shotgun_blunderbuss | shotgun_blunderbuss_base.glb | Met flintlock blunderbuss side (raked butt, wedge stock, full-length slim forestock, realistic gentle bell, slimmer barrel, 14-sided) | 2,060 |

### smg_bullpup polish3 (glossy near-black polymer, big butt radius)
Butt top-rear and bottom-rear corners are now 3.5 cm radius arcs (5 segments each), brass parting-line seam band follows the arc, polymer is near-black
(palette ~RGB 12-17) with roughness 0.30, specular 0.30, clearcoat weight 0.55 / roughness 0.10. The side-face crown is done with custom (domed) shading
normals on the cap faces (geometry stays flat; glTF exports the normals) - the loader must not recompute normals. 2,980 tris, verify_ads pass.

### Shotguns v4 (review fix pass)
- shotgun_pump: loading-gate shell now seated on a brass gate plate under the receiver (magazine node = plate + shell); trigger guard runs from the receiver floor into the stock tang.
- shotgun_double: true twin barrels (14-sided, 5 mm gap) with a brass rib between them, short coach-gun length (muzzle z -0.470, front sight z -0.4475; ADS re-verified), twin muzzle faces + brass rings, guard bow attached to the action and the stock tang enclosing the twin triggers.
- shotgun_combat: re-themed to Benelli M4: slim rounded flat-top receiver with rail, octagonal ghost-ring rear sight + hooded front post, tubular magazine under the barrel to z -0.505 (no box mag), slim rounded forend, traced pistol-grip stock. `magazine` node is now a loading-gate shell stand-in (mag_well at the gate).
- shotgun_blunderbuss: powder flask is a rounded 28 mm thick shell with a bone badge, strap and stopper; bell is 24-sided.

### Shotguns v5
- pump: trigger guard is now a 9 x 6 mm flat band.
- double: barrel centres 34 mm apart joined by a flat brass rib (figure-eight muzzle), straight English stock, short splinter forend (to z -0.246), tall hammer ears on the sides of the action, brass top lever on the tang, receiver widened to +-27 mm (sideplates/straps/hammers shifted), solid guard band; receiver top no longer uses the bright steel_top strip.
- combat: all furniture is glossy near-black polymer (bullpup polish3 recipe, `S.make_poly_mats`), one shell for stock + pistol grip raked ~20 deg (no brass foot plate), short slotted Picatinny rail on the receiver, slim front ghost-ring post on a low clamp, flat-band trigger guard.
- blunderbuss: removed the brass fore-tip block; the flask is now a smooth ivory powder horn (`S.horn`, 10-sided, 7 stations) on the right of the stock with a thin brass strap over the comb; proper curved 8 x 5.5 mm brass trigger guard. mag_well empty is now at the horn centre (+0.025, 0.025, 0.170).

## Snipers (HD pass)
All four rebuilt on the HD shared builders: 1024 px albedo (256 grid, EPX + bicubic), glTF sampler LINEAR, two embedded materials (1911 steel metallic 1 / roughness 0.30; non-metal wood / polymer / bone), 4 empties, redDot:false, <3k tris, verify_ads pass on all. New shared module `gun_sniper_common.py` (`scope()`: engraved steel scope tube with ocular / objective bells, brass rings, turrets, dark lens caps, two steel mount rings). Stocks are `K.shell(... gmap=True)` polygons traced from the photos (real thumbholes / cut-outs).

**Sight wiring (scoped rifles):** `rear_sight` = scope ocular centre, `front_sight` = scope objective centre, both X=0 at the scope axis height and parallel to the bore; `muzzle` at the barrel / brake / emitter end. `mag_well` sits where the magazine meets the receiver (bolt: floorplate stand-in).

| slot | node (slot id) | traced from | scope axis above bore | tris |
|---|---|---|---|---|
| sniper_bolt | sniper_bolt_base.glb | Kar98k side (full walnut stock, round receiver, swept bolt + brass knob, tall rings) | 40.5 mm | 2,308 |
| sniper_antimat | sniper_antimat_base.glb | Barrett M82A1 side mask (skeleton frame stock with cut-out, flat slab receiver + rail, slotted brake, folded bipod, carry handle, box mag); glossy near-black polymer stock + grip (polish3 recipe, `S.make_poly_mats`) | 68.5 mm | 2,788 |
| sniper_marksman | sniper_marksman_base.glb | SVD Dragunov side (thumbhole stock + lightening hole, slotted handguard, AK receiver, gas tube, slotted flash hider, curved mag, PSO-style scope) | 68.5 mm | 2,716 |
| sniper_rail | sniper_rail_base.glb | original gothic coil rifle (refs mood only): slab receiver with exposed capacitor tubes, twin rails with 8 brass coils, emitter cap, polymer skeleton stock + raked grip, battery-cell magazine | 68 mm | 2,652 |

## smg_bullpup v5 - P90 SHAPE REBUILD
Rebuilt from the FN P90 photos (outline traced, 1653 px/m, 0.505 m long): translucent smoked top magazine with 12 brass rounds (3rd glTF material `smg_bullpup_base_glass`, alpha-blended 0.8; the atlas region is also painted smoked + brass discs as an opaque fallback), bulbous polymer lower shell with teardrop thumbhole + trigger hole and a real geometric crown (`dome_shell`: cap edges subdivided + domed 8.5 mm), steel sight housing arching over the magazine with a hollow window, round brass-rimmed ring-sight caps, ring sight + front bead on top, slotted flash hider, charging rods + tabs on both sides, brass trigger. Meshes: body, receiver, magazine (under mag_well at the mag centre). Sight empties: rear_sight = ring centre (z -0.0568), front_sight = bead (z -0.130), both y 0.1571 (bore 0.050), muzzle z -0.2086. 2,240 tris, verify_ads pass.
Shared engine change: `gun_lowpoly_common.mat_index(region)` + `ENERGY_REGIONS` give an optional 3rd material (index 2; used for the rail's emissive energy and the P90 glass); empty by default so the other guns are unchanged.

## Fix pass 6 (review round)
- shotgun_double v6: barrels 20 mm touching + flat brass rib, big curled hammers, raised camera (`render_gun(three_y=...)`).
- shotgun_combat v6: separate raked finger-groove pistol grip, collapsible two-tube stock + slim butt pad.
- sniper_bolt v3: no nose block, barrel +30%, turned-down right-side bolt handle with round brass knob.
- sniper_antimat v3: raked pistol grip + lower receiver block, M82 chevron brake with side ports, 1.5x scope with large objective bell, bipod folded under the barrel.
- sniper_marksman v2: short straight 10 rd box mag, thicker barrel.
- sniper_rail v2: crimson emissive energy channel (3rd material `sniper_rail_base_energy`, emission strength 1.0) between top/bottom rails, helical copper wire coils (`SN.coil`), ribbed receiver with glow slits and bone inlays, solid sculpted polymer stock.

## HMGs (hmg_belt, hmg_minigun, hmg_drum, hmg_chain)

All four: HD builders (`gun_hmg_common.py`: make_atlas / finish_mats / grip_poly / rail / slotted_hider / round_belt), 1024 px LINEAR smooth albedo, locked 1911 steel material + glossy
near-black polymer (polish3 recipe) or satin wood (drum), brass bands, bone cross badge. 1911 GLB format with 4 empties (muzzle, mag_well, rear_sight, front_sight), redDot:false,
verify_ads passes on all. Sight empties sit at X=0, Y_SIGHT, parallel to the bore axis.

| slot | file | tris | Y_SIGHT | rear z | front z | muzzle z | mag_well |
|---|---|---|---|---|---|---|---|
| hmg_belt (M249/M60) | hmg_belt_base.glb | 2,760 | 0.134 | -0.02 | -0.60 | -0.70 | (0,-0.012,-0.125) |
| hmg_minigun (handheld M134) | hmg_minigun_base.glb | 1,996 | 0.162 | 0.085 | -0.755 | -0.80 | (0,0.020,-0.080) |
| hmg_drum (RPK + drum) | hmg_drum_base.glb | 2,308 | 0.134 | -0.27 | -0.765 | -0.80 | drum centre (y -0.100, z -0.165) |
| hmg_chain (handheld M230) | hmg_chain_base.glb | 2,520 | 0.160 | 0.125 | -0.51 | -0.86 | (0.085,-0.010,-0.145) |

Notes: drum + belt traced from the refs (RPK de-rotated 10.5 deg). Minigun/chain have a carry handle arching above the sight line (sights under it). Belt/chain ammo boxes
use `C.BEVEL_MINLEN` 0.9 on the magazine part to save tris. Minigun/chain mag_well is the ammo can, offset right on the chain gun (x 0.085).

### Polish pass (P90 + chain/minigun fixes)
- smg_bullpup v6: 2,880 tris; sight hood now polymer dome_shell (chaikin outline, crown 0.0045), shell rear radii 74/60 px, bevel 0.0165; ring/bead sights on steel stems; 'round' atlas region = dull brass for rounds.
- hmg_chain: 2,924 tris; mag_well now (0.0775, 0.0650-0.0750, -0.19) (can moved forward/smaller); 'leather' furniture region added via C.FURN_REGIONS in builder.
- hmg_minigun: 1,960 tris, leather handle sleeve, round vertical foregrip (S.horn).

### HMG stock pass
- hmg_drum: RPK club-foot stock retraced (rpk_boxmag_side.png, 963 px/m, receiver rear px 812) as one dome_shell (crown 0.0055, hw 0.0215, region wood) + steel buttplate prism; bipod legs thicker. 2,956 tris. `dome_shell` gained a `region` kwarg (default poly, P90 unchanged).
- hmg_chain: shoulder stock (polymer window shell, leather cheek rest + butt pad, steel collar). 2,908 tris. Barrel/shroud/hider segs reduced to 8, can bevel limited (BEVEL_MINLEN 0.075).

### hmg_drum v3
- Long RPK stock (0.31 m from receiver rear, butt 0.15 m tall, overall length 1.15 m, butt z +0.33), steel butt plate prism on the back edge, deployed A-frame bipod (feet y -0.198). 2,536 tris. mag_well/sights unchanged.
