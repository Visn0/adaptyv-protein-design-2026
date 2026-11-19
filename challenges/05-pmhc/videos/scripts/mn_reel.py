#!/usr/bin/env python3
"""Blender/Molecular-Nodes reel of the ten best challenge-5 designs.

The challenge-3 and challenge-4 reels, applied to the pMHC submission: the
target turning on the left through one continuous revolution, a metrics panel
on the right, one design at a time.  What differs is the target.  Challenge 5
binds a complex, not a receptor, so three bodies stay fixed while the binder
swaps: the HLA-A*11:01 heavy chain and beta-2 microglobulin in see-through
grey, and the KRAS G12D 10-mer in opaque amber inside the groove.  The peptide
is the surface the whole challenge is about, so it is drawn as its own body
(`spec["extras"]`, the one addition in this challenge's `mn_render.py`).

Stages, each skipped when its output is already there (`--force`):

    prep     pick each design's best G12D co-fold, align, write the PDBs
    panels   render the ten HTML metrics panels with chromium
    preview  one frame, composited as the reel will be - the look check
    render   Blender + Molecular Nodes frames, then ffmpeg

Run `preview` and have the frame approved before `render`: at 1080p24 the reel
is hours of CPU on this machine, a preview is seconds.  `--demo` runs the whole
pipeline over three designs at half size for a look at the motion.

    .venv/bin/python challenges/05-pmhc/videos/scripts/mn_reel.py preview

Structures come from the boltz-2 co-folds under ~/c5-work; every design's
target is superposed onto the top design's, so the complex is one fixed body.
Numbers come from `records/submitted-19-metrics-2026-11-08.csv` - no metric is
computed here.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from Bio.PDB import MMCIFParser, PDBIO, Select, Superimposer

REPO = Path(__file__).resolve().parents[4]
CH5 = REPO / "challenges/05-pmhc"
METRICS = CH5 / "records/submitted-19-metrics-2026-11-08.csv"
SUBMISSION = CH5 / "submission/submission-05-pmhc.csv"
WORK_ROOT = Path.home() / "c5-work"
RENDER_PY = Path(__file__).with_name("mn_render.py")

# the organizers' own peptide: KRAS G12D residues 3-12, aspartate at position 6
G12D_PEPTIDE = "VVVGADGVGK"
TARGET_CHAINS = ("A", "B")        # HLA-A*11:01 heavy chain, beta-2 microglobulin
PEPTIDE_CHAIN = "C"
BINDER_CHAIN = "D"
GATE = 0.61

SECS_PER_DESIGN = 3.0
ENGINE = "CYCLES"                 # set by --engine; CUDA needs no GL context
SAMPLES = 48                      # Cycles samples a frame, adaptive + denoised
SURFACE = ""                      # set by --surface: "", binders, target, both
SURFACE_OPACITY = 0.2
GLOW = 0.0
WIDTH, HEIGHT = 1280, 720         # the panel's CSS pixels

PEPTIDE_COLOR = "#f5a524"         # amber: the house colour for the interface
TARGET_LABEL = "HLA-A*11:01 + β2m"


def configure(scale: float, top: int, suffix: str = "", fps: int = 24) -> None:
    """Bind everything the output size decides; `--demo`/`--quick` go smaller."""
    global SCALE, TOP, FPS, VW, VH, MOL_W, MOL_H, MOL_X, MOL_Y, MOL_TALL, WORK, OUT
    SCALE, TOP, FPS = scale, top, fps
    VW, VH = int(WIDTH * scale), int(HEIGHT * scale)
    MOL_W = MOL_H = int(720 * scale)    # left half: the square Blender render
    MOL_X, MOL_Y = int(800 * scale), int(4 * scale)   # MOL_X: the panel's left edge
    MOL_TALL = VH - 2 * MOL_Y           # the height the molecule is scaled to
    WORK = WORK_ROOT / f"mn-reel{suffix}"
    OUT = CH5 / f"videos/out/05-pmhc-mn-reel{suffix}.mp4"


configure(1.5, 10)

CHROME = os.environ.get("PDT_CHROME") or os.environ.get("CHROME_PATH") or str(
    Path.home() / ".cache/ms-playwright/chromium-1243/chrome-linux64/chrome")

# one hue per design, reused by the panel and by the Blender binder material
HUES = ["#d6467f", "#2f86c9", "#e08a18", "#17a673", "#8b5cf6",
        "#0ea5a4", "#c2410c", "#4f46e5", "#be185d", "#2dd4bf"]


def read_csv(path: Path) -> list[dict]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def designs() -> list[dict]:
    """The top ten of the submitted nineteen, in the submitted order."""
    sequences = {r["name"]: r["sequence"] for r in read_csv(SUBMISSION)}
    rows = []
    for i, row in enumerate(read_csv(METRICS)[:TOP]):
        rows.append({
            "rank": i + 1,
            "name": row["design"],
            "color": HUES[i % len(HUES)],
            "family": row["family"],
            "mutation": row["mutation"],
            "length": int(row["length_aa"]),
            "mclass": row["molecule_class"].replace("_", " "),
            "score": row["score"],
            "read": float(row["peptide_read_g12d"]),
            "ipdae": float(row["ipdae_pep_g12d"]) if row["ipdae_pep_g12d"] else None,
            "e_score": float(row["e_score"]),
            "gate": row["gate"],
            "sequence": sequences[row["design"]],
        })
    return rows


# ---------------------------------------------------------------- structures

class Keep(Select):
    """PDBIO filter: write only the chains asked for."""

    def __init__(self, chains: tuple[str, ...]):
        self.chains = chains

    def accept_chain(self, chain):            # noqa: N802 - Biopython's API
        return chain.id in self.chains


def sequence_of(chain) -> str:
    from Bio.PDB.Polypeptide import protein_letters_3to1 as code
    return "".join(code.get(r.get_resname(), "X")
                   for r in chain if r.id[0] == " ")


def fold_models(name: str) -> list[Path]:
    """Every boltz G12D model of one design, newest batch first.

    A design may have been folded in several batches and under two names (the
    evolution children carry an `evo` prefix the fold directories do not).
    Wild-type and peptide-free folds live beside the G12D ones under a `__wt`
    or `__free` suffix, so they are excluded by the key, and `prep` checks the
    peptide it ended up with rather than trusting the path.
    """
    bases = [name] + ([name[3:]] if name.startswith("evo") else [])
    out: list[Path] = []
    for base in bases:
        for key in (base, base + "__g12d"):
            pattern = f"**/folds/{key}/boltz_results_{key}/predictions/{key}/{key}_model_*.cif"
            out += sorted(WORK_ROOT.glob(pattern))
    return out


def best_model(name: str) -> Path:
    """The model with the highest ipTM among every recorded G12D fold."""
    best, best_iptm = None, -1.0
    for cif in fold_models(name):
        confidence = cif.with_name(f"confidence_{cif.stem}.json")
        if not confidence.is_file():
            continue
        iptm = float(json.loads(confidence.read_text())["iptm"])
        if iptm > best_iptm:
            best, best_iptm = cif, iptm
    if best is None:
        raise SystemExit(f"no G12D co-fold with a confidence file for {name}")
    print(f"       fold ipTM {best_iptm:.3f}  {best.parent.name}/{best.name}")
    return best


def upright(target_ca: np.ndarray, peptide_ca: np.ndarray) -> np.ndarray:
    """Rotation putting the complex's long axis on +Z, the groove end up.

    The peptide says which end is the top, which is also where the eye should
    go: everything that matters happens in the groove it sits in.
    """
    centred = target_ca - target_ca.mean(axis=0)
    axes = np.linalg.svd(centred, full_matrices=False)[2]      # rows: principal
    if axes[0] @ (peptide_ca.mean(axis=0) - target_ca.mean(axis=0)) < 0:
        axes[0] = -axes[0]
    rot = np.vstack([axes[1], axes[2], axes[0]])               # long axis -> Z
    if np.linalg.det(rot) < 0:
        rot[1] = -rot[1]
    return rot


def prep(rows: list[dict], force: bool = False) -> None:
    """Write target.pdb, peptide.pdb and one binder PDB per design, one frame."""
    out_dir = WORK / "structures"
    if out_dir.exists() and not force:
        print(f"[prep] reusing {out_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    parser = MMCIFParser(QUIET=True)
    io = PDBIO()
    reference = None
    for row in rows:
        print(f"[prep] {row['rank']:2d}  {row['name']}")
        model = parser.get_structure(row["name"], str(best_model(row["name"])))[0]
        peptide = sequence_of(model[PEPTIDE_CHAIN])
        if peptide != G12D_PEPTIDE:
            raise SystemExit(f"{row['name']}: peptide is {peptide}, not the "
                             f"G12D {G12D_PEPTIDE} - wrong fold state")
        binder = sequence_of(model[BINDER_CHAIN])
        if binder != row["sequence"]:
            raise SystemExit(f"{row['name']}: the folded binder is not the "
                             f"submitted sequence ({len(binder)} aa folded, "
                             f"{row['length']} aa submitted)")
        heavy = [a for a in model[TARGET_CHAINS[0]].get_atoms() if a.name == "CA"]
        if reference is None:
            xyz = np.array([a.coord for a in heavy])
            peptide_ca = np.array([a.coord for a in model[PEPTIDE_CHAIN].get_atoms()
                                   if a.name == "CA"])
            centre, rot = xyz.mean(axis=0), upright(xyz, peptide_ca)
            for atom in model.get_atoms():
                atom.set_coord(rot @ (atom.coord - centre))
            reference = [a for a in model[TARGET_CHAINS[0]].get_atoms()
                         if a.name == "CA"]
            io.set_structure(model)
            io.save(str(out_dir / "target.pdb"), select=Keep(TARGET_CHAINS))
            io.save(str(out_dir / "peptide.pdb"), select=Keep((PEPTIDE_CHAIN,)))
        else:
            if len(heavy) != len(reference):
                raise SystemExit(f"{row['name']}: heavy chain is {len(heavy)} CA, "
                                 f"the reference is {len(reference)}")
            superimposer = Superimposer()
            superimposer.set_atoms(reference, heavy)
            superimposer.apply(model.get_atoms())
            print(f"       superposed, RMSD {superimposer.rms:.2f} A")
        io.set_structure(model)
        io.save(str(out_dir / f"binder-{row['rank']:02d}.pdb"),
                select=Keep((BINDER_CHAIN,)))


# -------------------------------------------------------------------- panels

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1280px;height:720px;
  background:#0a0e14 radial-gradient(760px 620px at 27% 48%,#18222f 0%,#0a0e14 72%);
  font-family:-apple-system,'Segoe UI','Liberation Sans','DejaVu Sans',sans-serif;
  color:#e9edf3;-webkit-font-smoothing:antialiased}
.panel{position:absolute;left:800px;top:50px;width:432px}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:2.4px;color:#78839a}
h1{font-size:26px;font-weight:600;letter-spacing:-.5px;margin-top:10px;
  line-height:1.18}
.sub{font-size:12px;color:#78839a;margin-top:9px;line-height:1.55}
.sub b{color:#e9edf3;font-weight:600;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
hr{border:0;border-top:1px solid rgba(255,255,255,.10);margin:18px 0}
.rank{display:flex;align-items:baseline;gap:11px}
.rank b{font-size:40px;font-weight:600;color:var(--c);letter-spacing:-1.5px;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.rank span{font-size:10px;font-weight:700;letter-spacing:1.6px;color:#78839a}
.name{font-size:13px;margin-top:5px;line-height:1.4;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
table{width:100%;font-size:12px;border-collapse:collapse;margin-top:16px}
td{padding:4px 0;vertical-align:top;line-height:1.45}
td.k{color:#78839a;width:120px}
.lab{font-size:10px;font-weight:700;letter-spacing:1.6px;color:#78839a;
  margin:20px 0 7px}
.big{font-size:44px;font-weight:600;color:var(--c);letter-spacing:-1.5px;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.big span{font-size:13px;color:#78839a;letter-spacing:0;margin-left:4px}
.stats{display:flex;gap:26px}
.stat b{display:block;font-size:19px;font-weight:600;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.stat span{display:block;font-size:10px;color:#78839a;margin-top:4px}
.note{font-size:10px;color:#9a7b45;margin-top:22px;line-height:1.5}
.key{position:absolute;left:40px;bottom:24px;font-size:10px;color:#8b94a7;
  display:flex;gap:16px;letter-spacing:.3px}
.key .grp{font-weight:700;letter-spacing:1.4px;color:#5d6678;font-size:9px}
.key i{display:inline-block;width:8px;height:8px;border-radius:2px;
  margin-right:6px;vertical-align:1px}
.bar{position:absolute;left:800px;width:432px;bottom:46px;display:flex;gap:6px}
.bar i{flex:1;height:2px;background:rgba(255,255,255,.13)}
.bar i.on{background:var(--c);height:3px}
.foot{position:absolute;left:800px;width:432px;bottom:22px;font-size:11px;
  color:#5d6678;text-align:right}
"""


