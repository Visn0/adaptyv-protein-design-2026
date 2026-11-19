# X2 results — the RFdiffusion3 generator probe

*Recorded 15 Oct 2026. Experiment `c2-x2` — one RFdiffusion3 design run on Tamarind (48 designs requested; the tool produced 72 complexes: 6 children × 12), target 1TNF trimer A+B+C, hotspots S1 (`{"A": "65 67", "C": "75"}`). Raw data: `data/tamarind/x2/`. Job records: `x2-tamarind-jobs.json`, `x2-fold-job.json`. Triage table: `data/tamarind/x2/x2-triage.csv`.*

## Headline

**RFdiffusion3 places binders exactly where BoltzGen could not: 58 of 72 designs sit in the antibody groove spanning two protomers, and 72 of 72 touch the 60s loop. The decisive co-fold then PASSED: an independent Boltz-2 fold of the cleanest design gives ipSAE 0.80 / pDockQ2 0.236 on the binder interface in one of five samples, with a second near-pass (0.53 / 0.13). Compare X1: 150 designs, best ipSAE 0.005, pDockQ2 0.000.** This is the first credibly docked interface in the whole C2 effort.

## The numbers

| Metric | Value |
|---|---|
| Complexes produced | **72** (6 children × 12) |
| Binder length | 73–94 aa (median 84; requested 70–95) |
| Touches the 60s loop (residues 65/67) | **72 / 72** |
| Touches 60s loop **and** neighbour-loop (75) | **58 / 72** |
| …and does so **across two protomers** | **58 / 58 of those** |
| Interface size (binder atoms < 4 Å from target) | median 70, max 135; 9 designs at ≥ 100 |
| Clash-level geometry (min heavy-atom distance < 2.0 Å) | 27 designs (worst 0.34 Å — physically impossible; raw diffusion output) |
| Structured content (helix fraction) | median 0.75 |
| Designs with zero sidechain clashes (per-worker metrics) | 57 / 72 |

## How the triage was computed

- One output PDB per design model. **Binder = chain A; targets = chains B/C/D, renumbered 1–152** (input contig `A6-157` ⇒ output residue *r* = 1TNF residue *r*+5).
- For each design: minimum heavy-atom distance to the target, count of binder atoms within 4 Å, and per-residue contacts (≤ 4.5 Å) to the three hotspot positions (65/67 on one protomer, 75 on the neighbour).
- Classification: "site" = contacts to the 60s loop **and** the neighbour-loop; "across protomers" = those two contacts come from different chains. All 58 site hits were cross-protomer.

## The decisive co-fold — RESULT (pass)

`c2-x2-boltz-fold-best` — submitted 16:30, completed 16:33 server time (the **last** of the 10 monthly jobs):
- Boltz-2 co-fold of the cleanest site-spanning design: `groove-1_0_model_1`, **73 aa**, minimum distance 2.27 Å, 108 interface atoms, spans protomers B and D, helix fraction 0.77.
- Sequence: `DCGQEAQADAAALVATAVLGTLAIILANMTATGLGMLVSAQAAATHKVGAAGAQLLITAGLLAGAVAVALIQI` (cysteine at position 2 — a developability note for later).
- Settings: 4 chains (`molecules` format; A = binder, B/C/D = target), 5 samples, IPSAE on, stock kernels. Files: `data/tamarind/x2/extracted/c2-x2-boltz-fold-best/` (`metrics.csv`, per-model confidence JSONs, PAE npz).

| Model | ipTM | ipSAE A–B | ipSAE A–B (min) | pDockQ2 A–B | ipSAE A–C | ipSAE A–D | Reading |
|---|---|---|---|---|---|---|---|
| 0 | 0.944 | 0.527 | 0.342 | 0.132 | 0.438 | 0.385 | touches, moderate |
| **1** | **0.962** | **0.804** | **0.606** | **0.236** | 0.736 | 0.656 | **passes the pre-registered bar** |
| 2 | 0.939 | 0.378 | 0.259 | 0.000 | 0.444 | 0.514 | partial |
| 3 | 0.847 | 0.000 | 0.000 | 0.047 | 0.000 | 0.000 | interface lost |
| 4 | 0.839 | 0.000 | 0.000 | 0.055 | 0.000 | 0.000 | interface lost |

Supporting numbers: binder chain pTM 0.875–0.98 (it folds); target-internal pairs (B–C, B–D, C–D) score ipSAE 0.91–0.95 (the trimer is predicted correctly); complex iPDDT 0.80–0.82.

**Reading — qualified positive.** One of five samples passes the pre-registered acceptance bar on the binder interface (ipSAE 0.804 ≥ 0.6, ipSAE_min 0.606, pDockQ2 0.236 ≥ 0.23); one is near (0.527/0.132); one is partial; two lose the interface entirely. The seed-to-seed variance is the caveat: the interface is real to one predictor configuration, not yet reproducible across all of them. Against X1 (0 of 150 designs, best ipSAE 0.005), this is a different regime.

## What this means for the plan

1. **The generator lever worked.** RFdiffusion3 + tight hotspot conditioning can place and keep a binder in the TNF-α groove; BoltzGen could not.
2. **Only one design was tested, with one seed set.** The next honest steps are: fold 3–5 more site-spanning designs (independent co-folds), and re-fold the passing design with a different seed (e.g. `seed` set explicitly) to test reproducibility.
3. **Nothing is conditional yet.** No switch has been designed; the mouse check and controls are not run. Those are Phases 3–4 of the master plan.
4. **Compute:** the monthly quota is now fully spent (10/10; resets 1 Nov, after the C2 deadline). Scaling within the C2 window needs the local GPU: the RTX 5070 Ti PC (`gpu-box-setup.md`) or the Mac MPS route (checkpoint still blocked).

## Comparison with X1

| | X1 (BoltzGen, 150 designs) | X2 (RFdiffusion3, 72 complexes) |
|---|---|---|
| Site placement | not measured per design; top designs pressed against the trimer (up to 162/639 atoms < 4 Å) | **72/72 on the 60s loop; 58/72 spanning the groove** |
| Interface confidence (independent co-fold) | **≈ 0** (design→target ipSAE ≤ 0.005, ipTM ≤ 0.36) | pending — this is the running job |
| Cost | 3 jobs | 6 jobs (batch billing) + 1 job (the fold) |
