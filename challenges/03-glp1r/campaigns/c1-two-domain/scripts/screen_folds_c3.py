#!/usr/bin/env python3
"""Screen every campaign-1 co-fold for the S1 signature: binding AND two-domain
reach.

A high ipSAE with the binder sitting only on the ECD groove is the known
antagonist outcome (see notes/research-brief.md). The S1 design intent is
contact with BOTH the groove and the TM pocket, so every sample is scored on:

  1. ipSAE + pDockQ2 (interface strength),
  2. groove contacts (6X18 residues 67,69,88,91,121,128 within 4.5 A),
  3. TM-pocket contacts (6X18 residues 298,300,309,313 within 4.5 A),
  4. severe clashes (< 2.0 A atom pairs - the ECD-only trap the public
     challenge-3 repos hit).

Boltz renumbers every chain from 1, and the fold target is the full 24-432
construct, so a 6X18/UniProt number N is fold number N - 23.

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/screen_folds_c3.py [folds_dir]
"""
from __future__ import annotations

import csv
import pathlib
import subprocess
import sys

import numpy as np
from Bio.PDB import MMCIFParser

HOME = pathlib.Path.home()
IPSAE = HOME / "tools/IPSAE/ipsae.py"
PY = HOME / ".venvs/tools/bin/python"
DEFAULT_FOLDS = HOME / "c3-work/folds"
CUTOFF = 4.5
CLASH = 2.0
BAR = 0.8  # the C2-calibrated line: below it, nothing bound in the wet lab

# The fold target is the full 24-432 challenge construct, so Boltz's renumbering
# (1..409) maps to 6X18/UniProt numbering as fold = 6x18 - 23.
GROOVE = [67, 69, 88, 91, 121, 128]
TM_POCKET = [298, 300, 309, 313]
# ECL3/TM6-7 region - the activation-associated reorganization site; residue 387
# is one of the public agonist-reach anchors.
ECL3 = [376, 377, 380, 381, 384, 387, 388, 391]
CONSTRUCT_START = 24


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


def ipsae_scores(model: pathlib.Path) -> dict[str, float]:
    """All interface metrics from the IPSAE report.

    Columns: 0 Chn1, 1 Chn2, 4 Type, 5 ipSAE, 6 ipSAE_d0chn, 7 ipSAE_d0dom,
    8 ipTM_af, 10 pDockQ, 11 pDockQ2, 12 LIS.
    """
    report = model.with_name(model.stem + "_10_10.txt")
    if not report.exists():
        pae = model.with_name("pae_" + model.name.replace(".cif", ".npz"))
        subprocess.run([str(PY), str(IPSAE), str(pae), str(model), "10", "10"],
                       capture_output=True)
    nan = float("nan")
    out = {"ipsae": nan, "ipsae_d0chn": nan, "iptm_af": nan,
           "pdockq": nan, "pdockq2": nan, "lis": nan}
    if not report.exists():
        return out
    for line in report.read_text().splitlines():
        fields = line.split()
        if len(fields) > 12 and fields[0] == "A" and fields[1] == "B" and fields[4] == "asym":
            out.update(ipsae=float(fields[5]), ipsae_d0chn=float(fields[6]),
                       iptm_af=float(fields[8]), pdockq=float(fields[10]),
                       pdockq2=float(fields[11]), lis=float(fields[12]))
            return out
    return out


def binder_plddt(model: pathlib.Path) -> float:
    """Mean pLDDT of the binder chain (Boltz writes pLDDT into the B-factor)."""
    st = MMCIFParser(QUIET=True).get_structure("m", str(model))[0]
    vals = [r["CA"].get_bfactor() for r in st["A"] if r.id[0] == " " and "CA" in r]
    return float(np.mean(vals)) if vals else float("nan")


