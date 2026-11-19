#!/usr/bin/env python3
"""Bind at pH 7.4, release at pH 6.0 - on the whole receptor dimer.

What is real here: the receptor (crystal dimer 11QC), the docked pose of the
design on each apical tip (its own Chai-1 co-fold, superposed onto each
protomer), the two engineered histidines and the two conserved lysines they
were placed against, their PROPKA pKa values, and the fraction of each site
protonated at every pH the clip passes through.

What is not: the motion.  Nothing in this project simulated binding or
unbinding - structure prediction has no pH in it, and the computed linkage for
this design is 1.8-fold weaker binding at pH 6.0, not release.  The approach
and the departure are animation, and the clip says so on screen from the first
frame to the last.

    .venv/bin/python challenges/04-tfr1/videos/scripts/bind_release.py preview
    .venv/bin/python challenges/04-tfr1/videos/scripts/bind_release.py

Structures come from `dimer_still.py prep`, which places the design on both
protomers; run that first if ~/c4-work/dimer-still is not there.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[4]
CH4 = REPO / "challenges/04-tfr1"
SOURCE = Path.home() / "c4-work/dimer-still/structures"
WORK = Path.home() / "c4-work/bind-release"
OUT = CH4 / "videos/out/04-tfr1-bind-release.mp4"
RENDER_PY = Path(__file__).with_name("bind_release_render.py")

DESIGN = "c3_e12rfd4_r4d5_d2"
SITES = ((9, 6.45), (28, 6.23))         # binder position, free-state pKa
SELECTIVITY = 1.8
HIGH_PH, LOW_PH = 7.4, 6.0

# 16 fps and seven seconds: the two passes only overlap across the fade, so
# this is 132 Blender frames where 24 fps over 9.5 s was 264.
FPS = 16
APPROACH, HOLD_HIGH, FADE, HOLD_LOW, RELEASE, TAIL = 32, 16, 20, 8, 28, 8
DOCKED = APPROACH
FADE_START = APPROACH + HOLD_HIGH
UNDOCK = FADE_START + FADE + HOLD_LOW
GONE = UNDOCK + RELEASE
TOTAL = GONE + TAIL                     # 228 frames, 9.5 s
TRAVEL = 1.6                            # Blender units out along the epitope normal

MOL_W, MOL_H = 1920, 620
MOL_Y = 210                             # clear of the title above and the
                                        # membrane line and caveat below
WIDTH, HEIGHT = 1920, 1080

DOMAINS = [("apical domain", "resid 189-383", "#9fb4d0"),
           ("helical domain", "resid 607-760", "#9a9478"),
           ("protease-like domain", "resid 121-188 384-606", "#9c7d80")]
BINDER_HUE = "#d6467f"
POSITIVE = "#4f9ad6"
NEUTRAL = "#efe6d2"                     # clearly not receptor grey, at any pH

CHROME = os.environ.get("PDT_CHROME") or os.environ.get("CHROME_PATH") or str(
    Path.home() / ".cache/ms-playwright/chromium-1243/chrome-linux64/chrome")


def protonated(ph: float, pka: float) -> float:
    return 1.0 / (1.0 + 10 ** (ph - pka))


def ph_at(frame: int) -> float:
    t = min(max((frame - FADE_START) / FADE, 0.0), 1.0)
    return HIGH_PH + (LOW_PH - HIGH_PH) * t


def stage(frame: int) -> tuple[str, str]:
    if frame < DOCKED:
        return "APPROACHING", "BLOOD"
    if frame < FADE_START:
        return "BOUND", "BLOOD"
    if frame < FADE_START + FADE:
        return "ACIDIFYING", "ENDOSOME"
    if frame < UNDOCK:
        return "BOTH SITES POSITIVE", "ENDOSOME"
    if frame < GONE:
        return "RELEASING", "ENDOSOME"
    return "RELEASED", "ENDOSOME"


# ---------------------------------------------------------------------- panel

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;
  background:#0a0e14 radial-gradient(1100px 820px at 50% 46%,#18222f 0%,#0a0e14 74%);
  font-family:-apple-system,'Segoe UI','Liberation Sans','DejaVu Sans',sans-serif;
  color:#e9edf3;-webkit-font-smoothing:antialiased}
.top{position:absolute;left:96px;top:66px}
.eyebrow{font-size:15px;font-weight:700;letter-spacing:3.4px;color:#78839a}
h1{font-size:36px;font-weight:600;letter-spacing:-.7px;margin-top:12px}
.stage{font-size:15px;letter-spacing:3px;color:#d6467f;margin-top:12px;
  font-weight:700}
.ph{position:absolute;right:96px;top:62px;text-align:right}
.ph b{font-size:62px;font-weight:600;letter-spacing:-2.5px;display:block;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.ph span{font-size:14px;letter-spacing:3px;color:#78839a}
.sites{position:absolute;right:96px;top:208px;width:420px}
.lab{font-size:11px;font-weight:700;letter-spacing:2px;color:#78839a;
  margin-bottom:10px;text-align:right}
.site{display:flex;align-items:center;gap:12px;margin-top:9px;font-size:14px}
.site b{width:66px;font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.site i{flex:1;height:6px;background:rgba(255,255,255,.10)}
.site u{display:block;height:6px}
.site s{width:56px;text-align:right;text-decoration:none;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.anchor{font-size:13px;color:#9aa3b4;margin-top:18px;text-align:right}
.anchor i{display:inline-block;width:10px;height:10px;border-radius:2px;
  background:#4f9ad6;margin-left:10px}
.membrane{position:absolute;left:0;width:1920px;height:0;
  border-top:2px dashed rgba(233,237,243,.20)}
.membrane span{position:absolute;right:96px;top:12px;font-size:13px;
  letter-spacing:2.4px;color:#5d6678}
.warn{position:absolute;left:96px;bottom:92px;font-size:13px;color:#9a7b45;
  line-height:1.6;max-width:1150px}
.warn b{letter-spacing:2.6px;font-size:12px}
.foot{position:absolute;left:96px;right:96px;bottom:44px;font-size:13px;
  color:#5d6678;display:flex;justify-content:space-between}
"""


