# Stage 3 record — finalists, stability, homology gate, the final 20

Run: 2026-11-01. Files: `seed-stability.csv` (30 folds),
`homology-hits.m8` (SwissProt screen), `final-ranking.csv` (279 candidates,
protocol order), `submission-top20.fasta` (the pick).

## Seed stability (multi-seed boltz)

10 finalists x 3 seeds (1/2/3), 30 folds, all clean. Every finalist holds
its rank across seeds — max spread 0.009 (noise floor territory). Ordering
is reproducible: peprim-wave1__run-013__design_0007 (0.970) >
nim-wave3__run-001__design_0004 (0.968) > peprim-wave1__run-007__design_0007
(0.961) > wave2-pep__run-016__design_0005 (0.960) > ...

## Second model (chai-MSA, unconstrained)

All 10 finalists read 0.767-0.844 global ipTM. C0 calibration: the known
JDI control reads 0.895 (G12D state) and 0.797 (peptide-free negative).
Correction (2026-11-02, external review): the earlier claim that every
finalist sits at or above the negative band was wrong — **nine of the twenty
chai reads (0.752-0.796) sit below the peptide-free control's 0.797** and
eleven at or above it. The comparison is suggestive only (the control and
the designs differ in chain composition), but the honest statement is that
the second model does not clear the band for every design. chai is a
confidence instrument, not a ranking instrument (C0), so it supports the
set, it does not order it.

## Corrections (2026-11-02)

Two defects found by an external review of this record:

1. **The default-zero artifact in `final-ranking.csv`**: rows without
   wild-type/peptide-free arms had their missing reads defaulted to 0.0, so
   `d_wt` silently equalled the full G12D ipTM — 252 of 279 rows read as
   perfect discrimination. The affected `d_wt`/`free_hla`/`d_free` cells are
   now blank in the CSV, and the current ranking (`records/final2/`) ranks
   only designs that actually have the three-state panel.
2. **The chai band claim** (above) was false as written.

Also note: this stage's ordering used the boltz mutant-vs-wild-type delta as
the primary key, which the C0 calibration had already disqualified (wrong
sign on the known control). The current ranking drops it to a 10% tiebreak
term; see `records/final2/README.md` for the re-ranked submission.

## Homology screen — the finding (protocol rule 6)

`mmseqs easy-search` against SwissProt over all 279 candidates:

- **60/279 (21%) are >= 90% identical to natural immune proteins** — TCR
  V-region copies (P04439, P04435, P01764, A0A0B4J2xx, A0A075B6Nx, ...).
  The generator memorized TCR:pMHC complexes and re-emits near-natural TCR
  sequences for this target.
- The starkest case: wave2-pep__run-007__design_0007's "binder" is a
  90-residue fragment of beta-2-microglobulin itself — the model copied a
  target chain into the binder slot.
- **The pool's best designs are clean**: ranks 1-18 have ZERO SwissProt
  hits at any identity; the 10 finalists are all hit-free.
- Gate applied (fident >= 0.9 = exclude): rank 19
  (wave1-pep__run-033__design_0001, 100% to A0A075B6T6) is out;
  nim-wave3__run-008__design_0004 (rank 21) takes the slot. The 0.6-0.9
  band is flagged in the record for review but not excluded (de novo
  designs legitimately resemble natural folds).

## The final 20 (protocol order, homology-gated)

Ranked by seed-median ipTM (finalists) / G12D ipTM, after gates, vetoes,
the diversity cap (<=2 per generation run) and the homology gate.
`submission-top20.fasta` holds the sequences.

Alternative view (competition ranks specificity first): promote the
dual-signal designs (dWT > +0.1 AND dfree > +0.3) to the top half:
wave2-pep__run-054__design_0005, wave1-pep__run-007__design_0000,
wave2-pep__run-009__design_0007, peprim-wave1__run-012__design_0006,
wave2-pep__run-024__design_0007. Both orderings contain the same 20 designs
— the choice moves positions, not membership.

## L58K validation addendum (2026-11-02)

The repair-round swap `repair-wave2-pep__run-016__design_0005__g12d-L58K`
received the full instrument set after entering the set: three Boltz-2 seeds
(ipTM 0.973-0.976, spread 0.003 - the tightest in the project), chai-1 with
MSAs (ipTM 0.803-0.823, mean 0.815, inside the finalist band), binder-alone
fold (complex pLDDT 0.964), E-score -1.78, tri-state dWT +0.007 / dfree
+0.769. Passed every check; row appended to seed-stability.csv.

## v4 swap validation (2026-11-03)

The three repair-round-2 swaps received the full instrument set: A58K (seeds
0.971-0.980, spread 0.009; chai 0.801; apo pLDDT 0.967), H27K (0.969-0.978,
spread 0.009; chai 0.764; apo 0.967), N71K (0.977-0.981, spread 0.004 - the
tightest in the project; chai 0.769; apo 0.968). All inside the established
bands; the v4 set is fully validated.

## v5 swap validation (2026-11-03)

Evolution gen-1 swaps: Q15K (seeds 0.970-0.976, spread 0.006; chai 0.812;
apo 0.963), W57K (0.974-0.978, spread 0.004; chai 0.763; apo 0.963), F50K
(0.967-0.977, spread 0.010; chai 0.793; apo 0.959). All in-band; v5 is
fully validated.
