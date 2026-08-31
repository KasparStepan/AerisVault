import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

AZ, EL = np.deg2rad(-42.0), np.deg2rad(20.0)
U = np.array([-np.sin(AZ), np.cos(AZ), 0.0])
V = np.array([-np.cos(AZ)*np.sin(EL), -np.sin(AZ)*np.sin(EL), np.cos(EL)])
N = np.array([ np.cos(AZ)*np.cos(EL), np.sin(AZ)*np.cos(EL), np.sin(EL)])
LIGHT = np.array([0.34, -0.56, 0.76]); LIGHT /= np.linalg.norm(LIGHT)
T0, T1 = 0.0, 1.5*np.pi

def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i+2], 16)/255 for i in (0, 2, 4)])

class Model:
    def __init__(self):
        self.f = []
        
    def add(self, v, c, cut=False):
        self.f.append((np.asarray(v, float), c, cut))
        
    def revolve(self, profile, color, nseg=56, caps=True):
        c = hex2rgb(color)
        th = np.linspace(T0, T1, nseg+1)
        pts = np.array(profile, float); n = len(pts)
        for i in range(n):
            r0, z0 = pts[i]; r1, z1 = pts[(i+1) % n]
            if abs(r0) < 1e-9 and abs(r1) < 1e-9:
                continue
            for a, b in zip(th[:-1], th[1:]):
                self.add([(r0*np.cos(a), r0*np.sin(a), z0),
                          (r0*np.cos(b), r0*np.sin(b), z0),
                          (r1*np.cos(b), r1*np.sin(b), z1),
                          (r1*np.cos(a), r1*np.sin(a), z1)], c)
        if caps:
            for a in (T0, T1):
                self.add([(r*np.cos(a), r*np.sin(a), z) for r, z in pts], c, True)
                
    def prism(self, poly, z0, z1, color):
        c = hex2rgb(color); n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]; x1, y1 = poly[(i+1) % n]
            self.add([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], c)
        self.add([(x, y, z1) for x, y in poly], c)
        self.add([(x, y, z0) for x, y in poly][::-1], c)
        
    def helix(self, rm, rw, z0, z1, turns, color, nlong=380, nround=10):
        c = hex2rgb(color); total = 2*np.pi*turns
        s = np.linspace(0, total, nlong+1)
        keep = ((s % (2*np.pi)) >= T0) & ((s % (2*np.pi)) <= T1)
        zz = z0 + (z1-z0)*s/total
        
        def fr(si, zi):
            ctr = np.array([rm*np.cos(si), rm*np.sin(si), zi])
            tan = np.array([-rm*np.sin(si), rm*np.cos(si), (z1-z0)/total])
            tan /= np.linalg.norm(tan)
            rad = np.array([np.cos(si), np.sin(si), 0.0])
            bi = np.cross(tan, rad); bi /= np.linalg.norm(bi)
            return ctr, np.cross(bi, tan), bi
            
        ph = np.linspace(0, 2*np.pi, nround+1)
        for i in range(nlong):
            if not (keep[i] and keep[i+1]):
                continue
            c0, r0v, b0 = fr(s[i], zz[i]); c1, r1v, b1 = fr(s[i+1], zz[i+1])
            for a, b in zip(ph[:-1], ph[1:]):
                self.add([c0 + rw*(np.cos(a)*r0v + np.sin(a)*b0),
                          c0 + rw*(np.cos(b)*r0v + np.sin(b)*b0),
                          c1 + rw*(np.cos(b)*r1v + np.sin(b)*b1),
                          c1 + rw*(np.cos(a)*r1v + np.sin(a)*b1)], c)
        for si in np.arange(0, total, 2*np.pi):
            for ang in (T0, T1):
                sv = si + ang
                if sv > total:
                    continue
                ctr, rv, bv = fr(sv, z0 + (z1-z0)*sv/total)
                self.add([ctr + rw*(np.cos(a)*rv + np.sin(a)*bv) for a in ph], c, True)

