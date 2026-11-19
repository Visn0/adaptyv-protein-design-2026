#!/usr/bin/env python3
"""R2: charge-directed repair of the top designs (the local substitute for
ArcRefine, which exceeds 12 GB on this complex).

For each design: find the binder positions whose CA sits 5-13 A from the D6
carboxylate (the shell that can read the mutation). Enumerate single-point
variants: basic substitutions (K/R) at those positions, and neutral/positive
replacements for acidic residues pointing at D6. Each variant is folded with
boltz and re-read with the E-score; improvements enter the pool.

Output: ~/c5-work/repair/folds/*.yaml + variants.csv
Usage: PYTHONPATH= .venv/bin/python repair-build.py
"""

from __future__ import annotations

import csv
import glob
import os
import pathlib

import gemmi
import yaml

W = pathlib.Path.home() / "c5-work"
OUT = W / os.environ.get("REPAIR_OUT", "repair") / "folds"
SETS = ("s1", "s1w3", "camp", "c2p", "c6", "s1w4")
BASIC = "KR"
ACIDIC = "DE"
_env = os.environ.get("REPAIR_DESIGNS")
DESIGNS = _env.split(",") if _env else [
    "nim-wave3__run-001__design_0004__g12d__c7",
    "wave2-pep__run-024__design_0007__g12d__c5",
    "peprim-wave1__run-001__design_0002__g12d",
    "wave2-pep__run-016__design_0005__g12d",
    "nim-wave3__run-021__design_0001__g12d",
    "nat-wave1__run-004__design_0001__g12d",
]
AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}


def fold_cif(design: str):
    for s in SETS:
        hits = glob.glob(str(W / s / "folds" / design / "boltz_results_*"
                             / "predictions" / design / f"{design}_model_0.cif"))
        if hits:
            return hits[0]
    return None


def shell_positions(design: str):
    """Binder residue numbers whose CA is 5-13 A from any D6 carboxylate O."""
    st = gemmi.read_structure(fold_cif(design))
    binder = st[0].find_chain("D")
    peptide = st[0].find_chain("C")
    d6 = [a.pos for r in peptide if r.seqid.num == 6 for a in r
          if a.name in ("OD1", "OD2", "CG")]
    out = []
    for r in binder:
        ca = next((a for a in r if a.name == "CA"), None)
        if ca is None:
            continue
        d = min(ca.pos.dist(p) for p in d6)
        if 5.0 <= d <= 13.0:
            out.append((r.seqid.num, AA3.get(r.name, "X"), round(d, 1)))
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    base_yaml = None
    for s in SETS:
        cand = sorted((W / s / "folds").glob("*.yaml"))
        if cand:
            base_yaml = cand[0]
            break
    head = base_yaml.read_text().split("  - protein:\n      id: D")[0]
    head = head.removeprefix("version: 1\n")
    rows = []
    made = 0
    for design in DESIGNS:
        cif = fold_cif(design)
        if not cif:
            print(f"no fold: {design}")
            continue
        st = gemmi.read_structure(cif)
        binder_seq = gemmi.one_letter_code(
            [r.name for r in st[0].find_chain("D")])
        shell = shell_positions(design)
        # variants: basic swaps at shell positions; neutralize acids in shell
        variants = []
        for num, aa, dist in shell:
            if aa not in BASIC and aa != "P":
                variants.append((num, aa, "K", dist))
            if aa in ACIDIC:
                variants.append((num, aa, "A", dist))
        # cap at 4 variants per design (the closest shell positions first)
        variants = sorted(variants, key=lambda v: v[3])[:4]
        for num, old, new, dist in variants:
            seq = list(binder_seq)
            if num - 1 >= len(seq):
                continue
            seq[num - 1] = new
            seq = "".join(seq)
            name = f"repair-{design}-{old}{num}{new}"
            (OUT / f"{name}.yaml").write_text(
                "version: 1\n" + head
                + "  - protein:\n      id: D\n      sequence: " + seq
                + "\n      msa: empty\n")
            rows.append({"variant": name, "parent": design, "position": num,
                         "from": old, "to": new, "dist_to_D6": dist})
            made += 1
    with (W / "repair" / "variants.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"repair variants: {made} yamls for {len(DESIGNS)} designs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
