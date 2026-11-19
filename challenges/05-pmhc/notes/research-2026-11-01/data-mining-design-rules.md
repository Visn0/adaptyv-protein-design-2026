# Mining the c5 campaign — what separates the best G12D-selective binders

**Scope.** 1,864 generator-pose candidates -> 417 with G12D fold reads -> **40 with full tri-state reads (G12D + WT + peptide-free)**. The **best set** is defined as `iptm_pep ≥ 0.93` (G12D state) AND `ipdae_pep ≥ 0.5` AND `dWT > 0.1` (`dWT = ipTM_pep(G12D) − ipTM_pep(WT)`) -> **7 designs**. 6 of the 7 also pass the dual-signal criterion `dfree > 0.3` (peptide-dependence; `dfree = ipTM_hla(G12D) − ipTM_hla(free)`, matching the stage-2 record). Everything below compares these 7 against the other 33 tri-state designs.

> **Small-sample caveat (read first).** n = 7 vs 33. Effect sizes below are large-ish (|Cohen's d| ≈ 0.4–0.9, |Cliff's δ| ≈ 0.3–0.6) but raw permutation p-values are 0.03–0.08 and **no feature survives Benjamini-Hochberg FDR control** (best q = 0.46 across ~45 tested features). Bootstrap 95% CIs for the mean difference exclude zero for only a handful of features (marked ✓ below). The rules in §6 were fitted on all 7 positives with no held-out set — treat them as **hypotheses with a direction**, not validated thresholds. One structural fact sharpens the interpretation: every one of the 33 'rest' designs *also* passes `iptm_pep ≥ 0.93` and `ipdae_pep ≥ 0.5` — within this cohort the *only* axis the label measures is **WT discrimination**, and every best design has a WT fold that collapses (peptide interface read 0.01–0.17; 7/7) while no rest design does (0/33).

## 1. Data and definitions

| item | source |
|---|---|
| G12D reads (iptm_pep, ipdae_pep, quality) | `s1/s1-summary.csv`, `s1w3/`, `camp/`, `c2p/` (`__g12d` rows); per-model values cross-checked against `s1-scores.csv` (summary = mean of 5 boltz-2 models, verified) |
| WT + peptide-free reads | `s2/`, `s2w3/`, `s2c/` summaries (`__wt`, `__free` rows) |
| binder sequences (chain D) | regex over `{s1,s1w3,camp,c2p}/folds/*.yaml`; 6/7 best from s1/c2p yamls, all 40 tri-state covered, binder_len == pose-screen binder_len for all 1,864 joins (join sanity check passed) |
| generator-pose geometry | `s0/pose-screen-*.csv` merged, deduped to the 1,864-design campaign file |
| campaign context | `records/stage2/README.md`, `campaigns/c2-peptide-only/README.md` (definitions confirmed; dWT/dfree values reproduce exactly) |

Feature definitions: charged = D,E,K,R; acidic = D,E; basic = K,R; aromatic = F,W,Y; hydrophobic = A,V,I,L,M,F,W,Y; polar-uncharged = S,T,N,Q,H; net charge at pH 7 by Henderson-Hasselbalch (standard pKa, includes chain termini). Helicity = Chou–Fasman Pα; `helix_frac_w11` = fraction of full 11-residue windows with mean Pα ≥ 1.0 (a coarse helical SS guess); `helix_breaker_frac` = (P+G)/L.

## 2. Data table — the 7 best designs

