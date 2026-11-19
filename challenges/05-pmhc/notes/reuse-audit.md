# C5 reuse audit - local assets for the KRAS G12D pMHC binder challenge

Scope: inventory of OUR OWN past work (repos, notes, tools, skills) that can be
reused for Challenge 5 (design a de novo binder against KRAS G12D peptide
VVVGADGVGK on HLA-A*11:01 + b2-microglobulin; must NOT bind the WT peptide
complex or the peptide-free MHC; de novo; 10-250 aa; up to 20 designs; deadline
2026-11-08). Read-only inspection; nothing in the inspected repos was modified.
Today: 2026-10-30.

Machine note: two paths named in the task are NOT on this host. The baseline
repo `~/Projects/Protein-design-competition-Anthropic-X-adaptyv` and the two
EGFR repos are absent here (they live on the source machine); the baseline
modules are vendored into `tools/binderkit/` and `tools/switch/`, and a
snapshot lives in `challenges/01-egfr/reference/baseline/` (see
ATTRIBUTION.md). `~/Projects/protein-design-competition-report.md` and
`~/Projects/protein-design-runbook.md` are also absent here; the report text
lives in the repo as `docs/competition-notes/00-competition-report.md`.

Legend for the tables: C5 applicability = high / medium / low; paths are
relative to the repository root unless absolute.

---

## (a) The C4 selection pipeline (rubric, prescreen, validator, builder)

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| C4 campaign-6 selector | `challenges/04-tfr1/campaigns/c6-selection/scripts/select-top20.py` | One script owns the ranking. Rubric `total = 2.0*S + 1.5*X + 1.5*B + 1.0*E` (max 30, normalised to 100); binding reads are engagement-gated means (worst-anchor <= 8 A AND binder residues at site > 0); floors live in code: `PLDDT_FLOOR = 63.0`, `PDOCKQ2_FLOOR = 0.18`, `MIN_ENTROPY = 2.5`, `MAX_TOP_SHARE = 0.45`, `MAX_HOMOPOLYMER = 6`, `TARGET_PICKS = 20`; soft family cap keeps over-cap designs as a top-up pool; within-batch duplicate rule (>= 0.95 identity over >= 0.80 coverage counts once) | High: this is the template for the C5 final-20 selection | Reweight components for C5 objectives: S -> specificity (WT-complex delta + peptide-P6 contacts), X -> peptide dependence (peptide-free arm), B -> affinity read, E -> expression; replace the `FAMILIES` and `LIABILITY_REPAIRS` maps; feed C5 restrained-screen CSVs with the same column names | Hardcoded `~/c4-work` paths; reads specific chai column names (`worst_hotspot_min_dist`, `binder_res_at_site`); the floors exist because C3's floors lived only in prose (lessons-c2-c3.md C1) |
| Pre-flight assertions | same file + `challenges/04-tfr1/campaigns/c6-selection/README.md` | Before ranking: every design has a row in every screen; every design has both required fold arms; every claim has its evidence row; sequence hash matches the folded sequence; count of ungated designs must print 0 | High: reuse as the C5 selection checklist verbatim in spirit | None (pattern). Add C5 rows: every design folded against all three states; every specificity claim has a delta row | C3's activation gate was never run on 482 designs and capped them at 56.5 (lessons-c2-c3.md C2); a silent zero count throws no exception |
| Submission validator | `tools/analysis/validate_submission.py` | Validates the upload CSV: required columns `name,sequence`; duplicate names/sequences; `molecule_class` enum (`single_chain`, `protein`, `nanobody`, `scfv`, `fab_kappa`, `fab_lambda`); AA alphabet; chain length 10-250; prompt-injection sniff words (`SNIFF_WORDS`); max rows | Direct reuse: C5 limits are identical (20 rows, 10-250 aa, same classes) | None. Use `--max-rows 40` only if Track 1 | The sniff-word check exists because instruction-like text can disqualify; default `max_rows=20` |
| Submission builder pattern | `challenges/04-tfr1/submission/build-submission.py` | One script writes the upload CSV from the selector's committed record; asserts exactly 20 unique picks; reads each sequence from the design's own fold input (`in.fasta`); writes only `name,sequence,molecule_class` | High: copy for C5 | Point `RECORD_DIR` glob at C5 records; sequence source = C5 fold dirs; keep the assert-20 + unique-names pattern | Hardcoded c4-work path; never retype sequences (byte-verify against fold inputs) |
| Novelty prescreen | `~/tools/binder-prescreen` (v0.5.0) | Sequence-level prior-art + known-binder filter: whole-sequence and binding-region arms vs PDB / SwissProt / PLAbDab / Thera-SAbDab / THPdb / published Proteinbase designs / USPTO patents, plus a curated per-target set. Verdicts: `known_target_binder`, `target_region_match`, `verbatim_target_fragment`, `existing_design`, `known_sequence`, `batch_duplicate`, `pass` | High: the `kras-pmhc` target slug already exists - 144 references (51 KRAS G12D/G12V TCRs on A*11:01: 61 V domains, 83 CDR3s, 22 confirmed binders), TCR-only, and the repo states no TCR-mimic or designed-binder reference exists for this pMHC | Set `PRESCREEN_DB_ROOT=~/prescreen-dbs`; put `~/tools/mmseqs/bin` on PATH; run `--skip-prior-art` for a 30 s check and the full arm on the final set | The reference DBs ARE built here: `~/prescreen-dbs` = 113 GB, all eight arms (pdb, swissprot, plabdab, plabdab_nano, therasabdab, thpdb, proteinbase_public, uspto), indexed. mmseqs is NOT on PATH by default. TCR pair rule: a CDR3 match decides only if both CDR3s match one receptor; a lone CDR3 vs a patent claim is `target_region_match_not_decisive`. Sequences under 25 aa return `no_reference_signal`, not pass. `batch_duplicate` at 0.95 identity / 0.80 coverage = one design per backbone family |

