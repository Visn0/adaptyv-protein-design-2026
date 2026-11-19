#!/usr/bin/env python
"""Generate challenges/03-glp1r/lineage.json — the challenge-3 campaign model.

Mirrors the shape of challenges/02-tnfa/lineage.json (the field names
predate the vocabulary: `experiments[]` holds the CAMPAIGNS, each entry's
`chapters[]` holds the EXPERIMENTS). Data comes from the campaign tables
that this repository and ~/c3-work already hold:

  - the fold screen table (~/c3-work/folds-screen.csv) — one row per sample
  - the campaign candidate table (c3-candidates.csv) — sequences + composite
  - the fold YAMLs (~/c3-work/folds/c3-*.yaml, e1*.yaml, c2-*.yaml) — sequences
  - the campaign READMEs — the chapter narratives

Run:  .venv/bin/python challenges/03-glp1r/viewers/scripts/make_lineage_json.py
"""
from __future__ import annotations

import csv
import json
import pathlib
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[4]
CH = REPO / "challenges" / "03-glp1r"
FOLDS = pathlib.Path.home() / "c3-work" / "folds"
SCREEN = pathlib.Path.home() / "c3-work" / "folds-screen.csv"
GATE = pathlib.Path.home() / "c3-work" / "c8-agonism" / "gate-summary-all.csv"
SELECTION = pathlib.Path.home() / "c3-work" / "c8-agonism" / "selection-all.csv"
OUT = CH / "lineage.json"


def read_screen():
    rows = list(csv.DictReader(open(SCREEN)))
    by_design = defaultdict(list)
    for r in rows:
        by_design[r["design"]].append(r)
    return by_design


def read_sequences():
    seqs = {}
    for y in FOLDS.glob("*.yaml"):
        txt = y.read_text().splitlines()
        for i, l in enumerate(txt):
            if l.strip() == "id: A":
                seqs[y.stem] = txt[i + 1].split("sequence:")[1].strip()
                break
    return seqs


def load_gate():
    gate = {}
    if GATE.exists():
        for r in csv.DictReader(open(GATE)):
            gate[r["design"]] = r
    return gate


def load_totals():
    totals = {}
    if SELECTION.exists():
        for r in csv.DictReader(open(SELECTION)):
            totals[r["design"]] = float(r["total"])
    return totals


def best_of(rows):
    return max(rows, key=lambda r: float(r["ipsae"]))


def protein(name, rows, seqs, gate):
    b = best_of(rows)
    two_domain = "two-domain" in (b.get("verdict") or "")
    g = gate.get(name)
    activation = ""
    if g:
        activation = f"{g['met']}/6 d{float(g['depth']):.1f}"
        if int(g["met"]) >= 6:
            activation += f" pose {g['deep_samples']}/{g['samples']}"
    p = {
        "design": name,
        "sequence": seqs.get(name, ""),
        "phase": None,
        "note": f"sample {b['sample']}" + (" · two-domain HIT" if two_domain else ""),
        "human": None,
        "mouse": None,
        "ph": None,
        "ipsae_min": float(b["ipsae"]),
        "pdockq2": float(b["pdockq2"]),
        "iptm": float(b["iptm_af"]) if b.get("iptm_af") else None,
        "activation": activation,
        "groove_site": f"{b.get('groove_hits', 0)}/6",
        "tm_site": f"{b.get('tm_hits', 0)}/4",
        "ecl3_site": f"{b.get('ecl3_hits', 0)}/8",
    }
    return p


