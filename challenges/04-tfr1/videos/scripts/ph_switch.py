#!/usr/bin/env python3
"""The pH switch, as far as it was actually measured.

The champion carries two engineered histidines, at binder positions 9 and 28,
placed against the two conserved lysines (K344, K374) that anchor the epitope.
PROPKA put their free-state pKa at 6.45 and 6.23, so between blood and endosome
they go from mostly neutral to mostly protonated - positive, beside two lysines
that are positive at both pH values.

That is the whole of what this clip shows, and it is all we have.  There is no
predicted unbinding here: structure prediction has no pH in it, we hold one
bound pose, and the computed linkage for this design is 1.8-fold weaker binding
at pH 6.0, not release.  The release half of the story is a separate, labelled
schematic - it is illustration, and it has to look like one.

    .venv/bin/python challenges/04-tfr1/videos/scripts/ph_switch.py

Stages: prep (the two chains in one frame), render (two Blender passes over one
camera move, differing only in the histidine colour), compose (cross-fade the
passes, lay them on the per-frame panel, encode).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from Bio.PDB import MMCIFParser, PDBIO

REPO = Path(__file__).resolve().parents[4]
CH4 = REPO / "challenges/04-tfr1"
CHAI = Path.home() / "c4-work/chai/designs"
HUMAN = Path.home() / "c4-work/targets/human_full.fa"
WORK = Path.home() / "c4-work/ph-switch"
OUT = CH4 / "videos/out/04-tfr1-ph-switch.mp4"
RENDER_PY = Path(__file__).with_name("ph_render.py")

DESIGN = "c3_e12rfd4_r4d5_d2"
SITES = ((9, 6.45), (28, 6.23))     # binder position, free-state pKa (PROPKA)
ANCHORS = ((223, "K344"), (253, "K374"))   # fold index -> crystal numbering
SELECTIVITY = 1.8                   # computed fold-change, campaigns/c3 linkage.csv

HIGH_PH, LOW_PH = 7.4, 6.0
FPS = 24
SECS = 3.5
TOTAL = int(SECS * FPS)             # 84
FADE_START, FADE = 36, 24           # the cross-fade window, in frames
MOL = 900                           # the square Blender render
WIDTH, HEIGHT = 1920, 1080
PANEL_W = 1280                      # the HTML page; rasterised at 1.5

RECEPTOR_GREY = "#949aa6"
BINDER_HUE = "#d6467f"
POSITIVE = "#4f9ad6"                # the charge colour, shared by both residues
NEUTRAL = "#8e97a6"

CHROME = os.environ.get("PDT_CHROME") or os.environ.get("CHROME_PATH") or str(
    Path.home() / ".cache/ms-playwright/chromium-1243/chrome-linux64/chrome")


def protonated(ph: float, pka: float) -> float:
    """Henderson-Hasselbalch: the fraction of a site carrying its proton."""
    return 1.0 / (1.0 + 10 ** (ph - pka))


def ph_at(frame: int) -> float:
    """The pH this frame is showing; it falls across the cross-fade only."""
    t = min(max((frame - FADE_START) / FADE, 0.0), 1.0)
    return HIGH_PH + (LOW_PH - HIGH_PH) * t


# ----------------------------------------------------------------- structures

def model_cif(name: str) -> Path:
    """The design's best restrained co-fold against the human receptor."""
    out_dir = CHAI / name / "out"
    if not out_dir.is_dir():
        raise SystemExit(f"no human chai fold for {name} at {out_dir}")
    best, best_iptm = None, -1.0
    for cif in sorted(out_dir.glob("pred.model_idx_*.cif")):
        idx = cif.stem.split("_")[-1]
        iptm = np.load(out_dir / f"scores.model_idx_{idx}.npz")["iptm"].item()
        if iptm > best_iptm:
            best, best_iptm = cif, iptm
    return best


