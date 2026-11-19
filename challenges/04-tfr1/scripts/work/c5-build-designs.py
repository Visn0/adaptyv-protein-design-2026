#!/usr/bin/env python3
"""C5 fold queue: the two-chain (multi-chain) binder pilot designs.

Sources: ~/c4-work/rfd4/C5/run-*/design_*.cif (chains A target, B and C
designed). Skips glycan-clashing designs (logs/rfd4-glycan.csv). Restraints
are derived from each design's own interface: a chain gets a pocket restraint
to an anchor lysine only if it contacts that lysine (>= 3 atom pairs < 4.5 A).

Builds chai dirs c5_r<run>d<i>/ : in.fasta (A + B + C), msa_pqt, restraints.
Writes chai/c5-screen-list.txt + logs/c5-designs.csv.
"""
from __future__ import annotations

import csv
import math
import pathlib
import shutil

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
RF = WORK / 'rfd4/C5'
GLYCAN = WORK / 'logs/rfd4-glycan.csv'
LIST = WORK / 'chai/c5-screen-list.txt'
META = WORK / 'logs/c5-designs.csv'

AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}
ANCHORS = (223, 253)  # fold numbering (auth 344, 374 - 121)


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
        if l.startswith(('ATOM', 'HETATM')):
            p = l.split()
            if len(p) < len(cols):
                continue
            atoms.append((p[idx['auth_asym_id']], int(p[idx['auth_seq_id']]),
                          p[idx['label_comp_id']],
                          (float(p[idx['Cartn_x']]), float(p[idx['Cartn_y']]),
                           float(p[idx['Cartn_z']]))))
    return atoms


def main():
    with open(DESIGNS / 'e12rfd4_r4d5/in.fasta') as fh:
        target = [l.strip() for l in fh if not l.startswith('>')][0]
    gly = {}
    with open(GLYCAN) as fh:
        for r in csv.DictReader(fh):
            gly[r['design']] = r
    rows, order = [], []
    for run in sorted(RF.glob('run-*')):
        rn = run.name.replace('run-', 'r')
        for cif in sorted(run.glob('design_*.cif')):
            name = f'c5_{rn}{cif.stem.replace("design_", "d")}'
            gkey = f'C5/{run.name}/{cif.stem}'
            if gly.get(gkey, {}).get('glycan_flag') == 'True':
                print(f'{name}: EXCLUDED (glycan clash {gly[gkey]["min_dist_to_glycan"]} A)')
                rows.append({'design': name, 'status': 'excluded-glycan', 'chains': '',
                             'restraints': ''})
                continue
            d = DESIGNS / name
            if (d / 'out' / 'scores.model_idx_0.npz').exists():
                order.append(name)
                continue
            atoms = parse_cif(cif)
            ch = {}
            for a in atoms:
                ch.setdefault(a[0], []).append(a)
            seqs = {}
            for chain in ('B', 'C'):
                res = sorted({a[1] for a in ch[chain]})
                seqs[chain] = ''.join(
                    AA3.get(next(a[2] for a in ch[chain] if a[1] == r), 'X') for r in res)
            # per-chain, per-anchor contacts -> restraints
            restr = []
            for chain in ('B', 'C'):
                for anchor in ANCHORS:
                    # design CIFs keep auth numbering (122-760); anchors are
                    # sequence positions: auth = seq + 121
                    side = [a for a in ch['A'] if a[1] == anchor + 121]
                    n = sum(1 for x in ch[chain] for y in side
                            if math.dist(x[3], y[3]) < 4.5)
                    if n >= 3:
                        restr.append((chain, anchor, n))
            if not restr:
                print(f'{name}: NO restraints derived - skipping')
                rows.append({'design': name, 'status': 'no-contacts', 'chains': '',
                             'restraints': ''})
                continue
            d.mkdir(parents=True, exist_ok=True)
            (d / 'in.fasta').write_text(
                f'>protein|A\n{target}\n>protein|B\n{seqs["B"]}\n>protein|C\n{seqs["C"]}\n')
            mp = d / 'msa_pqt'
            if mp.exists():
                shutil.rmtree(mp)
            shutil.copytree(DESIGNS / 'e12rfd4_r4d5/msa_pqt', mp)
            rs = ['restraint_id,chainA,res_idxA,chainB,res_idxB,max_distance_angstrom,'
                  'min_distance_angstrom,connection_type,confidence,comment']
            for k, (chain, anchor, n) in enumerate(restr, start=1):
                rs.append(f'restraint_{k},{chain},,A,K{anchor},8.0,0.0,pocket,1.0,'
                          f'design-contact-{n}pair')
            (d / 'restraints.csv').write_text('\n'.join(rs) + '\n')
            rows.append({'design': name, 'status': 'queued',
                         'chains': f'B{len(seqs["B"])}+C{len(seqs["C"])}',
                         'restraints': ';'.join(f'{c}->K{a}' for c, a, _ in restr)})
            order.append(name)
            print(f'{name}: queued  B={len(seqs["B"])} C={len(seqs["C"])}  '
                  f'restraints {", ".join(f"{c}->K{a}" for c, a, _ in restr)}')
    LIST.write_text('\n'.join(order) + '\n')
    with open(META, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['design', 'status', 'chains', 'restraints'])
        w.writeheader()
        w.writerows(rows)
    print(f'\nqueued {len(order)} -> {LIST}')


if __name__ == '__main__':
    main()
