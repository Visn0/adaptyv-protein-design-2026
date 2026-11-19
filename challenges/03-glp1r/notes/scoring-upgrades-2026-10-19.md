# Scoring & validation upgrades (2026-10-19 sweep)

Fresh research on validation/scoring tools, plus the BoltzGen feasibility
verdict. Sources and URLs in the delegation transcripts of 2026-10-19.

## 1b. BoltzGen — SOLVED: it runs on this box (2026-10-19, final verdict)

Earlier attempts failed because the memory cap was set at the default 10 GB
while the pipeline peaks at **9.97 GiB** — a ~0.3 GB miss. With the cap raised
to 12.5 GB and memory tuning, the full 6-step pipeline (design → inverse
folding → design folding → folding → analysis → filtering) **completes in
~8-10 minutes, exit 0** on the 5070 + 15 GB box.

Working recipe (reproduce exactly):

```
export MEMLIMIT_MB=12500 MALLOC_ARENA_MAX=2 \
       PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True OMP_NUM_THREADS=4
python3 memlimit.py boltzgen-env/bin/boltzgen run <spec>.yaml \
    --output <dir> --protocol protein-anything \
    --num_designs 1 --diffusion_batch_size 1 --num_workers 1 --use_kernels false
```

Outputs per run: `final_ranked_designs/` with ranked mmCIFs, a results PDF,
and a metrics CSV carrying **design_to_target_iptm, min_design_to_target_pae,
design_ptm, filter_rmsd, PLIP H-bonds, ΔSASA, shape-complementarity-style
features** — a ready-made validation suite. BoltzGen is therefore usable as a
second generator (cyclic peptides, disulfide conditioning) and as a scoring
pipeline for the campaigns.

## 1. BoltzGen — YES, on the released version only

- **Run `pip install boltzgen==0.3.2` (PyPI, 2026-05-01).** It has zero
  ESMFold2 code; downloads ~6 GB; GPU steps = design diffusion, inverse
  folding, Boltz-2 refolds; CPU = analysis/filtering; ships ipSAE metrics.
  Installed here as `~/c3-work/boltzgen-env`.
- **Do NOT use git `main`:** it makes the ESMFold2 scoring worker mandatory,
  and that worker peaks at 13.2–23.0 GiB VRAM (measured, official doc) — it
  cannot fit 12 GB, and no quantization/offload exists. The released version
  sidesteps it entirely.
- WSL2/5070 caveats: run with `--use_kernels false`; the sm_120/Blackwell path
  is unproven (a DGX Spark hang is open upstream) — verify produced counts
  (OOM'd design batches are silently skipped upstream); keep campaigns small
  (analysis OOM'd at 16 GB host RAM with 100 designs); tune
  `--diffusion_batch_size` and `analysis num_processes` down.
- **Not a standalone validator** (maintainer-confirmed): for fixed binders use
  Boltz-2 directly, as we already do. BoltzGen's value to us = a second
  generator (cyclic peptides, disulfide conditioning) + its ranking pipeline
  calibrated on validated binders.
- Bonus: Anthropic's Apache-2.0 `uplifting-biomolecular-modeling` kit has
  low-memory `big` modes for BoltzGen and **for Boltz-2 refolds** — worth
  testing for our own fold runs if RAM ever bites.

## 2. Scoring upgrades adopted (from the 3,766-binder meta-analysis)

Overath et al. 2025 (bioRxiv 10.1101/2025.08.14.670059) on 3,766 tested
binders: **ipSAE_min is the single best predictor**; useful filters:

- ipSAE_min > 0.61; or ipSAE_min × interface_ΔG/ΔSASA < −1.5; or
  LIS × shape_complementarity > 0.42.
- Prefilter shape complementarity > 0.62 and refold-RMSD < 3.73, then rank by
  ipSAE_min.

**Done (2026-10-19):** the screen now extracts every IPSAE metric already in
our reports — ipSAE, ipSAE_d0chn, ipTM_af, pDockQ, pDockQ2, **LIS** — plus
**binder pLDDT** and **inter-chain PAE** (the two metrics the PLOS 2026 GPCR
benchmark recommends), and the old "pDockQ2" column mislabel is fixed (it had
been reading pDockQ).

## 3. Still to add (ranked)

1. **Calibrate against real outcomes**: the Adaptyv/proteinbase HF dataset
   (`adaptyvbio/proteinbase`, ODC-BY) carries 4,069 proteins with experimental
   results incl. the SPR-validated Nipah round (1,196 designs, 111–116
   binders, best KD 3.7e-10) — run our screen over those and measure which
   metric/composite actually separated binders from non-binders.
2. **Orthogonal co-folder**: Protenix v1 (Apache-2.0, ~5.2 GB @500 tokens —
   fits; v2 weights are proprietary). Run the top candidates through a second
   model; the PLOS benchmark shows verifier-dependent bias is real.
3. **Peptide-specific pose scorers**: TopoDockQ and DeepPpIScore (both MIT) —
   test against our current suite on the campaign-2 peptides.
4. **Mutation follow-up**: Pythia-PPI (Apache-2.0, CPU) for ΔΔG on the best
   binders' interface positions.
5. Shape complementarity (the meta-analysis prefilter) — needs a local SC
   implementation; the simplest route is vendoring the calculation from the
   BindCraft codebase.

## 4. Explicit gaps (verified absences)

- No open-weight GLP-1R peptide potency model exists; our contact-span/reach
  proxy remains the practical state of the art for agonism-direction scoring.
- No trustworthy open PPI-affinity head: Boltz-2's affinity module is
  small-molecule only (protein chains rejected); Boltz-2-PPI underperforms
  sequence models and has no weights; APPT is CC-BY-NC and unpeer-reviewed.
- Interface-confidence scores have zero association with epitope engagement in
  an independent Oct 2026 benchmark — our designed-site contact screen is the
  right doctrine, keep it mandatory.
