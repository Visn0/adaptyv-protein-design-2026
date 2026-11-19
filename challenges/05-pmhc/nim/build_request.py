#!/usr/bin/env python3
"""Build an RFD4-Proteina NIM request for the C5 KRAS G12D pMHC challenge.

Target: the organizer G12D file (chains A = HLA-A*11:01 heavy chain 1-276,
B = beta2-microglobulin, C = peptide VVVGADGVGK). Binder = chain D,
expandable segment (default 60-110 aa).

Hotspot policy (the measured physics, not the default convention):
the JDI TCR reads the accessible ridge of the peptide — its heaviest contact
is P7 *backbone* (32 contacts), and Asp6's carboxylate is ~90% buried and
salt-bridged to HLA R114 (no binder can touch it). So the hotspot set marks
the accessible atoms of P4-P8 — CA plus non-buried sidechain atoms — and
EXCLUDES the Asp6 CG/OD1/OD2 (conditioning a generator onto a buried
carboxylate invites strained poses; the mutation is read as a field, not a
contact).

Sets:
  PEP     P4-P8 accessible ridge atoms (default)
  PEPRIM  PEP plus the JDI-adjacent groove-rim sidechains on chain A
          (R65, A69, T73, Q155)

Outputs (in this directory):
  target_pmhc_<set>_annotated.cif   annotated target + binder placeholder
  request_pmhc_<set>[_r<N>].json    the NIM request envelope

Usage:
  ../../.venv/bin/python build_request.py --set PEP --replicates 8
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import gemmi

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / "challenges/05-pmhc/inputs/7OW6-G12D-noTCR.pdb"

TARGET_CHAINS = {"A": "HLA-A*11:01 heavy chain (25-305, renumbered 1-276)",
                 "B": "beta2-microglobulin",
                 "C": "KRAS G12D peptide VVVGADGVGK"}
BINDER_CHAIN = "D"

# accessible ridge atoms per peptide position (non-H); backbone N/C/O excluded,
# CA included (Gly positions have no sidechain; the native read is backbone)
PEP_RIDGE = {4: ["CA"], 5: ["CA", "CB"], 6: ["CA", "CB"], 7: ["CA"],
             8: ["CA", "CB", "CG1", "CG2"]}
# groove-rim sidechains on chain A (JDI footprint residues)
RIM_A = {65: ["CA", "CB", "CG", "CD", "NE", "CZ", "NH1", "NH2"],
         69: ["CA", "CB"],
         73: ["CA", "CB", "OG1", "CG2"],
         155: ["CA", "CB", "CG", "CD", "OE1", "NE2"]}
# charge-first: crowd the mutation neighbourhood only (P5-P7 ridge)
PEP_TIGHT = {5: ["CA", "CB"], 6: ["CA", "CB"], 7: ["CA", "CB"]}
# natural reader: the exact peptide atoms the JDI TCR touches in 7OW6
# (measured: <4.5 A; backbone-dominated - P7 backbone is the anchor, P6 is
# read via its carbonyl, not the mutant sidechain)
PEP_NATURAL = {4: ["CA"], 5: ["CB", "O"], 6: ["C", "O"],
               7: ["N", "CA", "C", "O"],
               8: ["N", "CA", "C", "CB", "CG1", "CG2"], 9: ["N", "CA"]}

COLS = [
    "group_PDB", "type_symbol", "label_atom_id", "label_alt_id", "label_comp_id",
    "label_asym_id", "label_entity_id", "label_seq_id", "pdbx_PDB_ins_code",
    "auth_seq_id", "auth_comp_id", "auth_asym_id", "auth_atom_id", "B_iso_or_equiv",
    "occupancy", "pdbx_formal_charge",
    "annotation_expsegmax_1_residue", "mask_index_1_residue", "mask_expsegmax_1_residue",
    "mask_hotspot_1_atom", "mask_sequence_1_residue", "condition_hbond_1_atom",
    "condition_index-group_1_token", "annotation_expsegmin_1_residue",
    "mask_expsegmin_1_residue", "mask_coordinate_1_atom",
    "annotation_src-component_1_atom", "atom_array_index",
    "Cartn_x", "Cartn_y", "Cartn_z", "pdbx_PDB_model_num", "id",
    "condition_saltbridge_1_atom",
]

# SALT campaign: per-atom interaction conditions on the mutant carboxylate.
# hbond 2 = ACCEPTOR, saltbridge 2 = NEGATIVE partner (see rfproteina
# conditions.py: HBondEnum/SaltBridgeEnum, both 1-body ATOM level).
SALT_MARKS = {("C", 6, "OD1"): (2, 2), ("C", 6, "OD2"): (2, 2)}


AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}


def row(values: dict) -> str:
    return " ".join(str(values[c]) for c in COLS)


def hotspot_atoms(set_name: str):
    """(chain, resnum, atom_name) -> True for atoms that are hotspots."""
    marks = set()
    ridge = PEP_RIDGE
    if set_name == "TIGHT":
        ridge = PEP_TIGHT
    elif set_name == "NATURAL":
        ridge = PEP_NATURAL
    for pos, atoms in ridge.items():
        for a in atoms:
            marks.add(("C", pos, a))
    if set_name == "PEPRIM":
        for resnum, atoms in RIM_A.items():
            for a in atoms:
                marks.add(("A", resnum, a))
    return marks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=("PEP", "PEPRIM", "TIGHT", "NATURAL",
                                      "MINI", "SALT"), default="PEP")
    ap.add_argument("--min-len", type=int, default=60)
    ap.add_argument("--max-len", type=int, default=110)
    ap.add_argument("--strategy", default="thinking_medium")
    ap.add_argument("--replicates", type=int, default=1)
    args = ap.parse_args()

    st = gemmi.read_structure(str(SOURCE))
    model = st[0]
    marks = hotspot_atoms(args.set)

    lines: list[str] = []
    seqs: dict[str, str] = {}
    atom_index = 0
    entity_of = {chain: i for i, chain in enumerate(TARGET_CHAINS)}
    for chain_id in TARGET_CHAINS:
        chain = model[chain_id]
        residues = [r for r in chain if r.entity_type == gemmi.EntityType.Polymer]
        if not residues:
            print(f"no polymer residues in chain {chain_id}", file=sys.stderr)
            return 1
        seq_parts = []
        for res in residues:
            resnum = res.seqid.num
            seq_parts.append(AA3.get(res.name, "X"))
            for atom in res:
                if atom.element.name == "H":
                    continue
                lines.append(row({
                    "group_PDB": "ATOM",
                    "type_symbol": atom.element.name,
                    "label_atom_id": atom.name,
                    "label_alt_id": ".",
                    "label_comp_id": res.name,
                    "label_asym_id": chain_id,
                    "label_entity_id": entity_of[chain_id],
                    "label_seq_id": resnum,
                    "pdbx_PDB_ins_code": ".",
                    "auth_seq_id": resnum,
                    "auth_comp_id": res.name,
                    "auth_asym_id": chain_id,
                    "auth_atom_id": atom.name,
                    "B_iso_or_equiv": round(atom.b_iso, 2),
                    "occupancy": 1.0,
                    "pdbx_formal_charge": "?",
                    "annotation_expsegmax_1_residue": -1,
                    "mask_index_1_residue": True,
                    "mask_expsegmax_1_residue": False,
                    "mask_hotspot_1_atom": (chain_id, resnum, atom.name) in marks,
                    "mask_sequence_1_residue": True,
                    "condition_hbond_1_atom": SALT_MARKS.get(
                        (chain_id, resnum, atom.name), (0, 0))[0],
                    "condition_index-group_1_token": 0,
                    "condition_saltbridge_1_atom": SALT_MARKS.get(
                        (chain_id, resnum, atom.name), (0, 0))[1],
                    "annotation_expsegmin_1_residue": -1,
                    "mask_expsegmin_1_residue": False,
                    "mask_coordinate_1_atom": True,
                    "annotation_src-component_1_atom": f"{chain_id}{resnum}",
                    "atom_array_index": atom_index,
                    "Cartn_x": round(atom.pos.x, 3),
                    "Cartn_y": round(atom.pos.y, 3),
                    "Cartn_z": round(atom.pos.z, 3),
                    "pdbx_PDB_model_num": 1,
                    "id": atom_index + 1,
                }))
                atom_index += 1
        seqs[chain_id] = "".join(seq_parts)

    # binder placeholder: one X atom, NaN coordinates, length range in the label
    label = f"{args.min_len}-{args.max_len}"
    binder_entity = len(TARGET_CHAINS)
    lines.append(row({
        "group_PDB": "HETATM",
        "type_symbol": "X",
        "label_atom_id": "UNK",
        "label_alt_id": ".",
        "label_comp_id": label,
        "label_asym_id": BINDER_CHAIN,
        "label_entity_id": binder_entity,
        "label_seq_id": 1,
        "pdbx_PDB_ins_code": ".",
        "auth_seq_id": 1,
        "auth_comp_id": label,
        "auth_asym_id": BINDER_CHAIN,
        "auth_atom_id": "UNK",
        "B_iso_or_equiv": "nan",
        "occupancy": 0.0,
        "pdbx_formal_charge": "?",
        "annotation_expsegmax_1_residue": args.max_len,
        "mask_index_1_residue": True,
        "mask_expsegmax_1_residue": True,
        "mask_hotspot_1_atom": False,
        "mask_sequence_1_residue": False,
        "condition_hbond_1_atom": 0,
        "condition_index-group_1_token": 1,
        "condition_saltbridge_1_atom": 0,
        "annotation_expsegmin_1_residue": args.min_len,
        "mask_expsegmin_1_residue": True,
        "mask_coordinate_1_atom": False,
        "annotation_src-component_1_atom": ".",
        "atom_array_index": 0,
        "Cartn_x": "nan",
        "Cartn_y": "nan",
        "Cartn_z": "nan",
        "pdbx_PDB_model_num": 1,
        "id": atom_index + 1,
    }))

    ent_rows = "\n".join(f"{i} polymer \"{desc}\"" for i, desc in
                         enumerate(TARGET_CHAINS.values()))
    poly_rows = "\n".join(
        f"{i} polypeptide(L) no no\n;{seqs[c]}\n;\n;{seqs[c]}\n;\n {c} ?"
        for i, c in enumerate(TARGET_CHAINS))
    header = f"""data_01_C5_pmhc.cif
