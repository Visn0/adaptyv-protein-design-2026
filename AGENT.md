# AGENT.md — working rules and mistakes log

Living document. Read it before you change this repo. Update it when a rule
changes or when we make a mistake.

## What this repo is

A protein-design workshop for the Anthropic x Adaptyv 2026 competition.
- `challenges/<name>/` — one folder per challenge (inputs, data, specs, runs).
- `tools/` — pipelines, experiment runner, report builder, local web app.
- `challenges/02-tnfa/handoff/` — the PC package for the live C2 campaign: designs,
  sequences, Boltz-2 inputs, records, the full notes, an archive + SHA256SUMS.
- The app: `pdt serve` -> http://127.0.0.1:8737/.

## Rules

1. Write all prose in simplified English (STE). Short sentences. No contractions.
2. One experiment, one run folder. Never mix two experiments in one folder or on one page.
3. Pages stay visual: number cards, charts, a slowly rotating 3D view. No data tables.
4. Viewer color standard: blue = target, pink = designed binder, amber = interface. Interactive structure explorers use the Mol* style (proteinbase replica, `challenges/02-tnfa/viewers/`): binder pink `#e879f9`, target chains `#0099ff` / `#00d2ff` / `#03ffff`, cartoon/surface toggle.
5. Steps tree standard: inputs blue, outputs green, human step amber, fallback violet.
6. Device policy: specs declare `resources:` (cpu | gpu | auto). Resolution order is
   cuda -> mps -> cpu. `PDT_DEVICE` overrides. Never fail only because a GPU is missing:
   give a fallback path, or park the stage as `waiting_inputs` with a clear message.
7. No replay experiments remain. The third-party engines they ran on, and the
   study-repo snapshots they read, were removed on 2026-11-08: every experiment in
   this tree is our own work.
8. No test suite (removed 2026-11-08). Verify by running the experiments
   (`pdt exp run`), the submission validator, and the app itself. Do not add unit
   tests.
9. Keep heavy data out of git. `challenges/*/data` is gitignored; `pdt fetch-data`
   copies the public target files back into `challenges/*/inputs`.
10. Run stages through `pdt exp run` so every run gets status.json, summary.json,
    artifacts and a report.
11. Before you claim a visual works, verify it: pixel checks or the app. Do not trust prose.
12. The app mirrors proteinbase.com: dark navy #0b0c14 with a faint grid, Geist + Geist Mono
    (bundled in `tools/serve/static/fonts/`), cyan #0da2e7 accent, pill chips and buttons,
    panel cards rgba(19,22,38,.6) with #1d2435 borders, numbered section eyebrows (01 / ...). Pages use the full window width: the app body caps
    at 2000px, report pages cap at 1500px.
    Challenge home pages copy their brief shape: hero + 3D target viewer, objectives,
    ranking, requirements (text lives in `tools/serve/brief.py`). Animations follow
    their bundle: the 1 s `ping` dot on open-status chips, 2 s `pulse` skeletons, viewer
    fade-in, hover transitions.
13. Run folders are disposable; the specs are the toolkit. No run output is
    committed.
    The app lists runs as `<experiment> #n` (n counts the runs of that experiment,
    oldest first) plus the run folder id and a UTC datetime, newest first. Two runs of
    one experiment must never look alike on a page.
14. Every page carries a legend, and every experiment carries one verdict. The legend
    gives the colour standard, each number with its direction (higher / lower is
    better), and the pre-registered acceptance lines. The verdict comes from
    `tools/insights.py` (`promising` / `partial` / `insufficient` / `negative` /
    `check` / `waiting` / `failed`) and always names its basis. A verdict must never
    claim more than the run shows: a replay or control run is a `check`, not evidence
    about a binder.
15. No videos in the app. Every structure shows in a py3Dmol viewer that rotates slowly,
    hero viewers included. Rotate on a throttled interval (a 3° turn every 300 ms, skip it
    under `prefers-reduced-motion`), NOT `viewer.spin`: a continuous spin starves software
    renderers and heavy pages. Viewer styles are `cartoon`, `cloud` (one dot per atom) and
    `surface`. A multi-model file (an MD trajectory) opens the md player page instead:
    play, scrub, cartoon / cloud / surface. `pdt movie` stays an offline file exporter:
    nothing in the UI plays videos.
16. One writer per file. A background subagent that rewrites `tools/serve/app.py`
    while the main session works on the same file overwrites live edits. Give
    background work its own new files; re-read a shared file before finishing.
    Background work must also clean up its own smoke runs: only baseline or
    real runs stay in `challenges/*/runs/`.
17. Secrets never enter the repo. The Tamarind key lives at `~/.config/tamarind/api_key`
    (outside every repository, mode 600). Refer to the path only; never copy key values,
    claim URLs or tokens into notes, records or commits.
