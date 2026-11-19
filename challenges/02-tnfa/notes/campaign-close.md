# Campaign close — Challenge 2 (TNF-alpha conditional binder)

*16 October 2026. Scope: this closes the **RFdiffusion3 / BoltzGen campaign
track** (X1, X2, W2, X3) — not the challenge. Decision: **nothing from this
track goes into the submission**, on the pre-registered rule ("if W2 fails, stop
the campaign track and record the negative") plus the finding below. The
submission that went to Proteinbase on 18 October came from the separate Genie 3
line; see `../README.md`.*

## Why it is closed

No design in this campaign carries a TNF-alpha interface that survives an
independent structure prediction **at the site it was designed for**.

| stage | designs | result |
|---|---|---|
| X1 — BoltzGen, three hotspot sets | 150 | 0 docked (best ipSAE ≈ 0.005) |
| X2 — RFdiffusion3, the drug groove (Tamarind) | 72 | one fold cleared the ipSAE bar — but at a *different* site (see below) |
| W2 — the 8 shortlist designs, local GPU | 8 | one design reached ipSAE 0.733, again off-site |
| X3-A/B/C — local RFD3 on three patches, mouse/human | 72 | 0 that both clear the bar and sit at the designed patch |
| X3-D — the patch the fold model prefers | 96 | 0 of 6 folded, same result |

**Total: 18 designs co-folded (90 predicted samples). Zero samples clear the bar
and sit on the designed epitope.**

## The finding that should carry forward

`ipSAE` answers "is there an interface here", **not** "is the interface where the
design put it". Scoring folds by ipSAE alone selects interfaces anywhere on the
target:

- the earlier campaign's single "passing" fold (ipSAE 0.733) sits **15–18 Å from
  its designed groove**; the samples that do land on the groove score ≤ 0.433;
- in the X3 folds, the 9 samples that sit on their designed epitope score
  **0.000**, while the highest score in the batch (0.769) sits 18 Å away;
- the fold model prefers two surfaces on TNF — the drug groove
  (K65/Q67/E110) and the receptor-binding loops (R31/A33, Y84–91, A145–S147) —
  over every patch the design program was aimed at.

Selection must therefore require **score AND site together**. The check is
`handoff/scripts/screen_folds_site.py` (in this repo), with the site rules for
each set inside it.

## Bugs found on the way (each cost real time or a wrong number)

1. **IPSAE names its report after the model file, not the PAE file.** Copying
   Boltz outputs under new names silently removes the pLDDT file, and pDockQ2
   collapses to a floor value (0.0073 instead of 0.1325) while ipSAE stays right.
2. **`infer_ori_strategy` must be `hotspots` for a binder design.** Without it the
   diffusion origin comes from the structure's centre of mass and the binder is
   placed *inside* the target: 12 designs had their binder centroid 4.7–11.7 Å
   from the target centroid with 24–61 atoms under 2 Å. Corrected: 23–27 Å and
   0–2 atoms.
3. **A contig range must not skip a residue.** A trimmed target needs the contig
   built from the surviving blocks (`handoff/rfd3/make_patch.py`), or RFD3 stops
   with `Residue A20 not found in atom array`.
4. **A site check keyed by set name against per-design folders silently passes
   everything.** Every fold was scored against an empty site map and reported
   "no contact" until the map was matched by prefix.

## Numbers worth keeping (same machine, next time)

| item | value |
|---|---|
| RFD3 generation, trimmed patch target | 32–50 s per design, peak 7.0 GiB, GPU 8.8–11.9 GB |
| Boltz-2 co-fold, 4-chain ~540-residue complex | ~4 min, peak 7.6 GiB |
| Boltz-2 memory pressure needs | ≥11.3 GiB at cap-12 GiB settings — the WSL VM must be 16 GB |
| IPSAE scoring | CPU, seconds per sample |
| host | 32 GB Windows host; WSL capped 16 GB, every job under `memlimit.py` |

## What exists now

- The workbench (`pdt` CLI, app, run ledger) with the verdict layer, the fold
  pipeline and the shared `tools/insights.py`.
- The site-check screen and the RFD3 triage for patch-target runs.
- This record: `x3-strategy.md` (the strategy, the numbers, the finding),
  `w2-fold-triage.md` (the shortlist folds), `pc-session-1.md` (the GPU box).
- The designs and folds themselves: `~/c2-work/x3/` (out of git by design).

## Transfers to the next challenge

The pipeline and the pitfall list transfer as they are. The lesson that matters
most: **a docking score is not evidence about a designed interface** — check the
contacts against the designed residues, on two protomers, before any selection.
