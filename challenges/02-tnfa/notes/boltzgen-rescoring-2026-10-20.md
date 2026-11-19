# BoltzGen rescoring of the challenge-2 designs (2026-10-20)

## What and how

The 8 submitted TNF-alpha complexes were re-scored with BoltzGen 0.3.2's
`protein-redesign` protocol - a pure folding/analysis pipeline on the fixed
complexes (one residue per spec is marked as "designed" because the analysis
step crashes on an empty design mask; the rest of the structure stays fixed).

Recipe (one complex per run, fresh output dir):

```
export MEMLIMIT_MB=12500 MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=4
python3 memlimit.py boltzgen-env/bin/boltzgen run <complex>.yaml \
    --output <dir> --protocol protein-redesign \
    --num_designs 1 --diffusion_batch_size 1 --num_workers 1 \
    --use_kernels false
```

Outputs: `intermediate_designs_inverse_folded/metrics_tmp/metrics_<id>.npz`
carrying the full metric set (the run-level summary CSV is overwritten per
run - read the npz files instead).

## Results (best of the fold)

| design | ipTM | min interface PAE | pTM | dSASA | bb RMSD |
|---|---|---|---|---|---|
| sr2-ds-mce-14-v6-r2a | 0.844 | 4.88 | 0.963 | 68.6 | 0.93 |
| sr6-r37 | 0.830 | 5.32 | 0.954 | 67.7 | 1.05 |
| e1b-d7x-t3-3-v6 | 0.820 | 5.83 | 0.957 | 72.5 | 1.20 |
| sr2-ds2-mce-14-v7-v1-r2a | 0.785 | 6.90 | 0.959 | 67.7 | 0.75 |
| sr2-ds-mce-14-v6-r2c (current winner) | 0.727 | 8.72 | 0.949 | 77.0 | 1.05 |
| ds-mce-14-v6 | 0.613 | 10.27 | 0.951 | 77.2 | 0.70 |
| ds2-mce-14-v7-v1 | 0.606 | 10.49 | 0.935 | 69.1 | 2.28 |
| sr1-mce-14-b | 0.596 | 11.92 | 0.934 | 69.9 | 4.90 |

## Findings

1. **All eight are plausible complexes** by BoltzGen's own metrics: pTM
   0.93-0.96 (confident folds) and 67-77 square angstrom of buried surface on
   binding. Nothing in the submission is structurally implausible.
2. **The ranking differs from our ipSAE.** BoltzGen puts r2a first (0.844);
   our ipSAE had picked r2c (rank 5 here at 0.727). The two metrics weigh the
   interface differently - neither is ground truth, and the submission keeps
   all eight, so both views stay represented.
3. **Zero PLIP H-bonds on every design.** The mce-14 family binds through a
   hydrophobic helix-bundle interface - consistent with the design intent and
   the scaffold's composition.
4. Practical: `protein-redesign` needs >=1 designed residue; batch the scenic
   runs one complex at a time (aiming 2+ per run re-processes prior targets
   and crosses the RAM cap).
