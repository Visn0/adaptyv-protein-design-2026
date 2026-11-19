"""Local web app for the workbench: `pdt serve`.

Structure (each page has one job):
    /                    index — select a challenge, nothing else
    /ch/<challenge>      challenge home: the brief + the experiments
    /run/<ch>/<id>       one experiment: goal, steps, settings, results, 3D view
    /run/<ch>/<id>/3d    interactive structure viewer
                         (?file=N&style=cartoon|surface). A multi-model
                         file (an MD trajectory) loads the player instead:
                         play, scrub, and switch cartoon or surface.
    /api/struct/...      raw structure text for viewers
    /run/<ch>/<id>/file  one file from a run directory (the MD player page)
    /ch/<ch>/target      the challenge's target structure (hero viewer)
    /media/...           run media files, with Range support
    /static/...          vendored 3Dmol.js bundle (no network needed)

An experiment is one pipeline run: settings + steps + results. Experiments
never mix their information; chapters inside an experiment fold open and shut.

Every structure shows in a viewer that rotates slowly. The app has no videos.
Viewer styles:
    cartoon  protein ribbon only
    surface  smooth molecular surface only (binder still highlighted)
"""
from __future__ import annotations

import html as _html
import json
import re
import sys
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd

from tools import common
from tools.experiments import runner
from tools.experiments import spec as spec_mod
from tools.report.html import _headline  # same result line as the static hub
from tools import insights
from tools.serve import brief as brief_mod
from tools.serve import viewer3d

STATIC_DIR = Path(__file__).parent / "static"
VIEWER_STYLES = ("cartoon", "surface")

# Short, plain-language facts per challenge (shown on the index and challenge page).
# The home-page challenge cards: one rotating view per card, on its own dark panel.
_CARD_VIEWER_JS = viewer3d.block(
    "document.querySelectorAll('.card3d[data-src]').forEach(function (el) {"
    "  window.pdt3d.mount(el, { bg: 0x0f111f });"
    "});"
)

CHALLENGE_INFO = {
    "01-egfr": {
        "title": "EGFR",
        "tagline": "Design a conditional EGFR binder.",
        "open": False,
        "target": "Human EGFR, domain III (chain A).",
        "conditions": "Bind at pH 6.5. Do not bind at pH 7.4.",
        "goal": "A binder with a histidine pH switch near the epitope.",
        "status": "We could not take part: it closed before this workspace existed.",
        "metrics": ["selectivity", "ipsae", "iptm"],
        "bars": ["dock"],
        "fun_fact": "EGFR was the first growth-factor receptor ever cloned (1984). Antibodies "
                    "against it grew into some of the best-selling cancer drugs of the 2000s.",
    },
    "02-tnfa": {
        "title": "TNF-α",
        "tagline": "Design a conditional TNF-α binder.",
        "open": False,
        "target": "Human TNF-alpha trimer (PDB 1TNF, chains A-C) and mouse TNF-alpha.",
        "conditions": "Bind human at pH 7.4. Do not bind at pH 6.0. Also bind mouse.",
        "goal": "A conditional binder for the receptor-binding site between two protomers.",
        "status": "Closed. Designs submitted.",
        "metrics": ["delta_log_Ka", "ipsae", "pdockq2", "iptm"],
        "bars": ["dock", "coverage", "mouse"],
        "fun_fact": "TNF-α got its name for a strange effect: it kills tumour cells in mice. "
                    "The name stuck decades before its role in inflammation was understood — "
                    "blocking it later became a class of blockbuster drugs.",
    },
    "03-glp1r": {
        "title": "GLP1R",
        "tagline": "Design a GLP1R agonist.",
        "open": False,
        "target": "Human GLP-1 receptor (UniProt P43220, residues 24-432; ECD and ECD-TMD junction).",
        "conditions": "Agonist design.",
        "goal": "A binder that binds the receptor and activates it (cAMP reporter).",
        "status": "Closed. Campaigns complete.",
        # the metrics that score the designs (see tools/insights.py METRICS)
        "metrics": ["activation", "ipsae_min", "pdockq2", "groove_site", "tm_site",
                    "ecl3_site", "plddt"],
        "bars": [],
        "fun_fact": "The first GLP-1 drug did not come from humans: exendin-4, found in the "
                    "venom of the Gila monster, became exenatide. A lizard bite started the "
                    "drug class.",
        "validation": "Every design is co-folded with Boltz-2 and judged twice. First the "
                      "binding screen: ipSAE and pDockQ2, plus two-domain contact analysis "
                      "against the receptor. Then the activation-geometry gate: the six GLP-1 "
                      "message-region contacts and the insertion depth, calibrated on four "
                      "experimental structures. The final twenty are ranked activation-first "
                      "— total = 2.0·A + 1.5·B + 1.0·E + 0.5·R — after a prescreen against "
                      "known binders and a wrapping-pose check.",
    },
    "04-tfr1": {
        "title": "TfR1",
        "tagline": "Design a conditional TfR1 binder.",
        "open": False,
        "target": "Human transferrin receptor 1 ectodomain homodimer (UniProt P02786, residues "
                  "121-760) and mouse TfR1 (123-763).",
        "conditions": "Bind human at pH 7.4. Do not bind at pH 6.0. Also bind mouse.",
        "goal": "A binder against the apical domain, with a pH switch.",
        "status": "Closed. Campaigns complete.",
        # "human"/"mouse"/"ph" are target-tab ids, not insights.METRICS keys, so the
        # legend rendered empty. No human-vs-mouse selectivity metric exists yet; these
        # are the challenge-agnostic interface numbers that do.
        "metrics": ["ipsae", "pdockq2", "iptm"],
        "bars": [],
        "fun_fact": "Antibodies against TfR1 are the most advanced brain-shuttle route: they "
                    "hitch the receptor's recycling to ferry cargo across the blood-brain "
                    "barrier, which is why the apical domain — and not the transferrin site — "
                    "is the epitope to take.",
    },
    "05-pmhc": {
        "title": "KRAS G12D pMHC",
        "tagline": "Design a mutation-specific pMHC binder.",
        "open": True,
        "target": "KRAS G12D peptide (VVVGADGVGK · KRAS 7–16) on HLA-A*11:01 with "
                  "β2-microglobulin — a three-chain complex. The wild-type peptide "
                  "complex and the peptide-free MHC are the counter-targets.",
        "conditions": "Bind the G12D complex. Do not bind the wild-type complex or the "
                      "peptide-free MHC.",
        "goal": "A binder that reads the mutant position 6 of the peptide and nothing else.",
        "status": "Closed. Designs submitted.",
        "metrics": ["ipsae", "pdockq2", "iptm"],
        "bars": [],
        "fun_fact": "Position 6 — the one residue that separates the two peptides — sits in "
                    "the mobile middle of the peptide: the receptor-free G12D crystal has no "
                    "coordinates for it. With a T-cell receptor bound, the aspartate tucks "
                    "against Arg114 and Gln70 of the HLA.",
    },
}

# Legend content for a challenge with no runs yet (see CHALLENGE_INFO["metrics"]).
DEFAULT_METRICS = ["delta_log_Ka", "ipsae", "pdockq2", "iptm"]
DEFAULT_BARS = ["dock", "coverage", "mouse"]

# What every pipeline stage receives, produces, and needs from a human.
# `strategy` explains the method; `fallback` says what to do without a GPU.
STAGE_INFO = {
    ("screen", "score"): {
        "goal": "Rank folded designs by how well they engage the intended epitope.",
        "strategy": "Per sample: ipTM from the fold, plus the geometry - the worst per-hotspot "
                    "minimum distance and how many binder residues sit at the site. A read "
                    "counts only when both agree (the gate), because ipTM alone promotes a "
                    "binder that folded confidently somewhere else entirely. The reported "
                    "mean is over engaged samples only.",
        "inputs": ["folded complexes (<design>/out/pred.model_idx_*.cif)",
                   "per-model score npz", "hotspot positions from the spec"],
        "outputs": ["restrained-samples.csv (per sample)",
                    "restrained-designs.csv (gated mean per design)"],
        "manual": "The folds themselves come from Chai-1 on a GPU; this stage only reads them.",
        "fallback": "No folds yet: the stage reports waiting_inputs instead of failing.",
    },
    ("fold", "import"): {
        "goal": "Turn a Boltz-2 co-fold into a run: score every sample, keep the numbers.",
        "strategy": "Copy each predicted model and its PAE matrix into the run, run IPSAE at a "
                    "10 A cutoff, and write one row per sample (ipSAE both directions, ipSAE_min, "
                    "pDockQ2, ipTM). The bar is applied here, not chosen afterwards.",
        "inputs": ["Boltz-2 output directory", "IPSAE script"],
        "outputs": ["fold_metrics.csv", "best model in the viewer"],
        "manual": "The fold itself runs on the local CUDA machine (Boltz-2).",
        "fallback": "No GPU: fold with ColabFold on CPU (slow), or queue behind other local runs.",
    },
    ("md", "prepare"): {
        "goal": "Complete the fold and set the two histidine states.",
        "strategy": "PDBFixer adds the terminal groups. The switch histidine becomes HIP "
                    "(protonated, +1) for the low-pH run. It becomes the pose-facing "
                    "neutral tautomer (HIE or HID) for the high-pH run.",
        "inputs": ["folded complex (ColabFold result)", "switch_his residue number"],
        "outputs": ["prepared PDB per pH", "md_pairs.json"],
        "manual": None,
        "fallback": None,
    },
    ("md", "low"): {
        "goal": "All-atom MD with the switch histidine protonated (pH 6.5).",
        "strategy": "AMBER14 force field, GBn2 implicit solvent, 300 K Langevin "
                    "dynamics, 2 fs timestep. Restraints on the backbone during "
                    "equilibration only. Production runs free.",
        "inputs": ["the low-pH prepared structure"],
        "outputs": ["DCD trajectory", "timeseries CSV", "movie frames"],
        "manual": None,
        "fallback": "OpenMM uses the GPU when the platform exists and the CPU otherwise.",
    },
    ("md", "high"): {
        "goal": "All-atom MD with the switch histidine neutral (pH 7.4).",
        "strategy": "The same force field and settings as the low-pH run. Only the "
                    "histidine state differs. The comparison isolates the switch.",
        "inputs": ["the high-pH prepared structure"],
        "outputs": ["DCD trajectory", "timeseries CSV", "movie frames"],
        "manual": None,
        "fallback": "OpenMM uses the GPU when the platform exists and the CPU otherwise.",
    },
    ("md", "compare"): {
        "goal": "Compare the two trajectories and build the player page.",
        "strategy": "One CSV holds both timelines. Charts and number cards show the "
                    "contact occupancy and the interface size per state. The player "
                    "page plays both trajectories in cartoon or surface style.",
        "inputs": ["both timeseries CSVs"],
        "outputs": ["md_compare.csv", "md_summary.json", "md_player.html"],
        "manual": None,
        "fallback": None,
    },
}

# One-paragraph framing shown in the Goal chapter of every experiment page.
PIPELINE_INFO = {
    "screen": {
        "what": "Scores a directory of folded complexes against a named epitope.",
        "strategy": "One stage, driven entirely by the spec: the design-name prefix picks the "
                    "hotspot set, every fold sample gets an ipTM and a geometric engagement "
                    "read, and the engagement gate decides which samples count. Campaigns "
                    "differ by spec params, not by an edited copy of the script.",
    },
    "fold": {
        "what": "Import a Boltz-2 co-fold and score every predicted sample with IPSAE.",
        "strategy": "The fold itself runs on the CUDA machine (Boltz-2, five samples per design). "
                    "This stage copies the models into the run, runs IPSAE on every sample at a "
                    "10 A PAE cutoff, writes one metric row per sample, and carries the "
                    "comparison fold next to it. The interface bar is fixed before "
                    "the run: ipSAE >= 0.6 AND pDockQ2 >= 0.23. A single passing sample is a "
                    "qualified pass, not a binder: the fold is a distribution over poses, so "
                    "the spread across samples is read, not the best row alone.",
    },
    "md": {
        "what": "Real physics: all-atom molecular dynamics of one designed complex (OpenMM).",
        "strategy": "The predicted complex is simulated twice with the same force field. "
                    "The two runs differ in one thing only: the protonation state of the "
                    "designed switch histidine. The comparison shows whether the designed "
                    "contact and the interface hold in real dynamics. This is a physics "
                    "test of the predicted pose. It is not a binding assay.",
    },
}

# The tools behind the numbers: what each one is for, and where it runs.
TOOLS = [
    ("pdt runner", "one process per experiment, one run folder with status, summary, "
                   "artifacts and a report", "local, any machine"),
    ("PROPKA 3.5.1", "pKa shifts in the free and the bound state; the linkage formula turns "
                     "them into pH selectivity", "local, CPU"),
    ("RFdiffusion3", "generates the binder backbones under the hotspot and motif constraints",
     "local GPU (RTX 5070)"),
    ("Boltz-2 2.2.1", "co-folds binder and target and returns the PAE matrix the interface "
                      "scores are computed from", "the local GPU"),
    ("IPSAE", "reads the PAE matrix and scores the interface (ipSAE, pDockQ2) per chain pair",
     "local, CPU"),
    ("ProteinMPNN", "designs sequences for a generated backbone (with a histidine bias)",
     "local GPU or CPU"),
    ("Chai-1 0.6.1", "co-folds binder and target under pocket restraints; the restrained read "
                     "is what the campaign screens rank on", "the local GPU"),
    ("ColabFold / AlphaFold2", "independent fold check of a designed sequence",
     "external GPU"),
    ("OpenMM 8.6 + GBn2", "all-atom molecular dynamics in implicit solvent: the real-physics "
                          "check of one predicted pose", "local CPU (OpenCL on the Mac)"),
    ("3Dmol.js", "the rotating structure viewer on every page", "browser, no network"),
]

# Which tools a pipeline actually uses (names from TOOLS).
PIPELINE_TOOLS = {
    "screen": ["pdt runner", "Chai-1 0.6.1", "3Dmol.js"],
    "fold": ["pdt runner", "Boltz-2 2.2.1", "IPSAE", "3Dmol.js"],
    "md": ["pdt runner", "OpenMM 8.6 + GBn2", "3Dmol.js"],
}


def _strategy_html(pipeline: str, stage_names: list[str], spec) -> str:
    """The Strategy chapter: the method, the tools, and what each stage does.

    The chapter replaces the old "Goal" page: a goal says what we want, a
    strategy says how the numbers are produced and with which tools.
    """
    info = PIPELINE_INFO.get(pipeline, {})
    parts: list[str] = []
    if info.get("what"):
        parts.append(f"<div>{esc(info['what'])}</div>")
    if spec is not None and spec.description:
        parts.append(f"<div class='sub'><b>This run</b> {esc(spec.description)}</div>")
    if info.get("strategy"):
        parts.append(f"<div class='sub'><b>Method</b> {esc(info['strategy'])}</div>")

    wanted = set(PIPELINE_TOOLS.get(pipeline) or [])
    tool_rows = "".join(
        f"<div><b>{esc(name)}</b> {esc(role)}"
        f"<div class='sub mono raw'>{esc(where)}</div></div>"
        for name, role, where in TOOLS if name in wanted
    )
    if tool_rows:
        parts.append("<div class='rowline'><h3>Tools</h3></div>")
        parts.append(f"<div class='kv'>{tool_rows}</div>")

    parts.append("<div class='rowline'><h3>Stages</h3></div>")
    for name in stage_names:
        entry = STAGE_INFO.get((pipeline, name)) or {}
        block = [f"<div class='stagecard'><div class='mono raw'>{esc(name)}</div>"]
        if entry.get("goal"):
            block.append(f"<div><b>{esc(entry['goal'])}</b></div>")
        if entry.get("strategy"):
            block.append(f"<div class='sub'>{esc(entry['strategy'])}</div>")
        io = []
        if entry.get("inputs"):
            io.append("in: " + ", ".join(entry["inputs"]))
        if entry.get("outputs"):
            io.append("out: " + ", ".join(entry["outputs"]))
        if io:
            block.append(f"<div class='sub mono raw'>{esc(' · '.join(io))}</div>")
        if entry.get("manual"):
            block.append(f"<div class='sub'><b>human step</b> {esc(entry['manual'])}</div>")
        if entry.get("fallback"):
            block.append(f"<div class='sub'><b>fallback</b> {esc(entry['fallback'])}</div>")
        block.append("</div>")
        parts.append("".join(block))
    if not stage_names:
        parts.append("<div class='sub'>No stages recorded for this run.</div>")
    return "".join(parts)


