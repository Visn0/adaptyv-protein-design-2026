#!/usr/bin/env python3
"""C0 instrument metric: score the calibration arms, per sample and per state.

Instruments:
  boltz  - per sample: ipSAE chain-pair table (ipsae.py, 10/10 cutoffs) for the
           six binder x target pairs; peptide read = max over binder chains of
           ipSAE_min(A|B vs E); HLA read vs C; b2m read vs D. Plus contact
           metrics read straight from the model: P6 min distance, binder
           residues within 4.5 A of the peptide, binder-HLA contact count.
  chai   - contact metrics only (chai writes no PAE, so no ipSAE); iptm from
           the scores npz when present.

Aggregates per arm (mean over samples) and the G12D-minus-WT delta per metric.
Cutoffs are NOT decided here - the run prints the table; the campaign README
gets the dated cutoff addendum afterwards.

Run: .venv/bin/python challenges/05-pmhc/scripts/work/c0-tri-state-metric.py
"""

from __future__ import annotations

import csv
import os
import pathlib
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from tools.analysis.contacts import cif_atoms  # noqa: E402

C5 = ROOT / "challenges" / "05-pmhc"
RECORDS = C5 / "campaigns" / "c0-instrument-calibration" / "records"
WORK = pathlib.Path(os.environ.get("C0_WORK",
                                   pathlib.Path.home() / "c5-work" / "c0"))
IPSAE = pathlib.Path.home() / "tools/IPSAE/ipsae.py"

BINDER = ("A", "B")
TARGETS = {"C": "hla", "D": "b2m", "E": "peptide"}
PEPTIDE = "E"
P6 = 6


def parse_ipsae_report(path: pathlib.Path) -> dict[tuple[str, str], dict]:
    header, rows = None, {}
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "Chn1":
            header = parts
        elif header and len(parts) == len(header) and parts[4] == "asym":
            row = dict(zip(header, parts))
            rows[(row["Chn1"], row["Chn2"])] = row
    return rows


def pair_ipsae_min(rows: dict, a: str, b: str) -> float | None:
    vals = []
    for x, y in ((a, b), (b, a)):
        if (x, y) in rows:
            vals.append(float(rows[(x, y)]["ipSAE"]))
    return min(vals) if vals else None


def contact_metrics(atoms) -> dict:
    binder_xyz = np.array([a[3:6] for a in atoms if a[0] in BINDER], dtype=float)
    binder_res = [(a[0], a[1]) for a in atoms if a[0] in BINDER]
    out = {}
    for chain, label in TARGETS.items():
        tgt = [a for a in atoms if a[0] == chain]
        if not tgt:
            continue
        near = set()
        n_contacts = 0
        for a in tgt:
            d = np.linalg.norm(binder_xyz - np.array(a[3:6]), axis=1)
            n_contacts += int((d < 4.5).sum())
            for idx in np.where(d < 4.5)[0]:
                near.add(binder_res[idx])
        out[f"{label}_contacts_45"] = n_contacts
        if chain == PEPTIDE:
            out["peptide_binder_residues"] = len(near)
    pep6 = [a for a in atoms if a[0] == PEPTIDE and a[1] == P6]
    if pep6:
        d = min(float(np.linalg.norm(binder_xyz - np.array(a[3:6]), axis=1).min())
                for a in pep6)
        out["p6_min_dist"] = round(d, 2)
    return out


def score_boltz(arm_dir: pathlib.Path) -> list[dict]:
    preds = sorted(arm_dir.glob("boltz_results_*/predictions/*"))
    if not preds:
        return []
    pred = preds[0]
    out = []
    for model in sorted(pred.glob("*_model_*.cif")):
        stem = model.stem
        report = pred / f"{stem}_10_10.txt"
        if not report.exists():
            npz = pred / f"pae_{stem}.npz"
            if not npz.exists():
                continue
            subprocess.run([sys.executable, str(IPSAE), str(npz), str(model),
                            "10", "10"], cwd=pred, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        row = {"instrument": "boltz", "sample": stem}
        if report.exists():
            rows = parse_ipsae_report(report)
            for chain, label in TARGETS.items():
                vals = [pair_ipsae_min(rows, b, chain) for b in BINDER]
                vals = [v for v in vals if v is not None]
                if vals:
                    row[f"{label}_read"] = round(max(vals), 3)
        atoms = cif_atoms(model)
        row.update(contact_metrics(atoms))
        out.append(row)
    return out


def score_chai(design_dir: pathlib.Path, subdir: str = "out",
               instrument: str = "chai") -> list[dict]:
    out_dir = design_dir / subdir
    if not out_dir.is_dir():
        return []
    out = []
    for model in sorted(out_dir.glob("pred.model_idx_*.cif")):
        row = {"instrument": instrument, "sample": model.stem}
        atoms = cif_atoms(model)
        row.update(contact_metrics(atoms))
        npz = out_dir / model.name.replace("pred.model_idx_", "scores.model_idx_")
        npz = npz.with_suffix(".npz")
        if npz.exists():
            try:
                row["iptm"] = round(float(np.load(npz)["iptm"]), 3)
            except Exception:
                pass
        out.append(row)
    return out


def main() -> int:
    RECORDS.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    for arm in ("pos-g12d", "pos-wt", "neg-peptidefree", "neg-shuffled"):
        for row in score_boltz(WORK / "folds" / arm):
            all_rows.append({"arm": arm, **row})
        for row in score_chai(WORK / "chai" / "designs" / arm):
            all_rows.append({"arm": arm, **row})
        for row in score_chai(WORK / "chai" / "designs" / arm,
                              "out-msa", "chai-msa"):
            all_rows.append({"arm": arm, **row})
    if not all_rows:
        print("no fold outputs found under", WORK, "- nothing to score yet")
        return 1

    keys = sorted({k for r in all_rows for k in r if k not in ("arm", "instrument", "sample")})
    out = RECORDS / "metrics.csv"
    with open(out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["instrument", "arm", "sample"] + keys)
        writer.writeheader()
        writer.writerows(all_rows)

    lines = ["arm | instrument | metric | mean | min | max | n"]
    for instrument in ("boltz", "chai", "chai-msa"):
        for arm in ("pos-g12d", "pos-wt", "neg-peptidefree", "neg-shuffled"):
            rows = [r for r in all_rows if r["arm"] == arm and r["instrument"] == instrument]
            if not rows:
                continue
            for key in keys:
                vals = [r[key] for r in rows if key in r and r[key] is not None]
                if not vals:
                    continue
                lines.append(f"{arm} | {instrument} | {key} | "
                             f"{np.mean(vals):.3f} | {min(vals)} | {max(vals)} | {len(vals)}")
    delta = ["", "delta (pos-g12d - pos-wt), boltz means:"]
    g12d = {k: np.mean([r[k] for r in all_rows if r["arm"] == "pos-g12d"
                        and r["instrument"] == "boltz" and k in r])
            for k in keys}
    wt = {k: np.mean([r[k] for r in all_rows if r["arm"] == "pos-wt"
                      and r["instrument"] == "boltz" and k in r])
          for k in keys}
    for key in keys:
        if key in g12d and key in wt:
            delta.append(f"  {key}: {g12d[key] - wt[key]:+.3f}")

    summary = "\n".join(lines + delta)
    (RECORDS / "summary.txt").write_text(summary + "\n")
    print(summary)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
