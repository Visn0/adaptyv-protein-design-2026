#!/usr/bin/env python3
"""One-shot workbench update for challenge 4 (2026-10-27):
  - viewer lists for c1-c4 (they had none; the explorer pages get built)
  - a batch-3 chapter on c2 + the 39 b3 protein rows (E12 extension, E3 close)
  - the c5 multi-chain experiment (22 rows, per-chain reads, negative verdict)
Idempotent: re-running replaces the b3 chapter/rows and the c5 experiment.
"""
from __future__ import annotations

import csv
import json
import pathlib

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
LIN = REPO / 'challenges/04-tfr1/lineage.json'
LOGS = pathlib.Path.home() / 'c4-work/logs'

VIEWERS = {
    'c1-epitope-triage': ['e12_18', 'e12_9', 'e12_6', 'e12_19', 'e0_22', 'e0_21', 'e0_0'],
    'c2-binding-families': ['e12rfd4_r5d1', 'e12rfd4_r4d5', 'e12rfd4_r3d4', 'e12rfd4_r5d7',
                            'b3_E12_r90003', 'b3_E12_r110007', 'b3_E12_r100005'],
    'c3-switch-layer': ['c3_e12rfd4_r5d1_l1', 'c3_e12rfd4_r5d1_l2', 'c3_e12rfd4_r5d1_l3',
                        'c3_e12rfd4_r4d5_d2', 'c3_e12rfd4_r3d4_d2'],
    'c4-mouse-crossfold': ['c4mn_e12rfd4_r4d5', 'c4mn_e12rfd4_r5d1',
                           'c4mn_c3_e12rfd4_r3d4_d2', 'c4mn_e12rfd4_r5d7'],
}

data = json.loads(LIN.read_text())
exps = {e['id']: e for e in data['experiments']}

for exp_id, viewer in VIEWERS.items():
    exps[exp_id]['viewer'] = viewer

# ---- c2: batch-3 chapter + protein rows ----
c2 = exps['c2-binding-families']
c2['chapters'] = [ch for ch in c2.get('chapters', []) if ch.get('id') != 'b3']
c2['chapters'].append({
    'id': 'b3',
    'title': 'B — batch-3: the E12 extension and the E3 close',
    'date': '2026-10-27',
    'text': ('The hosted RFD4 pool was drained further: +24 E12 designs folded '
             '(4/24 at the bar, same band as the arm itself) and a triple-cation '
             'set E3 = {231, 344, 374} was generated and screened. The E12 '
             'extension produced a co-champion — b3_E12_r90003 at 0.776, a '
             'statistical tie with r5d1 — plus a second at 0.692. E3 is closed '
             'as a measured negative: 9 of its 24 designs were built into the '
             'N251 glycan and excluded, and of the 15 that folded only 1/15 '
             'reached the bar against the rule\'s 4 — the 231K corner is '
             'glycan-shielded and the wide patch is hard.'),
    'outcome': ('39 designs, 195 samples, zero fold failures. Co-champion '
                'b3_E12_r90003 (0.776); E3 closed negative.'),
})
c2['proteins'] = [p for p in c2.get('proteins', []) if p.get('phase') != 'b3']
seen = {}
with open(LOGS / 'b3-restrained.csv') as fh:
    for row in csv.DictReader(fh):
        seen.setdefault(row['design'], []).append(float(row['iptm']))
for design in sorted(seen):
    mean = sum(seen[design]) / len(seen[design])
    arm = 'E12 extension' if design.startswith('b3_E12_') else 'E3 triple-cation (closed negative)'
    c2['proteins'].append({
        'design': design, 'sequence': None, 'phase': 'b3',
        'note': f'batch-3 · {arm} · restrained ipTM {mean:.3f}',
        'human': None, 'mouse': None, 'ph': None,
        'ipsae_min': None, 'pdockq2': None, 'iptm': round(mean, 3)})

# ---- c5: the multi-chain experiment ----
per = {}
with open(LOGS / 'c5-restrained.csv') as fh:
    for row in csv.DictReader(fh):
        per.setdefault(row['design'], {})[row['chain']] = float(row['iptm'])
