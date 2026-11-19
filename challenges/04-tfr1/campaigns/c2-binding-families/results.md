# Campaign 2 — results (executed record)

Status: **complete** 2026-10-25 08:28 → 2026-10-26 01:35. **Decision: the
family pool clears — 20 of 81 designs score mean restrained ipTM >= 0.45;
campaign 3 (the pH switch layer) takes them as input.** Arms: RFD4 11 of 49
(22 %), genie3 batch-2 9 of 32 (28 %) — statistically indistinguishable,
Fisher's exact p = 0.605.

## What ran

| stage | tool | scope | result | artifacts |
|---|---|---|---|---|
| generation A | genie3 (local GPU) | `11qc_e12b2`, one run, 32 backbones | pass geometry | `~/c4-work/genie3/runs/11qc_e12b2/` |
| generation B | RFD4-Proteina (hosted NIM) | E12 replicates (runs r3–r8), 49 designs | all clean, obedience logged | `~/c4-work/rfd4/E12/` |
| sequencing | ProteinMPNN | genie3 designs: CA-only (as campaign 1); RFD4 designs carry the generator's own sequences | banked | `~/c4-work/seqs/`, `~/c4-work/seqs-fullbb/` |
| folds + read | Chai-1, pocket restraints on K223/K253, 5 samples, seed 42 | 81 designs, 405 samples | 20 designs >= 0.45 | `~/c4-work/chai/designs/`, `logs/c2-restrained.csv` |
| scoring | `scripts/work/c2-restrained-scores.py` | arm-aware tables | wrote both arm summaries | `logs/c2-restrained-aggregate.log` |

Wall span 16 h, of which ~11.5 h folding; a host crash cost 4.5 h (below).

## Key findings

1. **The batch-2 pool is materially stronger than campaign 1's.** 17 designs
   score >= 0.50 (campaign 1 had 7), 13 score >= 0.60 (campaign 1: 3), and the
   top is 0.779 (`e12rfd4_r5d1`) against campaign 1's 0.752 — all well above
   the native reference ceiling of 0.48. Generating batch-2 material on the
   advancing set produced the expected step up.
2. **No generator dominance at this n.** RFD4 11/49 (22 %) vs genie3 9/32
   (28 %), Fisher p = 0.605. The challenge-2 lesson ("the generator dominates
   the outcome") motivated running both arms; this screen cannot separate them.
   Note for the record: under campaign 1's 25 % rule applied per arm, genie3
   clears (28 %) and RFD4 misses narrowly (22 %) — campaign 2 was not gated by
   that rule; the line decides the carry-forward, above.
3. **The read behaved.** Native control unchanged across the campaign
   (0.42–0.48); per-design spread stays within +-0.02 as calibrated.
4. **Robustness incident, recorded honestly.** The host display-driver crash
   (2026-10-25 ~16:25, nvlddmkm `0xD1`; triage in
   `~/windows-crash-triage-2026-10-25-nvlddmkm.md`) killed the pass mid-design
   at 44/81. It resumed at 20:59 on driver 621.01 with
   `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False` (a WSL GPU-PV allocator
   workaround; it does not touch the potentials). The design killed mid-fold
   (`e12rfd4_r4d3`) completed on resume and scores 0.682; the pre- and
   post-crash halves are consistent (top designs in both).

## Carry-forward into campaign 3 (>= 0.45, sorted)

`e12rfd4_r5d1` 0.779 · `e12rfd4_r5d7` 0.761 · `e12b2_8` 0.747 ·
`e12rfd4_r6d5` 0.741 · `e12rfd4_r6d2` 0.738 · `e12b2_20` 0.735 ·
`e12rfd4_r4d5` 0.710 · `e12rfd4_r3d4` 0.694 · `e12rfd4_r4d3` 0.682 ·
`e12b2_26` 0.655 · `e12b2_23` 0.652 · `e12rfd4_r4d6` 0.648 ·
`e12rfd4_r8d4` 0.613 · `e12b2_29` 0.550 · `e12rfd4_r7d0` 0.527 ·
`e12b2_11` 0.517 · `e12b2_6` 0.503 · `e12rfd4_r6d1` 0.474 ·
`e12b2_31` 0.453 · `e12b2_25` 0.452

Near line, recorded and not carried: `e12b2_12` 0.446.

Campaign 3 input = these 20 (per its README: champions and family members
clearing the at-site line); the arm-L ladder runs on the top family,
`e12rfd4_r5d1`.

## Caveats

- Same directed-read caveat as campaign 1: the restrained pose is a
  consistency read, not independent binding evidence (`notes/c1-triage.md`).
- The allocator flag changed mid-campaign (item 4). The flag changes memory
  handling only; the two halves score consistently, and the crash-resumed
  design lands in the top ten.
- E0, the secondary arm, was not re-run in this campaign (E12 primary by the
  campaign-1 decision).

## Batch-3 addendum (2026-10-26)

The hosted RFD4 expansion (next-experiments P1 items 1-2) folded and scored:
39 designs, 195 samples, zero fold failures.

**E12 extension (`b3_E12`, +24 new RFD4 designs).** 4/24 (17%) at mean
restrained ipTM >= 0.45 — the same band as this campaign's own 22%, within
noise. The batch produced a co-champion: **`b3_E12_r90003` 0.776**, a
statistical tie with `e12rfd4_r5d1` (0.779), plus a second at 0.692
(`b3_E12_r110007`). E12 remains the lead set; both new names enter the
selection pool for campaign 6.

**E3 (triple cation, `b3_E3`, new set {231, 344, 374}).** 1/15 (7%) at the
bar against the registered 25% rule needing 4 — **E3 does not advance, and
the direction closes as a measured negative.** Three independent reads agree:
the three-cation patch is harder (hotspot obedience mean 0.50), the N251
glycan occludes the 231 K corner (9 of 24 generated designs were built into
the glycan and excluded), and the folded remainder sits below the E12 class
(median 0.274 vs 0.292; top 0.472). Recorded, not carried. The E3 geometry
work (span 14.8 A, glycan 7.7 A) stays as the explanation.

- Scores: `~/c4-work/logs/b3-restrained.csv` (195 samples);
  scorer `scripts/work/b3-restrained-scores.py`.

## Pointers

- Scores: `~/c4-work/logs/c2-restrained.csv` (405 samples) and
  `logs/c2-restrained-aggregate.log`.
- Reproduction: `scripts/work/` — `c2-restrained-scores.py` (arm tables),
  `chai-screen-batch.sh` (the fold queue), `c2-screen-watchdog.sh`.
- Host crash: `~/windows-crash-triage-2026-10-25-nvlddmkm.md`.