18. External (SaaS) experiments follow the C2 pattern: `notes/` for the spec, the
    pre-registration and the result; `data/<provider>/<experiment>/` for raw zips,
    extracted outputs and a triage CSV; `notes/<experiment>-jobs.json` for payloads and
    API responses. Learn a tool's billing first: boltzgen bills 1 job per run,
    rfdiffusion3 about 1 job per 8 designs.
19. C2 domain rules (learned the hard way): design against the full trimer, never a
    partial target; hotspot span <= 15 A; the pass bar is pre-registered (ipSAE >= 0.6
    AND pDockQ2 >= 0.23); score interfaces with ipSAE/pDockQ2, never with contact counts.
20. RFdiffusion3 output layout: binder = chain A; the target protomers are renumbered
    (a 1TNF 6-157 input becomes 1-152), so hotspot numbers shift. Triage with
    `challenges/02-tnfa/handoff/scripts/triage_rfd3.py` and pass the offset.
21. The handoff package rebuilds with
    `python challenges/02-tnfa/handoff/scripts/prepare_handoff.py`, then regenerate
    MANIFEST + SHA256SUMS, then tar. MANIFEST and SHA256SUMS must exist BEFORE tarring,
    and no file inside the archive may quote the archive's own hash (circular).

## Mistakes we made (do not repeat)

1. Scores JSON glob: a loose prefix match read the wrong file (`..._H47` matched
   `..._H47_H51`). Fix: anchor file matchers after the exact id
   (was `tools/pipelines/c1.py`; its regression test was removed 2026-10-23 and the file itself with challenge 1 on 2026-11-08).
2. Two NGL viewers on one report page: duplicate element ids made both scripts bind to
   the first box; the second view stayed blank. Fix: unique ids per viewer
   (`_viewer_html(..., index)` in `tools/report/html.py`).
3. Binding movie looked static: the binder moved along the camera axis. Fix: turn the
   complex so the binder-target axis is screen-horizontal first (`_binder_pose_texts`).
4. `surface` and `cartoon+surface` rendered the same picture. Fix: surface = surface only.
   Check that modes differ (md5 or pixel diff of screenshots).
5. PROPKA 3.5.1 breaks on Python >= 3.14 (PEP 649 annotations). Keep the venv on 3.12.
6. `file://` links do not open inside the desktop preview frame. Use the app server.
7. A report without WebGL: show a clear message in the viewport. Never leave a silent
   blank box.
8. A broken report must never fail a run: wrap report rendering in try/except (`worker.py`).
9. Per-file notes matter: a viewer with many structures needs its own note per structure,
   not only one stage-level note.
10. Do not trust a vision model's prose for counts or gaps. Measure pixels
    (see `ACTIVITY.md` style checks in tests and the movie debug session).
11. Hermes tooling: read a file fully before you overwrite it (stale-write guard).
12. `pdt exp run` must rebuild the hub and print the path; run pages link back to `/`.
13. A CSS transition started in `requestAnimationFrame` can never run in a background tab
    (rAF is throttled): the class never applies and the element stays at opacity 0. Force a
    reflow (`void el.offsetWidth`) between the class changes instead.
14. OpenMM 8.6: the XML implicit-solvent model consumes `implicitSolventKappa` (the Debye
    kappa), not `ionicStrength` — a wrong keyword is an error, never a silent default. One
    Integrator binds to one Context; create a second instance for the production run
    (`tools/md/simulate.py`).
15. A ps-to-steps factor error is silent (a 1 ns run became 50 ps). Smoke-run every new
    pipeline with tiny settings and check the step count in the log before the real run
    (`tools/md/`; its test was removed 2026-10-23).
16. mdtraj `atom_slice` renumbers atoms. Remap selection indices after slicing, or
    `superpose` fails with an out-of-bounds index (`tools/md/analyze.py`).
17. A set-membership test written as `num != nb_out` (an int against a set) is always
    true; the filter silently skipped every neighbour residue and reported 0 of 72
    designs at the site. Write `num not in nb_out`. Silent zero counts, no exception:
    assert a known-good count after any triage change.
18. Biopython 1.88 `PairwiseAligner`: a substitution matrix passed as the first
    positional argument is read as `scoring` and raises on its truth test. Construct
    with keywords, then set `aligner.substitution_matrix` separately.
19. Do not match a structure construct against UniProt by exact substring. The 1TNF
    construct differs from P01375 at position 219 (L vs D). Map by alignment and report
    the substitutions.
20. Relative paths from `__file__`: `parents[1]` pointed one level too high and the
    script silently prepared the wrong tree (`handoff/handoff/`). Assert a known child
    path after resolving.
21. RFdiffusion3 renumbers the target chains, so a fresh triage against the 1TNF 6-157
    construct needs offset -5. A wrong offset gives a confident, wrong 0/72.
