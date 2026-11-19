#!/usr/bin/env python3
"""Blender side of the bind/release clip - run by `bind_release.py render`.

The receptor dimer is the fixed target.  Two copies of the design fly in to the
poses the co-fold actually predicts, hold, and fly back out along the same
path.  The scene is rendered twice over identical motion, once with the
histidines neutral and once protonated, so the compositor can cross-fade the
charge change without re-rendering the geometry.

The docked pose is predicted; the travel to and from it is not.  The path here
is a straight glide along the outward normal of the epitope, eased at both
ends - a presentation choice, not a trajectory.

    blender -b --python bind_release_render.py -- spec.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
import numpy as np

bpy.ops.preferences.addon_enable(module="bl_ext.user_default.molecularnodes")
import bl_ext.user_default.molecularnodes as mn  # noqa: E402

# quality 3 rather than the reel's 4: the dimer is twice the geometry and this
# clip is four times the frames, and at this size the ribbons read the same
CARTOON = dict(quality=3, peptide_shape="Sharp",
               helix_thickness=0.45, helix_width=2.3)


def linear(hex_color: str) -> tuple[float, float, float, float]:
    srgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
           for c in srgb]
    return (*lin, 1.0)


def main() -> None:
    spec = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
    structures = Path(spec["structures"])
    frames = Path(spec["frames"])
    frames.mkdir(parents=True, exist_ok=True)

    canvas = mn.Canvas(engine="EEVEE",
                       resolution=(spec["width"], spec["height"]),
                       transparent=True)
    canvas.view_transform = "Standard"
    canvas.exposure = 1.8
    bpy.context.scene.eevee.use_shadows = False

    receptor = mn.Molecule.load(structures / "dimer.pdb", name="dimer")
    for selection, hue in spec["domains"]:
        receptor.add_style("cartoon", selection=selection,
                           color=linear(hue), **CARTOON)
    receptor.add_style("spheres", selection=spec["lysines"],
                       color=linear(spec["lysine_hue"]), scale=0.85)

    centre = np.asarray(receptor.get_view()).mean(axis=0)
    binders = []
    for protomer in "AB":
        binder = mn.Molecule.load(
            structures / f"binder-01{protomer}.pdb", name=f"binder-{protomer}")
        binder.add_style("cartoon", color=linear(spec["binder"]), **CARTOON)
        binder.add_style("spheres", selection=spec["histidines"],
                         color=linear(spec["histidine_hue"]), scale=0.95)
        binders.append(binder)

    # The glide path: straight out from the receptor's centre through each
    # binder, so each copy leaves along the face it binds and never crosses the
    # body of the receptor on its way.
    for binder in binders:
        here = np.asarray(binder.get_view()).mean(axis=0)
        outward = here - centre
        outward = outward / np.linalg.norm(outward)
        away = (outward * spec["travel"]).tolist()
        keying = bpy.context.preferences.edit
        keying.keyframe_new_interpolation_type = "BEZIER"
        keying.keyframe_new_handle_type = "AUTO_CLAMPED"
        for frame, where in ((0, away), (spec["docked"], [0.0, 0.0, 0.0]),
                             (spec["undock"], [0.0, 0.0, 0.0]),
                             (spec["gone"], away)):
            binder.object.location = where
            binder.object.keyframe_insert("location", frame=frame)

    xyz = np.asarray(sum((m.get_view() for m in [receptor, *binders]), []))
    canvas.look_at(xyz.tolist(), viewpoint="front")
    bpy.context.view_layer.update()
    canvas.look_at(xyz.tolist(), margin=0.04)

    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = int(spec["start"]), int(spec["end"])
    scene.render.filepath = str(frames / "frame_")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    print(f"[bind] rendering frames {scene.frame_start}-{scene.frame_end}"
          f" -> {frames}", flush=True)
    bpy.ops.render.render(animation=True)


main()
