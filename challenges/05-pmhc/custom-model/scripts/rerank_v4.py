#!/usr/bin/env python3
"""Composite v4: add the organizer-gate term and re-rank the operation pool.

v3 composite (0-100): 30*ipdae + 20*iptm + 20*dfree + 20*E + 10*dWT
v4 adds an explicit epitope-read term, because the organizers named the
peptide/groove surface as the actionable target and the v3 composite was
blind to it:
  25*i_pDAE + 15*ipTM + 15*dfree + 15*E + 10*dWT + 20*peptide_read
(peptide_read = fraction of confident models whose interface reads the
peptide; >= 0.61 passes the organizer's own archive gate.)

Merges: gen4 summary (104 designs, the carrier of the gate-passers) and the
current submission ranking, dedupes by design name, applies the hard vetoes
(E must be negative to score the specificity term; fold quality gate), and
writes a re-ranked table.
"""
import csv
import pathlib

C5 = pathlib.Path.home() / "c5-work"
GEN4 = C5 / "evo/gen4/s1-summary.csv"
OUT = C5 / "evo/gen4/rerank-v4.csv"


def load(path):
    return {r["design"]: r for r in csv.DictReader(open(path))}


def num(d, k, default=0.0):
    try:
        return float(d.get(k) or default)
    except (TypeError, ValueError):
        return default


def composite(r):
    ipdae = num(r, "ipdae_pep")
    iptm = num(r, "iptm_pep")
    dfree = num(r, "dfree") if r.get("dfree") else num(r, "iptm_pep") - num(r, "iptm_hla")
    e = num(r, "E", 99.0)
    dwt = num(r, "dWT")
    pr = num(r, "peptide_read")
    if e >= 0:
        return -1.0  # hard veto: positive E is the wrong electrostatic direction
    s = 25 * min(ipdae / 0.9, 1) + 15 * max(min((iptm - 0.85) / 0.12, 1), 0)
    s += 15 * min(max(dfree, 0) / 0.75, 1)
    s += 15 * max(min((0.2 - e) / 1.4, 0), 0)
    s += 10 * min(max(dwt, 0) / 0.46, 1)
    s += 20 * min(pr / 0.61, 1)
    return s


rows = load(GEN4)
# attach E-scores computed in the batch table (paste of the measured values)
E_TABLE = {
    "evonim-wave3__run-001__design_0004__g12d__c7-I13K": -2.63,
    "evonat-wave1__run-004__design_0001__g12d-D25K": -0.12,
    "evopeprim-wave1__run-013__design_0007__g12d__c1-E28K": -0.29,
    "evomini-wave1__run-014__design_0005__g12d-Q48K": -2.90,
    "evowave2-pep__run-026__design_0003__g12d-V24K": -1.35,
    "evopeprim-wave1__run-013__design_0007__g12d__c1-G24K": 0.36,
    "evomini-wave1__run-014__design_0005__g12d-A16K": -3.75,
    "evomini-wave1__run-014__design_0005__g12d-L23K": -3.20,
    "evopeprim-wave1__run-013__design_0007__g12d__c1-F47K": 0.08,
    "evonat-wave1__run-004__design_0001__g12d-E27K": 0.94,
    "evowave1-pep__run-016__design_0003__g12d-Q54K": -2.84,
    "evomini-wave1__run-014__design_0005__g12d-A47K": -2.77,
    "evowave2-pep__run-026__design_0003__g12d-G21K": -1.47,
    "evopeprim-wave1__run-013__design_0007__g12d__c1-L54K": -0.39,
    "evowave2-pep__run-049__design_0002__g12d-A46K": -2.60,
    "evomini-wave1__run-011__design_0001__g12d__c5-L11K": 0.81,
    "evowave2-pep__run-026__design_0003__g12d-A26K": -1.99,
    "evomini-wave1__run-011__design_0001__g12d__c5-A6K": 0.92,
}
for n, e in E_TABLE.items():
    if n in rows:
        rows[n]["E"] = str(e)

ranked = sorted(rows.values(), key=composite, reverse=True)
with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["rank", "design", "v4_score", "peptide_read", "iptm_pep", "E", "iptm_hla"])
    for i, r in enumerate(ranked[:40], 1):
        w.writerow([i, r["design"], f"{composite(r):.1f}", r.get("peptide_read", ""),
                    r.get("iptm_pep", ""), r.get("E", ""), r.get("iptm_hla", "")])
print(f"wrote {OUT} ({len(ranked)} designs ranked)")
for r in ranked[:12]:
    print(f"  {composite(r):5.1f}  pr={r.get('peptide_read','?')[:5]:<6} iptm={r.get('iptm_pep','?')[:5]} E={r.get('E','n/a'):<7} {r['design'][:52]}")
