# Challenge 3 videos

One episode, in the same format as the challenge-2 series: Manim scenes, the
edge-tts voice, the dark navy palette, mono font, soft subtitles + `.srt`
sidecar. The two molecular segments come from the established movie renderer
(3Dmol in headless Chrome — binder pink, target blue, interface amber).

| # | episode | length | contents |
|---|---|---|---|
| 1 | `01-glp1r-submission` | ~4.2 min | the brief, the target, the activation-geometry gate, the seven method families, the design reel (two seconds per design), the ranked first rows, the honest limits |

Build (from this directory):

```bash
# 1. the molecular segments: the design reel + the target clip
PDT_CHROME=~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome \
    ../../../.venv/bin/python scripts/build_reel.py --slow-reel
PDT_CHROME=~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome \
    ../../../.venv/bin/python scripts/build_reel.py --target-only

# 2. the episode
~/.venvs/manim-cf/bin/python build.py render 1 draft   # look check
~/.venvs/manim-cf/bin/python build.py audio 1          # edge-tts (retry on flake)
~/.venvs/manim-cf/bin/python build.py render 1 final
~/.venvs/manim-cf/bin/python build.py segments 1       # normalise the media segments
~/.venvs/manim-cf/bin/python build.py stitch 1         # concat + mux + subtitles -> out/
```

`scripts/build_reel.py --slow-reel` walks the ranked submission CSV
(`../submission/competition-submission-2026-10-21.csv`): one continuous slow
turn, frame by frame, with the design swapping every 2 s — the rotation never
restarts at a swap. Every frame renders a SWAP structure (`write_swap`): the
reference design's receptor (chain B) plus that design's own aligned binder
(chain A), so the target is the same atoms throughout and only the designed
protein appears and disappears. `--target-only` builds the S3_Target segment:
the receptor alone, turning slowly, with the GLP-1 pharmacophore residues in
amber.

Two renderer details that were hard to find:

- Surface styles race the screenshot (the surface computes in a web worker,
  Chrome shoots at page load) — the page holds its load event open until the
  surface is ready, via `LOAD_GATE` / `start_hang_server` in
  `tools/report/movie.py` (shared with every surface render now).
- Render long reels in batches of ~48 frames (`_render_pages` reuses the same
  `shot_*.png` names inside one work dir, so each batch must be copied out
  before the next one starts).

QA: `python3 qa_sheets.py` writes `qa/01-glp1r-submission_sheet.png`
(one frame every 10 s). The frame cache in `qa/frames/<slug>/` is reused when
present — delete it before regenerating after a re-render. Segments and the
per-design clips are regenerable and live outside git (`media/`,
`media_draft/`, `audio/`).

## Review notes for the next episode (from the user, 2026-10-21)

Recorded while experiments continue; the submitted designs may change, so the
next video is a fresh build. Apply all of these:

1. **The designed protein must read clearly.** His words: "the designed
   protein spheres make them a bit less transparent so they are more
   visible." The binder shows washed-out pink through the grey surface —
   raise its opacity, exclude the binder from the surface layer, or composite
   a binder-only pass (the challenge-2 carousel pattern).
2. **Swap the design every 2 seconds, not 1.** The current reel already runs
   at 2 s per design — keep it, and never go back to 1 s.
3. **Be less verbose; drop residue-level detail.** No per-amino-acid numbers,
   no residue lists, no counts for their own sake. Important facts only.
4. **Structure every episode around: hypothesis → tools used → steps →
   conclusions.** That is the frame he wants the narration to follow.
5. **Subtitles smaller.** He watches the mp4 directly, so the soft `mov_text`
   track renders at his player's default size. Burn the subtitles in at a
   small font (the `subtitles` filter with `force_style='FontSize=16'` at
   1080p) and keep the `.srt` sidecar.

## Episode 2 — the Molecular Nodes reel (2026-10-27)

`scripts/mn_reel.py` builds `out/02-glp1r-mn-reel.mp4` in the shape of the
reference clip Anton supplied: the receptor turning on the left, a metrics
panel on the right, one design at a time. No narration, no subtitles, and no
title or closing card — he asked for the reel and nothing else, so it opens on
rank 1 and ends on rank 10, thirty seconds in all.

