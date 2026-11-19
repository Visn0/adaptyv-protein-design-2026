#!/usr/bin/env python3
"""Generate challenges/02-tnfa/lineage.json (v2) — the campaign's experiment
model for the workbench app.

An EXPERIMENT is a methodology + configuration unit (the user's definition):
  - `c2-rfd3`        the RFdiffusion3 campaign (negative; recorded designs)
  - `genie3-campaign` the night run: Genie 3 + ProteinMPNN + Boltz-2, several
                      generations, one page. Its method chapters are the phases
                      (generation, families, evolution, mouse, switch).
Each experiment carries: method chapters (steps + tools + images), ALL proteins
it designed with their scores (negatives kept, grouped by phase), and the
prerendered viewer design list.
"""
import csv
import json
import pathlib
import re
from collections import defaultdict

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH = REPO / "challenges" / "02-tnfa"
SR = pathlib.Path.home() / "c2-work" / "switch-retrofit-01"
OUT = CH / "lineage.json"


# ---- metrics from the archives -------------------------------------------------
def at_site(prefixes, source):
    best = defaultdict(lambda: None)
    site = defaultdict(int)
    n = defaultdict(int)
    for r in csv.reader(open(source)):
        d = r[0].strip()
        if d.startswith(prefixes):
            n[d] += 1
            if r[5].strip() == "True":
                site[d] += 1
                ip = float(r[2])
                if best[d] is None or ip > best[d]:
                    best[d] = ip
    return {d: (best[d], site[d], n[d]) for d in n}


scores_csv = CH / "notes" / "genie3" / "genie3-all-scores.csv"
# human folds: vanilla batches keep the design name; the confirmation batches
# are prefixed (mceh- / dsh- / ds2h-) and their scores belong to the design
HUMAN_RAW = at_site(("genie3-", "bb-d7-", "d7x-", "b2x-", "e1b-", "e2-",
                     "mceh-", "dsh-", "ds2h-",
                     "sr1-", "sr2-", "sr3-", "sr4-", "sr6-"), scores_csv)
HUMAN = {}
for d, v in HUMAN_RAW.items():
    # the confirmation batches insert "h" into the batch prefix:
    # dsh-X = ds-X, mceh-X = mce-X, ds2h-X = ds2-X
    if d.startswith("dsh-"):
        key = "ds-" + d[4:]
    elif d.startswith("mceh-"):
        key = "mce-" + d[5:]
    elif d.startswith("ds2h-"):
        key = "ds2-" + d[5:]
    else:
        key = d
    HUMAN[key] = v

# mouse folds: mc-/wm- carry another design's name; mce-/ds-/ds2- designs are
# folded on mouse under their own name
MOUSE_RAW = at_site(("mc-", "wm-", "mce-", "ds-", "ds2-",
                     "sr1m-", "sr2m-", "sr6m-"), scores_csv)
MOUSE_BY_DESIGN = {}
for d, v in MOUSE_RAW.items():
    if d.startswith(("sr1m-", "sr2m-", "sr6m-")):
        MOUSE_BY_DESIGN[d[:3] + d[4:]] = v        # sr1m-X -> sr1-X
    elif d.startswith(("mc-", "wm-")):
        MOUSE_BY_DESIGN[d[3:]] = v                # mc-X / wm-X -> X
    else:
        MOUSE_BY_DESIGN[d] = v                    # mce-X / ds-X / ds2-X -> itself

PH = {}
for f in ("sr1-ranked.csv", "sr2-ranked.csv", "sr6-ranked.csv"):
    for r in csv.DictReader(open(SR / f)):
        name = r["design"].replace(".pdb", "")
        try:
            PH[name] = float(r["delta_log_Ka"])
        except ValueError:
            pass

archive = {r["design"]: r["binder_sequence"]
           for r in csv.DictReader(open(CH / "notes" / "genie3" / "archive-all-designs.csv"))}

