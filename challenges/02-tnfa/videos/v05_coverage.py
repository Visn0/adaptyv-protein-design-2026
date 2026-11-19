"""Video 05 — c2-coverage-scan: the cheap reachability filter.

Which generated backbones can physically reach two switch sites, decided
before any sequence design runs.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "c2-coverage-scan"

    def construct(self):
        k = T("VIDEO 05 / 12  \u00b7  EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("c2-coverage-scan", size=56, color=INK, weight=BOLD)
        s = T("The cheap filter that protects the expensive step \u2014\nswitch reachability, before sequence design.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=0.8)
        self.play(Write(t), run_time=1.4)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.0)
        self.wait(5.8)
        self.finish()


class S2_Why(C2):
    experiment = "c2-coverage-scan"

    def construct(self):
        self.header()
        head = T("A shape that cannot reach cannot switch", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c = self.card(12.0, 1.6, stroke=CYAN)
        t1 = T("a backbone that cannot reach two switch sites", size=22, color=INK)
        t2 = T("cannot pass the top-weighted objective \u2014 whatever its sequence", size=22, color=CYAN)
        g = VGroup(t1, t2).arrange(DOWN, buff=0.2).move_to(c)
        grp = VGroup(c, g).move_to(UP * 0.8)

        b = self.bullets([
            "so discard those shapes before ProteinMPNN and AlphaFold2 run on them",
            "this filter is the main compute saving of the campaign",
        ], size=21, buff=0.4)
        b.next_to(grp, DOWN, buff=0.9)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(grp, shift=UP * 0.15), run_time=1.98)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1.21)
            self.wait(2.5)
        self.wait(5.8)
        self.finish()


class S3_Steps(C2):
    experiment = "c2-coverage-scan"

    def construct(self):
        self.header()
        head = T("The filter, step by step", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        strip, boxes = self.step_strip(
            ["read\nmotif", "superpose", "side-chain\npoints", "3.5\u20138.5 \u00c5\nwindow",
             "assign\n1:1", "\u2265 2 sites\n\u2192 bias"],
            size=15,
        )
        strip.move_to(UP * 1.3)

        b = self.bullets([
            "transform the motif into the backbone frame (RFD3 recenters and renumbers)",
            "superposition RMSD above 1.0 \u00c5 raises a warning",
            "poly-glycine backbones have no CB: build a virtual one from N, CA, C",
            "one-to-one assignment: one residue cannot cover two distant sites",
        ], size=19, buff=0.32)
        b.next_to(strip, DOWN, buff=0.9).to_edge(LEFT, buff=1.0)

        self.play(Write(head), run_time=1.98)
        self.play(LaggedStart(*[FadeIn(x) for x in boxes], lag_ratio=0.16), run_time=3.3)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1.1)
            self.wait(2.5)
        self.wait(17.4)
        self.finish()


class S4_Result(C2):
    experiment = "c2-coverage-scan"

    def construct(self):
        self.header()
        head = T("Result \u2014 the reference run", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        row = self.number_row([
            ("32", "backbones\nscanned", MUTED),
            ("12", "pass the\n2-site filter", GREEN),
            ("3.0", "logit bias on\ncovered positions", CYAN),
        ], size_big=54, buff=1.2)
        row.move_to(UP * 0.4)

        note = T("upstream replay: 12 of 32 \u00b7 the filter throws away shapes,\nnot sequences \u2014 nothing has been designed yet",
                 size=20, color=MUTED)
        note.move_to(DOWN * 1.9)

        self.play(Write(head), run_time=1.18)
        self.play(FadeIn(row, shift=UP * 0.2), run_time=1.31)
        self.play(FadeIn(note, shift=UP * 0.12), run_time=1.05)
        self.wait(7)
        self.finish()


class S5_Output(C2):
    experiment = "c2-coverage-scan"

    def construct(self):
        self.header()
        head = T("What the stage hands over", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        chips = VGroup(
            self.chip("switch_positions_report.csv", CYAN, size=20),
            self.chip("ProteinMPNN bias file \u00b7 logit 3.0", CYAN, size=20),
        ).arrange(RIGHT, buff=0.6).move_to(UP * 0.5)

        note = T("the bias tells the sequence designer: prefer histidine at the covered positions",
                 size=20, color=MUTED)
        note.move_to(DOWN * 0.7)
        note2 = T("the stage waits for generator output \u2014 the hand-off to the external step",
                  size=20, color=VIOLET)
        note2.move_to(DOWN * 1.6)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(chips, shift=UP * 0.15), run_time=1.98)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(note2), run_time=1.32)
        self.wait(8.1)
        self.finish()


class S6_Close(C2):
    experiment = "c2-coverage-scan"

    def construct(self):
        l1 = T("Check reachability first.", size=44, color=INK, weight=BOLD)
        l2 = T("Spend the sequence design only on shapes that can switch.",
              size=26, color=CYAN)
        g = VGroup(l1, l2).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN).to_edge(LEFT, buff=1.0)
        self.play(Write(l1), run_time=1.1)
        self.play(FadeIn(l2, shift=UP * 0.15), run_time=0.9)
        self.wait(3.6)
        self.finish()


NARRATION = {
    "S1_Title": (
        "Experiment five: c2-coverage-scan. A cheap geometry filter that protects the most "
        "expensive step in the pipeline."
    ),
    "S2_Why": (
        "The logic is blunt: a backbone that cannot reach two switch sites cannot pass the "
        "top-weighted objective, whatever its sequence. So those shapes are discarded before "
        "ProteinMPNN and AlphaFold2 ever run on them. This filter is the main compute saving of "
        "the campaign."
    ),
    "S3_Steps": (
        "The filter works in steps. Read the motif. Superpose the backbone's target chains onto "
        "the reference, because RFdiffusion recenters its output and renumbers chains \u2014 the "
        "motif must be transformed into the backbone's frame. For every binder residue, compute "
        "a side-chain point: the CB position, or a virtual CB for poly-glycine backbones. "
        "Measure the distance to each cation tip inside a three point five to eight point five "
        "angstrom window. Keep the best position per site, and enforce a one-to-one assignment: "
        "one residue cannot cover two sites that lie far apart."
    ),
    "S4_Result": (
        "In the reference run, twelve of thirty-two backbones pass the two-site filter. The "
        "filter throws away shapes, not sequences \u2014 nothing has been designed yet."
    ),
    "S5_Output": (
        "The stage writes the positions report and a ProteinMPNN bias file: prefer histidine at "
        "the covered positions, with a logit bias of three. The stage is the hand-off point to "
        "the external generator, and waits until its output arrives."
    ),
    "S6_Close": (
        "Check reachability first. Spend the sequence design only on shapes that can switch."
    ),
}
