#!/usr/bin/env python3
"""Collect the mutant-complex fold of each submitted design for OpenDDE scoring.

For each of the 20 submitted designs, find the exact fold directory (the yaml
named after the design, i.e. the mutant-complex fold, not a combo child or a
tri-state arm) and copy its model_0.cif into one directory.
"""
import pathlib
import shutil

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


FASTA = _repo_root() / "challenges/05-pmhc/records/final2/submission-top20.fasta"
OUT = pathlib.Path.home() / "c5-work/opendde-20/cifs"
OUT.mkdir(parents=True, exist_ok=True)

names = [l[1:].strip() for l in FASTA.read_text().splitlines()[0::2]]

found, missing = [], []
for n in names:
    # exact yaml name == design name
    cands = sorted(pathlib.Path.home() / "c5-work".glob(f"**/folds/{n}.yaml"))
    # prefer the evolving generations (the design's own era), take the newest
    cif = None
    for c in sorted(cands, reverse=True):
        d = c.parent / n
        hits = sorted(d.glob("boltz_results_*/predictions/*/*_model_0.cif"))
        if hits:
            cif = hits[0]
            break
    if cif:
        dest = OUT / f"{n}.cif"
        shutil.copy(cif, dest)
        found.append(n)
        print(f"OK   {n[:60]}  <- {cif}")
    else:
        # fall back: any boltz fold whose directory name starts with the design name
        hits = sorted(pathlib.Path.home() / "c5-work".glob(
            f"**/{n}/boltz_results_*/predictions/*/{n}_model_0.cif"))
        if hits:
            shutil.copy(hits[0], OUT / f"{n}.cif")
            found.append(n)
            print(f"OK*  {n[:60]}  <- {hits[0]}")
        else:
            missing.append(n)
            print(f"MISS {n}")

print(f"\ncollected {len(found)}/20, missing: {missing}")
