# In-house pipeline: options for one integrated loop

Question: replace the hosted RFD4-Proteina generator with something we own, and
merge co-folding, scoring, E-score, repair, evolution and validation into a
single script, so the loop iterates faster.

## What "rewriting RFD4" really means

Three different projects hide under that phrase:

1. **Reimplement the network.** The architecture is a RoseTTAFold-family
   diffusion model, described in public papers. Reimplementing it buys nothing:
   the value is in the weights, not the code.
2. **Reuse the open weights.** RFdiffusion and RoseTTAFold All-Atom (RFAA) are
   the open members of the same family, with downloadable weights. They support
   the same "bind to a marked surface" mode we already use, and the annotated
   CIF we author by hand transfers almost unchanged.
3. **Fine-tune the open weights on our data.** The long-term play: 2,000+
   folded designs with measured scores are exactly the dataset such a fine-tune
   needs.

The speed gain does not come from the language of the generator. It comes from
the integration: today we pay network round-trips, rate limits, queue
serialization, per-design process starts, and model reloads. An integrated loop
pays none of these.

## Option A - the integrated local pipeline (recommended base)

All components local, all open weights: RFAA or RFdiffusion (generate), boltz
or chai (fold), our screens and E-score, our repair and evolution operators.

One Python orchestrator owns the cycle:

1. propose (mutations, pairs, enumeration - in-house, milliseconds)
2. pre-screen (cheap filter, see Option D1)
3. fold (batched)
4. measure (interface metrics + E-score)
5. select (composite + family rules)
6. repeat, unattended

Realistic cycle time: 1 to 1.5 hours against today's 2 to 3, with no queue
choreography and no shared-GPU waiting when the machine is ours.

## Option B - fine-tuning the generator

- Data: our 2,000+ folded designs, their scores, and the repair/evolution
  mutation outcomes.
- Approach: reward-style fine-tuning of the open model toward this target's
  chemistry; start from the conditioning level (interface motifs), then LoRA.
- Payoff: a generator biased toward backbones that read Asp6 well, which raises
  the yield of every downstream step.
- Timeline: weeks, research-grade. Do it after Option A works.

## Option C - a fully in-house generator

Every strong design in this project is a helical bundle capping the groove. That
is a small, describable geometry space, so a parametric generator is feasible:

- place idealized helix bundles (count, length, twist, radius as parameters)
- optimize the pose against the target with the E-score as the objective
  (seconds per candidate, pure geometry)
- design sequences onto the accepted poses with ProteinMPNN/LigandMPNN

Cost: days for a prototype. Risk: low diversity (the same morphology as today).
Value: it tests the project's central thesis - that specificity rides on the
electrostatic field, not the backbone - with a generator we fully control.
The older alternatives (AF2 hallucination, RFjoint inpainting) are slower and
weaker; skip them.

## Option D - speed levers (orthogonal, stackable)

1. **A delta-E model.** The repair and evolution rounds contain hundreds of
   measured single-point mutations with their delta-E. A small model (parent
   structure + mutation -> delta-E) will correlate far better than the current
   global surrogate (rank correlation 0.47). Use it to fold only the top-K
   proposals. This is the single biggest speedup.
2. **Batched folds.** boltz folds several designs per call; the 12 GB card
   allows small batches.
3. **Resident models.** Load once, keep in memory. boltz uses about 5-6 GB and
   the generator about 2-3 GB, so co-residency fits, carefully.
4. **Rust: no.** Neither the orchestrator nor the E-score is the bottleneck;
   numpy runs the E-score in milliseconds. Rust would add work and buy nothing.
5. **Exclusive GPU.** The 12 GB card is the binding constraint. The integrated
   loop wants the machine to itself; the current sharing with the other
   session's pipeline costs real time.

## Recommended path

1. Days: install RFAA, reproduce one known parent as a sanity check, then write
   the single orchestrator (Option A). Swap the generator; stages 3-10 do not
   change.
2. Days: train the delta-E model (D1) and wire it as the pre-screen.
3. Weeks: fine-tune (Option B). In parallel, prototype Option C.
