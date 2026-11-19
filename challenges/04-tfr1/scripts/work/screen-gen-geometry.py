#!/usr/bin/env python3
"""Geometry screen for Genie 3 CA-trace designs (challenge 4, campaign 1).

Per design (runs/<set>/pdbs/<set>_<i>.pdb):
  binder = chain A (CA trace, UNK), target = chain B (CA trace).
Metrics:
  min_ca     smallest CA-CA distance binder->target (a buried design reads < 2.5)
  contacts   target CAs within 8.0 A of any binder CA
  hotspot    smallest CA-CA distance to any designed hotspot residue
             (block numbering: auth - 179; the genie3 output keeps the input
             numbering, asserted against the target fasta on the first file)

Pass rule (pre-registered): min_ca >= 3.0 AND contacts >= 3 AND hotspot <= 12.0.

Writes logs/gen-geometry.csv and state/pass-gen.txt.
Run: .venv/bin/python screen-gen-geometry.py (from the repo root)
"""
from __future__ import annotations

import csv
import math
import pathlib

HOME = pathlib.Path.home()
RUNS = HOME / "c4-work/genie3/runs"
OUT_CSV = HOME / "c4-work/logs/gen-geometry.csv"
PASS = HOME / "c4-work/state/pass-gen.txt"

SETS = {
    "11qc_e0": (25, 29, 31, 32, 169, 192),
    "11qc_e1": (27, 28, 30, 195),
    "11qc_e2": (164, 165, 168, 171, 172),
    "11qc_e12": (165, 195),
    "11qc_e0b2": (25, 29, 31, 32, 169, 192),
    "11qc_e1b2": (27, 28, 30, 195),
    "11qc_e2b2": (164, 165, 168, 171, 172),
    "11qc_e12b2": (165, 195),
}


def load_ca(path: pathlib.Path):
    ca = {}
    for line in path.read_text().splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            key = (line[21], int(line[22:26]))
            ca[key] = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
    return ca


def dist(a, b):
    return math.dist(a, b)


def target_names(path: pathlib.Path):
    names = {}
    for line in path.read_text().splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA" and line[21] == "B":
            names[int(line[22:26])] = line[17:20].strip()
    return names


def main() -> int:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    PASS.parent.mkdir(parents=True, exist_ok=True)
    rows, passed = [], []
    first = True
    for key, hotspots in SETS.items():
        pdbs = sorted((RUNS / key / "pdbs").glob("*.pdb")) if (RUNS / key / "pdbs").exists() else []
        print(f"{key}: {len(pdbs)} designs")
        for pdb in pdbs:
            ca = load_ca(pdb)
            binder = {k: v for k, v in ca.items() if k[0] == "A"}
            target = {k: v for k, v in ca.items() if k[0] == "B"}
            if not binder or not target:
                print(f"  {pdb.name}: missing chains (binder {len(binder)}, target {len(target)})")
                continue
            if first:
                nums = sorted(k[1] for k in target)
                names = target_names(pdb)   # {resnum: three-letter}
                print(f"  NUMBERING CHECK on {pdb.name}: target residues {len(nums)}, "
                      f"range {nums[0]}-{nums[-1]}")
                exp = "".join((HOME / "c4-work/targets/block.fa").read_text().splitlines()[1:])
                three = {"A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS",
                         "Q": "GLN", "E": "GLU", "G": "GLY", "H": "HIS", "I": "ILE",
                         "L": "LEU", "K": "LYS", "M": "MET", "F": "PHE", "P": "PRO",
                         "S": "SER", "T": "THR", "W": "TRP", "Y": "TYR", "V": "VAL"}
                for n in sorted({h for s in SETS.values() for h in s}):
                    got = names.get(n, "?")
                    want = three[exp[n - 1]]
                    print(f"    B{n}: {got} (block fasta {want}) "
                          f"{'OK' if got == want else 'MISMATCH'}")
                first = False
            min_ca = min(dist(b, t) for b in binder.values() for t in target.values())
            contacts = sum(1 for t in target.values()
                           if min(dist(b, t) for b in binder.values()) <= 8.0)
            hot = min((min(dist(b, target["B", n]) for b in binder.values())
                       for n in hotspots if ("B", n) in target), default=99.0)
            ok = min_ca >= 3.0 and contacts >= 3 and hot <= 12.0
            rows.append({
                "design": pdb.stem, "set": key, "binder_len": len(binder),
                "min_ca": round(min_ca, 2), "contacts": contacts,
                "hotspot_ca": round(hot, 2), "pass": ok,
            })
            if ok:
                passed.append(pdb.stem)
    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    PASS.parent.mkdir(parents=True, exist_ok=True)
    PASS.write_text("\n".join(passed) + "\n")
    print(f"total {len(rows)} designs, {len(passed)} pass geometry -> {OUT_CSV.name}, {PASS.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
