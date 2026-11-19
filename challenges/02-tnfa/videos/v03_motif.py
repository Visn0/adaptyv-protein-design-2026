"""Video 03 — c2-switch-motif: where the binder histidines go.

The cation triad, the 5 angstrom standoff, and the motif file that conditions
the backbone generator.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa: F401,F403


class S1_Title(C2):
    experiment = "c2-switch-motif"

    def construct(self):
        k = T("VIDEO 03 / 12  ·  EXPERIMENT", size=20, color=CYAN, weight=BOLD)
        t = T("c2-switch-motif", size=56, color=INK, weight=BOLD)
        s = T("Where the binder histidines go \u2014 the geometry that\nconditions the backbone generator.",
              size=24, color=MUTED)
        g = VGroup(k, t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        g.move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.2), run_time=1.43)
        self.play(Write(t), run_time=2.5)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.78)
        self.wait(5.6)
        self.finish()


class S2_Cations(C2):
    experiment = "c2-switch-motif"

    def construct(self):
        self.header()
        head = T("The switch needs positive partners", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        def cat(name, res, chain, y):
            t1 = T(name, size=24, color=AMBER, weight=BOLD)
            t2 = T(f"{res}  ·  chain {chain}", size=17, color=MUTED)
            c = self.card(3.6, 1.4, stroke=AMBER)
            g = VGroup(t1, t2).arrange(DOWN, buff=0.12).move_to(c)
            grp = VGroup(c, g).move_to([0, y, 0])
            return grp

        triad = VGroup(
            cat("A103", "ARG", "A", 0.95),
            cat("B112", "LYS", "B", -0.65),
            cat("B103", "ARG", "B", -2.25),
        )
        triad.move_to(LEFT * 3.9 + DOWN * 0.35)

        lbl = T("cation triad", size=20, color=AMBER, weight=BOLD)
        lbl.next_to(triad, UP, buff=0.4)

        right = self.bullets([
            "linkage: binding must release net protons",
            "the protonated His must be uncomfortable bound",
            "a target carboxylate runs the switch backwards",
            "one protomer carries one cation \u2014 a two-subunit site",
        ], size=20, buff=0.4)
        right.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        right.move_to([2.75, -0.3, 0])

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(lbl), run_time=1.1)
        for c in triad:
            self.play(FadeIn(c, shift=RIGHT * 0.2), run_time=1.1)
        for ln in right:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1.1)
        self.wait(20.4)
        self.finish()


class S3_Geometry(C2):
    experiment = "c2-switch-motif"

    def construct(self):
        self.header()
        head = T("The 5 \u00c5 standoff", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        # left: small diagram — surface, cation, outward normal, His at standoff
        surf = Arc(radius=2.6, start_angle=-60 * DEGREES, angle=120 * DEGREES,
                   color=BORDER, stroke_width=3).move_to(DOWN * 2.6)
        cat = VGroup(
            Circle(radius=0.26, stroke_color=AMBER, stroke_width=2,
                   fill_color=AMBER, fill_opacity=0.15),
            T("+", size=18, color=AMBER, weight=BOLD).move_to([0, 0, 0]),
        )
        cat.move_to(surf.point_from_proportion(0.5))
        his = Circle(radius=0.26, stroke_color=INK, stroke_width=2, fill_opacity=0.05)
        his.move_to(cat.get_center() + UP * 1.5)
        his_lab = T("His", size=16, color=MUTED).next_to(his, RIGHT, buff=0.15)
        normal = Arrow(cat.get_center(), his.get_center() + UP * 0.45,
                       buff=0.32, stroke_width=2.4, color=CYAN, tip_length=0.16)
        dist = DoubleArrow(cat.get_center(), his.get_center(), buff=0.3,
                           stroke_width=1.8, color=CYAN, tip_length=0.12)
        dist_lab = T("5.0 \u00c5", size=17, color=CYAN).next_to(dist, LEFT, buff=0.12)
        diag = VGroup(surf, cat, normal, his, his_lab, dist, dist_lab)
        diag.move_to(LEFT * 3.9 + DOWN * 0.35)

        b = self.bullets([
            "place the His ring along the outward normal",
            "5 \u00c5: a neutral imidazole can hydrogen-bond;",
            "a protonated one feels real repulsion",
            "step outward 0.25 \u00c5 at a time until every",
            "target atom clears by \u2265 3.6 \u00c5",
        ], size=18, buff=0.36)
        b.arrange(DOWN, aligned_edge=LEFT, buff=0.36)
        b.move_to([2.85, -0.2, 0])

        self.play(Write(head), run_time=1.81)
        self.play(FadeIn(diag), run_time=2.01)
        for ln in b:
            self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=1)
            self.wait(2.5)
        self.wait(8.4)
        self.finish()


class S4_Result(C2):
    experiment = "c2-switch-motif"

    def construct(self):
        self.header()
        head = T("Result \u2014 the motif", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        row = self.number_row([
            ("4.57", "clearance \u00c5 \u00b7 A103", CYAN),
            ("5.00", "clearance \u00c5 \u00b7 B112", CYAN),
            ("3.79", "clearance \u00c5 \u00b7 B103", CYAN),
        ], size_big=46, buff=1.0)
        row.move_to(UP * 0.75)

        span = T("placed-histidine span  20.23 \u00c5", size=24, color=AMBER, weight=BOLD)
        span2 = T("cation CA\u2013CA separations 8.7\u201312.9 \u00c5", size=20, color=MUTED)
        s = VGroup(span, span2).arrange(DOWN, buff=0.25).move_to(DOWN * 0.75)

        note = T("one face of a 70\u201395 residue binder covers the span", size=20, color=MUTED)
        note.move_to(DOWN * 2.1)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(row, shift=UP * 0.2), run_time=2.2)
        self.play(FadeIn(s, shift=UP * 0.15), run_time=1.76)
        self.play(FadeIn(note), run_time=1.32)
        self.wait(15.6)
        self.finish()


class S5_Output(C2):
    experiment = "c2-switch-motif"

    def construct(self):
        self.header()
        head = T("The motif feeds the generator", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        chips = VGroup(
            self.chip("switch_motif.json", CYAN, size=20),
            self.chip("pseudo-atom PDB", CYAN, size=20),
            self.chip("motif_sites.csv", CYAN, size=20),
        ).arrange(RIGHT, buff=0.5).move_to(UP * 0.5)

        hs = T("hotspots \u2192 RFdiffusion:   A103, B112, B103", size=26, color=VIOLET, weight=BOLD)
        hs.move_to(DOWN * 0.8)
        note = T("the generator must build a binder face that can reach all three sites",
                 size=20, color=MUTED)
        note.move_to(DOWN * 1.8)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(chips, shift=UP * 0.15), run_time=1.98)
        self.play(FadeIn(hs, shift=UP * 0.12), run_time=1.76)
        self.play(FadeIn(note), run_time=1.32)
        self.wait(6.5)
        self.finish()


class S6_Caveat(C2):
    experiment = "c2-switch-motif"

    def construct(self):
        self.header()
        head = T("Recorded before the run", size=36, color=INK, weight=BOLD)
        head.to_edge(UP, buff=1.0)

        c = self.card(11.4, 2.4, stroke=AMBER)
        t1 = T("the local pair is strongly positive \u2014", size=22, color=INK)
        t2 = T("but carboxylates in the wider neighbourhood partially screen the patch",
               size=22, color=INK)
        t3 = T("most likely source of switch attenuation \u00b7 known up front", size=18, color=AMBER)
        g = VGroup(t1, t2, t3).arrange(DOWN, buff=0.25).move_to(c)
        grp = VGroup(c, g).move_to(UP * 0.3)

        foot = T("a known weakness recorded before any design ran is a strength, not a flaw",
                 size=20, color=MUTED)
        foot.next_to(grp, DOWN, buff=0.8)

        self.play(Write(head), run_time=1.98)
        self.play(FadeIn(grp, shift=UP * 0.15), run_time=1.98)
        self.play(FadeIn(foot), run_time=1.54)
        self.wait(9.5)
        self.finish()


NARRATION = {
    "S1_Title": (
        "Experiment three: c2-switch-motif. This stage decides where the binder histidines "
        "must sit, and writes the geometry that the backbone generator will be conditioned on."
    ),
    "S2_Cations": (
        "The switch needs positive partners. Linkage theory says binding must release net "
        "protons, which needs a pKa that drops on binding \u2014 so the protonated histidine must be "
        "uncomfortable in the bound state. Facing a target carboxylate would run the switch "
        "backwards. The scan therefore points at a triangle of positive residues: A103 "
        "arginine, B112 lysine, and B103 arginine. One protomer carries one of the three, so "
        "the site spans two subunits."
    ),
    "S3_Geometry": (
        "For each cation the stage computes the outward solvent direction, from the local mass "
        "centre to the tip atom, and places an ideal histidine ring at a five angstrom "
        "standoff. Five angstroms is the design choice: close enough for a neutral imidazole to "
        "hydrogen-bond, close enough for a protonated one to carry real repulsion. The ring "
        "steps outward in quarter-angstrom increments until every target atom clears by at "
        "least three point six angstroms."
    ),
    "S4_Result": (
        "The result: all three sites clear at the nominal standoff, with clearances of four "
        "point five seven, five point zero, and three point seven nine angstroms. The cation "
        "separations run from eight point seven to twelve point nine angstroms, and the placed "
        "histidines span twenty point two three angstroms \u2014 one face of a seventy to "
        "ninety-five residue binder can cover that."
    ),
    "S5_Output": (
        "The stage writes switch_motif.json, a pseudo-atom PDB, and the site table, and passes "
        "the hotspot string \u2014 A103, B112, B103 \u2014 to the generator."
    ),
    "S6_Caveat": (
        "One caveat was recorded before any design ran: the local pair is strongly positive, "
        "but carboxylates in the wider neighbourhood partially screen the cationic patch. That "
        "is the most likely source of switch attenuation, and it was known up front."
    ),
}
