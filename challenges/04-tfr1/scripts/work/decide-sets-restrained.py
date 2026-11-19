#!/usr/bin/env python3
"""Apply the registered campaign-1 advance rule (restrained ipTM), with guards.

Rule (registered 2026-10-24, before the full screen; revised the same day to
0.45 with truthful wording):

  A set advances when >= 25% of its screened designs (>=6 of 24) score mean
  restrained ipTM >= 0.45 (chai-1 pocket restraints on the set's own hotspot
  residues, 5 samples). The native VP1u reference scores 0.42-0.48 under the
  same protocol, so 0.45 means "level with the native reference".

Guards (added 2026-10-25, after a stale-CSV aggregation produced a verdict
from 4 designs per set): every judged set must hold exactly 24 designs with 5
samples each; the set is derived from the design name (e0_/e1_/e2_/e12_),
never by elimination; no verdict prints when a guard fails (exit 3).

Reads ~/c4-work/logs/chai-restrained.csv; writes state/advancing-sets.txt.
"""
import csv
import pathlib
import re
import statistics
import sys

CSV = pathlib.Path.home() / 'c4-work/logs/chai-restrained.csv'
OUT = pathlib.Path.home() / 'c4-work/state/advancing-sets.txt'
THRESHOLD = 0.45
MIN_FRACTION = 0.25
EXPECTED_N = 24
EXPECTED_SAMPLES = 5


def set_of(name):
    m = re.match(r'e(\d+)_', name)
    return f"E{m.group(1)}" if m else None


rows = list(csv.DictReader(CSV.open()))
per = {}
for r in rows:
    per.setdefault(r['design'], []).append(float(r['iptm']))

per_set = {}
for design, vals in per.items():
    setname = set_of(design)
    if setname is None:
        continue
    per_set.setdefault(setname, []).append((design, vals))

problems = []
for setname, items in per_set.items():
    if len(items) != EXPECTED_N:
        problems.append(f"{setname}: {len(items)} designs, expected {EXPECTED_N}")
    for d, v in items:
        if len(v) != EXPECTED_SAMPLES:
            problems.append(f"{d}: {len(v)} samples, expected {EXPECTED_SAMPLES}")
if problems:
    print("REFUSING verdict - guard failed:")
    for p in problems:
        print("  " + p)
    sys.exit(3)

advancing = []
print(f"rule: advance when >= {MIN_FRACTION:.0%} of screened designs have "
      f"mean restrained ipTM >= {THRESHOLD}")
print(f"guards: {EXPECTED_N} designs/set, {EXPECTED_SAMPLES} samples/design - passed")
for setname in sorted(per_set, key=lambda s: int(s[1:])):
    items = sorted(((d, statistics.mean(v)) for d, v in per_set[setname]),
                   key=lambda x: -x[1])
    n = len(items)
    n_ge = sum(1 for _, v in items if v >= THRESHOLD)
    frac = n_ge / n
    adv = frac >= MIN_FRACTION
    if adv:
        advancing.append(setname)
    print(f"{setname}: n={n}, >= {THRESHOLD}: {n_ge} ({frac:.0%}), "
          f"median {statistics.median(v for _, v in items):.3f}, top: "
          + ", ".join(f"{d} {v:.3f}" for d, v in items[:3])
          + f" -> {'ADVANCE' if adv else 'no'}")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(advancing) + ("\n" if advancing else ""))
print("advancing sets:", ", ".join(advancing) if advancing else "NONE")
