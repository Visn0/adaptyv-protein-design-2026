#!/usr/bin/env python3
"""Charge-clash check (ProtonPottsMPNN's 4 A same-sign criterion) on our folds.

For every binder-target residue pair, count same-sign charged atom pairs
within 4.0 A (Lys/Arg N vs Lys/Arg N; Asp/Glu O vs Asp/Glu O). Buried
same-sign pairs mark electrostatic stress in the interface.

Usage: PYTHONPATH= .venv/bin/python clash-check.py <fold.cif> [...]
"""

from __future__ import annotations

import pathlib
import sys

import gemmi

POS = {"NZ", "NH1", "NH2", "NE"}          # Lys/Arg positive nitrogens
NEG = {"OD1", "OD2", "OE1", "OE2"}        # Asp/Glu negative oxygens
INTERFACE = 6.0                            # atoms within 6 A of the binder


def charged_atoms(chain, binder_atoms):
    out = []
    for r in chain:
        for a in r:
            if a.name in POS or a.name in NEG:
                if min(a.pos.dist(b.pos) for b in binder_atoms) <= INTERFACE:
                    out.append((a.name, a.pos, 1 if a.name in POS else -1))
    return out


def main() -> int:
    for path in sys.argv[1:]:
        st = gemmi.read_structure(path)
        model = st[0]
        binder = model.find_chain("D")
        b_atoms = [a for r in binder for a in r]
        binder_charged = charged_atoms(binder, b_atoms)
        target_charged = []
        for cid in ("A", "B", "C"):
            ch = model.find_chain(cid)
            if ch is not None:
                target_charged += charged_atoms(ch, b_atoms)
        clashes = 0
        for _, p1, s1 in binder_charged:
            for _, p2, s2 in target_charged:
                if s1 == s2 and p1.dist(p2) <= 4.0:
                    clashes += 1
        print(f"{clashes:3d} same-sign pairs within 4 A | "
              f"charged: binder {len(binder_charged)} vs target "
              f"{len(target_charged)} | {pathlib.Path(path).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