| design | batch | len | Q(pH7) | S% | E% | polar% | helix_frac | P+G% | pose c3 | pose pshare | pose hla_cont | ridge_frac | ipTM_pep | i_pDAE | dWT | dfree | dual |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `wave1-pep__run-033__design_0003` | wave1-pep | 74 | -3.90 | 4.1 | 8.1 | 9.5 | 0.84 | 9.5 | False | 0.473 | 108 | 0.88 | 0.958 | 0.810 | +0.359 | +0.392 | YES |
| `wave1-pep__run-007__design_0000` | wave1-pep | 63 | -5.98 | 3.2 | 19.0 | 11.1 | 0.81 | 7.9 | True | 0.300 | 170 | 0.90 | 0.951 | 0.618 | +0.335 | +0.381 | YES |
| `wave2-pep__run-054__design_0005` | wave2-pep | 91 | -4.80 | 4.4 | 14.3 | 11.0 | 1.00 | 6.6 | True | 0.250 | 165 | 0.85 | 0.948 | 0.608 | +0.308 | +0.682 | YES |
| `peprim-wave1__run-012__design_0006` | peprim-wave1 | 79 | -3.90 | 5.1 | 7.6 | 16.5 | 0.99 | 7.6 | True | 0.286 | 155 | 0.94 | 0.934 | 0.606 | +0.232 | +0.396 | YES |
| `wave2-pep__run-049__design_0002` | wave2-pep | 64 | -1.00 | 1.6 | 6.2 | 3.1 | 1.00 | 4.7 | True | 0.277 | 175 | 0.99 | 0.950 | 0.728 | +0.181 | +0.027 | no |
| `wave2-pep__run-009__design_0007` | wave2-pep | 60 | -5.98 | 3.3 | 20.0 | 3.3 | 1.00 | 5.0 | True | 0.238 | 109 | 0.97 | 0.950 | 0.553 | +0.174 | +0.430 | YES |
| `wave2-pep__run-024__design_0007` | wave2-pep | 92 | -8.98 | 2.2 | 15.2 | 6.5 | 0.98 | 9.8 | True | 0.250 | 189 | 0.95 | 0.941 | 0.729 | +0.173 | +0.672 | YES |

Full 40-design tri-state table and all 1,864 campaign rows: see `features.csv`.

## 3. Best vs rest — requested feature groups, effect sizes

Primary contrast = best (n=7) vs other tri-state designs (n=33). ΔCI = bootstrap 95% CI of the mean difference; ✓ marks CIs excluding 0. `AUC` = P(best > rest) (0.5 = no separation); `AUC₂` = same vs all 411 other folded designs (campaign-wide context, only for sequence/pose features). q = BH-adjusted permutation p.

| feature | best mean [range] | rest mean [range] | Δ | ΔCI ✓ | d | AUC | AUC₂ | p | q |
|---|---|---|---|---|---|---|---|---|---|
| binder_len | 74.714 [60.00–92.00] | 81.697 [62.00–109.00] | -6.983 | [-16.987, +3.304]  | -0.57 | 0.35 | 0.26 | 0.186 | 0.50 |
| frac_charged | 0.275 [0.19–0.40] | 0.233 [0.09–0.32] | +0.042 | [-0.017, +0.107]  | +0.69 | 0.60 | 0.73 | 0.111 | 0.50 |
| frac_acidic | 0.171 [0.11–0.25] | 0.141 [0.05–0.20] | +0.030 | [-0.009, +0.071]  | +0.76 | 0.62 | 0.75 | 0.076 | 0.46 |
| frac_basic | 0.104 [0.07–0.15] | 0.092 [0.04–0.15] | +0.012 | [-0.011, +0.037]  | +0.44 | 0.57 | 0.65 | 0.298 | 0.62 |
| frac_aromatic | 0.042 [0.02–0.10] | 0.050 [0.00–0.13] | -0.009 | [-0.027, +0.013]  | -0.26 | 0.44 | 0.26 | 0.538 | 0.81 |
| frac_hydrophobic | 0.565 [0.43–0.72] | 0.559 [0.37–0.79] | +0.006 | [-0.059, +0.075]  | +0.07 | 0.50 | 0.72 | 0.864 | 0.94 |
| frac_polar | 0.087 [0.03–0.16] | 0.131 [0.04–0.30] | -0.043 | [-0.081, -0.004] ✓ | -0.75 | 0.28 | 0.19 | 0.077 | 0.46 |
| net_charge_pH7 | -4.935 [-8.98–-1.00] | -4.017 [-9.98–0.91] | -0.917 | [-2.798, +0.926]  | -0.37 | 0.42 | 0.30 | 0.397 | 0.71 |
| helix_prop_mean | 1.171 [1.11–1.25] | 1.126 [0.94–1.29] | +0.045 | [+0.004, +0.087] ✓ | +0.60 | 0.66 | 0.83 | 0.161 | 0.50 |
| helix_window11_max | 1.325 [1.24–1.40] | 1.304 [1.07–1.41] | +0.021 | [-0.027, +0.065]  | +0.26 | 0.57 | 0.75 | 0.536 | 0.81 |
| helix_frac_w11 | 0.945 [0.81–1.00] | 0.779 [0.20–1.00] | +0.166 | [+0.080, +0.258] ✓ | +0.86 | 0.78 | 0.87 | 0.040 | 0.46 |
| helix_breaker_frac | 0.073 [0.05–0.10] | 0.076 [0.03–0.16] | -0.003 | [-0.020, +0.014]  | -0.11 | 0.50 | 0.23 | 0.789 | 0.91 |
| ps_c3 | 0.857 [6/7 True] | 1.000 [33/33 True] | -0.143 | [-0.429, +0.000]  | — | 0.43 | — | 0.175 | 0.50 |
| ps_peptide_share | 0.296 [0.24–0.47] | 0.281 [0.20–0.45] | +0.015 | [-0.034, +0.082]  | +0.23 | 0.57 | 0.63 | 0.588 | 0.85 |
| ps_ridge_contacts | 59.286 [33.00–85.00] | 65.333 [33.00–93.00] | -6.048 | [-18.593, +5.844]  | -0.40 | 0.40 | 0.55 | 0.345 | 0.69 |
| ps_hla_contacts | 153.000 [108.00–189.00] | 194.364 [119.00–320.00] | -41.364 | [-71.032, -14.476] ✓ | -0.81 | 0.30 | 0.40 | 0.058 | 0.46 |
| ps_p6_min_dist | 3.286 [2.31–4.32] | 3.128 [2.41–4.54] | +0.157 | [-0.338, +0.663]  | +0.27 | 0.58 | 0.47 | 0.530 | 0.81 |
| ps_pass | 0.857 [6/7 True] | 1.000 [33/33 True] | -0.143 | [-0.429, +0.000]  | — | 0.43 | — | 0.176 | 0.50 |