def break_name(name: str) -> str:
    """Let the long design names wrap on their own separators, not mid-token."""
    return html.escape(name).replace("__", "__<wbr>").replace("-", "-<wbr>")


def rows_html(kv: list[tuple[str, str]]) -> str:
    return "".join(f'<tr><td class="k">{html.escape(k)}</td>'
                   f"<td>{html.escape(v)}</td></tr>" for k, v in kv if v)


def panel_html(row: dict) -> str:
    """The whole 1280x720 backdrop; the molecule render is laid over its left."""
    design = rows_html([("generator", row["family"]),
                        ("binder length", f"{row['length']} aa"),
                        ("molecule class", row["mclass"]),
                        ("point change", row["mutation"])])
    ipdae = f'{row["ipdae"]:.3f}' if row["ipdae"] is not None else "n/a"
    stats = (f'<div class="stat"><b>{row["read"]:.3f}</b>'
             f'<span>peptide ipSAE (G12D)</span></div>'
             f'<div class="stat"><b>{ipdae}</b>'
             f'<span>i_pDAE (peptide)</span></div>'
             f'<div class="stat"><b>{row["e_score"]:+.2f}</b>'
             f'<span>E-score at P6</span></div>')
    score = (f'{float(row["score"]):.1f}<span>/ 100</span>' if row["score"]
             else 'n/a<span>restored entry</span>')
    ticks = "".join(f'<i class="{"on" if i == row["rank"] else ""}"></i>'
                    for i in range(1, TOP + 1))
    return f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<body style="--c:{row['color']}"><div class="panel">