def prep(force: bool = False) -> None:
    out_dir = WORK / "structures"
    if out_dir.exists() and not force:
        print(f"[prep] reusing {out_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    model = MMCIFParser(QUIET=True).get_structure(DESIGN, str(model_cif(DESIGN)))[0]
    from Bio.PDB.Polypeptide import protein_letters_3to1 as code
    seq = "".join(code.get(r.get_resname(), "X")
                  for r in model["A"] if r.id[0] == " ")
    if seq != "".join(HUMAN.read_text().splitlines()[1:]):
        raise SystemExit("this fold is not against human TfR1")
    for position, pka in SITES:
        if model["B"][position].get_resname() != "HIS":
            raise SystemExit(f"binder position {position} is not a histidine")
    for index, label in ANCHORS:
        if model["A"][index].get_resname() != "LYS":
            raise SystemExit(f"receptor index {index} ({label}) is not a lysine")
    io = PDBIO()
    for chain, name in (("A", "receptor"), ("B", "binder")):
        io.set_structure(model[chain])
        io.save(str(out_dir / f"{name}.pdb"))
    print(f"[prep] {DESIGN}: His{', His'.join(str(p) for p, _ in SITES)} "
          f"against {' and '.join(label for _, label in ANCHORS)}")


# ---------------------------------------------------------------------- panel

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1280px;height:720px;
  background:#0a0e14 radial-gradient(760px 620px at 27% 48%,#18222f 0%,#0a0e14 72%);
  font-family:-apple-system,'Segoe UI','Liberation Sans','DejaVu Sans',sans-serif;
  color:#e9edf3;-webkit-font-smoothing:antialiased}
.panel{position:absolute;left:792px;top:58px;width:440px}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:2.4px;color:#78839a}
h1{font-size:26px;font-weight:600;letter-spacing:-.5px;margin-top:10px}
.sub{font-size:12px;color:#78839a;margin-top:9px;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
hr{border:0;border-top:1px solid rgba(255,255,255,.10);margin:18px 0}
.lab{font-size:10px;font-weight:700;letter-spacing:1.6px;color:#78839a;
  margin:16px 0 7px}
.ph{font-size:52px;font-weight:600;letter-spacing:-2px;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.ph span{font-size:13px;color:#78839a;letter-spacing:1.6px;margin-left:10px}
.dial{position:relative;height:4px;background:rgba(255,255,255,.10);
  margin-top:14px}
.dial i{position:absolute;top:-4px;width:12px;height:12px;border-radius:50%;
  background:#e9edf3}
.ends{display:flex;justify-content:space-between;font-size:10px;
  color:#5d6678;margin-top:9px;letter-spacing:1.4px}
.site{display:flex;align-items:center;gap:11px;margin-top:9px;font-size:12px}
.site b{width:62px;font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.site i{flex:1;height:5px;background:rgba(255,255,255,.10)}
.site u{display:block;height:5px}
.site s{width:52px;text-align:right;text-decoration:none;color:#e9edf3;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.anchor{font-size:11px;color:#9aa3b4;margin-top:16px}
.anchor i{display:inline-block;width:9px;height:9px;border-radius:2px;
  background:#4f9ad6;margin-right:8px;vertical-align:0}
.note{font-size:10px;color:#9a7b45;margin-top:18px;line-height:1.55}
.foot{position:absolute;left:792px;width:440px;bottom:22px;font-size:11px;
  color:#5d6678;text-align:right}
"""


def panel_html(frame: int) -> str:
    ph = ph_at(frame)
    where = "BLOOD" if ph > 6.9 else "ENDOSOME"
    sites = ""
    for position, pka in SITES:
        f = protonated(ph, pka)
        hue = blend_hex(NEUTRAL, POSITIVE, min(1.0, f / 0.75))
        sites += (f'<div class="site"><b>His{position}</b>'
                  f'<i><u style="width:{f*100:.0f}%;background:{hue}"></u></i>'
                  f'<s>{f*100:.0f}%</s></div>')
    pos = (HIGH_PH - ph) / (HIGH_PH - LOW_PH) * 100
    return f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<body><div class="panel">
<div class="eyebrow">TfR1 &middot; CHALLENGE 04</div>
<h1>The pH switch, measured</h1>
<div class="sub">{DESIGN}</div>
<hr>
<div class="ph">{ph:.2f}<span>pH &middot; {where}</span></div>
<div class="dial"><i style="left:calc({pos:.1f}% - 6px)"></i></div>
<div class="ends"><span>7.4 BLOOD</span><span>6.0 ENDOSOME</span></div>
<div class="lab">ENGINEERED HISTIDINES &middot; FRACTION PROTONATED</div>
{sites}
<div class="anchor"><i></i>K344 and K374 &mdash; positive at both pH values</div>
<div class="note">PROPKA per-site pK<sub>a</sub> 6.45 and 6.23. Computed linkage
for this design: {SELECTIVITY}&times; weaker binding at pH 6.0 &mdash; a push,
not a release. One bound pose; no unbinding was predicted.</div>
</div>
<div class="foot">linkedin.com/in/anton-chernysh</div></body>"""


def blend_hex(low: str, high: str, t: float) -> str:
    a = [int(low[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(high[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def panels(force: bool = False) -> None:
    out_dir = WORK / "panels"
    if out_dir.exists() and not force:
        print(f"[panels] reusing {out_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    src = WORK / "html"
    src.mkdir(parents=True, exist_ok=True)
    for frame in range(TOTAL):
        page = src / f"{frame:04d}.html"
        page.write_text(panel_html(frame))
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
             "--hide-scrollbars", "--force-device-scale-factor=1.5",
             f"--window-size={PANEL_W},720",
             f"--screenshot={out_dir / f'{frame:04d}.png'}", page.as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[panels] {TOTAL} frames")


# --------------------------------------------------------------------- render

def blender(state: str, start: int, end: int) -> None:
    frames = WORK / state
    spec = {"structures": str(WORK / "structures"), "frames": str(frames),
            "size": MOL, "total": TOTAL, "start": start, "end": end,
            "receptor": RECEPTOR_GREY, "binder": BINDER_HUE,
            "lysines": "resid " + " ".join(str(i) for i, _ in ANCHORS),
            "lysine_hue": POSITIVE,
            "histidines": "resid " + " ".join(str(p) for p, _ in SITES),
            "histidine_hue": NEUTRAL if state == "high" else POSITIVE}
    (WORK / f"spec-{state}.json").write_text(json.dumps(spec))
    subprocess.run(["blender", "-b", "--python", str(RENDER_PY),
                    "--", str(WORK / f"spec-{state}.json")], check=True)


def render(force: bool = False) -> None:
    """Two passes over one camera move: blood pH, then endosome pH.

    They overlap only across the cross-fade, so the pair costs about two thirds
    of rendering the clip twice.
    """
    for state, start, end in (("high", 0, FADE_START + FADE - 1),
                              ("low", FADE_START, TOTAL - 1)):
        frames = WORK / state
        want = set(range(start, end + 1))
        have = ({int(p.stem.split("_")[1]) for p in frames.glob("frame_*.png")}
                if frames.exists() else set())
        if want <= have and not force:
            print(f"[render] reusing {state} frames")
            continue
        blender(state, start, end)


def compose() -> None:
    """Cross-fade the two passes and lay each frame on its panel."""
    out_dir = WORK / "composited"
    out_dir.mkdir(parents=True, exist_ok=True)
    scale = WIDTH / PANEL_W
    for frame in range(TOTAL):
        if frame < FADE_START:
            molecule = open_rgba(WORK / "high", frame)
        elif frame >= FADE_START + FADE:
            molecule = open_rgba(WORK / "low", frame)
        else:
            t = (frame - FADE_START) / FADE
            molecule = Image.blend(open_rgba(WORK / "high", frame),
                                   open_rgba(WORK / "low", frame), t)
        page = Image.open(WORK / f"panels/{frame:04d}.png").convert("RGBA")
        size = int(MOL * scale)
        page.alpha_composite(molecule.resize((size, size), Image.LANCZOS),
                             (int(40 * scale), (HEIGHT - size) // 2))
        page.convert("RGB").save(out_dir / f"{frame:04d}.png")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", str(out_dir / "%04d.png"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", str(OUT)], check=True)
    print(f"[compose] {OUT}")


def open_rgba(folder: Path, frame: int) -> Image.Image:
    return Image.open(folder / f"frame_{frame:04d}.png").convert("RGBA")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="all",
                    choices=["all", "prep", "panels", "render", "compose"])
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.stage in ("all", "prep"):
        prep(args.force)
    if args.stage in ("all", "panels"):
        panels(args.force)
    if args.stage in ("all", "render"):
        render(args.force)
    if args.stage in ("all", "compose"):
        compose()


if __name__ == "__main__":
    main()
