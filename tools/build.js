// Joins src/referee_data.js + src/referee.js + src/screen/*.js + src/screen.js + src/index.template.html into one playable page: site/index.html
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const read = f => fs.readFileSync(path.join(root, 'src', f), 'utf8');
const label = process.argv[2] || 'local';
const cheat = process.argv.includes('--cheat');   // the private cheat build keeps the Effects and Gun menus; the published game never has them
const models = ['models/voxel.js', 'models/voxel_smooth.js', 'models/gothic_rifle_data.js', 'models/gothic_rifle.js', 'models/ember_profile.js', 'models/ember_rifle.js', 'models/revolver_data.js', 'models/revolver.js', 'models/gun_kit.js', 'models/guns_packed_data.js', 'models/guns_packed.js', 'models/guns_packed_pistol.js', 'models/guns_packed_smg.js', 'models/guns_packed_shotgun.js', 'models/guns_packed_sniper.js', 'models/guns_packed_hmg.js', 'models/gun_catalog.js', 'models/horned_fiend_data.js', 'models/horned_fiend.js', 'models/bestiary_kit.js', 'models/horned_fiend_v2.js', 'models/bone_hound.js', 'models/bone_hound_v2.js', 'models/rock_golem.js', 'models/demon_lord.js', 'models/demon_lord_data.js', 'models/demon_lord_v2.js', 'models/demon_lord_v3.js', 'models/goblin.js', 'models/skeleton.js', 'models/mushroom.js', 'models/eyeball.js', 'models/flame_spirit.js', 'models/bat_lord.js', 'models/lich_king.js', 'models/elder_dragon.js'].map(read).join('\n');
// a small build number on the start card, so anyone testing can say exactly which version they are on (the short git id; a + means local edits not yet committed)
let build = 'local';
try { const cp = require('child_process'); build = cp.execSync('git rev-parse --short HEAD', { cwd: root }).toString().trim() + (cp.execSync('git status --porcelain', { cwd: root }).toString().trim() ? '+' : ''); } catch (e) { /* no git here: stays local */ }
// mesh guns (assets/models/manifest.json): the GLBs ride inside the page as base64, with three's GLTFLoader (r128) and src/screen/glb_guns.js;
// a loader problem only warns, and the voxel guns stay. Wrok's v2 wall textures are embedded the same way (tools/wall_tex_embed.js).
const walltex = require('./wall_tex_embed.js').script(root);
const glb = require('./glb_embed.js').script(root) + '\ntry {\n' + read('vendor/gltf_loader_r128.js') + '\n} catch (e) { console.warn(\'GLTFLoader failed to start, voxel guns stay: \' + e.message); }\n' + read('screen/glb_guns.js') + '\n' + read('screen/crimson_halls.js');
const html = read('index.template.html')
  .replace('/*__REFEREE__*/', () => read('referee_data.js') + '\n' + read('floorgen_gates.js') + '\n' + read('floorgen.js') + '\n' + read('referee_shots.js') + '\n' + read('referee_coop.js') + '\n' + read('referee_classes.js') + '\n' + read('referee_class.js') + '\n' + read('referee_affixes.js') + '\n' + read('referee_boss_extras.js') + '\n' + read('referee_bosses.js') + '\n' + read('referee_trail.js') + '\n' + read('referee_locks.js') + '\n' + read('referee_stash.js') + '\n' + read('referee_mods.js') + '\n' + read('referee_weapons.js') + '\n' + read('referee_gear.js') + '\n' + read('referee_gunfx.js') + '\n' + read('referee_ailments.js') + '\n' + read('referee_variants.js') + '\n' + read('referee.js'))
  .replace('/*__MODELS__*/', () => models)
  .replace('/*__SCREEN__*/', () => 'const CHEATS = ' + cheat + ';\n' + glb + '\n' + walltex + '\n' + ['screen/wall_tex_v2.js', 'screen/world_tex.js', 'screen/wall_materials.js', 'screen/wall_sets.js', 'screen/world_bake.js', 'screen/world_view.js', 'screen/locks_view.js', 'screen/minimap.js', 'screen/compass.js', 'screen/monster_rigs.js', 'screen/shots_view.js', 'screen/floor_gun_shapes.js', 'screen/loot_view.js', 'screen/trap_view.js', 'screen/boss_fx.js', 'screen/variant_look.js', 'screen/skins_look.js', 'screen/friend_gun.js', 'screen/peers_view.js', 'screen/party_hud.js', 'coop_link.js', 'screen/net_peer.js', 'screen/coop.js', 'screen/hud.js', 'screen/gun_card.js', 'screen/menu_focus.js', 'screen/stash_menu.js', 'screen/gear_menu.js', 'screen/blueprints.js', 'screen/stash_store.js', 'screen/saves.js', 'screen/codex_text.js', 'screen/codex_pages.js', 'screen/codex.js', 'screen/pad_input.js', 'screen/xr_input.js', 'screen/xr_menu.js', 'screen/xr_grab.js', 'screen/xr_interact.js', 'screen/xr_feel.js', 'screen/xr_mode.js', 'screen/touch_layout.js', ...(fs.existsSync(path.join(root, 'src', 'screen', 'fx_data.js')) ? ['screen/fx_data.js'] : []), 'screen/fx_plan.js', 'screen/fx_sprites.js', 'screen/fx_picker.js', ...(fs.existsSync(path.join(root, 'src', 'screen', 'wall_data.js')) ? ['screen/wall_data.js'] : []), 'screen/wall_skin.js', 'screen/gun_skins.js', 'screen/gun_look.js', 'screen/gun_list.js', 'screen/gun_skin_picker.js', 'screen/gun_motion.js', 'screen.js'].map(read).join('\n'))
  .replace(/__BUILD__/g, label)
  .replace('<title>Crimson Plague</title>', cheat ? '<title>Crimson Plague CHEAT BUILD</title>' : '<title>Crimson Plague</title>')
  .replace('<p>Hold the corridor. Nothing stops coming.</p>', () => '<p>Hold the corridor. Nothing stops coming.</p><p class="buildTag">build ' + build + '</p>')
  .replace('<h1>Crimson Plague</h1>', cheat ? '<h1>Crimson Plague</h1><p class="cheatTag">CHEAT BUILD (private testing)</p>' : '<h1>Crimson Plague</h1>');
const out = cheat ? 'cheat' : 'site';      // cheat/ is git-ignored and never published
fs.mkdirSync(path.join(root, out), { recursive: true });
fs.writeFileSync(path.join(root, out, 'index.html'), html);
// models Grok delivered are served next to the page
const src = path.join(root, 'assets'), dst = path.join(root, out, 'assets');
if (fs.existsSync(src)) fs.cpSync(src, dst, { recursive: true });
console.log(out + '/index.html', (html.length / 1024).toFixed(0) + ' KB');
