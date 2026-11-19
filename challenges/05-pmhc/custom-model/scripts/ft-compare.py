#!/usr/bin/env python3
"""Rank the fine-tuned funnel against the campaign champions.

Joins the s1 summary (organizer gate reads) with the v2 E-scores, then reports
the designs that matter: gate passers (peptide_read >= 0.61) and anything that
beats the champion bar.

Champion bar (three-seed validated, from the v5 submission set):
  c7-I13K  peptide_read 0.754 (best seed)  E -2.63
  Q48K     0.698                            E -2.90
  Q54K     0.690                            E -2.84
  L23K     0.686                            E -3.20

Usage: PYTHONPATH= .venv/bin/python ft-compare.py [--work DIR]
"""

from __future__ import annotations

import argparse
import csv
import pathlib

GATE = 0.61
CHAMP_READ = 0.754
CHAMP_E = -2.63


def num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def load_escores(path: pathlib.Path) -> dict[str, float]:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            try:
                out[parts[0]] = float(parts[1])
            except ValueError:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=pathlib.Path,
                    default=pathlib.Path.home() / "c5-work" / "ft-batch")
    args = ap.parse_args()

    summary = args.work / "s1-summary.csv"
    if not summary.exists():
        print(f"no summary yet: {summary}")
        return 1
    rows = list(csv.DictReader(summary.open()))
    es = load_escores(args.work / "escores-v2.tsv")

    scored: list[dict] = [
        {
            "design": r["design"],
            "read": num(r.get("peptide_read")),
            "iptm": num(r.get("iptm_pep")),
            "E": es.get(r["design"], float("nan")),
        }
        for r in rows
    ]

    scored.sort(key=lambda r: -r["read"])
    passers = [r for r in scored if r["read"] >= GATE]
    beat = [r for r in scored if r["read"] > CHAMP_READ]

    print(f"designs scored: {len(scored)}")
    print(f"gate passers (peptide_read >= {GATE}): {len(passers)}")
    print(f"beat the champion bar ({CHAMP_READ}): {len(beat)}")
    if es:
        strong = [r for r in passers if r["E"] == r["E"] and r["E"] <= CHAMP_E]
        print(f"gate passers that also beat the E champion ({CHAMP_E}): {len(strong)}")
    print()
    print(f"{'design':12s} {'pep_read':>9s} {'iptm_pep':>9s} {'E_D6':>7s}  flag")
    for r in scored[:25]:
        flag = ""
        if r["read"] >= GATE:
            flag = "GATE"
        if r["read"] > CHAMP_READ:
            flag = "NEW-CHAMPION"
        e = r["E"]
        e_s = f"{e:7.2f}" if e == e else "   n/a "
        print(f"{r['design']:12s} {r['read']:9.3f} {r['iptm']:9.3f} {e_s}  {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
