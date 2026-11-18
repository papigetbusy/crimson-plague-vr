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
