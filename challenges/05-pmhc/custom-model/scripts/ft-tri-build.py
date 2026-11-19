#!/usr/bin/env python3
"""Tri-state yamls for the fine-tuned-model funnel: WT peptide + peptide-free.

The organizer criterion is specificity, so a design only counts if its
interface survives the G12D peptide and collapses without it. From each base
yaml (A=HLA, B=b2m, C=peptide G12D, D=binder) this writes:

  <design>__wt.yaml    same chains, peptide swapped to the WT sequence
  <design>__free.yaml  A + B + D, no peptide at all

Usage: PYTHONPATH= .venv/bin/python ft-tri-build.py <design> [<design> ...]
       PYTHONPATH= .venv/bin/python ft-tri-build.py --all
"""

from __future__ import annotations

import os
import pathlib
import sys

import yaml

WORK = pathlib.Path(os.environ.get("FT_WORK", pathlib.Path.home() / "c5-work/ft-batch"))
FOLDS = WORK / "folds"
WT_PEPTIDE = "VVVGAGGVGK"


def load_chains(path: pathlib.Path) -> dict[str, dict]:
    """chain id -> its protein block (parsed, not regex-matched)."""
    doc = yaml.safe_load(path.read_text())
    out = {}
    for entry in doc.get("sequences", []):
        prot = entry.get("protein")
        if prot and prot.get("id"):
            out[prot["id"]] = prot
    return out


def dump(path: pathlib.Path, chains: list[dict]) -> None:
    doc = {"version": 1, "sequences": [{"protein": c} for c in chains]}
    path.write_text(yaml.safe_dump(doc, sort_keys=False))


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    if args == ["--all"]:
        args = sorted(p.stem for p in FOLDS.glob("*.yaml")
                      if "__" not in p.stem)
    made = 0
    for design in args:
        base = FOLDS / f"{design}.yaml"
        if not base.exists():
            print(f"missing {base}")
            continue
        ch = load_chains(base)
        missing = [c for c in "ABCD" if c not in ch]
        if missing:
            print(f"{design}: chains missing {missing}, skipped")
            continue
        wt = dict(ch["C"])
        wt["sequence"] = WT_PEPTIDE
        dump(FOLDS / f"{design}__wt.yaml", [ch["A"], ch["B"], wt, ch["D"]])
        dump(FOLDS / f"{design}__free.yaml", [ch["A"], ch["B"], ch["D"]])
        made += 2
    print(f"built {made} yamls for {len(args)} designs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
