# Blender / Molecular Nodes binding animations

> **Clips cleared 2026-10-23.** No clip here shows a submitted design, so the
> MP4s and their `.meta.json` sidecars were deleted; `scripts/` is intact and
> the renders remain in git history.

The same two MD trajectories as `../md-movies/`, rendered in Blender with the
Molecular Nodes addon — a second, higher-fidelity look at the same runs:
Cycles path tracing, studio lighting, cartoon ribbons, amber ball-and-stick
interface, one full turntable turn.

| Clip | Design | Source run |
|---|---|---|
| `d7x-t3-3_mn-binding.mp4` | d7x-t3-3 (64 aa) | `~/c2-work/md-anim/runs/d7x-t3-3` |
| `b2x-d12-2_mn-binding.mp4` | b2x-d12-2 (92 aa) | `~/c2-work/md-anim/runs/b2x-d12-2` |

Both: 1920x1080, 24 fps, 6.0 s — one full camera turn over 5 s, then the last
frame holds for 1 s.

Colours follow the project standard: binder pink `#e879f9` (chain A), target
blue `#60a5fa` (chains B-D), interface residues amber `#fbbf24`
(ball-and-stick), background navy `#0b0f14`. The amber residue sets are the
same lists the 3Dmol movies paint, taken from each run's `summary.json`.

Playback: Molecular Nodes `subframes=1` — each MD frame spans two scene
frames and positions interpolate, so all 60 MD frames play over 120 render
frames (2x slow motion).

## Reproduce

Blender 5.2 + the Molecular Nodes extension (v520.2.0):

```bash
# one-time: blender tarball -> ~/tools, symlink ~/.local/bin/blender
curl -LO https://download.blender.org/release/Blender5.2/blender-5.2.2-linux-x64.tar.xz
tar -xf blender-5.2.2-linux-x64.tar.xz -C ~/tools/
ln -s ~/tools/blender-5.2.2-linux-x64/blender ~/.local/bin/blender

# one-time: the addon
curl -LO https://github.com/BradyAJohnston/MolecularNodes/releases/download/v520.2.0/molecularnodes-520.2.0-linux_x64.zip
blender -b --command extension install-file -r user_default -e molecularnodes-520.2.0-linux_x64.zip

# render (CPU Cycles, ~20 min per clip on 12 threads)
blender -b --python challenges/02-tnfa/mn-movies/scripts/build_mn.py -- \
    --design d7x-t3-3 --mode anim --engine cycles --samples 32 --outdir out/
```

`--mode still` renders a single frame instead (a quick look check);
`--help` lists the knobs (samples, resolution, margin, elevation, orbit
length, hold, fps, light boost).

The script needs the run dirs under `~/c2-work/md-anim/runs/` (the packed
`*_frames.pdb` trajectories) and writes an H264 MP4 via Blender's own
encoder.

## Design carousel (`tnfa-carousel-22-designs.mp4`)

The campaign's designs in one loop: the TNF-α trimer as a grey surface,
rotating slowly; every second the visible binder (light-blue cartoon) switches
to the next design — every design that has a co-fold against the human
construct and passes the at-site screen (ipSAE ≥ 0.6, one entry per unique
binder sequence, 22 designs; the submitted set is included under its submitted
names).

1080x1350 (4:5), 24 fps, 22 s. Light studio look (white background) after the
Apheris x Wells Wood showcase video; the binder blue `#77c9eb` is that video's
colour, not the house pink. `prep_carousel.py` superposes every co-fold onto
one common target frame (chains B/C/D Cα, Bio.PDB `Superimposer`), so only the
binder changes between seconds.

```bash
.venv/bin/python challenges/02-tnfa/mn-movies/scripts/prep_carousel.py
blender -b --python challenges/02-tnfa/mn-movies/scripts/build_carousel.py -- \
    --mode anim --samples 24 --device GPU --outdir ~/c2-work/mn-anim/carousel_render
blender -b --python challenges/02-tnfa/mn-movies/scripts/build_carousel.py -- \
    --pass binder --samples 24 --device GPU \
    --binder-dir ~/c2-work/mn-anim/carousel_render/binder_frames \
    --outdir ~/c2-work/mn-anim/carousel_render
bash challenges/02-tnfa/mn-movies/scripts/compose_carousel.sh \
    ~/c2-work/mn-anim/carousel_render/carousel_raw.mp4 \
    ~/c2-work/mn-anim/carousel_render/binder_frames \
    ~/c2-work/mn-anim/carousel_render/carousel_comp.mp4
python3 challenges/02-tnfa/mn-movies/scripts/finish_carousel.py \
    --raw ~/c2-work/mn-anim/carousel_render/carousel_comp.mp4 \
    --out challenges/02-tnfa/mn-movies/tnfa-carousel-22-designs.mp4
```

The second render pass draws the visible binder with the target invisible to
the camera but still lighting the scene, and `compose_carousel.sh` overlays it
on the first pass — a few folds tuck the binder deep into the junction groove
and the opaque surface would hide them completely.

## Honesty

Same as `../md-movies/`: a short run like this is a physics test of the
predicted pose. It is not a binding assay.
