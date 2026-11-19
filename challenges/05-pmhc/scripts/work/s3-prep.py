#!/usr/bin/env python3
"""Stage-3 prep: build the finalist inputs (chai fasta + msa_pqt + multi-seed
boltz yamls) for the 10 finalists.

Finalist set (protocol: tier-1 specificity + best composite affinity/
peptide-dependence): 5 C1 tier-1, 2 wave3 strong, 3 composite picks.
Source yamls: C1 -> ~/c5-work/s1/folds/<design>__g12d.yaml,
wave3 -> ~/c5-work/s1w3/folds/<design>__g12d.yaml.

Usage: .venv/bin/python s3-prep.py
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

HOME = pathlib.Path.home()
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root() / "challenges" / "05-pmhc"
S3 = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HOME / "c5-work" / "s3"
BUILD_MSA = REPO / "scripts" / "work" / "build_chai_msa.py"
ROOTS = ["s1", "s1w3", "camp", "c2p", "c6", "s1w4"]

FINALISTS = {
    # C1 tier-1 (peptide-dependent + G12D-preferring)
    "wave2-pep__run-054__design_0005__g12d": "c1",
    "wave2-pep__run-024__design_0007__g12d": "c1",
    "wave1-pep__run-007__design_0000__g12d": "c1",
    "peprim-wave1__run-012__design_0006__g12d": "c1",
    "wave2-pep__run-009__design_0007__g12d": "c1",
    # wave3 strong (peptide-dependent, top affinity)
    "nim-wave3__run-013__design_0003__g12d": "w3",
    "nim-wave3__run-001__design_0004__g12d": "w3",
    # composite picks (top affinity with strong free-state drop)
    "wave2-pep__run-016__design_0005__g12d": "c1",
    "peprim-wave1__run-013__design_0007__g12d": "c1",
    "peprim-wave1__run-007__design_0007__g12d": "c1",
    # s3b additions (2026-11-02): the C7 + wave4 leaders not yet validated
    "nim-wave3__run-021__design_0001__g12d": "s3b",
    "wave4-pep__run-017__design_0007__g12d": "s3b",
    "wave4-pep__run-007__design_0002__g12d": "s3b",
    "nat-wave1__run-011__design_0004__g12d": "s3b",
}
SEEDS = (1, 2, 3)
CHAINS = ("A", "B", "C", "D")


def parse_yaml(path: pathlib.Path) -> dict[str, str]:
    t = path.read_text()
    ids = re.findall(r"id: (\w)", t)
    seqs = re.findall(r"sequence: ([A-Z]+)", t)
    return dict(zip(ids, seqs))


def main() -> int:
    (S3 / "designs").mkdir(parents=True, exist_ok=True)
    (S3 / "folds").mkdir(parents=True, exist_ok=True)
    for design, src in FINALISTS.items():
        y = None
        for r in ROOTS:
            cand = HOME / "c5-work" / r / "folds" / f"{design}.yaml"
            if cand.exists():
                y = cand
                break
        if y is None:
            print(f"MISSING yaml: {design}", file=sys.stderr)
            return 1
        seqs = parse_yaml(y)
        if not all(c in seqs for c in CHAINS):
            print(f"chain parse failed for {design}: {sorted(seqs)}",
                  file=sys.stderr)
            return 1

        # multi-seed boltz yamls
        for s in SEEDS:
            dst = S3 / "folds" / f"{design}__s{s}.yaml"
            if not dst.exists():
                shutil.copy2(y, dst)

        # chai fasta + msa_pqt
        d = S3 / "designs" / design
        d.mkdir(parents=True, exist_ok=True)
        fasta = d / "in.fasta"
        with fasta.open("w") as fh:
            for c in CHAINS:
                fh.write(f">protein|{c}\n{seqs[c]}\n")
        if not (d / "msa_pqt").exists() or not list((d / "msa_pqt").glob("*.pqt")):
            subprocess.run([str(HOME / ".venvs" / "chai" / "bin" / "python"),
                            str(BUILD_MSA), "--fasta", str(fasta),
                            "--msa-dir", str(REPO / "inputs" / "msa"),
                            "--out", str(d / "msa_pqt")], check=False)
        print(f"{design}: fasta + msa_pqt + {len(SEEDS)} seed yamls ok")
    print(f"finalists prepped: {len(FINALISTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
