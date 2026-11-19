#!/usr/bin/env python3
"""Campaign-5 (multi-chain) scoring: per-chain folds, design-side B-C check.

The campaign read was adapted to per-chain folds (see campaigns/c5-multi-chain/
README.md): each design c5_r<X>d<Y> has two 2-chain folds, c5B_* (chain B
against the target) and c5C_*. For each fold: mean restrained ipTM over 5
samples, restraint satisfaction, DockQ vs a 2-chain reference cut from the
RFD4 design model, PRODIGY dG/Kd on sample 0. Design side (from the RFD4
model): B-C contact count and clash count.

Verdict vs the registered rule: unit ipTM = mean of the two chain folds;
advance needs >= 3 of 22 at unit ipTM >= 0.70 with both chain folds at >= 0.45,
B-C contacts >= 20, B-C clashes 0, and both DockQ >= 0.8.
Writes ~/c4-work/logs/c5-restrained.csv + prints the table.
"""
from __future__ import annotations

import csv
import math
import pathlib
import re
import subprocess

import gemmi
import numpy as np

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
RF = WORK / 'rfd4/C5'
SCRATCH = pathlib.Path.home() / '.hermes/cache/scratch/dockq-refs'
OUT = WORK / 'logs/c5-restrained.csv'
VENV = _repo_root() / '.venv/bin'
FOLD_RE = re.compile(r'c5([BC])_r(\d+)d0*(\d+)$')


def parse(path):
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
                              p[idx['label_atom_id']],
                              float(p[idx['Cartn_x']]), float(p[idx['Cartn_y']]),
                              float(p[idx['Cartn_z']])))
            except ValueError:
                continue
    return atoms


def ref_for(chain, run, didx):
    """2-chain reference (target + that design chain) cut from the design model."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    ref = SCRATCH / f'{chain}_r{run}d{didx}.pdb'
    if not ref.exists():
        st = gemmi.read_structure(str(RF / f'run-{run}' / f'design_{didx:04d}.cif'))
        m = gemmi.Model('1')
        for ch in st[0]:
            if ch.name in ('A', chain):
                m.add_chain(ch)
        s = gemmi.Structure()
        s.add_model(m)
        s.write_pdb(str(ref))
    return ref


def dockq(model, ref):
    try:
        r = subprocess.run([str(VENV / 'DockQ'), str(model), str(ref), '--short'],
                           capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None
    for line in r.stdout.splitlines():
        if line.startswith('Total DockQ'):
            m = re.search(r': ([\d.]+)', line)
            if m:
                return float(m.group(1))
    return None


def prodigy(cif):
    try:
        r = subprocess.run([str(VENV / 'prodigy'), str(cif), '--selection', 'A', 'B'],
                           capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None, None, None
    dg = kd = ic = None
    for line in r.stdout.splitlines():
        if 'Predicted binding affinity' in line:
            dg = float(line.split(':')[-1])
        elif 'Predicted dissociation constant' in line:
            kd = float(line.split(':')[-1].split()[0])
        elif 'No. of intermolecular contacts' in line:
            ic = int(line.split(':')[-1])
    return dg, kd, ic


def design_bc(run, didx):
    """(contacts, clashes) across the B-C interface in the design model."""
    atoms = parse(RF / f'run-{run}' / f'design_{didx:04d}.cif')
    b = [a for a in atoms if a[0] == 'B']
    c = [a for a in atoms if a[0] == 'C']
    contacts = clashes = 0
    for x in b:
        for y in c:
            d = math.dist(x[3:6], y[3:6])
            if d < 4.5:
                contacts += 1
            if d < 2.0:
                clashes += 1
    return contacts, clashes


rows = []
for fold in sorted(DESIGNS.glob('c5[BC]_*')):
    m = FOLD_RE.match(fold.name)
    if not m or not (fold / 'out').is_dir():
        continue
    chain, run, didx = m.group(1), int(m.group(2)), int(m.group(3))
    iptms, dists = [], []
    anchors = []
    with open(fold / 'restraints.csv') as fh:
        for row in csv.DictReader(fh):
            tok = (row['res_idxB'] or '').strip()
            if tok and tok[0].isalpha():
                anchors.append(int(tok[1:]))
    for i in range(5):
        cif = fold / 'out' / f'pred.model_idx_{i}.cif'
        npz = fold / 'out' / f'scores.model_idx_{i}.npz'
        if not cif.exists() or not npz.exists():
            continue
        iptms.append(float(np.asarray(np.load(npz, allow_pickle=True)['iptm'])
                           .reshape(-1)[0]))
        atoms = parse(cif)
        tgt = [a for a in atoms if a[0] == 'A']
        bnd = [a for a in atoms if a[0] != 'A']
        for r in anchors:
            side = [a for a in tgt if a[1] == r]
            if side:
                dists.append(min(math.dist(a[3:6], b[3:6]) for a in side for b in bnd))
    if not iptms:
        continue
    ref = ref_for(chain, run, didx)
    dq = dockq(fold / 'out' / 'pred.model_idx_0.cif', ref)
    dg, kd, ic = prodigy(fold / 'out' / 'pred.model_idx_0.cif')
    bc_contacts, bc_clashes = design_bc(run, didx)
    rows.append({'design': f'c5_r{run}d{didx}', 'chain': chain,
                 'iptm': round(float(np.mean(iptms)), 3),
                 'worst_restraint_dist': round(max(dists), 2) if dists else None,
                 'dockq': dq, 'prodigy_dG': dg, 'prodigy_Kd': kd,
                 'design_bc_contacts': bc_contacts, 'design_bc_clashes': bc_clashes})

with OUT.open('w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f'wrote {OUT} ({len(rows)} folds)')

per = {}
for r in rows:
    per.setdefault(r['design'], {})[r['chain']] = r
print(f'\n{"design":14}{"ipB":>6}{"ipC":>6}{"unit":>6}{"bcC":>5}{"bcX":>4}'
      f'{"dqB":>6}{"dqC":>6}{"restB":>6}{"restC":>6}')
adv = 0
for name, ch in sorted(per.items()):
    if 'B' not in ch or 'C' not in ch:
        continue
    unit = (ch['B']['iptm'] + ch['C']['iptm']) / 2
    dqB, dqC = ch['B']['dockq'], ch['C']['dockq']
    clean = (ch['B']['iptm'] >= 0.45 and ch['C']['iptm'] >= 0.45
             and ch['B']['design_bc_contacts'] >= 20
             and ch['B']['design_bc_clashes'] == 0
             and (dqB or 0) >= 0.8 and (dqC or 0) >= 0.8)
    mark = ''
    if unit >= 0.70 and clean:
        adv += 1
        mark = ' ADV'
    print(f'{name:14}{ch["B"]["iptm"]:>6.3f}{ch["C"]["iptm"]:>6.3f}{unit:>6.3f}'
          f'{ch["B"]["design_bc_contacts"]:>5}{ch["B"]["design_bc_clashes"]:>4}'
          f'{(dqB or 0):>6.2f}{(dqC or 0):>6.2f}'
          f'{str(ch["B"]["worst_restraint_dist"]):>6}'
          f'{str(ch["C"]["worst_restraint_dist"]):>6}{mark}')
print(f'\nadvance rule (>=3 of 22): {adv}/22 at unit ipTM >= 0.70 with a clean profile')
