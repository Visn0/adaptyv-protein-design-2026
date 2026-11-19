#!/usr/bin/env python3
"""Blender/Molecular-Nodes reel of the ten best challenge-4 designs - v2.

The v1 reel exactly (`out/04-tfr1-mn-reel.mp4`, which this does not touch),
re-rendered at 1080p and 24 fps instead of 720p and 16: the receptor turning on
the left through one continuous revolution, a metrics panel on the right, one
design at a time.  Nothing else about it differs.  The panel is still written
in 720p CSS pixels and rasterised at SCALE, so its text is native 1080p for
nothing; only Blender pays the resolution.

Stages, each skipped when its output is already there (`--force`):

    prep     orient + align the folds, write target.pdb and binder-NN.pdb
    panels   render the ten HTML metrics panels with chromium
    preview  one frame, composited as the reel will be - the look check
    render   Blender + Molecular Nodes frames, then ffmpeg

Run `preview` and have the frame approved before `render`: at 1080p24 the reel
is about three hours of CPU on this machine, a preview is seconds.  `--demo`
runs the whole pipeline over three designs at half size, which is about ten
minutes, for when the thing to check is motion rather than sharpness.

    .venv/bin/python challenges/04-tfr1/videos/scripts/mn_reel.py

Structures come from the restrained Chai-1 co-folds in ~/c4-work/chai; every
design's receptor is superposed onto the top design's, so the target is one
fixed body and only the binder swaps.  Numbers come from the committed record
files - no metric is computed here.

The Blender side is `mn_render.py` next to this file, a copy of the one the
challenge-3 reel used: it is driven entirely by spec.json and has nothing
challenge-specific in it.
"""

from __future__ import annotations

import argparse
import csv
import html
import itertools
import json
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from Bio.PDB import MMCIFParser, PDBIO, Superimposer

REPO = Path(__file__).resolve().parents[4]
CH4 = REPO / "challenges/04-tfr1"
TOP20 = CH4 / "records/selection-top20-2026-10-30.csv"
SUBMISSION = CH4 / "submission/submission-04-tfr1.csv"
CHAI = Path.home() / "c4-work/chai/designs"
HUMAN = Path.home() / "c4-work/targets/human_full.fa"
RENDER_PY = Path(__file__).with_name("mn_render.py")

SECS_PER_DESIGN = 3.0
SURFACE = ""                      # set by --surface: "", binders, target, both
SURFACE_OPACITY = 0.2             # set by --surface-opacity
GLOW = 0.0                        # set by --glow: bloom radius in output px
WIDTH, HEIGHT = 1280, 720         # the panel's CSS pixels


def configure(scale: float, top: int, suffix: str = "", fps: int = 24) -> None:
    """Bind everything the output size decides; `--demo`/`--quick` go smaller."""
    global SCALE, TOP, FPS, VW, VH, MOL_W, MOL_H, MOL_X, MOL_Y, MOL_TALL, WORK, OUT
    SCALE, TOP, FPS = scale, top, fps
    VW, VH = int(WIDTH * scale), int(HEIGHT * scale)
    MOL_W = MOL_H = int(720 * scale)    # left half: the square Blender render
    MOL_X, MOL_Y = int(67 * scale), int(4 * scale)
    MOL_TALL = VH - 2 * MOL_Y           # the height the molecule is scaled to
    WORK = Path.home() / f"c4-work/mn-reel-v2{suffix}"
    OUT = CH4 / f"videos/out/04-tfr1-mn-reel-v2{suffix}.mp4"


configure(1.5, 10)

CHROME = os.environ.get("PDT_CHROME") or os.environ.get("CHROME_PATH") or str(
    Path.home() / ".cache/ms-playwright/chromium-1243/chrome-linux64/chrome")

# one hue per design, reused by the panel and by the Blender binder material
HUES = ["#d6467f", "#2f86c9", "#e08a18", "#17a673", "#8b5cf6",
        "#0ea5a4", "#c2410c", "#4f46e5", "#be185d", "#2dd4bf"]

# family -> the campaign line shown on the panel (campaigns/c6-selection)
METHODS = {
    "rfd4-e12-switch": "RFD4-Proteina, conserved face · histidine switch",
    "rfd4-e12": "RFD4-Proteina, conserved face",
    "genie3-b2-e12-switch": "Genie 3, conserved face · histidine switch",
    "genie3-b2-e12": "Genie 3, conserved face",
    "wave2-hybrid": "wave-2 hybrid backbone · histidine switch",
    "rfd4-b3-e12": "RFD4-Proteina, conserved face",
    "genie3-e12": "Genie 3, conserved face",
}


