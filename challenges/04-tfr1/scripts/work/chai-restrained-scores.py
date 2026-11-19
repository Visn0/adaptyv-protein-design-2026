#!/usr/bin/env python3
"""Aggregate the restrained chai reads for design runs into one CSV + summary.

For each design dir under ~/c4-work/chai/designs/, reads the 5 prediction
models, computes chai's ipTM and the geometric hotspot engagement (min
distance per hotspot residue, count of binder residues within 5 A), and writes
~/c4-work/logs/chai-restrained.csv.

GATE (mandatory since 2026-10-27): a restrained-ipTM read only counts when
engaged - worst-anchor min distance <= 8 A and binder_res_at_site > 0. Off-site
poses can read ipTM >= 0.70 (e2_16 read 0.696 bound ~55 A away at auth
629-760), so the bar alone promotes migrated designs.

Hotspot positions are FASTA positions in the 639-residue target (author - 121).
"""
import csv
import math
import pathlib
import sys

import numpy as np

DESIGNS = pathlib.Path.home() / 'c4-work/chai/designs'
OUT = pathlib.Path.home() / 'c4-work/logs/chai-restrained.csv'
# hotspot FASTA positions per set number (author - 121)
SET_POS = {
    0: (83, 87, 89, 90, 227, 250),   # E0: auth 204,208,210,211,348,371
    1: (85, 86, 88, 253),            # E1: auth 206,207,209,374
    2: (222, 223, 226, 229, 230),    # E2: auth 343,344,347,350,351
    12: (223, 253),                  # E12: auth 344,374
}


def set_of(name):
    import re
    m = re.match(r'e(\d+)_', name)
    return int(m.group(1)) if m else None


def parse(path):
    txt = path.read_text().splitlines()
    start = next(i for i, l in enumerate(txt) if l.startswith('_atom_site.'))
    cols, i = [], start
    while txt[i].startswith('_atom_site.'):
        cols.append(txt[i].strip())
        i += 1
    names = [c.split('.')[1] for c in cols]
    atoms = []
    for l in txt[i:]:
        if not (l.startswith('ATOM') or l.startswith('HETATM')):
            continue
        p = l.split()
        if len(p) < len(cols):
            continue
        d = dict(zip(names, p))
        try:
            seq = int(d['label_seq_id'])
        except ValueError:
            continue
        atoms.append((d['label_asym_id'], seq, d['label_atom_id'],
                      float(d['Cartn_x']), float(d['Cartn_y']), float(d['Cartn_z'])))
    return atoms


rows = []
for d in sorted(DESIGNS.iterdir()):
    if '_r2' in d.name or '_s2' in d.name:
        continue  # confound reruns / second-seed reruns, not set members
    if not (d / 'out').is_dir():
        continue
    snum = set_of(d.name)
    hset = SET_POS.get(snum) if snum is not None else None
    if hset is None:
        continue
    for i in range(5):
        cif = d / 'out' / f'pred.model_idx_{i}.cif'
        npz = d / 'out' / f'scores.model_idx_{i}.npz'
        if not cif.exists() or not npz.exists():
            continue
        atoms = parse(cif)
        chains = {}
        for a in atoms:
            chains.setdefault(a[0], []).append(a)
        tgt = max(chains, key=lambda c: len(chains[c]))
        bnd = [c for c in chains if c != tgt][0]
        binder = [a for a in chains[bnd] if a[2] != 'H']
        dists, near = [], set()
        for hs in hset:
            t = [a for a in chains[tgt] if a[1] == hs and a[2] != 'H']
            if not t:
                continue
            dists.append(min(math.dist(a[3:6], b[3:6]) for a in t for b in binder))
            for b in binder:
                for a in t:
                    if math.dist(a[3:6], b[3:6]) <= 5.0:
                        near.add(b[1])
        s = np.load(npz, allow_pickle=True)
        iptm = float(np.asarray(s['iptm']).reshape(-1)[0])
        rows.append({
            'design': d.name, 'model': i, 'iptm': round(iptm, 3),
            'worst_hotspot_min_dist': round(max(dists), 2) if dists else None,
            'binder_res_at_site': len(near),
        })

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f'wrote {OUT} ({len(rows)} samples)')
per = {}
for r in rows:
    per.setdefault(r['design'], []).append(r['iptm'])
for name, vals in sorted(per.items()):
    print(f"{name}: ipTM mean {np.mean(vals):.3f} (range {min(vals):.3f}-{max(vals):.3f})")
