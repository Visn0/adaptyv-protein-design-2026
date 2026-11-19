#!/usr/bin/env python3
"""Specificity verdict for the pristine batch.

The organizer criterion has three parts: bind the G12D peptide complex, do NOT
bind the WT peptide complex, do NOT bind peptide-free MHC. Each gate passer was
therefore folded in all three states, and the top designs were folded across
three seeds.

Reads come from the s1 summary, keyed by arm name:
  <design>          G12D state
  <design>__wt      WT peptide (VVVGAGGVGK)
  <design>__free    no peptide
  <design>__s<N>    G12D state, seed N

A design is SPECIFIC when the G12D arm passes the organizer gate
(peptide_read >= 0.61) while both the WT and the free arms fail it.

Usage: PYTHONPATH= .venv/bin/python pr-specificity.py [--work DIR]
"""

from __future__ import annotations

import argparse
import csv
import pathlib

GATE = 0.61


def num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=pathlib.Path,
                    default=pathlib.Path.home() / "c5-work" / "pr-batch")
    args = ap.parse_args()

    summary = args.work / "s1-summary.csv"
    if not summary.exists():
        print(f"no summary yet: {summary}")
        return 1
    table = {r["design"]: r for r in csv.DictReader(summary.open())}

    def read(name: str) -> tuple[float, float] | None:
        r = table.get(name)
        if not r:
            return None
        return num(r.get("peptide_read")), num(r.get("iptm_pep"))

    base = sorted(n for n in table
                  if "__" not in n and num(table[n].get("peptide_read")) >= GATE)
    print(f"gate passers in the G12D state: {len(base)}")
    print()
    print(f"{'design':8s} {'G12D':>6s} {'WT':>6s} {'free':>6s} "
          f"{'d(WT)':>6s} {'d(free)':>7s}  verdict")
    specific = []
    for d in base:
        g = read(d)
        w = read(f"{d}__wt")
        f = read(f"{d}__free")
        if not (g and w and f):
            got = "G12D" if g else "no G12D"
            print(f"{d:8s}  (missing states: {got})")
            continue
        dw, df = g[0] - w[0], g[0] - f[0]
        ok = w[0] < GATE and f[0] < GATE
        if ok:
            specific.append(d)
        print(f"{d:8s} {g[0]:6.3f} {w[0]:6.3f} {f[0]:6.3f} "
              f"{dw:6.3f} {df:7.3f}  {'SPECIFIC' if ok else 'not specific'}")
    print()
    print(f"designs that are G12D-specific: {len(specific)} {specific}")
    print()
    print("multi-seed G12D reads (the champion was validated the same way):")
    print(f"{'design':8s} {'s0':>6s} {'s1':>6s} {'s2':>6s}   {'mean':>6s}  {'best':>6s}")
    for d in ("pr-089", "pr-001", "pr-021"):
        seeds = [read(f"{d}__s{i}") for i in range(3)]
        vals = [s[0] for s in seeds if s]
        if len(vals) < 3:
            print(f"{d:8s} (only {len(vals)} seed arms)")
            continue
        print(f"{d:8s} {vals[0]:6.3f} {vals[1]:6.3f} {vals[2]:6.3f}   "
              f"{sum(vals) / 3:6.3f}  {max(vals):6.3f}")
    print()
    print("champion reference: c7-I13K seeds 0.754 / 0.746 / 0.737, mean 0.746")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
