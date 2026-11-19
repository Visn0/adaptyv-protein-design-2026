# Interface-metric benchmark (Brian Naughton, 2026-10-30) — review and impact

Source: @btnaughton post 2116204127940424164, chart by "Decade — ProteinBase
Benchmark" (data: ProteinBase by Adaptyv Bio, 200 measured binders + 200
nonbinders, top-40-by-score positive predictive value, random = 50%).

## What the benchmark says

| Predictor | ipSAE | ipDAE | ipTM |
| --- | --- | --- | --- |
| ESMFold2 | 52.5% | 77.5% | 45% |
| Protenix2 | 65% | 72.5% | 70% |
| OpenDDE | 65% | 77.5% | 80% |
| ESMFold2 + Protenix2 | 67.5% | 80% | 70% |
| ESMFold2 + OpenDDE | 62.5% | 75% | 70% |
| Protenix2 + OpenDDE | 70% | 80% | 80% |
| All three | 72.5% | 72.5% | 75% |

Conclusions in the post: i_pDAE (BindCraft2's score) is consistently good;
OpenDDE + ipTM is the best single (80%); consensus ensembles do not help more
than the best pairs. Footer caveats: exploratory, uneven target counts,
training-set overlap unresolved.

## What it means for this campaign

1. **C0 verdict stands.** This benchmark ranks binder-vs-nonbinder confidence
   within a candidate set. C0 asked a different question (G12D vs WT
   separation) and found no fold metric separates the two. No conflict.
2. **ipSAE is the weakest of the three in general** (52.5% at ESMFold2, close
   to random) and its value is model-dependent. The organizer-aligned gate
   (ipSAE_min >= 0.61) stays, but it must not be the only confidence read.
3. **i_pDAE is computable from what we already have.** BindCraft2's
   `interface_pdae_metric` (bindcraft/filters.py) needs only the PAE matrix +
   a CA-CA <= 8 A contact mask. Ported into `s1-score.py`; no new model, no
   new weights. Smoke test: i_pDAE tracks ipSAE closely (0.82/0.90 and
   0.02/0.02 on the same designs) — it is a second, independent read of the
   same interface confidence.
4. **ipTM has a physical reference for us.** The C0 JDI control (a real
   425 nM binder) reads 0.95 peptide ipTM; our design pool spans 0.23-0.98.
   The stage-1 scorer records `iptm_pep` and counts "JDI-like" designs
   (mean >= 0.8) next to the ipSAE gate count.
5. **No ensembles.** The benchmark's consensus finding matches our C0
   experience (boltz/chai/BC2 signs disagreed). Keep one best metric per
   axis; do not build voting schemes.
6. **OpenDDE is a stage-3 candidate.** Aureka's open all-atom co-folding model
   (Apache-2.0, 656M params, PyPI install, open weights, v1.2.0 adds
   constraint-guided inference). The benchmark's best single predictor. Fits
   the 12 GB card. Preview-quality software — test on the JDI control before
   trusting any read from it.

## Actions taken (2026-10-31)

- `s1-score.py`: added `iptm_pep/hla/b2m` (confidence json) and
  `ipdae_pep/hla/b2m` (BC2 port) reads; summary gains `n_jdi_like`.
  The ipSAE 0.61 gate is unchanged (pre-registration discipline); the new
  reads are recorded ranking inputs.
- Preview scoring of the 120 completed stage-1 folds launched (CPU-only,
  parallel; GPU continues folding).
- OpenDDE setup done: venv `~/.venvs/opendde` (Python 3.11, torch
  2.14.1+cu130 — the default cu126 build has no sm_120 kernels for this
  card), weights at `~/.cache/opendde/checkpoint/opendde.pt` (2.6 GB),
  `opendde doctor` clean. Acceptance test (JDI control) pending a free GPU
  window.
- OpenDDE input gotchas (first-run debug, 2026-11-01):
  - every `proteinChain` entry needs `"count": 1` or the dataloader dies
    with `KeyError: 'count'`;
  - the MSA step runs locally with mmseqs (manifest `mode: env`) and writes
    `<out>/<job>/msa/<i>/{pairing,non_pairing}.a3m` plus a preprocessed
    input with `pairedMsaPath`/`unpairedMsaPath` wired in
    (`<out>/.opendde_preprocessed/<hash>/<job>-input-update-msa.json`) —
    reuse that file (add `count`) for re-runs so the MSA step stays cached.
- **OpenDDE shelved (2026-11-01 08:30).** Two full attempts, two host
  reboots: run 2 was killed with a boltz fold running concurrently
  (02:02, hypervisor family), run 3 ran ALONE and the host died ~18 min
  into inference with bugcheck `0xD1 DRIVER_IRQL_NOT_LESS_OR_EQUAL` — a
  driver-level fault, a new signature. The machine has idle-crash history
  (0x20001 family, incl. 15:32 and 23:14 on 10-31 with nothing running),
  so the cause is not proven, but a 2/2 correlation with a new workload is
  enough: the stage-3 core is multi-seed boltz + chai, and OpenDDE's
  marginal value does not justify more reboots. Revisit only after the
  submission is safe, and only with reduced settings.
