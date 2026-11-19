#!/usr/bin/env python3
"""Build an RFD4-Proteina NIM request for the TfR1 challenge (challenge 04).

Turns the 11QC ectodomain (chain A) into an *annotated CIF* in the format the
hosted NIM expects, then wraps it in a request JSON.

The annotation columns (semantics read off the toolkit's PD-1 example,
nim-skills/rfd4-proteina-nim/assets/requests/16_ppi_binder.json):

  annotation_src-component_1_atom   per-residue source id, "A<resnum>"
  mask_coordinate_1_atom            True  -> coordinates are fixed (the target)
  mask_sequence_1_residue           True  -> sequence is fixed (the target)
  mask_hotspot_1_atom               True  -> epitope atom the binder must contact
  mask_expsegmin/max_1_residue      True  -> residue belongs to an expandable segment
  annotation_expsegmin/max_1_residue  the binder length bounds (target rows: -1)
  condition_index-group_1_token     0 = target, 1 = binder
  atom_array_index                  running atom index

The binder is a single placeholder atom (X / UNK, NaN coordinates) whose
label_comp_id carries the length range; the model materialises the segment.

Outputs (in this directory):
  target_11QC_annotated.cif   the annotated target + binder placeholder
  request_tfr1.json           the NIM request envelope

Usage:
  ../../.venv/bin/python build_request.py [--min-len 70] [--max-len 120]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import gemmi

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / "challenges/04-tfr1/inputs/11QC.cif"

TARGET_CHAIN = "A"
TARGET_NAME = "TfR1 ectodomain 11QC chain A"

# The four epitope sets (author numbering, 11QC chain A). The binder must
# contact the marked side-chain atoms.
#   E0  the organizers' named tip (human-specific)
#   E1  north loop + 374 K (conserved)
#   E2  south ledge (conserved)
#   E12 dual anchor {344 K, 374 K} (conserved; the campaign-1 review proposal)
#   E3  triple cation {231 K, 344 K, 374 K}; CA span 14.8 A (inside the 15 A
#       feasibility line). Caveat: the N251 glycan sits 7.7 A from 231 K NZ and
#       is NOT carried in the request CIF (polymer-only) - E3 outputs get a
#       glycan-distance screen before folding (2026-10-26).
SETS = {
    "E0": (204, 208, 210, 211, 348, 371),
    "E1": (206, 207, 209, 374),
    "E2": (343, 344, 347, 350, 351),
    "E12": (344, 374),
    "E3": (231, 344, 374),
    # H = hybrid: the VP1u-tip residues (R208, Y211) plus the two cations
    # (K344/K374); four residues, tests whether the published-design patch and
    # the dual anchor can be engaged by one binder (2026-10-27 wave).
    "H": (208, 211, 344, 374),
}

# atom_site columns, in the example's order
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
]


def three_to_one(name: str) -> str:
    table = {
        "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
        "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
        "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
        "TYR": "Y", "VAL": "V",
    }
    return table.get(name, "X")


def row(values: dict) -> str:
    return " ".join(str(values[c]) for c in COLS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=sorted(SETS), default="E0",
                    help="epitope set to mark as hotspots (default E0)")
    ap.add_argument("--min-len", type=int, default=60)
    ap.add_argument("--max-len", type=int, default=110)
    ap.add_argument("--tag", default="",
                    help="filename tag, e.g. L for the long-length sweep")
    ap.add_argument("--strategy", default="thinking_medium",
                    help="sampling.recycle_strategy (enum validated by the server)")
    ap.add_argument("--replicates", type=int, default=1,
                    help="sampling.num_replicates (one HTTP call, one random stream)")
    args = ap.parse_args()
    APICAL_PATCH = SETS[args.set]

    st = gemmi.read_structure(str(SOURCE))
    model = st[0]
    chain = model[TARGET_CHAIN]

    residues = [r for r in chain if r.entity_type == gemmi.EntityType.Polymer]
    if not residues:
        print(f"no polymer residues in chain {TARGET_CHAIN}", file=sys.stderr)
        return 1
    present = {r.seqid.num for r in residues}
    missing = [n for n in APICAL_PATCH if n not in present]
    if missing:
        print(f"WARNING: apical residues not found in numbering: {missing}", file=sys.stderr)

    lines: list[str] = []
    seq_parts: list[str] = []
    atom_index = 0

    # ---- target atoms (fixed coordinates, fixed sequence, hotspots on the patch)
    for res in residues:
        resnum = res.seqid.num
        src_id = f"A{resnum}"
        hotspot_res = resnum in APICAL_PATCH
        seq_parts.append(three_to_one(res.name))
        for atom in res:
            if atom.element.name == "H":
                continue
            # hotspot = side-chain atoms of the epitope (the interaction surface)
            side_chain = atom.name not in ("N", "CA", "C", "O")
            lines.append(row({
                "group_PDB": "ATOM",
                "type_symbol": atom.element.name,
                "label_atom_id": atom.name,
                "label_alt_id": ".",
                "label_comp_id": res.name,
                "label_asym_id": TARGET_CHAIN,
                "label_entity_id": 0,
                "label_seq_id": resnum,
                "pdbx_PDB_ins_code": ".",
                "auth_seq_id": resnum,
                "auth_comp_id": res.name,
                "auth_asym_id": TARGET_CHAIN,
                "auth_atom_id": atom.name,
                "B_iso_or_equiv": round(atom.b_iso, 2),
                "occupancy": 1.0,
                "pdbx_formal_charge": "?",
                "annotation_expsegmax_1_residue": -1,
                "mask_index_1_residue": True,
                "mask_expsegmax_1_residue": False,
                "mask_hotspot_1_atom": bool(hotspot_res and side_chain),
                "mask_sequence_1_residue": True,
                "condition_hbond_1_atom": 0,
                "condition_index-group_1_token": 0,
                "annotation_expsegmin_1_residue": -1,
                "mask_expsegmin_1_residue": False,
                "mask_coordinate_1_atom": True,
                "annotation_src-component_1_atom": src_id,
                "atom_array_index": atom_index,
                "Cartn_x": round(atom.pos.x, 3),
                "Cartn_y": round(atom.pos.y, 3),
                "Cartn_z": round(atom.pos.z, 3),
                "pdbx_PDB_model_num": 1,
                "id": atom_index + 1,
            }))
            atom_index += 1

    # ---- binder placeholder: one X atom, NaN coordinates, length range in the label
    length_label = f"{args.min_len}-{args.max_len}"
    lines.append(row({
        "group_PDB": "HETATM",
        "type_symbol": "X",
        "label_atom_id": "UNK",
        "label_alt_id": ".",
        "label_comp_id": length_label,
        "label_asym_id": "B",
        "label_entity_id": 1,
        "label_seq_id": 1,
        "pdbx_PDB_ins_code": ".",
        "auth_seq_id": 1,
        "auth_comp_id": length_label,
        "auth_asym_id": "B",
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

    target_seq = "".join(seq_parts)
    header = f"""data_01_TfR1.cif
