# OpenFold3 v0.5.1 - install and attempt (2026-10-30)

**Status: installed and functional; not usable for this challenge's complex on
this host.**

- Installed per the official route: `uv venv ~/.venvs/openfold3 --python
  3.12`, `uv pip install openfold3`, `setup_openfold --non-interactive`.
  Weights: OpenBind-0 (`~/.openfold3/of3-ob-2025-06-30-174k.pt`, the
  maintainers' recommended inference checkpoint). The Biotite CCD download
  completed. Torch 2.15.0+cu132.
- First real fold - the champion against the full 639-residue TfR1
  ectodomain (715 residues total) - ran the model for ~24 minutes, then died
  at a triangular-attention layer with `CUDA_ERROR_OUT_OF_MEMORY`
  ("Failed to create GPU mapping", a WSL GPU-PV VMM failure), 12 GB card.
- Root cause in the code: `_configure_cuda_allocator()` sets
  `expandable_segments:True` by default, which routes through CUDA VMM
  (`cuMemCreate`/`cuMemSetAccess`) - exactly the calls this WSL host's GPU-PV
  stack fails on (the same family as the host's known `dxgkrnl` faults).
- Retry with `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False` (the code
  honours a user-set allocator env and leaves it untouched) reached the
  prediction stage, then **crashed the WSL host** (segfault, exit -11;
  `nvidia-smi` back after restart). No further large-input runs were made:
  the failure mode includes losing the whole guest, which is too expensive
  during a deadline week.
- Conclusion: OpenFold3 stays installed (small inputs are untested but the
  tool itself is fine on suitable hardware), and the confidence table keeps
  two independent folders (Chai-1, Boltz-2, 5 samples each) plus the
  unrestrained re-folds, the seed-7 re-folds, the mouse cross-folds and the
  structural-novelty arm. A third folder is a next-machine item, not a
  next-day item.

Evidence: `~/c4-work/openfold3/out-champion/summary.txt` (0/1 success),
`out-champion/logs/predict_err_rank0.log` (the OOM trace),
`of3-champion2.log` (the retry, host crash).
