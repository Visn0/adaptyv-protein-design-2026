#!/usr/bin/env python3
"""Apply the pre-registered campaign-1 advance rule to folds-screen.csv.

Rule (campaigns/c1-epitope-triage/README.md): an epitope set advances when at
least two of its backbones have a majority of their five samples at the
designed site, with a best at-site ipSAE of 0.60 or higher.

Writes state/advancing-sets.txt (one set key per line; empty = stop).
Run after the fold screen.
"""
from __future__ import annotations

import csv
from collections import defaultdict
import pathlib

HOME = pathlib.Path.home()
CSV = HOME / "c4-work/logs/folds-screen.csv"
OUT = HOME / "c4-work/state/advancing-sets.txt"
SET_KEYS = ("11qc_e0", "11qc_e1", "11qc_e2", "11qc_e12")


def set_of(design: str):
    for key in SET_KEYS:
        if (design == key or design.startswith(key + "_")
                or design.startswith(key + "b2_")):
            return key
    return None


def main() -> int:
    per_design = defaultdict(list)
    for row in csv.DictReader(CSV.open()):
        key = set_of(row["design"])
        if key is None:
            continue
        per_design[row["design"]].append(row)
    advancing, report = [], []
    for key in SET_KEYS:
        designs = [d for d in per_design if set_of(d) == key]
        backbones = 0
        for design in sorted(designs):
            rows = per_design[design]
            at_site = [r for r in rows if r["at_site"] == "True"]
            majority = len(at_site) >= 3
            best = max((float(r["ipsae"]) for r in at_site), default=0.0)
            ok = majority and best >= 0.6
            backbones += ok
            report.append(f"  {design}: samples {len(rows)}, at_site {len(at_site)}, "
                          f"best at-site ipSAE {best:.3f} -> {'QUALIFY' if ok else 'no'}")
        verdict = "ADVANCES" if backbones >= 2 else "no"
        report.append(f"{key}: {backbones} qualifying backbones -> {verdict}")
        if backbones >= 2:
            advancing.append(key)
    print("\n".join(report))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(f"{k}\n" for k in advancing))
    print(f"advancing sets: {advancing or 'NONE (campaign 1 negative)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
