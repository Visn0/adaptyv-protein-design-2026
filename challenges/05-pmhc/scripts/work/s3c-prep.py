#!/usr/bin/env python3
"""s3c prep: multi-seed + chai inputs for the submission entries that lack
instrument coverage (the wave4 champions and the two remaining picks).

Usage: PYTHONPATH= .venv/bin/python s3c-prep.py
"""

from __future__ import annotations

import pathlib
import re
import shutil
import sys
import subprocess

HOME = pathlib.Path.home()
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root() / "challenges" / "05-pmhc"
S3 = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HOME / "c5-work" / "s3c"
BUILD_MSA = REPO / "scripts" / "work" / "build_chai_msa.py"
ROOTS = ["s1", "s1w3", "camp", "c2p", "c6", "s1w4"]
DESIGNS = (pathlib.Path(sys.argv[2]).read_text().split()
           if len(sys.argv) > 2 else [
    "wave4-pep__run-017__design_0007__g12d",
    "wave4-pep__run-015__design_0000__g12d",
    "wave4-pep__run-008__design_0000__g12d",
    "wave4-pep__run-020__design_0007__g12d",
    "wave4-pep__run-011__design_0005__g12d",
    "nat-wave1__run-004__design_0001__g12d",
    "wave2-pep__run-024__design_0007__g12d__c5",
])
SEEDS = (1, 2, 3)
CHAINS = ("A", "B", "C", "D")


def parse_yaml(path: pathlib.Path) -> dict[str, str]:
    t = path.read_text()
    return dict(zip(re.findall(r"id: (\w)", t), re.findall(r"sequence: ([A-Z]+)", t)))


def main() -> int:
    (S3 / "designs").mkdir(parents=True, exist_ok=True)
    (S3 / "folds").mkdir(parents=True, exist_ok=True)
    for design in DESIGNS:
        y = None
        for r in ROOTS:
            for suff in ("", "__g12d"):
                cand = HOME / "c5-work" / r / "folds" / f"{design}{suff}.yaml"
                if cand.exists():
                    y = cand
                    break
            if y:
                break
        if y is None:
            print(f"MISSING yaml: {design}")
            continue
        seqs = parse_yaml(y)
        for s in SEEDS:
            dst = S3 / "folds" / f"{design}__s{s}.yaml"
            if not dst.exists():
                shutil.copy2(y, dst)
        d = S3 / "designs" / design
        d.mkdir(parents=True, exist_ok=True)
        fasta = d / "in.fasta"
        with fasta.open("w") as fh:
            for c in CHAINS:
                fh.write(f">protein|{c}\n{seqs[c]}\n")
        if not list((d / "msa_pqt").glob("*.pqt")):
            subprocess.run([str(HOME / ".venvs" / "chai" / "bin" / "python"),
                            str(BUILD_MSA), "--fasta", str(fasta),
                            "--msa-dir", str(REPO / "inputs" / "msa"),
                            "--out", str(d / "msa_pqt")], check=False)
        print(f"{design}: 3 seed yamls + fasta + msa_pqt ok")
    print(f"prepped {len(DESIGNS)} designs into {S3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
