#!/usr/bin/env python3
"""Pick the E1 designs worth folding: two-domain first, then groove-contact
count, then the cleanest. Writes their Boltz-2 fold YAMLs into ~/c3-work/folds.

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/pick_e1_folds.py [--top N]
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import subprocess

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
WORK = pathlib.Path.home() / "c3-work"
GEN = WORK / "generation/e1"
FOLDS = WORK / "folds"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=36)
    ap.add_argument("--csv", default=str(WORK / "e1-triage.csv"))
    ap.add_argument("--prefix", default="e1")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.csv)))
    gen = WORK / f"generation/{args.prefix}"
    good = [r for r in rows
            if int(r["clash_pairs"]) <= 2 and float(r["non_loop"]) >= 0.7
            and int(r["groove_atoms4"]) >= 10]
    good.sort(key=lambda r: (-int(r["two_domain"] == "True"),
                             -int(r["groove_atoms4"]), -int(r["tm_atoms4"])))
    FOLDS.mkdir(exist_ok=True)
    chosen = 0
    for row in good:
        if chosen >= args.top:
            break
        design = next(gen.glob(f"{row['design']}/*_model_0.cif.gz"), None)
        if design is None:
            print(f"missing {row['design']}")
            continue
        out = FOLDS / f"{args.prefix}-{row['design']}.yaml"
        result = subprocess.run(
            [str(REPO / ".venv/bin/python"),
             str(REPO / "challenges/03-glp1r/campaigns/c1-two-domain/scripts/make_fold_yaml_c3.py"),
             "--design", str(design), "--out", str(out)],
            capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr.strip())
            continue
        chosen += 1
        print(f"  e1-{row['index']:<4} 2D={row['two_domain']:<5} groove={row['groove_atoms4']:>4} "
              f"tm={row['tm_atoms4']:>3} -> {out.name}")
    print(f"\n{chosen} fold YAMLs written to {FOLDS}")


if __name__ == "__main__":
    main()
