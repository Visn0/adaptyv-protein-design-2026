# Genie 3 on the local box: feasibility yes, designs no

Date: 2026-10-16. Working artifacts: `~/c2-work/genie3/` (not in git).

## Why

The calibration on the released TNF-α campaign showed the generator dominates
outcomes: Genie 3 produced 8 of 23 binders there; our RFdiffusion3 produced 1 of
40. This run tests whether Genie 3 runs on the 12 GB card and what its designs
score under our calibrated protocol.

## Feasibility: yes, comfortably

- Checkpoint 347 MB (`yeqinglin/genie3`, Apache-2.0, ungated); `torch 2.7.1+cu128`
  in `~/.venvs/genie3` (Python 3.10); generation needs no ColabFold/ESMFold.
- `genie3 generate` on the released TNF-α problem (`10_tnfa`, hotspots B102+D62,
  binder length 50–120): **8 designs in 525 s (66 s each)**, peak 2.43 GiB under
  the memlimit, GPU about 4.5 GB, one-time warmup 76 s. A 100-design batch is
  about 1.8 h.
- Placement: **8 of 8 designs engage the designed interface** (CA–CA 4.3–8.1 Å
  to B102/D62; 18–32 target residues within 10 Å). The model reliably hits the
  specified epitope.

## Designs: negative under our calibrated protocol

Sequences: ProteinMPNN CA-only (the model's own setting), chain A only,
`v_48_020`, T = 0.1, best of 8 per design. Folds: our campaign protocol
(Boltz-2, 5 samples, seed 42, cap 12.5 GiB; peak 9.75 GiB RSS / 8.2 GiB GPU).
Screen: ipSAE (10 Å) plus the designed-site rule — the problem's B102 and D62
map to fold positions 108 and 68 (their chains are our construct minus its first
six residues), and the two halves must touch the binder on different protomers.

- Best ipSAE of all 40 folds: **0.252** (genie3-d6 sample 0 — touches only one
  half of the epitope).
- Best at-site ipSAE: **0.248** (genie3-d7 sample 0, crossing D/C); ten of the
  fourteen at-site samples score **0.000**.
- Max pDockQ2: 0.273 (d6 s0) — over the 0.23 pose line, but off-site and far
  under the score bar.
- Reference numbers in the same protocol: released real binders 0.86–0.90; our
  campaign's best off-site 0.455; bars are 0.6 (discard) and 0.8 (submit).

The pattern matches the whole campaign: the generator places binders on the
epitope and the co-fold finds no confident interface ("touching, not docking").
The CA-only ProteinMPNN sequences are the likely weak link.

## Verdict

No design from this batch is promising. Genie 3 is usable and fast on this box;
the next lever is sequence quality (full-backbone MPNN, more sequences per
design, larger batches), not generator speed.

## Artifacts

- `genie3/designs.csv` — the 8 binder sequences with their MPNN scores.
- `genie3/fold-scores.csv` — all 40 fold scores with site flags.
- Working copy: `~/c2-work/genie3/` (CA traces, MPNN outputs, folds, logs).
