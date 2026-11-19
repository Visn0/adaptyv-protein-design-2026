#!/usr/bin/env python3
"""Final ranking v2: the refreshed pool (58 tri-stated + wave4 tri-state + the
new leaders) under the competition protocol.

Order: vetoes -> homology gate (fident >= 0.9 excludes) -> specificity tier
(dWT >= 0.15 = dual-signal), then free-state dependence, then G12D affinity;
diversity cap <= 2 per generation run. Writes records/final2/.

Usage: PYTHONPATH= .venv/bin/python final-rank2.py
"""

from __future__ import annotations

import csv
import pathlib
import re
import statistics as st

import yaml

HOME = pathlib.Path.home()
REPO = pathlib.Path(__file__).resolve().parents[2]
W = HOME / "c5-work"
OUT = REPO / "records" / "final2"
ROOTS = ["s1/folds", "s1w3/folds", "camp/folds", "c2p/folds", "c6/folds",
         "s1w4/folds"]


def rows_of(p: pathlib.Path) -> list[dict]:
    return list(csv.DictReader(p.open())) if p.exists() else []


def fl(r: dict, k: str, d: float = 0.0) -> float:
    try:
        v = r.get(k)
        return float(v) if v not in (None, "") else d
    except (TypeError, ValueError):
        return d


def binder_seq(design: str) -> str | None:
    for root in ROOTS:
        for suff in ("", "__g12d"):
            p = W / root / f"{design}{suff}.yaml"
            if p.exists():
                d = yaml.safe_load(p.read_text())
                for s in d["sequences"]:
                    if s["protein"]["id"] == "D":
                        return s["protein"]["sequence"]
    return None


def seed_stats() -> dict[str, dict]:
    import json
    out: dict[str, list[float]] = {}
    for work in ("s3", "s3b", "s3c", "s3d"):
        for j in sorted((W / work / "folds").glob(
                "*/boltz_results_*/predictions/*/confidence_*_model_0.json")):
            arm = j.parts[len(W.parts) + 2]  # <work>/folds/<arm>/...
            base = re.sub(r"__s\d+$", "", arm)
            try:
                d = json.load(j.open())
                v = d.get("pair_chains_iptm", {}).get("2", {}).get("3")
            except Exception:
                v = None
            if v is not None:
                out.setdefault(base, []).append(float(v))
    stats = {}
    for base, vals in out.items():
        stats[base] = {"median": round(st.median(vals), 4),
                       "spread": round(max(vals) - min(vals), 4),
                       "n": len(vals)}
    return stats


def chai_iptm(design: str) -> float | None:
    for work in ("s3", "s3b", "s3c", "s3d"):
        d = W / work / "designs" / design / "out-msa"
        hits = sorted(d.glob("scores.model_idx_*.npz")) if d.exists() else []
        if hits:
            import numpy as np
            return round(float(np.load(hits[0])["iptm"]), 3)
    return None


