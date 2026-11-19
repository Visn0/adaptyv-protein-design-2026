"""Video 11 — W2: the shortlist folds on the local GPU.

Eight designs, human and mouse, five samples each — and the mouse result that
ran in the wrong direction.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "W2 \u00b7 shortlist folds"

    def construct(self):
        k = T("VIDEO 11 / 12  \u00b7  CAMPAIGN EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("W2: the shortlist folds", size=52, color=INK, weight=BOLD)
        s = T("Eight designs, human and mouse, five samples each \u2014\non the local GPU.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1)
        self.play(Write(t), run_time=1.75)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.25)
        self.wait(5.6)
        self.finish()


class S2_Setup(C2):
    experiment = "W2 \u00b7 shortlist folds"

    def construct(self):
        self.header()
        head = T("Does the shortlist hold?", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "8 designs \u00b7 5 samples each \u00b7 seed 42 \u00b7 local RTX 5070",
            "the same pre-registered bar, applied to every sample",
            "one detached, resumable runner \u2014 a killed job costs at most one design",
            "memory discipline: one GPU job at a time, every job under a memory limit",
        ], size=20, buff=0.36)
        b.move_to(UP * 0.2).to_edge(LEFT, buff=1.0)

        chip = self.chip("~3.5 min per design (MSA 3 min, 5 samples 30 s)", MUTED, size=18)
        chip.move_to(DOWN * 2.4)

        self.play(Write(head), run_time=1.1)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.67)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=0.73)
        self.wait(5.6)
        self.finish()


class S3_Table(C2):
    experiment = "W2 \u00b7 shortlist folds"

    def construct(self):
        self.header()
        head = T("The shortlist, best sample per design", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        rows = [
            ("rank 1", "groove-3_1_model_1", 0.000, RED),
            ("rank 2", "groove-1_0_model_1", 0.733, GREEN),
            ("rank 3", "groove-2_1_model_0", 0.359, MUTED),
            ("rank 4", "groove-5_0_model_4", 0.000, RED),
            ("rank 5", "groove-0_1_model_1", 0.281, MUTED),
            ("rank 6", "groove-4_1_model_2", 0.449, MUTED),
            ("rank 7", "groove-2_1_model_5", 0.347, MUTED),
            ("rank 8", "groove-5_0_model_5", 0.304, MUTED),
        ]
        g = VGroup()
        for rank, name, val, col in rows:
            r1 = T(rank, size=17, color=DIM)
            r2 = T(name, size=17, color=INK)
            bar = self.hbar(val, 1.0, width=3.0, height=0.16, color=col)
            bar.next_to(r2, RIGHT, buff=0.4).align_to(r2, UP).shift(DOWN * 0.09)
            v = T(f"{val:.3f}", size=17, color=col)
            v.next_to(bar, RIGHT, buff=0.25)
            row = VGroup(r1, r2, bar, v)
            r1.move_to([-6.0, 0, 0]); r2.next_to(r1, RIGHT, buff=0.35)
            g.add(row)
        g.arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to(DOWN * 0.15)

        self.play(Write(head), run_time=1.98)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in g], lag_ratio=0.12),
                  run_time=3.96)
        self.wait(14.8)
        self.finish()


class S4_One(C2):
    experiment = "W2 \u00b7 shortlist folds"

    def construct(self):
        self.header()
        head = T("One design carries the shortlist", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c = self.card(9.6, 2.6, stroke=GREEN)
        l1 = T("rank 2  \u00b7  groove-1_0_model_1  \u00b7  73 aa", size=22, color=INK, weight=BOLD)
        l2 = T("human ipSAE 0.733      mouse ipSAE 0.810", size=22, color=GREEN)
        g = VGroup(l1, l2).arrange(DOWN, buff=0.3).move_to(c)
        grp = VGroup(c, g).move_to(UP * 0.5)

        note = T("six of eight stay under 0.45 \u00b7 two show no interface at all", size=20, color=MUTED)
        note.next_to(grp, DOWN, buff=0.7)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(grp, scale=0.97), run_time=1.98)
        self.play(FadeIn(note), run_time=1.32)
        self.wait(6.6)
        self.finish()


class S5_Mouse(C2):
    experiment = "W2 \u00b7 shortlist folds"

    def construct(self):
        self.header()
        head = T("The mouse fold \u2014 the wrong direction", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "rank 2 folds onto mouse (0.810) better than onto human (0.733)",
            "the design idea is human-specific discrimination",
            "a fold cannot prove selectivity \u2014 a lab assay decides",
            "record it as a risk, not as a pass",
        ], size=21, buff=0.4)
        b.move_to(UP * 0.2).to_edge(LEFT, buff=1.0)

        chip = self.chip("the verdicts say 'insufficient' \u2014 on purpose", MUTED, size=19)
        chip.move_to(DOWN * 2.4)

        self.play(Write(head), run_time=0.9)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.55)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=0.6)
        self.wait(3.6)
        self.finish()


class S6_Method(C2):
    experiment = "W2 \u00b7 shortlist folds"

    def construct(self):
        self.header()
        head = T("Method notes for the next campaign", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "never copy a Boltz output directory while it is being written",
            "copy through a .partial name, then rename \u2014 or the import stalls",
            "retire a run that stopped waiting for input before re-importing it",
            "or the design gets two run folders",
        ], size=21, buff=0.4)
        b.move_to(UP * 0.2).to_edge(LEFT, buff=1.0)

        self.play(Write(head), run_time=0.9)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.55)
            self.wait(2.5)
        self.wait(2.2)
        self.finish()


class S7_Close(C2):
    experiment = "W2 \u00b7 shortlist folds"

    def construct(self):
        l1 = T("A weak fold is not proof of a failed binder.", size=34, color=INK, weight=BOLD)
        l2 = T("A strong fold is not proof of a binder.", size=34, color=INK, weight=BOLD)
        l3 = T("The campaign's real filter is the assay.", size=24, color=CYAN)
        g = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        g.move_to(ORIGIN).to_edge(LEFT, buff=1.0)
        self.play(Write(l1), run_time=1.39)
        self.play(Write(l2), run_time=1.39)
        self.play(FadeIn(l3, shift=UP * 0.15), run_time=1.01)
        self.wait(5.6)
        self.finish()


NARRATION = {
    "S1_Title": (
        "W two: the shortlist folds. Eight designs from the X two run, folded on the local GPU "
        "against both human and mouse TNF alpha."
    ),
    "S2_Setup": (
        "The setup: five samples per design, seed forty-two, on the RTX 5070. The acceptance bar "
        "was the same one, pre-registered. The runner is one detached, resumable script \u2014 a "
        "killed job costs at most one design. And every job runs under a memory limit, with one "
        "GPU job at a time."
    ),
    "S3_Table": (
        "The result: one design carries the shortlist. Rank two \u2014 the seventy-three residue "
        "design from X two \u2014 reaches ipSAE zero point seven three on human, and zero point eight "
        "one on mouse. Six of the eight stay under zero point four five, and two show no "
        "interface at all in any sample."
    ),
    "S4_One": (
        "But no design clears both halves of the bar. The best pDockQ2 with a real interface is "
        "zero point two seven, on a design whose ipSAE is only zero point three six."
    ),
    "S5_Mouse": (
        "And the mouse fold is not the check we wanted: rank two folds onto mouse better than "
        "onto human. The design idea is human-specific discrimination \u2014 this is the wrong "
        "direction. A fold cannot prove selectivity, and a lab assay decides. Record it as a "
        "risk, not as a pass."
    ),
    "S6_Method": (
        "Two method notes for the next campaign: never copy a Boltz output directory while it is "
        "being written \u2014 copy through a partial name, then rename. And retire a run that "
        "stopped waiting for input before re-importing it, or the design gets two run folders."
    ),
    "S7_Close": (
        "The verdicts in the app say 'insufficient' on purpose. A weak fold is not proof of a "
        "failed binder \u2014 and a strong fold is not proof of a binder."
    ),
}
