# Co-fold screen: predictor options (the open decision)

UPDATE 2026-10-24: the first option was tested in full. Chai-1 **does not fix
the screen either**: the native VP1u control floated 42-55 A from the verified
footprint in all five samples (ipTM 0.19, pTM 0.87, no contacts anywhere),
the same qualitative failure as Boltz-2. The limitation is not a Boltz quirk.
Measured details:

- chai-lab 0.6.1 on this box needed three fixes: torch 2.14.1+cu130 (the
  shipped pin `torch<2.7` has no sm_120 kernels for the RTX 5070); MSAs as
  `<sha256(QUERY uppercase)>.aligned.pqt` (plain .a3m is ignored; convert with
  `python -m chai_lab.data.parsing.msas.aligned_pqt <dir>`, pyarrow 17);
  `--no-use-esm-embeddings` (the 5.5 GB ESM checkpoint download broke twice).
- Run cost: peak 4.7 GiB, ~20 min per 5-sample fold - cheaper than Boltz-2
  here.
- The native footprint was re-verified straight from 11RN.cif: TfR1 auth
  contacts with the VP1u RBD are 202, 203, 204, 208, 209, 210, 211, 212, 348,
  371 (fold numbering 81-91, 227, 250); identical on both RBD copies.
- Restrained trial RESULT: with pocket restraints on the ten footprint
  residues (8 A), chai docks the native RBD at the footprint in all five
  samples (10-14 RBD residues within 5 A of the footprint; zero contacts at
  the dimer patch) and ipTM rises from 0.19 to 0.42-0.48. So the model can
  build the interface when directed; it will not find it on its own. A
  restrained pose is directed, not independent evidence, but it gives (a) a
  pose generator and (b) a consistency read (restrained ipTM) per design that
  is far from noise. Files: `~/c4-work/chai/control-11rn/` (control.fasta,
  msa_pqt/, restraints.csv, out/ unrestrained, out-restrained/).

## Restrained read on real designs (calibration)

Same protocol (pocket restraints on each set's own hotspot residues, 8 A,
5 samples), applied to campaign-1 designed binders:

Eight designs, five samples each (40 folds; `~/c4-work/logs/chai-restrained.csv`):

| design | set | restrained ipTM (mean of 5, range) | hotspots contacted | unrestrained read |
|---|---|---|---|---|
| e0_1 | E0 | 0.207 (0.203-0.210) | 6/6 | clash-at-site 4/5 |
| e0_0 | E0 | 0.291 (0.286-0.296) | 6/6 | floater 5/5 |
| e0_18 | E0 | 0.400 (0.395-0.405) | 6/6 | 1 clean at-site sample |
| e0_2 | E0 | 0.437 (0.423-0.447) | 6/6 | floater 5/5 |
| e12_17 | E12 | 0.300 (0.274-0.309) | 2/2 | 1 clean at-site sample |
| e12_20 | E12 | 0.361 (0.351-0.372) | 2/2 | 1 clean at-site sample |
| e12_9 | E12 | 0.655 (0.635-0.667) | 2/2 | 2 clean at-site samples |
| e12_18 | E12 | 0.752 (0.748-0.756) | 2/2 | 1 clean at-site sample |
| (native control) | - | 0.42-0.48 | 10/10 | floats, ipTM 0.19 |

Equal-bars check (review item, 2026-10-24): two E0 designs re-run with only 2
restraints ({R208, K371}, the pair most comparable to E12's K/K) score 0.412
and 0.405 - no jump toward the E12 range (0.655, 0.752). The E12-vs-E0 gap is
therefore not explained by restraint count, and the per-set-restraint protocol
stands for the full screen. Designs still overlap across sets at the design
level (e12_17 0.30, e12_20 0.36 vs e0_2 0.437); the set difference comes from
E12's upper tail. Runs: `designs/e0_18_r2/`, `designs/e0_2_r2/`.

Read: the protocol has real dynamic range (0.21-0.75 across designs, tight
within a design: +-0.02), so it can rank designs; the E12 pair
{e12_9, e12_18} forms clearly stronger directed interfaces than anything in
E0. ~~and the wide six-hotspot E0 patch is uniformly harder (0.21-0.44, all
below the native control)~~ SUPERSEDED 2026-10-25 by the full 24-design
screen: E0 reaches 0.556 with four designs at 0.5+, above the native
control's 0.48 - the pilot's four designs happened to miss E0's upper tail.
The confound test's premise was this sentence; the premise is corrected and
the confound result (no restraint-count artifact) stands. Caveat: these poses are directed by the restraints,
so the score is a consistency read, not independent evidence of binding; the
unrestrained read remains too noisy to rank (it disagreed with itself on
E0). Cost: ~12 min per design (5 samples) on this box; runs in
`~/c4-work/chai/designs/<name>/`.

The campaign-1 fold read is fold-limited: Boltz-2 (2.2.1) does not dock any
binder, the native VP1u included, to the TfR1 apical tip (full evidence in
`c1-triage.md`). Every campaign that needs a co-fold read is gated on a
working predictor for this target. Options, cheapest first:

1. **Chai-1** (`pip install chai-lab`, 0.6.1 on PyPI; weights fetched on first
   run). One maintained package, per-chain MSAs accepted, `--low-memory` flag
   exists for tight GPUs. Trial: fold the `00-control-11rn` pair (VP1u RBD +
   11QC protomer) and check the footprint, exactly as for Boltz-2.
2. **Protenix** (`pip install protenix`, 2.0.0; model weights from HF). AF3
   reproduction, supports MSA files; larger codebase, more setup surface.
3. **ColabFold local** (1.6.3; AF2-Multimer). Mature and well documented, but
   the 739-token complex at 12 GB VRAM needs its low-memory settings, and the
   result is an older model than the two above.
4. **Hosted routes** rechecked later (the local box does the work per our
   rules; no paid cloud).

Machine headroom for any of them: 642 GB disk free, 12 GB VRAM (RTX, WSL),
~20 GB system RAM available. Any install runs under the same `memlimit.py`
pattern the pipeline already uses for Boltz folds.

Acceptance test for the chosen predictor is fixed now, before installing:
the VP1u control must place the RBD on the native footprint (auth 303-328 is
NOT the footprint; the footprint is the apical tip region around 204-211 and
348-374) with a confident interface, and the C2 champion control (TNF) must
stay sane. If neither install docks the native control, the screen question
moves to wet-lab evidence and the campaign strategy must account for it.