CARD_LABELS = [
    ("n_designs", "designs"),
    ("best_selectivity_kcal", "best selectivity (kcal/mol)"),
    ("sign_pass", "pass the sign test"),
    ("geometry_pass", "pass the geometry test"),
    ("n_mutants", "variants"),
    ("improved_on_parent", "better than the parent"),
    ("pass_all_filters", "pass all filters"),
    ("n_candidates", "candidates"),
    ("n_passed_hard_filters", "pass the hard filters"),
    ("n_selected", "selected for review"),
    ("n_switch_conserved", "switch-conserved anchors"),
    ("n_switch_conserved_near_groove", "switch sites near the groove"),
    ("n_sites", "motif sites"),
    ("max_span_A", "motif span (A)"),
    ("n_controls", "control systems"),
    ("n_delta_ok", "controls: right delta"),
    ("n_sites_ok", "controls: right site count"),
    ("n_scored", "designs scored"),
    ("n_binding_at_high_pH", "bind at pH 7.4"),
    ("best_delta_log_Ka", "best delta logKa"),
    ("n_backbones", "backbones"),
    ("n_kept", "kept"),
    ("n_backbones_built", "backbones built (upstream)"),
    ("n_backbones_scanned", "backbones scanned"),
    ("n_passed_coverage", "passed the coverage filter"),
    ("n_sequences_designed", "designs folded (MPNN+AF2)"),
    ("n_docked", "docked designs"),
    ("best_iptm", "best ipTM"),
    ("n_submitted", "submitted designs"),
    ("md_prepared_atoms", "prepared atoms"),
    ("md_switch_his", "switch (His → partner)"),
    ("md_start_distance_A", "start distance (A)"),
    ("md_interface_residues", "interface residues"),
    ("md_ns", "nanoseconds per state"),
    ("md_platform", "OpenMM platform"),
    ("md_ns_day", "speed (ns/day)"),
    ("md_presence", "contact present (pH 6.5)"),
    ("md_presence_high", "contact present (pH 7.4)"),
    ("md_presence_delta", "presence drop at pH 7.4"),
    ("md_contacts_mean", "interface contacts (pH 6.5)"),
    ("md_contacts_high", "interface contacts (pH 7.4)"),
    ("md_binder_rmsd", "binder RMSD (A, pH 6.5)"),
    ("md_binder_rmsd_high", "binder RMSD (A, pH 7.4)"),
    ("md_min_distance_A", "mean His–partner distance (A, pH 6.5)"),
    ("md_min_distance_high_A", "mean His–partner distance (A, pH 7.4)"),
]

CSS = """
/* F10: every interactive element had a :hover rule and no focus ring, and the
   section nav's #sN jumps landed under the sticky navbar. */
html { scroll-padding-top: 64px }
.skip { position: absolute; left: -9999px; top: 0; }
.skip:focus { left: 8px; top: 8px; z-index: 20; padding: 8px 18px; border-radius: 999px;
             background: var(--accent); color: #fff; font-size: 13.5px; font-weight: 500; }
a:focus-visible, button:focus-visible, summary:focus-visible {
  outline: 2px solid #0da2e7; outline-offset: 2px; border-radius: 8px;
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important; animation-iteration-count: 1 !important;
    transition-duration: .01ms !important; scroll-behavior: auto !important;
  }
}
@font-face { font-family: 'Geist'; font-weight: 400; font-style: normal; font-display: swap;
             src: url('/static/fonts/geist-400.woff2') format('woff2'); }
@font-face { font-family: 'Geist'; font-weight: 500; font-style: normal; font-display: swap;
             src: url('/static/fonts/geist-500.woff2') format('woff2'); }
@font-face { font-family: 'Geist'; font-weight: 600; font-style: normal; font-display: swap;
             src: url('/static/fonts/geist-600.woff2') format('woff2'); }
@font-face { font-family: 'Geist Mono'; font-weight: 400; font-style: normal; font-display: swap;
             src: url('/static/fonts/geist-mono-400.woff2') format('woff2'); }
@font-face { font-family: 'Geist Mono'; font-weight: 500; font-style: normal; font-display: swap;
             src: url('/static/fonts/geist-mono-500.woff2') format('woff2'); }
:root { color-scheme: dark; --bg: #0b0c14; --panel: rgba(19, 22, 38, .6); --line: #1d2435;
        --line-strong: #2a3550; --text: #f8fafc; --muted: #8a94a6; --accent: #0da2e7;
        --green: #34d399; --amber: #f5a623; --violet: #a78bfa; }
* { box-sizing: border-box; }
body { margin: 0 auto; max-width: 2000px; padding: 0 22px 72px;
       background-color: var(--bg); color: var(--text); font-size: 15px; line-height: 1.6;
       font-family: 'Geist', -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
       background-image:
         linear-gradient(rgba(29, 36, 53, .30) 1px, transparent 1px),
         linear-gradient(90deg, rgba(29, 36, 53, .30) 1px, transparent 1px);
       background-size: 34px 34px; }
h1 { font-size: 38px; font-weight: 500; letter-spacing: -1.4px; margin: 6px 0 2px; }
h2 { font-size: 22px; font-weight: 600; letter-spacing: -.6px; margin: 24px 0 6px; }
h3 { font-size: 16px; font-weight: 600; letter-spacing: -.3px; margin: 14px 0 3px; }
.sub { color: var(--muted); font-size: 12.5px; line-height: 1.5; }
.eyebrow, .mono { font-family: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
                  font-size: 11.5px; letter-spacing: .08em; text-transform: uppercase;
                  color: var(--muted); }
.lead { font-size: 16.5px; color: #e6ebf2; max-width: 640px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code { font-family: 'Geist Mono', ui-monospace, Menlo, monospace; background: rgba(19, 22, 38, .9);
       border: 1px solid var(--line); padding: 1px 6px; border-radius: 6px; font-size: 12px; }
.chip { display: inline-block; padding: 2px 12px; border-radius: 999px; border: 1px solid var(--line);
        background: rgba(19, 22, 38, .8); color: #cbd5e1;
        font-family: 'Geist Mono', ui-monospace, Menlo, monospace; font-size: 11px;
        letter-spacing: .07em; text-transform: uppercase; }
.chip.open { color: var(--green); border-color: rgba(52, 211, 153, .35);
             background: rgba(52, 211, 153, .08); }
.chip.closed { color: var(--muted); }
.badge { display: inline-block; padding: 2px 11px; border-radius: 999px; font-size: 11px;
         font-family: 'Geist Mono', ui-monospace, Menlo, monospace; letter-spacing: .06em; }
.badge.done { color: var(--green); background: rgba(52, 211, 153, .12); }
.badge.failed { color: #f87171; background: rgba(248, 113, 113, .12); }
.badge.running { color: var(--accent); background: rgba(13, 162, 231, .12); }
.badge.waiting_inputs { color: var(--amber); background: rgba(245, 166, 35, .12); }
.badge.reference { color: var(--violet); background: rgba(167, 139, 250, .12); }
/* Verdict chips: what a run proves, and what it does not. */
.vchip { display: inline-block; padding: 2px 11px; border-radius: 999px; font-size: 11.5px;
         font-weight: 600; font-family: 'Geist Mono', ui-monospace, Menlo, monospace; letter-spacing: .04em; }
.vchip { color: var(--text); background: rgba(148, 163, 184, .14); }
.verdict { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin: 10px 0 2px; }
.verdict .basis { margin-left: auto; }
/* Legends: what the colours mean and which direction each number wants. */
.legend { border: 1px solid var(--line); border-radius: 14px; background: var(--panel);
          padding: 12px 16px; margin: 12px 0; }
.mleg { display: flex; align-items: baseline; gap: 10px; padding: 3px 0; flex-wrap: wrap; }
.mleg .mono { color: #dbe2ea; text-transform: none; letter-spacing: 0; font-size: 12px; }
.mono.raw { text-transform: none; letter-spacing: .02em; }
.mleg .dir { font-size: 11px; padding: 1px 9px; border-radius: 999px; border: 1px solid var(--line);
             color: var(--muted); white-space: nowrap; }
.mleg .dir.higher { color: var(--green); border-color: rgba(52, 211, 153, .35); }
.mleg .dir.lower { color: var(--accent); border-color: rgba(13, 162, 231, .35); }
.mleg .dir.range { color: var(--amber); border-color: rgba(245, 166, 35, .35); }
.mleg .swatch { width: 11px; height: 11px; border-radius: 3px; display: inline-block; }
.btn, .navbtn { display: inline-block; padding: 7px 18px; border-radius: 999px;
                border: 1px solid var(--line); background: rgba(19, 22, 38, .9); color: var(--text);
                font-size: 13.5px; font-weight: 500; }
.btn:hover, .navbtn:hover { text-decoration: none; border-color: var(--line-strong); }
.btn.accent { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn.accent:hover { background: #2bb3f0; }
.kv { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 10px 22px;
      margin: 14px 0; }
.kv div { font-size: 13.5px; color: #dbe2ea; }
.kv b { font-family: 'Geist Mono', ui-monospace, Menlo, monospace; font-size: 10.5px;
        letter-spacing: .07em; text-transform: uppercase; color: var(--muted); font-weight: 400;
        display: block; margin-bottom: 2px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px;
        margin: 14px 0; }
.card { display: block; border: 1px solid var(--line); border-radius: 14px; padding: 13px 15px;
        margin: 10px 0; background: var(--panel); }
.card:hover { border-color: var(--line-strong); background: rgba(13, 162, 231, .05); }
a.card { color: inherit; }
a.card:hover { text-decoration: none; }
.card .chipline { display: flex; gap: 8px; margin-bottom: 10px; align-items: center; }
.hublink { color: var(--accent); text-decoration: none; }
.hublink:hover { text-decoration: underline; }
.card3d { height: 168px; margin-top: 14px; border-radius: 12px; border: 1px solid var(--line);
          overflow: hidden; position: relative;
          background: radial-gradient(ellipse at 50% 35%, rgba(29, 36, 53, .55), transparent 70%) #0f111f; }
.card3d canvas { pointer-events: none; }   /* the whole card stays one click target */
.card3d-empty { display: flex; align-items: center; justify-content: center;
                color: var(--muted); font-size: 12.5px; }
.tgt { border: 1px solid var(--line); border-radius: 16px; background: var(--panel);
       overflow: hidden; margin: 12px 0; }
.tgt-tabs { display: flex; gap: 2px; padding: 6px 8px 0; border-bottom: 1px solid var(--line); }
.tgt-tab { padding: 9px 18px; border: 0; border-bottom: 2px solid transparent; background: none;
           color: var(--muted); font: inherit; font-size: 13.5px; cursor: pointer; }
.tgt-tab:hover { color: var(--text); }
.tgt-tab.cur { color: var(--text); border-bottom-color: var(--accent); }
.tgt-panel { display: none; }
.tgt-panel.cur { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr); }
.tgt-panel > * { min-width: 0; }
.tgt-facts { padding: 20px 22px; min-width: 0; }
.tgt-head { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.tgt-head h3 { margin: 0; font-size: 19px; letter-spacing: -.3px; }
.tgt-sec { margin-top: 16px; }
.tgt-sechead { display: flex; align-items: center; justify-content: space-between; gap: 12px;
               margin-bottom: 8px; font-family: 'Geist Mono', ui-monospace, monospace; font-size: 10px;
               letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.tgt-sechead a { color: var(--accent); text-decoration: none; }
.tgt-copy { border: 1px solid var(--line); background: rgba(19, 22, 38, .8); color: var(--muted);
            border-radius: 999px; padding: 3px 12px; font-size: 11px; cursor: pointer;
            font-family: 'Geist Mono', ui-monospace, monospace; }
.tgt-copy:hover { color: var(--text); border-color: var(--line-strong); }
.tgt-sec pre { max-height: 168px; overflow: auto; margin: 0; padding: 12px 14px;
               border: 1px solid var(--line); border-radius: 12px; background: rgba(9, 11, 20, .55);
               color: var(--muted); font-family: 'Geist Mono', ui-monospace, monospace;
               font-size: 11px; line-height: 1.75; white-space: pre-wrap; word-break: break-all; }
.tgt-view { border-left: 1px solid var(--line); padding: 16px 18px; min-width: 0; }
.tgt3d { height: 430px; border-radius: 12px; border: 1px solid var(--line); overflow: hidden;
         background: radial-gradient(ellipse at 50% 35%, rgba(29, 36, 53, .55), transparent 70%) #0f111f; }
@media (max-width: 980px) { .tgt-panel.cur { grid-template-columns: 1fr; }
  .tgt-view { border-left: 0; border-top: 1px solid var(--line); } .tgt3d { height: 320px; } }
.stats { display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0 10px; }
.stat { background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
        padding: 10px 14px; min-width: 116px; }
.stat b { display: block; font-size: 22px; font-weight: 600; color: var(--text); letter-spacing: -.5px; }
.stat span { font-family: 'Geist Mono', ui-monospace, Menlo, monospace; color: var(--muted);
             font-size: 10px; letter-spacing: .06em; text-transform: uppercase; }
.toolbar { margin: 12px 0; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.toolbar a, .toolbar span.cur, .toolbar select { padding: 4px 12px; border-radius: 999px;
    border: 1px solid var(--line); background: rgba(19, 22, 38, .8); font-size: 12.5px;
    color: var(--text); font-family: 'Geist Mono', ui-monospace, Menlo, monospace; }
.toolbar a { color: var(--accent); }
.toolbar span.cur { color: var(--green); border-color: rgba(52, 211, 153, .4); }
.viewerwrap { max-width: 100%; overflow: auto; margin: 12px 0; }
.viewport { width: 100%; height: 420px; border-radius: 14px; border: 1px solid var(--line);
            background: radial-gradient(ellipse at 50% 35%, rgba(29, 36, 53, .55), transparent 70%);
            margin: 8px 0; }
details.chapter { border: 1px solid var(--line); border-radius: 16px; margin: 12px 0;
                  padding: 2px 20px 4px; background: var(--panel); }
details.chapter > summary { cursor: pointer; padding: 13px 0; font-size: 15px; font-weight: 600;
                            letter-spacing: -.2px; color: var(--text); }
details.chapter > summary .eyebrow { margin-right: 8px; }
details.chapter[open] { padding-bottom: 16px; }
.chapterbody { padding-top: 4px; }
figure { margin: 12px 0; }
video { width: 100%; border-radius: 14px; border: 1px solid var(--line); background: #000; }
.topnav { position: sticky; top: 0; z-index: 10; display: flex; align-items: center; gap: 10px;
          padding: 14px 0 12px; margin-bottom: 8px; border-bottom: 1px solid var(--line);
          background: rgba(11, 12, 20, .85); backdrop-filter: blur(8px); }
.brand { font-weight: 600; color: var(--text); letter-spacing: -.3px; }
a.brand { color: var(--text); }
.navbtn { margin-left: auto; }
.shell { display: grid; grid-template-columns: 230px minmax(0, 1fr); gap: 26px; align-items: start; }
.shell .content { border-left: 1px solid rgba(29, 36, 53, .8); padding-left: 26px; min-height: 60vh; }
.sidebar { position: sticky; top: 76px; border: 1px solid var(--line); border-radius: 16px;
           padding: 12px 12px 14px; background: var(--panel); font-size: 12.5px; }
.sidebar h3 { margin: 2px 0 10px; }
.sideitem { display: block; padding: 6px 10px; border-radius: 999px; color: #cbd5e1;
            margin-bottom: 3px; }
.sideitem:hover { background: rgba(13, 162, 231, .07); text-decoration: none; }
.sideitem .sidelabel { display: inline-flex; flex-direction: column; line-height: 1.3; vertical-align: middle; }
.sideitem .sidedate { color: var(--muted); font-family: 'Geist Mono', ui-monospace, Menlo, monospace;
                      font-size: 10px; letter-spacing: .02em; }
.stagecard { border-left: 2px solid var(--line-strong); padding: 2px 0 6px 12px; margin: 10px 0; }
.sideitem.current { background: rgba(19, 22, 38, .95); color: var(--text);
                    border: 1px solid var(--line-strong); }
.sb-runs { margin-top: 12px; }
.sb-runs summary { cursor: pointer; color: var(--muted); font-size: 10.5px; letter-spacing: .07em;
                   text-transform: uppercase; padding: 6px 10px; }
.sb-runs summary:hover { color: var(--text); }
.dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 8px;
       vertical-align: 1px; }
.dot.done { background: var(--green); }
.dot.waiting_inputs { background: var(--amber); }
.dot.failed { background: #f87171; }
.dot.running { background: var(--accent); }
.hero { padding: 34px 0 6px; }
.rowline { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 12px 0 2px; }
.rowline h2 { margin: 0; }
/* Animations replicated from the proteinbase bundle: ping dot, pulse, fades. */
@keyframes ping { 75%, 100% { opacity: 0; transform: scale(2); } }
@keyframes pulse { 50% { opacity: .5; } }
@keyframes fadeup { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.live { position: relative; display: inline-flex; width: 8px; height: 8px; margin-right: 7px; }
.live .ping { position: absolute; inset: 0; border-radius: 50%; background: var(--green);
              opacity: .75; animation: ping 1s cubic-bezier(0, 0, .2, 1) infinite; }
.live .core { position: relative; width: 8px; height: 8px; border-radius: 50%; background: var(--green); }
.chip.now { color: var(--accent); border-color: rgba(13, 162, 231, .4); background: rgba(13, 162, 231, .08); }
.viewer-loading { display: flex; align-items: center; justify-content: center; color: var(--muted);
                  font-family: 'Geist Mono', ui-monospace, Menlo, monospace; font-size: 11.5px;
                  letter-spacing: .08em; text-transform: uppercase; animation: pulse 2s cubic-bezier(.4, 0, .6, 1) infinite; }
.viewer-fade { opacity: 0; transition: opacity .4s; }
.viewer-fade.on { opacity: 1; }
.hero-split { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0;
              align-items: start; margin-top: 6px; }
.hero-text { animation: fadeup .45s ease both; }
.headline { font-size: 17px; font-weight: 600; margin: 12px 0 6px; letter-spacing: -.2px; }
.hero-desc { color: #c6cdd9; font-size: 14.5px; max-width: 560px; }
.viewer-caption { margin-top: 10px; text-align: center; }
.objectives { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
              gap: 16px; margin: 14px 0; }
.obj { border: 1px solid var(--line); border-radius: 16px; padding: 18px 20px;
       background: var(--panel); animation: fadeup .45s ease both; }
.obj .num { font-family: 'Geist Mono', ui-monospace, Menlo, monospace; font-size: 13px;
            color: var(--muted); letter-spacing: .1em; }
.obj h3 { margin: 10px 0 6px; }
.obj p { font-size: 13.5px; color: #c6cdd9; margin: 0 0 12px; }
.ranking { margin: 10px 0; }
.rk { display: flex; gap: 16px; padding: 13px 0; border-bottom: 1px solid var(--line); }
.rk:last-child { border-bottom: none; }
.rk .n { font-family: 'Geist Mono', ui-monospace, Menlo, monospace; color: var(--muted);
         font-size: 14px; min-width: 22px; }
.rk h3 { margin: 0; }
.rk p { margin: 2px 0 0; font-size: 13.5px; color: var(--muted); }
.step { position: relative; padding-bottom: 20px; }
.step:last-child { padding-bottom: 4px; }
.step:before { content: ''; position: absolute; left: -31px; top: 5px; width: 9px; height: 9px;
               border-radius: 50%; background: #2a3550; }
.step.done:before { background: var(--green); }
.step.now:before { background: var(--accent); box-shadow: 0 0 0 5px rgba(13, 162, 231, .15); }
.step h3 { margin: 0 0 2px; font-size: 15px; }
.step p { margin: 0; font-size: 13px; color: var(--muted); }
/* Experiment-page motion: chapters, stats, viewers and media fade up, like the site. */
details.chapter[open] .chapterbody { animation: fadeup .35s ease both; }
.stats .stat { animation: fadeup .4s ease both; }
.stats .stat:nth-child(2) { animation-delay: .05s; }
.stats .stat:nth-child(3) { animation-delay: .1s; }
.stats .stat:nth-child(4) { animation-delay: .15s; }
.stats .stat:nth-child(5) { animation-delay: .2s; }
.stats .stat:nth-child(6) { animation-delay: .25s; }
.viewport { animation: fadeup .5s ease both; }
.chapterbody figure, .chapterbody video { animation: fadeup .45s ease both; }
@media (max-width: 1040px) { .hero-split { grid-template-columns: 1fr; } }
/* Narrow layout. The old rule only switched .shell to one column: .content kept
   its 26px padding-left and left border, and .kv/.grid kept 320px/310px minimum
   tracks, so the page was wider than a phone viewport and text was clipped
   rather than wrapped. The sidebar also stacked above the page title, putting
   13 campaign links before the reader learned what page they were on. */
@media (max-width: 880px) {
  /* minmax(0, 1fr), not 1fr: a bare 1fr track has min-width:auto, so the wide
     nowrap table inside .subtable expanded the track and pushed every sibling
     paragraph off the right edge instead of wrapping. */
  .shell { grid-template-columns: minmax(0, 1fr); }
  .sidebar { position: static; order: 2; min-width: 0; }
  .shell .content { order: 1; padding-left: 0; border-left: none; min-width: 0; }
  .kv, .grid, .objectives { grid-template-columns: 1fr; }
  h1 { font-size: 27px; letter-spacing: -.6px; }
  h2 { font-size: 19px; }
  body { padding: 0 14px 56px; }
  h1, h2, h3, .sub, .lead { overflow-wrap: anywhere; }
}

/* Back to top: a floating bubble, shown once the reader scrolls past the hero. */
.totop { position: fixed; right: 22px; bottom: 22px; z-index: 40; width: 42px; height: 42px;
  display: grid; place-items: center; border-radius: 50%; cursor: pointer; padding: 0;
  background: var(--panel); border: 1px solid var(--line); color: var(--text);
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, .35);
  opacity: 0; visibility: hidden; transform: translateY(8px);
  transition: opacity .2s ease, transform .2s ease, visibility .2s; }
.totop.show { opacity: 1; visibility: visible; transform: translateY(0); }
.totop:hover { border-color: var(--accent); color: var(--accent); }
"""


