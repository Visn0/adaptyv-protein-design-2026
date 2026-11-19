# Methodology — challenge 05 (KRAS G12D pMHC binder)

## The target and the discrimination problem

The assay presents the KRAS G12D peptide VVVGADGVGK (residues 7–16) on
HLA-A*11:01 + β2-microglobulin, with two counter-targets: the wild-type
peptide complex (a single D→G change at P6) and the peptide-free MHC. The
organizer crystals (7OW6 G12D, 7OW5 WT) show the mutant aspartate buried:
SASA 8.8 Å² (10.4% free), an OD2–R114 salt bridge at 2.95 Å and an OD2–Q70
hydrogen bond at 3.08 Å. The closest atom of the published JDI TCR sits
7.5 Å from that aspartate — the TCR reads the mutant through the
electrostatic field, not by contact, and gains a ~4000× mutant/WT window
that way.

## Instrument calibration (C0)

Before any design was trusted, the instruments were read against controls:
the organizers' crystals, the JDI TCR as a known-good binder, and shuffled
peptide / peptide-free negatives. Result: Boltz-2 and BindCraft2 read the
mutant-vs-wild-type comparison with the wrong sign (ipTM delta −0.043);
Chai-1 with MSAs reads it with the correct sign (0.895 vs 0.877) and is
used as supporting evidence. Fold-score deltas are therefore disqualified
as a specificity ranking signal. i_pDAE (BindCraft2's interface pDAE) was
added because the ProteinBase benchmark shows it has the best top-decile
precision of the fold metrics.

Later, the E-score's scope was tested against experimental data: a naive
whole-interface Coulomb sum does not predict measured affinity (r = −0.08
against 1,174 ATLAS TCR–pMHC mutant entries with wet-lab ΔΔG). The
site-specific form used here — the field read at the P6 site — remains the
control-validated instrument.

## Design funnel

1. **Generation** — hosted RFdiffusion4 NIM, conditioned on the peptide
   ridge (hotspots P4–P8) and variants: peptide-only, natural-reader
   hotspots measured from the JDI TCR contacts in 7OW6 (17 atoms, P4–P9,
   backbone-dominated), a 6-atom charge-first window (P5–P7), and a
   minibinder length constraint (30–50 aa). 2,264 backbones collected
   (2,247 unique) across five waves plus the three targeted campaigns; the
   final wave (200 designs) produced the strongest affinity reads of the
   project. At the end, the model was re-hosted locally
   (RFD4-Proteina-Diffusers, BSD-3): 32 fresh designs reproduced the
   hosted funnel's hit rate exactly (6 of 32 JDI-like, 19%), so the
   pipeline no longer depends on any hosted service.
2. **Pose screen** — every backbone screened for the design rule: peptide
   contact share ≥ ~0.35 with ≥ 8 ridge atoms, plus a basic nitrogen in
   the 6–8 Å shell above P6/P7. Roughly 20% pass, and the passers fold at
   4× the rate of unscreened designs.
3. **Sequencing** — ProteinMPNN on the passers; LigandMPNN with the
   interface frozen (atoms within 8 Å of the target) for surface-redesigned
   children of the ten best parents.
4. **Folding and scoring** — Boltz-2, five models per design; reads: ipTM,
   ipSAE, i_pDAE, contact geometry, P6 distance.
5. **Three-state panel** — every candidate folded against the mutant
   complex, the wild-type complex and the peptide-free MHC. Ranking
   metrics: dWT (mutant minus wild-type peptide ipTM) and dfree (mutant
   minus peptide-free HLA read); vetoes for designs that read better on a
   wrong state.

## Specificity findings along the way

- The peptide-first screen transfers to real folds (C1): 239 designs
  folded, 40 tri-stated, 6 dual-signal — specificity is rare, about 15%.
- Peptide-dense interfaces concentrate the mutation signal (C2, a mining
  campaign over 1,121 existing designs): the leader became submission
  entry 2.
- The natural reader's own contact pattern is the best variant
  conditioning (C3): 4 strict passers of 32 (28%), two submission entries.
- A too-tight charge window starves the interface (C4): 0 of 25.
- Minibinders (30–50 aa) hold up: 11 of 37 JDI-like, and the project's
  strongest free-state dependence (dfree +0.70).
- Surface naturalization preserves stability but erodes the discrimination
  signal in 8 of 10 children (C6) — the specificity lives in the exact
  sequence, not the interface geometry alone. Two children kept the dual
  signal and are submitted.
- Five design rules mined from the project's own data (length 55–80 aa,
  low serine/polar content, high helical fraction, acidic charge, tight
  HLA-contact budget) predicted 3 new dual-signal designs out of 8 blind
  candidates (C7) — including the project's best wild-type discriminator
  (dWT +0.457, apo pLDDT 0.981).
