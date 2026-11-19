#!/usr/bin/env python3
"""C6 prep: for each parent design, extract its G12D fold to PDB and compute
the interface residues (binder atoms within 8 A of the target chains), which
LigandMPNN will hold fixed while it redesigns the rest of the binder surface.

Usage: PYTHONPATH= .venv/bin/python c6-prep.py
"""

from __future__ import annotations

import pathlib
import sys

import gemmi

HOME = pathlib.Path.home()
WORK = HOME / "c5-work"
OUT = WORK / "c6"
CUTOFF = 8.0

PARENTS = [
    # dual-signal six
    "wave1-pep__run-033__design_0003__g12d",
    "wave1-pep__run-007__design_0000__g12d",
    "wave2-pep__run-054__design_0005__g12d",
    "peprim-wave1__run-012__design_0006__g12d",
    "wave2-pep__run-009__design_0007__g12d",
    "wave2-pep__run-024__design_0007__g12d",
    # affinity + dependence leaders from the new campaigns
    "nat-wave1__run-011__design_0004__g12d",
    "mini-wave1__run-011__design_0001__g12d",
    "nim-wave3__run-001__design_0004__g12d",
    "peprim-wave1__run-013__design_0007__g12d",
]
SEARCH_ROOTS = ["s1/folds", "s1w3/folds", "camp/folds", "c2p/folds"]


def find_model(design: str) -> pathlib.Path | None:
    for root in SEARCH_ROOTS:
        d = WORK / root / design
        hits = sorted(d.glob(
            "boltz_results_*/predictions/*/*_model_0.cif"))
        if hits:
            return hits[0]
    return None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for design in PARENTS:
        cif = find_model(design)
        if cif is None:
            print(f"MISSING fold: {design}", file=sys.stderr)
            continue
        st = gemmi.read_structure(str(cif))
        model = st[0]
        # write PDB (gemmi keeps chain letters and residue numbering)
        pdb = OUT / f"{design}.pdb"
        st.setup_entities()
        st.write_pdb(str(pdb))
        # interface: binder (D) atoms within CUTOFF of any A/B/C atom
        target_atoms = [a.pos for c in ("A", "B", "C") for r in model[c]
                        for a in r if a.element.name != "H"]
        fixed = []
        for r in model["D"]:
            if any(a.pos.dist(t) < CUTOFF for a in r
                   for t in target_atoms):
                fixed.append(f"D{r.seqid.num}")
        print(f"{design}: {len(fixed)} fixed interface residues -> "
              f"{pdb.name}")
        (OUT / f"{design}.fixed.txt").write_text(" ".join(fixed) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
