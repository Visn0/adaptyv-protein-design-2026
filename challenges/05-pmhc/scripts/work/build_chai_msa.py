#!/usr/bin/env python3
"""Build a chai `msa_pqt` directory for an arm/in.fasta from the repo MSAs.

chai 0.6.1 reads `<sha256(QUERY.upper())>.aligned.pqt` from `--msa-directory`;
plain .a3m files are silently ignored. The repo's a3m cache is named
`<sha1(seq)[:12]>-d<cap>.a3m`, so this script maps each chain's sequence to
its a3m, feeds chai's own converter (one file per chain, via a scratch dir),
and assembles `<out>/<sha256>.aligned.pqt` for every chain that has an MSA.
Chains without an MSA (e.g. the peptide, shuffled sequences) are skipped -
chai falls back to single-sequence for them with a log warning, which is the
normal designed-chain treatment.

Usage:
  ~/.venvs/chai/bin/python build_chai_msa.py \
      --fasta ~/c5-work/c0t/chai/designs/pos-g12d/in.fasta \
      --msa-dir challenges/05-pmhc/inputs/msa \
      --out ~/c5-work/c0t/chai/designs/pos-g12d/msa_pqt
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

CHAI_PY = pathlib.Path.home() / ".venvs/chai/bin/python"


def read_fasta(path: pathlib.Path) -> list[tuple[str, str]]:
    seqs, cur, name = [], [], None
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if name:
                seqs.append((name, "".join(cur)))
            name, cur = line[1:], []
        elif line.strip():
            cur.append(line.strip())
    if name:
        seqs.append((name, "".join(cur)))
    return seqs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fasta", type=pathlib.Path, required=True)
    ap.add_argument("--msa-dir", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    chains = read_fasta(args.fasta)
    made, skipped = 0, []
    for name, seq in chains:
        tag = hashlib.sha1(seq.encode()).hexdigest()[:12]
        hits = sorted(args.msa_dir.glob(f"{tag}-d*.a3m"))
        if not hits:
            skipped.append((name, tag))
            continue
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            shutil.copyfile(hits[0], tmp / "hits_uniref90.a3m")
            subprocess.run([str(CHAI_PY), "-m",
                            "chai_lab.data.parsing.msas.aligned_pqt",
                            str(tmp)],
                           check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            pqts = list(tmp.glob("*.aligned.pqt"))
            if not pqts:
                raise SystemExit(f"converter produced no pqt for {name}")
            shutil.copyfile(pqts[0], args.out / pqts[0].name)
        made += 1
        print(f"{name}: {hits[0].name} -> msa_pqt ({len(seq)} aa)")
    for name, tag in skipped:
        print(f"{name}: no MSA for {tag} (single-sequence fallback)", file=sys.stderr)
    print(f"wrote {made} pqt files under {args.out}")
    return 0 if made else 1


if __name__ == "__main__":
    raise SystemExit(main())