# phase per design prefix (the method chapter a protein belongs to)
PHASE_BY_PREFIX = [
    ("genie3-", "generation"), ("b2-", "generation"), ("bb-d6-", "generation"),
    ("bb-d7-", "d7-family"), ("d7x-", "d7-family"),
    ("e1b-", "evolution"), ("e2-", "evolution"), ("e1-", "evolution"),
    ("mc-", "mouse-check"), ("wm-", "mouse-check"),
    ("mce-", "mouse-directed"), ("mceh-", "mouse-directed"),
    ("ds-", "dualselect-01"), ("dsh-", "dualselect-01"),
    ("ds2-", "dualselect-02"), ("ds2h-", "dualselect-02"),
    ("b2x-", "d12-family"), ("m1-", "mining-01"), ("m2-", "mining-02"),
    ("r3x-", "rbs-batch-03"), ("r3-", "rbs-batch-03"),
    ("sr1m-", "switch-retrofit"), ("sr2m-", "switch-retrofit"), ("sr6m-", "switch-retrofit"),
    ("sr1-", "switch-retrofit"), ("sr2-", "switch-retrofit"), ("sr3-", "switch-retrofit"),
    ("sr4-", "switch-retrofit"), ("sr6-", "switch-retrofit"),
]


def phase_of(design):
    for prefix, phase in PHASE_BY_PREFIX:
        if design.startswith(prefix):
            return phase
    return "other"


def note_of(design):
    if design.startswith("wm-"):
        return "released mouse binder — calibration"
    if design.startswith("mc-"):
        return "champion folded against mouse"
    return None


def proteins_all():
    rows = []
    for design in sorted(archive):
        h = HUMAN.get(design)
        m = MOUSE_BY_DESIGN.get(design)
        ph = PH.get(design)
        rows.append({
            "design": design,
            "sequence": archive[design],
            "phase": phase_of(design),
            "note": note_of(design),
            "human": round(h[0], 3) if h and h[0] is not None else None,
            "human_site": f"{h[1]}/{h[2]}" if h else None,
            "mouse": round(m[0], 3) if m and m[0] is not None else None,
            "mouse_site": f"{m[1]}/{m[2]}" if m else None,
            "ph": round(ph, 3) if ph is not None else None,
        })
    rows.sort(key=lambda r: (-(r["human"] or 0), r["design"]))
    return rows


def c2_proteins():
    """The RFdiffusion3 campaign's designs from its fold runs' summaries."""
    rows = []
    for run in sorted((CH / "runs").glob("*c2-fold*")):
        summary = run / "summary.json"
        if not summary.exists():
            continue
        data = json.loads(summary.read_text())
        for stage in data.get("stages", []):
            design = str(stage.get("design", "")).replace("config_", "").replace(".pdb", "")
            if not design:
                continue
            rows.append({
                "design": design,
                "sequence": None,
                "phase": "rfd3-generation",
                "note": "batch " + ("w1" if "w1" in run.name else "w2"),
                "human": stage.get("ipsae"),
                "human_site": f"{stage.get('n_pass', 0)}/5",
                "ipsae_min": stage.get("ipsae_min"),
                "pdockq2": stage.get("pdockq2"),
                "iptm": stage.get("iptm"),
                "mouse": None, "mouse_site": None, "ph": None,
            })
    rows.sort(key=lambda r: (-(r["human"] or 0), r["design"]))
    return rows


IMG = "viewers/views/"

