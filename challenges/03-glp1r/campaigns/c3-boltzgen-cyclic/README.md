# Campaign 3: BoltzGen cyclic peptides against the GLP1R orthosteric site

## Why

BoltzGen became usable on this box on 2026-10-19 (see
`notes/scoring-upgrades-2026-10-19.md`): the full design pipeline runs under a
12.5 GB memory cap. It brings a different generator (peptide design with
`cyclic: True` and optional disulfide conditioning) and a built-in scoring
suite (design-to-target ipTM, interface PAE, RMSD, PLIP H-bonds, ΔSASA).

## Hypothesis

The EvoBind campaign (c2) showed that 15-aa cyclic peptides engage the
orthosteric groove+junction site. A second, independent generator aimed at the
same epitope gives orthogonal candidates and lets us cross-check scores
between two pipelines.

## Configuration

- **Target**: `inputs/target-ecd-junction.pdb` — chain **R**, original UniProt
  numbering 29–129 + 136–241 (chain break at 130–135).
- **Epitope constraint** (`binding_types`): R 67,69,88,91,121,128 (groove) and
  R 197,210,221,234 (ECD–TMD junction) — the same site set as c1/c2.
- **Designed entity**: one cyclic peptide, length range 12..18, id E.
- **Protocol**: `protein-anything` (peptide design against a protein target).

## Run recipe (proven on 2026-10-19)

```
export MEMLIMIT_MB=12500 MALLOC_ARENA_MAX=2 \
       PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True OMP_NUM_THREADS=4
python3 memlimit.py boltzgen-env/bin/boltzgen run spec.yaml \
    --output <dir> --protocol protein-anything \
    --num_designs <N> --diffusion_batch_size 1 --num_workers 1 --use_kernels false
```

Peak observed: 9.97 GiB (375-res target). Expect ~10–15 min per 10 designs.

## Status

- 2026-10-20: first run queued after the C2 rescoring job.

## Operating point found (2026-10-20)

- The design step's RAM scales with the **number of designs requested in the
  run**, and retries into the same `--output` dir **accumulate**: a failed
  10-design run leaves state that makes the next "1-design" retry regenerate
  all 11 (killed at 13.9 GiB). **Always use a fresh output dir per run.**
- Stable operating point: **1 design per run, fresh dir, ~10 min, peak
  9.95 GiB, exit 0.** Sampling is therefore a loop of single-design runs
  (see `~/c3-work/c3-sample-loop.sh`).
- First design: `TVTLKVPGTDVVIKVG` (16 aa) — weak (ipTM 0.412, design-folding
  RMSD 4.0). Single samples vary; the loop collects a batch for screening.

## Batch 1 (groove+junction constraint): weak

Seven single-design samples (2026-10-20 01:20-02:00):

| run | sequence | ipTM | minPAE | design-folding RMSD |
|---|---|---|---|---|
| 0 (first) | TVTLKVPGTDVVIKVG | 0.412 | 9.1 | 0.61 |
| 1 | GRVIYIPGDRTTVPVPGA | 0.206 | 15.0 | 0.81 |
| 2 | CRTVTVDGQTITLG | 0.290 | 9.1 | 0.64 |
| 3 | SRYVPAFGVFFR | 0.260 | 13.2 | 0.77 |
| 4 | CRTVTVDGQTFTLG | 0.246 | 10.2 | 0.54 |
| 5 | MRVVHVGPFKLTLG | 0.299 | 11.1 | 0.42 |
| 6 | CRVIHVGPQVLVLG | 0.243 | 14.8 | 0.62 |

All weak (ipTM 0.21-0.41 vs 0.60-0.84 for the C2 designs). The designs are
being cross-checked on our Boltz screen (metrics rank differently between
pipelines) before concluding.

## Variant: junction-only constraint

Batch 2 repeats the run with `binding_types` on the junction only (fragment
163,176,187,200), the configuration that beat groove+junction in campaign 1.
Spec: `scripts/spec-glp1r-cyclic-junction.yaml`.

## Batch 2 (junction-only) + cross-check: campaign 3 works