def interchain_pae(model: pathlib.Path) -> float:
    """Mean PAE across the binder->target block (the PLOS-recommended metric)."""
    npz = model.with_name("pae_" + model.name.replace(".cif", ".npz"))
    if not npz.exists():
        return float("nan")
    data = np.load(npz)
    key = "pae" if "pae" in data else list(data.keys())[0]
    pae = data[key]
    st = MMCIFParser(QUIET=True).get_structure("m", str(model))[0]
    n_a = sum(1 for r in st["A"] if r.id[0] == " ")
    n_b = sum(1 for r in st["B"] if r.id[0] == " ")
    if pae.shape[0] < n_a + n_b:
        return float("nan")
    block = pae[:n_a, n_a:n_a + n_b]
    return float(block.mean())


def site_metrics(chains) -> dict[str, tuple[int, float]]:
    """contacts + best distance for the groove and the TM pocket, fold numbering."""
    binder = np.vstack(list(chains["A"].values()))
    target = chains.get("B", {})
    out = {}
    for label, nums in (("groove", GROOVE), ("tm", TM_POCKET), ("ecl3", ECL3)):
        hits, best = 0, 99.0
        for num in nums:
            xyz = target.get(num - CONSTRUCT_START + 1)
            if xyz is None:
                continue
            d = float(np.linalg.norm(binder[:, None, :] - xyz[None, :, :], axis=2).min())
            best = min(best, d)
            if d <= CUTOFF:
                hits += 1
        out[label] = (hits, best)
    return out


def clash_count(chains) -> int:
    binder = np.vstack(list(chains["A"].values()))
    target = np.vstack(list(chains["B"].values()))
    total = 0
    for i in range(0, len(binder), 400):
        d2 = ((binder[i:i + 400, None, :] - target[None, :, :]) ** 2).sum(-1)
        total += int((d2 < CLASH ** 2).sum())
    return total


def main() -> None:
    folds = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FOLDS
    rows = []
    print(f"{'design':<26}{'smp':<5}{'ipSAE':>7}{'LIS':>7}{'pDQ2':>7}{'grv':>5}{'tm':>4}"
          f"{'dTM':>7}{'clash':>7}  verdict")
    for fold in sorted(p for p in folds.iterdir() if p.is_dir()):
        prediction = next(iter(fold.glob("boltz_results_*/predictions/*")), None)
        if prediction is None:
            continue
        for model in sorted(prediction.glob("*_model_*.cif")):
            index = model.name.rsplit("model_", 1)[1].split(".")[0]
            im = ipsae_scores(model)
            score = im["ipsae"]
            chains = load(model)
            metrics = site_metrics(chains)
            clashes = clash_count(chains)
            grv, grv_d = metrics["groove"]
            tm, tm_d = metrics["tm"]
            e3, e3_d = metrics["ecl3"]
            two_domain = grv >= 1 and tm >= 1 and clashes == 0
            if two_domain and score >= BAR:
                verdict = "HIT (two-domain)"
            elif grv >= 1 and clashes == 0:
                verdict = "groove-only"
            else:
                verdict = "-"
            print(f"{fold.name:<26}{index:<5}{score:>7.3f}{im['lis']:>7.3f}{im['pdockq2']:>7.3f}"
                  f"{grv:>5}{tm:>4}{tm_d:>7.1f}{clashes:>7}  {verdict}")
            rows.append([fold.name, index, round(score, 4), round(im["lis"], 4),
                         round(im["pdockq"], 4), round(im["pdockq2"], 4),
                         round(im["ipsae_d0chn"], 4), round(im["iptm_af"], 4),
                         grv, round(grv_d, 1), tm, round(tm_d, 1), e3, round(e3_d, 1),
                         round(binder_plddt(model), 1), round(interchain_pae(model), 2),
                         clashes, verdict])
    out = folds.parent / "folds-screen.csv"
    with open(out, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["design", "sample", "ipsae", "lis", "pdockq", "pdockq2",
                         "ipsae_d0chn", "iptm_af", "groove_hits", "groove_best_d",
                         "tm_hits", "tm_best_d", "ecl3_hits", "ecl3_best_d",
                         "binder_plddt", "interchain_pae", "clashes", "verdict"])
        writer.writerows(rows)
    print(f"\nwrote {out}")
    hits = [r for r in rows if r[17].startswith("HIT")]
    print(f"two-domain hits: {len(hits)} of {len(rows)} samples")


if __name__ == "__main__":
    main()
