#!/usr/bin/env python3
"""Aggregate the campaign-3 switch-variant screen: at-site read vs parent (gate 1).

Every c3_<parent>_<tag> design dir is scored exactly like its parent was
(same hotspots 223/253 on the target chain, same at-site logic), then compared:

  gate 1 (c3 README, adapted to the restrained instrument): the variant is
  discarded when its mean restrained ipTM falls more than 0.10 below its
  parent's. Absolute values are printed as well, and anything under the 0.45
  pool line is flagged for the record.

Writes ~/c4-work/logs/c3-restrained.csv (samples) and prints the per-variant
table. Run with /usr/bin/python3 (numpy only).
"""
from __future__ import annotations

import csv
import json
import math
import pathlib
import statistics

import numpy as np

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
OUT = WORK / 'logs/c3-restrained.csv'
PARENT_SCORES = WORK / 'logs/c2-restrained.csv'
POSITIONS = WORK / 'chai/c3/positions.jsonl'
HOTSPOTS = (223, 253)


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


def split_name(name):
    body = name[3:]                    # drop 'c3_'
    parent, _, tag = body.rpartition('_')
    return parent, tag


def main():
    parent_means = {}
    with open(PARENT_SCORES) as fh:
        per = {}
        for r in csv.DictReader(fh):
            per.setdefault(r['design'], []).append(float(r['iptm']))
        parent_means = {d: statistics.mean(v) for d, v in per.items()}

    rows = []
    for d in sorted(DESIGNS.iterdir()):
        if not d.name.startswith('c3_') or not (d / 'out').is_dir():
            continue
        parent, tag = split_name(d.name)
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
            rows.append({'design': d.name, 'parent': parent, 'tag': tag, 'model': i,
                         'iptm': round(iptm, 3),
                         'worst_hotspot_min_dist': round(max(dists), 2) if dists else None,
                         'binder_res_at_site': len(near)})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f'wrote {OUT} ({len(rows)} samples, {len({r["design"] for r in rows})} variants)')

    per = {}
    for r in rows:
        per.setdefault(r['design'], []).append(r['iptm'])
    table = []
    for design, v in per.items():
        parent, tag = split_name(design)
        mean = statistics.mean(v)
        pm = parent_means.get(parent)
        delta = None if pm is None else mean - pm
        keep = delta is not None and delta >= -0.10
        table.append((mean, design, parent, tag, pm, delta, keep))
    table.sort(reverse=True)
    print(f'\n{"variant":34}{"mean":>7}{"parent":>8}{"delta":>8}  gate1')
    for mean, design, parent, tag, pm, delta, keep in table:
        flag = 'KEEP' if keep else 'DISCARD'
        if keep and mean < 0.45:
            flag += ' (under pool line)'
        print(f'{design:34}{mean:7.3f}{(pm if pm else float("nan")):8.3f}'
              f'{(delta if delta is not None else float("nan")):8.3f}  {flag}')

    best = {}
    for r in rows:
        cur = best.get(r['design'])
        at_site = int(r['binder_res_at_site'] or 0) > 0
        score = float(r['iptm'])
        if cur is None or (at_site and score > cur[1]):
            best[r['design']] = (int(r['model']), score, at_site)
    with open(WORK / 'chai/c3/best-models.json', 'w') as fh:
        json.dump(best, fh, indent=1)
    print(f'\nbest at-site models recorded for {len(best)} variants '
          f'-> {WORK / "chai/c3/best-models.json"}')


if __name__ == '__main__':
    main()