## (b) Chai-1 restrained / pocket-restraint screening

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Constrained-screening reference | `~/.hermes/skills/research/protein-binder-design/references/chai-1-constrained-screening.md` | Full recipe: install fixes (torch 2.14.1+cu130 for sm_120; MSAs as `<sha256(QUERY.upper())>.aligned.pqt`; pyarrow==17; `--no-use-esm-embeddings`), pocket-restraint CSV format (`chainA` = binder with empty res; `chainB`+`res_idxB` = target residue as `<LETTER><FASTA position>`; `connection_type=pocket`, max 8.0 A), cost (~8.5-13 min/design, ~9.5 GiB RSS, trunk ~11.7 GB GPU peak), and the protocol that survived statistical review (native control first; pre-registration; engagement gate; equal-bars falsification; ortholog re-indexing) | High for the C5 counter-target folds: C5's known trap is that AF2 ipTM cannot separate G12D from WT (0.84 on both states, measured in research-synthesis.md), so a directed read is needed to test any instrument | Restraints target the peptide ridge (P4-P8 outward residues) plus groove-rim residues instead of TfR1 anchors; build per-state restraint rows (WT file has Gly at P6; positions identical, 10-mer in both); peptide-free has no peptide chain, so derive a groove-rim fallback (the reference documents the fallback-from-own-contacts rule) | A restrained score is a DIRECTED consistency read, never evidence of binding; gate every read by engagement (worst-anchor <= 8 A AND binder residues > 0) or a 0.696 off-site pose passes; an empty restraints CSV (header only) fails at load (rc=1, ~8 s); never SIGTERM chai in its first ~60 s (host crash); chai writes no PAE, so ipSAE needs Boltz-2 |
| Spec-driven restrained screen | `tools/pipelines/screen.py` + example spec `challenges/04-tfr1/experiments/c1-epitope-screen.yaml` | Pipeline stage `score`: scans `<design>/out/pred.model_idx_N.cif` + `scores.model_idx_N.npz`; computes per-sample hotspot engagement (`hotspot_engagement` in `tools/analysis/contacts.py`) and ipTM; writes `restrained-samples.csv` and `restrained-designs.csv` with `mean_iptm` over ENGAGED samples only | High: runnable as-is for a C5 chai batch once a C5 spec exists (new hotspots table + designs dir) | New spec under `challenges/05-pmhc/experiments/` (shape: `c1-epitope-screen.yaml`: `pipeline: screen`, `stages: [score]`, params designs/hotspots/models/cutoff/gate_max_dist/gate_min_residues/skip). Hotspot positions are label_seq_id (FASTA numbering) | ipTM alone promotes off-site poses (measured 0.696 at ~55 A); hotspot matching is by design-name prefix; raises `waiting_inputs` when the dir is missing (not an error) |
| C4 batch runners and watchdogs | `challenges/04-tfr1/scripts/work/*-restrained-scores.py`; `~/c4-work/bin/{b3,b4,b4r}-{chain,restrained-scores,screen-watchdog}.sh` | The hand scripts the `screen` pipeline was refactored from, plus the chain + watchdog + PAUSE-sentinel batch shape (systemd oneshot units, retry snapshot) | Medium: reuse the orchestration shape for C5 fold queues | Copy the chain/watchdog pattern for C5; prefer the pipeline version for scoring | Watchdog must count its end marker only after its own start (stale marker fired a fresh watch in seconds); retry pass must snapshot the failed list (self-extending loop burned a night); kill orphaned chai children by PID (they hold ~11 GB and starve the next batch) |

