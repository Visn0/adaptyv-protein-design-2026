"""Shared style, palette and layout helpers for the C2 campaign video series.

Every video module defines scene classes plus a NARRATION dict keyed by the
class name.  build.py renders each scene with Manim, synthesises one narration
track per scene (edge-tts), then stitches video, audio and subtitles into one
MP4 under out/.

Palette matches the local app (tools/serve): proteinbase navy, cyan accent,
and the repository colour standard: blue = target, pink = binder,
amber = interface.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))

# When C2_WAIT_LOG is set (used by tune_waits.py with manim --dry_run), every
# self.wait() call records "file_line duration" so loop iteration counts can
# be measured exactly.  C2_PLAY_LOG does the same for self.play() run_times.
_WAIT_LOG = os.environ.get("C2_WAIT_LOG")
_PLAY_LOG = os.environ.get("C2_PLAY_LOG")

# ------------------------------------------------------------------ palette
BG     = "#0b0c14"   # navy, same as the local app
PANEL  = "#12151f"
BORDER = "#232a3d"
INK    = "#e8ebf2"
MUTED  = "#8b93a7"
DIM    = "#4a5266"
CYAN   = "#0da2e7"   # accent
BLUE   = "#60a5fa"   # target
PINK   = "#e879f9"   # designed binder
AMBER  = "#fbbf24"   # interface / highlight
GREEN  = "#34d399"   # pass
RED    = "#f87171"   # fail
VIOLET = "#a78bfa"   # external / GPU step

FONT = "JetBrains Mono"

SERIES   = "TNF-\u03b1 CAMPAIGN"
N_VIDEOS = 12


def T(s, size=24, color=INK, weight=NORMAL, **kw) -> Text:
    return Text(s, font=FONT, font_size=size, color=color, weight=weight, **kw)


class C2(Scene):
    """Base scene: navy background plus small layout helpers."""

    series = SERIES
    experiment = ""

    def setup(self):
        self.camera.background_color = BG

    def wait(self, duration: float = 1.0, **kwargs):
        if _WAIT_LOG:
            import inspect
            frame = inspect.currentframe().f_back
            with open(_WAIT_LOG, "a", encoding="utf-8") as fh:
                fh.write(f"{frame.f_lineno} {duration}\n")
        return super().wait(duration, **kwargs)

    def play(self, *args, **kwargs):
        if _PLAY_LOG:
            import inspect
            frame = inspect.currentframe().f_back
            with open(_PLAY_LOG, "a", encoding="utf-8") as fh:
                fh.write(f"{frame.f_lineno} {kwargs.get('run_time', 1.0)}\n")
        return super().play(*args, **kwargs)

    # -------------------------------------------------------------- chrome
    def header(self, right=None):
        left = T(self.series, size=16, color=DIM)
        left.to_corner(UL, buff=0.42)
        grp = VGroup(left)
        tag = right or self.experiment
        if tag:
            r = T(tag, size=16, color=DIM)
            r.to_corner(UR, buff=0.42)
            grp.add(r)
        self.add(grp)
        return grp

    def caption(self, s, color=DIM, size=18):
        c = T(s, size=size, color=color)
        c.to_edge(DOWN, buff=0.5)
        return c

    def finish(self, run_time=0.6):
        self.play(FadeOut(Group(*self.mobjects)), run_time=run_time)

    # -------------------------------------------------------------- blocks
    def card(self, w, h, stroke=BORDER, fill=PANEL, fill_opacity=1.0, radius=0.14):
        return RoundedRectangle(corner_radius=radius, width=w, height=h,
                                stroke_color=stroke, stroke_width=2,
                                fill_color=fill, fill_opacity=fill_opacity)

    def chip(self, label, color=CYAN, size=18):
        t = T(label, size=size, color=color, weight=BOLD)
        box = RoundedRectangle(corner_radius=0.26,
                               width=t.width + 0.52, height=t.height + 0.3,
                               stroke_color=color, stroke_width=2,
                               fill_color=color, fill_opacity=0.12)
        t.move_to(box)
        return VGroup(box, t)

    def bullets(self, lines, size=24, buff=0.34, dot_color=CYAN, color=INK):
        rows = VGroup()
        for ln in lines:
            dot = Dot(radius=0.05, color=dot_color)
            t = T(ln, size=size, color=color)
            row = VGroup(dot, t).arrange(RIGHT, buff=0.24)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=buff)
        return rows

    def step_strip(self, labels, colors=None, active=None, size=15,
                   gap=0.34, pad=0.5):
        boxes = VGroup()
        for i, l in enumerate(labels):
            t = T(l, size=size, color=INK)
            base = colors[i] if colors else BORDER
            hot = active is not None and i == active
            stroke = CYAN if hot else base
            box = self.card(t.width + pad, max(t.height + 0.55, 0.85),
                            stroke=stroke,
                            fill=PANEL, fill_opacity=0.25 if hot else 1.0)
            t.move_to(box)
            boxes.add(VGroup(box, t))
        boxes.arrange(RIGHT, buff=gap)
        arrows = VGroup()
        for i in range(len(boxes) - 1):
            arrows.add(Arrow(boxes[i].get_right(), boxes[i + 1].get_left(),
                             buff=0.04, stroke_width=2.4, color=DIM,
                             tip_length=0.15,
                             max_tip_length_to_length_ratio=0.3))
        return VGroup(boxes, arrows), boxes

    def number_row(self, items, size_big=52, size_lab=18, buff=0.85, color=CYAN):
        """items: (value, label) or (value, label, color)."""
        g = VGroup()
        for it in items:
            col = it[2] if len(it) > 2 else color
            v = T(str(it[0]), size=size_big, color=col, weight=BOLD)
            l = T(str(it[1]), size=size_lab, color=MUTED)
            g.add(VGroup(v, l).arrange(DOWN, buff=0.14))
        g.arrange(RIGHT, buff=buff)
        return g

    def dot_plot(self, values, w=7.6, h=3.3, ymin=0.0, ymax=1.0,
                 thresholds=(), color=PINK, size=15):
        """values: list of (label, y).  thresholds: (y, color, label)."""
        if thresholds and not isinstance(thresholds[0], (tuple, list)):
            thresholds = (thresholds,)
        x0 = -w / 2

        def y2p(v):
            return -h / 2 + (v - ymin) / (ymax - ymin) * h

        axis = Line([x0, -h / 2, 0], [x0, h / 2, 0], color=BORDER, stroke_width=2)
        g = VGroup(axis)
        for tv, tc, tl in thresholds:
            gl = DashedLine([x0, y2p(tv), 0], [x0 + w, y2p(tv), 0],
                            color=tc, dash_length=0.09, stroke_width=1.7)
            lab = T(tl, size=size, color=tc).next_to(gl, LEFT, buff=0.1)
            g.add(gl, lab)
        step = w / max(len(values), 1)
        for i, (lab, v) in enumerate(values):
            x = x0 + step * (i + 0.55)
            g.add(Dot([x, y2p(v), 0], radius=0.085, color=color))
            g.add(T(lab, size=size, color=MUTED).move_to([x, -h / 2 - 0.26, 0]))
        return g

    def hbar(self, value, max_value=1.0, width=3.4, height=0.17, color=PINK):
        w = max(width * (value / max_value), 0.02)
        return RoundedRectangle(corner_radius=0.06, width=w, height=height,
                                stroke_width=0, fill_color=color, fill_opacity=1.0)
