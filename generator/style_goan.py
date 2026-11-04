"""
Portuguese-Goan style for the Puri home-hotel.

Same plan, a Goan-Portuguese skin:
  * ochre-yellow lime walls with white pilasters, cornices and window surrounds
  * tall windows with segmental heads and keystones, oyster-shell panes, and
    teal-blue shutters folded back against the wall
  * wrought-iron balconies with French doors on the road side
  * white Tuscan columns and round arches in the stilt parking
  * an entrance with a teal panelled door, fanlight, Baroque pediment and an
    azulejo (blue-and-white tile) name panel
  * a balcão-style rear sit-out: Tuscan columns, round arches, built-in seats
  * Baroque gable crest and obelisk pinnacles on the parapet, a Mangalore-tile
    hip roof on the stair mumty, a white pergola with bougainvillea on the terrace
  * black-and-white chequered floors inside
"""
import math

import bpy  # noqa: F401  (bpy must be imported before bmesh)
import bmesh

import build_model as BM
from build_model import Builder, F

L = BM.L


class GoanBuilder(Builder):
    STYLE = "goan"
    CHHATRIS = []
    PALETTE = {
        "WallPink": ("#E0A43A", 0.75, 0.0, dict(noise=0.07, bump=0.06)),    # Goan ochre yellow
        "Trim": ("#F8F5EE", 0.6, 0.0, dict(noise=0.03)),                    # white lime trim
        "Sandstone": ("#D9D2C3", 0.7, 0.0, dict(noise=0.08)),               # laterite plastered white-grey
        "Wood": ("#5B3A22", 0.5, 0.0, dict(noise=0.15)),                    # rosewood
        "Plaster": ("#F5F1E8", 0.55, 0.0, dict(noise=0.03)),
        "FloorStone": ("#EDEAE3", 0.2, 0.0, dict(checker="#262626", checker_scale=3.3)),
        "RoofTile": ("#A9573C", 0.9, 0.0, dict(noise=0.12)),
        "Blue": ("#1F6E8C", 0.45, 0.0, {}),                                 # painted doors / shutters
        "Oyster": ("#EEE5CC", 0.35, 0.0, dict(noise=0.1)),                  # oyster-shell panes
        "Iron": ("#1C2424", 0.45, 0.4, {}),
        "Azulejo": ("#F3F1EA", 0.2, 0.0, dict(checker="#2753A0", checker_scale=14.0)),
        "Mangalore": ("#B4532F", 0.85, 0.0, dict(noise=0.2, bump=0.35)),
        "Bougainvillea": ("#C2257A", 0.8, 0.0, dict(noise=0.25)),
    }

    # ---------------------------------------------------------- helpers
    def tuscan(self, x, y, z0, z1, r=0.45, mat="Trim"):
        """White Tuscan column with square plinth and capital."""
        self.box(x - r - 0.2, y - r - 0.2, z0, x + r + 0.2, y + r + 0.2, z0 + 0.45, mat, "col_plinth")
        h = z1 - z0 - 0.45 - 0.6
        prof = [(r * 1.15, 0), (r * 1.1, 0.12), (r, 0.25), (r, h * 0.3), (r * 0.88, h)]
        self.revolve(prof, x, y, z0 + 0.45, mat, 20, name="tuscan_shaft")
        zc = z0 + 0.45 + h
        self.revolve([(r * 0.88, 0), (r * 1.15, 0.25), (r * 1.15, 0.3)], x, y, zc, mat, 20, name="echinus")
        self.box(x - r - 0.18, y - r - 0.18, zc + 0.3, x + r + 0.18, y + r + 0.18, z1, mat, "abacus")

    def pinnacle(self, cx, cy, z0, s=1.0):
        """Obelisk pinnacle with a ball finial (Goan parapet corners)."""
        self.box(cx - 0.45 * s, cy - 0.45 * s, z0, cx + 0.45 * s, cy + 0.45 * s, z0 + 0.5 * s, "Trim", "pin_base")
        self.revolve([(0.45 * s, 0), (0.12 * s, 2.0 * s)], cx, cy, z0 + 0.5 * s, "Trim", 4, name="obelisk",
                     rot=math.pi / 4)
        self.sphere(cx, cy, z0 + 2.65 * s, 0.22 * s, "Trim", 2)

    def keystone(self, axis, face, s, u, z):
        lo, hi = sorted((face, face + s * 0.14))
        self._wprism(axis, [(u - 0.22, z - 0.35), (u + 0.22, z - 0.35), (u + 0.3, z + 0.25), (u - 0.3, z + 0.25)],
                     lo, hi, "Trim", "keystone")

    def oyster_grid(self, axis, c, a, b, z0, z1, mat="Oyster"):
        """Oyster-shell window panes in a fine timber grid."""
        self._wbox(axis, c - 0.04, c + 0.04, a, b, z0, z1, mat, "oyster")
        u = a + 0.32
        while u < b - 0.1:
            self._wbox(axis, c - 0.07, c + 0.07, u - 0.03, u + 0.03, z0, z1, "Wood", "muntin")
            u += 0.32
        z = z0 + 0.32
        while z < z1 - 0.1:
            self._wbox(axis, c - 0.07, c + 0.07, a, b, z - 0.03, z + 0.03, "Wood", "muntin")
            z += 0.32

    # ------------------------------------------------------------ stilt
    def stilt_column(self, x, y):
        self.tuscan(x, y, L.GF, L.GF_TOP - L.BEAM_D, r=0.5)

    def spandrel(self, axis, c, t, a, b, spring, top, cusped=True, mat="WallPink", name="round_arch"):
        """Plain round (semicircular-ish) arch - no cusps."""
        m = "Plaster" if mat == "Plaster" else "WallPink"
        return Builder.spandrel(self, axis, c, t, a, b, spring, top, False, m, name)

    def arch_trim(self, axis, face, outsign, a, b, spring, rise, width=0.3, proud=0.08, mat="Trim"):
        Builder.arch_trim(self, axis, face, outsign, a, b, spring, rise, width, proud, "Trim")
        self.keystone(axis, face, outsign, (a + b) / 2, spring + rise + 0.15)

    # --------------------------------------------------------- openings
    def opening(self, axis, c, t, s, face, o, base):
        a, b, kind = o["s"], o["e"], o["kind"]
        sill = base + o["sill"]
        head = base + o["head"]
        ext = s != 0
        if kind in ("window", "jharokha"):
            french = kind == "jharokha"
            if french:
                sill = base + 0.0 + o["sill"]
            rise = 0.55
            self.spandrel(axis, c, t, a, b, head - rise - 0.15, head, mat="WallPink" if ext else "Plaster")
            fan = head - rise - 0.15
            # frame, fanlight and sashes
            fr = 0.14
            for (p, q) in ((a, a + fr), (b - fr, b)):
                self._wbox(axis, c - 0.12, c + 0.12, p, q, sill, fan, "Blue" if french else "Wood", "frame")
            self._wbox(axis, c - 0.12, c + 0.12, a, b, fan - 0.12, fan, "Wood", "transom")
            self.oyster_grid(axis, c, a + fr, b - fr, fan, head)
            if french:
                mid = (a + b) / 2
                for (p, q) in ((a + fr, mid - 0.02), (mid + 0.02, b - fr)):
                    self._wbox(axis, c - 0.05, c + 0.05, p, q, sill, fan - 0.12, "Blue", "french_leaf")
                    self.oyster_grid(axis, c + (s or 1) * 0.07, p + 0.15, q - 0.15, sill + 2.2, fan - 0.3)
                    for zz in (sill + 0.6, sill + 1.6):
                        lo, hi = sorted((c, c + (s or 1) * 0.1))
                        self._wbox(axis, lo, hi, p + 0.2, q - 0.2, zz - 0.35, zz + 0.35, "Blue", "panel")
            else:
                self.oyster_grid(axis, c, a + fr, b - fr, sill + fr, fan - 0.12)
                self._wbox(axis, c - 0.1, c + 0.1, a, b, sill, sill + fr, "Wood", "sill_rail")
                self._wbox(axis, c - 0.09, c + 0.09, (a + b) / 2 - 0.05, (a + b) / 2 + 0.05, sill, fan, "Wood",
                           "meeting_rail")
            if ext:
                self.surround(axis, face, s, a, b, sill, head, rise)
                if not french:
                    self.open_shutters(axis, face, s, a, b, sill + 0.15, fan - 0.1)
                else:
                    self.iron_balcony(axis, face, s, a, b, sill)
        elif kind == "vent":
            self.oyster_grid(axis, c, a, b, sill, head)
            if ext:
                self.surround(axis, face, s, a, b, sill, head, 0)
        elif kind == "jaali":
            self.jaali(axis, c, a, b, sill, head, t=0.2)
            if ext:
                self.surround(axis, face, s, a, b, sill, head, 0)
        elif kind == "door_glass":
            mid = (a + b) / 2
            fan = head - 1.0
            self._wbox(axis, c - 0.12, c + 0.12, a, b, fan - 0.12, fan, "Wood")
            self.oyster_grid(axis, c, a + 0.14, b - 0.14, fan, head)
            for (p, q) in ((a, mid - 0.02), (mid + 0.02, b)):
                self._wbox(axis, c - 0.05, c + 0.05, p, q, sill, fan - 0.12, "Blue", "door_leaf")
                self.oyster_grid(axis, c + 0.07, p + 0.15, q - 0.15, sill + 2.4, fan - 0.3)
        elif kind == "door_main":
            self.main_door(axis, c, t, s, face, a, b, sill, head)
        elif kind in ("door", "arch_open"):
            w = 0.18
            for (p, q) in ((a, a + w), (b - w, b)):
                self._wbox(axis, c - t / 2 - 0.04, c + t / 2 + 0.04, p, q, base, head, "Wood", "frame")
            self._wbox(axis, c - t / 2 - 0.04, c + t / 2 + 0.04, a, b, head - w, head, "Wood", "frame")

    def surround(self, axis, face, s, a, b, sill, head, rise):
        n0, n1 = sorted((face, face + s * 0.1))
        w = 0.35
        jt = head - rise - 0.15 if rise else head
        self._wbox(axis, n0, n1, a - w, a, sill - 0.1, jt, "Trim", "surround")
        self._wbox(axis, n0, n1, b, b + w, sill - 0.1, jt, "Trim", "surround")
        if rise:
            Builder.arch_trim(self, axis, face, s, a, b, jt, rise, w, 0.1, "Trim")
            self.keystone(axis, face, s, (a + b) / 2, jt + rise + 0.2)
        else:
            self._wbox(axis, n0, n1, a - w, b + w, head, head + w, "Trim", "surround")
        lo, hi = sorted((face, face + s * 0.3))
        self._wbox(axis, lo, hi, a - w - 0.2, b + w + 0.2, sill - 0.32, sill - 0.08, "Trim", "sill")
        for u in (a + 0.1, b - 0.1):    # small sill corbels
            self._nprism(axis, [(face, sill - 0.32), (face + s * 0.25, sill - 0.32), (face, sill - 0.75)],
                         u - 0.12, u + 0.12, "Trim", "sill_corbel")

    def open_shutters(self, axis, face, s, a, b, z0, z1):
        """Teal-blue louvred shutters folded back flat against the wall."""
        w = (b - a) / 2
        for (p, q) in ((a - 0.4 - w, a - 0.4), (b + 0.4, b + 0.4 + w)):
            lo, hi = sorted((face + s * 0.02, face + s * 0.12))
            self._wbox(axis, lo, hi, p, q, z0, z1, "Blue", "shutter")
            lo2, hi2 = sorted((face + s * 0.12, face + s * 0.16))
            z = z0 + 0.3
            while z < z1 - 0.2:
                self._wbox(axis, lo2, hi2, p + 0.12, q - 0.12, z, z + 0.06, "Blue", "louvre")
                z += 0.22

    def iron_balcony(self, axis, face, s, a, b, sill):
        D = 1.6
        N = lambda d: face + s * d  # noqa: E731
        ua, ub = a - 0.7, b + 0.7
        lo, hi = sorted((N(0), N(D)))
        self._wbox(axis, lo, hi, ua, ub, sill - 0.35, sill, "Trim", "balcony_slab")
        lo2, hi2 = sorted((N(0), N(D + 0.12)))
        self._wbox(axis, lo2, hi2, ua - 0.1, ub + 0.1, sill - 0.5, sill - 0.35, "Trim", "balcony_moulding")
        for u in (ua + 0.3, (ua + ub) / 2, ub - 0.3):
            self._nprism(axis, [(N(0), sill - 0.5), (N(D - 0.1), sill - 0.5), (N(0), sill - 1.7)],
                         u - 0.15, u + 0.15, "Trim", "balcony_corbel")
        top = sill + 3.0
        # rails
        for (n_a, n_b, u_a, u_b) in ((N(D - 0.1), N(D - 0.04), ua, ub),):
            lo3, hi3 = sorted((n_a, n_b))
            for zz in (sill + 0.25, sill + 2.3, top):
                self._wbox(axis, lo3, hi3, u_a, u_b, zz - 0.04, zz + 0.04, "Iron", "rail")
        for uu in (ua + 0.05, ub - 0.05):
            for zz in (sill + 0.25, top):
                lo4, hi4 = sorted((N(0), N(D)))
                self._wbox(axis, lo4, hi4, uu - 0.04, uu + 0.04, zz - 0.04, zz + 0.04, "Iron", "rail")
        u = ua + 0.2
        while u < ub - 0.1:
            cx, cy = (u, N(D - 0.07)) if axis == "x" else (N(D - 0.07), u)
            self.cyl(cx, cy, sill, top, 0.025, "Iron", 6, "baluster")
            u += 0.3
        # scroll band (rings) between the upper rails
        u = ua + 0.35
        while u < ub - 0.2:
            pts = [(u + 0.22 * math.cos(2 * math.pi * k / 12), sill + 2.65 + 0.22 * math.sin(2 * math.pi * k / 12))
                   for k in range(12)]
            lo5, hi5 = sorted((N(D - 0.09), N(D - 0.05)))
            self._wprism(axis, pts, lo5, hi5, "Iron", "scroll")
            u += 0.55
        for uu in (ua + 0.05, ub - 0.05):
            d = 0.3
            while d < D - 0.1:
                cx, cy = (uu, N(d)) if axis == "x" else (N(d), uu)
                self.cyl(cx, cy, sill, top, 0.025, "Iron", 6, "baluster")
                d += 0.3

    def jaali(self, axis, c, a, b, z0, z1, t=0.2, mat="Iron", step=0.3, bar=0.07):
        """Simple wrought-iron grille in a white frame."""
        h = t / 2
        for (p, q, za, zb) in ((a, a + 0.12, z0, z1), (b - 0.12, b, z0, z1), (a, b, z0, z0 + 0.12),
                               (a, b, z1 - 0.12, z1)):
            self._wbox(axis, c - h, c + h, p, q, za, zb, "Trim")
        u = a + 0.12 + step / 2
        while u < b - 0.12:
            cx, cy = (u, c) if axis == "x" else (c, u)
            self.cyl(cx, cy, z0 + 0.12, z1 - 0.12, 0.03, "Iron", 6, "grille")
            u += step

    def main_door(self, axis, c, t, s, face, a, b, sill, head):
        mid = (a + b) / 2
        fan = head - 1.0
        # leaves with raised panels
        for (p, q) in ((a, mid - 0.02), (mid + 0.02, b)):
            self._wbox(axis, c - 0.1, c + 0.1, p, q, sill, fan, "Blue", "door_leaf")
            out = c + 0.1 * (s or 1)
            for zz in (sill + 1.0, sill + 3.0, sill + 5.0):
                lo, hi = sorted((out, out + (s or 1) * 0.06))
                self._wbox(axis, lo, hi, p + 0.2, q - 0.2, zz - 0.7, zz + 0.7, "Blue", "door_panel")
            lo, hi = sorted((out, out + (s or 1) * 0.1))
            self._wbox(axis, lo, hi, q - 0.3 if p < mid else p + 0.2, q - 0.2 if p < mid else p + 0.3,
                       sill + 3.2, sill + 3.5, "Gold", "handle")
        self._wbox(axis, c - 0.12, c + 0.12, a, b, fan - 0.1, fan, "Wood")
        self.spandrel(axis, c, t, a, b, fan, head)
        self.oyster_grid(axis, c, a, b, fan, head)
        if not s:
            return
        # pilasters + entablature + broken Baroque pediment
        n0, n1 = sorted((face, face + s * 0.18))
        for u in (a - 0.6, b + 0.1):
            self._wbox(axis, n0, n1, u, u + 0.5, sill, head + 0.3, "Trim", "door_pilaster")
            lo, hi = sorted((face, face + s * 0.25))
            self._wbox(axis, lo, hi, u - 0.08, u + 0.58, head + 0.3, head + 0.5, "Trim", "pilaster_cap")
        lo, hi = sorted((face, face + s * 0.3))
        self._wbox(axis, lo, hi, a - 0.7, b + 0.7, head + 0.5, head + 0.75, "Trim", "door_entablature")
        cu = (a + b) / 2
        hw = (b - a) / 2 + 0.7
        z = head + 0.75
        pts = [(cu - hw, z), (cu + hw, z)]
        for k in range(0, 9):          # S-curve up to the centre on the right
            tt = k / 8
            pts.append((cu + hw - (hw - 0.45) * tt, z + 0.25 + 0.55 * (3 * tt ** 2 - 2 * tt ** 3)))
        pts += [(cu, z + 0.95)]
        for k in range(8, -1, -1):
            tt = k / 8
            pts.append((cu - hw + (hw - 0.45) * tt, z + 0.25 + 0.55 * (3 * tt ** 2 - 2 * tt ** 3)))
        self._wprism(axis, pts, lo, hi, "Trim", "door_pediment")
        self.keystone(axis, face, s, cu, fan + 0.6)

    # ------------------------------------------------------- roof edges
    def chhajja(self, axis, face, s, u0, u1, z, proj=1.4, brackets=True, mat="Trim"):
        """Classical white cornice with dentils."""
        p = min(proj, 1.0)
        pts = [(face, z), (face + s * p * 0.35, z), (face + s * p * 0.35, z + 0.18), (face + s * p * 0.7, z + 0.18),
               (face + s * p * 0.7, z + 0.36), (face + s * p, z + 0.36), (face + s * p, z + 0.6), (face, z + 0.6)]
        self._nprism(axis, pts, u0, u1, "Trim", "cornice")
        u = u0 + 0.2
        while u < u1 - 0.2:
            lo, hi = sorted((face + s * p * 0.35, face + s * p * 0.55))
            self._wbox(axis, lo, hi, u, u + 0.18, z - 0.0, z + 0.18, "Trim", "dentil")
            u += 0.42

    def kangura(self, axis, c, t, u0, u1, ztop, mat="Trim", pitch=1.5):
        """Parapet: white moulded coping, pilasters with obelisk pinnacles."""
        self._wbox(axis, c - t / 2 - 0.12, c + t / 2 + 0.12, u0, u1, ztop, ztop + 0.25, "Trim", "coping")
        n = max(1, int(round((u1 - u0) / 7.0)))
        for i in range(n + 1):
            u = u0 + 0.45 + (u1 - u0 - 0.9) * i / n
            self._wbox(axis, c - t / 2 - 0.12, c + t / 2 + 0.12, u - 0.45, u + 0.45, ztop - L.PARAPET_H, ztop + 0.25,
                       "Trim", "parapet_pilaster")
            cx, cy = (u, c) if axis == "x" else (c, u)
            self.pinnacle(cx, cy, ztop + 0.25, 0.9)

    def _band(self, z0, z1):
        p = 0.15
        for (a, b, c_, d) in ((-p, 39.99, 30 + p, 40 + p), (-p, -p, 30 + p, 0.01), (-p, 0, 0.01, 40),
                              (29.99, 0, 30 + p, 40)):
            self.box(a, b, z0, c_, d, z1, "Trim", "string_course")

    # ---------------------------------------------------------- arcade
    def arcade(self):
        A = L.ARCADE
        y, t, base, top = A["y"], A["t"], A["base"], A["top"]
        spring = base + 6.6
        crown = base + 8.6
        for px in A["piers"]:
            x = min(max(px, 0.55), 29.45)
            self.tuscan(x, 0.45, base, spring, r=0.38)
        for pa, pb in zip(A["piers"], A["piers"][1:]):
            a, b = max(pa, 0.55) + 0.5, min(pb, 29.45) - 0.5
            Builder.spandrel(self, "x", 0.4, 0.8, a - 0.1, b + 0.1, spring, crown, False, "WallPink", "balcao_arch")
            Builder.arch_trim(self, "x", 0.0, -1, a - 0.1, b + 0.1, spring, crown - spring - 0.15, 0.3, 0.08, "Trim")
            # balcão: built-in seat with a low back and a short iron railing above
            self.box(a, 0.15, base, b, 0.75, base + 1.6, "WallPink", "seat_wall")
            self.box(a, 0.15, base + 1.6, b, 1.6, base + 1.78, "Trim", "seat_top")
            self.box(a, 0.75, base, b, 1.6, base + 1.6, "WallPink", "seat_body")
            u = a + 0.15
            while u < b - 0.05:
                self.cyl(u, 0.45, base + 1.78, base + 3.1, 0.025, "Iron", 6, "rail_bar")
                u += 0.3
            self.box(a, 0.4, base + 3.05, b, 0.5, base + 3.15, "Iron", "rail_top")
        self.box(0.0, 0.0, crown, 30.0, 0.8, top, "WallPink", "balcao_wall")

    # -------------------------------------------------------- mumty top
    def mumty_top(self, mz):
        x0, y0, x1, y1, z, h = 20.6, 23.6, 30.8, 40.8, mz + 0.5, 3.6
        bm = bmesh.new()
        V = lambda x, y, zz: bm.verts.new((x * F, y * F, zz * F))  # noqa: E731
        b = [V(x0, y0, z), V(x1, y0, z), V(x1, y1, z), V(x0, y1, z)]
        w = x1 - x0
        r0 = V((x0 + x1) / 2, y0 + w / 2, z + h)
        r1 = V((x0 + x1) / 2, y1 - w / 2, z + h)
        for f in ((b[0], b[1], r0), (b[1], b[2], r1, r0), (b[2], b[3], r1), (b[3], b[0], r0, r1)):
            bm.faces.new(f)
        bm.faces.new(b[::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self._obj("mumty_roof", bm, "Mangalore")
        for (a0, b0, a1, b1) in ((x0, y0, x1, y0 + 0.12), (x0, y1 - 0.12, x1, y1), (x0, y0, x0 + 0.12, y1),
                                 (x1 - 0.12, y0, x1, y1)):
            self.box(a0, b0, z - 0.35, a1, b1, z + 0.02, "Trim", "roof_fascia")

    # ---------------------------------------------------------- extras
    def extras(self):
        self.coll("ROOF")
        self.baroque_crest()
        self.pergola()
        self.coll("FF")
        self.pilasters()
        self.coll("GF")
        self.azulejo_panel()

    def pilasters(self):
        """White pilasters framing the bays of the road and rear facades."""
        z0, z1 = L.FF, L.FF_TOP
        for x in (0.0, 10.6, 16.6, 22.4, 29.1):
            for (ya, yb, cap) in ((40.0, 40.14, 40.25), (-0.14, 0.0, -0.25)):
                if ya < 0 and x not in (0.0, 29.1):
                    continue
                self.box(x, ya, z0, x + 0.9, yb, z1 - 0.9, "Trim", "pilaster")
                lo, hi = sorted((cap, 40.0 if ya > 1 else 0.0))
                self.box(x - 0.1, lo, z1 - 1.25, x + 1.0, hi, z1 - 0.9, "Trim", "pilaster_cap")
        for y in (0.0, 39.1):
            for (xa, xb) in ((-0.14, 0.0), (30.0, 30.14)):
                self.box(xa, y, z0, xb, y + 0.9, z1 - 0.9, "Trim", "pilaster")

    def baroque_crest(self):
        """Curving Baroque gable crest in the middle of the road-side parapet."""
        z = L.ROOF + L.PARAPET_H + 0.25
        cx, hw = 11.0, 5.2
        pts = [(cx - hw, z), (cx + hw, z)]
        n = 14
        for k in range(n + 1):                       # right half: scroll up to a rounded top
            tt = k / n
            x = cx + hw - (hw - 1.2) * tt
            zz = z + 0.4 + 1.7 * (3 * tt ** 2 - 2 * tt ** 3) + 0.35 * math.sin(math.pi * tt * 2) * (1 - tt)
            pts.append((x, zz))
        for k in range(1, 12):
            ang = math.pi * k / 12
            pts.append((cx + 1.2 * math.cos(ang), z + 2.1 + 0.9 * math.sin(ang)))
        for k in range(n, -1, -1):
            tt = k / n
            x = cx - hw + (hw - 1.2) * tt
            zz = z + 0.4 + 1.7 * (3 * tt ** 2 - 2 * tt ** 3) + 0.35 * math.sin(math.pi * tt * 2) * (1 - tt)
            pts.append((x, zz))
        self.prism(pts, "y", 39.25, 40.1, "WallPink", "crest")
        # white outline + niche with a star medallion
        outline = [(x, zz + 0.25) for x, zz in pts[2:]]
        inner = pts[2:]
        self.prism(outline[:len(outline) // 2 + 1] + inner[:len(inner) // 2 + 1][::-1], "y", 40.1, 40.18,
                   "Trim", "crest_outline_r")
        self.prism(outline[len(outline) // 2:] + inner[len(inner) // 2:][::-1], "y", 40.1, 40.18, "Trim",
                   "crest_outline_l")
        star = []
        for k in range(16):
            r = 0.55 if k % 2 == 0 else 0.25
            a = math.pi / 2 + 2 * math.pi * k / 16
            star.append((cx + r * math.cos(a), z + 1.85 + r * math.sin(a)))
        disc = [(cx + 0.75 * math.cos(2 * math.pi * k / 24), z + 1.85 + 0.75 * math.sin(2 * math.pi * k / 24))
                for k in range(24)]
        self.prism(disc, "y", 40.1, 40.2, "Blue", "crest_disc")
        self.prism(star, "y", 40.2, 40.3, "Trim", "crest_star")
        self.pinnacle(cx, 39.65, z + 3.0, 0.8)

    def pergola(self):
        z = L.ROOF
        x0, y0, x1, y1 = 3.0, 5.0, 14.0, 14.0
        for (px, py) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            self.tuscan(px, py, z, z + 8.0, r=0.35)
        for yy in (y0, y1):
            self.box(x0 - 0.8, yy - 0.25, z + 8.0, x1 + 0.8, yy + 0.25, z + 8.6, "Trim", "pergola_beam")
        x = x0 - 0.5
        while x <= x1 + 0.5:
            self.box(x - 0.12, y0 - 1.0, z + 8.6, x + 0.12, y1 + 1.0, z + 9.0, "Trim", "pergola_rafter")
            x += 1.1
        import random
        rnd = random.Random(7)
        for i in range(14):
            xx = rnd.uniform(x0 - 0.5, x1 + 0.5)
            yy = rnd.choice([rnd.uniform(y0 - 0.8, y0 + 2.0), rnd.uniform(y1 - 2.0, y1 + 0.8)])
            self.sphere(xx, yy, z + 9.2, rnd.uniform(0.7, 1.2), "Bougainvillea" if i % 3 else "Leaf", 2, 0.6)
        for (px, py) in ((x0, y0), (x1, y1)):
            self.revolve([(0.6, 0), (0.8, 1.6)], px + 1.0, py, z, "RoofTile", 16, name="planter")
            self.sphere(px + 1.0, py, z + 2.4, 1.0, "Bougainvillea", 2, 1.2)
        # table + chairs under the pergola
        self.cyl(8.5, 9.5, z + 2.4, z + 2.55, 1.4, "Wood", 24, "table")
        self.cyl(8.5, 9.5, z, z + 2.4, 0.15, "Iron", 8)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            px, py = 8.5 + 2.3 * math.cos(a), 9.5 + 2.3 * math.sin(a)
            self.box(px - 0.7, py - 0.7, z + 1.5, px + 0.7, py + 0.7, z + 1.65, "Wood", "chair")
            for dx in (-0.6, 0.6):
                for dy in (-0.6, 0.6):
                    self.cyl(px + dx, py + dy, z, z + 1.5, 0.05, "Iron", 6)

    def azulejo_panel(self):
        """Blue-and-white tile panel beside the entrance (house name plaque)."""
        x0, x1, z0, z1 = 26.2, 29.0, L.GF + 3.0, L.GF + 6.4
        self.box(x0 - 0.2, 40.0, z0 - 0.2, x1 + 0.2, 40.1, z1 + 0.2, "Trim", "azulejo_frame")
        self.box(x0, 40.1, z0, x1, 40.16, z1, "Azulejo", "azulejo")
        self.box(x0 + 0.3, 40.16, z0 + 0.5, x1 - 0.3, 40.2, z0 + 1.2, "Blue", "name_plate")

    # -------------------------------------------------------- furniture
    def furniture(self, level, kind, rect, extra):
        if kind == "water_tank":
            cx, cy = 26.3, 20.4
            self.box(cx - 2.3, cy - 2.3, L.ROOF, cx + 2.3, cy + 2.3, L.ROOF + 2.5, "WallPink", "tank_stand")
            self.box(cx - 2.4, cy - 2.4, L.ROOF + 2.5, cx + 2.4, cy + 2.4, L.ROOF + 2.7, "Trim")
            self.revolve([(2.0, 0), (2.1, 3.6), (1.2, 4.2), (0.5, 4.3), (0.5, 4.6), (0.0, 4.6)], cx, cy,
                         L.ROOF + 2.7, "Black", 28, name="water_tank")
            return
        if kind == "seat":
            return
        return super().furniture(level, kind, rect, extra)

    def arch_headboard(self, axis, xface, y0, y1, ztop):
        """Rosewood headboard with a plain round top."""
        pts = self.arch_curve(y0 + 0.3, y1 - 0.3, ztop, 1.2, False, 40)
        self.prism(pts, "x", xface - 0.35, xface, "Wood", "headboard_arch")
