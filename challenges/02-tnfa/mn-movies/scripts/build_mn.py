"""Molecular Nodes binding animations for the C2 MD trajectories.

Runs INSIDE Blender (headless):

    blender -b --python build_mn.py -- --design d7x-t3-3 --mode still --engine cycles
    blender -b --python build_mn.py -- --design d7x-t3-3 --mode anim  --engine cycles

Loads the packed MD frames (multi-model PDB), styles them to the project colour
standard (binder pink / target blue / interface amber), sets a turntable camera
and renders either a still (a look check) or the full animation.

Interface residue lists come from the md-movies run summaries
(~/c2-work/md-anim/runs/<design>/summary.json), so the amber patch is the same
interface the 3Dmol movies paint.

Any other complex renders through --cif, which needs --binder-chain and
--interface instead of a preset. A single-model structure still animates: the
turntable is a camera orbit, so only the frame series is MD-specific.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import bpy

import bl_ext.user_default.molecularnodes as mn

# ---------------------------------------------------------------- constants
RUNS = Path.home() / "c2-work/md-anim/runs"

DESIGNS = {
    "d7x-t3-3": dict(
        frames=RUNS / "d7x-t3-3/artifacts/md/d7x-t3-3_frames.pdb",
        binder="A",
        interface=(
            "(chainID A and resid 10 21 26 27 30 33 34 37 40 41 44 45 46) "
            "or (chainID B and resid 16 18 108 110 138 139 140 141) "
            "or (chainID D and resid 70 90 92 132 133)"
        ),
    ),
    "b2x-d12-2": dict(
        frames=RUNS / "b2x-d12-2/artifacts/md/b2x-d12-2_frames.pdb",
        binder="A",
        interface=(
            "(chainID A and resid 1 2 5 6 8 9 12 13 15 16 17 19 20 34 35 36 37 "
            "86 89 90 91 92) "
            "or (chainID B and resid 67 68 69 70 72 74 85 87 92 103 130 131 "
            "132 133) "
            "or (chainID C and resid 15 60 103 104 105 108 110 138 139 140 141)"
        ),
    ),
}

PINK = (232, 121, 249)   # #e879f9  binder
BLUE = (96, 165, 250)    # #60a5fa  target
AMBER = (251, 191, 36)   # #fbbf24  interface
BG = (11, 15, 20)        # #0b0f14  background


def lin(c):
    """sRGB 0-255 tuple -> linear RGBA, the space colour attributes live in."""

    def f(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="d7x-t3-3",
                    help="preset name, or the output label when --cif is given")
    ap.add_argument("--cif", help="render this structure instead of a preset")
    ap.add_argument("--binder-chain", default="A", help="with --cif")
    ap.add_argument("--interface", help="MN selection painted amber; with --cif")
    ap.add_argument("--mode", default="still", choices=["still", "anim"])
    ap.add_argument("--engine", default="cycles", choices=["cycles", "eevee"])
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--margin", type=float, default=0.05)
    ap.add_argument("--elevation", type=float, default=12.0)
    ap.add_argument("--orbit-frames", type=int, default=120)
    ap.add_argument("--hold", type=int, default=24)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--still-frame", type=int, default=60)
    ap.add_argument("--outdir", default=str(Path.home() / "c2-work/mn-anim"))
    ap.add_argument("--keep-backdrop", action="store_true")
    ap.add_argument("--light-boost", type=float, default=2.0)
    ap.add_argument("--debug", action="store_true")
    return ap.parse_args(argv)


def main() -> None:
    args = parse_args()
    res = tuple(int(v) for v in args.res.split("x"))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if args.cif:
        if not args.interface:
            sys.exit("--cif needs --interface (the amber selection)")
        spec = dict(frames=Path(args.cif), binder=args.binder_chain,
                    interface=args.interface)
    elif args.design in DESIGNS:
        spec = DESIGNS[args.design]
    else:
        sys.exit(f"unknown design {args.design!r}; presets: {sorted(DESIGNS)}, "
                 "or pass --cif")
    t0 = time.time()

    # -- studio preset: camera + lights + world; backdrop optional
    canvas = mn.Canvas()
    canvas.load_preset()
    print("[mn] preset objects:", sorted(o.name for o in bpy.data.objects))
    if not args.keep_backdrop:
        canvas.clear()  # keeps camera, lights, world, render settings

    # -- world + colour management
    # the preset world shader renders the background darker than the value it
    # is given (measured ~0.55x); compensate so the render matches #0b0f14
    bg = lin(BG)
    canvas.background = (bg[0] * 1.8, bg[1] * 1.8, bg[2] * 1.8, 1.0)
    bpy.context.scene.view_settings.view_transform = "Standard"

    if args.debug:
        w = bpy.context.scene.world
        print("[mn] world nodes:")
        for n in w.node_tree.nodes:
            print("   ", n.name, n.type,
                  [(i.name, getattr(i, "default_value", None)) for i in n.inputs])
        for o in bpy.data.objects:
            if o.type == "LIGHT":
                print("   light", o.name, o.data.type, "energy", o.data.energy)
    if args.light_boost != 1.0:
        for o in bpy.data.objects:
            if o.type == "LIGHT":
                o.data.energy = o.data.energy * args.light_boost
        print(f"[mn] lights boosted x{args.light_boost}")

    # -- the molecule
    mol = mn.Molecule.load(spec["frames"], name=args.design)
    u = mol.universe
    n_frames = u.trajectory.n_frames
    print(f"[mn] loaded {args.design}: {len(u.atoms)} atoms, "
          f"{n_frames} frames, chains {sorted(set(u.atoms.chainIDs))}")
    print("[mn] props:", [p for p in ("subframes", "interpolate", "offset",
                                      "update_with_scene", "n_frames")
                          if hasattr(mol.props, p)])

    # playback: one MD frame spans two scene frames, interpolated. A static
    # co-fold has nothing to interpolate, so leave its props alone.
    if n_frames > 1:
        mol.props.subframes = 1
        mol.props.interpolate = True

    # -- styles, project colour standard
    mol.add_style("cartoon", selection=f"chainID {spec['binder']}", color=lin(PINK))
    mol.add_style("cartoon", selection=f"not chainID {spec['binder']}", color=lin(BLUE))
    mol.add_style("ball_and_stick", selection=spec["interface"], color=lin(AMBER))

    # -- render settings
    canvas.resolution = res
    canvas.fps = args.fps
    if args.engine == "cycles":
        canvas.engine = mn.scene.Cycles(samples=args.samples, device="CPU",
                                        denoise=True, denoise_gpu=False)
    else:
        canvas.engine = mn.scene.EEVEE(samples=args.samples)
    total = args.orbit_frames + args.hold
    canvas.frame_start = 1
    canvas.frame_end = total

    # -- turntable camera
    bpy.context.scene.frame_set(1)
    try:
        points = mol.position
    except Exception:
        points = mol._scaled_position
    import numpy as np
    points = np.asarray(points, dtype=float)
    centre, radius = mn.framing.enclosing_sphere(points)
    print(f"[mn] centre {centre.round(2)} radius {radius:.2f}")

    cam_data = bpy.context.scene.camera.data
    el = math.radians(args.elevation)
    ce, se = math.cos(el), math.sin(el)
    # constant turntable distance: the largest distance the exact solver needs
    # across the whole orbit, so no angle crops and none wastes the frame
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

    aim = bpy.data.objects.new("MN_aim", None)
    orbit = bpy.data.objects.new("MN_orbit", None)
    for o in (aim, orbit):
        bpy.context.scene.collection.objects.link(o)
        o.location = tuple(float(v) for v in centre)

    camera = bpy.context.scene.camera
    camera.parent = orbit
    camera.location = (dist * math.cos(el), 0.0, dist * math.sin(el))
    for c in list(camera.constraints):
        camera.constraints.remove(c)
    con = camera.constraints.new("TRACK_TO")
    con.target = aim
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"

    orbit.rotation_euler = (0, 0, 0)
    orbit.keyframe_insert("rotation_euler", frame=1)
    orbit.rotation_euler = (0, 0, math.tau)
    orbit.keyframe_insert("rotation_euler", frame=1 + args.orbit_frames)
    action = orbit.animation_data.action
    fcurves = list(getattr(action, "fcurves", []) or [])
    if not fcurves:
        # Blender 4.4+ stores fcurves in layered action strips
        for layer in action.layers:
            for strip in layer.strips:
                for cbag in strip.channelbags:
                    fcurves.extend(cbag.fcurves)
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    print(f"[mn] orbit fcurves linearised: {len(fcurves)}")
    print(f"[mn] camera distance {dist:.1f}, elevation {args.elevation} deg, "
          f"orbit {args.orbit_frames} frames + {args.hold} hold")

    # -- render
    if args.mode == "still":
        out = outdir / f"still_{args.design}_{args.engine}.png"
        canvas.snapshot(path=str(out), frame=args.still_frame)
        print("[mn] still:", out)
    else:
        out = outdir / f"{args.design}_mn-binding.mp4"
        canvas.animation(path=str(out), fps=args.fps)
        print("[mn] animation:", out)

    print(f"[mn] done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
