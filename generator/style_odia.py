"""
Odia / Kalinga style for the Puri home-hotel.

Same layout as the Rajasthani version; only the skin changes:
  * laterite-red walls, khondalite (grey-buff stone) mouldings and bands
  * trabeated openings: stepped stone corbels under a lintel, no arches
  * turned stone balusters (as in Kalinga temple windows) instead of jaali
  * projecting bay windows and roof pavilions with stepped "pidha" roofs,
    bell (ghanta), amalaka and kalasa finials
  * a curvilinear "rekha" tower over the stair mumty
  * Konark-wheel relief at the entrance and a Pattachitra mural panel
"""
import math

import bpy  # noqa: F401  (bpy must be imported before bmesh)
import bmesh  # noqa: F401

import build_model as BM
from build_model import Builder, F

L = BM.L


class OdiaBuilder(Builder):
    STYLE = "odia"
    PALETTE = {
        "WallPink": ("#A85A3C", 0.95, 0.0, dict(noise=0.22, bump=0.45)),   # laterite
        "Trim": ("#CDBB9A", 0.85, 0.0, dict(noise=0.08, bump=0.15)),       # khondalite buff
        "Sandstone": ("#9C8E7C", 0.9, 0.0, dict(noise=0.14, bump=0.3)),    # carved khondalite
        "RoofTile": ("#8F4F35", 0.9, 0.0, dict(noise=0.12)),
        "Gold": ("#B88A2E", 0.4, 0.8, {}),
        "PattaRed": ("#B3261E", 0.8, 0.0, {}),
        "PattaYellow": ("#E3A52A", 0.8, 0.0, {}),
        "PattaBlack": ("#1C1A18", 0.8, 0.0, {}),
        "PattaGreen": ("#2F6B3A", 0.8, 0.0, {}),
        "PattaWhite": ("#F1E8D6", 0.8, 0.0, {}),
    }

    # ------------------------------------------------ openings (trabeated)
    def spandrel(self, axis, c, t, a, b, spring, top, cusped=True, mat="WallPink", name="corbel"):
        """Stepped stone corbels closing the top of an opening under a lintel."""
        h = top - spring
        n = 3
        sw = min(0.32, (b - a) * 0.09)
        zt = top - min(0.45, h * 0.3)
        dz = (zt - spring) / n
        zs = [spring + i * dz for i in range(n)] + [zt]
        # outline: lintel top, then down the right corbel steps, across, and up the left ones
        pts = [(a, top), (b, top)]
        for i in range(n):
            pts += [(b - i * sw, zs[i]), (b - (i + 1) * sw, zs[i]), (b - (i + 1) * sw, zs[i + 1])]
        for i in range(n - 1, -1, -1):
            pts += [(a + (i + 1) * sw, zs[i + 1]), (a + (i + 1) * sw, zs[i]), (a + i * sw, zs[i])]
        return self._wprism(axis, pts, c - t / 2, c + t / 2, "Sandstone" if mat != "Plaster" else "Plaster", name)

    def arch_trim(self, axis, face, outsign, a, b, spring, rise, width=0.28, proud=0.07, mat="Trim"):
        """Carved lintel band over the opening (replaces the arch outline)."""
        top = spring + rise + 0.15
        n0, n1 = sorted((face, face + outsign * 0.12))
        self._wbox(axis, n0, n1, a - 0.45, b + 0.45, top, top + 0.4, "Trim", "lintel")
        n0, n1 = sorted((face, face + outsign * 0.2))
        self._wbox(axis, n0, n1, a - 0.6, b + 0.6, top + 0.4, top + 0.55, "Sandstone", "lintel_band")
        # small rosettes at the lintel ends
        for u in (a - 0.25, b + 0.25):
            m0, m1 = sorted((face, face + outsign * 0.18))
            self._wbox(axis, m0, m1, u - 0.12, u + 0.12, top + 0.08, top + 0.32, "Sandstone", "rosette")

    def jaali(self, axis, c, a, b, z0, z1, t=0.2, mat="Sandstone", step=0.36, bar=0.07):
        """Kalinga-style screen: turned stone balusters between rails."""
        h = t / 2
        self._wbox(axis, c - h, c + h, a, a + 0.15, z0, z1, "Trim")
        self._wbox(axis, c - h, c + h, b - 0.15, b, z0, z1, "Trim")
        self._wbox(axis, c - h, c + h, a, b, z0, z0 + 0.18, "Trim")
        self._wbox(axis, c - h, c + h, a, b, z1 - 0.18, z1, "Trim")
        hh = z1 - z0 - 0.36
        if hh <= 0.1:
            return
        prof = [(0.07, 0), (0.1, 0.06), (0.06, 0.16), (0.11, 0.35), (0.13, 0.5), (0.11, 0.65),
                (0.06, 0.84), (0.1, 0.94), (0.07, 1.0)]
        u = a + 0.15 + step / 2
        while u < b - 0.15:
            cx, cy = (u, c) if axis == "x" else (c, u)
            self.revolve([(r * 1.1, z * hh) for r, z in prof], cx, cy, z0 + 0.18, "Sandstone", 10, name="baluster")
            u += step

    def chhajja(self, axis, face, s, u0, u1, z, proj=1.4, brackets=True, mat="Sandstone"):
        """Stepped stone cornice (horizontal tiers, as on Odia temple walls)."""
        p = proj
        pts = [(face, z), (face + s * p * 0.45, z), (face + s * p * 0.45, z + 0.14),
               (face + s * p * 0.75, z + 0.14), (face + s * p * 0.75, z + 0.28),
               (face + s * p, z + 0.28), (face + s * p, z + 0.46), (face, z + 0.46)]
        self._nprism(axis, pts, u0, u1, "Trim", "cornice")
        if brackets:
            span = u1 - u0
            nb = max(2, int(span / 3.0) + 1)
            for i in range(nb):
                uc = u0 + 0.4 + (span - 0.8) * i / (nb - 1)
                bp = [(face, z - 0.7), (face, z), (face + s * p * 0.42, z), (face + s * p * 0.42, z - 0.2),
                      (face + s * p * 0.22, z - 0.2), (face + s * p * 0.22, z - 0.45)]
                self._nprism(axis, bp, uc - 0.14, uc + 0.14, "Sandstone", "corbel_bracket")

    def kangura(self, axis, c, t, u0, u1, ztop, mat="Trim", pitch=1.5):
        """Parapet: stepped coping with small amalaka finials at intervals."""
        self._wbox(axis, c - t / 2 - 0.1, c + t / 2 + 0.1, u0, u1, ztop, ztop + 0.18, "Trim", "coping")
        self._wbox(axis, c - t / 2 - 0.02, c + t / 2 + 0.02, u0, u1, ztop + 0.18, ztop + 0.3, "Sandstone",
                   "coping2")
        n = max(1, int((u1 - u0) / 6.0))
        for i in range(n + 1):
            u = u0 + 0.6 + (u1 - u0 - 1.2) * i / max(n, 1)
            cx, cy = (u, c) if axis == "x" else (c, u)
            self.box(cx - 0.35, cy - 0.35, ztop + 0.3, cx + 0.35, cy + 0.35, ztop + 0.75, "Trim", "pedestal")
            self.amalaka(cx, cy, ztop + 0.75, 0.32)

    # --------------------------------------------------------- finials
    def amalaka(self, cx, cy, z0, r, kalasa=True):
        """Ribbed stone disc (amalaka) with kalasa on top."""
        prof = [(r * 0.45, 0), (r * 0.9, r * 0.12), (r, r * 0.3), (r * 0.9, r * 0.48), (r * 0.45, r * 0.6)]
        self.revolve(prof, cx, cy, z0, "Sandstone", 24, name="amalaka")
        if kalasa:
            kp = [(r * 0.35, 0), (r * 0.45, r * 0.25), (r * 0.25, r * 0.55), (r * 0.12, r * 0.8), (0, r * 1.1)]
            self.revolve(kp, cx, cy, z0 + r * 0.6, "Gold", 12, name="kalasa")

    def pidha(self, cx, cy, w, d, z, tiers=3, tier=0.55, mat="Sandstone"):
        """Stepped pyramidal roof (pidha deul) - returns top z."""
        for i in range(tiers):
            k = 1.0 - i * (0.55 / tiers)
            ww, dd = w * k, d * k
            z0 = z + i * tier
            self.box(cx - ww / 2, cy - dd / 2, z0, cx + ww / 2, cy + dd / 2, z0 + tier * 0.6, mat, "pidha")
            self.box(cx - ww * 0.42, cy - dd * 0.42, z0 + tier * 0.6, cx + ww * 0.42, cy + dd * 0.42, z0 + tier,
                     "WallPink", "pidha_recess")
        top = z + tiers * tier
        # bell (ghanta) + amalaka + kalasa
        r = min(w, d) * 0.28
        self.revolve([(r, 0), (r * 0.95, r * 0.35), (r * 0.6, r * 0.75), (r * 0.25, r * 0.95), (r * 0.2, r * 1.05)],
                     cx, cy, top, mat, 20, name="ghanta")
        self.amalaka(cx, cy, top + r * 1.05, r * 0.75)
        return top

    # ------------------------------------------------------- bay window
    def jharokha(self, axis, face, s, a, b, sill, head):
        D = 1.6
        N = lambda d: face + s * d  # noqa: E731
        ua, ub = a - 0.4, b + 0.4
        mid = (a + b) / 2
        st = "Sandstone"
        # corbelled base: three stepped stone courses
        for i, (inset, dz) in enumerate(((0.0, 0.35), (0.35, 0.35), (0.8, 0.4))):
            z1 = sill - sum(x[1] for x in ((0.0, 0.35), (0.35, 0.35), (0.8, 0.4))[:i])
            self._wbox(axis, N(0), N(D - inset * 0.8), ua + inset, ub - inset, z1 - dz, z1, "Trim" if i == 0 else st)
        self._wbox(axis, N(0), N(D + 0.12), ua - 0.1, ub + 0.1, sill - 0.12, sill + 0.05, "Trim", "bay_band")
        # baluster screen front + sides up to the lintel
        lint = head - 0.2
        self.jaali(axis, N(D - 0.12), ua + 0.2, ub - 0.2, sill + 0.05, lint, t=0.22)
        side_axis = "y" if axis == "x" else "x"
        for uu in (ua + 0.1, ub - 0.1):
            lo, hi = sorted((N(0), N(D - 0.24)))
            self.jaali(side_axis, uu, lo, hi, sill + 0.05, lint, t=0.2)
        # corner posts
        for uu in (ua + 0.1, ub - 0.1):
            lo, hi = sorted((N(D - 0.3), N(D + 0.02)))
            if axis == "x":
                self.box(uu - 0.16, lo, sill + 0.05, uu + 0.16, hi, lint, "Trim", "bay_post")
            else:
                self.box(lo, uu - 0.16, sill + 0.05, hi, uu + 0.16, lint, "Trim", "bay_post")
        # lintel + cornice + pidha roof
        self._wbox(axis, N(0), N(D + 0.1), ua - 0.1, ub + 0.1, lint, lint + 0.4, "Trim", "bay_lintel")
        self._nprism(axis, [(N(0), lint + 0.4), (N(D + 0.55), lint + 0.4), (N(D + 0.55), lint + 0.6),
                            (N(0), lint + 0.75)], ua - 0.5, ub + 0.5, st, "bay_cornice")
        w = (ub - ua) * 0.85
        if axis == "x":
            self.pidha(mid, N(D / 2), w, D * 0.95, lint + 0.6, tiers=3, tier=0.5)
        else:
            self.pidha(N(D / 2), mid, D * 0.95, w, lint + 0.6, tiers=3, tier=0.5)

    # --------------------------------------------------------- pavilion
    def chhatri(self, x0, y0, size, z):
        x1, y1 = x0 + size, y0 + size
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        st = "Sandstone"
        self.box(x0 - 0.2, y0 - 0.2, z, x1 + 0.2, y1 + 0.2, z + 0.5, "Trim", "pav_plinth")
        top = z + 5.6
        ins = 0.5
        for px, py in ((x0 + ins, y0 + ins), (x1 - ins, y0 + ins), (x1 - ins, y1 - ins), (x0 + ins, y1 - ins)):
            self.box(px - 0.35, py - 0.35, z + 0.5, px + 0.35, py + 0.35, z + 1.0, st)
            self.box(px - 0.24, py - 0.24, z + 1.0, px + 0.24, py + 0.24, top - 0.5, "Trim", "pav_pillar")
            self.box(px - 0.32, py - 0.32, top - 0.5, px + 0.32, py + 0.32, top - 0.3, st)
            self.box(px - 0.45, py - 0.45, top - 0.3, px + 0.45, py + 0.45, top, st)
        for (axis, c, u0, u1) in (("x", y0 + ins, x0 + ins + 0.24, x1 - ins - 0.24),
                                  ("x", y1 - ins, x0 + ins + 0.24, x1 - ins - 0.24),
                                  ("y", x0 + ins, y0 + ins + 0.24, y1 - ins - 0.24),
                                  ("y", x1 - ins, y0 + ins + 0.24, y1 - ins - 0.24)):
            self.spandrel(axis, c, 0.3, u0, u1, top - 1.2, top, True, st)
        self.box(x0 - 0.05, y0 - 0.05, top, x1 + 0.05, y1 + 0.05, top + 0.4, "Trim", "pav_lintel")
        self.box(x0 - 0.4, y0 - 0.4, top + 0.4, x1 + 0.4, y1 + 0.4, top + 0.6, st, "pav_cornice")
        self.pidha(cx, cy, size + 0.2, size + 0.2, top + 0.6, tiers=4, tier=0.6)

    # ---------------------------------------------------------- extras
    def extras(self):
        self.coll("ROOF")
        self.rekha_tower()
        self.coll("GF")
        self.konark_wheel(27.4, 40.01, L.GF + 4.2, 1.3)
        self.pattachitra()

    def rekha_tower(self):
        """Curvilinear rekha shikhara on the mumty roof (square plan)."""
        cx, cy = 25.8, 37.0
        z = L.ROOF + L.MUMTY_H + 0.5
        self.box(cx - 2.6, cy - 2.6, z, cx + 2.6, cy + 2.6, z + 0.6, "Trim", "rekha_base")
        h = 6.5
        prof = []
        for i in range(11):
            t = i / 10
            half = 2.2 * (1 - 0.55 * t ** 1.6)  # gently curving inwards towards the top
            prof.append((half * math.sqrt(2), z + 0.6 + h * t - z))
        # square section: 4 segments, rotated 45 degrees so faces align with the walls
        self.revolve(prof, cx, cy, z, "WallPink", 4, name="rekha", rot=math.pi / 4)
        # horizontal bhumi (storey) bands on the tower
        for i in range(1, 5):
            t = i / 5
            half = 2.2 * (1 - 0.55 * t ** 1.6) + 0.1
            zz = z + 0.6 + h * t
            self.box(cx - half, cy - half, zz - 0.12, cx + half, cy + half, zz + 0.05, "Trim", "bhumi")
        top = z + 0.6 + h
        neck = 2.2 * 0.45
        self.box(cx - neck * 0.7, cy - neck * 0.7, top, cx + neck * 0.7, cy + neck * 0.7, top + 0.3, "Sandstone")
        self.amalaka(cx, cy, top + 0.3, 1.1)

    def konark_wheel(self, uc, face_y, zc, R):
        """Relief of the Konark sun-temple wheel on the north (road) face."""
        y0, y1 = face_y, face_y + 0.22
        st = "Sandstone"
        n = 36
        for i in range(n):
            a0 = 2 * math.pi * i / n
            a1 = 2 * math.pi * (i + 1) / n
            pts = [(uc + R * math.cos(a0), zc + R * math.sin(a0)), (uc + R * math.cos(a1), zc + R * math.sin(a1)),
                   (uc + (R - 0.22) * math.cos(a1), zc + (R - 0.22) * math.sin(a1)),
                   (uc + (R - 0.22) * math.cos(a0), zc + (R - 0.22) * math.sin(a0))]
            self.prism(pts, "y", y0, y1, st, "wheel_rim")
        for i in range(16):
            a = 2 * math.pi * i / 16
            w = 0.09 if i % 2 == 0 else 0.05
            r0, r1 = 0.28, R - 0.2
            ca, sa = math.cos(a), math.sin(a)
            px, pz = -sa * w, ca * w
            pts = [(uc + ca * r0 + px, zc + sa * r0 + pz), (uc + ca * r1 + px, zc + sa * r1 + pz),
                   (uc + ca * r1 - px, zc + sa * r1 - pz), (uc + ca * r0 - px, zc + sa * r0 - pz)]
            self.prism(pts, "y", y0, y1 - 0.05, st, "wheel_spoke")
        hub = [(uc + 0.3 * math.cos(2 * math.pi * i / 20), zc + 0.3 * math.sin(2 * math.pi * i / 20))
               for i in range(20)]
        self.prism(hub, "y", y0, y1 + 0.06, "Trim", "wheel_hub")
        # axle stub frame
        self.box(uc - R - 0.3, y0, zc - R - 0.35, uc + R + 0.3, y0 + 0.08, zc - R - 0.15, "Trim", "wheel_base")

    def pattachitra(self):
        """Pattachitra-style mural panel on the stair wall facing the parking."""
        x = 21.625 - 0.04
        y0, y1, z0, z1 = 30.5, 37.0, L.GF + 2.2, L.GF + 7.6

        def panel(ya, yb, za, zb, mat, d):
            self.box(x - d, ya, za, x, yb, zb, mat, "patta")

        panel(y0, y1, z0, z1, "PattaRed", 0.05)
        panel(y0 + 0.2, y1 - 0.2, z0 + 0.2, z1 - 0.2, "PattaYellow", 0.07)
        panel(y0 + 0.4, y1 - 0.4, z0 + 0.4, z1 - 0.4, "PattaBlack", 0.08)
        panel(y0 + 0.5, y1 - 0.5, z0 + 0.5, z1 - 0.5, "PattaRed", 0.09)
        # border of small alternating squares (the typical pattachitra frieze)
        y = y0 + 0.6
        i = 0
        while y + 0.3 < y1 - 0.6:
            m = ("PattaYellow", "PattaWhite", "PattaGreen")[i % 3]
            panel(y, y + 0.25, z1 - 0.95, z1 - 0.7, m, 0.11)
            panel(y, y + 0.25, z0 + 0.7, z0 + 0.95, m, 0.11)
            y += 0.4
            i += 1
        # three framed figures (stylised trees / lamps) in the field
        for k, yc in enumerate((y0 + 1.65, (y0 + y1) / 2, y1 - 1.65)):
            panel(yc - 0.7, yc + 0.7, z0 + 1.2, z1 - 1.2, "PattaGreen" if k != 1 else "PattaYellow", 0.1)
            panel(yc - 0.5, yc + 0.5, z0 + 1.4, z1 - 1.4, "PattaWhite", 0.11)
            panel(yc - 0.12, yc + 0.12, z0 + 1.5, z1 - 1.7, "PattaRed", 0.12)
            for j in range(3):
                zz = z0 + 2.0 + j * 0.7
                ww = 0.42 - j * 0.1
                panel(yc - ww, yc + ww, zz, zz + 0.2, "PattaGreen", 0.12)
