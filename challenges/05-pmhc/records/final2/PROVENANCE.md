# Provenance of the top three designs

Purpose: an exact account of how the three best designs in the set were produced —
every step, every tool, every parameter — as the foundation for an in-house
generation pipeline.

## The pipeline at a glance

| stage | what happens | tool | where it lives |
|---|---|---|---|
| 1. target preparation | build an annotated CIF of HLA-A\*11:01 + beta2m + G12D peptide, with per-atom marks (hotspots P4-P8, H-bonds, and later salt-bridges) | in-house | `nim/build_request.py`, `nim/target_pmhc_*_annotated.cif` |
| 2. generation | de novo binder backbones conditioned on the annotated target | **RFD4-Proteina, hosted NIM (NVIDIA)** | `nim/rfd4-batch.sh` + `nim/request_pmhc_*.json` |
| 3. co-folding | fold binder + target complex, per design | **boltz** (open weights, local venv) | `scripts/work/c0-probe-fold.sh` |
| 4. scoring | interface metrics (ipTM, i_pDAE, pLDDT), pose geometry | in-house + boltz confidences | `scripts/work/s1-score.py` |
| 5. specificity screens | C3 electrostatic rule; tri-state fold (G12D / WT / peptide-free) | in-house | `scripts/work/c3-*`, tri-state queues |
| 6. E-score | Coulomb-field read of the binder shell around Asp6 | in-house (charge model + PROPKA v2) | `scripts/work/escore.py`, `escore2.py` |
| 7. ranking | composite: i_pDAE 30 / ipTM 20 / dfree 20 / E_D6 20 / dWT 10 | in-house | `scripts/work/final-rank2.py`, `rerank.py` |
| 8. repair + evolution | single-point K/R swaps at the D6 shell; shell scans; pair combos | in-house | `scripts/work/repair-build.py`, `evo.py` |
| 9. validation | 3-seed stability, chai co-folding, apo stability, homology gate | boltz, **chai-lab**, in-house | `scripts/work/s3-*`, `val-run.sh` |
| 10. selection | final 20 by composite, family diversity rules | in-house | `scripts/work/final-pick.py`, `evo-apply.py` |

Only stage 2 is a hosted black box. Everything else already runs locally on open
weights or is our own code.

## Design 1 — `evorepair-wave2-pep__run-016__design_0005__g12d-L58K-Q15K` (composite 90.5, set rank 1)

The chain has four links: NIM generation, fold + screens, one repair swap, one
evolution swap.

1. **Origin.** Campaign C1 ("the main funnel"), NIM wave `wave2-pep`, run-016,
   design_0005. The request (`request_pmhc_PEP.json`) conditions the hosted
   RFD4-Proteina generator on the annotated CIF with the peptide ridge marked as
   hotspots P4-P8 plus one H-bond mark. Sampling: `recycle_strategy:
   thinking_medium`, 1 replicate per call. The result: a 72-residue binder
   backbone.
2. **Fold and screens.** boltz co-fold of the 485-residue complex
   (`c0-probe-fold.sh`). The design passed the C3 electrostatic screen and the
   tri-state: it bound the G12D complex while keeping the WT and peptide-free
   reads below the gates. Parent fold scores: peptide ipTM 0.958, HLA read
   0.975, i_pDAE 0.733, closest binder-to-Asp6 distance 6.79 A.
3. **Repair R2 (one swap).** `repair-build.py` enumerated single-point K/R swaps
   at every shell position 5-13 A from Asp6 and re-folded them. Exactly one
   strict win: **L58K** (dfree +0.769, E_D6 improved to -1.78). The alternative
   A61K was rejected: its i_pDAE collapsed to 0.338 (the fold degraded, which
   inflated the apparent WT delta — the classic artifact this project guards
   against).
4. **Evolution gen 1 (one swap).** `evo.py` scanned the remaining unsampled
   shell positions of the top-8 parents. On the L58K parent, **Q15K** won:
   dfree +0.766, E_D6 -3.65 (the set's best electrostatic read until gen 4),
   composite 90.5.
5. **Validation.** 3-seed stability: 0.976/0.970/0.971 (median 0.971, spread
   0.006). chai-lab: 0.844 (the set's best chai read). Apo stability: pLDDT
   0.963. Homology gate: passed.

## Design 2 — `evomini-wave1__run-014__design_0005__g12d-A16K` (composite 87.1, set rank 2)

1. **Origin.** The MINI campaign (`request_pmhc_MINI_r8.json`): the same
   annotated-CIF conditioning, 8 replicates per call, binder length ~66
   residues (the short-binder arm). Run-014, design_0005.
2. **Fold and screens.** Same funnel as above; the parent entered the pool at a
   modest composite of 67.5.
3. **Evolution gen 4 (one swap).** The repaired loop (top-16 parents, full
   duplicate ledger) bred this parent and found **A16K**: composite 67.5 -> 87.1,
   E_D6 -3.75 (the best in the entire set). This is the loop's single largest
   jump and its first win after the plateau fix.
4. **Validation.** Seeds: 0.981/0.985/0.981 (median 0.981, spread 0.004 — the
   most stable seeds in the set). chai: 0.814. Apo: binder-chain pLDDT 97.2
   (the most stable apo fold ever measured here).

## Design 3 — `evopeprim-wave1__run-001__design_0002__g12d-W57K` (composite 84.3, set rank 3)

1. **Origin.** The PEPRIM campaign (`request_pmhc_PEPRIM_r8.json`): annotated-CIF
   conditioning with the peptide-rim emphasis, 8 replicates, binder ~98
   residues. Run-001, design_0002. Parent fold: peptide ipTM 0.975, HLA read
   0.985, i_pDAE 0.897 — the strongest raw interface of the three parents.
2. **Fold and screens.** Same funnel; strong tri-state reads from the start.
3. **Evolution gen 1 (one swap).** **W57K**: composite 84.3, E_D6 -2.09.
4. **Validation.** Seeds median 0.975, spread 0.004. chai: 0.797. Apo: ~0.96.

## What this means for building the generator in-house

The three chains share one bottleneck: **every design begins as a backbone from
the hosted RFD4-Proteina NIM**, and that is the only component we cannot run,
inspect, or fine-tune locally. Stages 3-10 are already ours or open.

Reusable open pieces (weights included):

- **boltz** and **chai-lab** — co-folding (already local).
- **ProteinMPNN / LigandMPNN** — sequence design on a fixed backbone (already
  local, already used in campaign C6).
- **BioEmu2** — equilibrium ensembles (already local).
- **ProtonPottsMPNN** — protonation-aware charge assignment (already local).

The missing piece — backbone generation — has three open-weight routes:

1. **RFdiffusion (Baker lab)** — the direct ancestor of the RFD4 family.
   Supports motif scaffolding and hotspot conditioning; peptide targets work via
   the same "bind to a marked surface" mode we already use. Runs on 12 GB.
2. **RoseTTAFold All-Atom (RFAA)** — atom-level conditioning, closer to the
   RFD4 annotated-CIF interface we already author. Our existing CIFs and
   hotspot marks transfer nearly unchanged.
3. **Fine-tuning** — take either open model and fine-tune on our own winning
   outputs (the top-20 set plus the qualified children) to bias it toward this
   target's chemistry. Our 2,000+ folded designs and their scores are exactly
   the dataset such a fine-tune needs; this is the strongest long-term play,
   because it closes the loop with our own reward signal instead of a black box.

Practical path: start with RFAA (the conditioning format matches what we already
build), reproduce one known design's parent as a sanity check, then swap the
generator into the existing pipeline — stages 3-10 need no changes at all.
