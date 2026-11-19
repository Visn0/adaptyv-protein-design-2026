#!/usr/bin/env python3
"""E2: pick the best MPNN sequences per design and write their fold YAMLs.

Reads the ProteinMPNN .fa files, takes the top-K by MPNN score, and writes
e2-<design>-s<k>.yaml with chain A = the new sequence and chain B = the
receptor (read byte-for-byte from an existing E1 fold YAML, so the chain
constant cannot drift).

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/e2_build_yamls.py
"""
from __future__ import annotations

import pathlib

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


WORK = pathlib.Path.home() / "c3-work"
E2 = WORK / "e2"
FOLDS = WORK / "folds"
TOP_K = 4
DESIGNS = ["e1-r0025", "e1-r0007", "e1b-r0037", "e1b-r0039"]


def receptor_from_existing_yaml() -> str:
    for name in ("e1-r0025", "e1b-r0037"):
        path = FOLDS / f"{name}.yaml"
        if not path.exists():
            continue
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "id: B":
                seq = lines[i + 1].split("sequence:", 1)[1].strip()
                assert len(seq) == 409, len(seq)
                return seq
    raise SystemExit("no existing E1 yaml found for the receptor constant")


def main() -> None:
    receptor = receptor_from_existing_yaml()
    msa_dir = _repo_root() / "challenges/03-glp1r/inputs/msa"
    receptor_msa = next(msa_dir.glob("receptor-*-d1024.a3m"))
    written = 0
    for design in DESIGNS:
        fa = E2 / f"{design}.fa"
        if not fa.exists():
            print(f"missing {fa}")
            continue
        lines = fa.read_text().splitlines()
        seqs = []
        i = 0
        while i < len(lines) - 1:
            if lines[i].startswith(">T="):
                score = float(lines[i].split("score=")[1].split(",")[0])
                seqs.append((score, lines[i + 1].strip()))
            i += 2
        seqs.sort(key=lambda x: x[0])
        print(f"{design}: {len(seqs)} seqs, best {seqs[0][0]:.3f}")
        for k, (score, seq) in enumerate(seqs[:TOP_K], start=1):
            assert all(c in "ACDEFGHIKLMNPQRSTVWY" for c in seq), "non-AA"
            out = FOLDS / f"e2-{design}-s{k}.yaml"
            out.write_text(
                "version: 1\n"
                "sequences:\n"
                "  - protein:\n"
                "      id: A\n"
                f"      sequence: {seq}\n"
                "      msa: empty\n"
                "  - protein:\n"
                "      id: B\n"
                f"      sequence: {receptor}\n"
                f"      msa: {receptor_msa}\n"
            )
            written += 1
    print(f"wrote {written} e2 fold YAMLs")


if __name__ == "__main__":
    main()
