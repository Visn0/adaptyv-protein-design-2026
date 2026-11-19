#!/usr/bin/env python3
"""Apply the evolution gen-1 swaps (v5 of the submission set)."""

from __future__ import annotations

import csv
import pathlib
import re

import yaml

HOME = pathlib.Path.home()
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root() / "challenges" / "05-pmhc"
W = HOME / "c5-work"

# the composite winner per family (peprim-001's W57K chosen over its T53K
# sibling: scores 84.3 vs 84.4 within noise; E -2.09 vs -1.64 and dWT +0.252
# decide - the validated instrument wins the tie)
SWAPS = {
    "repair-wave2-pep__run-016__design_0005__g12d-L58K":
        "evorepair-wave2-pep__run-016__design_0005__g12d-L58K-Q15K",
    "peprim-wave1__run-001__design_0002__g12d":
        "evopeprim-wave1__run-001__design_0002__g12d-W57K",
    "repair-wave4-pep__run-007__design_0002__g12d-A58K":
        "evorepair-wave4-pep__run-007__design_0002__g12d-A58K-F50K",
}
G_SETS = ("evo/gen1",)
TRI = W / "evo/gen1/tristate/s1-summary.csv"


def f(r, k, d=0.0):
    try:
        v = r.get(k)
        return float(v) if v not in (None, "") else d
    except (TypeError, ValueError):
        return d


def main() -> int:
    g = {r["design"]: r for r in csv.DictReader((W / "evo/gen1/s1-summary.csv").open())}
    arms = {}
    for r in csv.DictReader(TRI.open()):
        base, st = r["design"].rsplit("__", 1)
        arms.setdefault(base, {})[st] = r
    es = {}
    for line in (W / "evo/gen1/escores.txt").read_text().splitlines():
        m = re.match(r"\s*(-?[0-9.]+)\s+\d+\s+\d+\s+(\S+)$", line)
        if m:
            es[m.group(2)] = float(m.group(1))
    rows = list(csv.DictReader((REPO / "records/final2/ranking-v2.csv").open()))
    for r in rows:
        v = SWAPS.get(r["design"])
        if not v:
            continue
        rv = g[v]
        a = arms[v]
        gp, gh = f(rv, "iptm_pep"), f(rv, "iptm_hla")
        dwt = gp - f(a.get("wt", {}), "iptm_pep")
        dfr = gh - f(a.get("free", {}), "iptm_hla")
        e = es[v]
        r.update({
            "design": v, "g_iptm": f"{gp:.3f}", "g_ipdae": f"{f(rv,'ipdae_pep'):.3f}",
            "d_wt": f"{dwt:+.3f}", "d_free": f"{dfr:+.3f}", "E_D6": f"{e:.2f}",
            "tier": "dual" if (dwt >= 0.15 and dfr >= 0.2) else
                    ("dwt" if dwt >= 0.15 else ("dfree" if dfr >= 0.2 else "flat")),
        })
        r["score_v2"] = f"{30*min(f(rv,'ipdae_pep')/0.9,1) + 20*min(max((gp-0.85)/0.12,0),1) + 20*min(dfr/0.75,1) + 20*min(max((0.2-e)/1.4,0),1) + 10*min(max(dwt,0)/0.46,1):.1f}"
    rows.sort(key=lambda r: -float(r["score_v2"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = str(i)
    with (REPO / "records/final2/ranking-v2.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def seq_of(name: str):
        for src in ("evo/gen1", "repair2", "repair"):
            p = W / src / "folds" / f"{name}.yaml"
            if p.exists():
                d = yaml.safe_load(p.read_text())
                return [s for s in d["sequences"] if s["protein"]["id"] == "D"][0]["protein"]["sequence"]
        for s in ("s1", "s1w3", "camp", "c2p", "c6", "s1w4"):
            for suff in ("", "__g12d"):
                q = W / s / "folds" / f"{name}{suff}.yaml"
                if q.exists():
                    d = yaml.safe_load(q.read_text())
                    return [s2 for s2 in d["sequences"] if s2["protein"]["id"] == "D"][0]["protein"]["sequence"]
        raise FileNotFoundError(name)

    with (REPO / "records/final2/submission-top20.fasta").open("w") as fh:
        for r in rows:
            fh.write(f">{r['design']}\n{seq_of(r['design'])}\n")
    with (REPO / "submission/submission-05-pmhc.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "sequence", "molecule_class"])
        for r in rows:
            w.writerow([r["design"], seq_of(r["design"]), "single_chain"])
    with (REPO / "records/selection-scores-05-pmhc.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["design", "score"])
        for r in rows:
            w.writerow([r["design"], r["score_v2"]])
    print("v5 applied. top 8:")
    for r in rows[:8]:
        print(f"  {r['rank']:>2s} {r['score_v2']:>5s} {r['design'][:52]:52s} "
              f"dWT {r['d_wt']} dfree {r['d_free']} E {r['E_D6']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
