#!/usr/bin/env python3
"""Build the surrogate test: fold the top-50 predicted candidates from the
never-folded pool. Writes the screen csv + the fold yamls."""

from __future__ import annotations

import csv
import pathlib

HOME = pathlib.Path.home()
W = HOME / "c5-work"
ML = W / "ml"
OUT = ML / "surrogate-folds"

rows = []
for r in csv.DictReader((ML / "candidates.csv").open()):
    name = r["design"]
    if "-run-" not in name or "-design_" not in name:
        continue
    prefix, rest = name.rsplit("-run-", 1)
    run, design = rest.split("-", 1)          # "019" + "design_0001"
    rows.append({
        "design": f"{prefix}/run-{run}/{design}",
        "pass": "True",
        "pred_E": r["pred_E"], "pred_score": r["pred_score"],
    })
rows = rows[:50]
OUT.mkdir(parents=True, exist_ok=True)
with (ML / "surrogate-screen.csv").open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["design", "pass", "pred_E", "pred_score"])
    w.writeheader()
    w.writerows(rows)
print(f"surrogate test set: {len(rows)} designs")
for r in rows[:5]:
    print(" ", r["design"], "pred_E", r["pred_E"])
