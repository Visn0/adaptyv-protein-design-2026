#!/usr/bin/env python3
"""Batch-4R fold queue: RFdiffusion arm (third generator).

Sources: ~/c4-work/rfdiffusion/B4R/<tag>/design_<i>.pdb (chain B = the fixed
target, chain A = the designed binder backbone) + the MPNN sequences in
~/c4-work/seqs-b4r/<tag>_<i>/all.fa (the first sequence of the T=0.1 set is
the fold candidate; the rest stay on record).

Anchors (fold numbering): E12L -> 223, 253; E0L -> 83, 87, 89, 90, 227, 250;
H -> 87, 90, 223, 253. Restraints are 8 A pockets as in batch-3/4.

Writes chai/designs/b4r_* + chai/b4r-screen-list.txt + logs/b4r-designs.csv.
"""
from __future__ import annotations

import csv
import pathlib
import shutil

import gemmi

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
RF = WORK / 'rfdiffusion/B4R'
SEQS = WORK / 'seqs-b4r'
LIST = WORK / 'chai/b4r-screen-list.txt'
META = WORK / 'logs/b4r-designs.csv'
ANCHORS = {'E12L': (223, 253), 'E0L': (83, 87, 89, 90, 227, 250),
           'H': (87, 90, 223, 253)}
AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}


def first_seq(path):
    recs, cur = [], []
    for line in path.read_text().splitlines():
        if line.startswith('>'):
            if cur:
                recs.append(''.join(cur))
            cur = []
        else:
            cur.append(line.strip())
    if cur:
        recs.append(''.join(cur))
    return recs[0] if recs else None


def main():
    with open(DESIGNS / 'e12rfd4_r4d5/in.fasta') as fh:
        target = [l.strip() for l in fh if not l.startswith('>')][0]
    rows, order = [], []
    for tag, anchors in ANCHORS.items():
        for pdb in sorted((RF / tag).glob('design_*.pdb')):
            idx = int(pdb.stem.split('_')[1])
            name = f'b4r_{tag}_{idx:04d}'
            seq = first_seq(SEQS / f'{tag}_{idx:04d}' / 'all.fa')
            if not seq:
                print(f'{name}: no MPNN sequence yet - skipping')
                continue
            d = DESIGNS / name
            if (d / 'out' / 'scores.model_idx_0.npz').exists():
                order.append(name)
                continue
            d.mkdir(parents=True, exist_ok=True)
            (d / 'in.fasta').write_text(f'>protein|A\n{target}\n>protein|B\n{seq}\n')
            mp = d / 'msa_pqt'
            if mp.exists():
                shutil.rmtree(mp)
            shutil.copytree(DESIGNS / 'e12rfd4_r4d5/msa_pqt', mp)
            rs = ['restraint_id,chainA,res_idxA,chainB,res_idxB,max_distance_angstrom,'
                  'min_distance_angstrom,connection_type,confidence,comment']
            for k, a in enumerate(anchors, start=1):
                rs.append(f'restraint_{k},B,,A,K{a},8.0,0.0,pocket,1.0,anchorset-{a}')
            (d / 'restraints.csv').write_text('\n'.join(rs) + '\n')
            rows.append({'design': name, 'tag': tag, 'binder_len': len(seq),
                         'anchors': len(anchors)})
            order.append(name)
    # sanity: the backbone's chain B should equal the shared target
    sample = sorted(RF.glob('*/*.pdb'))
    if sample:
        st = gemmi.read_structure(str(sample[0]))
        tgt_b = ''.join(AA3.get(r.name, 'X') for ch in st[0] if ch.name == 'B'
                        for r in ch if r.entity_type == gemmi.EntityType.Polymer)
        if tgt_b and tgt_b != target:
            print('WARNING: backbone chain B != shared target (len %d vs %d)'
                  % (len(tgt_b), len(target)))
    LIST.write_text('\n'.join(order) + '\n')
    with open(META, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['design', 'tag', 'binder_len', 'anchors'])
        w.writeheader()
        w.writerows(rows)
    print(f'queued {len(order)} -> {LIST}')


if __name__ == '__main__':
    main()
