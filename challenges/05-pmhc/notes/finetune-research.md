# Fine-tuning research: a custom, reward-tuned generator

Question: retrain or fine-tune the best open model, use our own scores as the
training signal, and put co-folding and validation inside the training loop.

## Headline finding

The RFD4-Proteina model behind the hosted NIM is **Proteina** (NVIDIA, ICLR
2025 oral), and it is open: code, eight checkpoints, and published recipes for
exactly what we need.

- **LoRA fine-tuning for protein backbones** is in the paper and the release
  ("fine-tuning strategies like LoRA for protein backbones").
- **Guidance methods** (classifier-free, autoguidance) ship with it.
- **Motif scaffolding** is a supported mode. Our target is a peptide sitting in
  an MHC groove, which is a motif; the binder is the scaffold. This is the exact
  analogy our pipeline already uses.
- License: non-commercial research use. Fine for this project.
- Small checkpoints: 60M and 200M parameters. The 60M model fits a 12 GB card
  for both sampling and LoRA training.

This means our in-house generator can be the same model family we already trust,
not a substitute.

## The landscape (what exists for reward-driven tuning)

| approach | mechanism | weights change? | fit here |
|---|---|---|---|
| Feynman-Kac particle steering (FK-RFdiffusion, MIT, Nov 2025) | resample diffusion trajectories against a custom reward; ProteinMPNN + PyRosetta inside | no | excellent idea, RFdiffusion-based (older); porting to Proteina is real work |
| RAFT / iterative best-of-n fine-tuning | generate N, score them, fine-tune (LoRA) on the winners, repeat | **yes** | **the simplest path to tuned weights** |
| DRaFT / DRAKES / GLID2E | backpropagate differentiable rewards through the diffusion trajectory | yes | research-grade; DRAKES/GLID2E target sequence models |
| RFdiffusion training protocol (community implementation) | full retrain on custom data (dFrame + L2D losses) | yes | heavy (DeepSpeed, 16-bit), older model; a fallback |

## Chosen strategy: the RAFT-style LoRA loop on Proteina

The simplest strategy that actually tunes the weights with our scores:

1. **Generate**: Proteina (motif-scaffolding mode) proposes N scaffold
   backbones around the fixed peptide + HLA groove motif.
2. **Sequence**: ProteinMPNN (or LigandMPNN) designs sequences onto each
   backbone, as we already do.
3. **Fold**: boltz co-folds each design with the target (batched).
4. **Score**: our composite - interface metrics, the tri-state (G12D vs WT vs
   peptide-free), and the E-score. This is the reward.
5. **Select**: keep the top-K winners, with the hard gates (fold quality,
   tri-state margins, family diversity) applied exactly as in the evolution
   loop.
6. **Fine-tune**: LoRA-SFT on the K winners (the repo's recipe), which shifts
   the generator toward backbones that score well on THIS target.
7. **Repeat**: each cycle uses the updated LoRA. Track held-out designs so the
   reward cannot be gamed into collapse.

The co-folding and validation are not external checks; they are the training
loop's reward and filter. One cycle is roughly 1.5 to 2 hours, so the four days
before the deadline allow 15+ tuning cycles.

## Why this ordering

- Phase 1 (days): the RAFT-LoRA loop. Stable, standard, no RL gradient issues;
  it is the first step of every RLHF pipeline and it directly uses our scores.
- Phase 2 (optional): add Feynman-Kac style particle steering at sampling time,
  which biases generation toward high-reward trajectories without waiting for
  a full LoRA cycle. The FK-RFdiffusion code is the reference; the concepts
  port to Proteina's flow sampling.
- Phase 3 (later): full retraining or the discrete-sequence RL methods
  (DRAKES, GLID2E) on the inverse-folding step.

## Risks and guards

- **Reward hacking**: the composite could be gamed (the fold metrics invert
  signs under optimization). Guards: the hard gates, the tri-state validation,
  a held-out set, and family diversity caps.
- **Low-data overfit** in LoRA: keep the K small but diverse, and cap the
  training steps per cycle.
- **License**: non-commercial research only. The submission is research.
- **GPU**: the 12 GB card is the binding constraint. The 60M model first; try
  the 200M only after the 60M loop works.
- **Model scope**: Proteina is a backbone generator. Sequence quality still
  rides on ProteinMPNN, and specificity still rides on the E-score. The loop
  tunes the backbone distribution; it cannot invent physics.

## First steps

1. Install Proteina (started: clone + environment).
2. Download the 60M checkpoint and reproduce a baseline sample.
3. Build the peptide-motif input from our existing annotated CIF.
4. Wire one full cycle (generate -> MPNN -> fold -> score -> select) with no
   LoRA yet, to verify the plumbing and measure the baseline hit rate.
5. Add the LoRA step and run the first tuning cycles.
