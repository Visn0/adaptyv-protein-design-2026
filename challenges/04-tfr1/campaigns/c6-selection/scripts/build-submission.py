#!/usr/bin/env python3
"""Build the competition submission file from the campaign-6 selection.

Challenge-3 parity: the submission is written by one script from the
selector's output, so the file cannot drift from the ranking that produced
it (`campaigns/c6-selection/scripts/select-top20.py`). The file format is
the organizers' template: name, sequence, molecule_class.
"""
from __future__ import annotations

import csv
import pathlib

WORK = pathlib.Path.home() / 'c4-work'
DESIGNS = WORK / 'chai/designs'
# The selector's committed record (newest wins), so a clone can rebuild the
# submission without the work directory (review 2026-10-30, finding 8).
# This script lives in campaigns/c6-selection/scripts/, so parents[3] is the
# challenge root.
CH4 = pathlib.Path(__file__).resolve().parents[3]
RECORD_DIR = CH4 / 'records'
_candidates = sorted(RECORD_DIR.glob('selection-top20-*.csv'))
TOP20 = _candidates[-1] if _candidates else WORK / 'c6/selection-top20.csv'
OUT = CH4 / 'submission/submission-04-tfr1.csv'


def binder_seq(name: str) -> str:
    parts = (DESIGNS / name / 'in.fasta').read_text().split('>')
    return parts[2].split('\n')[1].strip()


def main() -> None:
    picks = list(csv.DictReader(open(TOP20)))
    assert len(picks) == 20, f'expected 20 picks, found {len(picks)}'
    names = [p['design'] for p in picks]
    assert len(set(names)) == 20, 'duplicate names in the picks'
    with open(OUT, 'w', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['name', 'sequence', 'molecule_class'])
        for p in picks:
            w.writerow([p['design'], binder_seq(p['design']), 'single_chain'])
    print(f'wrote {OUT} ({len(picks)} designs, rank order)')


if __name__ == '__main__':
    main()
