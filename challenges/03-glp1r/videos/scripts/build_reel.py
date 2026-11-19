#!/usr/bin/env python3
"""Build the submission video's design reel: 20 designs, one second each.

For every design in the ranked submission CSV:

1. prep the fold complex into a movie run dir (`build_md.py prep`)
2. write the run-dir summary with the viewer highlights (binder pink, target blue)
3. render a spin movie — the established look: headless Chrome + 3Dmol +
   ffmpeg via `tools.report.movie`

Each clip is 24 frames at 24 fps (a full turn in one second). The clips are
concatenated into `media/reel-20-designs.mp4` (the video's S6 segment).

Also builds `media/target-glp1r.mp4`: the receptor alone, turning slowly, with
the GLP-1 pharmacophore residues highlighted (the video's target scene).

Run with the project venv and PDT_CHROME set:

    PDT_CHROME=~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome \
        .venv/bin/python challenges/03-glp1r/videos/scripts/build_reel.py

Pass design names to render only those (debug); `--target-only` builds just
the target clip.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import socket
import threading

import numpy as np
from Bio.PDB import PDBIO, PDBParser, Superimposer
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from tools.report.movie import LOAD_GATE, render_movie, start_hang_server  # noqa: E402

CH2_SCRIPTS = REPO / "challenges/02-tnfa/md-movies/scripts"
SUBMISSION = REPO / "challenges/03-glp1r/submission/competition-submission-2026-10-21.csv"
FOLDS = Path.home() / "c3-work/folds"
RUNS = Path.home() / "c3-work/md-anim/reel-runs"
CLIPS = Path.home() / "c3-work/md-anim/reel-clips"
MEDIA = REPO / "challenges/03-glp1r/videos/media"

BINDER, TARGET = "#e879f9", "#60a5fa"
AMBER = "#fbbf24"
# GLP-1 pharmacophore residues (UniProt numbering) mapped to the construct
# numbering of the prepared folds (segment 24-432 starts at residue 1):
# R190 Y148 W306 Q234 E387 -> 167 125 283 211 364
PHARM = ["167:B", "125:B", "283:B", "211:B", "364:B"]


def interface_residues(pdb: Path, binder: str = "A", target: str = "B",
                       cutoff: float = 4.5) -> list[str]:
    """Target residues within cutoff of the binder, as ['123:B', ...]."""
    b, t = [], []
    for line in pdb.read_text().splitlines():
        if not line.startswith("ATOM"):
            continue
        xyz = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
        if line[21] == binder:
            b.append(xyz)
        elif line[21] == target:
            t.append((int(line[22:26]), xyz))
    if not b:
        return []
    b = np.asarray(b)
    hit = {resid for resid, xyz in t
           if float(np.linalg.norm(b - np.asarray(xyz), axis=1).min()) <= cutoff}
    return [f"{r}:{target}" for r in sorted(hit)]


def designs() -> list[str]:
    with SUBMISSION.open() as handle:
        return [row["name"] for row in csv.DictReader(handle)]


REFERENCE_CA: list = []


def align_to_reference(pdb: Path) -> None:
    """Superpose the receptor (chain B) onto the reference receptor frame.

    Every design's co-fold has its own receptor pose; without this the whole
    target would jump at each swap.  The binder keeps its pose relative to the
    receptor, so only the design changes.
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("m", str(pdb))[0]
    ca = [a for a in structure["B"].get_atoms() if a.name == "CA"]
    if not REFERENCE_CA:
        REFERENCE_CA.extend(ca)
        return
    if len(ca) != len(REFERENCE_CA):
        print(f"[reel] receptor CA count differs ({len(ca)} vs "
              f"{len(REFERENCE_CA)}) — not aligned")
        return
    sup = Superimposer()
    sup.set_atoms(REFERENCE_CA, ca)
    sup.apply(structure.get_atoms())
    io = PDBIO()
    io.set_structure(structure)
    io.save(str(pdb))


REF_DESIGN = ""            # the design whose receptor is the fixed target frame


