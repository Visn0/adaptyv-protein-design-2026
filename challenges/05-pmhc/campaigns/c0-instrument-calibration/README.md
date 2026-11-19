# C0 — instrument calibration (the gate)

Registered 2026-10-30, before any run. Source of record:
`notes/strategies.md` section C0 + this file. Nothing here changes after the
first deciding run; corrections go into `records/` as dated notes.

## Question

Can any scorer we own separate the G12D state from the WT state for a
**known** binder — the JDI TCR? Until a scorer passes this, no design is
ranked on fold scores (the kill criterion below).

## Arms

| arm | binder | target | source |
|---|---|---|---|
| pos-g12d | JDI TCR (chains A,B) | G12D pMHC (C,D,E) | 7OW6 |
| pos-wt | JDI TCR | WT pMHC | 7OW5 |
| neg-peptidefree | JDI TCR | peptide-free MHC (C,D) | 7OW6 |
| neg-shuffled | shuffled JDI sequences (seed 42) | G12D pMHC | sequence-level |

Chain map in every input: A = TCR alpha, B = TCR beta, C = HLA-A*11:01 heavy
chain, D = beta2-microglobulin, E = peptide.

Notes: 7OW5's TCR is the affinity-matured JDIa41b1 — a 425 nM WT binder; the
control's signal is the ~6000x G12D/WT window, not binary binding. The
peptide-free arm is a metric sanity control (no published JDI peptide-free
read exists). The shuffled arm tests the scorer against a non-binder.

## Step 0 — the crystal ground truth (done 2026-10-30)

`scripts/work/c0-crystal-read.py` → `records/crystal-read.csv`:

| state | peptide contacts P4/P5/P6/P7/P8/P9 | P6 min dist to TCR |
|---|---|---|
| G12D | 2 / 4 / 5 / 32 / 9 / 3 | 3.37 A |
| WT | 5 / 5 / 5 / 35 / 9 / 3 | 3.48 A |

**The geometric ground truth barely differs between the states** — the two
crystals have nearly identical contact patterns (as the literature says:
discrimination is energetic, not geometric). Calibration consequence: a
metric that separates G12D from WT must do it on the ipSAE/energetic read or
on the electrostatic layer — contact counts alone cannot separate the states
by construction. If the folded reads inherit this near-identity, the kill
criterion fires and selection falls back as registered.

## Instruments

1. **Boltz-2 folds** (5 diffusion samples, seed 42, depth-capped MSAs) +
   `ipsae.py` chain-pair table. Per sample: the six binder x target pairs
   (A-C, B-C, A-D, B-D, A-E, B-E); **peptide read** = max over binder chains
   of ipSAE_min(binder, E); HLA read vs C; b2m read vs D. Plus contact
   metrics from the model (P6 min distance, binder residues within 4.5 A of
   the peptide, per-chain contact counts).
2. **Chai-1 restrained** — pocket restraints on peptide P4–P8 and groove rim
   (65, 155), one row set per binder chain; **single-sequence control run**
   (no MSA; the design screens later use the msa_pqt route — a difference to
   keep in mind when comparing reads). Chai writes no PAE: contact metrics
   only, plus iptm from the scores npz.
3. **BindCraft2 `bindcraft score`** on the folded complexes — contact
   fractions (Hotspot_Contact_Fraction / Off_Epitope_Contact_Fraction).

## Metric and cutoffs

`scripts/work/c0-tri-state-metric.py` writes `records/metrics.csv` and
`records/summary.txt` (per-arm means, min/max, and the G12D-minus-WT delta).
**Cutoffs are fixed after this run and before any design batch**, recorded as
a dated addendum to this file.

## Kill criterion (registered)

If no instrument separates G12D from WT on the JDI control, we do not rank on
fold scores at all — selection falls back to the electrostatic placement rule
(strategies C3) plus footprint geometry, and the submission says so.

## Cost and commands

Inputs and MSAs (done):

    .venv/bin/python challenges/05-pmhc/scripts/work/c0-build-controls.py
    # MSA source A (network): ColabFold, when reachable —
    .venv/bin/python challenges/05-pmhc/scripts/work/fetch_msas.py \
        --fasta ~/c5-work/c0/seqs/msa-targets.fa \
        --out-dir challenges/05-pmhc/inputs/msa
    # MSA source B (local, used 2026-10-30 — ColabFold API was down):
    .venv/bin/python challenges/05-pmhc/scripts/work/fetch_msas_local.py \
        --fasta ~/c5-work/c0/seqs/msa-targets.fa \
        --out-dir challenges/05-pmhc/inputs/msa
    # then re-run the builder, to wire the a3m paths into the yamls

