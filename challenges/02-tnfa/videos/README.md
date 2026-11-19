# C2 campaign — video series

> **Outputs cleared 2026-10-23.** Only video 14 is kept, because it is the
> one episode that shows submitted designs (`sr2-ds-mce-14-v6-r2c`,
> `ds-mce-14-v6`). Episodes 01-13 were deleted and are to be re-rendered;
> the scene modules, narration and build driver below are all intact, and
> earlier renders remain in git history.

Fourteen narrated explainers about Challenge 2 (TNF-α), rendered with Manim CE
and voiced with edge-tts. One video covers the challenge itself; eleven cover
one experiment each; the thirteenth covers the Genie 3 round that produced the
two promising designs — the steps, the tools, and the reasons behind them; the
fourteenth covers the final campaign — the champion and the submission set,
with two MD binding clips.

Every video is under five minutes and carries soft subtitles (English) in the
MP4 plus a sidecar `.srt`.

## The series

| # | file | subject | length |
|---|------|---------|--------|
| 01 | `01-challenge-2-the-inverted-switch.mp4` | the challenge: ask, physics, strategy, outcome | 4:01 |
| 02 | `02-c2-anchors.mp4` | `c2-anchors` — the switch-anchor scan | 1:56 |
| 03 | `03-c2-switch-motif.mp4` | `c2-switch-motif` — histidine geometry | 2:08 |
| 04 | `04-c2-scorer-controls.mp4` | `c2-scorer-controls` — instrument validation | 1:41 |
| 05 | `05-c2-coverage-scan.mp4` | `c2-coverage-scan` — reachability filter | 1:38 |
| 06 | `06-c2-score-designs.mp4` | `c2-score-designs` — ranking stage | 1:20 |
| 07 | `07-c2-baseline-results.mp4` | `c2-baseline-results` — upstream reference | 1:48 |
| 08 | `08-c2-fold-w1-gpu.mp4` | `c2-fold-w1-gpu` — first local fold | 2:01 |
| 09 | `09-x1-boltzgen-benchmark.mp4` | X1 — BoltzGen benchmark (negative) | 2:19 |
| 10 | `10-x2-rfdiffusion3-probe.mp4` | X2 — RFdiffusion3 probe + co-fold | 2:10 |
| 11 | `11-w2-shortlist-folds.mp4` | W2 — shortlist folds, human/mouse | 1:49 |
| 12 | `12-x3-site-check-campaign-close.mp4` | X3 — the site check, campaign close | 2:53 |
| 13 | `13-genie3-two-promising-designs.mp4` | Genie 3 round 2 — the two promising designs (d7x-t3-3, b2x-d12-2) | 4:06 |
| 14 | `14-final-campaign-the-champion.mp4` | the final campaign — the champion (Genie 3 → E33H), with two MD binding clips | 4:50 |

## Rebuild

`build.py` must run with the manim venv python (it imports the scene modules,
which import manim):

```bash
V=~/.venvs/manim-cf/bin/python
$V build.py render all draft     # fast layout pass (480p15)
$V build.py render all final     # production render (1920x1080 @ 30 fps)
$V build.py audio all            # edge-tts narration per scene (cached)
$V build.py segments 14          # v14: prebuilt MD clips into the render tree
$V build.py check all            # timing + narration-margin report
$V build.py stitch all           # concat + mux + subtitles -> out/
```

Single video / single scene: `build.py render 3 draft S2_Cations`.
`stitch --draft` previews from the draft renders.

Video 14 mixes two prebuilt MD binding clips (from `../md-movies/`) into its
scene sequence: `build.py segments 14` normalizes each clip to 1920x1080/30
and pads it on its last frame to fit its narration, before `check`/`stitch`.

Narration length must fit each scene. `tune_waits.py` aligns the two:

```bash
$V tune_waits.py all pace --apply        # spread time over the reveals (static)
$V build.py render all draft             # measure the new durations
$V tune_waits.py all --draft --apply tail  # exact final correction (once!)
```

`pace` reads exact wait/play execution logs from `manim --dry_run`
(`C2_WAIT_LOG` / `C2_PLAY_LOG` in `common.py`), so it needs no render.
Run `tail` exactly once per render state; a second run double-applies.

QA: `python3 qa_sheets.py` takes a screenshot every 10 s from every final
video and writes one labelled contact sheet per video into `qa/`.

Requirements: `~/.venvs/manim-cf` (manim CE 0.22 with its own pango/cairo/
ffmpeg stack), `~/.venvs/tts` (edge-tts), `ffmpeg` on PATH. LaTeX is not
needed — all text uses the bundled mono font (JetBrains Mono).

## Layout

| Path | Contents |
|------|----------|
| `common.py` | palette, layout helpers, `C2` base scene |
| `vNN_*.py` | one module per video: scene classes + `NARRATION` dict |
| `build.py` | render / TTS / check / stitch driver |
| `tts_synth.py` | one edge-tts clip + boundary timings (for the SRT) |
| `tune_waits.py` | pace/tail tuning of scene waits against narration length |
| `qa_sheets.py` | QA: one frame every 10 s, one labelled contact sheet per video |
| `out/` | final MP4 + SRT files (committed) |
| `qa/` | QA contact sheets (committed); `qa/frames/` holds the raw frames (gitignored) |
| `media/`, `media_draft/`, `audio/` | render and TTS intermediates (gitignored) |

## Conventions

- Palette follows the local app: navy `#0b0c14`, cyan accent `#0da2e7`.
- Repository colour standard: blue = target, pink = binder, amber = interface.
- Voice: `en-US-AndrewNeural` (same as the C1 explainer), 350 ms lead-in per
  scene; each scene's narration is padded to the scene length, so the build is
  deterministic.
- A scene's narration must fit inside its rendered length. `build.py check`
  flags any overflow — fix by editing the scene's waits and re-rendering that
  scene only.

The numbers shown in every video come from the run records under
`challenges/02-tnfa/notes/` and `docs/competition-notes/`.