- Cross-panning against G12V/G12C and the 9-mer register is flat with this
  instrument (C8): the fold reads cannot resolve single-point peptide
  variants; the three-state panel and the wet-lab assay settle specificity.
- A third generator (genie3, CA-only output) produced no passing design in
  70 folds (C9); the retry path (full-atom reconstruction before screening)
  is documented. A fourth (BoltzGen) was evaluated later: its designs dock
  confidently but do not engage the peptide (peptide_read 0.10 max vs the
  RFD4's 0.58 on the same funnel), so it was not adopted.
- The specificity instrument that works is explicit electrostatics: the
  E-score (Coulomb interaction between binder charged groups and the P6
  aspartate, distance-dependent dielectric, plus charged-atom counts within
  8 Å) is the only metric whose control passes — the JDI reads the correct
  sign (−0.67). Fifteen of the nineteen submitted designs read negative
  (best −3.75). Four entries read neutral to positive (+0.14 to
  +1.47: nat-wave1 run-004 d0001, wave1-pep run-033 d0003,
  peprim-wave1 run-013 d0007 c1, wave2-pep run-054 d0005) and stay in the
  set on their other validated axes; the values are in
  `../records/final2/escores.csv`.
- A charge-directed repair round (24 variants of the top six: basic
  substitutions 8–11 Å from the aspartate) produced 11 fold-clean E-score
  improvements; the one strict win (L58K: E −0.96 → −1.78, fold reads
  unchanged) replaced its parent in the set. A tempting +0.497 dWT variant
  was rejected because its interface quality collapsed (i_pDAE 0.34) — the
  inflated-delta artifact class.
- An automated evolution loop then iterated: each generation bred the
  current top parents (single basic substitutions + combinations), folded
  and E-scored the children, and promoted winners under hard guardrails —
  a strict +1.0 composite margin over the parent, one winner per parent
  family, fold-quality gates. Six promotions in total reshaped the top of
  the set; the final champions are three single substitutions that each
  turned a modest parent into a leader: Q15K (composite 90.5, E −3.65),
  A16K (87.1, E −3.75 — the set's best), W57K (84.3, E −2.09). The loop
  converged after the top-16's mutation space was exhausted, which is
  itself recorded.
- Equilibrium ensembles (BioEmu2, contact-conditioned, 16 frames per state)
  show the charge reading persists under thermal motion (K58–D6 at
  7.4 ± 0.8 Å, the JDI's geometry class); the same-metric WT contrast is
  flat, confirming ensembles read stability, not specificity.
- The submitted set is electrostatically clean (same-sign charge clashes
  within 4 Å: max 2 pairs) and liability-screened (Asp-Pro sites and one
  deamidation motif, all minor and recorded).

## Selection

All tri-stated candidates were ranked under a composite that weights the
control-validated instruments first: i_pDAE 30%, ipTM 20%, peptide-free
dependence (dfree) 20%, E-score 20%, and wild-type discrimination (dWT)
10% — dWT was demoted after it failed its own control. Gates: vetoes out,
the de-novo homology gate (any SwissProt hit ≥ 90% identity excludes; one
100% antibody V-region copy was caught), and a diversity cap of two designs
per generation run. Every submitted design then received the full
instrument set: three-seed folds (medians 0.960–0.993, spread ≤ 0.01; the
evolution champions at spread ≤ 0.006), Chai-1 MSA cross-checks
(supporting only), binder-alone folds (the champions at pLDDT 0.96–0.97)
and the homology screen (clean).