Folds (serial, one GPU job at a time, under the memory cap):

    mkdir -p ~/c5-work/bin && cp ~/c4-work/bin/memlimit.py ~/c5-work/bin/
    for y in ~/c5-work/c0/folds/*.yaml; do
      name=$(basename "$y" .yaml)
      /usr/bin/python3 ~/c5-work/bin/memlimit.py \
        ~/.venvs/boltz/bin/boltz predict "$y" \
        --out_dir ~/c5-work/c0/folds/"$name" --seed 42 \
        --diffusion_samples 5 --output_format cif
    done

    for arm in pos-g12d pos-wt neg-peptidefree neg-shuffled; do
      ( cd ~/c5-work/c0/chai/designs/"$arm" && MEMLIMIT_MB=17000 \
        /usr/bin/python3 ~/c5-work/bin/memlimit.py \
        ~/.venvs/chai/bin/chai-lab fold in.fasta out \
        --constraint-path restraints.csv --no-use-esm-embeddings \
        > fold.log 2>&1 )
    done

    .venv/bin/python challenges/05-pmhc/scripts/work/c0-tri-state-metric.py

Do not SIGTERM chai in its first ~60 s (host-crash lesson, 2026-10-26). The
old `ipsae.py` scratch copy was pruned — the live one is
`~/tools/IPSAE/ipsae.py` (already wired into the metric script).

## Status

- [x] inputs built (control PDBs, boltz yamls, chai inputs)
- [x] crystal read (step 0) → `records/crystal-read.csv`
- [x] MSAs fetched — source: **local mmseqs over the on-disk SwissProt+PDB
  databases** (`scripts/work/fetch_msas_local.py`); the ColabFold API was
  unreachable from this network on 2026-10-30. Depths: HLA 254, WT-HLA 258,
  β2m 169, TCRα 415, TCRβ 608 rows; provenance in
  `inputs/msa/msa-provenance.json`. Shallower than a UniRef fetch — if the
  ColabFold server recovers before the design batches, richer MSAs are a
  drop-in improvement (delete the a3m, re-fetch, re-run the builder).
- [x] boltz folds — **Fv-trimmed set** (`~/c5-work/c0t`, 621 res; TCR chains
  cut at the FR4 V/C boundary: 181+245 → 120+116). The full-size 811-res
  constructs crash this host at fold start (three `0x20001` crashes on
  2026-10-30; one clean full-size pos-g12d fold exists, run under the
  hardening: allocator override + VRAM watchdog + fresh boot). Trim
  consistency is recorded below.
- [x] chai folds — single-sequence passes done (documented blind contrast);
  the **MSA pass** (`msa_pqt`, built by `scripts/work/build_chai_msa.py`)
  done for all four arms — the instrument works (0.895/0.877/0.797/0.653).
- [x] metric + cutoff addendum (below) — C0 CLOSED 2026-10-31 10:45.
  Verdict: three instruments separate binding quality; none separates
  G12D-vs-WT as a ranking signal (chai-MSA shows a small correctly-signed
  supporting delta). Selection carries specificity on the C3 rule +
  footprint discipline, per the pre-registered kill criterion.

## Cutoff addendum — registered 2026-10-31, before any design ranking

Source: `records/summary.txt` (trimmed set, boltz-2, 5 samples per arm).
Cutoffs here bind the design screens; changes are dated notes in `records/`.

### What the fold separates (usable)

| check | JDI control value | pre-registered cutoff |
|---|---|---|
| binding vs none (peptide-free) | hla_read 0.903 (bound) vs 0.487 (peptide-free) | a design must show a collapse of comparable size: hla_read(free) ≤ 0.7 x hla_read(G12D) |
| shuffled binder | all reads ≈ 0 (0.005) | sanity only |
| interface quality (G12D arm) | peptide_read 0.652, hla_read 0.903 | the organizers' gates stand: ipSAE_min ≥ 0.61 (0.70 stringent), joint ipSAE ≥ 0.6 + pDockQ2 ≥ 0.23 |

### What the fold does NOT separate (disqualified)

- **G12D vs WT fine specificity.** The JDI control — a real, G12D-specific
  binder — reads peptide 0.652 (G12D) vs 0.695 (WT): delta **−0.043, wrong
  sign**, inside the per-model spread (±0.02–0.03). Peptide contacts 58.6 vs
  70.2 (delta −11.6, also inverted). This is the pMHC face of the known
  AF2/Multimer ipTM 0.84/0.84 blindness: the folded read of this mutation is
  near-blind by construction (the crystal ground truth barely differs — see
  step 0).
- Therefore: **no design is ranked on Δ(fold scores) between the G12D and WT
  arms.** The WT and peptide-free arms stay in the tri-state screen as gross
  checks (is an interface present at all; is the peptide engaged), never as
  a fine ranking signal. Raw ipTM stays banned as a ranking input.
- The specificity axis is carried by the pre-registered fallback: the **C3
  electrostatic placement rule** (a binder basic side-chain nitrogen 6–8 A
  over P6–P7 of the peptide) plus the peptide-first footprint discipline
  (binder–HLA and binder–β2m contact shares stay weak).

### Third instrument — BindCraft2 `bindcraft score` (2026-10-31)

Geometry pass over all four arms, 5 models each (`records/bc2-score.csv`).
Means per arm:

| arm | Hotspot_Contact_Fraction | Off_Epitope | buried A² | all-atom clashes | interface res |
|---|---|---|---|---|---|
| pos-g12d | 1.00 | 0.05 | 882 | 1.4 | 17.6 |
| pos-wt | 1.00 | 0.11 | 867 | 2.6 | 17.8 |
| neg-peptidefree | n/a (no peptide) | n/a | 737 | 2.0 | 14.2 |
| neg-shuffled | 0.76 | 0.28 | 1846 | 12.2 | 34.0 |

- **Same split as the other two instruments:** the shuffled non-binder is
  cleanly separated (off-epitope 5.6x, clashes 9x, interface 2x the
  positives), and G12D vs WT is indistinguishable — hotspot fraction
  identical at 1.0, and the off-epitope reading tilts the WRONG way
  (0.05 G12D vs 0.11 WT). Three instruments, one verdict: structural-fold
  reads carry binding quality, not this mutation's specificity.
- BC2's hotspot fraction (on E4–E8) is 1.0 for both real complexes: the
  JDI fold satisfies the ridge hotspot definition in both states, as the
  crystal ground truth predicts.

### Second instrument — chai-1, single-sequence vs MSA (2026-10-31)

- **Single-sequence (documented contrast pass):** iptm 0.141 (pos-g12d) vs
  0.142 (pos-wt) — blind to even the presence of the binder. Recorded as the
  reason every design screen uses the `msa_pqt` route.
- **MSA pass (`--msa-directory`, depths 254–597; the route the screens use):**
  iptm by arm — pos-g12d **0.895** (0.883–0.902), pos-wt **0.877**
  (0.876–0.879), neg-peptidefree 0.797 (0.795–0.800), neg-shuffled 0.653
  (0.650–0.656).
- **This is the first correctly-signed separation in the campaign:** G12D > WT
  by +0.018 ipTM with non-overlapping 5-model ranges, and the state ordering
  is sensible (specific pair > cross pair > peptide-free > shuffled). Caveats:
  single seed, n=5, and ipTM is a whole-complex reading — this is recorded as
  *supporting* evidence, not as a ranking instrument. The specificity ranking
  stays on the C3 rule + footprint discipline (as pre-registered); the
  finalist stage re-reads this signal with more seeds.
- Contact metrics from the MSA pass ride along in `records/metrics.csv`
  (instrument `chai-msa`); note the shuffled arm shows the HIGHEST peptide
  contacts (151.6) with the LOWEST iptm — contact counts and confidence are
  anti-correlated for non-binders, which is why the C3/footprint filters
  never use raw contacts alone.

### Trim consistency (record)

Fv-trimmed vs full-size pos-g12d, boltz means: peptide_read 0.652 vs 0.676;
hla_read 0.903 vs 0.871; p6_min_dist 2.996 vs 3.014 A; peptide_contacts 58.6
vs 57.2 — every delta inside the per-model spread. The trimmed set is
canonical; the full-size fold stays as the consistency record in
`~/c5-work/c0` (the trimmed set lives in `~/c5-work/c0t`).
