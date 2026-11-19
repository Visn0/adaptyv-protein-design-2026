#!/usr/bin/env python3
"""Campaign 4 (mouse cross-fold), step 1: build the mouse fold dirs.

Takes every campaign-2 design clearing the human at-site line (mean restrained
ipTM >= 0.45) and builds c4mn_<parent> design dirs whose target is the MOUSE
construct instead of the human one:

  in.fasta       mouse target (AF-Q62351-F1, 641 aa; auth 123-763) + the
                 parent's binder sequence unchanged
  msa_pqt/       the mouse target MSA (colabfold, depth 1024, converted to
                 .aligned.pqt for chai) + the same shared binder-side pqt the
                 human dirs carry (binder chain falls back to single-sequence
                 exactly as in every human fold)
  restraints.csv pocket restraints on the mouse anchors: fold K224 = auth K346,
                 fold K254 = auth K376 (human K344/K374 via the alignment in
                 scripts/epitope_analysis.py - never a fixed offset)

Writes ~/c4-work/chai/c4-screen-list.txt and ~/c4-work/logs/c4-designs.csv.
"""
from __future__ import annotations

import csv
import pathlib
import shutil
import statistics

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
MOUSE_SEQ = (WORK / 'mouse-target.seq').read_text().strip()
MOUSE_PQT = WORK / 'msa/4e8e439fe989a0726bbe4b4dbe8b133c4b34e74ca541a566f2e97bbd203eb5b2.aligned.pqt'
BINDER_FALLBACK_PQT = 'dc95ce07b25c5e9264b33de7315b46a9778be320dc858f582d6baf9876917084.aligned.pqt'
LIST = WORK / 'chai/c4-screen-list.txt'
META = WORK / 'logs/c4-designs.csv'

RESTRAINTS = (
    'restraint_id,chainA,res_idxA,chainB,res_idxB,max_distance_angstrom,'
    'min_distance_angstrom,connection_type,confidence,comment\n'
    'restraint_1,B,,A,K224,8.0,0.0,pocket,1.0,mouse-hotspot-224\n'
    'restraint_2,B,,A,K254,8.0,0.0,pocket,1.0,mouse-hotspot-254\n'
)


def qualifiers():
    per = {}
    with open(WORK / 'logs/c2-restrained.csv') as fh:
        for r in csv.DictReader(fh):
            per.setdefault(r['design'], []).append(float(r['iptm']))
    return sorted(((statistics.mean(v), d) for d, v in per.items() if statistics.mean(v) >= 0.45),
                  reverse=True)


def main():
    rows, order = [], []
    for mean, parent in qualifiers():
        pdir = DESIGNS / parent
        seqs = [l.strip() for l in (pdir / 'in.fasta').read_text().splitlines()
                if not l.startswith('>')]
        binder = seqs[1]
        name = f'c4mn_{parent}'
        d = DESIGNS / name
        if (d / 'out' / 'scores.model_idx_0.npz').exists():
            print(f'{name}: already scored, skip')
            order.append(name)
            continue
        d.mkdir(parents=True, exist_ok=True)
        (d / 'in.fasta').write_text(f'>protein|A\n{MOUSE_SEQ}\n>protein|B\n{binder}\n')
        mp = d / 'msa_pqt'
        if mp.exists():
            shutil.rmtree(mp)
        mp.mkdir()
        shutil.copy(MOUSE_PQT, mp / MOUSE_PQT.name)
        shutil.copy(pdir / 'msa_pqt' / BINDER_FALLBACK_PQT, mp / BINDER_FALLBACK_PQT)
        (d / 'restraints.csv').write_text(RESTRAINTS)
        rows.append({'design': name, 'parent': parent, 'human_mean_iptm': round(mean, 3),
                     'binder_len': len(binder)})
        order.append(name)
        print(f'{name}: built (parent mean {mean:.3f})')
    LIST.write_text('\n'.join(order) + '\n')
    with open(META, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['design', 'parent', 'human_mean_iptm', 'binder_len'])
        w.writeheader()
        w.writerows(rows)
    print(f'\nqueued: {len(order)} -> {LIST}\nrecord: {META}')


if __name__ == '__main__':
    main()
