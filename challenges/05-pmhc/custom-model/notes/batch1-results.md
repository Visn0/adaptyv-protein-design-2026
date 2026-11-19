# Batch 1: the local RFD4-Proteina baseline

32 designs generated with the local RFD4-Proteina (seeds 1000-1031, one minute
each), folded with boltz, scored with s1 + E-score. Total wall time: about
90 minutes for the full pipeline.

## Headline

The local generator runs at parity with the hosted NIM:

- JDI-like interfaces (ipTM >= 0.8): 6 of 32 (19%), against the NIM campaign's
  ~15%. Best interface: batch1-017 at ipTM_pep 0.959.
- The organizer epitope gate (peptide_read >= 0.61): 0 of 32; best 0.577
  (batch1-008) - just under, and the highest peptide_read readings of the set.
- The E-score (specificity instrument): no design below -1.0; the strong
  interface designs carry positive E (wrong field direction), which is exactly
  the raw-design behavior the NIM funnel showed.

## Reading

Raw generation quality is not the bottleneck: the local model is as good as the
hosted one. Specificity is, as everywhere in this project, the rare commodity -
and this is precisely why the fine-tuning plan exists. These 32 designs (with
their measured scores) are themselves training material for the reward loop:
the pipeline now generates, folds, scores, and stores at ~1/3 the wall time of
the hosted path, with no rate limits.

## Top designs

| design | iptm_pep | ipdae_pep | peptide_read | E_D6 |
|---|---|---|---|---|
| batch1-017 | 0.959 | 0.718 | 0.574 | +3.04 |
| batch1-027 | 0.947 | 0.655 | 0.551 | +0.01 |
| batch1-008 | 0.945 | 0.733 | 0.577 | +1.61 |
| batch1-001 | 0.867 | 0.386 | 0.319 | +2.20 |
| batch1-016 | 0.822 | 0.111 | 0.084 | +0.32 |
| batch1-010 | 0.802 | 0.000 | 0.070 | +0.48 |

The top three are the candidates for the tri-state and, if they read the WT
distinctly, for the RAFT training pool.

## Artifacts

- designs: `~/c5-work/rfd4-batch1/designs/*.cif`
- folds + scores: `~/c5-work/rfd4-batch1/`
- scripts: `scripts/gen_batch.py`, `scripts/cif_to_boltz_yaml.py`,
  `scripts/analyze_batch.py`
