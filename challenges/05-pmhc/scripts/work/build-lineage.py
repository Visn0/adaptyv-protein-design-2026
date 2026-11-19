#!/usr/bin/env python3
"""Build challenges/05-pmhc/lineage.json — the campaign story for the web app.

Same shape as challenges/04-tfr1/lineage.json (see tools/serve/app.py:
_load_lineage, _lineage_steps_html, _campaigns_html). Keep entries short and
factual: verdict + summary carry the outcome, chapters carry the steps.

Usage: PYTHONPATH= .venv/bin/python build-lineage.py
"""

from __future__ import annotations

import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parents[2] / "lineage.json"

EXP = []


def add(**kw):
    """Every campaign carries the same keys, so the pages render alike."""
    kw.setdefault("proteins", [])
    kw.setdefault("viewer", [])
    kw.setdefault("scores", {})
    kw.setdefault("best", False)
    EXP.append(kw)


def ch(cid, title, date, tools, text, outcome, steps=None):
    return {"id": cid, "title": title, "date": date, "tools": tools,
            "text": text, "steps": steps or [], "outcome": outcome,
            "viewer": []}


# --------------------------------------------------------------- tool labels
# The site's Tools section lists recognised tools only. A chapter may name the
# project's own script as the thing that ran; that name is mapped to the
# recognised tool underneath it, and anything still unrecognised is dropped, so
# no internal script name ever reaches the page.
TOOL_ALIAS = {
    "boltz": "Boltz-2",
    "chai-lab": "Chai-1",
    "Proteina": "RFD4-Proteina",
    "E-score": "PROPKA 3.5.1",
    "MPNN variants": "ProteinMPNN",
    "LigandMPNN": "ProteinMPNN",
}
KNOWN_TOOLS = {
    "RFD4-Proteina", "Boltz-2", "BoltzGen", "Chai-1", "ColabFold / AlphaFold2",
    "OpenFold3", "ProteinMPNN", "SolubleMPNN", "Proton-PottsMPNN",
    "RFdiffusion3", "BindCraft2", "EvoBind", "Genie 3", "BioEmu2", "OpenDDE",
    "Gemmi", "IPSAE", "PROPKA 3.5.1", "OpenMM", "Rosetta ref2015", "FreeSASA",
    "MMseqs2", "Foldseek", "US-align", "3Dmol.js", "ATLAS", "SKEMPI2",
    "diffusers", "peft", "scikit-learn",
}

# Some chapters ran entirely through the project's own scripts. Those scripts
# are not tools the site lists, so where the underlying work clearly used a
# recognised tool, that tool is named instead of leaving an empty Tools row.
CHAPTER_TOOL_FIX = {
    ("c13-surrogate-screen", "t1"): ["scikit-learn"],
    ("c14-evolution-gen1", "g1"): ["RFD4-Proteina", "Boltz-2"],
    ("c15-evolution-autonomy", "g2"): ["RFD4-Proteina", "Boltz-2"],
    ("c15-evolution-autonomy", "g3"): ["RFD4-Proteina", "Boltz-2"],
    ("c16-evolution-gen4", "g4"): ["RFD4-Proteina", "Boltz-2"],
    ("c16-evolution-gen4", "g5"): ["RFD4-Proteina", "Boltz-2"],
    ("c16-evolution-gen4", "fix"): ["RFD4-Proteina", "Boltz-2"],
    ("c16-evolution-gen4", "g13"): ["RFD4-Proteina", "Boltz-2"],
    ("c17-generator-project", "trunc"): ["RFD4-Proteina"],
}


def clean_tools(labels) -> list:
    """Recognised tools only, alias-resolved, order kept, duplicates removed."""
    out = []
    for label in labels or []:
        label = TOOL_ALIAS.get(label, label)
        if label in KNOWN_TOOLS and label not in out:
            out.append(label)
    return out


def clean_all_tools() -> tuple[int, list]:
    """Rewrite every chapter's tool list. Returns (renamed or dropped, names)."""
    dropped = []
    for exp in EXP:
        for chapter in exp.get("chapters") or []:
            before = list(chapter.get("tools") or [])
            chapter["tools"] = clean_tools(before)
            fix = CHAPTER_TOOL_FIX.get((exp["id"], chapter.get("id")))
            if fix and not chapter["tools"]:
                chapter["tools"] = list(fix)
            for label in before:
                if label not in chapter["tools"] and label not in dropped:
                    dropped.append(label)
    return len(dropped), dropped


# ------------------------------------------------------------------- merging
# A campaign is a strategy, not a sync run. Several strategies here were told
# over three or four days and landed as separate campaigns; they are folded
# back into one entry. The surviving campaign keeps the LOWEST number of its
# group, so design names (c9-g3_*), records folders and older notes stay valid
# and the numbering simply has gaps.
MERGES = [
    {
        "into": "c7-rule-mining",
        "absorb": ["c13-surrogate-screen"],
        "id": "c7-cheap-prediction",
        "title": "C7 — predicting a winner without folding it",
        "date": "2026-11-02 → 2026-11-03",
        "verdict":
            "Split result: hand-mined rules work, a learned screen does not. "
            "Five features read off our own dual-signal winners picked 3 of 8 "
            "never-folded candidates correctly, a 2.5x lift on the pool base "
            "rate and including the project's best WT discriminator. The "
            "surrogate trained on the same labels returned a top 50 that "
            "folded to zero hits, below the random rate. Cheap triage is "
            "possible from explicit interface geometry and impossible from "
            "sequence composition alone.",
        "summary":
            "Two attempts to rank a design before paying for its fold. The "
            "first mined five features from the project's own winners and "
            "tested them out of sample. The second trained a cross-validated "
            "sequence-composition surrogate on every E-scored design and "
            "folded its own top 50 from the 1.6k never-folded pool. The "
            "contrast is the finding: features that name where a charge sits "
            "relative to the P6 aspartate carry signal, and features that "
            "only count what is in the sequence cannot see where those "
            "charges land after the chain folds.",
    },
    {
        "into": "c9-genie3",
        "absorb": ["c17-generator-project", "c18-finetune-verdict",
                   "c19-pristine-batch"],
        "id": "c9-generator-hunt",
        "title": "C9 — the generator hunt",
        "date": "2026-11-02 → 2026-11-08",
        "verdict":
            "Four attempts to replace or improve the hosted generator, and "
            "the frozen released model wins all four. genie3's CA-only route "
            "scored 0 of 70; BoltzGen reached 0.101 peptide_read against "
            "RFD4-Proteina's 0.577 on an identical funnel; the LoRA "
            "fine-tune was closed on the 12 GB card after six verified "
            "attempts, and the checkpoint trained on rented silicon "
            "destroyed the model's target conditioning. 100 raw designs from "
            "the frozen model then passed the organizer gate nine times and "
            "still lost the wild-type test to the evolved champions by an "
            "order of magnitude. The generator ends this campaign local, "
            "inspectable and deliberately unchanged.",
        "summary":
            "Every design on this site begins as a backbone from the hosted "
            "RFD4-Proteina NIM — the one stage the project could not run, "
            "inspect or fine-tune. This campaign opens that stage and then "
            "tries to beat it. It covers the third-generator trial (genie3), "
            "the local RFD4-Proteina copy and its parity check against the "
            "hosted service, a competing generator (BoltzGen) measured on "
            "the same funnel, wet-lab label sets for calibrating the score "
            "(ATLAS, SKEMPI2), the reward-tuned LoRA plan and the 12 GB wall "
            "that stopped it, the fine-tuned checkpoint that produced clean "
            "proteins 14 A away from the peptide, and the 100-design "
            "pristine batch whose three-arm specificity panel settled the "
            "question. Most of its experiments are negative, and that is the "
            "value: it fixes the generator as a trusted frozen input and "
            "locates this project's discriminating power in the selection "
            "loop instead.",
    },
    {
        "into": "c11-wave-five",
        "absorb": ["c12-salt"],
        "id": "c11-direct-grip",
        "title": "C11 — conditioning for a direct grip",
        "date": "2026-11-02",
        "verdict":
            "Both waves negative, and together decisive: the generator "
            "cannot be talked into touching the buried aspartate. Two "
            "hundred designs of the strongest working conditioning gave 30 "
            "pose-screen passers and zero swaps, with the affinity-strong "
            "designs reading wrong-sign electrostatics. Asked point-blank "
            "for a salt bridge to the mutant carboxylate, the generator "
            "still settled at 8-10 A. The indirect field-reading doctrine is "
            "confirmed by the failure of its alternative.",
        "summary":
            "Two generation waves that pushed the conditioning instead of "
            "the selection. The fifth wave asked for more of whatever the "
            "strongest earlier conditioning had produced. The salt wave "
            "asked for the thing the target physics says is hard: a direct "
            "ionic contact with the Asp6 carboxylate, which is about 90 "
            "percent buried and already salt-bridged to the HLA's own "
            "Arg114. Neither wave produced a submittable design, and the "
            "second one explains why the first could not.",
    },
    {
        "into": "c14-evolution-gen1",
        "absorb": ["c15-evolution-autonomy", "c16-evolution-gen4"],
        "id": "c14-evolution-loop",
        "title": "C14 — the evolution loop (generations 1-20)",
        "date": "2026-11-03 → 2026-11-05",
        "verdict":
            "The project's most productive campaign and its clearest "
            "ceiling. Generations 1 and 4 produced the top two designs of "
            "the submission — 79.1 to 90.5 and 67.5 to 87.1 — plus three "
            "further entrants; the other eighteen generations promoted "
            "nothing. Four loop bugs were found and fixed along the way, "
            "including generations that re-bred byte-identical children and "
            "a breeder that could not read the sequences of the winners it "
            "had itself swapped in.",
        "summary":
            "Twenty generations of mutate-and-select over the submitted set. "
            "For each top parent the loop proposes single swaps at unsampled "
            "shell positions 5-13 A from the P6 aspartate plus combo mutants "
            "stacking known repair hits, folds and E-scores them, sends the "
            "qualifiers through the tri-state panel, and admits a child only "
            "on a +1.0 composite margin with three-seed validation. The "
            "cycle went from hand-driven to unattended autopilot across its "
            "first three generations. Its wins are concentrated at the "
            "front: generation 1 gave the number-one design (Q15K, 90.5, E "
            "-3.65, dWT +0.747) and generation 4 promoted three "
            "single-lysine swaps. From generation 5 the loop plateaued "
            "twice, both times on repetition it could not see in itself, and "
            "both causes were diagnosed and repaired — the second fix "
            "landing after the run that exposed it.",
    },
]


def merge_campaigns() -> int:
    """Fold each MERGES group into its host campaign. Returns groups merged.

    Runs after clean_all_tools() so CHAPTER_TOOL_FIX still matches the
    original (campaign id, chapter id) pairs.
    """
    by_id = {e["id"]: e for e in EXP}
    absorbed = set()
    for m in MERGES:
        host = by_id[m["into"]]
        for src_id in m["absorb"]:
            src = by_id[src_id]
            taken = {c["id"] for c in host["chapters"]}
            for chapter in src.get("chapters") or []:
                old = chapter["id"]
                if old in taken:
                    chapter["id"] = f"{src_id.split('-')[0]}-{old}"
                    for p in src.get("proteins") or []:
                        if p.get("phase") == old:
                            p["phase"] = chapter["id"]
                host["chapters"].append(chapter)
                taken.add(chapter["id"])
            host["proteins"] += src.get("proteins") or []
            host["viewer"] += src.get("viewer") or []
            host["scores"].update(src.get("scores") or {})
            host["best"] = host.get("best") or src.get("best")
            absorbed.add(src_id)
        host.update({k: m[k] for k in
                     ("id", "title", "date", "verdict", "summary")})
    EXP[:] = [e for e in EXP if e["id"] not in absorbed]
    assert len({e["id"] for e in EXP}) == len(EXP), "duplicate campaign id"
    for e in EXP:
        ids = [c["id"] for c in e["chapters"]]
        assert len(set(ids)) == len(ids), f"duplicate chapter id in {e['id']}"
    return len(MERGES)



