#!/usr/bin/env python3
"""Build the competition submission CSV (name,sequence,molecule_class) from the
ranked set, with a three-way sequence check: fold YAML == archive == ranked CSV.
Writes challenges/02-tnfa/submission/competition-submission-2026-10-18.csv."""
import csv
import pathlib
import re
import sys

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


CH = _repo_root() / "challenges/02-tnfa"
FOLDS = pathlib.Path.home() / "c2-work" / "genie3" / "folds"

DESIGNS = [  # ranked submission order
    "sr2-ds-mce-14-v6-r2c",
    "sr2-ds2-mce-14-v7-v1-r2a",
    "sr2-ds-mce-14-v6-r2a",
    "sr6-r37",
    "sr1-mce-14-b",
    "ds-mce-14-v6",
    "ds2-mce-14-v7-v1",
    "e1b-d7x-t3-3-v6",
]


def yaml_chain_a(design: str):
    """The binder sequence as folded (chain A) from the run YAML."""
    path = FOLDS / f"{design}.yaml"
    if not path.exists():
        return None
    text = path.read_text()
    pairs = re.findall(r"id:\s*([A-Z])\s*\n\s*sequence:\s*([A-Z]+)", text)
    for chain, seq in pairs:
        if chain == "A":
            return seq
    return None


archive = {r["design"]: r["binder_sequence"]
           for r in csv.DictReader(open(CH / "notes" / "genie3" / "archive-all-designs.csv"))}
ranked_path = CH / "submission" / "submission-2026-10-18.csv"
ranked = ({r["design"]: r["sequence"] for r in csv.DictReader(open(ranked_path))}
          if ranked_path.exists() else {})

rows = []
fail = False
for design in DESIGNS:
    y = yaml_chain_a(design)
    a = archive.get(design)
    c = ranked.get(design)
    match = bool(y) and y == a and (c is None or c == y)
    print(f"{design:26s} len={len(y) if y else '?':>3}  yaml==archive (+ranked when present): {match}")
    if not match:
        fail = True
        print(f"   yaml={y}\n   archive={a}\n   ranked={c}")
    rows.append((design, y))

if fail:
    sys.exit("sequence mismatch — nothing written")

out = CH / "submission" / "competition-submission-2026-10-18.csv"
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["name", "sequence", "molecule_class"])
    for design, seq in rows:
        w.writerow([design, seq, "single_chain"])

# competition rules: <= 20 designs, chains 10-250 aa, unique, standard residues
assert len(rows) <= 20, "over the 20-design cap"
assert all(10 <= len(s) <= 250 for _, s in rows), "chain length outside 10-250"
assert len({s for _, s in rows}) == len(rows), "duplicate sequences"
assert all(re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", s) for _, s in rows), "non-standard residue"
print(f"\nwrote {out} ({len(rows)} designs, all single_chain)")
