# Experiments — the strategy and the steps

This document explains the experiments in this repository: the specs you can
run, the idea behind them, and the record of each challenge. You do not need
to read the code.

The specs are the YAML files in `challenges/<challenge>/experiments/`. A spec
names a pipeline (`fold`, `screen` or `md`), the stages to run, and the
parameters. The command `pdt exp run` executes one spec and writes one run
folder.

## 1. How an experiment runs

| Command | Function |
|---|---|
| `pdt exp list` | List every spec. |
| `pdt exp run <name>` | Run one spec. |
| `pdt exp run --all -j 4` | Run every spec, four at a time. |
| `pdt exp status` | Show the recent runs. |
| `pdt report <run_dir>` | Rebuild one report. |
| `pdt dashboard` | Build the hub page (`runs-dashboard.html`). |
| `pdt serve` | Start the local app on 127.0.0.1:8737. |
| `pdt movie <run_dir>` | Render an MP4 from one run. |

The runner starts one worker process per spec. Each worker writes its own run
folder, `challenges/<c>/runs/<stamp>-<name>/`:

| File | Contents |
|---|---|
| `run.log` | The full transcript: stage messages and subprocess output. |
| `status.json` | The state, the timing, the device and the git revision. |
| `summary.json` | The structured result. The report reads this file. |
| `spec.resolved.yaml` | A copy of the spec that ran. |
| `artifacts/` | Every file the stages wrote. |
| `report.html` | Tables, charts and a 3D view. |

A run finishes in one of three states:

- `done` — the stages finished. Read `report.html` or `summary.json`.
- `waiting_inputs` — a stage needs an external file. The message names the file. Provide it, then run the spec again.
- `failed` — an error stopped the pipeline. Read the end of `run.log` for the traceback.

Specs declare their resources (`cpu` or `gpu`). A missing GPU never fails a
run: the stage uses a fallback, or it waits for inputs. The report chapters
are Goal, Steps, Settings, Results and 3D view.

The replay specs, and the third-party engines they ran on, were removed on
2026-11-08. One spec stays as a reference run: `c1-epitope-screen`
(challenge 4).

## 2. The specs that exist now

| Spec | Challenge | What it does |
|---|---|---|
| `c2-fold-w1-gpu` | 02 | Imports the X2 shortlist co-fold against the human TNF-α trimer (Boltz-2, five samples). Scores every sample with IPSAE and compares against the Tamarind fold of the same design. |
| `c2-fold-w2-*` (nine specs) | 02 | The same import and score for the wave-2 designs: seven folds against the human trimer and two against the mouse trimer. |

The c2 folds apply the pre-registered bar to every sample: `ipSAE ≥ 0.6` AND
`pDockQ2 ≥ 0.23`.

## 3. The shared idea: a pH switch

Challenges 1, 2 and 4 ask for pH-dependent binding. Structure predictors
ignore pH. The repository adds the pH signal with a pKa predictor (PROPKA)
and geometric filters.

| Term | Meaning here |
|---|---|
| histidine (His) | The only residue that changes charge inside the 6.0–7.4 window. |
| carboxylate (Asp, Glu) | A group with a negative charge. |
| cation (Arg, Lys) | A group with a positive charge. |
| pKa | The pH value where a group is half protonated. |
| selectivity | The predicted binding difference between the two pH values. |

- When a group changes its pKa on binding, the binding energy changes with
  pH. The sum over the titratable interface groups is the selectivity score.
- The direction follows the chemistry. A binder histidine against a target
  carboxylate favors binding at low pH. Against a target cation it favors
  binding at pH 7.4.
- One switching site gives at most 1.4 log units (about 25x) across the
  1.4-pH window. A 100–1000x switch needs two or three sites.
- The score ranks designs. It does not predict absolute affinity. PROPKA is
  an empirical model.

## 4. The challenges, in short

**01 EGFR — not attempted.** The window closed on 2026-10-07, before this
workspace existed.

**02 TNF-α — the switch campaign.** The switch layer ran outside this
repository. Three external experiments asked whether an open generator can
place a binder in the TNF-α groove. BoltzGen found none (best ipSAE 0.005).
RFdiffusion3 placed 58 of 72 complexes in the antibody groove. The decisive
Boltz-2 co-fold passed in 1 of 5 samples. The record is in
`challenges/02-tnfa/notes/` and `challenges/02-tnfa/handoff/`.

**03 GLP1R — the campaigns.** The challenge ran as campaigns, not specs:
RFdiffusion3 mini-proteins, EvoBind cyclic peptides, BoltzGen cyclic peptides,
and later follow-ups. The 15-residue cyclic peptides were the sweet spot. The
record is in `challenges/03-glp1r/campaigns/`.

**04 TfR1 — the switch, again.** The challenge ran as campaigns, not specs:
its one reference spec went with the reference experiments on 2026-11-08. The
record is in `challenges/04-tfr1/`.

**05 KRAS G12D pMHC — campaigns, no specs.** The challenge ran as campaigns
and a custom model. The record is in `challenges/05-pmhc/`.

Update this document when a spec changes.