# ---------------------------------------------------------------- c0
add(
    id="c0-instrument-calibration",
    title="C0 — calibrating the instruments on this target",
    date="2026-10-29",
    verdict="The co-fold screens are blind to single-point peptide "
            "discrimination — proven with controls. Specificity must ride on "
            "interaction rules, not confidence deltas.",
    best=False,
    scores={},
    summary="Folded the organizers' own crystal structures plus a known-good "
            "control set (the published JDI TCR, shuffled-peptide and "
            "peptide-free negatives) and read every instrument against them. "
            "Boltz-2 and BindCraft2 read the wrong sign on the mutant-vs-"
            "wild-type comparison (ipTM delta -0.043); Chai-1 with MSAs was "
            "the first instrument with the correct sign. The target's "
            "chemistry was measured directly from the crystals: the G12D "
            "aspartate sits buried (10% exposed), salt-bridged to HLA R114 "
            "and hydrogen-bonded to Q70 — the discrimination is an "
            "electrostatic field perturbation, exactly what the JDI TCR "
            "reads indirectly. 2026-11-03: a third instrument class "
            "failed its control - the Rosetta desolvation ddG read +0.0 "
            "without repack and -0.1 with interface repack on the JDI "
            "control, so it is disqualified. Fold confidence, contact "
            "physics and shape ensembles (BioEmu2, flat WT/G12D "
            "contrast) now all fail their controls here; only the "
            "explicit-electrostatics E-score passes.",
    goal="Find out which instruments can see this target's specificity "
         "before trusting any of them.",
    goal_extra=[
        "Strategy difference: the only campaign whose deliverable is a "
        "decision, not designs — it judges instruments and rules, and every "
        "later campaign inherits that calibration.",
        "Answers: can a co-fold screen separate G12D from WT? (No.)",
        "Answers: what interaction should a designed binder make? (A basic "
        "residue in the 6-8 A shell above P6/P7 — the JDI TCR's indirect "
        "electrostatic read.)",
    ],
    verdict_detail="Controls: the known JDI TCR reads 0.94-0.95 peptide "
                   "ipTM in its own complex; the peptide-free and shuffled "
                   "controls collapse (0.49 / 0.005). Boltz-2 and BindCraft2 "
                   "read G12D-vs-WT with the wrong sign (their deltas are "
                   "disqualified as a specificity signal); Chai-1 with MSAs "
                   "reads 0.895 vs 0.877 — correct sign, supporting evidence "
                   "only. i_pDAE (BindCraft2's interface pDAE) was added "
                   "after the benchmark review showed it has the best "
                   "top-decile precision of the fold metrics. 2026-11-03 "
                   "instrument audit (corrected 20-design table): E_v2 "
                   "unchanged vs v1 on every entry; two designs have shell "
                   "histidines at 6.88 A and 6.10 A from the D6 carboxylate "
                   "- the polar-read class the charge model cannot see. 2026-11-03, "
                   "that desolvation instrument: built (Rosetta fa_sol ddG on the JDI "
                   "control) and FAILED - ddG +0.0 without repack, -0.1 with interface "
                   "repack - so it is disqualified for ranking. Three instrument "
                   "classes now fail their controls on this target: fold confidence "
                   "(C0, sign inversion), contact physics (Rosetta, zero) and shape "
                   "ensembles (BioEmu2, flat WT/G12D contrast). Only the "
                   "explicit-electrostatics E-score passes - the project's core "
                   "finding.",
    chapters=[
        ch("g1", "G — the target files and the control set", "2026-10-29",
           ["Gemmi", "Boltz-2"],
           "Three organizer structures (G12D complex, WT complex, "
           "peptide-free) plus RCSB references; controls built from the "
           "published JDI TCR with a 621-residue Fv trim that this host can "
           "fold without crashing.",
           "9 control folds, all instruments calibrated."),
        ch("v1", "V — the instrument matrix", "2026-10-30",
           ["Boltz-2", "Chai-1", "BindCraft2", "IPSAE"],
           "Every instrument read against the same controls: Boltz-2 "
           "(5 models per fold), Chai-1 (single-sequence and MSA routes), "
           "BindCraft2 filters, ipSAE and i_pDAE interface metrics. Only "
           "the MSA route of Chai-1 separates mutant from wild type with "
           "the correct sign.",
           "Specificity ranking rides on rules + the three-state panel, "
           "not on any single confidence number."),
        ch("r1", "R — the interaction rules from the crystals", "2026-10-31",
           ["Gemmi", "FreeSASA"],
           "Measured from the organizer crystals: Asp6 SASA 8.8 A2 (10.4% "
           "free), OD2-R114 2.95 A salt bridge, OD2-Q70 3.08 A hydrogen "
           "bond, closest JDI atom 7.51 A. The 10-mer register is the "
           "productive one; the 9-mer is a flattened decoy.",
           "The design rules: a peptide-first footprint (arc over the "
           "ridge P4-P8) plus a basic nitrogen in the 6-8 A shell above "
           "P6/P7."),
        ch("a1", "A - the 2026-11-03 instrument audit", "2026-11-03",
           ["PROPKA", "escore2.py"],
           "An external review caught the E-score's blind spot: v1 carried "
           "Asp/Glu/Lys/Arg only, blind to histidine - the residue class "
           "the native JDI discriminator itself uses (TCRbeta His100, "
           "7.5 A from the carboxylate). The fix, escore2.py, is "
           "PROPKA-aware: each binder His gets a pKa, the fraction "
           "f = 1/(1+10^(7.4-pKa)) puts +0.5*f on the ring nitrogens, "
           "calibration matched to v1 exactly. Re-read on all 20 "
           "submissions: every shell histidine reads 0% protonated (the "
           "HLA R114 +1 field disfavours it), so E_v2 equals v1 on the "
           "whole set and the corrected 20-design table is unchanged; no "
           "charged His exists in any shell, and the two closest shell "
           "histidines sit at 6.88 A and 6.10 A from the carboxylate. The "
           "finding that matters: the set's shell readers "
           "are polar groups (Ser/Thr/Tyr/Asn/Gln/His at 6-7 A), not "
           "charged ones - a charge-Coulomb score undercounts them, and a "
           "polar/desolvation instrument is the open item.",
           "Blind spot fixed; E_v2 equals v1 on all 20; no ranking "
           "changes."),
        ch("d1", "D - the desolvation instrument (control failed)",
           "2026-11-03", ["Rosetta ref2015", "ros-desolv.py"],
           "Built the external review's suggested desolvation upgrade: "
           "interface analysis, a P6 D->G mutation and a fa_sol "
           "decomposition in Rosetta. The standing control discipline "
           "applies: the JDI fold must read positive (it prefers the "
           "mutant peptide). It read +0.0 without repack and -0.1 with "
           "interface repack. The mutation is invisible to a "
           "fixed-charge force field because there are no contacts to "
           "change - the nearest JDI atom sits 7.5 A away (the C0 "
           "measurement). The interface repack drops absolute energies "
           "by about 96 REU and leaves the mutation effect at zero. "
           "The Wu 2022 precedent does not transfer: their mutated "
           "residue sits in the interface, ours is read through the "
           "field.",
           "Disqualified - do not rank on it. Three instrument classes "
           "now fail their controls on this target: fold confidence "
           "(C0, sign inversion), contact physics (Rosetta, zero) and "
           "shape ensembles (BioEmu2, flat WT/G12D contrast). Only "
           "direct electrostatics reads the mutation - the core "
           "finding."),
    ],
)

# ---------------------------------------------------------------- c1
add(
    id="c1-main-funnel",
    title="C1 — the main funnel (four NIM waves)",
    date="2026-10-31",
    verdict="239 designs folded, 40 tri-stated, 6 dual-signal. The pipeline "
            "works end to end; specificity is rare — about 15% of "
            "tri-stated candidates.",
    best=True,
    scores={},
    summary="Four hosted RFdiffusion4 NIM waves conditioned on the peptide "
            "ridge (hotspots P4-P8), screened for the peptide-first "
            "footprint before sequence assignment, folded against G12D, "
            "then tri-stated (mutant / wild-type / peptide-free). The best "
            "designs arc over the ridge and read the mutant's electrostatic "
            "field with basic residues — the C0 rule, executed at scale.",
    goal="Run the full design funnel at volume: generate, screen, fold, "
         "tri-state, rank.",
    goal_extra=[
        "Strategy difference: the volume campaign — every later campaign "
        "varies one axis (peptide-only, natural mimics, charge-first, "
        "minibinders) against this baseline.",
        "Answers: does the peptide-first screen transfer to real folds? "
        "(Yes — passers land 0.85-0.97 ipTM at 4x the rate of unscreened "
        "designs.)",
    ],
    verdict_detail="Wave yields: pose screen passes about 20% of every "
                    "wave; of the folded passers, roughly a quarter are "
                    "JDI-like (ipTM >= 0.8). Of 40 tri-stated candidates, "
                    "6 carry both signals (WT discrimination dWT >= 0.15 "
                    "and free-state dependence dfree >= 0.2) and none is "
                    "vetoed. Stage 3 added multi-seed folds (max spread "
                    "0.009), Chai-1 MSA cross-checks and the homology "
                    "screen — which found that 60 of 279 designs (21%) "
                    "were near-copies of natural immune proteins.",
    chapters=[
        ch("g1", "G — generation against the ridge", "2026-10-31",
           ["RFD4-Proteina", "ProteinMPNN"],
           "Four hosted NIM waves (239 designs kept) with the ridge "
           "hotspots, sequence assignment on the screened backbones.",
           "239 designs entered folding."),
        ch("f1", "F — folding and the first gate", "2026-10-31",
           ["Boltz-2", "IPSAE"],
           "Every passer folded against the G12D complex, five models per "
           "design; reads: ipTM, ipSAE, i_pDAE. The scorer was smoke-"
           "tested against the C0 controls before use.",
           "24 JDI-like folds; 5 pass the strict peptide gate."),
        ch("t1", "T — the three-state panel", "2026-11-01",
           ["Boltz-2", "Chai-1"],
           "Every candidate folded against WT and the peptide-free MHC; "
           "vetoes for designs that read better on the wrong state; "
           "multi-seed stability and Chai-1 MSA checks on the finalists.",
           "6 dual-signal designs; the stage-3 top-20 assembled."),
    ],
)

# ---------------------------------------------------------------- c2
add(
    id="c2-peptide-only",
    title="C2 — peptide-only readers (mining campaign)",
    date="2026-11-01",
    verdict="A mining campaign, not a generation one: 44 folds from the "
            "existing pool, 1 strict gate passer — and it became the "
            "submission's number two.",
    best=False,
    scores={},
    summary="No new generation: the 1,121 unfolded designs from earlier "
            "waves were re-mined by peptide contact share (>= 0.45, ridge "
            "contacts >= 10), because a binder that touches mostly the "
            "peptide has fewer chances to hold on to the healthy frame. "
            "45 designs selected (top share 0.96 — a near-pure peptide "
            "reader), folded and scored.",
    goal="Test the opposite interface shape from the main funnel's "
         "groove-floor binders: minimal HLA contact, maximal peptide "
         "contact.",
    goal_extra=[
        "Strategy difference: no new generator call — it re-mines the "
        "existing design pool by a geometry property (peptide contact "
        "share), the cheapest possible campaign.",
        "Answers: does a peptide-dense interface concentrate the mutation "
        "signal? (Yes — the family's signature holds.)",
    ],
    verdict_detail="44/45 folded, 6 JDI-like, 1 passing the strict gate. "
                    "The leader (wave1-pep run-033 design_0003) clears the "
                    "organizer gate, folds JDI-like and keeps a "
                    "peptide-heavy interface — tri-stated at dWT +0.359 / "
                    "dfree +0.392, submission entry 2. nim-wave3 run-010 "
                    "design_0002 is the most peptide-focused fold (0.67 "
                    "share) and is submission entry 11. Note: the fold's "
                    "share can differ from the generator pose's share — "
                    "the fold rearranges contacts.",
    chapters=[
        ch("g1", "G — re-mine the pool by peptide share", "2026-11-01",
           ["Binder prescreen"],
           "1,121 unfolded designs screened by peptide contact share "
           "(>= 0.45) and ridge contact count (>= 10).",
           "45 designs selected, top share 0.96."),
        ch("v1", "V — folds and the tri-state", "2026-11-01",
           ["Boltz-2", "IPSAE"],
           "G12D folds, the standard scorer, then the three-state panel "
           "for the winners.",
           "1 strict passer (submission #2); the peptide-dense signature "
           "is real but rare."),
    ],
)

# ---------------------------------------------------------------- c3
add(
    id="c3-natural-reader",
    title="C3 — the natural reader's pattern",
    date="2026-11-01",
    verdict="The best yield of the variant campaigns (4 strict passers of "
            "32, 28%) — the only conditioning set with experimental "
            "provenance, and it delivered two submission entries.",
    best=False,
    scores={},
    summary="Nature already solved this problem: the molecules evolved to "
            "read this exact target are T-cell receptors. The JDI TCR's "
            "contact atoms were measured from the real 7OW6 crystal — 17 "
            "atoms from P4 to P9, backbone-dominated, with the P7 backbone "
            "as the anchor and P6 read through its carbonyl, not its "
            "mutant side chain (the mutation acts as a field). The "
            "generator was conditioned on exactly those atoms.",
    goal="Condition the generator on a real, functional reader's "
         "interaction pattern instead of our own hotspot guess.",
    goal_extra=[
        "Strategy difference: the only campaign whose hotspot set comes "
        "from an experimentally verified reader of this exact target.",
        "Answers: does a natural binding mode transfer to a de novo "
        "binder? (Yes — best gate-pass rate of the variants.)",
    ],
    verdict_detail="160 designs generated (nat-wave1), 32 folded, 9 "
                    "JDI-like, 4 passing the strict gate (28%). "
                    "nat-wave1 run-011 design_0004 (ipTM 0.966, i_pDAE "
                    "0.862, submission 19) and nat-wave1 run-004 "
                    "design_0001 (0.959 / 0.845, submission 17).",
    chapters=[
        ch("g1", "G — measure the natural reader", "2026-11-01",
           ["Gemmi", "7OW6 crystal"],
           "Peptide atoms within 4.5 A of the JDI TCR: P4 CA; P5 CB, O; "
           "P6 C, O; P7 N, CA, C, O; P8 N, CA, C, CB, CG1, CG2; P9 N, CA "
           "— 17 atoms, backbone-dominated.",
           "The NATURAL hotspot set: what a real reader actually touches."),
        ch("v1", "V — generate and fold on the natural pattern",
           "2026-11-01", ["RFD4-Proteina", "ProteinMPNN", "Boltz-2"],
           "nat-wave1 generation on the NATURAL set, the standard pose "
           "screen, G12D folds, tri-state for the winners.",
           "4 strict passers (28%) — the variant campaigns' best; two "
           "submission entries."),
    ],
)

# ---------------------------------------------------------------- c4
add(
    id="c4-charge-first",
    title="C4 — charge first",
    date="2026-11-01",
    verdict="Zero strict passers of 25 folds — the tightest conditioning "
            "focus did not convert. An honest negative with a clear cause.",
    best=False,
    scores={},
    summary="The mutation is one extra negative charge, so this campaign "
            "conditioned the generator on the mutation's neighbourhood "
            "only (the P5-P7 ridge, 6 atoms) so every design had to solve "
            "the charge problem locally, with the C0 electrostatic rule "
            "promoted from filter to core gate.",
    goal="Force every design to address the mutated charge directly "
         "instead of spreading contacts over the whole ridge.",
    goal_extra=[
        "Strategy difference: the narrowest hotspot window of any "
        "campaign — 6 atoms around the mutation.",
        "Answers: does local charge focus beat ridge-wide coverage? "
        "(No — the narrow window starves the interface.)",
    ],
    verdict_detail="25 designs folded, 4 JDI-like, 0 strict passers, and "
                    "none reached the tri-state panel. The tight window "
                    "produces designs that engage P5-P7 but lack the "
                    "broader anchor contacts the gate requires — the "
                    "interface starves.",
    chapters=[
        ch("g1", "G — the TIGHT set", "2026-11-01",
           ["RFD4-Proteina", "ProteinMPNN"],
           "Generation on a 6-atom hotspot window (P5-P7 ridge) with the "
           "C0 electrostatic rule as the primary screen criterion.",
           "25 designs folded."),
        ch("v1", "V — the read", "2026-11-01",
           ["Boltz-2", "IPSAE"],
           "Standard folds and scoring; no design reaches the strict "
           "gate.",
           "0 strict passers — negative, cause understood (interface "
           "starvation)."),
    ],
)

