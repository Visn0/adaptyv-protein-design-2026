#!/usr/bin/env python3
"""Aggregate the wave-2 restrained screens (b4 = RFD4 arm, b4r = RFdiffusion).

Arms by prefix (fold numbering):
  *_H_*     anchors K87/K90/K223/K253      (auth 208/211/344/374 hybrid)
  *_E12L_*  anchors K223/K253              (auth 344/374 long sweep)
  *_E0L_*   anchors K83/K87/K89/K90/K227/K250  (auth 204..371 long sweep)

Same read as every restrained screen: mean ipTM over 5 samples, the anchor
geometry check, and the engagement gate (worst-anchor <= 8 A AND binder
residues at site > 0). Writes logs/b4r-restrained.csv and logs/b4-restrained.csv.
"""
import csv
import math
import pathlib

import numpy as np

DESIGNS = pathlib.Path.home() / 'c4-work/chai/designs'
LOGS = pathlib.Path.home() / 'c4-work/logs'
ANCHORS = {
    'b4r_H_': (87, 90, 223, 253),
    'b4r_E12L_': (223, 253),
    'b4r_E0L_': (83, 87, 89, 90, 227, 250),
    'b4_H_': (87, 90, 223, 253),
    'b4_E12L_': (223, 253),
    'b4_E0L_': (83, 87, 89, 90, 227, 250),
}


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
        worst = round(max(dists), 2) if dists else None
        rows.append({'design': d.name, 'model': i, 'iptm': round(iptm, 3),
                     'worst_anchor_min_dist': worst,
                     'binder_res_at_anchors': len(near),
                     'engaged': bool(worst is not None and worst <= 8.0 and len(near) > 0)})

for arm, out in (('b4r_', LOGS / 'b4r-restrained.csv'), ('b4_', LOGS / 'b4-restrained.csv')):
    sub = [r for r in rows if r['design'].startswith(arm)]
    if not sub:
        print(f'{arm}: no samples yet')
        continue
    with out.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(sub[0].keys()))
        w.writeheader()
        w.writerows(sub)
    print(f'wrote {out} ({len(sub)} samples, {len({r["design"] for r in sub})} designs)')

for tag in ANCHORS:
    per = {}
    for r in rows:
        if r['design'].startswith(tag):
            per.setdefault(r['design'], []).append(r)
    if not per:
        continue
    stats = []
    for k, v in per.items():
        eng = [x['iptm'] for x in v if x['engaged']]
        stats.append((np.mean(eng) if eng else None, len(eng), k))
    ok = sorted(((m, e, k) for m, e, k in stats if m is not None), reverse=True)
    n_ge = sum(1 for m, _, _ in ok if m >= 0.45)
    n_eng0 = sum(1 for m, e, _ in stats if m is None)
    print(f"\n{tag} n={len(stats)} | engaged >=1 sample: {len(stats)-n_eng0} | "
          f">=0.45 (engaged mean): {n_ge}")
    for m, e, k in ok[:6]:
        print(f'   {k}: {m:.3f} ({e}/5 engaged)')
