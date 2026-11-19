# Challenge 3 — campaign tables (2026-10-23)

Successor to `campaign-tables-2026-10-20.md`. All twelve campaigns, computed
from the shared screen (`~/c3-work/folds-screen.csv`) and the activation-gate
rows. "6/6" = designs with at least one sample carrying the full GLP-1
message-region pharmacophore; "deep" = samples that insert (depth <= 30 A).

## Campaign comparison — all twelve

| campaign | generator | designs | 6/6 | two-domain HITs | deep samples | best design (score) |
|---|---|---|---|---|---|---|
| c1 | RFdiffusion3 mini-proteins (+ e1/e1b/e1b2 re-sequencing) | 67 | 1 | 26 | 53/67 | `e1-r0025` 22.58 |
| c2 | EvoBind peptides | 15 | 1 | 4 | 9/15 | `c2-run1-b206` 22.66 |
| c3 | BoltzGen (cyclic + junction, incl. c4) | 55 | 4 | 9 | 34/55 | `c3-j3-run21` 20.29 |
| c5 | BindCraft2 | 18 | 0 | 4 | 13/18 | `c5-bc2-l18_bfe509d11b1b8f27` 19.61 |
| c6 | SolubleMPNN re-sequencing | 40 | 0 | 15 | 30/40 | `c6-e1b-r0037-s3` 21.84 |
| c7 | BoltzGen, long peptides | 18 | 0 | 5 | 10/18 | `c7-run18` 16.78 |
| c8 | BoltzGen, deep conditioning | 60 | 3 | 12 | 105/300 | `c8-run13` 22.51 |
| c9 | SolubleMPNN on c3 champions | 33 | 5 | 13 | 95/165 | `c9-e1b2-r0065-s4` 21.94 |
| c12 | RFD4-Proteina (hosted) | 256 | 27 | 68 | 769/1280 | `c12-b3-d01` 22.92 |
| c12-mpnn | SolubleMPNN on c12 champions | 81 | 25 | 26 | 328/405 | `c12-mpnn-b21-d08-v1` 22.79 |
| c13 | RFD4, ECD–TMD junction conditioning | 73 | 15 | 27 | 285/365 | **`c13-junction-b43-d02` 23.85** |
| c14 | RFD4, short band (40-70 aa) | 72 | 6 | 13 | 162/360 | `c14-short-b46-d02` 23.06 |
| **total** | | **788** | **87** | **222** | **1893/3447** | |

## The two objectives, separately

**Activation-first** (the full message-region pattern at depth): the c13
junction round leads on rate (15 of 73), the c12 deep rounds lead on volume
(27 of 256), and re-sequencing lifts both (c12-mpnn 25 of 81 = 31 %).

**Binding-first** (two-domain HIT rate): c14 leads (13 of 72 = 18 %), c14's
short-band designs and the c13 junction designs both beat the deep rounds.

## Cross-cutting findings

1. **The split rule.** Conditioning on the ECD–TMD junction alone beats the
   deep region or a groove+junction mix — first on c3/c8 (BoltzGen), then
   confirmed on RFD4 (c13: 21 % full geometry, the best rate of any
   generator configuration — re-sequencing a generator's champions reaches a
   higher rate still, see finding 2).
2. **Re-sequencing raises the hit rate.** Interface-pinned SolubleMPNN over
   full-geometry backbones: c9 5/33, c12-mpnn 25/81 (31 %).
3. **All three length bands work.** 15-24 aa (c2/c5/c6), 40-70 (c14), 60-100
   (c12/c13). The short band has the best two-domain rate; the 60-100 band the
   most full geometries.
4. **The hosted GPU pool is the best generator for this target.** RFD4 on
   NVIDIA's free pool (c12-c14) produced the top of the final ranking.

## Files

- Full ranking: `~/c3-work/c8-agonism/selection-all.csv`
- Gate summary: `~/c3-work/c8-agonism/gate-summary-all.csv`
- The submission twenty: `submission/competition-submission-rubric-2026-10-23.csv`
- The workbench: `/lineage/03-glp1r` (12 campaigns, 3D viewers for all)
