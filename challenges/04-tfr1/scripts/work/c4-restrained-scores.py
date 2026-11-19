#!/usr/bin/env python3
"""Aggregate the campaign-4 mouse cross-fold: at-site read vs the human one.

Every c4mn_<name> design is scored exactly like its human counterpart was
(same at-site logic, hotspots = mouse fold indices 224/254 on the target
chain), then paired with the human mean restrained ipTM:

  delta = human mean - mouse mean   (the cross-reactivity read)

Writes ~/c4-work/logs/c4-restrained.csv and prints the paired table.
Run with the repo venv python (numpy).
"""
from __future__ import annotations

import csv
import math
import pathlib
import statistics

import numpy as np

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
OUT = WORK / 'logs/c4-restrained.csv'
HOTSPOTS = (224, 254)


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


def human_means():
    per = {}
    for f in ('c2-restrained.csv', 'c3-restrained.csv'):
        with open(WORK / 'logs' / f) as fh:
            for r in csv.DictReader(fh):
                per.setdefault(r['design'], []).append(float(r['iptm']))
    return {d: statistics.mean(v) for d, v in per.items()}


def main():
    humans = human_means()
    rows = []
    for d in sorted(DESIGNS.iterdir()):
        if not d.name.startswith('c4mn_') or not (d / 'out').is_dir():
            continue
        human_name = d.name[5:]
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
            rows.append({'design': d.name, 'human_name': human_name, 'model': i,
                         'iptm_mouse': round(iptm, 3),
                         'worst_hotspot_min_dist': round(max(dists), 2) if dists else None,
                         'binder_res_at_site': len(near)})
    with OUT.open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    per = {}
    for r in rows:
        per.setdefault(r['design'], []).append(r['iptm_mouse'])
    table = []
    for design, v in per.items():
        mouse = statistics.mean(v)
        human = humans.get(design[5:])
        delta = None if human is None else human - mouse
        table.append((mouse, design, human, delta))
    table.sort(key=lambda t: -(t[0]))
    print(f'wrote {OUT} ({len(rows)} samples, {len(table)} designs)')
    print(f'{"design":34}{"mouse":>7}{"human":>7}{"delta(h-m)":>11}')
    for mouse, design, human, delta in table:
        print(f'{design:34}{mouse:7.3f}'
              f'{"" if human is None else f"{human:7.3f}"}'
              f'{"" if delta is None else f"{delta:11.3f}"}')


if __name__ == '__main__':
    main()
