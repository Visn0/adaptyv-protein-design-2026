# Challenge 2 (TNF-alpha) — master plan

Created 15 Oct 2026. Supersedes the older `plan.md` for the execution track (that file stays as the original path description).

**Goal.** Produce a defensible Challenge 2 entry (a conditional binder: bind human TNF-alpha at pH 7.4, release at pH 6.0, cross-react with mouse), built with our own tools, with every claim either measured or clearly labelled as a hypothesis. If a good entry cannot fit the deadline, the fallback is a calibrated experiment set that transfers directly to Challenge 3 and later work.

**Deadline (fixed):** Sunday **Oct 18, 23:59 AoE** — about 3.5 days from this plan's date. All phases below carry a "fits C2?" tag.

---

## What already exists (no new work)

- The workbench `~/Projects/protein-design-poc`: `pdt` CLI, experiment specs and runner, vendored `binderkit` tools, reports + web app; the two study-repo baselines replay exactly and are pinned by tests.
- Local analysis assets for C2: `challenges/02-tnfa/data/epitope-analysis/` (1TNF + antibody complexes, the third entry's epitope tables recomputed on this machine, our switch-anchor numbers).
- The international picture: three public entries reviewed (`~/Projects/protein-design-competition-report.md` + `repo-review-03-abdulrahman-neamah.md`).

## Phase 0 — Research and review (this turn, DONE)

Outputs: repo review 03; `research-phase-0.md` (findings, hotspot sets, scoring bands, failure analysis); confirmed local numbers (cation trio, mouse classes, acid neighbours).

## Phase 1 — Experiment 01: "groove docking benchmark" (next; spec in the research digest)

The purpose: measure the **docking rate** of a chosen generator against the **full trimer** at three hotspot sets, with pre-registered pass criteria and two controls. This is the place where both prior C2 entries died, so it is measured first, not assumed.

- **Status 15 Oct 2026 — X1 COMPLETE, NEGATIVE:** three BoltzGen runs delivered 150 designs; **0 dock** (best design→target ipTM 0.36, ipSAE ≈0; touch the surface but with zero interface confidence). Even the no-hotspot diagnostic (S3) fails → the site is not the limiter. Stop rule 1 activated: no further spend on this setup; next lever = generator or target-representation change. Full record: `x1-results.md`. Jobs: 3 of 10 used.
- **X2 (generator probe) — COMPLETE, ROUTE LIVE:** RFdiffusion3 at S1 placed **58 of 72 designs in the antibody groove spanning two protomers** (72/72 touch the 60s loop). The independent Boltz-2 co-fold of the cleanest design **passed the pre-registered bar in 1 of 5 samples** (ipSAE 0.804, ipSAE_min 0.606, pDockQ2 0.236; one near-pass, one partial, two failures — seed variance is the caveat). X1 comparison: 150 designs, best ipSAE 0.005. Quota fully spent (10/10; resets 1 Nov). Next: more folds for 3–5 designs (PC route), then switch layer + mouse check. See `x2-results.md`. The PC handoff package is built and verified: `handoff/README.md`.
- Output: a measured pass rate per hotspot set + the winning (set, generator) pair + calibrated thresholds for the campaign.

## Phase 2 — Campaign (scale generation on the winning setup)

- Generate at campaign scale: target N = 200–1000 backbones (prior pass rates: 1–10%; the failure analysis says volume is the deciding variable).
- Score everything locally (ipSAE, pDockQ2, contacts, clash checks) in one reproducible pass.
- Fits C2? Only in a reduced form (N ≈ 100–300). Full scale fits Challenge 3 timelines better.

## Phase 3 — Switch layer (only on designs that dock)

- Place the switch: binder histidines against the target cation trio (A103/B112/B103) with the acid-neighbour screening issue in mind (see digest).
- Build the switch motif geometrically, bias sequence design (ProteinMPNN logit bias), re-fold, re-score with the linkage scorer (PROPKA).
- Check the mouse chemistry classes on every switch site (A73-style trap: H in human, Y in mouse).
- Fits C2? Only as a stretch; Proton-PottsMPNN is a follow-on (its transitions stop at pH 5.8, below our window).

## Phase 4 — Selection and controls

- Pareto order (linkage score, ipSAE, switch-site count), diversity caps (≤2 designs per backbone).
- Build paired controls: same sequences with the switch residues reverted.
- Fits C2? Yes, compute-light (Python).

## Phase 5 — Submission and methods write-up

- Ranked CSV, methods text, risks section, honest limits.
- Pre-flight: novelty check per design (the platform scores it at upload).
- Fits C2? Only if Phases 1–3 produce candidates by Oct 18.

## Environment and services (what to install, what to buy)

**Python-only, local, available now (no action):** all analysis, scoring scripts (ipSAE is a single-file Python program), PROPKA, our workbench, the whole Phase 0 report set. The C2 venv already has numpy, pandas, biopython, propka, requests.

**Local GPU box — primary route (decided 15 Oct 2026):** the user's second PC, **NVIDIA RTX 5070 Ti (16 GB, Blackwell)**. It fits the recommended pipeline: RFdiffusion3 (documented minimum ~3 GB GPU memory), Boltz-2 (co-folding our ~600-residue complexes), ColabFold, ProteinMPNN, plus all CPU scoring. Requirement: NVIDIA driver ≥570 (latest preferred), CUDA toolkit 12.8+, PyTorch ≥2.7 with cu128+ wheels — Blackwell (sm_120) has no kernels in older torch builds, so never debug around an old pin. Checklist: `gpu-box-setup.md`.

**Does not fit the local box:**

- **BoltzGen** — community-documented minimum 24 GB VRAM; 16 GB is below it. BoltzGen stays a Tamarind route (or is skipped).
- **Original RFdiffusion** — legacy cu118-era torch stack, no Blackwell kernels ("no kernel image" failures). Not used; RFdiffusion3 replaces it.

**Fallback routes:**

| Route | What it is | Cost | Notes |
|---|---|---|---|
| Tamarind Bio free tier | SaaS runner (BoltzGen, Boltz-2, RFdiffusion + 200 tools) | $0, **10 jobs/month** | Gate fallback for Experiment 01; the only route for BoltzGen. |
| Competition Modal credits | The FAQ states Claude and Modal credits are provided for this competition | Included | **Verify how to claim** (FAQ 15 / Proteinbase). Optional; useful for the Phase 2 campaign. |
| Rented cloud GPU (RunPod, Lambda) | Raw CUDA box | approx. $0.3–1.0 per GPU-hour | Only if the local box fails the gate. |

**Not viable on this Mac:** the diffusion generators (BoltzGen, RFdiffusion/RFD3, BindCraft) are CUDA-first; Apple-Silicon (MPS) support is not realistic for these. BindCraft additionally needs a PyRosetta licence — avoid unless nothing else works.

**Binaries:** none new. Chrome, ffmpeg and uv already exist on this machine for the report/movie tooling.

## Stop rules (agreed before spending anything)

1. If Experiment 01 shows **no docks in any hotspot set**, stop the C2 generation track and re-plan (target representation or generator change is the next lever).
2. If per-set pass rate < 1% at pilot scale, do not start the campaign until the generator or target setup changes.
3. Budget caps: Tamarind free jobs ≤ 4 for Experiment 01; any paid compute needs explicit approval before spending.
4. Every candidate passes the **full-trimer loophole check** (no atoms where the third protomer sits) or it is discarded, whatever its score.
5. **GPU-box gate:** all smoke tests must pass on the PC by the evening of **Oct 16**. If not, Experiment 01 starts on the Tamarind fallback (≤4 jobs) while setup continues.

## Scope decision (locked 15 Oct 2026)

**Challenge 2 only.** Fixed sequence: Experiment 01 on the GPU box (gate: smoke tests by Oct 16 evening) → reduced campaign (N ≈ 100–300) → selection + submission before **Oct 18, 23:59 AoE**. If Experiment 01 fails its stop rules, the fallback is the Tamarind pilot — not a new direction. Challenge 3 gets no work in this window.