def panel_html(frame: int, membrane_y: int) -> str:
    ph = ph_at(frame)
    label, where = stage(frame)
    sites = ""
    for position, pka in SITES:
        f = protonated(ph, pka)
        hue = blend_hex(NEUTRAL, POSITIVE, min(1.0, f / 0.75))
        sites += (f'<div class="site"><b>His{position}</b>'
                  f'<i><u style="width:{f*100:.0f}%;background:{hue}"></u></i>'
                  f'<s>{f*100:.0f}%</s></div>')
    return f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<body>
<div class="membrane" style="top:{membrane_y}px"><span>PLASMA MEMBRANE</span></div>
<div class="top">
<div class="eyebrow">TfR1 &middot; CHALLENGE 04</div>
<h1>Hold at pH 7.4, let go at pH 6.0</h1>
<div class="stage">{label} &middot; {where}</div></div>
<div class="ph"><b>{ph:.2f}</b><span>pH</span></div>
<div class="sites"><div class="lab">ENGINEERED HISTIDINES &middot; FRACTION PROTONATED</div>
{sites}
<div class="anchor">K344 and K374, positive at both pH values<i></i></div></div>
<div class="warn"><b>SCHEMATIC.</b> The receptor, the docked pose, the four
residues and every number here are predicted or measured. The approach and the
release are animation &mdash; nothing in this project simulated binding or
unbinding, and the computed linkage for this design is {SELECTIVITY}&times;
weaker binding at pH 6.0, not release.</div>
<div class="foot"><span>{DESIGN} &middot; crystal dimer 11QC &middot; PROPKA
per-site pK<sub>a</sub> 6.45 and 6.23</span>
<span>linkedin.com/in/anton-chernysh</span></div></body>"""


def blend_hex(low: str, high: str, t: float) -> str:
    a = [int(low[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(high[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def shoot(frame: int, membrane_y: int, path: Path) -> None:
    page = WORK / "page.html"
    page.write_text(panel_html(frame, membrane_y))
    subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         "--force-device-scale-factor=1", f"--window-size={WIDTH},{HEIGHT}",
         f"--screenshot={path}", page.as_uri()],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# --------------------------------------------------------------------- render

def blender(state: str, start: int, end: int) -> None:
    frames = WORK / state
    spec = {"structures": str(SOURCE), "frames": str(frames),
            "width": MOL_W, "height": MOL_H, "start": start, "end": end,
            "docked": DOCKED, "undock": UNDOCK, "gone": GONE, "travel": TRAVEL,
            "domains": [[sel, hue] for _, sel, hue in DOMAINS],
            "binder": BINDER_HUE, "lysine_hue": POSITIVE,
            "lysines": "resid 344 374",
            "histidines": "resid " + " ".join(str(p) for p, _ in SITES),
            "histidine_hue": NEUTRAL if state == "high" else POSITIVE}
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / f"spec-{state}.json").write_text(json.dumps(spec))
    subprocess.run(["blender", "-b", "--python", str(RENDER_PY),
                    "--", str(WORK / f"spec-{state}.json")], check=True)


def molecule_at(frame: int) -> Image.Image:
    if frame < FADE_START:
        return open_rgba("high", frame)
    if frame >= FADE_START + FADE:
        return open_rgba("low", frame)
    t = (frame - FADE_START) / FADE
    return Image.blend(open_rgba("high", frame), open_rgba("low", frame), t)


def open_rgba(state: str, frame: int) -> Image.Image:
    return Image.open(WORK / state / f"frame_{frame:04d}.png").convert("RGBA")


def lay(frame: int, out: Path) -> None:
    molecule = molecule_at(frame)
    box = molecule.getchannel("A").getbbox()
    membrane = MOL_Y + (box[3] if box else MOL_H) + 24
    plate = WORK / "plate.png"
    shoot(frame, min(membrane, HEIGHT - 150), plate)
    page = Image.open(plate).convert("RGBA")
    page.alpha_composite(molecule, (0, MOL_Y))
    page.convert("RGB").save(out)


def preview(frame: int) -> None:
    """One composited frame, before paying for the whole clip."""
    for state, want in (("high", frame < FADE_START + FADE),
                        ("low", frame >= FADE_START)):
        if want and not (WORK / state / f"frame_{frame:04d}.png").exists():
            blender(state, frame, frame)
    out = WORK / "preview.png"
    lay(frame, out)
    print(f"[preview] frame {frame} ({stage(frame)[0]}, pH {ph_at(frame):.2f}): {out}")


def render(force: bool = False) -> None:
    for state, start, end in (("high", 0, FADE_START + FADE - 1),
                              ("low", FADE_START, TOTAL - 1)):
        want = set(range(start, end + 1))
        folder = WORK / state
        have = ({int(p.stem.split("_")[1]) for p in folder.glob("frame_*.png")}
                if folder.exists() else set())
        if want <= have and not force:
            print(f"[render] reusing {state} frames")
            continue
        blender(state, start, end)
    out_dir = WORK / "composited"
    out_dir.mkdir(parents=True, exist_ok=True)
    for frame in range(TOTAL):
        lay(frame, out_dir / f"{frame:04d}.png")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", str(out_dir / "%04d.png"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", str(OUT)], check=True)
    print(f"[render] {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="render",
                    choices=["preview", "render"])
    ap.add_argument("--frame", type=int, default=DOCKED + 12)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if not SOURCE.is_dir():
        raise SystemExit(f"run dimer_still.py prep first: {SOURCE} is missing")
    if args.stage == "preview":
        preview(args.frame)
    else:
        render(args.force)


if __name__ == "__main__":
    main()
