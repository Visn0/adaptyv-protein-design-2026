# Fine-tune v0: the 12 GB ceiling (honest record)

## What was attempted

The first LoRA fine-tune of RFD4-Proteina using the official diffusers
example (`train_rfd4_proteina_lora.py`, PR 15155), on 8 of the best batch1
complexes, with:
- rank 32, alpha 64, LR 5e-5, bf16, gradient checkpointing: OOM
- rank 8, alpha 32, same: OOM (expandable_segments on and off)

All three failed in the same place: the forward-backward pass on the ~490-token
complex. The failing allocation is small (102 MiB) - the card is right at the
edge, not far over.

## The constraint

The full pMHC + binder complex is ~490 residues. Training through the 435.6M
parameter transformer at that sequence length does not fit in 12 GB with any
LoRA rank or allocator setting. The release's own fine-tune was run at scale.

## Update: the 4-bit route also fails

The quantized base (NF4 via bitsandbytes) loads in 1.2 GB - a tenth of the card.
Training still OOMs: ~26 GiB of PyTorch allocations at the ~490-token complexes.
The wall is the training-time activations, not the weights. A six-attempt fork
(verified fixes: pipeline/model-level quant configs, peft-vs-transformers helper
moves, HF-interface stubs, VAE kwarg leakage) all reached the same place.

Conclusion, final for this machine: the 12 GB card cannot fine-tune this model
on our target's complexes at any setting tried.

## Options, in order of feasibility on this machine

1. **Train on smaller complexes.** The ATLAS natural pMHC set includes shorter
   class I complexes; smaller token counts may fit. Needs a token-count filter
   in the data prep. Cheapest path, untested.
2. **Quantized base (4-bit/8-bit) + LoRA.** The standard consumer-GPU approach.
   The example script has no quantization flag, so this needs a fork of the
   script (bitsandbytes + prepare_model_for_kbit_training). Moderate work.
3. **Cloud GPU.** Out of scope by standing rule (no cloud without explicit
   approval).
4. **Skip backbone fine-tuning; tune elsewhere.** The evidence so far: the
   frozen RFD4 already generates at parity with the hosted NIM (19% JDI-like),
   and the binding specificity gap is not a generator problem. Fine-tuning the
   inverse-folding or the scoring side may buy more per GPU-hour than pushing
   the denoiser.

## What this does not change

The custom-model project stands: local generation, our scores as the reward,
all plumbing verified. The training step needs either smaller complexes,
quantization, or a different component. Decision pending user input given the
day's compute budget.
