#!/usr/bin/env python3
"""Blender side of the challenge-3 reel - run by `mn_reel.py render`.

Loads the fixed receptor plus the ten aligned binders through Molecular Nodes,
parents them to one empty and turns that empty through a single continuous
revolution; the binder visible at any frame is the design whose panel is being
overlaid.  Frames come out RGBA so ffmpeg can lay them over the HTML panel.

The turn and the swaps are keyframed and rendered as one animation rather than
frame by frame: on this machine Blender has no GL driver, so every separate
render call pays ~11 s to stand up a software context and compile shaders -
flat, whatever the scene or the resolution.  One animation pays it once.

    blender -b --python mn_render.py -- spec.json
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

# A cool neutral, dark enough that the three-light rig still models it:
# lighter greys wash flat against the white page, and cast shadows buy
# little more depth for seven times the render time.
TARGET_GREY = "#949aa6"
QUALITY = 4            # cartoon subdivision; the node default of 2 reads coarse
# "Sharp" keeps flat ribbon faces; "Round" makes the cross-section an ellipse,
# so at every thickness the helices read as tubes rather than ribbons - tried
# at 0.6, 0.35, 0.22 and 0.12 and all of them look round.  Stay on Sharp and
# slim the ribbon a little instead, which is the only softening knob there is.
STYLE = dict(quality=QUALITY, peptide_shape="Sharp",
             helix_thickness=0.45, helix_width=2.3)
TURNS = 1.0            # revolutions across the whole reel


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

    canvas = mn.Canvas(engine="EEVEE",
                       resolution=(spec["width"], spec["height"]),
                       transparent=True)
    canvas.view_transform = "Standard"      # keep the hexes the panel uses
    canvas.exposure = 1.8                   # ... and keep them off a white page
    # Cast shadows cost ~10 s of the ~16 s a frame here and are flat-rate: the
    # shadow pool does not shrink with the render resolution.  The reference
    # clip has none either - ambient occlusion carries the depth.
    bpy.context.scene.eevee.use_shadows = False

    target = mn.Molecule.load(structures / "target.pdb", name="target")
    # Matched to the reference clip: the receptor still reads as a solid body,
    # just see-through enough that a design behind it shows.  No fresnel - its
    # grazing-angle rim darkens every edge at once and the receptor then reads
    # as scratched glass.
    target.add_style("cartoon", color=linear(TARGET_GREY), **STYLE,
                     material=mn.material.Transparent(transparency=0.35,
                                                      fresnel=False))
    binders = []
    for i, color in enumerate(spec["colors"], start=1):
        mol = mn.Molecule.load(structures / f"binder-{i:02d}.pdb",
                               name=f"binder-{i:02d}")
        mol.add_style("cartoon", color=linear(color), **STYLE)
        binders.append(mol)

    pivot = bpy.data.objects.new("pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    for mol in [target, *binders]:
        mol.object.parent = pivot

    # Frame the cylinder the assembly sweeps out, so nothing clips at any
    # angle.  A box round it would be its corners too, and frame half as big.
    xyz = np.asarray(sum((m.get_view() for m in [target, *binders]), []))
    radius = float(np.linalg.norm(xyz[:, :2], axis=1).max())
    lo, hi = float(xyz[:, 2].min()), float(xyz[:, 2].max())
    ring = [[radius * math.cos(a), radius * math.sin(a), z]
            for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)
            for z in (lo, hi)]
    canvas.look_at(ring, viewpoint="front")
    # the solve reads the camera's matrix_world, which is still the old
    # rotation until the depsgraph catches up - so aim, settle, then fit
    bpy.context.view_layer.update()
    canvas.look_at(ring, margin=0.04)

    per = spec["per_design"]
    total = per * len(binders)
    keying = bpy.context.preferences.edit
    # the full turn lands on frame `total`, one past the last rendered frame,
    # so the frames that do get rendered are evenly spaced
    keying.keyframe_new_interpolation_type = "LINEAR"
    for frame, angle in ((0, 0.0), (total, 2 * math.pi * TURNS)):
        pivot.rotation_euler[2] = angle
        pivot.keyframe_insert("rotation_euler", index=2, frame=frame)
    keying.keyframe_new_interpolation_type = "CONSTANT"
    for i, mol in enumerate(binders):
        for frame, hidden in ((0, True), (i * per, False), ((i + 1) * per, True)):
            mol.object.hide_render = hidden
            mol.object.keyframe_insert("hide_render", frame=frame)

    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 0, total - 1
    if spec.get("only_frame") is not None:          # preview: just that one
        scene.frame_start = scene.frame_end = int(spec["only_frame"])
    scene.render.filepath = str(frames / "frame_")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    print(f"[mn] rendering frames {scene.frame_start}-{scene.frame_end}"
          f" -> {frames}", flush=True)
    bpy.ops.render.render(animation=True)


main()
