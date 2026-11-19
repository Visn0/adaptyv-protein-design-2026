#!/usr/bin/env python3
"""E3: pick the top fixed-interface MPNN variants and write their fold YAMLs.

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/e3_build_yamls.py
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
TOP_K = 2
DESIGNS = ["e1-r0025", "e1b-r0023", "e1b-r0059", "e1-r0033", "e1-r0023"]


def receptor_from_existing_yaml() -> str:
    path = FOLDS / "e1-r0025.yaml"
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "id: B":
            seq = lines[i + 1].split("sequence:", 1)[1].strip()
            assert len(seq) == 409, len(seq)
            return seq
    raise SystemExit("receptor constant not found")


def main() -> None:
    receptor = receptor_from_existing_yaml()
    msa = next((_repo_root() / "challenges/03-glp1r/inputs/msa"
                ).glob("receptor-*-d1024.a3m"))
    written = 0
    for design in DESIGNS:
        fa = E2 / f"run-{design}-fixed/seqs/{design}.fa"
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
        if not seqs:
            print(f"{design}: no variants parsed")
            continue
        seqs.sort(key=lambda x: x[0])
        print(f"{design}: {len(seqs)} variants, best {seqs[0][0]:.3f}")
        for k, (score, seq) in enumerate(seqs[:TOP_K], start=1):
            assert all(c in "ACDEFGHIKLMNPQRSTVWY" for c in seq), "non-AA"
            out = FOLDS / f"e3-{design}-v{k}.yaml"
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
                f"      msa: {msa}\n"
            )
            written += 1
    print(f"wrote {written} e3 fold YAMLs")


if __name__ == "__main__":
    main()
