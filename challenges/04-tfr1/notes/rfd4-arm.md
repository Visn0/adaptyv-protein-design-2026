# RFD4-Proteina hosted arm (campaign-1 material)

Status: complete for the four epitope sets. 97 unvalidated design candidates
(full-atom complexes with sequences) in `~/c4-work/rfd4/`, aggregated in
`~/c4-work/logs/rfd4-batch.csv` and `~/c4-work/rfd4/binders-all.fasta`.

## Recipe (reproducible)

- Client: `~/tools/bionemo-agent-toolkit/skills/bionemo-agent-toolkit/skills/rfd4-proteina-nim/scripts/design.py`
- Destination: hosted, `https://health.api.nvidia.com/v1/biology/ipd/rfd4-proteina/generative`
- Auth: `NVIDIA_API_KEY` sourced from the repo `.env` (file is gitignored; the
  value never appears in a command line, a script, or this note).
- Requests: `nim/build_request.py --set <E0|E1|E2|E12> --replicates 8` builds
  `request_tfr1_<set>_r8.json` (annotated 11QC CIF inline; E0/E1/E2/E12
  hotspot letters asserted at build time).
- Schedule: `thinking_medium` (60 steps, 185 trunk passes), one call per
  8 replicates. Run dirs: `~/c4-work/rfd4/<set>/run-N/` with `request.json`,
  `transport.json`, `response.raw`, `summary.json`, per-design mmCIF + fasta.
- Batch runner: `~/c4-work/bin/rfd4-batch.sh` (sequential, 10 s gap); analyzer:
  `~/c4-work/bin/rfd4-analyze.py`.

Wire-contract notes that cost a call: `metrics.tags` accepts only names from
the server enum (`design`, `hotspot_conditioning`, ...) - a custom challenge
tag returns HTTP 422 `schema_violation`. Keep provenance in the run dirs and
notes, not in a metric tag.

## Results (returned poses; no oracle ran on this deployment)

| set | designs | binder length (median) | all hotspots contacted in pose | hotspot obedience (mean) | binder residues at site (median) |
|---|---|---|---|---|---|
| E0 | 24 | 61-110 (85) | 24/24 | 0.86 | 13 |
| E1 | 24 | 65-109 (91) | 24/24 | 0.65 | 10 |
| E2 | 24 | 64-106 (87) | 5/24 | 0.79 | 10 |
| E12 | 25 | 62-108 (88) | 25/25 | 0.62 | 5 |

Quality across all 97: motif all-atom RMSD <= 0.49 A, clash fraction <= 0.0003,
sequence adherence 1.0. Wall time ~2.5 min per 8-design call.

## Read

- The generator obeys the **E0 tip patch** cleanly (24/24 designs contact all
  six hotspots; the largest at-site interfaces of the four sets). That is the
  same surface the local co-fold screen cannot read (see `c1-triage.md`), so
  the generation-side and fold-side evidence point in different directions and
  neither vetoes a set on its own.
- E2 is the weakest for full-patch contact (5/24 contact all five hotspots)
  despite good per-design obedience; partial-patch poses dominate.
- E12's patch is thin (2 anchors), so its median at-site residue count is
  small by construction.
- Designs are generated poses, not predictions: they are unvalidated design
  candidates until the screen question (a working co-fold predictor) is
  answered. Every metric above is the service's own.

## Provenance for the methodology

Model `rfd4-proteina`, checkpoint
`chk_epoch_00000169_step_000000340000-ema.ckpt`, autoencoder
`2026_09_04_release_ae_z16_400k-ema.ckpt`, NIM 1.0.0, bioir backend,
`thinking_medium` schedule (recorded per run in `summary.json`). Runs executed
2026-10-24 07:39-08:02 CEST through the NVIDIA-hosted endpoint; request
payloads are committed under `challenges/04-tfr1/nim/`.
