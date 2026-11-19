"""Video 04 — c2-scorer-controls: validating the instrument.

The linkage scorer against three systems with known answers, and the honest
statement of what it can and cannot do.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "c2-scorer-controls"

    def construct(self):
        k = T("VIDEO 04 / 12  ·  EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("c2-scorer-controls", size=56, color=INK, weight=BOLD)
        s = T("Proving the ranking tool on systems where\nthe answer is already known.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.32)
        self.play(Write(t), run_time=2.31)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.65)
        self.wait(5.6)
        self.finish()


class S2_What(C2):
    experiment = "c2-scorer-controls"

    def construct(self):
        self.header()
        head = T("The linkage scorer, on trial", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "PROPKA three times: on the complex, the free binder, the free target",
            "integrate the proton-release curve across the 6.0\u20137.4 window",
            "count the effective switching sites",
            "compare with the reference: tolerance 0.1, site count exact",
        ], size=21, buff=0.38)
        b.move_to(UP * 0.1).to_edge(LEFT, buff=1.0)

        chip = self.chip("no design docked \u2014 so the tool itself must be checked", MUTED, size=18)
        chip.move_to(DOWN * 2.2)

        self.play(Write(head), run_time=0.9)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.55)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=0.6)
        self.wait(3.5)
        self.finish()


class S3_Controls(C2):
    experiment = "c2-scorer-controls"

    def construct(self):
        self.header()
        head = T("Three known systems", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        def ctrl(name, pdb, exp, note, col, y):
            t1 = T(name, size=21, color=col, weight=BOLD)
            t2 = T(pdb, size=16, color=MUTED)
            t3 = T(exp, size=17, color=INK)
            t4 = T(note, size=15, color=MUTED)
            c = self.card(4.2, 3.1, stroke=col)
            g = VGroup(t1, t2, t3, t4).arrange(DOWN, buff=0.22).move_to(c)
            return VGroup(c, g).move_to([0, y, 0])

        c1 = ctrl("FcRn / IgG Fc", "1I1A", "expect \u22121.02 \u00b7 3 sites",
                  "the canonical\nhistidine acid switch", GREEN, 0.2)
        c2 = ctrl("barnase / barstar", "1BRS A+D \u00b7 cognate", "expect \u22120.52 \u00b7 2 sites",
                  "electrostatically\nsteered interface", CYAN, 0.2)
        c3 = ctrl("barnase / barstar", "1BRS A+E \u00b7 non-cognate", "expect 0.00 \u00b7 0 sites",
                  "no interface \u2014\nthe true negative", MUTED, 0.2)
        row = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.4).move_to(DOWN * 0.3)

        self.play(Write(head), run_time=1.52)
        for c in (c1, c2, c3):
            self.play(FadeIn(c, shift=UP * 0.18), run_time=1.01)
            self.wait(2.5)
        self.wait(5.6)
        self.finish()


class S4_Result(C2):
    experiment = "c2-scorer-controls"

    def construct(self):
        self.header()
        head = T("All six checks pass", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        ch1 = self.chip("3 / 3  delta checks OK", GREEN, size=20)
        ch2 = self.chip("3 / 3  site counts exact", GREEN, size=20)
        chips = VGroup(ch1, ch2).arrange(RIGHT, buff=0.6).move_to(UP * 1.2)

        l1 = T("cognate pair returned \u22120.58 \u2014 inside the 0.1 tolerance", size=20, color=INK)
        l2 = T("FcRn switch histidines recovered blind:", size=20, color=MUTED)
        l3 = T("C310  \u00b7  C435  \u00b7  C436      pKa shifted up on binding", size=22, color=GREEN, weight=BOLD)
        g = VGroup(l1, l2, l3).arrange(DOWN, buff=0.3).move_to(DOWN * 0.35)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(chips, shift=UP * 0.15), run_time=1.76)
        self.wait(0.1)
        for ln in g:
            self.play(FadeIn(ln, shift=RIGHT * 0.15), run_time=1.32)
            self.wait(2.5)
        self.wait(13.9)
        self.finish()


class S5_Limit(C2):
    experiment = "c2-scorer-controls"

    def construct(self):
        self.header()
        head = T("The honest limit", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c = self.card(11.6, 2.5, stroke=AMBER)
        t1 = T("the real FcRn switch is more than 100-fold \u2014", size=22, color=INK)
        t2 = T("the predicted magnitudes are about two orders smaller", size=22, color=AMBER)
        t3 = T("the instrument ranks designs; it does not predict absolute selectivity",
               size=20, color=MUTED)
        g = VGroup(t1, t2, t3).arrange(DOWN, buff=0.25).move_to(c)
        grp = VGroup(c, g).move_to(UP * 0.2)

        foot = T("that is how it was specified \u2014 and how it was used",
                 size=20, color=MUTED)
        foot.next_to(grp, DOWN, buff=0.8)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(grp, shift=UP * 0.15), run_time=1.98)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(8.5)
        self.finish()


class S6_Close(C2):
    experiment = "c2-scorer-controls"

    def construct(self):
        l1 = T("Validated. Specified.", size=44, color=INK, weight=BOLD)
        l2 = T("Trusted within its stated limits.", size=44, color=CYAN, weight=BOLD)
        l3 = T("The same discipline the campaign later applied to its fold scores.",
               size=22, color=MUTED)
        g = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        g.move_to(ORIGIN).to_edge(LEFT, buff=1.0)

        self.play(Write(l1), run_time=1.0)
        self.play(Write(l2), run_time=1.0)
        self.play(FadeIn(l3, shift=UP * 0.12), run_time=0.8)
        self.wait(5.6)
        self.finish()


NARRATION = {
    "S1_Title": (
        "Experiment four: c2-scorer-controls. Before any ranking tool is trusted on designs, it "
        "must prove itself on systems where the answer is already known."
    ),
    "S2_What": (
        "The linkage scorer runs PROPKA three times \u2014 on the complex, on the free binder, and on "
        "the free target \u2014 integrates the proton-release curve across the six point zero to "
        "seven point four window, and counts the effective switching sites. Each result is "
        "compared with the reference value."
    ),
    "S3_Controls": (
        "Three controls. FcRn with the IgG Fc \u2014 the canonical histidine acid switch, and the "
        "natural version of this challenge. Barnase with barstar, the cognate pair. And the same "
        "barnase against a non-cognate barstar chain: no interface, the true negative."
    ),
    "S4_Result": (
        "The scorer returns minus one point zero two for FcRn, with three effective sites \u2014 the "
        "expected values \u2014 and recovers the known switch histidines blind: His three ten, His "
        "four thirty-five, His four thirty-six, with their pKa shifted up on binding. The cognate "
        "pair returns minus zero point five eight, inside the tolerance. The non-cognate pair "
        "returns zero, with no sites. All six checks pass."
    ),
    "S5_Limit": (
        "The honest limit, recorded up front: the magnitudes are about two orders smaller than "
        "the real FcRn switch. The instrument ranks designs. It does not predict absolute "
        "selectivity, and it is used only that way."
    ),
    "S6_Close": (
        "Validated, specified, and trusted within its stated limits \u2014 the same discipline the "
        "campaign later applied to its fold scores."
    ),
}
