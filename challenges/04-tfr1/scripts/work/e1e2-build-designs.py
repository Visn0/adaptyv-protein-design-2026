#!/usr/bin/env python3
"""E1/E2 restrained screen: chai dirs from the C1-era designs.

Sources: ~/c4-work/folds/11qc_e{1,2}_<n>.yaml (binder = chain A sequence,
target = chain B; both read from the yaml). Target sequence is taken from the
canonical shared fasta. Anchors (fold numbering):
  E1 -> 85, 86, 88, 253   (auth 206,207,209,374)
  E2 -> 222, 223, 226, 229, 230 (auth 343,344,347,350,351)
Writes chai/designs/e1_*/e2_* + chai/e1e2-screen-list.txt.
"""
from __future__ import annotations

import pathlib
import re
import shutil

WORK = pathlib.Path.home() / 'c4-work'
FOLDS = WORK / 'folds'
DESIGNS = WORK / 'chai/designs'
LIST = WORK / 'chai/e1e2-screen-list.txt'
ANCHORS = {'e1': (85, 86, 88, 253), 'e2': (222, 223, 226, 229, 230)}

with open(DESIGNS / 'e12rfd4_r4d5/in.fasta') as fh:
    target = [l.strip() for l in fh if not l.startswith('>')][0]

order = []
for setname, anchors in ANCHORS.items():
    for yaml in sorted(FOLDS.glob(f'11qc_{setname}_*.yaml')):
        num = yaml.stem.split('_')[-1]
        text = yaml.read_text()
        seqs = re.findall(r'sequence: ([A-Z]+)', text)
        binder = seqs[0]
        name = f'{setname}_{num}'
        d = DESIGNS / name
        if (d / 'out' / 'scores.model_idx_0.npz').exists():
            order.append(name)
            continue
        d.mkdir(parents=True, exist_ok=True)
        (d / 'in.fasta').write_text(f'>protein|A\n{target}\n>protein|B\n{binder}\n')
        mp = d / 'msa_pqt'
        if mp.exists():
            shutil.rmtree(mp)
        shutil.copytree(DESIGNS / 'e12rfd4_r4d5/msa_pqt', mp)
        rs = ['restraint_id,chainA,res_idxA,chainB,res_idxB,max_distance_angstrom,'
              'min_distance_angstrom,connection_type,confidence,comment']
        for k, a in enumerate(anchors, start=1):
            rs.append(f'restraint_{k},B,,A,K{a},8.0,0.0,pocket,1.0,anchorset-{a}')
        (d / 'restraints.csv').write_text('\n'.join(rs) + '\n')
        order.append(name)

LIST.write_text('\n'.join(order) + '\n')
print(f'queued {len(order)} -> {LIST}')
for setname in ANCHORS:
    print(setname, sum(1 for n in order if n.startswith(setname)), 'designs')
