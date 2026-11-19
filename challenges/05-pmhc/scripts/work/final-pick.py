#!/usr/bin/env python3
"""Final pick (policy): 11 dual-signal + 5 wave4 affinity champions + 4
validated campaign champions = 20. Writes submission-top20.fasta + pick.csv.

Policy notes: the competition ranks specificity -> peptide-dependence ->
affinity. All 11 dual-signal designs carry the specificity tier. The wave4
champions are the project's strongest measured G12D binders (top i_pDAE) and
the validated newcomers (seed 0.985 / chai 0.79). The last four are the best
affinity + dependence designs with seed/chai validation from the original
finalist set.

Usage: PYTHONPATH= .venv/bin/python final-pick.py
"""

from __future__ import annotations

import csv
import pathlib

import yaml

HOME = pathlib.Path.home()
REPO = pathlib.Path(__file__).resolve().parents[2]
OUT = REPO / "records" / "final2"
ROOTS = ["s1/folds", "s1w3/folds", "camp/folds", "c2p/folds", "c6/folds",
         "s1w4/folds"]

WAVE4 = [
    "wave4-pep__run-017__design_0007__g12d",   # top i_pDAE of the project
    "wave4-pep__run-015__design_0000__g12d",   # 0.969 / 0.819
    "wave4-pep__run-007__design_0002__g12d",   # seed 0.985, chai 0.79
    "wave4-pep__run-008__design_0000__g12d",
    "wave4-pep__run-020__design_0007__g12d",
]
CHAMPIONS = [
    "nat-wave1__run-004__design_0001__g12d",   # 0.959 / 0.845
    "nim-wave3__run-001__design_0004__g12d",   # seed 0.990, chai 0.773
    "nat-wave1__run-011__design_0004__g12d",   # seed 0.991, chai 0.799
    "wave2-pep__run-024__design_0007__g12d__c5",  # dfree 0.677, i_pDAE 0.809
]


def binder_seq(design: str) -> str | None:
    for root in ROOTS:
        for suff in ("", "__g12d"):
            p = HOME / "c5-work" / root / f"{design}{suff}.yaml"
            if p.exists():
                d = yaml.safe_load(p.read_text())
                for s in d["sequences"]:
                    if s["protein"]["id"] == "D":
                        return s["protein"]["sequence"]
    return None


def main() -> int:
    rank = {r["design"]: r for r in
            csv.DictReader((OUT / "ranking.csv").open())}
    duals = [r["design"] for r in rank.values() if r["tier"] == "dual"]
    picked = duals + WAVE4 + CHAMPIONS
    seen = set()
    rows = []
    with (OUT / "submission-top20.fasta").open("w") as fh:
        for name in picked:
            if name in seen:
                continue
            seen.add(name)
            seq = binder_seq(name)
            if not seq:
                print(f"MISSING sequence: {name}")
                continue
            r = rank.get(name, {})
            fh.write(f">{name}\n{seq}\n")
            rows.append({"design": name, "tier": r.get("tier", "wave4/champ"),
                         "d_wt": r.get("d_wt", ""), "d_free": r.get("d_free", ""),
                         "g_iptm": r.get("g_iptm", ""),
                         "g_ipdae": r.get("g_ipdae", ""),
                         "seed": r.get("seed_median", ""),
                         "chai": r.get("chai", "")})
    with (OUT / "pick.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"picked {len(rows)} designs -> submission-top20.fasta")
    for i, r in enumerate(rows, 1):
        print(f"{i:2d} {r['tier']:>10s} {r['design'][:44]:44s} "
              f"ipTM {r['g_iptm']:>5} dWT {r['d_wt']:>6} dfree {r['d_free']:>6}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
