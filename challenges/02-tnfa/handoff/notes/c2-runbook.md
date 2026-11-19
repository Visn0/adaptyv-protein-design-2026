# C2 runbook — every step, maximum detail

*Written 15 October 2026. The document is complete: research, planning, tooling, X1 (negative), X2 (placement works), the decisive co-fold (pass, qualified), the documentation set and the PC handoff. Timezone note: **server times** (Tamarind) run 2 hours behind **local time** (CEST). Example: X1 jobs created at server 11:45 = local 13:45.*

---

## 0. Scope and actors

- Goal of the whole track: a **Challenge 2** entry — a de-novo binder for human TNF-α that binds at **pH 7.4**, releases at **pH 6.0**, and cross-reacts with mouse TNF-α (1TNF numbering).
- Constraint: the instructions require **volume of evidence over cleverness**, an honest report, and a pre-registered decision rule before spending anything.
- Actors: the user (decides scope and spend) and the Hermes agent (research, tooling, submission, analysis, documentation).
- Everything below happened on 15 October 2026 between 12:00 and 19:00 local time.

---

## 1. Phase 0 — research and context (before any spend)

### 1.1 Third public entry cloned and reviewed

- Command: `git clone https://github.com/Abdulrahman-Neamah/egfr-conditional-binder.git egfr-conditional-binder-abdulrahman`
- Renamed on clone on purpose: the original folder name collides with the earlier BindCraft entry (`~/Projects/egfr-conditional-binder`).
- What that entry used: **BoltzGen** for design and **Boltz-2** for cross-species folds, both run through **Tamarind Bio** (SaaS; free tier 10 jobs/month; 50–110 min per design run); PROPKA for the pKa hypothesis; ~785 lines of numpy/pandas scripts.
- Its Challenge 1 result: 96 designs → 34 passed filters; lead design ipTM 0.95–0.96 and ipSAE 0.93–0.94 in all 10 folds across both species; 11 designs submitted; novelty gate 3/4 passed for most.
- Its Challenge 2 result — the crucial data point: **five BoltzGen runs (full trimer, dimer, two hotspot maps, one unrestricted diagnostic), nothing usable.** Best ipTM 0.46 with a valid target. The dimer-target runs were invalid: binders occupied the place of the **omitted third protomer** (19 of 20 finalists). Their conclusion: the target, not the site choice, was the limit.
- Lessons extracted and written into `docs/competition-notes/repo-review-03-abdulrahman-neamah.md` (MIT licence; full tables in their `results/`).

### 1.2 Local recomputation of that entry's TNF-α epitope analysis

- Files downloaded into `challenges/02-tnfa/data/epitope-analysis/`: `1TNF.pdb`, `3WD5.pdb1` (adalimumab Fab + TNF), `4G3Y.pdb1` (infliximab), plus `1TNF.cif`.
- Their script `06_tnf_epitope_analysis.py` was run unmodified on this machine (exit 0) and produced `tnf_epitope_table.csv` (58 rows) and `tnf_patch_map.csv`.
- Our own extension script produced these facts:
  - `1TNF.cif` **author numbering equals label numbering** on chains A/B/C — so hotspot residues can be given as plain numbers without a conversion step. Verified programmatically (zero differences).
  - The cation trio exists on all three chains: **A103 ARG, B103 ARG, B112 LYS**. Mouse substitutions: **R103→K, K112→K (charge class kept)**.
  - The trap residue **A73 is HIS in human and TYR in mouse** (charge class lost) — the same conclusion the baseline repo reached.
  - CA–CA spans of the trio: **A103–B112 8.7 Å · A103–B103 10.7 Å · B103–B112 12.9 Å**.
  - The trio sits in a mixed electrostatic neighbourhood: nearest acidic side chains **B104 GLU 3.1 Å** from A103, **C104 GLU 3.7 Å** from B103, **B104 GLU 4.7 Å** from B112. This is the screening effect the baseline repo warned about.

### 1.3 Tool-landscape research (documented in `docs/competition-notes/07-tools-to-measure-binding.md`)

