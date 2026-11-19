"""Video 1 — the challenge 3 submission: GLP-1R agonist.

The brief, the target, the activation-geometry gate, the seven method
families, the design reel (S6_Reel — a prebuilt segment: one slow continuous
turn with the designs swapping) and the ranked first rows. Plus the honest
limits.

Numbers come from challenges/03-glp1r/submission/ (methodology.md,
competition-submission-2026-10-21.csv, selection/selection-top20.csv) and
notes/submission-selection-2026-10-21.md.

Media segments (built by `scripts/build_reel.py --slow-reel` /
`--target-only`, assembled by `build.py segments 1`): S3_Target, S6_Reel.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C3):
    experiment = "the submission"
    WAIT = 9.3

    def construct(self):
        k = T("VIDEO 1  \u00b7  THE SUBMISSION", size=20, color=CYAN, weight=BOLD)
        t = T("GLP-1R agonist", size=58, color=INK, weight=BOLD)
        s = T("Twenty designs, seven method families, one ranked file \u2014\n"
              "ranked by activation evidence, not by score alone.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        rule = Line([-5.2, 0, 0], [5.2, 0, 0], color=BORDER, stroke_width=2)
        rule.next_to(g, DOWN, buff=0.85)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.0)
        self.play(Write(t), run_time=1.8)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.3)
        self.play(Create(rule), run_time=0.9)
        self.wait(self.WAIT)
        self.finish()


class S2_Challenge(C3):
    experiment = "the submission"
    WAIT = 16.2

    def construct(self):
        self.header()
        head = T("A functional objective", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        path_lb = T("the path GLP-1 takes", size=17, color=MUTED)
        row, boxes = self.step_strip(
            ["peptide groove\n(ECD)", "ECD\u2013TMD\njunction", "transmembrane\nbundle"],
            size=16, active=1)
        row.move_to(UP * 0.85)
        path_lb.next_to(row, UP, buff=0.3)

        anti = VGroup(
            self.chip("groove only", color=RED, size=17),
            T("caps the groove \u2014 antagonist", size=19, color=RED),
        ).arrange(DOWN, buff=0.32)
        anti.move_to([-3.4, -1.25, 0])
        ago = VGroup(
            self.chip("groove + junction + TM", color=GREEN, size=17),
            T("spans the path \u2014 agonist", size=19, color=GREEN),
        ).arrange(DOWN, buff=0.32)
        ago.move_to([2.9, -1.25, 0])

        foot = T("only a confirmed agonist counts", size=19, color=CYAN)
        foot.move_to([0, -2.45, 0])

        self.play(Write(head), run_time=1.6)
        self.play(FadeIn(path_lb), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(x) for x in boxes], lag_ratio=0.2), run_time=1.8)
        self.play(FadeIn(anti, shift=UP * 0.15), run_time=1.3)
        self.play(FadeIn(ago, shift=UP * 0.15), run_time=1.3)
        self.play(FadeIn(foot), run_time=1.0)
        self.wait(self.WAIT)
        self.finish()


class S4_Method(C3):
    experiment = "the submission"
    WAIT = 30.8

    def construct(self):
        self.header()
        head = T("The method: an activation-geometry gate", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        left_lb = T("six contacts + insertion depth", size=17, color=MUTED)
        left_lb.move_to([-3.6, 1.7, 0])
        chips = VGroup(*[
            self.chip(txt, color=CYAN, size=16)
            for txt in ["anion \u2192 R190", "aromatic \u2192 Y148",
                        "small \u2192 W306", "H-bond \u2192 Q234",
                        "hydrophobe \u2192 E387", "ECL3 contact"]
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        chips.next_to(left_lb, DOWN, buff=0.32).align_to(left_lb, LEFT)
        depth = T("depth below the vestibule rim", size=17, color=AMBER)
        depth.next_to(chips, DOWN, buff=0.45).align_to(chips, LEFT)

        right_lb = T("calibrated on real structures first", size=17, color=MUTED)
        right_lb.move_to([2.9, 1.7, 0])
        rows = VGroup()
        for name, score, depthv, color in [
            ("6X18  GLP-1", 6, "20.6 \u00c5", GREEN),
            ("6B3J  exendin-P5", 4, "23.6 \u00c5", AMBER),
            ("7LLL  exendin-4", 4, "18.9 \u00c5", AMBER),
            ("9IVG  GLP-1(9-36)", 1, "14.2 \u00c5", RED),
        ]:
            lab = T(name, size=18, color=INK)
            bar = self.hbar(score, max_value=6, width=1.5, color=color)
            num = T(f"{score}/6", size=18, color=color, weight=BOLD)
            dep = T(depthv, size=17, color=MUTED)
            rows.add(VGroup(lab, bar, num, dep).arrange(RIGHT, buff=0.24))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        rows.next_to(right_lb, DOWN, buff=0.32).align_to(right_lb, LEFT)

        foot = T("cutoffs fixed in the published tool \u00b7 every fold sample scored",
                 size=19, color=CYAN)
        foot.move_to([0, -2.45, 0])

        self.play(Write(head), run_time=1.6)
        self.play(FadeIn(left_lb), FadeIn(right_lb), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(c, scale=0.8) for c in chips],
                              lag_ratio=0.22), run_time=3.2)
        self.play(FadeIn(depth), run_time=0.8)
        for row in rows:
            self.play(FadeIn(row[0]), GrowFromEdge(row[1], LEFT),
                      FadeIn(row[2]), FadeIn(row[3]), run_time=0.9)
        self.play(FadeIn(foot), run_time=1.0)
        self.wait(self.WAIT)
        self.finish()


class S5_Families(C3):
    experiment = "the submission"
    WAIT = 23.8

    def construct(self):
        self.header()
        head = T("Seven method families", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        rows = VGroup()
        data = [
            ("rfd3-miniprotein", 5, CYAN), ("solublemnn-c3", 5, VIOLET),
            ("solublemnn-resequenced", 4, VIOLET), ("boltzgen-junction", 2, BLUE),
            ("boltzgen-peptide", 2, BLUE), ("evobind-peptide", 1, GREEN),
            ("bindcraft2-peptide", 1, GREEN),
        ]
        for name, count, color in data:
            lab = T(name, size=21, color=INK)
            bar = self.hbar(count, max_value=5, width=3.2, color=color)
            num = T(str(count), size=21, color=color, weight=BOLD)
            rows.add(VGroup(lab, bar, num).arrange(RIGHT, buff=0.3))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        rows.move_to([-0.6, -0.2, 0])
        foot = T("every backbone re-folded \u00b7 5 samples each \u00b7 every sample scored",
                 size=19, color=CYAN)
        foot.next_to(rows, DOWN, buff=0.55)
        self.play(Write(head), run_time=1.6)
        for row in rows:
            self.play(FadeIn(row[0]), GrowFromEdge(row[1], LEFT),
                      FadeIn(row[2]), run_time=0.55)
        self.play(FadeIn(foot), run_time=1.1)
        self.wait(self.WAIT)
        self.finish()


class S7_Top(C3):
    experiment = "the submission"
    WAIT = 27.7

    def construct(self):
        self.header()
        head = T("The first three rows", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        rows = VGroup()
        data = [
            ("c2-run1-b206", "6/6 @ 20.6 \u00c5", "GLP-1's depth", "0.87", CYAN, 6),
            ("e1-r0025", "5/6 @ 20.1 \u00c5", "best interface", "0.93", GREEN, 5),
            ("c8-run13", "6/6 @ 17.6 \u00c5", "two-domain", "0.85", AMBER, 6),
        ]
        for name, gate, note, ipsae, color, score in data:
            box = self.card(11.2, 1.0, stroke=BORDER)
            n = T(name, size=23, color=INK, weight=BOLD)
            n.move_to(box.get_left() + RIGHT * 2.0)
            g = T(gate, size=21, color=color)
            g.move_to(box.get_left() + RIGHT * 4.9)
            bar = self.hbar(score, max_value=6, width=1.1, color=color)
            bar.move_to(box.get_left() + RIGHT * 7.1)
            no = T(note, size=18, color=MUTED)
            no.move_to(box.get_left() + RIGHT * 9.1)
            i = T(ipsae, size=18, color=INK)
            i.move_to(box.get_left() + RIGHT * 10.85)
            rows.add(VGroup(box, n, g, bar, no, i))
        rows.arrange(DOWN, buff=0.32)
        rows.move_to([0, -0.05, 0])
        col_lb = T("gate  \u00b7  activation pharmacophore  \u00b7  ipSAE", size=16, color=DIM)
        col_lb.next_to(rows, UP, buff=0.3)
        foot = T("three screens each: pLDDT \u00b7 ipSAE \u00b7 hydropathy  \u2014  prescreen: zero flags",
                 size=19, color=CYAN)
        foot.next_to(rows, DOWN, buff=0.65)
        self.play(Write(head), run_time=1.6)
        self.play(FadeIn(col_lb), run_time=0.7)
        for row in rows:
            self.play(FadeIn(row[0]), FadeIn(row[1]), GrowFromEdge(row[3], LEFT),
                      FadeIn(row[4]), FadeIn(row[5]), run_time=1.1)
        self.play(FadeIn(foot), run_time=1.2)
        self.wait(self.WAIT)
        self.finish()


class S8_Limits(C3):
    experiment = "the submission"
    WAIT = 12.5

    def construct(self):
        self.header()
        head = T("Honest limits", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        b = self.bullets([
            "activation cannot be predicted from a co-fold",
            "the gate scores the pose it is given \u2014 not whether the design adopts it",
            "pose agreement across samples: mitigation, not proof",
            "binding affinities are for the assay to determine",
        ], size=23, dot_color=AMBER)
        b.move_to([0, 0.1, 0])
        self.play(Write(head), run_time=1.6)
        self.play(LaggedStart(*[FadeIn(x, shift=UP * 0.15) for x in b],
                              lag_ratio=0.22), run_time=2.6)
        self.wait(self.WAIT)
        self.finish()


class S9_Close(C3):
    experiment = "the submission"
    WAIT = 6.9

    def construct(self):
        self.header()
        head = T("The submission", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        nums = self.number_row([("20", "designs"), ("7", "method families"),
                                ("0", "prescreen flags")])
        nums.move_to(UP * 0.6)
        foot = T("ranked activation-first \u00b7 the full method in the methodology text",
                 size=20, color=MUTED)
        foot.next_to(nums, DOWN, buff=1.0)
        foot2 = T("the assay decides", size=26, color=CYAN, weight=BOLD)
        foot2.next_to(foot, DOWN, buff=0.8)
        self.play(Write(head), run_time=1.4)
        self.play(FadeIn(nums, shift=UP * 0.2), run_time=1.8)
        self.play(FadeIn(foot), run_time=1.0)
        self.play(FadeIn(foot2, shift=UP * 0.15), run_time=1.0)
        self.wait(self.WAIT)
        self.finish()


NARRATION = {
    "S1_Title": (
        "This is the submission for challenge three: a GLP-1 receptor agonist. "
        "Twenty de-novo designs, seven method families, one ranked file \u2014 and one "
        "method that ranks them: an activation-geometry gate."
    ),
    "S2_Challenge": (
        "The brief asks for an agonist, not a binder. Confirmed binders go into a "
        "receptor-activation assay, and only a confirmed agonist counts. GLP-1 itself "
        "runs from the peptide groove of the extracellular domain, along the junction "
        "toward the transmembrane bundle. A design that only caps the groove is the "
        "classic antagonist \u2014 so the designs must span the path."
    ),
    "S3_Target": (
        "The target: human GLP-1R, the challenge segment 24 to 432, scored against the "
        "active-state reference structure 6X18. The amber residues are the message "
        "region of GLP-1 \u2014 arginine 190, tyrosine 148, tryptophan 306, glutamine 234, "
        "and glutamate 387, plus the third extracellular loop. A design has to engage "
        "them, at the depth GLP-1 itself reaches."
    ),
    "S4_Method": (
        "We score activation geometry explicitly. Six contacts \u2014 an anion to R190, an "
        "aromatic at Y148, a small group at W306, a hydrogen bond to Q234, a hydrophobe "
        "at E387, and ECL3 \u2014 plus how deep the ligand inserts below the vestibule rim. "
        "The cutoffs are fixed in the published tool, so before trusting it we "
        "reproduced its calibration on four experimental structures. GLP-1 scores six "
        "of six at twenty-one \u00e5ngstr\u00f6ms. Exendin-P5, four of six. Exendin-4, four of "
        "six. And the weak partial agonist, one of six."
    ),
    "S5_Families": (
        "The designs come from seven independent method families. RFdiffusion3 "
        "mini-proteins targeted at the groove and the junction. BoltzGen cyclic "
        "peptides at the junction, and two shorter peptides. EvoBind, from sequence "
        "alone. One BindCraft2 peptide. And two SolubleMPNN families that re-sequenced "
        "the strongest backbones with the interface pinned. Every backbone was "
        "re-folded against the full receptor \u2014 five samples each \u2014 and every sample "
        "was scored."
    ),
    "S6_Reel": (
        "Here they are, one by one: the whole submission in ranked order. Each design "
        "is shown in its predicted pose on the receptor \u2014 the binder in pink, the "
        "interface residues in amber. Watch the groove and the junction: the strongest "
        "designs reach both. The first rows carry the full six-of-six pharmacophore at "
        "depth; then the strongest five-of-six binders. Twenty designs, seven method "
        "families, all sequences unique, no near-duplicates."
    ),
    "S7_Top": (
        "The first three rows carry the rubric. The EvoBind peptide c2-run1-b206 hits "
        "all six contacts at GLP-1's own depth. The RFdiffusion3 mini-protein e1-r0025 "
        "has the strongest interface in the set. And the BoltzGen peptide c8-run13 "
        "combines six of six with a two-domain hit. Every design carries three recorded "
        "screens \u2014 fold confidence, interface score, and hydropathy \u2014 and the "
        "organisers' own prescreen found no known binder among them."
    ),
    "S8_Limits": (
        "One honest limit. Activation cannot be predicted from a co-fold: the gate "
        "scores the pose it is given, not whether the design adopts it. Pose agreement "
        "across the five samples is the mitigation \u2014 not a proof. And the binding "
        "affinities are for the assay to decide."
    ),
    "S9_Close": (
        "That is the submission: twenty designs, seven method families, ranked by "
        "activation evidence first, prescreen clean, with the full method in the "
        "methodology text. The assay decides."
    ),
}
