# C1 — the main funnel (reference campaign)

**Strategy**: widest possible pool from the fastest generator, then filter
cheap-to-expensive: geometry, then fold confidence, then specificity.

**Tools**: hosted RFdiffusion4 (NIM, ~11 s/design), the s0 pose screen,
boltz-2, chai-1, ipSAE + ipTM + i_pDAE reads, the tri-state ranker.

**Pipeline**: 439 designs generated (PEP/PEPRIM hotspot sets, 60-110 aa)
-> s0 pose screen (contacts / ridge / peptide-first / C3 rule) -> 319
passers -> stage-1 boltz folds (5 models each) -> 27 candidates (ipSAE
gate + JDI-calibrated ipTM + i_pDAE) -> stage-2 tri-state folds (WT +
peptide-free) -> stage-3 (3 seeds + chai) -> final 20.

**Results**:
- 10 finalists: seed-stable (spread <= 0.009), chai-confident (0.77-0.84).
- 5 dual-signal designs (G12D-preferring AND peptide-dependent).
- Homology finding: 21% of the pool is >= 90% identical to natural immune
  proteins; the top 18 have zero SwissProt hits; one top-20 design was
  excluded by the gate.
- Deliverable: `records/stage3/submission-top20.fasta`.

**Status**: closed 2026-11-01. The other campaigns below compete against
its results.
