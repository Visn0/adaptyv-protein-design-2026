#!/usr/bin/env python3
"""Blender side of the folding clip - run by `fold_movie.py render`.

Loads the multi-model trajectory through Molecular Nodes as an MDAnalysis
universe, so the scene frame drives which of the model's guesses is drawn, and
turns the whole thing slowly under the folding for depth.  Frames come out RGBA
so ffmpeg can lay them over the backdrop.

    blender -b --python fold_render.py -- spec.json
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
from bl_ext.user_default.molecularnodes.nodes import geometry as mg  # noqa: E402

# A tube rather than a cartoon ribbon: secondary structure is meaningless for
# the early guesses, and a tube reads as one chain condensing rather than as a
# broken cartoon.  Rainbow along the chain so the fold's topology is legible -
# which end went where is the whole point of watching it.
# backbone_threshold cuts the ribbon wherever two alpha carbons are further
# apart than a real peptide bond allows.  That is every residue of a half-noised
# structure, which leaves nothing on screen, so it is turned off: the chain is
# known to be one chain, and watching it stay connected is the point.
STYLE = dict(quality=3, peptide_radius=1.7, backbone_smoothing=0.6,
             backbone_threshold=1000.0)


def main() -> None:
    spec = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
    frames = Path(spec["frames"])
    frames.mkdir(parents=True, exist_ok=True)
    size, n_frames = spec["size"], spec["n_frames"]

    canvas = mn.Canvas(engine="EEVEE", resolution=(size, size), transparent=True)
    canvas.view_transform = "Standard"
    canvas.exposure = 1.8
    bpy.context.scene.eevee.use_shadows = False

    traj = spec["traj"]
    mol = mn.Molecule.load(traj, traj, name="fold")
    mol.add_style("ribbon", color=lambda: mg.ColorRainbow(), **STYLE)

    pivot = bpy.data.objects.new("pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    mol.object.parent = pivot

    scene = bpy.context.scene
    # Frame the cylinder the whole clip sweeps out.  The early guesses are a
    # loose blob and the last is the compact fold, so sampling only one of them
    # either clips the start or leaves the end tiny.
    seen = []
    for frame in (0, n_frames // 3, n_frames - 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        seen.append(np.asarray(mol.get_view()))
    xyz = np.concatenate(seen)
    radius = float(np.linalg.norm(xyz[:, :2], axis=1).max())
    lo, hi = float(xyz[:, 2].min()), float(xyz[:, 2].max())
    ring = [[radius * math.cos(a), radius * math.sin(a), z]
            for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)
            for z in (lo, hi)]
    canvas.look_at(ring, viewpoint="front")
    bpy.context.view_layer.update()
    canvas.look_at(ring, margin=0.04)

    keying = bpy.context.preferences.edit
    keying.keyframe_new_interpolation_type = "LINEAR"
    for frame, angle in ((0, 0.0), (n_frames, math.radians(spec["turn_deg"]))):
        pivot.rotation_euler[2] = angle
        pivot.keyframe_insert("rotation_euler", index=2, frame=frame)

    # the turn is keyframed against absolute frame numbers, so a sub-range
    # lands on the same angles a full run would - which is what resume needs
    scene.frame_start, scene.frame_end = int(spec.get("start_frame", 0)), n_frames - 1
    if spec.get("only_frame") is not None:
        scene.frame_start = scene.frame_end = int(spec["only_frame"])
    scene.render.filepath = str(frames / "frame_")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    print(f"[fold] rendering frames {scene.frame_start}-{scene.frame_end}"
          f" -> {frames}", flush=True)
    bpy.ops.render.render(animation=True)


main()
