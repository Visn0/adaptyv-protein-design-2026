#!/usr/bin/env python3
"""Blender/Molecular-Nodes reel of the ten best challenge-3 designs.

Same shape as the reference clip: the receptor turning on the left, a metrics
panel on the right, one design at a time.  Three stages, each skipped when its
output is already there (`--force` to redo):

    prep     orient + align the folds, write target.pdb and binder-NN.pdb
    panels   render the ten HTML metrics panels with chromium
    preview  one frame, composited as the reel will be - the look check
    render   Blender + Molecular Nodes frames, then ffmpeg

Run `preview` and have the frame approved before `render`: the reel is half an
hour of CPU on this machine, a preview is five seconds.

    .venv/bin/python challenges/03-glp1r/videos/scripts/mn_reel.py

Structures come from the Boltz co-folds in ~/c3-work/folds; every design's
receptor is superposed onto the top design's, so the target is one fixed body
and only the binder swaps.  Numbers come from the submitted record files - no
metric is computed here.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from Bio.PDB import MMCIFParser, PDBIO, PDBParser, Superimposer

REPO = Path(__file__).resolve().parents[4]
CH3 = REPO / "challenges/03-glp1r"
SUBMISSION = CH3 / "submission/competition-submission-rubric-2026-10-23.csv"
SCORES = CH3 / "records/selection-scores-2026-10-23.csv"
PRESCREEN = CH3 / "records/prescreen-report-rubric-2026-10-23.csv"
FOLDS_SCREEN = Path.home() / "c3-work/folds-screen.csv"
FOLDS = Path.home() / "c3-work/folds"
WORK = Path.home() / "c3-work/mn-reel"
OUT = CH3 / "videos/out/02-glp1r-mn-reel.mp4"

TOP = 10
SECS_PER_DESIGN = 3.0
FPS = 16
WIDTH, HEIGHT = 1280, 720
MOL_W = 720                       # left half: the Blender render
# The turning-circle framing leaves the render about a quarter empty.  Rather
# than re-render tighter, crop to the box the content stays inside and scale
# that up.  shortcut: measured off this frame set (union 40-544 x 90-639, with
# 16 px to spare); re-measure whenever the designs or the framing change, with
#   ffmpeg -i frames/frame_%04d.png -vf \
#     format=rgba,alphaextract,cropdetect=limit=0:reset=1 -f null -
MOL_CROP = "crop=536:582:24:74"

CHROME = os.environ.get("PDT_CHROME") or os.environ.get("CHROME_PATH") or str(
    Path.home() / ".cache/ms-playwright/chromium-1243/chrome-linux64/chrome")

# one hue per design, reused by the panel and by the Blender binder material
HUES = ["#d6467f", "#2f86c9", "#e08a18", "#17a673", "#8b5cf6",
        "#0ea5a4", "#c2410c", "#4f46e5", "#be185d", "#0f766e"]

# family -> the campaign line shown on the panel (notes/campaign-tables-2026-10-23.md)
METHODS = {
    "rfd4-junction": "RFD4-Proteina, ECD\u2013TMD junction conditioning",
    "rfd4-short-band": "RFD4-Proteina, 40\u201370 aa short band",
    "rfd4-proteina": "RFD4-Proteina, deep message region",
    "evobind-peptide": "EvoBind, peptide from sequence alone",
}
MPNN = "SolubleMPNN re-sequencing of an RFD4 backbone"


def read_csv(path: Path) -> list[dict]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def designs() -> list[dict]:
    """The top-TOP submitted designs, joined to their record metrics."""
    names = [r["name"] for r in read_csv(SUBMISSION)][:TOP]
    scores = {r["design"]: r for r in read_csv(SCORES)}
    pre = {r["id"]: r for r in read_csv(PRESCREEN)}
    best: dict[str, dict] = {}
    for row in read_csv(FOLDS_SCREEN):            # keep each design's best sample
        cur = best.get(row["design"])
        if cur is None or float(row["ipsae"]) > float(cur["ipsae"]):
            best[row["design"]] = row
    out = []
    for i, name in enumerate(names):
        s, p, f = scores[name], pre[name], best[name]
        family = s["family"]
        out.append({
            "rank": i + 1,
            "name": name,
            "color": HUES[i],
            "family": family,
            "method": MPNN if "mpnn" in name else METHODS[family],
            "length": int(p["length"]),
            "mclass": p["declared_class"].replace("_", " "),
            "score": float(s["score"]),
            "ipsae": float(f["ipsae"]),
            "pdockq2": float(f["pdockq2"]),
            "plddt": float(f["binder_plddt"]),
        })
    return out


# ---------------------------------------------------------------- structures

def model_cif(name: str) -> Path:
    pred = FOLDS / name / f"boltz_results_{name}" / "predictions" / name
    cif = sorted(pred.glob(f"{name}_model_*.cif"))
    if not cif:
        raise SystemExit(f"no fold model for {name}")
    return cif[0]


def upright(ca: np.ndarray) -> np.ndarray:
    """Rotation putting the receptor's long axis on +Z and centring it."""
    centred = ca - ca.mean(axis=0)
    axes = np.linalg.svd(centred, full_matrices=False)[2]    # rows: principal axes
    if axes[0] @ (ca[-1] - ca[0]) > 0:        # N-term is the ECD: put it on top
        axes[0] = -axes[0]
    rot = np.vstack([axes[1], axes[2], axes[0]])             # long axis -> Z
    if np.linalg.det(rot) < 0:
        rot[1] = -rot[1]
    return rot


