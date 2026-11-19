#!/usr/bin/env python3
"""Evo gen-1 tri-state: WT and peptide-free arms for the qualifying variants."""

from __future__ import annotations

import pathlib
import re

R = pathlib.Path.home() / "c5-work" / "evo" / "gen1"
OUT = R / "tristate" / "folds"
OUT.mkdir(parents=True, exist_ok=True)
WT = "VVVGAGGVGK"
PICKS = [
    "evorepair-wave2-pep__run-016__design_0005__g12d-L58K-Q15K",
    "evorepair-wave4-pep__run-007__design_0002__g12d-A58K-F50K",
    "evopeprim-wave1__run-001__design_0002__g12d-W57K",
    "evopeprim-wave1__run-001__design_0002__g12d-T53K",
    "evopeprim-wave1__run-001__design_0002__g12d-A60K",
    "evonim-wave3__run-001__design_0004__g12d__c7-A64K",
    "evonim-wave3__run-001__design_0004__g12d__c7-V59K",
    "evowave2-pep__run-024__design_0007__g12d__c5-V15K",
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