# ---- the campaign's method chapters (the phases) -------------------------------
UNITS = [
    {
        "id": "calibration", "title": "Calibration — the bars", "date": "2026-10-16",
        "verdict": "baseline", "scores": {"human": None, "mouse": None, "ph": None},
        "summary": "The released campaign re-scored through our pipeline: sets every bar the campaign used.",
        "goal": "Before designing anything, the released Anthropic/Adaptyv campaign (150 TNF-α designs, 13 wet-lab binders) was re-scored with our own Boltz-2 + IPSAE pipeline. This fixed the acceptance bars: ipSAE >= 0.8 for submission-grade, mouse cross-reactivity tracks tightness, and the pipeline itself reproduces the released numbers within ±0.03.",
        "tools": ["Boltz-2", "IPSAE"],
        "steps": [
            {"title": "Re-score six released designs", "text": "Three wet-lab winners and three high-scoring losers folded with the standard protocol. Their ipsae_min_boltz2 reproduced within ±0.03.", "image": None},
            {"title": "Read the outcomes", "text": "The 0.6-0.7 band produced 0/22 binders; >= 0.8 bound at ~26%. Two never-bound designs outscored every winner — the metric is rank-grade, never a promise.", "image": None},
        ],
        "viewer": [],
    },
    {
        "id": "generation", "title": "Generation — Genie 3", "date": "2026-10-17",
        "verdict": "negative", "scores": {"human": 0.25, "mouse": None, "ph": None},
        "summary": "8 Genie 3 designs on the released problem; CA-only sequences capped at 0.25 — the backbone survived.",
        "goal": "Generate binders for the released TNF-α problem (hotspots B102 + D62) with Genie 3, then re-sequence and fold. This generation exposed the CA-only ProteinMPNN trap and produced the d7 backbone that everything later builds on.",
        "tools": ["Genie 3"],
        "steps": [
            {"title": "Generate 8 designs", "text": "Genie 3 (aqlaboratory, 347 MB checkpoint) on the BinderBench problem 10_tnfa. All 8 placed on the designed interface.", "image": None},
            {"title": "CA-only re-sequencing", "text": "ProteinMPNN on CA atoms only — every sequence capped at 0.248 ipSAE. The trap: sequence design needs the full backbone.", "image": None},
            {"title": "The lesson", "text": "Re-sequence the FOLDED backbone with full-backbone ProteinMPNN instead. That fix is what produced the d7 family.", "image": None},
        ],
        "viewer": [],
    },
    {
        "id": "d7-family", "title": "The d7 family", "date": "2026-10-17",
        "verdict": "positive", "scores": {"human": 0.852, "mouse": None, "ph": None},
        "summary": "Full-backbone re-sequencing of the folded d7 backbone: 18 variants 0.63-0.85, champion d7x-t3-3.",
        "goal": "Take the d7 backbone's FOLDED conformation and re-sequence it with vanilla full-backbone ProteinMPNN. The family converged: one backbone, many sequences, all at the designed interface.",
        "tools": ["ProteinMPNN", "Boltz-2", "IPSAE"],
        "steps": [
            {"title": "Extract the folded backbone", "text": "Chain A of the d7 fold becomes the template.", "image": None},
            {"title": "Re-sequence with ProteinMPNN", "text": "vanilla v_48_020, T = 0.1/0.3, several seeds — 18 variants.", "image": None},
            {"title": "Fold and screen", "text": "Every variant co-folded (Boltz-2, 5 samples, seed 42) and screened at the designed two-protomer junction. Champion: d7x-t3-3 (0.832-0.852).", "image": None},
        ],
        "viewer": ["d7x-t3-3", "d7x-t3-1", "bb-d7-3"],
    },
    {
        "id": "evolution", "title": "Directed evolution", "date": "2026-10-17",
        "verdict": "record", "scores": {"human": 0.871, "mouse": None, "ph": None},
        "summary": "Fixed-position mutation around the champions: D47A lifts the record to 0.871; generation 2 converged.",
        "goal": "Mutate the best family members directly (ProteinMPNN with 3 free positions per variant), fold, and keep what improves. The RF-style loop: each generation mutates the winners of the last and re-selects.",
        "tools": ["ProteinMPNN", "Boltz-2", "IPSAE"],
        "steps": [
            {"title": "Generation 1", "text": "24 variants around d7x-t3-3 / d7x-t3-1 / m1-d7b-3. e1b-d7x-t3-3-v6 = champion + ONE substitution (D47A) -> 0.871, the human record.", "image": None},
            {"title": "Generation 2", "text": "Mutants of v6 and the tight d7 members. Converged: no design beat v6; e2-e1b-d7x-t3-3-v6-v2 joined the ladder.", "image": None},
        ],
        "viewer": ["e1b-d7x-t3-3-v6", "e2-e1b-d7x-t3-3-v6-v2"],
    },
    {
        "id": "mouse-check", "title": "Mouse check + calibration", "date": "2026-10-17",
        "verdict": "mixed", "scores": {"human": None, "mouse": 0.872, "ph": None},
        "summary": "The family keeps the designed interface on mouse but degraded; the released mouse binders set the band (0.73-0.89).",
        "goal": "The challenge requires mouse cross-reactivity. Every candidate folded against the mouse construct (aligned window, P06804 85-235). The released mouse-binding winners were folded through the same pipeline to calibrate what a real cross-reactive binder reads.",
        "tools": ["Boltz-2", "IPSAE", "mouse construct P06804 85-235"],
        "steps": [
            {"title": "Build the mouse target", "text": "Human 82-233 -> mouse 85-235 by alignment; the designed site remaps to positions 107 + 67 (human H68 -> mouse Y).", "image": None},
            {"title": "Fold the candidates", "text": "The champions keep the designed interface on mouse but ~0.2 lower; the released mouse binders hold their human scores (0.73-0.89) — our family sat below that band.", "image": None},
            {"title": "The fix", "text": "Cross-reactivity must be selected for, not checked for. Next generation: select on mouse.", "image": None},
        ],
        "viewer": [],
    },
    {
        "id": "mouse-directed", "title": "Mouse-directed redesign", "date": "2026-10-17",
        "verdict": "positive", "scores": {"human": 0.852, "mouse": 0.847, "ph": None},
        "summary": "The d7 backbone re-sequenced and selected ON mouse: mce-14 is the first dual-species hit.",
        "goal": "Re-sequence the d7 backbone (64 sequences) and fold the top 16 against MOUSE first. Select on the harder target; confirm human after. mce-14 came out of this: mouse 0.704-0.847 and human 0.693-0.852, both 5/5 at the designed junction.",
        "tools": ["ProteinMPNN", "Boltz-2"],
        "steps": [
            {"title": "Generate + select on mouse", "text": "64 ProteinMPNN sequences; the 16 best-predicted folded against mouse.", "image": None},
            {"title": "One hit", "text": "mce-14: the only candidate reaching the mouse band. Human retention confirmed on the same binder.", "image": IMG + "mce-14-mouse/mce-14-mouse_interface_view1.png"},
            {"title": "Visual check", "text": "mce-14 hugs the trimer the same way on both species — the pose of the good designs.", "image": IMG + "mce-14-human/mce-14-human_cartoon_view1.png"},
        ],
        "viewer": ["mce-14"],
    },
    {
        "id": "dualselect-01", "title": "Dual-select generation 1", "date": "2026-10-17",
        "verdict": "positive", "scores": {"human": 0.856, "mouse": 0.854, "ph": None},
        "summary": "Mutants of the dual hits: five dual hits; ds-mce-14-v6 (T48S) beats its parent on both targets.",
        "goal": "Fixed-position mutants of mce-14 / m1-d7b-3 / v6, selected with the mouse-first cascade (mouse fold -> promote >= 0.7 -> human confirmation).",
        "tools": ["ProteinMPNN", "Boltz-2"],
        "steps": [
            {"title": "Mouse stage", "text": "All five mce-14 mutants hold mouse at 5/5 (0.839-0.863); one m1-d7b-3 mutant promoted.", "image": None},
            {"title": "Human stage", "text": "All six promoted designs fold 5/5 at-site. ds-mce-14-v6 (one substitution, T48S) = mouse 0.854 / human 0.856 — beats the parent on BOTH targets.", "image": IMG + "dsmce14v6-mouse/dsmce14v6-mouse_interface_view1.png"},
        ],
        "viewer": ["ds-mce-14-v6", "ds-mce-14-v7", "ds-mce-14-v3"],
    },
    {
        "id": "dualselect-02", "title": "Dual-select generation 2", "date": "2026-10-17",
        "verdict": "positive", "scores": {"human": 0.842, "mouse": 0.868, "ph": None},
        "summary": "One step deeper: seven dual hits; ds2-mce-14-v7-v1 sets the mouse record (0.868); combined plateau reached.",
        "goal": "The same cascade around the three best dual designs. The render-based tie-breaker fired on one borderline design (perched pose -> excluded).",
        "tools": ["ProteinMPNN", "Boltz-2", "Mol* (render review)"],
        "steps": [
            {"title": "Mouse stage", "text": "8 of 9 mutants >= 0.847 at-site; ds2-mce-14-v7-v1 = new mouse record 0.868.", "image": None},
            {"title": "Human stage", "text": "All seven promoted fold 5/5 (0.824-0.842). No design beats ds-mce-14-v6's combined profile: the family has plateaued.", "image": None},
        ],
        "viewer": ["ds2-mce-14-v7-v1", "ds2-mce-14-v6-v5"],
    },
    {
        "id": "linkage-check", "title": "pH linkage check — the missing objective", "date": "2026-10-17",
        "verdict": "negative", "scores": {"human": None, "mouse": None, "ph": -0.113},
        "summary": "The family has no pH switch — its natural linkage runs the wrong way (tighter at pH 6.0).",
        "goal": "The challenge ranks pH-selective binding FIRST. The vendored PROPKA linkage scorer (validated blind on FcRn) measured the binding-linked proton release of five lineage folds. All negative: the wrong direction.",
        "tools": ["PROPKA"],
        "steps": [
            {"title": "Score the family", "text": "delta_log_Ka from -0.11 to -0.99 — every design binds more in acid. Objective 1 unclaimable.", "image": None},
            {"title": "The mechanism to retrofit", "text": "A histidine facing a positively charged target residue: neutral at 7.4 (binds), +1 at 6.0 (repelled).", "image": None},
        ],
        "viewer": [],
    },
    {
        "id": "switch-retrofit", "title": "The switch — his retrofit + E33H", "date": "2026-10-18",
        "verdict": "record", "scores": {"human": 0.851, "mouse": 0.872, "ph": 1.738},
        "summary": "Histidine retrofit flips the linkage; the E33H single substitution gives the best design: human 0.849 / mouse 0.847 / switch 54.7x.",
        "goal": "Retrofit the upstream campaign's switch mechanism onto backbones that actually dock: histidines placed facing the interface cations (found in the fold geometry). Round 1 flipped the sign at a binding cost; the alternative-position scan found E33H — a salt-bridge residue converted into the switch — with binding intact on both species.",
        "tools": ["PROPKA", "ProteinMPNN", "Boltz-2"],
        "steps": [
            {"title": "Round 1 — the sign flips", "text": "Nine His mutants; the best (G45H+L37H+S48H) reads +0.877 (7.5x toward 7.4) at a binding cost of ~0.15-0.2.", "image": IMG + "sr2-r2c-human/sr2-r2c-human_interface_view1.png"},
            {"title": "The b-class survives mouse", "text": "sr1-mce-14-b: human 0.659 / mouse 0.703, both 5/5, switch +0.836.", "image": None},
            {"title": "Recovery generations", "text": "Whole-chain resampling (sr3/sr4) collapsed — recorded negative. The reversion scan (sr6) localized the cost to H37.", "image": None},
            {"title": "E33H — the winner", "text": "Converting the Glu33 salt bridge into a histidine: sr2-ds-mce-14-v6-r2c reads human 0.849 / mouse 0.847 / switch +1.738 (54.7x) — all three objectives, one molecule.", "image": IMG + "sr2-r2c-mouse/sr2-r2c-mouse_interface_view1.png"},
        ],
        "viewer": ["sr2-ds-mce-14-v6-r2c", "sr2-ds-mce-14-v6-r2a", "sr2-ds2-mce-14-v7-v1-r2a",
                   "sr6-r37", "sr1-mce-14-b", "ds-mce-14-v6"],
    },
    {
        "id": "d12-family", "title": "The d12 family — second scaffold", "date": "2026-10-17",
        "verdict": "mixed", "scores": {"human": 0.788, "mouse": 0.426, "ph": None},
        "summary": "The independent scaffold from Genie 3 batch 2: strong human interfaces, but mouse-weak.",
        "goal": "Batch 2 (16 Genie 3 designs) was screened the same way; its best backbone (d12, 92-residue binder) was re-sequenced and folded. It passes both legs of the original bar but drops on mouse (0.426) — kept as the independent backup family.",
        "tools": ["ProteinMPNN", "Boltz-2"],
        "steps": [
            {"title": "Batch 2 screening", "text": "16 designs; the d12 backbone re-sequenced with full-backbone ProteinMPNN.", "image": None},
            {"title": "The mouse verdict", "text": "b2x-d12-2: human 0.788 / mouse 0.426 — human-context only; the d7 lineage carries the dual objective.", "image": None},
        ],
        "viewer": ["b2x-d12-2"],
    },
    {
        "id": "mining-01", "title": "Mining-01 — the d7 plateau", "date": "2026-10-17",
        "verdict": "mixed", "scores": {"human": 0.837, "mouse": None, "ph": None},
        "summary": "80 further sequences on both backbones: plateau per the pre-registered rules; two members entered the ladder.",
        "goal": "After the families were established: broaden the sequence space (d7 at T = 0.1/0.3/0.5, d12 at 0.1/0.3), 20 folded. Outcome: no new best >= 0.85 and no worst-fold >= 0.80 — plateau; the d7 family now holds ~30 members.",
        "tools": ["ProteinMPNN", "Boltz-2"],
        "steps": [
            {"title": "Sample wide", "text": "80 sequences across two backbones and three temperatures.", "image": None},
            {"title": "Plateau", "text": "Best new 0.837 (< 0.85 bar). m1-d7b-3 and m1-d7a-4 joined the ladder; the family ceiling was measured.", "image": None},
        ],
        "viewer": ["m1-d7b-3"],
    },
    {
        "id": "mining-02", "title": "Mining-02 — fresh backbones", "date": "2026-10-17",
        "verdict": "negative", "scores": {"human": 0.599, "mouse": None, "ph": None},
        "summary": "The four best untreated backbones re-sequenced: no design reached 0.80 — those backbones are closed.",
        "goal": "Pre-registered search on four fresh backbones (b2-d14, b2-d11, b2-d10, genie3-d0). 24 designs folded. FAIL/STOP per the rules: best 0.599 at-site. No third family exists in the first two batches.",
        "tools": ["ProteinMPNN", "Boltz-2"],
        "steps": [
            {"title": "Fresh backbones only", "text": "The four best untreated backbones from both Genie 3 batches, vanilla MPNN, top-6 folded each.", "image": None},
            {"title": "Closed", "text": "Best: 0.599 at-site (5/5) — a near-miss. Recorded; the two families stand as the only productive scaffolds.", "image": None},
        ],
        "viewer": [],
    },
    {
        "id": "rbs-batch-03", "title": "RBS batch-03 + redesign", "date": "2026-10-17",
        "verdict": "negative", "scores": {"human": 0.23, "mouse": None, "ph": None},
        "summary": "Targeting our own campaign's receptor-binding site: the junction never scores; the r3x redesign confirmed it.",
        "goal": "A test of the alternative epitope (the campaign's own RBS junction): 12 Genie 3 designs at hotspots 78/82/84 + 142, then a full-backbone redesign (r3x, 18 folds). CA-only scores 0.02-0.23; the redesign did not rescue it.",
        "tools": ["Genie 3", "ProteinMPNN", "Boltz-2"],
        "steps": [
            {"title": "RBS batch", "text": "12 designs on the campaign's junction; winner-scale interfaces but low scores.", "image": None},
            {"title": "r3x redesign", "text": "Full-backbone re-sequencing on the three best backbones — still negative. The released problem's surface is the productive one.", "image": None},
        ],
        "viewer": [],
    },
]