<div class="eyebrow">KRAS G12D pMHC &middot; CHALLENGE 05</div>
<h1>Mutation-specific binder design</h1>
<div class="sub">HLA-A*11:01 presenting the KRAS G12D 10-mer
<b>VVVGADGVGK</b> &middot; bind the mutant, not the wild type</div>
<hr>
<div class="rank"><b>{row['rank']:02d}</b><span>OF 19 SUBMITTED</span></div>
<div class="name">{break_name(row['name'])}</div>
<table>{design}</table>
<div class="lab">COMPOSITE SELECTION SCORE</div>
<div class="big">{score}</div>
<div class="lab">BOLTZ-2 CO-FOLD &middot; MEAN OVER FIVE MODELS</div>
<div class="stats">{stats}</div>
<div class="note">predicted structures &mdash; interface confidence,
no measured affinity</div>
</div>
<div class="key"><span class="grp">TARGET &mdash; the pMHC complex</span>
<span><i style="background:#949aa6"></i>{TARGET_LABEL}</span>
<span><i style="background:{PEPTIDE_COLOR}"></i>KRAS G12D 10-mer, in the groove</span>
<span class="grp" style="margin-left:10px">BINDER</span>
<span><i style="background:{row['color']}"></i>this design</span></div>
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
             "--hide-scrollbars", f"--force-device-scale-factor={SCALE}",
             f"--window-size={WIDTH},{HEIGHT}",
             f"--screenshot={out_dir / f'{name}.png'}",
             (src / f"{name}.html").as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[panels] {name}.png")


