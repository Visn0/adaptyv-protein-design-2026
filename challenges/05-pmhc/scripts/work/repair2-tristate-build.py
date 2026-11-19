#!/usr/bin/env python3
"""Repair round 2 tri-state: WT and peptide-free arms for the chosen variants."""

from __future__ import annotations

import pathlib
import re

R = pathlib.Path.home() / "c5-work" / "repair2"
OUT = R / "tristate" / "folds"
OUT.mkdir(parents=True, exist_ok=True)
WT = "VVVGAGGVGK"
PICKS = [
    "repair-wave4-pep__run-007__design_0002__g12d-A58K",
    "repair-nat-wave1__run-011__design_0000__g12d-Q24K",
    "repair-nat-wave1__run-011__design_0000__g12d-H27K",
    "repair-nat-wave1__run-011__design_0004__g12d-N71K",
    "repair-peprim-wave1__run-013__design_0007__g12d__c1-A22K",
]
made = 0
for name in PICKS:
    src = R / "folds" / f"{name}.yaml"
    if not src.exists():
        print("missing", name)
        continue
    text = src.read_text()
    wt = re.sub(r"sequence: VVVGADGVGK", f"sequence: {WT}", text, count=1)
    (OUT / f"{name}__wt.yaml").write_text(wt)
    blocks = re.split(r"(?=  - protein:)", text)
    free = "".join(b for b in blocks if "id: C" not in b)
    (OUT / f"{name}__free.yaml").write_text(free)
    made += 2
print("tristate yamls:", made)
