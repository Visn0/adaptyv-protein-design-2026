"""Video 10 — X2: the RFdiffusion3 probe.

Changing the generator, the quota surprise, 72 placed complexes, and the
decisive co-fold that passed once.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "X2 \u00b7 RFdiffusion3 probe"

    def construct(self):
        k = T("VIDEO 10 / 12  \u00b7  CAMPAIGN EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("X2: the RFdiffusion3 probe", size=52, color=INK, weight=BOLD)
        s = T("Change the generator. 72 complexes \u2014 and the\ndecisive co-fold.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.39)
        self.play(Write(t), run_time=2.42)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.73)
        self.wait(5.6)
        self.finish()


class S2_Why(C2):
    experiment = "X2 \u00b7 RFdiffusion3 probe"

    def construct(self):
        self.header()
        head = T("The one lever without new hardware", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "RFdiffusion3: the all-atom successor, about 1/10 the compute",
            "schema read first \u2014 its built-in designability refold handles one chain only",
            "so for a trimer that option stays off",
            "candidates are scored by our own Boltz-2 co-folds instead",
        ], size=21, buff=0.4)
        b.move_to(UP * 0.2).to_edge(LEFT, buff=1.0)

        chip = self.chip("same hotspots as X1/S1 \u00b7 70\u201395 aa \u00b7 step scale 1.5", MUTED, size=18)
        chip.move_to(DOWN * 2.4)

        self.play(Write(head), run_time=1.06)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.65)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=0.71)
        self.wait(5.8)
        self.finish()


class S3_Quota(C2):
    experiment = "X2 \u00b7 RFdiffusion3 probe"

    def construct(self):
        self.header()
        head = T("The quota surprise", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        row = self.number_row([
            ("48", "designs\nrequested", MUTED),
            ("6", "GPU batches\n= 6 jobs", AMBER),
            ("9 / 10", "jobs spent\nafter X1", AMBER),
            ("1", "job left \u2014\none co-fold", CYAN),
        ], size_big=44, buff=0.95)
        row.move_to(UP * 0.45)

        note = T("RFdiffusion3 bills per diffusion batch \u2014 BoltzGen billed per run", size=19, color=INK)
        note.move_to(DOWN * 1.5)
        note2 = T("the twin run was rejected outright: 9 used, 6 requested, limit 10",
                  size=19, color=RED)
        note2.move_to(DOWN * 2.15)
        note3 = T("learn a tool's billing semantics before a large submission",
                  size=19, color=CYAN)
        note3.move_to(DOWN * 2.8)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.2), run_time=2.2)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(note2), run_time=1.32)
        self.play(FadeIn(note3), run_time=1.32)
        self.wait(15)
        self.finish()


class S4_Placement(C2):
    experiment = "X2 \u00b7 RFdiffusion3 probe"

    def construct(self):
        self.header()
        head = T("Placement works", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        row = self.number_row([
            ("72", "complexes\nproduced", CYAN),
            ("72/72", "touch the\n60s loop", GREEN),
            ("58/72", "span the groove\nacross protomers", GREEN),
        ], size_big=50, buff=1.1)
        row.move_to(UP * 0.5)

        note = T("interface median 70 binder atoms \u00b7 helix fraction 0.75", size=19, color=MUTED)
        note.move_to(DOWN * 1.35)
        caveat = T("caveat: 27 designs at clash-level geometry (worst 0.34 \u00c5) \u2014\n"
                   "raw diffusion output needs a clash filter before ranking",
                   size=19, color=AMBER)
        caveat.move_to(DOWN * 2.25)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.2), run_time=2.42)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(caveat), run_time=1.54)
        self.wait(19.6)
        self.finish()


class S5_Fold(C2):
    experiment = "X2 \u00b7 RFdiffusion3 probe"

    def construct(self):
        self.header()
        head = T("The last job \u2014 the decisive co-fold", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        plot = self.dot_plot(
            [("s0", 0.527), ("s1", 0.804), ("s2", 0.378), ("s3", 0.000), ("s4", 0.000)],
            w=7.6, h=3.0, ymax=0.9,
            thresholds=((0.6, CYAN, "bar 0.6"),),
        )
        plot.move_to(LEFT * 2.5 + DOWN * 0.2)

        lines = VGroup(
            T("sample 1: ipSAE 0.804", size=19, color=GREEN),
            T("pDockQ2 0.236 \u2265 0.23", size=19, color=GREEN),
            T("\u2192 passes the full bar", size=19, color=GREEN, weight=BOLD),
            T("one near \u00b7 one partial \u00b7 two lost", size=18, color=MUTED),
            T("X1 best was ipSAE 0.005", size=18, color=MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        lines.move_to(RIGHT * 3.6 + DOWN * 0.25)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(plot), run_time=2.42)
        for ln in lines:
            self.play(FadeIn(ln, shift=RIGHT * 0.15), run_time=0.99)
        self.wait(16.7)
        self.finish()


class S6_Reading(C2):
    experiment = "X2 \u00b7 RFdiffusion3 probe"

    def construct(self):
        self.header()
        head = T("How to read it", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "the generator lever worked \u2014 placement is solved",
            "but this is one design, with one seed set",
            "next: fold 3\u20135 more site-spanning designs",
            "and test reproducibility with a different seed",
        ], size=21, buff=0.4)
        b.move_to(UP * 0.2).to_edge(LEFT, buff=1.0)

        chip = self.chip("seed variance is the caveat", AMBER, size=20)
        chip.move_to(DOWN * 2.4)

        self.play(Write(head), run_time=0.9)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.55)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=0.6)
        self.wait(0.5)
        self.finish()


class S7_Close(C2):
    experiment = "X2 \u00b7 RFdiffusion3 probe"

    def construct(self):
        l1 = T("Placement is solved.", size=42, color=INK, weight=BOLD)
        l2 = T("Reproducibility is not.", size=42, color=AMBER, weight=BOLD)
        g = VGroup(l1, l2).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        g.move_to(ORIGIN).to_edge(LEFT, buff=1.0)
        self.play(Write(l1), run_time=1.1)
        self.play(Write(l2), run_time=1.1)
        self.wait(1.4)
        self.finish()


NARRATION = {
    "S1_Title": (
        "X two: the RFdiffusion3 probe. X one said the site is not the limiter \u2014 so the next "
        "experiment changes the generator, the one lever that needs no new hardware."
    ),
    "S2_Why": (
        "RFdiffusion3 is the all-atom successor of RFdiffusion, at roughly a tenth of the "
        "compute. Before submitting, the schema was read: its built-in designability refold only "
        "handles a single target chain, so for a trimer that option stays off \u2014 candidates are "
        "scored by our own Boltz-2 co-folds instead."
    ),
    "S3_Quota": (
        "Then the quota surprise. RFdiffusion3 bills per diffusion batch: forty-eight designs "
        "became six children \u2014 six jobs. X one had used three; nine of ten were now spent, and "
        "the twin run was rejected outright. One job left. It was reserved for a single decisive "
        "co-fold. The lesson: learn a tool's billing semantics before a large submission."
    ),
    "S4_Placement": (
        "The placement result is decisive. Seventy-two complexes. All seventy-two touch the "
        "sixty-s loop. Fifty-eight span the groove across two protomers \u2014 the antibody site, "
        "occupied exactly as specified. Interface size: median seventy binder atoms. One caveat: "
        "twenty-seven designs show clash-level geometry; raw diffusion output needs a clash "
        "filter before ranking."
    ),
    "S5_Fold": (
        "The last job was the decisive co-fold: one clean design, five samples. One sample "
        "passes the pre-registered bar \u2014 ipSAE zero point eight zero, pDockQ2 zero point two "
        "four. One is near, one partial, two lose the interface entirely. X one's best was zero "
        "point zero zero five. This is the first credibly docked interface in the whole effort \u2014 "
        "with seed variance as the caveat."
    ),
    "S6_Reading": (
        "The generator lever worked. But this is one design, with one seed set. The honest next "
        "step: fold three to five more site-spanning designs, and test reproducibility with a "
        "different seed."
    ),
    "S7_Close": (
        "Placement is solved. Reproducibility is not."
    ),
}
