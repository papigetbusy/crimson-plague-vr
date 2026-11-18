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
