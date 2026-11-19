# Tamarind Bio — agent flow, job budget, and how we spend it

Written 15 Oct 2026. Status: **key provisioned, nothing submitted yet** (user asked to review the budget first).

## The agent flow (verified today)

- Tamarind publishes an agent provisioning route: `POST /api/agent/provision` — no signup, no email, no card. Response: an API key (tier `agent-trial`), a 30-day validity window, and a **claim URL**.
- The key is saved at `~/.config/tamarind/api_key` (outside the repo, chmod 600). One key = one account = one quota. Never provision a second key.
- With the key: `submit-job` (spends 1 job), `submit-batch` (up to 100 jobs in one call, each row spends a job), `validate-job` (**free**), job list, results, file upload/download. All scriptable in Python — the whole loop runs without the user.
- Without claiming: pipeline endpoints (`submit-pipeline`, `run-pipeline`, `virtual-screening`) return 403. We do not need them.
- The user should open the claim URL once (given in chat): it moves the jobs into the user's own dashboard and removes the 30-day expiry. Nothing else changes.

## Quota and limits (free tier)

| Fact | Value |
|---|---|
| Jobs per month | **10** (all 378 tools share the quota) |
| Cost of one job | 1 job per run for most tools — **but billing is per sub-unit for some tools.** Observed 15 Oct: `rfdiffusion3` billed a 48-design run as **6 jobs** (≈1 job per 8 designs, the internal GPU batch), and the submission arrived as a Tamarind *batch*. Check the tool's batch semantics before large submissions. |
| Free actions | validate-job, schema browsing, job status, downloads, uploads |
| Runtime limit per job | enforced on free tier (exact value not published; the reviewed entry's runs at 50–110 min completed fine) |
| Batch | 1 call can submit up to 100 jobs; each child still costs 1 job |
| Failed job | unclear whether it refunds; assume it does not |

## What one job returns (the two tools we care about)

| Tool | One job gives | Notes |
|---|---|---|
| `boltzgen` (binder design) | N designed complexes + per-design metrics; `runIpsae` is ON by default (IPSAE computed for every design); optional binding-site filter, extra filters, refold step | `numDesigns` default 10; the reviewed entry's single Tamarind run returned ~96 designs in 50–110 min. Authors recommend ~60,000 designs for a production campaign — not reachable on the free tier. |
| `boltz` (Boltz-2 fold) | One complex, 5 samples, with PAE + ipsae metrics (runIpsae default on) | This is our independent validation fold: binder + full trimer, one job per complex. |

## Proposed allocation — Experiment 01 (10 of 10 jobs)

| # | Job | Tool | Purpose |
|---|---|---|---|
| 1–3 | Design runs for hotspot sets S1, S2, S3 | boltzgen, numDesigns ≈ 50, binding-site filter on, runIpsae on | measure the docking rate per set — the question both prior entries could not answer |
| 4 | Positive control | boltz: 3WD5 adalimumab Fab + TNF | confirm our scorer recovers a real interface |
| 5 | Negative control | boltz: best binder + shuffled sequence | floor of the score distribution |
| 6–10 | Validation folds | boltz: top 1–2 designs per set + full trimer (human), one per job | independent ipSAE/pDockQ2 scoring, loophole check |

**Alternative if the Mac MPS route proves fast enough:** generation moves to the Mac (free), and all 10 Tamarind jobs convert to validation folds + controls. Decision point: after the MPS smoke test.

## X1 — SUBMITTED (15 Oct 2026, 11:45 CEST)

Three BoltzGen jobs submitted, all validated first (free) and confirmed in queue. 3 of 10 monthly jobs spent.

| Job | Binding site | Note |
|---|---|---|
| `c2-x1-s1-antibody-epitope` | `{"A": "65 67", "C": "75"}` | max antibody contacts within a 12.7 Å span: adalimumab primary-protomer K65/Q67 + neighbour-protomer L75 (the 60s/70s groove loop pair) |
| `c2-x1-s2-cation-switch` | `{"A": "103", "B": "103 112"}` | the cation trio (spans 8.7–12.9 Å) |
| `c2-x1-s3-diagnostic` | none | floor measurement |

Common settings: target `1TNF.pdb` chains A+B+C; de-novo `protein` binders 70–95 aa; `numDesigns` 50, `budget` 50; IPSAE on; Boltz-2 refold on; `claude_inference_optimization` off. **Deviation from the proposal table above: the post-binding-site filter is OFF** — the binding site is soft conditioning only, and site adherence is measured locally, so the full pool is kept for the rate measurement.

Payloads + full API responses: `x1-tamarind-jobs.json`. Status at 11:45:47: all three `In Queue` → later `Complete` (server 12:46; about 60 min each). Results downloaded to `../data/tamarind/x1/` (three zips + extracted metrics). **Outcome: 0/150 designs dock — full analysis and the stop-rule decision in `x1-results.md`.**

## X2 — RFdiffusion3 generator probe (submitted 15 Oct 16:20 CEST)

Option A from `x1-results.md`, executed after the X1 negative. Two probes were prepared; **one was submitted, one was rejected by the quota**:

| Job | Hotspots | Status |
|---|---|---|
| `c2-x2-rfd3-s1-groove` | `{"A": "65 67", "C": "75"}` | **In Queue** (submitted 16:20; arrived as a *batch*; billed **6 jobs**) |
| `c2-x2-rfd3-s2-switch` | `{"A": "103", "B": "103 112"}` | **Rejected**: `monthly_limit_exceeded` (9 of 10 used, 6 requested) — NOT submitted |

Settings: same target `1TNF.pdb` trimer; de-novo binders 70–95 aa; 48 designs; `diffusionBatchSize` 6; `nonLoopy` on; `stepScale` 1.5 and `gammaZero` 0.6 (defaults); **`runDesignability` off** (its refold step is "single target chain only" — our target is a trimer; we co-fold candidates ourselves with Boltz-2 instead).

**Quota after this: 9 of 10 used, 1 left this month.** The last job is reserved for ONE Boltz-2 co-fold of the best X2 candidate (with PAE + IPSAE), if local triage finds one worth folding.

Watcher: `tamarind-watch-x2.py` → downloads to `../data/tamarind/x2/`.

## Gate before submitting

1. `validate-job` passes for all three design payloads (free).
2. The user approves the allocation (each job is 10% of the monthly quota).

## Mac MPS route (parallel track)

- The official foundry README documents an Apple-Silicon fork: RFD3, RF3 and ProteinMPNN all run on MPS (float32, inference only).
- Install state 15 Oct 12:50: torch 2.14.1 + the foundry fork are installed at `~/.venvs/rfd3-mac`; the import check passed (`mps True`). The RFD3 checkpoint download from `files.ipd.uw.edu` **fails from this network** — TCP connects but the TLS handshake times out (two attempts, one stalled the installer). A background retry loop runs every 10 minutes for up to 8 h; a mirror will be sought if it keeps failing. Generation fallback order stays: RTX 5070 Ti (WSL2), then Tamarind.
- Next: a tiny scaffold smoke test to measure per-design speed on the M3 Pro (once a checkpoint lands).
