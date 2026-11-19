#!/usr/bin/env python3
"""Build the challenge-4 Genie 3 target: the 11QC apical block (auth 180-400).

Writes into the genie3 dataset:
  targets/pdb/11qc_apical.pdb (+ -chain_B copy)   chain B, renumbered 1..N
  targets/fasta/11qc_apical.fasta (+ -chain_B copy)
  targets/msa/11qc_apical.a3m  (placeholder; replaced by the fetched MSA)
  problems/11qc_e0|e1|e2|e12.json                 hotspot sets, block numbering

And the genie3 run yamls into ~/c4-work/genie3/.

Hotspot numbering is auth - 179 ONLY IF the block has no missing residues.
The script asserts that and prints every hotspot letter after the shift.

Run: .venv/bin/python setup-c4-targets.py (from the repo root)
"""
from __future__ import annotations

import json
import pathlib

import gemmi

HOME = pathlib.Path.home()
GENIE = HOME / "tools/genie3"
BENCH = GENIE / "data/design/binder_design/binderbench"
WORK = HOME / "c4-work"
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


CH = _repo_root() / "challenges/04-tfr1"
SOURCE = CH / "inputs/11QC.cif"

FIRST, LAST = 180, 400
BINDER_MIN, BINDER_MAX = 60, 110
EXT_RADIUS = 8.0

SETS = {
    "11qc_e0": ("TfR1-E0 named tip", (204, 208, 210, 211, 348, 371)),
    "11qc_e1": ("TfR1-E1 north", (206, 207, 209, 374)),
    "11qc_e2": ("TfR1-E2 south", (343, 344, 347, 350, 351)),
    "11qc_e12": ("TfR1-E12 dual anchor", (344, 374)),
}
SEEDS = {"11qc_e0": 71, "11qc_e1": 72, "11qc_e2": 73, "11qc_e12": 74}


