#!/usr/bin/env python3
"""Aggregate the campaign-2 restrained screen: arm-aware.

Arms (by design-name prefix):
  e12b2_*    genie3 batch-2 backbones (CA-only MPNN sequences)
  e12rfd4_*  RFD4-Proteina designs (their own sequences)
Both restrained on the E12 anchors (FASTA positions 223, 253 = auth K344, K374).
Writes ~/c4-work/logs/c2-restrained.csv and prints per-arm summaries.
"""
import csv
import math
import pathlib
import re

import numpy as np

DESIGNS = pathlib.Path.home() / 'c4-work/chai/designs'
OUT = pathlib.Path.home() / 'c4-work/logs/c2-restrained.csv'
HOTSPOTS = (223, 253)
ARMS = (('e12rfd4_', 'RFD4'), ('e12b2_', 'genie3-b2'))


def arm_of(name):
    for prefix, arm in ARMS:
        if name.startswith(prefix):
            return arm
    return None


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
    arm = arm_of(d.name)
    if arm is None or not (d / 'out').is_dir():
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
        for hs in HOTSPOTS:
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
        rows.append({'design': d.name, 'arm': arm, 'model': i,
                     'iptm': round(iptm, 3),
                     'worst_hotspot_min_dist': round(max(dists), 2) if dists else None,
                     'binder_res_at_site': len(near)})

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f'wrote {OUT} ({len(rows)} samples, {len({r["design"] for r in rows})} designs)')
per = {}
for r in rows:
    per.setdefault(r['arm'], {}).setdefault(r['design'], []).append(r['iptm'])
for arm, designs in sorted(per.items()):
    vals = sorted((np.mean(v) for v in designs.values()), reverse=True)
    n_ge = sum(1 for v in vals if v >= 0.45)
    print(f"{arm}: n={len(vals)} | >=0.45: {n_ge} ({n_ge/len(vals):.0%}) | "
          f"median {np.median(vals):.3f} | top5: "
          + ", ".join(f"{v:.3f}" for v in vals[:5]))
