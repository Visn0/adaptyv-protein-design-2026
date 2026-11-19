#!/usr/bin/env python3
"""Verdict on the clean two-state panel.

Every design in the panel was folded twice from ONE sequence source: against
the mutant peptide (__g12d) and against the wild-type peptide (__wt). Because
both arms come from the same sequence in the same batch, the difference between
them is the discrimination signal, with no cross-batch or cross-generation
confound.

A design is submittable when the mutant arm passes the organizer gate
(peptide_read >= 0.61) while the wild-type arm fails it.

Usage: PYTHONPATH= .venv/bin/python wt-panel-verdict.py [--work DIR]
"""

from __future__ import annotations

import argparse
import csv
import pathlib

GATE = 0.61
# Reference points already in the submission, measured the same way.
CHAMPION_WT = 0.007
CHAMPION_SEP = 0.759


def num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=pathlib.Path,
                    default=pathlib.Path.home() / "c5-work" / "wt-panel")
    args = ap.parse_args()

    summary = args.work / "s1-summary.csv"
    if not summary.exists():
        print(f"no summary yet: {summary}")
        return 1
    table = {r["design"]: r for r in csv.DictReader(summary.open())}

    def read(name: str):
        r = table.get(name)
        return (num(r.get("peptide_read")), num(r.get("iptm_pep"))) if r else None

    bases = sorted({n[:-6] for n in table if n.endswith("__g12d")})
    if not bases:
        print("no __g12d arms found in the summary")
        return 1

    print(f"{'design':50s} {'g12d':>6s} {'WT':>6s} {'sep':>6s}  verdict")
    rows = []
    for base in bases:
        g, w = read(f"{base}__g12d"), read(f"{base}__wt")
        if not (g and w):
            print(f"{base[:50]:50s}  (incomplete: {bool(g)} {bool(w)})")
            continue
        sep = g[0] - w[0]
        if g[0] >= GATE and w[0] < GATE:
            verdict = "SUBMITTABLE"
        elif g[0] >= GATE:
            verdict = "not specific"
        else:
            verdict = "below gate"
        rows.append((base, g[0], w[0], sep, verdict))
        print(f"{base[:50]:50s} {g[0]:6.3f} {w[0]:6.3f} {sep:6.3f}  {verdict}")

    print()
    submittable = [r for r in rows if r[4] == "SUBMITTABLE"]
    print(f"submittable (gate passed, WT below gate): {len(submittable)}")
    for base, g, w, sep, _ in sorted(submittable, key=lambda r: -r[3]):
        print(f"  {base[:52]:52s} g12d {g:.3f}  WT {w:.3f}  sep {sep:.3f}")
    print()
    print(f"champion reference, same instrument: WT {CHAMPION_WT:.3f}, "
          f"separation {CHAMPION_SEP:.3f} (c7-I13K family)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
