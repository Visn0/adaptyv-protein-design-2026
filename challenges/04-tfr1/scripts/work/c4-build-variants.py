#!/usr/bin/env python3
"""Campaign 4, step 2: queue the campaign-3 survivors against the mouse target.

Scope per the c4 README: every histidine variant that clears campaign 3's
gates (binding kept, linkage sign positive). Reads the gate outcome from
logs/c3-linkage.csv + logs/c3-restrained.csv with the same rules as
c3-restrained-scores.py, builds c4mn_<variant> dirs (mouse target, parent
binder sequence = the variant's), restraints on mouse K224/K254.

Writes ~/c4-work/chai/c4v-screen-list.txt + appends to logs/c4-designs.csv.
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
LIST = WORK / 'chai/c4v-screen-list.txt'
META = WORK / 'logs/c4-designs.csv'

RESTRAINTS = (
    'restraint_id,chainA,res_idxA,chainB,res_idxB,max_distance_angstrom,'
    'min_distance_angstrom,connection_type,confidence,comment\n'
    'restraint_1,B,,A,K224,8.0,0.0,pocket,1.0,mouse-hotspot-224\n'
    'restraint_2,B,,A,K254,8.0,0.0,pocket,1.0,mouse-hotspot-254\n'
)


def scored(path):
    per = {}
    with open(path) as fh:
        for r in csv.DictReader(fh):
            per.setdefault(r['design'], []).append(float(r['iptm']))
    return {d: statistics.mean(v) for d, v in per.items()}


def signs(path):
    out = {}
    with open(path) as fh:
        for r in csv.DictReader(fh):
            try:
                out[r['design'].replace('.pdb', '')] = float(r['delta_log_Ka'])
            except (TypeError, ValueError):
                pass
    return out


def main():
    c3 = scored(WORK / 'logs/c3-restrained.csv')
    c2 = scored(WORK / 'logs/c2-restrained.csv')
    sg = signs(WORK / 'logs/c3-linkage.csv')
    survivors = []
    for d, m in c3.items():
        parent = d[3:].rsplit('_', 1)[0]
        if m - c2.get(parent, -9) < -0.10:
            continue
        if sg.get(d, -9) <= 0:
            continue
        survivors.append((m, d))
    survivors.sort(reverse=True)
    order = []
    for mean, variant in survivors:
        binder = [l.strip() for l in (DESIGNS / variant / 'in.fasta').read_text().splitlines()
                  if not l.startswith('>')][1]
        name = f'c4mn_{variant}'
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
        shutil.copy(DESIGNS / variant / 'msa_pqt' / BINDER_FALLBACK_PQT,
                    mp / BINDER_FALLBACK_PQT)
        (d / 'restraints.csv').write_text(RESTRAINTS)
        order.append(name)
        print(f'{name}: built (human variant mean {mean:.3f}, sign +{sg[variant]:.3f})')
    LIST.write_text('\n'.join(order) + '\n')
    with open(META, 'a', newline='') as fh:
        w = csv.writer(fh)
        for mean, variant in survivors:
            n = f'c4mn_{variant}'
            if n in order:
                binder = [l.strip() for l in (DESIGNS / variant / 'in.fasta').read_text().splitlines()
                          if not l.startswith('>')][1]
                w.writerow([n, variant, round(mean, 3), len(binder)])
    print(f'\nqueued: {len(order)} -> {LIST}')


if __name__ == '__main__':
    main()
