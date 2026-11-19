# Path to a Challenge-2 submission (state: 2026-10-15)

Deadline: **Oct 18, 23:59 AoE**. If C2 does not fit, the same factory serves
C3–C5 — only the target/epitope inputs change.

## Step 1 — local (minutes, already executable)

```bash
make fetch-data                       # if data/ is empty
pdt exp run --challenge 02-tnfa c2-anchors c2-switch-motif c2-scorer-controls -j 3
```

Targets: 14 anchor candidates / 7 switch-conserved; motif clearances
4.57 / 5.00 / 3.79 Å; scorer controls reproduce (FcRn −1.02/3 sites).

## Step 2 — generation (EXTERNAL; needs a CUDA GPU: Colab Pro / Modal / cloud)

RFdiffusion, binder design mode — exactly as in `reference/upstream-readme.md` §3:

- target: `inputs/target_AB.pdb` (chains A, B; residues 6–157, contiguous —
  do NOT crop further, cropping fragmented the chains last time)
- contigs: `[A6-157 B6-157 85-85]`, hotspots: `A103,B112,B103`, `diffuser.T=50`
- **sample size is the lever:** upstream generated 32 backbones, got 12 past the
  coverage filter, and nothing docked. Budget hundreds of backbones and expect
  low-percent pass rates. Batch this overnight, not "same-day".

Drop the resulting backbones into `02-tnfa/inputs/backbones/` and run:

```bash
pdt exp run --challenge 02-tnfa c2-coverage-scan
```

`tools/switch/switch_positions.py` finds which binder positions face the
cation triad (≥2 sites required), writes a ProteinMPNN His-bias file
(`*_bias.jsonl`) and a per-backbone report.

## Step 3 — sequence design + fold validation (EXTERNAL; CUDA)

Colab: ProteinMPNN with the His bias, then AlphaFold2 validation
(`initial_guess=True`, `num_recycles=3`, `use_solubleMPNN=True`, no Cys).
Drop folded **complex** PDBs into `02-tnfa/inputs/complexes/`.

## Step 4 — local screening → submission

```bash
pdt exp run --challenge 02-tnfa c2-score-designs      # linkage_score over folded complexes
python -m tools.switch.build_submission --mpnn <mpnn_results.csv> \
    --switch-report <switch_report.csv> --out submission.csv
```

`build_submission.py` places the histidines, pairs every switch variant with an
unmodified control (keep that — controls make a positive result interpretable),
and writes the CSV plus a sequences-only copy. Validate with
`tools/analysis/validate_submission.py` before uploading.

## Hard-won rules (do not re-learn these)

- One histidine cannot reach the ≥100× selectivity a switch needs (linkage
  ceiling: ~25× per ideal site). Target ≥2 sites, ideally 3.
- His faces target **cations** (Arg/Lys) for this direction; His-vs-carboxylate
  runs backwards (binds harder at 6.0).
- Score conservation by **chemistry class** (Glu↔Asp fine; His↔Tyr destroys it
  silently — that is the A73 trap).
- The scorer RANKS, it does not predict: PROPKA is compressed ~2 orders vs real
  switches. Use it for filtering, not for claims.
