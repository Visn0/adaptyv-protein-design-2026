#!/usr/bin/env python3
"""Glycan-distance screen for hosted RFD4 outputs (the E3 caveat).

The request CIFs carry no glycans (polymer only), so a design may be built
into the N251 glycan that sits 7.7 A from 231K. The RFD4 outputs keep the
target coordinates fixed (mask_coordinate), so the binder sits in the 11QC
frame and the distance to the 11QC glycan atoms can be measured directly.
The frame assumption is verified per design (chain A CA vs 11QC chain A CA).

Flags designs whose binder comes within 3.5 A of any glycan atom.
Run with the repo venv python.
"""
from __future__ import annotations

import csv
import importlib.util
import math
import pathlib

import numpy as np

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
WORK = pathlib.Path.home() / 'c4-work'
OUT = WORK / 'logs/rfd4-glycan.csv'

spec = importlib.util.spec_from_file_location('sw', REPO / 'tools/switch/switch_positions.py')
sw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sw)


def parse_cif(path):
    txt = path.read_text().splitlines()
    start = next(i for i, l in enumerate(txt) if l.startswith('_atom_site.'))
    cols, i = [], start
    while txt[i].startswith('_atom_site.'):
        cols.append(txt[i].strip())
        i += 1
    idx = {c.split('.')[1]: j for j, c in enumerate(cols)}
    atoms = []
    for l in txt[i:]:
        if l.startswith('ATOM') or l.startswith('HETATM'):
            p = l.split()
            if len(p) < len(cols):
                continue
            atoms.append({
                'chain': p[idx['auth_asym_id']], 'resname': p[idx['label_comp_id']],
                'resnum': int(p[idx['auth_seq_id']]), 'atom': p[idx['label_atom_id']],
                'xyz': (float(p[idx['Cartn_x']]), float(p[idx['Cartn_y']]), float(p[idx['Cartn_z']]))})
    return atoms


# 11QC glycans and chain A CAs (reference frame)
ref = parse_cif(REPO / 'challenges/04-tfr1/inputs/11QC.cif')
GLY = [a['xyz'] for a in ref if a['resname'] in ('NAG', 'MAN', 'BMA', 'FUC', 'GAL', 'SIA')]
REF_A_CA = {a['resnum']: a['xyz'] for a in ref if a['chain'] == 'A' and a['atom'] == 'CA'}
print(f'reference: {len(GLY)} glycan atoms, {len(REF_A_CA)} chain-A CA')


def main():
    rows = []
    for set_dir in sorted((WORK / 'rfd4').iterdir()):
        if set_dir.name not in ('E3', 'E12', 'C5'):
            continue
        for run in sorted(set_dir.glob('run-*')):
            for cif in sorted(run.glob('design_*.cif')):
                atoms = parse_cif(cif)
                chains = {}
                for a in atoms:
                    chains.setdefault(a['chain'], []).append(a)
                if len(chains) < 2:
                    continue
                big = sorted(chains, key=lambda c: -len(chains[c]))
                binder = [a for c in big[1:] for a in chains[c]]  # all designed chains
                # RFD4 recentres the system: superpose the design's target chain
                # onto the 11QC reference, then move the binder into that frame.
                tgt = sorted((a for a in chains[big[0]] if a['atom'] == 'CA'),
                             key=lambda a: a['resnum'])
                refnums = sorted(REF_A_CA)
                m = min(len(tgt), len(refnums))
                out_pts = np.array([a['xyz'] for a in tgt[:m]])
                ref_pts = np.array([REF_A_CA[n] for n in refnums[:m]])
                R, rc, oc, rmsd = sw.align_transform(ref_pts, out_pts)
                Rt = R.T
                gly_min = min(float(np.linalg.norm(Rt @ (np.array(b['xyz']) - oc) + rc - g))
                              for b in binder for g in GLY)
                frame_dev = rmsd
                rows.append({'design': f'{set_dir.name}/{run.name}/{cif.stem}',
                             'binder_len': len({(a['resnum']) for a in binder}),
                             'frame_max_dev': round(frame_dev, 2) if frame_dev is not None else None,
                             'min_dist_to_glycan': round(gly_min, 2),
                             'glycan_flag': gly_min < 3.5})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    flagged = [r for r in rows if r['glycan_flag']]
    bad_frame = [r for r in rows if r['frame_max_dev'] is not None and r['frame_max_dev'] > 2.0]
    print(f'wrote {OUT} ({len(rows)} designs)')
    print(f'gilgan clashes (< 3.5 A): {len(flagged)}')
    print(f'frame deviations > 2 A: {len(bad_frame)}')
    print(f'{"design":32}{"len":>5}{"frame":>8}{"glycan":>8}')
    for r in sorted(rows, key=lambda r: r['min_dist_to_glycan'])[:14]:
        print(f'{r["design"]:32}{r["binder_len"]:>5}{r["frame_max_dev"]:>8}{r["min_dist_to_glycan"]:>8}'
              + ('  <-- CLASH' if r['glycan_flag'] else ''))


if __name__ == '__main__':
    main()
