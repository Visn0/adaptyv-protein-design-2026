#!/usr/bin/env python
"""Campaign 6 driver: interface-pinned SolubleMPNN re-sequencing of the
campaign-1 champion backbones.

For each champion design:
  1. read its best co-fold sample (chain A = binder, chain B = the 409-res receptor)
  2. write the binder-only backbone (N/CA/C/O) for LigandMPNN
  3. list the binder residues within 4.5 A of the receptor (the fixed set)
  4. run SolubleMPNN (interface pinned), collect the sequences
  5. write Boltz fold YAMLs for every sequence (full receptor, as always)

Run:
  ~/.venvs/mpnn/bin/python run_c6.py <design> [<design> ...]
"""
from __future__ import annotations

import io
import pathlib
import subprocess
import sys

from Bio.PDB import MMCIFParser, PDBIO, Select

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
FOLDS = pathlib.Path.home() / "c3-work/folds"
OUT = pathlib.Path.home() / "c3-work/c6"
MPNN = pathlib.Path.home() / "tools/LigandMPNN"
MPNN_PY = pathlib.Path.home() / ".venvs/mpnn/bin/python"
BINDER = "A"
CONTACT = 4.5

# the receptor chain from the standard fold yaml (byte-identical for every design)
lines = (FOLDS / "e1-r0025.yaml").read_text().splitlines()
RECEPTOR = next(lines[i + 1].split("sequence:")[1].strip()
                for i, l in enumerate(lines) if l.strip() == "id: B")
MSA = next((REPO / "challenges/03-glp1r/inputs/msa").glob("receptor-*-d1024.a3m"))


class Backbone(Select):
    """Keep only the binder chain's N/CA/C/O atoms."""

    def accept_chain(self, chain):
        return chain.id == BINDER

    def accept_atom(self, atom):
        return atom.get_name() in ("N", "CA", "C", "O")


def best_sample(design: str) -> int:
    import csv
    best = None
    for r in csv.DictReader(open(pathlib.Path.home() / "c3-work/folds-screen.csv")):
        if r["design"].strip() != design:
            continue
        ip = float(r["ipsae"])
        if best is None or ip > best[0]:
            best = (ip, int(r["sample"]))
    return best[1] if best else 0


def main(designs):
    OUT.mkdir(parents=True, exist_ok=True)
    for design in designs:
        model = best_sample(design)
        cif = (FOLDS / design / f"boltz_results_{design}" / "predictions" / design
               / f"{design}_model_{model}.cif")
        structure = MMCIFParser(QUIET=True).get_structure("m", str(cif))[0]
        binder = structure[BINDER]
        targets = [c for c in structure if c.id != BINDER]

        # the pinned set: binder residues within 4.5 A of any receptor atom
        batoms = [(a.get_coord(), a.get_parent().id[1]) for a in binder.get_atoms()]
        contacts = set()
        for ch in targets:
            for ta in ch.get_atoms():
                tc = ta.get_coord()
                for bc, resnum in batoms:
                    if ((bc[0] - tc[0]) ** 2 + (bc[1] - tc[1]) ** 2
                            + (bc[2] - tc[2]) ** 2) <= CONTACT ** 2:
                        contacts.add(resnum)
                        break

        # the binder-only backbone, renumbered 1..N in the original order
        order = [r.id[1] for r in binder if r.id[0] == " "]
        fixed = [order.index(c) + 1 for c in sorted(contacts) if c in order]

        backbone = OUT / f"{design}-backbone.pdb"
        writer = PDBIO()
        writer.set_structure(structure)
        with open(backbone, "w") as fh:
            writer.save(fh, Backbone())

        # SolubleMPNN, interface-pinned, temp 0.1
        run_dir = OUT / design
        comp = subprocess.run(
            [str(MPNN_PY), "run.py", "--model_type", "soluble_mpnn",
             "--pdb_path", str(backbone), "--out_folder", str(run_dir),
             "--fixed_residues", " ".join(f"A{n}" for n in fixed),
             "--number_of_batches", "8", "--batch_size", "1",
             "--temperature", "0.1", "--seed", "42"],
            cwd=str(MPNN), capture_output=True, text=True)
        if comp.returncode != 0:
            print(f"{design}: LigandMPNN failed: {comp.stderr[-300:]}")
            continue

        # collect the sequences and write the fold YAMLs
        fasta = sorted((run_dir / "seqs").glob("*.fa"))[0]
        seqs = [l.strip() for l in open(fasta)
                if not l.startswith(">") and l.strip()]
        kept = 0
        for i, seq in enumerate(seqs[1:], start=1):   # seqs[0] = the input
            if "X" in seq or not (10 <= len(seq) <= 200):
                continue
            yml = FOLDS / f"c6-{design}-s{i}.yaml"
            yml.write_text("version: 1\nsequences:\n  - protein:\n      id: A\n"
                           f"      sequence: {seq}\n      msa: empty\n  - protein:\n      id: B\n"
                           f"      sequence: {RECEPTOR}\n      msa: {MSA}\n")
            kept += 1
        print(f"{design}: sample {model}, {len(fixed)} pinned residues, "
              f"{kept} fold YAMLs")


if __name__ == "__main__":
    main(sys.argv[1:] or ["e1b2-r0036", "e1-r0014", "e1b-r0059", "e1-r0025", "e1b-r0037"])
