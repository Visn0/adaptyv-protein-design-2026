#!/usr/bin/env python3
"""Build the challenge-3 competition submission CSV: name,sequence,molecule_class.

Reads the final candidate list (design -> sequence) and writes the upload file.
Rules checked here: 10-250 aa per chain, valid amino acids, unique names,
unique sequences, at most 20 designs.

    .venv/bin/python challenges/03-glp1r/submission/make_competition_csv.py \
        [--candidates <csv>] [--out <csv>]
"""
from __future__ import annotations

import argparse
import csv
import pathlib

VALID = set("ACDEFGHIKLMNPQRSTVWY")
MAX_DESIGNS = 20


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=str(pathlib.Path.home() / "c3-work/candidates.csv"))
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent
                                         / "competition-submission-2026-10-19.csv"))
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.candidates)))
    seen_names, seen_seqs, out_rows = set(), set(), []
    for row in rows:
        name, seq = row["design"], row["sequence"].strip().upper()
        if name in seen_names:
            raise SystemExit(f"duplicate name: {name}")
        if seq in seen_seqs:
            raise SystemExit(f"duplicate sequence: {name}")
        if not (10 <= len(seq) <= 250):
            raise SystemExit(f"{name}: length {len(seq)} outside 10-250")
        bad = set(seq) - VALID
        if bad:
            raise SystemExit(f"{name}: invalid residues {sorted(bad)}")
        seen_names.add(name)
        seen_seqs.add(seq)
        out_rows.append({"name": name, "sequence": seq, "molecule_class": "single_chain"})
    if len(out_rows) > MAX_DESIGNS:
        print(f"WARNING: {len(out_rows)} designs > {MAX_DESIGNS}; truncating")
        out_rows = out_rows[:MAX_DESIGNS]
    out = pathlib.Path(args.out)
    with open(out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "sequence", "molecule_class"])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"wrote {out}: {len(out_rows)} designs")


if __name__ == "__main__":
    main()