def prep(rows: list[dict], force: bool = False) -> None:
    """Write target.pdb plus one binder PDB per design, in one shared frame."""
    out_dir = WORK / "structures"
    if out_dir.exists() and not force:
        print(f"[prep] reusing {out_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    parser = MMCIFParser(QUIET=True)
    ref_ca, rot, centre = None, None, None
    for row in rows:
        model = parser.get_structure(row["name"], str(model_cif(row["name"])))[0]
        ca = [a for a in model["B"].get_atoms() if a.name == "CA"]
        if ref_ca is None:
            xyz = np.array([a.coord for a in ca])
            centre, rot = xyz.mean(axis=0), upright(xyz)
            for atom in model.get_atoms():
                atom.set_coord(rot @ (atom.coord - centre))
            ref_ca = [a for a in model["B"].get_atoms() if a.name == "CA"]
            io = PDBIO()
            io.set_structure(model["B"])
            io.save(str(out_dir / "target.pdb"))
        else:
            if len(ca) != len(ref_ca):
                raise SystemExit(f"{row['name']}: receptor is {len(ca)} CA, "
                                 f"reference is {len(ref_ca)}")
            sup = Superimposer()
            sup.set_atoms(ref_ca, ca)
            sup.apply(model.get_atoms())
        io = PDBIO()
        io.set_structure(model["A"])
        io.save(str(out_dir / f"binder-{row['rank']:02d}.pdb"))
        print(f"[prep] {row['rank']:2d}  {row['name']}")


# -------------------------------------------------------------------- panels

# Dark and typographic, deliberately unlike the reference clip's white
# two-column spec sheet: no boxes or rules round the data, one accent per
# design carrying rank/score/tick, and the numbers set in mono so they read
# as instrument output.  The page is the whole 1280x720 backdrop - the
# molecule render is laid over its left side, so the gradient has to sit
# behind the protein, not beside it.
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1280px;height:720px;
  background:#0a0e14 radial-gradient(760px 620px at 27% 48%,#18222f 0%,#0a0e14 72%);
  font-family:-apple-system,'Segoe UI','Liberation Sans','DejaVu Sans',sans-serif;
  color:#e9edf3;-webkit-font-smoothing:antialiased}
.panel{position:absolute;left:800px;top:54px;width:432px}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:2.4px;color:#78839a}
h1{font-size:26px;font-weight:600;letter-spacing:-.5px;margin-top:10px;
  line-height:1.18}
.sub{font-size:12px;color:#78839a;margin-top:9px;line-height:1.55}
hr{border:0;border-top:1px solid rgba(255,255,255,.10);margin:20px 0}
.rank{display:flex;align-items:baseline;gap:11px}
.rank b{font-size:40px;font-weight:600;color:var(--c);letter-spacing:-1.5px;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.rank span{font-size:10px;font-weight:700;letter-spacing:1.6px;color:#78839a}
.name{font-size:15px;margin-top:5px;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
table{width:100%;font-size:12px;border-collapse:collapse;margin-top:18px}
td{padding:4px 0;vertical-align:top;line-height:1.45}
td.k{color:#78839a;width:132px}
.lab{font-size:10px;font-weight:700;letter-spacing:1.6px;color:#78839a;
  margin:22px 0 7px}
.big{font-size:44px;font-weight:600;color:var(--c);letter-spacing:-1.5px;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.big span{font-size:13px;color:#78839a;letter-spacing:0;margin-left:4px}
.stats{display:flex;gap:30px}
.stat b{display:block;font-size:19px;font-weight:600;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.stat span{display:block;font-size:10px;color:#78839a;margin-top:4px}
.note{font-size:10px;color:#9a7b45;margin-top:26px;line-height:1.5}
.bar{position:absolute;left:800px;width:432px;bottom:46px;
  display:flex;gap:6px}
.bar i{flex:1;height:2px;background:rgba(255,255,255,.13)}
.bar i.on{background:var(--c);height:3px}
.foot{position:absolute;left:800px;width:432px;bottom:22px;font-size:11px;
  color:#5d6678;text-align:right}
"""


def rows_html(kv: list[tuple[str, str]]) -> str:
    return "".join(f'<tr><td class="k">{html.escape(k)}</td>'
                   f"<td>{html.escape(v)}</td></tr>" for k, v in kv)


def panel_html(row: dict) -> str:
    """The whole 1280x720 backdrop; the molecule render is laid over its left."""
    design = rows_html([("campaign method", row["method"]),
                        ("binder length", f"{row['length']} aa"),
                        ("molecule class", row["mclass"])])
    stats = "".join(f'<div class="stat"><b>{v}</b><span>{k}</span></div>'
                    for k, v in (("interface ipSAE", f"{row['ipsae']:.3f}"),
                                 ("pDockQ2", f"{row['pdockq2']:.3f}"),
                                 ("binder pLDDT", f"{row['plddt']:.1f}")))
    ticks = "".join(f'<i class="{"on" if i == row["rank"] else ""}"></i>'
                    for i in range(1, TOP + 1))
    return f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<body style="--c:{row['color']}"><div class="panel">
<div class="eyebrow">GLP-1R &middot; CHALLENGE 03</div>
<h1>De novo agonist design</h1>
<div class="sub">human GLP-1 receptor, 409-residue construct &middot;
ranked on active-state geometry</div>
<hr>
<div class="rank"><b>{row['rank']:02d}</b><span>OF 20 SUBMITTED</span></div>
<div class="name">{html.escape(row['name'])}</div>
<table>{design}</table>
<div class="lab">COMPOSITE SELECTION SCORE</div>
<div class="big">{row['score']:.1f}<span>/ 100</span></div>
<div class="lab">BOLTZ-2 CO-FOLD &middot; BEST OF FIVE SAMPLES</div>
<div class="stats">{stats}</div>
<div class="note">predicted structures &mdash; interface confidence,
not measured affinity</div>
</div>
<div class="bar">{ticks}</div>
<div class="foot">linkedin.com/in/anton-chernysh</div></body>"""


def shoot(pages: dict[str, str], force: bool = False) -> None:
    """Rasterise each HTML page to a PNG with headless chromium."""
    out_dir = WORK / "panels"
    if out_dir.exists() and not force:
        print(f"[panels] reusing {out_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    src = WORK / "html"
    src.mkdir(parents=True, exist_ok=True)
    for name, page in pages.items():
        (src / f"{name}.html").write_text(page)
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
             "--hide-scrollbars", "--force-device-scale-factor=1",
             f"--window-size={WIDTH},{HEIGHT}",
             f"--screenshot={out_dir / f'{name}.png'}",
             (src / f"{name}.html").as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[panels] {name}.png")


# -------------------------------------------------------------------- render

def blender(rows: list[dict], frames: Path, only: int | None = None) -> None:
    spec = {"structures": str(WORK / "structures"), "frames": str(frames),
            "colors": [r["color"] for r in rows],
            "per_design": int(SECS_PER_DESIGN * FPS),
            "width": MOL_W, "height": HEIGHT, "only_frame": only}
    (WORK / "spec.json").write_text(json.dumps(spec))
    subprocess.run(["blender", "-b", "--python",
                    str(Path(__file__).parent / "mn_render.py"),
                    "--", str(WORK / "spec.json")], check=True)


def preview(rows: list[dict], frame: int) -> None:
    """One frame, composited exactly as the reel will be - the look check.

    Always run this and have the frame approved before the full render: the
    reel is half an hour of CPU, a preview is five seconds.  A look change
    that only touches the panel reuses the frames already rendered, so it
    costs nothing but the composite.
    """
    frames = WORK / "frames"
    if not (frames / f"frame_{frame:04d}.png").exists():
        frames = WORK / "preview-frames"
        blender(rows, frames, only=frame)
    rank = min(frame // int(SECS_PER_DESIGN * FPS) + 1, len(rows))
    out = WORK / "preview.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-loop", "1", "-framerate", str(FPS),
                    "-i", str(WORK / f"panels/design-{rank:02d}.png"),
                    "-framerate", str(FPS), "-start_number", str(frame),
                    "-i", str(frames / "frame_%04d.png"), "-frames:v", "1",
                    "-filter_complex",
                    f"[1]{MOL_CROP},scale=-1:712:flags=lanczos[m];"
                    "[0][m]overlay=67:4:shortest=1", str(out)], check=True)
    print(f"[preview] frame {frame} (rank {rank}): {out}")


def render(rows: list[dict], force: bool = False) -> None:
    frames = WORK / "frames"
    n_frames = int(SECS_PER_DESIGN * FPS) * len(rows)
    have = len(list(frames.glob("frame_*.png"))) if frames.exists() else 0
    if have >= n_frames and not force:
        print(f"[render] reusing {have} frames")
    else:
        blender(rows, frames)
    stitch(rows)


def stitch(rows: list[dict]) -> None:
    """Overlay each design's frames on its panel, then join the ten."""
    seg = WORK / "segments"
    if seg.exists():
        shutil.rmtree(seg)
    seg.mkdir(parents=True)
    per = int(SECS_PER_DESIGN * FPS)
    parts = []
    for row in rows:
        clip = seg / f"design-{row['rank']:02d}.mp4"
        run_ffmpeg(
            ["-loop", "1", "-framerate", str(FPS),
             "-i", str(WORK / f"panels/design-{row['rank']:02d}.png"),
             "-framerate", str(FPS), "-start_number", str((row["rank"] - 1) * per),
             "-i", str(WORK / "frames/frame_%04d.png"),
             "-frames:v", str(per), "-filter_complex",
             f"[1]{MOL_CROP},scale=-1:712:flags=lanczos[m];"
             "[0][m]overlay=67:4:shortest=1,format=yuv420p"], clip)
        parts.append(clip)
    listing = seg / "parts.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", str(listing), "-c", "copy", str(OUT)],
                   check=True)
    print(f"[stitch] {OUT}")


def run_ffmpeg(inputs: list[str], out: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-r", str(FPS), str(out)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="all",
                    choices=["all", "prep", "panels", "preview", "render",
                             "stitch"])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--frame", type=int, default=30,
                    help="which frame the preview stage renders")
    args = ap.parse_args()
    rows = designs()
    if args.stage in ("all", "prep"):
        prep(rows, args.force)
    if args.stage in ("all", "panels"):
        pages = {f"design-{r['rank']:02d}": panel_html(r) for r in rows}
        shoot(pages, args.force)
    if args.stage == "preview":
        preview(rows, args.frame)
    elif args.stage in ("all", "render"):
        render(rows, args.force)
    elif args.stage == "stitch":
        stitch(rows)


if __name__ == "__main__":
    main()
