#!/usr/bin/env python3
"""Swap the six validated gate-passers into the submission deliverables.

CORRECTION (2026-11-08). An earlier version of this header claimed the six
removed entries were "the six weakest entries on the organizers' epitope
criterion (peptide_read <= 0.098)". That claim is FALSE. Nothing in the repo
or in ~/c5-work supports 0.098, and the six removed entries actually read:

    W57K 0.665 | N71K 0.641 | c5 0.644 | H27K 0.537 | A58K-F50K 0.527 |
    nim-wave3-021 0.441

Three of them read higher than fourteen of the twenty entries that stayed.
The 0.0 readings behind the 0.098 figure belong to a DESCENDANT design
(W57K-combo285357), not to any removed entry — the lookup joined the wrong
generation of the same family.

Correct rationale: six three-seed validated epitope-gate passers replaced
six entries and raised the set's mean gate read. The removed entries were
NOT weak readers, and this swap traded away gate-strong designs. The
selection criterion is not recoverable from the data. Re-derive it from a
criterion that holds before running another swap.

IN:  c7-I13K, Q48K, L23K, Q54K, A47K, A46K  (peptide_read 0.61-0.77,
     E -2.60 to -3.20, all three-seed validated).

Rewrites: submission-05-pmhc.csv, submission-top20.fasta,
selection-scores-05-pmhc.csv. Verifies count/order after writing.
"""
import csv
import pathlib
import re

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


C5 = _repo_root() / "challenges/05-pmhc"
SUB = C5 / "submission/submission-05-pmhc.csv"
FASTA = C5 / "records/final2/submission-top20.fasta"
SCORES = C5 / "records/selection-scores-05-pmhc.csv"
GEN4 = pathlib.Path.home() / "c5-work/evo/gen4/folds"

OUT = [
    "evopeprim-wave1__run-001__design_0002__g12d-W57K",
    "evorepair-nat-wave1__run-011__design_0000__g12d-H27K",
    "evorepair-nat-wave1__run-011__design_0004__g12d-N71K",
    "evorepair-wave4-pep__run-007__design_0002__g12d-A58K-F50K",
    "evonim-wave3__run-021__design_0001__g12d",
    "evomini-wave1__run-011__design_0001__g12d__c5",
]
IN = [
    ("evonim-wave3__run-001__design_0004__g12d__c7-I13K", "c7-I13K", 58.9),
    ("evomini-wave1__run-014__design_0005__g12d-Q48K", "Q48K", 57.2),
    ("evomini-wave1__run-014__design_0005__g12d-L23K", "L23K", 56.4),
    ("evowave1-pep__run-016__design_0003__g12d-Q54K", "Q54K", 55.4),
    ("evomini-wave1__run-014__design_0005__g12d-A47K", "A47K", 55.1),
    ("evowave2-pep__run-049__design_0002__g12d-A46K", "A46K", 54.7),
]


def seq_of(fold_name: str) -> str:
    y = GEN4 / f"{fold_name}.yaml"
    m = re.search(r"id: D\s*\n\s*sequence: ([A-Z]+)", y.read_text())
    return m.group(1)


# CSV: drop OUT rows (match by name with or without the 'evo' prefix)
rows = list(csv.reader(SUB.open()))
header, body = rows[0], rows[1:]
kept = [r for r in body if not any(o == r[0] or o == "evo" + r[0] for o in OUT)]
assert len(kept) == len(body) - 6, f"expected 6 out, matched {len(body) - len(kept)}"
for fold, disp, score in IN:
    kept.append([fold, seq_of(fold), "single_chain"])
with SUB.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(header)
    w.writerows(kept)

# FASTA in the same order
with FASTA.open("w") as fh:
    for name, seq, _ in kept:
        fh.write(f">{name}\n{seq}\n")

# scores: drop OUT, add IN with their v4 values
srows = list(csv.reader(SCORES.open()))
skept = [r for r in srows[1:] if not any(o == r[0] or o == "evo" + r[0] for o in OUT)]
assert len(skept) == len(srows) - 7, f"expected 6 score rows out, matched {len(srows) - 1 - len(skept)}"
for fold, disp, score in IN:
    skept.append([fold, f"{score}"])
with SCORES.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(srows[0])
    w.writerows(skept)

# verify
crows = list(csv.reader(SUB.open()))[1:]
fnames = [l[1:] for l in FASTA.read_text().splitlines()[0::2]]
fseqs = FASTA.read_text().splitlines()[1::2]
print(f"CSV rows: {len(crows)} | FASTA: {len(fnames)} | scores: {len(skept)}")
print("order matched:", [r[0] for r in crows] == fnames)
print("sequences matched:", [r[1] for r in crows] == fseqs)
print("stars present:", all(f in [r[0] for r in crows] for f, _, _ in IN))
print("OUT gone:", not any(o in [r[0] for r in crows] for o in OUT))
