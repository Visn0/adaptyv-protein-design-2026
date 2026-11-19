#!/usr/bin/env python3
"""C0 step 0: the crystal ground truth for the instrument-calibration gate.

Reads the two TCR-bound crystals directly (7OW6 = JDI + G12D pMHC;
7OW5 = JDI + WT pMHC) and writes the contact metrics the folded reads must
reproduce: contacts per peptide position, the P6-to-TCR minimum distance, and
the HLA-helix contact residues.

Output: challenges/05-pmhc/campaigns/c0-instrument-calibration/records/crystal-read.csv

Run: .venv/bin/python challenges/05-pmhc/scripts/work/c0-crystal-read.py
"""

from __future__ import annotations

import csv
import pathlib

import numpy as np
from Bio.PDB import MMCIFParser

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
C5 = ROOT / "challenges" / "05-pmhc"
RECORDS = C5 / "campaigns" / "c0-instrument-calibration" / "records"
REFS = C5 / "inputs" / "reference-structures"

BINDER = ("D", "E")
PEPTIDE = "C"


def heavy(res):
    return [a for a in res if a.element != "H"]


def main() -> int:
    RECORDS.mkdir(parents=True, exist_ok=True)
    parser = MMCIFParser(QUIET=True)
    rows = []
    summary = {}
    for state, cif in (("g12d", "7OW6.cif"), ("wt", "7OW5.cif")):
        model = parser.get_structure(state, str(REFS / cif))[0]
        binder_atoms = [(r.id[1], a) for ch in BINDER for r in model[ch]
                        if r.id[0] == " " for a in heavy(r)]
        binder_xyz = np.array([a.get_coord() for _, a in binder_atoms])
        pep_contacts, pep_residues = {}, set()
        p6_min = None
        for res in model[PEPTIDE]:
            if res.id[0] != " ":
                continue
            pos = res.id[1]
            n = 0
            for a in heavy(res):
                d = np.linalg.norm(binder_xyz - a.get_coord(), axis=1)
                n += int((d < 4.5).sum())
                if pos == 6:
                    m = float(d.min())
                    p6_min = m if p6_min is None else min(p6_min, m)
            if n:
                pep_contacts[pos] = n
        hla_res = {}
        for res in model["A"]:
            if res.id[0] != " ":
                continue
            n = sum(1 for a in heavy(res)
                    if (np.linalg.norm(binder_xyz - a.get_coord(), axis=1) < 4.5).any())
            if n:
                hla_res[res.id[1]] = n
        summary[state] = {
            "peptide_contacts_per_pos": dict(sorted(pep_contacts.items())),
            "p6_min_dist_to_tcr": round(p6_min, 2) if p6_min is not None else None,
            "hla_contact_residues": sorted(hla_res),
        }
        for pos in range(1, 11):
            rows.append({"state": state, "metric": f"peptide_contacts_P{pos}",
                         "value": pep_contacts.get(pos, 0)})
        rows.append({"state": state, "metric": "p6_min_dist_to_tcr",
                     "value": summary[state]["p6_min_dist_to_tcr"]})

    out = RECORDS / "crystal-read.csv"
    with open(out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["state", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)

    for state, s in summary.items():
        print(f"== {state} ==")
        print("  peptide contacts per position:", s["peptide_contacts_per_pos"])
        print("  P6 min dist to TCR:", s["p6_min_dist_to_tcr"], "A")
        print("  HLA helix contact residues:", s["hla_contact_residues"])
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