## (c) Multi-model / multi-state consistency filter

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Multi-model consistency practice | `challenges/04-tfr1/records/openfold3-attempt-2026-10-30.md` (two independent folders: Chai-1 + Boltz-2, 5 samples each, plus unrestrained re-folds, seed-7 re-folds, mouse cross-folds); `challenges/04-tfr1/notes/best-designs-by-campaign-2026-10-30.md` (the most cross-validated design: Boltz 0.808, ipSAE 0.50, chai 0.776); `challenges/04-tfr1/campaigns/c6-selection/scripts/select-top20.py` (tie-break on five-sample at-site agreement); `docs/competition-notes/07-tools-to-measure-binding.md` section 7 (ensemble and consistency protocols) | A design's read counts when independent instruments agree; the per-sample spread is reported, never the best sample; a fold is a distribution | High for C5: the specificity claim must reproduce across predictors and states. C5's decisive question (does the binder read the PEPTIDE, not the HLA framework) is exactly what multi-model + multi-state agreement tests | Build a tri-state x 2-model fold matrix per candidate (G12D / WT / peptide-free, Chai-1 + Boltz-2, 5 samples); aggregate: peptide-first engagement (P4-P8), binder-peptide vs binder-HLA vs binder-b2m chain-pair scores, delta G12D minus WT; pass only on majority agreement | Never compare numbers folded under different protocols (fold-limited vs restrained read); one passing sample in five is a qualified pass, not a result; ipSAE cutoffs differ per family (10 A for Boltz); OpenFold3 is installed but unusable on this host for large inputs (WSL crash) - a third folder is a next-machine item |

## (d) Contact analysis and hotspot selection

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Contact / engagement library | `tools/analysis/contacts.py` | `interface_contacts` (KD-tree contact residue lists at 4.5 A), `complex_viewer_hints` (blue target / pink binder / amber interface), `cif_atoms` (label_seq_id-indexed atom tuples), `split_binder_target`, `hotspot_engagement` (per-hotspot min distances + binder residue count - the exact gate the C4 screen uses) | High: the C5 tri-state screen primitives; the peptide is one more chain | Define C5 hotspot lists per state (peptide P4-P8 + groove rim); chain IDs from the provided files | Indexed by label_seq_id (FASTA), not author numbering; the C5 heavy chain is renumbered 1-276; assert a known-good count after any triage change (silent-zero lesson, lessons-c2-c3.md D4) |
| Reference-contact hotspot finders | `tools/analysis/epitope_contacts.py`; `tools/analysis/interface_residues.py` | Rank target residues by contacts from a reference complex (the cetuximab finder); interface + Asp/Glu vicinity lister | Medium: derive C5 hotspot sets from the JDI TCR contacts in 7OW6 (or read the already-measured list in target-physics.md) | Re-point at the 7OW6 chains; the JDI contact map is already measured: 275 contacts < 4.5 A, 20 percent on peptide, P7 32 / P8 9 / P6 5 / P5 4 / P4 2 | Crystal-symmetry and numbering pitfalls; use one copy of the complex |
| Hotspot-selection procedure | `~/.hermes/skills/research/protein-binder-design/references/hotspot-selection.md` | Procedure: contact ranking -> conservation/exposure filter -> span ladder; crystal-symmetry and residue-numbering pitfalls | Medium-high for the C5 hotspot set | Drop the conservation filter (C5 has no ortholog objective); keep contact ranking and the <= 15 A span check | Never copy hotspot numbers from the public 9-mer repos (9UV8 has Asp at P5; our target is the 10-mer with Asp at P6 - the register trap is documented in deep-campaigns.md); RFdiffusion renumbers and recenters outputs (superpose before measuring) |

## (e) The experiments runner and app wiring (what adding C5 experiments takes)

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Spec loader | `tools/experiments/spec.py` | YAML spec contract: `name`, `challenge`, `pipeline` required; `description`, `resources`, `reference`, `requires_network`, `stages`, `params` optional; discovery glob `challenges/*/experiments/*.yaml` | High: the way C5 experiments get defined | Write `challenges/05-pmhc/experiments/*.yaml` (no `experiments/` dir exists yet); shape example: `challenges/04-tfr1/experiments/c1-epitope-screen.yaml` | Params that name paths are challenge-relative (resolve with `ctx.resolve`); a bare path reads from CWD and silently finds nothing |
| Pipeline registry + runner | `tools/pipelines/__init__.py`; `tools/experiments/runner.py`; `tools/experiments/worker.py`; `tools/experiments/devices.py` | `PIPELINES` dict maps the spec key to `run(ctx)`; the worker writes one run dir (`status.json`, `summary.json`, `artifacts/`, `report.html`); `WaitingInputsError` -> `waiting_inputs`; GPU specs serialise; device order cuda -> mps -> cpu | High: adding a C5 pipeline = one module + one registry line + specs | For the tri-state specificity screen: new `tools/pipelines/c5.py` (or extend `screen`) that folds/reads all three states and computes deltas + per-chain-pair rows; register as `c5`. Worked example of a new pipeline: `tools/pipelines/fold.py`; obligations list: `~/.hermes/skills/research/protein-binder-design/references/adding-a-pipeline.md` | Worker swallows report-render errors (call `render_run_report` by hand to see the traceback); chart `series` must be a column name, not a list; obligations: a known-good-number test, an EXPERIMENTS.md section, run once and read `run.log`, restart `pdt serve` |
| Fold import + IPSAE stage | `tools/pipelines/fold.py` | Imports a Boltz-2 co-fold into a first-class run: copies model/PAE/pLDDT/confidence per sample under ORIGINAL names, runs IPSAE per sample (10 A PAE cutoff), writes `fold_metrics.csv`, embeds the best model in the viewer; acceptance line from `tools/insights.py` `BARS` | High: the pattern for turning C5 Boltz-2 tri-state folds into runs | Run per state (three spec instances) or extend to loop states; keep original file names | IPSAE finds companions by renaming the PAE path (`pae` -> `plddt`, `pae` -> `confidence`, `.npz` -> `.json`); renamed copies silently floor pDockQ2 while ipSAE stays right (AGENT.md mistake 27); suffix-less copies parse as PDB and fail |
| App wiring | `tools/serve/app.py` (`PIPELINE_INFO`, `STAGE_INFO`, `TOOLS`); `tools/serve/brief.py` (`05-pmhc` entry, lines ~267+); `tools/insights.py` (verdicts + `METRICS`) | The app pages: challenge brief with target viewers, strategy chapters, legends, verdict chips; the C5 challenge page IS already wired (targets `kras-g12d` and `wild-type`, viewer on `inputs/7OW6-G12D-noTCR.pdb`) | Medium: needed once C5 runs exist | Add `PIPELINE_INFO`/`STAGE_INFO` entries for any new C5 pipeline; add a verdict rule in `insights.assess_run` and a `METRICS` entry per new number | Restart `pdt serve` after app edits (kill by PID from `ss -ltnp`); one writer per file (AGENT.md rule 16) |

