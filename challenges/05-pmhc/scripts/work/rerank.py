#!/usr/bin/env python3
"""Re-rank the submission after the external review (2026-11-02).

The review's core point, verified: dWT (the boltz mutant-vs-wild-type ipTM
delta) FAILED its control in C0 (wrong sign on the known JDI TCR) yet led the
final sort and 45% of the composite score. It is demoted to a minor term.
Ranking now rides on the validated metrics:

  0.30 * i_pDAE   (benchmark: best top-decile precision)
+ 0.20 * ipTM     (fold confidence, calibrated on controls)
+ 0.20 * dfree    (peptide dependence - the direction the controls confirm)
+ 0.10 * dWT      (unvalidated; a weak tiebreak, not a gate)
+ 0.20 * E_D6     (the electrostatic reading - the only instrument with the
                   correct sign on the known control; see escore.py)

Plus: parent/child families collapse to their best member (the review found
three pairs eating six slots at 84-88% identity), the homology gate and the
per-run diversity cap stay.

Usage: PYTHONPATH= .venv/bin/python rerank.py
"""

from __future__ import annotations

import csv
import pathlib
import re

HOME = pathlib.Path.home()
REPO = pathlib.Path(__file__).resolve().parents[2]
W = HOME / "c5-work"
OUT = REPO / "records" / "final2"


def fl(r: dict, k: str, d: float = 0.0) -> float:
    try:
        v = r.get(k)
        return float(v) if v not in (None, "") else d
    except (TypeError, ValueError):
        return d


def family(name: str) -> str:
    """Parent/child collapse: strip the __cN child suffix (then __g12d)."""
    base = re.sub(r"__c\d+$", "", name)
    return base.removesuffix("__g12d")


def run_id(name: str) -> str:
    """Batch + run, so 'peprim-wave1__run-001' never collides with
    'nim-wave3__run-001' (the review found the cap silently merging them)."""
    parts = name.split("__")
    return "__".join(parts[:2]) if len(parts) >= 2 else name


def main() -> int:
    rows = [r for r in csv.DictReader((OUT / "ranking.csv").open())]
    escores = {r["design"]: r for r in
               csv.DictReader((OUT / "escores.csv").open())}
    for r in rows:
        ipdae = fl(r, "g_ipdae")
        iptm = fl(r, "g_iptm")
        dfr = fl(r, "d_free")
        dwt = max(fl(r, "d_wt"), 0.0)
        e = (float(escores[r["design"]]["E_D6"])
             if r["design"] in escores else None)
        e_norm = min(max((0.2 - e) / 1.4, 0.0), 1.0) if e is not None else 0.0
        r["_score"] = round(
            30 * min(ipdae / 0.9, 1.0)
            + 20 * min(max((iptm - 0.85) / 0.12, 0.0), 1.0)
            + 20 * min(dfr / 0.75, 1.0)
            + 10 * min(dwt / 0.46, 1.0)
            + 20 * e_norm, 1)
        r["_E"] = e if e is not None else ""
        r["_fam"] = family(r["design"])
    rows.sort(key=lambda r: -r["_score"])

    picked, fams, per_run = [], set(), {}
    for r in rows:
        if r["verdict"] != "keep" or fl(r, "max_fident") >= 0.9:
            continue
        if r["_fam"] in fams:            # parent/child collapse
            continue
        rid = run_id(r["design"])
        if per_run.get(rid, 0) >= 2:
            continue
        fams.add(r["_fam"])
        per_run[rid] = per_run.get(rid, 0) + 1
        picked.append(r)
        if len(picked) >= 20:
            break

    fields = ["rank", "design", "tier", "g_iptm", "g_ipdae", "d_wt", "d_free",
              "seed_median", "chai", "apo", "E_D6", "score_v2"]
    with (OUT / "ranking-v2.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(picked, 1):
            w.writerow({"rank": i, "design": r["design"], "tier": r["tier"],
                        "g_iptm": r["g_iptm"], "g_ipdae": r["g_ipdae"],
                        "d_wt": r["d_wt"], "d_free": r["d_free"],
                        "seed_median": r.get("seed_median", ""),
                        "chai": r.get("chai", ""), "apo": r.get("apo", ""),
                        "E_D6": r.get("_E", ""), "score_v2": r["_score"]})
    print(f"re-ranked: top 20 from {len(rows)} candidates "
          f"(family-collapsed, homology-clean)")
    print(f"{'#':>2s} {'score':>5s} {'ipTM':>5s} {'i_pDAE':>6s} {'dWT':>6s} "
          f"{'dfree':>6s} {'chai':>5s}  design")
    for i, r in enumerate(picked, 1):
        ch = (f"{float(r['chai']):.3f}"
              if r.get("chai") not in ("", None) else "  -  ")
        print(f"{i:2d} {r['_score']:>5.1f} {fl(r,'g_iptm'):>5.3f} "
              f"{fl(r,'g_ipdae'):>6.3f} {fl(r,'d_wt'):>+6.3f} "
              f"{fl(r,'d_free'):>+6.3f} {ch}  {r['design']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
