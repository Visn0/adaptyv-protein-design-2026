# Campaign 2 — peptide agonists via validated agonist-design tools (strategy S3)

## The bet

Campaign 1 produced mini-proteins with the right contact pattern but no
activation evidence. EvoBind is the only published pipeline whose GLP1R
designs have **activated the receptor in cAMP assays** (dual GCGR/GLP1R cyclic
agonists, EC50 32 nM; Commun Chem 2025, bioRxiv 2025). Campaign 2 designs
peptides with EvoBind against the same orthosteric site and screens them with
the campaign-1 pipeline.

## Why this is a different strategy, not a rerun

- Modality: short peptides (10–40 aa) instead of 60–100 aa mini-proteins.
- The design engine optimises sequence AND the receptor interface
  simultaneously (EvoBind2) — no backbone generation, no MPNN step.
- The agonism prior is experimental, not inferred: the same protocol produced
  receptor-activating peptides in published cAMP assays.

## Plan

1. Setup: EvoBind2 (AF2 parameters, its environment; receptor MSA reused from
   `challenges/03-glp1r/inputs/msa/` instead of the 30 GB uniclust download).
2. Design runs: receptor = the GLP1R sequence (6X18 chain R), interface
   residues = the campaign-1 groove + junction hotspots, peptide lengths swept
   (10–30 aa), cyclic and linear.
3. Scoring: the campaign-1 screen — Boltz co-folds against the full construct,
   ipSAE, groove + TM-pocket + ECL3 contacts, clash checks, active-state
   conformation check.
4. Selection: the reach-weighted composite; one design per family; prescreen
   before any submission.

## Pre-registered rules

- Discard rule: if after ≥3 design runs and ≥100 designs folded no peptide
  clears ipSAE ≥ 0.8 at the site, the campaign is discarded with the measured
  reason.
- Cap: every run under `memlimit`; one GPU job at a time.

## Decision record (2026-10-19, by the pre-registered rule)

**Outcome 1 — CONTINUE campaign 2.** Both runs finished and every design was
folded and screened (Boltz-2 vs the full receptor, ipTM 0.98–0.99):

| design | run | best ipSAE | pDockQ2 | groove | tm | ecl3 | clashes | verdict |
|---|---|---|---|---|---|---|---|---|
| c2-run1-b206 | linear, it. 206 | 0.873 | 0.217 | 4 | 4 | 5 | 0 | **HIT (two-domain)** |
| c2-run1-b297 | linear, it. 297 | 0.898 | 0.292 | 1 | 2 | 3 | 0 | HIT (two-domain) |
| c2-run2-i298 | cyclic | 0.845 | 0.279 | 1 | 1 | 4 | 0 | HIT (two-domain) |

Actions taken per the rule:

- **c2-run1-b206 promoted into the challenge submission** — it ranks #5 of 24
  in the combined reach composite (above e1-r0025), the first peptide in the
  set. The other two peptides are the first alternates.
- **Length sweep launched**: run 3 (20 aa cyclic) chained into run 4 (12 aa
  cyclic), 300 iterations each.
- The chemistry levers (D-amino-acid substitutions, N-terminal acetylation)
  are **dropped for the competition** — the submission format is a plain
  sequence, so neither can be expressed; they remain assay-side suggestions in
  the notes.
- Both runs converged to the MGIRYFV(N/G)QQRNYN(P/S) family (linear) and the
  AEAWCVNFIEDRAPS family (cyclic) — independent evidence that this interface
  region has a strong sequence preference.
- **Method notes (2026-10-19):** runs 1–2 were launched without
  `--receptor_if_residues`, so EvoBind designed against the whole 207-aa
  fragment and picked its own site — which turned out to be the orthosteric
  region anyway (all screened peptides docked the groove/TM/ECL3 area). The
  sweep runs add the campaign-1 interface residues explicitly. Also: the sweep
  scripts' first launch failed instantly because the copied `mkdir` still
  pointed at run2's directory while `--output_dir` pointed elsewhere — when
  copying a run script, diff every path in it.

### The rule as pre-registered (2026-10-18)

When the runs finish and every peptide is folded and screened, take the
continue-or-new decision by this rule:

1. **Any peptide clears ipSAE ≥ 0.8 at the designed site with the two-domain
   reach (groove + TM-side contacts) and no clashes → CONTINUE campaign 2**:
   sweep more lengths (10–30), cyclic variants, and the two cheap chemistry
   levers from the resources sweep (selected D-amino-acid substitutions;
   N-terminal acetylation), then promote the best peptides into the challenge
   submission.
