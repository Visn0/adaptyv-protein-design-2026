#!/usr/bin/env python3
"""Calibrate our interface-electrostatics metric against wet-lab affinity data.

For each unique pMHC structure in ATLAS: download, split chains into pMHC-side
and TCR-side, compute the total Coulomb interaction energy across the interface
at 10 A (simple charge model, same physical basis as our E-score), and record
it with the measured Kd. The question: does our field-based metric track real
measured binding?
"""
import csv
import pathlib
import subprocess
import sys

import gemmi

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


D = _repo_root() / "challenges/05-pmhc/custom-model/data"
STRUCT = D / "atlas_structures"
STRUCT.mkdir(exist_ok=True)

Q = {"ARG": 1, "LYS": 1, "ASP": -1, "GLU": -1, "HIS": 0.1}

rows = list(csv.DictReader((D / "atlas_Mutants.csv").open()))


def clean_pdb(x):
    x = x.strip().split("_")[0].lower()
    return x if (len(x) == 4 and x.isalnum()) else None


pdbs = sorted({clean_pdb(r["pMHC_PDB"]) for r in rows} - {None})
print(f"{len(pdbs)} structures to download", flush=True)

for p in pdbs:
    dest = STRUCT / f"{p}.cif"
    if dest.exists():
        continue
    url = f"https://files.rcsb.org/download/{p}.cif"
    subprocess.run(["curl", "-sfL", url, "-o", str(dest)], timeout=60)

# map structure -> the Kd measured with that pMHC (use WT/observed rows)
kd_by = {}
for r in rows:
    p = clean_pdb(r["pMHC_PDB"])
    if not p:
        continue
    try:
        kd = float(r["Kd_microM"].split()[0])
    except (ValueError, IndexError, KeyError):
        continue
    kd_by.setdefault(p, []).append(kd)

out = []
for p in pdbs:
    f = STRUCT / f"{p}.cif"
    if not f.exists():
        continue
    try:
        st = gemmi.read_structure(str(f))
        st.setup_entities()
    except Exception:
        continue
    if len(st) == 0 or len(st[0]) < 2:
        continue
    chains = [ch for ch in st[0] if len(ch) >= 5]
    # pMHC side: chains containing the 9/10-mer peptide (short chain) + the
    # two big MHC chains; TCR side = the rest
    lens = sorted(len(ch) for ch in chains)
    if len(chains) < 3:
        continue
    peptide = min(chains, key=len)
    big = sorted([ch for ch in chains if ch is not peptide], key=len, reverse=True)
    mhc = big[:2]
    tcr = big[2:]
    if not tcr:
        continue
    # Coulomb across the interface (10 A heavy-atom cutoff)
    tcr_atoms = [(a.pos, Q.get(r.name, 0.0)) for ch in tcr for r in ch for a in r
                 if a.element.name != "H" and Q.get(r.name, 0.0)]
    pmhc_atoms = [(a.pos, Q.get(r.name, 0.0)) for ch in mhc + [peptide] for r in ch for a in r
                  if a.element.name != "H" and Q.get(r.name, 0.0)]
    if not tcr_atoms or not pmhc_atoms:
        continue
    e = 0.0
    n_pairs = 0
    for p1, q1 in tcr_atoms:
        for p2, q2 in pmhc_atoms:
            d = p1.dist(p2)
            if d < 10.0:
                e += 332.0 * q1 * q2 / max(d, 3.0)
                n_pairs += 1
    kds = sorted(kd_by.get(p, []))
    if not kds:
        continue
    median_kd = kds[len(kds) // 2]
    out.append((p, round(e, 1), n_pairs, median_kd, len(kds)))
    print(f"{p}: E_int {e:9.1f} kcal/mol  ({n_pairs} pairs)  median Kd {median_kd} uM  ({len(kds)} rows)", flush=True)

with (D / "calibration_e_vs_kd.csv").open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["pdb", "E_interface_kcal", "n_pairs", "median_kd_uM", "n_rows"])
    w.writerows(out)

# correlation
import statistics
if len(out) >= 8:
    xs = [o[1] for o in out]
    ys = [__import__("math").log10(o[3]) for o in out]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    print(f"\nn={len(out)}  Pearson r(E_int, log10 Kd) = {num / den:.3f}")
print("CALIB_DONE")