#
_entry.id       01_TfR1.cif
_entry.author   protein-design-poc
#
loop_
_entity.id
_entity.type
_entity.pdbx_description
0 polymer "{TARGET_NAME}"
1 polymer "de novo binder (expandable segment)"
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
0 polypeptide(L) no no
;{target_seq}
;
;{target_seq}
;
 {TARGET_CHAIN} ?
1 polypeptide(L) no yes X
X
 B ?
#
loop_"""

    body = "\n".join(f"_atom_site.{c}" for c in COLS)
    cif = header + "\n" + body + "\n" + "\n".join(lines) + "\n#\n"

    cif_path = HERE / f"target_11QC_{args.set}{args.tag}_annotated.cif"
    cif_path.write_text(cif)

    payload = {
        "task": "generation",
        "input": {
            "format": "annotated_cif",
            "file": {"filename": cif_path.name, "content": cif},
        },
        "sampling": {"recycle_strategy": args.strategy, "num_replicates": args.replicates},
        # Only tags from the server enum are accepted; the challenge name lives
        # in the run folder and notes, not in a metric tag (HTTP 422 otherwise).
        "metrics": {"tags": ["design", "hotspot_conditioning"]},
        "output": {"structure_format": "mmcif", "include_sequence": True},
    }
    suffix = "" if args.replicates == 1 else f"_r{args.replicates}"
    req_path = HERE / f"request_tfr1_{args.set}{args.tag}{suffix}.json"
    req_path.write_text(json.dumps(payload, indent=2) + "\n")

    hotspot_atoms = sum(1 for l in lines if " True " in f" {l.split()[COLS.index('mask_hotspot_1_atom')]} ")
    letters = {r.seqid.num: three_to_one(r.name) for r in residues}
    marked = ", ".join(f"{n}{letters.get(n, '?')}" for n in APICAL_PATCH)
    print(f"target: {TARGET_NAME}, {len(residues)} residues, {atom_index} heavy atoms")
    print(f"set {args.set}: hot spots {marked}")
    print(f"hotspot atoms marked: {hotspot_atoms} across {len(APICAL_PATCH) - len(missing)} epitope residues")
    print(f"binder: expandable segment {args.min_len}-{args.max_len}")
    print(f"wrote {cif_path.relative_to(REPO)}  ({cif_path.stat().st_size / 1024:.0f} KB)")
    print(f"wrote {req_path.relative_to(REPO)}  ({req_path.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
