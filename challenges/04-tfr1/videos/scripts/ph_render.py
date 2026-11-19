#!/usr/bin/env python3
"""Blender side of the pH clip - run by `ph_switch.py render`.

Draws the champion's interface: the binder on the receptor, its two engineered
histidines as spheres, and the two conserved lysines they sit against.  The
same scene is rendered twice, once with the histidines in their blood-pH colour
and once in their endosome-pH colour, over an identical camera drift, so the
compositor can cross-fade one into the other.  Nothing moves between the two
passes except colour: we have one bound pose and no predicted unbinding.

    blender -b --python ph_render.py -- spec.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

bpy.ops.preferences.addon_enable(module="bl_ext.user_default.molecularnodes")
import bl_ext.user_default.molecularnodes as mn  # noqa: E402

CARTOON = dict(quality=4, peptide_shape="Sharp",
               helix_thickness=0.45, helix_width=2.3)
DRIFT_DEG = 14.0          # a slow turn, so the still frames do not read as dead


def linear(hex_color: str) -> tuple[float, float, float, float]:
    """sRGB hex -> Blender's linear RGBA, so renders match the HTML panel."""
    srgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
           for c in srgb]
    return (*lin, 1.0)


def main() -> None:
    spec = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
    structures = Path(spec["structures"])
    frames = Path(spec["frames"])
    frames.mkdir(parents=True, exist_ok=True)
    size = spec["size"]

    canvas = mn.Canvas(engine="EEVEE", resolution=(size, size), transparent=True)
    canvas.view_transform = "Standard"
    canvas.exposure = 1.8
    bpy.context.scene.eevee.use_shadows = False

    receptor = mn.Molecule.load(structures / "receptor.pdb", name="receptor")
    receptor.add_style("cartoon", color=linear(spec["receptor"]), **CARTOON,
                       material=mn.material.Transparent(transparency=0.30,
                                                        fresnel=False))
    # the anchors are positive at both pH values, so they never change colour
    receptor.add_style("spheres", selection=spec["lysines"],
                       color=linear(spec["lysine_hue"]), scale=0.85)

    binder = mn.Molecule.load(structures / "binder.pdb", name="binder")
    binder.add_style("cartoon", color=linear(spec["binder"]), **CARTOON)
    binder.add_style("spheres", selection=spec["histidines"],
                     color=linear(spec["histidine_hue"]), scale=0.95)

    pivot = bpy.data.objects.new("pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    for mol in (receptor, binder):
        mol.object.parent = pivot

    # Frame the binder and the two anchors: the receptor is mostly out of shot
    # on purpose, because the clip is about one interface, not the whole body.
    focus = np.asarray(binder.get_view())
    radius = float(np.linalg.norm(focus - focus.mean(axis=0), axis=1).max())
    centre = focus.mean(axis=0)
    ring = [centre + radius * np.array([math.cos(a), math.sin(a), z])
            for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)
            for z in (-0.8, 0.8)]
    canvas.look_at([p.tolist() for p in ring], viewpoint="front")
    bpy.context.view_layer.update()
    canvas.look_at([p.tolist() for p in ring], margin=0.10)

    keying = bpy.context.preferences.edit
    keying.keyframe_new_interpolation_type = "LINEAR"
    for frame, angle in ((0, 0.0), (spec["total"], math.radians(DRIFT_DEG))):
        pivot.rotation_euler[2] = angle
        pivot.keyframe_insert("rotation_euler", index=2, frame=frame)

    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = int(spec["start"]), int(spec["end"])
    scene.render.filepath = str(frames / "frame_")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    print(f"[ph] rendering frames {scene.frame_start}-{scene.frame_end}"
          f" -> {frames}", flush=True)
    bpy.ops.render.render(animation=True)


main()