c5_rows = []
for design in sorted(per):
    chans = per[design]
    unit = (chans.get('B', 0) + chans.get('C', 0)) / 2
    c5_rows.append({
        'design': design, 'sequence': None, 'phase': 'f1',
        'note': (f'per-chain folds · B {chans.get("B", float("nan")):.3f} · '
                 f'C {chans.get("C", float("nan")):.3f} · unit {unit:.3f}'),
        'human': None, 'mouse': None, 'ph': None,
        'ipsae_min': None, 'pdockq2': None, 'iptm': round(unit, 3)})
c5 = {
    'id': 'c5-multi-chain',
    'title': 'C5 — multi-chain units (two designed chains)',
    'date': '2026-10-27',
    'goal': ('Whether splitting the binder unit across two designed chains beats '
             'the single-chain class at the E12 patch.'),
    'goal_extra': ('RFD4 generated chains B and C jointly against {344K, 374K}; '
                   'the unit was read per chain because the assembled fold is '
                   'unrunnable on this host (VRAM cliff).'),
    'chapters': [
        {'id': 'g1', 'title': 'G — the hosted endpoint accepts two designed chains',
         'date': '2026-10-26',
         'text': ('The RFD4 request was extended with a second expandable segment '
                  '(chain C, entity 2, its own length range). The endpoint accepted '
                  'it with zero validation errors, 8 designs in 95 seconds. 24 '
                  'designs were generated; 23/24 form a real B-C unit covering both '
                  'anchor lysines; 2 designs clashed with the N251 glycan and were '
                  'excluded; 22 folded.'),
         'outcome': '24 -> 22 designs, 23/24 real two-chain units.'},
        {'id': 'f1', 'title': 'F — the assembled fold refused the host',
         'date': '2026-10-26',
         'text': ('The three-chain fold sits at 11.9 of 12.2 GB VRAM and runs its '
                  'trunk ~10x slow (775 s/recycle against an 82 s baseline); two '
                  'attempts, one on a cold boot, and the first ended in a host '
                  'crash. The read was taken per chain instead: each design folded '
                  'twice (chain B and chain C alone, own interface-derived '
                  'restraints) - 44 folds, all complete. The B-C interface stays '
                  'validated from the design models.'),
         'outcome': '44 per-chain folds; protocol adaptation recorded.'},
        {'id': 'd1', 'title': 'D — verdict: measured negative',
         'date': '2026-10-27',
         'text': ('0 of 22 designs reached the registered bar (unit ipTM >= 0.70; '
                  'best 0.502), and DockQ against the design models reads ~0.1 '
                  'where single-chain controls read 0.89-0.90 - the folds do not '
                  'return to the designed poses. One chain of one design reads '
                  'like an ordinary binder while its partner is flat: the '
                  'architecture fails, not the chain. The literature pass '
                  '(24 sources) is kept in the campaign folder.'),
         'outcome': 'Closed as measured-negative by the pre-registered rule.'},
    ],
    'proteins': c5_rows,
    'scores': [], 'best': 'c5_r3d6',
    'summary': ('A two-chain binder unit generated by RFD4, read per chain after '
                'the assembled fold proved unrunnable; closed as measured-negative.'),
    'verdict': 'measured-negative',
    'verdict_detail': ('0/22 at unit ipTM >= 0.70 (best 0.502); DockQ vs the '
                       'design models ~0.1 vs 0.89-0.90 for single-chain controls.'),
    'viewer': ['c5B_r3d0006', 'c5C_r3d0006', 'c5B_r3d0004', 'c5B_r2d0001', 'c5B_r1d0003'],
}

data['experiments'] = [e for e in data['experiments'] if e['id'] != 'c5-multi-chain']
data['experiments'].append(c5)
LIN.write_text(json.dumps(data, indent=2))
print('lineage updated:', [e['id'] for e in data['experiments']])
print('c2 proteins:', len(exps['c2-binding-families']['proteins']), '| c5 proteins:', len(c5_rows))