def main():
    by_design = read_screen()
    seqs = read_sequences()
    gate = load_gate()
    totals = load_totals()

    def viewer_for(names):
        """Every design of the campaign, best (by the selection total) first."""
        return sorted(names, key=lambda n: -totals.get(n, 0.0))

    c1_names = sorted(n for n in by_design if n.startswith(("e1-", "e1b-", "e1b2-")))
    c2_names = sorted(n for n in by_design if n.startswith("c2-run"))
    c3_names = sorted(n for n in by_design if n.startswith("c3-"))
    c5_names = sorted(n for n in by_design if n.startswith("c5-"))
    c6_names = sorted(n for n in by_design if n.startswith("c6-"))
    c7_names = sorted(n for n in by_design if n.startswith("c7-"))
    c8_names = sorted(n for n in by_design if n.startswith("c8-"))
    c9_names = sorted(n for n in by_design if n.startswith("c9-"))
    c12m_names = sorted(n for n in by_design if n.startswith("c12-mpnn-"))
    c12_names = sorted(n for n in by_design
                       if n.startswith("c12-") and not n.startswith("c12-mpnn-"))
    c13_names = sorted(n for n in by_design if n.startswith("c13-"))
    c14_names = sorted(n for n in by_design if n.startswith("c14-"))

    def phase_for(name):
        if name.startswith("e1b2-"):
            return "e1b2"
        if name.startswith("e1b-"):
            return "e1b"
        if name.startswith("e1-"):
            return "e1"
        if name.startswith("c2-run2"):
            return "run2"
        if name.startswith(("c2-run3", "c2-run4")):
            return "sweep"
        if name.startswith("c3-boltz"):
            return "b1"
        if name.startswith("c3-jun"):
            return "b2"
        if name.startswith("c3-j2"):
            return "scale"
        if name.startswith("c3-j3"):
            return "c4"
        if name.startswith("c5-"):
            return "run"
        if name.startswith("c6-"):
            return "resequencing"
        if name.startswith("c7-"):
            return "long"
        if name.startswith("c8-"):
            return "generation"
        if name.startswith("c9-"):
            return "resequencing"
        if name.startswith("c12-mpnn-"):
            return "resequencing"
        if name.startswith("c12-"):
            return "generation"
        if name.startswith("c13-"):
            return "junction"
        if name.startswith("c14-"):
            return "short"
        return None

    def proteins_for(names, phase):
        out = []
        for n in names:
            p = protein(n, by_design[n], seqs, gate)
            p["phase"] = phase_for(n) or phase
            out.append(p)
        return out

    def hits(names):
        n = 0
        for name in names:
            for r in by_design[name]:
                if "two-domain" in r["verdict"]:
                    n += 1
        return n

    experiments = [
        {
            "id": "c1-two-domain",
            "title": "C1 campaign — RFdiffusion3 mini-proteins",
            "date": "2026-10-18",
            "verdict": "partial",
            "best": True,
            "scores": {},
            "summary": (f"{len(c1_names)} designs folded, {hits(c1_names)} two-domain samples. "
                        "The reach across groove and junction exists; activation stays unproven."),
            "goal": ("Design mini-proteins that bind the GLP1R extracellular domain AND the "
                     "ECD-TMD junction — the pose that activation needs."),
            "goal_extra": [
                "Answers: does a de-novo mini-protein reach both sub-sites at once?",
                "Answers: which hotspot set gives the best two-domain rate?",
            ],
            "verdict_detail": ("Junction-only hotspots beat groove+junction for two-domain reach "
                               "(25% vs 14%). Best design e1-r0025 spans groove, junction, TM top "
                               "and ECL3."),
            "chapters": [
                {"id": "e1", "title": "E1 — groove + junction hotspots", "date": "2026-10-18",
                 "tools": ["RFdiffusion3", "Boltz-2", "IPSAE"],
                 "text": "43 backbones generated against groove and junction hotspots, co-folded "
                         "against the full 409-residue construct.",
                 "steps": ["Generate with RFD3 on the ECD+junction target",
                           "Co-fold every design with Boltz-2",
                           "Screen each sample for groove, junction, TM-top and ECL3 contacts"],
                 "outcome": "6 of 43 designs two-domain.", "viewer": []},
                {"id": "e1b", "title": "E1b — junction-only hotspots", "date": "2026-10-18",
                 "tools": ["RFdiffusion3", "Boltz-2", "IPSAE"],
                 "text": "60 backbones against the junction alone — the configuration the campaign "
                         "kept.",
                 "steps": ["Generate with junction-only hotspots", "Co-fold and screen as in E1"],
                 "outcome": "10 of 60 two-domain — the better rate.", "viewer": []},
                {"id": "e1b2", "title": "E1b2 — the junction repeat", "date": "2026-10-19",
                 "tools": ["RFdiffusion3", "Boltz-2", "IPSAE"],
                 "text": "80 more junction-only backbones to test the rate.",
                 "steps": ["Repeat E1b at larger sample size"],
                 "outcome": "20 of 80 two-domain (25%).", "viewer": []},
                {"id": "outcome", "title": "Outcome — reach proven, activation open",
                 "date": "2026-10-19", "tools": [],
                 "text": "The campaign closed with the best pose recorded and the activation "
                         "question handed to the peptide campaigns.",
                 "steps": ["Rank by the composite score", "Record learnings"],
                 "outcome": "Campaign complete. Best: e1-r0025 (ipSAE 0.933).", "viewer": []},
            ],
            "proteins": proteins_for(c1_names, "e1"),
            "viewer": viewer_for(c1_names),
        },
        {
            "id": "c2-peptide-agonists",
            "title": "C2 campaign — EvoBind cyclic peptides",
            "date": "2026-10-19",
            "verdict": "promising",
            "best": False,
            "scores": {},
            "summary": (f"{len(c2_names)} designs folded. The length sweep: 15 aa is the sweet "
                        "spot (3 hits, ipSAE 0.83-0.88); 12 aa and 20 aa produced none."),
            "goal": ("Cyclic peptides at the orthosteric site — the modality whose published "
                     "designs activated GLP1R in cAMP assays."),
            "goal_extra": [
                "Answers: which peptide length engages the groove+junction?",
                "Answers: does an independent peptide tool reach the site at all?",
            ],
            "verdict_detail": ("Three 15-aa peptides in the submission band; the 12-aa and 20-aa "
                               "runs produced no two-domain designs."),
            "chapters": [
                {"id": "run1", "title": "Run 1 — 15 aa linear", "date": "2026-10-19",
                 "tools": ["EvoBind", "Boltz-2", "IPSAE"],
                 "text": "EvoBind against the 207-residue fragment, 300 iterations, converged.",
                 "steps": ["Fetch the MSA", "Run EvoBind", "Extract converged designs",
                           "Co-fold and screen"],
                 "outcome": "Best iteration 206; the converged family is in the submission.",
                 "viewer": []},
                {"id": "run2", "title": "Run 2 — 15 aa cyclic", "date": "2026-10-19",
                 "tools": ["EvoBind", "Boltz-2", "IPSAE"],
                 "text": "The cyclic variant at the same length.",
                 "steps": ["Run EvoBind with cyclic offset", "Screen as before"],
                 "outcome": "Converged to the ALAWCVNFIEDRAPS family; one design in the pool.",
                 "viewer": []},
                {"id": "sweep", "title": "The length sweep — 20 aa and 12 aa", "date": "2026-10-19",
                 "tools": ["EvoBind", "Boltz-2", "IPSAE"],
                 "text": "Runs 3 and 4 tested the long and short ends.",
                 "steps": ["Run 3: 20 aa cyclic (died at 245/300, converged)",
                           "Run 4: 12 aa cyclic (298 iterations)",
                           "Screen both"],
                 "outcome": "Neither length produced a hit. 15 aa stands.", "viewer": []},
            ],
            "proteins": proteins_for(c2_names, "run1"),
            "viewer": viewer_for(c2_names),
        },
        {
            "id": "c3-boltzgen-cyclic",
            "title": "C3 campaign — BoltzGen cyclic peptides",
            "date": "2026-10-20",
            "verdict": "promising",
            "best": False,
            "scores": {},
            "summary": (f"{len(c3_names)} designs screened across four batches, "
                        f"{hits(c3_names)} two-domain samples. The junction constraint transfers "
                        "from campaign 1."),
            "goal": ("A second peptide generator at the same site, with its own scoring suite — "
                     "orthogonal candidates and a cross-check on the c1/c2 winners."),
            "goal_extra": [
                "Answers: does BoltzGen produce two-domain designs at the junction?",
                "Answers: do two independent pipelines agree on the same designs?",
            ],
            "verdict_detail": ("Seven two-domain hits across the four batches. Key lesson: "
                               "BoltzGen's own metrics ranked its best designs wrongly — every "
                               "design must pass the independent screen."),
            "chapters": [
                {"id": "b1", "title": "Batch 1 — groove + junction constraint", "date": "2026-10-20",
                 "tools": ["BoltzGen", "Boltz-2", "IPSAE", "reactifpTM"],
                 "text": "Seven single-design runs; the pipeline proved usable on the 12 GB card "
                         "at one design per run with a fresh output directory.",
                 "steps": ["Write the spec with binding_types on the ten site residues",
                           "Run one design per invocation", "Screen on the independent pipeline"],
                 "outcome": "Two groove-binding candidates the generator's own metrics called weak.",
                 "viewer": []},
                {"id": "b2", "title": "Batch 2 — junction-only constraint", "date": "2026-10-20",
                 "tools": ["BoltzGen", "Boltz-2", "IPSAE"],
                 "text": "The junction-only variant, following the campaign-1 lesson.",
                 "steps": ["Spec on the four junction residues", "Screen as before"],
                 "outcome": "Deeper reach (tm and ecl3 contacts) and better consistency.",
                 "viewer": []},
                {"id": "scale", "title": "Batch 3 — the junction scale-up", "date": "2026-10-20",
                 "tools": ["BoltzGen", "Boltz-2", "IPSAE"],
                 "text": "Twelve more junction designs.",
                 "steps": ["Sample twelve designs", "Fold and screen"],
                 "outcome": "Two two-domain hits.", "viewer": []},
                {"id": "c4", "title": "Batch 4 — thirty more junction designs", "date": "2026-10-20",
                 "tools": ["BoltzGen", "Boltz-2", "IPSAE"],
                 "text": "The scale batch.",
                 "steps": ["Sample thirty designs", "Fold and screen"],
                 "outcome": "Two more two-domain hits; three designs enter the campaign top eight.",
                 "viewer": []},
            ],
            "proteins": proteins_for(c3_names, "b1"),
            "viewer": viewer_for(c3_names),
        },
    ]

    if c5_names:
        experiments.append({
            "id": "c5-bindcraft2-junction",
            "title": "C5 campaign — BindCraft2 peptides",
            "date": "2026-10-20",
            "verdict": "promising",
            "best": False,
            "scores": {},
            "summary": (f"{len(c5_names)} designs screened. BindCraft2's first real run on the "
                        "junction site."),
            "goal": "A third generator at the junction, screened on the independent pipeline.",
            "goal_extra": ["Answers: does BindCraft2 add candidates our screen likes?"],
            "verdict_detail": "Pending full screening.",
            "chapters": [{"id": "run", "title": "The 50-trajectory run", "date": "2026-10-20",
                          "tools": ["BindCraft2", "Boltz-2", "IPSAE"],
                          "text": "Peptide modality, 15-18 aa, gates relaxed so raw output "
                                  "survives for the independent screen.",
                          "steps": ["Run 50 trajectories", "Collect sequences", "Fold and screen"],
                          "outcome": "Pending.", "viewer": []}],
            "proteins": proteins_for(c5_names, "run"),
            "viewer": viewer_for(c5_names),
        })

    if c6_names:
        experiments.append({
            "id": "c6-solublemnn-resequencing",
            "title": "C6 campaign — SolubleMPNN re-sequencing",
            "date": "2026-10-20",
            "verdict": "record",
            "best": False,
            "scores": {},
            "summary": (f"{len(c6_names)} re-sequenced designs, 20 two-domain samples. "
                        "The challenge's best design: ipSAE 0.934 with the full groove."),
            "goal": ("Re-sequence campaign 1's champion backbones with SolubleMPNN, "
                     "interface-pinned - the fix for ProteinMPNN's alanine collapse."),
            "goal_extra": ["Answers: does a better sequence model lift the c1 backbones?"],
            "verdict_detail": ("The retry worked: one backbone produced a family better than "
                               "the original on affinity, groove coverage and reach."),
            "chapters": [{"id": "resequencing", "title": "Interface-pinned re-sequencing + folds",
                          "date": "2026-10-20",
                          "tools": ["SolubleMPNN", "Boltz-2", "IPSAE"],
                          "text": ("5 champion backbones, interface residues pinned, 8 sequences "
                                   "each, all folded against the full receptor."),
                          "steps": ["Extract the binder backbones from the best co-folds",
                                    "Run soluble_mpnn with the interface pinned",
                                    "Fold and screen every sequence"],
                          "outcome": "20 samples cleared the bar; the challenge's best design resulted.",
                          "viewer": []}],
            "proteins": proteins_for(c6_names, "resequencing"),
            "viewer": viewer_for(c6_names),
        })
    if c7_names:
        experiments.append({
            "id": "c7-long-peptides",
            "title": "C7 campaign — extended-length peptides (20-24 aa)",
            "date": "2026-10-20",
            "verdict": "partial",
            "best": False,
            "scores": {},
            "summary": (f"{len(c7_names)} designs at 20-24 aa, 5 two-domain HITs. "
                        "Viable, not superior to 15-18 aa."),
            "goal": "The one untried length class at the junction site.",
            "goal_extra": ["Answers: does a longer peptide beat the 15-18 aa band?"],
            "verdict_detail": ("Longer peptides cover more groove (two touch all six residues) "
                               "but do not beat 15-18 aa on affinity (best 0.834 vs 0.934)."),
            "chapters": [{"id": "long", "title": "The 20-24 aa sampling + folds", "date": "2026-10-20",
                          "tools": ["BoltzGen", "Boltz-2", "IPSAE"],
                          "text": "30 single-design runs at the junction, then the standard fold and screen.",
                          "steps": ["Sample 30 designs", "Fold against the full receptor", "Screen"],
                          "outcome": "5 two-domain HITs; the length question answered.",
                          "viewer": []}],
            "proteins": proteins_for(c7_names, "long"),
            "viewer": viewer_for(c7_names),
        })

    if c8_names:
        sixes = sum(1 for n in c8_names if int((gate.get(n) or {}).get("met", 0)) >= 6)
        experiments.append({
            "id": "c8-deep-junction",
            "title": "C8 campaign — deep junction at scale",
            "date": "2026-10-21",
            "verdict": "promising",
            "best": False,
            "scores": {},
            "summary": (f"{len(c8_names)} designs repeating the c3 junction recipe, "
                        f"{hits(c8_names)} two-domain samples and {sixes} designs with "
                        "the full 6/6 activation pharmacophore."),
            "goal": ("Repeat the exact configuration that produced the most complete "
                     "activation geometries, at 60-design scale."),
            "goal_extra": ["Answers: does the c3 yield hold at scale?",
                           "Answers: how many 6/6 activation geometries does one batch give?"],
            "verdict_detail": ("The yield held: three more 6/6 designs, including c8-run13 - "
                               "a two-domain HIT with the full pharmacophore. The activation "
                               "pool is now nine designs."),
            "chapters": [{"id": "generation", "title": "60 junction-only runs + folds + gate",
                          "date": "2026-10-21",
                          "tools": ["BoltzGen", "Boltz-2", "IPSAE", "activation-geometry gate"],
                          "text": ("The c3 junction spec, one design per run, each folded "
                                   "against the full receptor and scored by both the binding "
                                   "screen and the activation-geometry gate."),
                          "steps": ["Sample 60 designs with the c3 junction spec",
                                    "Fold each against the full 409-residue construct",
                                    "Screen for two-domain reach and the 6/6 pharmacophore"],
                          "outcome": "11 two-domain HITs; three 6/6 activation geometries.",
                          "viewer": []}],
            "proteins": proteins_for(c8_names, "generation"),
            "viewer": viewer_for(c8_names),
        })

    if c9_names:
        sixes = sum(1 for n in c9_names if int((gate.get(n) or {}).get("met", 0)) >= 6)
        experiments.append({
            "id": "c9-solublemnn-resequenced",
            "title": "C9 campaign — SolubleMPNN on the activation champion",
            "date": "2026-10-21",
            "verdict": "record",
            "best": False,
            "scores": {},
            "summary": (f"{len(c9_names)} re-sequenced variants of e1b2-r0065 (the c1 6/6 "
                        f"miniprotein); {sixes} carry the full 6/6 activation pharmacophore."),
            "goal": ("Apply the c6 recipe — interface-pinned SolubleMPNN — to the c1 "
                     "design that carries the full activation geometry."),
            "goal_extra": ["Answers: does re-sequencing lift a 6/6 backbone?",
                           "Answers: how many variants of one family hold the full "
                           "pharmacophore?"],
            "verdict_detail": ("The cross-campaign improvement confirmed: five variants "
                               "reproduce the 6/6 geometry, several deeper than the parent."),
            "chapters": [{"id": "resequencing",
                          "title": "Interface-pinned re-sequencing + folds",
                          "date": "2026-10-21",
                          "tools": ["SolubleMPNN", "Boltz-2", "IPSAE",
                                    "activation-geometry gate"],
                          "text": ("47 interface positions of the 84-residue backbone pinned; "
                                   "every unique sequence folded against the full receptor "
                                   "and gated."),
                          "steps": ["Extract the backbone from the best co-fold",
                                    "Run soluble_mpnn with the interface pinned",
                                    "Fold each sequence and run both screens"],
                          "outcome": "Five designs with the full 6/6 pharmacophore.",
                          "viewer": []}],
            "proteins": proteins_for(c9_names, "resequencing"),
            "viewer": viewer_for(c9_names),
        })

    if c12_names:
        sixes = sum(1 for n in c12_names if int((gate.get(n) or {}).get("met", 0)) >= 6)
        twod = sum(1 for n in c12_names
                   if any("two-domain" in r["verdict"] for r in by_design[n]))
        experiments.append({
            "id": "c12-rfd4-proteina",
            "title": "C12 campaign — RFD4-Proteina on NVIDIA's hosted GPU pool",
            "date": "2026-10-22",
            "verdict": "record",
            "best": False,
            "scores": {},
            "summary": (f"{len(c12_names)} designs from RFD4-Proteina (medium and high "
                        f"thinking rounds on free hosted GPUs); {sixes} carry the full "
                        f"6/6 activation pharmacophore and {twod} are two-domain HITs."),
            "goal": ("Run the strongest published generator against the deep message "
                     "region (TM-pocket and ECL3) — the half of the activation span no "
                     "earlier generator reached."),
            "goal_extra": ["Answers: does RFD4-Proteina beat the local generators on "
                           "this target?",
                           "Answers: does high thinking change the design class?"],
            "verdict_detail": ("The strongest campaign of the challenge: the top of the "
                               "whole ranking, 52 full-geometry designs across both "
                               "rounds, and the best two-domain rate of any generator."),
            "chapters": [{"id": "generation",
                          "title": "Hosted generation + folds + screens",
                          "date": "2026-10-22",
                          "tools": ["RFD4-Proteina (hosted)", "Boltz-2", "IPSAE",
                                    "activation-geometry gate"],
                          "text": ("The annotated target CIF conditions generation on "
                                   "the TM-pocket/ECL3 message region; every design is "
                                   "re-folded against the full receptor construct."),
                          "steps": ["Build the annotated CIF from the condition spec",
                                    "Generate on the hosted pool, 8 designs per request",
                                    "Fold, screen and gate every design"],
                          "outcome": f"{sixes} full 6/6 activation geometries.",
                          "viewer": []}],
            "proteins": proteins_for(c12_names, "generation"),
            "viewer": viewer_for(c12_names),
        })

    if c12m_names:
        sixes = sum(1 for n in c12m_names if int((gate.get(n) or {}).get("met", 0)) >= 6)
        experiments.append({
            "id": "c12-mpnn-variants",
            "title": "C12 re-sequencing — SolubleMPNN on every full-geometry backbone",
            "date": "2026-10-22",
            "verdict": "record",
            "best": False,
            "scores": {},
            "summary": (f"{len(c12m_names)} interface-pinned SolubleMPNN variants of the "
                        f"campaign's full-geometry backbones; {sixes} carry the full 6/6 "
                        f"activation pharmacophore."),
            "goal": ("Expand the rare perfect class the generator found: re-sequence "
                     "every 6/6 backbone with the interface pinned."),
            "goal_extra": ["Answers: does the c6/c9 recipe transfer to RFD4 backbones?",
                           "Answers: how many variants keep the full pharmacophore?"],
            "verdict_detail": ("The best re-sequencing yield of the challenge: 25 new "
                               "full-geometry designs from 81 variants."),
            "chapters": [{"id": "resequencing",
                          "title": "Interface-pinned re-sequencing + folds",
                          "date": "2026-10-22",
                          "tools": ["SolubleMPNN", "Boltz-2", "IPSAE",
                                    "activation-geometry gate"],
                          "text": ("Interface residues within 4 A of the receptor pinned; "
                                   "the top three deduped variants per backbone are "
                                   "folded against the full receptor."),
                          "steps": ["Extract each champion's best deep fold sample",
                                    "Run soluble_mpnn with the interface pinned",
                                    "Fold and gate the variants"],
                          "outcome": f"{sixes} variants with the full 6/6 pharmacophore.",
                          "viewer": []}],
            "proteins": proteins_for(c12m_names, "resequencing"),
            "viewer": viewer_for(c12m_names),
        })

    if c13_names:
        sixes = sum(1 for n in c13_names if int((gate.get(n) or {}).get("met", 0)) >= 6)
        twod = sum(1 for n in c13_names
                   if any("two-domain" in r["verdict"] for r in by_design[n]))
        experiments.append({
            "id": "c13-junction",
            "title": "C13 campaign — RFD4 conditioned on the ECD–TMD junction",
            "date": "2026-10-22",
            "verdict": "record",
            "best": False,
            "scores": {},
            "summary": (f"{len(c13_names)} designs from a junction-conditioned hosted round; "
                        f"{sixes} carry the full 6/6 activation pharmacophore and {twod} are "
                        f"two-domain HITs."),
            "goal": ("Test the split rule on RFD4: condition on the ECD–TMD junction "
                     "(K197/Q210/Q221/Q234) instead of the deep region."),
            "goal_extra": ["Answers: does the junction conditioning transfer to RFD4?",
                           "Answers: does it beat the deep round's full-geometry rate?"],
            "verdict_detail": ("The strongest configuration of the challenge: 15 full 6/6 "
                               "geometries from 73 designs (21%), 78% of samples in the deep "
                               "tier, and the top of the final ranking."),
            "chapters": [{"id": "junction",
                          "title": "Hosted generation + folds + screens",
                          "date": "2026-10-22",
                          "tools": ["RFD4-Proteina (hosted)", "Boltz-2", "IPSAE",
                                    "activation-geometry gate"],
                          "text": ("The junction hotspot set alone; every design folded "
                                   "against the full receptor construct as always."),
                          "steps": ["Build the junction-conditioned CIF from the spec",
                                    "Generate on the hosted pool, 8 designs per request",
                                    "Fold, screen and gate every design"],
                          "outcome": f"{sixes} full 6/6 activation geometries.",
                          "viewer": []}],
            "proteins": proteins_for(c13_names, "junction"),
            "viewer": viewer_for(c13_names),
        })

    if c14_names:
        sixes = sum(1 for n in c14_names if int((gate.get(n) or {}).get("met", 0)) >= 6)
        twod = sum(1 for n in c14_names
                   if any("two-domain" in r["verdict"] for r in by_design[n]))
        experiments.append({
            "id": "c14-short-band",
            "title": "C14 campaign — RFD4 at the short length band (40-70 aa)",
            "date": "2026-10-23",
            "verdict": "record",
            "best": False,
            "scores": {},
            "summary": (f"{len(c14_names)} designs from the deep conditioning at a new "
                        f"length band; {sixes} carry the full 6/6 activation pharmacophore "
                        f"and {twod} are two-domain HITs."),
            "goal": ("Open the length axis: the deep message region at the c1-proven "
                     "40-70 aa size class."),
            "goal_extra": ["Answers: does the short band change the design class?",
                           "Answers: does it produce two-domain hits at a better rate?"],
            "verdict_detail": ("Six full 6/6 geometries and the best two-domain HIT rate of "
                               "any round; two designs entered the top twenty."),
            "chapters": [{"id": "short",
                          "title": "Hosted generation + folds + screens",
                          "date": "2026-10-23",
                          "tools": ["RFD4-Proteina (hosted)", "Boltz-2", "IPSAE",
                                    "activation-geometry gate"],
                          "text": ("The deep-region hotspot set at a 40-70 aa binder band, "
                                   "generated against the trimmed target and folded against "
                                   "the full construct."),
                          "steps": ["Build the short-band CIF from the spec",
                                    "Generate on the hosted pool, 8 designs per request",
                                    "Fold, screen and gate every design"],
                          "outcome": f"{sixes} full 6/6 activation geometries.",
                          "viewer": []}],
            "proteins": proteins_for(c14_names, "short"),
            "viewer": viewer_for(c14_names),
        })

    # the app renders steps as objects {title, text, image}; normalize
    for e in experiments:
        for c in e["chapters"]:
            c["steps"] = [s if isinstance(s, dict)
                          else {"title": s, "text": "", "image": None}
                          for s in c["steps"]]

    OUT.write_text(json.dumps({"experiments": experiments}, indent=1))
    total = sum(len(e["proteins"]) for e in experiments)
    print(f"wrote {OUT}")
    print(f"{len(experiments)} campaigns, {total} proteins")
    for e in experiments:
        print(f"  {e['id']}: {len(e['proteins'])} proteins")


if __name__ == "__main__":
    main()
