# Fine-tune verdict: the epoch-99 checkpoint cannot design for this target

**Conclusion: the fine-tuned checkpoint (435M, trained for 99 epochs over the
tutorial test set) destroyed the model's target conditioning. Training ran on
rented Modal A100-80GB silicon because the local 12 GB card cannot hold the
model; all generation, folding and scoring ran locally at no cloud cost. The
checkpoint is not usable for challenge 5. The v5 submission is unaffected — it
came from the frozen model through the evolution loop.**

This reverses the earlier "comparable geometry" reading. That reading measured
the *internal* quality of the generated complex (backbone bonds, packing,
radius of gyration). Internal quality survived the fine-tune. The relational
property — where the binder sits relative to the target — did not.

## Measurements

100 designs per model, same target input, same CLI, same conversion path.

| Measure | Fine-tuned (epoch 99) | Pristine (released EMA) |
|---|---|---|
| Binder–peptide min distance, median | 14.2 A (range 0.8–19.8) | 2.7 A (range 1.8–3.5) |
| Designs engaging the peptide (<4.5 A) | 0 | 100/100 |
| Median peptide contact atoms | 0 | 59 |
| Binder–HLA atom overlap <1.5 A | 59/100 | 0/100 |
| Median HLA contact atoms | 217 | 168 |

The three fine-tuned designs that appeared to touch the peptide sit at 0.8, 1.0
and 1.4 A from it — atom interpenetration, not contact. Their HLA minimum
distances are 0.08–0.41 A. A real interface sits at 2.5–4 A.

Folded reads agree. Of the 25 fine-tuned designs folded before the run was
stopped, 0 passed the organizer gate (peptide_read >= 0.61); the best read was
0.022. The unfrozen baseline batch (32 designs) reached 0.577.

## Why geometry metrics missed it

Every metric in the earlier comparison was internal to the generated structure:
CA-CA bond lengths, broken-backbone count, radius of gyration. A chain that
clashes with its target, or floats 14 A away from it, still has perfect bond
lengths. The failure is in chain-to-chain placement, so only a
placement-aware or fold-based read can see it.

## Failure mode: conditioning collapse

RFD4-Proteina is a flow-matching generator over complexes, conditioned on a
target context. Pretraining taught it to place a new chain onto a *specified*
surface patch. Fine-tuning on `test_dataset` — a narrow, non-pMHC set — for 99
epochs optimized only for reproducing that set's poses. The result:

- Structure priors are over-learned and survive: bonds, packing and sequence
  realism are intact (chain D is 78 residues of diverse sequence, not garbage).
- The conditional pathway degrades: the model stops reading the epitope
  specification and falls back on the fine-tune set's pose prior. It either
  dumps the chain onto the largest available surface (HLA, with clashes) or
  leaves it beside the complex.

The error is systematic, not random — consistent with a shifted pose prior
rather than a broken model.

## Contributing factor not yet ruled out

The pristine run used the released **EMA** weights. The fine-tuned run used a
**regular** checkpoint from the ladder (`chk_epoch_00000099_step_000000004775`),
not its EMA counterpart. EMA weights are smoother and generally more robust;
this may account for part of the degradation.

A cheap test settles it: generate ~10 designs with the fine-tuned EMA
checkpoint and apply the placement metric below. Generation is ~1.4 min per
design and the metric needs no folding.

## The instrument that catches this

Placement must be measured before any fold. For each generated complex, with
D = binder and C = peptide:

- `min ||D - C||` — a real pose reads 2.5–4 A; a floating chain reads >8 A.
- count of D atoms within 4.5 A of C — a real interface reads tens of atoms.
- `min ||D - A||` (HLA) below ~1.5 A means the chain interpenetrates the
  target, which is physically impossible and must be rejected outright.

Run this on every batch before spending GPU on folds.

## What was spent

Zero. All generation, folding and scoring was local. The 25 archived folds are
under `~/c5-work/ft-batch/`.