# ---------------------------------------------------------------- c5
add(
    id="c5-minibinders",
    title="C5 — minibinders",
    date="2026-11-01",
    verdict="30% JDI-like (11 of 37) — tied for the best yield; short "
            "chains hold up and one carries the project's strongest "
            "free-state dependence.",
    best=False,
    scores={},
    summary="Every design so far was a 60-110 residue chain; this campaign "
            "conditioned the same ridge hotspots but constrained the "
            "binder to 30-50 residues. Short, stiff binders are cheaper "
            "to make, easier to keep folded, and concentrate the "
            "interface on fewer contacts — precision over surface.",
    goal="Test whether small binders read this groove as well as large "
         "ones.",
    goal_extra=[
        "Strategy difference: varies binder size (the challenge allows "
        "10-250 aa; nothing forces large binders).",
        "Answers: do 30-50 aa designs reach the same fold quality? "
        "(Yes — 11 of 37 JDI-like.)",
    ],
    verdict_detail="37 designs folded, 11 JDI-like (30%), 3 passing the "
                    "strict gate. mini-wave1 run-011 design_0001 carries "
                    "the strongest free-state dependence in the project "
                    "(dfree +0.701, and its child +0.752). The short "
                    "format is viable; the yields match the main funnel "
                    "per folded design.",
    chapters=[
        ch("g1", "G — the MINI set", "2026-11-01",
           ["RFD4-Proteina", "ProteinMPNN"],
           "Same ridge hotspots as the main funnel, binder length "
           "constrained to 30-50 residues.",
           "37 designs folded."),
        ch("v1", "V — the read", "2026-11-01",
           ["Boltz-2", "IPSAE"],
           "Standard folds and scoring; the minibinders fold cleanly and "
           "the best one tops the dependence axis.",
           "3 strict passers; the dependence champion of the project."),
    ],
)

# ---------------------------------------------------------------- c6
add(
    id="c6-optimization",
    title="C6 — the optimization loop (children)",
    date="2026-11-01",
    verdict="The redesign preserves stability (apo folds equal or better "
            "than the parents) but naturalization erodes the "
            "discrimination signal in 8 of 10 children — the specificity "
            "lives in the exact sequence, not the interface geometry "
            "alone.",
    best=False,
    scores={},
    summary="After the campaigns reported, the best designs across all of "
            "them became parents: ProteinMPNN sequence design with the "
            "binding interface frozen (atoms within 8 A of the target "
            "held fixed) produced 8 children per parent, plus an apo-fold "
            "stability check (each binder folded alone). 80 children "
            "folded against G12D; the best child of each parent then went "
            "through the three-state panel.",
    goal="The cheapest remaining source of improvement: sequence-level "
         "polish around a proven interface.",
    goal_extra=[
        "Strategy difference: no new backbone — it optimizes the existing "
        "winners' sequences for stability and expressibility.",
        "Answers: does a naturalized surface keep the specificity? "
        "(Mostly no — a genuinely useful negative.)",
    ],
    verdict_detail="6 of 10 parents got children equal-or-better on the "
                    "G12D reads (best gain +0.08 i_pDAE). All 20 apo "
                    "folds read pLDDT 0.93-0.97, children consistently "
                    "slightly above their parents. But the WT "
                    "discrimination collapsed in 8 of 10 children — a "
                    "frozen interface is not enough; boltz reads "
                    "naturalized sequences as more confident on every "
                    "state. Two exceptions kept the dual signal: wave1-pep "
                    "run-007 design_0000's child c6 (dWT +0.349 / dfree "
                    "+0.350, submission 3) and wave2-pep run-009 "
                    "design_0007's child c2 (dWT +0.347, submission 4). "
                    "Several children improved the dependence axis "
                    "(dfree up to +0.752).",
    chapters=[
        ch("g1", "G — parents and interface extraction", "2026-11-01",
           ["Gemmi", "LigandMPNN"],
           "The ten best designs across C1-C5 became parents; each "
           "parent's complex was extracted to PDB and its interface "
           "residues listed (binder atoms within 8 A of the target).",
           "10 parents prepped."),
        ch("s1", "S — children with the interface frozen", "2026-11-01",
           ["LigandMPNN"],
           "8 children per parent (T=0.1), only non-interface residues "
           "redesigned; 80 children built and folded against G12D.",
           "80 children folded; 6/10 parents matched or beaten."),
        ch("v1", "V — tri-state and the apo check", "2026-11-02",
           ["Boltz-2", "Chai-1"],
           "The best child of each parent folded against WT and the "
           "peptide-free MHC, plus the apo set (each binder folded alone "
           "- the cheapest stability read).",
           "2 children kept the dual signal; stability confirmed across "
           "all 20 apo folds."),
    ],
)

# ---------------------------------------------------------------- c7
add(
    id="c7-rule-mining",
    title="C7 — the mined rules as a tri-state predictor",
    date="2026-11-02",
    verdict="The five design rules mined from our own data predicted 3 new "
            "dual-signal designs out of 8 candidates — a 2.5x lift over "
            "the pool baseline, including the project's best WT "
            "discriminator.",
    best=False,
    scores={},
    summary="A statistical pass over all 40 tri-stated designs found five "
            "features that separate the dual-signal winners from the "
            "rest: length 55-80 aa, low serine and polar content, high "
            "helical fraction with few helix breakers, acidic charge, and "
            "a tight HLA-contact budget in the generator pose. The rules "
            "were applied to every folded design that had never been "
            "tri-stated; eight candidates cleared four of five rules.",
    goal="Turn the accumulated data into a filter that predicts WT "
         "discrimination before spending folds on it.",
    goal_extra=[
        "Strategy difference: no generation and no new tool — it mines "
        "the project's own 417 folded designs for the features of the "
        "winners.",
        "Answers: can our own data predict specificity? (Yes — first "
        "out-of-sample test passed.)",
    ],
    verdict_detail="3 of 8 candidates tri-stated as dual-signal (38% vs "
                    "the 15% pool baseline). The top hit, nim-wave3 "
                    "run-021 design_0001, is the project's strongest WT "
                    "discriminator (dWT +0.457, dfree +0.603) and its "
                    "most stable design (apo pLDDT 0.981) — submission "
                    "entry 1. wave2-pep run-024 design_0001 and nim-wave3 "
                    "run-010 design_0002 also entered the submission "
                    "(entries 8 and 11). All 8 candidates show at least "
                    "peptide dependence; zero vetoes.",
    chapters=[
        ch("m1", "M — mine the winners' features", "2026-11-02",
           ["Pandas", "SciPy"],
           "All 40 tri-stated designs joined with composition, secondary-"
           "structure and generator-pose features; effect sizes computed "
           "for the dual-signal set against the rest.",
           "Five rules with a combined 7/7 in-sample hit rate."),
        ch("t1", "T — the out-of-sample test", "2026-11-02",
           ["Boltz-2", "IPSAE"],
           "Rule score >= 4/5 applied to every folded design never "
           "tri-stated; 8 candidates folded against WT and the "
           "peptide-free MHC.",
           "3 new dual-signal designs — the rules passed their first "
           "blind test."),
    ],
)

# ---------------------------------------------------------------- c8
add(
    id="c8-cross-panning",
    title="C8 — cross-panning against the variant peptides",
    date="2026-11-02",
    verdict="Flat at P6 for every design: this instrument cannot resolve "
            "single-point peptide variants — the C0 finding, confirmed at "
            "the variant level.",
    best=False,
    scores={},
    summary="The field's most predictive specificity filter — folding the "
            "designs against single-residue peptide variants — was tested "
            "directly: 42 folds across the 9-mer register, G12V and G12C "
            "for the top 14 designs.",
    goal="Test whether the cross-panning filter works with Boltz-2 as the "
         "instrument.",
    goal_extra=[
        "Strategy difference: a validation campaign — it tests an "
        "instrument, not designs.",
        "Answers: can fold reads separate P6 variants? (No.)",
    ],
    verdict_detail="The G12V/G12C deltas are 0.000-0.068 — flat; the "
                    "instrument is blind to P6 substitutions, exactly as "
                    "C0 established for the WT comparison. No design "
                    "reads cross-reactive (nothing exceeds its G12D "
                    "read), so no red flags — but no discrimination "
                    "evidence either. One consistent side-signal: the "
                    "9-mer register reads lower than the 10-mer in all 14 "
                    "designs (weak register preference). Specificity "
                    "ranking stays on the three-state panel.",
    chapters=[
        ch("g1", "G — the variant states", "2026-11-02",
           ["Boltz-2"],
           "42 folds: the 9-mer register (the flattened decoy), G12V and "
           "G12C, on the top 12 designs plus the 2 best children.",
           "No vetoes; no new signal."),
        ch("v1", "V — the read", "2026-11-02",
           ["Boltz-2", "IPSAE"],
           "Peptide interface reads compared against each design's G12D "
           "baseline.",
           "Filter unusable with this instrument — documented."),
    ],
)

# ---------------------------------------------------------------- c9
add(
    id="c9-genie3",
    title="C9 — the third generator (genie3)",
    date="2026-11-02",
    verdict="0 of 70 folded designs pass — the CA-only route loses the "
            "sidechain information this target needs. A clean, "
            "reproduced negative with the retry path documented.",
    best=False,
    scores={},
    summary="Genie 3 (all-atom SE(3) diffusion, a genuinely different "
            "architecture) was run end to end on the target: 100 "
            "backbones, chain-remapped, sequenced with ProteinMPNN's "
            "CA-only mode, screened on CA-CA geometry, folded. Both "
            "folded slices failed identically.",
    goal="Add a third, independent generator to the portfolio.",
    goal_extra=[
        "Strategy difference: a different architecture entirely — not a "
        "variation of the RFdiffusion line.",
        "Answers: does the third generator transfer to this target? "
        "(Not via the CA-only pipeline.)",
    ],
    verdict_detail="Best fold 0.661 ipTM, peptide reads <= 0.04 across "
                    "70 designs. Diagnosis: genie3 emits CA-only traces "
                    "(one atom per residue), so the pose screen is "
                    "sidechain-blind and the sequence assignment lacks "
                    "interface context — the fold ranking does not "
                    "correlate with the screen share. The retry path is "
                    "documented: fold each backbone with its designed "
                    "sequence first, screen the folded structures, then "
                    "triage.",
    chapters=[
        ch("g1", "G — generate and convert", "2026-11-02",
           ["Genie 3", "Gemmi"],
           "100 backbones in about an hour; the output is a CA trace in "
           "binder-first chain order, remapped to the project layout.",
           "100 backbones, 100 sequence sets."),
        ch("v1", "V — fold both slices", "2026-11-02",
           ["ProteinMPNN", "Boltz-2"],
           "ProteinMPNN CA-only (designing the binder chain only), a "
           "CA-trace pose screen, then folds of the top 30 and a second "
           "slice of 40.",
           "0 of 70 pass; the negative reproduced exactly."),
    ],
)

