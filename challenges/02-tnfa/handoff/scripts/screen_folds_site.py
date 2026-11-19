#!/usr/bin/env python3
"""Screen every X3 co-fold for the two things that must hold together:

  1. is there an interface at all (ipSAE, pDockQ2), and
  2. is that interface AT the designed epitope (contacts to the designed
     residues, on two different protomers, as the design intends)?

A high ipSAE with the binder 20 A from the designed residues is not a hit: the
folding program found *some* interface, not the designed one.

Numbering: Boltz renumbers every target chain from 1, and the construct is
P01375 82-233, which the 1TNF file numbers 6-157 — so fold = 1TNF - 5. The
target copies are identical, so the check accepts the designed residues on any
protomer, but requires the two halves of the epitope on DIFFERENT protomers.

Earlier version of this script keyed its site map by set name while the folders
are named per design, so nearly every fold was scored against an empty map and
reported "no contact". That is why the map is now matched by prefix.
"""
from __future__ import annotations

import pathlib
import subprocess

import numpy as np
from Bio.PDB import MMCIFParser

HOME = pathlib.Path.home()
C2 = pathlib.Path(__file__).resolve().parents[2]          # challenges/02-tnfa
IPSAE = HOME / "tools/IPSAE/ipsae.py"
PY = HOME / ".venvs/tools/bin/python"
FOLDS_DEFAULT = HOME / "c2-work/x3/folds"
CUTOFF = 4.5

# fold-name prefix -> (residues of half 1, residues of half 2), fold numbering
SITE_RULES = {
    "x3a-rbs": ([78, 82, 84], [142]),        # 84-89 loop and the neighbour's 143-148 loop
    "x3b-switch": ([98], [98, 107]),          # switch trio: R103 on one, R103/K112 on the other
    "x3c-groove": ([60, 62], [70]),           # X2 groove: K65/Q67 and the neighbour's L75
    "x3d-ntc": ([1, 2, 3], [50, 51, 120]),    # N-term/cross patch: R6/T7/P8 and the 52-57/125 loop
}


def rule_for(fold_name: str):
    for prefix, rule in SITE_RULES.items():
        if fold_name.startswith(prefix):
            return rule
    return None, None


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


def site_hits(chains, half1: list[int], half2: list[int]):
    """(touching protomers of half 1, of half 2, best distance over all sites)."""
    binder = np.vstack(list(chains["A"].values()))
    hit1, hit2, best = set(), set(), 99.0
    for chain_id, res_map in chains.items():
        if chain_id == "A":
            continue
        for number, bucket in [(n, hit1) for n in half1] + [(n, hit2) for n in half2]:
            xyz = res_map.get(number)
            if xyz is None:
                continue
            d = float(np.linalg.norm(binder[:, None, :] - xyz[None, :, :], axis=2).min())
            best = min(best, d)
            if d <= CUTOFF:
                bucket.add(chain_id)
    return hit1, hit2, best


def ipsae_scores(model: pathlib.Path) -> tuple[float, float]:
    report = model.with_name(model.stem + "_10_10.txt")
    if not report.exists():
        pae = model.with_name("pae_" + model.name.replace(".cif", ".npz"))
        subprocess.run([str(PY), str(IPSAE), str(pae), str(model), "10", "10"], capture_output=True)
    if not report.exists():
        return float("nan"), float("nan")
    for line in report.read_text().splitlines():
        fields = line.split()
        if len(fields) > 11 and fields[0] == "A" and fields[1] == "B" and fields[4] == "asym":
            # fields: [5]=ipSAE [10]=pDockQ [11]=pDockQ2 (IPSAE report header).
            # Rule 19 pre-registers the bar on pDockQ2, so read [11].
            return float(fields[5]), float(fields[11])
    return float("nan"), float("nan")


def main() -> None:
    import sys
    folds = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else FOLDS_DEFAULT
    print(f"{'design':<20}{'smp':<5}{'ipSAE':>7}{'pDockQ2':>9}{'near':>7}  site (half1/half2)   verdict")
    hits, site_only = [], []
    for fold in sorted(p for p in folds.iterdir() if p.is_dir()):
        prediction = next(iter(fold.glob("boltz_results_*/predictions/*")), None)
        if prediction is None:
            continue
        half1, half2 = rule_for(fold.name)
        for model in sorted(prediction.glob("*_model_*.cif")):
            index = model.name.rsplit("model_", 1)[1].split(".")[0]
            score, pd2 = ipsae_scores(model)
            if half1 is None:
                print(f"{fold.name:<20}{index:<5}{score:>7.3f}{pd2:>9.3f}{'-':>7}  no site rule")
                continue
            hit1, hit2, best = site_hits(load(model), half1, half2)
            cross = bool(hit1 and hit2 and hit1 != hit2)
            at_site = bool(hit1 and hit2)
            verdict = "HIT" if (at_site and score >= 0.6 and pd2 >= 0.23) else (
                "site only" if at_site else "-")
            print(f"{fold.name:<20}{index:<5}{score:>7.3f}{pd2:>9.3f}{best:>7.1f}  "
                  f"{','.join(sorted(hit1)) or '-'}/{','.join(sorted(hit2)) or '-'}"
                  f"{'  cross' if cross else ''}   {verdict}")
            if verdict == "HIT":
                hits.append((fold.name, index, score, pd2))
            elif at_site:
                site_only.append((fold.name, index, score, pd2))
    print()
    if hits:
        print("CLEARS THE BAR AND SITS ON THE DESIGNED EPITOPE:")
        for name, index, score, pd2 in hits:
            print(f"  {name} sample {index}: ipSAE {score:.3f}, pDockQ2 {pd2:.3f}")
    else:
        print("no sample clears the bar AND sits on the designed epitope")
    if site_only:
        print("\nat the site but under the bar (the honest shortlist):")
        for name, index, score, pd2 in sorted(site_only, key=lambda row: -row[2]):
            print(f"  {name} sample {index}: ipSAE {score:.3f}, pDockQ2 {pd2:.3f}")


if __name__ == "__main__":
    main()
