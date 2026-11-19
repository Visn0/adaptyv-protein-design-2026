"""Video 13 — the breakthrough: two promising designs (Genie 3 round 2).

The calibration on the released campaign, the generator change, the diff that
found the two errors, the fix, and the two designs it produced.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "genie3 \u00b7 round 2"

    def construct(self):
        k = T("VIDEO 13  \u00b7  THE BREAKTHROUGH", size=20, color=CYAN, weight=BOLD)
        t = T("Two promising designs", size=56, color=INK, weight=BOLD)
        s = T("After the campaign closed negative: a calibrated bar,\na new generator, and full-backbone sequence design.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.04)
        self.play(Write(t), run_time=1.82)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.3)
        self.wait(6.3)
        self.finish()


class S2_Calibration(C2):
    experiment = "genie3 \u00b7 round 2"

    def construct(self):
        self.header()
        head = T("First: calibrate the bar", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        # left: win rate by confidence bucket
        lb = T("released campaign \u00b7 150 designs", size=17, color=MUTED)
        lb.move_to([-3.9, 1.45, 0])
        rows = [
            ("\u2265 0.8", "9 / 35", "25.7 %", GREEN),
            ("0.7\u20130.8", "3 / 30", "10 %", MUTED),
            ("0.6\u20130.7", "0 / 22", "0 %", RED),
        ]
        g = VGroup(lb)
        y = 0.95
        for name, frac, rate, col in rows:
            row = T(f"ipSAE {name}   {frac}   \u2192 {rate}", size=18, color=col)
            row.move_to([-3.9, y, 0])
            g.add(row)
            y -= 0.55

        # right: generator win rates
        rb = T("which generator found them", size=17, color=MUTED)
        rb.move_to([3.9, 1.45, 0])
        g2 = VGroup(rb)
        gens = [
            ("Genie 3", "8 / 23", GREEN),
            ("PXDesign", "4 / 57", MUTED),
            ("RFdiffusion3  (ours)", "1 / 40", RED),
        ]
        y = 0.95
        for name, frac, col in gens:
            row = T(f"{name}   {frac}", size=18, color=col)
            row.move_to([3.9, y, 0])
            g2.add(row)
            y -= 0.55

        note = T("our pipeline reproduces their scores within \u00b10.03", size=18, color=CYAN)
        note.move_to([0, -1.45, 0])
        warn = T("one warning: two designs that never bound scored 0.906 / 0.910",
                 size=18, color=AMBER)
        warn.move_to([0, -2.15, 0])

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(g, shift=RIGHT * 0.2), run_time=1.76)
        self.play(FadeIn(g2, shift=LEFT * 0.2), run_time=1.76)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(warn), run_time=1.32)
        self.wait(28.7)
        self.finish()


class S3_Genie3(C2):
    experiment = "genie3 \u00b7 round 2"

    def construct(self):
        self.header()
        head = T("Change the generator", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c1 = self.chip("Genie 3 \u00b7 open \u00b7 347 MB \u00b7 66 s per design", GREEN, size=19)
        c1.move_to([0, 1.35, 0])
        c2 = self.chip("runs on the 12 GB card", GREEN, size=19)
        c2.next_to(c1, DOWN, buff=0.35)
        placed = T("8 designs out \u00b7 8 of 8 engage the designed interface", size=21, color=INK)
        placed.move_to([0, 0.0, 0])

        block = self.card(12.0, 2.0, stroke=RED)
        b1 = T("but the first batch stayed quiet:", size=20, color=MUTED)
        b2 = T("CA-only sequences \u00b7 best at-site fold 0.248 \u00b7 ten samples 0.000", size=19, color=RED)
        bl = VGroup(b1, b2).arrange(DOWN, buff=0.22).move_to(block)
        bg = VGroup(block, bl).move_to(DOWN * 1.5)

        foot = T("diagnosis: placement solved \u2014 the sequences were the weak link",
                 size=19, color=CYAN)
        foot.next_to(bg, DOWN, buff=0.55)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(c1, shift=UP * 0.15), run_time=1.32)
        self.play(FadeIn(c2), run_time=1.1)
        self.play(FadeIn(placed), run_time=1.32)
        self.play(FadeIn(bg, shift=UP * 0.15), run_time=1.76)
        self.play(FadeIn(foot), run_time=1.32)
        self.wait(20.8)
        self.finish()


class S4_Diff(C2):
    experiment = "genie3 \u00b7 round 2"

    def construct(self):
        self.header()
        head = T("The diff that found the errors", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        col_x = [-4.4, 0.0, 4.4]
        t1 = T("winners (13)", size=19, color=GREEN, weight=BOLD).move_to([col_x[0], 1.55, 0])
        t2 = T("our campaign", size=19, color=RED, weight=BOLD).move_to([col_x[1], 1.55, 0])
        t3 = T("batch-01", size=19, color=AMBER, weight=BOLD).move_to([col_x[2], 1.55, 0])

        rows = [
            ("charged %", "41.2", "9.8", "45.1"),
            ("greasy score", "\u22120.56", "+0.84", "\u22120.67"),
            ("largest AA %", "22.2", "37.3", "23.7"),
            ("interface pairs", "307\u2013370", "\u2014", "133\u2013185"),
        ]
        g = VGroup(t1, t2, t3)
        y = 1.0
        for name, a, b, c in rows:
            r = T(f"{name}", size=17, color=MUTED).move_to([-6.2, y, 0])
            va = T(a, size=19, color=INK).move_to([col_x[0], y, 0])
            vb = T(b, size=19, color=INK).move_to([col_x[1], y, 0])
            vc = T(c, size=19, color=INK).move_to([col_x[2], y, 0])
            g.add(r, va, vb, vc)
            y -= 0.62

        foot = T("greasy, alanine-heavy sequences are a class that does not bind",
                 size=19, color=RED)
        foot.move_to([0, -1.9, 0])
        foot2 = T("and the winners are one dominant backbone family \u2014 success converges",
                  size=19, color=MUTED)
        foot2.move_to([0, -2.6, 0])

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(g, shift=UP * 0.15), run_time=2.42)
        self.play(FadeIn(foot), run_time=1.32)
        self.play(FadeIn(foot2), run_time=1.32)
        self.wait(19.1)
        self.finish()


class S5_Fix(C2):
    experiment = "genie3 \u00b7 round 2"

    def construct(self):
        self.header()
        head = T("The fix: fold first, then re-sequence", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        strip, boxes = self.step_strip(
            ["fold a batch", "pick by\nsample spread", "full-backbone\nMPNN", "re-fold\nvariants",
             "keep only\nfamilies"],
            size=15,
        )
        strip.move_to(UP * 1.25)

        b = self.bullets([
            "CA-only sequencing was the chief error \u2014 redesign the same folded backbone",
            "18 variants \u00b7 family spans 0.63\u20130.85 \u00b7 every variant 5/5 at the designed site",
            "fresh seeds reproduced: 9 of 10 sequences landed 0.75\u20130.85",
            "a control backbone, treated identically, stayed below 0.19",
        ], size=19, buff=0.34)
        b.next_to(strip, DOWN, buff=0.85).to_edge(LEFT, buff=1.0)

        self.play(Write(head), run_time=1.98)
        self.play(LaggedStart(*[FadeIn(x) for x in boxes], lag_ratio=0.16), run_time=3.3)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1.1)
            self.wait(2.5)
        self.wait(17.5)
        self.finish()


class S6_Champion(C2):
    experiment = "genie3 \u00b7 round 2"

    def construct(self):
        self.header()
        head = T("Design one \u2014 d7x-t3-3", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        meta = T("64 aa \u00b7 alanine-rich \u00b7 designed to the released problem's interface",
                 size=19, color=MUTED)
        meta.move_to([0, 1.35, 0])
        seq = T("SEAERLRALRAEAEALLAQARAAGNKDAAQAAERAIVLYDRALSGDDTARAPAEAALAQARALV",
                size=14, color=INK)
        seq.move_to([0, 0.85, 0])

        plot = self.dot_plot(
            [("f0", 0.852), ("f1", 0.832), ("f2", 0.842), ("f3", 0.837), ("f4", 0.840)],
            w=6.6, h=2.7, ymin=0.78, ymax=0.88,
            thresholds=((0.8, GREEN, "0.8 line"),),
        )
        plot.move_to([-1.4, -0.75, 0])

        lines = VGroup(
            T("every fold \u2265 0.83", size=18, color=GREEN, weight=BOLD),
            T("every fold on the\ndesigned interface\n(cross-protomer)", size=16, color=INK),
            T("209 atom pairs", size=16, color=MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        lines.move_to([4.8, -0.75, 0])

        foot = T("released wet-lab binders score 0.86\u20130.91 here \u2014 the champion sits just below,\nin the band where about a quarter bound",
                 size=17, color=MUTED)
        foot.to_edge(DOWN, buff=0.55)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(meta), run_time=1.32)
        self.play(FadeIn(seq), run_time=1.32)
        self.play(FadeIn(plot), run_time=2.42)
        self.play(FadeIn(lines), run_time=1.76)
        self.play(FadeIn(foot), run_time=1.54)
        self.wait(26)
        self.finish()


class S7_Second(C2):
    experiment = "genie3 \u00b7 round 2"

    def construct(self):
        self.header()
        head = T("Design two \u2014 b2x-d12-2", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        meta = T("92 aa \u00b7 an independent scaffold \u00b7 the d12 family", size=19, color=MUTED)
        meta.move_to([0, 1.35, 0])

        row = self.number_row([
            ("0.788", "best fold", GREEN),
            ("0.673", "worst fold", CYAN),
            ("0.29", "pDockQ2", AMBER),
            ("311", "atom pairs", AMBER),
        ], size_big=40, buff=0.85)
        row.move_to([0, 0.1, 0])

        note = T("five of five samples at the designed site", size=19, color=INK)
        note.move_to([0, -1.45, 0])
        note1b = T("three folds pass both legs of the original bar", size=19, color=INK)
        note1b.move_to([0, -1.95, 0])
        note2 = T("interface size is winner-scale \u2014 the champion does not have that",
                  size=18, color=MUTED)
        note2.move_to([0, -2.6, 0])

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(meta), run_time=1.32)
        self.play(FadeIn(row, shift=UP * 0.18), run_time=2.2)
        self.play(FadeIn(note), run_time=1.32)
        self.play(FadeIn(note1b), run_time=1.32)
        self.play(FadeIn(note2), run_time=1.32)
        self.wait(17)
        self.finish()


class S8_Close(C2):
    experiment = "genie3 \u00b7 round 2"

    def construct(self):
        self.header()
        head = T("What stays negative, and what this is", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        b = self.bullets([
            "the same protocol on our own harder epitope stayed negative",
            "a third family scored lower despite larger interfaces",
            "more contact is not more confidence",
            "in-silico evidence only \u2014 no wet-lab data on these designs",
        ], size=20, buff=0.34)
        b.move_to(UP * 0.85).to_edge(LEFT, buff=1.0)

        rule = T("the protocol that found them:", size=19, color=CYAN)
        rule.move_to([0, -1.05, 0])
        proto = T("generate diverse backbones \u00b7 pick by folded spread\nfull-backbone ProteinMPNN \u00b7 keep families that reproduce",
                  size=18, color=INK)
        proto.move_to([0, -1.7, 0])
        ladder = T("if a window opens: d7x-t3-3 first, then the backup ladder",
                   size=18, color=MUTED)
        ladder.move_to([0, -2.55, 0])

        self.play(Write(head), run_time=1.98)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1.21)
            self.wait(2.5)
        self.play(FadeIn(rule), run_time=1.1)
        self.play(FadeIn(proto), run_time=1.32)
        self.play(FadeIn(ladder), run_time=1.32)
        self.wait(17)
        self.finish()


NARRATION = {
    "S1_Title": (
        "After the campaign closed with a negative, the work continued. This video covers the "
        "experiment that produced two promising designs \u2014 and every step that led there."
    ),
    "S2_Calibration": (
        "First, calibration. Anthropic released their full campaign dataset: one hundred and "
        "fifty TNF-alpha designs with wet-lab outcomes. We folded six of them through our own "
        "pipeline, and reproduced their published scores within three hundredths. The data said: "
        "the confidence band at or above zero point eight bound at twenty-six percent; the zero "
        "point six band produced zero binders; and the generator decides more than the filter \u2014 "
        "Genie three made eight of their twenty-three binders; our generator, one of forty. One "
        "warning: two designs that never bound scored higher than every winner."
    ),
    "S3_Genie3": (
        "So the generator changed. Genie three is open source, three hundred and forty-seven "
        "megabytes, and it runs on the twelve-gigabyte card \u2014 sixty-six seconds per design. Eight "
        "designs came out, and all eight engage the designed interface. But the first sequences "
        "were made the model's own way \u2014 a CA-only sequence model \u2014 and the folds stayed quiet: "
        "best at-site fold zero point two four eight, ten samples at zero. Placement solved; the "
        "sequences were the weak link."
    ),
    "S4_Diff": (
        "The comparison against the thirteen released winners named the errors. Winner "
        "sequences are forty-one percent charged; our campaign's were ten \u2014 greasy and "
        "alanine-heavy, a class that does not bind. The winners are one dominant backbone "
        "family \u2014 success converges. And our folded interfaces were half the winners' size. Two "
        "errors, measured: CA-only sequencing, and singletons instead of families."
    ),
    "S5_Fix": (
        "The fix had two moves. Pick backbones by their folded sample spread \u2014 fold first, then "
        "keep the backbone whose samples already land on the designed interface. Then "
        "re-sequence that same folded backbone with the full-backbone ProteinMPNN. Eighteen "
        "variants, every one re-folded: the family spans zero point six three to zero point "
        "eight five, and every variant puts all five samples at the designed site. Fresh "
        "sequences from new seeds reproduced \u2014 nine of ten landed between zero point seven five "
        "and zero point eight five. A control backbone stayed below zero point one nine."
    ),
    "S6_Champion": (
        "Design one: d seven x t three dash three. Sixty-four residues, alanine-rich. Five "
        "independent folds: zero point eight five two, eight three two, eight four two, eight "
        "three seven, and eight four zero \u2014 every fold above zero point eight three, every fold "
        "on the designed interface, cross-protomer, with two hundred and nine atom pairs. The "
        "released, wet-lab-verified binders score zero point eight six to zero point nine one "
        "in this same protocol. The champion sits just below them \u2014 in the band where about a "
        "quarter bound."
    ),
    "S7_Second": (
        "Design two is an independent scaffold: the d twelve family, ninety-two residues. Best "
        "fold zero point seven nine, worst fold zero point six seven, five of five samples at "
        "the designed site \u2014 and interface quality the champion lacks: pDockQ2 up to zero point "
        "two nine, with three hundred and eleven atom pairs buried, winner scale. Three of its "
        "five folds pass both legs of the original bar."
    ),
    "S8_Close": (
        "Discipline kept the rest: the same protocol, pointed at our own harder epitope, stayed "
        "negative; a third family with even larger interfaces scored lower \u2014 more contact is not "
        "more confidence. And the honest frame: this is in-silico evidence only, with no "
        "wet-lab data on these designs. If a submission window opens, the order is ready: the "
        "champion first, then the backup ladder. The protocol that found them is written down: "
        "generate diverse backbones; pick them by folded spread; re-sequence with full-backbone "
        "ProteinMPNN; and keep only families that reproduce."
    ),
}
