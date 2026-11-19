"""Video 12 — X3: the site check that closed the campaign.

The strategy change, the origin bug, four patches, and the finding that a
docking score is not evidence about a designed interface.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "X3 \u00b7 site check"

    def construct(self):
        k = T("VIDEO 12 / 12  \u00b7  CAMPAIGN EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("X3: the site check", size=52, color=INK, weight=BOLD)
        s = T("Four patches, 168 designs \u2014 and the finding that\nclosed the campaign.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.02)
        self.play(Write(t), run_time=1.78)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.27)
        self.wait(5.6)
        self.finish()


class S2_Levers(C2):
    experiment = "X3 \u00b7 site check"

    def construct(self):
        self.header()
        head = T("Two levers, measured before spending", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        def lever(title, lines, col, x):
            t1 = T(title, size=22, color=col, weight=BOLD)
            t2 = T(lines, size=17, color=INK)
            c = self.card(5.9, 3.2, stroke=col)
            g = VGroup(t1, t2).arrange(DOWN, buff=0.3).move_to(c)
            return VGroup(c, g).move_to([x, 0.1, 0])

        l1 = lever("1 \u00b7 the true receptor site",
                   "the 84\u201389 loop of one protomer\n+ the 147 loop of its neighbour\n"
                   "span 15.3 \u00c5 \u00b7 cross-protomer\nhotspots: A83, A87, A89, B147",
                   BLUE, -3.5)
        l2 = lever("2 \u00b7 a trimmed target",
                   "195 residues / 1543 atoms\ninstead of 456 / ~3600\n"
                   "50 s per design instead of 302 s\nsame geometry, all three chains",
                   CYAN, 3.5)

        foot = T("the hotspot set was never the receptor-binding site \u2014 now it is",
                 size=19, color=MUTED)
        foot.move_to(DOWN * 2.6)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(l1, shift=RIGHT * 0.2), run_time=1.76)
        self.play(FadeIn(l2, shift=LEFT * 0.2), run_time=1.76)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(27.3)
        self.finish()


class S3_Bug(C2):
    experiment = "X3 \u00b7 site check"

    def construct(self):
        self.header()
        head = T("The bug that made the first batch worthless", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c = self.card(12.4, 2.9, stroke=RED)
        r1 = VGroup(
            T("before", size=19, color=RED, weight=BOLD),
            T("centroid 4.7\u201311.7 \u00c5  \u00b7  24\u201332 atoms < 2 \u00c5", size=19, color=RED))
        r2 = VGroup(
            T("after ", size=19, color=GREEN, weight=BOLD),
            T("centroid 23\u201327 \u00c5  \u00b7  0\u20132 atoms < 2 \u00c5", size=19, color=GREEN))
        for r in (r1, r2):
            r.arrange(RIGHT, buff=0.7)
        grid = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        grid.move_to(c).align_to(c, LEFT).shift(RIGHT * 0.9)
        grp = VGroup(c, grid).move_to(UP * 0.15)

        note = T("without infer_ori_strategy=hotspots, the origin comes from the centre of mass \u2014\n"
                 "the binder is placed inside the target", size=19, color=AMBER)
        note.next_to(grp, DOWN, buff=0.55)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(grp, shift=UP * 0.15), run_time=1.98)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=1.54)
        self.wait(20.8)
        self.finish()


class S4_Sets(C2):
    experiment = "X3 \u00b7 site check"

    def construct(self):
        self.header()
        head = T("Four sets on the local GPU", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        def setrow(name, detail, chip_txt, chip_col, y):
            n = T(name, size=21, color=CYAN, weight=BOLD)
            n.move_to([-5.9, y, 0])
            d = T(detail, size=17, color=INK)
            d.next_to(n, RIGHT, buff=0.4)
            ch = self.chip(chip_txt, chip_col, size=15)
            ch.move_to([5.0, y, 0])
            return VGroup(n, d, ch)

        rows = VGroup(
            setrow("X3-A", "receptor-binding site (RBS)", "11 of 24 at the site", MUTED, 1.55),
            setrow("X3-B", "switch trio", "24 of 24 at the site", GREEN, 0.55),
            setrow("X3-C", "the X2 groove \u2014 control", "21 of 24 \u2192 setup validated", GREEN, -0.45),
            setrow("X3-D", "the patch the fold model prefers", "96 designs \u00b7 43 at the patch", MUTED, -1.45),
        )

        foot = T("the control ties this box to the Tamarind result \u2014 same behaviour",
                 size=19, color=MUTED)
        foot.move_to(DOWN * 2.6)

        self.play(Write(head), run_time=0.9)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.2), run_time=0.5)
            self.wait(2.5)
        self.play(FadeIn(foot), run_time=0.6)
        self.wait(3.8)
        self.finish()


class S5_Folds(C2):
    experiment = "X3 \u00b7 site check"

    def construct(self):
        self.header()
        head = T("The co-folds came back quiet", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        row = self.number_row([
            ("0.230", "x3b-switch-2", RED),
            ("0.229", "x3a-rbs-16", RED),
            ("0.012", "x3a-rbs-15", RED),
        ], size_big=46, buff=1.1)
        row.move_to(UP * 0.5)

        note = T("best ipSAE per design \u00b7 bar is 0.6 \u2014 all fail", size=19, color=MUTED)
        note.move_to(DOWN * 1.1)
        note2 = T("at this hit rate, 24 designs per set cannot be expected to produce a pass",
                  size=19, color=MUTED)
        note2.move_to(DOWN * 1.8)
        note3 = T("generation is cheap now \u2014 scale it, then fold only the best",
                  size=19, color=CYAN)
        note3.move_to(DOWN * 2.5)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.2), run_time=2.2)
        self.play(FadeIn(note), run_time=1.1)
        self.play(FadeIn(note2), run_time=1.1)
        self.play(FadeIn(note3), run_time=1.1)
        self.wait(10.9)
        self.finish()


class S6_Finding(C2):
    experiment = "X3 \u00b7 site check"

    def construct(self):
        self.header()
        head = T("The finding", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        q1 = T("ipSAE answers: is there an interface?", size=24, color=INK)
        q2 = T("Not: is the interface where the design put it.", size=24, color=AMBER, weight=BOLD)
        q = VGroup(q1, q2).arrange(DOWN, buff=0.25).move_to(UP * 1.35)

        c = self.card(12.2, 2.9, stroke=AMBER)
        l1 = T("12 designs folded \u00b7 60 predicted samples", size=19, color=MUTED)
        l2 = T("9 samples sit on the designed epitope \u2014 all score  ipSAE 0.000", size=19, color=RED)
        l3 = T("highest score in the batch: 0.769 \u2014 sitting 18 \u00c5 from the design", size=19, color=RED)
        l4 = T("retrospective: the earlier \"passing\" fold sat 15\u201318 \u00c5 off its groove",
               size=19, color=AMBER)
        g = VGroup(l1, l2, l3, l4).arrange(DOWN, aligned_edge=LEFT, buff=0.24).move_to(c)
        grp = VGroup(c, g).move_to(DOWN * 0.65)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(q, shift=UP * 0.15), run_time=1.98)
        self.play(FadeIn(grp, shift=UP * 0.15), run_time=2.2)
        self.wait(24.7)
        self.finish()


class S7_Total(C2):
    experiment = "X3 \u00b7 site check"

    def construct(self):
        self.header()
        head = T("The campaign total", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        row = self.number_row([
            ("18", "designs folded\nacross the campaign", MUTED),
            ("90", "predicted\nsamples", MUTED),
            ("0", "clear the bar AND\nsit on the design", RED),
        ], size_big=54, buff=1.2)
        row.move_to(UP * 0.5)

        rule = T("selection must require the score and the site together", size=24,
                 color=CYAN, weight=BOLD)
        rule.move_to(DOWN * 1.35)
        note = T("the check: contacts against the designed residues, on two protomers\n"
                 "screen_folds_site.py \u2014 in the repo", size=19, color=MUTED)
        note.move_to(DOWN * 2.35)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.2), run_time=2.42)
        self.play(FadeIn(rule, shift=UP * 0.12), run_time=1.76)
        self.play(FadeIn(note), run_time=1.32)
        self.wait(10.1)
        self.finish()


class S8_Close(C2):
    experiment = "X3 \u00b7 site check"

    def construct(self):
        l1 = T("The campaign closed on its pre-registered rule.", size=30, color=INK, weight=BOLD)
        l2 = T("No submission. The method and the negative stay.", size=30, color=INK, weight=BOLD)
        l3 = T("A docking score is not evidence about a designed interface.", size=24, color=CYAN)
        g = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        g.move_to(ORIGIN).to_edge(LEFT, buff=1.0)
        self.play(Write(l1), run_time=2.42)
        self.play(Write(l2), run_time=2.42)
        self.play(FadeIn(l3, shift=UP * 0.15), run_time=1.76)
        self.wait(7.3)
        self.finish()


NARRATION = {
    "S1_Title": (
        "X three \u2014 the site check that closed the campaign. Four patches, one hundred and "
        "sixty-eight designs, and one finding that matters more than any of the scores."
    ),
    "S2_Levers": (
        "W two failed its stop rule, so the strategy changed \u2014 but only after two levers were "
        "measured. First: the hotspot set was not the receptor-binding site. Pairing the "
        "eighty-four to eighty-nine loop of one protomer with the one-forty-seven loop of its "
        "neighbour gives a compact, cross-protomer epitope: span fifteen point three angstroms. "
        "Second: the target representation \u2014 a trimmed patch keeps the geometry with one "
        "hundred and ninety-five residues instead of four hundred and fifty-six, and cuts "
        "generation time from five minutes to fifty seconds per design."
    ),
    "S3_Bug": (
        "The first batch was worthless, and the reason is a lesson: without the origin strategy "
        "set to hotspots, the binder is placed at the target's centre of mass \u2014 inside the "
        "target. Centroid shifts of five to twelve angstroms, dozens of atoms under two. The fix "
        "moved the binders out to twenty-three to twenty-seven angstroms. Screen every generator "
        "output: count binder atoms closer than two angstroms."
    ),
    "S4_Sets": (
        "Four sets ran: the receptor-binding site; the switch trio; the X two groove as a "
        "control \u2014 twenty-one of twenty-four local designs land there, so the local setup is "
        "validated; and the patch the fold model itself prefers. Ninety-six designs on that last "
        "set alone."
    ),
    "S5_Folds": (
        "The co-folds came back quiet. The best switch-trio design: ipSAE zero point two three. "
        "The best receptor-site design: zero point two three. All under the bar. At this hit "
        "rate, twenty-four designs per set cannot be expected to produce a pass \u2014 and "
        "generation is cheap now."
    ),
    "S6_Finding": (
        "Then the site check \u2014 the finding. ipSAE answers: is there an interface. It does not "
        "answer: is the interface where the design put it. Of sixty predicted samples, nine sit "
        "on their designed epitope \u2014 and all nine score zero point zero zero zero. The highest "
        "score in the batch, zero point seven seven, sits eighteen angstroms away. And the "
        "retrospective check on the earlier passing fold: it sits fifteen to eighteen angstroms "
        "from its designed groove. It was an interface \u2014 somewhere else."
    ),
    "S7_Total": (
        "Campaign total: eighteen designs folded, ninety samples, zero that both clear the bar "
        "and sit on the designed epitope. The last set: ninety-six designs generated, six "
        "folded, zero at the patch. Selection must require the score and the site together."
    ),
    "S8_Close": (
        "So the campaign closed, on its pre-registered rule. No submission. What it leaves "
        "behind is the method, the pipeline, and an honest negative \u2014 and the transferable "
        "rule: a docking score is not evidence about a designed interface."
    ),
}
