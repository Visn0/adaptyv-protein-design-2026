#!/usr/bin/env python3
"""Campaign 3, gate 2 input prep: convert the chosen poses to PDB (no H) and
run the vendored linkage scorer over every variant plus every parent.

Best at-site model per item comes from c3-restrained-scores.py (variants) and
the same rule on c2-restrained.csv (parents). Output: ~/c4-work/logs/c3-linkage.csv
plus the intermediate PDBs under ~/c4-work/chai/c3/pdb/.
Run with the repo venv python (Bio + propka)."""
from __future__ import annotations

import csv
import json
import pathlib
import statistics
import subprocess
import sys

WORK = pathlib.Path.home() / 'c4-work'
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
DESIGNS = WORK / 'chai/designs'
PDBDIR = WORK / 'chai/c3/pdb'


def strip_and_write(cif, out_pdb):
    from Bio.PDB import MMCIFParser, PDBIO
    st = MMCIFParser(QUIET=True).get_structure('x', str(cif))
    for chain in st[0]:
        for res in chain:
            for atom in [a for a in res if a.element == 'H']:
                res.detach(atom)
    io = PDBIO()
    io.set_structure(st)
    io.save(str(out_pdb))


def best_variant_models():
    return {k: v[0] for k, v in json.loads(
        (WORK / 'chai/c3/best-models.json').read_text()).items()}


def best_parent_models():
    per = {}
    with open(WORK / 'logs/c2-restrained.csv') as fh:
        for r in csv.DictReader(fh):
            per.setdefault(r['design'], []).append(r)
    out = {}
    for design, rs in per.items():
        at = [r for r in rs if int(r['binder_res_at_site'] or 0) > 0]
        best = max(at or rs, key=lambda r: float(r['iptm']))
        out[design] = int(best['model'])
    return out


def main():
    PDBDIR.mkdir(parents=True, exist_ok=True)
    items = {}
    for name, idx in best_variant_models().items():
        items[name] = DESIGNS / name / 'out' / f'pred.model_idx_{idx}.cif'
    for name, idx in best_parent_models().items():
        cif = DESIGNS / name / 'out' / f'pred.model_idx_{idx}.cif'
        if cif.exists():
            items[name] = cif
    done = 0
    for name, cif in sorted(items.items()):
        out = PDBDIR / f'{name}.pdb'
        if out.exists():
            done += 1
            continue
        if not cif.exists():
            print(f'MISSING pose for {name}: {cif}')
            continue
        strip_and_write(cif, out)
        done += 1
    print(f'PDBs ready: {done}/{len(items)} -> {PDBDIR}')
    rc = subprocess.run(
        [sys.executable, str(REPO / 'tools/switch/linkage_score.py'),
         '--complexes', str(PDBDIR / '*.pdb'),
         '--binder-chain', 'B', '--target-chains', 'A',
         '--out', str(WORK / 'logs/c3-linkage.csv')],
        check=False)
    sys.exit(rc.returncode)


if __name__ == '__main__':
    main()
