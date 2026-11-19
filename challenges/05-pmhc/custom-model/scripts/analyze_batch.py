#!/usr/bin/env python3
"""Analyze the rfd4-batch1 results: hit rates, top designs, comparison table."""
import csv
import pathlib
import re

D = pathlib.Path.home() / "c5-work/rfd4-batch1"
es = {}
for line in (D / "escores.txt").read_text().splitlines():
    m = re.match(r"\s*(-?[0-9.]+)\s+\d+\s+\d+\s+(\S+)$", line)
    if m:
        es[m.group(2)] = float(m.group(1))

rows = list(csv.DictReader((D / "s1-summary.csv").open()))


def f(r, k, d=0.0):
    try:
        v = r.get(k)
        return float(v) if v not in (None, "") else d
    except (TypeError, ValueError):
        return d


hits_org = [r for r in rows if f(r, "peptide_read") >= 0.61]
hits_jdi = [r for r in rows if f(r, "iptm_pep") >= 0.8]
hits_e = [r for r in rows if es.get(r["design"], 0) <= -1.0]
dual = [r for r in rows if f(r, "peptide_read") >= 0.61 and es.get(r["design"], 0) <= -0.5]

print(f"designs folded: {len(rows)}")
print(f"organizer gate (peptide_read>=0.61): {len(hits_org)}")
print(f"JDI-like (iptm_pep>=0.8): {len(hits_jdi)}")
print(f"E_D6 <= -1.0: {len(hits_e)}")
print(f"dual signal (gate + E<=-0.5): {len(dual)}")
print()
print("all designs (sorted by peptide_read):")
print(f"{'design':14s} {'iptm_pep':>8s} {'ipdae_pep':>9s} {'pep_read':>8s} {'E_D6':>6s}")
for r in sorted(rows, key=lambda x: -f(x, "peptide_read")):
    d = r["design"]
    print(f"{d:14s} {f(r,'iptm_pep'):8.3f} {f(r,'ipdae_pep'):9.3f} "
          f"{f(r,'peptide_read'):8.3f} {es.get(d, float('nan')):6.2f}")
