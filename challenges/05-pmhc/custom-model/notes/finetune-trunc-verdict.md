# Fine-tune attempt: truncated complexes (2026-11-04, evening)

Goal: make 12 GB fine-tuning possible by shrinking the training complexes,
then compare fine-tuned vs frozen generations.

## What was tried

- Built a truncated dataset (binder + peptide + full beta2m + HLA residues
  1-200, the groove-carrying domains): 379 residues vs the full 449.
  Script: `scripts/truncate_for_training.py`; data in
  `~/c5-work/lora-data-trunc/`.
- Ran the 4-bit LoRA recipe on it (rank 16, bf16, gradient checkpointing
  verified active, max_tokens 520).

## Result: the wall does not move

- Full complex (620 tok): OOM at 25.99 GiB peak.
- Truncated (520 tok): OOM at 25.86 GiB peak — a 16% length cut moved the
  peak by 0.5%.
- Conclusion: the ~26 GiB allocation is effectively INPUT-INDEPENDENT for
  our sizes. Attention-style quadratic scaling would have cut ~30% of the
  peak; it did not. Something fixed in the training stack holds the bulk.
- The reported figure (25.86 GiB "allocated" on an 11.91 GiB device) is
  physically impossible as a live allocation. Either the accounting is
  split across host/device memory in this WSL GPU-PV setup, or a fixed
  structure (non-quantized layer copies, pair tensors) dominates. A fully
  clean diagnosis needs a debugging session on a machine where the
  allocations are observable, not more re-runs here.

## Verdict

On this 12 GB card, RFD4-Proteina fine-tuning is not reachable by input
shaping. The frozen-vs-fine-tuned comparison requires either a 24 GB+ GPU
(cloud rental, user's decision) or dropping to a smaller model (the parked
60M Proteina research release, itself not yet smoke-tested past its data
dependency issues).

The design-side alternative stands on its own: the evolution loop with the
v4 composite (epitope term added) improves the submission without any
fine-tuning — the gen4 pool holds 18 organizer-gate passers that the v3
composite never ranked.
