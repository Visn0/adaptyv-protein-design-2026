#!/usr/bin/env python3
"""c5 per-chain folds: split each c5 two-chain design into two 2-chain folds.

The assembled 3-chain fold is pathologically slow on this host (trunk 775 s
per recycle vs 82 s baseline; VRAM 11.9 of 12.2 GB; the first attempt ended in
a host crash), so the campaign read is taken per chain: chain B against the
target with B's restraints, chain C likewise. The B-C interface stays
validated from the design model (contacts + DockQ), recorded in the README.

Reads  chai/designs/c5_*/{in.fasta,restraints.csv}  ->
writes chai/designs/c5B_*/ and c5C_*/ (in.fasta, msa_pqt, restraints.csv)
and   chai/c5-screen-list.txt (44 entries, design-major order).
"""
from __future__ import annotations

import csv
import math
import pathlib
import re
import shutil

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
RF = WORK / 'rfd4/C5'
LIST = WORK / 'chai/c5-screen-list.txt'
AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
       "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
       "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
       "TYR": "Y", "VAL": "V"}


def _parse(path):
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
                              p[idx['label_comp_id']],
                              (float(p[idx['Cartn_x']]), float(p[idx['Cartn_y']]),
                               float(p[idx['Cartn_z']]))))
            except ValueError:
                continue
    return atoms


def fallback_restraints(suffix, chain, target_seq, header):
    """Pocket restraints from the design's own strongest target contacts.

    Used when a chain does not contact either anchor lysine in its design;
    an empty restraints file fails chai's schema check (max_distance column
    infers as object, 2026-10-27). Contacts are counted on the RFD4 design
    complex whose chain A carries AUTH numbering (122-760); the restraint
    file needs SEQUENCE numbering, seq = auth - 121. The first version fed
    auth numbers straight in, conditioning the folds on a wrong site (all
    nine reads floated at 39-48 A; fixed and re-folded 2026-10-27). The
    residue letter is taken from the target sequence itself, so the token
    cannot disagree with the fold's numbering.
    """
    m = re.match(r'r(\d+)d0*(\d+)$', suffix)
    cif = RF / f'run-{m.group(1)}' / f'design_{int(m.group(2)):04d}.cif'
    atoms = _parse(cif)
    tgt = [a for a in atoms if a[0] == 'A']
    bnd = [a for a in atoms if a[0] == chain]
    pairs = {}
    for b in bnd:
        for t in tgt:
            if math.dist(b[3], t[3]) < 4.5:
                pairs[(t[1], t[2])] = pairs.get((t[1], t[2]), 0) + 1
    top = sorted(pairs.items(), key=lambda kv: -kv[1])[:2]
    rows = []
    for n, ((auth, resname), count) in enumerate(top, start=1):
        seqpos = auth - 121
        if not (1 <= seqpos <= len(target_seq)):
            continue
        letter = target_seq[seqpos - 1]
        rows.append([f'restraint_{n}', 'B', '', 'A',
                     f'{letter}{seqpos}', '8.0', '0.0', 'pocket',
                     '1.0', f'design-contact-fallback-{count}pair-auth{auth}'])
    if rows:
        print(f'    fallback restraints for {chain}: ' +
              ', '.join(f'{r[4]}({r[9]})' for r in rows))
    return rows

order = []
for d in sorted(DESIGNS.glob('c5_*')):
    if not (d / 'in.fasta').exists():
        continue
    suffix = d.name[len('c5_'):]
    seqs = {}
    for line in (d / 'in.fasta').read_text().splitlines():
        if line.startswith('>protein|'):
            cur = line.split('|')[1]
        elif line.strip():
            seqs[cur] = line.strip()
    with open(d / 'restraints.csv') as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], rows[1:]
    for chain in ('B', 'C'):
        name = f'c5{chain}_{suffix}'
        out = DESIGNS / name
        if (out / 'out/scores.model_idx_0.npz').exists():
            order.append(name)
            continue  # already folded; never touch
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        (out / 'in.fasta').write_text(
            f'>protein|A\n{seqs["A"]}\n>protein|B\n{seqs[chain]}\n')
        keep = []
        for r in body:
            if not r or len(r) < 10:
                continue
            if r[1] != chain:
                continue
            r = list(r)
            r[1] = 'B'  # the binder chain in this 2-chain fold
            r[0] = f'restraint_{len(keep) + 1}'
            keep.append(r)
        if not keep:
            keep = fallback_restraints(suffix, chain, seqs['A'], header)
        with open(out / 'restraints.csv', 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(keep)
        shutil.copytree(d / 'msa_pqt', out / 'msa_pqt')
        order.append(name)
        print(f'{name}: {len(seqs[chain])} aa binder, {len(keep)} restraints')

LIST.write_text('\n'.join(order) + '\n')
print(f'\nwrote {LIST} ({len(order)} folds)')
