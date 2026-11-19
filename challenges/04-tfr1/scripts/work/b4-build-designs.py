#!/usr/bin/env python3
"""Batch-4 fold queue: the 2026-10-27 generation wave.

Sources: rfd4/B4/<tag>/run-*/design_*.cif for tags E12L, E0L, H.
Anchors (fold numbering) per tag:
  E12L -> 223, 253          (auth 344/374; the long-length E12 sweep)
  E0L  -> 83, 87, 89, 90, 227, 250   (auth 204..371; long-length E0)
  H    -> 87, 90, 223, 253  (auth 208/211/344/374 hybrid)
Restraints are the set's anchors as 8 A pockets, as in batch-3. No glycan
screen here: these patches are clear of the N251 glycan (that corner, 231 K,
is not among the anchors).

Writes chai/designs/b4_* + chai/b4-screen-list.txt + logs/b4-designs.csv.
"""
from __future__ import annotations

import csv
import pathlib
import shutil

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
RF = WORK / 'rfd4/B4'
LIST = WORK / 'chai/b4-screen-list.txt'
META = WORK / 'logs/b4-designs.csv'
AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}
ANCHORS = {'E12L': (223, 253), 'E0L': (83, 87, 89, 90, 227, 250),
           'H': (87, 90, 223, 253)}


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
            try:
                atoms.append((p[idx['auth_asym_id']], int(p[idx['auth_seq_id']]),
                              p[idx['label_comp_id']]))
            except ValueError:
                continue
    return atoms


def main():
    with open(DESIGNS / 'e12rfd4_r4d5/in.fasta') as fh:
        target = [l.strip() for l in fh if not l.startswith('>')][0]
    rows, order = [], []
    for tag, anchors in ANCHORS.items():
        for run in sorted((RF / tag).glob('run-*')):
            rn = run.name.replace('run-', 'r')
            for cif in sorted(run.glob('design_*.cif')):
                name = f'b4_{tag}_{rn}{cif.stem.replace("design_", "d")}'
                d = DESIGNS / name
                if (d / 'out' / 'scores.model_idx_0.npz').exists():
                    order.append(name)
                    continue
                atoms = parse_cif(cif)
                chains = {}
                for a in atoms:
                    chains.setdefault(a[0], []).append(a)
                big = sorted(chains, key=lambda c: -len(chains[c]))
                binder_res = sorted({a[1] for a in chains[big[1]]})
                seq = ''.join(AA3.get(next(a[2] for a in chains[big[1]] if a[1] == r), 'X')
                              for r in binder_res)
                d.mkdir(parents=True, exist_ok=True)
                (d / 'in.fasta').write_text(f'>protein|A\n{target}\n>protein|B\n{seq}\n')
                mp = d / 'msa_pqt'
                if mp.exists():
                    shutil.rmtree(mp)
                shutil.copytree(DESIGNS / 'e12rfd4_r4d5/msa_pqt', mp)
                rs = ['restraint_id,chainA,res_idxA,chainB,res_idxB,max_distance_angstrom,'
                      'min_distance_angstrom,connection_type,confidence,comment']
                for k, anchor in enumerate(anchors, start=1):
                    rs.append(f'restraint_{k},B,,A,K{anchor},8.0,0.0,pocket,1.0,anchorset-{anchor}')
                (d / 'restraints.csv').write_text('\n'.join(rs) + '\n')
                rows.append({'design': name, 'tag': tag, 'binder_len': len(seq),
                             'anchors': len(anchors)})
                order.append(name)
    LIST.write_text('\n'.join(order) + '\n')
    with open(META, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['design', 'tag', 'binder_len', 'anchors'])
        w.writeheader()
        w.writerows(rows)
    print(f'queued {len(order)} -> {LIST}')


if __name__ == '__main__':
    main()
