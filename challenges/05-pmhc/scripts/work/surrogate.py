#!/usr/bin/env python3
"""Surrogate screening: learn E_D6 / i_pDAE from sequence features, then rank
the never-folded pool so the next GPU hours go to the best predicted shots.

Discipline: the surrogate is a PRIOR for triage only. Every candidate it
proposes must still be folded and E-scored; the model is validated with
cross-validation and reported honestly (if it cannot predict above chance,
say so and stop).

Usage: ~/.venvs/ml/bin/python surrogate.py
Outputs: ~/c5-work/ml/surrogate-report.md, ~/c5-work/ml/candidates.csv
"""

from __future__ import annotations

import csv
import pathlib
import re

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from scipy.stats import spearmanr

W = pathlib.Path.home() / "c5-work"
ML = W / "ml"
AA = "ACDEFGHIKLMNPQRSTVWY"
KD = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5,
      "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9,
      "M": 1.9, "F": 2.8, "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9,
      "Y": -1.3, "V": 4.2}
CHARGED_POS = set("KR")
CHARGED_NEG = set("DE")
POLAR = set("STNQHY")


def features(seq: str) -> list[float]:
    n = len(seq)
    f = [n]
    f += [seq.count(a) / n for a in AA]                     # 20 fractions
    f.append((sum(seq.count(a) for a in CHARGED_POS) - sum(seq.count(a) for a in CHARGED_NEG)) / n)
    f.append(sum(seq.count(a) for a in POLAR) / n)
    f.append(sum(seq.count(a) for a in "FWY") / n)
    f.append(sum(KD[a] for a in seq) / n)                   # gravy
    runs = max((len(m) for m in re.findall(r"[AVILMFWY]+", seq)), default=0)
    f.append(runs / n)
    f.append(seq[:10].count("P") / 10)
    return f


def base_key(name: str) -> str:
    """Fold-tree name or repair variant -> the pool fasta's key."""
    n = name.removeprefix("repair-")
    n = n.split("__g12d")[0]
    n = re.split(r"__c\d+$|__nine$|__wt$|__g12v$|__g12c$|__free$", n)[0]
    n = re.sub(r"-[A-Z]\d+[A-Z]$", "", n)   # the repair variant suffix
    return n.replace("__", "-")


def load_folded():
    """design -> (sequence, E, ipdae) from the fold trees + label tables."""
    seqs = {}
    cur = ""
    for line in (W / "c1/pool/binder-pool.fasta").read_text().splitlines():
        if line.startswith(">"):
            cur = line[1:].strip()
            seqs[cur] = ""
        else:
            seqs[cur] += line.strip()
    es = {}
    p = ML / "escores-all.tsv"
    if p.exists():
        for line in p.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            m = re.search(r"(-?\d+\.\d+)\s+\d+\s+\d+\s+\S+$", parts[-1])
            if m:
                es[base_key(parts[0])] = float(m.group(1))
    ip = {}
    for s in ("s1", "s1w3", "camp", "c2p", "c6", "s1w4", "repair", "repair2", "s1w5", "s1w6"):
        q = W / s / "s1-summary.csv"
        if not q.exists():
            continue
        for r in csv.DictReader(q.open()):
            try:
                ip[base_key(r["design"])] = float(r.get("ipdae_pep") or 0)
            except ValueError:
                pass
    return seqs, es, ip


def main() -> int:
    seqs, es, ip = load_folded()
    keys = sorted(set(es) & set(ip))
    print(f"labeled designs: {len(keys)} (E {len(es)}, i_pDAE {len(ip)})")
    if len(keys) < 50:
        print("too few labels; rerun after es-all.sh finishes")
        return 1
    X = np.array([features(seqs[k]) for k in keys if k in seqs])
    keys = [k for k in keys if k in seqs]
    yE = np.array([es[k] for k in keys])
    yP = np.array([ip[k] for k in keys])
    report = ["# Surrogate screening report", "",
              f"labeled designs: {len(keys)}", ""]
    models = {}
    for name, y in (("E_D6", yE), ("i_pDAE", yP)):
        kf = KFold(n_splits=5, shuffle=True, random_state=0)
        pred = np.zeros_like(y)
        for tr, te in kf.split(X):
            m = GradientBoostingRegressor(n_estimators=300, max_depth=3,
                                          learning_rate=0.05, random_state=0)
            m.fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
        r2 = r2_score(y, pred)
        rho = spearmanr(y, pred).statistic
        report.append(f"- {name}: 5-fold CV R2 {r2:.3f}, Spearman {rho:.3f}")
        m = GradientBoostingRegressor(n_estimators=300, max_depth=3,
                                      learning_rate=0.05, random_state=0)
        m.fit(X, y)
        models[name] = m
    report.append("")
    folded = set(keys)
    unfurled = [k for k in seqs if k not in folded]
    report.append(f"unfolded pool: {len(unfurled)} designs")
    XU = np.array([features(seqs[k]) for k in unfurled])
    pE = models["E_D6"].predict(XU)
    pP = models["i_pDAE"].predict(XU)
    score = (30 * np.clip(pP / 0.9, 0, 1)
             + 20 * np.clip((0.2 - pE) / 1.4, 0, 1))
    order = np.argsort(-score)
    with (ML / "candidates.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["design", "pred_E", "pred_ipdae", "pred_score", "length"])
        for i in order[:200]:
            k = unfurled[i]
            w.writerow([k, f"{pE[i]:.2f}", f"{pP[i]:.3f}", f"{score[i]:.1f}",
                        len(seqs[k])])
    report.append("")
    report.append("Top 15 predicted candidates (fold these next):")
    report.append("")
    report.append("| design | pred E | pred i_pDAE | pred score | len |")
    report.append("|---|---|---|---|---|")
    for i in order[:15]:
        k = unfurled[i]
        report.append(f"| {k} | {pE[i]:+.2f} | {pP[i]:.3f} | {score[i]:.1f} | {len(seqs[k])} |")
    (ML / "surrogate-report.md").write_text("\n".join(report) + "\n")
    print("\n".join(report[:6]))
    print(f"wrote {ML/'surrogate-report.md'} and {ML/'candidates.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
