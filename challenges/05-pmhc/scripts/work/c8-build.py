#!/usr/bin/env python3
"""C8: multi-state cross-panning yamls for the finalists.

States (chain C swapped in the design's G12D yaml):
  nine  - VVGADGVGK  (9-mer flattened register decoy)
  g12v  - VVVGAVGVK  (most common KRAS mutation)
  g12c  - VVVGACGVGK  (sotorasib target)

Designs: top of records/stage3/final-ranking.csv (clean-20) + the two best
children. Output: ~/c5-work/c8/folds/<design>__<state>.yaml
Usage: PYTHONPATH= .venv/bin/python c8-build.py
"""

from __future__ import annotations

import csv
import pathlib
import re

HOME = pathlib.Path.home()
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
C8 = HOME / "c5-work" / "c8" / "folds"
SEARCH_ROOTS = ["s1/folds", "s1w3/folds", "camp/folds", "c2p/folds", "c6/folds"]
STATES = {
    "nine": "VVGADGVGK",
    "g12v": "VVVGAVGVGK",
    "g12c": "VVVGACGVGK",
}


def design_yaml(design: str) -> pathlib.Path | None:
    for root in SEARCH_ROOTS:
        y = HOME / "c5-work" / root / f"{design}.yaml"
        if y.exists():
            return y
    return None


def main() -> int:
    C8.mkdir(parents=True, exist_ok=True)
    rank = list(csv.DictReader(
        (REPO / "challenges/05-pmhc/records/stage3/final-ranking.csv").open()))
    names = [r["design"] for r in rank[:12]]
    names += [l.strip() for l in
              (HOME / "c5-work" / "s0" / "c6-best-children.txt").read_text().split()
              if l.strip()][:2]
    made = 0
    for name in names:
        y = design_yaml(name)
        if y is None:
            print(f"missing yaml for {name}")
            continue
        text = y.read_text()
        for state, pep in STATES.items():
            out = re.sub(r"sequence: VVVGADGVGK", f"sequence: {pep}", text, count=1)
            (C8 / f"{name}__{state}.yaml").write_text(out)
            made += 1
    print(f"built {made} c8 yamls for {len(names)} designs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
