# Campaign-1 work scripts (decision-gating tooling)

Copied from `~/c4-work/bin/` on 2026-10-24 so the repo can reproduce every
decision made in campaign 1 (the review flagged that only the conclusions were
committed; a disk loss would have erased the reasoning). No edits - the files
are byte-identical to the ones that ran, except where noted in git history.

Layout: these ran against the work area `~/c4-work/` (fold yamls, genie3 runs,
sequences, chai inputs, logs). Heavy artifacts stay out of git; the scripts
that produce them do not.

Which script gates which decision:

| script | decides / produces |
|---|---|
| `setup-c4-targets.py` | the 11QC apical-block targets + four problem JSONs (hotspot letters asserted) |
| `screen-gen-geometry.py` | generation-side geometry screen (all 96 pass) |
| `build-c4-fold-yamls.py` | the 96 fold yamls (full-protomer target, absolute MSA paths) |
| `run-c4-folds.sh`, `run-c4-gen.sh`, `mpnn-c4.sh`, `c4-night-1.sh`, `c4-main-chain.sh`, `c4-c2-chain.sh`, `mpnn-progressive.sh` | the overnight chains (generation -> MPNN -> folds) |
| `decide-c1.py` | the original fold-based advance rule -> "no set advances (cannot decide)" |
| `decide-sets-restrained.py` | the amended restrained-read advance rule |
| `screen_folds_c4.py` (in `../`) | unrestrained fold screen: ipSAE + at-site + clash |
| `chai-check-footprint.py` | control-pose checker (native footprint vs dimer patch) |
| `chai-restrained-scores.py` | aggregates the restrained chai reads into `chai-restrained.csv` |
| `rfd4-batch.sh` | hosted RFD4 submissions (3 x 8 per set) |
| `chai-screen-batch.sh` | the restrained screen batch runner (resumable, skips done designs) |
| `memlimit.py` | per-job memory guard used by every GPU run |
| `probe-c4-fold.py`, `watch_resources.py`, `fetch_msas.py`, `setup-c4-b2.py`, `kill_by_cmdline.py` | probes, resource watch, MSA fetch, batch-2 setup, process helper |

Campaign-2/3 additions (2026-10-25):

| script | decides / produces |
|---|---|
| `c2-restrained-scores.py` | C2 arm-aware restrained tables (arm = design-name prefix) |
| `c2-screen-watchdog.sh` | C2 screen unit watchdog: resumes on failure, aggregates both tables at the end |
| `c3-pick-positions.py` | C3: His-engaging positions on C2 designs (vendored `tools/switch/switch_positions.py` logic + relative-SASA exposure filter, strict 3->1 numbering check) |
| `c3-build-designs.py` | C3: the cold variant dirs - arm R single/double His + arm L ladder; copies the parent `msa_pqt` and `restraints.csv` (identical fold treatment; binder falls back to single-sequence exactly as the parent did) |
| `c3-kickoff.sh` | C3: pick + build; run at C2 completion |
| `c3-screen-watchdog.sh` | C3 screen unit watchdog (same pattern as C2) |
| `chai-c3-screen.service` | the C3 fold-queue unit (operator starts it after the kickoff) |
| `c3-histidine-pka.py` | C3 per-site mechanism read: PROPKA pKa of every engineered His, bound vs free |
| `c4-prep-mouse-target.py` | C4: mouse sequence + alignment-derived anchors + MSA→pqt |
| `c4-build-designs.py`, `c4-build-variants.py` | C4: the mouse fold queues (C2 designs + C3 survivors) |
| `c4-restrained-scores.py` | C4: the paired human/mouse table |
| `c4v-chain.sh`, `c4mn-screen-watchdog.sh` | C4: the chained survivor pass + watchdog |
| `make-campaign-diagrams.py` | per-campaign Gantt SVGs (c2/c3/c4) |
| `build-lineage-c2c4.py` | workbench lineage entries for c2/c3/c4 |

Design-dir builder note: the C2 chai design dirs (in.fasta + msa_pqt copy +
restraints.csv) were built inline and were never scripted. `c3-build-designs.py`
closes that gap for C3; the C2 dirs remain as built (recorded by
`logs/c2-restrained.csv` and the parent in.fasta files).

Provenance: `~/c4-work/` held these since 2026-10-23; runner logs live in
`~/c4-work/logs/`. The metric-tag fix and the `--replicates` flag landed in
`nim/build_request.py` in this repo; everything else here was copied verbatim.
