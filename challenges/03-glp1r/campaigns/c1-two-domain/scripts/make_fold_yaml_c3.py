#!/usr/bin/env python3
"""Write a Boltz-2 fold YAML for one E1 design: chain A = the design's binder
sequence, chain B = the challenge receptor construct (P43220-1 24-432, 409 aa).

The receptor string is the challenge page's sequence, byte-for-byte (the C2
"chain constant" rule: the constant is asserted here so it cannot drift).

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/make_fold_yaml_c3.py \
        --design <design.cif.gz> --out <name>.yaml
"""
from __future__ import annotations

import argparse
import gzip
import pathlib

from Bio.PDB import MMCIFParser
from Bio.Data.PDBData import protein_letters_3to1_extended as T31

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


# human GLP1R P43220-1, residues 24-432 (the challenge segment; assay construct
# is 13944-H18H-DD with undisclosed thermostabilising mutations)
RECEPTOR = ("RPQGATVSLWETVQKWREYRRQCQRSLTEDPPPATDLFCNRTFDEYACWPDGEPGSFVNVSCPWYLPWASSVPQGHVYRFCTAEGLWL"
            "QKDNSSLPWRDLSECEESKRGERSSPEEQLLFLYIIYTVGYALSFSALVIASAILLGFRHLHCTRNYIHLNLFASFILRALSVFIKD"
            "AALKWMYSTAAQQHQWDGLLSYQDSLSCRLVFLLMQYCVAANYYWLLVEGVYLYTLLAFSVLSEQWIFRLYVSIGWGVPLLFVVPW"
            "GIVKYLYEDEGCWTRNSNMNYWLIIRLPILFAIGVNFLIFVRVICIVVSKLKANLMCKTDIKCRLAKSTLTLIPLLGTHEVIFAFV"
            "MDEHARGTLRFIKLFTELSFTSFQGLMVAILYCFVNNEVQLEFRKSWERWRLEHLHIQRDSS")
assert len(RECEPTOR) == 409, len(RECEPTOR)


def binder_sequence(path: pathlib.Path) -> str:
    tmp = pathlib.Path.home() / "c3-work/_tmp_yaml.cif"
    with gzip.open(path, "rt") as fh:
        tmp.write_text(fh.read())
    st = MMCIFParser(QUIET=True).get_structure("m", str(tmp))[0]
    chain = st["A"]
    return "".join(T31.get(r.resname, "X") for r in chain if r.id[0] == " ")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    seq = binder_sequence(pathlib.Path(args.design))
    assert 10 <= len(seq) <= 250, len(seq)
    msa_dir = (_repo_root() / "challenges/03-glp1r/inputs/msa")
    receptor_msa = next(msa_dir.glob("receptor-*-d1024.a3m"), None)
    if receptor_msa is None:
        raise SystemExit("receptor MSA not found; run working/fetch_msas.py first")
    text = (
        "version: 1\n"
        "sequences:\n"
        "  - protein:\n"
        "      id: A\n"
        f"      sequence: {seq}\n"
        "      msa: empty\n"
        "  - protein:\n"
        "      id: B\n"
        f"      sequence: {RECEPTOR}\n"
        f"      msa: {receptor_msa}\n"
    )
    pathlib.Path(args.out).write_text(text)
    print(f"{args.out}: binder {len(seq)} aa (msa empty) + receptor {len(RECEPTOR)} aa "
          f"(msa {receptor_msa.name})")


if __name__ == "__main__":
    main()
