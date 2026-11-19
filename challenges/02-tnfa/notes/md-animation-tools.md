# MD binding movies — tool survey

Goal: show each promising design next to its target with molecular dynamics,
as an animation of the binding interface. This note lists the GitHub tools
that can do this, and records what we chose and why.

## What we chose: the repo stack

- MD: `tools/md` — OpenMM 8.6.1, AMBER14 force field, GBn2 implicit solvent,
  300 K, 2 fs timestep, 0.15 M salt. Runs on the CPU platform on this box
  (~3.7 ns/day for the 8 093-atom d7x-t3-3 complex).
- Animation: `tools/report/movie.py` in `trajectory` mode — one 3Dmol.js
  scene per trajectory frame, screenshots from headless Chromium, stitched
  with ffmpeg. Binder pink, target blue, interface residues amber — the same
  colours as the app.

Reasons: no new heavy dependency, the movie carries the honesty captions,
the colours match the rest of the project, and the render is deterministic.
On Linux the renderer needs a Chromium binary; set `PDT_CHROME` to it
(here: the Playwright build in `~/.cache/ms-playwright/`).

Driver for the two C2 movies: `~/c2-work/md-anim/build_md.py`
(prep → run → pack) plus `tools.report.movie.render_movie`.

## GitHub options surveyed

| Tool | What it is | Fit for this job |
| --- | --- | --- |
| [BradyAJohnston/MolecularNodes](https://github.com/BradyAJohnston/MolecularNodes) | Blender add-on; imports PDB/mmCIF and MDAnalysis trajectories, styles them with geometry nodes | Best-looking renders, real production tool. Needs Blender (~150 MB) and scene work; headless scripting is possible but heavy. Future upgrade for cinematic shots. |
| [yuxuanzhuang/ggmolvis](https://github.com/yuxuanzhuang/ggmolvis) | Python API over Molecular Nodes | Automates MN renders from scripts. Same Blender requirement. |
| [nglviewer/ngl](https://github.com/nglviewer/ngl) | WebGL molecular viewer; trajectories, MDsrv streaming | Already bundled in the repo (report assets). Interactive, not a renderer by itself. |
| [arose/mdsrv](https://github.com/arose/mdsrv) | Serves MD trajectories through NGL in the browser | Good for sharing an interactive trajectory; needs a server and a running instance. |
| [3Dmol.js](https://github.com/3dmol/3Dmol.js) | WebGL viewer, small and scriptable | The renderer we use; already vendored in `tools/serve/static`. |
| [MDAnalysis/mdanalysis](https://github.com/MDAnalysis/mdanalysis) | Python trajectory analysis library | The engine behind Molecular Nodes import and many pipelines. We use mdtraj (lighter, already a dependency); MDAnalysis is the stronger long-term choice for analysis breadth. |
| [schrodinger/pymol-open-source](https://github.com/schrodinger/pymol-open-source) | Open-source PyMOL; ray-traced frames, `mpng` movies | Classic publication look. macOS wheels were broken in this project's history; Linux needs conda. Not needed while the 3Dmol path works. |
| [usman4373/Dynamics-Visualizer](https://github.com/usman4373/Dynamics-Visualizer) | Streamlit app: PyMOL frame renders from GROMACS trajectories to MP4 | Easy route if the simulation lives in GROMACS; GUI-centric, GROMACS file assumptions. |
| [aai-research-lab/FastMDXplora](https://github.com/aai-research-lab/FastMDXplora) | One command: setup, simulate, analyse, report | Wraps a full MD stack with figures and slides. Heavy dependency tree; our pipeline already exists. |
| [Kopec-Lab/cmd-viewer](https://github.com/Kopec-Lab/cmd-viewer) | Terminal MD viewer with GIF export | Nice for quick trajectory checks over SSH; not for final renders. |
| [daniil-a-baranov/ppi-fingerprints](https://github.com/daniil-a-baranov/ppi-fingerprints) | ProLIF consensus interaction maps from trajectories | Complementary: per-residue interaction occupancy heatmaps. A good follow-up analysis, not an animation. |
| [BMMG-Curtin/Molecular-Dynamics-Visualization-MDV](https://github.com/BMMG-Curtin/Molecular-Dynamics-Visualization-MDV) | Large-scale stereo display renderer (Curtin HIVE) | Specialised hardware display; not applicable here. |

## Honesty rules

The movies inherit the pipeline captions: real all-atom MD, frames superposed
on the target, a physics test of the predicted pose — not a binding assay.
