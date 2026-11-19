# Campaign 4 — results (executed record)

Status: **complete** 2026-10-26 05:18 → 09:30. **Decision read: two designs are
mouse-competent at or near the top band, and one of them carries the switch —
`e12rfd4_r4d5` (mouse 0.760, delta -0.050) and `c3_e12rfd4_r3d4_d2` (mouse
0.603, delta +0.018). The tightest human designs are the weakest cross-reads.**
Deep record: `notes/c4-mouse.md`.

## What ran

| stage | tool | scope | result | artifacts |
|---|---|---|---|---|
| target prep | `scripts/work/c4-prep-mouse-target.py` | mouse construct + anchors by alignment | K346/K376 (fold 224/254), MSA depth 1024 | `~/c4-work/mouse-target.seq` |
| folds | chai, restrained on the mouse anchors, 5 samples | 20 C2 designs + 13 C3 variants = 33 designs, 165 samples | 33/33 | `logs/c4-screen.log`, `logs/c4v-screen.log` |
| paired read | `scripts/work/c4-restrained-scores.py` | human vs mouse means per design | table below; full CSV here | `mouse-scores.csv` |

## Bands (adapted instrument; `notes/strategies.md`)

| band | designs |
|---|---|
| top (<= 0.05) | `e12rfd4_r4d5` (-0.050), **`c3_e12rfd4_r3d4_d2` (+0.018)**, `e12b2_31` (-0.053) |
| second (<= 0.15) | `e12b2_29` (-0.065), `c3_e12rfd4_r4d5_d2` (+0.094), `e12rfd4_r6d2` (+0.105) |
| third | `e12b2_23`, `c3_e12rfd4_r5d7_d2`, `c3_e12rfd4_r5d1_l2/_d2`, `e12rfd4_r3d4`, ... |
| floor (human-only) | the strong human parents `r5d1`/`r5d7`/`b2_20` and the rest; deltas to +0.535 |

## Key findings

1. **Affinity and cross-transfer read as opposed** in this data: the three
   strongest human designs (r5d1 0.779, r5d7 0.761, b2_20 0.735) are the
   weakest mouse reads (0.364 / 0.266 / 0.257).
2. **Two usable cross candidates**: `r4d5` (best mouse read; its C3 double
   `r4d5_d2` also stays second-band at 0.688) and `r3d4_d2` (top band AND the
   strongest switch variant: engineered-site pKa shifts -0.39/-2.13) — the
   objectives-1-and-2 compound candidate.
3. **The His retrofits improve the mouse read in most families** (r5d7 +0.31,
   r5d1 +0.18, r3d4 +0.08; r4d5 strong; b2_20 unchanged). Observation,
   flagged; no explanation claimed.

## Caveats

- Mouse target is an AlphaFold model; the human is experimental. The
  co-folding read is weak evidence about species selectivity — the claim is
  "the interface reads on both receptors", not a KD ratio.
- Same restrained-read caveat as campaigns 1–3.

## Pointers

- `notes/c4-mouse.md` (paired table, per-family notes).
- `mouse-scores.csv` (165 samples), `designs.csv`, `fold-queue.txt`,
  `survivor-queue.txt` in this folder.
- Reproduction: `scripts/work/c4-*.{py,sh}`, `chai-c4mn-screen.service`,
  `chai-c4mnv-screen.service`.