TO_TOP_HTML = (
    "<button class='totop' id='totop' type='button' aria-label='Back to top'"
    " title='Back to top'>"
    "<svg width='16' height='16' viewBox='0 0 16 16' fill='none' aria-hidden='true'>"
    "<path d='M8 13V3M8 3L3.5 7.5M8 3l4.5 4.5' stroke='currentColor'"
    " stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'/></svg>"
    "</button>"
    "<script>(function(){var b=document.getElementById('totop');if(!b)return;"
    "function s(){b.classList.toggle('show',window.scrollY>480)}"
    "window.addEventListener('scroll',s,{passive:true});s();"
    "b.addEventListener('click',function(){"
    "var r=window.matchMedia('(prefers-reduced-motion: reduce)').matches;"
    "window.scrollTo({top:0,left:0,behavior:r?'auto':'smooth'})})})();</script>"
)


def esc(value) -> str:
    return _html.escape(str(value))


def _topnav(challenge: str | None = None, campaign: str | None = None) -> str:
    parts = ["<div class='topnav'><a class='brand' href='/'>Protein design workbench</a>"]
    if challenge:
        parts.append(f"<span class='sub'>/</span>"
                     f"<a class='brand' href='/ch/{esc(challenge)}'>"
                     f"{esc(CHALLENGE_INFO.get(challenge, {}).get('title') or challenge)}</a>")
    if campaign:
        parts.append(f"<span class='sub'>/</span><span class='sub'>{esc(campaign)}</span>")
    parts.append("<a class='navbtn' href='/about'>About</a> "
                 "<a class='navbtn' href='/'>Home</a></div>")
    return "".join(parts)


def _sidebar(challenge: str, current_run: str | None = None,
             rows: list[dict] | None = None,
             current_experiment: str | None = None) -> str:
    """Experiments first (the methodology units), the run folders below."""
    if rows is None:
        rows = runner.status_rows(challenge=challenge, recent=insights.RECENT_RUNS)
    labels = insights.unique_labels(rows)
    overview_current = (" current" if current_run is None and current_experiment is None else "")
    items = [f"<a class='sideitem{overview_current}' href='/ch/{esc(challenge)}'>Overview</a>"]
    lineage = _load_lineage(challenge)
    if lineage:
        for exp in lineage.get("experiments", []):
            scores = exp.get("scores") or {}
            bits = []
            if scores.get("human") is not None:
                bits.append(f"human {scores['human']:.3f}")
            if scores.get("mouse") is not None:
                bits.append(f"mouse {scores['mouse']:.3f}")
            if scores.get("ph") is not None:
                bits.append(f"switch {scores['ph']:+.2f}")
            meta = " · ".join([exp.get("date", "")] + bits)
            current = " current" if exp.get("id") == current_experiment else ""
            items.append(
                f"<a class='sideitem{current}' href='/lineage/{esc(challenge)}/{esc(exp['id'])}'>"
                f"<span class='sidelabel'>{esc(exp['title'])}"
                f"<span class='sidedate'>{esc(meta)}</span></span></a>")
    run_items = []
    for row in rows:
        run_id = _run_id(row)
        state = row.get("state", "?")
        current = " current" if run_id == current_run else ""
        label = labels.get(run_id, str(row.get("name", "?")))
        run_items.append(
            f"<a class='sideitem{current}' title='{esc(insights.format_when(row.get('started_utc')))}' "
            f"href='/run/{esc(challenge)}/{esc(run_id)}'>"
            f"<span class='dot {esc(state)}'></span>"
            f"<span class='sidelabel'>{esc(label)}"
            f"<span class='sidedate'>{esc(insights.format_when(row.get('started_utc')))}</span>"
            f"</span></a>"
        )
    if lineage:
        # the experiment model carries the story; the run folders are the
        # receipts and stay on disk, not in the navigation
        return "<h3>Campaigns</h3>" + "".join(items)
    if not run_items:
        run_items.append("<div class='sub'>No runs yet.</div>")
    runs_block = (f"<details class='sb-runs'><summary>Run folders ({len(rows)})</summary>"
                  + "".join(run_items) + "</details>")
    return "<h3>Campaigns</h3>" + "".join(items) + runs_block


def _page(title: str, body: str, challenge: str | None = None,
          current_run: str | None = None, with_sidebar: bool = False,
          sidebar_rows: list[dict] | None = None,
          current_experiment: str | None = None,
          campaign: str | None = None, totop: bool = True) -> str:
    page_body = body
    if with_sidebar and challenge:
        page_body = (f"<div class='shell'><aside class='sidebar'>"
                     f"{_sidebar(challenge, current_run, sidebar_rows, current_experiment)}</aside>"
                     f"<main class='content' id='main'>{body}</main></div>")
    else:
        page_body = f"<main id='main'>{body}</main>"
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(title)}</title><style>{CSS}</style></head><body>"
        "<a class='skip' href='#main'>Skip to content</a>"
        f"{_topnav(challenge, campaign)}{page_body}"
        f"{TO_TOP_HTML if totop else ''}</body></html>"
    )


def _badge(state: str) -> str:
    dot = _live_dot() if state == "running" else ""
    return f"<span class='badge {esc(state)}'>{dot}{esc(state)}</span>"


def _reference_badge() -> str:
    return "<span class='badge reference'>reference</span>"


def _run_id(row: dict) -> str:
    return Path(row.get("run_dir", "")).name


def _verdict_for(challenge: str, row: dict, specs: dict | None = None) -> dict:
    """The run's verdict, computed from its spec + status + summary."""
    specs = specs if specs is not None else spec_mod.specs_by_name(challenge)
    spec = specs.get(str(row.get("name", "")))
    return insights.assess_run(spec, row, row.get("summary") or {})


def _style_label(name: str) -> str:
    return "cartoon+surface" if name == "both" else name


def _chapter(number: int, title: str, content: str, open_chapter: bool = False) -> str:
    opened = " open" if open_chapter else ""
    return (f"<details class='chapter'{opened}><summary>"
            f"<span class='eyebrow'>{number:02d} /</span> {esc(title)}</summary>"
            f"<div class='chapterbody'>{content}</div></details>")


# ------------------------------------------------------------------ pages

def _live_dot() -> str:
    """The pulsing dot from the proteinbase status chip (their `ping` animation)."""
    return "<span class='live'><span class='ping'></span><span class='core'></span></span>"


def _target_payload(challenge: str, rel: str | None = None):
    """A target structure: the hero viewer's file, or one named in the brief."""
    if not rel:
        brief = brief_mod.BRIEF.get(challenge, {})
        viewer = brief.get("viewer") or {}
        rel = viewer.get("file", "")
    if not rel:
        return None
    root = (common.CHALLENGES_DIR / challenge).resolve()
    path = (root / rel).resolve()
    if root not in path.parents or not path.is_file():
        return None
    return path.read_text(errors="replace"), 200, "text/plain; charset=utf-8"


def _herohome() -> str:
    """Index: select a challenge."""
    rows = runner.status_rows(recent=insights.RECENT_RUNS)
    counts: dict[str, int] = {}
    for row in rows:
        challenge = row.get("challenge", "?")
        counts[challenge] = counts.get(challenge, 0) + 1
    order = list(CHALLENGE_INFO)
    challenges = order + sorted(set(counts) - set(order))
    body = [
        "<div class='hero'>",
        "<div class='eyebrow'><a class='hublink' href='https://proteinbase.com/competitions/anthropic-adaptyv-2026' target='_blank' rel='noopener'>Anthropic × Adaptyv 2026 ↗</a></div>",
        "<h1>Protein design workbench</h1>",
        "<div class='lead'>Five competition challenges, one workspace. "
        "Select a challenge.</div>",
        "<div class='sub' style='margin-top:10px'><span class='mono'>"
        "Sep 28 – Nov 8, 2026</span></div>",
        "</div>",
        "<div class='rowline'><span class='eyebrow'>01 /</span><h2>Challenges</h2></div>",
        "<div class='grid'>",
    ]
    for challenge in challenges:
        info = CHALLENGE_INFO.get(challenge, {})
        number = challenge[:2]
        viewer_file = (brief_mod.BRIEF.get(challenge, {}).get("viewer") or {}).get("file")
        if viewer_file:
            # Name the file, not the default route: a static host cannot serve
            # both /ch/<c>/target and /ch/<c>/target/<file> (site/PLAN.md).
            visual = (f"<div class='card3d viewer-loading' "
                      f"data-src='/ch/{esc(challenge)}/target/{esc(viewer_file)}'>"
                      f"<span>Loading target…</span></div>")
        else:
            visual = ("<div class='card3d card3d-empty'>Target structure is not in the "
                      "workspace yet.</div>")
        body.append(
            f"<a class='card' href='/ch/{esc(challenge)}'>"
            f"<div class='chipline'><span class='chip'>Challenge {esc(number)}</span></div>"
            f"<h3>{esc(info.get('title', challenge))}</h3>"
            f"<div class='sub'>{esc(info.get('tagline', ''))}</div>"
            f"{visual}"
            "</a>"
        )
    body.append("</div>")
    body.append(_CARD_VIEWER_JS)
    body.append("<div class='rowline'><span class='eyebrow'>02 /</span>"
                "<h2>Tools used</h2></div>")
    body.append(
        "<div class='sub' style='margin-bottom:6px'>Every tool this workspace has tried so "
        "far, what we used it for, and where it lives.</div>")
    body.append(_TABLES_STYLE + _tools_table_html())
    return _page("workbench", "".join(body))


def page_about() -> str:
    """The About page: who built this, and how to reach him."""
    links = (
        "<div class='rowline' style='margin-top:14px'>"
        "<a class='navbtn' href='https://www.linkedin.com/in/anton-chernysh/'"
        " target='_blank' rel='me noopener'>LinkedIn</a> <a class='navbtn'"
        " href='https://github.com/Visn0' target='_blank' rel='me noopener'>GitHub</a>"
        "</div>"
    )
    body = [
        "<div class='hero'>",
        "<div class='eyebrow'>About</div>",
        "<h1>Anton Chernysh</h1>",
        "<div class='lead'>I am a site reliability engineer in Zurich. "
        "This workbench is my entry for the Anthropic \u00d7 Adaptyv 2026 "
        "protein-design competition.</div>",
        links,
        "</div>",
        "<div class='card'>",
        "<p>I build and scale infrastructure for startups, with five years of "
        "taking products from an early prototype to production systems that "
        "stay up under real traffic. I write production code in Go and Python, "
        "and I care about the whole lifecycle: architecture, observability, "
        "incident response, and the optimizations that make systems faster "
        "and cheaper to run.</p>",
        "<p>This workspace is the competition work itself: one folder per "
        "challenge, every campaign kept, the negative results included, and "
        "every number sourced from the dated records beside it. The site you "
        "are reading is built from the same files the local app serves.</p>",
        "</div>",
        "<div class='sub' style='margin-top:18px'>"
        "<a href='/'>\u2190 back to the workbench</a></div>",
    ]
    return _page("about", "".join(body))


# ------------------------------------------------------- lineage (campaign)

def _load_lineage(challenge: str):
    path = common.CHALLENGES_DIR / challenge / "lineage.json"
    if not path.exists():
        return None
    return common.read_json(path)


def _score_chips(scores: dict) -> str:
    out = []
    if scores.get("human") is not None:
        out.append(f"<span class='chip'>human {scores['human']:.3f}</span>")
    if scores.get("mouse") is not None:
        out.append(f"<span class='chip'>mouse {scores['mouse']:.3f}</span>")
    if scores.get("ph") is not None:
        fold = 10 ** scores["ph"]
        out.append(f"<span class='chip'>switch {scores['ph']:+.3f} ({fold:.1f}×)</span>")
    return "".join(out)


def _lineage_steps_html(challenge: str, exp: dict) -> str:
    parts = []
    for index, step in enumerate(exp.get("steps") or [], start=1):
        img = step.get("image")
        img_html = ""
        if img:
            # removeprefix, not replace: an unanchored replace strips "viewers/"
            # from anywhere in the path (AGENT.md mistake 1). quote first, then
            # esc: the value is a URL inside an HTML attribute.
            rel = img.removeprefix("viewers/")
            src = f"/viewer-asset/{esc(challenge)}/{esc(urllib.parse.quote(rel))}"
            img_html = (f"<div style='margin-top:8px'><img src='{src}' "
                        f"style='max-width:440px;border-radius:10px;border:1px solid #232c44'/></div>")
        parts.append(f"<li style='margin-bottom:14px'><b>{index:02d} · {esc(step.get('title', ''))}</b>"
                     f"<div class='sub'>{esc(step.get('text', ''))}</div>{img_html}</li>")
    return "<ol style='margin:0;padding-left:22px'>" + "".join(parts) + "</ol>"


