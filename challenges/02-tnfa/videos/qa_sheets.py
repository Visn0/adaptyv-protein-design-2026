#!/usr/bin/env python3
"""QA sheets: one frame every 10 s from every final video, one sheet per video.

Each sheet is a grid of frames scaled to CELL_W, every cell labelled with its
timestamp.  Sheets land in qa/ (<slug>_sheet.png); the raw frames land in
qa/frames/<slug>/ (gitignored).

Usage:  python3 qa_sheets.py [slug ...]     # default: every out/*.mp4
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
QA = ROOT / "qa"
STEP = 10.0          # one screenshot every 10 seconds
CELL_W = 480         # px per cell in the sheet
COLS = 5
LABEL_H = 26
FONT_CANDIDATES = [
    str(Path.home() / ".fonts/JetBrainsMono-Regular.ttf"),
    "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]


def head(t: float) -> str:
    s = int(round(t))
    return f"{s // 60}:{s % 60:02d}"


def font(size: int = 18) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def one_sheet(video: Path) -> None:
    slug = video.stem
    dur = probe_duration(video)
    fdir = QA / "frames" / slug
    fdir.mkdir(parents=True, exist_ok=True)

    times = []
    t = 0.0
    while t < dur - 0.4:
        times.append(t)
        t += STEP
    if dur > 2 and (not times or dur - 1.0 - times[-1] > 4):
        times.append(dur - 1.0)          # always show the final frame

    frames = []
    for t in times:
        png = fdir / f"t{int(t):04d}.png"
        if not png.exists():
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(video),
                 "-frames:v", "1", str(png)],
                capture_output=True, check=True)
        frames.append((t, Image.open(png)))

    cell_h = int(frames[0][1].height * CELL_W / frames[0][1].width)
    rows = math.ceil(len(frames) / COLS)
    sheet = Image.new("RGB",
                      (COLS * (CELL_W + 8) + 8, rows * (cell_h + LABEL_H + 8) + 8),
                      (16, 18, 26))
    d = ImageDraw.Draw(sheet)
    f = font()
    for i, (t, im) in enumerate(frames):
        x = 8 + (i % COLS) * (CELL_W + 8)
        y = 8 + (i // COLS) * (cell_h + LABEL_H + 8)
        sheet.paste(im.resize((CELL_W, cell_h)), (x, y))
        d.text((x + 4, y + cell_h + 3), f"t = {head(t)}", fill=(150, 160, 180), font=f)
    out = QA / f"{slug}_sheet.png"
    sheet.save(out)
    print(f"{slug}: {len(frames)} frames -> {out.name} ({sheet.size[0]}x{sheet.size[1]})")


def main() -> None:
    QA.mkdir(exist_ok=True)
    wanted = set(sys.argv[1:])
    vids = sorted(OUT.glob("*.mp4"))
    if wanted:
        vids = [v for v in vids if v.stem in wanted]
    if not vids:
        raise SystemExit("no videos found in out/")
    for v in vids:
        one_sheet(v)


if __name__ == "__main__":
    main()
