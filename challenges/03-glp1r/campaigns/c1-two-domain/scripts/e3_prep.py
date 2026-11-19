#!/usr/bin/env python3
"""E3 prep: for each top design, compute the binder's interface positions (from
the co-folded pose), extract the design's chain A as a PDB, and write the
ProteinMPNN fixed-positions JSONL (the interface stays, the periphery is free).

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/e3_prep.py e1b-r0023 e1b-r0059 e1-r0033
"""
from __future__ import annotations

import gzip
import json
import pathlib
import sys

import numpy as np
from Bio.PDB import MMCIFParser, PDBIO, Select

WORK = pathlib.Path.home() / "c3-work"
E2 = WORK / "e2"
CUTOFF = 4.5


class OnlyA(Select):
    def accept_chain(self, c):
        return c.id == "A"


def interface_positions(fold_cif: pathlib.Path) -> list[int]:
    st = MMCIFParser(QUIET=True).get_structure("m", str(fold_cif))[0]
    binder = {r.id[1]: np.array([a.coord for a in r.get_atoms()])
              for r in st["A"] if r.id[0] == " "}
    target = np.vstack([np.array([a.coord for a in r.get_atoms()])
                        for r in st["B"] if r.id[0] == " "])
    out = []
    for num, xyz in sorted(binder.items()):
        d = float(np.linalg.norm(xyz[:, None, :] - target[None, :, :], axis=2).min())
        if d <= CUTOFF:
            out.append(num)
    return out


def main() -> None:
    for design in sys.argv[1:]:
        set_name, round_ = design.split("-")
        src = next((WORK / f"generation/{set_name}/{round_}").glob("*_model_0.cif.gz"), None)
        fold = next((WORK / f"folds/{design}").glob("boltz_results_*/predictions/*/*_model_0.cif"), None)
        if src is None or fold is None:
            print(f"{design}: missing source or fold")
            continue
        tmp = WORK / "_e3_extract.cif"
        with gzip.open(src, "rt") as fh:
            tmp.write_text(fh.read())
        st = MMCIFParser(QUIET=True).get_structure("m", str(tmp))[0]
        io = PDBIO()
        io.set_structure(st)
        io.save(str(E2 / f"{design}.pdb"), OnlyA())
        iface = interface_positions(fold)
        (E2 / f"{design}-fixed.jsonl").write_text(
            json.dumps({design: {"A": iface}}) + "\n")
        print(f"{design}: pdb + {len(iface)} fixed interface positions")


if __name__ == "__main__":
    main()