C, R_CAV, R_OUT, R_FL, FLOOR = 72.0, 10.75, 13.75, 21.0, 4.0
GREY, BLUE, DBLUE = "#b9bec6", "#4a90d9", "#2f6ba8"
RED, GREEN, PURPLE, DARK = "#cf4b42", "#4fae74", "#8d6fb5", "#646a73"
SLEEVE_H, DNO, PLUG_H, COLLAR = 35.0, 1.6, 12.0, 4.0

def build(t, L, stack):
    m = Model()
    m.revolve([(0, 0), (R_FL, 0), (R_FL, FLOOR), (R_OUT, FLOOR), (R_OUT, C+FLOOR),
               (R_CAV, C+FLOOR), (R_CAV, FLOOR), (0, FLOOR)], GREY)
    z = FLOOR
    for th in stack:
        m.revolve([(0, z), (10.5, z), (10.5, z+th), (0, z+th)], PURPLE)
        z += th
    zb = FLOOR + t
    m.revolve([(0, zb), (10.5, zb), (10.5, zb+SLEEVE_H), (7.2, zb+SLEEVE_H),
               (7.2, zb+DNO), (0, zb+DNO)], BLUE)
    m.revolve([(0, zb+DNO), (5.25, zb+DNO), (5.25, zb+DNO+20.9), (0, zb+DNO+20.9)], DBLUE)
    zs = zb + DNO
    m.helix(6.275, 0.625, zs+0.7, zs+L-0.7, 10, RED)
    zp = zs + L
    m.revolve([(0, zp), (7.0, zp), (7.0, zp+PLUG_H), (10.5, zp+PLUG_H),
               (10.5, zp+PLUG_H+COLLAR), (6.0, zp+PLUG_H+COLLAR), (6.0, C+FLOOR+14),
               (0, C+FLOOR+14)], GREEN)
    m.revolve([(6.3, C+FLOOR), (R_FL, C+FLOOR), (R_FL, C+FLOOR+4), (6.3, C+FLOOR+4)], GREY)
    for ang in (50, 140, 230):
        a = np.deg2rad(ang); cx, cy = 17*np.cos(a), 17*np.sin(a)
        m.prism([(cx+2*np.cos(p), cy+2*np.sin(p)) for p in np.linspace(0, 2*np.pi, 17)],
                0.0, C+FLOOR+6.5, DARK)
        m.prism([(cx+3.2*np.cos(p), cy+3.2*np.sin(p)) for p in np.linspace(0, 2*np.pi, 17)],
                C+FLOOR+4, C+FLOOR+6.5, DARK)
    return m

def draw(ax, m, dx):
    polys, cols, eds, dep = [], [], [], []
    for v, base, cut in m.f:
        p2 = np.stack([v @ U + dx, v @ V], axis=-1)
        nr = np.cross(v[1]-v[0], v[2]-v[1] if len(v) > 2 else v[0]-v[1])
        ln = np.linalg.norm(nr)
        if ln < 1e-12:
            continue
        nr /= ln
        if nr @ N < 0:
            nr = -nr
        lam = 0.44 + 0.56*max(0.0, nr @ LIGHT)
        c = np.clip(base*0.55 + 0.30, 0, 1)*(0.74+0.26*lam) if cut else base*lam
        polys.append(p2); cols.append(np.clip(c, 0, 1))
        eds.append((0.15, 0.16, 0.18, 0.6) if cut else (0, 0, 0, 0.09))
        dep.append(v.mean(axis=0) @ N)
    o = np.argsort(dep)
    ax.add_collection(PolyCollection([polys[i] for i in o],
                                     facecolors=[cols[i] for i in o],
                                     edgecolors=[eds[i] for i in o],
                                     linewidths=0.32, antialiased=True))

def pt(r, z, ang, dx):
    a = np.deg2rad(ang)
    p = np.array([r*np.cos(a), r*np.sin(a), z])
    return (p @ U + dx, p @ V)

fig, ax = plt.subplots(figsize=(13.6, 10.6), dpi=185)
ax.set_facecolor("#f7f6f3"); fig.patch.set_facecolor("#f7f6f3")

DXL, DXR = -46.0, 62.0
mL = build(0.0, 54.4, [])
mR = build(32.4, 21.9, [25.6, 6.4, 0.4])
draw(ax, mL, DXL); draw(ax, mR, DXR)

