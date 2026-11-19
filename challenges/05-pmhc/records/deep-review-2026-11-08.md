# Deep review of challenge 05 — repo, strategy and tool coverage (2026-11-08)

Scope: the challenge-05 submission package, the repository organization, the
campaign coverage and the tool coverage. Method: direct reading of the records
and notes, a rerun of the submission validator, a recount of the set's
properties from the CSV and the fold summaries, a spot-check of the clean
panel's numbers and a check of the working tree. This review is in-silico
only. The wet lab decides the result.

## Verdict

The submission is in good shape and needs no further design work. The
validator passes, the three deliverables agree 20/20/20, and the last swap of
2026-11-08 rests on measured panel evidence. The record is unusually complete,
negative results included. This review corrected every stale or wrong claim
found in the submission-facing texts, refreshed the index documents
(section 3) and lists the residual gaps in strategy and tool coverage
(sections 4 and 5). No residual gap can change the
submitted set before the deadline. Do not churn the set again.

## 1. Submission package audit — verified today

| check | result | evidence |
|---|---|---|
| Validator | `20 design(s) checked` · `OK - ready to upload` · exit 0 | `tools/analysis/validate_submission.py` rerun |
| CSV vs FASTA vs scores | 20/20/20, identical order and sequences | scripted comparison |
| Lengths | 64–98 aa, all inside 10–250 | scripted count |
| Names and sequences | unique, no duplicates | scripted count |
| `molecule_class` | `single_chain` — the submission template's vocabulary; challenges 3 and 4 used it | `records/` of C3/C4 |
| Prompt-injection sniff | both submission texts clean | grep over `SNIFF_WORDS` |
| Organizer gate (peptide_read >= 0.61) | 16 of 20 pass | clean panel + the 2026-11-04/08 records |
| Set composition | 8 campaign parents, 12 evolution/repair children, 14 unique backbones | scripted count from the CSV |
| Four below-gate entries, kept on separation | wave2-pep-049 0.596/0.053 · L58K-Q15K 0.554/0.000 · E23K 0.545/0.313 · wave2-pep-054 0.463/0.019 (G12D/WT reads) | `~/c5-work/wt-panel/s1-summary.csv` |

The clean two-state panel's numbers reproduce. Spot-checked against the
2026-11-08 independent review: N71K 0.676/0.006, W57K 0.641/0.223, mini-011 c5
0.635/0.519 (correctly rejected as cross-reactive), peprim-007 0.486/0.429 and
peprim-012 c3 0.411/0.113 (both removed). The swap is a strict improvement on
both criteria, and gate compliance rose from 14/20 to 16/20.

The score column (`records/selection-scores-05-pmhc.csv`) mixes two formulas
by design: the six 2026-11-04 additions carry the v4 composite, the two
2026-11-08 restorations carry no score. This stays an author decision.
The CSV row order carries the ranking.

## 2. Repository state

- The challenge-05 tree is organized and findable: `README.md` (entry point,
  refreshed today), `notes/` (research + decisions), `campaigns/` and
  `records/` (per-campaign evidence), `submission/` (the three upload files),
  `custom-model/` (the generator project), `viewers/` (the local workbench).
- No junk: no tracked `__pycache__`, no backup files, no stray large files in
  the challenge folder. Heavy artifacts stay outside the repo in `~/c5-work`
  by convention.
- One orphan file sat untracked since 2026-11-04
  (`custom-model/scripts/collect_submitted_cifs.py`, the OpenDDE input
  collector). It is committed with this review.
- Another agent is working in this repo concurrently (the 03/04 challenge
  files and a site-restructure of `lineage.json` / `viewers/`). This review
  touched no file of that workstream and used explicit-path staging only.
- This review's changes: only the files listed in the commit.

## 3. Fixes applied by this review

