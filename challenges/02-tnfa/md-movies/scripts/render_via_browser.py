#!/usr/bin/env python
"""Browser-driven render for the surface movies.

Chrome's one-shot --screenshot fires at page-idle, before the surface worker
finishes at 1080p. This driver splits the job in three:

    pages <design>   write the 60 frame pages + assets + meta into a work dir
    (the frames are then screenshotted from a real browser session that waits
     for window.__surface_done -- driven from the agent side)
    stitch <design>  PNGs -> mp4 (fps 5, hold 12) into the repo, copy meta

Work dir: ~/c2-work/md-anim/browser_render/<design>/
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
sys.path.insert(0, str(REPO))
from tools.report import movie  # noqa: E402

OUT = REPO / "challenges" / "02-tnfa" / "md-movies"
WORK = Path.home() / "c2-work" / "md-anim" / "browser_render"
RUNS = Path.home() / "c2-work" / "md-anim" / "runs"


def pages(design: str) -> None:
    work = WORK / design
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    run = RUNS / design
    entries = movie.serve_app._viewer_entries(run)
    entry = entries[0]
    structure = entry["path"].read_text(errors="replace")
    highlights = movie.serve_app._client_highlights([entry])[0]
    binder = movie._binder_chain(entry)
    rows = movie._legend_rows(entry, binder)
    frame_pages, meta = movie._trajectory_pages(
        structure, entry, highlights, rows, "pdb", 60, "surface+cartoon",
        run, 1920, 1080, binder_chain=binder, orbit=True)
    for index, page in enumerate(frame_pages):
        (work / f"frame_{index:05d}.html").write_text(page)
    shutil.copy(REPO / "tools" / "serve" / "static" / "3Dmol-min.js", work / "3Dmol-min.js")
    for font in movie.FONT_FILES:
        src = REPO / "tools" / "serve" / "static" / "fonts" / font
        if src.exists():
            shutil.copy(src, work / font)
    (work / "meta.json").write_text(json.dumps({
        "mode": "trajectory", "design": None, "frames": len(frame_pages),
        "fps": 5, "hold": 12, "res": "1920x1080", "style": "surface+cartoon",
        "structure": entry["path"].name, "label": entry.get("label", ""),
        "stage": entry.get("stage", ""), "stats": meta,
    }, indent=1))
    print(f"pages: {work} ({len(frame_pages)} frames)")


def stitch(design: str) -> None:
    work = WORK / design
    out = OUT / f"{design}_md-binding.mp4"
    sequence = work / "frames"
    sequence.mkdir(exist_ok=True)
    pngs = sorted(work.glob("frame_*.png"))
    if not pngs:
        raise SystemExit(f"no frame PNGs in {work}")
    for index, png in enumerate(pngs):
        shutil.copy(png, sequence / f"frame_{index:04d}.png")
    counter = len(pngs)
    for _ in range(12):
        shutil.copy(pngs[-1], sequence / f"frame_{counter:04d}.png")
        counter += 1
    subprocess.run(["ffmpeg", "-y", "-loglevel", "warning", "-framerate", "5",
                    "-i", str(sequence / "frame_%04d.png"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", str(out)], check=True)
    meta = json.loads((work / "meta.json").read_text())
    (OUT / f"{design}_md-binding.meta.json").write_text(json.dumps(meta, indent=1))
    print(f"stitched: {out} ({len(pngs)} frames)")


if __name__ == "__main__":
    mode, design = sys.argv[1], sys.argv[2]
    {"pages": pages, "stitch": stitch}[mode](design)
