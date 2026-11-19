#!/usr/bin/env python3
"""Screen every C4 co-fold for score AND designed-site contacts together.

Single-chain target (one protomer), so unlike the TNF screen there is no
cross-protomer rule: the designed residues all sit on chain A of the 11QC
numbered construct. Two numberings exist:

  --target full   receptor = 11QC chain A 122-760; fold position = auth - 121
  --target block  receptor = apical block 180-400; fold position = auth - 179

at-site rule (pre-registered): at least half of the designed residues (rounded
up, at least 1) have a heavy atom within 5.0 A of the binder. The raw contact
count is printed beside the verdict.

Verdicts: HIT needs at-site AND ipSAE >= 0.6 (the discard line). ipSAE >= 0.8
is the submission line.

Usage:
    python screen_folds_c4.py <folds-dir> --target full|block [--out CSV]
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import subprocess

import numpy as np
from Bio.PDB import MMCIFParser

HOME = pathlib.Path.home()
IPSAE = HOME / "tools/IPSAE/ipsae.py"
PY = HOME / ".venvs/tools/bin/python"
CUTOFF = 5.0

AUTH_SETS = {
    "11qc_e0": (204, 208, 210, 211, 348, 371),
    "11qc_e1": (206, 207, 209, 374),
    "11qc_e2": (343, 344, 347, 350, 351),
    "11qc_e12": (344, 374),
}
# Diagnostic controls, keyed by exact fold name with FINAL fold numbering:
# the 11RN VP1u footprint (the real apical binder) in full-protomer numbering,
# and the same footprint in block numbering for the block-receptor control.
CONTROL_RULES = {
    "00-control-11rn": (81, 82, 83, 87, 88, 89, 90, 91, 227, 250),
    "00a-control-vp1u-msa": (81, 82, 83, 87, 88, 89, 90, 91, 227, 250),
    "00b-control-block": (23, 24, 25, 29, 30, 31, 32, 33, 169, 192),
}
CLASH = 2.8   # below this an atom pair is a clash, not a contact


def rule_for(fold_name: str, offset: int):
    if fold_name in CONTROL_RULES:
        return list(CONTROL_RULES[fold_name])
    for base, auth in AUTH_SETS.items():
        for prefix in (base, base + "b2"):
            if fold_name == prefix or fold_name.startswith(prefix + "_"):
                return [n - offset for n in auth]
    return None


def load(path):
    st = MMCIFParser(QUIET=True).get_structure("m", str(path))[0]
    chains = {}
    for chain in st:
        res = {}
        for r in chain:
            xyz = np.array([a.coord for a in r.get_atoms()])
            if len(xyz):
                res[r.id[1]] = xyz
        chains[chain.id] = res
    return chains


def ipsae_scores(model: pathlib.Path):
    report = model.with_name(model.stem + "_10_10.txt")
    if not report.exists():
        pae = model.with_name("pae_" + model.name.replace(".cif", ".npz"))
        subprocess.run([str(PY), str(IPSAE), str(pae), str(model), "10", "10"],
                       capture_output=True)
    if not report.exists():
        return float("nan"), float("nan")
    for line in report.read_text().splitlines():
        fields = line.split()
        if len(fields) > 11 and fields[0] == "A" and fields[1] == "B" and fields[4] == "asym":
            return float(fields[5]), float(fields[11])
    return float("nan"), float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folds")
    ap.add_argument("--target", choices=("full", "block"), required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    offset = 121 if args.target == "full" else 179
    folds = pathlib.Path(args.folds)
    out_csv = pathlib.Path(args.out) if args.out else folds / "folds-screen.csv"

    rows = []
    print(f"{'design':<16}{'smp':<5}{'ipSAE':>7}{'pDockQ2':>8}{'contacts':>9}{'minSite':>8}{'minAll':>8}  verdict common")
    for fold in sorted(p for p in folds.iterdir() if p.is_dir()):
        prediction = next(iter(fold.glob("boltz_results_*/predictions/*")), None)
        if prediction is None:
            continue
        designed = rule_for(fold.name, offset)
        for model in sorted(prediction.glob("*_model_*.cif")):
            index = model.name.rsplit("model_", 1)[1].split(".")[0]
            score, pd2 = ipsae_scores(model)
            if designed is None:
                print(f"{fold.name:<16}{index:<5}{score:>7.3f}{pd2:>8.3f}{'-':>9}{'-':>7}  no site rule")
                continue
            chains = load(model)
            binder = np.vstack(list(chains["A"].values()))
            target_all = np.vstack(list(chains["B"].values()))
            hits, best = 0, 99.0
            for n in designed:
                xyz = chains.get("B", {}).get(n)
                if xyz is None:
                    continue
                d = float(np.linalg.norm(binder[:, None, :] - xyz[None, :, :], axis=2).min())
                best = min(best, d)
                if d <= CUTOFF:
                    hits += 1
            # clash = any binder-target atom pair below CLASH, anywhere on the
            # target (the site-only check let an off-site jam pass as clean)
            min_all = float(
                np.linalg.norm(binder[:, None, :] - target_all[None, :, :], axis=2).min()
            )
            need = max(1, (len(designed) + 1) // 2)
            at_site = hits >= need and min_all >= CLASH
            # common bar: >= 2 hotspot residues contacted, same for every set
            # (the per-set rule rewards small sets: E12 passes on 1 of 2)
            at_site_common = hits >= 2 and min_all >= CLASH
            verdict = ("HIT" if (at_site and score >= 0.6) else
                       "site" if at_site else ("clash" if hits >= need else "-"))
            verdict_common = ("HIT" if (at_site_common and score >= 0.6) else
                              "site" if at_site_common else
                              ("clash" if hits >= 2 else "-"))
            print(f"{fold.name:<16}{index:<5}{score:>7.3f}{pd2:>8.3f}{hits:>4}/{len(designed):<4}"
                  f"{best:>7.1f}{min_all:>8.2f}  {verdict:<6} {verdict_common}")
            rows.append({"design": fold.name, "sample": index, "ipsae": round(score, 4),
                         "pdockq2": round(pd2, 4), "site_contacts": hits,
                         "site_total": len(designed), "min_dist": round(best, 2),
                         "min_dist_all": round(min_all, 2),
                         "at_site": at_site, "at_site_common": at_site_common,
                         "verdict": verdict, "verdict_common": verdict_common})
    if rows:
        with out_csv.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        hits = {r["design"] for r in rows if r["verdict"] == "HIT"}
        print(f"\nwrote {out_csv} ({len(rows)} samples, {len(hits)} designs with a HIT)")
    else:
        print("no samples scored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