**Null results, stated plainly.** Generator-pose `peptide_share` does not separate (0.296 vs 0.281, p 0.59, ΔCI [−0.03, +0.08]) — the fold-stage shares are also flat. `c3` and the pose `pass` flag are **saturated** at this stage (39/40 and 40/40 tri-state designs have c3 True / pass True; the single c3 = False design is one of the best) — c3 was evidently a gate *into* folding, not a discriminator thereafter. Aromatic fraction, hydrophobic fraction, breakers, p6_min_dist: no usable separation (all p > 0.5).

## 4. Top 10 discriminative features (ranked by |Cliff's δ|, primary contrast)

| # | feature | family | direction | best mean | rest mean | d | Cliff δ | AUC | p | q |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | aa_S | AA fraction | lower in best | 0.034 | 0.060 | -0.90 | -0.57 | 0.21 | 0.033 | 0.46 |
| 2 | helix_frac_w11 | helicity | higher in best | 0.945 | 0.779 | +0.86 | +0.56 | 0.78 | 0.040 | 0.46 |
| 3 | g12d_n_confident **(fold readout — not a design rule)** | fold readout | lower in best | 0.857 | 2.727 | -0.90 | -0.50 | 0.25 | 0.045 | 0.46 |
| 4 | aa_V | AA fraction | lower in best | 0.049 | 0.079 | -0.82 | -0.46 | 0.27 | 0.058 | 0.46 |
| 5 | frac_polar | group fraction | lower in best | 0.087 | 0.131 | -0.75 | -0.44 | 0.28 | 0.077 | 0.46 |
| 6 | ps_hla_contacts | generator pose | lower in best | 153.000 | 194.364 | -0.81 | -0.40 | 0.30 | 0.058 | 0.46 |
| 7 | aa_E | AA fraction | higher in best | 0.129 | 0.094 | +0.87 | +0.40 | 0.70 | 0.044 | 0.46 |
| 8 | aa_N | AA fraction | lower in best | 0.005 | 0.015 | -0.57 | -0.38 | 0.31 | 0.176 | 0.50 |
| 9 | aa_W | AA fraction | lower in best | 0.000 | 0.004 | -0.79 | -0.36 | 0.32 | 0.102 | 0.50 |
| 10 | helix_prop_mean | helicity | higher in best | 1.171 | 1.126 | +0.60 | +0.32 | 0.66 | 0.161 | 0.50 |