def _tools_html(tools) -> str:
    if not tools:
        return ""
    labels = []
    for t in tools:
        label = _tool_label(t)
        if label not in labels and not _is_non_tool(label):
            labels.append(label)
    if not labels:
        return ""
    chips = "".join(_tool_chip_html(label) for label in labels)
    return f"<div style='margin:6px 0'><span class='sub'>tools </span>{chips}</div>"


def _submission_rows(challenge: str):
    import csv as _csv

    sub_dir = common.CHALLENGES_DIR / challenge / "submission"
    files = ([f for f in sorted(sub_dir.glob("competition-submission-*.csv"))
              if "template" not in f.name] if sub_dir.exists() else [])
    if not files and sub_dir.exists():
        # challenge 4's file follows the organizers' template name directly
        files = [f for f in sorted(sub_dir.glob("submission-*.csv"))
                 if "template" not in f.name]
    if not files:
        return None
    with open(files[-1]) as handle:
        return list(_csv.DictReader(handle))


def _selection_scores(challenge: str) -> dict:
    """design -> normalized 0-100 score from select-top20.py, the only selector."""
    import csv as _csv

    rec_dir = common.CHALLENGES_DIR / challenge / "records"
    files = sorted(rec_dir.glob("selection-scores-*.csv")) if rec_dir.exists() else []
    if not files:
        return {}
    with open(files[-1]) as handle:
        return {r["design"]: r.get("score") for r in _csv.DictReader(handle)}


def _md_simple(text: str) -> str:
    """Minimal markdown: paragraphs + bold. The submission text is short."""
    import re as _re

    parts = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        block = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(block))
        parts.append(f"<p style='margin:8px 0'>{block.replace(chr(10), ' ')}</p>")
    return "".join(parts)


def _submitted_designs(challenge: str) -> set:
    rows = _submission_rows(challenge)
    return {row.get("name", "") for row in (rows or [])}


def _campaign_number(design: str) -> str:
    """The campaign number a design came from, read from its name (c13-... -> 13)."""
    match = re.match(r"^c(\d+)", design)
    if match:
        return match.group(1)
    if design.startswith("e1"):
        return "1"
    return "—"


def _history_build(challenge: str) -> Path | None:
    """The challenge README built to a self-contained HTML page, if it exists."""
    folder = common.CHALLENGES_DIR / challenge / "docs"
    builds = sorted(folder.glob("*-complete-history.html")) if folder.is_dir() else []
    return builds[0] if builds else None


def _history_section_html(challenge: str) -> str:
    """Link out to the complete history — the challenge README, built to HTML.

    The app has no markdown renderer (and markdown is not a dependency), so the
    page it serves is the build produced by tools/report/md_to_html.py.
    """
    build = _history_build(challenge)
    if build is None:
        return ""
    readme = common.CHALLENGES_DIR / challenge / "README.md"
    if not readme.exists():
        return ""
    chapters = [line[3:].strip() for line in readme.read_text().splitlines()
                if line.startswith("## ")]
    stale = readme.stat().st_mtime > build.stat().st_mtime
    parts = [
        "<div class='card'>",
        "<div class='sub'>The whole campaign in one document: the target and what "
        "it asks for, the biology in plain words, how every instrument was "
        "calibrated before it was trusted, the pipeline stage by stage, each "
        "campaign with its date, tools and result, how the designs were ranked, "
        "and what is honestly still unknown. Every number is sourced from the "
        "dated records in this challenge's folder.</div>",
    ]
    if chapters:
        parts.append("<div class='sub' style='margin-top:8px'>"
                     + " · ".join(esc(c) for c in chapters) + "</div>")
    parts.append(f"<div style='margin-top:10px'><a href='/ch/{esc(challenge)}/history'>"
                 f"read the complete history →</a></div>")
    if stale:
        parts.append("<div class='sub' style='margin-top:8px'>The built page is older "
                     "than <code>README.md</code>. Rebuild it: <code>python3 "
                     f"tools/report/md_to_html.py challenges/{esc(challenge)}/README.md "
                     f"{esc(str(build.relative_to(common.PROJECT_ROOT)))}</code> "
                     "(needs the <code>markdown</code> package).</div>")
    parts.append("</div>")
    return "".join(parts)


def _submission_section_html(challenge: str) -> str:
    """The submission — its own section on the challenge page.

    The selected designs, ranked (row order is the ranking), with the
    method family each came from, their scores, one 3D explorer for all of them,
    and the methodology text. Designs may come from MANY campaigns, so no single
    campaign page carries the submission."""
    rows = _submission_rows(challenge)
    scores = _selection_scores(challenge)
    if not rows:
        return ""
    by_design = {}
    lineage_path = common.CHALLENGES_DIR / challenge / "lineage.json"
    if lineage_path.exists():
        try:
            data = json.loads(lineage_path.read_text())
            for e in data.get("experiments", []):
                for p in e.get("proteins") or []:
                    by_design.setdefault(p["design"], p)
        except Exception:
            pass

    def num_cell(value, best, plus=False):
        if value is None:
            return "<td>—</td>"
        text = f"{value:+.3f}" if plus else f"{value:.3f}"
        cls = " class='best'" if best is not None and value == best else ""
        return f"<td{cls}>{text}</td>"

    submitted = [by_design.get(row.get("name", ""), {}) for row in rows]
    has_species = any(p.get("human") is not None or p.get("mouse") is not None
                      or p.get("ph") is not None for p in submitted)
    if has_species:
        best_h = max((p["human"] for p in submitted if p.get("human") is not None), default=None)
        best_m = max((p["mouse"] for p in submitted if p.get("mouse") is not None), default=None)
        best_ph = max((p["ph"] for p in submitted if p.get("ph") is not None), default=None)
        trs = []
        for index, row in enumerate(rows, start=1):
            design = row.get("name", "")
            p = by_design.get(design, {})
            trs.append(
                "<tr>"
                f"<td class='sub'>{index:02d}</td>"
                f"<td><code>{esc(design)}</code></td>"
                + f"<td>{insights.score_chip(scores.get(design))}</td>"
                + num_cell(p.get("human"), best_h)
                + num_cell(p.get("mouse"), best_m)
                + num_cell(p.get("ph"), best_ph, plus=True)
                + "<td><code style='font-size:11px;word-break:break-all;white-space:normal'>"
                f"{esc(row.get('sequence', ''))}</code></td>"
                "</tr>")
        return (_TABLES_STYLE
                + "<div class='sub'><b>The submission set — the final proteins, in "
                  "rank order (row order is the ranking).</b> The best value in each "
                  "column is highlighted in green.</div>"
                + "<div class='subtable'><table class='lt'>"
                + "<tr><th>#</th><th>design</th><th>score</th><th>human</th><th>mouse</th>"
                  "<th>switch</th><th>sequence</th></tr>" + "".join(trs) + "</table></div>"
                + _metric_legend_html(["ipsae", "delta_log_Ka", "pdockq2"])
                + _methodology_html(challenge))

    best_ip = max((p["ipsae_min"] for p in submitted if p.get("ipsae_min") is not None),
                  default=None)
    best_pd = max((p["pdockq2"] for p in submitted if p.get("pdockq2") is not None),
                  default=None)
    # challenge-5 style proteins carry i_pDAE + a specificity tier instead of
    # pDockQ2 + activation geometry; the column set follows the data.
    has_ipdae = any("ipdae" in p for p in submitted)
    best_dae = max((p["ipdae"] for p in submitted if p.get("ipdae") is not None),
                   default=None)
    trs = []
    for index, row in enumerate(rows, start=1):
        design = row.get("name", "")
        p = by_design.get(design, {})
        trs.append(
            "<tr>"
            f"<td class='sub'>{index:02d}</td>"
            f"<td><code>{esc(design)}</code></td>"
            f"<td class='sub'>{esc(_campaign_number(design))}</td>"
            + f"<td>{insights.score_chip(scores.get(design))}</td>"
            + num_cell(p.get("ipsae_min"), best_ip)
            + (num_cell(p.get("ipdae"), best_dae) if has_ipdae
               else num_cell(p.get("pdockq2"), best_pd))
            + (f"<td>{esc(p.get('tier') or '—')}</td>" if has_ipdae
               else f"<td>{esc(p.get('activation') or '—')}</td>")
            + "<td><code style='font-size:11px;word-break:break-all;white-space:normal'>"
            f"{esc(row.get('sequence', ''))}</code></td>"
            + "</tr>")
    return (_TABLES_STYLE
            + f"<div class='sub'><b>The submission set — the final {len(rows)} designs, in rank "
              "order (row order is the ranking).</b> Activation evidence first, then "
              "binding; score is the normalized 0-100 selection score. The entries "
              "of the original selection carry the v2 score from "
              "select-top20.py; the six epitope-gate additions of 2026-11-04 carry the "
              "v4 composite score, which counts the organizer's gate as a term - two "
              "formulas on one scale. The best value in each numeric "
              "column is highlighted in green.</div>"
            + "<div class='subtable'><table class='lt'>"
            + "<tr><th>#</th><th>design</th><th>campaign</th><th>score</th><th>ipSAE</th>"
              + ("<th>i_pDAE</th><th>specificity tier</th>" if has_ipdae
                 else "<th>pDockQ2</th><th>activation geometry</th>")
              + "<th>sequence</th></tr>"
            + "".join(trs) + "</table></div>"
            + _metric_legend_html(["score", "ipsae_min", "ipdae", "tier"] if has_ipdae
                                  else ["score", "ipsae_min", "pdockq2", "activation"])
            + f"<div class='rowline'><h3>The {len(rows)}, in 3D</h3></div>"
            + _explorer_iframe_html(
                challenge, "submission",
                f"All {len(rows)} designs on the receptor, each with its interface residues. "
                "The eye icon on the left toolbar opens the design list (the top three are "
                "shown together).")
            + _methodology_html(challenge))


def _goal_html(exp: dict) -> str:
    """Goal + the facts of the experiment + the objectives it answers."""
    parts = [f"<p>{esc(exp.get('goal', ''))}</p>"]
    tools = []
    for chapter in exp.get("chapters") or []:
        for tool in chapter.get("tools") or []:
            label = _tool_label(tool)
            if label and label not in tools and not _is_non_tool(label):
                tools.append(label)
    facts = [exp.get("date", ""),
             f"{len(exp.get('chapters') or [])} experiments",
             f"{len(exp.get('proteins') or [])} designs"]
    if tools:
        facts.append("tools: " + ", ".join(tools))
    parts.append("<div class='sub'>" + " · ".join(esc(f) for f in facts if f) + "</div>")
    extra = exp.get("goal_extra") or []
    if extra:
        parts.append("<ul style='margin:10px 0 0 0;padding-left:22px'>"
                     + "".join(f"<li style='margin-bottom:5px'>{esc(line)}</li>" for line in extra)
                     + "</ul>")
    return "".join(parts)


def _no_submission_html(exp: dict) -> str:
    """The honest verdict for an experiment that produced no submission."""
    proteins = exp.get("proteins") or []
    scored = [p for p in proteins
              if p.get("human") is not None or p.get("ipsae_min") is not None]

    def passes(p):
        # challenge 1/2 style: a scored species with a non-zero site count
        site = str(p.get("human_site") or "").split("/")[0]
        if site not in ("", "0"):
            return True
        # challenge 3 style: binding bar plus at least one receptor site reached
        ipsae = p.get("ipsae_min")
        if ipsae is not None and ipsae >= 0.8:
            for key in ("groove_site", "tm_site", "ecl3_site"):
                value = str(p.get(key) or "").split("/")[0]
                if value.isdigit() and int(value) > 0:
                    return True
        return False

    passed = [p for p in scored if passes(p)]
    best = max((p["ipsae_min"] for p in scored if p.get("ipsae_min") is not None),
               default=None)
    text = (f"<p><b>No design from this campaign entered the submission set.</b> "
            f"It recorded {len(proteins)} designs")
    if best is not None:
        text += f"; the best ipSAE recorded was {best:.3f}"
    text += "."
    if scored:
        text += f" {len(passed)} of {len(scored)} pass every filter — the rest were discarded."
    else:
        text += " No scores were recorded for them."
    text += "</p>"
    if passed:
        rows = sorted(passed, key=lambda p: -float(p.get("ipsae_min") or 0))[:10]

        def site_count(p, key):
            value = str(p.get(key) or "0/0").split("/")[0]
            return int(value) if value.isdigit() else 0

        best_ipsae = max(round(float(p.get("ipsae_min") or 0), 3) for p in rows)
        best_pdq = max(round(float(p.get("pdockq2") or 0), 3) for p in rows)
        best_grv = max(site_count(p, "groove_site") for p in rows)
        best_tm = max(site_count(p, "tm_site") for p in rows)
        best_ecl = max(site_count(p, "ecl3_site") for p in rows)

        def cell(value, best, text) -> str:
            cls = " class='best'" if value == best else ""
            return f"<td{cls}>{text}</td>"

        text += ("<div class='sub' style='margin-top:8px'>The best designs that pass every "
                 "filter (binding and site reach). The best value in each column is "
                 "highlighted in green:</div>")
        text += ("<table class='lt'><tr><th>design</th><th>ipSAE</th><th>pDockQ2</th>"
                 "<th>groove</th><th>TM</th><th>ECL3</th><th>agon</th><th>note</th></tr>")
        for p in rows:
            text += (
                f"<tr><td>{esc(p['design'])}</td>"
                + cell(round(float(p.get("ipsae_min") or 0), 3), best_ipsae,
                       f"{float(p['ipsae_min']):.3f}" if p.get("ipsae_min") is not None else "—")
                + cell(round(float(p.get("pdockq2") or 0), 3), best_pdq,
                       f"{float(p.get('pdockq2') or 0):.3f}")
                + cell(site_count(p, "groove_site"), best_grv, esc(p.get("groove_site") or "—"))
                + cell(site_count(p, "tm_site"), best_tm, esc(p.get("tm_site") or "—"))
                + cell(site_count(p, "ecl3_site"), best_ecl, esc(p.get("ecl3_site") or "—"))
                + f"<td>{esc(p.get('activation') or '—')}</td>"
                + f"<td class='sub'>{esc(p.get('note') or '')}</td></tr>")
        text += "</table>"
        text += _metric_legend_html(["ipsae_min", "pdockq2", "groove_site", "tm_site",
                                     "ecl3_site", "activation"])
    if exp.get("verdict_detail"):
        text += f"<p class='sub'>{esc(exp['verdict_detail'])}</p>"
    text += ("<p class='sub'>The designs themselves, with their scores, are in the experiments "
             "above.</p>")
    return text


def _methodology_html(challenge: str) -> str:
    path = common.CHALLENGES_DIR / challenge / "submission" / "methodology.md"
    if not path.exists():
        return ""
    return ("<div class='sub'><b>Methodology — as written for the submission.</b></div>"
            + _md_simple(path.read_text()))


# ------------------------------------------------------ challenge sections
# The challenge page has exactly five sections: Target information, Submission
# requirements, Our validation process, Campaigns (folded), Final submission.

def _tool_label(name) -> str:
    """One canonical label per tool, so the chips read the same everywhere."""
    base = re.sub(r"\s*\(.*\)\s*$", "", str(name)).strip()
    aliases = {
        "activation-geometry gate": "Activation gate",
        "solublemnn": "SolubleMPNN",
        "propka": "PROPKA 3.5.1",
        "boltzgen (cyclic + junction)": "BoltzGen",
        "rfd4-proteina, ecd–tmd junction conditioning": "RFD4-Proteina",
        "rfd4-proteina, 40-70 aa band": "RFD4-Proteina",
        "md (openmm)": "OpenMM",
        "chai-1 read": "Chai-1",
        "colabfold msa": "ColabFold / AlphaFold2",
        "propka 3.5.1": "PROPKA 3.5.1",
    }
    return aliases.get(base.lower(), base)


# Chapter records that are metrics or constructs, not tools.
_NON_TOOLS = {"reactifpTM", "mouse construct P06804 85-235",
              # challenge-4 chapter labels that are methods or data, not tools
              "pocket restraints", "pre-registered rule", "second-seed rerun",
              "vendored switch geometry", "rSASA filter", "wyman linkage",
              "alignment-derived anchors", "11RN native complex"}


def _is_non_tool(label: str) -> bool:
    return label.strip().lower() in {x.lower() for x in _NON_TOOLS}


def _campaign_tools(exp: dict) -> list:
    tools = []
    for chapter in exp.get("chapters") or []:
        for tool in chapter.get("tools") or []:
            label = _tool_label(tool)
            if label and label not in tools and not _is_non_tool(label):
                tools.append(label)
    return tools


