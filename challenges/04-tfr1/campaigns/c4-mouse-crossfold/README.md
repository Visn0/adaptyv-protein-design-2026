# Campaign 4 — mouse cross-fold

Status: **complete** 2026-10-26 → 2026-10-30 — the pool grew with every
round and now covers **63 designs** (33 C2+C3 survivors, then the switch
variants and the liability repairs; one last fold, `b4_H_r1d0004_13_48`,
2026-10-30). Two mouse-competent candidates at the start, one carrying the
switch (`e12rfd4_r4d5`, `c3_e12rfd4_r3d4_d2`); the final twenty's mouse reads
are in `mouse-scores.csv` (running table, updated each round). Executed
record: `results.md`; deep record: `notes/c4-mouse.md`.

Instrument notes as executed (adaptations recorded, not silent):
- **The read is the restrained Chai-1 protocol, not Boltz-2.** Boltz-2 cannot
  dock on this target (`notes/c1-triage.md`); both species must be read with
  the same instrument for the delta to mean anything.
- **Anchors by alignment**: human K344/K374 -> mouse K346/K376 (fold indices
  224/254), via `scripts/epitope_analysis.py`; both conserved as lysine.
  Restraints: pocket, 8 A, identical to the human runs.
- **Mouse target MSA** is cached in `inputs/msa/5f2d464a5da3-d1024.a3m`
  (ColabFold, depth 1024) and converted to `.aligned.pqt`; prep is scripted as
  `scripts/work/c4-prep-mouse-target.py`.
- Binder chains fall back to single-sequence MSA exactly as in every human
  fold — the fold treatment is identical across species.

## Why this campaign

This is objective 2. It is ranked above affinity and below the switch.

The epitope choice already does most of the work. Every residue in sets E1 and
E2 is identical in mouse, which is why those sets were chosen over the
organizers' named patch, where all six residues are either substituted or fall in
an indel. This campaign measures whether that design intent survives an
independent fold against the mouse receptor.

It measures and it does not gate. A human-only design is still a valid objective-3
entry.

## The two facts that shape it

1. **Cross-reactivity came only from tight designs.** In Anthropic's released
   TNF-alpha campaign the three mouse-cross-reactive binders had human KD of
   2.1, 4.2 and 18.9 nM. Nothing weaker than 19 nM bound mouse at all. So
   cross-reactivity is not a property to trade against affinity. It follows from
   a tight design on a conserved epitope.
2. **The species numbering offset is not constant.** Mouse minus human author
   numbering is +3 across 359 positions and +2 across 279. There is an indel. A
   fixed offset silently mis-maps the epitope, which is the same class of error
   as AGENT.md mistake 21. Every mapping goes through the alignment in
   `scripts/epitope_analysis.py`.

## Configuration

**Mouse target.** `inputs/AF-Q62351-F1.pdb`, residues 123 to 763, the construct
the challenge page specifies. It is an AlphaFold model, not an experimental
structure, and the records must say so. If a mouse TfR1 experimental structure
exists, prefer it and record the substitution.

**Mouse hotspot numbers.** Derived from the alignment, never from an offset. For
the two conserved sets the mouse equivalents are produced by
`epitope_analysis.py` and written into the site map before any fold runs.

**Folds.** The same protocol as the human folds: Boltz-2, 5 samples, seed 42,
MSA depth-capped at 1024 rows, the same fold target size class. Identical
settings are required, because the organizers compare self-reported metrics only
within a submission and recompute ratios.

**Scope.** Every design that clears the human at-site line in campaign 2, plus
every histidine variant that clears campaign 3's gates.

## What is measured per design

| quantity | meaning |
|---|---|
| mouse at-site ipSAE, five-sample spread | does the interface form on the mouse receptor |
| mouse at-site contact | at the mouse equivalents of the designed residues |
| delta ipSAE, human minus mouse | the cross-reactivity read; the rubric's X component |
| mouse pLDDT and pDockQ2 | the same screens, same settings |
| mouse linkage sign | whether the switch direction holds in the second species |

The rubric bands, fixed in `notes/strategies.md`: at site in both species within
0.05 ipSAE is the top band, within 0.15 the next, mouse at site but clearly
weaker the third, human only the floor.

## The honest caveat this campaign must carry

A co-folding model scoring two receptors it was never trained to discriminate is
weak evidence about species selectivity. Two designs can score identically and
behave differently in the lab. The claim this campaign supports is "the epitope
is conserved and the interface forms on both receptors in prediction", not "the
KD ratio is near 1".

Because the mouse structure is a prediction and the human one is experimental,
the comparison also carries a structural asymmetry. Record it.

## What this campaign records

`notes/c4-mouse.md`: the alignment-derived mouse hotspot map, the paired
human-and-mouse fold table with both five-sample spreads, the delta ipSAE per
design, and the caveat above restated beside the numbers.
