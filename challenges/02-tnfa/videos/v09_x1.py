"""Video 09 — X1: the BoltzGen groove-docking benchmark.

Three hotspot sets, 150 designs, a pre-registered bar, and a measured negative.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "X1 \u00b7 BoltzGen benchmark"

    def construct(self):
        k = T("VIDEO 09 / 12  \u00b7  CAMPAIGN EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("X1: the BoltzGen benchmark", size=52, color=INK, weight=BOLD)
        s = T("Three hotspot sets, 150 designs. Does anything\nland in the antibody groove?",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.76)
        self.play(Write(t), run_time=3.08)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=2.2)
        self.wait(7.5)
        self.finish()


class S2_Rules(C2):
    experiment = "X1 \u00b7 BoltzGen benchmark"

    def construct(self):
        self.header()
        head = T("The rules, fixed before the spend", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "design against the full trimer \u2014 a partial target lets binders fill the omitted protomer",
            "keep the hotspot span near 15 \u00c5",
            "a design docks only if the interface confidence clears the bar",
            "a stop rule: nothing docks anywhere \u2192 stop, change the setup, do not rerun",
        ], size=20, buff=0.38)
        b.move_to(UP * 0.15).to_edge(LEFT, buff=1.0)

        chip = self.chip("ipSAE \u2265 0.6  AND  pDockQ2 \u2265 0.23  AND  ~100 atom contacts", CYAN, size=18)
        chip.move_to(DOWN * 2.5)

        self.play(Write(head), run_time=1.98)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1.21)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=1.32)
        self.wait(7.4)
        self.finish()


class S3_Setup(C2):
    experiment = "X1 \u00b7 BoltzGen benchmark"

    def construct(self):
        self.header()
        head = T("Three sets, one service", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        def setcard(name, detail, note, col, x):
            t1 = T(name, size=22, color=col, weight=BOLD)
            t2 = T(detail, size=17, color=INK)
            t3 = T(note, size=15, color=MUTED)
            c = self.card(4.15, 2.7, stroke=col)
            g = VGroup(t1, t2, t3).arrange(DOWN, buff=0.22).move_to(c)
            return VGroup(c, g).move_to([x, 0.15, 0])

        c1 = setcard("S1", "antibody epitope\n{A65, A67, C75}", "the drug-antibody\ngroove", BLUE, -4.55)
        c2 = setcard("S2", "switch trio\n{A103, B103, B112}", "the charged\npatch", AMBER, 0.0)
        c3 = setcard("S3", "no hotspots", "the diagnostic:\nis the site the limiter?", MUTED, 4.55)
        row = VGroup(c1, c2, c3)

        foot = T("Tamarind, free agent tier: 10 jobs a month \u00b7 50 designs per set \u00b7 refold on",
                 size=18, color=MUTED)
        foot.move_to(DOWN * 2.4)

        self.play(Write(head), run_time=1.98)
        for c in (c1, c2, c3):
            self.play(FadeIn(c, shift=UP * 0.18), run_time=1.32)
            self.wait(2.5)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(11.7)
        self.finish()


class S4_Result(C2):
    experiment = "X1 \u00b7 BoltzGen benchmark"

    def construct(self):
        self.header()
        head = T("Result \u2014 150 designs, zero docks", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        row = self.number_row([
            ("150", "designs\ndelivered", CYAN),
            ("0.356", "best ipTM\n(S1)", MUTED),
            ("0.005", "best ipSAE\nany set", RED),
            ("0", "pass the bar", RED),
        ], size_big=46, buff=0.95)
        row.move_to(UP * 0.35)

        note = T("best ipTM per set: 0.356 / 0.220 / 0.326 \u00b7 pDockQ2 0.000 everywhere",
                 size=19, color=MUTED)
        note.move_to(DOWN * 1.75)
        note2 = T("all three sets fail \u2014 including the one with no hotspots",
                  size=19, color=RED)
        note2.move_to(DOWN * 2.4)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.2), run_time=2.42)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(note2), run_time=1.32)
        self.wait(13.8)
        self.finish()


class S5_Touching(C2):
    experiment = "X1 \u00b7 BoltzGen benchmark"

    def construct(self):
        self.header()
        head = T("Touching, not docking", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c = self.card(12.2, 3.0, stroke=RED)
        l1 = T("designs fold well alone:  pTM 0.76\u20130.81", size=20, color=GREEN)
        l2 = T("they press against the trimer:  up to 162 of 639 atoms within 4 \u00c5", size=20, color=INK)
        l3 = T("but interface confidence \u2248 0:  ipSAE 0.005 best \u00b7 PAE 14\u201321 \u00c5", size=20, color=RED)
        l4 = T("the trimer itself scores fine:  internal pairs ipSAE 0.30\u20130.44", size=20, color=MUTED)
        g = VGroup(l1, l2, l3, l4).arrange(DOWN, aligned_edge=LEFT, buff=0.26).move_to(c)
        grp = VGroup(c, g).move_to(UP * 0.2)

        foot = T("a credible interface looks like the reviewed EGFR entry: ipTM 0.95",
                 size=19, color=MUTED)
        foot.next_to(grp, DOWN, buff=0.7)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(grp, shift=UP * 0.15), run_time=2.2)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(17.1)
        self.finish()


class S6_Meaning(C2):
    experiment = "X1 \u00b7 BoltzGen benchmark"

    def construct(self):
        self.header()
        head = T("What the diagnostic proves", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "the no-hotspot set does exactly as well as the targeted sets",
            "so the site choice is not the limiter",
            "stop rule 1 activated: no further spend on this setup",
            "the result replicates both public attempts, on a different tool stack",
        ], size=21, buff=0.42)
        b.move_to(UP * 0.2).to_edge(LEFT, buff=1.0)

        chip = self.chip("change the generator \u2014 not the site", CYAN, size=20)
        chip.move_to(DOWN * 2.5)

        self.play(Write(head), run_time=0.9)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.55)
            self.wait(2.5)
        self.play(FadeIn(chip), run_time=0.6)
        self.wait(3.4)
        self.finish()


class S7_Close(C2):
    experiment = "X1 \u00b7 BoltzGen benchmark"

    def construct(self):
        l1 = T("A measured, pre-registered negative.", size=36, color=INK, weight=BOLD)
        l2 = T("The next experiment changes the generator.", size=26, color=CYAN)
        g = VGroup(l1, l2).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN).to_edge(LEFT, buff=1.0)
        self.play(Write(l1), run_time=1.1)
        self.play(FadeIn(l2, shift=UP * 0.15), run_time=0.8)
        self.wait(4.9)
        self.finish()


NARRATION = {
    "S1_Title": (
        "This is X one: the BoltzGen benchmark. The question is narrow and pre-registered: with "
        "a full trimer as the target, does any design land in the antibody groove? One hundred "
        "and fifty designs across three hotspot sets say no."
    ),
    "S2_Rules": (
        "The rules were fixed before the spend. Design against the full trimer only \u2014 a partial "
        "target lets binders fill the omitted protomer. Keep the hotspot span near fifteen "
        "angstroms. A design docks only if ipSAE is at least zero point six, pDockQ2 at least "
        "zero point two three, and it makes about a hundred atom contacts. And a stop rule: if "
        "nothing docks anywhere, stop and change the setup."
    ),
    "S3_Setup": (
        "The runs went to Tamarind on the free agent tier: ten jobs a month, no email, no card, "
        "and the key stored outside every repository. Three sets of fifty designs. S one, the "
        "antibody epitope: residues sixty-five, sixty-seven, and seventy-five. S two, the switch "
        "trio. And S three, the diagnostic with no hotspots at all. Every set was refolded for "
        "interface metrics."
    ),
    "S4_Result": (
        "The result: one hundred and fifty designs delivered. The best interface confidence per "
        "set: zero point three six, zero point two two, zero point three three. Best ipSAE: zero "
        "point zero zero five. Best pDockQ2: zero. Zero designs pass the bar, in any set."
    ),
    "S5_Touching": (
        "The designs are not ignored by the model \u2014 they press against the trimer surface, some "
        "even overlap it. But the model gives the design-to-target interface almost no "
        "confidence, with interface errors of fourteen to twenty-one angstroms. Touching, not "
        "docking. The trimer itself is predicted normally; its internal interfaces score up to "
        "zero point four four."
    ),
    "S6_Meaning": (
        "The decisive number is the diagnostic. The no-hotspot set does exactly as well as the "
        "targeted sets \u2014 so the site choice is not the limiter. Stop rule one activated: no "
        "further spend on this setup. The result replicates both public attempts, with a "
        "different tool stack."
    ),
    "S7_Close": (
        "A measured, pre-registered negative \u2014 and the reason the next experiment changes the "
        "generator, not the site."
    ),
}
