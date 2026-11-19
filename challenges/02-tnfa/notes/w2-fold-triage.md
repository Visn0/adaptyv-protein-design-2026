# W2 fold triage — the X2 shortlist against human and mouse TNF

Date: 16 October 2026. Tool: Boltz-2 2.2.1 on the local RTX 5070 (5 samples per
design, seed 42). Scores: IPSAE 10 A cutoff. Bar: ipSAE >= 0.6 AND pDockQ2 >= 0.23.
Every fold is one run in the app: `c2-fold-w2-human-*` and `c2-fold-w2-mouse-*`
(the rank 2 human fold is `c2-fold-w1-gpu`, refolded on 15 October).

## Results

| rank | design | length | human ipSAE | human pDockQ2 | mouse ipSAE | mouse pDockQ2 |
|---|---|---|---|---|---|---|
| 1 | groove-3_1_model_1 | 94 aa | 0.000 | 0.015 | 0.046 | 0.033 |
| **2** | **groove-1_0_model_1** | **73 aa** | **0.733** | **0.133** | **0.810** | **0.217** |
| 3 | groove-2_1_model_0 | 76 aa | 0.359 | 0.273 | — | — |
| 4 | groove-5_0_model_4 | 85 aa | 0.000 | 0.000 | — | — |
| 5 | groove-0_1_model_1 | 91 aa | 0.281 | 0.052 | — | — |
| 6 | groove-4_1_model_2 | 84 aa | 0.449 | 0.091 | — | — |
| 7 | groove-2_1_model_5 | 76 aa | 0.347 | 0.060 | — | — |
| 8 | groove-5_0_model_5 | 85 aa | 0.304 | 0.048 | — | — |

## What the numbers say

- **One design carries the shortlist.** Rank 2 (`groove-1_0_model_1`) is the only
  design whose best sample clears the ipSAE half of the bar (0.733). No design
  clears both halves: the best pDockQ2 with a real interface is 0.273 (rank 3,
  whose ipSAE is 0.359).
- **The rest are quiet.** Six of eight designs stay under ipSAE 0.45, and two
  (ranks 1 and 4) show no interface at all in any sample (`ipSAE 0.000`,
  `n0res 0` in the IPSAE report: the chains never come within the cutoff).
- **The mouse fold is not the check we wanted.** Rank 2 folds onto mouse TNF
  *better* than onto human (0.810 vs 0.733). The design idea is human-specific
  discrimination, so this is the wrong direction — a fold cannot prove
  selectivity, and a lab assay decides. Record it as a risk, not as a pass.
- **A weak fold is not proof of a failed binder.** A fold model gives a pose, not
  a binding energy: Boltz-2 can place a chain badly with no evidence about the
  real interaction. The campaign's real filter is the Osato assay. The verdicts
  in the app say `insufficient` on purpose.

## Method notes for the next campaign

- Do not copy a Boltz output directory while `boltz predict` writes it: the copy
  misses the `.cif` models and the import stops as `waiting_inputs`. Copy
  through a `.partial` name, then rename (see
  `~/.hermes/cache/scratch/setup/make_w2_specs.py`).
- The fold runner is one detached, resumable bash script
  (`~/.hermes/cache/scratch/setup/run-w2.sh`): it skips designs that already have
  models, so a killed job costs at most one design. Each design costs about
  3.5 min (MSA 3 min, 5 samples 30 s).
- Retire a run that stopped `waiting_inputs` before re-importing, or the design
  gets two run folders.
