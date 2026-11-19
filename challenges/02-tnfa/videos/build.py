#!/usr/bin/env python3
"""Build driver for the C2 campaign video series.

Commands
--------
render <vid|all> draft|final [Scene ...]   Manim-render each scene
audio  <vid|all>                            edge-tts narration per scene
check  <vid|all> [--draft]                  duration + narration-margin report
segments <vid|all>                          build prebuilt media segments
stitch <vid|all> [--draft]                  concat + mux + subtitles -> out/
build  <vid|all> [--draft]                  audio + stitch (renders assumed done)

`vid` is a video number (1..14) or a module name (v01_challenge2).
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
MANIM = HOME / ".venvs/manim-cf/bin/manim"
TTS_PY = HOME / ".venvs/tts/bin/python"
VOICE = "en-US-AndrewNeural"
LEAD_MS = 350
MAX_S = 300.0  # the hard cap per video

VIDEOS = [
    dict(num=1, module="v01_challenge2", slug="01-challenge-2-the-inverted-switch"),
    dict(num=2, module="v02_anchors", slug="02-c2-anchors"),
    dict(num=3, module="v03_motif", slug="03-c2-switch-motif"),
    dict(num=4, module="v04_controls", slug="04-c2-scorer-controls"),
    dict(num=5, module="v05_coverage", slug="05-c2-coverage-scan"),
    dict(num=6, module="v06_score", slug="06-c2-score-designs"),
    dict(num=7, module="v07_baseline", slug="07-c2-baseline-results"),
    dict(num=8, module="v08_foldw1", slug="08-c2-fold-w1-gpu"),
    dict(num=9, module="v09_x1", slug="09-x1-boltzgen-benchmark"),
    dict(num=10, module="v10_x2", slug="10-x2-rfdiffusion3-probe"),
    dict(num=11, module="v11_w2", slug="11-w2-shortlist-folds"),
    dict(num=12, module="v12_x3", slug="12-x3-site-check-campaign-close"),
    dict(num=13, module="v13_genie3", slug="13-genie3-two-promising-designs"),
    dict(num=14, module="v14_champion", slug="14-final-campaign-the-champion",
         media=[
             dict(scene="S7_MD_d7", src="../md-movies/d7x-t3-3_md-binding.mp4"),
             dict(scene="S8_MD_d12", src="../md-movies/b2x-d12-2_md-binding.mp4"),
         ]),
]


# ------------------------------------------------------------------ helpers
def pick(arg: str):
    if arg == "all":
        return VIDEOS
    for v in VIDEOS:
        if str(v["num"]) == arg or v["module"] == arg or v["slug"] == arg:
            return [v]
    raise SystemExit(f"unknown video: {arg}")


def module(v):
    sys.path.insert(0, str(ROOT))
    return importlib.import_module(v["module"])


def names_of(v):
    return list(module(v).NARRATION.keys())


def dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def media_dir(quality: str) -> Path:
    return ROOT / ("media" if quality == "final" else "media_draft")


def scene_clip(v, scene: str, quality: str):
    base = media_dir(quality) / "videos" / v["module"]
    hits = [p for p in base.rglob(f"{scene}.mp4")
            if "partial_movie_files" not in str(p)]
    return hits[0] if hits else None


def audio_path(v, scene: str) -> Path:
    return ROOT / "audio" / v["module"] / f"{scene}.mp3"


# ------------------------------------------------------------------ commands
def cmd_render(v, quality, only=None):
    m = module(v)
    # Manim renders scenes that have a class; media segments are prebuilt
    names = [n for n in m.NARRATION
             if (not only or n in only) and hasattr(m, n)]
    md = media_dir(quality)
    res = ["-r", "1920,1080", "--fps", "30"] if quality == "final" else ["-ql"]
    for n in names:
        print(f"render {v['module']} {n} [{quality}]", flush=True)
        subprocess.run(
            [str(MANIM), *res, "--media_dir", str(md), "-v", "WARNING",
             "-o", n, str(ROOT / f"{v['module']}.py"), n],
            check=True, cwd=str(ROOT))


def cmd_audio(v):
    m = module(v)
    adir = ROOT / "audio" / v["module"]
    adir.mkdir(parents=True, exist_ok=True)
    for n, text in m.NARRATION.items():
        mp3, js = adir / f"{n}.mp3", adir / f"{n}.json"
        if mp3.exists() and js.exists() and mp3.stat().st_size > 1000:
            print(f"audio {v['module']} {n} (cached)")
            continue
        tf = adir / f"{n}.txt"
        tf.write_text(text, encoding="utf-8")
        print(f"audio {v['module']} {n}", flush=True)
        subprocess.run([str(TTS_PY), str(ROOT / "tts_synth.py"),
                        str(tf), str(mp3), str(js), VOICE], check=True)


def cmd_check(vs, quality="final"):
    bad = 0
    for v in vs:
        names = names_of(v)
        total_v = total_a = 0.0
        print(f"\n== {v['slug']}")
        for n in names:
            clip = scene_clip(v, n, quality)
            if clip is None:
                print(f"  {n:16s}  NO RENDER")
                bad += 1
                continue
            vd = dur(clip)
            total_v += vd
            ap = audio_path(v, n)
            if ap.exists():
                ad = dur(ap)
                total_a += ad
                margin = vd - ad - LEAD_MS / 1000
                flag = "  <<< OVERFLOW" if margin < 0.15 else ""
                if margin < 0.15:
                    bad += 1
                print(f"  {n:16s}  video {vd:6.2f}s  audio {ad:6.2f}s  margin {margin:+5.2f}s{flag}")
            else:
                print(f"  {n:16s}  video {vd:6.2f}s  audio  (none)")
        cap = "  <<< OVER CAP" if total_v > MAX_S else ""
        print(f"  total video {total_v:6.1f}s  narration {total_a:6.1f}s{cap}")
    return bad


def _fmt(t: float) -> str:
    ms = int(round(t * 1000))
    h, m = ms // 3600000, (ms % 3600000) // 60000
    s, mm = (ms % 60000) // 1000, ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{mm:03d}"


def _wrap(text: str, width: int = 46) -> str:
    """Two-line wrap at a word boundary for long subtitle cues."""
    if len(text) <= width:
        return text
    mid = len(text) // 2
    left = text.rfind(" ", 0, mid)
    right = text.find(" ", mid)
    if left == -1 and right == -1:
        return text
    cut = left if (left != -1 and (right == -1 or mid - left <= right - mid)) else right
    return text[:cut] + "\n" + text[cut + 1:]


def write_srt(v, names, vdurs, srt: Path):
    cues = []
    off = 0.0
    for n, vd in zip(names, vdurs):
        events = json.loads((audio_path(v, n).with_suffix(".json")).read_text())
        if events and events[0].get("kind") == "SentenceBoundary":
            for e in events:
                start = off + LEAD_MS / 1000 + e["offset"] / 1e7
                end = off + LEAD_MS / 1000 + (e["offset"] + e["duration"]) / 1e7
                cues.append((start, end, _wrap(e["text"])))
        else:
            cur: list = []

            def flush():
                nonlocal cur
                if not cur:
                    return
                start = off + LEAD_MS / 1000 + cur[0]["offset"] / 1e7
                end = off + LEAD_MS / 1000 + (cur[-1]["offset"] + cur[-1]["duration"]) / 1e7
                cues.append((start, end, _wrap(" ".join(w["text"] for w in cur))))
                cur = []

            for w in events:
                cur.append(w)
                if w["text"].rstrip().endswith((".", "!", "?", "\u2026")) or len(cur) >= 12:
                    flush()
            flush()
        off += vd
    out = []
    for i, (a, b, txt) in enumerate(cues, 1):
        out.append(f"{i}\n{_fmt(a)} --> {_fmt(b)}\n{txt}\n")
    srt.write_text("\n".join(out), encoding="utf-8")


def cmd_segments(v):
    """Build prebuilt media segments (video clips) into the scene render tree.

    A segment replaces a Manim scene: it is a normalized 1920x1080/30 clip,
    cloned on its last frame when the narration needs more time.
    """
    specs = v.get("media") or []
    if not specs:
        print(f"no media segments for {v['module']}")
        return
    md = media_dir("final") / "videos" / v["module"]
    md.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        scene = spec["scene"]
        src = (ROOT / spec["src"]).resolve()
        ap = audio_path(v, scene)
        if not ap.exists():
            raise SystemExit(f"missing narration audio for {scene} — run `audio` first")
        ad = dur(ap)
        clip_d = dur(src)
        target = max(clip_d, ad + LEAD_MS / 1000 + 0.85)
        pad = max(0.0, target - clip_d)
        vf = (f"fps=30,tpad=stop_mode=clone:stop_duration={pad:.3f}"
              if pad > 0.001 else "fps=30")
        out = md / f"{scene}.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src),
                        "-vf", vf, "-t", f"{target:.3f}",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                        "-pix_fmt", "yuv420p", "-an", str(out)], check=True)
        print(f"segment {v['module']} {scene}: {dur(out):.2f}s (narration {ad:.2f}s)")


def cmd_stitch(v, draft=False):
    quality = "draft" if draft else "final"
    names = names_of(v)
    clips = [scene_clip(v, n, quality) for n in names]
    missing = [n for n, c in zip(names, clips) if c is None]
    if missing:
        raise SystemExit(f"missing renders for {v['module']}: {missing}")
    adir = ROOT / "audio" / v["module"]
    vdurs = [dur(c) for c in clips]
    adurs = [dur(audio_path(v, n)) for n in names]
    total = sum(vdurs)
    ok = True
    for n, vd, ad in zip(names, vdurs, adurs):
        if ad + LEAD_MS / 1000 > vd - 0.15:
            print(f"  !! OVERFLOW {n}: audio {ad:.2f}s > video {vd:.2f}s", flush=True)
            ok = False
    if total > MAX_S:
        print(f"  !! over the {MAX_S:.0f}s cap: {total:.1f}s", flush=True)
        ok = False

    outdir = ROOT / "out"
    outdir.mkdir(exist_ok=True)

    # narration track: one padded segment per scene, concatenated
    cmd = ["ffmpeg", "-y"]
    for n in names:
        cmd += ["-i", str(audio_path(v, n))]
    fc = [f"[{i}:a]adelay={LEAD_MS}:all=1,apad=whole_dur={vd:.3f}[a{i}]"
          for i, (n, vd) in enumerate(zip(names, vdurs))]
    fc.append("".join(f"[a{i}]" for i in range(len(names)))
              + f"concat=n={len(names)}:v=0:a=1[out]")
    narr = outdir / (v["slug"] + ".m4a")
    subprocess.run(cmd + ["-filter_complex", ";".join(fc), "-map", "[out]",
                          "-c:a", "aac", "-b:a", "192k", str(narr)],
                   check=True, capture_output=True)

    # silent video: concat the scene clips
    lst = outdir / (v["slug"] + ".list.txt")
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    silent = outdir / (v["slug"] + ".silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(silent)], check=True, capture_output=True)

    # subtitles from the edge-tts word boundaries
    srt = outdir / (v["slug"] + ".srt")
    write_srt(v, names, vdurs, srt)

    final = outdir / (v["slug"] + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-i", str(silent), "-i", str(narr), "-i", str(srt),
                    "-map", "0:v", "-map", "1:a", "-map", "2:s",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
                    "-t", f"{total:.3f}", "-movflags", "+faststart", str(final)],
                   check=True, capture_output=True)
    silent.unlink()
    lst.unlink()
    narr.unlink()
    print(f"FINAL {final.name}  {total:.1f}s  {'OK' if ok else 'WITH WARNINGS'}")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["render", "audio", "check", "segments", "stitch", "build"])
    ap.add_argument("vid")
    ap.add_argument("quality", nargs="?", default="final")
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    vs = pick(a.vid)

    if a.cmd == "render":
        q = "draft" if a.quality == "draft" else "final"
        for v in vs:
            cmd_render(v, q, only=a.scenes or None)
    elif a.cmd == "audio":
        for v in vs:
            cmd_audio(v)
    elif a.cmd == "check":
        bad = cmd_check(vs, "draft" if a.draft else "final")
        print(f"\nproblems: {bad}")
    elif a.cmd == "segments":
        for v in vs:
            cmd_segments(v)
    elif a.cmd == "stitch":
        for v in vs:
            cmd_stitch(v, draft=a.draft)
    elif a.cmd == "build":
        for v in vs:
            cmd_audio(v)
            cmd_segments(v)
            cmd_stitch(v, draft=a.draft)


if __name__ == "__main__":
    main()