def lbl(anchor, xy, txt, size=7.4, weight="normal"):
    ax.annotate(txt, xy=anchor, xytext=xy, fontsize=size, color="#1b1d20",
                weight=weight, ha="left" if xy[0] > anchor[0] else "right",
                va="center", linespacing=1.5,
                arrowprops=dict(arrowstyle="-", color="#565a60", lw=0.7,
                                shrinkA=0, shrinkB=3))

lbl(pt(6, 88, 150, DXL),    (-118,  84), "DŘÍK PÍSTU Ø12\nvyčnívá 10 mm nad víko")
lbl(pt(16, 78, 165, DXL),   (-124,  62), "VÍKO Ø42 × 4\n3× stahovací šroub M4\n(mosazné heat-set vložky)")
lbl(pt(10, 74, 205, DXL),   (-124,  38), "LÍMEC PÍSTU Ø21 × 4\ndosedá zdola na víko\n= PEVNÝ DORAZ")
lbl(pt(6.3, 42, 250, DXL),  ( -18,  30), "PRUŽINA 13,8/1,25\nL0 = 62,5")
lbl(pt(10.5, 26, 235, DXL), ( -16,   4), "POUZDRO VLOŽKY\nØ21 / Ø14,4, výška 35")
lbl(pt(5.25, 16, 205, DXL), (-118,  -6), "TRN Ø10,5 × 20,9\nsoučást vložky")
lbl(pt(12.5, 30, 160, DXL), (-124, -30), "TĚLO – dutina Ø21,5\nhloubka C = 72, stěna 3")
lbl(pt(18, 2, 200, DXL),    (-120, -52), "PŘÍRUBA Ø42 × 4")

lbl(pt(7, 20, 250, DXR),    ( 128, -14), "PODLOŽKY 32,4 mm\n(25,6 + 6,4 + 0,4)\nplné disky Ø21 bez díry")
lbl(pt(6.3, 50, 250, DXR),  ( 128,  24), "pružina zkrácena na 21,9\n→ 50 N")
lbl(pt(6.5, 66, 250, DXR),  ( 128,  50), "dřík pístu Ø14 × 12\nzajíždí do pouzdra")
lbl(pt(9, 74, 300, DXR),    ( 128,  72), "čelo pístu se NEHNULO –\nlímec pořád leží na víku")

for dx, txt in ((DXL, "NEJNIŽŠÍ SÍLA – bez podložek\npružina 54,4 mm  →  10 N"),
                (DXR, "NEJVYŠŠÍ SÍLA – plný stoh\npružina 21,9 mm  →  50 N")):
    ax.text(dx, 100, txt, ha="center", va="center", fontsize=9.6,
            color="#1b1d20", weight="bold", linespacing=1.6)

ax.text(0, -76,
        "ŘETĚZEC VÝŠEK  (platí pro každou pružinu i každou sílu):\n"
        "podložky  +  dno vložky  +  délka pružiny  +  dřík pístu 12,0  +  límec 4,0  =  C = 72,0 mm\n\n"
        "Podložka o tloušťce t zvedne vložku i pružinu o t, ale límec pístu drží čelo v pevné poloze "
        "→ pružina se dostlačí přesně o t.\n"
        "Vlevo 0 + 1,6 + 54,4 + 12 + 4 = 72     ·     vpravo 32,4 + 1,6 + 21,9 + 12 + 4 = 71,9",
        ha="center", va="top", fontsize=8.4, color="#2f3339", linespacing=1.85)

ax.set_title("PŘÍPRAVEK PRO OVĚŘENÍ PŘÍTLAČNÉ SÍLY  ·  čtvrtinový řez, ISO  ·  pružina 3) 13,8/1,25 L0 = 62,5",
             fontsize=12, color="#15171a", pad=18)
ax.set_xlim(-190, 190); ax.set_ylim(-104, 112)
ax.set_aspect("equal"); ax.axis("off")
plt.tight_layout()
plt.savefig("pripravek_rez_iso.png", dpi=185,
            facecolor=fig.get_facecolor(), bbox_inches="tight")
print("ok")