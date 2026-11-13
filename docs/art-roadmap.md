# Crimson Plague VR: Art and Content Roadmap

Dictated by the owner on 2026-11-13. Work in this order. Each step builds on the art style locked in step 1.

## Key principles
- **A gameplay loop that never gets repetitive.** This is a core design rule for every step: runs should keep changing, not repeat the same thing.
- **Lock the art style first.** Nothing else starts until the starter pistol sets the look.
- **Voxels stay as the fallback.** If a mesh is missing or fails to load, the game uses the existing voxel model.
- **Tools:** use Meshy to generate meshes when reference pictures exist, and Blender (free) to rig, texture and export.
- **Still needed in the game:** a GLB loader and a model manifest the game actually reads.
- **Budget:** PS2 / Metal Gear Solid 3 Snake Eater style, with low-poly meshes and small limited-palette textures (see `docs/lowpoly-pipeline.md`).

## 1. Starter pistol (1911)
- A low-poly test model in PS2 Snake Eater style.
- 300 to 1,500 triangles, with a 128 or 256 px texture in a limited palette.
- Uses the existing voxel pistol as the silhouette and proportion reference.
- **This is where the art style gets locked, before anything else.**
- Give the 1911 a bigger moveset and a better feel in the hand.

## 2. Crimson Halls environment
- The first environment: red walls, low gold lighting, and the feel of a Castlevania-style overlord demon castle.
- Once the style is locked on the walls, use each existing level's color palette as the reference for the remaining six environments, seven in total.

## 3. All guns
- Model every gun individually.
- Give every gun its own reload animation.

## 4. Mobs
- One default model per mob type: fiend, goblin, skeleton dog, golem and the rest.
- **Do not make a new model for each evolution.** Mobs evolve with level (harder, new powers, some disappear and reappear) but share the base mesh.

## 5. Mob skins
- A skin for each power-up or evolution a mob gets at higher levels, all on the shared base mesh.

## 6. Bosses
- Bigger rooms that open up into Elden Ring-style boss arenas, for that "oh no, here's this guy" moment.
- New boss-only game mechanics and bigger movesets.

## 7. Ongoing
- Bug fixing for guns, shooting, item procs and so on happens continuously as we go deeper. It never blocks the steps above.