Reading: the top features form **two coherent stories** rather than ten independent knobs — (i) a *composition/order* axis (low Ser/Val/polar-uncharged, high Glu, high predicted helicity), and (ii) an *interface-placement* axis (fewer generator-pose contacts to the HLA scaffold). Serine and polar fractions are the most separable single features; Glu and helix windows the most mechanistically legible. The directions replicate against the campaign-wide folded set (AUC₂: aa_S 0.19, frac_polar 0.19, helix_frac_w11 0.87, helix_prop_mean 0.83, aa_E 0.80, frac_acidic 0.75, binder_len 0.26) — which is the least selection-biased view available.

**Batch is the strongest single signal** (below), but it is a protocol label, not a designable trait: the wave1-pep/wave2-pep families produced 6 of 7 best designs; nat-wave1, mini-wave1, nim-wave3 produced none in this cohort.

## 5. Source batch

| batch | best | rest (tri-state) | OR | Fisher p |
|---|---|---|---|---|
| mini-wave1 | 0/7 | 4/33 | 0.00 | 1.000 |
| nat-wave1 | 0/7 | 8/33 | 0.00 | 0.309 |
| nim-wave3 | 0/7 | 4/33 | 0.00 | 1.000 |
| peprim-wave1 | 1/7 | 5/33 | 0.93 | 1.000 |
| pilot-pep | 0/7 | 1/33 | 0.00 | 1.000 |
| wave1-pep | 2/7 | 4/33 | 2.90 | 0.279 |
| wave2-pep | 4/7 | 7/33 | 4.95 | 0.075 |
| **wave1+wave2 combined** | **6/7** | **11/33** | **12.0** | **0.029** |

## 6. Proposed design rules for the next generation round

Pass counts: best pass / rest pass / campaign-wide (418 folded designs) pass.

| rule | best | rest-tri | campaign 418 |
|---|---|---|---|
| R1 len 55–80 aa | 5/7 | 16/33 | 146/418 |
| R2 Ser ≤ 5.5% and polar ≤ 12% | 6/7 | 12/33 | 101/418 |
| R3 helix_frac_w11 ≥ 0.80 and P+G ≤ 10% | 7/7 | 17/33 | 130/418 |
| R4 net charge ≤ −1 at pH 7 | 6/7 | 29/33 | 298/418 |
| R5 generator-pose HLA contacts ≤ 190 | 7/7 | 18/33 | 324/418 |

**Combined specificity score** (number of the 5 rules passed): best = 4 designs at 4/5 and 3 at 5/5 (mean 4.43); rest = 5 at 1/5, 9 at 2/5, 9 at 3/5, 8 at 4/5, 2 at 5/5 (mean 2.79); campaign 418 (mean 2.39). Score ≥ 4: **7/7 best, 10/33 rest, 97/418 campaign** (rule-score AUC 0.80 in-cohort / 0.83 vs folded campaign — in-sample, optimistic).

**R1 — Cap binder length at ~80 aa (target 55–80; 5 of 7 best designs are ≤ 79 aa).** Best 74.7 [60–92] vs rest 81.7 [62–109]; Δ = −7.0 aa (d −0.57, p 0.19; the direction also holds against the campaign-wide folded set, AUC₂ 0.26). No best design exceeded 92 aa; 6/33 rest did.

**R2 — Keep serine and polar-uncharged content low (S ≤ 5.5%; S+T+N+Q+H ≤ 12%).** S: 3.4% [2.0–5.1] vs 6.0% [1.0–15.0] (d −0.90, p 0.033, ΔCI [−4.0, −1.2] pts ✓ — one of the few features whose CI excludes zero; also lower in the within-wave check: 3.1% vs 6.8%). Polar: 8.7% vs 13.1% (d −0.75, p 0.077). Rationale is empirical, not mechanistic — do not over-interpret as 'Ser is bad chemistry'; it is a flag for the Ser-rich polar-coil style that keeps binding WT.

