#!/usr/bin/env python3
"""Build the multi-protein structure explorer: the shared TNF target plus every
designed binder of an experiment, in the same UI as the single-design explorer
(make_molstar_explorer.py) — header, left toolbar, DESIGNS panel, coloring
options — with one addition: the DESIGNS panel selects one or many designs
(colour dot + name + score chips), so they are compared against the same
target in one scene.

    .venv/bin/python make_molstar_multiview.py genie3-campaign

Reads the experiment's `viewer` design list from lineage.json, picks each
design's best at-site model, extracts the binder chain, computes its interface
residues, and embeds everything in a self-contained page.
"""
from __future__ import annotations

import csv
import io
import json
import pathlib
import re
import sys

import numpy as np

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH = REPO / "challenges" / "03-glp1r"
REPO_PATH = _repo_root()
sys.path.insert(0, str(REPO_PATH))
from tools.serve import molstar_viewer  # noqa: E402
FOLDS = pathlib.Path.home() / "c3-work" / "folds"
SCREEN = pathlib.Path.home() / "c3-work" / "folds-screen.csv"
OUT = CH / "viewers" / "multiview"

# binder palette: the standing binder pink first, then distinct hues; the
# target chains keep the cyan family (per-chain uniform)
BINDER_COLORS = [0xe879f9, 0x34d399, 0xfbbf24, 0x60a5fa, 0xf472b6, 0x22d3ee,
                 0xa78bfa, 0xfb7185, 0x4ade80, 0xfacc15]
TARGET_CHAIN_COLORS = {"B": 0x0099ff}
BINDER_CHAIN = "A"

from Bio.PDB import MMCIFParser, PDBIO, Select, Superimposer  # noqa: E402


class _Chains(Select):
    def __init__(self, chains):
        self.chains = set(chains)

    def accept_chain(self, chain):
        return chain.id in self.chains


def best_model(design: str) -> int:
    """Best-ipSAE sample index from the challenge-3 screen table; 0 as fallback."""
    best = None
    for r in csv.DictReader(open(SCREEN)):
        if r["design"].strip() != design:
            continue
        ip = float(r["ipsae"])
        if best is None or ip > best[0]:
            best = (ip, int(r["sample"]))
    return best[1] if best else 0


def cif_path(design: str, model: int) -> pathlib.Path:
    return (FOLDS / design / f"boltz_results_{design}" / "predictions" / design
            / f"{design}_model_{model}.cif")


def _pdb_text(structure, select=None) -> str:
    writer = PDBIO()
    writer.set_structure(structure)
    handle = io.StringIO()
    writer.save(handle, select)
    return handle.getvalue()


def _target_ca(structure) -> dict:
    """CA atoms of the target chains, keyed by (chain id, residue number)."""
    out = {}
    for chain in structure:
        if chain.id == BINDER_CHAIN:
            continue
        for residue in chain:
            if "CA" in residue:
                out[(chain.id, residue.id[1])] = residue["CA"]
    return out


_REFERENCE: dict = {}


def _reference(design: str):
    """(structure, target CA atoms) of the scene's reference fold, parsed once."""
    if design not in _REFERENCE:
        model = best_model(design)
        structure = MMCIFParser(QUIET=True).get_structure(
            "ref", str(cif_path(design, model)))[0]
        _REFERENCE[design] = (structure, _target_ca(structure))
    return _REFERENCE[design]


LOCAL_CUTOFF = 12.0   # A around the binder: the epitope neighbourhood
LOCAL_MIN = 12        # fall back to a global fit below this many residues


def superpose_onto_reference(structure, design: str, reference_design: str):
    """Move `structure` into the reference fold's frame; return (rmsd, n, mode).

    Boltz writes every complex in its own arbitrary global frame, so embedding
    one fold's target beside another fold's binder puts the binder wherever its
    own fold happened to land - through the receptor core, not at the epitope.

    A GLOBAL fit on all shared target CA is not enough on its own: the predicted
    receptor conformation differs between folds by 2-13 A CA RMSD (measured
    across the 20 submitted designs), and a rigid global fit spreads that error
    over the whole chain, leaving the binder several angstrom off its true site
    and still inside the receptor. Fitting on the target residues that this
    binder actually touches preserves the binder-epitope geometry, which is what
    the scene is about; the far side of the receptor is allowed to disagree.
    """
    _, reference_ca = _reference(reference_design)
    this_ca = _target_ca(structure)
    shared = [k for k in reference_ca if k in this_ca]
    if not shared:
        raise ValueError(f"{design}: no target residues shared with {reference_design}")
    binder = np.array([a.get_coord() for a in structure[BINDER_CHAIN].get_atoms()])
    near = [k for k in shared
            if np.linalg.norm(binder - this_ca[k].get_coord(), axis=1).min() <= LOCAL_CUTOFF]
    keys, mode = (near, "epitope") if len(near) >= LOCAL_MIN else (shared, "global")
    fit = Superimposer()
    fit.set_atoms([reference_ca[k] for k in keys], [this_ca[k] for k in keys])
    fit.apply(list(structure.get_atoms()))
    return float(fit.rms), len(keys), mode


