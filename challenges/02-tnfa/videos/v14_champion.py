"""Video 14 — the final campaign: the champion.

From Genie 3 backbones to the E33H pH switch: the method, the steps and the
tools behind the submission set — plus two prebuilt MD binding clips
(S7_MD_d7, S8_MD_d12; built by `build.py segments 14`).

Numbers come from challenges/02-tnfa/notes/ (lineage-best-design.md,
submission-set-2026-10-18.md, filter-calibration.md) and the md-movies README.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403

VIEWS = Path(__file__).resolve().parent.parent / "viewers" / "views"


class S1_Title(C2):
    experiment = "final campaign"
    WAIT = 3.5

    def construct(self):
        k = T("VIDEO 14  \u00b7  THE FINAL CAMPAIGN", size=20, color=CYAN, weight=BOLD)
        t = T("The champion", size=56, color=INK, weight=BOLD)
        s = T("From Genie 3 backbones to the E33H switch \u2014 the method, the steps,\n"
              "the tools. And two of the designs, in motion.", size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.04)
        self.play(Write(t), run_time=1.82)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.3)
        self.wait(self.WAIT)
        self.finish()


class S2_Lineage(C2):
    experiment = "final campaign"
    WAIT = 15.1

    def construct(self):
        self.header()
        head = T("One line of ancestry", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        row1, boxes1 = self.step_strip(
            ["Genie 3\nbackbones", "d7 family\nfull-backbone MPNN", "+D47A\nhuman record",
             "mouse-first\nmce redesign"], size=15)
        row1.move_to(UP * 1.2)
        row2, boxes2 = self.step_strip(
            ["dual-select\n2 generations", "histidine\nretrofit (sr)", "E33H\none swap",
             "the champion\n+ submission set"], size=15)
        row2.next_to(row1, DOWN, buff=0.8)
        foot = T("every link had a measured decision behind it", size=19, color=CYAN)
        foot.next_to(row2, DOWN, buff=0.85)
        self.play(Write(head), run_time=1.98)
        self.play(LaggedStart(*[FadeIn(b) for b in boxes1], lag_ratio=0.15), run_time=2.42)
        self.play(LaggedStart(*[FadeIn(b) for b in boxes2], lag_ratio=0.15), run_time=2.42)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(self.WAIT)
        self.finish()


class S3_Calibration(C2):
    experiment = "final campaign"
    WAIT = 15.0

    def construct(self):
        self.header()
        head = T("First: calibrate the bar", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        lb = T("released campaign \u00b7 re-scored here", size=17, color=MUTED)
        lb.move_to([-3.9, 1.5, 0])
        left = VGroup(
            lb,
            T("ipSAE 0.6\u20130.8   0 of 22 bound", size=19, color=RED).move_to([-3.9, 0.95, 0]),
            T("ipSAE \u2265 0.8   ~26 % bound", size=19, color=GREEN).move_to([-3.9, 0.4, 0]),
            T("reproduces within \u00b10.03", size=19, color=CYAN).move_to([-3.9, -0.15, 0]),
        )
        rb = T("which generator found them", size=17, color=MUTED)
        rb.move_to([3.9, 1.5, 0])
        right = VGroup(
            rb,
            T("Genie 3   8 / 23", size=19, color=GREEN).move_to([3.9, 0.95, 0]),
            T("PXDesign   4 / 57", size=19, color=MUTED).move_to([3.9, 0.4, 0]),
            T("RFdiffusion3   1 / 40", size=19, color=RED).move_to([3.9, -0.15, 0]),
        )
        note = T("the bar: ipSAE \u2265 0.8 at the designed junction", size=19, color=CYAN)
        note.move_to([0, -1.6, 0])
        warn = T("one warning: two never-binding designs outscored every winner",
                 size=18, color=AMBER)
        warn.move_to([0, -2.3, 0])
        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(left, shift=RIGHT * 0.2), run_time=1.76)
        self.play(FadeIn(right, shift=LEFT * 0.2), run_time=1.76)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(warn), run_time=1.32)
        self.wait(self.WAIT)
        self.finish()


class S4_Backbones(C2):
    experiment = "final campaign"
    WAIT = 20.8

    def construct(self):
        self.header()
        head = T("Genie 3 makes the backbones", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        c1 = self.chip("Genie 3 \u00b7 open \u00b7 347 MB \u00b7 66 s per design", GREEN, size=19)
        c1.move_to([0, 1.35, 0])
        c2 = self.chip("runs on the 12 GB card", GREEN, size=19)
        c2.next_to(c1, DOWN, buff=0.3)
        fmt = T("format: single chain \u00b7 50\u2013120 aa \u00b7 two-protomer junction \u00b7 hotspots B102 + D62",
                size=18, color=AMBER)
        fmt.move_to([0, -0.25, 0])
        r1 = T("batch 1 \u2014 8 designs \u2192 one clean fold: d7 \u00b7 64 aa", size=20, color=INK)
        r1.move_to([0, -0.85, 0])
        r2 = T("batch 2 \u2014 16 designs \u2192 the d12 family \u00b7 92 aa", size=20, color=INK)
        r2.next_to(r1, DOWN, buff=0.4)
        foot = T("backbone choice dominates everything after it", size=19, color=CYAN)
        foot.next_to(r2, DOWN, buff=0.7)
        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(c1, shift=UP * 0.15), run_time=1.32)
        self.play(FadeIn(c2), run_time=1.1)
        self.play(FadeIn(fmt), run_time=1.32)
        self.play(FadeIn(r1), run_time=1.32)
        self.play(FadeIn(r2), run_time=1.32)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(self.WAIT)
        self.finish()


class S5_MPNN(C2):
    experiment = "final campaign"
    WAIT = 17.7

    def construct(self):
        self.header()
        head = T("Fold first, then re-sequence", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        b = self.bullets([
            "the first family came out capped \u2014 the CA-only lesson",
            "fix: re-sequence the FOLDED backbone \u00b7 full-backbone ProteinMPNN",
            "d7 family: 18 variants \u00b7 0.63\u20130.85 \u00b7 every fold at the designed site",
            "a control backbone stayed below 0.19",
        ], size=20, buff=0.42)
        b.next_to(head, DOWN, buff=1.1).to_edge(LEFT, buff=1.0)
        foot = T("expand families on the winners \u2014 backbones, not sequences, are the budget",
                 size=19, color=CYAN)
        foot.to_edge(DOWN, buff=0.75)
        self.play(Write(head), run_time=1.98)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.2) for x in b], lag_ratio=0.3),
                  run_time=3.2)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(self.WAIT)
        self.finish()


class S6_CoFold(C2):
    experiment = "final campaign"
    WAIT = 12.8

    def construct(self):
        self.header()
        head = T("One gate for every candidate", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        strip, boxes = self.step_strip(
            ["Boltz-2 co-fold\n5 samples \u00b7 seed 42", "ipSAE at the\ndesigned junction",
             "site check\nboth protomers", "bar \u2265 0.8"], size=15)
        strip.move_to(UP * 1.05)
        note = T("score and site, together \u2014 neither is evidence alone", size=20, color=INK)
        note.move_to([0, -0.5, 0])
        note2 = T("both designs passed", size=20, color=GREEN)
        note2.move_to([0, -1.3, 0])
        self.play(Write(head), run_time=1.98)
        self.play(LaggedStart(*[FadeIn(x) for x in boxes], lag_ratio=0.16), run_time=3.3)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(note2), run_time=1.1)
        self.wait(self.WAIT)
        self.finish()


class S9_Mouse(C2):
    experiment = "final campaign"
    WAIT = 14.1

    def construct(self):
        self.header()
        head = T("Mouse: select, do not check", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        b = self.bullets([
            "first mouse check \u2014 the site held, the scores degraded (0.46\u20130.64)",
            "released mouse binders read 0.73\u20130.89 \u2014 the family sat below",
            "fix: SELECT on mouse \u2014 64 sequences, 16 folded",
            "mce-14: the first design strong on both species at once",
        ], size=20, buff=0.42)
        b.next_to(head, DOWN, buff=1.1).to_edge(LEFT, buff=1.0)
        foot = T("cross-reactivity must be selected for, not checked for", size=19, color=CYAN)
        foot.to_edge(DOWN, buff=0.75)
        self.play(Write(head), run_time=1.98)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.2) for x in b], lag_ratio=0.3),
                  run_time=3.2)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(self.WAIT)
        self.finish()


class S10_DualSelect(C2):
    experiment = "final campaign"
    WAIT = 15.3

    def construct(self):
        self.header()
        head = T("Two generations lock the dual profile", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        row = self.number_row([
            ("0.856", "ds-mce-14-v6 \u00b7 human", GREEN),
            ("0.854", "mouse", GREEN),
            ("0.868", "ds2 \u00b7 mouse record", CYAN),
        ], size_big=42, buff=0.95)
        row.move_to([0, 0.7, 0])
        n1 = T("every fold 5/5 at the designed site", size=19, color=INK)
        n1.move_to([0, -1.3, 0])
        n2 = T("then the family plateaued \u2014 change the input, not the volume",
                size=19, color=AMBER)
        n2.move_to([0, -2.05, 0])
        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.18), run_time=2.2)
        self.play(FadeIn(n1), run_time=1.32)
        self.play(FadeIn(n2), run_time=1.32)
        self.wait(self.WAIT)
        self.finish()


class S11_Switch(C2):
    experiment = "final campaign"
    WAIT = 21.9

    def construct(self):
        self.header()
        head = T("The switch: one histidine", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        m1 = T("pH 7.4 \u2014 histidine neutral \u00b7 the binder sticks", size=19, color=INK)
        m2 = T("pH 6.0 \u2014 histidine protonated \u00b7 repelled by the target lysine \u00b7 released",
               size=19, color=INK)
        mech = self.card(max(m1.width, m2.width) + 1.0, 1.75, stroke=AMBER)
        mg = VGroup(m1, m2).arrange(DOWN, buff=0.3).move_to(mech)
        mech = VGroup(mech, mg).move_to([0, 0.9, 0])
        rows = VGroup(
            T("linkage check: the lineage had NO switch \u2014 slightly tighter in acid",
              size=19, color=RED),
            T("sr1 \u00b7 three histidines \u2014 sign flipped (+0.836 = 6.9\u00d7) but binding cost",
              size=19, color=AMBER),
            T("sr2 scan \u2192 E33H on the salt bridge \u2014 binding kept", size=19, color=GREEN),
            T("+1.738 = 54.7\u00d7 toward pH 7.4 \u2014 the strongest switch measured here",
              size=19, color=CYAN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        rows.move_to([0, -1.35, 0])
        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(mech, shift=UP * 0.15), run_time=1.76)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.15) for x in rows], lag_ratio=0.35),
                  run_time=3.6)
        self.wait(self.WAIT)
        self.finish()


class S12_Champion(C2):
    experiment = "final campaign"
    WAIT = 15.4

    def construct(self):
        self.header()
        head = T("The champion \u2014 sr2-ds-mce-14-v6-r2c", size=34, color=INK, weight=BOLD)
        head.to_edge(UP, buff=0.85)
        row = self.number_row([
            ("0.849", "human \u00b7 5/5", GREEN),
            ("0.847", "mouse \u00b7 5/5", GREEN),
            ("54.7\u00d7", "switch toward 7.4", CYAN),
        ], size_big=40, buff=0.85)
        row.move_to([0, 1.55, 0])
        img1 = ImageMobject(str(VIEWS / "sr2-r2c-human" / "sr2-r2c-human_interface_view1.png"))
        img2 = ImageMobject(str(VIEWS / "sr2-r2c-mouse" / "sr2-r2c-mouse_interface_view1.png"))
        img1.scale_to_fit_height(2.75)
        img2.scale_to_fit_height(2.75)
        pair = Group(img1, img2).arrange(RIGHT, buff=0.55).move_to([0, -0.75, 0])
        cap1 = T("human interface", size=16, color=MUTED).next_to(img1, DOWN, buff=0.12)
        cap2 = T("mouse interface", size=16, color=MUTED).next_to(img2, DOWN, buff=0.12)
        foot = T("E33H \u00b7 one substitution of the best dual design \u00b7 "
                 "every switch ships with its paired control", size=16, color=MUTED)
        foot.to_edge(DOWN, buff=0.45)
        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.18), run_time=2.2)
        self.play(FadeIn(pair, scale=0.98), run_time=1.76)
        self.play(FadeIn(cap1), FadeIn(cap2), run_time=1.1)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(self.WAIT)
        self.finish()


class S13_Close(C2):
    experiment = "final campaign"
    WAIT = 12.6

    def construct(self):
        self.header()
        head = T("The submission set", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)
        b = self.bullets([
            "8 designs \u00b7 5 switch variants \u00b7 2 paired controls \u00b7 the human record",
            "one molecule carries all three ranked objectives",
        ], size=20, buff=0.45)
        b.move_to([0, 0.7, 0]).to_edge(LEFT, buff=1.0)
        honest = T("in-silico only \u2014 prediction until the lab runs it", size=20, color=AMBER)
        honest.move_to([0, -1.0, 0])
        tools = T("Genie 3 \u00b7 ProteinMPNN \u00b7 Boltz-2 \u00b7 ipSAE \u00b7 PROPKA linkage\n"
                  "OpenMM MD \u00b7 Mol* review \u00b7 the released campaign for calibration",
                  size=17, color=MUTED)
        tools.move_to([0, -2.0, 0])
        fin = T("the champion: sr2-ds-mce-14-v6-r2c", size=18, color=CYAN)
        fin.to_edge(DOWN, buff=0.5)
        self.play(Write(head), run_time=1.98)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.2) for x in b], lag_ratio=0.4),
                  run_time=2.0)
        self.play(FadeIn(honest), run_time=1.32)
        self.play(FadeIn(tools), run_time=1.32)
        self.play(FadeIn(fin), run_time=1.1)
        self.wait(self.WAIT)
        self.finish()


NARRATION = {
    "S1_Title": (
        "The campaign that produced the champion. The method, the steps, the tools \u2014 "
        "and two of the designs, in motion."
    ),
    "S2_Lineage": (
        "The ancestry in one line: Genie three made the backbones. Full-backbone ProteinMPNN "
        "built families on the best one. A mutation round lifted the human record. A "
        "mouse-first redesign made it cross-reactive. Two selection generations tightened "
        "both species. And one histidine gave it the pH switch. Every link had a measured "
        "decision behind it."
    ),
    "S3_Calibration": (
        "First, calibration. We re-scored the released campaign \u2014 one hundred and fifty "
        "designs \u2014 and reproduced their scores within three hundredths. The bar: below zero "
        "point eight, almost no binders; at or above, a quarter bound. The generator decides "
        "more than the filter: Genie three made eight of their twenty-three binders; ours, "
        "one of forty."
    ),
    "S4_Backbones": (
        "The format came first: single small chains, the full trimer, the junction of two "
        "protomers \u2014 the released hotspot pair, B one-oh-two and D sixty-two. Genie three "
        "then made the backbones \u2014 open source, sixty-six seconds per design. Batch one: "
        "eight designs, one clean fold \u2014 d seven, sixty-four residues. Batch two: sixteen "
        "designs \u2014 the d twelve family, ninety-two residues. Backbone choice dominates "
        "everything after it."
    ),
    "S5_MPNN": (
        "Then the sequences. The first family came out capped \u2014 the CA-only lesson: "
        "without the side chains, every score stays low. The fix: re-sequence the folded "
        "backbone. Eighteen variants of d seven \u2014 zero point six three to zero point "
        "eight five \u2014 every fold at the designed site; a control backbone stayed below "
        "zero point one nine. Fold first; expand families on the winners."
    ),
    "S6_CoFold": (
        "Every candidate met the same gate. Boltz two co-folds it: five samples, seed "
        "forty-two. I P S A E scores the interface at the designed two-protomer junction, "
        "and a site check requires both halves of the epitope to touch. Score and site, "
        "together \u2014 neither is evidence alone. Both designs passed."
    ),
    "S7_MD_d7": (
        "Two of the designs, in motion. D seven x t three dash three \u2014 real all-atom "
        "molecular dynamics against human TNF-alpha. Pink is the binder; blue is the "
        "target. About three quarters of the interface contacts hold through the run. A "
        "physics test of the pose, not an assay."
    ),
    "S8_MD_d12": (
        "The second design: b two x d twelve dash two \u2014 the independent scaffold, "
        "ninety-two residues. Same treatment, same physics. Fifty-three interface pairs at "
        "the start, and the contact count holds through the run. The backup sits where it "
        "was designed to sit."
    ),
    "S9_Mouse": (
        "Then mouse. The first check said the family kept the designed interface on mouse "
        "\u2014 but degraded, below the band of released mouse binders. So we stopped checking "
        "and started selecting: sixty-four sequences designed against the mouse protein, "
        "sixteen folded. mce fourteen: the first design strong on both species at once."
    ),
    "S10_DualSelect": (
        "Two selection generations locked it in. ds-mce-14-v6 \u2014 one substitution \u2014 at "
        "zero point eight five six human and zero point eight five four mouse. The ds two "
        "family pushed the mouse side to zero point eight six eight. Then the family "
        "plateaued \u2014 the pre-registered move: change the input, not the volume."
    ),
    "S11_Switch": (
        "Now the switch \u2014 the objective ranked first. The linkage check found no switch at "
        "all \u2014 slightly tighter in acid, the wrong direction. The retrofit: histidines "
        "against the interface lysine. The first version, three histidines, flipped the sign "
        "but cost binding. A position scan found the fix: at residue thirty-three, one "
        "histidine on the salt bridge kept the binding \u2014 the strongest switch measured "
        "here, fifty-four point seven times toward pH seven point four."
    ),
    "S12_Champion": (
        "That is the champion: S R two, D S mce fourteen, V six, R two C \u2014 one "
        "substitution, E thirty-three H, of the best dual design. Human zero point eight "
        "four nine, mouse zero point eight four seven, five of five on both. Every switch "
        "ships with its paired control \u2014 the lab subtracts everything except the histidine."
    ),
    "S13_Close": (
        "Final tally: eight designs submitted \u2014 five switch variants, two paired controls, "
        "and the human-target record. Everything is prediction until the lab runs it. Tools: "
        "Genie three, ProteinMPNN, Boltz two, I P S A E, PROPKA linkage, OpenMM dynamics, "
        "Mol star renders."
    ),
}
