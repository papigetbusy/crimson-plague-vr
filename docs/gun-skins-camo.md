# Crimson Plague VR: Gun Skins, Camo and Wear

Dictated by the owner on 2026-11-13. This is a design note; no game code has changed yet.

## The selling point
The heart of the game is **the guns you find, the mods you put on, and what you stash to bring back every run.** Skins, camo and wear exist to make every gun you find feel like your own.

## 1. Rarity stays as it is
- The in-game gun rarity system (gray up to legendary and so on) already exists. Keep it unchanged.

## 2. Camo is a separate random drop
- Camo is its own random roll, layered on top of the gun's rarity. It does not replace rarity.
- Rarity and camo are independent. A great gun can roll a terrible camo, and an ordinary gun can roll one of the best camos.

## 3. Camo coverage
- Camo can cover 100% of the gun, or only part of it, such as just the barrel.
- Coverage is shown as a percentage on the gun, the way CS:GO shows it.
- The best possible roll is one of the top camos at 100% coverage.

## 4. Wear, like CS:GO
- Each gun rolls a wear level.
- **Worn guns** look scratched and beaten up, with scars and damage.
- **Pristine guns** look perfect, metallic and glistening. When you hold one, you can't help but look at it.
- Wear and camo coverage together decide how that particular gun looks.

## 5. Free forever
- The game is 100% free. There are no paid skins and no battle pass.
- Every gun, camo and wear level is earned by grinding: found in runs, then modded and stashed.

## Notes for building it later (not started)
- This fits the PS2 low-poly art style: camo and wear go into the texture (masks plus a wear and scratch layer), and the model stays the same.
- Each gun model needs separate texture areas, such as barrel, slide or receiver, grip and stock, so camo can cover just part of the gun.
- Show the rarity, camo name, coverage percentage and wear on the gun's card in the stash and bag. Pair it with an inspect view so players can admire a pristine gun.
