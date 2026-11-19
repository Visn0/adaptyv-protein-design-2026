# MD binding movies

> **Clips cleared 2026-10-23.** No clip here shows a submitted design, so the
> MP4s and their `.meta.json` sidecars were deleted; `scripts/` is intact and
> the renders remain in git history.

Two movies of the promising designs against human TNF-α, from real all-atom
molecular dynamics: OpenMM, AMBER14 force field, GBn2 implicit solvent,
300 K, 120 ps per design, CPU platform (~1.7 ns/day under two concurrent
runs).

| Movie | Design | Interface at t=0 | Contacts held (mean → last half) | Binder RMSD |
|---|---|---|---|---|
| `d7x-t3-3_md-binding.mp4` | d7x-t3-3 (64 aa) | 24 residue pairs | 18.1 → 17.0 of 24 (75% → 71%) | 1.8 → 2.1 Å |
| `b2x-d12-2_md-binding.mp4` | b2x-d12-2 (92 aa) | 53 residue pairs | 33.0 → 31.5 of 53 (62% → 59%) | 2.5 → 3.1 Å |

Contacts held: frame-0 residue pairs (heavy atoms < 4.5 Å) still in contact
per frame. Binder RMSD: displacement of the binder relative to the target
after superposing the target chains — the binder breathes at the interface
but the contact count does not collapse.

Colours follow the project standard: binder pink (chain A), target blue
(chains B, C, D), interface residues amber (ball+stick). Style is
`surface+cartoon`: a translucent exterior surface over the cartoon ribbons.
The surface paints the binding hotspot (target residues within 8 A of the
binder) amber and the binder pink, so the binding area reads at a glance.
Frames are superposed on the target chains; the camera keeps the binder→target
axis horizontal and makes one full turn over the clip. A HUD panel carries the
live numbers of the current frame, and a hot-zone inset zooms into the
interface residues with dashed lines between the closest contacting atoms.

Interactive companion: `../viewers/` holds one self-contained HTML explorer
per design (cartoon / surface / both, spin, interface highlight).

Inputs: the Boltz-2 folds — `d7x-t3-3` sample 0, `b2x-d12-2` sample 2.
Tool choice and the alternatives surveyed: `../notes/md-animation-tools.md`.

Mouse TNF: these two designs were folded against **human** TNF only. No mouse
fold exists for them, and the movie work does not run folds — the mouse
question is open and belongs to the experiment owners. The earlier W2
shortlist mouse comparison (a different design round) is in
`../notes/w2-fold-triage.md`; the lesson there: a fold cannot prove species
selectivity, the lab assay decides.

## Reproduce

The scripts that built these movies live in `scripts/` (run with the project
venv from the repo root):

```bash
# 1. prepare + simulate + package a run dir (per design)
.venv/bin/python challenges/02-tnfa/md-movies/scripts/build_md.py prep \
    --design d7x-t3-3 --cif <fold>.cif --run-dir ~/c2-work/md-anim/runs/d7x-t3-3
.venv/bin/python challenges/02-tnfa/md-movies/scripts/build_md.py run \
    --design d7x-t3-3 --run-dir ~/c2-work/md-anim/runs/d7x-t3-3 \
    --length-ps 120 --equil-ps 12 --save-every-ps 2
.venv/bin/python challenges/02-tnfa/md-movies/scripts/build_md.py pack \
    --design d7x-t3-3 --run-dir ~/c2-work/md-anim/runs/d7x-t3-3 --movie-frames 60

# 2. render (needs a Chromium binary on this box)
PDT_CHROME=~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome \
    .venv/bin/python challenges/02-tnfa/md-movies/scripts/render_movies.py
```

## Honesty

A short run like this is a physics test of the predicted pose. It is not a
binding assay, and it is not a free-energy calculation. The movies carry the
same captions.
