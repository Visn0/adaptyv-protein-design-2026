#!/usr/bin/env python3
"""C9 prep: genie3 problem files for the KRAS G12D pMHC target.

Splits the organizer PDB into per-chain files, writes fastas, copies the
chain MSAs (chain C gets a stub), writes the binderbench problem JSON and
the experiment yaml.

Usage: .venv/bin/python c9-prep.py (from the repo root)
"""

from __future__ import annotations

import json
import pathlib

import gemmi

HOME = pathlib.Path.home()
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH5 = REPO / "challenges" / "05-pmhc"
C9 = HOME / "c5-work" / "c9"
TARGETS = C9 / "targets"
GENIE = HOME / "tools" / "genie3"
PROBLEMS = GENIE / "data" / "design" / "binder_design" / "binderbench" / "problems"
PDB_SRC = CH5 / "inputs" / "7OW6-G12D-noTCR.pdb"
MSA_SRC = {
    "A": CH5 / "inputs" / "msa" / "c56917c149b0-d1024.a3m",
    "B": CH5 / "inputs" / "msa" / "3c7486ad1c1e-d1024.a3m",
}
HOTSPOT = ["C4", "C5", "C6", "C7", "C8"]
EXTENDED = ["C3", "C9"]


def main() -> int:
    (TARGETS / "pdb").mkdir(parents=True, exist_ok=True)
    (TARGETS / "fasta").mkdir(parents=True, exist_ok=True)
    (TARGETS / "msa").mkdir(parents=True, exist_ok=True)

    st = gemmi.read_structure(str(PDB_SRC))
    full_fasta, full_a3m = [], []
    by_chain_pdb, by_chain_fasta, by_chain_msa = [], [], []
    for c in st[0]:
        seq = gemmi.one_letter_code([r.name for r in c])
        # per-chain pdb
        sub = gemmi.Structure()
        sub.name = "pmhc"
        m = gemmi.Model("1")
        m.add_chain(c.clone())
        sub.add_model(m)
        pdb_out = TARGETS / "pdb" / f"pmhc_g12d-chain_{c.name}.pdb"
        sub.write_pdb(str(pdb_out))
        # fasta
        fa = TARGETS / "fasta" / f"pmhc_g12d-chain_{c.name}.fasta"
        fa.write_text(f">{c.name}\n{seq}\n")
        # msa
        msa_out = TARGETS / "msa" / f"pmhc_g12d-chain_{c.name}.a3m"
        if c.name in MSA_SRC:
            msa_out.write_text(MSA_SRC[c.name].read_text())
        else:
            msa_out.write_text(f">query\n{seq}\n")
        full_fasta.append(f">{c.name}\n{seq}\n")
        by_chain_pdb.append(str(pdb_out))
        by_chain_fasta.append(str(fa))
        by_chain_msa.append(str(msa_out))
    full_fasta_path = TARGETS / "fasta" / "pmhc_g12d.fasta"
    full_fasta_path.write_text("".join(full_fasta))
    full_msa_path = TARGETS / "msa" / "pmhc_g12d.a3m"
    full_msa_path.write_text("".join(
        (TARGETS / "msa" / f"pmhc_g12d-chain_{n}.a3m").read_text()
        for n in ("A", "B", "C")))

    problem = {
        "key": "pmhc_g12d",
        "name": "KRAS G12D pMHC (HLA-A*11:01 + b2m + VVVGADGVGK)",
        "target_pdb_filepath": str(PDB_SRC),
        "target_fasta_filepath": str(full_fasta_path),
        "target_msa_filepath": str(full_msa_path),
        "target_pdb_filepath_by_chain": by_chain_pdb,
        "target_fasta_filepath_by_chain": by_chain_fasta,
        "target_msa_filepath_by_chain": by_chain_msa,
        "target_chain_and_residues": ["A1-276", "B1-99", "C1-10"],
        "target_interface_residues": {"hotspot": HOTSPOT, "extended": EXTENDED},
        "binder_min_length": 60,
        "binder_max_length": 110,
        "tag": ["ch5-pmhc"],
        "pdb_id": "7OW6",
        "note": "challenge 5 target; hotspots = peptide P4-P8 ridge "
                "(P6 = the G12D aspartate). Created 2026-11-01.",
    }
    PROBLEMS.mkdir(parents=True, exist_ok=True)
    (PROBLEMS / "pmhc_g12d.json").write_text(json.dumps(problem, indent=2))

    exp = {
        "experiment": {"name": "pmhc_g12d_wave1"},
        "paths": {
            "rootdir": str(C9 / "genie3"),
            "dataset": str(GENIE / "data/design/binder_design/binderbench"),
        },
        "generation": {
            "dataset": {
                "source": "target",
                "selections": "pmhc_g12d",
                "n_sample": 100,
            },
            "sampler": {"sampler": {"direction_scale": 0.0}},
        },
    }
    exp_path = C9 / "experiment-pmhc_g12d.yaml"
    import yaml
    exp_path.write_text(yaml.safe_dump(exp, sort_keys=False))
    print(f"problem: {PROBLEMS / 'pmhc_g12d.json'}")
    print(f"experiment: {exp_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
