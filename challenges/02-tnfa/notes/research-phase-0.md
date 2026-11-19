# Challenge 2 — Phase 0 research digest

Written 15 Oct 2026, with the plan (`master-plan.md`). Everything below is either measured on this machine, quoted from a public source, or labelled as an open item. Nothing is designed here; Experiment 01 is a measurement.

## 1. The failure analysis (why this research exists)

Both published C2 attempts failed at the same step: **nothing docks to the receptor-binding groove of the TNF-alpha trimer**.

| Attempt | Setup | Result |
|---|---|---|
| Baseline repo (Nandini Gantayat) | RFdiffusion, 36 backbones → 12 passed coverage → 48 sequences folded | 0 docked; best ipTM 0.161; 0–12 atom contacts where a real interface shows 100–300 |
| Third entry (Abdulrahman Neamah) | BoltzGen via Tamarind free tier, 5 runs (trimer + dimer targets, 2 hotspot maps, 1 unrestricted diagnostic) | best ipTM 0.46 / ipSAE 0.11; dimer run invalid (binders filled the omitted protomer); no submission |
| Same third entry, same tool, EGFR | BoltzGen, 96 designs | 34 passed filters; lead design ipTM 0.95–0.96 both species |

Conclusion recorded by both authors: **undersampling and target difficulty, not the switch chemistry, are the bottleneck.** Any new attempt must measure docking first.

## 2. Tool landscape (checked Oct 2026)

| Tool | Role | Compute | Licence/route |
|---|---|---|---|
| BoltzGen (Stark et al., Oct 2025) | Binder generation, all-atom, one model for design + prediction | CUDA | MIT; Tamarind offers it |
| Boltz-2 | Structure + affinity, strong interface scores | CUDA | MIT; Tamarind offers it |
| RFdiffusion (2023) / RFdiffusion3 (Butcher et al., 2025) | Backbone generation; RFD3 is all-atom at ~1/10 the compute of RFD2 | CUDA | open; Tamarind lists RFdiffusion |
| ProteinMPNN | Sequence design for a fixed backbone (logit bias supported) | CUDA (small) | MIT |
| ColabFold / AlphaFold2 | Folding + PAE (needed by ipSAE) | CUDA | open |
| ipSAE (Dunbrack 2025) | Interface scoring from PAE; fixes ipTM weaknesses | CPU, Python | single-file script, free |
| PROPKA 3.5.1 | pKa prediction for the linkage scorer | CPU, Python | already installed in our venv |
| Proton-PottsMPNN (2026) | Protonation-aware sequence design | CUDA | open; transitions only reach pH 4.0–5.8 — below our 6.0–7.4 window |

**Scoring bands (pre-registered for all our runs):** ipSAE ≥0.8 very high · 0.7–0.8 confident · 0.6–0.7 low · <0.6 very low; AlphaFold DB's own filter is ipSAE ≥0.6 **and** pDockQ2 ≥0.23. Compare scores only at the same PAE cutoff (10 Å for Boltz-family outputs). ipSAE_min was the best single predictor of lab binding in a meta-analysis of 3,766 tested designs.

## 3. Local measurements (run this turn on 1TNF, this machine)

Files in `challenges/02-tnfa/data/epitope-analysis/`: `1TNF.pdb`, `3WD5.pdb1` (adalimumab), `4G3Y.pdb1` (infliximab), the third entry's recomputed `tnf_epitope_table.csv` and `tnf_patch_map.csv`.

New numbers, computed with our own script:

- **The candidate switch trio exists and survives mouse:** chain A/B/C all carry Arg103 and Lys112; human→mouse substitutions are **R103→K and K112→K** (charge class KEPT). The trap residue **A73 is HIS in human and TYR in mouse** (charge class LOST) — same conclusion as the baseline repo.
- **CA–CA spans (1TNF numbering):** A103–B103 10.7 Å · A103–B112 8.7 Å · B103–B112 12.9 Å. (Open item: the baseline repo quotes a 20.2 Å "max span" for its triad; our three pairs all sit under 13 Å. Reconcile before fixing the motif geometry.)
- **The trio sits in an electrostatically mixed neighbourhood:** the nearest acidic side chains are B104/Glu at 3.1 Å from A103, C104/Glu at 3.7 Å from B103, and B104/Glu at 4.7 Å from B112. Those glutamates are also the affinity anchors. Consequence for the switch layer: a binder histidine aimed at a cation must not be screened by these acids; the baseline repo recorded the same concern ("net charge within 8 Å of A103/B112 is 0/−2/−3"). The local 5 Å pair is strongly positive; the medium-range field is not.
- **The groove is polar** (third entry: E23 patch 3% apolar, Q67 15%): apolar-patch targeting failed for them; a design aimed here should expect a charged interface, which is fine for a salt-bridge-based switch but needs explicit polar contacts.

