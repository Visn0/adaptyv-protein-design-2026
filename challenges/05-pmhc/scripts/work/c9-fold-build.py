#!/usr/bin/env python3
"""C9 fold-yaml builder: top-screened backbones' MPNN sequences -> boltz yamls.

Takes the N best backbones by peptide_share from the CA screen, picks the
best-scoring MPNN sequence of each (lowest score), and writes the fold yamls
(target chains + MSAs from a standard c5 yaml, binder = the MPNN sequence).

Usage: PYTHONPATH= .venv/bin/python c9-fold-build.py [--top 30]
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import re

HOME = pathlib.Path.home()
C9 = HOME / "c5-work" / "c9"
FOLDS = C9 / "folds"
TEMPLATE = HOME / "c5-work" / "s1" / "folds" / "wave2-pep__run-008__design_0003__g12d.yaml"
HEAD = "version: 1\n"


def best_seq(fa: pathlib.Path) -> str | None:
    """Lowest-score designed sequence's binder segment.

    ProteinMPNN fastas wrap sequence lines and do not use colon separators:
    the full sequence is A (276) + B (99) + C (10) + binder.
    """
    lines = fa.read_text().splitlines()
    best, best_score = None, 1e9
    cur_score: str | None = None
    cur_parts: list[str] = []
    records: list[tuple[float, str]] = []
    for line in lines:
        if line.startswith(">"):
            if cur_score is not None and cur_parts:
                records.append((float(cur_score), "".join(cur_parts)))
            cur_score = None
            cur_parts = []
            if "T=" in line:
                m = re.search(r"score=([0-9.]+)", line)
                cur_score = m.group(1) if m else None
        elif line.strip() and cur_score is not None:
            cur_parts.append(line.strip())
    if cur_score is not None and cur_parts:
        records.append((float(cur_score), "".join(cur_parts)))
    for score, seq in records:
        if score < best_score and 40 < len(seq) < 130:
            best_score, best = score, seq
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()
    FOLDS.mkdir(parents=True, exist_ok=True)
    screen = list(csv.DictReader((C9 / "screen.csv").open()))
    head = TEMPLATE.read_text().split("  - protein:\n      id: D")[0]
    head = head.removeprefix("version: 1\n")
    made = 0
    for row in screen[: args.top]:
        name = row["design"]  # g3_N
        fa = C9 / "mpnn" / name / "seqs" / f"{name}.fa"
        if not fa.exists():
            print(f"no mpnn fasta for {name}")
            continue
        seq = best_seq(fa)
        if not seq:
            print(f"no sequence parsed for {name}")
            continue
        out = FOLDS / f"c9-{name}.yaml"
        out.write_text(HEAD + head + "  - protein:\n      id: D\n      sequence: "
                       + seq + "\n      msa: empty\n")
        made += 1
    print(f"built {made} c9 fold yamls (top {args.top} by peptide_share)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