#
_entry.id       01_C5_pmhc.cif
_entry.author   protein-design-poc
#
loop_
_entity.id
_entity.type
_entity.pdbx_description
{ent_rows}
{binder_entity} polymer "de novo binder (expandable segment)"
#
loop_
_entity_poly.entity_id
_entity_poly.type
_entity_poly.nstd_linkage
_entity_poly.nstd_monomer
_entity_poly.pdbx_seq_one_letter_code
_entity_poly.pdbx_seq_one_letter_code_can
_entity_poly.pdbx_strand_id
_entity_poly.pdbx_target_identifier
{poly_rows}
{binder_entity} polypeptide(L) no yes X
X
 {BINDER_CHAIN} ?
#
loop_"""

    body = "\n".join(f"_atom_site.{c}" for c in COLS)
    cif = header + "\n" + body + "\n" + "\n".join(lines) + "\n#\n"

    cif_path = HERE / f"target_pmhc_{args.set}_annotated.cif"
    cif_path.write_text(cif)

    payload = {
        "task": "generation",
        "input": {
            "format": "annotated_cif",
            "file": {"filename": cif_path.name, "content": cif},
        },
        "sampling": {"recycle_strategy": args.strategy,
                     "num_replicates": args.replicates},
        "metrics": {"tags": ["design", "hotspot_conditioning"]},
        "output": {"structure_format": "mmcif", "include_sequence": True},
    }
    suffix = "" if args.replicates == 1 else f"_r{args.replicates}"
    req_path = HERE / f"request_pmhc_{args.set}{suffix}.json"
    req_path.write_text(json.dumps(payload) + "\n")

    n_hot = sum(1 for l in lines if " True " in f" {l.split()[COLS.index('mask_hotspot_1_atom')]} ")
    print(f"target: 3 chains, {atom_index} heavy atoms; hotspots {n_hot} atoms "
          f"({args.set})")
    print(f"binder: expandable segment {args.min_len}-{args.max_len}, chain {BINDER_CHAIN}")
    print(f"replicates: {args.replicates}, strategy {args.strategy}")
    print(f"wrote {cif_path.relative_to(REPO)} ({cif_path.stat().st_size / 1024:.0f} KB)")
    print(f"wrote {req_path.relative_to(REPO)} ({req_path.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