## (f) Campaign README and pre-registered discard-rule template

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Campaign README template | `challenges/04-tfr1/campaigns/c1-epitope-triage/README.md` ... `c6-selection/README.md`; `challenges/04-tfr1/notes/strategies.md` sections 6-7 (campaign map with per-campaign discard rules + pre-registered bars) | Each campaign README states: why the campaign exists, its configuration (arms, epitope sets, lengths, sequence protocol), and the advance rule + discard rule REGISTERED BEFORE its deciding run | High: stand up the C5 campaigns in this shape - the first campaign should be the instrument test (run the JDI control through our stack) | Write `challenges/05-pmhc/campaigns/<name>/README.md` before any generation; register C5 bars (peptide-first footprint; delta G12D-WT; ipSAE bands; instrument must separate the JDI control) | The C3 failure (floors in prose, not code) is the reason floors live in the selector; a new design direction is its own campaign (standing instruction, skill SKILL.md) |
| Carried rules from C2/C3 | `challenges/04-tfr1/notes/lessons-c2-c3.md` (A1-A5, B1-B4, C1-C7, D1-D13); `challenges/02-tnfa/notes/filter-calibration.md` | The hard rules: score AND site together (A1); generator dominates (A2); ipSAE bar 0.8, discard line 0.6 (A3); a high score is not binding (A4); screens only discard, generation must supply features (A5); full-backbone MPNN only (B1); composition bands of real winners (charged ~41 percent, GRAVY -0.56, largest residue ~22 percent) (B3); verify gates ran on every design (C2); one writer per derived number (C3); operational traps D1-D13 | High: most already carry into the C5 synthesis; keep them as the C5 working rules | Drop the pH-specific rules (C5, C6, C7); keep A1, A3, A4, B1, B3, C1-C4, D1-D13 | The numbers are TNF-calibrated; do not quote them as C5 predictions |

## (g) Mol* viewer / movies / report tooling for C5 structures

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Viewpoint renderer | `tools/report/molstar_views.py` | Renders 3 viewpoints x 5 modes (cartoon, surface, plddt, hydrophobicity, interface) with headless Chrome; writes `<name>_<mode>_viewN.png` + `manifest.json` (+ explorer HTML with `--explorer`); interface mode = amber 4.5 A contacts | High: render the C5 finalists tri-state (interface mode shows the peptide-ridge contacts); doubles as a selection tie-breaker | None; pass `--complex` or `--binder`/`--target` | Surface styles need the load gate; verify PNG counts and spot-check with vision |
| Interactive Mol* viewers | `tools/serve/molstar_viewer.py`; `challenges/03-glp1r/viewers/scripts/make_molstar_multiview.py`; `challenges/04-tfr1/viewers/multiview/*.html` | Per-campaign interactive explorers (DESIGNS panel, per-design score chips `ipsae`/`pdockq2`/`iptm`); mounted via each lineage experiment's viewer list | High: the natural C5 deliverable surface - a tri-state multiview (G12D / WT / peptide-free tabs per candidate) | Build `challenges/05-pmhc/viewers/` from the C4 builder; resolve fold dirs by argmax sample | Mol* bundle API traps (skill reference workbench-site.md); viewer score chips need the right metric keys |
| Movie exporter | `tools/report/movie.py`; `tools/report/sim.py` | `pdt movie`: modes trajectory / sim / dock / spin; `sim` is driven by pH-linkage wells; every render writes `movie.meta.json` with honesty notes | Low-medium: only `dock`, `spin` and `trajectory` are meaningful for C5; `sim` is pH-specific and NOT reusable | Use `trajectory` only if a C5 MD run exists; otherwise skip movies for C5 | Do not present the pH `sim` mode as C5 evidence |
| Report generator | `tools/report/html.py`; `tools/report/charts.py` | Per-run self-contained `report.html`: tables, SVG charts, inline viewer; charts support hbar/scatter/line with legends | High: automatic for every C5 run | None; follow the chart-spec shapes | Report failures are swallowed by the worker; a missing chart renders as nothing, silently |