# ---------------------------------------------------------------- c10
add(
    id="c10-final-selection",
    title="C10 — wave four and the final selection",
    date="2026-11-02",
    verdict="The strongest generation wave of the project (10 of 39 "
            "JDI-like, top i_pDAE 0.870) and the original twenty: 11 "
            "dual-signal designs, 5 affinity champions, 4 validated "
            "champions - all homology-clean, all instrument-validated. "
            "Two repair rounds and one evolution generation then "
            "swapped six weak entries, and the loop's generation 4 "
            "swapped three more (A16K 87.1, E23K 79.5, V24K 68.7). A "
            "final re-cut on 2026-11-04 moved the set onto the "
            "organizers' own epitope gate: six validated gate readers "
            "entered (peptide_read 0.637-0.766) and six entries left. "
            "A final cut on 2026-11-08 ran the organizers' ipSAE gate "
            "(peptide_read >= 0.61) over the twenty: sixteen passed, "
            "three of the four below it were restored on their wild-type "
            "separation and one (E23K) left. The submitted set is "
            "nineteen; the best E-score is -3.75.",
    best=None,
    scores={},
    summary="A final sampling wave (200 designs) produced the project's "
            "strongest affinity reads. Then the protocol's selection ran "
            "over all tri-stated candidates under a composite that "
            "weights the control-validated instruments first (i_pDAE, "
            "ipTM, peptide-free dependence, E-score; WT discrimination "
            "demoted after it failed its own control); vetoes out; the "
            "de-novo homology gate (a 100% antibody "
            "V-region copy was caught and excluded); a diversity cap of "
            "two designs per generation run. Every one of the twenty "
            "then got the full instrument set: three-seed folds, Chai-1 "
            "MSA cross-checks, apo stability, and the homology screen. "
            "Two charge-directed repair rounds (2026-11-02, "
            "2026-11-03) and the evolution loop's first generation "
            "(2026-11-03) replaced six weak entries with stronger "
            "swaps; the loop's generation 4 (2026-11-04) then replaced "
            "three more (A16K 87.1, E23K 79.5, V24K 68.7). The current "
            "order is records/final2/ranking-v2.csv, also written to the "
            "submission file. The set's best E-score is now -3.75 (the "
            "generation-4 swap A16K, past Q15K's -3.65) and its number "
            "one scores 90.5 (the evolution swap Q15K, dWT +0.747 - a "
            "project record); the top four entries all score above 76. "
            "On 2026-11-04 the set was re-cut on the organizers' own "
            "epitope gate: the six strongest gate readers of the "
            "generation-4 pool entered (peptide_read 0.637-0.766, E "
            "-2.60 to -3.20, all three-seed validated) and six entries "
            "left. On 2026-11-08 a two-for-two panel swap brought N71K "
            "and W57K back, then the organizers' ipSAE gate "
            "(peptide_read >= 0.61) was applied: sixteen of the twenty "
            "passed, three of the four below it were restored on their "
            "wild-type separation and one (E23K) left. The submitted "
            "set is nineteen designs; their metrics table is records/"
            "submitted-19-metrics-2026-11-08.csv.",
    goal="Assemble the submitted set under the competition's own ranking "
         "logic and validate every entry.",
    goal_extra=[
        "Strategy difference: the closing campaign — it decides what "
        "gets submitted, not what gets made.",
        "Answers: which nineteen designs carry the strongest combined "
        "evidence? (See the submission.)",
    ],
    verdict_detail="Wave four: 39 folded, 10 JDI-like (the best wave), "
                    "top i_pDAE 0.870. Final twenty: 11 dual-signal "
                    "(dWT up to +0.457, dfree up to +0.769), 5 wave-four "
                    "affinity champions (i_pDAE up to 0.870), 4 validated "
                    "affinity/dependence champions - every one with a "
                    "negative E-score (set best -1.78). Seed medians "
                    "0.960-0.993 (spread <= 0.01), Chai-1 MSA reads "
                    "supporting only (several sit inside the negative "
                    "band), apo pLDDT >= 0.93, zero homology hits at 90% "
                    "identity, zero vetoes. 2026-11-03: after the two "
                    "repair rounds and "
                    "the evolution gen-1 swaps, the set's best E was -3.65 and its number "
                    "one scores 90.5 (the evolution swap Q15K, dWT +0.747 - a project "
                    "record); the top four entries all score above 76. 2026-11-04: the "
                    "loop's generation 4 replaced three more entries (A16K 87.1, E23K "
                    "79.5, V24K 68.7) and the set's best E is now -3.75. "
                    "2026-11-04: the twenty were re-cut on the organizers' epitope "
                    "gate (rerank v4) - six gate passers entered, six entries "
                    "left, and the deliverables were re-verified 20/20/20. "
                    "2026-11-08: a two-for-two panel swap (N71K and W57K "
                    "back) lifted gate compliance to 16 of 20; then the "
                    "organizers' ipSAE gate (peptide_read >= 0.61) was "
                    "applied - sixteen of the twenty passed, three of the "
                    "four below it were restored on their wild-type "
                    "separation and one (E23K) left. The submitted set is "
                    "nineteen designs, 64-98 aa, sixteen above the gate.",
    chapters=[
        ch("w1", "W — wave four", "2026-11-02",
           ["RFD4-Proteina", "Boltz-2"],
           "200 fresh designs on the proven ridge conditioning; 39 pose-"
           "screen passers folded; 10 JDI-like with the strongest "
           "affinity reads of the project.",
           "The best raw-affinity wave."),
        ch("s1", "S — the selection", "2026-11-02",
           ["Pandas", "MMseqs2"],
           "All 65 tri-stated candidates ranked under the competition "
           "protocol; homology gate (SwissProt, 90% identity) and the "
           "diversity cap applied.",
           "Twenty picked with a documented rationale."),
        ch("v1", "V — full instrument coverage", "2026-11-02",
           ["Boltz-2", "Chai-1", "IPSAE"],
           "Three-seed folds, Chai-1 MSA cross-checks, apo stability and "
           "the homology screen for every entry.",
           "All twenty validated; the package frozen."),
        ch("r1", "R — the repair round and the ensembles", "2026-11-02",
           ["MPNN variants", "Boltz-2", "E-score", "BioEmu2"],
           "24 charge-directed variants of the top six (basic swaps at "
           "the aspartate shell, 8-11 A) produced 11 fold-clean E-score "
           "improvements; the strict win (L58K: E -0.96 to -1.78, fold "
           "reads unchanged) replaced its parent and leads the set. "
           "BioEmu2 contact-conditioned ensembles then showed the "
           "reading persists under thermal motion (K58-D6 at 7.4 +- 0.8 A "
           "across 16 frames) while the interface breathes.",
           "The set's final upgrade, and the mechanism's robustness "
           "confirmed."),
        ch("q1", "Q - the liability and charge-clash screens", "2026-11-02",
           ["binderkit liabilities", "clash-check.py"],
           "Two final screens on the submitted twenty. Liabilities "
           "(binderkit assess): 11 designs flagged, all minor - Asp-Pro "
           "cleavage sites, NG deamidation and DG isomerisation motifs, "
           "five hydrophobic runs of 8-10; mini-wave1 run-014 design_0005 "
           "(gravy 1.11) is the one expression risk to watch. Charge "
           "clashes (same-sign charged atoms within 4 A): the set is "
           "electrostatically clean - max 2 same-sign pairs (wave2-pep "
           "run-054 design_0005); 19 of the 20 designs sit at 0-1.",
           "All flagged items minor and recorded; the twenty stand."),
        ch("r2", "R2 - the second repair round", "2026-11-03",
           ["MPNN variants", "Boltz-2", "E-score", "PROPKA"],
           "36 charge-directed variants of the nine weak-E entries; three "
           "beat their parents on the full composite and entered the set. "
           "A58K lifts its design from 62.5 to 80.1 (E -0.46 to -1.77, "
           "interface quality improved); H27K replaces the native-like "
           "shell histidine itself with a lysine - the external review's "
           "observation turned into a design fix - and lifts rank 20 into "
           "the top five (H27K and N71K left the set again in the "
           "2026-11-04 epitope-gate re-cut, C10); N71K charges the residue "
           "nearest the carboxylate "
           "in its design (best dWT of the three, +0.287). One variant "
           "was rejected despite a large E gain (its peptide dependence "
           "collapsed), and five entries resisted repair. The set's top "
           "four entries now all score above 76.",
           "Three swaps; the set's average E-term roughly tripled. All "
           "three then cleared the full instrument set: A58K (seeds "
           "0.971-0.980, spread 0.009; chai 0.801; apo 0.967), H27K "
           "(0.969-0.978, spread 0.009; chai 0.764; apo 0.967), N71K "
           "(0.977-0.981, spread 0.004 - the tightest in the project; "
           "chai 0.769; apo 0.968) - all inside the established "
           "bands."),
        ch("gate", "E - the epitope-gate re-cut", "2026-11-04",
           ["rerank_v4.py", "swap_stars.py"],
           "The twenty were re-cut on the criterion the organizers "
           "name: how often the interface reads the peptide in the "
           "groove. Six designs of the generation-4 pool clear their "
           "archive gate (peptide_read 0.637-0.766) with E -2.60 to "
           "-3.20 and three-seed validation: c7-I13K 0.766 (E -2.63), "
           "Q48K 0.694 (E -2.90), L23K 0.663 (E -3.20), Q54K 0.655 (E "
           "-2.84), A47K 0.650 (E -2.77) and A46K 0.637 (E -2.60). "
           "They replaced six entries: W57K, A58K-F50K, H27K, N71K, "
           "nim-wave3 run-021 design_0001 and mini-wave1 run-011 "
           "design_0001 c5. The submission CSV, the FASTA and the "
           "score file were rewritten by one script and checked "
           "20/20/20 (count, order and sequences matched). The six new "
           "entries carry the v4 composite score (54.7-58.9), which "
           "counts the gate as a term, so their score column and the "
           "v2 scores of the other fourteen are not the same formula.",
           "Six gate passers in, six entries out; the twenty "
           "re-verified in all three files."),
        ch("cut", "F - the final cut to nineteen", "2026-11-08",
           ["IPSAE"],
           "The organizers' ipSAE gate (peptide_read >= 0.61, the mean "
           "peptide ipSAE over the five boltz models) was applied to the "
           "twenty: sixteen passed and four failed. Three of the four "
           "were restored after their reads were audited - L58K-Q15K "
           "0.554, wave2-pep-049 0.596 and wave2-pep-054 0.463 all read "
           "the wild-type peptide near zero, so their separation is "
           "large - and one left. E23K (0.545) was the weakest of the "
           "four on separation (0.232) and reads the wild-type complex "
           "at 0.313, so it fails the mutation-specificity criterion. "
           "The submitted set is nineteen designs, 64-98 aa, 8 campaign "
           "parents and 11 evolution/repair children, 13 unique "
           "backbones; sixteen sit above the gate. The validator passes "
           "19/19.",
           "One design out; the nineteen re-verified in all three files."),
    ],
)

# ---------------------------------------------------------------- c11
add(
    id="c11-wave-five",
    title="C11 — the fifth wave (more of the strongest conditioning)",
    date="2026-11-02",
    verdict="Negative — 200 fresh designs, 30 pose-screen passers, zero "
            "swaps. The affinity-strong designs read positive E (wrong "
            "electrostatics); the one strongly negative design folds "
            "weakly. This conditioning buys interface quality, not the "
            "charge reading.",
    best=False,
    scores={},
    summary="A final generation wave at the campaign with the best "
            "historical yield: 25 calls x 8 designs (zero validation "
            "errors, 22 minutes). All 200 designs went through the pose "
            "screen; 30 passed all three rules and were folded and "
            "E-scored. The best raw reads (ipTM 0.973 / i_pDAE 0.871) "
            "come with E +1.38 — repulsive, the wrong sign for this "
            "target; the only design with E below -1 folds at i_pDAE "
            "0.18. No candidate beats the frozen set's twentieth place.",
    goal="Test whether the strongest-conditioning campaign scales with "
         "more shots.",
    goal_extra=[
        "Strategy difference: quantity at a fixed strategy, judged by "
        "the validated instrument.",
        "Answers: does more of the same produce an E-passing candidate? "
        "(Roughly 1 in 30, and those fold weakly.)",
    ],
    verdict_detail="Best reads of the wave: 0.973/0.871 (E +1.38), "
                    "0.965/0.817 (E +0.20), 0.964/0.749 (E -0.10); the "
                    "single E -1.82 design reads 0.801/0.176. Composite "
                    "estimate ~57 against the set's twentieth place 60.9.",
    chapters=[
        ch("w5", "W — the fifth wave", "2026-11-02",
           ["RFD4-Proteina", "Boltz-2", "E-score"],
           "200 designs generated clean; 30 pose-screen passers folded; "
           "every one E-scored against the frozen set.",
           "Negative — no swaps; the set stands."),
    ],
)

# ---------------------------------------------------------------- c12
add(
    id="c12-salt",
    title="C12 — asking for a direct grip (salt-bridge conditioning)",
    date="2026-11-02",
    verdict="Negative but decisive — asked point-blank to form a salt "
            "bridge to the mutant aspartate, the generator still settles "
            "at 8-10 A. The buried charge cannot be reached; the "
            "field-reading doctrine is confirmed by the tool itself.",
    best=False,
    scores={},
    summary="The RFD4 annotated-CIF schema carries per-atom interaction "
            "conditions that no earlier request used (the catalog lives "
            "in the installed RFD4-Proteina source). The strongest "
            "untried one: saltbridge + hbond written on the D6 "
            "carboxylate oxygens themselves — asking for a direct "
            "interaction with the mutation's own chemical group instead "
            "of an arc near it. The NIM accepted the new column cleanly; "
            "eight pilot designs were generated and folded. Result: no "
            "design formed the interaction. The closest binder atom sits "
            "5.9 A from the carboxylate and the closest charged atom 8+ A "
            "— the ordinary field zone, the same class as the published "
            "JDI's 7.5 A read. The aspartate is ~90% buried with R114 and "
            "Q70 already occupying its interaction capacity; conditioning "
            "cannot override that physics.",
    goal="Ask for the most direct read of the mutation the tooling "
         "offers, and learn whether the buried charge is reachable at "
         "all.",
    goal_extra=[
        "Strategy difference: per-atom interaction conditioning — a "
        "channel never used in any earlier wave.",
        "Answers: can a generator grip the mutant carboxylate directly? "
        "(No — and that is the doctrine's strongest confirmation.)",
    ],
    verdict_detail="Pilot: 8 designs, all folded, zero validation "
                    "errors. Closest binder atom to the carboxylate: "
                    "5.9 A; closest charged atom 8.1 A. The negative-E "
                    "designs fold weakly (i_pDAE 0.03/0.18); the "
                    "affinity-strong ones read positive E. Not scaled "
                    "(~1-in-50 odds for an E-negative with a clean "
                    "interface).",
    chapters=[
        ch("i", "I — the idea", "2026-11-02",
           ["RFD4-Proteina source", "annotated-CIF schema"],
           "The conditioning catalog has per-atom channels beyond "
           "hotspots: hbond, saltbridge, rasa, secondary structure, "
           "pi-stacking, pi-cation. The builder now writes hbond = "
           "ACCEPTOR and saltbridge = NEGATIVE on the D6 carboxylate.",
           "A new request channel, accepted by the NIM."),
        ch("p", "P — the pilot", "2026-11-02",
           ["RFD4-Proteina", "Boltz-2", "E-score"],
           "Eight designs generated and folded; binder atoms measured "
           "against the carboxylate oxygens.",
           "Zero contacts — an 8-10 A floor. The buried charge stays "
           "unreachable."),
    ],
)

# ---------------------------------------------------------------- c13
add(
    id="c13-surrogate-screen",
    title="C13 - the surrogate screen (negative)",
    date="2026-11-03",
    verdict="Negative - the learned screen's own top 50 folded to zero "
            "hits, below the random base rate. A route closed with its "
            "diagnosis: sequence-composition features cannot see where the "
            "charges land after folding.",
    best=False,
    scores={},
    summary="The active-learning idea: train a model on the folded "
            "designs' E_D6 and i_pDAE from sequence-composition features, "
            "then fold only the best of the never-folded pool. Honest "
            "cross-validation first: E_D6 R2 -0.072 / Spearman 0.466 and "
            "i_pDAE R2 0.014 / Spearman 0.254 - the value prediction is "
            "noise, the rank correlation usable but weak. Then the test "
            "that settles it: the top 50 predicted candidates were folded "
            "and E-scored. 0 of 50 pass the strong bar (i_pDAE >= 0.70 and "
            "E <= -1.0) and 0 of 50 pass the soft bar (i_pDAE >= 0.60 and "
            "E <= -0.5), against a historical base rate of about 5-10% and "
            "the repair rounds' 1 in 9. The model's own most confident "
            "call (predicted E -4.88, far outside its training range) "
            "folded to a mediocre interface with a positive E - its "
            "single worst miss.",
    goal="Spend GPU hours only on the candidates a learned screen likes "
         "best.",
    goal_extra=[
        "Strategy difference: the only campaign that tries to replace "
        "folding with a model - it tests a shortcut, not a design idea.",
        "Answers: can a sequence-level screen predict the structural "
        "E-score? (No - and the hand-made pose screen it replaced had "
        "already rejected all 50.)",
    ],
    verdict_detail="The model's single most confident call (tight-wave1 "
                    "run-019 design_0001, predicted E -4.88, far outside "
                    "the training range) folded to a mediocre interface "
                    "with a positive E - its worst miss. Diagnosis: the "
                    "features are composition, the target is where the "
                    "charges end up after folding; the model also learned "
                    "to prefer long, charge-rich sequences - the class "
                    "whose interfaces destabilise when folded (the C4 "
                    "lesson). The 50 folds stay in the pool data. What "
                    "remains sufficient: generate, screen on geometry, "
                    "fold, and rank with the control-validated "
                    "instruments.",
    chapters=[
        ch("t1", "T - training and cross-validation", "2026-11-03",
           ["scikit-learn", "surrogate.py", "es-all.sh"],
           "Gradient-boosted regression on composition features (length, "
           "the 20 amino-acid fractions, net charge, polar and aromatic "
           "fractions, gravy, longest hydrophobic run) against the folded "
           "designs' E_D6 and i_pDAE, read with 5-fold cross-validation.",
           "No value signal (R2 at or below zero); a weak rank "
           "correlation, reported honestly before the test."),
        ch("f1", "F - the top-50 test", "2026-11-03",
           ["Boltz-2", "E-score", "surrogate-test-prep.py"],
           "The top 50 predicted candidates were folded against G12D and "
           "E-scored, then read against the strong and soft bars.",
           "0 of 50 on both bars - below the base rate. The route is "
           "closed."),
    ],
)