## 4. Candidate hotspot sets for Experiment 01 (decision input, not a design)

All sets measured on the **full trimer (chains A+B+C)**. Selection rule from the lessons: every set must fit within ~15 Å CA–CA span so a 70–95-residue binder can reach it; hotspots from adalimumab/infliximab contacts are cross-checked with the recomputed epitope table.

| Set | Members (1TNF numbering) | Rationale | Span |
|---|---|---|---|
| **S1 — antibody-derived** | K65, Q67, E110 (chain A) + L75 or Q88 (chain C) — final pick after polarity review of the epitope table | real drug epitope, conserved fraction high, functionally validated site | ≈15 Å |
| **S2 — switch-oriented** | A103, B112, B103 (the trio) + A104/B104 (acid anchors) as secondary | the only site with a documented charge-switch mechanism for the inverted direction | <13 Å |
| **S3 — diagnostic** | none (binding-site filter off) | floor measurement: what docks anywhere on the trimer | n/a |

## 5. Experiment 01 — draft spec (for approval, not yet run)

**Name:** `c2-x1-groove-docking-benchmark`
**Question:** with the planned generator, at what rate do designs dock to the receptor-binding groove of the full trimer — overall and per hotspot set?
**Setup:** target 1TNF chains A+B+C (never a partial target); binder length 70–95; one complex per scoring job; **generator: RFdiffusion3 on the local RTX 5070 Ti; co-folds by Boltz-2** (BoltzGen stays a Tamarind fallback — 16 GB is below its 24 GB floor).
**Runs (pilot scale):** sets S1, S2, S3; N = 40–60 designs per set on the local GPU (≈2–3 GPU-hours total).
**Scoring (all local, Python):** per design — ipSAE (10 Å cutoff), ipSAE_min, pDockQ2, atom contacts <5 Å, hotspot-hit fraction, and the **full-trimer loophole check** (any atoms within 4 Å of where the third protomer sits ⇒ discard).
**Controls:** (a) positive: fold the real adalimumab Fab–TNF complex (3WD5) through the same scoring pipeline and confirm the scorer recovers its known interface; (b) negative: shuffled binder sequence.
**Pre-registered pass criteria:** a design "docks" if ipSAE ≥0.6 and pDockQ2 ≥0.23 and ≥100 atom contacts <5 Å. A set "works" if ≥2 designs dock and the pass rate ≥1%.
**Decision tree:** S2 works → campaign with S2 (switch-first). Only S1 works → campaign with S1 (binding-first), revisit switch placement. Only S3 works → the hotspots are wrong, not the target; rebuild sets from `tnf_patch_map.csv`. Nothing docks → change generator (RFdiffusion3) or target representation (trimmed local patch of the groove) before any further spend — this is a stop rule, not a rerun rule.
**Cost:** local GPU route: ≈2–3 GPU-hours on the 5070 Ti, zero marginal cost. Fallback Tamarind route: 3 jobs (of 10 monthly).

## 6. Decisions (locked 15 Oct 2026)

1. **Scope:** **Challenge 2 only.** No work on other challenges in this window.
2. **GPU route:** **local RTX 5070 Ti (16 GB)** — fits RFdiffusion3, Boltz-2, ColabFold, ProteinMPNN. **BoltzGen does not fit** (24 GB floor) and stays a Tamarind fallback. Original RFdiffusion is excluded (no Blackwell kernels); RFdiffusion3 replaces it.
3. **Gate:** tool smoke tests green on the PC by the evening of Oct 16, else Experiment 01 starts on the Tamarind fallback (≤4 jobs).

## 7. Sources

- Third entry repo + lessons: `~/Projects/egfr-conditional-binder-abdulrahman` · https://github.com/Abdulrahman-Neamah/egfr-conditional-binder
- BoltzGen (MIT; 66% of target campaign gave nanomolar binders): https://github.com/HannesStark/boltzgen
- RFdiffusion3 (all-atom successor, ~1/10 compute): https://www.biorxiv.org/content/10.1101/2025.09.18.676967
- ipSAE (Dunbrack 2025): https://github.com/DunbrackLab/IPSAE · bands: https://proteiniq.io/guides/ipsae
- Tamarind Bio pricing: https://www.tamarind.bio/pricing
- Baseline C2 numbers: `~/Projects/protein-design-competition-report.md` §4