def chain_sequence(chain) -> str:
    """One-letter sequence of a chain, for telling human TfR1 from mouse."""
    from Bio.PDB.Polypeptide import protein_letters_3to1 as code
    return "".join(code.get(r.get_resname(), "X")
                   for r in chain if r.id[0] == " ")


def read_csv(path: Path) -> list[dict]:
    with path.open() as fh:
        return list(csv.DictReader(fh))


def designs() -> list[dict]:
    """The top ten, joined with the submitted sequences."""
    sub = {r["name"]: r for r in read_csv(SUBMISSION)}
    out = []
    for i, row in enumerate(read_csv(TOP20)[:TOP]):
        name = row["design"]
        s = sub[name]
        out.append({
            "rank": i + 1,
            "name": name,
            "color": HUES[i],
            "method": METHODS.get(row["family"], row["family"]),
            "length": len(s["sequence"]),
            "mclass": s["molecule_class"].replace("_", " "),
            "score": float(row["score"]),
            "switch": f"S{int(float(row['S']))}",
            "iptm": float(row["iptm"]),
            "mouse": float(row["mouse"]),
            "plddt": float(row["plddt"]),
        })
    return out


# ---------------------------------------------------------------- structures

def model_cif(name: str) -> Path:
    """The best restrained co-fold against the *human* receptor.

    Each design's mouse cross-fold sits beside this one under a `c4mn_` prefix.
    It is the same design against a receptor that is 78% identical and looks
    the same on screen, so picking the wrong one is silent - `prep` checks the
    sequence it ended up with rather than trusting the path.
    """
    out_dir = CHAI / name / "out"
    if not out_dir.is_dir():
        raise SystemExit(f"no human chai fold for {name} at {out_dir}")
    best, best_iptm = None, -1.0
    for cif in sorted(out_dir.glob("pred.model_idx_*.cif")):
        idx = cif.stem.split("_")[-1]
        iptm = np.load(out_dir / f"scores.model_idx_{idx}.npz")["iptm"].item()
        if iptm > best_iptm:
            best, best_iptm = cif, iptm
    if best is None:
        raise SystemExit(f"no fold model for {name}")
    return best


def upright(target_ca: np.ndarray, binder_ca: np.ndarray) -> np.ndarray:
    """Rotation putting the receptor's long axis on +Z, binder end up.

    The apical epitope has no landmark that survives every construct's
    numbering, so the binder itself says which end is the top - which is also
    where the eye should go.
    """
    centred = target_ca - target_ca.mean(axis=0)
    axes = np.linalg.svd(centred, full_matrices=False)[2]    # rows: principal
    if axes[0] @ (binder_ca.mean(axis=0) - target_ca.mean(axis=0)) < 0:
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
    ref_ca = None
    for row in rows:
        model = parser.get_structure(row["name"], str(model_cif(row["name"])))[0]
        ca = [a for a in model["A"].get_atoms() if a.name == "CA"]
        if ref_ca is None:
            xyz = np.array([a.coord for a in ca])
            binder = np.array([a.coord for a in model["B"].get_atoms()
                               if a.name == "CA"])
            centre, rot = xyz.mean(axis=0), upright(xyz, binder)
            for atom in model.get_atoms():
                atom.set_coord(rot @ (atom.coord - centre))
            ref_ca = [a for a in model["A"].get_atoms() if a.name == "CA"]
            if chain_sequence(model["A"]) != HUMAN.read_text().split("\n", 1)[1] \
                    .replace("\n", "").strip():
                raise SystemExit("the folds are not against human TfR1 - check "
                                 "the chai directory, the mouse arm looks the same")
            io = PDBIO()
            io.set_structure(model["A"])
            io.save(str(out_dir / "target.pdb"))
        else:
            if len(ca) != len(ref_ca):
                raise SystemExit(f"{row['name']}: receptor is {len(ca)} CA, "
                                 f"reference is {len(ref_ca)}")
            sup = Superimposer()
            sup.set_atoms(ref_ca, ca)
            sup.apply(model.get_atoms())
        io = PDBIO()
        io.set_structure(model["B"])
        io.save(str(out_dir / f"binder-{row['rank']:02d}.pdb"))
        print(f"[prep] {row['rank']:2d}  {row['name']}")


