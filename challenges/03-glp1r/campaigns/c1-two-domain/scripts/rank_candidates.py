#!/usr/bin/env python3
"""Rank the two-domain hit designs: screen scores + Boltz confidence +
liability flags (cys report-only, His rule off - no pH objective in challenge 3).

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/rank_candidates.py
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys
from collections import defaultdict

import numpy as np
from Bio.PDB import MMCIFParser
from Bio.Data.PDBData import protein_letters_3to1_extended as T31

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


sys.path.insert(0, str(_repo_root() / "tools"))
from binderkit.liability import assess  # noqa: E402

WORK = pathlib.Path.home() / "c3-work"
OUT_CSV = WORK / "candidates.csv"


def binder_seq(fold_dir: pathlib.Path, sample: str) -> str:
    cif = next(fold_dir.glob(f"boltz_results_*/predictions/*/*_model_{sample}.cif"))
    st = MMCIFParser(QUIET=True).get_structure("m", str(cif))[0]
    return "".join(T31.get(r.resname, "X") for r in st["A"] if r.id[0] == " ")


def confidence(fold_dir: pathlib.Path, sample: str) -> dict:
    path = next(fold_dir.glob(f"boltz_results_*/predictions/*/confidence_*_model_{sample}.json"), None)
    return json.loads(path.read_text()) if path else {}


def main() -> None:
    rows = list(csv.DictReader(open(WORK / "folds-screen.csv")))
    hits = [r for r in rows if r["verdict"].startswith("HIT")]
    by_design: dict[str, list[dict]] = defaultdict(list)
    for r in hits:
        by_design[r["design"]].append(r)
    table = []
    for design, rs in by_design.items():
        best = max(rs, key=lambda r: float(r["ipsae"]))
        fold_dir = WORK / "folds" / design
        seq = binder_seq(fold_dir, best["sample"])
        conf = confidence(fold_dir, best["sample"])
        pair = conf.get("pair_chains_iptm", {})
        iptm_ab = None
        if pair:
            try:
                iptm_ab = list(pair.values())[0]
                iptm_ab = list(iptm_ab.values())[0] if isinstance(iptm_ab, dict) else iptm_ab
            except Exception:
                iptm_ab = None
        report = assess(design, seq, min_his=0, max_cys=99, length_range=(40, 110))
        table.append({
            "design": design,
            "sample": best["sample"],
            "ipsae": float(best["ipsae"]),
            "pdockq2": float(best["pdockq2"]),
            "groove": best["groove_hits"],
            "tm": best["tm_hits"],
            "ecl3": best.get("ecl3_hits", ""),
            "lis": best.get("lis", ""),
            "clashes": best["clashes"],
            "iptm": round(float(iptm_ab), 3) if iptm_ab is not None else None,
            "plddt": round(float(conf.get("complex_plddt", 0)), 1) if conf else None,
            "n_res": len(seq),
            "n_cys": seq.count("C"),
            "liabilities": ";".join(report.failures) if report.failures else "",
            "sequence": seq,
        })
    table.sort(key=lambda t: -t["ipsae"])
    with open(OUT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(table[0].keys()))
        writer.writeheader()
        writer.writerows(table)
    print(f"{'design':<12}{'ipSAE':>7}{'pD2':>7}{'ipTM':>7}{'pLDDT':>7}{'n':>4}{'C':>3}  liabilities")
    for t in table:
        iptm = f"{t['iptm']:.3f}" if t["iptm"] is not None else "-"
        print(f"{t['design']:<12}{t['ipsae']:>7.3f}{t['pdockq2']:>7.3f}{iptm:>7}"
              f"{t['plddt']:>7}{t['n_res']:>4}{t['n_cys']:>3}  {t['liabilities']}")
    print(f"\nwrote {OUT_CSV}")


if __name__ == "__main__":
    main()
