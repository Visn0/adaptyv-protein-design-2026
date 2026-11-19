#!/usr/bin/env python3
"""Stage-1 scorer: ipSAE + ipTM + i_pDAE reads and contact gates over the
shortlist folds.

Scores every model of every design under <work>/folds/<design>/ (chain map in
the yamls: A=HLA, B=b2m, C=peptide, D=binder) and writes
<work>/s1-scores.csv (per model) plus a design-level summary.

Reads recorded per model:
  - ipSAE pair reads (ipsae.py; organizer-aligned gate: peptide_read >= 0.61)
  - ipTM pair reads from the confidence json (binder->peptide/HLA/b2m)
  - i_pDAE from the PAE matrix (BindCraft2's interface_pdae_metric, ported:
    CA-CA <= 8 A contact mask, anchored TM transform, max over directions)
  - contact counts / peptide share / P6 min distance from the folded CIF

Pre-registered gate (C0 addendum): ipSAE_min(D, C) >= 0.61, unchanged. The
ipTM/i_pDAE reads are recorded as ranking inputs (ProteinBase benchmark: ipDAE
has the best top-decile PPV across folding models; JDI control reads 0.95
peptide ipTM for a real binder).

ipsae.py is slow (~10-15 s/model), so models are scored in parallel.

Usage:
  .venv/bin/python s1-score.py [--work ~/c5-work/s1] [--jobs 6]
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
import pathlib
import subprocess
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from tools.analysis.contacts import cif_atoms  # noqa: E402

IPSAE = pathlib.Path.home() / "tools/IPSAE/ipsae.py"
CHAINS = ["A", "B", "C", "D"]  # yaml input order = npz concatenation order
BINDER, HLA, B2M, PEP = "D", "A", "B", "C"
P6 = 6
CONTACT_CA = 8.0  # BC2 i_pDAE contact cutoff (Angstrom)
TGT_LABEL = {HLA: "hla", B2M: "b2m", PEP: "pep"}


def parse_ipsae(report: pathlib.Path) -> dict:
    header, rows = None, {}
    for line in report.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "Chn1":
            header = parts
        elif header and len(parts) == len(header) and parts[4] == "asym":
            row = dict(zip(header, parts))
            rows[(row["Chn1"], row["Chn2"])] = row
    return rows


def pair_read(rows: dict, a: str, b: str):
    vals = []
    for x, y in ((a, b), (b, a)):
        if (x, y) in rows:
            vals.append(float(rows[(x, y)]["ipSAE"]))
    return min(vals) if vals else None


def anchored_tm_per_residue(pae: np.ndarray, contact: np.ndarray) -> np.ndarray:
    """BindCraft2 anchored interface TM: per-row masked mean of
    1/(1 + (pae/d0)**2) over contacting partner residues."""
    counts = contact.sum(-1).astype(np.float64)
    d0 = np.maximum(1.24 * (np.maximum(counts, 19.0) - 15.0) ** (1 / 3) - 1.8,
                    1.0)
    tm = 1.0 / (1.0 + (pae / d0[:, None]) ** 2)
    return np.where(contact, tm, 0.0).sum(-1) / np.maximum(counts, 1.0)


def ipdae_reads(npz: pathlib.Path, ca_by_chain: dict) -> dict:
    """i_pDAE per target chain, BC2 definition (max over both directions)."""
    out = {}
    try:
        pae = np.load(npz)["pae"]
    except Exception:
        return out
    lens = {c: len(ca_by_chain.get(c, [])) for c in CHAINS}
    if sum(lens.values()) != pae.shape[0] or not lens.get(BINDER):
        return out
    sl, off = {}, 0
    for c in CHAINS:
        sl[c] = slice(off, off + lens[c])
        off += lens[c]
    b = ca_by_chain[BINDER]
    for tgt in (HLA, B2M, PEP):
        t = ca_by_chain.get(tgt)
        if t is None or not len(t):
            continue
        d2 = ((b[:, None, :] - t[None, :, :]) ** 2).sum(-1)
        contact = d2 <= CONTACT_CA ** 2
        if not contact.any():
            continue
        sub = pae[sl[BINDER], sl[tgt]]
        s = max(anchored_tm_per_residue(sub, contact).max(),
                anchored_tm_per_residue(sub.T, contact.T).max())
        out[TGT_LABEL[tgt]] = round(float(s), 3)
    return out


def score_model(model: pathlib.Path) -> dict | None:
    stem = model.stem
    pred = model.parent
    report = pred / f"{stem}_10_10.txt"
    if not report.exists():
        npz = pred / f"pae_{stem}.npz"
        if not npz.exists():
            return None
        subprocess.run([sys.executable, str(IPSAE), str(npz), str(model),
                        "10", "10"], cwd=pred, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    row = {"design": pred.name, "sample": stem}
    if report.exists():
        rows = parse_ipsae(report)
        for label, chain in (("peptide_read", PEP), ("hla_read", HLA),
                             ("b2m_read", B2M)):
            v = pair_read(rows, BINDER, chain)
            if v is not None:
                row[label] = round(v, 3)

    conf = pred / f"confidence_{stem}.json"
    if conf.exists():
        try:
            pc = json.load(open(conf)).get("pair_chains_iptm", {})
            # chain keys follow the input order; the binder is always the LAST
            # chain (4-chain folds: A,B,C,D; free-state 3-chain folds: A,B,D)
            n = len(pc)
            binder = str(n - 1)
            pairs = [("iptm_hla", "0"), ("iptm_b2m", "1")]
            if n == 4:
                pairs.append(("iptm_pep", "2"))
            for label, idx in pairs:
                v = pc.get(binder, {}).get(idx)
                if v is not None:
                    row[label] = round(float(v), 3)
        except Exception:
            pass

    atoms = cif_atoms(model)
    ca_by_chain = {c: np.array([(a[3], a[4], a[5]) for a in atoms
                                if a[0] == c and a[2] == "CA"], dtype=float)
                   for c in CHAINS}
    npz = pred / f"pae_{stem}.npz"
    if npz.exists():
        for label, v in ipdae_reads(npz, ca_by_chain).items():
            row[f"ipdae_{label}"] = v

    bxyz = ca_by_chain[BINDER]
    if len(bxyz):
        pep6 = [(a[3], a[4], a[5]) for a in atoms
                if a[0] == PEP and a[1] == P6]
        if pep6:
            row["p6_min_dist"] = round(min(
                float(np.linalg.norm(bxyz - np.array(p), axis=1).min())
                for p in pep6), 2)
        b_all = np.array([(a[3], a[4], a[5]) for a in atoms
                          if a[0] == BINDER], dtype=float)
        pep_all = [(a[3], a[4], a[5]) for a in atoms if a[0] == PEP]
        hl_all = [(a[3], a[4], a[5]) for a in atoms if a[0] == HLA]
        b2_all = [(a[3], a[4], a[5]) for a in atoms if a[0] == B2M]

        def cont(pts):
            return sum(int((np.linalg.norm(b_all - np.array(p),
                                           axis=1) < 4.5).sum())
                       for p in pts)
        pep_c, hl_c, b2_c = cont(pep_all), cont(hl_all), cont(b2_all)
        row["peptide_contacts"] = pep_c
        row["hla_contacts"] = hl_c
        row["b2m_contacts"] = b2_c
        tot = pep_c + hl_c + b2_c
        row["peptide_share"] = round(pep_c / tot, 3) if tot else 0.0
    return row


FIELDS = ["design", "sample", "peptide_read", "hla_read", "b2m_read",
          "iptm_pep", "iptm_hla", "iptm_b2m", "ipdae_pep", "ipdae_hla",
          "ipdae_b2m", "peptide_contacts", "hla_contacts", "b2m_contacts",
          "peptide_share", "p6_min_dist"]
MEANS = ["peptide_read", "hla_read", "b2m_read", "iptm_pep", "iptm_hla",
         "ipdae_pep", "ipdae_hla", "peptide_share", "p6_min_dist"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=pathlib.Path,
                    default=pathlib.Path.home() / "c5-work" / "s1")
    ap.add_argument("--jobs", type=int, default=6)
    args = ap.parse_args()

    models = []
    for d in sorted((args.work / "folds").iterdir()):
        preds = sorted(d.glob("boltz_results_*/predictions/*"))
        if preds:
            models += sorted(preds[0].glob("*_model_*.cif"))
    print(f"{len(models)} models to score")
    rows = []
    with cf.ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for i, row in enumerate(pool.map(score_model, models), 1):
            if row:
                rows.append(row)
            if i % 50 == 0:
                print(f"  {i}/{len(models)}")

    out = args.work / "s1-scores.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})

    # design-level means + gate counts
    by_design: dict[str, list[dict]] = {}
    for r in rows:
        by_design.setdefault(r["design"], []).append(r)
    summary_rows = []
    for design, rs in sorted(by_design.items()):
        mean = {}
        for k in MEANS:
            vals = [r[k] for r in rs if isinstance(r.get(k), (int, float))]
            mean[k] = round(float(np.mean(vals)), 3) if vals else None
        n_conf = sum(1 for r in rs if isinstance(r.get("peptide_read"), float)
                     and r["peptide_read"] >= 0.61)
        n_jdi = sum(1 for r in rs if isinstance(r.get("iptm_pep"), float)
                    and r["iptm_pep"] >= 0.8)
        summary_rows.append({"design": design, "n_models": len(rs),
                             "n_confident": n_conf, "n_jdi_like": n_jdi,
                             **mean})
    sfields = ["design", "n_models", "n_confident", "n_jdi_like"] + MEANS
    sout = args.work / "s1-summary.csv"
    with sout.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=sfields)
        w.writeheader()
        w.writerows(summary_rows)

    passers = [r for r in summary_rows if (r["peptide_read"] or 0) >= 0.61]
    jdi = [r for r in summary_rows if (r["iptm_pep"] or 0) >= 0.8]
    print(f"{len(summary_rows)} designs scored; "
          f"{len(passers)} with mean peptide_read >= 0.61 (organizer gate); "
          f"{len(jdi)} with mean iptm_pep >= 0.8 (JDI-like)")
    print(f"wrote {out} and {sout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