# ---------------------------------------------------------------- c14
add(
    id="c14-evolution-gen1",
    title="C14 - the evolutionary loop (generation 1)",
    date="2026-11-03",
    verdict="The loop pays for itself in its first generation: 52 "
            "children folded, 11 qualifying, three swaps entered the set - "
            "and one of them, Q15K, is the project's new number one (90.5, "
            "E -3.65, dWT +0.747, all simultaneous).",
    best=True,
    scores={},
    summary="The first generation of the automated evolutionary loop "
            "(evo.py): for each of the current top-8 parents, basic swaps "
            "at up to six unsampled shell positions (5-13 A from the P6 "
            "aspartate) plus combo mutants that stack known repair hits. "
            "52 variants were folded and E-scored; the qualifiers (ipTM >= "
            "0.93, i_pDAE >= 0.60, E gain >= 0.3) then received the full "
            "tri-state panel and the composite ranking the selection uses. "
            "Validation: three Boltz-2 seeds each (spread 0.004-0.010), "
            "chai 0.763-0.812, apo pLDDT at or above 0.959 - all in band. "
            "Two rejected qualifiers stay in the records: "
            "peprim-001's T53K (84.4 against the W57K's 84.3 - a dead "
            "heat decided by the E-score) "
            "and nim-001 c7's A64K, which carries the project's best "
            "interface quality (i_pDAE 0.853).",
    goal="Close the loop: let the validated instruments choose the parents "
         "and the mutations, and generate the next set automatically.",
    goal_extra=[
        "Strategy difference: the first self-driving campaign - the "
        "fitness function is the calibrated composite, the operators are "
        "the swaps the project had already validated by hand.",
        "Answers: does the repair trick generalise when the loop, not a "
        "human, picks the positions? (Yes - 3 of 52 folds entered the "
        "set.)",
    ],
    verdict_detail="Three swaps earned entry on the full composite: Q15K "
                    "(from L58K; E -1.78 to -3.65, score 90.5, and the "
                    "first design strong on every axis - dWT +0.747, a "
                    "project record, with dfree +0.766 and E -3.65), W57K "
                    "(84.3, E -2.09) and F50K (81.8, E -2.55). 11 of the "
                    "52 children qualified on the fold gate. Rejected "
                    "despite qualifying: peprim-001's T53K sibling (84.4 "
                    "against the W57K's 84.3 - a dead heat decided by the "
                    "validated instrument, E -1.64 vs -2.09), nim-001 c7's "
                    "children A64K (82.5, carrying the project's best "
                    "interface quality at i_pDAE 0.853) and V59K (80.5), "
                    "both just under their parent 82.8, and wave2-024's "
                    "V15K (79.7 vs 79.1, inside the anti-churn threshold). "
                    "Validation: three Boltz-2 seeds each (Q15K spread "
                    "0.006, W57K 0.004, F50K 0.010), chai 0.812 / 0.763 / "
                    "0.793, apo pLDDT 0.963 / 0.963 / 0.959 - all in band. "
                    "The W57K was produced in the round-1 repair but never "
                    "tri-stated then; the loop recovered it as a full "
                    "entrant. Cost: about 2.5 h per generation (52 folds "
                    "plus 16 tri-state arms); the loop continues.",
    chapters=[
        ch("g1", "G - the generation", "2026-11-03",
           ["evo.py", "swap-apply-v5.py"],
           "52 children of the current top-8 parents: basic swaps at up to "
           "six unsampled shell positions (5-13 A from the P6 aspartate) "
           "plus combos stacking the known repair hits. All folded against "
           "G12D and E-scored. The gen-1 combo operator was buggy (it "
           "built from variant templates, so the combo yamls repeated a "
           "variant's sequence); fixed in evo.py before generation 2 "
           "(parent-yaml templates, duplicate-position exclusion, cap 8).",
           "11 children qualify; 3 enter the set."),
        ch("e1", "E - entry on the full composite", "2026-11-03",
           ["Boltz-2", "E-score", "Chai-1"],
           "Each qualifier received the tri-state panel (the WT and "
           "peptide-free arms) and the composite the selection uses; three "
           "swaps beat their parents and replaced them in the set.",
           "Q15K 90.5 (the new number one), W57K 84.3, F50K 81.8."),
        ch("v1", "V - the v5 validation", "2026-11-03",
           ["Boltz-2", "Chai-1", "v5-val.sh"],
           "The three entrants received the full instrument set: three "
           "Boltz-2 seeds, chai-1 with MSAs, an apo fold and the E-score.",
           "All in band (seeds 0.970-0.976, chai 0.763-0.812, apo >= "
           "0.959); the v5 set is fully validated."),
    ],
)

# ---------------------------------------------------------------- c15
add(
    id="c15-evolution-autonomy",
    title="C15 - the loop goes autonomous (generations 2-3)",
    date="2026-11-03",
    verdict="Negative for the set, positive for the method: two unattended "
            "generations promoted nothing - the best child (88.6) stayed "
            "1.9 under its parent (90.5), so the +1.0 margin held - and "
            "generation 3 re-bred generation 2 exactly. That plateau was "
            "read from the identical fold sets and fixed.",
    best=False,
    scores={},
    summary="The loop moved from a hand-driven cycle to an autopilot: each "
            "generation now runs breed, fold, score, tri-state, auto-apply "
            "and the validation queue end to end. Breeding widened to the "
            "current top-16 parents (was top-8) and now reads every "
            "generation tree for shell positions already tried, at up to "
            "five positions per parent. The auto-apply guardrail: a child "
            "replaces its parent only when its composite beats the "
            "parent's by more than 1.0, with one winner per parent family. "
            "A winner then receives the full instrument set (three Boltz-2 "
            "seeds, chai-1, an apo fold) without a prompt. Two generations "
            "ran unattended and the set did not move: 4 qualifiers each, "
            "the best child at 88.6 against its parent 90.5, and the "
            "loop's own apply step reads 'no winners above margin'. The "
            "record set stayed as C10 wrote it through both (Q15K 90.5, "
            "E -3.65). The "
            "failure of the run was the plateau: generation 3's fold names "
            "and score tables were byte-identical to generation 2's. "
            "Generation 4 then ran under the fixed breeder, promoted "
            "three swaps and moved the set (C16).",
    goal="Run the loop without a person in the promotion path and find out "
         "whether it keeps improving on its own.",
    goal_extra=[
        "Strategy difference: the first campaign with no human in the "
        "promotion path - the composite margin and the fold gates decide "
        "what enters the set, not an operator.",
        "Answers: does an autonomous loop keep improving with the "
        "validated operators? (No, not by itself - generation 3 "
        "reproduced generation 2 exactly, a plateau the loop could not "
        "see from the inside.)",
    ],
    verdict_detail="Generations 2 and 3 each folded 28 children and sent 4 "
                    "qualifiers to the tri-state panel: L58K-Q15K-A56K, "
                    "L58K-Q15K-L51K, nim-wave3 c7's I13K and the N71K "
                    "parent's S13K. The best composite was 88.6 "
                    "(L58K-Q15K-A56K, E -3.22, dWT +0.597, dfree +0.710) "
                    "against its parent Q15K on 90.5 - a strong all-axis "
                    "child that the +1.0 anti-churn margin still rejects. "
                    "L58K-Q15K-L51K carries the project's best E read so "
                    "far (-3.74, under the record -3.65) but it loses the "
                    "wild-type arm (dWT -0.010), so its composite lands at "
                    "78.9: the E alone does not buy entry. Running the "
                    "loop's own apply step on both generations returns "
                    "'no winners above margin' and writes nothing. The "
                    "plateau: generation 3's 28 fold names and both score "
                    "tables are byte-identical to generation 2's. The "
                    "pre-fix breeder read only the repair and generation-1 "
                    "trees for tried mutations and drew its parents from a "
                    "fixed list, so it regenerated its own children. The "
                    "fix in evo.py breeds from the top-16 and scans every "
                    "generation tree, so a later generation cannot re-breed "
                    "a predecessor's positions in ignorance. This entry "
                    "records generations 2 and 3 only; generation 4 then "
                    "promoted three swaps and the set moved (C16).",
    chapters=[
        ch("g2", "G2 - the autonomous cycle", "2026-11-03",
           ["evo.py", "autopilot.sh", "evo-apply.py", "val-run.sh"],
           "The autopilot now runs the whole cycle per generation: breed "
           "from the top-16, fold against G12D, E-score, tri-state the "
           "qualifiers, compare the composites and apply a winner, then "
           "queue the validation. The guardrails live in evo-apply.py: a "
           "+1.0 composite margin over the parent's set score, one winner "
           "per parent family, and the fold gates (peptide ipTM at or "
           "above 0.93, i_pDAE at or above 0.60). val-run.sh runs the "
           "swapped designs through three Boltz-2 seeds, chai-1 and an apo "
           "fold on its own. Result: generations 2 and 3 each folded 28 "
           "children and tri-stated 4 qualifiers. The best composite was "
           "88.6 (L58K-Q15K-A56K, E -3.22, dWT +0.597, dfree +0.710) "
           "against its parent Q15K's 90.5, so the +1.0 anti-churn margin "
           "rejected it. L58K-Q15K-L51K holds the best E read so far "
           "(-3.74, under the record -3.65) but loses the wild-type arm "
           "(dWT -0.010) and lands at 78.9.",
           "Two generations ran unattended. Neither promoted a swap."),
        ch("g3", "G3 - the plateau and the fix", "2026-11-03",
           ["evo.py"],
           "Generation 3 wrote 28 fold names and two score tables "
           "byte-identical to generation 2's. Cause: the breeder read only "
           "the repair and generation-1 fold trees for mutations already "
           "tried and drew its parents from a fixed list, so it rebuilt "
           "the same children. The fix in evo.py breeds from the current "
           "top-16 and scans every generation tree, so the tried-position "
           "set grows with the work.",
           "Plateau read from the identical fold sets, fixed before "
           "generation 4."),
    ],
)

