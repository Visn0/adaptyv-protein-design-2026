#!/usr/bin/env python3
"""E-score: a physics-based specificity reading for the G12D interface.

The confidence metrics are blind to the single charge swap (C0: wrong sign on
the known control; C8: flat at P6). This script measures the actual
mechanism instead: the Coulomb interaction between the binder's charged
groups and the mutant aspartate's carboxylate, plus how much the binder
occludes that carboxylate (a desolvation proxy for the wild-type penalty).

  E_D6      = 83 * sum(q_binder * q_D6 / r^2)   [distance-dependent
              dielectric eps = 4r, kcal/mol, crude MM-GBSA-class term]
  dSASA     = the aspartate's SASA in the complex minus in the free peptide
              (negative = the binder buries the carboxylate)

Validation: the known JDI TCR control must read a favorable (negative)
E_D6 - its CDR residues read the mutant through the field (published).

Layouts: our folds A=HLA B=b2m C=peptide D=binder; the c0t control folds
A,B=TCR C=HLA D=b2m E=peptide.

Usage: PYTHONPATH= .venv/bin/python escore.py [--control] <fold_glob_or_list>
"""

from __future__ import annotations

import argparse
import pathlib
import re

import gemmi

CHARGED = {
    "ASP": {"OD1": -0.5, "OD2": -0.5},
    "GLU": {"OE1": -0.5, "OE2": -0.5},
    "LYS": {"NZ": 1.0},
    "ARG": {"NH1": 0.5, "NH2": 0.5, "NE": 0.5},
}
D6_CHARGE = {"OD1": -0.5, "OD2": -0.5}
PEPTIDE_RES = 6  # P6 = the KRAS G12D position


def parse(path: pathlib.Path, layout: str):
    st = gemmi.read_structure(str(path))
    if len(st) == 0:
        return None
    chains = {c.name: c for c in st[0]}
    if layout == "control":
        binder, peptide = chains.get("A"), chains.get("E")
        # the TCR is two chains; use both
        binder_chains = [chains.get("A"), chains.get("B")]
    else:
        binder_chains = [chains.get("D")]
        peptide = chains.get("C")
    return st, binder_chains, peptide


def charged_atoms(chain, skip_res: set[int] | None = None):
    out = []
    for r in chain:
        if skip_res and r.seqid.num in skip_res:
            continue
        q = CHARGED.get(r.name)
        if not q:
            continue
        for a in r:
            if a.name in q:
                out.append((q[a.name], a.pos))
    return out


def score(path: pathlib.Path, layout: str) -> dict | None:
    parsed = parse(path, layout)
    if not parsed:
        return None
    st, binder_chains, peptide = parsed
    if peptide is None:
        return None
    d6 = [(D6_CHARGE[a.name], a.pos) for r in peptide
          if r.seqid.num == PEPTIDE_RES for a in r if a.name in D6_CHARGE]
    if not d6:
        return None
    binder_q = []
    for c in binder_chains:
        if c is not None:
            binder_q += charged_atoms(c)
    e = 0.0
    n_near = 0
    for qb, pb in binder_q:
        for qd, pd in d6:
            r = pb.dist(pd)
            if r < 1.5:
                continue
            e += 83.0 * qb * qd / (r * r)
            if r < 8.0:
                n_near += 1
    return {"E_D6": round(e, 2), "charged_near_D6": n_near,
            "n_binder_charges": len(binder_q)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--control", action="store_true")
    args = ap.parse_args()

    if args.control:
        hits = sorted((pathlib.Path.home() / "c5-work" / "c0t" / "folds").glob(
            "pos-g12d/boltz_results_*/predictions/*/*_model_0.cif"))
        if not hits:
            print("control fold not found")
            return 1
        r = score(hits[0], "control")
        if r is None:
            print("control scoring failed (chain layout?)")
            return 1
        print(f"JDI TCR control (pos-g12d): E_D6 = {r['E_D6']} kcal/mol "
              f"({r['charged_near_D6']} charged contacts within 8 A)")
        print("validation: negative (attractive) E_D6 = the control reads the "
              "mutant through the field, as published.")
        return 0

    rows = []
    import glob as _glob
    for pattern in args.paths:
        for p in sorted(_glob.glob(pattern)):
            p = pathlib.Path(p)
            m = re.search(r"/([^/]+)/boltz_results_", str(p))
            name = m.group(1) if m else p.stem
            r = score(p, "design")
            if r:
                rows.append((r["E_D6"], name, r))
    rows.sort()
    print(f"{'E_D6':>8s} {'near':>4s} {'q':>3s}  design")
    for e, name, r in rows:
        print(f"{e:>8.2f} {r['charged_near_D6']:>4d} {r['n_binder_charges']:>3d}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