# the campaign-level viewer: the designs we actually submit (from the
# competition CSV, so the two can never drift apart)
def submission_names():
    files = [f for f in sorted((CH / "submission").glob("competition-submission-*.csv"))
             if "template" not in f.name]
    if not files:
        return []
    with open(files[-1]) as handle:
        return [row["name"] for row in csv.DictReader(handle)]


CAMPAIGN_VIEWER = submission_names()

C2_CHAPTERS = [
    {
        "id": "rfd3-generation", "title": "Generation — RFdiffusion3", "date": "2026-10-15",
        "tools": ["RFdiffusion3"],
        "text": "RFdiffusion3 (the released checkpoint) generated binder backbones against the released TNF-α problem, in two batches (w1/w2) around the B102/D62 junction and the human groove.",
        "steps": [
            {"title": "Batch w1 + w2", "text": "Backbones under hotspot constraints; several models per design id.", "image": None},
        ],
        "outcome": "40 backbones across the batches.",
    },
    {
        "id": "rfd3-folding", "title": "Folding — Boltz-2 on the local GPU", "date": "2026-10-15",
        "tools": ["Boltz-2"],
        "text": "Each candidate co-folded with the human TNF-α construct: 5 diffusion samples per design, seed 42, on the local RTX 5070.",
        "steps": [
            {"title": "Five samples per design", "text": "The fold is a distribution over poses; the spread across samples is read, not the best row alone.", "image": None},
        ],
        "outcome": "One fold run per design.",
    },
    {
        "id": "rfd3-screening", "title": "Screening — IPSAE at the designed site", "date": "2026-10-15",
        "tools": ["IPSAE"],
        "text": "IPSAE scored every sample at the designed interface (10 Å PAE cutoff); the bar: ipSAE >= 0.6 AND pDockQ2 >= 0.23. Later recalibrated: the submission line moved to 0.8.",
        "steps": [
            {"title": "Score every sample", "text": "fold_metrics.csv per run; the at-site check distinguishes a real interface from an off-site pose.", "image": None},
        ],
        "outcome": "0 of 18 designs cleared the bar at the designed site.",
    },
    {
        "id": "rfd3-outcome", "title": "Outcome — the negative, and what it taught", "date": "2026-10-16",
        "tools": [],
        "text": "The campaign closed as a documented negative: good iPTM, weak interfaces. The lesson shaped everything after: generator choice dominates (Genie 3 8/23 vs RFdiffusion3 1/40 on the calibration), and the acceptance line belongs at 0.8.",
        "steps": [
            {"title": "Recorded, not discarded", "text": "Every design stays in the table below with its score — the negative is part of the campaign's evidence.", "image": None},
        ],
        "outcome": "Closed 2026-10-16; Genie 3 became the generator.",
    },
]

