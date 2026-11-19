# BoltzGen verdict: not adopted as the generator

Run: 8 designs, its full 6-step pipeline, our target spec (mirrors the shipped
helicon_against_peptide_in_pmhc example), then through OUR funnel after fixing a
chain-order mismatch (BoltzGen emits A=binder; our pipeline expects A=HLA).

## Head-to-head on our instruments

| metric | RFD4-Proteina (32) | BoltzGen (8) |
|---|---|---|
| ipTM_pep | up to 0.959, 6/32 JDI-like | 0.965-0.974, 8/8 |
| peptide_read | up to 0.577 | 0.101 max |
| p6 min distance | 5.5 A best | 4.3 A best, then 6.6, 8.6, 16-28 A |
| E_D6 | best -0.86 | best -0.06 |

## Reading

BoltzGen's designs dock confidently but do not engage the peptide epitope:
the peptide_read is 5x worse than the RFD4's best and almost all are flat on the
E-score. Its internal metrics rank these designs as good; our epitope-specific
instruments say otherwise. 8 designs is a small sample and its recommended
campaign is 10,000+, so this is a plumbing verdict, not a final quality claim -
but nothing here motivates displacing the RFD4, and the training program
proceeds against the RFD4 as planned.
