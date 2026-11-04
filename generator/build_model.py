"""
Blender (bpy) builder for the Puri home-cum-hotel.

Reads design/layout.py (feet) and builds a real-scale model in metres.
Style: traditional Rajasthani haveli - Jaipur-pink lime-plaster walls with
cream outlines, jharokhas (projecting oriel windows), chhajjas (stone eaves),
cusped (multifoil) arches, jaali screens, kangura (crenellated) parapets and
domed chhatris on the roof.

Usage (from generator/render.py):  build(cut_z=None) -> dict of collections
"""
import math
import os
import sys

import bpy  # noqa: I001  (bpy must be imported before bmesh)
import bmesh
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "design"))
import layout as L  # noqa: E402

F = 0.3048  # feet -> metres

# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------
MATS = {
    # name: (hex, roughness, metallic, extra)
    "WallPink": ("#D4876A", 0.9, 0.0, dict(noise=0.10, bump=0.15)),
    "Trim": ("#F3EADB", 0.75, 0.0, dict(noise=0.04, bump=0.05)),
    "Plaster": ("#EFE5D3", 0.85, 0.0, dict(noise=0.04)),
    "Sandstone": ("#E6CB9C", 0.85, 0.0, dict(noise=0.10, bump=0.2)),
    "Wood": ("#5A3418", 0.55, 0.0, dict(noise=0.15)),
    "GlassDark": ("#22303A", 0.08, 0.0, {}),
    "GlassClear": ("#CFE3EA", 0.05, 0.0, dict(alpha=0.25)),
    "FloorStone": ("#C9BCA4", 0.45, 0.0, dict(noise=0.08)),
    "Tile": ("#E4E1DA", 0.3, 0.0, {}),
    "Pavers": ("#8E887D", 0.9, 0.0, dict(noise=0.12, bump=0.2)),
    "Asphalt": ("#3A3A3C", 0.95, 0.0, dict(noise=0.1)),
    "Concrete": ("#A9A398", 0.9, 0.0, dict(noise=0.08)),
    "Earth": ("#B9A47F", 1.0, 0.0, dict(noise=0.15)),
    "RoofTile": ("#A85B3A", 0.9, 0.0, dict(noise=0.12)),
    "Gold": ("#C9A23A", 0.35, 0.9, {}),
    "Fabric": ("#EEEAE2", 0.9, 0.0, {}),
    "FabricRed": ("#A3232E", 0.9, 0.0, {}),
    "FabricOchre": ("#C88A1E", 0.9, 0.0, {}),
    "Steel": ("#9CA2A8", 0.35, 0.8, {}),
    "Black": ("#161616", 0.5, 0.0, {}),
    "CarRed": ("#8E1414", 0.25, 0.3, {}),
    "CarWhite": ("#E6E6E4", 0.25, 0.2, {}),
    "CarBlue": ("#1F3D66", 0.25, 0.3, {}),
    "Tyre": ("#1A1A1A", 0.8, 0.0, {}),
    "Leaf": ("#3F6B2B", 0.8, 0.0, dict(noise=0.15)),
    "Trunk": ("#6B5843", 0.95, 0.0, {}),
    "Marking": ("#EFEFEA", 0.7, 0.0, {}),
    "Ceramic": ("#F6F5F1", 0.15, 0.0, {}),
    "Granite": ("#2C2A28", 0.3, 0.0, {}),
    "Rebar": ("#6B3A25", 0.6, 0.5, {}),
    "Cap": ("#C2262E", 0.5, 0.0, {}),
    "Cut": ("#2F2F31", 0.9, 0.0, {}),
}


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h):
    h = h.lstrip("#")
    return tuple(srgb_to_lin(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (1.0,)


class Builder:
    STYLE = "rajasthani"
    PALETTE = {}   # material overrides {name: (hex, rough, metal, extra)}
    CHHATRIS = L.CHHATRIS   # roof corner kiosks (a style may drop them)
    VIEW_OVERRIDES = {}     # per-style camera tweaks {view: {key: value}}

    def __init__(self):
        self.mats = {}
        self.colls = {}
        self.cur_coll = None

    # ---------------------------------------------------------------- setup
    def reset(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.palette = dict(MATS, **self.PALETTE)
        for name, (hx, rough, metal, extra) in self.palette.items():
            self.mats[name] = self._make_mat(name, hx, rough, metal, extra)

    def _make_mat(self, name, hx, rough, metal, extra):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        rgba = hex_rgba(hx)
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if "alpha" in extra:
            bsdf.inputs["Alpha"].default_value = extra["alpha"]
            try:
                m.surface_render_method = "BLENDED"
            except Exception:
                pass
        m.diffuse_color = rgba
        if extra.get("brick"):
            # laterite blocks: brick pattern on (x + y, z) so it wraps axis-aligned walls
            tc = nt.nodes.new("ShaderNodeTexCoord")
            sep = nt.nodes.new("ShaderNodeSeparateXYZ")
            add = nt.nodes.new("ShaderNodeMath")
            comb = nt.nodes.new("ShaderNodeCombineXYZ")
            brick = nt.nodes.new("ShaderNodeTexBrick")
            nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
            nt.links.new(sep.outputs["X"], add.inputs[0])
            nt.links.new(sep.outputs["Y"], add.inputs[1])
            nt.links.new(add.outputs["Value"], comb.inputs["X"])
            nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
            nt.links.new(comb.outputs["Vector"], brick.inputs["Vector"])
            brick.inputs["Color1"].default_value = rgba
            brick.inputs["Color2"].default_value = hex_rgba(extra.get("brick2", hx))
            brick.inputs["Mortar"].default_value = hex_rgba(extra["brick"])
            brick.inputs["Scale"].default_value = extra.get("brick_scale", 1.6)
            brick.inputs["Mortar Size"].default_value = 0.012
            nt.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
        if extra.get("checker"):
            # patterned floor tiles for renders (flat base colour is kept for glTF)
            tc = nt.nodes.new("ShaderNodeTexCoord")
            chk = nt.nodes.new("ShaderNodeTexChecker")
            chk.inputs["Scale"].default_value = extra.get("checker_scale", 3.3)
            chk.inputs["Color1"].default_value = rgba
            chk.inputs["Color2"].default_value = hex_rgba(extra["checker"])
            nt.links.new(tc.outputs["Object"], chk.inputs["Vector"])
            nt.links.new(chk.outputs["Color"], bsdf.inputs["Base Color"])
        if extra.get("noise"):
            # subtle colour variation (lime plaster / stone) for renders only
            tc = nt.nodes.new("ShaderNodeTexCoord")
            noise = nt.nodes.new("ShaderNodeTexNoise")
            noise.inputs["Scale"].default_value = 6.0
            noise.inputs["Detail"].default_value = 8.0
            nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = extra["noise"]
            mix.inputs["A"].default_value = rgba
            nt.links.new(noise.outputs["Fac"], mix.inputs["B"])
            # bring noise around 1.0 so multiply keeps brightness
            ramp = nt.nodes.new("ShaderNodeMapRange")
            ramp.inputs["To Min"].default_value = 0.75
            ramp.inputs["To Max"].default_value = 1.25
            nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
            nt.links.new(ramp.outputs["Result"], mix.inputs["B"])
            nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
            if extra.get("bump"):
                bump = nt.nodes.new("ShaderNodeBump")
                bump.inputs["Strength"].default_value = extra["bump"]
                noise2 = nt.nodes.new("ShaderNodeTexNoise")
                noise2.inputs["Scale"].default_value = 60.0
                nt.links.new(tc.outputs["Object"], noise2.inputs["Vector"])
                nt.links.new(noise2.outputs["Fac"], bump.inputs["Height"])
                nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        return m

    def simplify_materials(self):
        """Drop procedural nodes (for glTF export) keeping flat base colours."""
        for name, m in self.mats.items():
            nt = m.node_tree
            bsdf = nt.nodes.get("Principled BSDF")
            for link in list(nt.links):
                if link.to_node == bsdf and link.to_socket.name in ("Base Color", "Normal"):
                    nt.links.remove(link)
            bsdf.inputs["Base Color"].default_value = hex_rgba(self.palette[name][0])

    def coll(self, name):
        if name not in self.colls:
            c = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(c)
            self.colls[name] = c
        self.cur_coll = self.colls[name]
        return self.cur_coll

    # ------------------------------------------------------------ primitives
    def _obj(self, name, bm, mat):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(self.mats[mat])
        ob = bpy.data.objects.new(name, me)
        self.cur_coll.objects.link(ob)
        return ob

    def box(self, x0, y0, z0, x1, y1, z1, mat, name="box"):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4:
            return None
        bm = bmesh.new()
        vs = [bm.verts.new((x * F, y * F, z * F)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
        idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        for f in idx:
            bm.faces.new([vs[i] for i in f])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return self._obj(name, bm, mat)

    def prism(self, pts, axis, c0, c1, mat, name="prism"):
        """Extrude 2D polygon pts=(p,q) along axis between c0 and c1.
        axis 'y': (p,q)=(x,z); 'x': (p,q)=(y,z); 'z': (p,q)=(x,y)."""
        clean = []
        for p in pts:
            if not clean or (abs(p[0] - clean[-1][0]) > 1e-5 or abs(p[1] - clean[-1][1]) > 1e-5):
                clean.append(p)
        if len(clean) > 2 and abs(clean[0][0] - clean[-1][0]) < 1e-5 and abs(clean[0][1] - clean[-1][1]) < 1e-5:
            clean.pop()
        if len(clean) < 3:
            return None

        def P(p, q, c):
            if axis == "y":
                return (p * F, c * F, q * F)
            if axis == "x":
                return (c * F, p * F, q * F)
            return (p * F, q * F, c * F)

        bm = bmesh.new()
        v0 = [bm.verts.new(P(p, q, c0)) for p, q in clean]
        v1 = [bm.verts.new(P(p, q, c1)) for p, q in clean]
        if len(clean) > 4:
            tris = tessellate_polygon([[Vector((p, q, 0.0)) for p, q in clean]])
            seen = set()
            for i, j, k in tris:
                key = frozenset((i, j, k))
                if len(key) < 3 or key in seen:   # collinear outlines can yield repeats
                    continue
                seen.add(key)
                bm.faces.new((v0[i], v0[j], v0[k]))
                bm.faces.new((v1[k], v1[j], v1[i]))
        else:
            bm.faces.new(v0)
            bm.faces.new(v1[::-1])
        n = len(clean)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((v0[i], v0[j], v1[j], v1[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return self._obj(name, bm, mat)

    def revolve(self, profile, cx, cy, z0, mat, segs=24, sx=1.0, sy=1.0, name="rev", rot=0.0):
        """profile: [(r, z)] bottom->top (z relative to z0)."""
        bm = bmesh.new()
        rings = []
        for r, z in profile:
            if r < 1e-6:
                rings.append([bm.verts.new((cx * F, cy * F, (z0 + z) * F))])
            else:
                ring = []
                for i in range(segs):
                    a = 2 * math.pi * i / segs + rot
                    ring.append(bm.verts.new(((cx + r * sx * math.cos(a)) * F,
                                              (cy + r * sy * math.sin(a)) * F, (z0 + z) * F)))
                rings.append(ring)
        for ra, rb in zip(rings, rings[1:]):
            if len(ra) == 1 and len(rb) == 1:
                continue
            if len(ra) == 1:
                for i in range(segs):
                    bm.faces.new((ra[0], rb[i], rb[(i + 1) % segs]))
            elif len(rb) == 1:
                for i in range(segs):
                    bm.faces.new((ra[i], ra[(i + 1) % segs], rb[0]))
            else:
                for i in range(segs):
                    j = (i + 1) % segs
                    bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
        if len(rings[0]) > 1:
            bm.faces.new(rings[0][::-1])
        if len(rings[-1]) > 1:
            bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return self._obj(name, bm, mat)

    def cyl(self, cx, cy, z0, z1, r, mat, segs=20, name="cyl"):
        return self.revolve([(r, 0), (r, z1 - z0)], cx, cy, z0, mat, segs, name=name)

    def sphere(self, cx, cy, cz, r, mat, sub=2, sz=1.0, name="sph"):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r * F)
        for v in bm.verts:
            v.co.z *= sz
            v.co += Vector((cx * F, cy * F, cz * F))
        return self._obj(name, bm, mat)

    # ------------------------------------------------------- arch geometry
    @staticmethod
    def arch_curve(a, b, spring, rise, cusped=True, n=60, lobes=5):
        """Points along a (multifoil) arch from a to b, starting & ending at spring."""
        c = (a + b) / 2.0
        w = (b - a) / 2.0
        d = min(w, rise) * 0.16
        pts = []
        for i in range(n + 1):
            t = math.pi * i / n
            # slightly pointed envelope
            px = c - w * math.cos(t)
            pz = spring + rise * (math.sin(t) ** 0.85)
            if cusped:
                off = d * (1.0 - abs(math.sin(lobes * t)))
                # inward normal ~ towards arch centre (c, spring)
                vx, vz = c - px, spring - pz
                ln = math.hypot(vx, vz) or 1.0
                px += vx / ln * off
                pz += vz / ln * off
                pz = max(pz, spring)
            pts.append((px, pz))
        return pts

    def spandrel(self, axis, c, t, a, b, spring, top, cusped=True, mat="WallPink", name="spandrel"):
        """Solid panel filling [a,b]x[spring,top] minus the arch => arched opening."""
        rise = top - spring - 0.15
        curve = self.arch_curve(a, b, spring, rise, cusped)
        pts = [(a, top), (b, top)] + curve[::-1]
        return self._wprism(axis, pts, c - t / 2, c + t / 2, mat, name)

    def arch_trim(self, axis, face, outsign, a, b, spring, rise, width=0.28, proud=0.07, mat="Trim"):
        """Cream outline following the arch envelope + jambs, proud of facade."""
        c = (a + b) / 2.0
        w = (b - a) / 2.0
        n = 40
        outer, inner = [], []
        for i in range(n + 1):
            t = math.pi * i / n
            outer.append((c - (w + width) * math.cos(t), spring + (rise + width) * (math.sin(t) ** 0.85)))
            inner.append((c - w * math.cos(t), spring + rise * (math.sin(t) ** 0.85)))
        pts = outer + inner[::-1]
        c0, c1 = sorted((face, face + outsign * proud))
        return self._wprism(axis, pts, c0, c1, mat, "arch_trim")

    # ----------------------------------------------------------- ornaments
    def jaali(self, axis, c, a, b, z0, z1, t=0.2, mat="Sandstone", step=0.38, bar=0.07):
        """Lattice screen (orthogonal + diagonal bars read as stone jaali)."""
        h = t / 2
        # frame
        self._wbox(axis, c - h, c + h, a, a + 0.18, z0, z1, mat)
        self._wbox(axis, c - h, c + h, b - 0.18, b, z0, z1, mat)
        self._wbox(axis, c - h, c + h, a, b, z0, z0 + 0.18, mat)
        self._wbox(axis, c - h, c + h, a, b, z1 - 0.18, z1, mat)
        u = a + step
        while u < b - 0.1:
            self._wbox(axis, c - h * 0.6, c + h * 0.6, u - bar / 2, u + bar / 2, z0, z1, mat)
            u += step
        z = z0 + step
        while z < z1 - 0.1:
            self._wbox(axis, c - h * 0.6, c + h * 0.6, a, b, z - bar / 2, z + bar / 2, mat)
            z += step

    def _wbox(self, axis, n0, n1, u0, u1, z0, z1, mat, name="wpart"):
        """Box in wall-local coords. axis = direction the wall RUNS ('x' or 'y');
        n = coordinate across the wall, u = along the wall."""
        if axis == "x":
            return self.box(u0, n0, z0, u1, n1, z1, mat, name)
        return self.box(n0, u0, z0, n1, u1, z1, mat, name)

    def _wprism(self, axis, pts_uz, n0, n1, mat, name="wprism"):
        """Polygon in (u, z) of a wall running along axis, extruded across it."""
        return self.prism(pts_uz, "y" if axis == "x" else "x", n0, n1, mat, name)

    def _nprism(self, axis, pts_nz, u0, u1, mat, name="nprism"):
        """Polygon in (n, z) (across the wall) extruded along the wall."""
        return self.prism(pts_nz, axis, u0, u1, mat, name)

    def chhajja(self, axis, face, s, u0, u1, z, proj=1.4, brackets=True, mat="Sandstone"):
        """Sloping stone eave on the facade at height z (underside)."""
        n0 = face
        n1 = face + s * proj
        pts = [(n0, z), (n0, z + 0.55), (n1, z + 0.18), (n1, z)]
        self._nprism(axis, pts, u0, u1, mat, "chhajja")
        # drip band under the edge
        self._wbox(axis, min(n1 - s * 0.12, n1), max(n1 - s * 0.12, n1), u0, u1, z - 0.08, z, mat)
        if brackets:
            span = u1 - u0
            nb = max(2, int(span / 2.2) + 1)
            for i in range(nb):
                uc = u0 + 0.35 + (span - 0.7) * i / (nb - 1)
                bp = [(n0, z - 1.1), (n0, z), (n0 + s * proj * 0.85, z), (n0 + s * proj * 0.85, z - 0.15),
                      (n0 + s * 0.25, z - 0.55)]
                self._nprism(axis, bp, uc - 0.12, uc + 0.12, mat, "bracket")

    def kangura(self, axis, c, t, u0, u1, ztop, mat="Trim", pitch=1.5):
        """Crenellated parapet top (merlons with pointed caps)."""
        self._wbox(axis, c - t / 2 - 0.06, c + t / 2 + 0.06, u0, u1, ztop - 0.25, ztop, mat)
        u = u0 + 0.2
        while u + 0.8 <= u1 - 0.1:
            pts = [(u, ztop), (u + 0.8, ztop), (u + 0.8, ztop + 0.55), (u + 0.4, ztop + 0.95), (u, ztop + 0.55)]
            self._wprism(axis, pts, c - t / 2 + 0.05, c + t / 2 - 0.05, mat, "merlon")
            u += pitch

    def kalash(self, cx, cy, z0, scale=1.0):
        prof = [(0.32, 0), (0.36, 0.12), (0.18, 0.3), (0.3, 0.5), (0.3, 0.62), (0.12, 0.8),
                (0.08, 1.1), (0.14, 1.2), (0.0, 1.55)]
        self.revolve([(r * scale, z * scale) for r, z in prof], cx, cy, z0, "Gold", 16, name="kalash")

    def dome(self, cx, cy, z0, rx, ry, h, mat="Trim", segs=28):
        prof = []
        for i in range(13):
            a = (math.pi / 2) * i / 12
            r = math.cos(a)
            # slight onion bulge
            r *= 1.0 + 0.08 * math.sin(a * 2)
            prof.append((max(r, 0.0) if i < 12 else 0.0, h * math.sin(a)))
        bm_prof = [(r, z) for r, z in prof]
        self.revolve(bm_prof, cx, cy, z0, mat, segs, sx=rx, sy=ry, name="dome")
        # lotus band at base
        self.revolve([(1.05, 0), (1.08, 0.15), (1.0, 0.3)], cx, cy, z0 - 0.15, "Trim", segs, sx=rx, sy=ry)
        self.kalash(cx, cy, z0 + h - 0.05, scale=min(rx, ry) * 0.9)

    # -------------------------------------------------------------- walls
    def wall(self, w):
        (ax, ay), (bx, by) = w["a"], w["b"]
        t, z0, z1 = w["t"], w["base"], w["top"]
        horiz = abs(ay - by) < 1e-6
        axis = "x" if horiz else "y"
        c = ay if horiz else ax
        u0, u1 = (min(ax, bx), max(ax, bx)) if horiz else (min(ay, by), max(ay, by))
        out = w["out"]
        s = 0
        if out:
            s = 1 if out[0] == "+" else -1
        face = c + s * t / 2
        interior = w["level"] == "FF"
        mat = "Plaster" if (interior and not out) else "WallPink"
        inner = c - s * t / 2

        def seg(ua, ub, za, zb):
            self._wbox(axis, c - t / 2, c + t / 2, ua, ub, za, zb, mat, "wall")
            if interior and out:  # ivory lime-plaster lining on the room side
                self._wbox(axis, inner - s * 0.03, inner, ua, ub, za, zb, "Plaster", "lining")

        ops = sorted(w["openings"], key=lambda o: o["s"])
        cur = u0
        for o in ops:
            a, b = o["s"], o["e"]
            if a > cur:
                seg(cur, a, z0, z1)
            if o["sill"] > 0:
                seg(a, b, z0, z0 + o["sill"])
            if z0 + o["head"] < z1:
                seg(a, b, z0 + o["head"], z1)
            cur = b
            self.opening(axis, c, t, s, face, o, z0)
        if cur < u1:
            seg(cur, u1, z0, z1)

    def opening(self, axis, c, t, s, face, o, base):
        a, b = o["s"], o["e"]
        kind = o["kind"]
        sill = base + o["sill"]
        head = base + o["head"]
        width = b - a
        ext = s != 0
        if kind in ("window", "jharokha", "door_main", "arch_open", "door_glass"):
            rise = min(1.3, width * 0.38)
            if kind in ("door_glass",):
                rise = 0.0
            if rise > 0:
                self.spandrel(axis, c, t, a, b, head - rise - 0.15, head, cusped=True,
                              mat="WallPink" if ext or base < L.FF else "Plaster")
            if ext:
                # cream outline: jambs + arch
                if rise > 0:
                    self.arch_trim(axis, face, s, a, b, head - rise - 0.15, rise)
                    jt = head - rise - 0.15
                else:
                    jt = head
                    self._wbox(axis, face, face + s * 0.07, a - 0.28, b + 0.28, head, head + 0.28, "Trim", "trim")
                self._wbox(axis, face, face + s * 0.07, a - 0.28, a, sill, jt, "Trim", "trim")
                self._wbox(axis, face, face + s * 0.07, b, b + 0.28, sill, jt, "Trim", "trim")
                if kind == "window":
                    self._wbox(axis, face, face + s * 0.25, a - 0.4, b + 0.4, sill - 0.2, sill, "Trim", "sill")
                    self.chhajja(axis, face, s, a - 0.7, b + 0.7, head + 0.35, proj=1.2)
        if kind in ("window", "door_glass"):
            # wooden frame + glazing / shutters, set in the middle of the wall
            g0, g1 = c - 0.05, c + 0.05
            self._wbox(axis, g0, g1, a, b, sill, head, "GlassDark", "glass")
            fr = 0.15
            self._wbox(axis, g0 - 0.03, g1 + 0.03, a, a + fr, sill, head, "Wood")
            self._wbox(axis, g0 - 0.03, g1 + 0.03, b - fr, b, sill, head, "Wood")
            self._wbox(axis, g0 - 0.03, g1 + 0.03, a, b, sill, sill + fr, "Wood")
            self._wbox(axis, g0 - 0.03, g1 + 0.03, (a + b) / 2 - 0.06, (a + b) / 2 + 0.06, sill, head, "Wood")
            self._wbox(axis, g0 - 0.03, g1 + 0.03, a, b, sill + (head - sill) * 0.62,
                       sill + (head - sill) * 0.62 + 0.1, "Wood")
        if kind == "door_main":
            # carved double wooden door with brass studs
            g0, g1 = c - 0.12, c + 0.12
            mid = (a + b) / 2
            for (p, q) in ((a, mid - 0.02), (mid + 0.02, b)):
                self._wbox(axis, g0, g1, p, q, sill, head - 0.1, "Wood", "door")
                for zz in (sill + 1.5, sill + 3.5, sill + 5.5):
                    for uu in (p + 0.35, q - 0.35):
                        self._wbox(axis, g1 if s > 0 else g0 - 0.05, (g1 + 0.05) if s > 0 else g0,
                                   uu - 0.06, uu + 0.06, zz - 0.06, zz + 0.06, "Gold")
        if kind in ("jaali", "vent"):
            self.jaali(axis, c, a, b, sill, head, t=0.22)
            if ext:
                self._wbox(axis, face, face + s * 0.07, a - 0.25, b + 0.25, head, head + 0.25, "Trim")
                self._wbox(axis, face, face + s * 0.07, a - 0.25, b + 0.25, sill - 0.25, sill, "Trim")
                self._wbox(axis, face, face + s * 0.07, a - 0.25, a, sill, head, "Trim")
                self._wbox(axis, face, face + s * 0.07, b, b + 0.25, sill, head, "Trim")
                if kind == "jaali":
                    self.chhajja(axis, face, s, a - 0.6, b + 0.6, head + 0.3, proj=1.0, brackets=False)
        if kind == "door":
            # simple timber frame
            for (p, q) in ((a, a + 0.12), (b - 0.12, b)):
                self._wbox(axis, c - t / 2 - 0.03, c + t / 2 + 0.03, p, q, base, head, "Wood", "frame")
            self._wbox(axis, c - t / 2 - 0.03, c + t / 2 + 0.03, a, b, head - 0.12, head, "Wood", "frame")
        if kind == "jharokha":
            self.jharokha(axis, face, s, a, b, sill, head)

    # ------------------------------------------------------------ jharokha
    def jharokha(self, axis, face, s, a, b, sill, head):
        D = 1.75
        n0 = face
        N = lambda d: n0 + s * d  # noqa: E731
        ua, ub = a - 0.5, b + 0.5
        mid = (a + b) / 2
        st = "Sandstone"
        # corbelled base
        self._wbox(axis, N(0), N(D), ua, ub, sill - 0.35, sill, st, "j_base")
        self._wbox(axis, N(0), N(D + 0.12), ua - 0.1, ub + 0.1, sill - 0.12, sill, "Trim", "j_band")
        self._wbox(axis, N(0), N(D - 0.3), ua + 0.25, ub - 0.25, sill - 0.75, sill - 0.35, st)
        self._wbox(axis, N(0), N(D - 0.7), ua + 0.7, ub - 0.7, sill - 1.15, sill - 0.75, st)
        self._wbox(axis, N(0), N(D - 1.15), mid - 0.5, mid + 0.5, sill - 1.6, sill - 1.15, st)
        for uu in (ua + 0.25, mid, ub - 0.25):
            bp = [(N(0), sill - 1.9), (N(0), sill - 0.35), (N(D - 0.15), sill - 0.35),
                  (N(D - 0.15), sill - 0.6), (N(0.3), sill - 1.4)]
            self._nprism(axis, bp, uu - 0.14, uu + 0.14, st, "j_bracket")
        # low jaali parapet (front + sides)
        pz = sill + 1.6
        self.jaali(axis, N(D - 0.12), ua, ub, sill, pz, t=0.2)
        side_axis = "y" if axis == "x" else "x"
        for uu in (ua + 0.1, ub - 0.1):
            lo, hi = sorted((N(0), N(D - 0.2)))
            self.jaali(side_axis, uu, lo, hi, sill, pz, t=0.2)
        self._wbox(axis, N(0), N(D + 0.05), ua - 0.05, ub + 0.05, pz, pz + 0.18, "Trim", "j_rail")
        # slender pillars, 3 cusped arches across the front
        spring = head - 1.35
        pu = [ua + 0.15, ua + (ub - ua) / 3, ua + 2 * (ub - ua) / 3, ub - 0.15]
        for uu in pu:
            if axis == "x":
                cx, cy = uu, N(D - 0.15)
            else:
                cx, cy = N(D - 0.15), uu
            self.revolve([(0.16, 0), (0.12, 0.2), (0.1, 0.4), (0.1, spring - pz - 0.4), (0.15, spring - pz - 0.2),
                          (0.18, spring - pz)], cx, cy, pz + 0.18, st, 12, name="j_pillar")
        for i in range(3):
            p0, p1 = pu[i] + 0.1, pu[i + 1] - 0.1
            lo, hi = sorted((N(D - 0.28), N(D - 0.02)))
            self._wprism(axis, [(p0, head)] + [(p1, head)] +
                         self.arch_curve(p0, p1, spring, head - spring - 0.12, True, 40, 3)[::-1],
                         lo, hi, st, "j_arch")
        for uu in (ua, ub):
            lo, hi = sorted((N(0), N(D)))
            self._wbox(axis, lo, hi, uu - 0.12 if uu == ua else uu - 0.12, uu + 0.12, pz + 0.18, head, st, "j_side")
        # entablature + chhajja + dome
        self._wbox(axis, N(0), N(D + 0.1), ua - 0.15, ub + 0.15, head, head + 0.35, "Trim", "j_lintel")
        ch_pts = [(N(0), head + 0.35), (N(0), head + 0.75), (N(D + 0.75), head + 0.45), (N(D + 0.75), head + 0.35)]
        self._nprism(axis, ch_pts, ua - 0.8, ub + 0.8, st, "j_chhajja")
        dz = head + 0.75
        rx = (ub - ua) / 2 - 0.1
        ry = D / 2 + 0.05
        if axis == "x":
            cx, cy = mid, N(D / 2)
            self.box(ua + 0.2, min(N(0), N(D - 0.1)), dz - 0.3, ub - 0.2, max(N(0), N(D - 0.1)), dz + 0.25,
                     "Trim", "j_drum")
            self.dome(cx, cy, dz + 0.25, rx, ry, 1.6, "Sandstone")
        else:
            cx, cy = N(D / 2), mid
            self.box(min(N(0), N(D - 0.1)), ua + 0.2, dz - 0.3, max(N(0), N(D - 0.1)), ub - 0.2, dz + 0.25,
                     "Trim", "j_drum")
            self.dome(cx, cy, dz + 0.25, ry, rx, 1.6, "Sandstone")

    # ------------------------------------------------------------- chhatri
    def chhatri(self, x0, y0, size, z):
        x1, y1 = x0 + size, y0 + size
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        st = "Sandstone"
        self.box(x0 - 0.2, y0 - 0.2, z, x1 + 0.2, y1 + 0.2, z + 0.6, "Trim", "c_plinth")
        top = z + 6.2
        spring = top - 1.3
        ins = 0.45
        pts = [(x0 + ins, y0 + ins), (x1 - ins, y0 + ins), (x1 - ins, y1 - ins), (x0 + ins, y1 - ins)]
        for px, py in pts:
            self.revolve([(0.32, 0), (0.28, 0.35), (0.2, 0.6), (0.18, spring - z - 1.0), (0.26, spring - z - 0.7),
                          (0.3, spring - z - 0.6)], px, py, z + 0.6, st, 8, name="c_pillar")
            self.box(px - 0.32, py - 0.32, spring - 0.05, px + 0.32, py + 0.32, spring + 0.15, st)
        # arches on 4 sides
        for (axis, c, u0, u1) in (("x", y0 + ins, x0 + ins + 0.25, x1 - ins - 0.25),
                                  ("x", y1 - ins, x0 + ins + 0.25, x1 - ins - 0.25),
                                  ("y", x0 + ins, y0 + ins + 0.25, y1 - ins - 0.25),
                                  ("y", x1 - ins, y0 + ins + 0.25, y1 - ins - 0.25)):
            self.spandrel(axis, c, 0.3, u0, u1, spring, top, True, st, "c_arch")
        self.box(x0 + 0.1, y0 + 0.1, top, x1 - 0.1, y1 - 0.1, top + 0.35, "Trim", "c_lintel")
        # chhajja (pyramidal eave)
        o = 0.9
        bm = bmesh.new()
        e0 = top + 0.35
        rect = lambda xa, ya, xb, yb, zz: [bm.verts.new((xa * F, ya * F, zz * F)), bm.verts.new((xb * F, ya * F, zz * F)),  # noqa
                                           bm.verts.new((xb * F, yb * F, zz * F)), bm.verts.new((xa * F, yb * F, zz * F))]
        r0 = rect(x0 - o, y0 - o, x1 + o, y1 + o, e0)
        r1 = rect(x0 - o, y0 - o, x1 + o, y1 + o, e0 + 0.15)
        r2 = rect(x0 + 0.3, y0 + 0.3, x1 - 0.3, y1 - 0.3, e0 + 0.75)
        bm.faces.new(r0[::-1])
        for ra, rb in ((r0, r1), (r1, r2)):
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
        bm.faces.new(r2)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self._obj("c_chhajja", bm, st)
        dz = e0 + 0.75
        r = size / 2 - 0.35
        self.cyl(cx, cy, dz, dz + 0.45, r, "Trim", 28, "c_drum")
        self.dome(cx, cy, dz + 0.45, r, r, r * 1.05, "Trim")

    # --------------------------------------------------------------- stair
    def stair_storey(self, zb, last=False):
        S = L.STAIR
        x0w, x1w = S["west_flight"]
        x0e, x1e = S["east_flight"]
        yl = S["floor_landing_y"]
        ym = S["mid_landing_y"]
        r, g = L.RISER, L.TREAD
        ix0, iy0, ix1, iy1 = S["inner"]
        mat = "Sandstone"
        # flight 1 (west half, going south)
        for i in range(9):
            top = zb + (i + 1) * r
            ya, yb = yl - (i + 1) * g, yl - i * g
            self.box(x0w, ya, max(zb, top - 1.0), x1w, yb, top, mat, "step")
        # mid landing
        zm = zb + 10 * r
        self.box(ix0, iy0, zm - 0.6, ix1, ym, zm, mat, "landing")
        # flight 2 (east half, going north)
        for i in range(9):
            top = zm + (i + 1) * r
            ya, yb = ym + i * g, ym + (i + 1) * g
            self.box(x0e, ya, max(zm - 0.6, top - 1.0), x1e, yb, top, mat, "step")
        # central dividing wall with cream coping
        self.box(x1w, ym, zb, x0e, yl, zb + L.FLOOR_TO_FLOOR - (0.75 if not last else 0), "WallPink", "stair_mid")

    # --------------------------------------------------------------- furn
    def furniture(self, level, kind, rect, extra):
        x0, y0, x1, y1 = rect
        z = {"GF": L.GF, "FF": L.FF, "ROOF": L.ROOF + 8.5}[level]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if kind == "car":
            self.car(rect, z, extra.get("color", "CarRed"))
        elif kind == "scooter":
            self.box(x0 + 0.8, cy - 0.35, z + 0.6, x1 - 1.6, cy + 0.35, z + 1.6, "CarBlue", "scooter")
            self.box(x1 - 1.6, cy - 0.3, z + 0.6, x1 - 1.1, cy + 0.3, z + 3.2, "CarBlue")
            self.box(x0 + 1.0, cy - 0.3, z + 1.6, x0 + 3.0, cy + 0.3, z + 2.3, "Black")
            self.box(x1 - 1.35, cy - 0.9, z + 3.2, x1 - 1.2, cy + 0.9, z + 3.3, "Black")
            for wx in (x0 + 0.8, x1 - 0.8):
                ob = self.cyl(0, 0, -0.12, 0.12, 0.6, "Tyre", 16)
                ob.rotation_euler = (math.pi / 2, 0, 0)
                ob.location = (wx * F, cy * F, (z + 0.6) * F)
        elif kind == "tank":
            self.box(x0, y0, z, x1, y1, z + 3.5, "Steel", "meter_panel")
        elif kind == "bed":
            head = extra.get("head", "-x")
            self.box(x0, y0, z, x1, y1, z + 1.1, "Wood", "bed")
            self.box(x0 + 0.05, y0 + 0.05, z + 1.1, x1 - 0.05, y1 - 0.05, z + 1.85, "Fabric")
            if head == "-x":
                self.box(x0, y0 - 0.1, z, x0 + 0.35, y1 + 0.1, z + 4.2, "Wood", "headboard")
                self.box(x0 + 0.4, y0 + 0.4, z + 1.85, x0 + 1.6, cy - 0.15, z + 2.3, "Fabric")
                self.box(x0 + 0.4, cy + 0.15, z + 1.85, x0 + 1.6, y1 - 0.4, z + 2.3, "Fabric")
                self.box(x1 - 1.9, y0, z + 1.86, x1 - 0.9, y1, z + 1.95, "FabricRed")
                self.arch_headboard("y", x0 + 0.36, y0, y1, z + 4.2)
            else:
                self.box(x1 - 0.35, y0 - 0.1, z, x1, y1 + 0.1, z + 4.2, "Wood", "headboard")
                self.box(x1 - 1.6, y0 + 0.4, z + 1.85, x1 - 0.4, cy - 0.15, z + 2.3, "Fabric")
                self.box(x1 - 1.6, cy + 0.15, z + 1.85, x1 - 0.4, y1 - 0.4, z + 2.3, "Fabric")
                self.box(x0 + 0.9, y0, z + 1.86, x0 + 1.9, y1, z + 1.95, "FabricRed")
                self.arch_headboard("y", x1 - 0.36, y0, y1, z + 4.2)
        elif kind == "side_table":
            self.box(x0, y0, z, x1, y1, z + 1.9, "Wood", "side_table")
            self.cyl(cx, cy, z + 1.9, z + 2.9, 0.25, "Gold", 12)
        elif kind == "wardrobe":
            self.box(x0, y0, z, x1, y1, z + 7.0, "Wood", "wardrobe")
        elif kind == "tv":
            self.box(x0, y0, z, x1, y1, z + 2.3, "Wood", "tv_unit")
            sx0 = x0 + 0.05 if x0 < 1.0 else x1 - 0.15
            self.box(sx0, y0 + 0.2, z + 3.4, sx0 + 0.1, y1 - 0.2, z + 5.4, "Black", "tv")
        elif kind == "armchair" or kind == "chair":
            self.box(x0, y0, z, x1, y1, z + 1.5, "Wood" if kind == "chair" else "FabricOchre", kind)
            self.box(x0, y1 - 0.25, z, x1, y1, z + 3.0, "Wood" if kind == "chair" else "FabricOchre")
        elif kind == "seat":
            self.box(x0 + 0.1, y0 + 0.1, z + 1.5, x1 - 0.1, y1 - 0.1, z + 1.9, "FabricRed", "seat")
            for i in range(3):
                u = x0 + 0.6 + i * (x1 - x0 - 1.2) / 2
                self.box(u - 0.45, y1 - 0.5, z + 1.9, u + 0.45, y1 - 0.2, z + 2.6, "FabricOchre")
        elif kind == "desk":
            self.box(x0, y0, z + 2.4, x1, y1, z + 2.6, "Wood", "desk")
            self.box(x0, y0, z, x0 + 0.2, y1, z + 2.4, "Wood")
            self.box(x1 - 0.2, y0, z, x1, y1, z + 2.4, "Wood")
        elif kind == "table":
            self.cyl(cx, cy, z + 2.0, z + 2.15, (x1 - x0) / 2, "Wood", 20, "table")
            self.cyl(cx, cy, z, z + 2.0, 0.12, "Wood", 10)
        elif kind == "wc":
            back = extra.get("back", "+x")
            if back == "+x":
                self.box(x1 - 0.6, y0 + 0.1, z, x1, y1 - 0.1, z + 2.6, "Ceramic", "wc_tank")
                self.revolve([(0.55, 0), (0.6, 1.3), (0.62, 1.4)], x1 - 1.2, cy, z, "Ceramic", 20, sx=1.0, sy=0.8)
            else:
                self.box(x0, y0 + 0.1, z, x0 + 0.6, y1 - 0.1, z + 2.6, "Ceramic", "wc_tank")
                self.revolve([(0.55, 0), (0.6, 1.3), (0.62, 1.4)], x0 + 1.2, cy, z, "Ceramic", 20, sx=1.0, sy=0.8)
        elif kind == "basin":
            self.box(x0, y0, z + 2.5, x1, y1, z + 2.8, "Granite", "basin")
            self.revolve([(0.2, 0), (0.55, 0.35)], cx, cy, z + 2.8, "Ceramic", 20)
            self.box(x0, y0, z, x1, y1, z + 2.5, "Wood")
            mx = x1 - 0.02 if extra.get("back") == "+x" else x0 + 0.02
            self.box(mx - 0.05, y0 + 0.2, z + 3.6, mx + 0.05, y1 - 0.2, z + 5.6, "GlassDark", "mirror")
        elif kind == "shower":
            self.box(x0, y0, z, x1, y1, z + 0.1, "Tile", "shower_tray")
            self.box(x0, y0 - 0.03, z, x1 if (x1 - x0) < 3 else x0 + (x1 - x0) * 0.6, y0 + 0.03, z + 6.5,
                     "GlassClear", "shower_glass")
            self.cyl(cx, y1 - 0.4, z + 6.4, z + 6.5, 0.35, "Steel", 16)
        elif kind == "counter":
            self.box(x0, y0, z, x1, y1, z + 2.7, "Wood", "counter")
            self.box(x0, y0, z + 2.7, x1, y1, z + 2.85, "Granite")
            if extra.get("sink"):
                self.box(cx - 0.8, y0 + 0.4, z + 2.86, cx + 0.8, y1 - 0.4, z + 2.88, "Steel", "sink")
            if extra.get("stove"):
                self.box(x0 + 0.3, cy - 1.0, z + 2.86, x1 - 0.3, cy + 1.0, z + 2.95, "Black", "stove")
            if extra.get("sink") or extra.get("stove"):
                # wall cabinets
                pass
        elif kind == "fridge":
            self.box(x0, y0, z, x1, y1, z + 5.2, "Ceramic", "fridge")
        elif kind == "bench":
            self.box(x0, y0, z, x1, y1, z + 1.5, "Wood", "bench")
            self.box(x0 + 0.1, y0 + 0.1, z + 1.5, x1 - 0.1, y1 - 0.1, z + 1.7, "FabricRed")
        elif kind == "plant":
            self.revolve([(0.35, 0), (0.5, 1.2)], cx, cy, z, "RoofTile", 16, name="pot")
            self.sphere(cx, cy, z + 2.2, 0.75, "Leaf", 2, 1.3)
        elif kind == "water_tank":
            self.revolve([(2.0, 0), (2.1, 3.6), (1.2, 4.2), (0.5, 4.3), (0.5, 4.6), (0.0, 4.6)], cx, cy,
                         L.ROOF + L.MUMTY_H + 0.5, "Black", 28, name="water_tank")

    def arch_headboard(self, axis, xface, y0, y1, ztop):
        pts = self.arch_curve(y0 + 0.3, y1 - 0.3, ztop, 1.4, True, 40, 5)
        self.prism(pts, "x", xface - 0.35, xface, "Wood", "headboard_arch")

    def car(self, rect, z, color):
        x0, y0, x1, y1 = rect
        cx = (x0 + x1) / 2
        w = x1 - x0
        # nose faces north (y1), the car reversed in from the road
        self.box(x0 + 0.1, y0 + 0.2, z + 0.9, x1 - 0.1, y1 - 0.2, z + 3.0, color, "car_body")
        # bonnet slope & cabin
        cab = [(y0 + 1.2, z + 3.0), (y0 + 2.2, z + 4.7), (y1 - 5.6, z + 4.75), (y1 - 4.0, z + 3.0)]
        self.prism(cab, "x", x0 + 0.45, x1 - 0.45, color, "car_cab")
        gl = [(y0 + 1.5, z + 3.05), (y0 + 2.35, z + 4.5), (y1 - 5.7, z + 4.55), (y1 - 4.35, z + 3.05)]
        self.prism(gl, "x", x0 + 0.4, x1 - 0.4, "GlassDark", "car_glass")
        self.box(x0 + 0.1, y1 - 0.25, z + 1.9, x0 + 1.0, y1 - 0.15, z + 2.3, "Ceramic")
        self.box(x1 - 1.0, y1 - 0.25, z + 1.9, x1 - 0.1, y1 - 0.15, z + 2.3, "Ceramic")
        self.box(x0 + 0.1, y0 + 0.15, z + 2.0, x0 + 1.0, y0 + 0.25, z + 2.4, "CarRed")
        self.box(x1 - 1.0, y0 + 0.15, z + 2.0, x1 - 0.1, y0 + 0.25, z + 2.4, "CarRed")
        for wy in (y0 + 2.6, y1 - 2.8):
            for wx in (x0 + 0.35, x1 - 0.35):
                ob = self.cyl(0, 0, -0.4, 0.4, 1.05, "Tyre", 20)
                ob.rotation_euler = (0, math.pi / 2, 0)
                ob.location = (wx * F, wy * F, (z + 1.05) * F)
                ob = self.cyl(0, 0, -0.42, 0.42, 0.6, "Steel", 16)
                ob.rotation_euler = (0, math.pi / 2, 0)
                ob.location = (wx * F, wy * F, (z + 1.05) * F)

    # -------------------------------------------------------------- trees
    def palm(self, x, y, z, h=26.0, lean=(0.08, 0.03)):
        segs = 8
        for i in range(segs):
            za = z + h * i / segs
            zb = z + h * (i + 1) / segs
            r = 0.55 - 0.15 * i / segs
            ox, oy = lean[0] * (za - z), lean[1] * (za - z)
            self.revolve([(r + 0.05, 0), (r, zb - za)], x + ox, y + oy, za, "Trunk", 10, name="palm")
        tx, ty = x + lean[0] * h, y + lean[1] * h
        top = z + h
        self.sphere(tx, ty, top, 0.9, "Trunk", 1)
        for k in range(16):
            ang = 2 * math.pi * k / 16 + 0.3 * (k % 2)
            ln = 8.5 + 1.5 * ((k * 7) % 3) / 2
            rise = 2.5 if k % 2 else 1.2
            self.frond(tx, ty, top, ang, ln, rise)

    def frond(self, x, y, z, ang, ln, rise, n=28):
        """Feathery drooping palm frond (serrated leaf strip)."""
        bm = bmesh.new()
        ca, sa = math.cos(ang), math.sin(ang)
        prev = None
        for i in range(n + 1):
            t = i / n
            d = t * ln
            zc = rise * math.sin(math.pi * t * 0.6) - 5.5 * t ** 2.2
            hw = 1.6 * (math.sin(math.pi * min(1.0, t * 1.05)) ** 0.7) * (1.0 if i % 2 else 0.45) + 0.02
            cxp, cyp = x + ca * d, y + sa * d
            px, py = -sa * hw, ca * hw
            vl = bm.verts.new(((cxp + px) * F, (cyp + py) * F, (z + zc - 0.35 * hw) * F))
            vc = bm.verts.new((cxp * F, cyp * F, (z + zc) * F))
            vr = bm.verts.new(((cxp - px) * F, (cyp - py) * F, (z + zc - 0.35 * hw) * F))
            if prev:
                bm.faces.new((prev[0], prev[1], vc, vl))
                bm.faces.new((prev[1], prev[2], vr, vc))
            prev = (vl, vc, vr)
        return self._obj("frond", bm, "Leaf")

    def tree(self, x, y, z, r=7.0):
        self.cyl(x, y, z, z + 8, 0.7, "Trunk", 10, "trunk")
        import random
        rnd = random.Random(int(x * 13 + y * 7))
        for i in range(7):
            dx, dy, dz = rnd.uniform(-r * .5, r * .5), rnd.uniform(-r * .5, r * .5), rnd.uniform(0, r * .6)
            self.sphere(x + dx, y + dy, z + 10 + dz, r * rnd.uniform(0.5, 0.75), "Leaf", 2, 0.85)

    # -------------------------------------------------------------- build
    def build(self):
        Lz = L
        # ---------------- SITE
        self.coll("SITE")
        self.box(-600, -600, -0.3, 600, 40.0, -0.02, "Earth", "ground")
        self.box(-600, 40.0, -0.3, 600, 44.0, 0.25, "Concrete", "verge")
        self.box(-600, 44.0, -0.3, 600, 66.0, 0.0, "Asphalt", "road")
        self.box(-600, 66.0, -0.3, 600, 72.0, 0.5, "Concrete", "footpath")
        self.box(-600, 72.0, -0.3, 600, 600.0, -0.02, "Earth", "ground_n")
        for i in range(-60, 60):
            self.box(i * 10 + 2, 54.85, 0.0, i * 10 + 7, 55.15, 0.02, "Marking", "lane")
        # ramp from road into stilt
        self.prism([(40.0, 0.25), (40.0, L.GF), (43.0, 0.25)], "x", 0.0, 30.0, "Concrete", "ramp")
        # neighbouring compound walls (context)
        self.box(-0.6, -2, 0, -0.1, 40, 5.0, "Concrete", "nbr_w")
        self.box(30.1, -2, 0, 30.6, 40, 5.0, "Concrete", "nbr_e")
        self.palm(-16, 42.5, 0.25, 30, lean=(-0.05, 0.02))
        self.palm(40.0, 43.0, 0.25, 26, lean=(0.05, 0.04))
        self.palm(-14, 70.0, 0.5, 25, lean=(0.05, -0.02))
        self.tree(-12, 8, 0, 8)
        self.tree(44, 18, 0, 7)

        # ---------------- GROUND FLOOR
        self.coll("GF")
        self.box(0, 0, 0, 30, 40, L.GF, "Concrete", "plinth")
        self.box(0.2, 0.2, L.GF - 0.02, 29.8, 39.8, L.GF + 0.01, "Pavers", "pavers")
        # parking markings
        for (x0, y0, x1, y1) in [(1.5, 24.0, 10.2, 39.4), (12.0, 24.0, 21.2, 39.4), (1.6, 2.0, 10.4, 19.6),
                                 (15.8, 2.0, 22.6, 19.6)]:
            for (a, b, c, d) in [(x0, y0, x0 + 0.25, y1), (x1 - 0.25, y0, x1, y1), (x0, y0, x1, y0 + 0.25)]:
                self.box(a, b, L.GF + 0.01, c, d, L.GF + 0.03, "Marking", "bay")
        # columns (stilt)
        for (x, y) in L.COLUMNS:
            self.stilt_column(x, y)
        # beams
        for (x0, y0, x1, y1) in L.BEAMS:
            hw = 0.395  # a hair wider than the 9" walls (avoids coplanar faces)
            edge = lambda v, lo, hi: (v + 0.05 if v <= lo else (v - 0.05 if v >= hi else v))  # noqa: E731
            if abs(y0 - y1) < 1e-6:
                if y0 in (0.375, 39.625):   # perimeter beams run past the ends
                    xa, xb = x0 - 0.02, x1 + 0.02
                else:                       # inner beams stop short of the perimeter faces
                    xa, xb = edge(x0, 0.0, 30.0), edge(x1, 0.0, 30.0)
                self.box(xa, y0 - hw, L.GF_TOP - L.BEAM_D, xb, y0 + hw, L.GF_TOP - 0.02, "WallPink", "beam")
            else:
                ya, yb = edge(y0, 0.0, 40.0), edge(y1, 0.0, 40.0)
                if x0 not in (0.375, 29.625):
                    ya, yb = ya + (0.4 if ya < 1 else 0), yb - (0.4 if yb > 39 else 0)
                self.box(x0 - hw, ya, L.GF_TOP - L.BEAM_D, x0 + hw, yb, L.GF_TOP - 0.02, "WallPink", "beam")
        # cusped arches facing the road
        for (a, b) in L.STILT_ARCHES:
            spring = L.GF + L.STILT_ARCH_SPRING
            top = L.GF_TOP - L.BEAM_D
            self.spandrel("x", 39.625, 0.75, a, b, spring, top, True, "WallPink", "stilt_arch")
            self.arch_trim("x", 40.0, 1, a, b, spring, top - spring - 0.15)
        for w in L.WALLS:
            if w["level"] == "GF":
                self.wall(w)
                if w["top"] < L.GF_TOP:  # screen wall coping
                    self._coping(w)
        self.stair_storey(L.GF)
        # first floor slab (void over stair except north landing)
        self.coll("FF")
        S = L.STAIR
        ix0, iy0, ix1, iy1 = S["inner"]
        yl = S["floor_landing_y"]
        zs0, zs1 = L.GF_TOP, L.FF
        for (x0, y0, x1, y1) in [(0, 0, 30, iy0), (0, iy0, ix0, 40), (ix0, yl, 30, 40), (ix1, iy0, 30, yl)]:
            self.box(x0, y0, zs0, x1, y1, zs1 - 0.05, "Concrete", "ff_slab")
        # floor finishes
        for lvl, name, (x0, y0, x1, y1), fin in L.ROOMS:
            if lvl == "FF" and fin:
                self.box(x0, y0, zs1 - 0.06, x1, y1, zs1, "FloorStone" if fin == "stone" else "Tile", "floor")
        self.box(ix0, yl, zs1 - 0.06, ix1, iy1, zs1, "Sandstone", "landing")
        # floor band (cream string course) all round
        self._band(zs0 - 0.05, zs1 + 0.15)

        # ---------------- FIRST FLOOR
        for w in L.WALLS:
            if w["level"] == "FF":
                self.wall(w)
        self.arcade()
        self.stair_storey(L.FF, last=False)
        self.box(0.75, 0.75, L.FF_TOP - 0.04, 29.25, 39.25, L.FF_TOP - 0.01, "Plaster", "ceiling")
        # eaves (chhajja) running along north and south at roof level
        for (u0, u1) in [(-0.6, 2.0), (10.0, 22.5), (29.5, 30.6)]:
            self.chhajja("x", 40.0, 1, u0, u1, L.FF_TOP - 0.9, proj=1.5)
        self.chhajja("x", 0.0, -1, -0.6, 30.6, L.FF_TOP - 0.9, proj=1.5)

        # ---------------- ROOF
        self.coll("ROOF")
        for (x0, y0, x1, y1) in [(0, 0, 30, iy0), (0, iy0, ix0, 40), (ix0, yl, 30, 40), (ix1, iy0, 30, yl)]:
            self.box(x0, y0, L.FF_TOP, x1, y1, L.ROOF - 0.05, "Concrete", "roof_slab")
        self.box(0.75, 0.75, L.ROOF - 0.06, 21.625, 39.25, L.ROOF, "RoofTile", "terrace")
        self.box(21.625, 0.75, L.ROOF - 0.06, 29.25, 24.625, L.ROOF, "RoofTile", "terrace")
        self.box(ix0, yl, L.ROOF - 0.06, ix1, iy1, L.ROOF, "Sandstone", "landing")
        self._band(L.FF_TOP - 0.05, L.ROOF + 0.2)
        for w in L.WALLS:
            if w["level"] == "ROOF":
                self.wall(w)
                ax, ay = w["a"]
                bx, by = w["b"]
                horiz = abs(ay - by) < 1e-6
                axis = "x" if horiz else "y"
                c = ay if horiz else ax
                u0, u1 = (min(ax, bx), max(ax, bx)) if horiz else (min(ay, by), max(ay, by))
                if w["name"].startswith("par_"):
                    self.kangura(axis, c, w["t"], u0, u1, w["top"])
        # mumty roof slab
        mz = L.ROOF + L.MUMTY_H
        self.box(21.4, 24.4, mz, 30.0, 40.0, mz + 0.5, "Concrete", "mumty_slab")
        self.box(21.3, 24.3, mz - 0.25, 30.15, 40.15, mz, "Trim", "mumty_band")
        # mumty chhajja over its roof door
        self.chhajja("y", 21.625, -1, 36.0, 39.6, L.ROOF + 7.3, proj=1.1, brackets=True)
        self.mumty_top(mz)
        # chhatris on solid corner towers
        ct = L.ROOF + L.PARAPET_H + 0.95
        for (x0, y0, size) in self.CHHATRIS:
            self.box(x0, y0, L.ROOF, x0 + size, y0 + size, ct, "WallPink", "c_tower")
            self.box(x0 - 0.1, y0 - 0.1, ct - 0.3, x0 + size + 0.1, y0 + size + 0.1, ct, "Trim", "c_band")
            self.chhatri(x0, y0, size, ct)
        # starter bars at columns (future floors)
        for (x, y) in L.COLUMNS:
            if 22 <= x <= 30 and 25 <= y <= 40:
                continue  # inside mumty
            if any(x0 - 0.5 <= x <= x0 + s + 0.5 and y0 - 0.5 <= y <= y0 + s + 0.5 for x0, y0, s in self.CHHATRIS):
                continue
            for dx in (-0.3, 0.3):
                for dy in (-0.3, 0.3):
                    self.cyl(x + dx, y + dy, L.ROOF, L.ROOF + 2.0, 0.04, "Rebar", 6, "starter_bar")
                    self.sphere(x + dx, y + dy, L.ROOF + 2.0, 0.09, "Cap", 1)
            self.box(x - 0.55, y - 0.55, L.ROOF, x + 0.55, y + 0.55, L.ROOF + 0.25, "Concrete", "col_stub")

        self.extras()

        # ---------------- FURNITURE
        self.coll("FURNITURE")
        for lvl, kind, rect, extra in L.FURNITURE:
            self.furniture(lvl, kind, rect, extra)
        # bay labels on floor (painted numbers skipped)

    def extras(self):
        """Style-specific additions (overridden by other styles)."""

    def stilt_column(self, x, y):
        h = L.COL / 2 + 0.04
        self.box(x - h, y - h, L.GF, x + h, y + h, L.GF_TOP - L.BEAM_D, "WallPink", "column")
        self.box(x - h - 0.12, y - h - 0.12, L.GF, x + h + 0.12, y + h + 0.12, L.GF + 0.8, "Trim", "col_base")
        self.box(x - h - 0.1, y - h - 0.1, L.GF_TOP - L.BEAM_D - 0.35, x + h + 0.1, y + h + 0.1,
                 L.GF_TOP - L.BEAM_D, "Trim", "col_cap")

    def mumty_top(self, mz):
        for (axis, c, u0, u1) in (("x", 24.65, 21.4, 30.0), ("x", 39.75, 21.4, 30.0),
                                  ("y", 21.65, 24.4, 40.0), ("y", 29.75, 24.4, 40.0)):
            self._wbox(axis, c - 0.25, c + 0.25, u0, u1, mz + 0.5, mz + 1.6, "WallPink", "mumty_par")
            self.kangura(axis, c, 0.5, u0, u1, mz + 1.6)

    def _coping(self, w):
        (ax, ay), (bx, by) = w["a"], w["b"]
        horiz = abs(ay - by) < 1e-6
        axis = "x" if horiz else "y"
        c = ay if horiz else ax
        u0, u1 = (min(ax, bx), max(ax, bx)) if horiz else (min(ay, by), max(ay, by))
        t = w["t"]
        self._wbox(axis, c - t / 2 - 0.08, c + t / 2 + 0.08, u0, u1, w["top"], w["top"] + 0.25, "Trim", "coping")
        # little jaali panels on top of the screen walls for cross ventilation
        u = u0 + 1.5
        while u + 3.0 < u1 - 1.0:
            self.jaali(axis, c, u, u + 3.0, w["top"] + 0.25, w["top"] + 2.25, t=0.25)
            self._wbox(axis, c - t / 2 - 0.05, c + t / 2 + 0.05, u - 0.3, u, w["top"] + 0.25, w["top"] + 2.6,
                       "Trim")
            self._wbox(axis, c - t / 2 - 0.05, c + t / 2 + 0.05, u + 3.0, u + 3.3, w["top"] + 0.25,
                       w["top"] + 2.6, "Trim")
            u += 4.5

    def _band(self, z0, z1):
        """Cream string course around the building at slab level."""
        p = 0.15
        self.box(-p, 40.0 - 0.01, z0, 30 + p, 40.0 + p, z1, "Trim", "band")
        self.box(-p, -p, z0, 30 + p, 0.01, z1, "Trim", "band")
        self.box(-p, 0, z0, 0.01, 40, z1, "Trim", "band")
        self.box(29.99, 0, z0, 30 + p, 40, z1, "Trim", "band")

    def arcade(self):
        A = L.ARCADE
        y, t, base, top = A["y"], A["t"], A["base"], A["top"]
        piers = A["piers"]
        spring = base + A["spring"]
        crown = base + A["crown"]
        for i, px in enumerate(piers):
            hw = t / 2
            x0 = max(0.0, px - hw)
            x1 = min(30.0, px + hw)
            self.box(x0, y - hw, base, x1, y + hw, top, "WallPink", "pier")
            self.box(x0 - 0.1, y - hw - 0.1, base, x1 + 0.1, y + hw + 0.1, base + 0.6, "Trim", "pier_base")
            self.box(x0 - 0.12, y - hw - 0.12, spring - 0.3, x1 + 0.12, y + hw + 0.12, spring, "Trim", "pier_cap")
        for pa, pb in zip(piers, piers[1:]):
            a, b = pa + t / 2, pb - t / 2
            self.spandrel("x", y, t, a, b, spring, crown, True, "WallPink", "arcade_arch")
            self.arch_trim("x", 0.0, -1, a, b, spring, crown - spring - 0.15)
            # low jaali railing
            self.jaali("x", y, a, b, base, base + A["parapet"], t=0.25)
            self._wbox("x", y - t / 2, y + t / 2, a, b, base + A["parapet"], base + A["parapet"] + 0.2, "Trim")
        self.box(0, 0, crown, 30, 0.75, top, "WallPink", "arcade_lintel")


# --------------------------------------------------------------------------
# post-processing
# --------------------------------------------------------------------------
def join_by_material(colls):
    """Merge every collection's objects per material (fast to render/export)."""
    for cname, coll in colls.items():
        groups = {}
        for ob in list(coll.objects):
            if ob.type != "MESH":
                continue
            # bake transform into mesh data
            mb = ob.matrix_basis.copy()
            if mb != Matrix.Identity(4):
                ob.data.transform(mb)
                ob.matrix_basis = Matrix.Identity(4)
            mname = ob.data.materials[0].name if ob.data.materials else "none"
            groups.setdefault(mname, []).append(ob)
        for mname, obs in groups.items():
            bm = bmesh.new()
            for ob in obs:
                bm.from_mesh(ob.data)
            me = bpy.data.meshes.new(f"{cname}__{mname}")
            bm.to_mesh(me)
            bm.free()
            me.materials.append(bpy.data.materials[mname])
            for ob in obs:
                old = ob.data
                bpy.data.objects.remove(ob)
                if old.users == 0:
                    bpy.data.meshes.remove(old)
            nob = bpy.data.objects.new(f"{cname}__{mname}", me)
            coll.objects.link(nob)


def apply_cut(z_ft, cut_mat):
    """Section the whole model at height z (feet): remove everything above and
    cap the cut faces with a dark poché material."""
    zc = z_ft * F
    for ob in list(bpy.data.objects):
        if ob.type != "MESH" or (ob.name.startswith("SITE__") and ob.name not in ("SITE__Leaf", "SITE__Trunk")):
            continue
        me = ob.data
        bm = bmesh.new()
        bm.from_mesh(me)
        if ob.name in ("SITE__Leaf", "SITE__Trunk"):
            bm.free()
            bpy.data.objects.remove(ob)
            continue
        if not bm.verts or min(v.co.z for v in bm.verts) >= zc:
            bm.free()
            bpy.data.objects.remove(ob)
            continue
        if max(v.co.z for v in bm.verts) <= zc:
            bm.free()
            continue
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, zc), plane_no=(0, 0, 1), clear_outer=True)
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if cut_mat.name not in [m.name for m in me.materials]:
            me.materials.append(cut_mat)
        idx = [m.name for m in me.materials].index(cut_mat.name)
        try:
            filled = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
            for f in filled["faces"]:
                f.material_index = idx
        except Exception:
            pass
        bm.to_mesh(me)
        bm.free()


def build(cut_z=None, style="rajasthani"):
    if style == "odia":
        from style_odia import OdiaBuilder
        b = OdiaBuilder()
    elif style == "goan":
        from style_goan import GoanBuilder
        b = GoanBuilder()
    elif style == "kerala":
        from style_kerala import KeralaBuilder
        b = KeralaBuilder()
    elif style == "chettinad":
        from style_chettinad import ChettinadBuilder
        b = ChettinadBuilder()
    else:
        b = Builder()
    b.reset()
    b.build()
    join_by_material(b.colls)
    if cut_z is not None:
        apply_cut(cut_z, b.mats["Cut"])
    return b
