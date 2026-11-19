#!/usr/bin/env python3
"""Stage 0: the pose-based screen over the C1 design pool (CPU only).

Every RFD4 NIM design is already a posed binder-pMHC complex
(A=HLA 1-276, B=b2m 1-99, C=peptide 1-10, D=binder), so the cheap specificity
signals read directly off the generator's pose - no fold needed. The
shortlist from this screen is what gets independent Boltz-2 folds for the
ipSAE gates (notes/strategies.md, funnel revision 2026-10-31).

Per design:
  contacts (<4.5 A heavy-atom) binder->peptide / ridge(P4-P8) / HLA / b2m,
  peptide share of all target contacts, P6 min distance,
  C3 electrostatic rule: a binder basic side-chain N (Arg/Lys/His) in the
  6-8 A shell over P6-P7; n_other_positives = other binder basic nitrogens
  within 8 A of the same shell.

Pre-registered pass flags (the C0 addendum logic applied to poses):
  arcs         ridge_contacts >= 10 and hla_contacts >= 30
  peptide_first  peptide_share >= 0.20
  c3            has the 6-8 A basic nitrogen over P6-P7

Usage:
  .venv/bin/python s0-pose-screen.py --dir ~/c5-work/c1 --out ~/c5-work/s0/pose-screen.csv
"""

from __future__ import annotations

import argparse
import csv
import pathlib

import gemmi
import numpy as np

AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V", "MSE": "M"}
BASIC_N = {"ARG": ("NE", "NH1", "NH2"), "LYS": ("NZ",),
           "HIS": ("ND1", "NE2")}
BINDER, PEPTIDE, HLA, B2M = "D", "C", "A", "B"
P6, P7 = 6, 7
SHELL_LO, SHELL_HI, OTHER_WINDOW = 6.0, 8.0, 8.0


def load(st: gemmi.Structure):
    atoms = []
    for c in st[0]:
        for r in c:
            if r.name not in AA3:
                continue
            for a in r:
                if a.element.name == "H":
                    continue
                atoms.append((c.name, r.seqid.num, r.name, a.name, a.pos))
    return atoms


def screen(path: pathlib.Path, args) -> dict | None:
    try:
        st = gemmi.read_structure(str(path))
    except Exception:
        return None
    if not len(st):
        return None
    atoms = load(st)
    if not atoms:
        return None
    bxyz = np.array([(a[4].x, a[4].y, a[4].z) for a in atoms if a[0] == BINDER])
    if not len(bxyz):
        return None

    def contacts(chain: str, resnums: set[int] | None = None) -> int:
        n = 0
        for a in atoms:
            if a[0] != chain or (resnums and a[1] not in resnums):
                continue
            d = np.linalg.norm(bxyz - np.array([a[4].x, a[4].y, a[4].z]), axis=1)
            n += int((d < args.cutoff).sum())
        return n

    pep = contacts(PEPTIDE)
    ridge = contacts(PEPTIDE, {4, 5, 6, 7, 8})
    hl = contacts(HLA)
    b2 = contacts(B2M)
    total = pep + hl + b2
    share = pep / total if total else 0.0

    shell = [(a[4].x, a[4].y, a[4].z) for a in atoms
             if a[0] == PEPTIDE and a[1] in (P6, P7)
             and a[3] in ("CA", "CB", "CG")]
    p6 = [(a[4].x, a[4].y, a[4].z) for a in atoms
          if a[0] == PEPTIDE and a[1] == P6]
    p6_min = None
    if p6 and len(bxyz):
        p6_min = min(float(np.linalg.norm(bxyz - np.array(p), axis=1).min())
                     for p in p6)

    basics = [(a[2], a[3], a[4]) for a in atoms
              if a[0] == BINDER and a[2] in BASIC_N and a[3] in BASIC_N[a[2]]]
    has_c3, n_others, min_shell = False, None, None
    if basics and shell:
        sh = np.array(shell)
        d = {i: float(np.linalg.norm(
            np.array([b[2].x, b[2].y, b[2].z]) - sh, axis=1).min())
            for i, b in enumerate(basics)}
        in_shell = [i for i, v in d.items() if SHELL_LO <= v <= SHELL_HI]
        if in_shell:
            has_c3 = True
            idx = min(in_shell, key=lambda i: d[i])
            n_others = sum(1 for i, v in d.items()
                           if i != idx and v <= OTHER_WINDOW)
            min_shell = d[idx]
        else:
            min_shell = min(d.values())

    arcs = ridge >= args.min_ridge_atoms and hl >= args.min_hla_atoms
    return {
        "design": f"{path.parent.parent.name}/{path.parent.name}/{path.stem}",
        "binder_len": len({a[1] for a in atoms if a[0] == BINDER}),
        "peptide_contacts": pep, "ridge_contacts": ridge,
        "hla_contacts": hl, "b2m_contacts": b2,
        "peptide_share": round(share, 3),
        "p6_min_dist": round(p6_min, 2) if p6_min is not None else "",
        "c3": has_c3,
        "c3_min_dist": round(min_shell, 2) if min_shell is not None else "",
        "c3_other_positives": n_others if has_c3 else "",
        "arcs": arcs,
        "peptide_first": share >= args.min_share,
        "pass": arcs and share >= args.min_share and has_c3,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--cutoff", type=float, default=4.5)
    ap.add_argument("--min-ridge-atoms", type=int, default=10)
    ap.add_argument("--min-hla-atoms", type=int, default=30)
    ap.add_argument("--min-share", type=float, default=0.20)
    args = ap.parse_args()

    rows = []
    for cif in sorted(args.dir.rglob("design_*.cif")):
        row = screen(cif, args)
        if row:
            rows.append(row)
    if not rows:
        print("no designs under", args.dir)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    npass = sum(1 for r in rows if r["pass"])
    nc3 = sum(1 for r in rows if r["c3"])
    narcs = sum(1 for r in rows if r["arcs"])
    nfirst = sum(1 for r in rows if r["peptide_first"])
    print(f"{len(rows)} designs: arcs {narcs}, peptide-first {nfirst}, "
          f"C3 shell {nc3}, PASS (all three) {npass}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
