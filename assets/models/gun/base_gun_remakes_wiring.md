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