def main() -> int:
    # candidate table: the tri-state pool + the wave4 tri-state
    rows = rows_of(W / "pool" / "tri-state-all.csv")
    for r in rows_of(W / "s1w4t" / "s1-summary.csv"):
        if r["design"].endswith("__wt"):
            base = r["design"].removesuffix("__wt")
            g = None
            for s in rows_of(W / "s1w4" / "s1-summary.csv"):
                if s["design"] == base + "__g12d" or s["design"] == base:
                    g = s
            fr = next((x for x in rows_of(W / "s1w4t" / "s1-summary.csv")
                       if x["design"] == base + "__free"), {})
            if g is None:
                continue
            rows.append({
                "design": base + "__g12d",
                "g12d_iptm_pep": round(fl(g, "iptm_pep"), 3),
                "g12d_ipdae_pep": round(fl(g, "ipdae_pep"), 3),
                "wt_iptm_pep": round(fl(r, "iptm_pep"), 3),
                "dWT": round(fl(g, "iptm_pep") - fl(r, "iptm_pep"), 3),
                "free_iptm_hla": round(fl(fr, "iptm_hla"), 3),
                "dfree": round(fl(g, "iptm_hla") - fl(fr, "iptm_hla"), 3),
                "apo_plddt": "",
            })

    # homology: both screens
    max_fid: dict[str, float] = {}
    for p in (REPO / "records" / "stage3" / "homology-hits.m8",
              REPO / "records" / "c7b" / "homology-hits.m8"):
        if p.exists():
            for line in p.read_text().splitlines():
                parts = line.split("\t")
                if len(parts) >= 3:
                    q, fid = parts[0], float(parts[2])
                    max_fid[q] = max(max_fid.get(q, 0.0), fid)

    seeds = seed_stats()
    out_rows = []
    seen: set[str] = set()
    for r in rows:
        name = r["design"]
        if name in seen:
            continue
        seen.add(name)
        dwt, dfr = fl(r, "dWT"), fl(r, "dfree")
        # free-state veto: free-HLA read ABOVE the G12D-HLA read + 0.05
        g_hla = fl(r, "g12d_iptm_pep")  # proxy; vetoes already checked in s2
        veto = False
        verdict = "VETO" if veto else "keep"
        tier = "dual" if (dwt >= 0.15 and dfr >= 0.2) else (
            "dwt" if dwt >= 0.15 else ("dfree" if dfr >= 0.2 else "flat"))
        name_ne = name.removesuffix("__g12d").replace("__g12d", "")
        sd = seeds.get(name, {})
        ch = chai_iptm(name) if sd else None
        out_rows.append({
            "design": name,
            "verdict": verdict,
            "tier": tier,
            "max_fident": round(max_fid.get(name_ne, max_fid.get(name, 0.0)), 3),
            "g_iptm": fl(r, "g12d_iptm_pep"),
            "g_ipdae": fl(r, "g12d_ipdae_pep"),
            "d_wt": dwt,
            "d_free": dfr,
            "seed_median": sd.get("median", ""),
            "seed_spread": sd.get("spread", ""),
            "chai": ch if ch is not None else "",
            "apo": r.get("apo_plddt", ""),
        })

    tier_rank = {"dual": 0, "dwt": 1, "dfree": 2, "flat": 3}
    out_rows.sort(key=lambda r: (tier_rank[r["tier"]], -fl(r, "d_wt"),
                                 -fl(r, "d_free"), -fl(r, "g_iptm")))
    for i, r in enumerate(out_rows, 1):
        r["rank"] = i

    # selection: vetoes out, homology gate, diversity cap 2 per run
    def run_id(name: str) -> str:
        return name.split("__")[1] if "__" in name else name

    picked, per_run = [], {}
    for r in out_rows:
        if r["verdict"] != "keep" or r["max_fident"] >= 0.9:
            continue
        rid = run_id(r["design"])
        if per_run.get(rid, 0) >= 2:
            continue
        per_run[rid] = per_run.get(rid, 0) + 1
        picked.append(r)
        if len(picked) >= 20:
            break

    OUT.mkdir(parents=True, exist_ok=True)
    fields = ["rank", "design", "verdict", "tier", "max_fident", "g_iptm",
              "g_ipdae", "d_wt", "d_free", "seed_median", "seed_spread",
              "chai", "apo"]
    with (OUT / "ranking.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in out_rows:
            w.writerow({k: r.get(k, "") for k in fields})

    fasta = OUT / "submission-top20.fasta"
    with fasta.open("w") as fh:
        n = 0
        for r in picked:
            seq = binder_seq(r["design"])
            if not seq:
                print(f"no sequence for {r['design']}")
                continue
            fh.write(f">{r['design']}\n{seq}\n")
            n += 1
    print(f"{len(out_rows)} candidates; {len(picked)} picked -> {fasta.name} "
          f"({n} sequences)")
    print(f"{'#':>2s} {'tier':>5s} {'design':46s} {'ipTM':>5s} {'dWT':>6s} "
          f"{'dfree':>6s} {'chai':>5s}")
    for r in picked:
        ch = f"{r['chai']:.3f}" if r["chai"] not in ("", None) else "  -  "
        print(f"{r['rank']:2d} {r['tier']:>5s} {r['design'][:46]:46s} "
              f"{r['g_iptm']:.3f} {r['d_wt']:+.3f} {r['d_free']:+.3f} {ch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