EXPERIMENTS = [
    {
        "id": "c2-rfd3", "title": "C2 campaign — RFdiffusion3", "date": "2026-10-15 → 16",
        "verdict": "negative", "scores": {},
        "verdict_detail": "The campaign's record counts 18 designs and 90 samples across two "
                          "batches; the fold runs that survive in this workspace are listed in "
                          "the generation chapters. Closed as a negative: the generator was "
                          "replaced (Genie 3) and the acceptance bar moved from 0.6 to 0.8.",
        "summary": "The first attempt at the released problem: RFdiffusion3 backbones, Boltz-2 folds, IPSAE screening — closed as a negative. Every recorded design and score kept below.",
        "goal": "Run the released TNF-α problem end to end with RFdiffusion3 as the generator: generate, fold, screen, and judge against the challenge's objectives. The campaign is the baseline the Genie 3 campaign is measured against.",
        "goal_extra": [
            "The brief ranks three objectives: (1) pH-selective human binding (bind at 7.4, none at 6.0), (2) mouse cross-reactivity, (3) affinity.",
            "This campaign tests the first generator (RFdiffusion3) against objective 3 (binding) only — and produced no submission candidate.",
            "Its negative result set the rules for the Genie 3 campaign: full-backbone re-sequencing, the 0.8 acceptance line, and mouse-first selection.",
        ],
        "chapters": C2_CHAPTERS,
        "proteins": c2_proteins(),
        "viewer": [],
    },
    {
        "id": "genie3-campaign", "title": "Genie 3 campaign — the night run", "date": "2026-10-17 → 18",
        "verdict": "record", "best": True,
        "scores": {"human": 0.871, "mouse": 0.872, "ph": 1.738},
        "summary": "One campaign, one methodology (Genie 3 → ProteinMPNN → Boltz-2 → IPSAE), several experiments: 279 designs, from the first 0.25 to the submission set. Every design and score below, experiment by experiment.",
        "goal": "Take the one productive backbone (d7, from Genie 3) and run experiments on it — re-sequencing, dual-species selection, directed evolution, and finally the histidine retrofit for the pH switch. Each experiment answers one objective; they are the sections below.",
        "goal_extra": [
            "The brief ranks three objectives: (1) pH-selective human binding (bind at 7.4, none at 6.0), (2) mouse cross-reactivity, (3) affinity — all three on one molecule.",
            "This experiment answers all three: sr2-ds-mce-14-v6-r2c — human 0.849, mouse 0.847 (both 5/5 at the designed site), pH switch +1.738 (54.7x toward 7.4).",
            "Every experiment has its own section: re-sequencing, mouse-first selection, directed evolution, and the histidine retrofit that flipped the switch.",
            "All numbers are in-silico (Boltz-2, IPSAE, PROPKA); no wet-lab data exists.",
        ],
        "chapters": UNITS,
        "proteins": proteins_all(),
        "viewer": CAMPAIGN_VIEWER,
    },
]

OUT.write_text(json.dumps({"experiments": EXPERIMENTS}, indent=1))
print(f"wrote {OUT}")
for e in EXPERIMENTS:
    print(f"  {e['id']}: {len(e['chapters'])} chapters, {len(e['proteins'])} proteins, "
          f"{len(e['viewer'])} viewer designs")
