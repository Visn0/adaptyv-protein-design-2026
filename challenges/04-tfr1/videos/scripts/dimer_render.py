#!/usr/bin/env python3
"""Blender side of the dimer still - run by `dimer_still.py compose`.

Loads the oriented crystal dimer and the two copies of one design, styles the
receptor by domain and the design in its reel accent, and renders a single RGBA
frame for the compositor to lay over the backdrop.

    blender -b --python dimer_render.py -- spec.json
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

QUALITY = 4
STYLE = dict(quality=QUALITY, peptide_shape="Sharp",
             helix_thickness=0.45, helix_width=2.3)


def linear(hex_color: str) -> tuple[float, float, float, float]:
    """sRGB hex -> Blender's linear RGBA, so renders match the HTML backdrop."""
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

    # One molecule, three style branches: the domain boundaries are residue
    # ranges, so a selection per domain covers the whole chain exactly once and
    # the receptor still reads as a single body.
    receptor = mn.Molecule.load(structures / "dimer.pdb", name="dimer")
    for selection, hue in spec["domains"]:
        receptor.add_style("cartoon", selection=selection,
                           color=linear(hue), **STYLE)

    molecules = [receptor]
    for protomer in "AB":
        path = structures / f"binder-{spec['rank']:02d}{protomer}.pdb"
        binder = mn.Molecule.load(path, name=f"binder-{protomer}")
        binder.add_style("cartoon", color=linear(spec["binder"]), **STYLE)
        molecules.append(binder)

    xyz = np.asarray(sum((m.get_view() for m in molecules), []))
    canvas.look_at(xyz.tolist(), viewpoint="front")
    bpy.context.view_layer.update()
    canvas.look_at(xyz.tolist(), margin=0.03)

    scene = bpy.context.scene
    scene.frame_start = scene.frame_end = 0
    scene.render.filepath = str(frames / "frame_")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    print(f"[dimer] rendering -> {frames}", flush=True)
    bpy.ops.render.render(animation=True)


main()
