#!/usr/bin/env python3
"""Batch-3 fold queue: the new hosted RFD4 designs (E12 runs 9-11, E3 runs 1-3).

Sources: ~/c4-work/rfd4/<set>/run-*/design_*.cif (binder = the smaller chain).
Applies the glycan screen result for E3 (logs/rfd4-glycan.csv; clash designs are
excluded and recorded). Builds chai design dirs:

  b3_<set>_r<n>d<i>/  in.fasta (human 639 target + the design's binder)
                      msa_pqt  (shared receptor pqt + binder fallback pqt)
                      restraints.csv  pockets at the set's anchors, 8 A
                          E12 -> K223, K253
                          E3  -> K110, K223, K253  (auth 231/344/374 - 121)

Writes ~/c4-work/chai/b3-screen-list.txt + logs/b3-designs.csv.
"""
from __future__ import annotations

import csv
import pathlib
import shutil

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
RF = WORK / 'rfd4'
GLYCAN = WORK / 'logs/rfd4-glycan.csv'
LIST = WORK / 'chai/b3-screen-list.txt'
META = WORK / 'logs/b3-designs.csv'

AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}
ANCHORS = {'E12': (223, 253), 'E3': (110, 223, 253)}


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
            atoms.append((p[idx['auth_asym_id']], int(p[idx['auth_seq_id']]),
                          p[idx['label_comp_id']]))
    return atoms


def main():
    with open(WORK / 'chai/designs/e12rfd4_r4d5/in.fasta') as fh:
        target = [l.strip() for l in fh if not l.startswith('>')][0]
    gly = {}
    with open(GLYCAN) as fh:
        for r in csv.DictReader(fh):
            gly[r['design']] = r
    rows, order = [], []
    for set_name in ('E12', 'E3'):
        for run in sorted((RF / set_name).glob('run-*')):
            nrun = int(run.name.split('-')[1])
            if set_name == 'E12' and nrun < 9:
                continue  # runs 2-8 are the campaign-2 designs, already folded
            rn = run.name.replace('run-', 'r')
            for cif in sorted(run.glob('design_*.cif')):
                did = cif.stem.replace('design_', 'd').lstrip('d')
                name = f'b3_{set_name}_{rn}{did}'
                gkey = f'{set_name}/{run.name}/{cif.stem}'
                if set_name == 'E3' and gly.get(gkey, {}).get('glycan_flag') == 'True':
                    print(f'{name}: EXCLUDED (glycan clash {gly[gkey]["min_dist_to_glycan"]} A)')
                    rows.append({'design': name, 'set': set_name, 'status': 'excluded-glycan',
                                 'binder_len': '', 'glycan_min': gly[gkey]['min_dist_to_glycan']})
                    continue
                atoms = parse_cif(cif)
                chains = {}
                for a in atoms:
                    chains.setdefault(a[0], []).append(a)
                big = sorted(chains, key=lambda c: -len(chains[c]))
                binder_res = sorted({a[1] for a in chains[big[1]]})
                seq = ''.join(AA3.get(next(a[2] for a in chains[big[1]] if a[1] == rn2), 'X')
                              for rn2 in binder_res)
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
                for k, anchor in enumerate(ANCHORS[set_name], start=1):
                    rs.append(f'restraint_{k},B,,A,K{anchor},8.0,0.0,pocket,1.0,anchorset-{anchor}')
                (d / 'restraints.csv').write_text('\n'.join(rs) + '\n')
                rows.append({'design': name, 'set': set_name, 'status': 'queued',
                             'binder_len': len(seq),
                             'glycan_min': gly.get(gkey, {}).get('min_dist_to_glycan', '')})
                order.append(name)
                print(f'{name}: queued ({len(seq)} aa)')
    LIST.write_text('\n'.join(order) + '\n')
    with open(META, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['design', 'set', 'status', 'binder_len', 'glycan_min'])
        w.writeheader()
        w.writerows(rows)
    q = sum(1 for r in rows if r['status'] == 'queued')
    print(f'\nqueued {q} ({len(order)} in list) -> {LIST}')


if __name__ == '__main__':
    main()
