#!/usr/bin/env python3
"""Campaign 2: extract the converged peptides from an EvoBind run and write
their fold YAMLs (chain A = peptide, msa empty; chain B = the full receptor
construct with the depth-capped MSA - same setup as campaign 1).

Takes the last 3 iterations' unrelaxed_N.pdb files (near-converged, still
diverse) and deduplicates their peptide sequences.

    .venv/bin/python challenges/03-glp1r/campaigns/c2-peptide-agonists/scripts/c2_extract_designs.py <run_dir> <tag>
"""
from __future__ import annotations

import pathlib
import re
import sys

from Bio.PDB import PDBParser
from Bio.Data.PDBData import protein_letters_3to1_extended as T31

FOLDS = pathlib.Path.home() / "c3-work/folds"
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()


def peptide_sequence(pdb: pathlib.Path) -> str:
    st = PDBParser(QUIET=True).get_structure("x", str(pdb))[0]
    chains = {ch.id: [r for r in ch if r.id[0] == " "] for ch in st}
    shortest = min(chains, key=lambda cid: len(chains[cid]))
    return "".join(T31.get(r.resname, "X") for r in chains[shortest])


def receptor_from_existing_yaml() -> str:
    lines = (FOLDS / "e1-r0025.yaml").read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "id: B":
            return lines[i + 1].split("sequence:", 1)[1].strip()
    raise SystemExit("receptor constant not found")


def main() -> None:
    run_dir, tag = pathlib.Path(sys.argv[1]), sys.argv[2]
    pdbs = sorted(run_dir.glob("unrelaxed_*.pdb"),
                  key=lambda p: int(re.search(r"unrelaxed_(\d+)", p.name).group(1)))
    if not pdbs:
        raise SystemExit(f"no unrelaxed pdbs in {run_dir}")
    last = pdbs[-3:]
    receptor = receptor_from_existing_yaml()
    msa = next((REPO / "challenges/03-glp1r/inputs/msa").glob("receptor-*-d1024.a3m"))
    seen, written = set(), 0
    for pdb in last:
        it = re.search(r"unrelaxed_(\d+)", pdb.name).group(1)
        try:
            seq = peptide_sequence(pdb)
        except Exception as exc:  # file mid-write or empty
            print(f"skip {pdb.name}: {exc}")
            continue
        if not seq or seq in seen:
            continue
        seen.add(seq)
        out = FOLDS / f"c2-{tag}-i{it}.yaml"
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
        print(f"{out.name}: {len(seq)} aa {seq}")
    print(f"{written} peptide fold YAMLs written for {tag}")


if __name__ == "__main__":
    main()
