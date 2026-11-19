# Challenge 5 videos

One reel, built the way the challenge-3 and challenge-4 reels were built:
Blender and Molecular Nodes draw the structures as RGBA frames, headless
chromium rasterises an HTML metrics panel, and ffmpeg lays one over the other.

```bash
.venv/bin/python challenges/05-pmhc/videos/scripts/mn_reel.py prep
.venv/bin/python challenges/05-pmhc/videos/scripts/mn_reel.py panels
.venv/bin/python challenges/05-pmhc/videos/scripts/mn_reel.py preview   # look check
.venv/bin/python challenges/05-pmhc/videos/scripts/mn_reel.py render    # hours
```

`preview` composites a single frame exactly as the reel will look and costs
about ten seconds. Always run it, and have the frame approved, before
`render`: the full reel is 720 frames of software-rendered EEVEE.
`--quick` runs the whole thing small and choppy in about ten minutes;
`--demo` does three designs at half size.

## What the reel shows

The ten highest-ranked of the nineteen submitted designs, in the submitted
order, three seconds each. The pMHC complex turns through one continuous
revolution and only the binder swaps, because every design's fold is
superposed onto the first design's heavy chain (RMSD 0.27 to 0.38 A).

- grey, see-through: HLA-A*11:01 heavy chain and beta-2 microglobulin
- amber, opaque: the KRAS G12D 10-mer `VVVGADGVGK` in the groove
- one hue per design: the designed binder

The peptide is drawn as its own body so that it stays readable inside the
see-through groove. That is the one thing this challenge's `mn_render.py`
adds to the challenge-4 renderer: `spec["extras"]`.

## Where the numbers come from

The panel reads `records/submitted-19-metrics-2026-11-08.csv` and the
submission CSV. Nothing is computed in the video code. Structures are the
best G12D co-fold of each design by complex ipTM, picked from the boltz-2
runs under `~/c5-work`; `prep` checks that the peptide in the fold is the
G12D decamer and that the binder chain is the submitted sequence, so a
wild-type or peptide-free fold cannot slip in.