- Structure engines and their confidence outputs (pLDDT, PAE, ipTM), the AlphaFold Server FAQ bands (ipTM < 0.6 likely failed, 0.6–0.8 grey zone, > 0.8 high).
- Interface scores: ipSAE (Dunbrack 2025), pDockQ (2022), pDockQ2 (2023), actifpTM (2024/25), LIS; the acceptance filter used by AlphaFold DB itself: **ipSAE ≥ 0.6 AND pDockQ2 ≥ 0.23**.
- Reference scoring: DockQ and the CAPRI classes (0.23 / 0.49 / 0.80).
- Affinity guesses: PRODIGY, FoldX, Rosetta, MM/GBSA, Boltz-2 affinity (with the caveat that protein–protein affinity prediction is still weak — arXiv 2512.06592).
- The pH layer: PROPKA, the Wyman linkage relation, constant-pH MD in AMBER/CHARMM — research grade, not a design loop.
- Reality checks on hit rates: BindCraft 10–100% (published), a controlled RFdiffusion study that mostly failed at five designs per target, and the ~0.5% pass rate of the AlphaFold-DB-style filter on one proteome-scale viral screen.

### 1.4 Planning artefacts created (all in `challenges/02-tnfa/notes/`)

- `master-plan.md` — phases 0–5, environment table, stop rules, scope decision (Challenge 2 only).
- `research-phase-0.md` — the failure analysis of both prior attempts, the tool landscape, the local measurements, the three candidate hotspot sets, and the **pre-registered Experiment 01 specification**.
- `gpu-box-setup.md` — the checklist for the user's RTX 5070 Ti PC (WSL2 route; driver ≥ 570; PyTorch cu128+; what fits 16 GB and what does not).

### 1.5 The rules fixed before any submission

