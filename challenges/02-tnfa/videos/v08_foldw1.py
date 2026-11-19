"""Video 08 — c2-fold-w1-gpu: the fold becomes a first-class run.

Importing a Boltz-2 co-fold, scoring every sample with IPSAE, and applying a
bar that was fixed before the result existed.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "c2-fold-w1-gpu"

    def construct(self):
        k = T("VIDEO 08 / 12  ·  EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("c2-fold-w1-gpu", size=56, color=INK, weight=BOLD)
        s = T("The co-fold as a first-class run \u2014 imported, scored,\nand measured against a bar fixed in advance.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.76)
        self.play(Write(t), run_time=3.08)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=2.2)
        self.wait(5.7)
        self.finish()


class S2_What(C2):
    experiment = "c2-fold-w1-gpu"

    def construct(self):
        self.header()
        head = T("Import the fold, score every sample", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "the fold runs outside the repo: Boltz-2 on the local GPU, or Tamarind",
            "this spec imports the result \u2014 one metric row per sample",
            "ipSAE in both directions, ipSAE_min, pDockQ2, ipTM \u2014 at a 10 \u00c5 PAE cutoff",
            "the acceptance bar is applied to every sample, not chosen after the fact",
        ], size=20, buff=0.36)
        b.move_to(UP * 0.2).to_edge(LEFT, buff=1.0)

        chip = self.chip("ipSAE \u2265 0.6   AND   pDockQ2 \u2265 0.23   \u2014 pre-registered", CYAN, size=18)
        chip.move_to(DOWN * 2.4)

        self.play(Write(head), run_time=1.98)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1.21)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=1.32)
        self.wait(18.3)
        self.finish()


class S3_Pitfall(C2):
    experiment = "c2-fold-w1-gpu"

    def construct(self):
        self.header()
        head = T("One pitfall, stated plainly", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c = self.card(12.0, 2.8, stroke=AMBER)
        t1 = T("IPSAE finds its companion files by renaming the PAE path", size=21, color=INK)
        t2 = T("copy the output under new names \u2192 the pLDDT file is silently lost", size=21, color=AMBER)
        t3 = T("pDockQ2 collapses to a floor value \u2014 while ipSAE stays correct", size=21, color=RED)
        g = VGroup(t1, t2, t3).arrange(DOWN, buff=0.3).move_to(c)
        grp = VGroup(c, g).move_to(UP * 0.2)

        foot = T("a silent wrong number \u2014 so the import keeps the original names",
                 size=20, color=MUTED)
        foot.next_to(grp, DOWN, buff=0.7)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(grp, shift=UP * 0.15), run_time=1.98)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(15.3)
        self.finish()


class S4_Result(C2):
    experiment = "c2-fold-w1-gpu"

    def construct(self):
        self.header()
        head = T("Result \u2014 five samples, one design", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        plot = self.dot_plot(
            [("s0", 0.733), ("s1", 0.454), ("s2", 0.646), ("s3", 0.433), ("s4", 0.025)],
            w=8.4, h=3.0, ymax=0.8,
            thresholds=((0.6, CYAN, "bar 0.6"),),
        )
        plot.move_to(DOWN * 0.25)

        note = T("best sample 0.733 \u00b7 pDockQ2 0.133 \u2014 below the 0.23 half of the bar\n"
                 "the Tamarind reference met the full bar once: 0.804 / 0.236",
                 size=17, color=MUTED)
        note.to_edge(DOWN, buff=0.55)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(plot), run_time=2.64)
        self.play(FadeIn(note), run_time=1.54)
        self.wait(19.5)
        self.finish()


class S5_Reading(C2):
    experiment = "c2-fold-w1-gpu"

    def construct(self):
        self.header()
        head = T("How to read a fold", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "a fold is a distribution over poses \u2014 read the spread, not one sample",
            "the spread shape matches the Tamarind run: one locked, one near, one partial, two lost",
            "a passing sample is evidence about a model \u2014 not about binding in a lab",
        ], size=21, buff=0.42)
        b.move_to(UP * 0.3).to_edge(LEFT, buff=1.0)

        chip = self.chip("qualified pass \u2014 not a binder", AMBER, size=20)
        chip.move_to(DOWN * 2.3)

        self.play(Write(head), run_time=0.9)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.55)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=0.6)
        self.wait(1.5)
        self.finish()


class S6_Close(C2):
    experiment = "c2-fold-w1-gpu"

    def construct(self):
        l1 = T("The local GPU reproduces the Tamarind fold.", size=34, color=INK, weight=BOLD)
        l2 = T("Same shape of spread \u2014 no more SaaS quota.", size=26, color=CYAN)
        g = VGroup(l1, l2).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        g.move_to(ORIGIN).to_edge(LEFT, buff=1.0)
        self.play(Write(l1), run_time=2.4)
        self.play(FadeIn(l2, shift=UP * 0.15), run_time=1.75)
        self.wait(5.6)
        self.finish()


NARRATION = {
    "S1_Title": (
        "Video eight: c2-fold-w1-gpu. The first co-fold treated as a first-class run \u2014 "
        "imported, scored, and measured against a bar that was fixed before the result existed."
    ),
    "S2_What": (
        "The fold itself runs outside this repository: Boltz-2 on the local RTX 5070, or on "
        "Tamarind. This spec imports the result. It copies the model, the PAE matrix, the pLDDT "
        "file and the confidence JSON for every sample \u2014 under their original names \u2014 runs "
        "IPSAE on each sample at a ten angstrom PAE cutoff, and writes one metric row per "
        "sample. The acceptance line is pre-registered: ipSAE at least zero point six, and "
        "pDockQ2 at least zero point two three. It is applied to every sample, not chosen after "
        "the fact."
    ),
    "S3_Pitfall": (
        "One pitfall is worth stating: IPSAE finds its companion files by renaming the PAE "
        "path. Copy the output under new names, and the pLDDT file is silently lost \u2014 pDockQ2 "
        "collapses to a floor value while ipSAE stays correct. A silent wrong number. So the "
        "import keeps the original names."
    ),
    "S4_Result": (
        "The result, on the design that passed on Tamarind: five samples, ipSAE from zero point "
        "zero three up to zero point seven three. Two samples clear the ipSAE line of zero point "
        "six; none meets the full bar, because pDockQ2 stays at zero point one three on the best "
        "sample. The Tamarind reference met the full bar once. This is a qualified pass \u2014 not a "
        "binder."
    ),
    "S5_Reading": (
        "How to read it: a fold is a distribution over poses. Read the spread, not a single "
        "sample. And remember: a passing sample is evidence about a model \u2014 not about binding "
        "in a lab."
    ),
    "S6_Close": (
        "What it proves: the local GPU reproduces the Tamarind fold, with the same shape of "
        "spread. From here, the campaign no longer depends on a SaaS quota."
    ),
}
