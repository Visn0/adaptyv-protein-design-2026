#!/usr/bin/env python3
"""Write Boltz-2 fold inputs for X3 designs.

The X3 designs are RFdiffusion3 outputs; the binder is chain A and the target
arrives as one merged chain B. A Boltz-2 co-fold needs the binder sequence
against the full target construct (three protomers), so this script takes a
design file, reads the binder sequence, and writes the same 4-chain layout that
the handoff used for the W2 folds.

Usage:
    python make_fold_yaml.py --design <design.cif.gz> --out fold-x3a-rbs-<id>.yaml [--mouse]

Both constructs come from `handoff/sequences/targets.fasta` (human P01375 82-233,
mouse P06804 85-235), so a fold is always the same target the W2 folds used.
"""
from __future__ import annotations

import argparse
import gzip
import pathlib

THREE2ONE = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
             "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
             "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
             "TYR": "Y", "VAL": "V"}
C2 = pathlib.Path(__file__).resolve().parents[2]
FASTA = C2 / "handoff/sequences/targets.fasta"


def construct(species: str) -> str:
    lines = FASTA.read_text().splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f">{species}"):
            return lines[index + 1].strip()
    raise SystemExit(f"no {species} construct in {FASTA}")


def atom_site_columns(handle) -> dict[str, int]:
    """{column name: index} from the file's own `_atom_site.` loop header.

    RFdiffusion3 writes a non-standard column order (its own extra columns), so
    never index by convention: even label_atom_id and label_asym_id move.
    """
    columns: list[str] = []
    while True:
        position = handle.tell()
        line = handle.readline()
        if not line:
            break
        if line.startswith("_atom_site."):
            columns.append(line.strip().split(".")[-1])
            continue
        if columns:
            handle.seek(position)   # put the first non-header line back for the caller
            break
    return {name: index for index, name in enumerate(columns)}


def binder_sequence(design: pathlib.Path) -> str:
    """Chain A of the design, in file order, as a one-letter sequence."""
    order: list[tuple[int, str]] = []
    seen: set[int] = set()
    with gzip.open(design, "rt") as fh:
        columns = atom_site_columns(fh)
        for line in fh:
            if not line.startswith("ATOM"):
                continue
            fields = line.split()
            if len(fields) <= max(columns.values()):
                continue
            if fields[columns["label_asym_id"]] != "A":
                continue
            if fields[columns["label_atom_id"]] != "CA":
                continue
            number = int(fields[columns["label_seq_id"]])
            if number in seen:
                continue
            seen.add(number)
            order.append((number, THREE2ONE.get(fields[columns["label_comp_id"]].upper(), "X")))
    order.sort()
    return "".join(letter for _number, letter in order)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--mouse", action="store_true", help="use the mouse construct")
    args = parser.parse_args()

    binder = binder_sequence(args.design)
    target = construct("mouse" if args.mouse else "human")
    body = ["version: 1", "sequences:"]
    for chain, seq in (("A", binder), ("B", target), ("C", target), ("D", target)):
        body += ["  - protein:", f"      id: {chain}", f"      sequence: {seq}"]
    args.out.write_text("\n".join(body) + "\n")
    print(f"{args.design.name} -> {args.out.name}: binder {len(binder)} aa, "
          f"target {len(target)} aa x3 ({'mouse' if args.mouse else 'human'})")
    print(f"  {binder}")


if __name__ == "__main__":
    main()