1. **Full trimer only** (never a partial target): partial targets let binders fill the omitted protomer.
2. **Hotspot span ≤ ~15 Å** (from the reviewed entry's C1 success and C2 failure).
3. **A pre-registered pass bar** for X1: a design "docks" if `ipSAE ≥ 0.6` AND `pDockQ2 ≥ 0.23` AND at least ~100 atom contacts under 5 Å; a hotspot set "works" if at least two designs dock and the rate is at least 1%.
4. **A loophole check** on every candidate (no atoms where the third protomer sits).
5. **Stop rules**: no docks anywhere → stop and change the setup, do not rerun.

---

## 2. Phase 1 — environment and tooling

### 2.1 Tamarind Bio — the agent route

- Endpoint used: `POST https://app.tamarind.bio/api/agent/provision` with an empty body. Response 201: tier `agent-trial`, limits `{jobs: 10, allowedTools: all, expiresInDays: 30}`, plus a **claim URL** for a human.
- No email, no password, no CAPTCHA, no card. Tamarind documents this for agents at `/auth.md`.
- The API key is stored at `~/.config/tamarind/api_key` (mode 600, outside every repository). All later calls carry the header `x-api-key`.
- Free actions: `POST /api/validate-job` (dry-run, no job consumed), tool catalog (`GET /tools.json`), schemas (`GET /api/tools/{name}/schema`), status (`POST /api/jobs/search`), file upload (`PUT /api/upload/{filename}`), results (`POST /api/result`).
- Tool catalog: **378 tools**, including `boltzgen`, `boltz` (Boltz-2), `rfdiffusion3`, `rfdiffusion`, `ipsae`, `proteinmpnn`, `bindcraft2`, `freebindcraft`.

### 2.2 Local Mac — the MPS route (parallel, non-blocking)

- The official foundry README documents an Apple-Silicon fork. Installed: `uv venv --python 3.12 ~/.venvs/rfd3-mac`, then torch + `rc-foundry[all] @ git+https://github.com/fnachon/foundry.git`.
- Result of the import check: **`FOUNDRY OK, torch 2.14.1, mps True`** — RFD3/MPNN inference on the M3 Pro is plausible.
- The checkpoint download is blocked: `files.ipd.uw.edu` accepts TCP but never completes the TLS handshake from this network (five attempts, one stalled the installer for 17 minutes). A retry loop (every 10 minutes, up to 8 hours) runs in the background. The exact checkpoint URL: `https://files.ipd.uw.edu/pub/rfd3/rfd3_foundry_2025_12_01_remapped.ckpt`, expected local name `rfd3_latest.ckpt`.

### 2.3 The user's GPU PC (later)

- Decided: RTX 5070 Ti, 16 GB, Blackwell (sm_120), WSL2 Ubuntu.
- Fits 16 GB: RFdiffusion3 (~3 GB minimum), Boltz-2, ColabFold, ProteinMPNN, all CPU scoring.
- Does not fit: **BoltzGen** (community-documented floor 24 GB) and the original RFdiffusion (cu118-era torch pin, no Blackwell kernels).

---

## 3. Phase 2 — X1: the groove docking benchmark

### 3.1 Building the hotspot sets

- Contacts were recomputed here from `3WD5.pdb1`, model 1: chains A (TNF) plus H and L (Fab). Atom-pair contacts ≤ 4.5 Å, counted per TNF residue. Top contact list: Q67 (59 pairs), K65 (31), E146 (24), E23 (21), A145 (17), Q21 (16), Y141 (16), G66 (11), S147 (11), A111 (9), P113 (8), P20 (7), E110 (7), D140 (7), F144 (5), Y115 (2), D143 (1).
- Candidates were kept only if **conserved in mouse** (from the recomputed epitope table) AND **exposed** (rSASA ≥ 0.28) AND with at least 7 contact pairs: Q67, K65, E23, A145, Q21, S147, P113, E110.
- A tower of trios was searched: maximum total antibody contacts inside a span ladder (15.5 Å → 17.5 → 20 → 22.5 Å), preferring trios that span **two protomers**. First rung that produced a solution: **15.5 Å**.
- **S1 = {A65 LYS, A67 GLN, C75 LEU}** — total weight 107 contact pairs, maximum CA–CA span **12.7 Å**. This is the classic 60s-loop / neighbour-loop pair of the antibody epitope.
- **S2 = {A103 ARG, B103 ARG, B112 LYS}** — the switch trio (spans 8.7–12.9 Å).
- **S3 = no binding site** — the diagnostic floor measurement.

### 3.2 Payloads (validated for free, then submitted)

Common settings for all three jobs (`type: boltzgen`):

```json
{"binderType": "protein", "targetFile": "1TNF.pdb", "targetChains": ["A","B","C"],
 "scaffold": "default", "lengthRange": "70,95", "numDesigns": 50, "budget": 50,
 "runIpsae": true, "filterBindingSite": false, "skipRefolding": false,
 "saveIntermediates": false, "claude_inference_optimization": "off"}
```

Per-job difference: `bindingSite` = `{"A": "65 67", "C": "75"}` (S1) · `{"A": "103", "B": "103 112"}` (S2) · absent (S3).

Deliberate deviations from the first proposal, each with a reason:
- **Post-binding-site filter OFF** — the site stays soft conditioning, and site adherence is measured locally, so the whole pool counts.
- **Refold ON** — the Boltz-2 refold supplies the interface metrics (ipTM, PAE, ipSAE, pDockQ2) that the analysis needs.
- **budget 50 = numDesigns 50** — no design is dropped from the delivered set for diversity reasons.

### 3.3 Submission and runtime

| Job | Created (server) | Started | Completed | Runtime |
|---|---|---|---|---|
| `c2-x1-s1-antibody-epitope` | 11:45:36 | 11:45:56 | 12:46:38 | ~61 min |
| `c2-x1-s2-cation-switch` | 11:45:41 | 11:45:58 | 12:46:16 | ~60 min |
| `c2-x1-s3-diagnostic` | 11:45:47 | 11:46:04 | 12:46:54 | ~61 min |

All three were validated first (`{"valid": true, "normalized": {...}}`), then submitted (`submitted to queue`), and confirmed with `POST /api/jobs/search`.

A watcher (`tamarind-watch.py`) polled every 5 minutes and downloaded the three result zips (50.7 / 50.5 / 50.7 MB) to `data/tamarind/x1/`. Note: the Mac slept between 14:36 and 18:01 local, and the watcher resumed exactly when the machine woke.

### 3.4 Results (all three sets, from the extracted CSVs)

| Metric | S1 antibody-epitope | S2 cation-switch | S3 diagnostic |
|---|---|---|---|
| Designs delivered | 50 | 49 | 50 |
| Best `design_to_target_iptm` | **0.356** | 0.220 | 0.326 |
| Median `design_to_target_iptm` | 0.143 | 0.142 | 0.143 |
| Best `design_to_target_ipsae` | 0.005 | 0.000 | 0.004 |
| Best design `pDockQ2` (all pairs) | 0.000 | 0.000 | 0.000 |
| Designs passing the pre-registered bar | **0** | **0** | **0** |
| Binder folds alone (`design_ptm`) | 0.76–0.80 | 0.75–0.78 | 0.76–0.81 |
| Trimer-internal pairs (`ipSAE_AB/AC/BC`) | 0.30–0.44 | 0.30–0.44 | 0.30–0.44 |

Geometry check on the top designs (refolded complexes, binder = chain D):

| Design | Atoms within 4 Å of the trimer | Closest atom pair |
|---|---|---|
| S1 `design_spec_18` (best ipTM 0.356) | 162 / 639 | 1.4 Å |
| S1 `design_spec_20` | 124 / 693 | 2.2 Å |
| S1 `design_spec_10` | 115 / 557 | 1.6 Å |
| S2 top design | 135 / 680 | 2.3 Å |
| S3 top design | 58 / 688 | 2.1 Å |

**Interpretation.** The designs fold (pTM ≈ 0.8 alone) and press against the trimer surface (some atoms overlap it), but the model gives the design–target interface almost no confidence (PAE 14–21 Å, ipSAE ≈ 0). "Touching, not docking." A credible interface looks like the reviewed entry's EGFR result (ipTM 0.95). The trimer itself is predicted normally (its own A–B, A–C, B–C interfaces score 0.30–0.44).

**Conclusion (X1).** 0 of 150 designs dock. Even the no-hotspot diagnostic S3 fails, so the **site choice is not the limiter**. Stop rule 1 activated: no further spend on this setup; the next lever is a changed generator or a changed target representation.

---

## 4. Phase 3 — X2: the RFdiffusion3 generator probe (in flight)

### 4.1 Rationale

Option A from `x1-results.md`: change the generator (the one lever that does not need new hardware). RFdiffusion3 is the all-atom successor of RFdiffusion (Butcher et al., 2025, ~1/10 the compute) and is live on Tamarind.

### 4.2 Schema reconnaissance before submitting

Fields read from `GET /api/tools/rfdiffusion3/schema`: `task` (`protein-binder-design`), `pdbFile`, `targetChains`, `hotspots` (keyed by chain, e.g. `{"A": "20 21 23"}`), `binderLength` ("min,max"), `numDesigns`, `diffusionBatchSize` (designs per GPU pass; each batch shares one sampled binder length), `nonLoopy`, `stepScale` (1.5 default), `gammaZero` (0.6 default), `runDesignability`, `useSolubleMpnn`, `claude_inference_optimization`.

Critical find: **`runDesignability`'s refold step is "single target chain only"** — our target is a trimer, so that option stays OFF. Candidates will be scored by our own Boltz-2 co-folds instead.

### 4.3 Submission and the quota discovery

- Payload (S1): `{"task": "protein-binder-design", "pdbFile": "1TNF.pdb", "targetChains": ["A","B","C"], "hotspots": {"A": "65 67", "C": "75"}, "binderLength": "70,95", "numDesigns": 48, "diffusionBatchSize": 6, "nonLoopy": true, "stepScale": 1.5, "gammaZero": 0.6, "runDesignability": false, "claude_inference_optimization": "off"}`.
- `c2-x2-rfd3-s1-groove`: validated, submitted 16:20:00 server ("batch submitted to queue"). The submission arrived as a **batch with six children** (`…-0` … `…-5`), all `Running`.
- `c2-x2-rfd3-s2-switch`: **rejected** with HTTP 400:

```json
{"error":"Monthly job limit exceeded. You have 9 jobs this month and are trying to submit 6 more, but your limit is 10.",
 "code":"monthly_limit_exceeded","quota":{"used":9,"limit":10,"remaining":1}}
```

- **Why 6 jobs:** RFdiffusion3 bills **per diffusion batch** — 48 designs at the tool's internal GPU batch of 8 = 6 children = **6 jobs**. X1's three BoltzGen runs cost one job each (3 total). 3 + 6 = 9 of 10.
- Consequence: the monthly quota now has **1 job left**, and the modifiers reset on **1 November** — after the C2 deadline (18 October, 23:59 AoE). The last job is reserved for **one Boltz-2 co-fold** of the best X2 candidate.

### 4.4 Result — COMPLETE: RFdiffusion3 places the binders at the site

- The batch finished (all 6 children `Complete`, parent `Complete`) and the watcher downloaded a 14.8 MB result zip.
- **72 complexes** (6 children × 12; contigs sampled 73–94 aa, median 84).
- **72 of 72 designs touch the 60s loop** (residues 65/67 in original numbering).
- **58 of 72 contact both the 60s loop and the neighbour-loop (75) — and always across two protomers.** That is the antibody groove, occupied exactly as specified.
- Interface size: median 70 binder atoms within 4 Å of the target (maximum 135). Helix fraction median 0.75.
- Caveat: 27 designs show clash-level contacts (minimum heavy-atom distance below 2.0 Å; the worst is 0.34 Å — physically impossible). RFD3 emits raw diffusion geometry; filter on minimum distance before ranking.
- Output layout note: **binder = chain A; the three target protomers are renumbered 1–152** (1TNF 6–157) as chains B/C/D. Full table: `data/tamarind/x2/x2-triage.csv`; analysis in `x2-results.md`.

### 4.5 The last job — the decisive co-fold

`c2-x2-boltz-fold-best`, submitted 16:30 server time: a Boltz-2 co-fold of the cleanest site-spanning design (`groove-1_0_model_1`, 73 aa, minimum distance 2.27 Å, 108 interface atoms, spans protomers B and D), 4 chains, 5 samples, IPSAE on. A second watcher (`tamarind-watch-x2fold.py`, 60 s) downloaded it (12.7 MB) at 18:33 local.

**Result — PASS (qualified).** Per-model binder-interface scores (chain A = binder, B/C/D = target):

| Model | ipTM | ipSAE A–B | ipSAE A–B min | pDockQ2 A–B | Reading |
|---|---|---|---|---|---|
| 0 | 0.944 | 0.527 | 0.342 | 0.132 | moderate |
| 1 | 0.962 | **0.804** | **0.606** | **0.236** | **passes the bar** |
| 2 | 0.939 | 0.378 | 0.259 | 0.000 | partial |
| 3 | 0.847 | 0.000 | 0.000 | 0.047 | interface lost |
| 4 | 0.839 | 0.000 | 0.000 | 0.055 | interface lost |

One sample passes the pre-registered criteria (ipSAE ≥ 0.6 and pDockQ2 ≥ 0.23), one is near, one partial, two fail — seed variance is the caveat, and single-design evidence. X1's 150 designs peaked at ipSAE 0.005 and pDockQ2 0.000, so this is a different regime. The monthly quota is now fully spent (10/10; resets 1 November). Next: repeat folds for 3–5 more designs (PC or next month), then the switch layer and the mouse check. See `x2-results.md`.

---

## 5. Lessons learned (in order of importance)

1. **Check a tool's quota semantics before a large submission** — RFdiffusion3 bills ≈ 1 job per 8 designs; BoltzGen bills 1 job per run. The 6-job surprise cost the second probe.
2. **A partial target hides failures** — always design against the full trimer, and run the loophole check.
3. **The site is not the limiter on TNF-α** — a no-hotspot diagnostic that performs the same as targeted sets proves it.
4. **"Touching" is not "docking"** — contact counts and buried area can look fine while the interface confidence is zero. Score with ipSAE/pDockQ2, never with contact counts alone.
5. **Pre-registered criteria save time** — the X1 negative was decided in minutes because the bar was set before the spend.
6. **Watch the machine state** — a sleeping laptop stalls background watchers; the resume worked, but the log looked stale for hours.
7. **Free tier is a probe budget, not a campaign budget** — 10 jobs/month cannot carry a design campaign; the local GPU is the campaign path.

---

## 6. Artifact index

| Path | Content |
|---|---|
| `challenges/02-tnfa/notes/master-plan.md` | Phases 0–5, environment table, stop rules, scope |
| `challenges/02-tnfa/notes/research-phase-0.md` | Failure analysis, tool landscape, hotspot sets, X1 pre-registration |
| `challenges/02-tnfa/notes/tamarind-job-plan.md` | Agent flow, quota table, X1 + X2 submission records |
| `challenges/02-tnfa/notes/x1-results.md` · `x2-results.md` | Per-experiment records: numbers, interpretation, options |
| `challenges/02-tnfa/notes/x1-tamarind-jobs.json` · `x2-tamarind-jobs.json` · `x2-fold-job.json` | Verbatim payloads and API responses |
| `challenges/02-tnfa/notes/figures/c2-pipeline-steps.svg` · `.png` | The experiment-log diagram |
| `challenges/02-tnfa/notes/pc-handoff.md` | Pointer and archive record for the PC package |
| `challenges/02-tnfa/notes/gpu-box-setup.md` | RTX 5070 Ti / WSL2 checklist |
| `challenges/02-tnfa/data/epitope-analysis/` | 1TNF, 3WD5, 4G3Y, UniProt records, recomputed epitope tables, S1 choice |
| `challenges/02-tnfa/data/tamarind/x1/` | Three result zips + extracted metrics + `x1-triage.csv` (149 designs) |
| `challenges/02-tnfa/data/tamarind/x2/` | RFD3 zip, fold zip, `x2-triage.csv` (72 designs with sequences), `x2-fold-metrics.csv` |
| `challenges/02-tnfa/handoff/` | The PC package: designs, sequences, Boltz YAMLs, records, notes, scripts, archive + `SHA256SUMS` |
| `~/.hermes/cache/scratch/` | Watchers, Tamarind catalog + schemas, saved API guide |
| `docs/competition-notes/` | Beginner explainers (01–07), repo review 03, figures |

## 7. Open items

- **Claim URL** for the user (moves the jobs into their Tamarind dashboard; removes the key's 30-day expiry).
- **MPS checkpoint**: the retry loop ended; `files.ipd.uw.edu` stayed unreachable from this network. The Mac generation route is still blocked.
- **PC route**: the handoff package is built and verified (45 files, 44 checksums OK, sha256 `28ee9408…90dfd`). Work starts at `handoff/README.md` W0.
- **Switch layer, mouse check, controls**: not started. They need the PC (or Tamarind after 1 November).
- **Free cysteines**: every shortlist sequence carries at least one. Record them as liabilities for the write-up.

## 8. Timeline (15 October 2026)

| Local (CEST) | Server (Tamarind) | Event |
|---|---|---|
| 12:00 | — | Phase 0 starts: the third entry is cloned and reviewed |
| 13:45 | 11:45 | X1 submitted: three BoltzGen jobs (S1, S2, S3) |
| 14:46 | 12:46 | X1 complete on the server; the Mac sleeps 14:36–18:01 |
| 18:01–18:15 | — | X1 zips downloaded (50 MB each); triage: 0 of 150 dock |
| 18:16–18:20 | — | `x1-results.md`, stop rule 1, Option A chosen |
| 18:20 | 16:20 | X2 submitted: RFdiffusion3 batch, 6 children; the S2 twin is quota-rejected |
| 18:26 | 16:26 | X2 batch aggregating |
| 18:27 | — | X2 zip downloaded (14.8 MB); triage: 58 of 72 in the groove |
| 18:30 | 16:30 | The decisive co-fold submitted (the 10th and last job of the month) |
| 18:33 | 16:33 | Co-fold complete; downloaded (12.7 MB); 1 of 5 samples passes the bar |
| 18:35–19:25 | — | Documentation set, diagram, triage scripts, the PC handoff package |
