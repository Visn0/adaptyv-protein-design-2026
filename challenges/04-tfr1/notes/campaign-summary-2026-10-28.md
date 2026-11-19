# Campaign summary — challenge 4 (TfR1), 2026-10-28

The read: chai restrained pocket fold, mean ipTM over 5 samples, gated by
engagement (worst-anchor distance <= 8 A AND binder residues at site > 0).
Calibration: native VP1u control 0.42-0.48; champion class ~0.78; champion
fold vs its design model DockQ 0.897 (iRMSD 0.55 A). Second reads: mouse
cross-fold, PROPKA per-site, PRODIGY (calibrated on the native interface),
ipSAE pending the Boltz-2 pass.

## Campaign status

| # | campaign | status | result |
|---|---|---|---|
| 1 | epitope triage | complete | E12 (K344/K374) advances; E0 one short (5/24); E1/E2 closed 27 Oct (0/48 engaged); E3 closed (1/15, glycan corner) |
| 2 | binding families | complete | 81 designs, 20/81 >= 0.45; champions `e12rfd4_r5d1` 0.779 and `b3_E12_r90003` 0.776 (third `b3_E12_r110007` 0.692) |
| 3 | switch layer | complete | 29 variants, 13 carry; strong pKa shifts (-1.35..-2.16) confirmed, weak class unresolved; switch costs ~0.00-0.03 of binding |
| 4 | mouse cross-fold | complete | 20/20 folded; best mouse reads `e12rfd4_r4d5` 0.760, `c3_e12rfd4_r4d5_d2` 0.688 |
| 5 | multi-chain units | closed untested (cost grounds) | block-target rescue recorded, not queued |
| 6 | selection/submission | in progress | 287 designs scored, 129 floored, top 20 selected; Boltz/ipSAE + prescreen full arm pending |

## Wave 2 (27-28 Oct)

- b4 (RFD4 arm): 26/26 folded; **hybrid set H delivered `b4_H_r1d0000` =
  0.777 (5/5 engaged)** and `b4_H_r1d0004` = 0.645 - champion class on the
  organizers' named patch + our functional tip.
- b4r (RFdiffusion arm): 16/16; underperforms on this target (best engaged
  0.420).
- Long-length sweep (110-140 aa): does not beat the short champions.
- 22 designs above 126 aa held (crash class, `scripts/work/*-long-held.txt`).

## Proton-PottsMPNN (new)

First mirrored-direction variant `ppmpnn_r4d5_l03_s1` = 0.726 (engaged 5/5),
0.034 below its parent while carrying the engineered switch layer. Five more
folding.

## Best designs (the current pool)

| design | ipTM | mouse | switch | composite | note |
|---|---|---|---|---|---|
| `c3_e12rfd4_r4d5_d2` | 0.782 | **0.688** | S5 | **95.0** | the full package - lead candidate |
| `c3_e12rfd4_r5d1_d2` | 0.779 | 0.545 | S5 | 90.0 | co-champion parent |
| `c3_e12rfd4_r5d1_l2` | 0.781 | 0.551 | S5 | 90.0 | co-champion parent, other site pair |
| `c3_e12rfd4_r5d7_d2` | 0.777 | 0.579 | S5 | 88.3 | third family |
| `c3_e12rfd4_r5d1_l3` | 0.748 | 0.471 | S5 | 85.0 | three-site ladder |
| `c3_e12b2_20_s2` | **0.802** | 0.267 | S5 | 78.3 | highest single read; weak mouse |
| `b4_H_r1d0000` | 0.777 | - | S1 | 51.7 | hybrid epitope, no mouse read yet |
| `e12rfd4_r5d1` | 0.779 | 0.364 | S1 | 53.3 | champion parent |
| `b3_E12_r90003` | 0.776 | - | S1 | 53.3 | co-champion, 81 aa |
| `e12rfd4_r4d5` | 0.760 | **0.760** | S1 | - | mouse flagship |
| `ppmpnn_r4d5_l03_s1` | 0.726 | - | designed | - | pH-conditioned redesign |

## Cross-checks

- DockQ (champion vs design model): 0.897. PRODIGY on the native interface:
  1.3-1.7 uM vs ~1 uM published (calibrated).
- POISK patent maps: 8D3 maps to peptides 373-375 (our K374 anchor); 3M12 to
  K362-K371; our top designs provably contact 374 (all) and 370/371 (r4d5
  class).
- Prescreen v0.5 (target arm): all spot-checked candidates clean on
  whole-sequence identity vs 6,695 TfR1 references; parent+His pairs count
  once in the final 20 (0.95/0.80 within-batch rule).
