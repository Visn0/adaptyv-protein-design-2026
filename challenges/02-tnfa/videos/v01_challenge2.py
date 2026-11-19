"""Video 01 — Challenge 2: the inverted switch (series overview).

Covers: the ask, the biology and physics of the inverted pH switch, why the
problem is hard, the strategy, and the campaign result that this series
documents experiment by experiment.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


# ----------------------------------------------------------------- scenes
class S1_Title(C2):
    def construct(self):
        k = T("VIDEO 01 / 12  ·  SERIES OVERVIEW", size=20, color=CYAN, weight=BOLD)
        t = T("Challenge 2: the inverted switch", size=52, color=INK, weight=BOLD)
        s = T("A TNF-\u03b1 binder that holds at pH 7.4 and releases at pH 6.0.\n"
              "How the campaign attacked it \u2014 and what it found.", size=24, color=MUTED)
        f = T("Anthropic \u00d7 Adaptyv 2026  ·  challenges/02-tnfa", size=18, color=DIM)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        g.move_to(ORIGIN)
        f.next_to(g, DOWN, buff=0.9).align_to(g, LEFT)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.39)
        self.play(Write(t), run_time=2.78)
        self.wait(0.3)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.74)
        self.play(FadeIn(f), run_time=1.04)
        self.wait(5.6)
        self.finish()


class S2_Ask(C2):
    def construct(self):
        self.header("the ask")
        head = T("Three ranked objectives", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        def obj(n, title, sub, col):
            t1 = T(f"{n}  {title}", size=24, color=col, weight=BOLD)
            t2 = T(sub, size=18, color=MUTED)
            c = self.card(6.0, 1.45, stroke=col)
            g = VGroup(t1, t2).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
            g.move_to(c).align_to(c, LEFT).shift(RIGHT * 0.30)
            return VGroup(c, g)

        o1 = obj("1", "pH-selective binding \u2014 inverted", "bind at pH 7.4  ·  release at pH 6.0", CYAN)
        o2 = obj("2", "mouse cross-reactivity", "tested at pH 7.4", BLUE)
        o3 = obj("3", "affinity", "for human TNF-\u03b1", PINK)
        col = VGroup(o1, o2, o3).arrange(DOWN, buff=0.30)
        col.move_to(LEFT * 3.4 + DOWN * 0.35)

        # right: target card with a trimer glyph
        tc = self.card(5.4, 5.3)
        tc.move_to(RIGHT * 3.65 + DOWN * 0.25)
        tt = T("target  ·  1TNF", size=20, color=BLUE, weight=BOLD)
        tri = VGroup(
            Circle(radius=0.52, stroke_color=BLUE, stroke_width=2,
                   fill_color=BLUE, fill_opacity=0.08).move_to(UP * 0.52),
            Circle(radius=0.52, stroke_color=BLUE, stroke_width=2,
                   fill_color=BLUE, fill_opacity=0.08).move_to(DOWN * 0.30 + LEFT * 0.45),
            Circle(radius=0.52, stroke_color=BLUE, stroke_width=2,
                   fill_color=BLUE, fill_opacity=0.08).move_to(DOWN * 0.30 + RIGHT * 0.45),
        )
        seam = DashedLine(UP * 0.98 + RIGHT * 0.23, DOWN * 0.58 + RIGHT * 0.23,
                          color=AMBER, stroke_width=2, dash_length=0.07)
        tri_grp = VGroup(tri, seam)
        seam_lab = T("epitope: the receptor-binding site\nbetween two subunits", size=15, color=AMBER)
        note = T("soluble trimer \u00b7 the drug antibodies\nadalimumab and infliximab block this seam",
                 size=15, color=DIM)
        inner = VGroup(tt, tri_grp, seam_lab, note).arrange(DOWN, buff=0.42)
        inner.move_to(tc)

        self.play(Write(head), run_time=2.2)
        for o in (o1, o2, o3):
            self.play(FadeIn(o, shift=RIGHT * 0.25), run_time=1.54)
            self.wait(2.5)
        self.play(FadeIn(tc), run_time=1.54)
        self.play(FadeIn(tri, scale=0.9), run_time=1.98)
        self.play(Create(seam), FadeIn(seam_lab), run_time=1.98)
        self.play(FadeIn(note), run_time=1.1)
        self.wait(21.8)
        self.finish()


class S3_Mechanism(C2):
    def construct(self):
        self.header("the physics")

        def panel(x, ph, sub):
            p = self.card(6.1, 4.0).move_to([x, 0.15, 0])
            lab = T(ph, size=22, color=CYAN, weight=BOLD)
            lab.move_to(p.get_corner(UL) + RIGHT * 1.35 + DOWN * 0.42)
            sub_lab = T(sub, size=16, color=DIM)
            sub_lab.next_to(lab, RIGHT, buff=0.35)
            return p, lab, sub_lab

        pl, l1, s1 = panel(-3.6, "pH 7.4", "blood")
        pr, l2, s2 = panel(3.6, "pH 6.0", "recycling compartment")

        def scene_blocks(p, protonated, released=False):
            pc = p.get_center()
            tgt = RoundedRectangle(corner_radius=0.12, width=1.75, height=1.75,
                                   stroke_color=BLUE, stroke_width=2,
                                   fill_color=BLUE, fill_opacity=0.10)
            tgt.move_to(pc + RIGHT * 1.55)
            tgt_lab = T("TNF-\u03b1", size=18, color=BLUE).move_to(tgt)
            cation = Circle(radius=0.30, stroke_color=AMBER, stroke_width=2,
                            fill_color=AMBER, fill_opacity=0.15)
            cation.move_to(tgt.get_left() + LEFT * 0.30)
            cation_lab = T("+", size=20, color=AMBER, weight=BOLD).move_to(cation)
            cat = VGroup(cation, cation_lab)
            binder = RoundedRectangle(corner_radius=0.12, width=1.75, height=1.75,
                                      stroke_color=PINK, stroke_width=2,
                                      fill_color=PINK, fill_opacity=0.10)
            binder.move_to(pc + LEFT * (1.40 + (0.70 if released else 0.0)))
            blab = T("binder", size=18, color=PINK).move_to(binder)
            hcol = RED if protonated else INK
            his = Circle(radius=0.30, stroke_color=hcol, stroke_width=2,
                         fill_color=hcol, fill_opacity=0.15 if protonated else 0.05)
            his.move_to(binder.get_right() + RIGHT * 0.30)
            his_lab = T("+" if protonated else "0", size=20, color=hcol, weight=BOLD).move_to(his)
            his_v = VGroup(his, his_lab)
            his_name = T("His", size=16, color=hcol).next_to(his_v, DOWN, buff=0.10)
            return tgt, tgt_lab, cat, binder, blab, his_v, his_name

        parts_l = scene_blocks(pl, False)
        parts_r = scene_blocks(pr, True, released=True)
        gl = VGroup(*parts_l)
        gr = VGroup(*parts_r)
        cat1, his1 = parts_l[2], parts_l[5]
        cat2, his2 = parts_r[2], parts_r[5]

        bond = DashedLine(his1.get_center(), cat1.get_center(),
                          color=GREEN, stroke_width=2.5, dash_length=0.09)
        ok = self.chip("holds \u2713", GREEN, size=17)
        ok.next_to(pl, DOWN, buff=0.22)

        gap_c = (his2.get_right() + cat2.get_left()) / 2
        rep1 = Arrow(gap_c, gap_c + LEFT * 0.45, color=RED, buff=0,
                     stroke_width=3, tip_length=0.18)
        rep2 = Arrow(gap_c, gap_c + RIGHT * 0.45, color=RED, buff=0,
                     stroke_width=3, tip_length=0.18)
        no = self.chip("releases", RED, size=17)
        no.next_to(pr, DOWN, buff=0.22)

        top = T("histidine is the switch", size=30, color=INK, weight=BOLD)
        top.to_edge(UP, buff=1.05)
        bot = T("His pKa \u2248 6.0\u20136.5  \u00b7  neutral at 7.4, +1 below \u2014 "
                "against a target cation (Arg/Lys)\n"
                "FcRn, nature's version: holds antibodies at 7.4, releases at 6.0",
                size=18, color=MUTED)
        bot.to_edge(DOWN, buff=0.5)

        self.play(Write(top), run_time=1.98)
        self.play(FadeIn(pl), FadeIn(l1), FadeIn(s1), run_time=1.54)
        self.play(FadeIn(gl, shift=RIGHT * 0.2), run_time=2.2)
        self.play(Create(bond), run_time=1.54)
        self.play(FadeIn(ok), run_time=1.1)
        self.wait(1.1)
        self.play(FadeIn(pr), FadeIn(l2), FadeIn(s2), run_time=1.54)
        self.play(FadeIn(gr, shift=LEFT * 0.2), run_time=2.2)
        self.play(GrowArrow(rep1), GrowArrow(rep2), run_time=1.76)
        self.play(FadeIn(no), run_time=1.1)
        self.play(FadeIn(bot), run_time=1.54)
        self.wait(30.2)
        self.finish()


class S4_Hard(C2):
    def construct(self):
        self.header("why it is hard")
        head = T("Three hard parts", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        def card(title, lines, col):
            t1 = T(title, size=22, color=col, weight=BOLD)
            t2 = T(lines, size=18, color=MUTED)
            c = self.card(4.15, 2.6, stroke=col)
            g = VGroup(t1, t2).arrange(DOWN, buff=0.3)
            g.move_to(c)
            return VGroup(c, g)

        c1 = card("shallow groove", "the epitope sits between\ntwo subunits \u2014 a harder\nsurface to grip", BLUE)
        c2 = card("one site is weak", "\u2248 1.4 log units per site;\na useful switch needs\n2\u20133 pairs", AMBER)
        c3 = card("sample size decides", "successful campaigns screened\ntens of thousands \u2014 dozens\nof designs \u2248 zero", PINK)
        row = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.42).shift(UP * 0.2)

        bar = T("so the acceptance bar is pre-registered, before any spend:", size=20, color=MUTED)
        chip = self.chip("ipSAE \u2265 0.6   AND   pDockQ2 \u2265 0.23", CYAN, size=22)
        bot = VGroup(bar, chip).arrange(DOWN, buff=0.3).shift(DOWN * 2.3)

        self.play(Write(head), run_time=1.98)
        for c in (c1, c2, c3):
            self.play(FadeIn(c, shift=UP * 0.2), run_time=1.43)
            self.wait(2.5)
        self.play(FadeIn(bot, shift=UP * 0.15), run_time=1.76)
        self.wait(12.5)
        self.finish()


class S5_Plan(C2):
    def construct(self):
        self.header("the strategy")
        head = T("Anchor the switch on the target", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        strip, boxes = self.step_strip(
            ["anchors", "switch\nmotif", "RFdiffusion", "coverage",
             "MPNN\n+ AF2", "linkage\nscore", "submission"],
            colors=[BORDER, BORDER, VIOLET, BORDER, VIOLET, BORDER, BORDER],
            size=15,
        )
        strip.move_to(UP * 1.15)

        ext = T("violet = external step, needs a CUDA GPU", size=16, color=VIOLET)
        ext.next_to(strip, DOWN, buff=0.35).to_edge(RIGHT, buff=1.0)

        b = self.bullets([
            "the target is already folded and stable \u2014 it absorbs the electrostatic cost",
            "three binder histidines, one aimed at each cation of the target triad",
            "filter shapes for switch reachability before spending compute on sequences",
            "fold the complexes, score them, and validate the scorer on controls",
        ], size=20, buff=0.34)
        b.next_to(strip, DOWN, buff=1.15).to_edge(LEFT, buff=1.0)

        self.play(Write(head), run_time=1.98)
        self.play(LaggedStart(*[FadeIn(x) for x in boxes], lag_ratio=0.18), run_time=3.52)
        self.play(FadeIn(ext), run_time=1.1)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1.21)
            self.wait(2.5)
        self.wait(11.9)
        self.finish()


class S6_Timeline(C2):
    def construct(self):
        self.header("the campaign")
        head = T("Four moves, one verdict", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        def row(name, sub, detail, chip_txt, chip_col, y):
            n = T(name, size=24, color=CYAN, weight=BOLD)
            n.move_to([-5.85, y, 0])
            txt = VGroup(T(sub, size=15, color=MUTED),
                         T(detail, size=15, color=INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            txt.next_to(n, RIGHT, buff=0.45)
            ch = self.chip(chip_txt, chip_col, size=15)
            ch.move_to([5.15, y, 0])
            return VGroup(n, txt, ch)

        rows = VGroup(
            row("X1", "BoltzGen \u00b7 Tamarind \u00b7 150 designs",
                "three hotspot sets, refold on", "0 docked", RED, 2.1),
            row("X2", "RFdiffusion3 \u00b7 Tamarind \u00b7 72 complexes",
                "58/72 span the groove across protomers", "1 of 5 samples passed", AMBER, 0.85),
            row("W2", "8 shortlist folds \u00b7 local GPU",
                "human + mouse, 5 samples each", "best ipSAE 0.733", AMBER, -0.40),
            row("X3", "4 patches \u00b7 168 designs \u00b7 local GPU",
                "RBS, switch trio, groove, fold-preferred patch", "0 at the designed site", RED, -1.65),
        )
        div = Line([-6.2, -2.30, 0], [6.2, -2.30, 0], color=BORDER, stroke_width=2)
        b1 = T("18 designs folded \u00b7 90 predicted samples", size=20, color=INK)
        b1.move_to([0, -2.68, 0])
        b2 = T("0 samples clear the bar AND sit on the designed epitope",
               size=22, color=RED, weight=BOLD)
        b2.move_to([0, -3.16, 0])
        chip = self.chip("campaign closed \u00b7 no submission", MUTED, size=18)
        chip.move_to([0, -3.66, 0])

        self.play(Write(head), run_time=1.98)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.25), run_time=1.1)
            self.wait(2.5)
        self.play(Create(div), run_time=1.1)
        self.play(FadeIn(b1), run_time=1.1)
        self.play(FadeIn(b2, shift=UP * 0.12), run_time=1.54)
        self.play(FadeIn(chip), run_time=1.1)
        self.wait(21.2)
        self.finish()


class S7_Lessons(C2):
    def construct(self):
        l1 = T("A docking score is not evidence", size=44, color=INK, weight=BOLD)
        l2 = T("about a designed interface.", size=44, color=INK, weight=BOLD)
        l3 = T("Check the contacts against the designed residues \u2014\non both protomers.",
               size=24, color=CYAN)
        g = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        g.move_to(UP * 0.5).to_edge(LEFT, buff=1.0)

        f1 = T("The campaign's value is its method and an honest negative.", size=20, color=MUTED)
        f2 = T("The rest of this series: one video per experiment \u2014 steps, tools, reasons.",
               size=20, color=MUTED)
        foot = VGroup(f1, f2).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        foot.next_to(g, DOWN, buff=1.2).to_edge(LEFT, buff=1.0)

        self.play(Write(l1), run_time=2.64)
        self.play(Write(l2), run_time=2.64)
        self.wait(0.1)
        self.play(FadeIn(l3, shift=UP * 0.15), run_time=1.98)
        self.play(FadeIn(foot), run_time=1.76)
        self.wait(20.2)
        self.finish()


# ----------------------------------------------------------------- narration
NARRATION = {
    "S1_Title": (
        "This is the story of Challenge Two of the Anthropic and Adaptyv protein design "
        "competition. The task: a binder for human TNF alpha that holds its target at blood pH, "
        "and releases it inside the cell."
    ),
    "S2_Ask": (
        "The challenge asks for three things, in ranked order. First, pH-selective binding, with "
        "the switch inverted: the binder must hold human TNF alpha at pH 7.4, the pH of blood, "
        "and release it at pH 6.0, the pH of the recycling compartment inside a cell. Second, "
        "cross-reactivity with the mouse protein at pH 7.4. Third, affinity. The target is the "
        "soluble TNF alpha trimer, PDB 1TNF. The recommended epitope is the receptor-binding "
        "site, at the seam between two subunits: the exact spot where the natural receptor "
        "docks, and where the antibody drugs adalimumab and infliximab neutralise the target."
    ),
    "S3_Mechanism": (
        "The switch runs in the opposite direction to Challenge One, and physics decides the "
        "design. Histidine is the only residue that changes charge inside the 6.0 to 7.4 window. "
        "Place a histidine opposite a positive group on the target: an arginine or a lysine. "
        "At pH 7.4 the histidine is neutral. It packs against the cation, and the binder holds. "
        "At pH 6.0 the histidine gains a proton and becomes positive. Equal charges repel, the "
        "contact breaks, and the binder lets go. Nature already runs this exact switch: the "
        "recycling receptor FcRn holds antibodies at pH 7.4 and releases them at 6.0, which is "
        "how antibody drugs survive in circulation for weeks."
    ),
    "S4_Hard": (
        "Three things make this hard. The epitope is a shallow groove between two subunits, a "
        "harder surface to grip than a flat domain face. A single switching pair is weak: the "
        "linkage ceiling is about one and a half log units per site, so a useful switch needs "
        "two or three pairs. And sample size decides the outcome. Campaigns that succeeded "
        "screened tens of thousands of sequences; a run of a few dozen expects roughly zero "
        "successes."
    ),
    "S5_Plan": (
        "The strategy came from the strongest published thinking. Anchor the switch on the "
        "target, not on the binder: the target is already folded and stable, so it absorbs the "
        "electrostatic cost. Aim three binder histidines at a triangle of positive residues on "
        "the target. Filter generated shapes for switch reachability before spending compute on "
        "sequence design. Then fold the complexes and score them honestly, with controls. This "
        "repository's pipeline covers every step after structure generation; the generators "
        "themselves need a GPU."
    ),
    "S6_Timeline": (
        "The campaign ran in four moves. X one: one hundred and fifty BoltzGen designs across "
        "three hotspot sets. Zero docked. X two: RFdiffusion3 placed binders in the drug groove, "
        "fifty-eight of seventy-two spanning two protomers, and one fold cleared the bar in one "
        "of five samples. W two: the eight best designs, re-folded on the local GPU. One reached "
        "ipSAE zero point seven three. X three: three more sites, then a fourth patch \u2014 and the "
        "finding that closed the campaign. Eighteen designs were folded, ninety predicted "
        "samples. Not one sample both cleared the acceptance bar and sat on the epitope it was "
        "designed for."
    ),
    "S7_Lessons": (
        "The lesson that carries forward is worth more than the designs. A docking score "
        "answers: is there an interface? It does not answer: is the interface where the design "
        "put it. Selection must require the score and the site together, checked against the "
        "designed residues, on both protomers. The campaign closed with no submission, on the "
        "pre-registered stop rule. The rest of this series walks through every experiment, one "
        "video each: the steps, the tools, and the reasons behind them."
    ),
}
