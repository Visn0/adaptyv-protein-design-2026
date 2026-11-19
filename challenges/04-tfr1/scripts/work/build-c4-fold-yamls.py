#!/usr/bin/env python3
"""Build Boltz-2 fold yamls for the passing C1 designs (binder + one receptor).

--target full  : receptor = 11QC chain A, 639 aa  (fold numbering = auth - 121)
--target block : receptor = apical block 180-400  (fold numbering = auth - 179)

Binder MSA is `empty`; the receptor MSA is the prefetched depth-capped a3m,
looked up by sha1(seq)[:12] exactly as fetch_msas.py names it.

Run: .venv/bin/python build-c4-fold-yamls.py --target full (from the repo root)
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib

HOME = pathlib.Path.home()
WORK = HOME / "c4-work"
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


MSA_DIR = _repo_root() / "challenges/04-tfr1/inputs/msa"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=("full", "block"), required=True)
    args = ap.parse_args()
    fasta = WORK / ("targets/human_full.fa" if args.target == "full" else "targets/block.fa")
    target_seq = "".join(fasta.read_text().splitlines()[1:])
    tag = hashlib.sha1(target_seq.encode()).hexdigest()[:12]
    hits = list(MSA_DIR.glob(f"{tag}-d*.a3m"))
    if not hits:
        raise SystemExit(f"no MSA for {fasta.name} (hash {tag})")
    msa = hits[0]
    print(f"receptor {args.target}: {len(target_seq)} aa, msa {msa.name}")

    designs = [d.strip() for d in (WORK / "state/pass-gen.txt").read_text().split() if d.strip()]
    made, skipped = 0, []
    for design in designs:
        seqfile = WORK / f"seqs/{design}.fa"
        if not seqfile.exists():
            skipped.append(design)
            continue
        binder = "".join(seqfile.read_text().splitlines()[1:])
        yaml = WORK / f"folds/{design}.yaml"
        if yaml.exists():
            continue
        yaml.write_text(
            "version: 1\n"
            "sequences:\n"
            "  - protein:\n"
            "      id: A\n"
            f"      sequence: {binder}\n"
            "      msa: empty\n"
            "  - protein:\n"
            "      id: B\n"
            f"      sequence: {target_seq}\n"
            f"      msa: {msa}\n")
        made += 1
    print(f"wrote {made} fold yamls ({len(designs)} passing, {len(skipped)} without a sequence)")
    if skipped:
        print("without sequence:", ",".join(skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
