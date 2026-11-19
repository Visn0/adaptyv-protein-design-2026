#!/usr/bin/env python3
"""Prep the validation inputs for the three v4 swaps (seeds + chai + apo)."""

from __future__ import annotations

import pathlib
import shutil

import yaml

HOME = pathlib.Path.home()
W = HOME / "c5-work"
V = W / "v4-val"
SRC_S3 = W / "s3/designs"
VARIANTS = {
    "a58k": "repair-wave4-pep__run-007__design_0002__g12d-A58K",
    "h27k": "repair-nat-wave1__run-011__design_0000__g12d-H27K",
    "n71k": "repair-nat-wave1__run-011__design_0004__g12d-N71K",
}

(V / "folds").mkdir(parents=True, exist_ok=True)
(V / "apo").mkdir(parents=True, exist_ok=True)

# a chai msa_pqt donor (same HLA + b2m sequences in every design)
donor = sorted(SRC_S3.glob("*/msa_pqt"))[0]

for short, name in VARIANTS.items():
    src = W / "repair2/folds" / f"{name}.yaml"
    text = src.read_text()
    for s in (0, 1, 2):
        (V / "folds" / f"{short}__s{s}.yaml").write_text(text)
    # apo: binder only
    d = yaml.safe_load(text)
    bseq = [x for x in d["sequences"] if x["protein"]["id"] == "D"][0]["protein"]["sequence"]
    apo = {"version": 1, "sequences": [{"protein": {"id": "D", "sequence": bseq, "msa": "empty"}}]}
    (V / "apo" / f"{short}-apo.yaml").write_text(yaml.safe_dump(apo, sort_keys=False))
    # chai inputs
    dest = V / "designs" / short
    (dest / "msa_pqt").mkdir(parents=True, exist_ok=True)
    seqs = {x["protein"]["id"]: x["protein"]["sequence"] for x in d["sequences"]}
    with (dest / "in.fasta").open("w") as fh:
        for cid in ("A", "B", "C", "D"):
            fh.write(f">protein|{cid}\n{seqs[cid]}\n")
    for pqt in donor.glob("*.pqt"):
        shutil.copy(pqt, dest / "msa_pqt" / pqt.name)
    print(f"{short}: seeds 0-2, apo, chai inputs ready")
print("done")
