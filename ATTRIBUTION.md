# Attribution

This repository's own work is **MIT** licensed (`LICENSE`): use it for
anything, commercial included, and keep the copyright notice. The
third-party exceptions below carry their own terms.

Third-party code and assets **bundled in this tree**:

| Bundled file | What it is | License |
|---|---|---|
| `tools/report/assets/ngl.min.js` | NGL Viewer — the 3D viewer inlined into every run `report.html` | MIT · <https://github.com/nglviewer/ngl> |
| `tools/serve/static/3Dmol-min.js` | 3Dmol.js — the viewer behind the `pdt serve` structure pages | BSD-3-Clause · <https://github.com/3dmol/3Dmol.js> |
| `tools/serve/static/fonts/geist-*.woff2` | Geist and Geist Mono — the web app's typefaces | SIL OFL 1.1 · <https://github.com/vercel/geist-font> |
| `challenges/*/viewers/molstar-bundle.js` | Mol* — the interactive structure explorers under `challenges/*/viewers/` (one bundle per challenge) | MIT · <https://github.com/molstar/molstar> |

NGL is inlined into every `report.html`, so a report opens from disk with no
server and no network. The vendored 3Dmol.js keeps `pdt serve` working
offline.

Each bundled asset ships its license text beside it:
`tools/report/assets/ngl.min.js.LICENSE.txt`,
`tools/serve/static/3Dmol-min.js.LICENSE.txt` (the path the minified header
points at), `tools/serve/static/fonts/OFL.txt`, and
`challenges/*/viewers/molstar-bundle.js.LICENSE.txt`. All four were copied
from the upstream projects.

## No vendored source

Code copied or adapted from other people's repositories was removed on
2026-11-08: the two study-repo snapshots, the `binderkit` and `switch` engines
they contained, the pipelines and specs that drove them, and the four adapted
scripts under `tools/analysis/`. The submission validator was rewritten from
the competition's own submission rules and is this workspace's own work.
