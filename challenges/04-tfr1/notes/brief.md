# 04 — TfR1 conditional binder · brief (captured 2026-10-23)

Source: the challenge page
(proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/tfr1) + the hub.

## The task

Design a **conditional TfR1 binder**: bind human transferrin receptor 1, bind the
mouse receptor as well, and hold human TfR1 at **pH 7.4** while releasing it at
**pH 6.0** — the same three objectives as the TNF-α challenge, in the same
direction. Submissions close **Sunday, November 1, 23:59 AoE** (window
Oct 19 – Nov 1).

## Target information

| field | value |
|---|---|
| Target | Human TfR1 (CD71), UniProt P02786-1 |
| Segment | residues 121–760 (640 aa), the soluble ectodomain, supplied as a homodimer |
| Mouse construct | residues 123–763 |
| Recommended epitope | the **apical domain** — the tip of each subunit that arenaviruses, parvovirus B19 and brain-shuttle antibodies bind, which leaves the transferrin site free |
| Structure reference | PDB 11QC, chains A–B (apical-domain complex: 11RN chain A with VP1u) |
| Conditions | human pH 7.4 / human pH 6.0 / mouse pH 7.4, design immobilised, target in solution |

Each subunit has three domains; the receptor is a disulfide-linked homodimer, so
every target presents two copies of the epitope. The two ectodomains (human vs
mouse) are 78% identical and the apical patch differs at six of nine positions —
TfR1 binders are notoriously species-specific.

## How designs are ranked

1. **pH-selective binding** — a measurable KD against human TfR1 at pH 7.4 and no
   detectable binding at pH 6.0. Designs that bind at both pH values rank after
   these, by the ratio of their KD at 6.0 to their KD at 7.4.
2. **Mouse cross-reactivity** — binds mouse as well as human at pH 7.4, ranked by
   how close the mouse-to-human KD ratio is to 1, among designs with a human KD
   below 1 µM.
3. **Affinity** — lowest KD against human TfR1 at pH 7.4. A functional epitope
   counts in its favour: name the epitope and link the evidence.

A design counts as binding when its sensorgram gives a fittable curve and a KD,
or — where the curve cannot be fitted — when the association shift clears 300%
over the negative control.

## What this means for the design (first notes)

- The objectives and the direction mirror challenge 2 exactly: the C2 tool chain
  (Genie 3 backbones, full-backbone ProteinMPNN, Boltz-2 co-folds, ipSAE at the
  designed site, PROPKA linkage for the switch) applies unchanged.
- The epitope choice is the first decision: the apical domain keeps the
  transferrin site free, and that is what the challenge recommends.
- The mouse problem is sharper here than in C2: the apical patch differs at six
  of nine positions, so cross-reactivity must be selected for on the mouse fold
  from the start.
- The pH direction is the C2 direction (bind at 7.4, release at 6.0) — the
  C2 switch lessons transfer directly.
