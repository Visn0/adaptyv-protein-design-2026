#!/usr/bin/env python3
"""Build the Mol* structure-explorer pages for the challenge-5 campaigns.

Same pattern as the challenge-2/3/4 builds: each experiment (or chapter)
lists the folds to show in its lineage `viewer` field; this script superposes
every fold's target onto the organizer crystal frame (7OW6, chains A/B/C,
numbering identical to the folds), extracts the binder chain (D) and its
interface residues, and renders one page per experiment via the shared
tools.serve.molstar_viewer.

Fold sources: ~/c5-work/{s1,s1w3,camp,c2p,c6,s1w4,c9,c0t}/folds/<design>/
boltz_results_<design>/predictions/<design>/<design>_model_0.cif

Usage:
  .venv/bin/python challenges/05-pmhc/viewers/scripts/make_molstar_multiview.py <exp_id> [...]
"""

from __future__ import annotations

import io
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402
from Bio.PDB import MMCIFParser, PDBIO, Select, Superimposer  # noqa: E402

from tools.serve import molstar_viewer  # noqa: E402

CH = pathlib.Path(__file__).resolve().parents[2]
WORK = pathlib.Path.home() / "c5-work"
OUT = CH / "viewers" / "multiview"
CRYSTAL = CH / "inputs" / "7OW6-G12D-noTCR.pdb"

BINDER_CHAIN = "D"
FOLD_SETS = ["s1", "s1w3", "camp", "c2p", "c6", "s1w4", "c9", "c0t", "repair", "s1w5", "s1w6", "c8", "repair2",
             "evo/gen1", "evo/gen2", "evo/gen3", "evo/gen4", "ml/surrogate-folds", "rfd4-batch1",
             "ft-batch", "pr-batch"]
BINDER_COLORS = [0xe879f9, 0x34d399, 0xa3e635, 0xf472b6, 0x22d3ee, 0xa78bfa,
                 0xfb7185, 0x4ade80, 0x2dd4bf, 0xd946ef]
TARGET_CHAIN_COLORS = {"A": 0x0099ff, "B": 0x64748b, "C": 0xfbbf24}


class _Chains(Select):
    def __init__(self, chains):
        self.chains = set(chains)

    def accept_chain(self, chain):
        return chain.id in self.chains


def fold_cif(design: str) -> pathlib.Path | None:
    for s in FOLD_SETS:
        hits = sorted((WORK / s / "folds").glob(
            f"{design}/boltz_results_*/predictions/{design}/{design}_model_0.cif"))
        if hits:
            return hits[0]
    return None


def ipTM(design: str) -> float | None:
    for s in FOLD_SETS:
        p = WORK / s / "s1-summary.csv"
        if not p.exists():
            continue
        import csv
        for row in csv.DictReader(p.open()):
            if row.get("design") == design:
                try:
                    return round(float(row["iptm_pep"]), 3)
                except (KeyError, ValueError):
                    return None
    return None


def _pdb_text(structure, select=None) -> str:
    writer = PDBIO()
    writer.set_structure(structure)
    handle = io.StringIO()
    if select is None:
        writer.save(handle)
    else:
        writer.save(handle, select)
    return handle.getvalue()


def _ca_map(structure, skip_binder=True):
    out = {}
    for chain in structure:
        if skip_binder and chain.id == BINDER_CHAIN:
            continue
        for residue in chain:
            if "CA" in residue:
                out[(chain.id, residue.id[1])] = residue["CA"]
    return out


# the crystal is the common frame; parse once
_CRYSTAL = MMCIFParser(QUIET=True).get_structure("c", str(CRYSTAL))[0] \
    if CRYSTAL.suffix == ".cif" else None
if _CRYSTAL is None:
    from Bio.PDB import PDBParser
    _CRYSTAL = PDBParser(QUIET=True).get_structure("c", str(CRYSTAL))[0]
CRYSTAL_CA = _ca_map(_CRYSTAL)

LOCAL_CUTOFF = 12.0
LOCAL_MIN = 12


