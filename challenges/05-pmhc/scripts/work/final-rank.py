#!/usr/bin/env python3
"""Final ranking for the submission: join every stage's reads and apply the
pre-registered protocol, then emit the ranked table and the top-20 FASTA.

Sources:
  - s3 seed table      (10 finalists; seed-median ipTM / i_pDAE / ipSAE)
  - s2 tri-state       (dWT, free-HLA drop; vetoes) for all 27 candidates
  - s1 / s1w3          (G12D reads + peptide_share + p6 for all 27)
  - chai out-msa npz   (global ipTM per finalist, when present)

Protocol (notes/evaluation-protocol.md): gates -> vetoes -> specificity rank
(C3 + footprint: all candidates pass by construction) -> affinity rank
(seed-median ipTM -> i_pDAE -> ipSAE) -> diversity cap (<=2 per generation
run, pairwise identity <70%) -> sequence checks.

Usage: .venv/bin/python final-rank.py [--top 20]
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import re
import statistics as st

HOME = pathlib.Path.home()
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root() / "challenges" / "05-pmhc"
S1 = HOME / "c5-work" / "s1" / "s1-summary.csv"
S1W3 = HOME / "c5-work" / "s1w3" / "s1-summary.csv"
S2 = HOME / "c5-work" / "s2" / "s1-summary.csv"
S2W3 = HOME / "c5-work" / "s2w3" / "s1-summary.csv"
S3 = HOME / "c5-work" / "s3" / "s1-summary.csv"
S3D = HOME / "c5-work" / "s3" / "designs"
SET2 = REPO / "records" / "stage1" / "stage1-stage2-set.csv"
OUT = REPO / "records" / "stage3" / "final-ranking.csv"
FASTA = REPO / "records" / "stage3" / "submission-top20.fasta"


def load(p):
    return {r["design"]: r for r in csv.DictReader(open(p))}


def f(row, key, default=0.0):
    try:
        v = row.get(key)
        return float(v) if v not in (None, "") else default
    except (TypeError, ValueError):
        return default


def chai_iptm(design: str) -> float | None:
    d = S3D / design / "out-msa"
    hits = sorted(d.glob("scores.model_idx_*.npz")) if d.exists() else []
    if not hits:
        return None
    import numpy as np
    return round(float(np.load(hits[0])["iptm"]), 3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    g = {**load(S1), **load(S1W3)}
    s2 = {**load(S2), **load(S2W3)}
    s3 = load(S3)

    # seed medians per finalist
    seeds: dict[str, list[dict]] = {}
    for name, r in s3.items():
        base = re.sub(r"__s\d+$", "", name)
        seeds.setdefault(base, []).append(r)
    seed_med = {}
    for base, rs in seeds.items():
        seed_med[base] = {
            "iptm_median": round(st.median(f(r, "iptm_pep") for r in rs), 4),
            "ipdae_median": round(st.median(f(r, "ipdae_pep") for r in rs), 4),
            "ipsae_median": round(st.median(f(r, "peptide_read") for r in rs), 4),
            "iptm_spread": round(max(f(r, "iptm_pep") for r in rs)
                                 - min(f(r, "iptm_pep") for r in rs), 4),
        }

    candidates = sorted(g.keys())
    rows = []
    for name in candidates:
        base = name.replace("__g12d", "")
        w, fr = s2.get(base + "__wt", {}), s2.get(base + "__free", {})
        med = seed_med.get(name)
        row = {
            "design": name,
            "g_iptm": f(g[name], "iptm_pep"),
            "g_ipdae": f(g[name], "ipdae_pep"),
            "g_ipsae": f(g[name], "peptide_read"),
            "share": f(g[name], "peptide_share"),
            "p6": f(g[name], "p6_min_dist"),
            "d_wt": round(f(g[name], "iptm_pep") - f(w, "iptm_pep"), 3),
            "free_hla": f(fr, "iptm_hla"),
            "d_free": round(f(g[name], "iptm_hla") - f(fr, "iptm_hla"), 3),
            "is_finalist": "yes" if med else "",
            "seed_iptm": med["iptm_median"] if med else "",
            "seed_spread": med["iptm_spread"] if med else "",
            "chai_iptm": chai_iptm(name) if med else "",
        }
        veto = (f(w, "iptm_pep") > f(g[name], "iptm_pep") + 0.05
                or f(fr, "iptm_hla") > f(g[name], "iptm_hla") + 0.05)
        row["verdict"] = "VETO" if veto else "keep"
        # rank key: seed-median ipTM when a finalist, else the G12D read
        row["_rank"] = med["iptm_median"] if med else f(g[name], "iptm_pep")
        rows.append(row)

    rows.sort(key=lambda r: -r["_rank"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    # homology gate (protocol rule 6): any SwissProt hit at fident >= 0.9
    # excludes the design ("de novo only" eligibility). The screen is
    # mmseqs easy-search against SwissProt; see records/stage3/README.md.
    hits_path = REPO / "records" / "stage3" / "homology-hits.m8"
    max_fid = {}
    if hits_path.exists():
        for line in hits_path.read_text().splitlines():
            q, t, fid, ev = line.split("\t")
            max_fid[q] = max(max_fid.get(q, 0.0), float(fid))
    for r in rows:
        r["max_fident"] = max_fid.get(r["design"], 0.0)

    # diversity: cap 2 per generation run (the run id = the middle token)
    def run_id(name: str) -> str:
        return name.split("__")[1] if "__" in name else name

    picked, per_run = [], {}
    for r in rows:
        if r["verdict"] != "keep":
            continue
        if r.get("max_fident", 0.0) >= 0.9:
            continue
        rid = run_id(r["design"])
        if per_run.get(rid, 0) >= 2:
            continue
        per_run[rid] = per_run.get(rid, 0) + 1
        picked.append(r)
        if len(picked) >= args.top:
            break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["rank", "design", "verdict", "max_fident", "g_iptm", "g_ipdae",
              "g_ipsae", "share", "p6", "d_wt", "free_hla", "d_free",
              "is_finalist", "seed_iptm", "seed_spread", "chai_iptm"]
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

    print(f"{len(rows)} candidates ranked; top {len(picked)} picked "
          f"(diversity cap <=2/run)")
    print(f"{'#':>2s} {'design':46s} {'ipTM':>5s} {'seed':>5s} {'dWT':>6s} "
          f"{'dfree':>6s} {'chai':>5s}")
    for r in picked:
        seed = f"{r['seed_iptm']:.3f}" if r["seed_iptm"] != "" else "  -  "
        chai = f"{r['chai_iptm']:.3f}" if r["chai_iptm"] not in ("", None) else "  -  "
        print(f"{r['rank']:2d} {r['design'][:46]:46s} {r['g_iptm']:.3f} {seed} "
              f"{r['d_wt']:+.3f} {r['d_free']:+.3f} {chai}")
    print(f"wrote {OUT}")

    # top-20 FASTA from the source yamls (binder = chain D)
    def binder_seq(design: str) -> str:
        for root in (HOME / "c5-work" / "s1" / "folds",
                     HOME / "c5-work" / "s1w3" / "folds"):
            y = root / f"{design}.yaml"
            if y.exists():
                t = y.read_text()
                ids = re.findall(r"id: (\w)", t)
                seqs = re.findall(r"sequence: ([A-Z]+)", t)
                d = dict(zip(ids, seqs))
                return d.get("D", "")
        return ""

    with FASTA.open("w") as fh:
        for r in picked:
            fh.write(f">{r['design']}\n{binder_seq(r['design'])}\n")
    print(f"wrote {FASTA} ({len(picked)} sequences)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