| # | file | problem | fix |
|---|---|---|---|
| 1 | `submission/methodology.md` | claimed "all 20 submitted designs read negative" on the E-score | corrected to 16 of 20 (best −3.75), with the four neutral-to-positive entries named and cited to `records/final2/escores.csv` |
| 2 | `submission/methodology.md` | described the score column as one composite (v3) | states the two-scale mix instead |
| 3 | `submission/design-method.md` | described the set as "11 dual-signal / 5 affinity / 4 champions" — counts from the 2026-11-02 era | replaced with the current composition (8 parents + 12 children, 16/20 gate, the set's best reads) |
| 4 | `records/final2/METHODS.md` | same two stale statements, plus "60-99 aa" and "fold alone at pLDDT >= 0.95" | corrected to 64-98 aa and the true composition |
| 5 | `challenges/05-pmhc/README.md` | one month stale ("C0 is the next thing to run") | rewritten as the final state and index |
| 6 | `records/final2/README.md` | presented a 2026-11-02 snapshot as "final" | marked historical with pointers to the current set |
| 7 | root `README.md` | row 05 said "open — brief captured" | now "submission ready (2026-11-08)" |
| 8 | `custom-model/scripts/collect_submitted_cifs.py` | untracked since 2026-11-04 | committed |

The E-score finding (fix 1) matters most: the claim was wrong for four legacy
entries (nat-wave1 run-004 d0001 +0.14, wave1-pep run-033 d0003 +0.23,
peprim-wave1 run-013 d0007 c1 +0.85, wave2-pep run-054 d0005 +1.47). They stay
in the set on their other validated axes. No submission text may claim
otherwise.

## 4. Strategy coverage — planned, run, verdict

| strategy | run | verdict | record |
|---|---|---|---|
| Instrument calibration (C0) | yes | fold metrics are blind to the single-point mutation (wrong sign on the JDI control); only direct electrostatics passes | `campaigns/c0-*`, crystal read, metric cutoffs pre-registered |
| Main funnel, hosted RFD4 (C1) | yes | 2,264 backbones (2,247 unique) across five waves and three targeted campaigns; the base supply of the set | `campaigns/c1-*`, `records/stage*` |
| Peptide-only mining (C2) | yes | 1 gate passer of 44 folds; became a submission family | `campaigns/c2-*` |
| Natural-reader conditioning (C3) | yes | best variant yield (4 strict passers of 32); two submission entries | `campaigns/c3-*` |
| Charge-first / TIGHT (C4) | yes | negative, 0 of 25 — the tight window starves the interface | `campaigns/c4-*` |
| Minibinders (C5) | yes | 11 of 37 JDI-like; strongest free-state dependence | `campaigns/c5-*` |
| Optimization loop, MPNN children (C6) | yes | stability holds, discrimination erodes in 8 of 10 children | `campaigns/c6-*`, `records/c6` |
| Rule mining + surrogate (C7) | yes | rules predict (3 of 8; 2.5x lift), the learned surrogate fails (0 of 50) | `records/c7`, `records/surrogate-test` |
| Cross-panning against variants (C8) | yes | negative — the instrument cannot resolve single-point variants | `records/c8` |
| Generator hunt (C9) | yes | genie3 0/70; BoltzGen not adopted; local RFD4-Proteina at parity; the fine-tune destroyed target conditioning (Modal A100 run) | `records/c9`, `custom-model/notes` |
| Pristine local batch (C19) | yes | 9 of 100 pass the gate, none beats the champions on specificity; the set stands | `custom-model/notes/pr-batch-results.md` |
| PEPRIM wave 5 + SALT (direct grip) | yes | both negative — the generator cannot be conditioned onto the buried carboxylate; the field-reading doctrine is confirmed by its alternative's failure | `records/c11-wave5`, `records/c12-salt` |
| Repair rounds (R1/R2) | yes | R1 one strict win (L58K), R2 three composite wins (A58K, H27K, N71K); five entries resisted with folded arms | `records/repair2`, notes |
| Evolution loop (generations 1–20) | yes | six promotions; Q15K and A16K carry record reads; generations 13–20 then plateaued | `records/evo-gen1`, site C14 |
| Two-for-two gate swap (panel) | yes | today's final set change; strict improvement on both criteria | `records/independent-review-2026-11-08.md` |
| Counter-selection by partial diffusion | no | replaced by the evolution loop as the specificity driver; the planned round never ran as such | `notes/strategies.md` §C4 |
| RFdiffusion3 local hedge | pilot only | 2 designs generated, no folds or verdict recorded — a record gap, not a design gap | `~/c5-work/c2`, `scripts/work/c2-rfd3-chain.sh` |
| VHH / scFv modality | no | cut at planning, then closed by the instrument audit as out of the window | `notes/edge-modalities.md`, instrument audit |
| Picomolar affinity chase | no | deliberate — the KD(WT)/KD(G12D) window outranks absolute affinity | `notes/strategies.md` |

Assessment: the campaign space is covered with two honest gaps. First, the
negative-design round was replaced by evolution and the substitution is
recorded. Second, the RFdiffusion3 hedge left no verdict. Neither changes the
submitted set.

## 5. Tool coverage

Used and current (release dates from `custom-model/notes/tool-audit-2026.md`):
RFD4-Proteina (hosted NIM + local BSD-3 re-host), Boltz-2 2.2.1, Chai-1 0.6.1,
BindCraft2 (scoring), IPSAE, ProteinMPNN + LigandMPNN, BioEmu2, PROPKA
(escore2), PyRosetta (control failed, disqualified), scikit-learn (surrogate,
negative), MMseqs2 (MSA + homology), ATLAS/SKEMPI (labels for calibration,
scope test only, r = −0.08).

Not used, with reason:

- **PXDesign / Protenix-v2** — the one open generator never run. The
  installer needs conda/Docker, custom CUDA kernels and ~9 GB of downloads,
  and the project recommends its web server. The server sends the target
  off-machine. That is a disclosure decision and a day of setup. Both are
  wrong for the last window. The tool audit already ranks it as the backup
  generator for a future campaign.
- **OpenDDE (second co-folding opinion)** — shelved after two host reboots.
  A retry pass collected 20 complex files but produced no scores. It is a
  binder-vs-nonbinder instrument, not a G12D-vs-WT instrument. Skip.
- **APBS continuum electrostatics** — not installed (needs a package
  install). It is the community-standard form of the field reading the
  E-score implements crudely. An optional post-deadline addition.
- **Chai-2** — access-gated product, watch list only.
- **pMHCI classifier / ADAPT** — the original parameters were never released
  cleanly.
- **Complexa / OpenFold3** — available, never used for this challenge; no
  specificity value over the existing panels.
- **FEP / flex-ddG, all-atom MD** — not run. The BioEmu2 ensembles cover
  thermal stability at a fraction of the cost.

Assessment: the primary stack is the current release family of every tool it
uses. The unused tools cannot move the submission's fate. The evidence rests
on control-validated instruments, and that is the project's core and honest
finding.

## 6. Competitive context

A public archive from another participant (AethronPhantom, 64 designs, same
generator family) was folded through this funnel on 2026-11-08. Their
selected competition entries read weaker on specificity than the submitted
set: their strongest gate readers cross-react on the wild-type peptide
(best three at WT 0.546, 0.607, 0.630 against G12D 0.645, 0.594, 0.612),
while the submitted set's top entries separate mutant from wild type by
0.42–0.67. The archive's own README states that specificity remains
unresolved on its side. This comparison lives in `~/c5-work/rival-panel/`.
It is not yet in the repo records. Add it post-deadline.

## 7. Open items that do not block the submission

Items 1–4 are tracked by the site-sync workflow. Item 5 came up in this
review. None blocks the submission:

1. The workbench app does not render `verdict` / `verdict_detail` on lineage
   pages (cosmetic).
2. The evolution autopilot has no convergence stop (the loop is idle).
3. `rerank_v4.py` carries a pasted E table instead of reading the fold trees.
4. The score column's two-scale mix (section 1) — author's decision.
5. The site shows 84.3 for W57K while the score file leaves the cell empty —
   cosmetic inconsistency in the middle of the site restructure.

## 8. Recommendations before upload

1. Upload the CSV as-is. Keep names and sequences exact. The row order is the
   ranking.
2. Paste `submission/design-method.md` and `submission/methodology.md` into
   the submission form. The texts now match the final set.
3. Do not add, remove or swap any design. The two-for-two swap of 2026-11-08
   is the last change and it is measured.
4. If any file changes again, rerun the validator and the 20/20/20 check.
5. After upload, confirm the challenge page lists 20 designs in order. The
   window closes on 2026-11-09 at 12:59 CET.
6. Optional after upload: a single-scale score column, the rival-panel
   comparison as a repo record, the EMA fine-tune check, the APBS install.

## 9. Verification log

```
validator          20 design(s) checked / OK - ready to upload (exit 0)
csv vs fasta       order and sequences identical (True)
lengths            min 64, max 98; no duplicate names or sequences
families           20 entries, 14 families; mini-014 contributes 4
sniff check        design-method.md and methodology.md clean
gate compliance    16/20 pass; four below-gate kept on separation
panel spot-check   N71K 0.676/0.006; W57K 0.641/0.223; c5 0.635/0.519;
                   peprim-007 0.486/0.429; peprim-012 c3 0.411/0.113
E-score count      16 of 20 negative; four positive (+0.14, +0.23, +0.85, +1.47)
lineage rebuild    reproduced the working tree byte-for-byte (no drift)
git working tree   only this review's files staged and committed
```

Limits: all numbers come from fold models and the repo's own records. This
review did not refold any design. The selection process and the wet lab
decide the outcome.
