# Campaign 4 — mouse cross-fold (deep record)

Executed 2026-10-26 05:18 → 09:30. Scope: the 20 campaign-2 designs clearing
the human line + the 13 campaign-3 gate survivors = 33 designs, 165 samples,
against the mouse TfR1 construct (AF-Q62351-F1, residues 123-763; an AlphaFold
model — the structural asymmetry against the human experimental structure is
recorded, not hidden).

Protocol: identical to every human fold — chai, restrained pocket contacts on
the alignment-derived anchors (mouse K346/K376 = fold indices 224/254, 8 A),
5 samples, seed 42; binder chain on the same single-sequence fallback. The
alignment (never a fixed offset) is in `scripts/epitope_analysis.py`; prep is
`scripts/work/c4-prep-mouse-target.py`.

## The paired table (human vs mouse, mean restrained ipTM)

Full data: `campaigns/c4-mouse-crossfold/mouse-scores.csv`. Bands per
`notes/strategies.md` (adapted to this instrument): within 0.05 = top, within
0.15 = second, mouse clearly weaker = third, human-only = floor.

| design | mouse | human | delta (h-m) | band |
|---|---|---|---|---|
| e12rfd4_r4d5 | 0.760 | 0.710 | -0.050 | top |
| **c3_e12rfd4_r3d4_d2** | **0.603** | 0.621 | **+0.018** | **top** |
| e12b2_31 | 0.507 | 0.453 | -0.053 | top |
| e12b2_29 | 0.615 | 0.550 | -0.065 | second |
| c3_e12rfd4_r4d5_d2 | 0.688 | 0.782 | +0.094 | second |
| e12rfd4_r6d2 | 0.633 | 0.738 | +0.105 | second |
| e12b2_23 | 0.497 | 0.652 | +0.156 | third |
| c3_e12rfd4_r5d7_d2 | 0.579 | 0.777 | +0.198 | third |
| c3_e12rfd4_r5d1_l2 | 0.551 | 0.781 | +0.229 | third |
| c3_e12rfd4_r5d1_d2 | 0.545 | 0.779 | +0.233 | third |
| e12rfd4_r3d4 | 0.528 | 0.694 | +0.166 | third |
| ... | | | | |
| e12rfd4_r5d1 (parent) | 0.364 | 0.779 | +0.416 | floor |
| e12rfd4_r5d7 (parent) | 0.266 | 0.761 | +0.496 | floor |
| e12b2_20 (parent) | 0.257 | 0.735 | +0.478 | floor |

(The floor entries continue to b2_8, r6d5, r4d6, r4d3, b2_26, b2_11 etc. with
deltas up to +0.535.)

## What the numbers say

1. **The tightest human designs are the weakest mouse cross-reads.** The three
   strongest human parents (r5d1 0.779, r5d7 0.761, b2_20 0.735) drop to
   0.364 / 0.266 / 0.257 against mouse (deltas +0.42..+0.50). Affinity on the
   human read and cross-species transfer are, in this data, opposed — the
   instructive inverse of the challenge-2 lesson that cross-reactivity came
   only from tight designs; here the mouse-competent designs are mid-table on
   the human read.
2. **Two designs read at-or-above human (mouse-competent) and one of them
   carries the switch.** `r4d5` (mouse 0.760, delta -0.050 — the single best
   cross candidate) and `r3d4_d2` (mouse 0.603, delta +0.018 — top band AND
   the strongest switch variant: per-site His pKa shifts -0.39 and -2.13, the
   latter measured 2026-10-26 to complete its family read). `b2_29`/`b2_31`
   read mouse-above-human too, but with weaker human scores.
3. **The histidine retrofits improve the mouse read in most families**
   (observation, flagged): r5d7 0.266 -> 0.579 (+0.31), r5d1 0.364 -> 0.545 /
   0.551 (+0.18), r3d4 0.528 -> 0.603 (+0.08); r4d5 stays strong (0.688),
   b2_20 unchanged (~0.26). Not explained; recorded as a read-level
   observation with the same standing caveat as everything here.

## The caveat this campaign carries (from the README, restated)

A co-folding model scoring two receptors it was never trained to discriminate
is weak evidence about species selectivity. Two designs can score identically
and behave differently in the lab. The claim supported is "the epitope is
conserved and the interface reads on both receptors", not "the KD ratio is
near 1". The mouse structure is a prediction and the human one is
experimental — the comparison carries that asymmetry.
