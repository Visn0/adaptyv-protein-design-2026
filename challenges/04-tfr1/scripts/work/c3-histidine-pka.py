#!/usr/bin/env python3
"""Does the engineered histidine actually register a pKa perturbation?

For each chosen design, re-run PROPKA on bound and free states (same pieces as
linkage_score.py) and report the pKa of every binder-side HIS residue, plus
delta = bound - free. The mechanism predicts a NEGATIVE delta (the anchor
cation destabilises the protonated form when bound). Totals in c3-linkage.csv
can move for many reasons; this reads the engineered site itself.

Also prints the unmodified-parent null from the committed linkage table.
Run with the repo venv python.
"""
from __future__ import annotations

import csv
import importlib.util
import pathlib
import tempfile

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
WORK = pathlib.Path.home() / 'c4-work'
PDBDIR = WORK / 'chai/c3/pdb'
DESIGNS = WORK / 'chai/designs'

spec = importlib.util.spec_from_file_location('ls', REPO / 'tools/switch/linkage_score.py')
ls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ls)

from Bio.PDB import PDBParser  # noqa: E402


def his_pkas(pdb_path, binder='B'):
    structure = PDBParser(QUIET=True).get_structure('x', pdb_path)
    with tempfile.TemporaryDirectory() as wd:
        cplx = pathlib.Path(wd) / 'complex.pdb'
        binder_p = pathlib.Path(wd) / 'binder.pdb'
        ls.write_subset(structure, ['A', 'B'], str(cplx))
        ls.write_subset(structure, [binder], str(binder_p))
        bound = ls.run_propka(cplx, wd)
        free = ls.run_propka(binder_p, wd)
    return bound, free


def mutated_positions(parent, variant):
    def seq(name):
        return [l.strip() for l in (DESIGNS / name / 'in.fasta').read_text().splitlines()
                if not l.startswith('>')][1]
    ps, vs = seq(parent), seq(variant)
    return [i + 1 for i, (a, b) in enumerate(zip(ps, vs)) if a != b]


def main():
    # 1) the null: unmodified parents in the committed linkage table
    pos, vals = 0, []
    with open(WORK / 'logs/c3-linkage.csv') as fh:
        for r in csv.DictReader(fh):
            name = r['design'].replace('.pdb', '')
            if name.startswith('c3_'):
                continue
            try:
                v = float(r['delta_log_Ka'])
            except (TypeError, ValueError):
                continue
            vals.append(v)
            if v > 0:
                pos += 1
    vals.sort()
    print(f'parent null: {pos} of {len(vals)} positive, '
          f'range {vals[0]:+.3f}..{vals[-1]:+.3f}')
    posv = [v for v in vals if v > 0]
    if posv:
        print(f'  positive parents sorted: ' + ', '.join(f'{v:+.3f}' for v in posv))

    # 2) engineered histidine pKa, bound vs free
    # families carrying S5 designs into the final twenty (2026-10-28):
    # r4d5 (the champion), r5d7, r6d2, b2_26 (r5d1/b2_20 already recorded)
    fams = ['e12rfd4_r4d5', 'e12rfd4_r5d7', 'e12rfd4_r6d2', 'e12b2_26',
            'b4_H_r1d0000', 'e12_18', 'b4_H_r1d0004']
    print(f'\n{"variant":32}{"pos":>4}{"pKa_bound":>10}{"pKa_free":>9}{"delta":>8}')
    for parent in fams:
        for variant_dir in [parent] + [d.name for d in sorted(DESIGNS.iterdir())
                                       if d.name.startswith(f'c3_{parent}_')]:
            pdb = PDBDIR / f'{variant_dir}.pdb'
            if not pdb.exists():
                print(f'{variant_dir}: no PDB, skip')
                continue
            bound, free = his_pkas(pdb)
            for (ch, resnum, resname), pkb in sorted(bound.items()):
                if resname != 'HIS' or ch != 'B':
                    continue
                pkf = free.get((ch, resnum, 'HIS'))
                d = (pkb - pkf) if pkf is not None else float('nan')
                print(f'{variant_dir:32}{resnum:>4}{pkb:>10.2f}'
                      f'{(pkf if pkf is not None else float("nan")):>9.2f}{d:>8.2f}')


if __name__ == '__main__':
    main()
