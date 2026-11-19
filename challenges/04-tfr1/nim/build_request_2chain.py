#!/usr/bin/env python3
"""Build a TWO-chain RFD4-Proteina NIM request (multi-chain binder experiment).

Same annotated-CIF format as build_request.py; adds a second expandable
segment: chain B (entity 1, condition group 1) and chain C (entity 2,
condition group 2), each with its own length range. Both segments see the
same hotspot set, so the model decides how to split the patch between them.

Usage:
  ../../.venv/bin/python build_request_2chain.py --set E12 \
      --min-len1 50 --max-len1 80 --min-len2 50 --max-len2 80 --replicates 8
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import gemmi

import build_request as br

HERE = Path(__file__).resolve().parent


def placeholder(atom_index, chain, entity, group, lo, hi):
    label = f"{lo}-{hi}"
    return br.row({
        "group_PDB": "HETATM",
        "type_symbol": "X",
        "label_atom_id": "UNK",
        "label_alt_id": ".",
        "label_comp_id": label,
        "label_asym_id": chain,
        "label_entity_id": entity,
        "label_seq_id": 1,
        "pdbx_PDB_ins_code": ".",
        "auth_seq_id": 1,
        "auth_comp_id": label,
        "auth_asym_id": chain,
        "auth_atom_id": "UNK",
        "B_iso_or_equiv": "nan",
        "occupancy": 0.0,
        "pdbx_formal_charge": "?",
        "annotation_expsegmax_1_residue": hi,
        "mask_index_1_residue": True,
        "mask_expsegmax_1_residue": True,
        "mask_hotspot_1_atom": False,
        "mask_sequence_1_residue": False,
        "condition_hbond_1_atom": 0,
        "condition_index-group_1_token": group,
        "annotation_expsegmin_1_residue": lo,
        "mask_expsegmin_1_residue": True,
        "mask_coordinate_1_atom": False,
        "annotation_src-component_1_atom": ".",
        "atom_array_index": 0,
        "Cartn_x": "nan",
        "Cartn_y": "nan",
        "Cartn_z": "nan",
        "pdbx_PDB_model_num": 1,
        "id": atom_index + 1,
    })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=sorted(br.SETS), default="E12")
    ap.add_argument("--min-len1", type=int, default=50)
    ap.add_argument("--max-len1", type=int, default=80)
    ap.add_argument("--min-len2", type=int, default=50)
    ap.add_argument("--max-len2", type=int, default=80)
    ap.add_argument("--replicates", type=int, default=8)
    args = ap.parse_args()
    patch = br.SETS[args.set]

    st = gemmi.read_structure(str(br.SOURCE))
    chain = st[0][br.TARGET_CHAIN]
    residues = [r for r in chain if r.entity_type == gemmi.EntityType.Polymer]

    lines: list[str] = []
    seq_parts: list[str] = []
    atom_index = 0
    for res in residues:
        resnum = res.seqid.num
        hot = resnum in patch
        seq_parts.append(br.three_to_one(res.name))
        for atom in res:
            if atom.element.name == "H":
                continue
            side_chain = atom.name not in ("N", "CA", "C", "O")
            lines.append(br.row({
                "group_PDB": "ATOM",
                "type_symbol": atom.element.name,
                "label_atom_id": atom.name,
                "label_alt_id": ".",
                "label_comp_id": res.name,
                "label_asym_id": br.TARGET_CHAIN,
                "label_entity_id": 0,
                "label_seq_id": resnum,
                "pdbx_PDB_ins_code": ".",
                "auth_seq_id": resnum,
                "auth_comp_id": res.name,
                "auth_asym_id": br.TARGET_CHAIN,
                "auth_atom_id": atom.name,
                "B_iso_or_equiv": round(atom.b_iso, 2),
                "occupancy": 1.0,
                "pdbx_formal_charge": "?",
                "annotation_expsegmax_1_residue": -1,
                "mask_index_1_residue": True,
                "mask_expsegmax_1_residue": False,
                "mask_hotspot_1_atom": bool(hot and side_chain),
                "mask_sequence_1_residue": True,
                "condition_hbond_1_atom": 0,
                "condition_index-group_1_token": 0,
                "annotation_expsegmin_1_residue": -1,
                "mask_expsegmin_1_residue": False,
                "mask_coordinate_1_atom": True,
                "annotation_src-component_1_atom": f"A{resnum}",
                "atom_array_index": atom_index,
                "Cartn_x": round(atom.pos.x, 3),
                "Cartn_y": round(atom.pos.y, 3),
                "Cartn_z": round(atom.pos.z, 3),
                "pdbx_PDB_model_num": 1,
                "id": atom_index + 1,
            }))
            atom_index += 1

    lines.append(placeholder(atom_index, "B", 1, 1, args.min_len1, args.max_len1))
    atom_index += 1
    lines.append(placeholder(atom_index, "C", 2, 2, args.min_len2, args.max_len2))

    target_seq = "".join(seq_parts)
    header = f"""data_01_TfR1_2ch.cif
#
_entry.id       01_TfR1_2ch.cif
_entry.author   protein-design-poc
#
loop_
_entity.id
_entity.type
_entity.pdbx_description
0 polymer "{br.TARGET_NAME}"
1 polymer "de novo binder chain B (expandable segment)"
2 polymer "de novo binder chain C (expandable segment)"
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
 {br.TARGET_CHAIN} ?
1 polypeptide(L) no yes X
X
 B ?
2 polypeptide(L) no yes X
X
 C ?
#
loop_"""

    body = "\n".join(f"_atom_site.{c}" for c in br.COLS)
    cif = header + "\n" + body + "\n" + "\n".join(lines) + "\n#\n"

    cif_path = HERE / f"target_11QC_{args.set}_2ch_annotated.cif"
    cif_path.write_text(cif)

    payload = {
        "task": "generation",
        "input": {
            "format": "annotated_cif",
            "file": {"filename": cif_path.name, "content": cif},
        },
        "sampling": {"recycle_strategy": "thinking_medium", "num_replicates": args.replicates},
        "metrics": {"tags": ["design", "hotspot_conditioning"]},
        "output": {"structure_format": "mmcif", "include_sequence": True},
    }
    req_path = HERE / f"request_tfr1_{args.set}_2ch.json"
    req_path.write_text(json.dumps(payload, separators=(",", ":")))

    print(f"target: {br.TARGET_NAME}, {len(residues)} residues, {atom_index + 1} heavy atoms + 2 placeholders")
    print(f"set {args.set}: hot spots {patch}")
    print(f"segments: B {args.min_len1}-{args.max_len1}, C {args.min_len2}-{args.max_len2}, "
          f"replicates {args.replicates}")
    print(f"wrote {cif_path.name}  ({cif_path.stat().st_size / 1024:.0f} KB)")
    print(f"wrote {req_path.name}  ({req_path.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
