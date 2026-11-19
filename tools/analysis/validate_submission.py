"""Check a submission CSV before uploading.

The rules are the competition's own submission format: one row per design,
at most 20 rows, `name` and `sequence` required, a canonical amino-acid
sequence of 10-250 residues per chain, a molecule_class the organizers
accept, and no duplicate name or sequence. Free-text columns are also
sniffed for reviewer-directed text, which can disqualify a submission.

Usage:
    python -m tools.analysis.validate_submission submission.csv [--max-rows 20]

Importable:
    from tools.analysis.validate_submission import validate
    errors, warnings, rows = validate(list_of_dict_rows)
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

AA = set("ACDEFGHIKLMNPQRSTVWY")
CLASSES = ("single_chain", "protein", "nanobody", "scfv", "fab_kappa", "fab_lambda")
REQUIRED = ("name", "sequence")
MIN_LEN, MAX_LEN = 10, 250
SNIFF_WORDS = ("ignore", "instruction", "select this", "rank this", "claude")


def _row_errors(index: int, row: dict, seen_names: set, seen_seqs: set) -> list[str]:
    name = (row.get("name") or "").strip()
    sequence = (row.get("sequence") or "").strip().upper()
    mol_class = (row.get("molecule_class") or "single_chain").strip()
    where = f"row {index} ({name})" if name else f"row {index}"
    out = []

    if not name:
        out.append(f"row {index}: empty name")
    elif name in seen_names:
        out.append(f"{where}: duplicate name")
    if sequence in seen_seqs:
        out.append(f"{where}: duplicate sequence")
    seen_names.add(name)
    seen_seqs.add(sequence)

    if mol_class not in CLASSES:
        out.append(f"{where}: molecule_class {mol_class!r} not in {sorted(CLASSES)}")
    # A Fab is two chains in one cell, colon-separated; everything else is one chain.
    for chain in (sequence.split(":") if mol_class.startswith("fab") else [sequence]):
        bad = sorted(set(chain) - AA)
        if bad:
            out.append(f"{where}: invalid characters {bad}")
        if not MIN_LEN <= len(chain) <= MAX_LEN:
            out.append(f"{where}: chain length {len(chain)} outside {MIN_LEN}-{MAX_LEN}")
    return out


def _row_warnings(index: int, row: dict) -> list[str]:
    name = (row.get("name") or "").strip()
    out = []
    for key, value in row.items():
        if key in REQUIRED or not value:
            continue
        if any(word in str(value).lower() for word in SNIFF_WORDS):
            out.append(f"row {index} ({name}) column {key!r}: text looks like an instruction "
                       "to the reviewer - remove it (prompt injection can disqualify)")
    return out


def validate(rows: list[dict], max_rows: int = 20) -> tuple[list[str], list[str], list[dict]]:
    """Return (errors, warnings, rows). Errors block an upload; warnings do not."""
    if not rows:
        return ["no rows in submission"], [], rows

    errors, warnings = [], []
    missing = [column for column in REQUIRED if column not in rows[0]]
    if missing:
        errors.append(f"missing required columns: {missing}")

    seen_names: set[str] = set()
    seen_seqs: set[str] = set()
    for index, row in enumerate(rows, start=1):
        errors += _row_errors(index, row, seen_names, seen_seqs)
        warnings += _row_warnings(index, row)

    if len(rows) > max_rows:
        errors.append(f"{len(rows)} rows exceeds the {max_rows}-per-submission limit")
    return errors, warnings, rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path")
    parser.add_argument("--max-rows", type=int, default=20)
    args = parser.parse_args(argv)

    with open(Path(args.csv_path)) as handle:
        rows = list(csv.DictReader(handle))
    errors, warnings, _ = validate(rows, max_rows=args.max_rows)
    print(f"{len(rows)} design(s) checked")
    for warning in warnings:
        print("WARN:", warning)
    for error in errors:
        print("ERROR:", error)
    print("OK - ready to upload" if not errors else f"{len(errors)} error(s) - fix before uploading")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
