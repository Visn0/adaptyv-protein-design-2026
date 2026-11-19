"""Post-process the carousel render: fades, title block, per-design labels.

Reads the manifest written by prep_carousel.py, builds the ffmpeg filter chain
(one drawtext window per design, one second each) and writes the final MP4.

    python3 finish_carousel.py --raw ~/c2-work/mn-anim/carousel_render/carousel_raw.mp4 \
        --out tnfa-carousel-22-designs.mp4
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

FONT = "/mnt/c/Windows/Fonts/arial.ttf"
FONT_BOLD = "/mnt/c/Windows/Fonts/arialbd.ttf"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--manifest",
                    default=str(Path.home() / "c2-work/mn-anim/carousel"
                                / "manifest.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--secs-per-design", type=float, default=1.0)
    ap.add_argument("--headline", default="22 designs bind a subunit interface")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    n = len(manifest)
    total = n * args.secs_per_design
    fade_out = round(max(0.0, total - 0.5), 2)

    parts = [
        f"fade=t=in:st=0:d=0.5",
        f"fade=t=out:st={fade_out}:d=0.5",
        # title block, top-left
        (f"drawtext=fontfile={FONT}:"
         f"text='Anthropic × Adaptyv Protein Design Competition':"
         f"fontcolor=0x6b7280:fontsize=30:x=64:y=74"),
        (f"drawtext=fontfile={FONT_BOLD}:text='TNF-α':"
         f"fontcolor=0x111827:fontsize=80:x=64:y=118"),
        (f"drawtext=fontfile={FONT}:text='{args.headline}':"
         f"fontcolor=0x4b5563:fontsize=36:x=64:y=224"),
    ]
    # per-design label, bottom-left
    for e in manifest:
        t0 = (e["idx"] - 1) * args.secs_per_design
        t1 = e["idx"] * args.secs_per_design
        label = f"{e['idx']:02d}/{n} · {e['name']}"
        parts.append(
            f"drawtext=fontfile={FONT}:text='{label}':fontcolor=0x6b7280:"
            f"fontsize=30:x=64:y=h-84:enable='gte(t,{t0})*lt(t,{t1})'")

    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", args.raw,
        "-vf", ",".join(parts),
        "-c:v", "libx264", "-crf", "17", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        args.out,
    ]
    print("[finish]", " ".join(cmd[:8]), "...")
    subprocess.run(cmd, check=True)
    print(f"[finish] wrote {args.out} ({total:.0f}s, {n} designs)")


if __name__ == "__main__":
    main()
