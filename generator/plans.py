"""
Dimensioned 2D floor plans (SVG) generated from design/layout.py.

    python3 generator/plans.py      ->  output/plans/{ground,first,roof}_floor.svg
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "design"))
import layout as L  # noqa: E402

S = 20.0          # px per foot
M = 110.0         # margin
W_PX = L.PLOT_W * S + 2 * M
H_PX = L.PLOT_D * S + 2 * M + 150

INK = "#2b211c"
WALL = "#3b2a22"
PINK = "#d4876a"
MUTED = "#8a7d72"
FURN = "#a89a8c"


def X(x):
    return M + x * S


def Y(y):
    return M + 110 + (L.PLOT_D - y) * S


def ftin(v):
    ft = int(v + 1e-6)
    inch = round((v - ft) * 12)
    if inch == 12:
        ft, inch = ft + 1, 0
    return f"{ft}'-{inch}\""


def wrap(text, n):
    out, cur = [], ""
    for wd in text.split():
        if len(cur) + len(wd) + 1 > n:
            out.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    return out + [cur]


class SVG:
    def __init__(self):
        self.items = []

    def add(self, s):
        self.items.append(s)

    def rect(self, x0, y0, x1, y1, fill="none", stroke="none", sw=1, dash=None, rx=0, op=1.0):
        xa, xb = sorted((X(x0), X(x1)))
        ya, yb = sorted((Y(y0), Y(y1)))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{xa:.1f}" y="{ya:.1f}" width="{xb - xa:.1f}" height="{yb - ya:.1f}" rx="{rx}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d} opacity="{op}"/>')

    def line(self, x0, y0, x1, y1, stroke=INK, sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{X(x0):.1f}" y1="{Y(y0):.1f}" x2="{X(x1):.1f}" y2="{Y(y1):.1f}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def path(self, d, stroke=INK, sw=1, fill="none", dash=None):
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" fill="{fill}"{dd}/>')

    def text(self, x, y, s, size=12, weight=400, fill=INK, anchor="middle", rot=0, px=False):
        tx, ty = (x, y) if px else (X(x), Y(y))
        tr = f' transform="rotate({rot} {tx:.1f} {ty:.1f})"' if rot else ""
        self.add(f'<text x="{tx:.1f}" y="{ty:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
                 f'text-anchor="{anchor}" dominant-baseline="middle"{tr}>{s}</text>')

    def save(self, path, title, subtitle):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_PX:.0f} {H_PX:.0f}" '
                f'width="{W_PX:.0f}" height="{H_PX:.0f}" font-family="Helvetica, Arial, sans-serif">'
                f'<rect width="100%" height="100%" fill="#fbf8f3"/>'
                f'<text x="{M}" y="34" font-size="20" font-weight="700" fill="{INK}">{title}</text>'
                + "".join(f'<text x="{M}" y="{58 + 16 * i}" font-size="12" fill="{MUTED}">{ln}</text>'
                          for i, ln in enumerate(wrap(subtitle, 92))))
        with open(path, "w") as f:
            f.write(head + "\n".join(self.items) + "</svg>")


def wall_geom(w):
    (ax, ay), (bx, by) = w["a"], w["b"]
    horiz = abs(ay - by) < 1e-6
    c = ay if horiz else ax
    u0, u1 = (min(ax, bx), max(ax, bx)) if horiz else (min(ay, by), max(ay, by))
    return horiz, c, u0, u1


def draw_wall(g, w, fill=WALL):
    horiz, c, u0, u1 = wall_geom(w)
    t = w["t"]
    ops = sorted(w["openings"], key=lambda o: o["s"])
    cur = u0
    segs = []
    for o in ops:
        if o["kind"] in ("vent",) and o["sill"] >= 4.5:
            continue  # high vents: wall is solid at plan-cut height
        segs.append((cur, o["s"]))
        cur = o["e"]
    segs.append((cur, u1))
    for a, b in segs:
        if b - a < 1e-3:
            continue
        if horiz:
            g.rect(a, c - t / 2, b, c + t / 2, fill=fill)
        else:
            g.rect(c - t / 2, a, c + t / 2, b, fill=fill)
    for o in ops:
        draw_opening(g, w, o, horiz, c, t)


def draw_opening(g, w, o, horiz, c, t):
    a, b, kind = o["s"], o["e"], o["kind"]

    def P(u, n):  # wall-local -> plan
        return (u, n) if horiz else (n, u)

    if kind in ("window", "jaali", "vent", "jharokha"):
        for off in (-t / 2, -t / 6, t / 6, t / 2):
            x0, y0 = P(a, c + off)
            x1, y1 = P(b, c + off)
            g.line(x0, y0, x1, y1, stroke=INK, sw=0.8)
        if kind == "jharokha" and w["out"]:
            s = 1 if w["out"][0] == "+" else -1
            n0, n1 = c + s * t / 2, c + s * (t / 2 + 1.75)
            pts = [P(a - 0.5, n0), P(a - 0.5, n1), P(b + 0.5, n1), P(b + 0.5, n0)]
            d = "M " + " L ".join(f"{X(x):.1f} {Y(y):.1f}" for x, y in pts)
            g.path(d, stroke=INK, sw=1.2, dash="5 3")
            mx, my = P((a + b) / 2, c + s * (t / 2 + 0.9))
            g.text(mx, my, "jharokha", 9, fill=MUTED)
    elif kind in ("door", "door_main", "door_glass"):
        sw = 1 if o["swing"] == "+" else -1
        r = b - a
        if kind == "door_main" or kind == "door_glass":
            # double leaf
            hr = r / 2
            for hinge, sgn in ((a, 1), (b, -1)):
                hx, hy = P(hinge, c + sw * t / 2)
                ex, ey = P(hinge, c + sw * (t / 2 + hr))
                g.line(hx, hy, ex, ey, sw=1.2)
                fx, fy = P(hinge + sgn * hr, c + sw * t / 2)
                g.path(f"M {X(ex):.1f} {Y(ey):.1f} A {hr * S:.1f} {hr * S:.1f} 0 0 "
                       f"{arc_flag(horiz, sw, sgn)} {X(fx):.1f} {Y(fy):.1f}", stroke=MUTED, sw=0.8)
        else:
            hx, hy = P(a, c + sw * t / 2)
            ex, ey = P(a, c + sw * (t / 2 + r))
            g.line(hx, hy, ex, ey, sw=1.4)
            fx, fy = P(b, c + sw * t / 2)
            g.path(f"M {X(ex):.1f} {Y(ey):.1f} A {r * S:.1f} {r * S:.1f} 0 0 {arc_flag(horiz, sw, 1)} "
                   f"{X(fx):.1f} {Y(fy):.1f}", stroke=MUTED, sw=0.8)
    elif kind == "arch_open":
        for off in (-t / 2, t / 2):
            x0, y0 = P(a, c + off)
            x1, y1 = P(b, c + off)
            g.line(x0, y0, x1, y1, stroke=MUTED, sw=0.8, dash="4 3")


def arc_flag(horiz, sw, sgn):
    # SVG y is flipped; work out sweep so the arc bows away from the wall
    f = 1 if sw * sgn > 0 else 0
    return f if horiz else 1 - f


def dim_h(g, x0, x1, y, label=None, off=0):
    yy = y
    g.line(x0, yy, x1, yy, stroke=INK, sw=0.8)
    for x in (x0, x1):
        g.add(f'<line x1="{X(x) - 4:.1f}" y1="{Y(yy) + 4:.1f}" x2="{X(x) + 4:.1f}" y2="{Y(yy) - 4:.1f}" '
              f'stroke="{INK}" stroke-width="1.2"/>')
        g.line(x, yy - 0.5, x, yy + 0.5, stroke=INK, sw=0.6)
    g.text((x0 + x1) / 2, yy, f'<tspan dy="-9">{label or ftin(x1 - x0)}</tspan>', 11)


def dim_v(g, y0, y1, x, label=None):
    g.line(x, y0, x, y1, stroke=INK, sw=0.8)
    for y in (y0, y1):
        g.add(f'<line x1="{X(x) - 4:.1f}" y1="{Y(y) + 4:.1f}" x2="{X(x) + 4:.1f}" y2="{Y(y) - 4:.1f}" '
              f'stroke="{INK}" stroke-width="1.2"/>')
        g.line(x - 0.5, y, x + 0.5, y, stroke=INK, sw=0.6)
    tx, ty = X(x) - 9, Y((y0 + y1) / 2)
    g.text(tx, ty, label or ftin(y1 - y0), 11, rot=-90, px=True)


def north_and_road(g):
    # road strip & arrow
    g.add(f'<rect x="{X(-3):.1f}" y="{Y(46.0):.1f}" width="{36 * S:.1f}" height="{2.2 * S:.1f}" fill="#d9d4cc"/>')
    g.text(15, 44.9, "ROAD  (north side)", 12, 700, MUTED)
    ax, ay = X(33.6), Y(37.0)
    g.add(f'<g transform="translate({ax:.1f} {ay:.1f})"><circle r="16" fill="none" stroke="{INK}"/>'
          f'<path d="M0 -14 L6 6 L0 2 L-6 6 Z" fill="{INK}"/><text y="-22" font-size="12" font-weight="700" '
          f'text-anchor="middle" fill="{INK}">N</text></g>')


def furniture(g, level):
    for lvl, kind, (x0, y0, x1, y1), extra in L.FURNITURE:
        if lvl != level:
            continue
        if kind == "car":
            g.rect(x0, y0, x1, y1, fill="none", stroke=FURN, sw=1, rx=10)
            g.rect(x0 + 0.6, y0 + 3.0, x1 - 0.6, y1 - 4.5, fill="none", stroke=FURN, sw=0.8, rx=4)
        elif kind == "scooter":
            g.rect(x0, y0 + 0.5, x1, y1 - 0.5, fill="none", stroke=FURN, sw=0.8, rx=5)
        elif kind == "bed":
            g.rect(x0, y0, x1, y1, fill="#fff", stroke=FURN, sw=1)
            if extra.get("head") == "-x":
                g.rect(x0 + 0.4, y0 + 0.4, x0 + 1.6, y1 - 0.4, fill="none", stroke=FURN, sw=0.8)
            else:
                g.rect(x1 - 1.6, y0 + 0.4, x1 - 0.4, y1 - 0.4, fill="none", stroke=FURN, sw=0.8)
        elif kind in ("wc", "basin"):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            r = min(x1 - x0, y1 - y0) / 2 * 0.8
            g.add(f'<ellipse cx="{X(cx):.1f}" cy="{Y(cy):.1f}" rx="{r * S:.1f}" ry="{r * S * 0.85:.1f}" '
                  f'fill="#fff" stroke="{FURN}"/>')
        elif kind == "shower":
            g.rect(x0, y0, x1, y1, fill="none", stroke=FURN, sw=0.8, dash="3 2")
            g.line(x0, y0, x1, y1, stroke=FURN, sw=0.6)
            g.line(x0, y1, x1, y0, stroke=FURN, sw=0.6)
        elif kind in ("table", "plant"):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            g.add(f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="{(x1 - x0) / 2 * S:.1f}" fill="none" '
                  f'stroke="{FURN}"/>')
        elif kind in ("water_tank",):
            continue
        else:
            g.rect(x0, y0, x1, y1, fill="none", stroke=FURN, sw=0.9)


def room_labels(g, level, extra=None):
    for lvl, name, (x0, y0, x1, y1), fin in L.ROOMS:
        if lvl != level or name in ("Stair",):
            continue
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        dims = f"{ftin(x1 - x0)} x {ftin(y1 - y0)}"
        pos = (extra or {}).get(name)
        if pos:
            cx, cy = pos[0], pos[1]
            if len(pos) > 2:
                dims = pos[2]
        size = 12 if "Bath" not in name and "Kitchen" not in name else 10
        g.text(cx, cy, name.upper(), size, 700)
        g.text(cx, cy - 0.85 * (size / 12), dims, size - 2, 400, MUTED)


def stairs(g, base_label="UP"):
    S_ = L.STAIR
    ix0, iy0, ix1, iy1 = S_["inner"]
    yl, ym = S_["floor_landing_y"], S_["mid_landing_y"]
    for (x0, x1) in (S_["west_flight"], S_["east_flight"]):
        for i in range(10):
            y = ym + i * L.TREAD
            g.line(x0, y, x1, y, stroke=INK, sw=0.7)
    g.rect(S_["west_flight"][1], ym, S_["east_flight"][0], yl, fill=WALL)
    # arrow: up flight 1 (south) then flight 2 (north)
    xa = sum(S_["west_flight"]) / 2
    xb = sum(S_["east_flight"]) / 2
    pts = [(xa, yl + 1.2), (xa, ym - 1.6), (xb, ym - 1.6), (xb, yl - 0.4)]
    d = "M " + " L ".join(f"{X(x):.1f} {Y(y):.1f}" for x, y in pts)
    g.path(d, stroke=PINK, sw=1.6)
    ex, ey = X(xb), Y(yl - 0.4)
    g.add(f'<path d="M {ex - 5:.1f} {ey + 8:.1f} L {ex:.1f} {ey:.1f} L {ex + 5:.1f} {ey + 8:.1f}" fill="none" '
          f'stroke="{PINK}" stroke-width="1.6"/>')
    g.text(xa, yl + 1.9, base_label, 10, 700, PINK)


def overall_dims(g):
    dim_h(g, 0, 30, -3.6)
    dim_v(g, 0, 40, -2.2)


def ground():
    g = SVG()
    north_and_road(g)
    g.rect(0, 0, 30, 40, fill="#f1ece4", stroke=MUTED, sw=1, dash="6 4")
    # bays
    for lvl, name, (x0, y0, x1, y1), _ in L.ROOMS:
        if lvl == "GF" and name.startswith("Car"):
            g.rect(x0 + 0.5, y0, x1 - 0.5, y1 - 0.3, fill="none", stroke="#c9bfb2", sw=1, dash="6 4")
    furniture(g, "GF")
    for w in L.WALLS:
        if w["level"] == "GF":
            draw_wall(g, w, WALL if w["top"] > L.GF + 5 else "#7c6a5e")
    for (x, y) in L.COLUMNS:
        g.rect(x - 0.5, y - 0.5, x + 0.5, y + 0.5, fill=WALL)
    stairs(g, "UP")
    labels = {
        "Car bay A": (5.75, 31.8, "car 1"), "Car bay B": (16.5, 31.8, "car 2"),
        "Car bay C": (6.0, 11.0, "car 3 (tandem)"), "Car bay D": (19.25, 11.0, "car 4 (tandem, optional)"),
        "Two-wheelers": (26.3, 15.4, "4-6 bikes"), "Utility / sump": (26.3, 22.9, "meter, pump"),
    }
    room_labels(g, "GF", labels)
    g.text(26.0, 34.2, "STAIR", 11, 700)
    g.text(24.2, 40.8, "entry", 10, 400, PINK)
    # ramp
    g.rect(0, 40, 30, 43.0, fill="none", stroke=MUTED, sw=0.8, dash="2 3")
    g.text(11, 41.5, "ramp 1:4 (plinth +1'-0\")", 9, 400, MUTED)
    overall_dims(g)
    dim_h(g, 0, 11, -1.6, "11'-0\" c/c")
    dim_h(g, 11, 22, -1.6, "11'-0\" c/c")
    dim_h(g, 22, 30, -1.6, "8'-0\"")
    g.save(os.path.join(OUT, "ground_floor.svg"), "Ground floor (stilt parking)",
           "Open stilt with 4' screen walls + jaali; 2 cars at the front, 2 tandem behind, bikes along the east "
           "side. Dog-leg stair entered directly from the road.")


def first():
    g = SVG()
    north_and_road(g)
    g.rect(0, 0, 30, 40, fill="#fff", stroke="none")
    for lvl, name, (x0, y0, x1, y1), fin in L.ROOMS:
        if lvl == "FF" and fin == "tile":
            g.rect(x0, y0, x1, y1, fill="#eef0f0")
        if lvl == "FF" and name.startswith("Sit-out"):
            g.rect(x0, y0, x1, y1, fill="#f7efe4")
    furniture(g, "FF")
    for w in L.WALLS:
        if w["level"] == "FF":
            draw_wall(g, w)
    A = L.ARCADE
    for px in A["piers"]:
        g.rect(max(0, px - 0.375), 0, min(30, px + 0.375), 0.75, fill=WALL)
    for pa, pb in zip(A["piers"], A["piers"][1:]):
        g.rect(pa + 0.375, 0.15, pb - 0.375, 0.6, fill="none", stroke=INK, sw=0.6)
    stairs(g, "UP / DN")
    labels = {
        "Room 1": (5.6, 32.0, "12'-0\" x 15'-0\""), "Bath 1": (14.5, 30.8, "5' x 7'"),
        "Kitchenette": (14.6, 35.6, "5' x 8'"), "Lobby": (19.5, 33.0, "5' x 15'"),
        "Corridor": (5.0, 23.0, "4'-0\" wide"), "Room 2": (5.0, 9.5, "15' x 17' (less bath)"),
        "Room 3": (25.0, 9.5, "15' x 17' (less bath)"), "Bath 2": (2.6, 17.2, "5' x 8'"),
        "Bath 3": (27.4, 17.2, "5' x 8'"), "Sit-out 2": (11.6, 2.2, "15' x 4'"),
        "Sit-out 3": (18.4, 2.2, "15' x 4'"),
    }
    room_labels(g, "FF", labels)
    g.text(26.0, 33.6, "STAIR", 11, 700)
    overall_dims(g)
    for (a, b) in ((0, 12), (12, 17), (17, 22), (22, 30)):
        dim_h(g, a, b, 42.7)
    for (a, b) in ((0, 15), (15, 30)):
        dim_h(g, a, b, -1.6)
    for (a, b) in ((0, 4), (4, 21), (21, 25), (25, 40)):
        dim_v(g, a, b, 32.2)
    g.save(os.path.join(OUT, "first_floor.svg"), "First floor (guest rooms)",
           "3 rooms with attached baths + kitchenette. Room 1 faces the road (jharokha); Rooms 2 & 3 open to "
           "private arcaded sit-outs on the south.")


def roof():
    g = SVG()
    north_and_road(g)
    g.rect(0, 0, 30, 40, fill="#f3e3d9")
    for w in L.WALLS:
        if w["level"] == "ROOF":
            draw_wall(g, w)
    for (x0, y0, s) in L.CHHATRIS:
        g.rect(x0, y0, x0 + s, y0 + s, fill="#efe2c8", stroke=INK, sw=1)
        cx, cy = x0 + s / 2, y0 + s / 2
        g.add(f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="{(s / 2 - 0.4) * S:.1f}" fill="none" '
              f'stroke="{INK}"/>')
        g.text(cx, cy, "chhatri", 9, 700)
    for (x, y) in L.COLUMNS:
        if 22 <= x <= 30 and 25 <= y <= 40:
            continue
        if any(x0 - 0.5 <= x <= x0 + s + 0.5 and y0 - 0.5 <= y <= y0 + s + 0.5 for x0, y0, s in L.CHHATRIS):
            continue
        g.rect(x - 0.55, y - 0.55, x + 0.55, y + 0.55, fill="none", stroke=PINK, sw=1.4)
        g.add(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="2.5" fill="{PINK}"/>')
    stairs(g, "DN")
    g.text(26.4, 38.4, "MUMTY", 11, 700)
    g.text(26.4, 37.5, "(water tank on top)", 9, 400, MUTED)
    g.text(11.5, 18.5, "ROOF TERRACE", 13, 700)
    g.text(11.5, 17.4, "= floor of the future 2nd floor (reception + rooms)", 10, 400, MUTED)
    g.text(11.5, 13.0, "pink squares: column stubs with capped starter bars", 10, 400, PINK)
    overall_dims(g)
    g.save(os.path.join(OUT, "roof_plan.svg"), "Roof / terrace",
           "Kangura (crenellated) parapet, three corner chhatris, stair mumty with water tank. Every column "
           "continues up so 2nd/3rd floors can be added.")


OUT = os.path.join(HERE, "..", "output", "plans")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    ground()
    first()
    roof()
    print("plans written to", os.path.abspath(OUT))
