# Submission set — Challenge 02 (assembled 2026-10-18)

Status: the in-silico campaign is complete. No wet-lab data exists for any
design below. Every number comes from the local pipeline (Boltz-2 co-folds,
ipSAE + designed-site screen, PROPKA linkage scorer).

The brief ranks the objectives: (1) bind human TNF-alpha at pH 7.4, no
detectable binding at pH 6.0; (2) mouse cross-reactivity (measured at pH 7.4);
(3) affinity. The designs below carry all three, measured.

## The picks (ranked)

**1. `sr2-ds-mce-14-v6-r2c`** — ONE substitution (E33H) of the best dual design:

    SETARIRAARAEAEALLAQAKAAKNAEARQAAHRAILLYDRALAGDASALAPAEAALAKARALV

- Human: ipSAE 0.849, 5/5 samples at the designed two-protomer junction.
- Mouse: 0.847, 5/5 — released-winner calibration level on both species at once.
- Switch: delta_log_Ka +1.738 (54.7x toward pH 7.4; its parent scores -0.113).
  Mechanism: Glu33 forms a salt bridge to a conserved interface lysine; the
  E33H swaps it for a histidine that protonates at pH 6.0 against the
  positively charged lysine and releases the binder.
- Paired control: `ds-mce-14-v6` (the same binder without the histidine).

**2. `sr2-ds2-mce-14-v7-v1-r2a`** — Q30H+E33H of the mouse-record family:

    SEAARIRALRAEAEALLAQAKAAKNAEARHAAHRAILLYDRALAGDATALAPAEAALAKARALV

- Human 0.843 (5/5), mouse 0.860 (5/5), switch +0.734 (5.4x).
- Paired control: `ds2-mce-14-v7-v1`.

**3. `sr2-ds-mce-14-v6-r2a`** — Q30H+E33H of the champion family:

    SETARIRAARAEAEALLAQAKAAKNAEARHAAHRAILLYDRALAGDASALAPAEAALAKARALV

- Human 0.851 (5/5), mouse 0.852 (5/5), switch +0.629 (4.3x).
- Paired control: `ds-mce-14-v6`.

## Supporting candidates

| design | human | mouse | switch | note |
|---|---|---|---|---|
| sr6-r37 | 0.811 (5/5) | 0.872 (5/5) | +0.169 (1.5x) | 2-His variant; the highest mouse score in the project |
| sr1-mce-14-b | 0.659 (5/5) | 0.703 (5/5) | +0.836 (6.9x) | alternative switch geometry (3 His) |
| ds-mce-14-v6 | 0.854 (5/5) | 0.856 (5/5) | -0.113 | best no-switch dual; r2c's control |
| ds2-mce-14-v7-v1 | 0.824 (5/5) | 0.868 (5/5) | -0.198 | mouse-record no-switch |
| e1b-d7x-t3-3-v6 | 0.871 (5/5) | 0.632 | — | the human-target record |

## Caveats (all of them)

- In-silico only. The ipSAE calibration transfers from the released campaign
  (our pipeline reproduces its scores within ±0.03); the linkage scorer is
  rank-grade and conservative by about two orders against FcRn, so the SIGN
  and relative magnitude of the switch are the readable parts.
- The 54.7x switch magnitude is the highest this project has measured and is
  above every value the scorer produced in its own validation (FcRn: -1.02,
  the known >100-fold real switch, scored two orders conservative). The assay
  decides.
- Cross-reactivity here means co-fold confidence at the designed site on both
  species, nothing more.
- Every claim above names its artifact: `notes/calibration/*.csv`,
  `notes/genie3/genie3-all-scores.csv`, `notes/linkage-check.md`,
  `notes/switch-retrofit-01` records in the working tree
  (`~/c2-work/switch-retrofit-01/`).

## Files

- Ranks and raw scores: `notes/calibration/sr2-linkage-ranked.csv`,
  `notes/calibration/sr6-linkage-ranked.csv`, `notes/calibration/sr1-linkage-ranked.csv`.
- Folds: `~/c2-work/genie3/folds/sr*` (sequences + models);
  screens: `notes/genie3/genie3-all-scores.csv`.
- The story: `notes/linkage-check.md`, `notes/views-review-mce14.md`, and the
  experiment READMEs in `~/c2-work/switch-retrofit-01/`.

## Submitted (2026-10-18)

Submission 1 on Proteinbase — **DESIGNATED**. All 8 designs uploaded from
`submission/competition-submission-2026-10-18.csv`, with the design method
`Genie 3 + ProteinMPNN + Boltz-2` attached to every one. Reviewer text:
`submission/methodology.md`; design-method fields: `submission/design-method.md`.

Proteinbase ids seen on the submission page (page order, sorted by their
Boltz2 ipSAE — mapping to our names to be confirmed):
crimson-swan-quartz, gentle-raven-ivy, noble-ram-granite, golden-ram-willow,
silver-mole-bronze, calm-dove-leaf, …