# ---------------------------------------------------------------- c16
add(
    id="c16-evolution-gen4",
    title="C16 - the fixed loop's first wins, then a second ceiling (generations 4-20)",
    date="2026-11-04",
    verdict="Positive then negative: the repaired breeder's first "
            "generation, 4, promoted three single-lysine swaps - 67.5 to "
            "87.1, 65.1 to 79.5, 64.1 to 68.7 - all validated and all in "
            "the submission at ranks 2, 4 and 6 of the 2026-11-04 file. "
            "The next eight "
            "generations promoted nothing, and generations 6 to 12 rebuilt "
            "the identical thirteen children: the loop still cannot see "
            "its own repetition, and it cannot breed from its own winners. "
            "The repetition had one cause, and it was fixed after the run: "
            "the breeder's combo operator now walks untried pairs and "
            "skips combos that already exist (evo.py v4). The second "
            "cause - the breeder cannot read the sequence of the designs "
            "the loop itself swapped in - was fixed the same evening: the "
            "parent lookups now fall back to a recursive search over "
            "every era's fold tree, so A16K, E23K and V24K resolve and "
            "the loop can build children of them. The breeder's selection "
            "also moved to the v4 composite, which counts the organizers' "
            "epitope gate. That pool held 18 passers of the gate; six of "
            "them entered the submission on 2026-11-04 (C10). The "
            "loop then ran generations 13 to 20 and promoted nothing, "
            "and generations 15 to 20 rebuilt the same 60 "
            "children. The run was requested for generations 14 to 20 "
            "and ended at the end of that range on 2026-11-05, not at "
            "a convergence rule.",
    best=False,
    scores={},
    summary="The generation-4 run folded 35 children of the current top-16 "
            "parents, sent 26 qualifiers to the tri-state panel (52 arms) "
            "and applied three swaps. A16K lifted mini-wave1 run-014 "
            "design_0005 g12d from 67.5 to 87.1 (E -3.75, the strongest "
            "read in the set, past Q15K's -3.65), E23K lifted nim-wave3 "
            "run-013 design_0003 g12d from 65.1 to 79.5 (E -2.88) and V24K "
            "lifted wave2-pep run-026 design_0003 g12d from 64.1 to 68.7 "
            "(E -1.35). All three passed the v5 validation (three Boltz-2 "
            "seeds 0.972-0.981, chai 0.774-0.814, apo in band) and entered "
            "the submission at ranks 2, 4 and 6 of the 2026-11-04 file. "
            "Generations 5 to 12 then "
            "promoted nothing: each bred 13 or 14 children, none passed "
            "the fold gate, and the apply step wrote nothing. Generations "
            "6 to 12 are byte-identical - the same thirteen fold names and "
            "the same E table in every one - and every build log skips the "
            "three swapped-in winners with 'no sequence found', so the "
            "breeder went blind to its own best designs once the remaining "
            "shell positions were exhausted. The autopilot stopped at "
            "generation 12, the end of the requested range, not at a "
            "convergence rule. Both causes were then fixed and committed "
            "(evo.py v4: the combo operator checks duplicates, and a "
            "recursive parent lookup now reads the sequence of the "
            "swapped-in winners), and the breeder's selection moved to the "
            "v4 composite, which counts the organizers' epitope gate: the "
            "generation-4 pool holds 18 gate passers and six of them are "
            "in the submission (C10). Generations 13 to 20 then ran "
            "back to back with no promotion. Generation 13 built 52 "
            "children and was left incomplete. Generation 14 bred 67 "
            "children in two runs under the v4 ranking, sent 14 "
            "qualifiers to the tri-state panel and promoted nothing. "
            "Generations 15 to 20 bred 60 children each, and all six "
            "child sets are the same: the same 60 fold names, the same "
            "structures, the same E table and the same s1 outcome "
            "inside them (4 children reach the organizer's peptide "
            "gate, 27 interfaces are JDI-like), so the same folds were "
            "paid for six times at about 2.5 h each. Their tri-state "
            "panels agree too: each sent 12 qualifiers (24 arms) and "
            "no winner cleared the margin in any of the six, "
            "generations 19 and 20 included. Generation 20 was the "
            "last of the requested range (generations 14 to 20), so "
            "the run ended there at 14:55 on 2026-11-05 and the loop "
            "still has no plateau rule. The v4 combo dedupe compares "
            "only the current generation's fold directory, which is "
            "empty when the children are written, so the repeated child "
            "set recurred. "
            "Three of the sixteen parents carry a v4 score of -1 (no E "
            "read in the v4 table) and were used anyway. A convergence "
            "stop is still absent and stays in the site-sync TODO.",
    goal="Learn whether the repaired breeder keeps improving the set, and "
         "how far it goes before it stops paying.",
    goal_extra=[
        "Strategy difference: the first fully unattended run on the "
        "repaired breeder - nine generations (4-12) in one sitting, with "
        "no human in the promotion path.",
        "Answers: does generation 4's promotion rate hold? (No - one "
        "winning generation, then sixteen more with no promotion, each "
        "costing about 2.5 h.)",
    ],
    verdict_detail="Generation 4 folded 35 children and 26 cleared the "
                    "fold gate (peptide ipTM at or above 0.93, i_pDAE at "
                    "or above 0.60); the tri-state panel ran 52 arms and "
                    "the apply rule kept one winner per parent family "
                    "above the +1.0 margin, so three of the 26 moved. "
                    "A16K: 67.5 to 87.1 (E -3.75, dWT +0.269, dfree "
                    "+0.574, seed median 0.981, chai 0.814). E23K: 65.1 "
                    "to 79.5 (E -2.88, dWT +0.045, dfree +0.542, seeds "
                    "0.972, chai 0.777). V24K: 64.1 to 68.7 (E -1.35, dWT "
                    "+0.029, dfree +0.046, seeds 0.979, chai 0.774). The "
                    "three parents left the top-20. The generation's "
                    "strongest E read, Y19K at -4.47, did not clear the "
                    "margin against its parent and stayed out. Generation "
                    "4 was restarted twice before its final run (28 and "
                    "56 variants built, then 35 under the current "
                    "parents). Generations 5 to 12: 14, then 13, children "
                    "each, zero qualifiers, no apply. Generations 6 to 12 "
                    "share one child set and one E table byte for byte; "
                    "their build logs skip the three winners ('no sequence "
                    "found, skipped') and the basic-swap operator had no "
                    "new position left, so only the combo operator fired, "
                    "rebuilding the same children it had already built.",
    chapters=[
        ch("g4", "G4 - the generation that paid", "2026-11-04",
           ["evo.py", "evo-tri-auto.py", "evo-apply.py", "val-run.sh"],
           "Generation 4 ran the whole cycle unattended on the repaired "
           "breeder: 35 children of the current top-16, folded against "
           "G12D and E-scored; 26 cleared the fold gate and went to the "
           "tri-state panel (52 arms); the apply step compared composites "
           "under the +1.0 margin and the one-winner-per-family rule, and "
           "swapped three children in.",
           "Three swaps: 67.5 to 87.1, 65.1 to 79.5, 64.1 to 68.7."),
        ch("v4", "V - the three entrants validated", "2026-11-04",
           ["Boltz-2", "Chai-1", "val-run.sh"],
           "The three swaps received the full instrument set on their own: "
           "three Boltz-2 seeds each, chai-1 with MSAs and an apo fold.",
           "All in band (seeds 0.972-0.981, chai 0.774-0.814, apo "
           "recorded); all three stand in the submission."),
        ch("g5", "G5-12 - the second ceiling", "2026-11-04",
           ["evo.py", "autopilot.sh"],
           "Eight further generations ran back to back and promoted "
           "nothing. Each bred 13 or 14 children and none cleared the fold "
           "gate, so the tri-state panel and the apply step saw no "
           "candidate. Generations 6 to 12 are byte-identical, and their "
           "logs show why: the three swapped-in winners are skipped with "
           "'no sequence found', so the breeder cannot make children of "
           "them, and the remaining positions of the other parents were "
           "already tried, leaving only the combo operator - which "
           "rebuilds the same combos without a duplicate check.",
           "Eight generations, zero swaps; the loop did not detect the "
           "repetition."),
        ch("fix", "The breeder rewritten after the run (evo.py v4)",
           "2026-11-04", ["evo.py", "rerank_v4.py"],
           "The byte-identical rebuild had one cause: the combo operator "
           "took the first three known mutations of a parent and rebuilt "
           "that same combo every generation, with no check against what "
           "already existed. The combo operator (evo.py v4) now walks "
           "untried PAIRS of each family's known mutations and skips "
           "a combo file already written in that generation's fold "
           "directory. The later runs show that this check holds inside "
           "one generation only (G13-20). The parent-sequence gap "
           "closed the same "
           "evening: the fold and yaml lookups now fall back to a "
           "recursive search over every fold tree of the project, so the "
           "three swapped-in winners resolve - generation 14's build log "
           "no longer skips them. The breeder also ranks by the v4 "
           "composite (see C17), so it works from the epitope-gate top "
           "instead of the gate-blind v2 ranking. That composite counts "
           "the organizers' epitope gate, and the generation-4 pool it "
           "re-ranks holds 18 passers of the gate (peptide_read >= 0.61, "
           "best 0.766) that the v2 ranking could not see; six of them "
           "entered the submission the same day (C10). One gap stays open "
           "and is recorded in the site-sync TODO: the loop has no "
           "convergence or plateau rule - the autopilot stops only at "
           "the end of the requested generation range.",
           "Combo operator and parent-sequence lookup fixed and "
           "committed; the repeat check holds inside one generation "
           "only (G13-20), and a plateau stop stays open."),
        ch("g13", "G13-20 - the plateau holds", "2026-11-05",
           ["evo.py", "autopilot.sh", "evo-select.py"],
           "The loop ran eight more generations with no human in the "
           "promotion path, one every two to three hours, and promoted "
           "nothing. Generation 13 built 52 children and was left "
           "incomplete. Generation 14 ran twice: the first pass built "
           "nothing, the second bred 67 children from the v4 ranking, "
           "14 cleared the fold gate, the tri-state panel ran 28 arms "
           "and no winner cleared the margin. Generations 15 to 20 bred "
           "60 children each and all six wrote the same child set: the "
           "same 60 fold names, the same structures, the same E table "
           "and the same s1 outcome inside them (4 children reach the "
           "organizer's peptide gate, 27 interfaces are JDI-like), so "
           "the same folds were paid for six times at about 2.5 h each. "
           "All six then sent 12 qualifiers to the tri-state panel "
           "(24 arms) and no winner cleared the margin - generation 19 "
           "and generation 20 cleared none either. Generation 20 was "
           "the last generation of the requested range (14 to 20), so "
           "the run ended there at 14:55 on 2026-11-05 and the loop "
           "stopped without a plateau rule. "
           "The cause sits in the fixed operator: the v4 combo dedupe "
           "skips a combo only when that file already exists in the "
           "current generation's fold directory, which is empty at build "
           "time, so nothing is skipped across generations. Three of the "
           "sixteen parents also carry a v4 score of -1 (no E read in "
           "the v4 table) and stayed in the breed list.",
           "Eight generations, zero promotions; the repeated child set "
           "recurred in six of them."),
    ],
    proteins=[
        {"design": "evomini-wave1__run-014__design_0005__g12d-A16K",
         "phase": "g4", "ipsae_min": 0.663, "iptm": 0.964,
         "note": "from mini-wave1 67.5; E -3.75; seeds 0.981, chai 0.814"},
        {"design": "evonim-wave3__run-013__design_0003__g12d-E23K",
         "phase": "g4", "ipsae_min": 0.600, "iptm": 0.963,
         "note": "from nim-wave3 65.1; E -2.88; seeds 0.972, chai 0.777"},
        {"design": "evowave2-pep__run-026__design_0003__g12d-V24K",
         "phase": "g4", "ipsae_min": 0.682, "iptm": 0.964,
         "note": "from wave2-pep 64.1; E -1.35; seeds 0.979, chai 0.774"},
    ],
)

