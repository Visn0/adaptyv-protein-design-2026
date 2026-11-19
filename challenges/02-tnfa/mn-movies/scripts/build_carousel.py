"""Design carousel: the TNF-alpha surface rotating, one design per second.

Renders INSIDE Blender (headless):

    blender -b --python build_carousel.py -- --carousel-dir ~/c2-work/mn-anim/carousel
    blender -b --python build_carousel.py -- --mode still --still-frame 1

Reads the prepared structures (`prep_carousel.py`): one shared target PDB and
one binder PDB per design, all in the same frame.  The target is a grey
surface, the binders are light-blue cartoons; every second the visible binder
switches to the next design while the camera makes one slow full turn.

Look: light background, soft studio light, portrait 1080x1350 — the reference
style (Apheris x Wells Wood showcase video).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np

import bl_ext.user_default.molecularnodes as mn
from bl_ext.user_default.molecularnodes import material as mn_material
from nodebpy import shader as s

PINK = (232, 121, 249)   # #e879f9  house binder colour (kept for the record)
BLUE = (119, 201, 235)   # #77c9eb  binder, the reference's light blue
GREY = (196, 205, 209)   # #c4cdd1  target surface
RIM = (150, 162, 168)    # #96a2a8  surface rim (fresnel outline)
BG = (253, 253, 253)     # #fdfdfd  background


def lin(c):
    """sRGB 0-255 tuple -> linear RGBA, the space colour attributes live in."""

    def f(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--carousel-dir",
                    default=str(Path.home() / "c2-work/mn-anim/carousel"))
    ap.add_argument("--mode", default="anim", choices=["anim", "still"])
    ap.add_argument("--engine", default="cycles", choices=["cycles", "eevee"])
    ap.add_argument("--device", default="CPU", choices=["CPU", "GPU"])
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--res", default="1080x1350")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--secs-per-design", type=float, default=1.0)
    ap.add_argument("--margin", type=float, default=0.15)
    ap.add_argument("--elevation", type=float, default=10.0)
    ap.add_argument("--aim-shift", type=float, default=0.0,
                    help="raise the aim point by this fraction of the radius, "
                         "to seat the complex lower in the frame")
    ap.add_argument("--light-boost", type=float, default=1.0)
    ap.add_argument("--world-strength", type=float, default=0.8)
    ap.add_argument("--transparency", type=float, default=0.45,
                    help="target surface transparency (0 opaque, 1 clear)")
    ap.add_argument("--surface", default="ao", choices=["ao", "transparent"],
                    help="target surface material")
    ap.add_argument("--pass", dest="render_pass", default="full",
                    choices=["full", "binder"],
                    help="full scene, or the binder-only alpha pass")
    ap.add_argument("--binder-dir", default="",
                    help="PNG sequence dir for the binder pass")
    ap.add_argument("--still-frame", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0, help="render only N frames")
    ap.add_argument("--probe", action="store_true",
                    help="time frame_set and single-frame render, then exit")
    ap.add_argument("--outdir", default=str(Path.home() / "c2-work/mn-anim"))
    return ap.parse_args(argv)


def main() -> None:
    args = parse_args()
    res = tuple(int(v) for v in args.res.split("x"))
    carousel = Path(args.carousel_dir)
    struct = carousel / "structures"
    manifest = json.loads((carousel / "manifest.json").read_text())
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    canvas = mn.Canvas()
    canvas.load_preset()
    canvas.clear()

    # -- light studio: white world, suns from the preset
    with canvas.world.reset() as surface:
        s.Background(color=(1.0, 1.0, 1.0, 1.0),
                     strength=args.world_strength) >> surface
    bpy.context.scene.view_settings.view_transform = "Standard"
    if args.light_boost != 1.0:
        for o in bpy.data.objects:
            if o.type == "LIGHT":
                o.data.energy = o.data.energy * args.light_boost

    # -- target surface + binder cartoons
    target = mn.Molecule.load(str(struct / "target.pdb"), name="target")
    # translucent surface with a fresnel rim: some folds tuck the binder into
    # a groove and an opaque surface hides them completely
    if args.surface == "transparent":
        surf_mat = mn_material.Transparent(transparency=args.transparency,
                                           fresnel=True,
                                           outline_color=lin(RIM))
    else:
        surf_mat = "Ambient Occlusion"
    target.add_style("surface", selection="all", color=lin(GREY),
                     material=surf_mat)
    print(f"[car] target: {len(target.universe.atoms)} atoms, surface "
          f"material {args.surface}")

    binders, binder_objs = [], []
    for e in manifest:
        m = mn.Molecule.load(str(struct / e["binder_file"]),
                             name=f"b{e['idx']:02d}")
        m.add_style("cartoon", selection="all", color=lin(BLUE),
                    material="Default")
        obj = getattr(m, "obj", None) or bpy.data.objects[f"b{e['idx']:02d}"]
        binders.append(m)
        binder_objs.append(obj)
    print(f"[car] {len(binders)} binders loaded")

    # -- static molecules: drop MN's per-frame entity update handler, it is
    # pure overhead here and costs ~6 s per rendered frame
    from bl_ext.user_default.molecularnodes.handlers import update_entities
    if update_entities in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(update_entities)

    # -- render settings
    canvas.resolution = res
    canvas.fps = args.fps
    if args.engine == "cycles":
        canvas.engine = mn.scene.Cycles(samples=args.samples, device=args.device,
                                        denoise=True, denoise_gpu=False)
    else:
        canvas.engine = mn.scene.EEVEE(samples=args.samples)
    bpy.context.scene.render.use_persistent_data = True
    frames_per_design = args.secs_per_design * args.fps
    total = int(round(len(manifest) * frames_per_design))
    canvas.frame_start = 1
    canvas.frame_end = total
    print(f"[car] {len(manifest)} designs x {args.secs_per_design}s "
          f"= {total} frames at {args.fps} fps")

    # -- one visible binder at a time
    state = {"idx": -1}

    def show(scene, *depsgraph):
        idx = int((scene.frame_current - 1) // frames_per_design)
        idx = max(0, min(idx, len(binder_objs) - 1))
        if idx == state["idx"]:
            return  # only touch the objects on a swap, not every frame
        state["idx"] = idx
        for k, obj in enumerate(binder_objs):
            obj.hide_render = (k != idx)

    bpy.app.handlers.frame_change_pre.append(show)
    show(bpy.context.scene)

    # -- turntable camera, constant distance over the full turn
    bpy.context.scene.frame_set(1)
    points = np.vstack([np.asarray(target._scaled_position, dtype=float)]
                       + [np.asarray(m._scaled_position, dtype=float)
                          for m in binders])
    centre, radius = mn.framing.enclosing_sphere(points)
    el = math.radians(args.elevation)
    ce, se = math.cos(el), math.sin(el)
    bounds = mn.scene.Camera().frame_bounds()
    rel = points - centre
    dist = 0.0
    for a in np.linspace(0.0, math.tau, 25, endpoint=False):
        ca, sa = math.cos(a), math.sin(a)
        forward = -np.array([ca * ce, sa * ce, se])
        right = np.array([-sa, ca, 0.0])
        up = np.cross(right, forward)
        basis = np.array([right, up, forward])
        loc = mn.framing.fit_camera_to_points(rel, basis, bounds, args.margin)
        dist = max(dist, float(np.linalg.norm(loc)))
    print(f"[car] centre {centre.round(2)} radius {radius:.2f} "
          f"camera distance {dist:.1f}")

    aim = bpy.data.objects.new("MN_aim", None)
    orbit = bpy.data.objects.new("MN_orbit", None)
    for o in (aim, orbit):
        bpy.context.scene.collection.objects.link(o)
        o.location = tuple(float(v) for v in centre)
    aim.location.z += args.aim_shift * radius

    camera = bpy.context.scene.camera
    for c in list(camera.constraints):
        camera.constraints.remove(c)
    camera.parent = orbit
    camera.location = (dist * math.cos(el), 0.0, dist * math.sin(el))
    con = camera.constraints.new("TRACK_TO")
    con.target = aim
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"

    orbit.rotation_euler = (0, 0, 0)
    orbit.keyframe_insert("rotation_euler", frame=1)
    orbit.rotation_euler = (0, 0, math.tau)
    orbit.keyframe_insert("rotation_euler", frame=1 + total)
    action = orbit.animation_data.action
    fcurves = list(getattr(action, "fcurves", []) or [])
    if not fcurves:
        for layer in action.layers:
            for strip in layer.strips:
                for cbag in strip.channelbags:
                    fcurves.extend(cbag.fcurves)
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

    if args.probe:
        for f in (1, 2, 3, 4):
            t = time.time()
            bpy.context.scene.frame_set(f)
            dt = time.time() - t
            t = time.time()
            canvas.snapshot(path=str(outdir / "probe.png"), frame=f)
            dr = time.time() - t
            print(f"[probe] frame {f}: frame_set {dt:.2f}s  render {dr:.2f}s")
        return

    # -- render
    try:
        if args.render_pass == "binder":
            # binder only, alpha background, composited over the full pass so
            # binders tucked into a groove still show. The target stays
            # visible to shadow/diffuse rays — the binder keeps its pocket
            # shading — but is invisible to the camera, so nothing occludes it.
            bpy.data.objects["target"].visible_camera = False
            scene = bpy.context.scene
            scene.render.film_transparent = True
            scene.render.image_settings.file_format = "PNG"
            scene.render.image_settings.color_mode = "RGBA"
            bdir = Path(args.binder_dir) if args.binder_dir else (outdir / "binder_frames")
            bdir.mkdir(parents=True, exist_ok=True)
            scene.render.filepath = str(bdir / "binder_")
            print(f"[car] binder pass -> {bdir}")
            bpy.ops.render.render(animation=True)
            print("[car] binder pass done")
        elif args.mode == "still":
            out = outdir / f"carousel_still_{args.still_frame}.png"
            canvas.snapshot(path=str(out), frame=args.still_frame)
            print("[car] still:", out)
        else:
            if args.limit:
                canvas.frame_end = args.limit
            out = outdir / "carousel_raw.mp4"
            canvas.animation(path=str(out), fps=args.fps)
            print("[car] animation:", out)
    finally:
        # MN's unregister at exit removes this handler; put it back so the
        # removal does not raise
        if update_entities not in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.append(update_entities)
    print(f"[car] done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