**R3 — Design for high helical content (helix_frac_w11 ≥ 0.80; keep P+G ≤ 10%).** Helix-window fraction 0.945 [0.81–1.00] vs 0.779 [0.20–1.00] (d +0.86, p 0.040, ΔCI [+0.08, +0.26] ✓); mean Pα 1.171 vs 1.126 (ΔCI excludes 0). All 7 best designs clear 0.80; 16/33 rest fail it. The best designs are rigid, fully-helical scaffolds — consistent with an interface that loses all contacts when the peptide's P6 sidechain changes.

**R4 — Bias charge acidic (D+E ≥ 15%, E ≥ 10%; net charge −1 to −9 at pH 7).** Acidic fraction 17.1% vs 14.1% (d +0.76, p 0.076; campaign-wide AUC₂ 0.75); Glu 12.9% vs 9.4% (d +0.87, p 0.044); net charge −4.9 vs −4.0, and −5.1 vs −3.0 within the wave family (where the batch confound is removed). Lone-rule specificity is weak (only 4/33 rest fail Q ≤ −1) — use it as a tiebreaker inside the combined screen, not a filter.

**R5 — Screen generator poses to sit on the peptide, not the HLA scaffold; source candidates from the peptide-first wave families.** Pose HLA contacts 153 [108–189] vs 194 [119–320] (d −0.81, p 0.058, ΔCI [−71, −15] ✓); ridge share of peptide contacts 0.925 vs 0.888 (weaker). All 7 best designs had ≤ 189 HLA contacts; 15/33 rest exceeded 190. Batch: wave1+wave2 contributed 6/7 best vs 11/33 rest (OR 12.0, Fisher p 0.030). **Caveat:** batch is confounded with generator protocol and campaign era — treat 'prefer the wave-style peptide-aware protocol' as the actionable form of this rule, and the contact-budget threshold as its mechanism-level screen.

Nulls that should *not* go into generation goals: c3 (saturated), generator peptide_share (no separation), aromatic/hydrophobic fractions, p6_min_dist, binder_len beyond the ~80 aa cap.

## 7. Caveats, and what would falsify these rules

- **n = 7.** With 6/7 dual-signal positives and zero held-out designs, all thresholds are in-sample. A next round that folds ~20 designs passing ≥ 4 rules, plus ~10 random folded controls, would test the screen at a useful scale.
- **The label is WT-discrimination only.** All 40 tri-state designs pass the affinity gates; the best set is exactly the set whose WT folds collapse (WT peptide-interface read 0.01–0.17 vs 0.18–0.70 for all rest; WT ipTM_pep 0.60–0.78 vs 0.87–0.97). Rules derived here separate *specific* from *pan-peptide* binders of this groove — not strong from weak binders.
- **Batch confound.** wave1-pep/wave2-pep designs were mined/generated under a different protocol; the sequence rules replicate within the wave family (S 3.1% vs 6.8%; E 13.8% vs 8.3%; helix 0.94 vs 0.68; Q −5.1 vs −3.0), which is reassuring but is still n = 6 vs 11.
- **Multiple testing.** ~45 features, no BH-FDR survivor. The honest summary is 'several coherent, medium-large effects in the expected directions', not 'ten validated discriminators'.
- **Selective cohort.** The tri-state 40 were themselves run because they passed earlier screens; campaign-wide AUC₂ columns are the less-biased (but label-incomplete) view — they agree in direction for length, helicity, acidic/charged fraction, and Ser.

## 8. Files

- `features.csv` — per-design table: reads (all three states), dWT/dfree, sequence features for 418 designs, pose features for 1,864, provenance columns.
- `stats_best_vs_rest.csv` — every feature with group stats, effect sizes, permutation p, BH q, AUCs.
- `best_designs.csv` — the 7 best designs with full feature/read detail.
- `assemble.py` / `analyze.py` / `diag2.py` — reproducible pipeline (read-only over the campaign dirs).

