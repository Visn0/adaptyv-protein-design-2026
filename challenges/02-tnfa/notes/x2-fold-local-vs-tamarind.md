# The known C2 fold, local GPU vs Tamarind — 15 October 2026

*Written 15 October 2026 (evening, CEST). Same experiment on both sides: a Boltz-2
co-fold of the X2 shortlist design `config_c2-x2-rfd3-s1-groove-1_0_model_1`
(73 aa) against the human TNF-α trimer (binder chain A, target B/C/D), 5 samples,
IPSAE on. Purpose: decide whether the local RTX 5070 can replace the Tamarind
route for the campaign.*

## 1. Commands (both sides)

Tamarind (15 Oct, server time 16:30 → 16:33): tool `boltz`, 4 protein chains,
`numSamples: 5`, `runIpsae: true`. Payload + response:
`handoff/records/x2-fold-job.json`; result: `handoff/records/x2-fold-metrics.csv`.

Local (15 Oct, 20:18 → 20:20 local):

```bash
cd challenges/02-tnfa/handoff
~/.venvs/boltz/bin/boltz predict \
    boltz/fold-human-config_c2-x2-rfd3-s1-groove-1_0_model_1.pdb.yaml \
    --out_dir ~/c2-work/w1-gpu-s7 --use_msa_server --seed 7 --diffusion_samples 5
```

IPSAE per model (runs in `~/.venvs/tools`):

```bash
python ~/tools/IPSAE/ipsae.py pae_..._model_N.npz ..._model_N.cif 10 10
```

## 2. Per-sample ipSAE (chain A against chain B, 10 Å cutoff)

| sample | Tamarind (their seed) | ours, seed 7 | ours, seed 42 |
|---|---|---|---|
| 1 | 0.527 | 0.378 | 0.733 |
| 2 | **0.804** | 0.614 | 0.454 |
| 3 | 0.378 | 0.344 | 0.646 |
| 4 | 0.000 | 0.000 | 0.433 |
| 5 | 0.000 | 0.000 | 0.025 |
| samples >= 0.6 | 1 / 5 | 1 / 5 | 2 / 5 |
| ipTM range | 0.839-0.962 | 0.860-0.937 | 0.903-0.949 |

The Tamarind seed is not recorded, so the sample indices are independent draws.
Compare the distributions, not the rows.

## 3. What the comparison shows

- **The same regime.** Both sides produce one locked interface, two partial ones and
  two where the interface is lost. The best sample is 0.80 on Tamarind and 0.73
  locally (seed 42); across 10 local samples, 3 clear the 0.6 ipSAE line.
- **Wall time is not the differentiator.** Tamarind: about 3 minutes from submission
  to download (queue included). Local: 2 min 30 s (MSA fetch + 76 s of GPU time for
  the 5 samples). GPU peak: 7.8 GB of 12 GB.
- **The cap is the differentiator.** Tamarind costs 1 of 10 free jobs per month and
  its quota is spent; the local card has no cap. For a campaign of tens of folds the
  local route is the only one that fits the deadline.
- **ipTM does not separate a dock from a miss.** It stays 0.84-0.96 in every sample
  on both sides, including the samples with ipSAE 0.000.

## 4. Limits of this comparison

- One design, three draws (15 samples total). This is a reproducibility check of the
  local route, not a rate measurement.
- The strict pre-registered bar (ipSAE >= 0.6 AND pDockQ2 >= 0.23) is met by 1 of 5
  Tamarind samples and by 0 of 5 local samples (the best local sample has ipSAE 0.733
  with pDockQ2 0.133). The local draw is not weaker overall: 3 of 10 local samples
  clear the ipSAE half of the bar.
- MSA: the local run uses the public ColabFold server, the same source the Tamarind
  job used. Both cache their MSA per output directory.

## 5. Correction to the record (the `nvidia-smi` finding)

An earlier note in `pc-session-1.md` said that Boltz-2 sizes its batches from the GPU
figure it reads. That is wrong, and the source is now read:

- The messages come from `cuequivariance_ops/triton/cache_manager.py`, not from Boltz.
  `get_gpu_name()` shells out to `nvidia-smi`; when that fails it prints
  `Error getting GPU memory: ...` and returns `"NVIDIA RTX A6000"`.
- The A6000 numbers (45 GB, 84 SMs, sm_86) are a **cache key and tuning default** for
  cuequivariance's Triton kernel cache (`gpu_information_to_key`), not a batching
  decision. Boltz has no memory-aware auto-batching: `--diffusion_samples` and
  `--max_parallel_samples` are explicit.
- The `~/.local/bin/nvidia-smi` symlink removes the "No such file or directory" error
  and makes the reported name correct, but the RTX 5070 has no entry in the package's
  default map, so the A6000 defaults are still used. The effect is limited to kernel
  cache keys; measured runs are unaffected (5 samples peak at 7.8 GB).

## 6. The fold is now a run

`challenges/02-tnfa/experiments/c2-fold-w1-gpu.yaml` (pipeline `fold`) imports a Boltz-2
output directory and turns it into a first-class run: every sample is scored with IPSAE,
one row per sample in `fold_metrics.csv`, the best model in the 3D view, and the
Tamarind fold drawn next to it as a second line. The run on this machine:

- `challenges/02-tnfa/runs/20261015-200107-c2-fold-w1-gpu` — 5 samples, best ipSAE 0.73
  (pDockQ2 0.13), verdict `partial`: "best sample ipSAE 0.73 — under the full bar".

**A bug this run exposed in the stage itself.** The first version copied the Boltz files
under new names. IPSAE finds its companions by renaming the PAE path (`pae`→`plddt`,
`pae`→`confidence`, `.npz`→`.json`), so the renamed copies made it read **no pLDDT**: ipSAE
stayed exactly right (0.733) while pDockQ2 collapsed to its floor (0.0073 instead of
0.1325). The stage now copies the files under their original names and warns when a
pLDDT file is missing. Recorded as mistake 27 in `AGENT.md`; the regression is pinned by
a test. Numbers in section 2 above come from the manual runs and are unaffected.

## 7. Next step

W2: fold the 8 shortlist designs (human, 5 samples each), triage every sample with
IPSAE, then fold ranks 1-2 against the mouse construct.
