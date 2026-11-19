#!/usr/bin/env python
"""Render the two MD binding movies from the packed run dirs.

Run with the project venv and PDT_CHROME set:

    PDT_CHROME=~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome \
        .venv/bin/python ~/c2-work/md-anim/render_movies.py
"""
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
from tools.report.movie import render_movie  # noqa: E402

OUT = REPO / "challenges" / "02-tnfa" / "md-movies"

designs = sys.argv[1:] or ["d7x-t3-3", "b2x-d12-2"]

for design in designs:
    run = Path.home() / "c2-work" / "md-anim" / "runs" / design
    OUT.mkdir(parents=True, exist_ok=True)
    movie = render_movie(
        run, mode="trajectory", frames=60, res="1920x1080", fps=5, hold=12,
        style="surface+cartoon", orbit=True, workers=4, out=OUT / f"{design}_md-binding.mp4")
    print("rendered:", movie)
