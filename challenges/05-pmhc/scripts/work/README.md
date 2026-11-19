# 05 scripts/work — the C5 hand scripts

- `c0-build-controls.py` — builds the C0 calibration inputs: control PDBs
  (7OW6/7OW5 complexes, also copied to the gitignored `inputs/controls/`),
  Boltz-2 fold yamls (chains A=TCRα, B=TCRβ, C=HLA, D=β2m, E=peptide; MSAs
  wired in from `inputs/msa` when present), and chai input dirs
  (`in.fasta` + `restraints.csv`, one restraint row set per binder chain).
- `c0-crystal-read.py` — step 0 of C0: contact metrics straight from the two
  crystals (the ground truth the folded reads must reproduce).
- `c0-tri-state-metric.py` — the C0 scorer: ipSAE chain-pair table (via
  `~/tools/IPSAE/ipsae.py`) + contact metrics per sample, per arm;
  writes `campaigns/c0-instrument-calibration/records/`.
- `fetch_msas.py` — depth-capped a3m fetch from the ColabFold server, cached
  by sha1(seq)-depth, with per-sequence retries (the shared server is flaky).
- `fetch_msas_local.py` — the local fallback: depth-capped a3m from the
  on-disk mmseqs databases (`~/prescreen-dbs/{swissprot,pdb}`, merged and
  deduplicated), same file-naming contract as `fetch_msas.py`, provenance in
  `inputs/msa/msa-provenance.json`. Used when the ColabFold API is down.

Run order for C0 is in `campaigns/c0-instrument-calibration/README.md`.