# One short line per tool: how it is used in this competition.
TOOL_USAGE = {
    "RFdiffusion3": "Generates mini-protein backbones under hotspot constraints.",
    "BoltzGen": "Generates peptide binders, cyclic or junction-conditioned.",
    "EvoBind": "Designs peptides directly on the receptor structure.",
    "BindCraft2": "Generates binders with built-in interface optimisation.",
    "RFD4-Proteina": "Generates binder backbones (hosted NIM): the ECD–TMD junction on challenge 3, the TfR1 apical epitope sets on challenge 4.",
    "SolubleMPNN": "Re-sequences full-geometry backbones with the interface pinned.",
    "ProteinMPNN": "Designs sequences for a fixed backbone, with a histidine bias.",
    "scikit-learn": "Trains and cross-validates the sequence-feature surrogate used to screen large design pools.",
    "Boltz-2": "Co-folds designs with the receptor, five samples; supplies the PAE matrix. It cannot dock TfR1, so its challenge-4 reads stay diagnostic.",
    "IPSAE": "Scores the interface from the PAE matrix: ipSAE and pDockQ2.",
    "Activation gate": "Scores the six GLP-1 message-region contacts and the insertion depth.",
    "Genie 3": "Generates protein backbones with a diffusion model.",
    "BioEmu2": "Samples the receptor ensemble to check the binding site stays open.",
    "PROPKA 3.5.1": "Computes pKa shifts; the linkage formula gives the pH selectivity.",
    "OpenMM": "All-atom molecular dynamics: the real-physics check of one pose.",
    "ColabFold / AlphaFold2": "Builds MSAs and provides an independent fold check (challenge 4: MSAs for the OpenFold3 trial; the mouse receptor model is from the AlphaFold DB).",
    "pdt runner": "Runs each experiment and keeps its folder, status and report.",
    "3Dmol.js": "Draws the rotating structure viewers on every page.",
    "Chai-1": "The challenge-4 binding instrument: restrained pocket co-folds of every design, five samples; the engagement-gated ipTM read.",
    "US-align": "Structural-similarity arm: TM-align search of the finalists against known TfR1-binder references.",
    "Foldseek": "Fast structural search over the same references (installed for the novelty arm).",
    "Proton-PottsMPNN": "Re-sequences backbones with protonation-aware histidines: the challenge-4 switch arm.",
    "Gemmi": "Reads and writes the structure files: chain extraction, atom geometry and the CIF/PDB conversions between tools.",
    "Mol*": "Draws the interactive structure explorers: many designs in one scene, with the pLDDT, hydrophobicity and interface colourings.",
    "Binder prescreen": "The organizers' own novelty screen: flags prior art and known binders in the set before it ships.",
    "MMseqs2": "The homology gate: searches each design against SwissProt and excludes anything at or above 90 percent identity to a natural protein.",
    "ATLAS": "Wet-lab TCR-pMHC affinities (1,174 mutants with KD and ddG): the calibration set for the electrostatic score.",
    "SKEMPI2": "Measured mutation effects on binding (7,085, of which 764 sit at TCR/pMHC interfaces): the second wet-lab label set.",
    "FreeSASA": "Solvent-accessible surface area: how deeply the mutant aspartate is buried in the groove.",
    "Rosetta ref2015": "Tried on challenge 5 as a desolvation instrument (interface fa_sol decomposition); disqualified when it read the control wrong.",
    "OpenDDE": "Installed during the challenge-5 tool audit as a second co-folding opinion.",
    "diffusers": "Runs the training loop for the LoRA fine-tune of RFD4-Proteina.",
    "peft": "Supplies the LoRA adapter for that fine-tune, leaving the base weights frozen.",
    "OpenFold3": "Tried as a third folder for the finalists: installed with OpenBind-0 weights, but the 715-residue complex exceeds this host (out of memory, then a host crash) - recorded, no result used.",
}


# One unique colour per tool, so its label reads the same on every page.
TOOL_COLORS = {
    "RFdiffusion3": "#f472b6",
    "RFD4-Proteina": "#e879f9",
    "BoltzGen": "#fbbf24",
    "EvoBind": "#34d399",
    "BindCraft2": "#22d3ee",
    "SolubleMPNN": "#a3e635",
    "ProteinMPNN": "#fb923c",
    "Boltz-2": "#38bdf8",
    "IPSAE": "#818cf8",
    "Activation gate": "#f87171",
    "BioEmu2": "#2dd4bf",
    "PROPKA 3.5.1": "#facc15",
    "OpenMM": "#94a3b8",
    "ColabFold / AlphaFold2": "#fb7185",
    "pdt runner": "#8a94a6",
    "3Dmol.js": "#c084fc",
    "Mol*": "#67e8f9",
    "MMseqs2": "#fde047",
    "Genie 3": "#93c5fd",
    "Two-domain screen": "#f9a8d4",
    "Binder prescreen": "#fcd34d",
    "Chai-1": "#f0abfc",
    "US-align": "#5eead4",
    "Foldseek": "#c4b5fd",
    "Proton-PottsMPNN": "#fdba74",
    "OpenFold3": "#d1d5db",
    "Gemmi": "#a5b4fc",
    "FreeSASA": "#7dd3fc",
    "Rosetta ref2015": "#d8b4fe",
    "scikit-learn": "#86efac",
    "OpenDDE": "#6ee7b7",
    "ATLAS": "#fca5a5",
    "SKEMPI2": "#bef264",
    "diffusers": "#99f6e4",
    "peft": "#fed7aa",
}
TOOL_PALETTE = ["#f472b6", "#fbbf24", "#34d399", "#22d3ee", "#e879f9", "#a3e635",
                "#fb923c", "#38bdf8", "#818cf8", "#f87171", "#2dd4bf", "#facc15",
                "#94a3b8", "#fb7185", "#c084fc", "#f9a8d4"]


def _tool_color(tool: str) -> str:
    if tool in TOOL_COLORS:
        return TOOL_COLORS[tool]
    import zlib
    return TOOL_PALETTE[zlib.crc32(tool.encode()) % len(TOOL_PALETTE)]


def _tool_chip_html(tool: str) -> str:
    """A tool label chip in its own colour."""
    color = _tool_color(tool)
    return (f"<span class='chip tool' style='color:{color};border-color:{color}55;"
            f"background:{color}14'>{esc(tool)}</span>")


def _tool_table_html(tools) -> str:
    """tool -> its category and one line on how we use it, in the tool's colour."""
    if not tools:
        return ""
    rows = "".join(
        f"<tr><td><code style='color:{_tool_color(tool)}'>{esc(tool)}</code></td>"
        f"<td class='sub'>{esc(TOOL_CATEGORY.get(tool, '—'))}</td>"
        f"<td>{esc(TOOL_USAGE.get(tool, 'Used in this challenge\'s campaigns.'))}</td></tr>"
        for tool in tools)
    return ("<table class='lt'><tr><th>tool</th><th>category</th><th>how we use it</th></tr>"
            + rows + "</table>")


# Every tool this workspace has tried, with its role and its home on the web.
TOOLS_TABLE = [
    ("RFdiffusion3", "design", "https://github.com/RosettaCommons/foundry"),
    ("BoltzGen", "design", "https://github.com/HannesStark/boltzgen"),
    ("EvoBind", "design", "https://github.com/patrickbryant1/EvoBind"),
    ("Genie 3", "design", "https://github.com/aqlaboratory/genie3"),
    ("BindCraft2", "design", "https://github.com/martinpacesa/BindCraft"),
    ("RFD4-Proteina", "design (hosted)", "https://huggingface.co/spaces/nvidia/rfd4-proteina-space"),
    ("SolubleMPNN", "design (re-sequencing)", "https://github.com/dauparas/LigandMPNN"),
    ("ProteinMPNN", "design (re-sequencing)", "https://github.com/dauparas/ProteinMPNN"),
    ("Proton-PottsMPNN", "design (re-sequencing, pH-aware)", "https://github.com/christian-creator/ProtonPottsMPNN"),
    ("Boltz-2", "fold", "https://github.com/jwohlwend/boltz"),
    ("Chai-1", "fold", "https://github.com/chaidiscovery/chai-lab"),
    ("OpenFold3", "fold (trial - blocked on this host)", "https://github.com/aqlaboratory/openfold-3"),
    ("US-align", "score (structural similarity)", "https://zhanggroup.org/US-align/"),
    ("Foldseek", "validate (structural search)", "https://github.com/steineggerlab/foldseek"),
    ("ColabFold / AlphaFold2", "fold (independent check)", "https://github.com/sokrypton/ColabFold"),
    ("IPSAE", "score", "https://github.com/DunbrackLab/IPSAE"),
    # Not ours: the published community gate (charleneleong-ai/ai4science PR #98).
    ("Activation gate", "score (published)", "https://github.com/charleneleong-ai/ai4science"),
    ("Two-domain screen", "score (ours)", ""),
    ("PROPKA 3.5.1", "score (pH linkage)", "https://github.com/jensengroup/propka"),
    ("BioEmu2", "validate (ensembles)", "https://github.com/microsoft/bioemu"),
    ("OpenMM", "validate (molecular dynamics)", "https://openmm.org"),
    ("MMseqs2", "validate (homology screen)", "https://github.com/soedinglab/MMseqs2"),
    ("Binder prescreen", "validate (organizers' release)", "https://github.com/adaptyvbio/binder-prescreen"),
    ("Mol*", "view", "https://molstar.org"),
    ("3Dmol.js", "view", "https://3dmol.org"),
]

# tool -> category, for the per-challenge tools table (one taxonomy everywhere).
TOOL_CATEGORY = {tool: category for tool, category, _ in TOOLS_TABLE}
TOOL_CATEGORY["pdt runner"] = "run"
TOOL_CATEGORY["Genie 3"] = "design"
TOOL_CATEGORY["Gemmi"] = "structure I/O"
TOOL_CATEGORY["FreeSASA"] = "score (surface area)"
TOOL_CATEGORY["Rosetta ref2015"] = "score (trial - disqualified)"
TOOL_CATEGORY["scikit-learn"] = "score (surrogate)"
TOOL_CATEGORY["OpenDDE"] = "fold (second opinion)"
TOOL_CATEGORY["ATLAS"] = "data (wet-lab labels)"
TOOL_CATEGORY["SKEMPI2"] = "data (wet-lab labels)"
TOOL_CATEGORY["diffusers"] = "train"
TOOL_CATEGORY["peft"] = "train"


def _tools_table_html() -> str:
    """The whole tool set: tool, category, and its home on the web."""
    rows = []
    for tool, category, url in TOOLS_TABLE:
        link = (f"<a href='{esc(url)}' target='_blank' rel='noopener'>"
                f"{esc(url.replace('https://', ''))}</a>" if url
                else "<span class='sub'>ours — in this repo</span>")
        rows.append(f"<tr><td><code style='color:{_tool_color(tool)}'>{esc(tool)}</code></td>"
                    f"<td>{esc(category)}</td><td>{link}</td></tr>")
    return ("<table class='lt'><tr><th>tool</th><th>category</th><th>link</th></tr>"
            + "".join(rows) + "</table>")


_TARGET_JS = viewer3d.block(
    "function init(panel) {"
    "  const el = panel.querySelector('.tgt3d[data-src]');"
    "  if (el) window.pdt3d.mount(el);"
    "}"
    "document.querySelectorAll('.tgt').forEach(function (box) {"
    "  const panels = box.querySelectorAll('.tgt-panel');"
    "  const first = box.querySelector('.tgt-panel.cur') || panels[0];"
    "  if (first) init(first);"
    "  box.querySelectorAll('.tgt-tab').forEach(function (btn) {"
    "    btn.addEventListener('click', function () {"
    "      box.querySelectorAll('.tgt-tab').forEach(function (b) {"
    "        b.classList.toggle('cur', b === btn); });"
    "      panels.forEach(function (p) {"
    "        p.classList.toggle('cur', p.dataset.tgt === btn.dataset.tgt); });"
    "      const panel = box.querySelector('.tgt-panel.cur');"
    "      if (panel) init(panel);"
    "    });"
    "  });"
    "  const want = new URLSearchParams(location.search).get('tgt');"
    "  if (want) {"
    "    const btn = box.querySelector('.tgt-tab[data-tgt=\"' + want + '\"]');"
    "    if (btn) btn.click();"
    "  }"
    "  box.querySelectorAll('.tgt-copy').forEach(function (btn) {"
    "    btn.addEventListener('click', function () {"
    "      const pre = document.getElementById(btn.dataset.copy);"
    "      if (pre && navigator.clipboard) navigator.clipboard.writeText(pre.textContent);"
    "      btn.textContent = 'Copied';"
    "      setTimeout(function () { btn.textContent = 'Copy sequence'; }, 1200);"
    "    });"
    "  });"
    "});"
)


def _target_info_html(challenge: str, info: dict, brief: dict) -> str:
    """Target facts and structure, one tab per species (the proteinbase layout)."""
    targets = brief.get("targets") or []
    parts = []
    if targets:
        tabs, panels = [], []
        for index, t in enumerate(targets):
            cur = " cur" if index == 0 else ""
            tabs.append(f"<button type='button' class='tgt-tab{cur}' data-tgt='{esc(t['id'])}'>"
                        f"{esc(t['label'])}</button>")
            rows = []
            if t.get("accession"):
                uni = (f"<a href='{esc(t['uniprot'])}' target='_blank' rel='noopener'>"
                       f"{esc(t['accession'])} ↗</a>" if t.get("uniprot") else esc(t["accession"]))
                rows.append(f"<div><b>UniProt reference</b> {uni}</div>")
            if t.get("residues"):
                rows.append(f"<div><b>Target residues · UniProt</b> {esc(t['residues'])}</div>")
            for label, value, href in t.get("details", []):
                body = (f"<a href='{esc(href)}' target='_blank' rel='noopener'>{esc(value)} ↗</a>"
                        if href else esc(value))
                rows.append(f"<div><b>{esc(label)}</b> {body}</div>")
            seq_id = f"seq-{esc(challenge)}-{esc(t['id'])}"
            viewer = t.get("viewer") or {}
            ref = (f"<a class='mono' href='{esc(viewer.get('ref_url',''))}' target='_blank' "
                   f"rel='noopener'>{esc(viewer.get('ref_label',''))} ↗</a>"
                   if viewer.get("ref_url") else "")
            panels.append(
                f"<div class='tgt-panel{cur}' data-tgt='{esc(t['id'])}'>"
                "<div class='tgt-facts'>"
                f"<div class='tgt-head'><h3>{esc(t['label'])}</h3>"
                + (f"<span class='chip'>{esc(t['form'])}</span>" if t.get("form") else "")
                + "</div>"
                f"<div class='kv'>{''.join(rows)}</div>"
                "<div class='tgt-sec'><div class='tgt-sechead'><span>Amino acid sequence</span>"
                f"<button type='button' class='tgt-copy' data-copy='{seq_id}'>Copy sequence</button>"
                "</div>"
                f"<pre id='{seq_id}'>{esc(t.get('sequence',''))}</pre></div>"
                "</div>"
                "<div class='tgt-view'>"
                f"<div class='tgt-sechead'><span>Structure explorer</span>{ref}</div>"
                f"<div class='tgt3d viewport viewer-loading' "
                f"data-src='/ch/{esc(challenge)}/target/{esc(viewer.get('file',''))}'>"
                "Loading structure…</div>"
                "</div></div>")
        parts.append(f"<div class='tgt'><div class='tgt-tabs'>{''.join(tabs)}</div>"
                     f"{''.join(panels)}</div>" + _TARGET_JS)
    else:
        rows = "".join(
            f"<div><b>{esc(label)}</b> {esc(info[key])}</div>"
            for label, key in (("Target", "target"), ("Conditions", "conditions"),
                               ("Goal", "goal"), ("Status", "status"))
            if info.get(key)
        ) + "".join(
            f"<div><b>{esc(label)}</b> {esc(value)}</div>" for label, value in brief.get("rows", [])
        )
        parts.append(f"<div class='kv'>{rows}</div>")
    if info.get("fun_fact"):
        parts.append(
            "<div class='card' style='margin-top:12px'>"
            "<span class='eyebrow'>Fun fact</span>"
            f"<div style='margin-top:4px'>{esc(info['fun_fact'])}</div></div>")
    return "".join(parts)


def _requirements_html(brief: dict) -> str:
    """The organizers' rules, their hints, and how they rank designs."""
    parts = []
    if brief.get("requirements"):
        reqs = "".join(f"<div><b>{esc(label)}</b> {esc(value)}</div>"
                       for label, value in brief_mod.REQUIREMENTS)
        parts.append("<div class='rowline'><h3>Submission requirements</h3></div>"
                     f"<div class='kv'>{reqs}</div>")
    hints = brief.get("hints") or []
    if hints:
        items = "".join(
            f"<div class='rk'><span class='n'>·</span><div><h3>{esc(title)}</h3>"
            f"<p>{esc(text)}</p></div></div>" for title, text in hints)
        parts.append("<div class='rowline'><h3>Hints from the organizers</h3></div>"
                     f"<div class='ranking'>{items}</div>")
    objectives = brief.get("objectives") or []
    if objectives:
        cards = "".join(
            f"<div class='obj'><div class='num'>{index:02d}</div>"
            f"<h3>{esc(title)}</h3><p>{esc(text)}</p>"
            f"<span class='chip'>{esc(tag)}</span></div>"
            for index, (title, text, tag) in enumerate(objectives, start=1))
        parts.append("<div class='rowline'><h3>The objectives</h3></div>"
                     f"<div class='objectives'>{cards}</div>")
    ranking = brief.get("ranking") or []
    if ranking:
        ranks = "".join(
            f"<div class='rk'><span class='n'>{index}</span>"
            f"<div><h3>{esc(title)}</h3><p>{esc(text)}</p></div></div>"
            for index, (title, text) in enumerate(ranking, start=1))
        parts.append("<div class='rowline'><h3>How the organizers rank designs</h3></div>"
                     f"<div class='ranking'>{ranks}</div>")
    return "".join(parts)


