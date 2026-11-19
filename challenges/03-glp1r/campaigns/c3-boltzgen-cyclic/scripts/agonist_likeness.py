#!/usr/bin/env python
"""Agonist-likeness: how much of the real GLP-1 contact pattern a design copies.

The reference is the activating peptide itself (6X18 chain P, GLP-1) against
the receptor (chain R, UniProt numbering). For each of the four sub-sites the
script collects the receptor residues the real agonist touches, then for every
design's fold it measures how many of those same residues the binder touches
(4.5 A heavy-atom contact). The score is the fraction of the reference pattern
reproduced, per sub-site and overall.

    .venv/bin/python challenges/03-glp1r/campaigns/c3-boltzgen-cyclic/scripts/agonist_likeness.py [design ...]

With no arguments it scores every design that has a fold under ~/c3-work/folds
and writes ~/c3-work/agonist-likeness.csv.
"""
from __future__ import annotations

import csv
import pathlib
import sys

from Bio.PDB import MMCIFParser, PDBParser

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH = REPO / "challenges" / "03-glp1r"
FOLDS = pathlib.Path.home() / "c3-work" / "folds"
SCREEN = pathlib.Path.home() / "c3-work" / "folds-screen.csv"
OUT = pathlib.Path.home() / "c3-work" / "agonist-likeness.csv"

SUBSITES = {
    "groove": [67, 69, 88, 91, 121, 128],
    "junction": [197, 210, 221, 234],
    "tm": [298, 300, 309, 313],
    "ecl3": [376, 377, 380, 381, 384, 387, 388, 391],
}
CONTACT = 4.5


def contacts(structure, chain_a, chain_b, allowed=None):
    """Receptor residues (chain_b) within CONTACT of any atom of chain_a."""
    a_atoms = [a.get_coord() for a in structure[chain_a].get_atoms()]
    hits = set()
    for atom in structure[chain_b].get_atoms():
        resnum = atom.get_parent().id[1]
        if allowed is not None and resnum not in allowed:
            continue
        c = atom.get_coord()
        for ac in a_atoms:
            if ((c[0] - ac[0]) ** 2 + (c[1] - ac[1]) ** 2
                    + (c[2] - ac[2]) ** 2) <= CONTACT ** 2:
                hits.add(resnum)
                break
    return hits


def reference_pattern():
    """The residues GLP-1 (chain P) touches on the receptor (chain R), by sub-site."""
    st = PDBParser(QUIET=True).get_structure("ref", str(CH / "inputs" / "6X18.pdb"))[0]
    ref = {}
    for name, residues in SUBSITES.items():
        touched = contacts(st, "P", "R", allowed=set(residues))
        ref[name] = touched
    return ref


def design_pattern(cif: pathlib.Path):
    st = MMCIFParser(QUIET=True).get_structure("d", str(cif))[0]
    return {name: contacts(st, "A", "B", allowed=set(residues))
            for name, residues in SUBSITES.items()}


def best_sample(design: str) -> int:
    best = None
    for r in csv.DictReader(open(SCREEN)):
        if r["design"].strip() != design:
            continue
        ip = float(r["ipsae"])
        if best is None or ip > best[0]:
            best = (ip, int(r["sample"]))
    return best[1] if best else 0


def fold_cif(design: str, model: int) -> pathlib.Path:
    return (FOLDS / design / f"boltz_results_{design}" / "predictions" / design
            / f"{design}_model_{model}.cif")


def main(designs):
    ref = reference_pattern()
    print("reference (GLP-1, 6X18) contacts per sub-site:")
    for name, touched in ref.items():
        print(f"  {name:8s} {sorted(touched)}")

    if not designs:
        designs = sorted({r["design"] for r in csv.DictReader(open(SCREEN))})

    rows = []
    for design in designs:
        cif = fold_cif(design, best_sample(design))
        if not cif.exists():
            continue
        pat = design_pattern(cif)
        row = {"design": design}
        total_hit, total_ref = 0, 0
        for name in SUBSITES:
            r, d = ref[name], pat[name]
            row[name] = len(r & d)
            row[f"{name}_ref"] = len(r)
            total_hit += len(r & d)
            total_ref += len(r)
        row["likeness"] = round(total_hit / total_ref, 3) if total_ref else 0.0
        rows.append(row)

    rows.sort(key=lambda r: -r["likeness"])
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["design", "likeness"] + list(SUBSITES)
                           + [f"{n}_ref" for n in SUBSITES])
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} designs scored -> {OUT}")
    print(f"{'design':26s} {'like':>5s} {'grv':>3s} {'jun':>3s} {'tm':>3s} {'ecl3':>4s}")
    for r in rows[:15]:
        print(f"{r['design']:26s} {r['likeness']:5.2f} {r['groove']:>3d} "
              f"{r['junction']:>3d} {r['tm']:>3d} {r['ecl3']:>4d}")


if __name__ == "__main__":
    main(sys.argv[1:])
