#!/usr/bin/env python3
"""Auto-apply a generation's winners: composite comparison, swap, validation prep.

Guardrails: the +1.0 composite margin, one winner per parent family, the fold
gates, and the standing rule that the loop never touches the set's identity
beyond what the composite justifies. Writes the updated ranking + FASTA + CSVs
and prepares the seeds/chai/apo validation inputs for each new entrant.

Usage: PYTHONPATH= .venv/bin/python evo-apply.py <gen>
"""

from __future__ import annotations

import csv
import pathlib
import re
import shutil
import sys

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
GEN = int(sys.argv[1])
G = W / "evo" / f"gen{GEN}"
VAL = W / f"val-gen{GEN}"
MARGIN = 1.0


def f(r, k, d=0.0):
    try:
        v = r.get(k)
        return float(v) if v not in (None, "") else d
    except (TypeError, ValueError):
        return d


def parent_of(v: str) -> str:
    n = v.removeprefix("evo")
    n = re.sub(r"-combo\d+$", "", n)
    n = re.sub(r"-[A-Z]\d+K$", "", n)
    return n


def composite(ipdae, iptm, dfr, e, dwt):
    return (30*min(ipdae/0.9, 1) + 20*min(max((iptm-0.85)/0.12, 0), 1)
            + 20*min(dfr/0.75, 1) + 20*min(max((0.2-e)/1.4, 0), 1)
            + 10*min(max(dwt, 0)/0.46, 1))


def main() -> int:
    g = {r["design"]: r for r in csv.DictReader((G / "s1-summary.csv").open())}
    es = {}
    for line in (G / "escores.txt").read_text().splitlines():
        m = re.match(r"\s*(-?[0-9.]+)\s+\d+\s+\d+\s+(\S+)$", line)
        if m:
            es[m.group(2)] = float(m.group(1))
    arms = {}
    tri = G / "tristate/s1-summary.csv"
    if tri.exists():
        for r in csv.DictReader(tri.open()):
            base, st = r["design"].rsplit("__", 1)
            arms.setdefault(base, {})[st] = r
    rows = list(csv.DictReader((REPO / "records/final2/ranking-v2.csv").open()))
    rank = {r["design"]: r for r in rows}

    # per-parent best winner above the margin
    winners: dict[str, tuple] = {}
    for base, a in arms.items():
        r = g.get(base)
        if not r:
            continue
        gp, gh = f(r, "iptm_pep"), f(r, "iptm_hla")
        if gp < 0.93 or f(r, "ipdae_pep") < 0.60:
            continue
        dwt = gp - f(a.get("wt", {}), "iptm_pep")
        dfr = gh - f(a.get("free", {}), "iptm_hla")
        e = es.get(base)
        if e is None:
            continue
        s = composite(f(r, "ipdae_pep"), gp, dfr, e, dwt)
        p = parent_of(base)
        ps = float(rank[p]["score_v2"]) if p in rank else None
        if ps is None or s <= ps + MARGIN:
            continue
        cur = winners.get(p)
        if cur is None or s > cur[1]:
            winners[p] = (base, s, ps, e, f(r, "ipdae_pep"), dwt, dfr, gp)

    if not winners:
        print(f"gen{GEN}: no winners above margin")
        return 0
    for p, (v, s, ps, e, ipdae, dwt, dfr, gp) in winners.items():
        for r in rows:
            if r["design"] != p:
                continue
            r.update({
                "design": v, "g_iptm": f"{gp:.3f}", "g_ipdae": f"{ipdae:.3f}",
                "d_wt": f"{dwt:+.3f}", "d_free": f"{dfr:+.3f}", "E_D6": f"{e:.2f}",
                "tier": "dual" if (dwt >= 0.15 and dfr >= 0.2) else
                        ("dwt" if dwt >= 0.15 else ("dfree" if dfr >= 0.2 else "flat")),
                "score_v2": f"{s:.1f}",
            })
    rows.sort(key=lambda r: -float(r["score_v2"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = str(i)
    with (REPO / "records/final2/ranking-v2.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def seq_of(name: str):
        for src in sorted((W / "evo").glob("gen*/folds")) + [W / s / "folds" for s in
                        ("repair2", "repair", "s1", "s1w3", "camp", "c2p", "c6", "s1w4")]:
            for cand in (src / f"{name}.yaml", src / f"{name}__g12d.yaml"):
                if cand.exists():
                    d = yaml.safe_load(cand.read_text())
                    return [x for x in d["sequences"]
                            if x["protein"]["id"] == "D"][0]["protein"]["sequence"]
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

    # validation inputs for the new entrants
    (VAL / "folds").mkdir(parents=True, exist_ok=True)
    (VAL / "apo").mkdir(parents=True, exist_ok=True)
    donor = sorted((W / "s3/designs").glob("*/msa_pqt"))[0]
    for i, (p, tup) in enumerate(winners.items()):
        v = tup[0]
        src = G / "folds" / f"{v}.yaml"
        if not src.exists():
            continue
        text = src.read_text()
        short = f"g{GEN}w{i+1}"
        for s in (0, 1, 2):
            (VAL / "folds" / f"{short}__s{s}.yaml").write_text(text)
        d = yaml.safe_load(text)
        bseq = [x for x in d["sequences"] if x["protein"]["id"] == "D"][0]["protein"]["sequence"]
        (VAL / "apo" / f"{short}-apo.yaml").write_text(yaml.safe_dump(
            {"version": 1, "sequences": [{"protein": {"id": "D", "sequence": bseq,
                                                      "msa": "empty"}}]}, sort_keys=False))
        dest = VAL / "designs" / short
        (dest / "msa_pqt").mkdir(parents=True, exist_ok=True)
        seqs = {x["protein"]["id"]: x["protein"]["sequence"] for x in d["sequences"]}
        with (dest / "in.fasta").open("w") as fh:
            for cid in ("A", "B", "C", "D"):
                fh.write(f">protein|{cid}\n{seqs[cid]}\n")
        for pqt in donor.glob("*.pqt"):
            shutil.copy(pqt, dest / "msa_pqt" / pqt.name)
    print(f"gen{GEN}: {len(winners)} swap(s) applied")
    for p, tup in winners.items():
        print(f"  {p[:44]:44s} -> {tup[0][:52]:52s} {tup[2]:.1f} -> {tup[1]:.1f}  E {tup[3]:+.2f}")
    print(f"validation inputs under {VAL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