The junction-only variant produced the better batch. Our screen (the
authoritative filter; BoltzGen's internal ipTM proved misleading here) on all
13 designs:

| rank | design | sequence | ipSAE | grv | tm | ecl3 | plddt |
|---|---|---|---|---|---|---|---|
| 1 | c3-jun-run4 | MTFEYDVRTGRPVLVD | 0.859 | 1 | 1 | 4 | 67 |
| 2 | c3-boltz-run1 | GRVIYIPGDRTTVPVPGA | 0.858 | 4 | 0 | 3 | 66 |
| 3 | c3-jun-run6 | TVFEYRGFTIKVM | 0.846 | 1 | 2 | 7 | 71 |
| 4 | c3-boltz-run3 | SRYVPAFGVFFR | 0.834 | 2 | 0 | 1 | 74 |
| 5 | c3-jun-run1 | TVSLTNLETGFTITVG | 0.797 | 0 | 4 | 4 | 73 |
| 6 | c3-jun-run2 | TVSLEVTVRGVRVTATFL | 0.781 | 1 | 2 | 4 | 75 |
| 7 | c3-jun-run5 | TVSFYNPKTGFTITVL | 0.772 | 2 | 2 | 4 | 63 |

Seven of thirteen reach ipSAE 0.77-0.86 — the same band as the EvoBind 15-aa
hits. The junction-only constraint (the campaign-1 lesson) transferred: its
batch gives deeper reach (tm 1-4, ecl3 4-7) and better consistency
(c3-jun-run1: 5/5 samples at ipSAE ~0.78, plddt ~75).

**Key finding: BoltzGen's internal metrics rank these designs wrongly** (its
ipTM called c3-jun-run4-like designs weak at 0.2-0.4 while our screen puts
them at 0.77-0.86). Screen every BoltzGen design on the orthogonal pipeline
before judging. Full table: `c3-candidates.csv`.

## Batch 3 (12 more junction designs): FOUR two-domain HITs

The scaled junction batch cleared the two-domain bar (ipSAE >= 0.8 with both
groove and TM/junction contacts) - the same class as the campaign 1 and 2
winners:

| design | sequence | ipSAE | grv | tm | ecl3 | plddt |
|---|---|---|---|---|---|---|
| c3-j2-run8 | TVSFTDFKTGFTITVL | 0.862 | 1 | 1 | 5 | 65 |
| c3-j2-run2 | TVLVVEDLKTGYNITIM | 0.859 | 1 | 2 | 7 | 62 |
| c3-boltz-run1 | GRVIYIPGDRTTVPVPGA | 0.858 | 4 | 0 | 3 | 66 |
| c3-jun-run6 | TVFEYRGFTIKVM | 0.846 | 1 | 2 | 7 | 71 |

Campaign 3 total: 19 screened designs (6 more re-folding), 4 HIT designs,
10 designs at ipSAE >= 0.75. These four are submission candidates.

## Campaign 4 (`c4-junction-scale`): 30 more junction designs, 2 HITs

Ran 2026-10-20 (30 single-design runs, ~3 min each, all screened).

- **2 two-domain HITs**: `c3-j3-run11` (ipSAE 0.846, groove 4 + tm 1 + ecl3 4)
  and `c3-j3-run3` (0.807, groove 1 + tm 2 + ecl3 3, binder pLDDT 77).
- Deep-reach cluster without groove contact: `run7` (0.846, tm 3 + ecl3 3),
  `run13` (0.843, tm 3 + ecl3 6), `run21` (0.838, tm 3 + ecl3 4) — all at
  binder pLDDT 74-75.
- Three campaign-4 designs enter the top eight by composite: `j3-run13`
  (15.65, rank 4), `j3-run18` (14.50), `j3-run24` (14.18).

Campaign 3 totals after four batches: **47 designs screened, 7 HIT designs**,
13 designs at ipSAE >= 0.80. Full table: `c3-candidates.csv`.


## Campaign 5 (BindCraft2) — cross-reference

`c5-bindcraft2-junction` (50 trajectories, peptide modality, 15-18 aa) ran
after this campaign. BindCraft2 accepted 0/50, but its raw designs scored by
this campaign's screen include the challenge's best design so far
(`c5-bc2-l18_bfe509d11b1b8f27`, ipSAE 0.861, two-domain HIT). Details:
`notes/best-per-campaign.md` and `docs/tool-audit-2026-10-20.md`.