def _validation_html(info: dict, lineage) -> str:
    """How we judge designs: the tools (a table), and the metrics that score them."""
    parts = []
    if info.get("validation"):
        parts.append(f"<div class='sub'>{esc(info['validation'])}</div>")
    tools = []
    for exp in (lineage or {}).get("experiments", []):
        for tool in _campaign_tools(exp):
            if tool not in tools:
                tools.append(tool)
    for tool in info.get("tools") or []:
        label = _tool_label(tool)
        if label not in tools:
            tools.append(label)
    if tools:
        parts.append("<div class='rowline'><h3>The tools, and how we use them</h3></div>")
        parts.append(_tool_table_html(tools))
    legend = _metric_legend_html(info.get("metrics") or DEFAULT_METRICS)
    if legend:
        parts.append("<div class='rowline'>"
                     "<h3>The numbers that score the designs</h3></div>")
        parts.append(legend)
    if info.get("bars"):
        parts.append("<div class='sub' style='margin-top:10px'>The bars are the acceptance "
                     "lines fixed before the campaign.</div>" + insights.bars_html(info["bars"]))
    return _TABLES_STYLE + "".join(parts)


def _campaigns_html(challenge: str, lineage) -> str:
    """Folded campaigns: title, datetime and tool labels, all visible while
    folded; opening one shows the short description, the counts and the link."""
    parts = ["<div class='sub'>A campaign is a set of experiments that share the same tools "
             "and strategy. Each entry names its tools; open one to see its experiments, "
             "every design with its scores, and the structure explorer.</div>"]
    for exp in lineage.get("experiments", []):
        chips = "".join(_tool_chip_html(tool) for tool in _campaign_tools(exp))
        inner = []
        if exp.get("summary"):
            inner.append(f"<div class='sub'>{esc(exp['summary'])}</div>")
        inner.append(f"<div class='sub'>{len(exp.get('chapters') or [])} experiments · "
                     f"{len(exp.get('proteins') or [])} designs</div>")
        inner.append(f"<div style='margin-top:8px'>"
                     f"<a class='navbtn' href='/lineage/{esc(challenge)}/{esc(exp['id'])}'>"
                     f"open campaign →</a></div>")
        parts.append(
            "<details class='campaign'>"
            f"<summary><b>{esc(exp['title'])}</b> "
            f"<span class='mono'>{esc(exp.get('date', ''))}</span> "
            f"{chips}</summary>"
            + "".join(inner) + "</details>")
    return _TABLES_STYLE + "".join(parts)


def _progression_html(exp: dict) -> str:
    """The best score each phase reached, in chapter order — the climb.

    There are two views. A species challenge climbs on human/mouse/switch; a
    binding challenge (with no species labels) climbs on best ipSAE, best
    pDockQ2 and the strongest activation geometry of the phase."""
    by_phase = {}
    for p in exp.get("proteins") or []:
        by_phase.setdefault(p.get("phase"), []).append(p)
    has_species = any(p.get("human") is not None or p.get("mouse") is not None
                      or p.get("ph") is not None
                      for group in by_phase.values() for p in group)

    def met_of(p):
        try:
            return int(str(p.get("activation") or "").split("/")[0])
        except ValueError:
            return -1

    rows = []
    for chapter in exp.get("chapters") or []:
        group = by_phase.get(chapter["id"]) or []
        if not group:
            continue
        if has_species:
            best_h = max((p["human"] for p in group if p.get("human") is not None), default=None)
            best_m = max((p["mouse"] for p in group if p.get("mouse") is not None), default=None)
            best_ph = max((p["ph"] for p in group if p.get("ph") is not None), default=None)

            def bar(v):
                if v is None:
                    return "<td class='sub'>—</td>"
                width = max(2.0, min(100.0, v * 100))
                return ("<td><span style='display:inline-block;width:{:.0f}%;min-width:2px;height:8px;"
                        "border-radius:3px;background:#0da2e7;vertical-align:middle'></span> "
                        "<span class='sub'>{:.3f}</span></td>").format(width, v)

            rows.append(
                f"<tr><td>{esc(chapter['title'])}</td>{bar(best_h)}{bar(best_m)}"
                f"<td class='sub'>{('%.3f' % best_ph) if best_ph is not None else '—'}</td>"
                f"<td class='sub'>{len(group)}</td></tr>")
        else:
            best_ip = max((p["ipsae_min"] for p in group if p.get("ipsae_min") is not None), default=None)
            best_pd = max((p["pdockq2"] for p in group if p.get("pdockq2") is not None), default=None)
            strongest = max(group, key=met_of).get("activation") or "—"
            rows.append(
                f"<tr><td>{esc(chapter['title'])}</td>"
                f"<td>{('%.3f' % best_ip) if best_ip is not None else '—'}</td>"
                f"<td>{('%.3f' % best_pd) if best_pd is not None else '—'}</td>"
                f"<td class='sub'>{esc(strongest)}</td>"
                f"<td class='sub'>{len(group)}</td></tr>")
    if not rows:
        return ""
    if has_species:
        intro = ("The best score each phase reached — the campaign's climb. "
                 "human / mouse = best ipSAE at the designed interface (of 5 samples); "
                 "switch = pH linkage, positive = tighter at 7.4.")
        header = ("<tr><th>phase</th><th>human</th><th>mouse</th><th>switch</th>"
                  "<th>designs</th></tr>")
    else:
        intro = ("The best score each phase reached — the campaign's climb. "
                 "ipSAE / pDockQ2 = best interface scores of the phase; "
                 "activation = the strongest geometry reached (of 6 pharmacophore "
                 "contacts, with insertion depth).")
        header = ("<tr><th>phase</th><th>ipSAE</th><th>pDockQ2</th>"
                  "<th>activation</th><th>designs</th></tr>")
    return ("<div class='sub'>" + intro + "</div>"
            "<table class='lt'>" + header + "".join(rows) + "</table>")


_TABLES_STYLE = (
    "<style>table.lt{border-collapse:collapse;font-size:11.5px;width:100%}"
    "table.lt td,table.lt th{padding:5px 10px;border-bottom:1px solid #1d2435;text-align:left;white-space:nowrap}"
    "table.lt td:last-child,table.lt th:last-child{width:100%}"
    "table.lt th{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:#8b93a7;font-weight:600}"
    "table.lt{display:block;overflow-x:auto}"
    "table.lt tbody,table.lt thead{display:table;width:100%}"
    "details.gen{border:1px solid #1d2435;border-radius:10px;padding:5px 10px;margin:5px 0}"
    "details.gen summary{cursor:pointer;font-size:13px;font-weight:600;padding:4px 0}"
    "details.gen summary:hover{color:#0da2e7}"
    "details.genchapter{border:1px solid #1d2435;border-radius:10px;padding:7px 12px;margin:5px 0;"
    "background:rgba(19,22,38,.55)}"
    "details.genchapter summary{cursor:pointer;font-size:13.5px;font-weight:600;padding:4px 0}"
    "details.genchapter summary:hover{color:#0da2e7}"
    "details.campaign{border:1px solid #1d2435;border-radius:12px;padding:2px 14px 4px;"
    "margin:5px 0;background:rgba(19,22,38,.45)}"
    "details.campaign summary{cursor:pointer;padding:7px 0;font-size:13px}"
    "details.campaign summary:hover{color:#0da2e7}"
    "details.campaign[open]{padding-bottom:14px}"
    ".best{color:#34d399;font-weight:700}"
    ".subtable{border:1px solid #1d2435;border-left:3px solid var(--green,#34d399);"
    "border-radius:10px;padding:6px 10px;margin:6px 0;background:rgba(52,211,153,.04);"
    "overflow-x:auto}</style>")


def _metric_legend_html(keys) -> str:
    """One small line per metric: what the column means, and which way is better."""
    items = []
    for key in keys:
        entry = insights.METRICS.get(key)
        if not entry:
            print(f"warning: unknown metric key {key!r} (not in insights.METRICS)",
                  file=sys.stderr)
            continue
        label, direction, sentence = entry
        arrow = {"higher": "higher is better",
                 "lower": "lower is better"}.get(direction, direction)
        items.append(f"<li><b>{esc(label)}</b> — {esc(sentence)} <i>({arrow})</i></li>")
    if not items:
        return ""
    return ("<div class='sub' style='margin-top:6px'>What the columns mean:</div>"
            "<ul style='margin:4px 0 0 0;padding-left:20px;font-size:11px;color:#8b93a7'>"
            + "".join(items) + "</ul>")


def _generation_tables(exp: dict, challenge: str | None = None) -> dict:
    """phase id -> the folded proteins block of that generation."""
    by_phase = {}
    for p in exp.get("proteins") or []:
        by_phase.setdefault(p.get("phase"), []).append(p)
    tables = {}
    for chapter in exp.get("chapters") or []:
        group = by_phase.get(chapter["id"]) or []
        if not group:
            continue
        scored = [p for p in group
                  if any(p.get(k) is not None for k in ("human", "mouse", "ph",
                                                         "ipsae_min", "pdockq2", "iptm"))]
        unscored = [p for p in group if p not in scored]
        inner = []
        if scored:
            cols = [("human", lambda p: f"{p['human']:.3f}" if p.get("human") is not None else "—"),
                    ("mouse", lambda p: f"{p['mouse']:.3f}" if p.get("mouse") is not None else "—"),
                    ("switch", lambda p: f"{p['ph']:+.3f}" if p.get("ph") is not None else "—"),
                    ("sites (h/m)", lambda p: f"{p.get('human_site') or '—'} / {p.get('mouse_site') or '—'}"),
                    ("groove", lambda p: p.get("groove_site") or "—"),
                    ("TM", lambda p: p.get("tm_site") or "—"),
                    ("ECL3", lambda p: p.get("ecl3_site") or "—"),
                    ("agon", lambda p: p.get("activation") or "—"),
                    ("ipsae_min", lambda p: f"{p['ipsae_min']:.3f}" if p.get("ipsae_min") is not None else "—"),
                    ("pDockQ2", lambda p: f"{p['pdockq2']:.3f}" if p.get("pdockq2") is not None else "—"),
                    ("ipTM", lambda p: f"{p['iptm']:.3f}" if p.get("iptm") is not None else "—"),
                    ("note", lambda p: p.get("note") or "")]
            keep = [name for name, _ in cols
                    if any(getter(p) not in ("—", "") for _, getter in [c for c in cols if c[0] == name]
                           for p in scored)]

            def numeric(text):
                try:
                    return float(str(text).replace("+", ""))
                except (TypeError, ValueError):
                    return None

            bests = {}
            for name, getter in cols:
                values = [v for v in (numeric(getter(p)) for p in scored) if v is not None]
                if values:
                    bests[name] = max(values)

            scores = _selection_scores(challenge) if challenge else {}
            header = ("<th>design</th><th>score</th>"
                      + "".join(f"<th>{esc(name)}</th>" for name in keep) + "<th>sequence</th>")
            rows = []
            for p in scored:
                cells = ""
                for name, getter in cols:
                    if name not in keep:
                        continue
                    value = getter(p)
                    parsed = numeric(value)
                    cls = " class='best'" if parsed is not None and bests.get(name) == parsed else ""
                    cells += f"<td{cls}>{esc(value)}</td>"
                seq = p.get("sequence") or ""
                rows.append("<tr>" f"<td><code>{esc(p['design'])}</code></td>"
                            f"<td>{insights.score_chip(scores.get(p['design']))}</td>{cells}"
                            f"<td><details><summary class='sub'>seq</summary>"
                            f"<code style='font-size:11px'>{esc(seq)}</code></details></td></tr>")
            inner.append("<table class='lt'><tr>" + header + "</tr>" + "".join(rows) + "</table>")
            legend_keys = [{"sites (h/m)": "human_site", "ipsae_min": "ipsae_min",
                            "pDockQ2": "pdockq2", "ipTM": "iptm",
                            "groove": "groove_site", "TM": "tm_site",
                            "ECL3": "ecl3_site", "agon": "activation"}.get(name, name)
                           for name in keep]
            inner.append(_metric_legend_html(legend_keys))
        if unscored:
            rows = []
            for p in unscored:
                seq = p.get("sequence") or "—"
                rows.append("<tr>" f"<td><code>{esc(p['design'])}</code></td>"
                            f"<td><code style='font-size:11px'>{esc(seq)}</code></td></tr>")
            inner.append(
                f"<div class='sub' style='margin-top:10px'>{len(unscored)} sequences were "
                "filtered out before folding — name and sequence only:</div>"
                "<table class='lt'><tr><th>design</th><th>sequence</th></tr>"
                + "".join(rows) + "</table>")
        title = f"Proteins · {len(group)} designs"
        if scored:
            title += f" · {len(scored)} scored"
        tables[chapter["id"]] = (f"<details class='gen'><summary>{title}</summary>"
                                 + "".join(inner) + "</details>")
    return tables


def _lineage_proteins_html(exp: dict) -> str:
    """Results content for an experiment without a submission set: the
    generations, folded, with the climb on top."""
    tables = _generation_tables(exp)
    chapter_ids = {c["id"] for c in exp.get("chapters") or []}
    parts = list(tables.values())
    orphan = [p for p in (exp.get("proteins") or []) if p.get("phase") not in chapter_ids]
    if orphan:
        parts.append(f"<div class='sub'>{len(orphan)} further designs without a phase.</div>")
    if not parts:
        return "<div class='sub'>No designs in this experiment — it measured or calibrated " \
               "designs made elsewhere.</div>"
    return (_TABLES_STYLE + _progression_html(exp)
            + "<div class='sub' style='margin-top:10px'>Every design of the experiment, phase by "
              "phase (folded — open a generation to see its proteins). Negative results stay on "
              "purpose.</div>"
            + "".join(parts))


def _explorer_iframe_html(challenge: str, slug: str, intro: str, height: int = 680) -> str:
    """One wrapper for every Mol* explorer embed: same frame, same full-screen link."""
    rel = f"multiview/{slug}.html"
    if not (common.CHALLENGES_DIR / challenge / "viewers" / rel).is_file():
        # Never leave a silent blank box (AGENT.md mistake 7). Without this the
        # iframe 404s and renders the app's own error page - navbar, sidebar and
        # all - inside the viewer frame, beside a dead full-screen link.
        return (f"<div class='sub'>{intro}</div>"
                "<div class='card' style='padding:14px;color:#8b93a7;font-size:12px'>"
                "No 3D page has been generated for this view yet. Build it with "
                f"<code>make_molstar_multiview.py {esc(slug)}</code>.</div>")
    src = f"/viewer-asset/{esc(challenge)}/{esc(urllib.parse.quote(rel))}"
    # allowfullscreen: the viewer's own Expand button calls requestFullscreen(),
    # which a frame without the permission refuses silently.
    return (f"<div class='sub'>{intro}</div>"
            + insights.colour_legend_html()
            + (f"<iframe src='{src}' title='Structure explorer' loading='lazy' "
            f"allowfullscreen allow='fullscreen' "
            f"style='width:100%;height:{height}px;border:1px solid #232c44;"
            "border-radius:12px;background:#0b0c14'></iframe>"
            f"<div class='sub'><a href='{src}' target='_blank'>open full screen →</a></div>"))


def _lineage_viewer_html(challenge: str, exp: dict) -> str:
    if not exp.get("viewer"):
        return "<div class='sub'>This experiment has no structures to view.</div>"
    target = CHALLENGE_INFO.get(challenge, {}).get("target", "the target")
    intro = (f"The designs of this experiment on {esc(target)}, in the structure explorer. "
             "The eye icon on the left toolbar opens the design list (one or many, with "
             "scores); Coloring Options switches pLDDT / hydrophobicity / interface — or "
             "back to the default design colours.")
    return _explorer_iframe_html(challenge, exp["id"], intro)


def _campaign_verdict_html(exp: dict) -> str:
    """The campaign's verdict, in the same shape a run uses: the reading as
    prose, the basis as facts (insights.result_block).

    A bare level word ("record", "promising") is a label, not a reading, and
    `insights.result_block` drops those on purpose — such a campaign shows its
    computed basis only, which makes the missing text visible instead of
    dressing it up.
    """
    bare = {"promising", "partial", "insufficient", "negative", "check",
            "waiting", "failed", "record"}
    text = (exp.get("verdict") or "").strip()
    if text.lower().rstrip(".") in bare:
        text = ""
    prots = exp.get("proteins") or []
    bits = []
    if exp.get("chapters"):
        bits.append(f"{len(exp['chapters'])} experiments")
    if prots:
        bits.append(f"{len(prots)} designs recorded")
    best = max((float(p["ipsae_min"]) for p in prots
                if p.get("ipsae_min") is not None), default=None)
    if best is not None:
        bits.append(f"best ipSAE {best:.3f}")
    if not text and not bits:
        return ""
    return ("<div class='verdict'>"
            + (f"<span class='sub'><b>Verdict.</b> {esc(text)}</span>" if text else "")
            + (f"<span class='mono basis'>basis: {esc(', '.join(bits))}</span>"
               if bits else "")
            + "</div>")


