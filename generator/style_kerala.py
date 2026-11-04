"""
Kerala (nalukettu-inspired) style for the Puri home-hotel.

Same plan, a new roofscape and skin:
  * a big steep hip-and-gable roof of clay tiles over the whole terrace, on
    wooden posts and a light frame (removable when the 2nd floor is built),
    with lattice "mukhappu" gables and brass "kodi" finials
  * white lime-washed walls with exposed laterite courses, laterite stilt piers
  * wooden "azhi" bar windows under small tile hoods on timber brackets
  * "charupady" (sloped-backrest wooden seat railings) on the rear sit-outs and
    the road-side balconies, each balcony under its own little gable
  * a gabled timber canopy over the entrance, tile skirt roofs at the first floor
  * red-oxide floors and wooden ceilings inside, a tulasi thara on the terrace
"""
import math

import bpy  # noqa: F401  (bpy must be imported before bmesh)
import bmesh

import build_model as BM
from build_model import Builder, F

L = BM.L

# main roof geometry (feet)
ROOF_X0, ROOF_X1 = -2.0, 32.0
ROOF_Y0, ROOF_Y1 = -2.5, 42.5
EAVE_Z = L.ROOF + 8.5
RIDGE_H = 11.0
GABLET = 4.5


class KeralaBuilder(Builder):
    STYLE = "kerala"
    CHHATRIS = []
    PALETTE = {
        "WallPink": ("#F2EDE3", 0.7, 0.0, dict(noise=0.05, bump=0.05)),     # lime wash
        "Trim": ("#9A4A2F", 0.9, 0.0, dict(brick="#6E3624", brick2="#A85636", brick_scale=1.6)),  # laterite
        "Sandstone": ("#6E6862", 0.75, 0.0, dict(noise=0.15, bump=0.3)),    # granite
        "Wood": ("#5A3519", 0.55, 0.0, dict(noise=0.2)),                    # jackwood / teak
        "Plaster": ("#F4F0E8", 0.6, 0.0, dict(noise=0.03)),
        "FloorStone": ("#8C2E22", 0.18, 0.0, dict(noise=0.05)),             # polished red oxide
        "RoofTile": ("#8C2E22", 0.5, 0.0, dict(noise=0.08)),
        "Pavers": ("#7E786F", 0.85, 0.0, dict(noise=0.12, bump=0.15)),
        "KTile": ("#8A3A25", 0.85, 0.0, dict(noise=0.22, bump=0.4)),        # clay roof tiles
        "Laterite": ("#9A4A2F", 0.95, 0.0, dict(brick="#6E3624", brick2="#A85636", brick_scale=1.6)),
        "DarkWood": ("#3B2210", 0.55, 0.0, dict(noise=0.15)),
        "Gold": ("#C9A23A", 0.3, 0.9, {}),                                  # brass
        "Bars": ("#4A2C14", 0.5, 0.0, {}),
    }
    VIEW_OVERRIDES = {
        "hero": dict(loc=(48, 90, 6.0), target=(15, 30, 19.0), lens=26, shift=0.17),
        "street": dict(loc=(-20, 66, 5.6), target=(16, 36, 16.0), lens=24, shift=0.12),
        "aerial": dict(loc=(-52, 100, 82), target=(15, 18, 16)),
        "rear": dict(loc=(64, -60, 30), target=(14, 16, 18)),
    }

    # ---------------------------------------------------------- helpers
    def post(self, x, y, z0, z1, w=0.55, base=True):
        """Square timber post on a granite base with a simple capital."""
        if base:
            self.box(x - w / 2 - 0.2, y - w / 2 - 0.2, z0, x + w / 2 + 0.2, y + w / 2 + 0.2, z0 + 0.5, "Sandstone",
                     "post_base")
            z0 += 0.5
        self.box(x - w / 2, y - w / 2, z0, x + w / 2, y + w / 2, z1 - 0.35, "Wood", "post")
        self.box(x - w / 2 - 0.12, y - w / 2 - 0.12, z1 - 0.35, x + w / 2 + 0.12, y + w / 2 + 0.12, z1, "DarkWood",
                 "post_cap")

    def lattice_triangle(self, axis, c, u0, u1, zb, zt, s, mat="Wood"):
        """Mukhappu: triangular gable face with vertical slats and barge boards."""
        mid = (u0 + u1) / 2
        half = (u1 - u0) / 2
        lo, hi = sorted((c, c + s * 0.06))
        self._wprism(axis, [(u0, zb), (u1, zb), (mid, zt)], lo, hi, "DarkWood", "gable_back")
        lo, hi = sorted((c + s * 0.06, c + s * 0.16))
        u = u0 + 0.35
        while u < u1 - 0.3:
            h = (zt - zb) * (1 - abs(u - mid) / half)
            if h > 0.2:
                self._wbox(axis, lo, hi, u - 0.06, u + 0.06, zb, zb + h, "Wood", "gable_slat")
            u += 0.42
        z = zb + 0.6
        while z < zt - 0.3:
            k = 1 - (z - zb) / (zt - zb)
            self._wbox(axis, lo, hi, mid - half * k, mid + half * k, z - 0.05, z + 0.05, "Wood", "gable_rail")
            z += 1.1
        # barge boards along both slopes
        lo, hi = sorted((c + s * 0.0, c + s * 0.3))
        for sgn in (-1, 1):
            e = u0 if sgn < 0 else u1
            pts = [(e + sgn * 0.3, zb - 0.25), (e + sgn * 0.3, zb + 0.15), (mid, zt + 0.5), (mid, zt + 0.05)]
            self._wprism(axis, pts, lo, hi, "Wood", "barge")
        self._wbox(axis, lo, hi, u0 - 0.2, u1 + 0.2, zb - 0.3, zb, "Wood", "gable_tie")

    def kodi(self, cx, cy, z0, s=1.0):
        """Brass ridge finial."""
        prof = [(0.22, 0), (0.28, 0.2), (0.12, 0.45), (0.2, 0.7), (0.08, 1.0), (0.14, 1.25), (0.05, 1.6),
                (0.0, 2.3)]
        self.revolve([(r * s, z * s) for r, z in prof], cx, cy, z0, "Gold", 12, name="kodi")

    def mini_gable(self, axis, face, s, ua, ub, zb, depth, rise):
        """Small gabled tile roof projecting from a wall, ridge perpendicular to it."""
        mid = (ua + ub) / 2
        n0, n1 = sorted((face, face + s * depth))
        self._wprism(axis, [(ua - 0.5, zb), (ub + 0.5, zb), (ub + 0.5, zb + 0.18), (mid, zb + rise + 0.18),
                            (ua - 0.5, zb + 0.18)], n0, n1, "KTile", "mini_gable")
        self.lattice_triangle(axis, face + s * (depth - 0.4), ua - 0.1, ub + 0.1, zb, zb + rise - 0.2, s)
        self.kodi(*((mid, face + s * (depth - 0.2)) if axis == "x" else (face + s * (depth - 0.2), mid)),
                  zb + rise + 0.1, 0.6)

    def charupady(self, axis, line, s, u0, u1, z, depth=1.2):
        """Sloped-backrest seat railing; `line` is the outer edge, s points outward."""
        n_in, n_out = line - s * depth, line
        lo, hi = sorted((n_in, n_out))
        self._wbox(axis, lo, hi, u0, u1, z + 1.3, z + 1.48, "Wood", "seat")
        lo2, hi2 = sorted((n_out - s * 0.15, n_out))
        self._wbox(axis, lo2, hi2, u0, u1, z, z + 1.3, "DarkWood", "seat_apron")
        u = u0 + 0.2
        while u < u1 - 0.1:
            pts = [(n_out - s * 0.1, z + 1.48), (n_out + s * 0.05, z + 1.48), (n_out + s * 0.75, z + 3.25),
                   (n_out + s * 0.6, z + 3.25)]
            self._nprism(axis, pts, u - 0.06, u + 0.06, "Wood", "backrest")
            u += 0.3
        for zz, off in ((z + 2.0, 0.22), (z + 3.25, 0.68)):
            pts = [(n_out + s * (off - 0.12), zz - 0.12), (n_out + s * (off + 0.08), zz - 0.12),
                   (n_out + s * (off + 0.08), zz + 0.05), (n_out + s * (off - 0.12), zz + 0.05)]
            self._nprism(axis, pts, u0, u1, "DarkWood", "back_rail")

    # ------------------------------------------------------------ stilt
    def stilt_column(self, x, y):
        top = L.GF_TOP - L.BEAM_D
        self.box(x - 0.75, y - 0.75, L.GF, x + 0.75, y + 0.75, L.GF + 0.6, "Sandstone", "pier_base")
        self.box(x - 0.6, y - 0.6, L.GF + 0.6, x + 0.6, y + 0.6, top - 0.5, "Laterite", "laterite_pier")
        self.box(x - 0.68, y - 0.68, top - 0.5, x + 0.68, y + 0.68, top, "Wood", "pier_cap")

    def spandrel(self, axis, c, t, a, b, spring, top, cusped=True, mat="WallPink", name="beam"):
        """Plain timber beam: no arch, no brackets."""
        self._wbox(axis, c - 0.25, c + 0.25, a, b, top - 0.5, top, "Wood", name)

    def arch_trim(self, axis, face, outsign, a, b, spring, rise, width=0.28, proud=0.07, mat="Trim"):
        top = spring + rise + 0.15
        n0, n1 = sorted((face, face + outsign * 0.12))
        self._wbox(axis, n0, n1, a - 0.6, b + 0.6, top, top + 0.5, "Wood", "fascia")

    # --------------------------------------------------------- openings
    def opening(self, axis, c, t, s, face, o, base):
        a, b, kind = o["s"], o["e"], o["kind"]
        sill = base + o["sill"]
        head = base + o["head"]
        ext = s != 0
        if kind in ("window", "jharokha"):
            self.azhi_window(axis, c, t, s, face, a, b, sill, head, ext)
            if ext and kind == "window":
                self.tile_hood(axis, face, s, a - 0.6, b + 0.6, head + 0.35, 1.3)
            if ext and kind == "jharokha":
                self.balcony(axis, face, s, a, b, sill, head)
        elif kind in ("vent", "jaali"):
            self.jaali(axis, c, a, b, sill, head, t=0.25)
            if ext and kind == "jaali":
                self.tile_hood(axis, face, s, a - 0.5, b + 0.5, head + 0.3, 1.0)
        elif kind == "door_glass":
            self.plank_door(axis, c, a, b, sill, head, bars_top=True)
        elif kind == "door_main":
            self.plank_door(axis, c, a, b, sill, head)
            if ext:
                fr = sorted((face, face + s * 0.25))
                self._wbox(axis, fr[0], fr[1], a - 0.4, a, sill, head + 0.4, "Wood", "door_frame")
                self._wbox(axis, fr[0], fr[1], b, b + 0.4, sill, head + 0.4, "Wood", "door_frame")
                self._wbox(axis, fr[0], fr[1], a - 0.4, b + 0.4, head, head + 0.4, "Wood", "door_frame")
                for u in (a - 0.2, b + 0.2):
                    pts = [(face, head + 0.3), (face + s * 2.0, head + 0.3), (face + s * 2.0, head + 0.05),
                           (face + s * 0.3, head - 1.0), (face, head - 1.0)]
                    self._nprism(axis, pts, u - 0.15, u + 0.15, "Wood", "canopy_bracket")
                self.mini_gable(axis, face, s, a - 0.4, b + 0.4, head + 0.35, 2.4, 1.9)
        elif kind in ("door", "arch_open"):
            w = 0.2
            for (p, q) in ((a, a + w), (b - w, b)):
                self._wbox(axis, c - t / 2 - 0.04, c + t / 2 + 0.04, p, q, base, head, "Wood", "frame")
            self._wbox(axis, c - t / 2 - 0.04, c + t / 2 + 0.04, a, b, head - w, head, "Wood", "frame")

    def azhi_window(self, axis, c, t, s, face, a, b, sill, head, ext):
        """Heavy timber frame, vertical wooden bars, dark shutters behind."""
        fr = 0.25
        for (p, q) in ((a, a + fr), (b - fr, b)):
            self._wbox(axis, c - t / 2 - 0.05, c + t / 2 + 0.05, p, q, sill, head, "Wood", "win_frame")
        self._wbox(axis, c - t / 2 - 0.05, c + t / 2 + 0.05, a, b, sill, sill + fr, "Wood", "win_frame")
        self._wbox(axis, c - t / 2 - 0.05, c + t / 2 + 0.05, a, b, head - fr, head, "Wood", "win_frame")
        self._wbox(axis, c - 0.05, c + 0.05, a + fr, b - fr, sill + fr, head - fr, "GlassDark", "pane")
        nb = c + (s if s else 1) * (t / 2 - 0.12)
        u = a + fr + 0.25
        while u < b - fr - 0.1:
            self._wbox(axis, nb - 0.07, nb + 0.07, u - 0.07, u + 0.07, sill + fr, head - fr, "Bars", "azhi_bar")
            u += 0.42
        self._wbox(axis, nb - 0.09, nb + 0.09, a + fr, b - fr, (sill + head) / 2 - 0.08, (sill + head) / 2 + 0.08,
                   "Wood", "azhi_rail")
        if ext:
            lo, hi = sorted((face, face + s * 0.3))
            self._wbox(axis, lo, hi, a - 0.3, b + 0.3, sill - 0.25, sill, "Laterite", "win_sill")

    def tile_hood(self, axis, face, s, u0, u1, z, proj):
        pts = [(face, z + 0.75), (face + s * proj, z + 0.1), (face + s * proj, z + 0.25), (face, z + 0.92)]
        self._nprism(axis, pts, u0, u1, "KTile", "tile_hood")
        for u in (u0 + 0.35, u1 - 0.35):
            bp = [(face, z + 0.7), (face + s * (proj - 0.15), z + 0.12), (face + s * (proj - 0.15), z - 0.05),
                  (face, z - 0.6)]
            self._nprism(axis, bp, u - 0.1, u + 0.1, "Wood", "hood_bracket")

    def plank_door(self, axis, c, a, b, sill, head, bars_top=False):
        mid = (a + b) / 2
        fr = 0.2
        for (p, q) in ((a, a + fr), (b - fr, b)):
            self._wbox(axis, c - 0.14, c + 0.14, p, q, sill, head, "Wood", "door_frame")
        self._wbox(axis, c - 0.14, c + 0.14, a, b, head - fr, head, "Wood", "door_frame")
        zt = head - 1.6 if bars_top else head - fr
        for (p, q) in ((a + fr, mid - 0.02), (mid + 0.02, b - fr)):
            self._wbox(axis, c - 0.08, c + 0.08, p, q, sill, zt, "DarkWood", "door_leaf")
            for zz in (sill + 0.6, (sill + zt) / 2, zt - 0.6):
                self._wbox(axis, c - 0.12, c + 0.12, p + 0.08, q - 0.08, zz - 0.12, zz + 0.12, "Wood", "batten")
            self._wbox(axis, c - 0.13, c + 0.13, q - 0.3 if p < mid else p + 0.2, q - 0.2 if p < mid else p + 0.3,
                       (sill + zt) / 2 - 0.3, (sill + zt) / 2 + 0.3, "Gold", "door_ring")
        if bars_top:
            self._wbox(axis, c - 0.04, c + 0.04, a + fr, b - fr, zt, head - fr, "GlassDark")
            u = a + fr + 0.25
            while u < b - fr - 0.1:
                self._wbox(axis, c - 0.07, c + 0.07, u - 0.06, u + 0.06, zt, head - fr, "Bars", "azhi_bar")
                u += 0.38

    def jaali(self, axis, c, a, b, z0, z1, t=0.2, mat="Wood", step=0.3, bar=0.07):
        """Azhi: close-set square wooden slats in a heavy frame."""
        h = t / 2
        self._wbox(axis, c - h, c + h, a, a + 0.18, z0, z1, "Wood")
        self._wbox(axis, c - h, c + h, b - 0.18, b, z0, z1, "Wood")
        self._wbox(axis, c - h, c + h, a, b, z0, z0 + 0.18, "Wood")
        self._wbox(axis, c - h, c + h, a, b, z1 - 0.18, z1, "Wood")
        u = a + 0.18 + step / 2
        while u < b - 0.18:
            self._wbox(axis, c - h * 0.7, c + h * 0.7, u - 0.06, u + 0.06, z0 + 0.18, z1 - 0.18, "Bars", "slat")
            u += step

    def balcony(self, axis, face, s, a, b, sill, head):
        """Timber balcony with a charupady and its own little gable roof."""
        D = 1.8
        N = lambda d: face + s * d  # noqa: E731
        ua, ub = a - 0.5, b + 0.5
        lo, hi = sorted((N(0), N(D)))
        self._wbox(axis, lo, hi, ua, ub, sill - 0.3, sill, "Wood", "balcony_floor")
        for u in (ua + 0.2, ub - 0.2):
            pts = [(N(0), sill - 0.3), (N(D - 0.1), sill - 0.3), (N(D - 0.1), sill - 0.6), (N(0.4), sill - 1.8),
                   (N(0), sill - 1.8)]
            self._nprism(axis, pts, u - 0.16, u + 0.16, "Wood", "balcony_beam")
        self.charupady(axis, N(D - 0.1), s, ua + 0.2, ub - 0.2, sill - 0.05, depth=1.1)
        for uu in (ua + 0.15, ub - 0.15):
            cx, cy = (uu, N(D - 0.2)) if axis == "x" else (N(D - 0.2), uu)
            self.post(cx, cy, sill, head + 0.6, w=0.3, base=False)
        self._wbox(axis, lo, hi, ua - 0.1, ub + 0.1, head + 0.6, head + 0.85, "Wood", "balcony_plate")
        self.mini_gable(axis, face, s, ua, ub, head + 0.85, D + 0.9, 2.2)

    # ------------------------------------------------------- roof edges
    def chhajja(self, axis, face, s, u0, u1, z, proj=1.4, brackets=True, mat="KTile"):
        """Tile skirt roof on exposed rafters."""
        p = proj + 0.8
        pts = [(face, z + 1.3), (face + s * p, z + 0.1), (face + s * p, z + 0.28), (face, z + 1.48)]
        self._nprism(axis, pts, u0, u1, "KTile", "skirt_roof")
        lo, hi = sorted((face + s * (p - 0.1), face + s * p))
        self._wbox(axis, lo, hi, u0, u1, z - 0.15, z + 0.25, "Wood", "skirt_fascia")
        u = u0 + 0.4
        while u < u1 - 0.2:
            r = [(face, z + 1.2), (face + s * (p - 0.1), z + 0.12), (face + s * (p - 0.1), z - 0.05),
                 (face, z + 1.03)]
            self._nprism(axis, r, u - 0.07, u + 0.07, "Wood", "rafter")
            u += 1.6

    def kangura(self, axis, c, t, u0, u1, ztop, mat="Trim", pitch=1.5):
        """Parapet: laterite coping with a timber top rail."""
        self._wbox(axis, c - t / 2 - 0.08, c + t / 2 + 0.08, u0, u1, ztop, ztop + 0.3, "Laterite", "coping")
        self._wbox(axis, c - t / 2 + 0.05, c + t / 2 - 0.05, u0, u1, ztop + 0.3, ztop + 0.45, "Wood", "top_rail")

    def _band(self, z0, z1):
        p = 0.12
        for (a, b, c_, d) in ((-p, 39.99, 30 + p, 40 + p), (-p, -p, 30 + p, 0.01), (-p, 0, 0.01, 40),
                              (29.99, 0, 30 + p, 40)):
            self.box(a, b, z0, c_, d, z1, "Laterite", "laterite_band")

    def _coping(self, w):
        """Screen walls round the parking: laterite with a timber azhi above."""
        (ax, ay), (bx, by) = w["a"], w["b"]
        horiz = abs(ay - by) < 1e-6
        axis = "x" if horiz else "y"
        c = ay if horiz else ax
        u0, u1 = (min(ax, bx), max(ax, bx)) if horiz else (min(ay, by), max(ay, by))
        t = w["t"]
        for sgn in (-1, 1):
            n0, n1 = sorted((c + sgn * t / 2, c + sgn * (t / 2 + 0.04)))
            self._wbox(axis, n0, n1, u0, u1, w["base"], w["top"], "Laterite", "laterite_skin")
        self._wbox(axis, c - t / 2 - 0.08, c + t / 2 + 0.08, u0, u1, w["top"], w["top"] + 0.25, "Sandstone",
                   "coping")
        self.jaali(axis, c, u0 + 0.2, u1 - 0.2, w["top"] + 0.25, w["top"] + 2.2, t=0.25)
        self._wbox(axis, c - t / 2, c + t / 2, u0, u1, w["top"] + 2.2, w["top"] + 2.4, "Wood", "rail")

    # ---------------------------------------------------------- arcade
    def arcade(self):
        A = L.ARCADE
        base, top = A["base"], A["top"]
        beam = base + 8.2
        for i, px in enumerate(A["piers"]):
            x = min(max(px, 0.4), 29.6)
            self.post(x, 0.4, base, beam, w=0.6)
        self.box(0.0, 0.05, beam, 30.0, 0.75, beam + 0.6, "Wood", "arcade_beam")
        self.box(0.0, 0.0, beam + 0.6, 30.0, 0.75, top, "WallPink", "arcade_wall")
        for pa, pb in zip(A["piers"], A["piers"][1:]):
            a, b = max(pa, 0.4) + 0.45, min(pb, 29.6) - 0.45
            self.charupady("x", 0.15, -1, a, b, base, depth=1.25)

    # -------------------------------------------------------- mumty top
    def mumty_top(self, mz):
        """The big roof shelters the mumty, so it only gets a laterite top course."""
        self.box(21.4, 24.4, mz + 0.5, 30.0, 40.0, mz + 0.8, "Laterite", "mumty_cap")

    # ---------------------------------------------------------- extras
    def extras(self):
        self.coll("ROOF")
        self.main_roof()
        self.tulasi_thara(8.0, 10.0)
        self.coll("FF")
        self.wood_ceiling()
        # GF: laterite skin on the stair core facing the parking + road
        self.coll("GF")
        for (x0, y0, x1, y1) in ((21.585, 25.0, 21.625, 39.6), (21.6, 24.585, 30.0, 24.625)):
            self.box(x0, y0, L.GF, x1, y1, L.GF + 3.0, "Laterite", "core_skin")

    def main_roof(self):
        """Hip-and-gable roof on timber posts over the whole terrace."""
        x0, x1, y0, y1 = ROOF_X0, ROOF_X1, ROOF_Y0, ROOF_Y1
        z0 = EAVE_Z
        H = RIDGE_H
        w = x1 - x0
        xc = (x0 + x1) / 2
        sl = H / (w / 2)
        a = GABLET
        zt = z0 + sl * a
        bm = bmesh.new()
        V = lambda x, y, z: bm.verts.new((x * F, y * F, z * F))  # noqa: E731
        b0, b1, b2, b3 = V(x0, y0, z0), V(x1, y0, z0), V(x1, y1, z0), V(x0, y1, z0)
        g0l, g0r = V(x0 + a, y0 + a, zt), V(x1 - a, y0 + a, zt)
        g1l, g1r = V(x0 + a, y1 - a, zt), V(x1 - a, y1 - a, zt)
        r0, r1 = V(xc, y0 + a, z0 + H), V(xc, y1 - a, z0 + H)
        faces = [
            (b0, b1, g0r, g0l),                       # south hip
            (b2, b3, g1l, g1r),                       # north hip
            (b1, b2, g1r, r1, r0, g0r),               # east slope
            (b3, b0, g0l, r0, r1, g1l),               # west slope
            (g0l, g0r, r0),                           # south gablet
            (g1r, g1l, r1),                           # north gablet
        ]
        for f in faces:
            bm.faces.new(f)
        bm.faces.new((b3, b2, b1, b0))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self._obj("main_roof", bm, "KTile")
        # ridge + hip cappings
        self.box(xc - 0.25, y0 + a - 0.6, z0 + H - 0.05, xc + 0.25, y1 - a + 0.6, z0 + H + 0.35, "KTile", "ridge")
        # fascia boards round the eave
        for (a0, b0_, a1, b1_) in ((x0, y0, x1, y0 + 0.15), (x0, y1 - 0.15, x1, y1), (x0, y0, x0 + 0.15, y1),
                                   (x1 - 0.15, y0, x1, y1)):
            self.box(a0, b0_, z0 - 0.5, a1, b1_, z0 + 0.05, "Wood", "eave_fascia")
        # mukhappu gables (lattice faces) at both ends + brass kodi finials
        self.lattice_triangle("x", y1 - a + 0.05, x0 + a + 0.3, x1 - a - 0.3, zt + 0.05, z0 + H - 0.4, 1)
        self.lattice_triangle("x", y0 + a - 0.05, x0 + a + 0.3, x1 - a - 0.3, zt + 0.05, z0 + H - 0.4, -1)
        for yy in (y0 + a - 0.3, y1 - a + 0.3):
            self.kodi(xc, yy, z0 + H + 0.3, 1.3)
        # wall plate + posts on the perimeter columns
        for (px, py) in L.COLUMNS:
            if px in (0.5, 29.5) or py in (0.5, 39.5):
                if 22 <= px <= 30 and 25 <= py <= 40:
                    zb = L.ROOF + L.MUMTY_H + 0.8   # stands on the mumty
                else:
                    zb = L.ROOF + L.PARAPET_H + 0.45
                self.post(px, py, zb, z0 - 0.6, w=0.6, base=False)
        for (ax0, ay0, ax1, ay1) in ((0.2, 0.2, 29.8, 0.8), (0.2, 39.2, 29.8, 39.8), (0.2, 0.2, 0.8, 39.8),
                                     (29.2, 0.2, 29.8, 39.8)):
            self.box(ax0, ay0, z0 - 0.6, ax1, ay1, z0, "Wood", "wall_plate")
        # tie beams across (visible from the terrace)
        for yy in (11.0, 21.0, 30.5):
            self.box(0.5, yy - 0.25, z0 - 0.6, 29.5, yy + 0.25, z0 - 0.1, "Wood", "tie_beam")
        # wooden ceiling under the eave overhang
        self.box(x0 + 0.15, y0 + 0.15, z0 - 0.06, x1 - 0.15, y1 - 0.15, z0 - 0.01, "Wood", "eave_soffit")

    def tulasi_thara(self, x, y):
        z = L.ROOF
        self.box(x - 1.5, y - 1.5, z, x + 1.5, y + 1.5, z + 0.5, "Sandstone", "thara_base")
        self.box(x - 1.1, y - 1.1, z + 0.5, x + 1.1, y + 1.1, z + 2.6, "Laterite", "thara")
        self.box(x - 1.3, y - 1.3, z + 2.6, x + 1.3, y + 1.3, z + 2.9, "WallPink", "thara_cap")
        self.sphere(x, y, z + 3.6, 0.8, "Leaf", 2, 1.1)
        self.revolve([(0.25, 0), (0.35, 0.3), (0.1, 0.6), (0.08, 3.0), (0.4, 3.1), (0.0, 3.4)], x + 3.0, y,
                     z, "Gold", 12, name="nilavilakku")

    def wood_ceiling(self):
        """Timber ceiling with exposed joists in the first-floor rooms."""
        z = L.FF_TOP - 0.05
        self.box(0.75, 4.2, z - 0.06, 29.25, 39.25, z, "Wood", "ceiling")
        y = 5.0
        while y < 39.0:
            self.box(0.75, y - 0.12, z - 0.4, 29.25, y + 0.12, z - 0.06, "DarkWood", "joist")
            y += 2.5

    # -------------------------------------------------------- furniture
    def furniture(self, level, kind, rect, extra):
        if kind == "water_tank":
            cx, cy = 26.3, 18.0
            self.box(cx - 2.3, cy - 2.3, L.ROOF, cx + 2.3, cy + 2.3, L.ROOF + 1.2, "Laterite", "tank_stand")
            self.revolve([(2.0, 0), (2.1, 3.6), (1.2, 4.2), (0.5, 4.3), (0.5, 4.6), (0.0, 4.6)], cx, cy,
                         L.ROOF + 1.2, "Black", 28, name="water_tank")
            return
        if kind == "seat":
            return  # the road-side balconies carry their own charupady seats
        return super().furniture(level, kind, rect, extra)

    def arch_headboard(self, axis, xface, y0, y1, ztop):
        """Plain jackwood headboard with a carved top rail."""
        self.prism([(y0 + 0.1, ztop), (y1 - 0.1, ztop), (y1 - 0.1, ztop + 0.35), (y0 + 0.1, ztop + 0.35)], "x",
                   xface - 0.45, xface + 0.05, "DarkWood", "headboard_rail")