# -------------------------------------------------------------------- panels

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
                        ("molecule class", row["mclass"]),
                        ("switch class", row["switch"])])
    stats = "".join(f'<div class="stat"><b>{v}</b><span>{k}</span></div>'
                    for k, v in (("human ipTM", f"{row['iptm']:.3f}"),
                                 ("mouse ipTM", f"{row['mouse']:.3f}"),
                                 ("binder pLDDT", f"{row['plddt']:.1f}")))
    ticks = "".join(f'<i class="{"on" if i == row["rank"] else ""}"></i>'
                    for i in range(1, TOP + 1))
    return f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<body style="--c:{row['color']}"><div class="panel">
<div class="eyebrow">TfR1 &middot; CHALLENGE 04</div>
<h1>Conditional binder design</h1>
<div class="sub">human transferrin receptor 1, apical domain &middot;
hold at pH 7.4, release at pH 6.0</div>
<hr>
<div class="rank"><b>{row['rank']:02d}</b><span>OF 20 SUBMITTED</span></div>
<div class="name">{html.escape(row['name'])}</div>
<table>{design}</table>
<div class="lab">COMPOSITE SELECTION SCORE</div>
<div class="big">{row['score']:.1f}<span>/ 100</span></div>
<div class="lab">CHAI-1 CO-FOLD &middot; BEST OF FIVE SAMPLES</div>
<div class="stats">{stats}</div>
<div class="note">predicted structures &mdash; interface confidence,
no measured affinity</div>
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
            "colors": [r["color"] for r in rows],
            "per_design": int(SECS_PER_DESIGN * FPS),
            "surface": SURFACE, "surface_opacity": SURFACE_OPACITY,
            "width": MOL_W, "height": MOL_H, "only_frame": only,
            "start_frame": start, "end_frame": end}
    (WORK / "spec.json").write_text(json.dumps(spec))
    subprocess.run(["blender", "-b", "--python", str(RENDER_PY),
                    "--", str(WORK / "spec.json")], check=True)


def crop(frames: Path) -> str:
    """The box the molecule stays inside across every frame given, plus a margin.

    The turning-circle framing leaves the render about a quarter empty; rather
    than re-render tighter, crop to the measured content and scale it up.
    Measured from the alpha channel of every frame given, never hard-coded, so
    a longer binder or a new design set cannot silently clip.
    """
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

    Always run this and have the frame approved before the full render.  A
    look change that only touches the panel reuses the frames already
    rendered, so it costs nothing but the composite.
    """
    frames = WORK / "frames"
    # a surface layer changes the geometry, so finished cartoon-only frames
    # are not reusable for its preview
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
                    f"[0][m]overlay={MOL_X}:{MOL_Y}:shortest=1",
                    str(out)], check=True)
    print(f"[preview] frame {frame} (rank {rank}): {out}")


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


def readable(path: Path) -> bool:
    """Whether a frame is whole.

    This machine has rebooted three times mid-render, and Blender has several
    frames in flight when it does, so some are left on disk truncated.  They
    have to count as missing or the stitch dies on them hours later.
    """
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except Exception:
        return False


def runs(numbers: list[int]):
    """The contiguous spans of a sorted index list, as (first, last) pairs.

    One Blender call per span: a resume is one span to the end, and a repair
    after a crash is a few short ones, without re-rendering what sits between.
    """
    for _, group in itertools.groupby(enumerate(numbers), lambda p: p[1] - p[0]):
        span = [n for _, n in group]
        yield span[0], span[-1]


def glow() -> str:
    """A bloom pass on the molecule layer only, so the panel text stays crisp.

    Done in the composite rather than in Blender: the 720 frames are already
    on disk, so this costs a two-minute re-stitch instead of a re-render.
    """
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
             f"[0][m]overlay={MOL_X}:{MOL_Y}:shortest=1,format=yuv420p"], clip)
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
    args = ap.parse_args()
    global SURFACE, SURFACE_OPACITY, GLOW, OUT
    SURFACE, SURFACE_OPACITY = args.surface, args.surface_opacity
    GLOW = args.glow
    if args.demo:
        configure(SCALE / 2, 3, "-demo", fps=FPS)
    elif args.quick:
        # a third of the width is a ninth of the pixels, and half the frame rate
        # halves the frames again: about ten minutes instead of ninety
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
