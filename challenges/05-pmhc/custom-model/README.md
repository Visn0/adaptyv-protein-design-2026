# Custom model: an in-house, reward-tuned generator for this target

Goal: own the generator. Fine-tune an open model on this target, with our
composite score and co-folding validation inside the training loop, so the
model itself learns to produce backbones that read Asp6 the way the natural
reader does.

## Base model

**RFD4-Proteina** (Baker Lab x NVIDIA, released 2026-10-19 on Hugging Face).
This is the *actual* model behind the hosted NIM, and it is open:

- `nvidia/RFD4-Proteina` (native) and `nvidia/RFD4-Proteina-Diffusers` — BSD 3-Clause
- 435.6M parameters, FP32 (1.74 GB), runs in BF16 on the local 12 GB GPU
- the release itself is a rank-32 LoRA fine-tune of a pretrained base; the
  base and the adapter ship on the `pretrain-base` branch — the fine-tuning
  path we need is the release's own design
- joint sequence + all-atom structure generation (no separate MPNN step needed)
- inputs are annotated CIFs — the exact format our `nim/build_request.py`
  already authors; sampler is the same `thinking_medium` recipe our NIM
  requests used

Verified locally: a ~64-residue binder was designed against our G12D pMHC in
about one minute, with the entire pMHC held fixed (chains 276/99/10 preserved,
one new chain of 64 residues). See `scripts/rfd4_smoke.py` and
`data/smoke/pmhc_target.cif`.

The February-2025 Proteina 60M (motif checkpoint at `~/tools/proteina`) is
superseded and parked; it also needs the aux-files download we skipped.

## Training loop (RAFT-style LoRA)

1. generate N scaffold backbones around the fixed peptide motif
2. sequence them (ProteinMPNN/LigandMPNN)
3. co-fold each with the target (boltz, batched)
4. score with the composite: interface metrics, tri-state (G12D/WT/free),
   E-score
5. select the top-K under the hard gates and the family-diversity rules
6. LoRA-SFT on the winners
7. repeat with the updated LoRA; held-out designs guard against reward collapse

## Labeled data (wet lab)

Downloaded under `data/`:

| dataset | content | size |
|---|---|---|
| `atlas_Mutants.csv` | TCR mutant affinities on pMHC, with KD, dG, **dDeltaG** | 1,174 rows |
| `atlas_TCRs.csv`, `atlas_MHCs.csv` | TCR and MHC reference tables | 186 / 65 rows |
| `skempi2.csv` | protein-protein mutation binding data (dDeltaG) | 7,085 mutations |

The SKEMPI subset tagged "TCR/pMHC" holds 764 mutations - the slice matching
our interface class.

The single most valuable external fact: the **JDI / JDIa41b1 TCR** binds the
KRAS G12D decamer on HLA-A*11:01 with measured KD 63 uM -> 743 pM after
affinity enhancement, while KD for the WT peptide stays at 3.0 uM. Structures:
PDB 7PB2, 7OW6 (G12D) and 7OW5 (WT). The paper states explicitly that
selectivity is driven by differences in indirect electrostatic interactions,
not by direct contacts - the same thesis this project has pursued.

## Why labels matter here

The generator loop does not need external labels; our pipeline computes the
reward. The wet-lab data serves three sharper purposes:

1. **Calibrate the instruments.** The E-score and composite are currently
   validated by one control (the JDI sign check). The ATLAS and SKEMPI tables
   let us measure how well the scores track real measured binding. An
   instrument that predicts experimental dDeltaG is a very different claim
   from one that merely passes a sign test.
2. **Shape the reward.** If specific energy terms correlate with measured
   affinity changes, they earn weight in the composite.
3. **Positive examples.** The 803 TCR-pMHC structures in ATLAS are wet-lab
   confirmed readers of this exact interface class. They are the natural
   examples the fine-tune can imitate first.

## Phases

1. Baseline: Proteina sampling on our motif, no weights moved. Measure the
   hit rate with the existing screens.
2. Calibration: composite and E-score against the ATLAS/SKEMPI dDeltaG.
3. First LoRA cycles with the calibrated reward.
4. Evaluation against the current top-20 set, same instruments.

## Status

- Proteina env, checkpoint, configs: ready
- datasets: downloaded
- next: motif PDB + contig for our target, then the first baseline samples