# -------------------------------------------------------------------- render

def blender(rows: list[dict], frames: Path, only: int | None = None,
            start: int = 0, end: int | None = None) -> None:
    spec = {"structures": str(WORK / "structures"), "frames": str(frames),
            "engine": ENGINE, "samples": SAMPLES,
            "colors": [r["color"] for r in rows],
            "extras": [{"file": "peptide.pdb", "color": PEPTIDE_COLOR,
                        "transparency": 0.0}],
            "per_design": int(SECS_PER_DESIGN * FPS),
            "surface": SURFACE, "surface_opacity": SURFACE_OPACITY,
            "width": MOL_W, "height": MOL_H, "only_frame": only,
            "start_frame": start, "end_frame": end}
    (WORK / "spec.json").write_text(json.dumps(spec))
    subprocess.run(["blender", "-b", "--python", str(RENDER_PY),
                    "--", str(WORK / "spec.json")], check=True)


def crop(frames: Path) -> str:
    """The box the molecule stays inside across every frame given, plus a margin."""
    boxes = [Image.open(p).getchannel("A").getbbox()
             for p in sorted(frames.glob("frame_*.png"))]
    boxes = [b for b in boxes if b]
    if not boxes:
        raise SystemExit(f"no opaque pixels in any frame under {frames}")
    x = min(b[0] for b in boxes)
    y = min(b[1] for b in boxes)
    w = max(b[2] for b in boxes) - x
    h = max(b[3] for b in boxes) - y
    pad = 16
    x, y = max(0, x - pad), max(0, y - pad)
    w, h = min(MOL_W - x, w + 2 * pad), min(MOL_H - y, h + 2 * pad)
    print(f"[crop] crop={w}:{h}:{x}:{y}")
    return f"crop={w}:{h}:{x}:{y}"


