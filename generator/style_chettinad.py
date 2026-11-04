"""
Chettinad (Tamil Nadu) style for the Puri home-hotel.

Same plan, a completely different skin and roofscape:
  * egg-white lime plaster walls, red-oxide bands, white stucco mouldings
  * granite pillars with timber bracket capitals in the stilt parking
  * rectangular windows: peacock-green louvred shutters under stained-glass transoms
  * carved Burma-teak balconies on curved brackets with Mangalore-tile canopies
  * a grand carved teak entrance door with brass studs and a stucco crest
  * teak colonnade with turned wooden railings on the rear sit-outs
  * Mangalore-tile pent roofs, a hipped tile roof on the stair mumty and a tiled
    terrace pavilion with a traditional oonjal (wooden swing)
  * Athangudi-tile floors inside
"""
import math

import bpy  # noqa: F401  (bpy must be imported before bmesh)
import bmesh

import build_model as BM
from build_model import Builder, F

L = BM.L


class ChettinadBuilder(Builder):
    STYLE = "chettinad"
    CHHATRIS = []
    PALETTE = {
        "WallPink": ("#EEE5D3", 0.55, 0.0, dict(noise=0.05, bump=0.04)),   # egg-white lime plaster
        "Trim": ("#FAF7F0", 0.5, 0.0, dict(noise=0.03)),                   # white stucco
        "Sandstone": ("#77716B", 0.7, 0.0, dict(noise=0.18, bump=0.3)),    # granite
        "Wood": ("#4A2914", 0.45, 0.0, dict(noise=0.18)),                  # Burma teak
        "Plaster": ("#F2EBDC", 0.35, 0.0, dict(noise=0.03)),               # polished interior plaster
        "FloorStone": ("#A3402B", 0.3, 0.0, dict(checker="#EADFC6", checker_scale=3.3)),  # Athangudi
        "RoofTile": ("#9E5A3F", 0.9, 0.0, dict(noise=0.12)),
        "Pavers": ("#8C867E", 0.8, 0.0, dict(noise=0.12, bump=0.15)),
        "RedOxide": ("#9A3A28", 0.6, 0.0, dict(noise=0.06)),
        "Shutter": ("#1F6A5C", 0.5, 0.0, {}),                              # peacock green
        "Iron": ("#22302C", 0.5, 0.3, {}),
        "GlassBlue": ("#2D6E9E", 0.1, 0.0, {}),
        "GlassAmber": ("#D08B2B", 0.1, 0.0, {}),
        "GlassRuby": ("#9C2436", 0.1, 0.0, {}),
        "Mangalore": ("#B4532F", 0.85, 0.0, dict(noise=0.2, bump=0.35)),   # clay roof tiles
        "Gold": ("#C49A3A", 0.35, 0.85, {}),                               # brass
    }

    # ------------------------------------------------------------ helpers
    def urn(self, cx, cy, z0, s=1.0, mat="Trim"):
        prof = [(0.35, 0), (0.35, 0.15), (0.18, 0.25), (0.3, 0.45), (0.38, 0.65), (0.3, 0.85), (0.15, 0.95),
                (0.2, 1.05), (0.0, 1.3)]
        self.revolve([(r * s, z * s) for r, z in prof], cx, cy, z0, mat, 16, name="urn")

    def hip_roof(self, x0, y0, x1, y1, z, h, mat="Mangalore", fascia=True):
        """Hipped roof; ridge runs along the longer side."""
        bm = bmesh.new()
        V = lambda x, y, zz: bm.verts.new((x * F, y * F, zz * F))  # noqa: E731
        b = [V(x0, y0, z), V(x1, y0, z), V(x1, y1, z), V(x0, y1, z)]
        w, d = x1 - x0, y1 - y0
        if d >= w:
            r0 = V((x0 + x1) / 2, y0 + w / 2, z + h)
            r1 = V((x0 + x1) / 2, y1 - w / 2, z + h)
            faces = [(b[0], b[1], r0), (b[1], b[2], r1, r0), (b[2], b[3], r1), (b[3], b[0], r0, r1)]
        else:
            r0 = V(x0 + d / 2, (y0 + y1) / 2, z + h)
            r1 = V(x1 - d / 2, (y0 + y1) / 2, z + h)
            faces = [(b[0], b[1], r1, r0), (b[1], b[2], r1), (b[2], b[3], r0, r1), (b[3], b[0], r0)]
        for f in faces:
            bm.faces.new(f)
        bm.faces.new(b[::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self._obj("hip_roof", bm, mat)
        if fascia:
            t = 0.12
            for (a0, b0, a1, b1) in ((x0, y0, x1, y0 + t), (x0, y1 - t, x1, y1), (x0, y0, x0 + t, y1),
                                     (x1 - t, y0, x1, y1)):
                self.box(a0, b0, z - 0.45, a1, b1, z + 0.02, "Wood", "fascia")
        # ridge cap
        if d >= w:
            self.box((x0 + x1) / 2 - 0.15, y0 + w / 2, z + h - 0.05, (x0 + x1) / 2 + 0.15, y1 - w / 2, z + h + 0.15,
                     "RedOxide", "ridge")
        else:
            self.box(x0 + d / 2, (y0 + y1) / 2 - 0.15, z + h - 0.05, x1 - d / 2, (y0 + y1) / 2 + 0.15, z + h + 0.15,
                     "RedOxide", "ridge")

    def teak_post(self, x, y, z0, z1, r=0.3, base=True):
        if base:
            self.box(x - r - 0.25, y - r - 0.25, z0, x + r + 0.25, y + r + 0.25, z0 + 0.6, "Sandstone", "post_base")
            z0 += 0.6
        h = z1 - z0
        prof = [(r * 1.25, 0), (r * 1.1, 0.25), (r, 0.45), (r, h * 0.45), (r * 1.2, h * 0.47), (r * 1.2, h * 0.5),
                (r, h * 0.52), (r * 0.92, h - 0.6), (r * 1.25, h - 0.35), (r * 1.4, h)]
        self.revolve(prof, x, y, z0, "Wood", 16, name="teak_post")

    def bracket_pair(self, axis, c, t, u, z_top, reach=1.2, drop=1.0, mat="Wood"):
        """Curved timber brackets springing from a post at u, both sides."""
        for sgn in (1, -1):
            pts = [(u, z_top), (u + sgn * reach, z_top), (u + sgn * reach, z_top - 0.18)] + \
                  [(u + sgn * reach * (1 - math.sin(a)), z_top - 0.18 - (drop - 0.18) * (1 - math.cos(a)))
                   for a in [(math.pi / 2) * k / 10 for k in range(1, 11)]]
            self._wprism(axis, pts, c - t / 2, c + t / 2, mat, "bracket")

    # ------------------------------------------------------------ stilt
    def stilt_column(self, x, y):
        top = L.GF_TOP - L.BEAM_D
        self.box(x - 0.75, y - 0.75, L.GF, x + 0.75, y + 0.75, L.GF + 0.9, "Sandstone", "pillar_base")
        h = top - 1.0 - (L.GF + 0.9)
        prof = [(0.66, 0), (0.6, 0.3), (0.6, h * 0.48), (0.7, h * 0.5), (0.6, h * 0.52), (0.6, h)]
        self.revolve(prof, x, y, L.GF + 0.9, "Sandstone", 8, name="granite_pillar", rot=math.pi / 8)
        z = L.GF + 0.9 + h
        self.box(x - 0.68, y - 0.68, z, x + 0.68, y + 0.68, z + 0.3, "Sandstone", "pillar_cap")
        # timber bracket capital (potika) in both directions
        self.box(x - 0.55, y - 0.55, z + 0.3, x + 0.55, y + 0.55, top, "Wood", "potika_block")
        for axis in ("x", "y"):
            c = y if axis == "x" else x
            u = x if axis == "x" else y
            self.bracket_pair(axis, c, 0.5, u, top, reach=1.1, drop=0.7)

    def spandrel(self, axis, c, t, a, b, spring, top, cusped=True, mat="WallPink", name="bracket"):
        """No arches: timber brackets at both ends of the span."""
        for u, sgn in ((a, 1), (b, -1)):
            pts = [(u, top), (u + sgn * 1.4, top), (u + sgn * 1.4, top - 0.2)] + \
                  [(u + sgn * 1.4 * (1 - math.sin(k * math.pi / 20)), top - 0.2 - 0.9 * (1 - math.cos(k * math.pi / 20)))
                   for k in range(1, 11)]
            self._wprism(axis, pts, c - 0.2, c + 0.2, "Wood", name)

    def arch_trim(self, axis, face, outsign, a, b, spring, rise, width=0.28, proud=0.07, mat="Trim"):
        """Teak fascia board on the beam over a span."""
        top = spring + rise + 0.15
        n0, n1 = sorted((face, face + outsign * 0.1))
        self._wbox(axis, n0, n1, a - 0.6, b + 0.6, top + 0.05, top + 0.45, "Wood", "fascia")
        n0, n1 = sorted((face, face + outsign * 0.14))
        self._wbox(axis, n0, n1, a - 0.6, b + 0.6, top + 0.45, top + 0.6, "RedOxide", "fascia_band")

    # --------------------------------------------------------- openings
    def opening(self, axis, c, t, s, face, o, base):
        a, b, kind = o["s"], o["e"], o["kind"]
        sill = base + o["sill"]
        head = base + o["head"]
        ext = s != 0
        if kind in ("window", "jharokha", "vent", "jaali") and ext:
            self.stucco_surround(axis, face, s, a, b, sill, head, hood=kind != "vent")
        if kind in ("window", "jharokha"):
            self.shutter_window(axis, c, a, b, sill, head)
            if kind == "jharokha" and ext:
                self.balcony(axis, face, s, a, b, sill, head)
        elif kind == "vent":
            self.louvre_panel(axis, c, a, b, sill, head)
        elif kind == "jaali":
            self.jaali(axis, c, a, b, sill, head, t=0.2)
        elif kind == "door_glass":
            self.french_door(axis, c, a, b, sill, head)
        elif kind == "door_main":
            self.main_door(axis, c, t, s, face, a, b, sill, head)
        elif kind in ("door", "arch_open"):
            w = 0.18 if kind == "door" else 0.3
            for (p, q) in ((a, a + w), (b - w, b)):
                self._wbox(axis, c - t / 2 - 0.04, c + t / 2 + 0.04, p, q, base, head, "Wood", "frame")
            self._wbox(axis, c - t / 2 - 0.04, c + t / 2 + 0.04, a, b, head - w, head, "Wood", "frame")

    def stucco_surround(self, axis, face, s, a, b, sill, head, hood=True):
        n = lambda d: sorted((face, face + s * d))  # noqa: E731
        w = 0.32
        n0, n1 = n(0.08)
        self._wbox(axis, n0, n1, a - w, a, sill, head, "Trim", "surround")
        self._wbox(axis, n0, n1, b, b + w, sill, head, "Trim", "surround")
        self._wbox(axis, n0, n1, a - w, b + w, head, head + w, "Trim", "surround")
        n0, n1 = n(0.22)
        self._wbox(axis, n0, n1, a - w - 0.15, b + w + 0.15, sill - 0.22, sill, "Trim", "sill")
        if hood:
            n0, n1 = n(0.45)
            self._wbox(axis, n0, n1, a - w - 0.3, b + w + 0.3, head + w + 0.25, head + w + 0.45, "Trim", "hood")
            n0, n1 = n(0.12)
            self._wbox(axis, n0, n1, a - w, b + w, head + w, head + w + 0.25, "RedOxide", "hood_frieze")
            for u in (a - w - 0.05, b + w + 0.05):
                pts_n = [(face, head + w + 0.25), (face + s * 0.4, head + w + 0.25), (face + s * 0.12, head)]
                self._nprism(axis, pts_n, u - 0.12, u + 0.12, "Trim", "hood_bracket")

    def shutter_window(self, axis, c, a, b, sill, head):
        """Peacock-green louvred shutters with a stained-glass transom above."""
        zt = head - min(1.2, (head - sill) * 0.28)
        fr = 0.14
        # frame
        self._wbox(axis, c - 0.12, c + 0.12, a, a + fr, sill, head, "Wood", "frame")
        self._wbox(axis, c - 0.12, c + 0.12, b - fr, b, sill, head, "Wood", "frame")
        self._wbox(axis, c - 0.12, c + 0.12, a, b, sill, sill + fr, "Wood", "frame")
        self._wbox(axis, c - 0.12, c + 0.12, a, b, zt - 0.06, zt + 0.06, "Wood", "transom")
        # stained glass transom, three colours
        cols = ("GlassBlue", "GlassAmber", "GlassRuby")
        n = 3
        for i in range(n):
            u0 = a + fr + (b - a - 2 * fr) * i / n
            u1 = a + fr + (b - a - 2 * fr) * (i + 1) / n
            self._wbox(axis, c - 0.04, c + 0.04, u0, u1, zt + 0.06, head, cols[i % 3], "stained")
            if i:
                self._wbox(axis, c - 0.08, c + 0.08, u0 - 0.04, u0 + 0.04, zt, head, "Wood")
        # two leaves with louvres
        mid = (a + b) / 2
        for (p, q) in ((a + fr, mid - 0.02), (mid + 0.02, b - fr)):
            self._wbox(axis, c - 0.05, c + 0.05, p, q, sill + fr, zt - 0.06, "Shutter", "shutter")
            self._wbox(axis, c - 0.09, c + 0.09, p, p + 0.12, sill + fr, zt - 0.06, "Shutter")
            self._wbox(axis, c - 0.09, c + 0.09, q - 0.12, q, sill + fr, zt - 0.06, "Shutter")
            z = sill + fr + 0.25
            while z < zt - 0.3:
                self._wbox(axis, c - 0.09, c + 0.09, p + 0.12, q - 0.12, z, z + 0.07, "Shutter", "louvre")
                z += 0.24
            self._wbox(axis, c - 0.1, c + 0.1, p + 0.1, q - 0.1, (sill + zt) / 2 - 0.08, (sill + zt) / 2 + 0.08,
                       "Shutter", "rail")

    def louvre_panel(self, axis, c, a, b, sill, head):
        self._wbox(axis, c - 0.1, c + 0.1, a, b, sill, sill + 0.12, "Wood")
        self._wbox(axis, c - 0.1, c + 0.1, a, b, head - 0.12, head, "Wood")
        z = sill + 0.2
        while z < head - 0.15:
            self._wbox(axis, c - 0.08, c + 0.08, a, b, z, z + 0.07, "Shutter", "louvre")
            z += 0.2

    def jaali(self, axis, c, a, b, z0, z1, t=0.2, mat="Iron", step=0.33, bar=0.07):
        """Painted cast-iron grille: plain vertical bars between rails."""
        h = t / 2
        self._wbox(axis, c - h, c + h, a, a + 0.12, z0, z1, "Wood")
        self._wbox(axis, c - h, c + h, b - 0.12, b, z0, z1, "Wood")
        self._wbox(axis, c - h, c + h, a, b, z0, z0 + 0.14, "Wood")
        self._wbox(axis, c - h, c + h, a, b, z1 - 0.14, z1, "Wood")
        u = a + 0.12 + step / 2
        while u < b - 0.12:
            cx, cy = (u, c) if axis == "x" else (c, u)
            self.cyl(cx, cy, z0 + 0.14, z1 - 0.14, 0.035, "Iron", 6, "grille_bar")
            u += step
        if z1 - z0 > 2.0:
            self._wbox(axis, c - h * 0.5, c + h * 0.5, a, b, (z0 + z1) / 2 - 0.04, (z0 + z1) / 2 + 0.04, "Iron")

    def french_door(self, axis, c, a, b, sill, head):
        zt = head - 1.0
        fr = 0.15
        self._wbox(axis, c - 0.12, c + 0.12, a, a + fr, sill, head, "Wood")
        self._wbox(axis, c - 0.12, c + 0.12, b - fr, b, sill, head, "Wood")
        self._wbox(axis, c - 0.12, c + 0.12, a, b, zt - 0.06, zt + 0.06, "Wood")
        for i, col in enumerate(("GlassBlue", "GlassAmber", "GlassBlue")):
            u0 = a + fr + (b - a - 2 * fr) * i / 3
            u1 = a + fr + (b - a - 2 * fr) * (i + 1) / 3
            self._wbox(axis, c - 0.04, c + 0.04, u0, u1, zt + 0.06, head, col)
        mid = (a + b) / 2
        for (p, q) in ((a + fr, mid - 0.02), (mid + 0.02, b - fr)):
            self._wbox(axis, c - 0.03, c + 0.03, p, q, sill, zt - 0.06, "GlassDark")
            for z in (sill, sill + 2.4, zt - 0.2):
                self._wbox(axis, c - 0.07, c + 0.07, p, q, z, z + 0.2, "Wood")
            for u in (p, (p + q) / 2 - 0.05, q - 0.12):
                self._wbox(axis, c - 0.07, c + 0.07, u, u + 0.12, sill, zt - 0.06, "Wood")

    def main_door(self, axis, c, t, s, face, a, b, sill, head):
        """Carved teak double door with brass studs and a stucco crest."""
        N = lambda d: sorted((face, face + s * d))  # noqa: E731
        # thick carved frame proud of the wall
        n0, n1 = N(0.3)
        self._wbox(axis, n0, n1, a - 0.55, a, sill, head + 0.6, "Wood", "door_frame")
        self._wbox(axis, n0, n1, b, b + 0.55, sill, head + 0.6, "Wood", "door_frame")
        self._wbox(axis, n0, n1, a - 0.55, b + 0.55, head, head + 0.6, "Wood", "door_lintel")
        n0, n1 = N(0.4)
        self._wbox(axis, n0, n1, a - 0.7, b + 0.7, head + 0.6, head + 0.75, "Wood", "door_cornice")
        for u in (a - 0.28, b + 0.28):
            n0, n1 = N(0.36)
            for k in range(6):
                zz = sill + 0.6 + k * 1.25
                self._wbox(axis, n0, n1, u - 0.15, u + 0.15, zz, zz + 0.5, "Wood", "carving")
        # leaves with raised panels + brass studs
        g0, g1 = c - 0.12, c + 0.12
        mid = (a + b) / 2
        out = g1 if s > 0 else g0
        for (p, q) in ((a, mid - 0.02), (mid + 0.02, b)):
            self._wbox(axis, g0, g1, p, q, sill, head, "Wood", "door_leaf")
            for k in range(4):
                z0 = sill + 0.4 + k * (head - sill - 0.6) / 4
                z1 = z0 + (head - sill - 0.6) / 4 - 0.25
                lo, hi = sorted((out, out + s * 0.06))
                self._wbox(axis, lo, hi, p + 0.2, q - 0.2, z0, z1, "Wood", "panel")
                for uu in (p + 0.2, q - 0.2):
                    for zz in (z0, z1):
                        lo2, hi2 = sorted((out, out + s * 0.1))
                        self._wbox(axis, lo2, hi2, uu - 0.05, uu + 0.05, zz - 0.05, zz + 0.05, "Gold", "stud")
        # stucco crest above the door
        zc = head + 0.75
        cu = (a + b) / 2
        hw = (b - a) / 2 + 0.6
        pts = [(cu - hw, zc), (cu + hw, zc), (cu + hw, zc + 0.15), (cu + hw - 0.3, zc + 0.15)]
        for k in range(1, 12):
            ang = math.pi * k / 12
            pts.append((cu + (hw - 0.3) * math.cos(ang), zc + 0.15 + 0.75 * math.sin(ang)))
        pts += [(cu - hw + 0.3, zc + 0.15), (cu - hw, zc + 0.15)]
        n0, n1 = N(0.25)
        self._wprism(axis, pts, n0, n1, "Trim", "door_crest")
        n0, n1 = N(0.3)
        disc = [(cu + 0.28 * math.cos(2 * math.pi * k / 16), zc + 0.5 + 0.28 * math.sin(2 * math.pi * k / 16))
                for k in range(16)]
        self._wprism(axis, disc, n0, n1, "RedOxide", "crest_medallion")

    def balcony(self, axis, face, s, a, b, sill, head):
        """Carved teak balcony on curved brackets with a Mangalore-tile canopy."""
        D = 1.9
        N = lambda d: face + s * d  # noqa: E731
        ua, ub = a - 0.6, b + 0.6
        lo, hi = sorted((N(0), N(D)))
        self._wbox(axis, lo, hi, ua, ub, sill - 0.3, sill, "Wood", "balcony_floor")
        for u in (ua + 0.2, (ua + ub) / 2, ub - 0.2):
            pts = [(N(0), sill - 0.3)] + [(N((D - 0.15) * math.cos(t)), sill - 0.3 - 1.4 * math.sin(t))
                                         for t in [(math.pi / 2) * k / 10 for k in range(11)]]
            self._nprism(axis, pts, u - 0.15, u + 0.15, "Wood", "balcony_bracket")
        # turned wooden balusters with rails (front + sides)
        rail = sill + 2.6
        prof = [(0.07, 0), (0.1, 0.1), (0.06, 0.3), (0.12, 0.9), (0.06, 1.6), (0.1, 2.0), (0.07, 2.1)]
        scale = (rail - sill - 0.15) / 2.1
        u = ua + 0.25
        while u < ub - 0.15:
            cx, cy = (u, N(D - 0.12)) if axis == "x" else (N(D - 0.12), u)
            self.revolve([(r, z * scale) for r, z in prof], cx, cy, sill + 0.05, "Wood", 10, name="baluster")
            u += 0.35
        for uu in (ua + 0.1, ub - 0.1):
            d = 0.3
            while d < D - 0.2:
                cx, cy = (uu, N(d)) if axis == "x" else (N(d), uu)
                self.revolve([(r, z * scale) for r, z in prof], cx, cy, sill + 0.05, "Wood", 10, name="baluster")
                d += 0.35
        lo, hi = sorted((N(0), N(D)))
        self._wbox(axis, lo, hi, ua, ub, rail, rail + 0.15, "Wood", "rail")
        for uu in (ua, ub - 0.15):
            self._wbox(axis, lo, hi, uu, uu + 0.15, rail, rail + 0.15, "Wood", "rail")
        # posts + tile canopy
        for uu in (ua + 0.15, ub - 0.15):
            cx, cy = (uu, N(D - 0.15)) if axis == "x" else (N(D - 0.15), uu)
            self.teak_post(cx, cy, sill, head + 0.6, r=0.14, base=False)
        lo, hi = sorted((N(0), N(D + 0.2)))
        self._wbox(axis, lo, hi, ua - 0.1, ub + 0.1, head + 0.6, head + 0.85, "Wood", "canopy_beam")
        pts = [(N(0), head + 1.75), (N(D + 0.7), head + 0.85), (N(D + 0.7), head + 1.0), (N(0), head + 1.95)]
        self._nprism(axis, pts, ua - 0.6, ub + 0.6, "Mangalore", "canopy")
        lo, hi = sorted((N(D + 0.6), N(D + 0.72)))
        self._wbox(axis, lo, hi, ua - 0.6, ub + 0.6, head + 0.7, head + 1.0, "Wood", "canopy_fascia")

    # ------------------------------------------------------- roof edges
    def chhajja(self, axis, face, s, u0, u1, z, proj=1.4, brackets=True, mat="Mangalore"):
        """Mangalore-tile pent roof on timber brackets."""
        p = proj + 0.4
        pts = [(face, z + 1.0), (face + s * p, z + 0.2), (face + s * p, z + 0.38), (face, z + 1.2)]
        self._nprism(axis, pts, u0, u1, "Mangalore", "pent_roof")
        lo, hi = sorted((face + s * (p - 0.1), face + s * p))
        self._wbox(axis, lo, hi, u0, u1, z - 0.05, z + 0.3, "Wood", "pent_fascia")
        if brackets:
            span = u1 - u0
            nb = max(2, int(span / 3.5) + 1)
            for i in range(nb):
                uc = u0 + 0.5 + (span - 1.0) * i / (nb - 1)
                bp = [(face, z + 0.95), (face + s * (p - 0.1), z + 0.25), (face + s * (p - 0.1), z + 0.05),
                      (face + s * 0.3, z - 0.7), (face, z - 0.8)]
                self._nprism(axis, bp, uc - 0.12, uc + 0.12, "Wood", "rafter_bracket")

    def kangura(self, axis, c, t, u0, u1, ztop, mat="Trim", pitch=1.5):
        """Plain parapet: white coping, red-oxide frieze, pilasters with urns."""
        self._wbox(axis, c - t / 2 - 0.15, c + t / 2 + 0.15, u0, u1, ztop, ztop + 0.25, "Trim", "coping")
        for sgn in (-1, 1):
            n0, n1 = sorted((c + sgn * t / 2, c + sgn * (t / 2 + 0.04)))
            self._wbox(axis, n0, n1, u0, u1, ztop - 0.75, ztop - 0.25, "RedOxide", "frieze")
        n = max(1, int(round((u1 - u0) / 5.5)))
        for i in range(n + 1):
            u = u0 + 0.5 + (u1 - u0 - 1.0) * i / n
            self._wbox(axis, c - t / 2 - 0.14, c + t / 2 + 0.14, u - 0.45, u + 0.45, ztop - L.PARAPET_H, ztop + 0.4,
                       "Trim", "pilaster")
            cx, cy = (u, c) if axis == "x" else (c, u)
            self.urn(cx, cy, ztop + 0.4, 0.95)

    def _band(self, z0, z1):
        p = 0.15
        for (a, b, c_, d) in ((-p, 39.99, 30 + p, 40 + p), (-p, -p, 30 + p, 0.01), (-p, 0, 0.01, 40),
                              (29.99, 0, 30 + p, 40)):
            self.box(a, b, z0, c_, d, z1 - 0.2, "RedOxide", "band")
            self.box(a - 0.02, b - 0.02 if b < 0 else b, z1 - 0.2, c_ + 0.02, d + 0.02 if d > 40 else d, z1,
                     "Trim", "band_line")

    # ---------------------------------------------------------- arcade
    def arcade(self):
        A = L.ARCADE
        y, t, base, top = A["y"], A["t"], A["base"], A["top"]
        beam = base + 8.0
        for i, px in enumerate(A["piers"]):
            if i in (0, 3, len(A["piers"]) - 1):   # structural piers stay masonry
                x0, x1 = max(0.0, px - 0.45), min(30.0, px + 0.45)
                self.box(x0, 0.0, base, x1, 0.9, top, "WallPink", "pier")
                self.box(x0 - 0.05, -0.05, base, x1 + 0.05, 0.95, base + 0.7, "RedOxide", "pier_base")
            else:
                self.teak_post(px, y, base, beam, r=0.28)
                for axis_u in (px,):
                    self.bracket_pair("x", y, 0.4, axis_u, beam, reach=1.1, drop=0.8)
        self.box(0.0, 0.05, beam, 30.0, 0.7, beam + 0.6, "Wood", "arcade_beam")
        self.box(0.0, 0.0, beam + 0.6, 30.0, 0.75, top, "WallPink", "arcade_wall")
        self.box(-0.05, -0.05, beam + 0.6, 30.05, 0.0, beam + 0.8, "RedOxide", "arcade_band")
        # turned wooden railing between the posts
        prof = [(0.07, 0), (0.1, 0.1), (0.06, 0.3), (0.12, 0.9), (0.06, 1.6), (0.1, 2.0), (0.07, 2.1)]
        rail = base + A["parapet"]
        sc = (rail - base - 0.2) / 2.1
        for pa, pb in zip(A["piers"], A["piers"][1:]):
            a, b = pa + 0.45, pb - 0.45
            self.box(a, 0.2, base, b, 0.55, base + 0.15, "Wood", "rail_bottom")
            self.box(a, 0.15, rail, b, 0.6, rail + 0.18, "Wood", "rail_top")
            u = a + 0.25
            while u < b - 0.1:
                self.revolve([(r, z * sc) for r, z in prof], u, 0.375, base + 0.15, "Wood", 10, name="baluster")
                u += 0.38

    # -------------------------------------------------------- mumty top
    def mumty_top(self, mz):
        self.hip_roof(20.4, 23.4, 31.0, 41.0, mz + 0.5, 3.4)

    # ---------------------------------------------------------- extras
    def extras(self):
        self.coll("ROOF")
        self.facade_crest()
        self.terrace_pavilion()

    def facade_crest(self):
        """Stucco crest at the centre of the road-side parapet."""
        z = L.ROOF + L.PARAPET_H + 0.25
        cx = 11.0
        hw = 4.6
        pts = [(cx - hw, z), (cx + hw, z), (cx + hw, z + 0.5), (cx + hw - 0.9, z + 0.5), (cx + hw - 0.9, z + 1.1)]
        for k in range(1, 16):
            ang = math.pi * k / 16
            pts.append((cx + (hw - 0.9) * math.cos(ang), z + 1.1 + 1.3 * math.sin(ang)))
        pts += [(cx - hw + 0.9, z + 1.1), (cx - hw + 0.9, z + 0.5), (cx - hw, z + 0.5)]
        self.prism(pts, "y", 39.2, 40.12, "Trim", "crest")
        inner = [(cx - hw + 1.3, z + 0.5), (cx + hw - 1.3, z + 0.5)]
        for k in range(1, 14):
            ang = math.pi * k / 14
            inner.append((cx + (hw - 1.3) * math.cos(ang), z + 0.9 + 0.95 * math.sin(ang)))
        self.prism(inner, "y", 40.12, 40.18, "RedOxide", "crest_panel")
        disc = [(cx + 0.5 * math.cos(2 * math.pi * k / 20), z + 1.35 + 0.5 * math.sin(2 * math.pi * k / 20))
                for k in range(20)]
        self.prism(disc, "y", 40.18, 40.3, "Trim", "crest_medallion")
        petals = [(cx + (0.3 if k % 2 else 0.45) * math.cos(2 * math.pi * k / 16),
                   z + 1.35 + (0.3 if k % 2 else 0.45) * math.sin(2 * math.pi * k / 16)) for k in range(16)]
        self.prism(petals, "y", 40.3, 40.36, "Gold", "crest_flower")
        for u in (cx - hw + 0.45, cx + hw - 0.45):
            self.urn(u, 39.65, z + 0.5, 1.1)
        self.urn(cx, 39.65, z + 2.4, 0.9)

    def terrace_pavilion(self):
        """Open tiled pavilion on the terrace with an oonjal (wooden swing)."""
        z = L.ROOF
        x0, y0, x1, y1 = 3.0, 4.0, 13.0, 13.0
        self.box(x0, y0, z, x1, y1, z + 0.4, "Sandstone", "pav_plinth")
        self.box(x0 + 0.3, y0 + 0.3, z + 0.4, x1 - 0.3, y1 - 0.3, z + 0.42, "FloorStone", "pav_floor")
        top = z + 8.0
        posts = [(x0 + 0.6, y0 + 0.6), ((x0 + x1) / 2, y0 + 0.6), (x1 - 0.6, y0 + 0.6),
                 (x0 + 0.6, y1 - 0.6), ((x0 + x1) / 2, y1 - 0.6), (x1 - 0.6, y1 - 0.6)]
        for (px, py) in posts:
            self.teak_post(px, py, z + 0.4, top, r=0.28)
        for yy in (y0 + 0.6, y1 - 0.6):
            self.box(x0 + 0.2, yy - 0.25, top, x1 - 0.2, yy + 0.25, top + 0.6, "Wood", "pav_beam")
            for (px, py) in posts:
                if abs(py - yy) < 0.1:
                    self.bracket_pair("x", yy, 0.35, px, top, reach=1.0, drop=0.7)
        for xx in (x0 + 0.6, x1 - 0.6):
            self.box(xx - 0.25, y0 + 0.2, top, xx + 0.25, y1 - 0.2, top + 0.6, "Wood", "pav_beam")
        cy = (y0 + y1) / 2
        self.box(x0 + 0.6, cy - 0.2, top, x1 - 0.6, cy + 0.2, top + 0.5, "Wood", "swing_beam")
        self.hip_roof(x0 - 1.2, y0 - 1.2, x1 + 1.2, y1 + 1.2, top + 0.6, 3.6)
        # oonjal: teak plank hung on brass chains
        sx0, sx1 = (x0 + x1) / 2 - 2.6, (x0 + x1) / 2 + 2.6
        seat = z + 2.0
        self.box(sx0, cy - 1.0, seat, sx1, cy + 1.0, seat + 0.25, "Wood", "oonjal")
        self.box(sx0, cy - 1.05, seat + 0.25, sx1, cy + 1.05, seat + 0.4, "RedOxide", "oonjal_trim")
        for (cxx, cyy) in ((sx0 + 0.3, cy - 0.8), (sx1 - 0.3, cy - 0.8), (sx0 + 0.3, cy + 0.8), (sx1 - 0.3, cy + 0.8)):
            self.cyl(cxx, cyy, seat + 0.25, top, 0.05, "Gold", 6, "chain")
        # brass lamp + planters
        self.revolve([(0.25, 0), (0.35, 0.3), (0.1, 0.6), (0.08, 3.0), (0.4, 3.1), (0.0, 3.4)], x1 - 1.6, y0 + 1.6,
                     z + 0.42, "Gold", 12, name="kuthu_vilakku")
        for (px, py) in ((x0 - 1.8, y0 + 1.0), (x0 - 1.8, y1 - 1.0)):
            self.revolve([(0.5, 0), (0.7, 1.4)], px, py, z, "RoofTile", 16, name="planter")
            self.sphere(px, py, z + 2.2, 0.95, "Leaf", 2, 1.1)

    # -------------------------------------------------------- furniture
    def furniture(self, level, kind, rect, extra):
        if kind == "water_tank":
            cx, cy = 26.3, 20.6
            self.box(cx - 2.3, cy - 2.3, L.ROOF, cx + 2.3, cy + 2.3, L.ROOF + 2.5, "WallPink", "tank_stand")
            self.box(cx - 2.4, cy - 2.4, L.ROOF + 2.5, cx + 2.4, cy + 2.4, L.ROOF + 2.7, "Trim")
            self.revolve([(2.0, 0), (2.1, 3.6), (1.2, 4.2), (0.5, 4.3), (0.5, 4.6), (0.0, 4.6)], cx, cy,
                         L.ROOF + 2.7, "Black", 28, name="water_tank")
            return
        return super().furniture(level, kind, rect, extra)

    def arch_headboard(self, axis, xface, y0, y1, ztop):
        """Carved teak headboard crest with stepped top (no arch)."""
        pts = [(y0 + 0.3, ztop), (y1 - 0.3, ztop), (y1 - 0.3, ztop + 0.4), (y1 - 1.1, ztop + 0.4),
               (y1 - 1.1, ztop + 0.8), ((y0 + y1) / 2 + 0.6, ztop + 0.8), ((y0 + y1) / 2 + 0.6, ztop + 1.2),
               ((y0 + y1) / 2 - 0.6, ztop + 1.2), ((y0 + y1) / 2 - 0.6, ztop + 0.8), (y0 + 1.1, ztop + 0.8),
               (y0 + 1.1, ztop + 0.4), (y0 + 0.3, ztop + 0.4)]
        self.prism(pts, "x", xface - 0.35, xface, "Wood", "headboard_crest")