# ---------------------------------------------------------------- c17
add(
    id="c17-generator-project",
    title="C17 - the hosted black box opens (the custom generator project)",
    date="2026-11-04",
    verdict="Every design on this site starts as a backbone from the hosted "
            "RFD4-Proteina NIM - the one stage this project cannot run, "
            "inspect or fine-tune. That stage is now open, and the local "
            "copy is proven: 32 local designs matched the hosted funnel's "
            "hit rate (6 of 32 JDI-like, 19 percent against about 15 "
            "percent) at about a third of the wall time and with no rate "
            "limits. Two limits are now measured. Raw local designs read "
            "the epitope as weakly as the hosted ones, so specificity still "
            "comes from the repair and evolution stages, not from "
            "generation. The reward-tuned fine-tune is blocked on this "
            "machine: the 12 GB card cannot train through the 435M model at "
            "the ~490-residue complexes at any setting tried. Truncating "
            "the complexes did not move that wall either, and the design "
            "side replaced the training route: composite v4 adds the "
            "organizers' epitope gate as a term, and re-ranking the "
            "generation-4 pool on it found 18 gate passers the v3 "
            "ranking could not see - six of them are in the submission.",
    best=False,
    scores={},
    summary="The generator project: own the model, so the loop can use the "
            "project's own scores as a training signal. The model behind the "
            "hosted NIM is open - nvidia/RFD4-Proteina and its Diffusers "
            "build, BSD 3-Clause, released 2026-10-19, 435.6M parameters - "
            "and it runs in BF16 on the local 12 GB card; the release is "
            "itself a rank-32 LoRA of a pretrain-base, so the fine-tuning "
            "path is the release's own design. Verified locally: a "
            "64-residue binder designed against our G12D pMHC in about one "
            "minute, with all three target chains held fixed (HLA 276 "
            "residues, b2m 99, peptide 10) and one new chain added. Three "
            "pieces support it. The target is verified against the "
            "challenge's own reference, 7OW6 chains A-C with the TCR "
            "removed: b2m and the G12D peptide exact, HLA-A*11:01 at 99.1 "
            "percent, the only gap the disordered C-terminal tail LSSQT. "
            "The wet-lab tables are downloaded for score calibration: ATLAS "
            "1,174 TCR-mutant affinities with dDeltaG, and SKEMPI2 7,085 "
            "mutations, 764 of them TCR/pMHC. The chosen loop is a "
            "RAFT-style LoRA tune of this model: generate, sequence, "
            "co-fold, score with the composite, keep the top-K under the "
            "existing gates, tune on the winners, repeat - about 1.5 to 2 h "
            "per cycle, with the co-folding inside the loop instead of "
            "after it. The tool audit finds boltz 2.2.1 current and confirms "
            "that boltz-2's affinity head covers small molecules only, not "
            "protein-protein, so the E-score stays the specificity "
            "instrument. The baseline batch has now run: 32 local designs "
            "(seeds 1000-1031, about one minute each) went through the full "
            "pipeline - co-fold, s1 screen, E-score - in about 90 minutes, "
            "and 6 of 32 interfaces are JDI-like (ipTM >= 0.8), 19 percent "
            "against the hosted campaign's about 15 percent, best interface "
            "ipTM_pep 0.959. None of them reached the organizer's epitope "
            "gate (peptide_read >= 0.61, best 0.577) and the strong "
            "interfaces carry positive E - the same raw-design behaviour "
            "the hosted funnel showed. A competing generator, BoltzGen, was "
            "evaluated on our target and not adopted: its 8 designs dock "
            "confidently (ipTM_pep 0.965-0.974) but do not engage the "
            "peptide epitope (peptide_read 0.101 max against 0.577, E best "
            "-0.06 against -0.86). The E-score's scope was tested against "
            "wet-lab affinity: a naive whole-interface Coulomb sum does not "
            "track it (Pearson r -0.08 over 12 ATLAS structures with a "
            "median Kd), so the site-specific form stays the validated "
            "instrument. The reward-tuned fine-tune is blocked on this "
            "machine: the first LoRA attempt ran out of memory on the 12 GB "
            "card at the ~490-residue complexes, a 4-bit base loads at 1.2 "
            "GB but training still needs about 26 GiB of activations, and a "
            "six-attempt fork reached the same wall. The fine-tune search "
            "closed on this machine with a truncation test: a 16 percent "
            "cut of the training complexes moved the out-of-memory peak by "
            "0.5 percent, so the ~26 GiB allocation is input-independent "
            "and input shaping cannot reach it. The design-side route "
            "replaced the training loop the same day: composite v4 adds a "
            "20 percent peptide_read term, and re-ranking the generation-4 "
            "pool (104 designs) on it surfaced 18 passers of the "
            "organizers' own archive gate that the v3 composite never "
            "ranked - six of them are now in the submission (C10).",
    goal="Run, inspect and fine-tune the model behind this project's designs, "
         "so the loop uses the project's own scores as the training signal.",
    goal_extra=[
        "Strategy difference: the first workstream that changes the "
        "generator itself rather than the designs it produces. Stages 3 "
        "to 10 (fold, score, repair, evolution, validation) need no "
        "change.",
        "Answers: does an open model exist with the same conditioning? "
        "(Yes - the NIM's own model, BSD 3-Clause.) Does it run at usable "
        "speed on the local 12 GB card? (Yes - about one minute per "
        "design.)",
    ],
    verdict_detail="Scope: the generator only. The local smoke produced a "
                    "64-residue binder on the G12D pMHC with chains A, B "
                    "and C held fixed at 276, 99 and 10 residues and one "
                    "new chain of 64 (data/smoke/pmhc_target.cif). Target "
                    "check: 7OW6 A-C, b2m 99 residues exact, peptide "
                    "VVVGADGVGK exact, HLA-A*11:01 99.1 percent, the "
                    "5-residue disordered tail the only difference. Labels: "
                    "ATLAS 1,174 mutants with dDeltaG and 803 TCR-pMHC "
                    "structures, SKEMPI2 7,085 mutations (764 TCR/pMHC). "
                    "Instrument note: boltz-2 has no protein-protein "
                    "affinity head, so the composite is unchanged. Baseline: "
                    "32 local designs, 6 JDI-like (19 percent), best "
                    "ipTM_pep 0.959, best peptide_read 0.577, no E below "
                    "-1.0. BoltzGen: 8 designs, not adopted (peptide_read "
                    "0.101 max). Calibration: an interface-wide Coulomb sum "
                    "against 12 ATLAS structures, r -0.08. Fine-tune: "
                    "blocked at 12 GB (rank 32 and rank 8 out of memory; a "
                    "4-bit NF4 base loads in 1.2 GB but training needs "
                    "about 26 GiB of activations; six-attempt fork, the "
                    "same wall). Truncation: 379 residues against 449, 520 "
                    "tokens against 620, peak 25.86 against 25.99 GiB. "
                    "Gate term: composite v4, 18 passers of peptide_read "
                    ">= 0.61 in the generation-4 pool. Nothing generated "
                    "by the local model is in the submission; the twenty "
                    "were re-cut on the gate, and no batch design entered "
                    "(C10).",
    chapters=[
        ch("gen", "The generator is open and runs locally", "2026-11-04",
           ["RFD4-Proteina", "rfd4_smoke.py"],
           "The hosted NIM's RFD4-Proteina is public: nvidia/RFD4-Proteina "
           "and the Diffusers build, BSD 3-Clause, released 2026-10-19, "
           "435.6M parameters, 1.74 GB in FP32. It runs in BF16 on the "
           "local 12 GB GPU with the same annotated-CIF conditioning our "
           "NIM requests used, and it emits sequence and all-atom "
           "structure together. The release is itself a rank-32 LoRA of a "
           "pretrain-base, which is the fine-tuning route. Smoke run "
           "(scripts/rfd4_smoke.py): the shipped example first, then our "
           "target - a 64-residue binder against the G12D pMHC in about "
           "one minute, chains A/B/C held fixed at 276/99/10 residues, one "
           "new chain added.",
           "The generator runs locally, about one minute per design."),
        ch("target", "The target verified against the challenge reference",
           "2026-11-04", ["verify_target.py", "align_hla.py"],
           "The challenge's three parts against our local structure, 7OW6 "
           "chains A-C with the TCR removed: beta2-microglobulin exact (99 "
           "residues), the G12D peptide VVVGADGVGK exact, and HLA-A*11:01 "
           "at 99.1 percent identity. The only difference is the disordered "
           "C-terminal tail LSSQT (5 residues), which the crystal does not "
           "resolve and which sits far from the binding groove. Construct "
           "numbering 25-305 maps cleanly onto our chain.",
           "Target confirmed: the binder is designed against the right "
           "surface."),
        ch("labels", "Wet-lab labels for calibrating the scores",
           "2026-11-04", ["ATLAS", "SKEMPI2"],
           "Downloaded under custom-model/data/. ATLAS holds 1,174 "
           "TCR-mutant affinities on pMHC with KD, dG and dDeltaG, plus 803 "
           "TCR-pMHC structures. SKEMPI2 holds 7,085 measured mutation "
           "effects, 764 of them at TCR/pMHC interfaces. The sharpest "
           "external fact: the JDI TCR binds the KRAS G12D decamer on "
           "HLA-A*11:01 at 63 uM, affinity enhancement takes it to 743 pM, "
           "and the wild-type peptide stays at 3.0 uM (PDB 7PB2 and 7OW6 "
           "for G12D, 7OW5 for WT); the paper attributes the selectivity to "
           "indirect electrostatic differences, the thesis this project has "
           "tested all along. The loop's own reward needs no labels - this "
           "data is here to measure how well the scores track real "
           "binding.",
           "Labels in place; the site-specific E-score keeps its sign "
           "control, the composite stays uncalibrated."),
        ch("plan", "The chosen loop: reward-tuned LoRA", "2026-11-04",
           ["Proteina", "ProteinMPNN", "boltz"],
           "The chosen strategy is a RAFT-style loop. Generate N backbones "
           "around the fixed peptide motif; sequence them with ProteinMPNN "
           "or LigandMPNN; co-fold each with boltz; score with the "
           "composite (interface metrics, the tri-state, the E-score); "
           "keep the top-K under the existing gates; LoRA-SFT on the "
           "winners; repeat, with held-out designs as the guard against "
           "reward collapse. One cycle is about 1.5 to 2 h. Rejected "
           "alternatives: RFdiffusion-based particle steering (older "
           "model, porting is real work) and reward backpropagation "
           "through the trajectory (research-grade). Also recorded: an "
           "integrated local pipeline (RFAA or RFdiffusion generator, one "
           "orchestrator) and, later, a parametric helix-bundle generator "
           "that optimizes the pose against the E-score directly. The loop "
           "is drawn out in custom-model/diagram-pipeline.html (the frozen "
           "submission path against the RAFT training loop; the LoRA "
           "adapter is the only trained component).",
           "Plan recorded; the first tuning cycle was attempted and is "
           "blocked on the 12 GB card (see the tune chapter)."),
        ch("batch", "The local baseline, and it matches the hosted funnel",
           "2026-11-04", ["gen_batch.py", "analyze_batch.py", "boltz"],
           "32 designs from the local RFD4-Proteina (seeds 1000-1031, about "
           "one minute each), then the whole pipeline - co-fold, s1 screen, "
           "E-score - in about 90 minutes. Result: 6 of 32 interfaces are "
           "JDI-like (ipTM >= 0.8), 19 percent against the hosted "
           "campaign's about 15 percent, best interface batch1-017 at "
           "ipTM_pep 0.959. The organizer epitope gate (peptide_read >= "
           "0.61) caught none of them: the best read 0.577 (batch1-008), "
           "just under. No design scored E below -1.0, and the strongest "
           "interfaces carry positive E (wrong field direction) - exactly "
           "the raw-design behaviour the hosted funnel showed. Raw "
           "generation is not the bottleneck: the local model matches the "
           "hosted one at about a third of the wall time, with no rate "
           "limits. These 32 designs and their scores are themselves "
           "training material for the reward loop.",
           "Local generation is at parity; specificity stays the rare "
           "commodity."),
        ch("boltzgen", "A competing generator, measured and not adopted",
           "2026-11-04", ["BoltzGen"],
           "BoltzGen (MIT, all-atom binder design) was run on our target: "
           "8 designs through its full six-step pipeline, on a spec that "
           "mirrors the shipped peptide-in-pMHC example, then through our "
           "own funnel after fixing a chain-order mismatch (BoltzGen emits "
           "the binder as chain A; our pipeline expects A = HLA). "
           "Head-to-head with the local batch: its designs dock "
           "confidently (ipTM_pep 0.965-0.974, 8 of 8) but do not engage "
           "the peptide epitope (peptide_read 0.101 max against the local "
           "RFD4's 0.577) and sit flat on the E-score (best -0.06 against "
           "-0.86). Its internal metrics rank these designs as good; the "
           "epitope-specific instruments disagree. Eight designs is a "
           "small sample and its recommended campaign is 10,000 or more, "
           "so this is a plumbing verdict, not a final quality claim - but "
           "nothing here motivates displacing the RFD4, and the training "
           "program proceeds against the RFD4 as planned.",
           "BoltzGen not adopted; the RFD4 stays the generator."),
        ch("calib", "The E-score against wet-lab affinity: a scope found",
           "2026-11-04", ["calibrate_e.py", "ATLAS"],
           "First calibration of the electrostatic instrument against "
           "measured binding. A whole-interface Coulomb sum (E_int) was "
           "computed for 12 ATLAS structures that carry a median Kd "
           "(61 were selected, 12 had usable affinity rows), then compared "
           "with log10 Kd: Pearson r = -0.08. The naive whole-interface "
           "form does not predict measured affinity, so interface-wide "
           "electrostatics is not an affinity proxy here. The site-specific "
           "E-score - charged groups against the P6 aspartate, "
           "distance-dependent dielectric - keeps its one passing control, "
           "the JDI sign check (-0.67), and stays the specificity "
           "instrument. The mutant-versus-wild-type reading is a local "
           "effect, which is the scope note, not a failure of the "
           "instrument.",
           "Scope caveat recorded; the site-specific E-score still passes "
           "its control."),
        ch("oom", "The tune hits the 12 GB wall (honest record)",
           "2026-11-04", ["train_lora_4bit.py", "diffusers", "peft"],
           "The first LoRA fine-tune of RFD4-Proteina used the official "
           "diffusers example on 8 of the best batch1 complexes. Every "
           "configuration failed in the same place, the forward-backward "
           "pass on the ~490-residue complex: rank 32 / alpha 64 and rank "
           "8 / alpha 32, bf16, gradient checkpointing, "
           "expandable_segments on and off. The failing allocation is small "
           "(102 MiB) - the card sits at the edge, not far over. The 4-bit "
           "route fails too: an NF4 base loads in 1.2 GB, a tenth of the "
           "card, but training allocates about 26 GiB of activations, so "
           "the wall is the activations, not the weights. Six verified "
           "fixes (quant configs, peft-versus-transformers helper moves, "
           "HF interface stubs, VAE kwarg leakage) reached the same place. "
           "Conclusion, final for this machine: the 12 GB card cannot "
           "fine-tune this model on our target's complexes at any setting "
           "tried. Options recorded, in order: train on shorter class I "
           "complexes from ATLAS (cheapest, untested), quantized base with "
           "LoRA, or tune a different component - the frozen RFD4 already "
           "generates at parity, so the specificity gap is not a generator "
           "problem.",
           "Fine-tune blocked on 12 GB; the next step needs smaller "
           "complexes or a different component."),
        ch("trunc", "The truncated-complex attempt: the wall does not move",
           "2026-11-04", ["truncate_for_training.py", "train_lora_4bit.py"],
           "The remaining idea was to shrink the training complexes "
           "instead of the model. A truncated dataset was built (binder "
           "+ peptide + full beta2m + HLA residues 1-200, the "
           "groove-carrying part: 379 residues against 449) and the same "
           "4-bit recipe ran on it. At 520 tokens against the full "
           "complex's 620 the out-of-memory peak moved from 25.99 to "
           "25.86 GiB, so a 16 percent length cut moved the peak by 0.5 "
           "percent: the allocation is effectively input-independent at "
           "our sizes, and fine-tuning is not reachable on this card by "
           "input shaping. The design-side route replaced it the same "
           "day - the loop with the v4 composite improved the submission "
           "with no training at all, on the 18 gate passers the v3 "
           "composite could not rank (see the next chapter). The choice "
           "of fallback (shorter class I complexes, a quantized base, or "
           "another component) still needs the owner's decision and is "
           "recorded in the site-sync TODO.",
           "Truncation does not move the wall; the fine-tune needs a "
           "bigger card or a smaller model."),
        ch("rank", "The composite gains the organizer's gate term (v4)",
           "2026-11-04", ["rerank_v4.py"],
           "The v3 composite (30 i_pDAE, 20 ipTM, 20 dfree, 20 E, 10 "
           "dWT) had no term for the surface the organizers name as the "
           "target: the peptide in the groove. Composite v4 keeps the "
           "same shape and adds a 20 percent peptide_read term (25 "
           "i_pDAE, 15 ipTM, 15 dfree, 15 E, 10 dWT, 20 peptide_read), "
           "with a hard veto on a positive E. Re-ranking the "
           "generation-4 pool (104 designs) finds 18 designs that clear "
           "the organizers' own archive gate (peptide_read >= 0.61), "
           "best 0.766, which the v3 ranking could not see. The "
           "evolution loop's own selection moved to this ranking the "
           "same evening, so the loop breeds from the gate top. The "
           "consequence is on the submission table: six of the gate "
           "passers entered the twenty (C10).",
           "The composite can see the organizer's gate, and the loop "
           "breeds from it."),
        ch("audit", "Tool audit and the 2026 field", "2026-11-04",
           ["boltz", "chai-lab", "OpenDDE"],
           "boltz 2.2.1 is the latest release, and its affinity head does "
           "NOT cover protein-protein binding, so there is still no direct "
           "Kd estimate for a binder from boltz: the E-score and the "
           "interface metrics remain the specificity instruments. The open "
           "models released after our NIM campaigns started, all candidates "
           "for the generator slot: BoltzGen (MIT, all-atom binder design), "
           "PXDesign (ByteDance, Apache 2.0, 17 to 82 percent nanomolar "
           "hit rates on seven targets) and Protenix-v2. Chai-2 is "
           "access-gated but reports a peptide-MHC target among its "
           "validated cases. OpenDDE was installed for a second co-folding "
           "opinion and then shelved: it rebooted the host twice, its "
           "retry pass collected 20 complex files and produced no scores, "
           "and it is a binder-versus-nonbinder instrument, not a "
           "G12D-versus-WT one. PXDesign/Protenix-v2 was never run - it "
           "needs conda or Docker and its recommended server sends the "
           "target off-machine - so it stays the backup generator. APBS "
           "is not installed and is an optional post-deadline addition; "
           "Complexa and OpenFold3 were available and unused; no all-atom "
           "MD or FEP run was made, because the BioEmu2 ensembles cover "
           "thermal stability.",
           "boltz cannot give a binder Kd; BoltzGen was then measured on "
           "our target and not adopted (see its chapter). OpenDDE is "
           "shelved, and no unused tool can move the submission's fate."),
        ch("prov", "The provenance record of the top three", "2026-11-04",
           ["PROVENANCE.md"],
           "The chain of the set's best three designs is now written down "
           "end to end (records/final2/PROVENANCE.md): hosted generation, "
           "fold and screens, one repair swap, one evolution swap, then the "
           "full instrument set. Rank 1 L58K-Q15K (Q15K took it to 90.5, E "
           "-3.65), rank 2 A16K (67.5 to 87.1, E -3.75, the set's best "
           "read) and rank 3 W57K (84.3) - the order as this record was "
           "written, before the evening's epitope-gate re-cut moved W57K "
           "out of the set (C10). All three begin at the same "
           "place: a backbone from the hosted generator. Stages 3 to 10 are "
           "already ours or open (boltz, chai-lab, ProteinMPNN, BioEmu2). The "
           "submission's methods text is written from these records "
           "(records/final2/METHODS.md).",
           "Provenance recorded; the single external dependency is the "
           "generator stage, which this campaign now owns."),
    ],
    proteins=[],
)

# ---------------------------------------------------------------- c18
add(
    id="c18-finetune-verdict",
    title="C18 — the fine-tune, and the reading that killed it",
    date="2026-11-07",
    verdict="The 435M release fine-tunes end to end and still produces clean "
            "proteins, but the fine-tuned checkpoint cannot design for this "
            "target: it leaves the binder 14 A from the peptide or inside the "
            "MHC surface. Backbone geometry never showed that. The checkpoint "
            "is withdrawn and the submission is untouched.",
    verdict_detail="100 designs per model, same target, same funnel. "
                   "Binder-to-peptide median 14.2 A fine-tuned against 2.7 A "
                   "pristine. 59 of 100 fine-tuned designs interpenetrate the "
                   "MHC below 1.5 A, which is physically impossible. 0 of 25 "
                   "folded designs pass the organizer gate, best 0.022, "
                   "against 0.577 for the earlier unfrozen batch.",
    best=False,
    scores={},
    summary="The generator project's training half. The release is a rank-32 "
            "LoRA of a pretrain base, so fine-tuning is its own design: the "
            "435M model was tuned on rented A100-80GB silicon for 99 epochs "
            "over the official tutorial test set, with a checkpoint ladder "
            "kept every ten epochs and a volume holding the runs. The tune "
            "completed and the epoch-99 checkpoint came home. Generation then "
            "ran on the local 12 GB card with no cloud cost. The first "
            "comparison looked fine and was wrong: 100 designs per model read "
            "CA-CA bonds 3.76 A fine-tuned against 3.84 A pristine, with zero "
            "broken backbones on both sides. Every one of those metrics is "
            "internal to the generated chain, so a binder that floats away "
            "from its target still scores perfect bond lengths. The placement "
            "check is the one that sees it, it costs no GPU time, and it "
            "reversed the result. The failure mode is conditioning collapse: "
            "the structure priors are broad and over-learned and survive the "
            "tune, while the narrow mapping from target input to chain "
            "position does not. The model still builds a protein. It no "
            "longer reads the epitope. Cloud spend stopped at 24.43 dollars "
            "of the 30 dollar free tier.",
    goal="Stop treating the hosted generator as the ceiling: own the model, "
         "tune it against the project's own scores, and find out whether a "
         "tuned generator designs better binders than the release.",
    goal_extra=[
        "Answers: can the 435M model be fine-tuned at all? (Yes, on rented "
        "silicon — the local card cannot hold it.)",
        "Answers: does a tuned generator design better binders? (No — it "
        "loses the target, while keeping perfect backbone geometry.)",
    ],
    chapters=[
        ch("f1", "F — the tune on rented silicon", "2026-11-05",
           ["RFD4-Proteina"],
           "Local training was closed first, after six verified out-of-memory "
           "attempts on the 12 GB card: the 435M model needs about 26 GiB per "
           "allocation. The tune moved to a rented A100-80GB, ran the official "
           "tutorial recipe against the test dataset, and kept a checkpoint "
           "ladder every ten epochs in a persisting volume.",
           "99 epochs, 4,775 steps, epoch-99 checkpoint downloaded. Spend "
           "24.43 of 30 dollars."),
        ch("f2", "G — the comparison that misled", "2026-11-07",
           ["Boltz-2", "Gemmi"],
           "100 designs were generated from the tuned checkpoint and 100 from "
           "the released weights, then scored with the same geometry pass. "
           "Both sets produced 4-chain complexes, and both were clean.",
           "Fine-tuned 3.76 A CA-CA, 0 broken backbones; pristine 3.84 A, 0 "
           "broken. Read at the time as parity. The reading was internal to "
           "the chain and could not see placement."),
        ch("f3", "P — the placement check that reversed it", "2026-11-07",
           ["Gemmi"],
           "For each generated complex, measure the binder-to-peptide "
           "distance, the peptide contact count, and the closest approach to "
           "the MHC. A real pose sits at 2.5-4 A; below 1.5 A the atoms "
           "interpenetrate, which no real structure does.",
           "Fine-tuned: median 14.2 A from the peptide, 0 peptide contacts, "
           "59 of 100 designs interpenetrating the MHC. Pristine: median 2.7 "
           "A, 59 contact atoms, no clashes. The tuned checkpoint was "
           "withdrawn."),
    ],
    proteins=[],
    viewer=[],
)

