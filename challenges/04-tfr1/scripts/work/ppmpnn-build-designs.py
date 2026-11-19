#!/usr/bin/env python3
"""Fold queue for the Proton-PottsMPNN variants of e12rfd4_r4d5 (2026-10-27).

Six capped designs (max_mutations=12, lambda 0.1/0.3/0.6) from
~/c4-work/ppmpnn-r4d5-out/designs.json. Same fold treatment as the c3
variants: parent target + mutated binder, E12 anchors, copied msa.
Writes chai/designs/ppmpnn_* + chai/ppmpnn-screen-list.txt.
"""
import json
import pathlib
import re
import shutil

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
PARENT = 'e12rfd4_r4d5'
ANCHORS = (223, 253)

rows = json.loads((WORK / 'ppmpnn-r4d5-out/designs.json').read_text())
target = (DESIGNS / PARENT / 'in.fasta').read_text().split('>')[1].split('\n')[1]
order = []
for i, r in enumerate(rows):
    lam = str(r['combined_lambda']).replace('.', '')
    name = f'ppmpnn_r4d5_l{lam}_s{r["sample"]}'
    seq = r['canonical_sequence']
    d = DESIGNS / name
    if (d / 'out/scores.model_idx_0.npz').exists():
        order.append(name)
        continue
    d.mkdir(parents=True, exist_ok=True)
    (d / 'in.fasta').write_text(f'>protein|A\n{target}\n>protein|B\n{seq}\n')
    mp = d / 'msa_pqt'
    if mp.exists():
        shutil.rmtree(mp)
    shutil.copytree(DESIGNS / PARENT / 'msa_pqt', mp)
    rs = ['restraint_id,chainA,res_idxA,chainB,res_idxB,max_distance_angstrom,'
          'min_distance_angstrom,connection_type,confidence,comment']
    for k, a in enumerate(ANCHORS, start=1):
        rs.append(f'restraint_{k},B,,A,K{a},8.0,0.0,pocket,1.0,anchorset-{a}')
    (d / 'restraints.csv').write_text('\n'.join(rs) + '\n')
    order.append(name)
    print(f'{name}: {len(seq)} aa, lam={r["combined_lambda"]}')

(WORK / 'chai/ppmpnn-screen-list.txt').write_text('\n'.join(order) + '\n')
print(f'queued {len(order)} -> chai/ppmpnn-screen-list.txt')