## (h) Liability / sequence-QC module

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Liability module | `tools/binderkit/liability.py` | `assess()`: length range, free Cys count, His count, hydrophobic runs, motifs (`N[^P][ST]` glycosylation, NG, DG, DP), structure-based exposed hydrophobic patch (Shrake-Rupley clustering), identity-to-reference; plus gravy, net charge (pH-aware), hydrophobic fraction. Docstring: everything here is a filter, not a ranking signal; thresholds are defaults for recalibration | High: C5 QC layer; the C4 liability round (`challenges/04-tfr1/records/liability-round-2026-10-30.csv`) shows the repair pattern: N->Q repairs replace parents only at no measured binding cost (within 0.02), 3 repairs held because they hurt binding | Set `length_range=(10, 250)` and `min_his=0` (C5 has no histidine requirement - the defaults 40-100 aa / min 2 His are C1 pH-switch assumptions); recalibrate the patch threshold; run identity vs the prescreen reference sets | Defaults are C1 assumptions; do not quote the defaults as C5 gates |
| Diversity picker | `tools/binderkit/select.py` | `pareto_mask` / `pareto_rank` (non-dominated sorting, no weighted sums) + `diverse_pick` (greedy max-min sequence difference) | Medium: diversity picking for the final 20 (one design per backbone family) | Superseded by the C4-style rubric selector for ranking; use `diverse_pick` for family spread if the rubric alone under-diversifies | C3 lesson C4: real winners converge into families; keep over-cap members as a top-up pool, never drop them |

## (i) docs/competition-notes 06 and 07 - the reusable checklists

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Judging stations | `docs/competition-notes/06-how-we-judge-designs.md` | Four stations: (1) dock check - co-fold, ipSAE/pDockQ2/contacts, 5-seed site agreement; (2) species and site check; (3) switch audit (pH); (4) chemistry sanity + controls (positive known complex, negative shuffled); plus the reality check (1 in 10 to 1 in 3 for good targets) | High as the C5 evidence-structure template | Re-cast: station 2 -> peptide-first site check; station 3 -> specificity audit (delta G12D-WT + electrostatic placement); controls: the JDI TCR as positive, shuffled sequences as negative, WT and peptide-free as counter-target folds | Station 3's pH machinery is not C5-relevant |
| Tools landscape + checklist | `docs/competition-notes/07-tools-to-measure-binding.md` | Tool stack by layer: co-fold confidence (pLDDT/PAE/ipTM) -> interface scores (ipSAE, pDockQ2, actifpTM; bands >=0.8 very high; common acceptance ipSAE >= 0.6 AND pDockQ2 >= 0.23; ipSAE_min best single predictor of lab binding) -> DockQ vs reference -> affinity (PRODIGY; treat PPI affinity as ranking only) -> chemistry (PLIP, freesasa, P2Rank) -> ensemble/consistency (5 seeds, chain-pair values) -> pH layer -> wet lab BLI; section 11 is a 10-item practical checklist | High: the C5 scoring-plan skeleton | Add the pMHC-specific thresholds from `challenges/05-pmhc/notes/research-tooling.md`: ipSAE_min > 0.61 standard, > 0.70 stringent; add the tri-state protocol; keep the controls rule | Confidence is not probability; compare scores only at identical settings and cutoffs |

## (j) The C3 activation-geometry gate PATTERN -> the C5 analog

