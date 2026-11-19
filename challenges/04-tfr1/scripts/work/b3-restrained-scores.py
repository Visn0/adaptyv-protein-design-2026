#!/usr/bin/env python3
"""Aggregate the batch-3 restrained screen (hosted RFD4, b3_* designs).

Arms by prefix:
  b3_E12_*  anchors K223/K253           (auth 344/374)
  b3_E3_*   anchors K110/K223/K253      (auth 231/344/374)
Same read as every restrained screen: mean ipTM over 5 samples plus the
hotspot geometry check. Writes ~/c4-work/logs/b3-restrained.csv.
"""
import csv
import math
import pathlib

import numpy as np

DESIGNS = pathlib.Path.home() / 'c4-work/chai/designs'
OUT = pathlib.Path.home() / 'c4-work/logs/b3-restrained.csv'
ANCHORS = {'b3_E12_': (223, 253), 'b3_E3_': (110, 223, 253)}


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
                atoms.append((p[idx['label_asym_id']], int(p[idx['label_seq_id']]),
                              p[idx['label_atom_id']],
                              float(p[idx['Cartn_x']]), float(p[idx['Cartn_y']]),
                              float(p[idx['Cartn_z']])))
            except ValueError:
                continue
    return atoms


rows = []
for d in sorted(DESIGNS.iterdir()):
    hs = next((v for k, v in ANCHORS.items() if d.name.startswith(k)), None)
    if hs is None or not (d / 'out').is_dir():
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
        binder = [a for c in chains if c != tgt for a in chains[c]]
        dists, near = [], set()
        for h in hs:
            t = [a for a in chains[tgt] if a[1] == h]
            if not t:
                continue
            dists.append(min(math.dist(a[3:6], b[3:6]) for a in t for b in binder))
            for b in binder:
                for a in t:
                    if math.dist(a[3:6], b[3:6]) <= 5.0:
                        near.add(b[1])
        iptm = float(np.asarray(np.load(npz, allow_pickle=True)['iptm']).reshape(-1)[0])
        rows.append({'design': d.name, 'model': i, 'iptm': round(iptm, 3),
                     'worst_anchor_min_dist': round(max(dists), 2) if dists else None,
                     'binder_res_at_anchors': len(near)})

with OUT.open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f'wrote {OUT} ({len(rows)} samples, {len({r["design"] for r in rows})} designs)')

for arm in ANCHORS:
    per = {}
    for r in rows:
        if r['design'].startswith(arm):
            per.setdefault(r['design'], []).append(r)
    vals = sorted(((np.mean([x['iptm'] for x in v]), k) for k, v in per.items()), reverse=True)
    n_ge = sum(1 for v, _ in vals if v >= 0.45)
    thresh = max(1, math.ceil(0.25 * len(vals)))
    print(f"\n{arm} n={len(vals)} | >=0.45: {n_ge} ({n_ge/len(vals):.0%}) | "
          f"25% rule needs {thresh} | median {np.median([v for v, _ in vals]):.3f}")
    for v, k in vals[:6]:
        print(f"   {k}: {v:.3f}")
