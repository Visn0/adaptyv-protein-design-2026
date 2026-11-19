#!/usr/bin/env python3
"""C3 — the electrostatic placement filter (the differentiator layer).

Rule (pre-registered in notes/strategies.md): a design passes when a binder
side-chain nitrogen of Arg, Lys or His sits in the 6-8 A shell over P6-P7 of
the peptide, and it is preferred (not required) that no other binder formal
positive is in that shell.

Mechanism: the G12D-minus-WT difference field is negative, epicentre 6-8 A
above P6-P7 (Asp6 is buried and salt-bridged to HLA R114; no binder touches
it). A cation placed in that shell reads the mutation the way the JDI TCR
does. Distances are measured from the binder basic nitrogen to the nearest
P6/P7 peptide atom (CA, CB, CG where present).

Also reported, not gated: whether any HLA heavy-chain basic nitrogen is in
the same shell (context for the "only positive nearby" preference).

Inputs: fold outputs (cif or pdb) with explicit chain roles. Batch mode
globs a directory recursively.

Usage:
  .venv/bin/python c3-electrostatic-filter.py FOLD.cif --binder D --peptide C
  .venv/bin/python c3-electrostatic-filter.py --dir FOLDS/ --out filter.csv
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import sys

import gemmi

BASIC_N = {"ARG": ("NE", "NH1", "NH2"), "LYS": ("NZ",),
           "HIS": ("ND1", "NE2")}
SHELL_LO, SHELL_HI = 6.0, 8.0
OTHER_WINDOW = 8.0     # other positives counted within this of the shell atoms
P6, P7 = 6, 7          # 10-mer register


def _res_atoms(res) -> dict[str, gemmi.Atom]:
    return {a.name: a for a in res}


def shell_atoms(peptide_chain) -> list[gemmi.Atom]:
    atoms = []
    for res in peptide_chain:
        if res.seqid.num not in (P6, P7):
            continue
        names = _res_atoms(res)
        for name in ("CA", "CB", "CG"):
            if name in names:
                atoms.append(names[name])
    return atoms


def _min_dist(atom: gemmi.Atom, others: list[gemmi.Atom]) -> float:
    return min(atom.pos.dist(o.pos) for o in others)


def analyze(path: pathlib.Path, binder_id: str, peptide_id: str,
            hla_id: str | None) -> dict | None:
    st = gemmi.read_structure(str(path))
    if not len(st):
        return None
    model = st[0]
    binder = model.find_chain(binder_id)
    peptide = model.find_chain(peptide_id)
    if binder is None or peptide is None:
        return None
    shell = shell_atoms(peptide)
    if not shell:
        return None

    basics: list[tuple[str, str, gemmi.Atom]] = []   # (resname, atomname, atom)
    for res in binder:
        if res.name in BASIC_N:
            for name in BASIC_N[res.name]:
                if name in _res_atoms(res):
                    basics.append((res.name, name, _res_atoms(res)[name]))
    if not basics:
        return {"design": path.stem, "has_field_cation": False,
                "n_other_positives": None, "min_shell_dist": None,
                "n_basic_total": 0, "hla_positive_in_shell": None}

    dists = {i: _min_dist(a, shell) for i, (_, _, a) in enumerate(basics)}
    in_shell = [i for i, d in dists.items() if SHELL_LO <= d <= SHELL_HI]
    others = 0
    if in_shell:
        idx = min(in_shell, key=lambda i: dists[i])
        others = sum(1 for i, (_, _, a) in enumerate(basics)
                     if i != idx and _min_dist(a, shell) <= OTHER_WINDOW)
        best = dists[idx]
    else:
        best = min(dists.values())

    hla_positive = None
    if hla_id:
        hla = model.find_chain(hla_id)
        if hla is not None:
            hla_positive = any(
                SHELL_LO <= a.pos.dist(s.pos) <= SHELL_HI
                for res in hla if res.name in BASIC_N
                for name in BASIC_N[res.name] if name in _res_atoms(res)
                for a in [_res_atoms(res)[name]] for s in shell)
    return {
        "design": path.stem,
        "has_field_cation": bool(in_shell),
        "n_other_positives": others if in_shell else None,
        "min_shell_dist": round(best, 2),
        "n_basic_total": len(basics),
        "hla_positive_in_shell": hla_positive,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", type=pathlib.Path)
    ap.add_argument("--dir", type=pathlib.Path)
    ap.add_argument("--binder", default="D")
    ap.add_argument("--peptide", default="C")
    ap.add_argument("--hla", default="A")
    ap.add_argument("--out", type=pathlib.Path)
    args = ap.parse_args()

    paths = list(args.paths)
    if args.dir:
        paths += sorted(p for ext in ("cif", "pdb")
                        for p in args.dir.rglob(f"*.{ext}"))
    if not paths:
        ap.error("no inputs")

    rows = [r for p in paths
            if (r := analyze(p, args.binder, args.peptide, args.hla)) is not None]
    fields = ["design", "has_field_cation", "n_other_positives",
              "min_shell_dist", "n_basic_total", "hla_positive_in_shell"]
    out = args.out or (pathlib.Path.cwd() / "c3-filter.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    n_pass = sum(1 for r in rows if r["has_field_cation"])
    print(f"{len(rows)} folds scanned; {n_pass} pass the shell rule "
          f"({SHELL_LO}-{SHELL_HI} A over P{P6}-P{P7})")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
