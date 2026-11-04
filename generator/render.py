"""
Build the model, render the views and export .blend + .glb.

    /opt/bvenv/bin/python generator/render.py              # everything
    /opt/bvenv/bin/python generator/render.py --views hero --samples 32 --scale 50
    /opt/bvenv/bin/python generator/render.py --export-only
    /opt/bvenv/bin/python generator/render.py --style odia       # Odia / Kalinga variant -> output/odia/

Requires the `bpy` module (pip install bpy) or run inside Blender:
    blender -b -P generator/render.py -- --views hero
"""
import argparse
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_model as BM  # noqa: E402

F = BM.F
OUT = os.path.join(HERE, "..", "output")

# view name -> (camera location ft, target ft, lens mm, cut height ft or None, sun (azimuth, elevation))
VIEWS = {
    "hero":   dict(loc=(50, 86, 5.8), target=(15, 30, 15.5), lens=28, cut=None, sun=(55, 38), shift=0.12),
    "aerial": dict(loc=(-48, 92, 70), target=(15, 18, 10), lens=35, cut=None, sun=(55, 42)),
    "rear":   dict(loc=(58, -52, 26), target=(14, 16, 14), lens=34, cut=None, sun=(150, 45)),
    "street": dict(loc=(-18, 62, 5.6), target=(16, 36, 13.5), lens=26, cut=None, sun=(55, 38), shift=0.08),
    "first_floor": dict(loc=(15, -20, 80), target=(15, 20, 11.5), lens=34, cut=16.0, sun=(160, 60)),
    "ground_floor": dict(loc=(-22, 72, 52), target=(15, 19, 1.0), lens=30, cut=7.0, sun=(160, 60)),
    "interior": dict(loc=(1.6, 12.4, 16.2), target=(12.5, 5.2, 14.6), lens=17, cut=None, sun=(150, 45),
                     interior=True),
}


def setup_scene(samples, scale):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 2
    sc.cycles.transparent_max_bounces = 4
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1200
    sc.render.resolution_percentage = scale
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 90
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    # world: soft sky
    world = bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes.get("Background")
    sky = None
    try:
        sky = nt.nodes.new("ShaderNodeTexSky")
        sky.sky_type = "MULTIPLE_SCATTERING"
        sky.sun_disc = False
        sky.air_density = 1.0
        sky.aerosol_density = 1.6
        nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = 0.22
    except Exception:
        bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1)
        bg.inputs["Strength"].default_value = 1.0
    return sky


def sun(az, el, sky=None):
    for ob in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(ob)
    ld = bpy.data.lights.new("Sun", "SUN")
    ld.energy = 4.2
    ld.angle = math.radians(1.2)
    ld.color = (1.0, 0.95, 0.87)
    ob = bpy.data.objects.new("Sun", ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = (math.radians(90 - el), 0, math.radians(180 - az))
    if sky is not None:
        try:
            sky.sun_elevation = math.radians(el)
            sky.sun_rotation = math.radians((90 - az) % 360)
        except Exception:
            pass


def camera(loc, target, lens, shift=0.0):
    for ob in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(ob)
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_end = 2000
    ob = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(ob)
    p = Vector(loc) * F
    t = Vector(target) * F
    ob.location = p
    d = t - p
    if shift:
        # two-point perspective: keep verticals vertical, use lens shift
        yaw = math.atan2(d.y, d.x) - math.pi / 2
        ob.rotation_euler = (math.radians(90), 0, yaw)
        cd.shift_y = shift
    else:
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob


def interior_lights():
    """Warm lamps in the rooms (for interior render)."""
    for (x, y) in [(6, 12), (22, 12), (6, 32), (19.5, 30), (15, 23)]:
        ld = bpy.data.lights.new("Lamp", "POINT")
        ld.energy = 220
        ld.color = (1.0, 0.82, 0.6)
        ld.shadow_soft_size = 0.4
        ob = bpy.data.objects.new("Lamp", ld)
        ob.location = (x * F, y * F, 19.8 * F)
        bpy.context.scene.collection.objects.link(ob)


STYLE = "rajasthani"


def out_dir(*parts):
    """Rajasthani (the original) writes to output/, other styles to output/<style>/."""
    base = OUT if STYLE == "rajasthani" else os.path.join(OUT, STYLE)
    return os.path.join(base, *parts)


def render_view(name, samples, scale):
    v = dict(VIEWS[name])
    t0 = time.time()
    b = BM.build(cut_z=v["cut"], style=STYLE)
    v.update(b.VIEW_OVERRIDES.get(name, {}))
    sky = setup_scene(samples, scale)
    sun(*v["sun"], sky=sky)
    if v.get("interior"):
        interior_lights()
        bpy.context.scene.render.resolution_y = 1280
    camera(v["loc"], v["target"], v["lens"], v.get("shift", 0.0))
    os.makedirs(out_dir("renders"), exist_ok=True)
    path = out_dir("renders", f"{name}.jpg")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"[render] {name} -> {path} ({time.time() - t0:.0f}s)", flush=True)


def export():
    b = BM.build(style=STYLE)
    os.makedirs(out_dir("model"), exist_ok=True)
    blend = os.path.abspath(out_dir("model", "home_hotel.blend"))
    sky = setup_scene(64, 100)
    sun(55, 38, sky)
    camera(**{k: VIEWS["hero"][k] for k in ("loc", "target", "lens")}, shift=VIEWS["hero"]["shift"])
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    b.simplify_materials()
    glb = os.path.abspath(out_dir("model", "home_hotel.glb"))
    for ob in [o for o in bpy.data.objects if o.type in ("LIGHT", "CAMERA")]:
        bpy.data.objects.remove(ob)
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_apply=True,
                              export_cameras=False, export_lights=False)
    from glb_to_json import convert
    convert(glb, glb.replace(".glb", ".gltf.json"))   # same model as JSON for the web viewer
    print("[export]", blend, glb, flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--views", default=",".join(VIEWS))
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--scale", type=int, default=100)
    ap.add_argument("--export-only", action="store_true")
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--style", default="rajasthani", choices=["rajasthani", "odia", "chettinad", "kerala"])
    a = ap.parse_args(argv)
    global STYLE
    STYLE = a.style
    os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)
    if not a.export_only:
        for name in [n for n in a.views.split(",") if n]:
            render_view(name, a.samples, a.scale)
    if not a.no_export:
        export()


if __name__ == "__main__":
    main()
