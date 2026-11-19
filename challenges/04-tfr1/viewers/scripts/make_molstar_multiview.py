#!/usr/bin/env python3
"""Build the Mol* structure-explorer pages for the challenge-4 campaigns.

Same pattern as the challenge-2/3 builds: each experiment lists the folds to
show in its lineage entry's `viewer` field; this script superposes every fold's
target onto the reference fold's frame, extracts the binder chain and its
interface residues, and renders one page per experiment via the shared
`tools.serve.molstar_viewer`.

Challenge-4 adaptations:
  - folds are chai runs: ~/c4-work/chai/designs/<name>/out/pred.model_idx_N.cif
  - the best sample is the argmax-ipTM npz of that design
  - scores shown = the campaign read, mean restrained ipTM over the 5 samples
Names in a viewer list may be any fold-dir name (e12_*, e12rfd4_*, b3_*,
c3_*, c4mn_*, c5B_*/c5C_*). Usage:

  .venv/bin/python challenges/04-tfr1/viewers/scripts/make_molstar_multiview.py <exp_id> [...]
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
FOLDS = pathlib.Path.home() / "c4-work" / "chai" / "designs"
OUT = CH / "viewers" / "multiview"

BINDER_COLORS = [0xe879f9, 0x34d399, 0xfbbf24, 0x60a5fa, 0xf472b6, 0x22d3ee,
                 0xa78bfa, 0xfb7185, 0x4ade80, 0xfacc15]
TARGET_CHAIN_COLORS = {"A": 0x0099ff}
BINDER_CHAIN = "B"


class _Chains(Select):
    def __init__(self, chains):
        self.chains = set(chains)

    def accept_chain(self, chain):
        return chain.id in self.chains


def best_model(design: str) -> int:
    best = None
    for i in range(5):
        npz = FOLDS / design / "out" / f"scores.model_idx_{i}.npz"
        if not npz.exists():
            continue
        value = float(np.asarray(np.load(npz, allow_pickle=True)["iptm"]).reshape(-1)[0])
        if best is None or value > best[0]:
            best = (value, i)
    return best[1] if best else 0


def mean_iptm(design: str) -> float | None:
    values = []
    for i in range(5):
        npz = FOLDS / design / "out" / f"scores.model_idx_{i}.npz"
        if npz.exists():
            values.append(float(np.asarray(np.load(npz, allow_pickle=True)["iptm"])
                                .reshape(-1)[0]))
    return round(float(np.mean(values)), 3) if values else None


def cif_path(design: str, model: int) -> pathlib.Path:
    return FOLDS / design / "out" / f"pred.model_idx_{model}.cif"


def _pdb_text(structure, select=None) -> str:
    writer = PDBIO()
    writer.set_structure(structure)
    handle = io.StringIO()
    if select is None:
        writer.save(handle)
    else:
        writer.save(handle, select)
    return handle.getvalue()


def _target_ca(structure) -> dict:
    out = {}
    for chain in structure:
        if chain.id == BINDER_CHAIN:
            continue
        for residue in chain:
            if "CA" in residue:
                out[(chain.id, residue.id[1])] = residue["CA"]
    return out


_REFERENCE: dict = {}


REF11QC = MMCIFParser(QUIET=True).get_structure(
    "r", str(REPO / "challenges/04-tfr1/inputs/11QC.cif"))[0]
_GLYCAN = {"NAG", "MAN", "BMA", "FUC", "GAL", "SIA"}
# chain A CAs keyed in FOLD numbering (auth 122-760 -> 1-639); chain A is
# exactly the fold target sequence (verified 2026-10-28).
REF11QC_CA = {("A", r.id[1] - 121): r["CA"] for r in REF11QC["A"]
              if r.resname not in _GLYCAN and "CA" in r}


def _reference_fold(design: str):
    if design not in _REFERENCE:
        model = best_model(design)
        structure = MMCIFParser(QUIET=True).get_structure(
            "ref", str(cif_path(design, model)))[0]
        _REFERENCE[design] = (structure, _target_ca(structure))
    return _REFERENCE[design]


def _reference(design: str):
    """Human items share the 11QC dimer frame (the overview's target); mouse
    items keep their own fold frame (the mouse model is a single chain)."""
    if design.startswith("c4mn_"):
        return _reference_fold(design)
    return REF11QC, REF11QC_CA


LOCAL_CUTOFF = 12.0
LOCAL_MIN = 12


def superpose_onto_reference(structure, design: str, reference_design: str):
    """Move `structure` into the reference fold's frame; return (rmsd, n, mode).

    Every chai run writes its complex in its own recentered frame, so the fit
    is on the target residues this binder actually touches (epitope-local);
    the far side of the receptor is allowed to disagree.
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


def focus_of(pdb_text, chains):
    """The binder atoms' bounding sphere, for the viewer's default camera.

    The generator precomputes it so the page can frame the interaction region
    (the visible designs) instead of the whole 639-residue ectodomain. Radius
    carries a margin so a couple of target residues stay in view."""
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


def target_pdb(design: str) -> str:
    structure, _ = _reference(design)
    if not design.startswith("c4mn_"):
        return _pdb_text(structure)  # 11QC: both protomers + glycans
    return _pdb_text(structure, _Chains([c.id for c in structure if c.id != BINDER_CHAIN]))


def target_pdb_superposed(design: str, reference_design: str) -> str:
    """The target chains of `design`, moved onto the reference frame."""
    model = best_model(design)
    structure = MMCIFParser(QUIET=True).get_structure("m", str(cif_path(design, model)))[0]
    superpose_onto_reference(structure, design, reference_design)  # in place
    return _pdb_text(structure, _Chains([c.id for c in structure if c.id != BINDER_CHAIN]))


def build(exp_id: str) -> pathlib.Path | None:
    if exp_id == "c5-multi-chain":
        # c5's page is the block-rescue explorer, built by make_extra_viewers.py
        # from the boltz c5-rescue outputs; the lineage's unit tags do not
        # resolve to chai folds, so building it here only ever failed.
        print("c5-multi-chain: built by make_extra_viewers.py - skipped here")
        return None
    data = json.loads((CH / "lineage.json").read_text())
    exp = None
    for candidate in data.get("experiments", []):
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

    reference_design = exp["viewer"][0]
    items = [{
        "id": "target",
        "label": "TfR1 ectodomain homodimer \u00b7 chain A = binder target",
        "color": TARGET_CHAIN_COLORS["A"],
        "pdb": target_pdb(reference_design),
        "chains": ["A"],
        "chainColors": dict(TARGET_CHAIN_COLORS),
        "interface": [], "scores": {},
    }]
    mouse_first = next((d for d in exp["viewer"] if d.startswith("c4mn_")), None)
    if mouse_first:
        # the mouse receptor carries its own numbering, so mouse items get their
        # own frame (the mouse target), independent of the human frame; the
        # species tabs show one frame at a time, so the overlap is invisible.
        items.append({
            "id": "target-mouse",
            "label": "TfR1 ectodomain (mouse target)",
            "color": TARGET_CHAIN_COLORS["A"],
            "pdb": target_pdb(mouse_first),
            "chains": ["A"],
            "chainColors": dict(TARGET_CHAIN_COLORS),
            "interface": [], "scores": {}, "species": "mouse", "on": False,
        })
    base_order = []
    for d in exp["viewer"]:
        b = d[5:] if d.startswith("c4mn_") else d
        if b not in base_order:
            base_order.append(b)
    top3 = set(base_order[:3])   # only the best three designs are visible by default
    for index, design in enumerate(exp["viewer"]):
        ref = mouse_first if (design.startswith("c4mn_") and mouse_first) else reference_design
        try:
            binder, interface, fit = design_parts(design, ref)
        except Exception as exc:  # a missing fold must not kill the whole build
            print(f"  {design}: skipped ({exc.__class__.__name__}: {exc})")
            continue
        base = design[5:] if design.startswith("c4mn_") else design
        label = (base + " \u00b7 mouse") if design.startswith("c4mn_") else design
        items.append({
            "id": design, "label": label, "design": base,
            "species": "mouse" if design.startswith("c4mn_") else "human",
            "color": BINDER_COLORS[index % len(BINDER_COLORS)],
            "pdb": binder, "chains": [BINDER_CHAIN],
            "chainColors": {BINDER_CHAIN: BINDER_COLORS[index % len(BINDER_COLORS)]},
            "interface": interface,
            "focus": focus_of(binder, [BINDER_CHAIN]),
            "on": base in top3,
            "scores": {"iptm": mean_iptm(design)},
        })
        print(f"  {design}: {len(interface)} interface residues, "
              f"fit {fit[2]} on {fit[1]} CA, RMSD {fit[0]:.2f} A")

    OUT.mkdir(parents=True, exist_ok=True)
    # the Mol* library must sit one level above the multiview pages; the
    # challenge-2/3 generators copy it, this one used to skip it (viewer
    # failed with "Molstar is not defined", 2026-10-28).
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
