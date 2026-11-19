#!/usr/bin/env python3
"""Collect RFD4 NIM designs into the C1 sequence pool.

Scans ~/c5-work/c1/<batch>/run-*/design_*.cif, extracts the binder chain
(D) from each, deduplicates by sequence, and writes:

  ~/c5-work/c1/pool/designs.csv        batch, run, design, length, seq sha1
  ~/c5-work/c1/pool/binder-pool.fasta  unique binder sequences
  ~/c5-work/c1/pool/collect.json       totals + per-batch counts

Usage:
  .venv/bin/python challenges/05-pmhc/scripts/work/c1-collect.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import re

import gemmi

C1 = pathlib.Path.home() / "c5-work" / "c1"
POOL = C1 / "pool"
BINDER_CHAIN = "D"
AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}


def binder_sequence(cif_path: pathlib.Path) -> str | None:
    try:
        st = gemmi.read_structure(str(cif_path))
    except Exception:
        return None
    if not len(st):
        return None
    chain = st[0].find_chain(BINDER_CHAIN)
    if chain is None:
        return None
    # the NIM mmCIF carries no entity_poly info for the binder, so filter by
    # residue name instead of entity_type
    seq = "".join(AA3[r.name] for r in chain if r.name in AA3)
    return seq or None


def main() -> None:
    POOL.mkdir(parents=True, exist_ok=True)
    rows, seen, fasta = [], {}, []
    per_batch: dict[str, int] = {}
    for batch_dir in sorted(p for p in C1.iterdir() if p.is_dir()
                            and p.name != "pool"):
        n = 0
        for run_dir in sorted(batch_dir.glob("run-*")):
            for cif in sorted(run_dir.glob("design_*.cif")):
                seq = binder_sequence(cif)
                if not seq:
                    continue
                sha = hashlib.sha1(seq.encode()).hexdigest()[:12]
                rows.append({"batch": batch_dir.name, "run": run_dir.name,
                             "design": cif.stem, "length": len(seq),
                             "seq_sha1": sha})
                n += 1
                if sha not in seen:
                    seen[sha] = seq
                    fasta.append((f"{batch_dir.name}-{run_dir.name}-{cif.stem}", seq))
        if n:
            per_batch[batch_dir.name] = n

    with (POOL / "designs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["batch", "run", "design", "length",
                                           "seq_sha1"])
        w.writeheader()
        w.writerows(rows)
    with (POOL / "binder-pool.fasta").open("w") as fh:
        for name, seq in fasta:
            fh.write(f">{name}\n{seq}\n")

    lengths = [r["length"] for r in rows]
    stats = {
        "designs_total": len(rows),
        "unique_sequences": len(seen),
        "per_batch": per_batch,
        "length_min": min(lengths) if lengths else 0,
        "length_max": max(lengths) if lengths else 0,
        "length_mean": round(sum(lengths) / len(lengths), 1) if lengths else 0,
    }
    (POOL / "collect.json").write_text(json.dumps(stats, indent=1) + "\n")
    print(json.dumps(stats, indent=1))
    if rows:
        print(f"pool: {POOL / 'binder-pool.fasta'}")


if __name__ == "__main__":
    main()
