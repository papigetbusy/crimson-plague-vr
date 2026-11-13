/* Every gun you can hold, in the order the Tune panel shows them: the hand-made guns (Gothic Rifle, Ember Rifle, Revolver, M4 voxel fallback), then the 20 from the gun catalog. find(id) gives { id, name, build }. */
const GunList = (function () {
  const nice = (id) => id.split('_').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ');
  const LIST = [
    { id: 'rifle', name: 'Gothic Rifle', build: () => GothicRifle.build(), hands: { grip: [0, -0.15, 0.15], fore: [0, -0.12, -0.45], mag: [0, -0.15, -0.13] } },   // the rifle keeps the hand spots it always had
    { id: 'rifle_m4', name: 'M4 Carbine', build: () => GothicRifle.build(), hands: { grip: [0, -0.15, 0.15], fore: [0, -0.12, -0.45], mag: [0, -0.15, -0.13] } },   // if the M4 GLB fails, the Gothic Rifle voxel is used
    { id: 'ember', name: 'Ember Rifle', build: () => EmberRifle.build() },
    { id: 'revolver', name: 'Revolver', build: () => Revolver.build() },
  ].concat(GunCatalog.LIST.map((g) => ({ id: g.id, name: nice(g.id), build: g.build })));
  const find = (id) => LIST.find((g) => g.id === id) || LIST[0];
  const HIP_DOT = { y: 0.1755, z: -0.026 };   // the Gothic Rifle's sight dot (look-only): the hip pose was tuned with it, other guns are lifted and moved to match
  return { LIST, find, HIP_DOT };
})();
if (typeof module !== 'undefined') module.exports = GunList;