def write_swap(design_pdb: Path, design: str) -> Path:
    """Write the fixed reference receptor + this design's aligned binder.

    The receptors of two co-folds still differ by a few Angstroms even after
    superposition, which reads as the target changing shape.  The reel shows
    one fixed target: the reference receptor's chain B plus the design's
    binder (chain A, in the pose its own co-fold gave it).
    """
    swap_dir = design_pdb.parent.parent / "swap"
    swap_dir.mkdir(parents=True, exist_ok=True)
    out = swap_dir / f"{design}.pdb"
    ref = RUNS / REF_DESIGN / "artifacts/md" / f"{REF_DESIGN}.pdb"
    a_lines = [l for l in design_pdb.read_text().splitlines()
               if l.startswith(("ATOM", "HETATM")) and l[21:22] == "A"]
    b_lines = [l for l in ref.read_text().splitlines()
               if l.startswith(("ATOM", "HETATM")) and l[21:22] == "B"]
    out.write_text("\n".join(a_lines + ["TER"] + b_lines + ["TER", "END"]) + "\n")
    return out


def prep(design: str) -> Path:
    """Prep the fold into a run dir; return the run dir."""
    run = RUNS / design
    prepared = run / "artifacts/md" / f"{design}.pdb"
    if not prepared.exists():
        cif = next((FOLDS / design / f"boltz_results_{design}" / "predictions"
                    / design).glob(f"{design}_model_*.cif"), None)
        if cif is None:
            raise SystemExit(f"no fold model for {design}")
        subprocess.run([sys.executable, str(CH2_SCRIPTS / "build_md.py"), "prep",
                        "--design", design, "--cif", str(cif),
                        "--run-dir", str(run)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        src = run / "artifacts/md" / f"{design}_prepared.pdb"
        shutil.copy(src, prepared)  # the overlay title reads the file stem
    align_to_reference(prepared)
    global REF_DESIGN
    if not REF_DESIGN:
        REF_DESIGN = design
    swap = write_swap(prepared, design)
    summary = {
        "stages": [{
            "stage": "md",
            "viewer": {
                "note": "Predicted co-fold pose. Not a binding assay.",
                "files": [{
                    "path": f"swap/{design}.pdb",
                    "label": f"{design} · GLP-1R complex · binder chain A",
                    "highlights": [
                        {"selections": ["A"], "color": BINDER,
                         "repr": "cartoon", "opacity": 0.98},
                        {"selections": ["B"], "color": TARGET,
                         "repr": "cartoon", "opacity": 0.98},
                        *([{"selections": iface, "color": AMBER,
                            "repr": "ball+stick"}]
                          if (iface := interface_residues(swap)) else []),
                    ],
                }],
            },
        }]
    }
    (run / "summary.json").write_text(json.dumps(summary, indent=1))
    return run


def render_slow_reel(names: list[str], secs_per_design: float = 2.0,
                     fps: int = 16, deg_per_frame: float = 1.8,
                     res: str = "1280x800", style: str = "surface+cartoon",
                     workers: int = 4) -> Path:
    """One continuous slow turn with the designs swapping — the reel.

    Renders every frame itself through the movie renderer's page builder, so
    the rotation never restarts at a swap: frame N of design k+1 continues the
    angle where design k left off.
    """
    from tools.report import movie as mv
    from tools.serve import app as serve_app
    import tempfile

    width, height = (int(v) for v in res.split("x"))
    port = start_hang_server()
    print(f"[reel] load-gate server on 127.0.0.1:{port}")
    caption = mv._caption_html([
        ("Structure rotation \u2014 geometry only. No physics in this clip.", False),
    ])
    pages = []
    n = len(names)
    for k, design in enumerate(names):
        run = prep(design)
        entry = serve_app._viewer_entries(run)[0]
        text = entry["path"].read_text(errors="replace")
        fmt = serve_app._format_of(entry["path"].name)
        highlights = serve_app._client_highlights([entry])[0]
        binder = mv._binder_chain(entry)
        rows = mv._legend_rows(entry, binder)
        for j in range(int(secs_per_design * fps)):
            angle = (k * secs_per_design * fps + j) * deg_per_frame
            config = {"highlights": highlights, "angle": angle,
                      "bridge": None, "style": style}
            page = mv._build_page(
                text, fmt, config, design,
                f"design {k+1}/{n}  \u00b7  the submission  \u00b7  GLP-1R",
                rows, "", "", caption, width, height)
            pages.append(page.replace("</body>", LOAD_GATE.format(port=port) + "</body>"))
    print(f"[reel] {len(pages)} frames "
          f"({secs_per_design}s x {n} designs, {deg_per_frame} deg/frame)")
    with tempfile.TemporaryDirectory() as workdir:
        work = Path(workdir)
        shutil.copy(serve_app.STATIC_DIR / "3Dmol-min.js", work / "3Dmol-min.js")
        fonts = serve_app.STATIC_DIR / "fonts"
        for font in mv.FONT_FILES:
            if (fonts / font).exists():
                shutil.copy(fonts / font, work / font)
        seq = Path.home() / "c3-work/md-anim/reel-seq"
        seq.mkdir(parents=True, exist_ok=True)
        for start in range(0, len(pages), 48):      # small batches: free RAM between
            chunk = pages[start:start + 48]
            shots = mv._render_pages(chunk, work, width, height, workers,
                                     wait_mode="timeout")
            # copy out NOW: the next batch reuses shot_00000.png... in the same dir
            for i, png in enumerate(shots):
                shutil.copy(png, seq / f"frame_{start + i:04d}.png")
            print(f"[reel] batch {min(start + 48, len(pages))}/{len(pages)} done")
    out = MEDIA / "reel-20-designs.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "warning", "-framerate", str(fps),
                    "-i", str(seq / "frame_%04d.png"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", str(out)], check=True)
    print(f"[reel] slow reel: {out}")
    return out


def build_target() -> Path:
    """Receptor alone, slow turn, pharmacophore highlighted."""
    run = RUNS / "target-glp1r"
    run.mkdir(parents=True, exist_ok=True)
    src = prep(designs()[0]) / "artifacts/md" / f"{designs()[0]}.pdb"
    out_pdb = run / "artifacts/md/target-glp1r.pdb"
    out_pdb.parent.mkdir(parents=True, exist_ok=True)
    keep = []
    for line in src.read_text().splitlines(keepends=True):
        if line.startswith(("ATOM", "HETATM")) and line[21] != "B":
            continue
        keep.append(line)
    out_pdb.write_text("".join(keep))
    summary = {
        "stages": [{
            "stage": "md",
            "viewer": {
                "note": "The receptor alone. Amber: the GLP-1 message-region "
                        "residues the designs must engage.",
                "files": [{
                    "path": "md/target-glp1r.pdb",
                    "label": "GLP-1R · the target · pharmacophore in amber",
                    "highlights": [
                        {"selections": ["B"], "color": TARGET,
                         "repr": "cartoon", "opacity": 0.98},
                        {"selections": PHARM, "color": AMBER,
                         "repr": "ball+stick"},
                    ],
                }],
            },
        }]
    }
    (run / "summary.json").write_text(json.dumps(summary, indent=1))
    MEDIA.mkdir(parents=True, exist_ok=True)
    out = MEDIA / "target-glp1r.mp4"
    render_movie(run, mode="spin", frames=120, fps=4, hold=0, res="1280x800",
                 style="surface+cartoon", orbit=True, workers=6, out=out)
    print(f"[reel] target clip: {out}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--target-only", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="re-render even if a clip is cached")
    ap.add_argument("--slow-reel", action="store_true",
                    help="one continuous slow turn, designs swapping (the reel)")
    ap.add_argument("--secs-per-design", type=float, default=2.0)
    args = ap.parse_args()

    MEDIA.mkdir(parents=True, exist_ok=True)
    if args.target_only:
        build_target()
        return

    names = args.names or designs()
    global REF_DESIGN
    REF_DESIGN = names[0]                      # fixed target frame = first design
    for design in names:                       # idempotent receptor alignment
        run = RUNS / design
        prepared = run / "artifacts/md" / f"{design}.pdb"
        if prepared.exists():
            align_to_reference(prepared)
    if args.slow_reel:
        render_slow_reel(names, secs_per_design=args.secs_per_design)
        return
    CLIPS.mkdir(parents=True, exist_ok=True)
    clips = []
    t0 = time.time()
    for i, design in enumerate(names, 1):
        out = CLIPS / f"{i:02d}_{design}.mp4"
        if out.exists() and not args.force:
            print(f"[reel] {i:2d}/{len(names)} {design} (cached)")
            clips.append(out)
            continue
        run = prep(design)
        t = time.time()
        render_movie(run, mode="spin", frames=24, fps=24, hold=0,
                     res="1280x800", style="surface+cartoon", orbit=True,
                     workers=6, out=out)
        print(f"[reel] {i:2d}/{len(names)} {design}  {time.time()-t:.0f}s")
        clips.append(out)

    reel = MEDIA / "reel-20-designs.mp4"
    lst = CLIPS / "reel.list.txt"
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(reel)], check=True)
    total = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(reel)],
        capture_output=True, text=True, check=True).stdout.strip()
    print(f"[reel] {len(clips)} clips -> {reel} ({float(total):.1f}s) "
          f"in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