def _experiment_page(challenge: str, exp: dict) -> str:
    gen_tables = _generation_tables(exp, challenge)
    chapters_html = []
    for index, chapter in enumerate(exp.get("chapters") or [], start=1):
        chapters_html.append(
            "<details class='genchapter'>"
            f"<summary>{index:02d} · {esc(chapter['title'])}"
            f" <span class='sub'>{esc(chapter.get('date', ''))}</span></summary>"
            + _tools_html(chapter.get("tools"))
            + f"<p style='margin:6px 0'>{esc(chapter.get('text', ''))}</p>"
            + _lineage_steps_html(challenge, chapter)
            + (f"<div class='sub'><b>Outcome.</b> {esc(chapter.get('outcome', ''))}</div>"
               if chapter.get("outcome") else "")
            + gen_tables.get(chapter["id"], "")
            + "</details>")
    # The campaign's own best designs, whichever challenge it belongs to and
    # whether or not they went on to the submission: the same table structure
    # everywhere, with only the columns that carry data for this campaign.
    submitted = _submitted_designs(challenge)
    prots = exp.get("proteins") or []
    scores = _selection_scores(challenge)
    challenge_has_submission = bool(submitted)

    def rank_key(p):
        return (float(p.get("human") or 0), float(p.get("mouse") or 0),
                float(p.get("ipsae_min") or 0), float(p.get("iptm") or 0))

    ranked = sorted(prots, key=rank_key, reverse=True)[:12]
    mine = [p for p in prots if p.get("design") in submitted]
    n_mine = sum(1 for p in ranked if p.get("design") in submitted)

    cols = [c for c in ("human", "mouse", "ipsae_min", "pdockq2", "ph", "iptm")
            if any(p.get(c) is not None for p in ranked)]
    if "human" in cols and "iptm" in cols:
        # the human read IS the restrained ipTM; one column is enough
        cols.remove("iptm")
    heads = {"human": "human read", "mouse": "mouse read", "ipsae_min": "ipSAE",
             "pdockq2": "pDockQ2", "ph": "switch (linkage)", "iptm": "ipTM"}
    trs = []
    for p in ranked:
        cells = [f"<td><code>{esc(p['design'])}</code></td>",
                 f"<td>{insights.score_chip(scores.get(p['design']))}</td>"]
        for c in cols:
            v = p.get(c)
            cells.append(f"<td>{v if v is not None else '—'}</td>")
        mark = "✓" if p.get("design") in submitted else ""
        cells.append(f"<td style='color:#34d399'>{mark}</td>")
        cells.append(f"<td class='sub'>{esc(p.get('note') or '')}</td>")
        trs.append("<tr>" + "".join(cells) + "</tr>")
    no_scores = not any(scores.get(p.get("design")) for p in ranked)
    score_note = (" The score column is empty here: the composite ranks the single-chain "
                  "submission candidates, and this campaign sits outside the selection pool - its "
                  "own metrics stand instead." if no_scores else "")
    if mine and challenge_has_submission:
        results_title = "Results — this campaign's best designs"
        lead = (f"{len(mine)} of this campaign's designs are in the submission set "
                f"({n_mine} of the top {len(ranked)} shown). The ranked submission set and its 3D "
                "explorer are in the submission section of the challenge page.")
    elif challenge_has_submission:
        results_title = "Results — this campaign's best designs"
        lead = ("None of this campaign's designs are in the submission set; its best reads "
                "stand as the campaign record.")
    else:
        results_title = "Results — this campaign's best designs"
        lead = ("This challenge made no submission (closed on its pre-registered rule); "
                "the campaign's best reads stand as the record.")
    results_body = (_TABLES_STYLE
                    + f"<div class='sub'>{lead}{score_note}</div>"
                    + "<table class='lt'><tr><th>design</th><th>score</th>"
                    + "".join(f"<th>{heads[c]}</th>" for c in cols)
                    + "<th>in submission</th><th>note</th></tr>"
                    + "".join(trs) + "</table>"
                    + _metric_legend_html([c for c in cols] + ["score"]))
    body = [
        "<div class='rowline'><span class='eyebrow'>Campaign</span></div>",
        f"<h1>{esc(exp['title'])}</h1>",
        f"<div class='sub'>"
        + " · ".join(p for p in (esc(exp.get('date', '')),
                                  _score_chips(exp.get('scores') or {})) if p)
        + "</div>",
        f"<div class='sub'>{esc(exp.get('summary', ''))}</div>",
        _campaign_verdict_html(exp),
        _chapter(1, "Goal", _goal_html(exp), open_chapter=True),
        _chapter(2, "Experiments",
                 _TABLES_STYLE
                 + "<div class='sub'>Each experiment: the method, the tools, the steps — and its "
                   "proteins, folded. The climb first.</div>"
                 + _progression_html(exp)
                 + ("".join(chapters_html)
                    or "<div class='sub'>No method chapters recorded.</div>"),
                 open_chapter=False),
        _chapter(3, results_title, results_body, open_chapter=True),
        _chapter(4, "Binding", _lineage_viewer_html(challenge, exp), open_chapter=True),
    ]
    lineage = _load_lineage(challenge)
    siblings = (lineage or {}).get("experiments", [])
    ids = [e.get("id") for e in siblings]
    if exp.get("id") in ids:
        position = ids.index(exp["id"])
        nav = []
        if position > 0:
            prev = siblings[position - 1]
            nav.append(f"<a href='/lineage/{esc(challenge)}/{esc(prev['id'])}'>"
                       f"← {esc(prev['title'])}</a>")
        if position < len(siblings) - 1:
            nxt = siblings[position + 1]
            nav.append(f"<a href='/lineage/{esc(challenge)}/{esc(nxt['id'])}'>"
                       f"{esc(nxt['title'])} →</a>")
        if nav:
            body.append("<div class='sub' style='margin-top:18px'>" + " · ".join(nav) + "</div>")
    rows = runner.status_rows(challenge=challenge, recent=insights.RECENT_RUNS)
    return _page(exp["title"], "".join(body), challenge=challenge, with_sidebar=True,
                 sidebar_rows=rows, current_experiment=exp.get("id"),
                 campaign=exp["title"])


def page_lineage(challenge: str, exp_id: str) -> str | None:
    lineage = _load_lineage(challenge)
    if not lineage:
        return None
    experiments = lineage.get("experiments", [])
    exp = next((e for e in experiments if e.get("id") == exp_id), None)
    if exp is not None:
        return _experiment_page(challenge, exp)
    # deep link to a method chapter: render it as a focused page
    for parent in experiments:
        for chapter in parent.get("chapters", []):
            if chapter.get("id") == exp_id:
                focused = dict(parent)
                focused["id"] = chapter["id"]
                focused["title"] = chapter["title"]
                focused["summary"] = chapter.get("text", "")
                focused["goal"] = chapter.get("text", "")
                focused["chapters"] = [chapter]
                focused["proteins"] = [p for p in parent.get("proteins", [])
                                       if p.get("phase") == chapter["id"]]
                focused["viewer"] = chapter.get("viewer") or []
                focused["best"] = False
                return _experiment_page(challenge, focused)
    return None


def page_challenge(challenge: str) -> str | None:
    """Challenge home: the brief (hero, objectives, ranking, timeline), then experiments."""
    rows = runner.status_rows(challenge=challenge, recent=insights.RECENT_RUNS)
    specs = spec_mod.specs_by_name(challenge)
    info = CHALLENGE_INFO.get(challenge, {})
    if not rows and not specs and not info:
        return None
    brief = brief_mod.BRIEF.get(challenge, {})
    number = challenge[:2]
    chips = [f"<span class='chip'>Challenge {esc(number)}</span>"]
    if info.get("open") is True:
        chips.append(f"<span class='chip open'>{_live_dot()}Submissions open</span>")
    elif info.get("open") is False:
        chips.append("<span class='chip closed'>Submissions closed</span>")
    body = [
        "<div class='hero-split'>",
        "<div class='hero-text'>",
        "<div class='eyebrow'><a class='hublink' href='https://proteinbase.com/competitions/anthropic-adaptyv-2026' target='_blank' rel='noopener'>Anthropic × Adaptyv 2026 ↗</a></div>",
        f"<div class='rowline'>{''.join(chips)}</div>",
        f"<h1>{esc(info.get('title', challenge))}</h1>",
    ]
    if brief.get("subtitle"):
        body.append(f"<div class='sub' style='font-size:15px'>{esc(brief['subtitle'])}</div>")
    if info.get("tagline"):
        body.append(f"<div class='headline'>{esc(info['tagline'])}</div>")
    if brief.get("description"):
        body.append(f"<p class='hero-desc'>{esc(brief['description'])}</p>")
    body.append("</div>")
    body.append("</div>")

    # Exactly five sections: target information, submission requirements, our
    # validation process, campaigns (folded), final submission.
    sections: list[tuple[str, str]] = []
    sections.append(("The complete history", _history_section_html(challenge)))
    sections.append(("Target information", _target_info_html(challenge, info, brief)))
    sections.append(("Submission requirements", _requirements_html(brief)))
    lineage = _load_lineage(challenge)
    # A challenge we never worked on has no validation process to describe.
    # Claiming one would be the page inventing work (AGENT.md rule 14).
    if lineage or rows:
        sections.append(("Our validation process", _validation_html(info, lineage)))

    expo = ["<div class='sub'>Each run keeps its own "
            "folder; the run number in the label counts the runs of that experiment, "
            "oldest first.</div>"]
    if not rows:
        expo.append(f"<div class='sub'>No experiments yet. Start one: "
                    f"<code>pdt exp run --challenge {esc(challenge)} --all</code></div>")
    labels = insights.unique_labels(rows)
    for row in sorted(rows, key=insights.run_sort_key, reverse=True):
        run_id = _run_id(row)
        spec = specs.get(str(row.get("name", "")))
        goal = (spec.description or "").strip() if spec else ""
        reference = f" {_reference_badge()}" if spec and spec.reference else ""
        verdict = insights.assess_run(spec, row, row.get("summary") or {})
        expo.append(
            "<div class='card'>"
            f"<div>{_badge(row.get('state', '?'))} "
            f"<b>{esc(labels.get(run_id, row.get('name', '?')))}</b>"
            f"{reference} "
            f"<span class='sub'>{esc(insights.format_when(row.get('started_utc')))}"
            f" · {esc(row.get('duration_s', '?'))}s"
            f" · <span class='mono raw'>{esc(run_id)}</span></span></div>"
            + (f"<div class='sub'>{esc(goal)}</div>" if goal else "")
            + insights.result_block(verdict)
            + f"<div class='sub'>{esc(_headline(row.get('summary')))}</div>"
            + f"<div><a href='/run/{esc(challenge)}/{esc(run_id)}'>open experiment →</a></div>"
            "</div>"
        )
    runs_html = "".join(expo)

    if lineage:
        sections.append(("Campaigns", _campaigns_html(challenge, lineage)))
    elif rows:  # no campaigns and no runs: nothing to show, and nothing to invite
        sections.append(("Campaigns",
                         _TABLES_STYLE + "<div class='sub'>No campaigns yet — the run "
                         "folders are the history.</div>" + runs_html))
    submission_html = _submission_section_html(challenge)
    if submission_html:
        sections.append(("Final submission", submission_html))

    if len(sections) > 3:
        body.append("<div class='sub' style='display:flex;gap:12px;flex-wrap:wrap;"
                    "margin:6px 0 2px 0'>"
                    + "".join(f"<a href='#s{index}'>{index:02d} {esc(title)}</a>"
                              for index, (title, _) in enumerate(sections, start=1))
                    + "</div>")
    sections = [(t, m) for t, m in sections if m and m.strip()]
    for index, (title, markup) in enumerate(sections, start=1):
        body.append(f"<div class='rowline' id='s{index}'>"
                    f"<span class='eyebrow'>{index:02d} /</span>"
                    f"<h2>{esc(title)}</h2></div>")
        body.append(markup)
    return _page(info.get("title") or challenge, "".join(body), challenge=challenge,
                 with_sidebar=True,
                 sidebar_rows=rows)


# --------------------------------------------------------------- run views

def _run_dir(challenge: str, run_id: str) -> Path | None:
    folder = common.CHALLENGES_DIR / challenge / "runs" / run_id
    return folder if folder.is_dir() else None


def _viewer_entries(folder: Path) -> list[dict]:
    """All structures a run embedded for 3D viewing, in report order."""
    summary_path = folder / "summary.json"
    summary = common.read_json(summary_path) if summary_path.exists() else {}
    entries: list[dict] = []
    seen_paths: set = set()
    for stage in (summary.get("stages") or []):
        viewer = stage.get("viewer") or {}
        global_hints = viewer.get("highlights") or []
        for index, entry in enumerate(viewer.get("files") or []):
            path = folder / "artifacts" / entry["path"]
            if not path.exists() or str(path.resolve()) in seen_paths:
                continue
            seen_paths.add(str(path.resolve()))
            hints = list(entry.get("highlights") or [])
            if entry.get("highlight"):
                hints.append(entry["highlight"])
            hints.extend(hint for hint in global_hints if hint.get("file") == index)
            entries.append({
                "path": path,
                "label": entry.get("label", path.name),
                "stage": stage.get("stage", "?"),
                "note": entry.get("note") or viewer.get("note", ""),
                "highlights": hints,
                "trajectory": bool(entry.get("trajectory")),
            })
    # Trajectories first: a run with an MD player opens on the player.
    entries.sort(key=lambda item: 0 if item.get("trajectory") else 1)
    return entries


def _format_of(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].lower()
    return {"pdb": "pdb", "cif": "cif", "mmcif": "cif"}.get(ext, "pdb")


def _3dmol_selections(ngl_selection: str) -> list[dict]:
    """Translate an NGL-style selection ('B', '53:A', 'CAT or HSP') to 3Dmol."""
    selections = []
    for token in ngl_selection.split(" or "):
        token = token.strip()
        match = re.fullmatch(r"(\d+):([A-Za-z0-9])", token)
        if match:
            selections.append({"resi": int(match.group(1)), "chain": match.group(2)})
        elif len(token) == 1:
            selections.append({"chain": token})
        elif token:
            selections.append({"resn": token})
    return selections


def _client_highlights(entries: list[dict]) -> list[list[dict]]:
    """Pre-translate highlight hints for client-side 3Dmol scripts (app viewers)."""
    out = []
    for entry in entries:
        hints = []
        for hint in entry["highlights"]:
            selections = _3dmol_selections(" or ".join(hint.get("selections") or []))
            if not selections:
                continue
            hints.append({"sels": selections, "color": hint.get("color", "orange"),
                          "repr": hint.get("repr", "ball+stick")})
        out.append(hints)
    return out


# ------------------------------------------------------- experiment page

def _steps_html(pipeline: str, stage_names: list[str]) -> str:
    items = []
    for index, name in enumerate(stage_names, start=1):
        info = STAGE_INFO.get((pipeline, name), {})
        goal = info.get("goal", "")
        strategy = info.get("strategy", "")
        detail = f"<div class='sub'>{esc(strategy)}</div>" if strategy else ""
        items.append(f"<li><b>{index:02d} · {esc(name)}</b> — {esc(goal)}{detail}</li>")
    return ("<ol style='margin:0;padding-left:22px;display:flex;flex-direction:column;gap:10px'>"
            + "".join(items) + "</ol>")


def _stat_cards(stages: list[dict]) -> str:
    parts = []
    for stage in stages:
        cards = []
        for key, label in CARD_LABELS:
            value = stage.get(key)
            if value is None or isinstance(value, (list, dict)):
                continue
            if isinstance(value, bool):
                text = "yes" if value else "no"
            elif isinstance(value, float):
                text = f"{value:g}"
            else:
                text = str(value)
            cards.append(f"<div class='stat'><b>{esc(text)}</b><span>{esc(label)}</span></div>")
        if cards:
            parts.append(f"<div class='sub'>{esc(stage.get('stage', 'stage'))}</div>")
            parts.append("<div class='stats'>" + "".join(cards) + "</div>")
    return "".join(parts)


def _charts_html(folder: Path, stages: list[dict]) -> str:
    from tools.report import charts as charts_mod

    parts = []
    for stage in stages:
        for chart in stage.get("charts") or []:
            source = folder / "artifacts" / str(chart.get("source", ""))
            if not source.exists():
                continue
            try:
                svg = charts_mod.render_chart(chart, pd.read_csv(source))
            except Exception:
                svg = None
            if svg:
                parts.append(f"<figure>{svg}</figure>")
    return "".join(parts)


def _settings_html(status: dict) -> str:
    cards = "".join(
        f"<div class='stat'><b>{esc(value)}</b><span>{esc(key)}</span></div>"
        for key, value in (status.get("params") or {}).items()
    )
    meta = "".join(
        f"<div><b>{esc(label)}</b> {esc(value)}</div>"
        for label, value in (
            ("device", (status.get("device") or {}).get("recommended", "?")),
            ("python", status.get("python", "?")),
            ("duration", f"{status.get('duration_s', '?')}s"),
            ("started", status.get("started_utc", "?")),
            ("git", status.get("git", "?")),
        )
    )
    body = f"<div class='kv'>{meta}</div>"
    if cards:
        body = f"<div class='stats'>{cards}</div>" + body
    return body


