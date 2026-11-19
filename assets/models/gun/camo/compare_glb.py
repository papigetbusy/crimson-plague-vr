"""Check camo GLBs vs the original 1911 GLB: node names/transforms, empties, positions/indices/normals identical; report UV changes."""
import json, struct, sys, numpy as np
def load(p):
    b = open(p, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + L]); off = 20 + L + 8; binb = b[off:]
    return j, binb
def acc(j, binb, i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a['componentType']]
    st = bv.get('byteStride') or n * np.dtype(dt).itemsize
    o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    arr = np.frombuffer(binb, dtype=np.uint8, count=a['count'] * st, offset=o).reshape(a['count'], st)
    return np.frombuffer(arr[:, :n * np.dtype(dt).itemsize].tobytes(), dtype=dt).reshape(a['count'], n)
def prims(j, binb):
    out = {}
    for ni, n in enumerate(j['nodes']):
        if 'mesh' in n:
            for k, p in enumerate(j['meshes'][n['mesh']]['primitives']):
                at = p['attributes']
                out[(n['name'], k)] = dict(pos=acc(j, binb, at['POSITION']), idx=acc(j, binb, p['indices']), nrm=acc(j, binb, at['NORMAL']), uv=acc(j, binb, at['TEXCOORD_0']), mat=j['materials'][p['material']])
    return out
a, ab = load(sys.argv[1]); 
for f in sys.argv[2:]:
    b, bb = load(f)
    na = {(n['name']): (n.get('translation'), n.get('rotation'), n.get('scale'), n.get('children')) for n in a['nodes']}
    nb = {(n['name']): (n.get('translation'), n.get('rotation'), n.get('scale'), n.get('children')) for n in b['nodes']}
    print(f, 'node table identical:', na == nb, '| nodes', sorted(nb))
    pa, pb = prims(a, ab), prims(b, bb)
    print('  primitive keys identical:', sorted(pa) == sorted(pb))
    for k in sorted(pa):
        x, y = pa[k], pb[k]
        same = lambda q: x[q].shape == y[q].shape and np.allclose(x[q], y[q], atol=1e-6)
        mats = {q: (x['mat'].get('pbrMetallicRoughness', {}).get(q)) for q in ('metallicFactor', 'roughnessFactor')}, {q: (y['mat'].get('pbrMetallicRoughness', {}).get(q)) for q in ('metallicFactor', 'roughnessFactor')}
        print('  ', k, 'verts', len(y['pos']), 'pos==', same('pos'), 'idx==', same('idx'), 'nrm==', same('nrm'), 'uv==', same('uv'), 'mat factors same:', mats[0] == mats[1])

    # exporter may reorder vertices/triangles when UVs differ: compare triangle geometry order-independently
    def canon(p):
        T = np.round(p['pos'][p['idx'].reshape(-1, 3)], 5); out = []
        for t in T:
            vs = [tuple(v) for v in t]; i = vs.index(min(vs)); out.append(tuple(vs[i:] + vs[:i]))
        return sorted(out)
    for k in sorted(pa):
        print('  ', k, 'triangle geometry identical (order-independent):', canon(pa[k]) == canon(pb[k]))
