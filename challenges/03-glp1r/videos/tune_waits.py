#!/usr/bin/env python3
"""Tune each scene so video_duration = audio_duration + LEAD + TAIL.

Modes:
  pace    one static pass, no render needed.  Uses `manim --dry_run` logs
          (C2_WAIT_LOG / C2_PLAY_LOG instrumentation in common.py) to know
          every wait execution and every play run_time exactly.  It then:
            - sets each in-loop wait (a reveal dwell) to PACE_DWELL,
            - scales every explicit `run_time=` by f (up to 2.2) so the
              reveals stretch over the narration,
            - gives the remainder to the scene's tail wait.
  tail    adjust only the LAST non-loop wait by (target - rendered duration);
          exact cleanup pass after a draft render.

Durations for `tail` come from the rendered draft clips and audio/.

Usage:  python tune_waits.py <vid|all> [--draft] [--apply] {pace,tail}
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

LEAD = build.LEAD_MS / 1000.0
TAIL = 1.2
PACE_DWELL = 2.5
PACE_F_MAX = 2.2
TAIL_TARGET = 7.0
MIN_WAIT = 0.5
WAIT_RE = re.compile(r"self\.wait\((\d+(?:\.\d+)?)\)")
RT_RE = re.compile(r"run_time=(\d+(?:\.\d+)?)")
DRY_WAIT_LOG = Path("/tmp/c2wait.log")
DRY_PLAY_LOG = Path("/tmp/c2play.log")


def class_span(src: str, scene: str):
    m = re.search(rf"^class {scene}\(\w+\):", src, re.M)
    if not m:
        return None
    nxt = re.search(r"^class \w+\(\w+\):", src[m.end():], re.M)
    end = m.end() + nxt.start() if nxt else len(src)
    return m.start(), end


def waits_with_context(body: str):
    """[(abs_start, abs_end, value, in_loop, line_index)] per self.wait(N)."""
    out = []
    for_stack: list[int] = []
    pos = 0
    for li, ln in enumerate(body.split("\n")):
        stripped = ln.lstrip()
        indent = len(ln) - len(stripped)
        while for_stack and indent <= for_stack[-1]:
            for_stack.pop()
        if re.match(r"for\b.*:\s*$", stripped):
            for_stack.append(indent)
        for m in WAIT_RE.finditer(ln):
            out.append((pos + m.start(), pos + m.end(), float(m.group(1)),
                        bool(for_stack), li))
        pos += len(ln) + 1
    return out


def apply_repls(path: Path, src: str, span, body: str, repls) -> bool:
    if not repls:
        return False
    out = body
    for a, b, new in sorted(repls, key=lambda x: -x[0]):
        out = out[:a] + new + out[b:]
    start, end = span
    path.write_text(src[:start] + out + src[end:])
    return True


def get_logs(v, scene: str):
    for p in (DRY_WAIT_LOG, DRY_PLAY_LOG):
        if p.exists():
            p.unlink()
    env = dict(os.environ, C2_WAIT_LOG=str(DRY_WAIT_LOG),
               C2_PLAY_LOG=str(DRY_PLAY_LOG))
    subprocess.run(
        [str(build.MANIM), "--dry_run", "-ql",
         str(build.ROOT / f"{v['module']}.py"), scene],
        cwd=str(build.ROOT), env=env, capture_output=True)

    def parse(path):
        rows = []
        if path.exists():
            for ln in path.read_text().splitlines():
                parts = ln.split()
                if len(parts) >= 2:
                    try:
                        rows.append((int(parts[0]), float(parts[1])))
                    except ValueError:
                        pass
        return rows

    return parse(DRY_WAIT_LOG), parse(DRY_PLAY_LOG)


def pace_scene(v, scene: str, target: float, apply: bool) -> str:
    src_path = build.ROOT / f"{v['module']}.py"
    src = src_path.read_text()
    span = class_span(src, scene)
    if span is None:
        return "class not found"
    body = src[span[0]:span[1]]
    start_line = src[:span[0]].count("\n") + 1
    end_line = start_line + body.count("\n")

    wait_log, play_log = get_logs(v, scene)
    in_class = lambda l: start_line <= l <= end_line
    P = sum(rt for l, rt in play_log if in_class(l))
    counts: dict[int, int] = {}
    for l, _ in wait_log:
        if in_class(l):
            counts[l] = counts.get(l, 0) + 1
    if not counts:
        return "no dry-run wait counts"

    waits = waits_with_context(body)
    tail_i = None
    for i, (_, _, _, in_loop, _) in enumerate(waits):
        if not in_loop:
            tail_i = i
    if tail_i is None:
        tail_i = len(waits) - 1

    W_new = 0.0
    for i, (_, _, val, in_loop, li) in enumerate(waits):
        cnt = counts.get(start_line + li, 1)
        nv = PACE_DWELL if (in_loop and i != tail_i) else val
        W_new += nv * cnt

    delta = target - (P + W_new)
    T = waits[tail_i][2]

    f = 1.0
    if P > 0.2:
        f = 1.0 + (T + delta - TAIL_TARGET) / P
        f = max(1.0, min(PACE_F_MAX, f))
    tail_new = T + delta - (f - 1.0) * P
    if tail_new < MIN_WAIT and P > 0.2:
        f = max(1.0, 1.0 + (T + delta - MIN_WAIT) / P)
        f = min(f, PACE_F_MAX)
        tail_new = T + delta - (f - 1.0) * P
    tail_new = max(MIN_WAIT, round(tail_new, 1))

    repls = []
    for i, (a, b, val, in_loop, _) in enumerate(waits):
        if i == tail_i:
            if abs(val - tail_new) >= 0.05:
                repls.append((a, b, f"self.wait({tail_new:g})"))
        elif in_loop and abs(val - PACE_DWELL) >= 0.05:
            repls.append((a, b, f"self.wait({PACE_DWELL:g})"))
    if f > 1.05:
        for m in RT_RE.finditer(body):
            old = float(m.group(1))
            new = round(old * f, 2)
            if abs(new - old) >= 0.05:
                repls.append((m.start(), m.end(), f"run_time={new:g}"))

    if apply:
        apply_repls(src_path, src, span, body, repls)
    return (f"P={P:5.1f} W={W_new:5.1f} delta={delta:+6.2f} f={f:.2f} "
            f"tail {T:g}->{tail_new:g}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    ap.add_argument("mode", choices=["pace", "tail"])
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    quality = "draft" if a.draft else "final"
    for v in build.pick(a.vid):
        mod = build.module(v)
        print(f"== {v['module']}")
        for n in mod.NARRATION:
            ap_ = build.audio_path(v, n)
            if not ap_.exists():
                print(f"  {n:16s}  missing audio")
                continue
            ad = build.dur(ap_)
            target = ad + LEAD + TAIL
            if a.mode == "pace":
                msg = pace_scene(v, n, target, a.apply)
                print(f"  {n:16s}  {'APPLIED' if a.apply else 'DRY    '}  {msg}")
                continue
            clip = build.scene_clip(v, n, quality)
            if clip is None:
                print(f"  {n:16s}  missing render")
                continue
            vd = build.dur(clip)
            delta = target - vd
            if abs(delta) < 0.3:
                print(f"  {n:16s}  ok  (video {vd:6.2f}s, audio {ad:6.2f}s)")
                continue
            src = (build.ROOT / f"{v['module']}.py").read_text()
            span = class_span(src, n)
            body = src[span[0]:span[1]]
            waits = waits_with_context(body)
            outside = [w for w in waits if not w[3]]
            x, y, val, _, _ = outside[-1] if outside else waits[-1]
            new = max(0.5, round(val + delta, 1))
            repls = [(x, y, f"self.wait({new:g})")] if abs(new - val) >= 0.05 else []
            if a.apply:
                apply_repls(build.ROOT / f"{v['module']}.py", src, span, body, repls)
            print(f"  {n:16s}  tail {'APPLIED' if a.apply else 'DRY'}  "
                  f"({val:g} -> {new:g})   (video {vd:6.2f}s, audio {ad:6.2f}s)")


if __name__ == "__main__":
    main()
