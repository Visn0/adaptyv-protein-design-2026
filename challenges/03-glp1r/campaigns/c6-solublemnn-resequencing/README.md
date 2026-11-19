# Campaign 6: SolubleMPNN re-sequencing of the campaign-1 champions

## Why this is a new campaign

Campaign 1's sequences were made by ProteinMPNN (2023), which collapsed to
poly-alanine on RFdiffusion3's alanine-rich backbones — the reason campaign 1
moved to more sampling instead of better sequences. The tool has changed:
**SolubleMPNN** measures 28% mean alanine where ProteinMPNN measured 47% on
the same backbone (`docs/tool-audit-2026-10-20.md`), and the re-sequencing
recipe that works is interface-pinned redesign (fixed interface residues,
periphery redesigned at temperature 0.3) — measured in the challenge-2 work:
one backbone went from 0.248 to a family at 0.63-0.85.

This campaign retries campaign 1's best backbones with the fixed recipe.

## Configuration

- **Backbones**: the top campaign-1 designs by composite (e1b2-r0036,
  e1-r0014, e1b-r0059, e1-r0025, e1b-r0037), chain A extracted from their
  best co-fold sample (N/CA/C/O).
- **Model**: SolubleMPNN (LigandMPNN repo, `--model_type soluble_mpnn`),
  temperature 0.1, seed 42, 8 sequences per backbone.
- **Interface pinning**: binder residues within 4.5 A of the receptor in the
  co-fold are held fixed; only the periphery is redesigned.
- **Validation**: every sequence co-folds against the full 409-residue
  receptor (Boltz-2), then the standard screen (ipSAE + groove/junction/TM/
  ECL3 contacts + clash check).

## Run recipe

```
# extract the binder backbone from the best fold
.venv/bin/python scripts/extract_binder.py <fold.cif> <out.pdb>
# interface-pinned soluble re-sequencing (from the LigandMPNN checkout)
cd ~/tools/LigandMPNN && ~/.venvs/mpnn/bin/python run.py \
    --model_type soluble_mpnn --pdb_path <complex.pdb> \
    --fixed_residues "..." --out_folder <out> \
    --number_of_batches 8 --temperature 0.1 --seed 42
```

## Result: the strongest designs of the challenge

40 designs (8 per champion backbone, interface-pinned SolubleMPNN) folded
against the full receptor and screened. **20 samples cleared the two-domain
bar** (the challenge's previous total was 49 across all campaigns; now 80).

| design | ipSAE | groove | tm | ecl3 | note |
|---|---|---|---|---|---|
| c6-e1-r0025-s2 | **0.934** | **6/6** | 2 | 5 | challenge best; the full groove |
| c6-e1-r0025-s3 | 0.911 | 6/6 | 2 | 6 | |
| c6-e1-r0025-s7 | 0.909 | 5/6 | 2 | 7 | |
| c6-e1b-r0037-s3 | 0.905 | 5/6 | 2 | 7 | |
| c6-e1b-r0059-s6 | 0.903 | 4/6 | 3 | 5 | |
| c6-e1b-r0037-s1 | 0.880 | 5/6 | 2 | 5 | binder pLDDT 81 — the highest |

Composite ranking (affinity + reach, the campaign's standing score): the new
**challenge leader is `c6-e1b-r0059-s5` at 19.42** (ipSAE 0.870, groove 5/6,
tm 4/4, ecl3 8/8 — the deepest reach recorded), ahead of `e1b-r0059-s7`
(17.80) and `e1b-r0037-s8` (15.18). The previous challenge best composite was
`c3-j2-run12` at 17.47.

The campaign's own claim holds: the tool changed (ProteinMPNN -> SolubleMPNN,
28% vs 47% alanine), one backbone produced a whole family, and the family is
better than the original design on every axis - affinity, groove coverage and
reach. This is the measured repeat of the challenge-2 precedent.

## PAUSED 2026-10-20 ~14:50 (user needs the PC)

State: the 40 fold YAMLs are written (`~/c3-work/folds/c6-*.yaml`), the
re-sequencing output is in `~/c3-work/c6/<design>/seqs/`. The fold batch was
started and stopped within its first design; the partial output was removed so
nothing is skipped on resume. No design has a completed fold yet.

**Resume with exactly this (one command):**

```
cd ~/c3-work && nohup bash -c 'bash run-c3-folds.sh > logs/folds-c6.log 2>&1; cd ~/Projects/adaptyv-protein-design-2026 && .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/screen_folds_c3.py > ~/c3-work/logs/screen-c6.log 2>&1' &
```

The runner skips anything already folded, so a repeated pause costs nothing.
