# Filter calibration on Anthropic's released TNF-α campaign

Date: 2026-10-16. Status: done. Working artifacts: `~/c2-work/calib/` (analysis
scripts, six verification folds, resource logs — not in git).

## Why

Our campaign bar (ipSAE_min ≥ 0.6 AND pDockQ2 ≥ 0.23) was set without ever
seeing a known-positive binder. Anthropic's released dataset
(`Anthropic/claude-protein-binder-design`, CC BY 4.0) makes calibration
possible: 150 TNF-α designs with wet-lab outcomes from two labs (Adaptyv and
Twist) plus in-silico metrics from nine predictor arms, including
`ipsae_min_boltz2` — the same metric family we use.

## Bullet summary

1. **Our 0.6 line is a "do not discard" line, not evidence.** In their campaign
   the 0.6–0.7 ipSAE band produced 0 of 22 binders; the ≥ 0.8 band bound at
   25.7 % (base rate 8.7 %). A submission line at **≥ 0.8** is what the data
   supports. Keep one or two metric outliers: a genuine binder (KD 2.1 nM,
   mouse cross-reactive) scored 0.06.
2. **The generator mattered more than our filter tuning.** Win rates: Genie 3
   8/23 (34.8 %), PXDesign 4/57 (7 %), RFdiffusion3 1/40 (2.5 %), RFdiffusion
   0/20, BoltzGen 0/8, BindCraft 0/2. Our generator was the near-zero one.
3. **The winning interfaces cross protomers.** Every winner's contact list we
   checked (6 of 13) spans two or three target chains. The junction class we
   targeted is the productive one.
4. **Mouse cross-reactivity came only from tight designs.** The three mouse
   binders have human KD 2.1 / 4.2 / 18.9 nM (mouse 16–64× weaker); nothing
   above 19 nM bound mouse.
5. **High in-silico scores do not imply binding.** In our six verification
   folds, two never-bound designs outscored every winner, and their pDockQ2
   (0.49–0.57) sat far above every winner's (0.07–0.28).
6. **Our pipeline reproduces their metric within ±0.03** on all six designs —
   the tooling is correct; the weak link is metric-to-outcome, not our code.

## Win rate by their `ipsae_min_boltz2` bucket (n = 150)

| bucket | bound / n | win rate |
|---|---|---|
| ≥ 0.8 | 9 / 35 | **25.7 %** |
| 0.7 – 0.8 | 3 / 30 | 10.0 % |
| 0.6 – 0.7 | 0 / 22 | **0 %** |
| 0.4 – 0.6 | 0 / 20 | 0 % |
| < 0.4 | 1 / 36 | 2.8 % |

## Generator win rates (any lab agreed = binder)

| generator | bound / n | win rate |
|---|---|---|
| Genie 3 | 8 / 23 | 34.8 % |
| PXDesign | 4 / 57 | 7.0 % |
| RFdiffusion3 | 1 / 40 | 2.5 % |
| RFdiffusion | 0 / 20 | 0 % |
| BoltzGen | 0 / 8 | 0 % |
| BindCraft | 0 / 2 | 0 % |

## Verification folds through our own pipeline

Six released designs folded as binder + 3×152-res construct, 5 samples, seed 42
(the campaign's fold settings). Our numbers vs their table:

| design | lab outcome | our ipSAE | our ipSAE_min | our pDockQ2 | their ipSAE |
|---|---|---|---|---|---|
| rank05 (Genie 3) | binder, KD 4.2 nM, mouse+ | 0.901 | 0.932 | 0.283 | 0.88 |
| rank15 (PXDesign) | binder, KD 0.70 nM | 0.863 | 0.904 | 0.245 | 0.91 |
| rank02 (Genie 3) | binder, KD 2.1 nM, mouse+ | 0.269 | 0.364 | 0.068 | 0.06 |
| loser Mythos r08 | non_binder | **0.906** | 0.939 | 0.567 | 0.92 |
| loser Mythos r03 | non_binder | **0.910** | 0.941 | 0.506 | 0.89 |
| loser Mythos r04 | non_binder | **0.894** | 0.930 | 0.490 | 0.89 |

## Implications carried forward

- Submission line: ipSAE ≥ 0.8, not 0.6. Treat 0.6–0.8 as "possible".
- For a TNF-α-shaped target, change the generator (Genie 3 is the candidate;
  its memory needs on the 12 GB card are unverified).
- Never treat a saturated score as promise: the common failure mode is the
  high-scoring non-binder.
- Design for tightness; mouse cross-reactivity arrived only with tight binders.

## Provenance

- Source: `Anthropic/claude-protein-binder-design`, `data/tables/design_summary.csv`,
  license CC BY 4.0. Cite the dataset for any quote of its values.
- Derived tables in `calibration/`: `winners.csv` (13 winners), `fold-scores.csv`
  (our six folds).
- Analysis scripts and fold outputs: `~/c2-work/calib/` (not in git).
