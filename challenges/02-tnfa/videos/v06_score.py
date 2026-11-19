"""Video 06 — c2-score-designs: ranking folded complexes by pH selectivity.

The final local ranking stage, its sign convention, and why it waited for
input that never came in this campaign.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "c2-score-designs"

    def construct(self):
        k = T("VIDEO 06 / 12  ·  EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("c2-score-designs", size=56, color=INK, weight=BOLD)
        s = T("Ranking folded complexes by predicted pH selectivity \u2014\nthe final local stage.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=0.92)
        self.play(Write(t), run_time=1.61)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.15)
        self.wait(5.6)
        self.finish()


class S2_What(C2):
    experiment = "c2-score-designs"

    def construct(self):
        self.header()
        head = T("Rank the folds by predicted selectivity", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "run the linkage scorer over folded complexes",
            "PROPKA on the complex, the free binder, the free target",
            "integrate across the 6.0\u20137.4 window",
            "write ranked_designs.csv \u2014 one row per design",
        ], size=21, buff=0.38)
        b.move_to(UP * 0.2).to_edge(LEFT, buff=1.0)

        chip = self.chip("for challenge 2 the wanted sign is POSITIVE", CYAN, size=20)
        chip.move_to(DOWN * 2.3)

        self.play(Write(head), run_time=0.9)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.55)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=0.7)
        self.wait(4.4)
        self.finish()


class S3_Sign(C2):
    experiment = "c2-score-designs"

    def construct(self):
        self.header()
        head = T("The sign convention", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        def panel(sign, label, detail, col, x):
            c = self.card(5.9, 3.0, stroke=col)
            s = T(sign, size=40, color=col, weight=BOLD)
            l = T(label, size=22, color=INK)
            d = T(detail, size=18, color=MUTED)
            g = VGroup(s, l, d).arrange(DOWN, buff=0.28).move_to(c)
            return VGroup(c, g).move_to([x, 0.1, 0])

        p1 = panel("delta_log_Ka > 0", "binds harder at pH 7.4", "the wanted direction \u2014 challenge 2", GREEN, -3.5)
        p2 = panel("delta_log_Ka < 0", "binds harder at pH 6.0", "the challenge 1 direction \u2014 the trap", RED, 3.5)

        note = T("always read the sign before believing a candidate", size=20, color=MUTED)
        note.move_to(DOWN * 2.6)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(p1, shift=RIGHT * 0.2), run_time=1.76)
        self.play(FadeIn(p2, shift=LEFT * 0.2), run_time=1.76)
        self.play(FadeIn(note), run_time=1.32)
        self.wait(10.4)
        self.finish()


class S4_Steps(C2):
    experiment = "c2-score-designs"

    def construct(self):
        self.header()
        head = T("The stage, end to end", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        strip, boxes = self.step_strip(
            ["complexes\nin", "PROPKA \u00d73", "integrate", "ranked\ndesigns.csv",
             "count > 0", "top 16\n\u2192 viewer"],
            size=15,
        )
        strip.move_to(UP * 1.2)

        b = self.bullets([
            "input: folded complexes \u2014 binder chain C, target chains A and B",
            "the summary states the sign convention in its note, every run",
            "the report shows the best complexes in the 3D view",
        ], size=20, buff=0.36)
        b.next_to(strip, DOWN, buff=1.0).to_edge(LEFT, buff=1.0)

        self.play(Write(head), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(x) for x in boxes], lag_ratio=0.16), run_time=1.5)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.5)
            self.wait(2.5)
        self.wait(2.3)
        self.finish()


class S5_Status(C2):
    experiment = "c2-score-designs"

    def construct(self):
        self.header()
        head = T("Status: waiting for input", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "the stage needs folded complexes \u2014 it never got them",
            "the upstream run docked 0 designs; local folds were scored by ipSAE",
            "and, later, by the site check that closed the campaign",
        ], size=21, buff=0.4)
        b.move_to(UP * 0.4).to_edge(LEFT, buff=1.0)

        note = T("a stage that is never fed is not a failure \u2014 it is a gate that held",
                 size=20, color=MUTED)
        note.move_to(DOWN * 2.1)

        self.play(Write(head), run_time=1.46)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.89)
            self.wait(2.5)
        self.play(FadeIn(note), run_time=1.13)
        self.wait(5.8)
        self.finish()


NARRATION = {
    "S1_Title": (
        "Experiment six: c2-score-designs. The final local stage \u2014 ranking folded complexes by "
        "predicted pH selectivity."
    ),
    "S2_What": (
        "The stage runs the validated linkage scorer over folded complexes: PROPKA on the "
        "complex, on the free binder, and on the free target; integrate across the window; "
        "write one row per design. For challenge 2, the wanted sign is positive \u2014 binding "
        "stronger at pH seven point four."
    ),
    "S3_Sign": (
        "The sign convention decides everything. A positive delta_log_Ka means the binder holds "
        "harder at pH seven point four: the wanted direction. A negative value is the challenge "
        "one direction \u2014 the trap for this challenge. Always read the sign before believing a "
        "candidate."
    ),
    "S4_Steps": (
        "The stage takes folded complexes \u2014 binder chain C, target chains A and B \u2014 scores "
        "them, ranks them, counts the designs above zero, and puts the best sixteen into the 3D "
        "viewer."
    ),
    "S5_Status": (
        "The honest status: this stage waits for folded complexes, and in this campaign it "
        "never got them. The upstream run docked nothing, and the local folds were scored by "
        "ipSAE \u2014 and later by the site check that closed the campaign. A stage that is never "
        "fed is not a failure. It is a gate that held."
    ),
}