def page_experiment(challenge: str, run_id: str) -> str | None:
    """One experiment: goal, steps, settings, results, video — all foldable."""
    folder = _run_dir(challenge, run_id)
    if folder is None:
        return None
    status_path = folder / "status.json"
    status = common.read_json(status_path) if status_path.exists() else {}
    summary_path = folder / "summary.json"
    summary = common.read_json(summary_path) if summary_path.exists() else {}
    stages = summary.get("stages") or []
    spec = next(
        (s for s in spec_mod.discover()
         if s.challenge == challenge and s.name == status.get("name")), None,
    )
    pipeline = status.get("pipeline") or (spec.pipeline if spec else "?")
    stage_names = [stage.get("stage", "?") for stage in stages]
    if spec and spec.stages:
        stage_names = list(spec.stages)

    # Strategy: how the numbers are produced, with which tools (replaces "Goal").
    strategy_html = _strategy_html(pipeline, stage_names, spec)

    # 3D view: the run's first structure in a slowly rotating viewer. No videos.
    entries = _viewer_entries(folder)
    view_parts = []
    if status.get("state") == "waiting_inputs":
        view_parts.append(f"<div class='sub'>This experiment waits for input files. "
                          f"{esc(status.get('error', ''))}</div>")
    if entries:
        first = entries[0]
        hints = json.dumps(_client_highlights([first])[0])
        note = (first.get("note") or "").strip()
        view_parts.append(
            f"<div class='sub mono'>{esc(first['label'])}</div>"
            f"<div id='run3d' class='viewport viewer-loading' "
            f"data-src='/api/struct/{esc(challenge)}/{esc(run_id)}/0'>"
            "Loading structure…</div>"
            + (f"<div class='sub'>{esc(note)}</div>" if note else "")
            + f"<div class='sub'><a href='/run/{esc(challenge)}/{esc(run_id)}/3d'>"
            f"Open all {len(entries)} structures with style controls →</a></div>"
        )
        view_parts.append(
            viewer3d.block(
                "window.pdt3d.mount(document.getElementById('run3d'), "
                f"{{hints: {hints}}});"
            )
        )
    else:
        view_parts.append("<div class='sub'>This run has no structures yet.</div>")
    player_file = folder / "artifacts" / "md" / "md_player.html"
    if player_file.exists():
        view_parts.append(
            f"<div class='sub'><a href='/run/{esc(challenge)}/{esc(run_id)}/file"
            "?name=md/md_player.html'>Open the MD player page (cartoon / cloud / surface, "
            "both pH states) →</a></div>")

    chips = _badge(status.get("state", "?")) + (
        " " + _reference_badge() if spec and spec.reference else "")
    verdict = insights.assess_run(spec, status, summary)
    rows = runner.status_rows(challenge=challenge, recent=insights.RECENT_RUNS)
    labels = insights.unique_labels(rows)
    body = [
        f"<div class='rowline'><span class='eyebrow'>Experiment</span>{chips}</div>",
        f"<h1>{esc(labels.get(run_id, status.get('name', run_id)))}</h1>",
        f"<div class='sub mono raw'>{esc(insights.format_when(status.get('started_utc')))}"
        f" · {esc(status.get('duration_s', '?'))}s · {esc(run_id)}</div>",
        insights.result_block(verdict),
        f"<div class='sub'>{esc(_headline(summary))}</div>",
        _chapter(1, "Method — step by step", _steps_html(pipeline, stage_names), open_chapter=True),
        _chapter(2, "Results",
                 _stat_cards(stages) + _charts_html(folder, stages)
                 + insights.legend_html(insights.stage_metric_keys(stages)),
                 open_chapter=True),
        _chapter(3, "3D view", "".join(view_parts) + insights.colour_legend_html(),
                 open_chapter=True),
    ]
    return _page(labels.get(run_id, status.get('name', run_id)), "".join(body),
                 challenge=challenge, current_run=run_id, with_sidebar=True,
                 sidebar_rows=rows)


# ---------------------------------------------------------- 3D viewer page

def _toolbar(challenge: str, run_id: str, entries: list[dict], file_index: int,
             style: str, with_styles: bool = True) -> str:
    base = f"/run/{esc(challenge)}/{esc(run_id)}/3d"
    options = "".join(
        f"<option value='{index}'{' selected' if index == file_index else ''}>"
        f"{esc(entry['label'])}</option>"
        for index, entry in enumerate(entries)
    )
    styles = "".join(
        f"<span class='cur'>{esc(_style_label(name))}</span>" if name == style
        else f"<a href='{base}?file={file_index}&style={name}'>{esc(_style_label(name))}</a>"
        for name in VIEWER_STYLES
    )
    form = (
        f"<form method='get' action='{base}' style='margin:0'>"
        f"<input type='hidden' name='style' value='{esc(style)}'/>"
        f"<label class='sub'>structure <select name='file' onchange='this.form.submit()'>"
        f"{options}</select></label></form>"
    )
    style_part = f"<span class='sub'>style:</span> {styles}" if with_styles else ""
    return (
        "<div class='toolbar'>" + form + style_part
        + f"<a href='{base}?file={file_index}&style={style}'>reset view</a>"
        + "</div>"
    )


def _apply_py3dmol_styles(view, entry: dict, style: str) -> None:
    """Two styles: cartoon (protein ribbon) or surface only."""
    import py3Dmol

    if style == "cartoon":
        view.setStyle({}, {"cartoon": {"colorscheme": "chain"}})
    # style == "surface": no base style; the surface below carries the shape
    for hint in entry["highlights"]:
        color = hint.get("color", "orange")
        for selection in _3dmol_selections(" or ".join(hint.get("selections") or [])):
            if hint.get("repr") == "cartoon":
                view.setStyle(selection, {"cartoon": {"color": color}})
            else:
                view.setStyle(selection, {"stick": {"color": color, "radius": 0.15}})
                view.setStyle(selection, {"sphere": {"color": color, "scale": 0.35}})
    if style == "surface":
        view.addSurface(py3Dmol.SAS, {"opacity": 0.75, "color": "#5f6f86"})


def _player_3d_page(challenge: str, run_id: str, entries: list[dict], file_index: int,
                    style: str, entry: dict, model_count: int) -> str:
    """The 3D page for a multi-model structure: the MD player page."""
    from tools.md import player as md_player

    config = {
        "title": None,
        "note": None,
        "states": [{
            "key": entry["path"].stem,
            "label": f"{model_count} frames",
            "url": f"/api/struct/{esc(challenge)}/{esc(run_id)}/{file_index}",
            "stat": entry.get("note", ""),
        }],
        "hints": _client_highlights([entry])[0],
        "footer": "Real MD trajectory · play, scrub, switch cartoon / surface",
    }
    fragment = md_player.player_fragment(config, "/static/3Dmol-min.js")
    note = entry.get("note") or ""
    body = (
        f"<h1>{esc(entry['label'])}</h1>"
        f"<div class='sub'><a href='/'>workbench</a> · "
        f"<a href='/ch/{esc(challenge)}'>{esc(challenge)}</a> · "
        f"<a href='/run/{esc(challenge)}/{esc(run_id)}'>← back to the experiment</a> · "
        f"stage: {esc(entry['stage'])}</div>"
        + _toolbar(challenge, run_id, entries, file_index, style, with_styles=False)
        + f"<div class='viewerwrap'>{fragment}</div>"
        + (f"<div class='sub'>{esc(note)}</div>" if note else "")
        + "<div class='sub'>Play or scrub the frames. Drag = rotate · scroll = zoom.</div>"
    )
    return _page(f"3D · {entry['label']}", body, challenge=challenge, totop=False)


def page_3d(challenge: str, run_id: str, file_index: int = 0, style: str = "cartoon") -> str | None:
    folder = _run_dir(challenge, run_id)
    if folder is None:
        return None
    entries = _viewer_entries(folder)
    if not entries:
        return _page("no structures", "<h1>No structures in this run</h1>"
                     f"<div class='sub'><a href='/run/{esc(challenge)}/{esc(run_id)}'>"
                     "← back to the experiment</a> — this run has no 3D structures yet.</div>",
                     challenge=challenge)
    file_index = max(0, min(file_index, len(entries) - 1))
    entry = entries[file_index]
    style = style if style in VIEWER_STYLES else "cartoon"
    structure_text = entry["path"].read_text(errors="replace")
    model_count = structure_text.count("\nMODEL ")
    if model_count >= 4:
        # an MD trajectory: the player gives play, scrub and cartoon/surface
        return _player_3d_page(challenge, run_id, entries, file_index, style,
                               entry, model_count)

    import py3Dmol

    view = py3Dmol.view(width=980, height=540)
    view.setBackgroundColor("#0b0f14")
    view.addModel(structure_text, _format_of(entry["path"].name))
    _apply_py3dmol_styles(view, entry, style)
    view.zoomTo()

    fragment = view._make_html()
    # Swap the CDN loader for the vendored bundle: the app stays offline.
    fragment = re.sub(r"(?:https?:)?//cdn\.jsdelivr\.net/npm/3dmol@[\d.]+/build/3Dmol-min\.js",
                      "/static/3Dmol-min.js", fragment)
    fragment = re.sub(r"(?:https?:)?//3dmol\.org/build/3Dmol-min\.js",
                      "/static/3Dmol-min.js", fragment)

    note = entry.get("note") or ""
    body = (
        f"<h1>{esc(entry['label'])}</h1>"
        f"<div class='sub'><a href='/'>workbench</a> · "
        f"<a href='/ch/{esc(challenge)}'>{esc(challenge)}</a> · "
        f"<a href='/run/{esc(challenge)}/{esc(run_id)}'>← back to the experiment</a> · "
        f"stage: {esc(entry['stage'])}</div>"
        + _toolbar(challenge, run_id, entries, file_index, style)
        + f"<div class='viewerwrap'>{fragment}</div>"
        + (f"<div class='sub'>{esc(note)}</div>" if note else "")
        + "<div class='sub'>Drag = rotate · scroll = zoom · right-drag = move.</div>"
    )
    return _page(f"3D · {entry['label']}", body, challenge=challenge, totop=False)


def _structure_payload(challenge: str, run_id: str, index: int):
    """Raw structure text for viewers (fetch target)."""
    folder = _run_dir(challenge, run_id)
    if folder is None:
        return None
    entries = _viewer_entries(folder)
    if not (0 <= index < len(entries)):
        return None
    return entries[index]["path"].read_text(errors="replace"), 200, "text/plain; charset=utf-8"


_RUN_FILE_TYPES = {
    ".html": "text/html; charset=utf-8", ".mp4": "video/mp4", ".png": "image/png",
    ".json": "application/json", ".csv": "text/csv; charset=utf-8",
    ".pdb": "text/plain; charset=utf-8", ".js": "application/javascript; charset=utf-8",
}


def _run_file_payload(challenge: str, run_id: str, name: str):
    """One file inside a run directory. `name` is relative to the run root.

    A name that is not at the run root also resolves under `artifacts/`, so
    'md/md_player.html' finds 'artifacts/md/md_player.html'. Names with '..'
    are refused.
    """
    folder = _run_dir(challenge, run_id)
    if folder is None or not name or ".." in name:
        return None
    for candidate in (folder / name, folder / "artifacts" / name):
        target = candidate.resolve()
        if folder.resolve() not in target.parents or not target.is_file():
            continue
        content_type = _RUN_FILE_TYPES.get(target.suffix.lower(), "application/octet-stream")
        return target.read_bytes(), 200, content_type
    return None


# ---------------------------------------------------------------- server

def _not_found() -> str:
    return _page("not found", "<h1>404</h1><div class='sub'><a href='/'>← workbench</a></div>")


class Handler(BaseHTTPRequestHandler):
    server_version = "pdt-serve/2.0"

    def _send(self, body, status: int = 200,
              content_type: str = "text/html; charset=utf-8") -> None:
        payload = body.encode() if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        query = urllib.parse.parse_qs(parsed.query)
        try:
            if path.startswith("/media/"):
                self._send_media(path)
                return
            result = self._route(path, query)
        except Exception:
            self._send(_page("error", f"<h1>500</h1><pre>{esc(traceback.format_exc())}</pre>"), 500)
            return
        if result is None:
            self._send(_not_found(), 404)
        elif isinstance(result, tuple):
            body, status, content_type = result
            self._send(body, status, content_type)
        else:
            self._send(result)

    def _route(self, path: str, query: dict):
        if path == "/":
            return _herohome()
        if path == "/about":
            return page_about()
        if path.startswith("/static/"):
            return self._static(path)
        match = re.fullmatch(r"/api/struct/([^/]+)/([^/]+)/(\d+)", path)
        if match:
            return _structure_payload(match.group(1), match.group(2), int(match.group(3)))
        match = re.fullmatch(r"/ch/([^/]+)/target", path)
        if match:
            return _target_payload(match.group(1))
        match = re.fullmatch(r"/ch/([^/]+)/target/(.+)", path)
        if match:
            return _target_payload(match.group(1), match.group(2))
        match = re.fullmatch(r"/ch/([^/]+)/history", path)
        if match:
            build = _history_build(match.group(1))
            if build is None:
                return None
            # the file stays standalone on disk; the way back is added on serve
            back = (f"<div style='margin-bottom:28px'><a href='/ch/{esc(match.group(1))}'"
                    f" style='color:#7dd3fc'>&larr; back to the challenge</a></div>")
            page = build.read_text().replace("<main>", f"<main>{back}", 1)
            return page.encode("utf-8"), 200, "text/html; charset=utf-8"
        match = re.fullmatch(r"/ch/([^/]+)", path)
        if match:
            return page_challenge(match.group(1))
        match = re.fullmatch(r"/run/([^/]+)/([^/]+)/file", path)
        if match:
            name = (query.get("name") or [""])[0]
            return _run_file_payload(match.group(1), match.group(2), name)
        match = re.fullmatch(r"/run/([^/]+)/([^/]+)/3d", path)
        if match:
            try:
                file_index = int((query.get("file") or ["0"])[0])
            except ValueError:
                file_index = 0
            style = (query.get("style") or ["cartoon"])[0]
            return page_3d(match.group(1), match.group(2), file_index, style)
        match = re.fullmatch(r"/run/([^/]+)/([^/]+)", path)
        if match:
            return page_experiment(match.group(1), match.group(2))
        match = re.fullmatch(r"/lineage/([^/]+)/([^/]+)", path)
        if match:
            return page_lineage(match.group(1), match.group(2))
        match = re.fullmatch(r"/viewer-asset/([^/]+)/(.+)", path)
        if match:
            return self._viewer_asset(match.group(1), match.group(2))
        return None

    def _static(self, path: str):
        target = (STATIC_DIR / path[len("/static/"):]).resolve()
        if STATIC_DIR.resolve() not in target.parents or not target.is_file():
            return None
        content_type = {
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".txt": "text/plain; charset=utf-8",
            ".woff2": "font/woff2",
        }.get(target.suffix, "application/octet-stream")
        return target.read_bytes(), 200, content_type

    def _viewer_asset(self, challenge: str, rel: str):
        root = (common.CHALLENGES_DIR / challenge / "viewers").resolve()
        target = (root / rel).resolve()
        if root not in target.parents or not target.is_file():
            return None
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
        }.get(target.suffix, "application/octet-stream")
        return target.read_bytes(), 200, content_type

    def _send_media(self, path: str) -> None:
        """Serve run media files with HTTP Range support."""
        parts = path[len("/media/"):].split("/")
        target = None
        if len(parts) == 3 and all(re.fullmatch(r"[A-Za-z0-9._-]+", part) and ".." not in part
                                   for part in parts):
            challenge, run_id, name = parts
            folder = _run_dir(challenge, run_id)
            if folder is not None:
                candidate = (folder / name).resolve()
                if folder.resolve() in candidate.parents and candidate.is_file():
                    target = candidate
        if target is None:
            self._send(_not_found(), 404)
            return
        data = target.read_bytes()
        content_type = {".mp4": "video/mp4", ".png": "image/png", ".jpg": "image/jpeg",
                        ".gif": "image/gif"}.get(target.suffix.lower(), "application/octet-stream")
        range_header = self.headers.get("Range")
        if range_header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
            if match:
                start = int(match.group(1)) if match.group(1) else 0
                end = int(match.group(2)) if match.group(2) else len(data) - 1
                end = min(end, len(data) - 1)
                if start <= end:
                    chunk = data[start:end + 1]
                    self.send_response(206)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Content-Range", f"bytes {start}-{end}/{len(data)}")
                    self.send_header("Content-Length", str(len(chunk)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(chunk)
                    return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):  # keep the console quiet  # noqa: A002
        pass


def run(port: int = 8737, host: str = "127.0.0.1", open_browser: bool = False) -> None:
    """Start the local app server (blocking). Ctrl-C stops it."""
    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/"
    print(f"pdt serve: {url} — open this URL in a browser (Ctrl-C stops the server)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\npdt serve: stopped")
    finally:
        server.server_close()