2. **Peptides bind (clear the site test) but never clear ipSAE 0.8** → CONTINUE
   with one focused fix round (longer peptides 20–30 aa and a re-run against
   the junction-only interface set — the campaign-1 lesson), then re-decide.
3. **No peptide reaches the site at all after the three runs** → DISCARD
   campaign 2 and START a new campaign; the next strategy is chosen from the
   resources sweep (candidates: BoltzGen cyclic-peptide generator; BindCraft2;
   the N-terminal-module conversion of campaign-1's best binder — the
   documented agonist-rescue pattern).
4. Any decision also weighs the calendar: challenge 4 opens Oct 19 and
   challenge 5 Oct 26 — a new campaign can target the next challenge instead
   of stretching this one.

## Risks (acknowledged)

- **License:** EvoBind2 is CC BY-NC 4.0. Competition use is non-commercial
  research; the user decides if that is acceptable. Designs generated with it
  carry no license restriction.
- **Resources:** AF2 parameters ~3.5 GB; the setup script builds hh-suite and
  wants conda — replaced by our existing MSA where possible.
- **Novelty:** peptides from this pipeline are de-novo sequences; the
  prescreen's peptide-heavy GLP1R reference set (215 GLP-1 analogue peptides)
  is the right filter.

## Submission update (2026-10-19, composite v2)

The enriched screen (LIS + corrected pDockQ2; the old column had been reading
pDockQ) plus the 3,766-binder meta-analysis evidence (ipSAE-family metrics are
the best predictors) motivated a composite update:
`ipSAE*3 + pDockQ2*2 + LIS + tm*2 + ecl3`. Ranking the 25-candidate pool puts
**three peptides in the 20-design submission**: c2-run1-b206 (#3),
c2-run2-i299 (#10), and — on an affinity-first tie-break, since the challenge
ranks affinity first — c2-run1-b297 (#22 by composite, but ipSAE 0.898 and the
pool's best pDockQ2 0.493) replacing e1b2-r0080. Prescreen: 17 pass + 3
peptides flagged only with the tool's short-sequence `no_reference_signal`
note (< 25 aa), which is documented behaviour, not a failure.

## PAUSE (2026-10-19, ~14:05) — PC handed over at the user's request

State: EvoBind run 3 (20-aa cyclic) reached iteration **245 of 300** and then
stopped at ~14:03 — cancelling the chain scripts propagated further than
intended and took the run's process tree with it. The loss is immaterial: the
design sequence had already converged by iteration ~229 (unchanged through the
end), so the 245 on-disk iterations carry the run's result. Run 4 (12-aa) and
the BoltzGen smoke test were deliberately NOT auto-started. Everything on disk
is resumable; the GPU is free.

Resume (in order, one GPU job at a time):
1. `bash ~/c3-work/c2-run4.sh 300`               # 12-aa cyclic sweep run
2. `bash ~/c3-work/boltzgen-test.sh`             # BoltzGen smoke test (now runs immediately)
3. Extract + fold + screen run 3's and run 4's best iterations:
   `c2_extract_designs.py <run_dir> <tag>` → `run-c3-folds.sh` → `screen_folds_c3.py`
4. Promote winners via the composite v2 ranking, rebuild the submission CSV,
   re-run the prescreen.

## Sweep first result: 20-aa designs (run 3) do NOT clear the bar

Run 3 reached 245/300 before the pause (the sequence had converged from ~229).
Its four sampled iterations (100/150/200/245) were folded and screened
(2026-10-19 14:36): none is a two-domain HIT. Best ipSAE 0.780, all
groove-only; binder pLDDT 33–55 (vs 80–90 for the 15-aa designs) — the 20-aa
peptides fold less confidently and dock worse. Length trend so far:
15 aa > 20 aa. The 12-aa run (run 4, queued for resume) tests the short end.

## Sweep conclusion: 15 aa is the sweet spot

Run 4 (12-aa cyclic, 298 iterations, converged to IVGETCPVKCFC) finished
2026-10-20 00:00. Its designs were folded and screened: **no hits**. Best
ipSAE 0.802 with zero groove contacts; iterations 200-299 drifted to
non-binding designs (pLDDT 23-55). Full length sweep:

| length | run | result |
|--------|-----|--------|
| 12 aa  | 4   | 0 hits (best 0.80, no groove contact) |
| 15 aa  | 1,2 | 3 hits (ipSAE 0.83-0.88, groove+junction) |
| 20 aa  | 3   | 0 hits (best 0.78, groove-only) |

**Decision (pre-registered rule): promote the 15-aa winners (already in the
submission CSV) and close campaign 2.** Next: campaign 3 (BoltzGen cyclic
peptides at the same site), started 2026-10-20.
