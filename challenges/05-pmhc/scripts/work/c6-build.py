#!/usr/bin/env python3
"""C6 step 2: turn LigandMPNN children into boltz fold yamls.

For each parent: read the MPNN fasta (chain sequences colon-separated; the
4th field is the redesigned binder), take the target chains (A/B/C) and MSA
paths from the parent's own fold yaml, and write one yaml per child under
c6/folds/ as <parent>__c<N>.yaml.

Usage: PYTHONPATH= .venv/bin/python c6-build.py
"""

from __future__ import annotations

import pathlib
import re
import sys

HOME = pathlib.Path.home()
C6 = HOME / "c5-work" / "c6"
FOLDS = C6 / "folds"
SEARCH_ROOTS = ["s1/folds", "s1w3/folds", "camp/folds", "c2p/folds"]


def parent_yaml(design: str) -> pathlib.Path | None:
    for root in SEARCH_ROOTS:
        y = HOME / "c5-work" / root / f"{design}.yaml"
        if y.exists():
            return y
    return None


def main() -> int:
    FOLDS.mkdir(parents=True, exist_ok=True)
    made = 0
    for parent_dir in sorted((C6 / "mpnn").glob("*")):
        name = parent_dir.name
        fa = parent_dir / "seqs" / f"{name}.fa"
        src = parent_yaml(name)
        if not fa.exists() or src is None:
            print(f"skip {name} (fasta={fa.exists()}, yaml={src is not None})",
                  file=sys.stderr)
            continue
        src_text = src.read_text()
        # keep the target part of the parent yaml up to the binder block
        head = src_text.split("  - protein:\n      id: D")[0]
        for line in fa.read_text().splitlines():
            if not line.startswith(">"):
                continue
            m = re.search(r"id=(\d+)", line)
            if not m:
                continue
            child = int(m.group(1))
            seq_line = fa.read_text().splitlines()[
                fa.read_text().splitlines().index(line) + 1]
            chains = seq_line.split(":")
            if len(chains) != 4:
                continue
            binder = chains[3]
            out = FOLDS / f"{name}__c{child}.yaml"
            out.write_text(
                head
                + "  - protein:\n      id: D\n      sequence: "
                + binder
                + "\n      msa: empty\n")
            made += 1
    print(f"built {made} child yamls under {FOLDS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
