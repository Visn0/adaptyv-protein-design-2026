#!/usr/bin/env python3
"""C6 follow-ups: (a) WT/free yamls for the best child of each parent
(tri-state), (b) apo-fold yamls (binder chain alone) for the parents and the
best children - the cheapest available stability signal.

Writes: ~/c5-work/c6t/folds/*.yaml  (child__wt, child__free)
        ~/c5-work/apo/folds/*.yaml  (binder alone)
Usage: PYTHONPATH= .venv/bin/python c6-tri-build.py
"""

from __future__ import annotations

import pathlib
import re

HOME = pathlib.Path.home()
C6 = HOME / "c5-work" / "c6"
C6T = HOME / "c5-work" / "c6t" / "folds"
APO = HOME / "c5-work" / "apo" / "folds"
BEST = HOME / "c5-work" / "s0" / "c6-best-children.txt"
WT_PEPTIDE = "VVVGAGGVGK"


def blocks(text: str) -> dict[str, str]:
    """chain id -> full '  - protein:' block."""
    out = {}
    parts = re.split(r"(?=  - protein:)", text)
    for p in parts:
        m = re.search(r"id: (\w)", p)
        if m:
            out[m.group(1)] = p.rstrip("\n") + "\n"
    return out


def main() -> int:
    C6T.mkdir(parents=True, exist_ok=True)
    APO.mkdir(parents=True, exist_ok=True)
    best = [l.strip() for l in BEST.read_text().split() if l.strip()]
    head = "version: 1\nsequences:\n"
    made = 0
    for child in best:
        y = C6 / "folds" / f"{child}.yaml"
        if not y.exists():
            print(f"missing {y}")
            continue
        b = blocks(y.read_text())
        # WT variant: same, peptide swapped
        wt = b["A"] + b["B"] + re.sub(
            r"sequence: [A-Z]+", f"sequence: {WT_PEPTIDE}", b["C"]) + b["D"]
        (C6T / f"{child}__wt.yaml").write_text(head + wt)
        # free variant: no peptide
        free = b["A"] + b["B"] + b["D"]
        (C6T / f"{child}__free.yaml").write_text(head + free)
        # apo: binder alone
        (APO / f"{child}__apo.yaml").write_text(head + b["D"])
        made += 3
    # parents' apo folds too
    for parent_dir in sorted((C6 / "mpnn").glob("*")):
        name = parent_dir.name
        for root in ("s1", "s1w3", "camp", "c2p"):
            y = HOME / "c5-work" / root / "folds" / f"{name}.yaml"
            if y.exists():
                b = blocks(y.read_text())
                (APO / f"{name}__apo.yaml").write_text(head + b["D"])
                made += 1
                break
    print(f"built {made} yamls (c6t + apo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