| Asset | Path | What it does | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Reference-pattern gate (the pattern) | Scorer: `~/c3-work/c8-agonism/scorers/activation_geometry.py`; note: `challenges/03-glp1r/notes/agonism-geometry-2026-10-20.md`; rubric integration: `challenges/03-glp1r/campaigns/c8-deep-junction/scripts/select-top20.py` (component A: 6/6 = 5, 5/6 = 3.5, ...; weights `2.0*A + 1.5*B + 1.0*E + 0.5*R`); pattern description: `~/.hermes/skills/research/protein-binder-design/references/receptor-targets.md` (score each design against the REAL agonist's own contact set - GLP-1 in 6X18 touches all 19 groove+junction+TM+ECL3 residues; likeness and affinity rank differently) | The pattern: take the REAL reference binder's own contact pattern from a crystal structure, pre-register the cutoffs, score every design against it, read pose agreement across samples, and weight it as the hardest objective's evidence. Calibration discipline: reproduce the published numbers on experimental structures first (including quirks), then rescore our own designs | High as a PATTERN, not as code. The C5 analog: score designs against the JDI TCR's contact pattern from 7OW6 - a peptide-first footprint on the P4-P8 ridge (the measured JDI contact map: 275 contacts < 4.5 A, P7 32 / P8 9 / P6 5 / P5 4 / P4 2), plus P6/P7 adjacency; require weak binder-HLA and binder-b2m reads (a framework-reading binder fails all three objectives) | Re-implement for C5: contact sets from 7OW6 (already measured in `challenges/05-pmhc/notes/target-physics.md`); pre-register cutoffs before the deciding batch; read pose agreement across 5 samples x 2 models; run the JDI control through the identical pipeline first (C5 synthesis step 1) | The activation scorer itself is target-specific (NOT reusable); the scorer scores the pose it is given - pose agreement across samples is the mitigation; depth-like metrics can be generous for large binders (C3 caveat 1) |

## (k) The six 05-pmhc scout reports + target physics (facts already established - do not re-research)

| Asset | Path | What it establishes | C5 applicability | Adaptation needed | Pitfalls |
|---|---|---|---|---|---|
| Target physics (measured) | `challenges/05-pmhc/notes/target-physics.md`; script `challenges/05-pmhc/scripts/target_physics.py`; outputs `notes/target-physics.csv`, `notes/references/target-physics.json` | The measured reading: peptide exposure table (readable ridge P4-P8; anchors P1-P3/P9-P10 buried); D6 sidechain ~90 percent buried (8.8 A2), OD2-R114 2.95 A, OD2-Q70 3.08 A; closest JDI atom to D6 carboxylate 7.51 A; peptide mobility (P5/P6 missing in 7OW4); peptide-free deletion exposes 678 A2; Debye-Huckel G12D-minus-WT difference field (cation 6-8 A above P6-P7 is the specificity handle); assay physics (design immobilised, C-terminal Twin-Strep, keep C-terminus away); a 13-item design checklist | High: the design constraints are settled; regenerate numbers with the script any time | None; keep the checklist as the C5 campaign contract | It is a deletion model for the peptide-free state (no conformational change encoded); the electrostatic table is an order-of-magnitude estimate, not a free energy |
| research-mechanism.md | `challenges/05-pmhc/notes/research-mechanism.md` | Literature and prior art: JDI TCR discrimination (indirect electrostatics; enthalpy -20.3 vs -9.6 kcal/mol; >6000x window after maturation), TCR-mimic antibodies and biologics, de novo pMHC campaigns 2023-2026, target biology, assay expectations; URL per item; [computed] distances from 7OW3/4/5/6 and 7PB2 | High: the evidence base for the strategy step | None | Abstract-only items flagged; do not re-fetch what is already computed |
| research-community.md | `challenges/05-pmhc/notes/research-community.md` | Public C5 signals: rpinho campaign (AF2 control cannot separate G12D/WT - ipTM 0.84 both; APBS difference map; BindCraft overnight 0 accepted), guillemares, ElainW 9-mer campaign (1000 backbones -> 4 pass), participant repos, access notes and gaps | High: competitor intel + the negative controls already observed by others | None | X/LinkedIn login-walled; snippets only; the 9-mer register trap |
| research-tooling.md | `challenges/05-pmhc/notes/research-tooling.md` | Tooling mapped to this box: binder-prescreen `kras-pmhc` slug details; adaptyvbio protein-design-skills (24); competition_metrics repo; RFdiffusion v1 / RFD3 / BindCraft2 / BoltzGen pMHC configs; ipSAE thresholds (0.61 / 0.70); local clone evidence | High: the generator/scorer menu and thresholds for C5 | None | Some configs are third-party and unvalidated for our 3-chain target |
| deep-physics.md | `challenges/05-pmhc/notes/deep-physics.md` | Water and desolvation (conserved groove water networks; the p53 R175H TCR 6-11 desolvation precedent), peptide dynamics (induced fit; 9-mer vs 10-mer registers), empty-MHC states (metastable, peptide-scavenging; the C8K10D lesson - counter-select against the peptide-free state from round 1), the 12-factor physical/chemical checklist | High: feeds scoring choices (desolvation term; peptide-free read caution) | None | Empty MHC is heterogeneous; the deletion model cannot prove non-binding |
| deep-similar-targets.md | `challenges/05-pmhc/notes/deep-similar-targets.md` | TCR-mimic antibodies (ESK1 / 4WUU; NY-ESO-1 TCRm; H2/p53 as the direct-contact counterexample) and engineered TCRs: the affinity/specificity ladder (Holler, Zhao: the highest-affinity variants lost specificity), footprint and specificity-engineering lessons | High: informs the footprint and the do-not-over-mature rule | None | Some claims are UNVERIFIED in the source; keep the labels |
| deep-campaigns.md | `challenges/05-pmhc/notes/deep-campaigns.md` | Published campaign numbers: Liu et al. Science 2025 (1000-20000 backbones per cycle; 4-32 MPNN sequences per backbone; Rosetta CMS; partial diffusion 12-25 steps; yeast display 200-12000 designs; nM binders; crystal 0.4 A), Johansen NY1-B04 (44 filtered -> 1 binder, ~2 percent; 46 MHC vs 21 peptide contact pairs), ElainW numbers (0.4 percent), the 9-mer/10-mer register warning | High: expected yields and design geometry (arc above the groove; peptide-first hotspots) | None | The public 9-mer work must not be copied (register trap) |

## (l) Explicitly NOT reusable for C5

| Asset | Path | Why not |
|---|---|---|
| pH-switch stack | `tools/binderkit/phscore.py` (PROPKA linkage), `tools/switch/*` (target_switch_anchors, make_switch_motif, switch_positions, linkage_score, build_submission), `tools/analysis/his_variants.py`, ProtonPottsMPNN (`~/tools/ProtonPottsMPNN`), the C4 switch campaigns | C5 has no pH objective. His-gating and linkage scoring are inert here |
| Membrane checks | `tools/analysis/membrane_space_check.py`; insertion-depth metric | AGENT.md item 28 decided 2026-10-30: C5 is a soluble pMHC complex; neither check applies |
| Mouse cross-species machinery | C4 campaign 4 (mouse cross-fold), conservation-by-chemistry-class analysis | C5's counter-target is the WT PEPTIDE on the same HLA, not an ortholog; the logic is specificity, not cross-reactivity |
| Activation geometry scorer (code) | `~/c3-work/c8-agonism/scorers/activation_geometry.py` | Target-specific (GLP1R pharmacophore); only the PATTERN transfers (see section j) |
| pH movie / simulation modes | `tools/report/sim.py`; `pdt movie --mode sim`; the `md` pipeline's His protonation-state design | The sim wells are pH-linkage-derived; not C5 evidence. `trajectory`/`dock`/`spin` modes remain generic |
| Tamarind route and C2 handoff package | `challenges/02-tnfa/handoff/`; `~/.config/tamarind/api_key` | Tamarind quota spent (resets 2026-11-01); the C2 campaign is closed. Historical record only |
| C1 replay fixtures | `challenges/01-egfr/`, `tools/pipelines/c1.py`, tests `tests/test_units.py` parity checks | Regression material for the vendored binderkit; not C5 design work. Keep them green, do not extend |
| C4 target-specific data | `challenges/04-tfr1/inputs/*` (11QC, mouse model), epitope sets E0/E1/E2/E12, `nim/build_request.py` (hard-codes the TfR1 patch) | TfR1-specific. The RFD4 request builder must be re-pointed for C5 |

## Adjacent assets worth knowing

| Asset | Path | Note |
|---|---|---|
| C5 research scratch | `~/.hermes/cache/scratch/c5/` (61 MB) | Raw materials behind the scout reports: downloaded PDBs (7OW4/5/6), paper XML/HTML, tooling readmes, `deep-*.md` drafts, `extracts/`, and `apply_c5.py` (the patch that wired the C5 challenge into the workbench app - already applied; `tools/serve/brief.py` has the `05-pmhc` entry) |
| Workbench app | `pdt serve` on 127.0.0.1:8737; `tools/serve/app.py`, `tools/serve/brief.py`, `tools/serve/viewer3d.py` | The C5 challenge page is already wired with both target viewers; run pages appear once C5 specs run |
| Tests | `tests/` (`test_contacts.py`, `test_runner.py`, `test_serve.py`, `test_units.py`) | Offline suite (`pytest -m 'not network'`). Add a C5 test only for logic that gates a submission or a served page (AGENT.md rule 8) |
| Working rules | `AGENT.md` (repo root) | Read before changing the repo; item 28 records the C5 soluble decision; mistake 27 records the IPSAE companion-name trap; update it after mistakes |
| Skill | `~/.hermes/skills/research/protein-binder-design/` (SKILL.md + 31 references) | The tool-level knowledge base; the C5-relevant references are listed in sections b, d, e and the j pattern row. Domain rules already include the C5 rule: require contacts to the PEPTIDE at the mutated position in every passing fold |

---

## 2. Reuse plan (highest value first)

1. **Run the JDI TCR control through the existing stack before any generation.**
   Fold 7OW6 chains (JDI + G12D) and 7OW5 (JDI + WT) with Chai-1 restrained
   (pocket restraints on peptide P4-P8 + groove rim) and with Boltz-2 + ipSAE;
   the synthesis (research-synthesis.md step 1) makes instrument separation of
   G12D vs WT the precondition for trusting any screen. Recipe:
   `references/chai-1-constrained-screening.md`; screen mechanics:
   `tools/pipelines/screen.py`.
2. **Author the first C5 spec from the screen pipeline.**
   `challenges/05-pmhc/experiments/<name>.yaml` with `pipeline: screen`, the
   peptide-ridge hotspots (label_seq_id), and the designs dir of the control
   folds. Shape: `challenges/04-tfr1/experiments/c1-epitope-screen.yaml`.
3. **Build the tri-state specificity screen as one new pipeline (`tools/pipelines/c5.py`).**
   For each candidate: fold/read against G12D, WT and peptide-free; compute
   peptide-first engagement (contacts.py `hotspot_engagement`), binder-peptide
   vs binder-HLA vs binder-b2m chain-pair scores (ipSAE from Boltz PAE), and
   the G12D-minus-WT delta; register it in `tools/pipelines/__init__.py`.
   Template for a new pipeline: `tools/pipelines/fold.py` + the obligations in
   `references/adding-a-pipeline.md`.
4. **Copy and reweight the C4 selector.**
   `challenges/04-tfr1/campaigns/c6-selection/scripts/select-top20.py` ->
   C5 rubric (specificity first), keeping the floors and the pre-flight
   assertions exactly as they are.
5. **Stand up the first C5 campaign README with pre-registered advance/discard rules.**
   Shape: `challenges/04-tfr1/campaigns/c2-binding-families/README.md`; the
   rules must exist before the deciding run (lessons-c2-c3.md).
6. **Wire the submission early.**
   `challenges/04-tfr1/submission/build-submission.py` pattern +
   `tools/analysis/validate_submission.py` + the novelty prescreen
   (`--target kras-pmhc`, `PRESCREEN_DB_ROOT=~/prescreen-dbs`).
7. **Viewers for the finalists.**
   `tools/report/molstar_views.py` for review images; a C5 tri-state multiview
   built from `challenges/03-glp1r/viewers/scripts/make_molstar_multiview.py`.
8. **QC passes at the end.**
   `tools/binderkit/liability.py` with C5 thresholds (10-250 aa, min_his 0) and
   the C4 liability-repair pattern; full prescreen arm on the finished set.

## 3. Gaps (what we lack for C5)

1. **No C5 experiments yet.** `challenges/05-pmhc/` has inputs, notes and one
   script - no `experiments/`, `runs/`, `campaigns/`, `viewers/` or
   `lineage.json`. Everything in the reuse plan above is still to be built.
2. **The instrument question is open.** No fold of the JDI control has been run
   through our stack on all three states; whether Chai-1 restrained or Boltz-2
   separates G12D from WT is untested anywhere public (research-synthesis.md,
   open unknowns).
3. **The peptide-free arm has no defined in-silico read.** The deletion model
   has no peptide chain, so pocket restraints need a groove-rim fallback and
   the screen needs a pre-registered definition of what peptide dependence
   means in silico (proposal: require peptide contacts in the G12D fold and a
   large engagement drop in the peptide-free fold).
4. **No specificity aggregation tool.** ipSAE gives chain-pair tables, but the
   tri-state delta aggregator (binder-peptide vs binder-HLA vs binder-b2m;
   delta G12D-WT; contact-at-P6 metric) does not exist yet - it is the core of
   the new C5 pipeline.
5. **Electrostatic scoring is estimate-grade.** APBS is not installed; the
   target-physics estimate is Debye-Huckel with a uniform dielectric. If the
   cation-placement strategy is used for selection, decide whether the APBS
   difference map is worth the install.
6. **Generator choice for C5 is unmade and unmeasured.** RFdiffusion v1 is
   proven on pMHC in the literature but not installed locally; RFdiffusion3 is
   installed but its pMHC hotspot config is open; RFD4-Proteina hosted route
   exists (`nim/build_request.py` must be re-pointed); BindCraft2 is installed
   but the one public pMHC run failed. No local generation against this
   3-chain target has been run.
7. **3-chain fold memory is unmeasured.** Local precedents: a 456-residue
   4-chain complex fit at 11.3 GiB (C2); a 789-residue 3-chain fold sat at the
   VRAM cliff (11.9 of 12.2 GB). The C5 complex (binder + heavy chain + b2m +
   peptide, ~500-600 residues total) should fit, but needs a measured smoke
   run; HLA MSAs need the depth-capped MSA path.
8. **Novelty reference limits.** The `kras-pmhc` prescreen set is TCR-only by
   construction (no designed-binder references exist for this pMHC), so the
   target arm cannot catch a copied designed binder - because none is public.
   The prior-art arm (built, 113 GB) covers the general corpora.
9. **Absent on this host:** the baseline repo dir
   (`~/Projects/Protein-design-competition-Anthropic-X-adaptyv`), the two EGFR
   repos, `~/Projects/protein-design-competition-report.md` and
   `~/Projects/protein-design-runbook.md`. Use the vendored modules
   (`tools/binderkit/`, `tools/switch/`), the snapshot
   (`challenges/01-egfr/reference/baseline/`) and
   `docs/competition-notes/00-competition-report.md`.
10. **No C5 MD run and no C5 movies.** `trajectory` mode needs an OpenMM run;
    the pH `sim` mode does not apply. Optional, not on the critical path.
11. **No C5 lineage/viewer pages yet.** The multiview builder needs a C5
    lineage JSON (schema: skill reference workbench-app.md) before the app can
    show campaigns.

## 4. Verification notes (read-only audit)

- Every claim above was checked against the files at the cited paths on
  2026-10-30. Key verified facts: `~/prescreen-dbs` exists (113 GB, eight
  arms); `~/tools/mmseqs/bin/mmseqs` exists; `tools/serve/brief.py` carries
  the `05-pmhc` entry; `challenges/04-tfr1/submission/` holds the built
  submission + methodology + self-evaluation; `~/c3-work/c8-agonism/scorers/
  activation_geometry.py` exists; the C5 inputs (3 PDBs + 4 reference CIFs)
  are committed under `challenges/05-pmhc/inputs/`.
- No file in any inspected repo was created, modified or deleted by this
  audit.