def preview(rows: list[dict], frame: int) -> None:
    """One frame, composited exactly as the reel will be - the look check.

    Always run this and have the frame approved before the full render.  A look
    change that only touches the panel reuses the frames already rendered, so
    it costs nothing but the composite.
    """
    frames = WORK / "frames"
    if SURFACE or not (frames / f"frame_{frame:04d}.png").exists():
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
                    f"[1]{crop(frames)},scale=-1:{MOL_TALL}:flags=lanczos[m];"
                    f"[0][m]overlay=x=({MOL_X}-w)/2:y={MOL_Y}:shortest=1",
                    str(out)], check=True)
    print(f"[preview] frame {frame} (rank {rank}): {out}")


def readable(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            image.load()
        return True
    except Exception:
        return False


def runs(numbers: list[int]):
    """Contiguous [first, last] spans of a sorted frame-number list."""
    if not numbers:
        return
    first = previous = numbers[0]
    for n in numbers[1:]:
        if n != previous + 1:
            yield first, previous
            first = n
        previous = n
    yield first, previous


def render(rows: list[dict], force: bool = False) -> None:
    frames = WORK / "frames"
    n_frames = int(SECS_PER_DESIGN * FPS) * len(rows)
    done = set()
    if frames.exists() and not force:
        for path in frames.glob("frame_*.png"):
            if readable(path):
                done.add(int(path.stem.split("_")[1]))
            else:
                path.unlink()                  # mid-write when the host went
    missing = [i for i in range(n_frames) if i not in done]
    if not missing:
        print(f"[render] reusing {n_frames} frames")
    for first, last in runs(missing):
        if (first, last) != (0, n_frames - 1):
            print(f"[render] filling frames {first}-{last}")
        blender(rows, frames, start=first, end=last)
    stitch(rows)


def glow() -> str:
    """A bloom pass on the molecule layer only, so the panel text stays crisp."""
    if not GLOW:
        return ""
    return (f",split=2[base][halo];[halo]gblur=sigma={GLOW}:steps=3,"
            f"eq=saturation=1.6,colorchannelmixer=aa=0.95[lit];"
            f"[lit][base]overlay=0:0")


def stitch(rows: list[dict]) -> None:
    """Overlay each design's frames on its panel, then join the ten."""
    frames = WORK / "frames"
    box = crop(frames)
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
             "-i", str(frames / "frame_%04d.png"),
             "-frames:v", str(per), "-filter_complex",
             f"[1]{box},scale=-1:{MOL_TALL}:flags=lanczos{glow()}[m];"
             f"[0][m]overlay=x=({MOL_X}-w)/2:y={MOL_Y}:shortest=1,"
             f"format=yuv420p"], clip)
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
    ap.add_argument("--demo", action="store_true",
                    help="three designs at half size: the quick check")
    ap.add_argument("--quick", action="store_true",
                    help="all ten, small and choppy: a fast look at the whole reel")
    ap.add_argument("--surface", default="",
                    choices=["", "binders", "target", "both"],
                    help="draw a molecular surface as well as the cartoon")
    ap.add_argument("--surface-opacity", type=float, default=0.2,
                    help="how solid that surface is; the cartoon shows through")
    ap.add_argument("--glow", type=float, default=0.0,
                    help="bloom radius on the molecule; re-stitch only")
    ap.add_argument("--frame", type=int, default=30,
                    help="which frame the preview stage renders")
    ap.add_argument("--engine", default="cycles", choices=["cycles", "eevee"],
                    help="cycles runs on the GPU through CUDA (5x faster here); "
                         "eevee needs a GL context and falls back to software")
    ap.add_argument("--samples", type=int, default=48,
                    help="Cycles samples a frame")
    args = ap.parse_args()
    global SURFACE, SURFACE_OPACITY, GLOW, OUT, ENGINE, SAMPLES
    ENGINE, SAMPLES = args.engine.upper(), args.samples
    SURFACE, SURFACE_OPACITY = args.surface, args.surface_opacity
    GLOW = args.glow
    if args.demo:
        configure(SCALE / 2, 3, "-demo", fps=FPS)
    elif args.quick:
        configure(0.5, TOP, "-quick", fps=12)
    if GLOW:                            # after configure, which rebuilds OUT
        OUT = OUT.with_name(OUT.stem + "-glow.mp4")
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