# ---------------------------------------------------------------- c19
add(
    id="c19-pristine-batch",
    title="C19 — 100 raw designs, and the test that separates the loop from "
          "the generator",
    date="2026-11-08",
    verdict="Raw generation from the frozen model passes the organizer gate "
            "in 9 of 100 designs, and one of them beats the champion on that "
            "metric. The wild-type test then reverses it: the champions "
            "separate mutant from wild type by 0.65-0.76 while the best raw "
            "design separates them by 0.205. Specificity comes from the "
            "selection loop, not from the generator. The submission stands.",
    verdict_detail="pr-089 reads 0.756 on the gate against the champion's "
                   "0.754, and 0.759 as a three-seed mean against 0.746. Its "
                   "wild-type read is 0.727, so it binds the wild-type peptide "
                   "almost as well as the mutant. The champions read 0.000 to "
                   "0.050 on wild type. The E-score agrees independently: "
                   "-0.28 to +2.15 for the new batch against -2.60 to -3.75 "
                   "for the submitted set. Three instruments, one conclusion.",
    best=False,
    scores={},
    summary="The funnel's own front end, measured end to end. 100 designs from "
            "the frozen release were folded with five diffusion samples each "
            "and scored with the campaign's s1 instrument: 9 pass the "
            "organizer gate against 0 of 32 for the earlier unfrozen batch, "
            "and 27 are JDI-like against 19 percent. The top design beat the "
            "champion on the gate, three seeds, same instrument. That is where "
            "the good news ends. Every candidate was then folded in the "
            "wild-type and peptide-free states, which is the test that decides "
            "the challenge, and the picture inverted: the high gate readers "
            "are the poor discriminators. pr-089 binds the wild-type peptide "
            "at 0.727. The five designs that do pass all three criteria have "
            "wild-type reads of 0.451 to 0.572 against 0.000 to 0.050 for the "
            "submitted champions. The E-score, the campaign's own "
            "electrostatic specificity instrument, agreed without being asked. "
            "The conclusion is the useful part: the generator supplies "
            "candidates, the loop supplies specificity, and a gate read alone "
            "would have promoted a design that fails the second criterion. "
            "Nothing from this batch entered the submission. All of it ran "
            "locally at no cost. The clean two-state panel that followed did "
            "change the submission: it measured the six entries below the "
            "organizer gate against the three designs an independent review "
            "proposed to restore, all from one sequence source in one fold "
            "batch. Two restorations held - N71K at 0.676 and W57K at 0.641, "
            "both separating mutant from wild type far better than the "
            "entries they replace - and one did not, so the swap was made "
            "two-for-two. Gate compliance rose from 14 of 20 to 16 of 20.",
    goal="Test the generator on its own: can raw output from the frozen model "
         "reach submission grade, without the selection loop?",
    goal_extra=[
        "Answers: does raw generation pass the organizer gate? (Yes — 9 of "
        "100, against 0 of 32 before.)",
        "Answers: is raw generation enough? (No — specificity comes from the "
        "loop, and the gate read alone selects the wrong designs.)",
    ],
    chapters=[
        ch("p1", "G — 100 designs through the fold funnel", "2026-11-08",
           ["RFD4-Proteina", "Boltz-2", "Gemmi"],
           "100 raw designs were converted to fold inputs with canonical "
           "chains, folded at five diffusion samples each, and scored. The "
           "fold batch ran 100 of 100 with no failures in about two hours of "
           "local GPU time.",
           "9 of 100 pass the organizer gate; 27 of 100 are JDI-like. pr-089 "
           "reads 0.756, above the champion's 0.754."),
        ch("p2", "S — the three-arm specificity panel", "2026-11-08",
           ["Boltz-2", "Gemmi"],
           "Every gate passer was folded again with the wild-type peptide and "
           "with no peptide at all, and the top three across three seeds. A "
           "design only counts when the mutant arm passes the gate while both "
           "other arms fail it.",
           "pr-089 separates mutant from wild type by 0.029. The submitted "
           "champions separate them by 0.65 to 0.76. Five new designs pass all "
           "three criteria, the best by 0.205."),
        ch("p3", "E — the electrostatic instrument agrees", "2026-11-08",
           ["Python", "Gemmi"],
           "The histidine-aware E-score was run on the new candidates as an "
           "independent check, reading the charge environment around the "
           "mutant aspartate.",
           "Every new design reads -0.28 or higher and places no histidine in "
           "the shell. The champions read -2.60 to -3.75. Third instrument, "
           "same answer: no new design displaces the submitted set."),
    ],
    proteins=[],
    viewer=[],
)

if __name__ == "__main__":
    VIEWERS = {
        "c0-instrument-calibration": ["pos-g12d"],
        "c1-main-funnel": [
            "wave2-pep__run-054__design_0005__g12d",
            "wave1-pep__run-007__design_0000__g12d",
            "wave2-pep__run-024__design_0007__g12d",
            "peprim-wave1__run-012__design_0006__g12d",
            "wave2-pep__run-009__design_0007__g12d",
        ],
        "c2-peptide-only": [
            "wave1-pep__run-033__design_0003__g12d",
            "wave1-pep__run-026__design_0000__g12d",
            "wave2-pep__run-024__design_0001__g12d",
            "nim-wave3__run-010__design_0002__g12d",
        ],
        "c3-natural-reader": [
            "nat-wave1__run-011__design_0004__g12d",
            "nat-wave1__run-015__design_0000__g12d",
            "nat-wave1__run-005__design_0001__g12d",
            "nat-wave1__run-004__design_0001__g12d",
        ],
        "c4-charge-first": [
            "tight-wave1__run-013__design_0000__g12d",
            "tight-wave1__run-003__design_0001__g12d",
            "tight-wave1__run-007__design_0007__g12d",
            "tight-wave1__run-018__design_0005__g12d",
        ],
        "c5-minibinders": [
            "mini-wave1__run-011__design_0001__g12d",
            "mini-wave1__run-014__design_0005__g12d",
            "mini-wave1__run-019__design_0002__g12d",
            "mini-wave1__run-012__design_0006__g12d",
        ],
        "c6-optimization": [
            "wave1-pep__run-007__design_0000__g12d__c6",
            "wave2-pep__run-009__design_0007__g12d__c2",
            "wave2-pep__run-024__design_0007__g12d__c5",
            "mini-wave1__run-011__design_0001__g12d__c5",
        ],
        "c7-rule-mining": [
            "nim-wave3__run-021__design_0001__g12d",
            "wave2-pep__run-024__design_0001__g12d",
            "nim-wave3__run-010__design_0002__g12d",
            "wave1-pep__run-019__design_0004__g12d",
        ],
        "c8-cross-panning": [
            "mini-wave1__run-011__design_0001__g12d__c5__nine",
            "peprim-wave1__run-001__design_0002__g12d__nine",
            "nat-wave1__run-011__design_0004__g12d__c1__g12v",
        ],
        "c9-genie3": ["c9-g3_0", "c9-g3_47", "c9-g3_83"],
        "c10-final-selection": [
            "wave4-pep__run-017__design_0007__g12d",
            "wave4-pep__run-015__design_0000__g12d",
            "wave4-pep__run-007__design_0002__g12d",
            "wave4-pep__run-008__design_0000__g12d",
            "wave4-pep__run-020__design_0007__g12d",
            "repair-wave2-pep__run-016__design_0005__g12d-L58K",
            "repair-wave4-pep__run-007__design_0002__g12d-A58K",
            "repair-nat-wave1__run-011__design_0000__g12d-H27K",
            "repair-nat-wave1__run-011__design_0004__g12d-N71K",
        ],
        "c11-wave-five": [
            "wave5-peprim__run-014__design_0002__g12d",
            "wave5-peprim__run-021__design_0006__g12d",
            "wave5-peprim__run-021__design_0003__g12d",
        ],
        "c12-salt": [
            "wave6-salt__run-001__design_0000__g12d",
            "wave6-salt__run-001__design_0004__g12d",
            "wave6-salt__run-001__design_0002__g12d",
        ],
        "c13-surrogate-screen": [
            "tight-wave1__run-019__design_0001__g12d",
            "wave2-pep__run-025__design_0000__g12d",
            "nat-wave1__run-019__design_0001__g12d",
        ],
        "c14-evolution-gen1": [
            "evorepair-wave2-pep__run-016__design_0005__g12d-L58K-Q15K",
            "evopeprim-wave1__run-001__design_0002__g12d-W57K",
            "evorepair-wave4-pep__run-007__design_0002__g12d-A58K-F50K",
        ],
        "c15-evolution-autonomy": [
            "evoevorepair-wave2-pep__run-016__design_0005__g12d-L58K-Q15K-A56K",
            "evoevorepair-wave2-pep__run-016__design_0005__g12d-L58K-Q15K-L51K",
            "evonim-wave3__run-001__design_0004__g12d__c7-I13K",
        ],
        "c16-evolution-gen4": [
            "evomini-wave1__run-014__design_0005__g12d-A16K",
            "evonim-wave3__run-013__design_0003__g12d-E23K",
            "evowave2-pep__run-026__design_0003__g12d-V24K",
        ],
        "c17-generator-project": [
            "batch1-017",
            "batch1-008",
            "batch1-027",
        ],
        # C18: the same target from both checkpoints. pr-000 is the released
        # model, ft-000 the fine-tune - the binder that floats away.
        "c18-finetune-verdict": [
            "pr-000",
            "ft-000",
        ],
        # C19: the gate winner, the best specific design, and the runner-up.
        "c19-pristine-batch": [
            "pr-089",
            "pr-081",
            "pr-001",
        ],
    }
    for e in EXP:
        e["viewer"] = VIEWERS.get(e["id"], [])
    # the submission set's proteins: the twenty of the live submission file,
    # in submission order. The v2 ranking carries the metrics of the fourteen
    # entries it selected; the six 2026-11-04 epitope-gate additions carry
    # their own reads from the generation-4 pool.
    import csv as _csv
    chal = OUT.parent
    pick_path = chal / "records" / "final2" / "ranking-v2.csv"
    sub_path = chal / "submission" / "submission-05-pmhc.csv"
    g4_path = pathlib.Path.home() / "c5-work" / "evo" / "gen4" / "s1-summary.csv"
    ip = {}
    for src in ("s1", "s1w3", "camp", "c2p", "c6", "s1w4", "repair",
                "evo/gen4"):
        p = pathlib.Path.home() / "c5-work" / src / "s1-summary.csv"
        if p.exists():
            for row in _csv.DictReader(p.open()):
                try:
                    ip[row["design"]] = round(float(row["peptide_read"]), 3)
                except (KeyError, ValueError):
                    pass
    v2 = ({r["design"]: r for r in _csv.DictReader(pick_path.open())}
          if pick_path.exists() else {})
    g4 = ({r["design"]: r for r in _csv.DictReader(g4_path.open())}
          if g4_path.exists() else {})
    if sub_path.exists():
        tier_label = {"dual": "dual-signal", "dwt": "dWT only",
                      "dfree": "dependence", "flat": "affinity"}
        for e in EXP:
            if e["id"] == "c10-final-selection":
                e["proteins"] = []
                for r in _csv.DictReader(sub_path.open()):
                    name = r["name"]
                    v2row = v2.get(name)
                    if v2row:
                        e["proteins"].append({
                            "design": name,
                            "ipsae_min": ip.get(name),
                            "ipdae": float(v2row["g_ipdae"]),
                            "score": float(v2row["score_v2"]),
                            "tier": tier_label.get(v2row["tier"],
                                                   v2row["tier"]),
                            "d_wt": float(v2row["d_wt"]),
                            "d_free": float(v2row["d_free"]),
                        })
                    else:
                        g = g4.get(name) or {}
                        e["proteins"].append({
                            "design": name,
                            "ipsae_min": ip.get(name),
                            "ipdae": (round(float(g["ipdae_pep"]), 3)
                                      if g.get("ipdae_pep") else None),
                            "tier": None,
                            "note": "epitope-gate addition (composite v4)",
                        })
                print(f"proteins: {len(e['proteins'])} submitted designs, "
                      f"reads known for "
                      f"{sum(1 for p in e['proteins'] if p['ipsae_min'] is not None)}")
    ndrop, dropped = clean_all_tools()
    print(f"campaigns: {merge_campaigns()} groups merged, "
          f"{len(EXP)} campaigns remain")
    print(f"tool labels: {ndrop} unrecognised names dropped: {dropped}")
    OUT.write_text(json.dumps({"experiments": EXP}, indent=2,
                              ensure_ascii=False) + "\n")
    print(f"wrote {OUT} ({len(EXP)} experiments, "
          f"{sum(len(e['chapters']) for e in EXP)} chapters, "
          f"{sum(len(e['viewer']) for e in EXP)} viewer designs)")