22. `files.ipd.uw.edu` is unreachable from **both** networks we have (the Mac and the
    PC): DNS resolves, TCP 443 times out on IPv4 and IPv6. This is not a Mac or a
    driver problem, so retry loops are wasted work. The RFD3 checkpoint is mirrored
    byte-identical on Hugging Face
    (`datasets/sgetttt/rfdiffusion3-assets` → `models/weight/rfd3_latest.ckpt`,
    2 690 316 669 bytes, sha256 `9b3f8592…d67c1`); `make rfd3` fetches and verifies it.
23. Two machines, one repo: the Mac resolves to MPS/CPU, the PC (Windows/WSL2) to CUDA.
    The PC's card is an **RTX 5070 with 12 GB**, not the 5070 Ti 16 GB the notes assumed
    (`nvidia-smi` inside WSL lives at `/usr/lib/wsl/lib/nvidia-smi`, not on PATH).
    `make setup-gpu` builds the PC stack; `make rfd3` adds RFdiffusion3.
24. `uv pip install --torch-backend=auto` does not cover a transitive torch dependency:
    `rc-foundry[rfd3]` pulled a **CPU** torch. After any GPU tool install, assert
    `torch.cuda.is_available()` in that venv before trusting it. uv also keeps the CPU
    build unless you pass `--reinstall-package torch`.
25. `tests/test_serve.py` picked the **newest** run of a name, so the first local
    `pdt exp run` on the PC (a `waiting_inputs` run with no structures) broke four
    viewer tests. Fix: `_find_run(..., need_structures=True)` keeps only runs whose
    summary carries a viewer with files. A run-state change must not fail the suite.
    (The suite was removed on 2026-11-08.)
26. A command's **exit code** is the verification, not the environment it leaves behind.
    The first `make rfd3` on the PC died at its first line (the Makefile fallback resolved
    `uv` to the Mac binary in a PATH-less background shell, exit 127) while the venvs
    looked right from earlier manual installs, so it was reported as verified. Two
    Makefile rules now hold: resolve tools from PATH **then a known path**, and fail
    loudly (`uv-check`, exit 2) when a tool is missing. `uv venv` also needs
    `--allow-existing` to re-run.
27. IPSAE finds its companion files by **renaming the PAE path**: `pae`→`plddt` for the
    pLDDT npz and `pae`→`confidence`, `.npz`→`.json` for the metrics JSON. Copy Boltz
    outputs into a run under their original names (`tools/pipelines/fold.py`); renamed
    copies make IPSAE read no pLDDT and report pDockQ/pDockQ2 at their floor
    (0.018 / 0.005) while ipSAE stays correct — a silent wrong number. Symptom to
    watch for: ipSAE matches the reference exactly, pDockQ2 does not.

28. **A membrane-less co-fold cannot see lipid intrusion.** Boltz/AF models contain no
    membrane, so nothing penalises a binder backbone lying where lipid would be — a public
    commenter caught this in the C3 reel: 5 of the final 20 put atoms in the bilayer zone
    (2 of them were on screen). Check any membrane-receptor design against a membrane frame
    derived from the model's OWN TM helices — `tools/analysis/membrane_space_check.py`;
    flag = atoms outside the helix-bundle envelope, inside the middle 30 A of the helix
    extent, >4 A from every receptor atom; calibrate on the natural ligand first (GLP-1 in
    6X18 flags zero). Screen-grade: state the few-A frame uncertainty. Do not borrow a
    membrane plane by superposing onto an experimental structure (the ECD drags the fit:
    3.7 A TM RMSD measured). C4 does NOT need it as a gate — the supplied target is the
    soluble ectodomain homodimer (121-760) and the designed epitope sits ~70 A from that
    construct's membrane-side terminus. C5: decide by target class the day the brief lands
    (`challenges/05-pmhc/README.md`). **Decided 2026-10-30: C5 is a soluble peptide–MHC
    complex (HLA-A*11:01 + β2-microglobulin + peptide) — neither check applies; the two
    counter-targets (wild-type peptide, peptide-free MHC) are the screening gate instead.**

## Housekeeping

- `make install` builds the venv (Python 3.12).
- No absolute machine paths in code or configs. Python scripts resolve the repo
  root from `__file__` (the `_repo_root()` helper) or use `pathlib.Path.home()`;
  shell scripts use `${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}`
  and `$HOME`; campaign work dirs live under `$HOME/cN-work` (some scripts take a
  `*_WORK` override). Keep it that way when you add a script.
- On the PC (WSL2 + CUDA): `make setup-gpu` builds the project venv, the tools venv,
  the Boltz-2 venv and the source checkouts; `make rfd3` adds RFdiffusion3 and its
  checkpoint. `make` finds `uv` on PATH first, then the bundled Mac build.
- Fast path on a fresh machine: `uv sync --all-extras --inexact` (uses `uv.lock`;
  `--all-extras` keeps the OpenMM stack, `--inexact` leaves `make torch` installs in
  place). Plain-pip users: `requirements.txt`.
- Handoff tools venv on the PC: `uv pip install -r challenges/02-tnfa/handoff/requirements-tools.txt`.
- Update `README.md` when the command surface changes. Update this file after mistakes.
