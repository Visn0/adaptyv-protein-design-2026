#!/usr/bin/env python3
"""Multi-chain (C5) evaluation: per-chain-pair reads for the two-chain units.

For each c5_* design and each of the 5 fold samples:
  - chai scores npz: global ipTM + per_chain_pair_iptm matrix + chain_chain_clashes
  - PRODIGY  : dG/Kd for the whole unit (A vs B,C) and for every pair
  - DockQ v2 : fold vs the RFD4 design model, per interface (recapitulation)
  - anchor contacts: B/C atoms within 4.5 A of K223 / K253 (fold numbering)

Usage:  c5-restrained-scores.py [design_name_glob] [--ref path.cif]
Writes  ~/c4-work/logs/c5-restrained.csv
"""
from __future__ import annotations

import csv
import itertools
import math
import pathlib
import re
import subprocess
import sys

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
OUT = WORK / 'logs/c5-restrained.csv'
VENV = _repo_root() / '.venv/bin'
ANCHORS = (223, 253)


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
                              p[idx['label_atom_id']],
                              float(p[idx['Cartn_x']]), float(p[idx['Cartn_y']]),
                              float(p[idx['Cartn_z']])))
            except ValueError:
                continue
    return atoms


def prodigy(cif, selection):
    try:
        r = subprocess.run([str(VENV / 'prodigy'), str(cif), '--selection', *selection],
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


def dockq(model_cif, ref_cif):
    """Total DockQ and the minimum per-interface DockQ of the fold vs design."""
    if not ref_cif or not pathlib.Path(ref_cif).exists():
        return None, None
    try:
        r = subprocess.run([str(VENV / 'DockQ'), str(model_cif), str(ref_cif), '--short'],
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return None, None
    total = None
    per = []
    for line in r.stdout.splitlines():
        if line.startswith('Total DockQ'):
            m = re.search(r'over (\d+) native interfaces?: ([\d.]+)', line)
            if m:
                total = float(m.group(2))
        if line.startswith('DockQ '):
            per.append(float(line.split()[1]))
    return total, (min(per) if per else None)


def main() -> int:
    pat = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'c5_*'
    ref_override = None
    if '--ref' in sys.argv:
        ref_override = sys.argv[sys.argv.index('--ref') + 1]
    rows = []
    for d in sorted(DESIGNS.glob(pat)):
        if not (d / 'out').is_dir():
            continue
        m = re.match(r'c5_r(\d+)d0*(\d+)$', d.name)
        ref = pathlib.Path(ref_override) if ref_override else (
            RF / f'run-{m.group(1)}' / f'design_{int(m.group(2)):04d}.cif' if m else None)
        for i in range(5):
            cif = d / 'out' / f'pred.model_idx_{i}.cif'
            npz = d / 'out' / f'scores.model_idx_{i}.npz'
            if not cif.exists() or not npz.exists():
                continue
            s = np.load(npz, allow_pickle=True)
            iptm = float(np.asarray(s['iptm']).reshape(-1)[0])
            pp = np.asarray(s['per_chain_pair_iptm'])[0]
            cl = np.asarray(s['chain_chain_clashes'])[0]
            chain_names = sorted({a[0] for a in parse_cif(cif)})
            pair_iptm = {}
            pair_clash = {}
            for a, b in itertools.combinations(range(len(chain_names)), 2):
                key = f'{chain_names[a]}_{chain_names[b]}'
                pair_iptm[key] = round(float(pp[a][b]), 3)
                pair_clash[key] = int(cl[a][b])
            atoms = parse_cif(cif)
            byc = {}
            for a in atoms:
                byc.setdefault(a[0], []).append(a)
            anchors = {}
            for ch in chain_names[1:]:
                n = 0
                for r in ANCHORS:
                    side = [a for a in byc[chain_names[0]] if a[1] == r]
                    n += 1 if any(math.dist(x[3:6], y[3:6]) < 4.5 for x in byc[ch] for y in side) else 0
                anchors[ch] = n
            dg_u, kd_u, ic_u = prodigy(cif, [chain_names[0], ','.join(chain_names[1:])])
            dq_t, dq_min = dockq(cif, ref)
            row = {'design': d.name, 'model': i, 'iptm': round(iptm, 3),
                   'dockq_total': dq_t, 'dockq_min_interface': dq_min,
                   'prodigy_dG_unit': dg_u, 'prodigy_Kd_unit': kd_u,
                   'unit_contacts': ic_u,
                   'anchors_hit': ';'.join(f'{k}={v}' for k, v in anchors.items())}
            for key in pair_iptm:
                row[f'iptm_{key}'] = pair_iptm[key]
                row[f'clashes_{key}'] = pair_clash[key]
                dg_p, kd_p, ic_p = prodigy(cif, list(key.split('_')))
                row[f'dG_{key}'] = dg_p
                row[f'Kd_{key}'] = kd_p
            rows.append(row)
    if not rows:
        print('no scored designs found')
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with OUT.open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f'wrote {OUT} ({len(rows)} samples, {len({r["design"] for r in rows})} designs)')
    per = {}
    for r in rows:
        per.setdefault(r['design'], []).append(r)
    for name, rs in sorted(per.items()):
        iptm = np.mean([r['iptm'] for r in rs])
        dq = [r['dockq_total'] for r in rs if r['dockq_total'] is not None]
        print(f'{name}: ipTM {iptm:.3f} | DockQ {np.mean(dq):.3f}' if dq else
              f'{name}: ipTM {iptm:.3f} | DockQ n/a | {rs[0]["anchors_hit"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
