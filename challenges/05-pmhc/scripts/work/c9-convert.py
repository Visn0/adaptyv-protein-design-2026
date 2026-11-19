#!/usr/bin/env python3
"""C9 convert: genie3 output layout -> our standard layout.

genie3 writes: A = binder (poly-X backbone), B = HLA, C = b2m, D = peptide.
Our pipeline uses: A = HLA, B = b2m, C = peptide, D = binder.
Renames chains (one pass, captured map) into ~/c5-work/c9/backbones/.

Usage: .venv/bin/python c9-convert.py (from the repo root)
"""

from __future__ import annotations

import pathlib

import gemmi

HOME = pathlib.Path.home()
SRC = HOME / "c5-work" / "c9" / "genie3" / "pmhc_g12d" / "pdbs"
DST = HOME / "c5-work" / "c9" / "backbones"
MAP = {"A": "D", "B": "A", "C": "B", "D": "C"}


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    n = 0
    for pdb in sorted(SRC.glob("*.pdb")):
        st = gemmi.read_structure(str(pdb))
        if len(st) == 0:
            continue
        chains = {c.name: c for c in st[0]}
        if set(chains) != set(MAP):
            print(f"skip {pdb.name}: chains {sorted(chains)}")
            continue
        for name, c in chains.items():
            c.name = MAP[name]
        out = DST / f"g3_{pdb.stem.split('_')[-1]}.pdb"
        st.write_pdb(str(out))
        n += 1
    print(f"converted {n} backbones -> {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