def superpose_onto_crystal(structure):
    this_ca = _ca_map(structure)
    shared = [k for k in CRYSTAL_CA if k in this_ca]
    if not shared:
        raise ValueError("no shared target residues with the crystal")
    binder = np.array([a.get_coord() for a in structure[BINDER_CHAIN].get_atoms()])
    near = [k for k in shared
            if np.linalg.norm(binder - this_ca[k].get_coord(), axis=1).min()
            <= LOCAL_CUTOFF]
    keys, mode = (near, "epitope") if len(near) >= LOCAL_MIN else (shared, "global")
    fit = Superimposer()
    fit.set_atoms([CRYSTAL_CA[k] for k in keys], [this_ca[k] for k in keys])
    fit.apply(list(structure.get_atoms()))
    return float(fit.rms), len(keys), mode


def design_parts(design: str):
    cif = fold_cif(design)
    if cif is None:
        raise FileNotFoundError(f"no fold for {design}")
    structure = MMCIFParser(QUIET=True).get_structure("m", str(cif))[0]
    rms, nfit, mode = superpose_onto_crystal(structure)
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


def focus_of(pdb_text, chains):
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
    return {"center": [round(cx, 1), round(cy, 1), round(cz, 1)],
            "radius": round(r + 6.0, 1)}


def build(exp_id: str) -> pathlib.Path | None:
    if exp_id == "c0-instrument-calibration":
        # the control folds live in the TCR-Fv frame, not the pMHC frame -
        # showing the crystal target alone is the honest page here.
        exp = {"id": exp_id, "title": "C0 - the target and its chemistry",
               "summary": "", "proteins": [], "viewer": []}
    elif exp_id == "submission":
        import csv
        rows = list(csv.DictReader(
            (CH / "submission" / "submission-05-pmhc.csv").open()))
        exp = {"id": "submission", "title": "The submitted twenty",
               "summary": "", "proteins": [],
               "viewer": [r["name"] for r in rows]}
    else:
        data = json.loads((CH / "lineage.json").read_text())
        exp = None
        for candidate in data.get("experiments", []):
            if candidate.get("id") == exp_id and candidate.get("viewer"):
                exp = candidate
                break
            for chapter in candidate.get("chapters", []):
                if chapter.get("id") == exp_id and chapter.get("viewer"):
                    exp = {"id": exp_id, "title": chapter["title"],
                           "summary": chapter.get("text", ""),
                           "proteins": candidate.get("proteins", []),
                           "viewer": chapter["viewer"]}
    if exp is None or (not exp.get("viewer")
                       and exp_id != "c0-instrument-calibration"):
        return None

    items = [{
        "id": "target",
        "label": "KRAS G12D pMHC (7OW6) \u00b7 A = HLA-A*11:01, B = \u03b22m, C = peptide",
        "color": TARGET_CHAIN_COLORS["A"],
        "pdb": _pdb_text(_CRYSTAL, _Chains(["A", "B", "C"])),
        "chains": ["A", "B", "C"],
        "chainColors": dict(TARGET_CHAIN_COLORS),
        "interface": [], "scores": {},
    }]
    designs = exp["viewer"]
    top3 = set(designs[:3])
    for index, design in enumerate(designs):
        try:
            binder, interface, fit = design_parts(design)
        except Exception as exc:
            print(f"  {design}: skipped ({exc.__class__.__name__}: {exc})")
            continue
        score = ipTM(design)
        items.append({
            "id": design, "label": design, "design": design,
            "color": BINDER_COLORS[index % len(BINDER_COLORS)],
            "pdb": binder, "chains": [BINDER_CHAIN],
            "chainColors": {BINDER_CHAIN: BINDER_COLORS[index % len(BINDER_COLORS)]},
            "interface": interface,
            "focus": focus_of(binder, [BINDER_CHAIN]),
            "on": design in top3,
            "scores": {"iptm": score} if score is not None else {},
        })
        print(f"  {design}: {len(interface)} interface residues, "
              f"fit {fit[2]} on {fit[1]} CA, RMSD {fit[0]:.2f} A")

    OUT.mkdir(parents=True, exist_ok=True)
    bundle = OUT.parent / "molstar-bundle.js"
    if not bundle.exists():
        src = REPO / "challenges/02-tnfa/viewers/molstar-bundle.js"
        if src.exists():
            bundle.write_bytes(src.read_bytes())
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
