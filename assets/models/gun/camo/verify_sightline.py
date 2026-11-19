"""Sight-line clearance check on an exported 1911 GLB: casts rays along the rear_sight -> front_sight line (offsets 0.3 / 1 / 2 mm above)
from 0.30 m behind the rear sight to 1 m past the muzzle empty; nothing in the GLB may intersect them. Also checks the muzzle empty sits at the
frontmost point of the mesh bore axis."""
import sys, numpy as np
sys.argv = [sys.argv[0]] + sys.argv[1:]
import importlib.util, os
spec = importlib.util.spec_from_file_location('cg', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compare_glb.py'))
src = open(spec.origin).read().split("a, ab = load")[0]
ns = {}; exec(src, ns)
load, acc, prims = ns['load'], ns['acc'], ns['prims']
import json
def world(j):
    parent = {}
    for i, n in enumerate(j['nodes']):
        for c in n.get('children', []): parent[c] = i
    memo = {}
    def w(i):
        if i in memo: return memo[i]
        n = j['nodes'][i]; t = np.array(n.get('translation', [0, 0, 0])); q = n.get('rotation', [0, 0, 0, 1]); s = np.array(n.get('scale', [1, 1, 1]))
        if i in parent:
            pt, pq, ps = w(parent[i])
            return memo.setdefault(i, (pt + qrot(pq, t * ps), qmul(pq, q), ps * s))
        return memo.setdefault(i, (t, q, s))
    return {n['name']: w(i) for i, n in enumerate(j['nodes']) if 'name' in n}, w
def qrot(q, v):
    x, y, z, w = q; u = np.array([x, y, z]); return v + 2 * np.cross(u, np.cross(u, v) + w * v)
def qmul(a, b):
    return [a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1], a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0], a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3], a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]]
def hit(o, d, T):
    v0, v1, v2 = T[:, 0], T[:, 1], T[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    p = np.cross(d, e2); det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    tv = o - v0; u = (tv * p).sum(1) * inv
    q = np.cross(tv, e1); v = (q * d).sum(1) * inv
    t = (e2 * q).sum(1) * inv
    m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return t[m]
def hits_for(path):
    j, b = load(path)
    W, w = world(j)
    tris = []
    for i, n in enumerate(j['nodes']):
        if 'mesh' not in n: continue
        wt, wq, ws = w(i)
        for p in j['meshes'][n['mesh']]['primitives']:
            pos = acc(j, b, p['attributes']['POSITION']).astype(np.float64); idx = acc(j, b, p['indices']).reshape(-1, 3)
            pos = np.array([wt + qrot(wq, v * ws) for v in pos])
            tris.append(pos[idx])
    T = np.concatenate(tris)
    R = W['rear_sight'][0]; F = W['front_sight'][0]; Mz = W['muzzle'][0]
    d = (F - R); d /= np.linalg.norm(d)
    print('rear', np.round(R, 4), 'front', np.round(F, 4), 'muzzle', np.round(Mz, 4))
    zmin = T[..., 2].min()   # forward is -z in glTF? report
    allv = T.reshape(-1, 3)
    print('mesh z range', round(allv[:, 2].min(), 4), round(allv[:, 2].max(), 4), '| muzzle empty z', round(Mz[2], 4), '(tip gap mm)', round((Mz[2] - allv[:, 2].min()) * 1000, 2))
    res = {}
    for off in (0.0003, 0.001, 0.002):
        o = R - d * 0.30 + np.array([0, off, 0])
        ts = hit(o, d, T)
        lim = 0.30 + np.linalg.norm(F - R) - 0.0005
        res[off] = np.sort(ts[ts < lim])
    return res

def main(path, base):
    new = hits_for(path); old = hits_for(base)
    bad = 0
    for off in new:
        extra = [t for t in new[off] if not any(abs(t - o) < 0.0003 for o in old[off])]
        print(f'offset +{off*1000:.1f} mm: hits before front sight: tier {len(new[off])} vs locked base {len(old[off])} | NEW blockers: {len(extra)}', ('(t=' + ', '.join(f'{x:.3f}' for x in extra[:4]) + ')') if extra else '')
        bad += len(extra)
    print('SIGHT LINE', 'CLEAR (no new geometry on the line; only the locked 1911 rear-sight block itself)' if bad == 0 else 'BLOCKED')
    return bad

if __name__ == '__main__':
    base = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pistol_1911_base.glb')
    sys.exit(1 if main(sys.argv[1], base) else 0)
