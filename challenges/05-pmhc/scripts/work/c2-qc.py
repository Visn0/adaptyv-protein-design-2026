#!/usr/bin/env python3
"""C2 QC: does an RFD3 backbone arc the groove with a peptide-first footprint?

The C2 kill criterion (notes/strategies.md): two overnight runs producing no
backbone that arcs the groove with a peptide-first footprint -> stop, hand the
budget to C1. This script makes the criterion measurable.

RFD3 outputs (cif.gz + json sidecar) renumber the target and may concatenate
its chains; the json's diffused_index_map gives input -> output residue refs
(e.g. "C6" -> "B381"). The script uses the map to locate the peptide (input
C1..C10), the HLA heavy chain (A1..A276) and beta2-microglobulin (B1..B99)
inside the output, then measures contacts from the designed chain (the output
chain not covered by the map image).

Flags per design (thresholds are CLI args with documented defaults):
  arcs        peptide ridge (P4-P8) contacts >= 10 atoms AND HLA contacts >= 30
  peptide_first  peptide share of all target contacts >= 0.20

Usage:
  .venv/bin/python c2-qc.py --dir ~/c5-work/c2/rfd3-e1 --out ~/c5-work/c2/qc.csv
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import pathlib
import shutil
import tempfile

import gemmi
import numpy as np

AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V", "MSE": "M"}

PEPTIDE_INPUT = [f"C{i}" for i in range(1, 11)]
RIDGE_INPUT = [f"C{i}" for i in range(4, 9)]        # P4-P8, 10-mer register
HLA_INPUT = [f"A{i}" for i in range(1, 277)]
B2M_INPUT = [f"B{i}" for i in range(1, 100)]


def load_atoms(gz_path: pathlib.Path):
    with tempfile.NamedTemporaryFile(suffix=".cif", delete=False) as fh:
        with gzip.open(gz_path, "rb") as src:
            shutil.copyfileobj(src, fh)
        tmp = fh.name
    try:
        st = gemmi.read_structure(tmp)
    finally:
        pathlib.Path(tmp).unlink(missing_ok=True)
    if not len(st):
        return None
    # RFD3 cifs carry no entity_poly typing: filter by residue name instead
    return [(c.name, r.seqid.num, r.name, a.name,
             a.pos.x, a.pos.y, a.pos.z)
            for c in st[0] for r in c if r.name in AA3
            for a in r if a.element.name != "H"]


def ref_set(map_values, keys):
    out = set()
    for k in keys:
        v = map_values.get(k)
        if v:
            chain = "".join(ch for ch in v if ch.isalpha())
            num = int("".join(ch for ch in v if ch.isdigit()) or 0)
            out.add((chain, num))
    return out


def qc_one(gz_path: pathlib.Path, args) -> dict | None:
    js = gz_path.with_name(gz_path.name.replace(".cif.gz", ".json"))
    if not js.exists():
        return None
    try:
        imap = json.loads(js.read_text()).get("diffused_index_map", {})
    except Exception:
        return None
    atoms = load_atoms(gz_path)
    if not atoms:
        return None

    peptide = ref_set(imap, PEPTIDE_INPUT)
    ridge = ref_set(imap, RIDGE_INPUT)
    hla = ref_set(imap, HLA_INPUT)
    b2m = ref_set(imap, B2M_INPUT)
    target_refs = peptide | ridge | hla | b2m
    binder_chains = {a[0] for a in atoms
                     if (a[0], a[1]) not in target_refs}
    if len(binder_chains) != 1:
        # fallback: the largest chain whose residues are NOT in the map image
        counts: dict[str, int] = {}
        for a in atoms:
            if (a[0], a[1]) not in target_refs:
                counts[a[0]] = counts.get(a[0], 0) + 1
        if not counts:
            return None
        binder = max(counts, key=lambda k: counts[k])
    else:
        binder = binder_chains.pop()

    bx = np.array([a[4:7] for a in atoms if a[0] == binder], dtype=float)

    def cont(refs) -> int:
        n = 0
        for a in atoms:
            if (a[0], a[1]) in refs:
                d = np.linalg.norm(bx - np.array(a[4:7]), axis=1)
                n += int((d < args.cutoff).sum())
        return n

    pep = cont(peptide)
    pir = cont(ridge)
    hl = cont(hla)
    b2 = cont(b2m)
    total = pep + hl + b2
    share = pep / total if total else 0.0
    arcs = (pir >= args.min_ridge_atoms) and (hl >= args.min_hla_atoms)
    return {
        "design": gz_path.stem.replace(".cif", ""),
        "binder_len": len({a[1] for a in atoms if a[0] == binder}),
        "peptide_contacts": pep, "ridge_contacts": pir,
        "hla_contacts": hl, "b2m_contacts": b2,
        "peptide_share": round(share, 3),
        "arcs": arcs,
        "peptide_first": share >= args.min_share,
        "pass": arcs and share >= args.min_share,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--cutoff", type=float, default=4.5)
    ap.add_argument("--min-ridge-atoms", type=int, default=10)
    ap.add_argument("--min-hla-atoms", type=int, default=30)
    ap.add_argument("--min-share", type=float, default=0.20)
    args = ap.parse_args()

    rows = []
    for gz in sorted(args.dir.rglob("*.cif.gz")):
        row = qc_one(gz, args)
        if row:
            rows.append(row)
    if not rows:
        print("no scoreable designs under", args.dir)
        return 1
    fields = list(rows[0])
    with args.out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    npass = sum(1 for r in rows if r["pass"])
    n_arcs = sum(1 for r in rows if r["arcs"])
    print(f"{len(rows)} designs: {n_arcs} arc the groove, {npass} also peptide-first")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
