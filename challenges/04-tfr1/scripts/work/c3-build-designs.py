#!/usr/bin/env python3
"""Campaign 3, step 2: build the histidine variants as chai design dirs.

Input: ~/c4-work/chai/c3/positions.jsonl (from c3-pick-positions.py).

Per design (arm R, retrofit):
  - the best exposed candidate per anchor site becomes a single-His variant
    (one fold each), plus a double-His variant when both anchors are covered.
Per the ladder-design (arm L, the top-scoring design only):
  - l1/l2/l3 add exposed candidates by distance until 1/2/3 histidines are in.
  - l0 is the parent and needs no new fold.

Each variant dir (~/c4-work/chai/designs/c3_<parent>_<tag>/) holds:
  in.fasta   target chain A copied from the parent + the mutated binder chain
  msa_pqt/   copied from the parent (target MSA 1024; binder falls back to
             single-sequence exactly as its parent did — same treatment)
  restraints.csv  copied from the parent (pocket restraints unchanged)

Writes ~/c4-work/chai/c3-screen-list.txt (fold order: doubles and ladders
first) and ~/c4-work/logs/c3-variants.csv (the record).
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import shutil

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
POSITIONS = WORK / 'chai/c3/positions.jsonl'
LIST = WORK / 'chai/c3-screen-list.txt'
META = WORK / 'logs/c3-variants.csv'


def load_parent(design):
    d = DESIGNS / design
    lines = [l.strip() for l in (d / 'in.fasta').read_text().splitlines()]
    seqs = [l for l in lines if not l.startswith('>')]
    target_seq, binder_seq = seqs[0], seqs[1]
    return d, target_seq, binder_seq


def write_variant(parent, target_seq, binder_seq, positions, tag, meta_rows, order):
    seq = list(binder_seq)
    for p in positions:
        fpos = p['fasta_pos']
        before = seq[fpos - 1]
        chg = '→H' if before != 'H' else '(already H)'
        seq[fpos - 1] = 'H'
        print(f'    pos {fpos} {before}{chg} (site {p["site"]}, {p["dist"]} A, sasa {p["rel_sasa"]})')
    seq = ''.join(seq)
    if seq == binder_seq:
        print('    no change from parent — skipped')
        return None
    name = f'c3_{parent}_{tag}'
    d = DESIGNS / name
    if (d / 'out' / 'scores.model_idx_0.npz').exists():
        print(f'    {name} already scored — skipped')
        return None
    d.mkdir(parents=True, exist_ok=True)
    pd = DESIGNS / parent
    (d / 'in.fasta').write_text(
        f'>protein|A\n{target_seq}\n>protein|B\n{seq}\n')
    if (d / 'msa_pqt').exists():
        shutil.rmtree(d / 'msa_pqt')
    shutil.copytree(pd / 'msa_pqt', d / 'msa_pqt')
    shutil.copy(pd / 'restraints.csv', d / 'restraints.csv')
    meta_rows.append({'variant': name, 'parent': parent, 'tag': tag,
                      'positions': ' '.join(str(p['fasta_pos']) for p in positions),
                      'sites': ' '.join(p['site'] for p in positions),
                      'dists': ' '.join(str(p['dist']) for p in positions),
                      'n_his': len([p for p in positions]),
                      'binder_len': len(seq)})
    order.append(name)
    return name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-designs', type=int, default=10,
                    help='cap on retrofitted designs, best mean ipTM first')
    ap.add_argument('--ladder', action='store_true',
                    help='also build the arm-L ladder on the top design')
    args = ap.parse_args()

    recs = [json.loads(l) for l in POSITIONS.read_text().splitlines() if l.strip()]
    recs.sort(key=lambda r: -r['mean_iptm'])
    kept = [r for r in recs if any(c['exposed'] for c in r['candidates'])]
    print(f'designs with at least one exposed candidate: {len(kept)}; '
          f'retrofitting the top {min(args.max_designs, len(kept))}')
    meta_rows, order, doubles = [], [], []
    singles = []
    for r in kept[:args.max_designs]:
        parent = r['design']
        print(f'  {parent} (mean {r["mean_iptm"]}, arm {r["arm"]}):')
        d, target_seq, binder_seq = load_parent(parent)
        per_site = {}
        for c in sorted((c for c in r['candidates'] if c['exposed']),
                        key=lambda c: c['dist']):
            per_site.setdefault(c['site'], c)
        picks = list(per_site.values())
        if len(picks) >= 2:
            v = write_variant(parent, target_seq, binder_seq, picks[:2],
                              'd2', meta_rows, [])
            if v:
                doubles.append(v)
        for i, p in enumerate(picks, start=1):
            v = write_variant(parent, target_seq, binder_seq, [p],
                              f's{i}', meta_rows, [])
            if v:
                singles.append(v)
    if args.ladder and kept:
        r = kept[0]
        parent = r['design']
        print(f'  ladder on {parent} (top design):')
        d, target_seq, binder_seq = load_parent(parent)
        cs = sorted((c for c in r['candidates'] if c['exposed']),
                    key=lambda c: c['dist'])
        seq_used, seen_pos = [], set()
        for c in cs:
            if c['fasta_pos'] in seen_pos:
                continue
            seen_pos.add(c['fasta_pos'])
            seq_used.append(c)
        for n in (1, 2, 3):
            if len(seq_used) < n:
                print(f'    ladder l{n}: not enough exposed candidates, stopped')
                break
            v = write_variant(parent, target_seq, binder_seq, seq_used[:n],
                              f'l{n}', meta_rows, [])
    ladders = [r['variant'] for r in meta_rows if r['tag'].startswith('l')]
    order = doubles + ladders + singles
    seen = set()
    order = [v for v in order if not (v in seen or seen.add(v))]
    LIST.write_text('\n'.join(order) + '\n')
    META.parent.mkdir(parents=True, exist_ok=True)
    with open(META, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(meta_rows[0].keys()) if meta_rows else
                           ['variant', 'parent', 'tag', 'positions', 'sites', 'dists', 'n_his', 'binder_len'])
        w.writeheader()
        w.writerows(meta_rows)
    print(f'\nfolds queued: {len(order)} -> {LIST}')
    print(f'record: {META}')


if __name__ == '__main__':
    main()