The panel is deliberately thin: title, what the target is, rank, design name,
campaign method, binder length, molecule class, the composite score and the
three Boltz-2 metrics under a heading that names where they came from. The
footer carries `linkedin.com/in/anton-chernysh`.

The receptor renders at `transparency=0.35` — matched to the reference clip,
where it still reads as a solid body — so the part of each design that runs
behind or inside it still reads — the binder, not the target, is the
subject. Leave `fresnel` off: its grazing-angle rim darkens every edge of a
409-residue cartoon at once and the receptor comes out looking like scratched
glass (Anton's word was "weird ... kinda like glass with low definition"). The
cartoon runs at `quality=4` rather than the node default of 2, which is
visibly coarse at this size, and the receptor grey is `#949aa6` — a cool
neutral dark enough that the three-light rig still models it. Lighter greys
(`#d9d9de`, `#c2c2cc`) wash flat against the white page. Cast shadows are off:
they take the frame from 3.8 s to 27 s and add very little depth that the
tonal range of a darker grey does not already give.

On the ribbon profile: `peptide_shape` is a two-way switch, and `"Round"`
swaps the rectangular cross-section for an ellipse, so the helices read as
tubes at every thickness tried (0.6, 0.35, 0.22, 0.12). There is no
intermediate bevel exposed. Stay on `"Sharp"` and slim the ribbon instead —
`helix_thickness=0.45`, `helix_width=2.3` is where Anton settled.

```bash
# ALWAYS look at a frame first — the reel is ~30 min of CPU, a preview is ~8 s
.venv/bin/python challenges/03-glp1r/videos/scripts/mn_reel.py preview --frame 30
.venv/bin/python challenges/03-glp1r/videos/scripts/mn_reel.py          # all stages
.venv/bin/python challenges/03-glp1r/videos/scripts/mn_reel.py render --force
```

Three stages, each skipped when its output is already in `~/c3-work/mn-reel/`:

- **prep** — each design's Boltz co-fold is oriented so the receptor's long
  axis stands up (ECD at the top, PCA on the chain-B CAs), then superposed on
  the top design's receptor. One `target.pdb` plus ten binder PDBs in that
  shared frame, so only the binder swaps.
- **panels** — the panels are HTML, shot with the Playwright
  chromium (`PDT_CHROME`/`CHROME_PATH`). Every number is read from
  `records/selection-scores-*.csv`, `records/prescreen-report-*.csv` and
  `~/c3-work/folds-screen.csv` — nothing is computed in the builder.
- **render** — `scripts/mn_render.py` runs inside Blender 5.2 with the
  Molecular Nodes extension: cartoon styles, one pivot empty turning all
  eleven objects through a single revolution, RGBA frames that ffmpeg lays
  over the panel.

Renderer notes worth keeping:

- `Canvas.look_at` solves from the camera's `matrix_world`, which is still the
  old rotation right after `set_viewpoint` — aim, `view_layer.update()`, then
  fit, or the camera lands in the wrong place. Pass plain lists, not an
  ndarray.
- Framing uses a box around the assembly's *turning circle*, not its bounding
  box, so nothing clips as it rotates.
- `view_transform = "Standard"` plus `exposure = 1.8` keeps the render's
  colours equal to the panel's hexes and readable on a white page.
- EEVEE's default 64 samples are needed: below that the shaded grey of the
  receptor dithers visibly, and neither shadow jitter nor fast GI is the
  cause. Cast shadows are a flat ~10 s a frame on top of that and do not
  shrink with the render resolution, so they are off; ambient occlusion
  carries the depth, as it does in the reference clip. ~6 s a frame on
  llvmpipe (WSL2 has no GL driver), so 480 frames is about fifty minutes on
  CPU. The GPU was busy with folds and was left alone.
- The molecule crop in `stitch` is measured off the rendered frames, not
  guessed — re-measure it (the command is in the code comment) whenever the
  design set or the framing changes, or a long binder will clip.
