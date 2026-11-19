"""Shared helpers for the gothic HMG remakes (belt, minigun, drum, chain): HD atlas + materials, raked finger-groove pistol grip,
carry handle, picatinny rail, slotted flash hider, belt-of-rounds."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_sniper_common as SN
S, K, C, M, G = SN.S, SN.K, SN.C, SN.M, SN.G


def make_atlas(out_dir, name, wood=False, extra=()):
    C.M.reset_scene()
    reg = [('barrel', 128, 72), ('tube', 128, 48), ('panel', 112, 36), ('port', 56, 28), ('mag', 96, 32), ('bone_stock', 40, 40),
           ('steel', 48, 32), ('steel_top', 48, 24), ('muzzle', 28, 28), ('brass', 24, 24), ('bone_end', 16, 16),
           ('wood', 128, 48) if wood else ('poly', 128, 40)] + list(extra)
    A = K.Atlas(reg)
    A.install()
    A.steel('steel', seed=5, grime=0.84)
    A.steel('steel_top', ('steel_mid', 'steel_light', 'sheen', 'steel_edge'), seed=6, grime=0.74)
    A.engraved('panel', seed=9, lam=22, grime=0.84, arches=True)
    A.wrap('barrel', 12, 6, lambda j: 'eng' if j in (0, 6) else 'hi' if j == 3 else 'dark' if j == 9 else 'plain', seed=11, lam=18)
    A.wrap('tube', 8, 6, lambda j: 'eng' if j in (0, 4) else 'hi' if j == 2 else 'dark' if j == 6 else 'plain', seed=17, lam=16)
    A.muzzle('muzzle'); A.brass('brass', engrave=True)
    A.bone('bone_stock', seed=37, motif='cross'); A.bone('bone_end', motif=None, rim=False)
    if wood:
        S.paint_wood(A, 'wood')
    else:
        A.poly('poly', seed=43, fine=True)
    S.paint_port(A, 'port'); A.mag('mag', holes=True)
    return A


def finish_mats(A, out_dir, name, wood=False):
    tex = os.path.join(out_dir, name + '_albedo.png')
    A.save(tex)
    return S.make_mats(name, tex) if wood else S.make_poly_mats(name, tex)


RK20 = math.radians(20)


def grip_poly(z0, y0, length=0.115, thick=0.0165, rake=RK20, grooves=True):
    """raked pistol grip outline (z, y): top-front corner at (z0, y0); finger grooves on the front edge."""
    def gp(u, v):
        return (round(z0 + u * math.sin(rake) + v * math.cos(rake), 4), round(y0 - u * math.cos(rake) + v * math.sin(rake), 4))
    sc = length / 0.118
    front = [(0.000, -0.0150), (0.016, -thick), (0.030, -thick), (0.040, -0.0125), (0.052, -thick), (0.064, -thick), (0.074, -0.0125),
             (0.086, -thick), (0.098, -thick), (0.108, -0.0135), (0.118, -0.0140)]
    back = [(0.118, 0.0150), (0.104, 0.0178), (0.084, 0.0168), (0.062, 0.0158), (0.040, 0.0168), (0.020, 0.0200), (0.000, 0.0180)]
    if not grooves:
        front = [(0.0, -0.015), (0.06, -0.0165), (0.118, -0.0145)]
    return [gp(u * sc, v) for u, v in front + back]


def rail(part, z0, z1, y_base, w=0.0085, tooth=0.0200, step=0.0360):
    part.box((-w, y_base - 0.0004, z1), (w, y_base + 0.0014, z0), 'steel', top='steel_top')
    zz = z0
    while zz - tooth > z1:
        part.box((-w, y_base + 0.0012, zz - tooth), (w, y_base + 0.0032, zz), 'steel', top='steel_top')
        zz -= step


def slotted_hider(part, by, z0, z1, r=0.0125, n_slots=3, segs=10, cx=0.0, phase=-math.pi / 12):
    """barrel cage: alternating ring / groove radii, dark muzzle cap."""
    st = [(z0, r * 0.8)]
    L = z0 - z1
    seg = L / (2 * n_slots + 1)
    z = z0
    for i in range(2 * n_slots + 1):
        rr = r if i % 2 == 0 else r * 0.80
        st.append((z - 0.001, rr)); z -= seg; st.append((z, rr))
    st[-1] = (z1, st[-1][1])
    K.revolve(part, st, by, segs=segs, region='barrel', cx=cx, cap_f='muzzle', cap_b='steel', phase=phase)


def round_belt(part, path_yz, x0, x1, r=0.0050, segs=5, link=True):
    """cartridges lying across X (brass) with a steel link band, at (y, z) positions."""
    for y, z in path_yz:
        part.cyl((x0, y, z), (x1, y, z), r, segs, 'brass', cap='brass')
        if link:
            part.box((x0 + 0.003, y - r * 0.55, z - r * 0.55), (x0 + 0.0075, y + r * 0.55, z + r * 0.55), 'steel')
