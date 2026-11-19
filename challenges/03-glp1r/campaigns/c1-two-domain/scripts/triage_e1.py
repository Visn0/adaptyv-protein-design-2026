#!/usr/bin/env python3
"""Triage the E1 RFD3 designs before any folding: pre-fold contact counts at
the two sites, straight from the design file, plus the RFD3 sidecar metrics.

The design file keeps the input numbering pattern: the receptor is chain B and
is renumbered 1..384 over the resolved 6X18 chain-R blocks
[(29-129), (136-338), (344-423)] -> NMAP. The binder is chain A.

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/triage_e1.py [gen_dir]
"""
from __future__ import annotations

import csv
import gzip
import json
import pathlib
import sys

import numpy as np
from Bio.PDB import MMCIFParser

GEN = pathlib.Path.home() / "c3-work/generation/e1"
OUT_CSV = pathlib.Path.home() / "c3-work/e1-triage.csv"
TMP = pathlib.Path.home() / "c3-work/_tmp_triage.cif"

GROOVE = [67, 69, 88, 91, 121, 128]
TM_POCKET = [298, 300, 309, 313]
JUNCTION = [197, 210, 221, 234]  # the ECD-TMD interface / GLP-1 N-terminal path
BLOCKS = [(29, 129), (136, 338), (344, 423)]

NMAP: dict[int, int] = {}
_i = 1
for _a, _b in BLOCKS:
    for _n in range(_a, _b + 1):
        NMAP[_n] = _i
        _i += 1


def load_design(path: pathlib.Path):
    with gzip.open(path, "rt") as fh:
        TMP.write_text(fh.read())
    st = MMCIFParser(QUIET=True).get_structure("m", str(TMP))[0]
    chains = {}
    for chain in st:
        res = {}
        for r in chain:
            xyz = np.array([a.coord for a in r.get_atoms()])
            if len(xyz):
                res[r.id[1]] = xyz
        chains[chain.id] = res
    return chains


def site_contacts(chains, nums) -> tuple[int, float]:
    binder = np.vstack(list(chains["A"].values()))
    target = chains.get("B", {})
    atoms4, best = 0, 99.0
    for num in nums:
        xyz = target.get(NMAP.get(num))
        if xyz is None:
            continue
        d = np.linalg.norm(binder[:, None, :] - xyz[None, :, :], axis=2)
        atoms4 += int((d < 4).sum())
        best = min(best, float(d.min()))
    return atoms4, best


def clash_pairs(chains) -> int:
    binder = np.vstack(list(chains["A"].values()))
    target = np.vstack(list(chains["B"].values()))
    total = 0
    for i in range(0, len(binder), 400):
        d2 = ((binder[i:i + 400, None, :] - target[None, :, :]) ** 2).sum(-1)
        total += int((d2 < 2.0 ** 2).sum())
    return total


def main() -> None:
    gen = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else GEN
    out_csv = gen.parent.parent / f"{gen.name}-triage.csv"
    rows = []
    for path in sorted(gen.glob("**/*_model_0.cif.gz")):
        index = path.name.rsplit("_", 3)[-3]
        side_path = path.with_suffix("").with_suffix(".json")
        side = json.loads(side_path.read_text()) if side_path.exists() else {}
        metrics = side.get("metrics", {})
        chains = load_design(path)
        g_atoms, g_best = site_contacts(chains, GROOVE)
        j_atoms, j_best = site_contacts(chains, JUNCTION)
        t_atoms, t_best = site_contacts(chains, TM_POCKET)
        clashes = clash_pairs(chains)
        two_domain = g_atoms > 0 and j_atoms > 0 and clashes == 0
        rows.append({
            "design": path.parent.name,
            "index": index,
            "n_res": metrics.get("num_residues", 0),
            "non_loop": round(metrics.get("non_loop_fraction", 0), 2),
            "side_clashes": (metrics.get("n_clashing.interresidue_clashes_w_sidechain", 0)
                             + metrics.get("n_clashing.interresidue_clashes_w_backbone", 0)),
            "groove_atoms4": g_atoms,
            "groove_best_d": round(g_best, 1),
            "junc_atoms4": j_atoms,
            "junc_best_d": round(j_best, 1),
            "tm_atoms4": t_atoms,
            "tm_best_d": round(t_best, 1),
            "clash_pairs": clashes,
            "two_domain": two_domain,
        })
    rows.sort(key=lambda r: (-int(r["two_domain"]), -r["groove_atoms4"], -r["junc_atoms4"]))
    with open(out_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["design"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{'index':<6}{'n':>4}{'nl':>5}{'sc':>4}{'grvA':>6}{'grvd':>6}{'jcA':>5}"
          f"{'jcd':>6}{'tmA':>5}{'tmd':>6}{'cl':>4}  2D")
    for r in rows[:40]:
        print(f"{r['index']:<6}{r['n_res']:>4}{r['non_loop']:>5}{r['side_clashes']:>4}"
              f"{r['groove_atoms4']:>6}{r['groove_best_d']:>6}{r['junc_atoms4']:>5}"
              f"{r['junc_best_d']:>6}{r['tm_atoms4']:>5}{r['tm_best_d']:>6}"
              f"{r['clash_pairs']:>4}  {'yes' if r['two_domain'] else ''}")
    two = sum(1 for r in rows if r["two_domain"])
    print(f"\n{len(rows)} designs; two-domain pre-fold: {two}")
    print(f"wrote {out_csv}")


if __name__ == "__main__":
    main()
