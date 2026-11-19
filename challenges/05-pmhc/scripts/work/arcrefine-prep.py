#!/usr/bin/env python3
"""Prep ArcRefine configs for the top v3 designs (fold -> template PDB + JSON).

Usage: .venv/bin/python arcrefine-prep.py (from the repo root)
"""

from __future__ import annotations

import glob
import json
import pathlib

import gemmi

W = pathlib.Path.home() / "c5-work"
OUT = W / "arcrefine"
SETS = ("s1", "s1w3", "camp", "c2p", "c6", "s1w4")
DESIGNS = [
    "nim-wave3__run-001__design_0004__g12d__c7",
    "wave2-pep__run-024__design_0007__g12d__c5",
    "peprim-wave1__run-001__design_0002__g12d",
    "wave2-pep__run-016__design_0005__g12d",
    "nim-wave3__run-021__design_0001__g12d",
    "mini-wave1__run-014__design_0005__g12d",
    "nat-wave1__run-004__design_0001__g12d",
    "peprim-wave1__run-013__design_0007__g12d__c1",
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    for design in DESIGNS:
        cfg_path = OUT / f"{design}.json"
        if cfg_path.exists():
            print(f"skip {design} (config exists)")
            continue
        hits = []
        for s in SETS:
            hits = glob.glob(str(W / s / "folds" / design / "boltz_results_*"
                                 / "predictions" / design / f"{design}_model_0.cif"))
            if hits:
                break
        if not hits:
            print(f"no fold for {design}")
            continue
        st = gemmi.read_structure(hits[0])
        pdb = OUT / f"{design}-template.pdb"
        st.write_pdb(str(pdb))
        ch = {c.name: gemmi.one_letter_code([r.name for r in c]) for c in st[0]}
        cfg = {
            "name": design,
            "parent_sequence": ch["D"],
            "targets": [
                {"id": cid, "sequence": ch[cid], "template_pdb": str(pdb),
                 "template_chain": cid, "use_msa": False}
                for cid in ("A", "B", "C")
            ],
            "carryover": True,
            "phase_steps": [50, 50, 15],
        }
        cfg_path.write_text(json.dumps(cfg, indent=2))
        made += 1
        print(f"prepped {design} (binder {len(ch['D'])} aa)")
    print(f"configs ready: {made} new, total "
          f"{len(list(OUT.glob('*.json')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