def main() -> int:
    st = gemmi.read_structure(str(SOURCE))
    st.setup_entities()
    rows = []
    for res in st[0]["A"]:
        info = gemmi.find_tabulated_residue(res.name)
        if info and info.is_amino_acid() and FIRST <= res.seqid.num <= LAST:
            rows.append(res)
    nums = [r.seqid.num for r in rows]
    print(f"apical block: {len(rows)} residues, auth {nums[0]}-{nums[-1]}")
    gaps = [b for a, b in zip(nums, nums[1:]) if b != a + 1]
    if gaps or (nums[-1] - nums[0] + 1) != len(nums):
        raise SystemExit(f"block has missing residues (after {gaps}); fix the map")
    print("contiguous: hotspot number = auth - 179")
    index = {r.seqid.num: i + 1 for i, r in enumerate(rows)}
    letters = {}
    for r in rows:
        letters[index[r.seqid.num]] = gemmi.find_tabulated_residue(r.name).one_letter_code.upper()

    # ---- block PDB, chain B, renumbered
    out = gemmi.Structure()
    out.name = "11qc_apical"
    model = gemmi.Model("1")
    chain = gemmi.Chain("B")
    remarks = ["REMARK 999 KEY    11qc_apical",
               "REMARK 999 NAME   TfR1 apical block (11QC chain A 180-400)",
               f"REMARK 999 TARGET B    1  {len(rows)}"]
    for i, res in enumerate(rows, start=1):
        new = gemmi.Residue()
        new.name = res.name
        new.seqid = gemmi.SeqId(str(i))
        for atom in res:
            if atom.is_hydrogen() or (atom.altloc not in ("", "\0", "A")):
                continue
            a = gemmi.Atom()
            a.name = atom.name
            a.element = atom.element
            a.pos = atom.pos
            a.b_iso = atom.b_iso
            a.occ = atom.occ
            new.add_atom(a)
        chain.add_residue(new)
    model.add_chain(chain)
    out.add_model(model)
    pdb_text = out.make_pdb_string()
    pdb_text = "\n".join(remarks) + "\n" + pdb_text
    (BENCH / "targets/pdb/11qc_apical.pdb").write_text(pdb_text)
    (BENCH / "targets/pdb/11qc_apical-chain_B.pdb").write_text(pdb_text)
    seq = "".join(letters[i] for i in sorted(letters))
    (BENCH / "targets/fasta/11qc_apical.fasta").write_text(f">11qc_apical\n{seq}\n")
    (BENCH / "targets/fasta/11qc_apical-chain_B.fasta").write_text(f">11qc_apical-chain_B\n{seq}\n")
    stub = BENCH / "targets/msa/11qc_apical.a3m"
    if not stub.exists():
        stub.write_text(f"#1\t1\n>101\n{seq}\n")
    print(f"target written: {len(seq)} aa, chain B")

    # ---- problem JSONs
    rel = "data/design/binder_design/binderbench/targets"
    for key, (name, auth_set) in SETS.items():
        block_set = sorted(index[n] for n in auth_set)
        check = {n: letters[index[n]] for n in auth_set}
        side_atoms = []
        for n in auth_set:
            res = next(r for r in rows if r.seqid.num == n)
            side_atoms += [a.pos for a in res if a.name not in ("N", "C", "O")]
        ext = set(block_set)
        for i, res in enumerate(rows, start=1):
            if any(a.pos.dist(p) <= EXT_RADIUS for a in res for p in side_atoms):
                ext.add(i)
        payload = {
            "key": key,
            "name": name,
            "target_pdb_filepath": f"{rel}/pdb/11qc_apical.pdb",
            "target_fasta_filepath": f"{rel}/fasta/11qc_apical.fasta",
            "target_msa_filepath": f"{rel}/msa/11qc_apical.a3m",
            "target_pdb_filepath_by_chain": [f"{rel}/pdb/11qc_apical-chain_B.pdb"],
            "target_fasta_filepath_by_chain": [f"{rel}/fasta/11qc_apical-chain_B.fasta"],
            "target_msa_filepath_by_chain": [f"{rel}/msa/11qc_apical-chain_B.a3m"],
            "target_chain_and_residues": [f"B1-{len(rows)}"],
            "target_interface_residues": {
                "hotspot": [f"B{n}" for n in block_set],
                "extended": [f"B{n}" for n in sorted(ext)],
                "common": [f"B{n}" for n in sorted(ext)],
            },
            "binder_min_length": BINDER_MIN,
            "binder_max_length": BINDER_MAX,
            "tag": ["ours-tfr1"],
            "pdb_id": "11QC",
            "note": (f"11QC chain A apical block 180-400 (block = auth - 179). "
                     f"{name}: human " +
                     ", ".join(f"{n}{letters[index[n]]}" for n in auth_set) +
                     " (author numbering). Created 2026-10-23 for challenge 04."),
        }
        (BENCH / f"problems/{key}.json").write_text(json.dumps(payload, indent=4) + "\n")
        print(f"  {key}: hotspots {[f'B{n}{letters[n]}' for n in block_set]}, "
              f"extended {len(ext)} residues")

    # ---- genie3 run yamls
    (WORK / "genie3").mkdir(parents=True, exist_ok=True)
    for key in SETS:
        yaml_text = f"""experiment:
  name: {key.replace('_', '-')}
  seed: {SEEDS[key]}

paths:
  rootdir: {WORK}/genie3/runs
  dataset: data/design/binder_design/binderbench

generation:
  dataset:
    source: target
    selections: {key}
    n_sample: 24
  sampler:
    sampler:
      direction_scale: 0.0

evaluation:
  version: binder
  inverse_folding:
    num_seq: 1
  folding:
    model_name: colabfold
    mode: template
"""
        (WORK / f"genie3/{key}.yaml").write_text(yaml_text)
    print("wrote 4 run yamls into", WORK / "genie3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
