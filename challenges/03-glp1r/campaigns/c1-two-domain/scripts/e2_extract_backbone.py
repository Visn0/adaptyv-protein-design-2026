#!/usr/bin/env python3
"""E2: extract a design's binder backbone (chain A) as a PDB for ProteinMPNN.

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/e2_extract_backbone.py <design.cif.gz> <out.pdb>
"""
from __future__ import annotations

import gzip
import pathlib
import sys

from Bio.PDB import MMCIFParser, PDBIO, Select


class OnlyA(Select):
    def accept_chain(self, c):
        return c.id == "A"


def main() -> None:
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    tmp = pathlib.Path.home() / "c3-work/_e2_extract.cif"
    if src.suffix == ".gz":
        with gzip.open(src, "rt") as fh:
            tmp.write_text(fh.read())
    else:
        tmp.write_text(src.read_text())
    st = MMCIFParser(QUIET=True).get_structure("m", str(tmp))[0]
    io = PDBIO()
    io.set_structure(st)
    io.save(str(out), OnlyA())
    n = sum(1 for r in st["A"] if r.id[0] == " ")
    print(f"{out.name}: chain A {n} residues")


if __name__ == "__main__":
    main()
