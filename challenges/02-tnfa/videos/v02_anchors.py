"""Video 02 — c2-anchors: finding the switch anchors on the target.

The scan for titratable groups that can carry the switch, the chemistry-class
conservation rule, and the A73 trap (His in human, Tyr in mouse).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "c2-anchors"

    def construct(self):
        k = T("VIDEO 02 / 12  ·  EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("c2-anchors", size=56, color=INK, weight=BOLD)
        s = T("Finding the switch anchors on the target \u2014\nand proving they survive in the mouse protein.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.19)
        self.play(Write(t), run_time=2.09)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.49)
        self.wait(5.6)
        self.finish()


class S2_Why(C2):
    experiment = "c2-anchors"

    def construct(self):
        self.header()
        head = T("Every anchor must survive in mouse", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "the switch is anchored on the target, so the scan comes first",
            "objective 2 is mouse cross-reactivity",
            "an anchor that dies in mouse fails silently",
            "so conservation is scored by chemistry class, never by residue letter",
        ], size=20, buff=0.36)
        b.move_to(UP * 0.3).to_edge(LEFT, buff=1.0)

        ex = self.card(9.2, 1.35, stroke=GREEN)
        l1 = T("human GLU   \u2194   mouse ASP", size=22, color=INK)
        l2 = T("both carboxylates \u00b7 the switch chemistry survives", size=17, color=GREEN)
        g = VGroup(l1, l2).arrange(DOWN, buff=0.14).move_to(ex)
        ex_grp = VGroup(ex, g)
        ex_grp.next_to(b, DOWN, buff=1.0).to_edge(LEFT, buff=1.0)

        self.play(Write(head), run_time=0.9)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.55)
            self.wait(2.5)
        self.play(FadeIn(ex_grp, shift=UP * 0.15), run_time=0.8)
        self.wait(5.1)
        self.finish()


class S3_Steps(C2):
    experiment = "c2-anchors"

    def construct(self):
        self.header()
        head = T("The scan, step by step", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        strip, boxes = self.step_strip(
            ["load\n1TNF", "rSASA", "exposed\ninterface", "distance\nto groove",
             "align\nhuman/mouse", "rank\nanchors"],
            size=15,
        )
        strip.move_to(UP * 1.3)

        b = self.bullets([
            "relative solvent accessibility (Shrake\u2013Rupley) on the full assembly",
            "keep protomer-interface residues that stay exposed \u2014 the buried core is unreachable",
            "distance to the nearest exposed boundary residue \u2014 not a centroid",
            "the exposed boundary wraps around the protomer junction; it is not one compact spot",
        ], size=19, buff=0.32)
        b.next_to(strip, DOWN, buff=0.9).to_edge(LEFT, buff=1.0)

        self.play(Write(head), run_time=1.92)
        self.play(LaggedStart(*[FadeIn(x) for x in boxes], lag_ratio=0.16), run_time=3.2)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1.07)
            self.wait(2.5)
        self.wait(5.6)
        self.finish()


class S4_Trap(C2):
    experiment = "c2-anchors"

    def construct(self):
        self.header()
        head = T("The trap: position A73", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c = self.card(8.6, 3.1, stroke=RED)
        a73 = T("A73", size=54, color=INK, weight=BOLD)
        conv = T("human:  HIS          mouse:  TYR", size=24, color=MUTED)
        ch = self.chip("SWITCH LOST", RED, size=22)
        inner = VGroup(a73, conv, ch).arrange(DOWN, buff=0.35).move_to(c)
        grp = VGroup(c, inner).move_to(UP * 0.4)

        note = T("a design built around the target's own histidine would look\n"
                 "correct \u2014 and fail the mouse objective silently", size=20, color=MUTED)
        note.next_to(grp, DOWN, buff=0.6)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(grp, scale=0.95), run_time=2.2)
        self.play(FadeIn(ch, scale=1.1), run_time=1.1)
        self.play(FadeIn(note, shift=UP * 0.12), run_time=1.76)
        self.wait(12.7)
        self.finish()


class S5_Result(C2):
    experiment = "c2-anchors"

    def construct(self):
        self.header()
        head = T("Result \u2014 the usable anchors", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        row = self.number_row([
            ("14", "candidates near\nthe groove", CYAN),
            ("12", "chemistry-class\nconserved", GREEN),
            ("7", "within 6 \u00c5 of\nthe groove", AMBER),
        ], size_big=56, buff=1.1)
        row.move_to(UP * 0.35)

        chem = self.card(10.6, 1.5, stroke=GREEN)
        l1 = T("scored by letter, usable anchors:  0", size=20, color=MUTED)
        l2 = T("scored by chemistry class:  7", size=22, color=GREEN, weight=BOLD)
        g = VGroup(l1, l2).arrange(DOWN, buff=0.16).move_to(chem)
        cg = VGroup(chem, g)
        cg.next_to(row, DOWN, buff=0.9)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.2), run_time=2.42)
        self.wait(0.1)
        self.play(FadeIn(cg, shift=UP * 0.15), run_time=1.76)
        self.wait(16.4)
        self.finish()


class S6_Output(C2):
    experiment = "c2-anchors"

    def construct(self):
        self.header()
        head = T("What the stage hands over", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c1 = self.chip("anchors.csv", CYAN, size=20)
        c2 = self.chip("hotspot candidates for the motif step", CYAN, size=20)
        chips = VGroup(c1, c2).arrange(DOWN, buff=0.35).move_to(UP * 0.55)

        line = T("Takeaway: score conservation by chemistry class, not by letter.",
                 size=24, color=INK)
        line2 = T("Letter identity throws away usable anchors \u2014 and hides traps like A73.",
                  size=22, color=MUTED)
        foot = VGroup(line, line2).arrange(DOWN, buff=0.3).move_to(DOWN * 1.3)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(chips, shift=UP * 0.15), run_time=1.76)
        self.play(FadeIn(foot, shift=UP * 0.12), run_time=1.98)
        self.wait(9.3)
        self.finish()


NARRATION = {
    "S1_Title": (
        "Experiment two of the pipeline: c2-anchors. The switch is anchored on the target, "
        "so the first job is to find which groups on the TNF alpha surface can carry it."
    ),
    "S2_Why": (
        "The scan looks for titratable groups on the exposed surface around the recommended "
        "groove. One filter decides the outcome: mouse cross-reactivity is the second-ranked "
        "objective, so every candidate must keep its switch chemistry after the human-to-mouse "
        "substitution. Chemistry class decides, not residue letter."
    ),
    "S3_Steps": (
        "Six steps. Load the 1TNF trimer. Compute the relative solvent accessibility of every "
        "residue, on the full assembly. Keep the protomer-interface residues that stay exposed. "
        "Measure the distance to the nearest exposed boundary residue, not to a centroid \u2014 the "
        "boundary wraps around the protomer junction. Align the human and mouse sequences, and "
        "map conservation onto the structure."
    ),
    "S4_Trap": (
        "One position is a trap. Residue A73 is a histidine in human, and a tyrosine in mouse. "
        "The switch chemistry does not survive. A design that built its switch around the "
        "target's own histidine would look correct, and fail the mouse objective silently. The "
        "scan flags it: switch lost."
    ),
    "S5_Result": (
        "The result: fourteen candidates near the groove, twelve conserved by chemistry class, "
        "seven within six angstroms of the groove. The scoring rule matters. By letter, every "
        "usable anchor is non-conserved, because several positions are human glutamate and mouse "
        "aspartate \u2014 both carboxylates. Chemistry class took the usable count from zero to seven."
    ),
    "S6_Output": (
        "The stage writes anchors.csv and the hotspot candidates for the next step. The "
        "takeaway: score conservation by chemistry class, not by letter. Letter identity throws "
        "away usable anchors \u2014 and hides traps like A73."
    ),
}