def design_parts(design: str, reference_design: str):
    """(binder PDB text, interface residues, target RMSD after superposition)."""
    model = best_model(design)
    structure = MMCIFParser(QUIET=True).get_structure("m", str(cif_path(design, model)))[0]
    rms, nfit, mode = superpose_onto_reference(structure, design, reference_design)
    binder = structure[BINDER_CHAIN]
    targets = [c for c in structure if c.id != BINDER_CHAIN]
    batoms = [(a.get_coord(), a.get_parent().id[1]) for a in binder.get_atoms()]
    contacts = set()
    for ch in targets:
        for ta in ch.get_atoms():
            tc = ta.get_coord()
            for bc, resnum in batoms:
                if ((bc[0] - tc[0]) ** 2 + (bc[1] - tc[1]) ** 2
                        + (bc[2] - tc[2]) ** 2) <= 4.5 ** 2:
                    contacts.add(resnum)
                    break
    binder_pdb = _pdb_text(structure, _Chains([BINDER_CHAIN]))
    return binder_pdb, sorted(contacts), (rms, nfit, mode)


def target_pdb(design: str) -> str:
    """The target chains of the reference fold: the frame every binder is fitted to."""
    structure, _ = _reference(design)
    return _pdb_text(structure, _Chains([c.id for c in structure if c.id != BINDER_CHAIN]))





def _submission_designs() -> list[str]:
    """The ranked design names from the newest submission CSV (template skipped)."""
    sub_dir = CH / "submission"
    files = [f for f in sorted(sub_dir.glob("competition-submission-*.csv"))
             if "template" not in f.name]
    if not files:
        return []
    with open(files[-1]) as handle:
        return [row.get("name", "") for row in csv.DictReader(handle) if row.get("name")]


def focus_of(pdb_text, chains):
    """The binder atoms' bounding sphere, for the viewer's default camera."""
    pts = []
    for line in pdb_text.splitlines():
        if line.startswith(("ATOM", "HETATM")):
            if chains and line[21] not in chains:
                continue
            try:
                pts.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
    if not pts:
        return None
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    cz = sum(p[2] for p in pts) / len(pts)
    r = max(((p[0]-cx)**2 + (p[1]-cy)**2 + (p[2]-cz)**2) ** 0.5 for p in pts)
    return {"center": [round(cx, 1), round(cy, 1), round(cz, 1)], "radius": round(r + 6.0, 1)}


def build(exp_id: str) -> pathlib.Path | None:
    data = json.loads((CH / "lineage.json").read_text())
    exp = None
    if exp_id == "submission":
        # the submission draws designs from many campaigns: collect them all
        designs = _submission_designs()
        proteins = [p for e in data.get("experiments", []) for p in e.get("proteins", [])]
        exp = {"id": "submission", "title": "The submission — selected 20",
               "summary": "The twenty selected designs, in rank order.",
               "proteins": proteins, "viewer": designs}
    for candidate in ([] if exp else data.get("experiments", [])):
        if candidate.get("id") == exp_id:
            exp = candidate
            break
        for chapter in candidate.get("chapters", []):
            if chapter.get("id") == exp_id and chapter.get("viewer"):
                exp = {"id": exp_id, "title": chapter["title"],
                       "summary": chapter.get("text", ""),
                       "proteins": candidate.get("proteins", []),
                       "viewer": chapter["viewer"]}
    if exp is None or not exp.get("viewer"):
        return None

    by_design = {p["design"]: p for p in exp.get("proteins", [])}
    is_tnfa = "tnfa" in str(CH)
    items = [{
        "id": "target",
        "label": "TNF-\u03b1 trimer (target)" if is_tnfa else "GLP-1 receptor (target)",
        "color": TARGET_CHAIN_COLORS["B"],
        "pdb": target_pdb(exp["viewer"][0]),
        "chains": ["B", "C", "D"] if is_tnfa else ["B"],
        "chainColors": dict(TARGET_CHAIN_COLORS),
        "interface": [], "scores": {},
    }]
    reference_design = exp["viewer"][0]
    for index, design in enumerate(exp["viewer"]):
        binder, interface, fit = design_parts(design, reference_design)
        entry = by_design.get(design, {})
        items.append({
            "id": design, "label": design,
            "color": BINDER_COLORS[index % len(BINDER_COLORS)],
            "pdb": binder, "chains": [BINDER_CHAIN],
            "chainColors": {BINDER_CHAIN: BINDER_COLORS[index % len(BINDER_COLORS)]},
            "interface": interface,
            "focus": focus_of(binder, [BINDER_CHAIN]),
            # best three only, by the ranked viewer order (2026-10-30 consistency pass)
            "on": index < 3,
            "scores": {"ipsae": entry.get("ipsae_min"), "pdockq2": entry.get("pdockq2"),
                       "activation": entry.get("activation")},
        })
        print(f"  {design}: {len(interface)} interface residues, "
              f"fit {fit[2]} on {fit[1]} CA, RMSD {fit[0]:.2f} A")

    OUT.mkdir(parents=True, exist_ok=True)
    html = molstar_viewer.render_viewer_page(
        items, title=exp["title"], label=exp["title"], slug=exp_id,
        binder_chain=BINDER_CHAIN)
    out = OUT / f"{exp_id}.html"
    out.write_text(html)
    return out


if __name__ == "__main__":
    for exp_id in sys.argv[1:]:
        path = build(exp_id)
        print(f"{exp_id} -> {path}" if path else f"{exp_id}: nothing to build")
