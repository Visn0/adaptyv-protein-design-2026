# Final submission set — re-ranked twice (2026-11-02)

**Historical snapshot.** This file documents ranking v3 as of 2026-11-02. The
set changed after that date: repair swaps, the evolution loop's promotions, the
epitope-gate re-cut (2026-11-04) and the two-for-two panel swap (2026-11-08).
The current twenty live in `../../submission/submission-05-pmhc.csv`; the swap
evidence is in `../independent-review-2026-11-08.md` and the coverage audit in
`../deep-review-2026-11-08.md`. The table below is kept as the ranking history.

**Ranking v3, after external review.** The first ranking sorted on dWT — the
boltz mutant-vs-wild-type ipTM delta — at 45% of the score, although the C0
calibration had disqualified that metric (wrong sign on the known control).
The final blend rides on validated instruments only:

| term | weight | instrument | validation |
|---|---|---|---|
| i_pDAE | 30% | interface pDAE | best top-decile precision in the benchmark |
| ipTM | 20% | fold confidence | calibrated on the controls (C0) |
| dfree | 20% | peptide dependence | correct direction on the controls (C0) |
| E_D6 | 20% | electrostatic reading (`escore.py`) | **correct sign on the JDI control** — the only specificity instrument that passes |
| dWT | 10% | mutant-vs-WT ipTM delta | disqualified as a primary key (C0); a weak tiebreak |

The E-score measures the mechanism C0 identified: the Coulomb interaction
between the binder's charged groups and the mutant aspartate's carboxylate
(distance-dependent dielectric, crude MM-GBSA class) plus the count of
charged atoms within 8 A of it. The JDI control reads -0.67 (attractive,
its charges sit 8-12 A away — the published indirect read). Magnitudes are
model-dependent; the sign is validated on one control.

| # | score | design | ipTM | i_pDAE | dWT | dfree | E_D6 | seed | chai |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 82.8 | nim-wave3 run-001 design_0004 g12d c7 | 0.973 | 0.88 | 0.01 | 0.536 | -1.13 | - | - |
| 2 | 79.1 | wave2-pep run-024 design_0007 g12d c5 | 0.955 | 0.809 | 0.06 | 0.677 | -0.87 | 0.987 | 0.782 |
| 3 | 78.1 | peprim-wave1 run-001 design_0002 | 0.975 | 0.897 | 0.012 | 0.296 | -1.22 | - | - |
| 4 | 76.8 | wave2-pep run-016 design_0005 | 0.958 | 0.733 | 0.001 | 0.665 | -0.96 | 0.986 | 0.844 |
| 5 | 68.3 | nim-wave3 run-021 design_0001 | 0.922 | 0.663 | 0.457 | 0.603 | -0.37 | 0.971 | 0.782 |
| 6 | 67.5 | mini-wave1 run-014 design_0005 | 0.964 | 0.832 | 0.006 | 0.025 | -1.77 | - | - |
| 7 | 66.1 | nat-wave1 run-004 design_0001 | 0.959 | 0.845 | 0.037 | 0.678 | 0.14 | 0.988 | 0.8 |
| 8 | 65.7 | peprim-wave1 run-013 design_0007 g12d c1 | 0.965 | 0.849 | 0.023 | 0.665 | 0.85 | - | - |
| 9 | 65.7 | mini-wave1 run-011 design_0001 g12d c5 | 0.965 | 0.793 | 0.004 | 0.752 | 1.62 | - | - |
| 10 | 65.6 | wave2-pep run-049 design_0002 | 0.95 | 0.728 | 0.181 | 0.027 | -1.92 | - | - |
| 11 | 65.6 | wave1-pep run-016 design_0003 | 0.962 | 0.78 | 0.009 | 0.029 | -1.69 | - | - |
| 12 | 65.1 | nim-wave3 run-013 design_0003 | 0.96 | 0.724 | 0.026 | 0.682 | -0.07 | 0.980 | 0.82 |
| 13 | 64.1 | wave2-pep run-026 design_0003 | 0.964 | 0.843 | 0.012 | 0.021 | -0.93 | - | - |
| 14 | 64.0 | peprim-wave1 run-012 design_0006 g12d c3 | 0.932 | 0.616 | 0.11 | 0.571 | -0.65 | - | - |
| 15 | 63.4 | nat-wave1 run-011 design_0004 | 0.966 | 0.862 | 0.018 | 0.507 | 0.1 | 0.991 | 0.799 |
| 16 | 63.3 | wave1-pep run-033 design_0003 | 0.958 | 0.81 | 0.359 | 0.392 | 0.23 | 0.988 | 0.798 |
| 17 | 62.5 | wave4-pep run-007 design_0002 | 0.951 | 0.795 | 0.124 | 0.619 |  | 0.985 | 0.79 |
| 18 | 62.5 | peprim-wave1 run-007 design_0004 | 0.933 | 0.535 | -0.001 | 0.408 | -1.51 | - | - |
| 19 | 61.5 | wave2-pep run-054 design_0005 | 0.948 | 0.608 | 0.308 | 0.682 | 1.47 | 0.984 | 0.767 |
| 20 | 60.9 | nat-wave1 run-011 design_0000 | 0.952 | 0.737 | 0.016 | 0.676 | 0.13 | - | - |

**What changed vs the first pick:** the buried champion `peprim-wave1 run-001
d0002` (0.975 ipTM / 0.897 i_pDAE / E -1.22, rank 38 under the old sort) is
entry 3; the E-score also promoted two designs the old sort never saw
(`mini-wave1 run-014 d0005`, `wave2-pep run-049 d0002`); parent/child
duplicates exit; designs with a repulsive electrostatic reading
(E > +0.5: `mini-wave1 run-011 d0001 c5`, `peprim-wave1 run-013 d0007 c1`,
`wave2-pep run-054 d0005`) stay in the set on their other validated reads but
rank low. Files: `submission-top20.fasta`, `ranking-v2.csv` (this table),
`escores.csv` (the 58-design E-scan), `ranking.csv` (the 65-candidate table
under the old key).

**Open (the review's remaining items):** a rigorous free-energy instrument
(FEP/flex-ddG) would replace the crude E-term; counter-selection as a design
objective; both are user decisions with ~5 days left.
