#!/usr/bin/env python3
"""C9 pose screen for CA-trace backbones (genie3 output has CA atoms only,
residue name UNK). Same geometry as s0-pose-screen.py but CA-CA distances and
no sidechain rule (the C3/charge rules apply after folding).

Layout: A = HLA, B = b2m, C = peptide, D = binder.

Usage (from the repo root):
    .venv/bin/python c9-screen.py --dir ~/c5-work/c9/backbones --out ~/c5-work/c9/screen.csv
"""

from __future__ import annotations

import argparse
import csv
import pathlib

import gemmi
import numpy as np

BINDER, PEPTIDE, HLA, B2M = "D", "C", "A", "B"
RIDGE = {4, 5, 6, 7, 8}


def ca_atoms(st: gemmi.Structure) -> list[tuple[str, int, tuple[float, float, float]]]:
    out = []
    for c in st[0]:
        for r in c:
            for a in r:
                if a.name == "CA":
                    out.append((c.name, r.seqid.num, (a.pos.x, a.pos.y, a.pos.z)))
    return out


def screen(path: pathlib.Path, cutoff: float) -> dict | None:
    try:
        st = gemmi.read_structure(str(path))
    except Exception:
        return None
    if not len(st):
        return None
    atoms = ca_atoms(st)
    if not atoms:
        return None
    bxyz = np.array([p for _c, _n, p in atoms if _c == BINDER])
    if not len(bxyz):
        return None

    def contacts(chain: str, resnums: set[int] | None = None) -> int:
        n = 0
        for c, rn, p in atoms:
            if c != chain or (resnums and rn not in resnums):
                continue
            d = np.linalg.norm(bxyz - np.array(p), axis=1)
            n += int((d < cutoff).sum())
        return n

    pep = contacts(PEPTIDE)
    ridge = contacts(PEPTIDE, RIDGE)
    hl = contacts(HLA)
    b2 = contacts(B2M)
    total = pep + hl + b2
    share = pep / total if total else 0.0
    p6 = [p for c, rn, p in atoms if c == PEPTIDE and rn == 6]
    p6_min = min(float(np.linalg.norm(bxyz - np.array(p), axis=1).min())
                 for p in p6) if p6 else None
    return {
        "design": path.stem,
        "peptide_contacts": pep,
        "ridge_contacts": ridge,
        "hla_contacts": hl,
        "b2m_contacts": b2,
        "peptide_share": round(share, 3),
        "p6_min_dist": round(p6_min, 2) if p6_min is not None else "",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--cutoff", type=float, default=10.0)
    args = ap.parse_args()
    rows = []
    for pdb in sorted(args.dir.glob("g3_*.pdb")):
        r = screen(pdb, args.cutoff)
        if r:
            rows.append(r)
    rows.sort(key=lambda r: -r["peptide_share"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"screened {len(rows)} backbones -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
