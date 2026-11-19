"""Video 07 — c2-baseline-results: the upstream campaign in our frame.

The study repo's own C2 run: 48 sequences, zero docks, and the sample-size
lesson that shaped everything after.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "c2-baseline-results"

    def construct(self):
        k = T("VIDEO 07 / 12  ·  REFERENCE EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("c2-baseline-results", size=56, color=INK, weight=BOLD)
        s = T("The study repo's own campaign, presented in our frame \u2014\nthe comparison base.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.49)
        self.play(Write(t), run_time=2.61)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.87)
        self.wait(5.4)
        self.finish()


class S2_What(C2):
    experiment = "c2-baseline-results"

    def construct(self):
        self.header()
        head = T("A reference, kept runnable", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "read the upstream coverage report: 32 scanned backbones and the bias file",
            "build the distribution of switch sites per backbone",
            "put the labelled target structure in the viewer \u2014 no designed complex exists",
            "every new run gets compared against these numbers",
        ], size=21, buff=0.38)
        b.move_to(UP * 0.2).to_edge(LEFT, buff=1.0)

        chip = self.chip("reference experiments stay runnable \u2014 they are the ruler", MUTED, size=18)
        chip.move_to(DOWN * 2.3)

        self.play(Write(head), run_time=0.9)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.55)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=0.6)
        self.wait(4.3)
        self.finish()


class S3_Funnel(C2):
    experiment = "c2-baseline-results"

    def construct(self):
        self.header()
        head = T("The upstream funnel", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        steps = [
            ("36", "backbones\nbuilt", MUTED),
            ("32", "scanned", MUTED),
            ("12", "pass coverage\nfilter", CYAN),
            ("48", "sequences\ndesigned", CYAN),
            ("0", "docked", RED),
            ("20", "submitted with\ncontrols", AMBER),
        ]
        row = self.number_row(steps, size_big=40, size_lab=15, buff=0.55)
        row.move_to(UP * 0.35)

        note = T("twelve backbones \u00d7 four sequences = 48 \u00b7 best ipTM 0.161",
                 size=20, color=MUTED)
        note.move_to(DOWN * 1.9)
        note2 = T("at a 2 % pass rate, the expected number of successes from 48 is about one",
                  size=20, color=MUTED)
        note2.move_to(DOWN * 2.6)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.2), run_time=2.64)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(note2), run_time=1.32)
        self.wait(18.7)
        self.finish()


class S4_Metrics(C2):
    experiment = "c2-baseline-results"

    def construct(self):
        self.header()
        head = T("They fold. They do not dock.", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c = self.card(11.4, 3.2, stroke=RED)
        l1 = T("binder folds alone:      pTM 0.74\u20130.89", size=20, color=GREEN)
        l2 = T("interface confidence:    ipTM 0.130 median \u00b7 0.161 best", size=20, color=RED)
        l3 = T("interface PAE:           27.9 \u00c5 median \u00b7 target below 10 \u00c5", size=20, color=RED)
        l4 = T("atom contacts under 5 \u00c5:   0\u201312   (a real interface: 100\u2013300)", size=20, color=RED)
        g = VGroup(l1, l2, l3, l4).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(c)
        grp = VGroup(c, g).move_to(UP * 0.2)

        foot = T("the single most honest sentence in the campaign", size=20, color=MUTED)
        foot.next_to(grp, DOWN, buff=0.7)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(grp, shift=UP * 0.15), run_time=2.2)
        for ln in g:
            self.play(Indicate(ln, color=INK, scale_factor=1.0), run_time=0.88)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(13.7)
        self.finish()


class S5_Submission(C2):
    experiment = "c2-baseline-results"

    def construct(self):
        self.header()
        head = T("20 designs \u2014 and why the controls matter", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c1 = self.chip("16 switch variants", AMBER, size=20)
        c2 = self.chip("4 paired controls", MUTED, size=20)
        chips = VGroup(c1, c2).arrange(RIGHT, buff=0.6).move_to(UP * 0.7)

        note = T("the controls are the same sequences without the histidine substitutions",
                 size=21, color=INK)
        note.move_to(DOWN * 0.3)
        note2 = T("without them, a positive result cannot separate\n\"the design binds\" from \"the histidines did something\"",
                  size=21, color=MUTED)
        note2.move_to(DOWN * 1.6)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(chips, shift=UP * 0.15), run_time=1.76)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(note2, shift=UP * 0.1), run_time=1.54)
        self.wait(8)
        self.finish()


class S6_Close(C2):
    experiment = "c2-baseline-results"

    def construct(self):
        l1 = T("The failure was the sample size,", size=40, color=INK, weight=BOLD)
        l2 = T("not the mechanism.", size=40, color=RED, weight=BOLD)
        l3 = T("48 sequences against a field that screens tens of thousands.", size=22, color=MUTED)
        l4 = T("Everything after this baseline was sized around that lesson.", size=22, color=CYAN)
        g = VGroup(l1, l2, l3, l4).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        g.move_to(ORIGIN).to_edge(LEFT, buff=1.0)

        self.play(Write(l1), run_time=1.6)
        self.play(Write(l2), run_time=1.6)
        self.play(FadeIn(l3, shift=UP * 0.12), run_time=1.12)
        self.play(FadeIn(l4, shift=UP * 0.12), run_time=1.12)
        self.wait(5.8)
        self.finish()


NARRATION = {
    "S1_Title": (
        "Video seven: c2-baseline-results. The study repository's own challenge two campaign, "
        "presented in the same frame as our runs \u2014 the comparison base."
    ),
    "S2_What": (
        "The experiment reads the upstream coverage report, rebuilds the distribution of switch "
        "sites per backbone, and puts the labelled target structure in the viewer \u2014 because no "
        "designed complex exists to show. It is a reference experiment: it stays runnable, and "
        "every future run is measured against it."
    ),
    "S3_Funnel": (
        "The upstream funnel: thirty-six backbones built, thirty-two scanned, twelve passing the "
        "coverage filter. Twelve backbones times four sequences each: forty-eight sequences "
        "designed. Zero docked. Twenty designs were still submitted, with paired controls. At a "
        "two percent pass rate, the expected number of successes from forty-eight sequences is "
        "about one \u2014 and zero is the single most likely outcome."
    ),
    "S4_Metrics": (
        "The numbers behind that verdict: the binders fold well on their own. But the interface "
        "confidence is 0.13 to 0.16, the interface PAE sits near 28 angstroms against a target "
        "below 10, and the models show zero to twelve atom contacts where a real interface has "
        "hundreds. The binders fold. They do not dock."
    ),
    "S5_Submission": (
        "The submission carried sixteen switch variants and four paired controls \u2014 the same "
        "sequences without the histidine substitutions. Without the controls, a positive result "
        "could not separate 'the design binds' from 'the histidines did something'."
    ),
    "S6_Close": (
        "The failure was the sample size, not the mechanism. Forty-eight sequences against a "
        "field that screens tens of thousands. Everything after this baseline was sized around "
        "that lesson."
    ),
}
