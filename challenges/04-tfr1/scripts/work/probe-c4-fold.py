#!/usr/bin/env python3
"""Build the C4 fold-memory probe: a real-length binder vs the 639-res protomer.

Picks the C2 binder sequence closest to 100 aa, takes the human protomer
sequence (11QC chain A, 122-760) and the prefetched depth-capped MSA, and
writes ~/c4-work/folds/probe-100aa.yaml.

Run: .venv/bin/python probe-c4-fold.py (from the repo root)
"""
from __future__ import annotations

import hashlib
import pathlib
import re

HOME = pathlib.Path.home()
WORK = HOME / "c4-work"
C2F = HOME / "c2-work/genie3/folds"
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


MSA_DIR = _repo_root() / "challenges/04-tfr1/inputs/msa"
TARGETS = WORK / "targets"


def binder_seqs():
    out = []
    for yaml in sorted(C2F.glob("*.yaml")):
        text = yaml.read_text()
        m = re.search(r"id: A\s*\n\s*sequence: (\S+)", text)
        if m:
            out.append((len(m.group(1)), m.group(1), yaml.name))
    return out


def msa_for(seq: str) -> str:
    tag = hashlib.sha1(seq.encode()).hexdigest()[:12]
    hits = list(MSA_DIR.glob(f"{tag}-d*.a3m"))
    if not hits:
        raise SystemExit(f"no MSA for sequence hash {tag}; run fetch_msas.py first")
    return str(hits[0])


def main() -> int:
    target_seq = "".join((TARGETS / "human_full.fa").read_text().splitlines()[1:])
    seqs = binder_seqs()
    if not seqs:
        raise SystemExit("no C2 binder yamls found")
    seqs.sort(key=lambda t: abs(t[0] - 100))
    length, binder, source = seqs[0]
    print(f"probe binder {length} aa from {source}")
    yaml = WORK / "folds/probe-100aa.yaml"
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
        f"      msa: {msa_for(target_seq)}\n")
    print(f"wrote {yaml} (receptor {len(target_seq)} aa, msa {msa_for(target_seq)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
