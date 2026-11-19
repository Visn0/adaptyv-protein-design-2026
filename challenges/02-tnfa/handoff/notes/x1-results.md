# X1 results — the groove docking benchmark (final)

*Recorded 15 Oct 2026. Experiment `c2-x1` — three BoltzGen design runs on Tamarind (50 designs each), target 1TNF trimer A+B+C, pre-registered in `research-phase-0.md`. Raw results: `data/tamarind/x1/` (extracted zips + metrics CSVs). Job IDs and payloads: `x1-tamarind-jobs.json`.*

## Headline

**Zero of 150 designs dock. All three hotspot sets fail. X1 is a measured, pre-registered negative — and it replicates both public attempts.**

## The numbers

| | S1 antibody-epitope | S2 cation-switch | S3 diagnostic (no site) |
|---|---|---|---|
| Designs delivered | 50 | 49 | 50 |
| Best `design_to_target_ipTM` | 0.356 | 0.220 | 0.326 |
| Median `design_to_target_ipTM` | 0.143 | 0.142 | 0.143 |
| Best `design_to_target_ipSAE` | 0.005 | 0.000 | 0.004 |
| Design–target `pDockQ2` (all pairs) | 0.000 | 0.000 | 0.000 |
| Designs passing the pre-registered bar (ipSAE ≥0.6 ∧ pDockQ2 ≥0.23) | **0** | **0** | **0** |
| Designs fold alone (design_pTM) | ~0.76–0.80 | ~0.75–0.78 | ~0.76–0.81 |

Geometry check on the top designs (refolded complexes, chain D = binder):
- S1 `design_spec_18` (best ipTM): 162 of 639 binder atoms within 4 Å of the trimer, closest atom pair 1.4 Å.
- S2 top: 135/680 atoms within 4 Å. S3 top: 58/688 within 4 Å.

**Reading:** the top designs are not ignored by the model — they press against the trimer surface (some even overlap it) — but the model assigns essentially zero confidence to that interface (design→target ipSAE ≈ 0, ipTM ≤ 0.36, PAE 14–21 Å). "Touching, not docking." A credible docking event looks like the reviewed entry's EGFR result (ipTM 0.95). Nothing here is close.

Also observable: targets-side pairs (A–B, A–C, B–C) score as real interfaces (ipSAE 0.30–0.44) — the trimer itself is predicted fine. The failure is specifically the design→target interface.

## What this means

1. The hotspot-set question is answered: **the site choice is not the limiter.** The no-hotspot S3 run does no better than S1/S2. Same conclusion the reviewed entry reached (their diagnostic: ipTM 0.45).
2. Three independent attempts, three tool stacks, one verdict: **the TNF-α groove resists current open-tool docking at small-to-medium scale** (RFdiffusion, 48 seqs: 0 docked; BoltzGen free-tier, 5 runs: ipTM ≤0.46; our BoltzGen, 150 designs: ipTM ≤0.36, ipSAE ≈0).
3. Per the pre-registered stop rule (`master-plan.md`, stop rule 1): **stop the C2 generation track on this setup before any further spend.** The next lever is a changed generator (RFdiffusion3) or a changed target representation — not a rerun.

## Options from here (user decision)

| Option | Cost | Note |
|---|---|---|
| A. RFdiffusion3 probe on Tamarind | 1–2 jobs of the 7 left | RFD3 is live on Tamarind (`rfdiffusion3` tool, has hotspots + binderLength + internal MPNN/AF designability check). Cheapest generator change; results within a day. |
| B. RFdiffusion3 on local hardware | free-ish | MPS route: checkpoint download still blocked (files.ipd.uw.edu); WSL2 PC route: needs the setup day. |
| C. Change target representation | engineering time | e.g. design against a trimmed local groove patch, or a different epitope framing; keeps BoltzGen. |
| D. Park C2 generation | 0 jobs | Keep the 7 jobs for validation folds if a future run produces dockers. Deadline (Oct 18 23:59 AoE) makes a full campaign unlikely either way. |

## Status of the job budget

3 of 10 jobs used. 7 remain (no expiry issue; the agent key works for 30 days unless claimed).
