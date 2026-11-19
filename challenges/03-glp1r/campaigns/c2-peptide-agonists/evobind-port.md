# EvoBind2 local port — recipe (2026-10-18)

EvoBind2's pinned stack (jax 0.4.30, TF 2.16, haiku from 2024) cannot target the
RTX 5070 (sm_120). The port below works; every step is needed.

## Environment

```
micromamba create -y -f environment.yml -p env          # as shipped
env/bin/pip install "nvidia-cuda-nvcc-cu12>=12.8"       # ptxas 12.9 for sm_120
env/bin/pip install -U "jax[cuda12]"                    # jax/jaxlib 0.11.x
env/bin/pip install -U dm-haiku                         # 0.0.17+
env/bin/pip install -U tensorflow                       # 2.21 (numpy-2 safe)
```

## Source patches (src/AF2)

- `jax.tree_map(` / `jax.tree_multimap(` → `jax.tree.map(` (29 sites)
- `jax.tree_flatten/unflatten/leaves/structure(` → `jax.tree.flatten/...`
- `clip(..., a_max=/a_min=)` → `max=/min=`
- `jax.util.wraps(fun, docstr=...)` → `functools.wraps(fun)` (mapping.py)

## Gotchas

- `--data_dir` must be `<repo>/src/AF2` — the code appends `params/` itself;
  pointing at `.../src/AF2/params` looks for `params/params/...`.
- The receptor MSA is ours (ColabFold, depth 512) — the setup's 30 GB
  uniclust/HHblits path is skipped entirely.
- Measured: ~28 s per optimisation iteration on the RTX 5070 (207-aa receptor
  fragment + 15-aa peptide), peak 7.6 GiB. 300 iterations ≈ 2.3 h.

## Inputs used (campaign 2)

- Receptor: GLP1R 6X18 chain R fragment 29-129 + 136-241 (207 aa,
  `data/c3/glp1r-frag.fasta`, byte-checked against the campaign-1 target pdb).
- Interface residues (fragment numbering): 39,41,60,63,93,100,163,176,187,200 —
  the campaign-1 groove + junction hotspots mapped to the fragment.
- MSA: `data/c3/glp1r-frag.a3m` (512 rows, ColabFold).
- Run: `mc_design.py --peptide_length=15 --num_iterations=300 ...`
  (linear; add `--cyclic_offset=1` for cyclic).
