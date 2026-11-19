#!/usr/bin/env python3
"""Build a truncated-complex dataset for 12 GB fine-tuning.

Full complexes are 449 residues (~620 tokens) and their training activations
do not fit a 12 GB card. The RFD4 forward pass reads the target grooves
locally; this script keeps the HLA alpha-1/alpha-2 domain plus the floor
(residues 1-180, which carries both helices flanking the peptide), the full
beta-2-microglobulin, the peptide, and the designed binder. Complexes drop
to ~360 residues, roughly halving the attention memory.

Input:  ~/c5-work/lora-data-v0/*.cif   (full annotated complexes)
Output: ~/c5-work/lora-data-trunc/*.cif
"""
import pathlib

import gemmi

SRC = pathlib.Path.home() / "c5-work/lora-data-v0"
DST = pathlib.Path.home() / "c5-work/lora-data-trunc"
DST.mkdir(parents=True, exist_ok=True)

KEEP = {
    "A": (1, 200),    # HLA heavy chain: alpha1+alpha2 keep the peptide groove
    "B": (1, 999),    # beta-2-microglobulin: keep complete
    "C": (1, 999),    # peptide
    "D": (1, 999),    # binder
}


def trim(st):
    out = gemmi.Structure()
    out_model = gemmi.Model("1")
    for ch in st[0]:
        lo, hi = KEEP.get(ch.name, (1, 999))
        newch = gemmi.Chain(ch.name)
        for res in ch:
            if lo <= res.seqid.num <= hi:
                newch.add_residue(res)
        if len(newch):
            out_model.add_chain(newch)
    out.add_model(out_model)
    return out


def main():
    n = 0
    for src in sorted(SRC.glob("*.cif")):
        st = gemmi.read_structure(str(src))
        out = trim(st)
        dest = DST / src.name
        out.make_mmcif_document().write_file(str(dest))
        sizes = [len(ch) for ch in out[0]]
        n += 1
        print(f"{src.name}: chains {sizes} total {sum(sizes)}")
    print(f"\nwrote {n} truncated complexes to {DST}")


if __name__ == "__main__":
    main()
