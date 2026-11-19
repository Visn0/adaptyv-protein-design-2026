#!/usr/bin/env python3
"""Assemble every tri-stated design (parents + c7 rule candidates + c6
children) into one table with the specificity reads and the apo stability
where measured. Output: ~/c5-work/pool/tri-state-all.csv

Usage: PYTHONPATH= .venv/bin/python pool-assemble.py
"""

from __future__ import annotations

import csv
import json
import pathlib

HOME = pathlib.Path.home()
W = HOME / "c5-work"
OUT = W / "pool" / "tri-state-all.csv"


def f(r: dict, k: str, d: float = 0.0) -> float:
    try:
        v = r.get(k)
        return float(v) if v not in (None, "") else d
    except (TypeError, ValueError):
        return d


def load(src: str) -> dict[str, dict]:
    out = {}
    for r in csv.DictReader((W / src).open()):
        out[r["design"]] = r
    return out


def main() -> int:
    g12d = {}
    for src in ("s1/s1-summary.csv", "s1w3/s1-summary.csv", "camp/s1-summary.csv",
                "c2p/s1-summary.csv", "c6/s1-summary.csv"):
        g12d.update(load(src))
    wt_free = {}
    for src in ("s2/s1-summary.csv", "s2w3/s1-summary.csv", "s2c/s1-summary.csv",
                "c7/s1-summary.csv", "c6t/s1-summary.csv"):
        for k, r in load(src).items():
            wt_free[k] = r
    apo = {}
    stab = W / "apo" / "stability.csv"
    if stab.exists():
        for r in csv.DictReader(stab.open()):
            apo[r["design"].replace("__apo", "")] = f(r, "plddt")

    rows = []
    for name, r in sorted(g12d.items()):
        base = name
        st = wt_free.get(name + "__wt")
        sf = wt_free.get(name + "__free")
        if st is None:
            alt = name.removesuffix("__g12d")
            st = wt_free.get(alt + "__wt")
            sf = wt_free.get(alt + "__free")
        if st is None or sf is None:
            continue
        g_pep, g_hla = f(r, "iptm_pep"), f(r, "iptm_hla")
        rows.append({
            "design": base,
            "g12d_iptm_pep": round(g_pep, 3),
            "g12d_ipdae_pep": round(f(r, "ipdae_pep"), 3),
            "wt_iptm_pep": round(f(st, "iptm_pep"), 3),
            "dWT": round(g_pep - f(st, "iptm_pep"), 3),
            "free_iptm_hla": round(f(sf, "iptm_hla"), 3),
            "dfree": round(g_hla - f(sf, "iptm_hla"), 3),
            "apo_plddt": round(apo.get(base, 0.0), 3),
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    dual = [r for r in rows if r["dWT"] >= 0.15 and r["dfree"] >= 0.2]
    print(f"pool: {len(rows)} tri-stated designs | dual-signal: {len(dual)}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
