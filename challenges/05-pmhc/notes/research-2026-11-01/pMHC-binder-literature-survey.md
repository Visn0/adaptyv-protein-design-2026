# Designed binders against peptide–MHC complexes (2024–2026)
### Survey for a KRAS G12D / HLA-A\*11:01 (VVVGADGVGK) binder campaign — with tactical recommendations

*Compiled 2026-11-01. Scope: TCR-mimic antibodies, peptide-centric de novo binders/miniproteins; emphasis on how specificity for the mutated peptide over WT was achieved or attempted. Includes the Anthropic × Adaptyv 2026 competition record and the specific challenge on this exact target (closes Nov 8, 2026).*

---

## 1. Executive summary

- **The field broke through in late 2024 / mid-2025.** Three coordinated Science papers (Liu et al., Householder et al., Johansen et al., all Jul 2025) showed de novo-designed proteins — RFdiffusion-based minibinders and α-helical "mini-TCR mimics" — can bind specific pMHCs with nM affinity, discriminate against closely related off-target peptides, and function as CAR/T-cell engagers [1–4].
- **Specificity is engineered, not lucky:** all three pipelines condition designs to make extensive contacts with *outward-facing peptide side chains* and to avoid MHC contact, then apply explicit negative design (ΔpAE/ΔipAE against off-target peptides, per-residue ProteinMPNN scanning) before any wet-lab screen [1,3].
- **The exact campaign target has a public negative result.** The ADAPT pipeline (Baker/Bradley/Garcia) attempted *de novo* TCR design against A\*11:01 + VVVGADGVGK and got **0% success** in a clonal screen (tens of designs of the same scale that yielded hits for 4/9 other targets), while the pipeline as a whole succeeded on 6/9 pMHCs (and 3/3 for its antibody extension, 5–8%/target) [5]. This is the single most important data point for planning.
- **Natural TCRs solve this problem, but only after affinity maturation.** The JDI TCR (Immunocore) reaches 743 pM for G12D vs 3.0 µM WT (~4000-fold window) — with near-identical crystal structures for both complexes; discrimination is driven by *indirect electrostatics* around Asp6 [7]. Affini-T's affinity-matured TCRs report a >7000-fold mutant/WT window [11].
- **A designed binder discriminating this exact single point mutation is not yet published.** Closest analogs: a designed binder discriminating CTNNb1 S5F vs WT (a bulkier mutant, via cation-π/π-π contacts) [1], a TCR-like antibody discriminating KRAS G12D vs WT on HLA-C\*08:02 [14], and TCR-mimics for KRAS G12V on HLA-A\*11:01 [15].

---

## 2. The three flagship de novo pMHC-binder papers (Science, 24 Jul 2025)

### 2.1 Liu, Greenwood, Bonzanini et al. — "Design of high-specificity binders for peptide–MHC-I complexes" [1]
- **Targets (11 pMHCs; A\*01:01, A\*02:01, A\*03:01, C\*07:02):** MAGE-A3 (EVDPIGHLY/A1), CTNNb1 S5F neoantigen (TTAPFLSGK/A3), HIV Env (KLTPLCVTL/A2), WT1 (RMFPNAPYL/A2), PAP (TLMSAMTNL/A2), SARS-CoV (GLMWLSYFV/A2), YFV (LLWNGPIAV/A2), MART-1 (ELAGIGILTV/A2), gp100 (YLEPGPVTA/A2), PRAME (ALYVDSLFFL/A2; designed from a *predicted* structure), plus the Titin off-target pair (ESDPIVAQY/A1). Preprint version reported 10 targets [cited as PMC11623666].
- **Method:** RFdiffusion with the *upward-facing peptide residues as hotspots*, generating small proteins that "arc above" the peptide-binding groove with limited MHC contact; ProteinMPNN for sequence; AF2 (initial guess) filtering; **partial diffusion** (partial_t 12–25) to recycle good scaffolds onto new targets. 200–12,000 designs per target screened on yeast (dual-color FACS, on-target vs 2–4 off-target tetramers); top hits validated in CAR-Jurkat cells.
- **Success rate:** specific binders for **all 11 targets**; **8/11 conferred peptide-specific T-cell activation** in CARs; SPR affinities low-nM (e.g., PRAME_A9 96 nM, PRAME_A2 35 nM); crystal structure of the MART-1 binder (mart1-3) matched the design model fold and peptide contacts.
- **Specificity mechanism(s):**
  - **Peptide-centric interfaces** — binders contact many peptide positions and little MHC. The MAGE-A3 binder (MAGE-513) additionally has a **gatekeeper residue (D29)** that sterically clashes with bulky side chains at peptide P4 of off-target peptides [1].
  - **In silico negative design:** (i) ProteinMPNN per-residue scoring — require high probability for the on-target peptide residue and a large drop when mutated to alanine (a de facto in silico alanine scan); (ii) ΔpAE filtering with a MHC-finetuned AF2 against 2–3 proteome-derived off-target peptides presented by the same allele (thresholds −0.5 to −10).
  - **Global specificity audit:** yeast-displayed peptide library scan (P3/P9 anchor-fixed, NNK elsewhere) for MAGE-513 — cross-reactive peptides had *similar outward-facing side chains* to the target; predictable and narrow cross-reactivity, "similar to TCRs".
- **Single-point mutation discrimination:** the **CTNNb1 S5F** binder is the showcase — it makes "extensive contact with the mutated Phe" through cation-π, π-π and hydrophobic interactions and binds the S5F peptide but **not WT CTNNb1** [1].

### 2.2 Householder, Xiang, Jude et al. (Garcia lab) — "De novo design and structure of a peptide-centric TCR mimic binding module" [2]
- **Target:** NY-ESO-1(157–165 C9V) SLLMWITQV / HLA-A\*02:01.
- **Method:** RFdiffusion **fold-conditioning** onto four-helix bundles; peptide residues **Ile6 and Gln8 as hotspots**; 100 distinct folds → 600 designs → iPAE filtering (<10) → 500 sequences per hit scaffold (~2000 designs); top 5 designs displayed on yeast.
- **Success rate:** **4/100 scaffolds** yielded at least one iPAE-passing design; top-5 test → **2/5 stained NY-ESO-1 but not MART-1**; lead "mini-TCRm 1.1" = **Kd 9.5 nM**, **crystal structure 2.05 Å** (rigid TCR-like docking; peptide-focused contacts, two shape-complementary pockets capturing Met4 and Trp5 independently; less than half the height of a Fab/TCR).
- **Specificity mechanism:** rigidity over CDR-loop flexibility ("more rigid scaffold could help minimize structural adaptation to alternative peptides"); structure-informed **in-silico screen of 14,363 MS-detected HLA-A\*02 9-mers** (MHC Motif Atlas) predicted **two off-target peptides** (Hamming distance 4) correctly; functionally the TCRm retained peptide selectivity and cytotoxicity as a T-cell engager [2].

### 2.3 Johansen, Wolff, Scapolo et al. (DTU / Adaptyv-adjacent) — "De novo-designed pMHC binders facilitate T cell–mediated cytotoxicity" [3]
- **Targets:** NY-ESO-1(157–165) SLLMWITQC/HLA-A\*02:01 (primary); RVTDESILSY/HLA-A\*01:01 (second target, no experimental structure).
- **Method:** RFdiffusion + ProteinMPNN + AF2(initial guess), partial diffusion for in-silico affinity maturation; **in silico cross-panning**: AF2-IG scores against the target plus **10 single/double-mutant peptides** in the same HLA; select designs with target ipAE <10 and all variants >10; then **MD simulations** to deselect dynamic/false-positive interfaces. 44 miBds taken to in-vitro characterization (yeast/mammalian display), lead = NY1-B04.
- **Success rate:** ~**2% (1:50)** binder discovery; 44 designs → 1 lead (NY1-B04) with high specificity + minimal cross-reactivity; on the second, structure-less target, 2 unique binders (~2%). **In-silico cross-panning predictions correlated 89% with in-vitro specificity results.** CAR ("BIKE") T cells selectively killed NY-ESO-1+ melanoma cells. Design-to-therapeutic-cell-product "<8 weeks".
- **Specificity mechanism:** target the **non-anchor residues** of the peptide; multi-variant ΔipAE cross-panning before synthesis; MD interface-stability filter (high interface variability and interaction-energy fluctuation → deselect). In vitro, NY1-B04 cross-bound only 2 of 9 single-mutant peptides tested (SLL**A**WITQC, SLLMWITQ**V**) — i.e., it discriminated the majority of single point mutants [3].

---

## 3. Designed TCRs and TCR-mimic antibodies — ADAPT and related

### 3.1 Motmaen, Jude, Wang et al. — ADAPT framework (Baker/Garcia/Bradley; bioRxiv Nov 2025) [5]
- **What it is:** structure-based deep-learning pipeline (fine-tuned AF2 as sampling engine + pMHC docking-geometry templates + genetic-algorithm refinement) for de novo **TCRs** and, via antibody-variable templates, **TCR-mimic antibodies**; code open-sourced (github.com/phbradley/ADAPT; Zenodo data).
- **TCR design results (9 targets):** binders for **6/9** targets. Small clonal screens (30–60 designs) succeeded for MAGE-A3 (16.7%), PAP (20.0%), SARS (4.2%), YFV (20.8%); larger libraries (1,000–5,000 designs) were needed for TdT (0.3%) and PIK3CA/B\*44:02 (0.1%). **Three targets failed outright: p53 R175H (0%), PIK3CA/A\*03:01 (0%), and — critically — A\*11:01 + VVVGADGVGK (KRAS G12D neoepitope): 0% (clonal screen)** [5, Table 1].
- **Antibody results (3 targets):** binders for **all three** in small clonal screens — MAGE-A3 6.25%, PAP 8.33%, TdT (polar peptide ALYDKTKRI) 5.21%; affinities **5–700 nM**; cryo-EM structures of two complexes (vAB-30 and vAB-66) show 0.6–0.7 Å accuracy at the interface. Designed binding modes fall within the orientation space of natural TCRs; peptide contacts via CDRs (e.g., HC-R54 H-bond to peptide C-terminal main chain; LC-Y32 CH–π to Pro4). PDB 9YTF = vAB-30/MAGE-A3/HLA-A1.
- **Takeaway:** the same target that broke TCR design in this pipeline is where TCR-like **antibody** scaffolds (designed, not repurposed) may have the better odds; the TCR-mimic antibody extension has not (publicly) been tried on A\*11-VVV.

### 3.2 TCR-like antibodies to KRAS G12D/HLA-C\*08:02 (Ahn et al., bioRxiv Aug 2025) [14]
- **Target:** KRAS G12D decamer GADGVGKSAL / HLA-C\*08:02 (the clinically validated epitope; different HLA and peptide register from the campaign target).
- **Method:** in silico docking of human antibody Fv frameworks onto the pMHC (using known TCR-like antibody–pMHC complexes as templates), limited CDR3 sequence design at 3–4 positions; yeast surface display library; MACS/FACS with KRAS G12D tetramers and **negative selection with a SARS-peptide/HLA-C\*08:02 tetramer**.
- **Success rate:** 9 designed Fv lineages → lead C8K10D (KD ≈ 1.36 µM) → affinity maturation → 7 clones (C8K10D1–7), several low-nM (C8K10D3/5/6); further CDR-L2 library + structure-guided engineering to C8K10D5-18 variants; CAR-T cells activated specifically on target cells.
- **Specificity:** **no cross-reactivity to WT KRAS peptide, SARS peptide, or KRAS G12V/G12C/G12R**; alanine scan shows peptide positions 3, 7, 10 are critical contacts — residue-level specificity with a peptide differing from WT by a single amino acid [14].

---

## 4. KRAS G12D / HLA-A\*11:01 (VVVGADGVGK) — everything published

**Structural biology of the exact target:**
- PDB **7OW4**: HLA-A\*11:01 + VVVGADGVGK (no TCR; **positions 5–6 disordered** — the central peptide is mobile); **7OW6**: JDI TCR + G12D peptide; **7OW5**: JDI TCR + WT peptide; **9UV8**: A\*11:01 + 9-mer VVGADGVGK [7,8].
- **Zhu et al., Commun Biol 2025 [8]:** G12D is presented as both a 9-mer (VVGADGVGK; bent, "conformationally flattened", poorly TCR-recognized) and a 10-mer (VVVGADGVGK; compact, stable, **bulged with Asp12 shifted to p6**, TCR-accessible). The Asp adds an unusual "buried/electrostatic" perturbation; peptide-length/register is a major determinant of immunogenicity. (See also the challenge note: in TCR-bound 7OW6 the Asp is "tucked against Arg114 and Gln70" of the HLA.)
- **Baker-lab abstract (Eldaly et al., J Immunol 2025) [10]:** five patient-derived TCRs recognize G12D/A11 with high specificity; a **conserved conformational shift accompanies TCR binding — residues A5 and D6 flip from exposed to downward-facing, adopting a polyproline-II conformation**; they propose stabilizing this peptide conformation by chemical modification (a "super-agonist").
- **JDI TCR (Poole et al., Nat Commun 2022; Immunocore IMC-KRAS G12D) [7]:** affinity-enhanced patient TCR (phage display, >10⁶-fold affinity gain) — **KD 743 pM (G12D) vs 3.0 µM (WT)**; 7OW5/7OW6 structures nearly identical (TCR VM RMSD 0.29 Å) — "**specificity driven by differences in indirect electrostatic interactions**"; CDR2α W53 contacts D6; soluble parental JDI bound G12D (63 µM) and *nothing* for WT, G12C, ERAS/RRAS/MRAS/DIRAS2/RAP1A; 18/20 proteome-derived peptide mimics not bound; 2 weak (460 nM, 2.3 µM).
- **TCR discovery and off-target repair (Han et al., J Transl Med 2025) [9]:** new A\*11:01-restricted TCRs; TCR1 had high avidity but cross-reacted with an SMC1A self-peptide; structure-guided CDR1α mutations produced TCR1a7 with restored specificity — a worked example of specificity repair by loop engineering (X-scan + proteome scan methodology).

**Industry/clinical (affinity-matured natural TCRs — the proven route):**
- **Affini-T (SITC 2024) [11]:** bispecific TCR-based T-cell engagers vs G12D and G12V/A\*11:01; yeast-display affinity maturation (>1000-fold); **>7000-fold affinity window mutant vs WT**; endogenous-mutation cell killing; X-scan + yeast peptide-library off-target profiling.
- **Medigene (ESMO 2024) [12]:** 3S TCR program targeting G12D across HLA-A\*11 subtypes (high sensitivity, tumor recognition, clean safety).
- **DCTY1102** — Phase I/II TCR-T for KRAS/NRAS G12D+ advanced tumors (NCT07014878, China) [13].
- Bispecific TCR-mimic for the **G12V** neighbor: scFv2 from phage display binds G12V/A\*11:01 *and* A\*03:01, discriminates WT and other KRAS mutants, works as an in-vivo-active T-cell engager [15].

**Conclusion for the campaign target:** specificity for D6 over G6 is achievable by natural, affinity-matured TCRs (4000–7000-fold windows), but so far **no de novo-designed binder** against this exact epitope has been reported as successful, and the one serious public attempt (ADAPT TCR design) returned 0/≈40–60 designs [5]. The competition (below) is aimed at filling exactly that gap.

---

## 5. Single-point peptide mutation discrimination by designed binders — the state of the art

| Evidence | What was discriminated | How |
|---|---|---|
| **Liu et al. 2025** [1] | **CTNNb1 S5F vs WT** (neoantigen) | Binder makes cation-π/π-π/hydrophobic contacts to the *mutated* Phe; no binding to WT peptide. |
| Liu et al., MAGE-513 [1] | MAGE-A3 vs 14k-peptide yeast library | Extensive peptide contacts + gatekeeper (D29) clashing with bulky P4 residues; cross-reactants share outward side chains. |
| **Johansen et al. 2025** [3] | NY-ESO-1 vs 10 single/double peptide mutants | ΔipAE cross-panning (>10 gap) filtered pre-synthesis; lead cross-bound only 2/9 single mutants. |
| **Householder et al. 2025** [2] | NY-ESO-1 vs 14,363 A\*02 9-mers | Rigid scaffold; predicted 2 off-targets (Hamming 4); retained functional selectivity. |
| **Ahn et al. 2025** [14] | KRAS **G12D vs WT, G12V/G12C/G12R** (HLA-C\*08:02) | Designed + display-selected scFv; single-residue specificity confirmed by alanine scan and negative selection. |
| JDI TCR; Affini-T [7,11] | KRAS G12D vs WT (A\*11:01) | Not designed de novo — evolved; 4000–7000× windows; electrostatics-driven. |
| Prediction tools | TCR cross-reactivity to single mutations | **BATMAN/BATCAVE** (Cell Systems 2025; 22,000+ TCR–pMHC mutation pairs) [20]; biophysical escape-variant framework (bioRxiv 2026; reproduces affinity disruption at P5/D6 of an autoantigenic peptide) [21]; structure-guided specificity prediction (Nat Commun 2026) [22]. |

**Pattern:** discrimination of a *bulkier/aromatic* mutant (S5F) was achieved by direct favorable contacts + steric exclusion of WT. For **Gly→Asp**, the mutant is bigger but polar — WT exclusion cannot be clash-based (Gly leaves no bulk to clash with); specificity must come from **Asp-dependent favorable interactions** (H-bond/salt bridge, desolvation, charge complementarity) plus any **conformational differences** D6 imposes on the peptide register. This is exactly the regime where the JDI TCR needed affinity maturation and where designed binders remain unproven.

---

## 6. Adaptyv Bio competitions — challenges, winners, and what worked

Adaptyv runs open protein-design competitions with standardized wet-lab validation (expression + SPR/BLI, results public on Proteinbase). Track record:

1. **EGFR round 1 (Sep–Oct 2024)** [26,27]: ~200 designs tested; 13 binder calls in the open dataset (blog quotes 2.5% strict hit rate), 76–92% expression; most used RFdiffusion+ProteinMPNN; **the winning combination was AF2 hallucination + SolubleMPNN inverse folding**; >50 teams.
2. **EGFR round 2 (Nov–Dec 2024)** [28,29]: 400 tested, 378 expressed (95%), **53 binders (14%)**; top affinities single-digit nM (cetuximab-comparable). Winners/notables: **Cradle** (protein language model mutations in cetuximab framework; scFv KD 1.2 nM), **Tihumab/Chris Xu** (nanobody humanization, ranks 2–3), **Aurelia Bustos** (TGF-α scaffold + diffusion; **8/8 of her tested designs bound**), **Lennart Nickel** (BindCraft fully de novo), **Yoichi Kurumida** (RFdiffusion-scaffolded), plus Raygun+Protrek filtering and linker-combination approaches.
3. **Community paper / BenchBB (2025)** [30]: pooled analysis of 1,857 submissions (600 tested; 60 novel binders validated); created the 7-target BenchBB benchmark; central finding — no single in-silico metric predicts experimental success well; standardize and diversify.
4. **Nipah competition (Nov–Dec 2025)** [31,32]: 10,000+ submissions; **1,196 selected (Boltz-2 ipSAE + expert + community vote), 1,028 expressed (86%), 111 binders (9.3%), 28 ≤ single-digit nM**. Top: **Miles McGibbon (0.37 nM)**, Liviu Copoiu (0.45 nM), Andrew Huang (0.72 nM); de-novo-class winners: **Nick Boyd (1.4 nM)**, Johannes Klier (12 nM), Brian Coventry (18 nM). Independent analysis: **shape complementarity emerged as a useful binding predictor**; expression ≠ binding.
5. **GEM × Adaptyv RBX1 (2026)** [33]: 322 validated, **9 binders (~2.8%)**, 79% expression; method mix — RFdiffusion 27, EB Mosaic 18, BoltzGen 15, Bagel+Solupnn 7, LFM2-custom 7 (a hard E3-ligase RING target). Participant lesson: Boltz-2 ipSAE **weakly** predicted both AF3 validation and competition outcomes (~r≈0.3) — do not over-optimize one metric.
6. **Anthropic × Adaptyv 2026 (current)** [23–25]: five 2-week challenges — EGFR (conditional), TNF-α, GLP1R (agonist), TfR1 (conditional), and **Challenge 5: KRAS G12D pMHC (Oct 26–Nov 8, 2026, closes Nov 8 23:59 AoE — the campaign deadline)**. ~1,500 designs screened per challenge; up to 20 designs for Tracks 2/3, up to 40 for Track 1; **de novo, zero-shot only** (no modifying an existing binder; no existing binder as a starting point; CDR/framework-common regions allowed for antibodies; novelty triage on Proteinbase uses a 1–4 scale [34]). Selection for Tracks 2/3 is done by a **public Claude prompt** weighing method novelty, design diversity, and several confidence metrics (no single metric decider) [25]. All results published openly (~Dec 2026).

### Challenge 5 rules (the exact target — read this before designing) [24]
- Target: HLA-A\*11:01 + β2m + **VVVGADGVGK** (G12D); negatives: **WT VVVGAGGVGK** and **peptide-free A\*11:01/β2m**. Recommended epitope: *the peptide and the groove around it*; structure ref **7OW6 chains A–C, TCR removed**. Note given: 7OW4 (no TCR) **lacks coordinates for positions 5–6**; in 7OW6 the Asp is tucked against HLA R114/Q70.
- Ranking: (1) **mutation specificity** (measurable KD to G12D AND no detectable binding to WT; else ranked by WT/G12D KD ratio); (2) **peptide-dependent binding** (no binding to peptide-free MHC); (3) **affinity**. Winner must clear all three; a binder "that reads the HLA or β2m instead of the peptide" ranks last. Assay: design **immobilized (C-terminal Twin-Strep capture)**, pMHC in solution; binding = fittable KD or >300% association shift over negative control; His/Avi and Twin-Strep tags off-limits.
- Formats: single chain 10–250 aa; minibinder/large binder/microbinder/nanobody/scFv/Fab categories; must be de novo & zero-shot; ≤20 designs (Tracks 2/3) ranked in submission.

---

## 7. Synthesis: how specificity for the mutated peptide was achieved or attempted

1. **Peptide-centric docking geometry** — force contacts to outward-facing peptide residues, minimize MHC contacts (RFdiffusion hotspots; binders "arc over" the groove). Every successful pipeline does this; it serves both on-target binding and the peptide-free objective [1,2,3,5].
2. **Favorable contacts to the mutated residue itself** — CTNNb1 S5F: cation-π/π-π/hydrophobic to the mutant side chain, no WT binding [1]. HBV MUR35 shows high structural specificity is even achievable with light-chain-only CDR contacts [16].
3. **In silico negative design / cross-panning** — ΔpAE or ΔipAE against proteome-derived off-target peptides and single/double mutants (Liu; Johansen, 89% predictive) before synthesis [1,3].
4. **Per-residue sequence scoring** — ProteinMPNN on-target vs mutant/alanine log-probability demands that every peptide residue matter [1].
5. **Gatekeeper/scaffold principles** — rigid scaffolds over flexible CDR loops; shape-complementary pockets per side chain; occasional deliberately clashing "gatekeeper" residues for bulky off-targets [1,2].
6. **MD and biophysical deselection** — interface-fluctuation filtering to remove confidence-only designs [3]; shape complementarity as a signal [32].
7. **Experimental negative selection in display** — dual-color FACS with on/off tetramers (Liu), SARS-peptide negative tetramers (Ahn), negative selection in yeast display (all).
8. **Post-hoc specificity repair** — if a binder cross-reacts, structure-guided loop mutations can eliminate off-target recognition (TCR1a7 precedent) [9].

---

## 8. Tactical ideas for a KRAS G12D pMHC binder campaign

*Assumptions: de novo, zero-shot designs for Challenge 5; design is SPR-captured C-terminally; winner must show G12D binding with **no detectable** WT or peptide-free binding. Each idea cites its evidence.*

1. **Assume the target is genuinely hard and run a portfolio, not a single pipeline.** The only public de novo attempt on A\*11-VVV (ADAPT TCR design) scored 0%, while the same pipeline's antibody extension scored 5–8% per target on three other pMHCs, and Liu/Johansen/Householder each needed 200–12,000-design screens to find hits. Split ≤20 submissions across 2–3 independent design philosophies (e.g., minibinder arcs à la Liu; rigid helical bundles à la Householder; de novo CDR antibody/TCR-like modules à la ADAPT/RFantibody), so a systemic failure of one pipeline does not zero the campaign. [1,2,3,5,37]

2. **Design *toward* the Asp — do not build around a clash-based negative-design strategy.** WT has Gly at p6: there is no bulk to sterically exclude, and Gly's flexibility makes cavity-based penalties weak. Specificity must come from **favorable, D6-dependent interactions**: H-bonds/salt bridges to the carboxylate (Arg/Lys/His/Asn/Gln/Tyr), charge complementarity, and tight desolvation of D6 — so WT binding is lost because the interactions are missing, not because of a clash. Precedent for the "engage the mutant residue directly" logic: CTNNb1 S5F binder (cation-π/π-π to mutant Phe, no WT binding); precedent that Asp-dependent TCR discrimination works but is subtler: JDI binds D6 via CDR2α W53 and wins specificity mainly through indirect electrostatics (4000× window after maturation). [1,7,14]

3. **Explicitly model peptide mobility: p5–p6 are the battlefield.** 7OW4 has no coordinates for positions 5–6; in TCR-bound 7OW6 the Asp tucks against HLA R114/Q70; patient TCRs induce an exposed→downward PPII flip of A5/D6 upon binding; the 9-mer registers bend and are poorly recognized. Practical approach: predock/build against **at least two peptide states** (7OW6-derived "tucked" state + an MD/AF3-derived "exposed" ensemble), select designs whose D6 engagement is stable across states (and that still pass when the pMHC is given the WT G6 — for which there is no reading frame — and the 9-mer, as an extra discard filter). Designs validated against a single convenient conformation will likely fail the WT or mobility gate. [8,10,24]

4. **Make multi-state in-silico cross-panning the central filter — it is the best-validated predictor in the field.** Score every design (AF2 initial-guess / AF3 / Boltz-2) against: G12D complex, **WT complex**, G12C/G12V/G12R variants, the 9-mer complex, and a **peptide-free A\*11:01/β2m model**; require a large ΔipTM/ΔipAE gap for G12D over every negative (Liu used −0.5 to −10 thresholds; Johansen's ΔipAE >10 gap predictions matched in-vitro specificity 89% of the time and picked their winning binder). Add Liu's ProteinMPNN per-residue trick: require high log-probability of Asp at p6 and a large drop for G6/alanine — this forces designs to "care" about the discriminating residue. [1,3]

5. **Use complementary biophysical filters to kill confident-but-false designs.** Boltz-2 ipSAE alone is a weak experimental predictor (RBX1 analysis ~r≈0.3; competition FAQ explicitly refuses single-metric ranking); MD interface-stability filtering removed false positives in Johansen; shape complementarity was a useful correlate in Nipah; ESM2 PLL flags expressibility. Practical stack: require agreement of ≥2 structure predictors on interface quality, low predicted MHC-contact fraction, stable MD interface (low RMSF/energy variance), and reasonable ESM2 PLL — then rank. [3,24,25,32,33]

6. **Keep an explicit MHC-contact budget — it doubles as insurance for objective 3 (peptide-free MHC).** The peptide-free complex contains the entire HLA/β2m surface; any design with substantial HLA-helix or β2m contact (or tag-adjacent geometry) risks "no detectable binding" failure even if it never binds WT peptide. Score and filter on predicted contact surface to peptide vs HLA helices/β2m; reject designs whose interface is MHC-dominated (the challenge states such designs "rank there" — i.e., last). Liu's "minimal MHC contact" design principle is also the peptide-free objective in disguise. [1,24]

7. **Choose formats that can wrap the peptide, and mind the zero-shot rules.** Householder's four-helix bundles hug the peptide with rigid side-chain pockets (two independent pockets for M4/W5) and produced a 2.05 Å co-crystal; Liu's arc-shaped minibinders work across 11 targets/4 alleles. For antibody-format entries, RFantibody-style de novo CDR design (common framework + designed CDRs) is permitted, but you may not start from an existing binder (JDI/MUR35/affinity-matured TCRs are out; using known complexes only for calibration/fine-tuning is allowed). If you use TCR-like docking geometries as templates (ADAPT-style), describe this explicitly in your methods — the Claude-based selection weighs method novelty and every selected design's provenance will be public. [2,5,24,25,37,38]

8. **Rank and submit specificity-first, and write the methods section like it is part of the score.** The winner must clear all three gates (G12D KD, no WT, no empty), and tie-breaks use KD ratios — so among your ≤20 designs, order by strength of *discrimination evidence* (Δ-scores, D6-engagement evidence), not raw affinity; include topological/interface diversity because selection rewards diversity; document negative-design steps, MD, and metrics (ipTM/ipSAE/AF3 models) since the public selection prompt reads all of it and takes several designs per submission. [24,25]

9. **Instrument the in-silico pipeline for "no detectable binding" arithmetic.** "No detectable binding" in the assay (fittable KD or >300% shift) is a strong bar; a design with 100 nM G12D affinity and 500 nM WT would fail objective 1, while one with 1 µM G12D and undetectable WT could still rank well if it is the only clean binder. Optimize for the **ratio (WT KD / G12D KD) → ∞**, not KD alone: prefer designs whose predicted D6 contacts are binary (present-or-lost) rather than graded. This mirrors how Affini-T/JDI report "windows" (up to >7000×, ≈4000×) rather than single KDs. [7,11,24]

10. **Plan a specificity-repair loop, and reserve a "gatekeeper" design sub-family.** Before submission, run an in-silico alanine/X-scan on your top designs (which binder residues touch D6? what happens with G6?) and kill designs whose specificity rests on shared backbone/anchors. Also include 3–5 designs built with deliberate gatekeeper/salt-bridge arrangements (D6-shape pocket + Arg/Lys) even if their predicted affinity is mid-range — they are the designs that can actually satisfy "no WT binding", and the winner must satisfy it. Precedent for repair: TCR1a7 (structure-guided loop mutations eliminated SMC1A cross-reactivity while retaining avidity). [1,9,14]

---

## 9. Reference list

**De novo pMHC binders (core)**
1. Liu B, Greenwood NF, Bonzanini JE, … Garcia KC, Baker D. *Design of high-specificity binders for peptide–MHC-I complexes.* Science (2025). https://www.science.org/doi/10.1126/science.adv0185 — preprint: https://pmc.ncbi.nlm.nih.gov/articles/PMC11623666/
2. Householder KD, Xiang X, Jude KM, … Garcia KC. *De novo design and structure of a peptide-centric TCR mimic binding module.* Science (2025). https://www.science.org/doi/10.1126/science.adv3813 — PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC12313176/
3. Johansen KH, Wolff DS, Scapolo B, … Jenkins TP. *De novo-designed pMHC binders facilitate T cell–mediated cytotoxicity toward cancer cells.* Science (2025). https://www.science.org/doi/10.1126/science.adv0422 — preprint: https://www.biorxiv.org/content/10.1101/2024.11.27.624796v1
4. Hickok & Stromnes. *Beyond the native repertoire* (Perspective). Science (2025). https://www.science.org/doi/10.1126/science.adz6423
5. Motmaen A, Jude KM, Wang N, … Bradley P. *Targeting peptide–MHC complexes with designed T cell receptors and antibodies* (ADAPT). bioRxiv 2025. https://www.biorxiv.org/content/10.1101/2025.11.19.689381v1 — code: https://github.com/phbradley/ADAPT — data: https://doi.org/10.5281/zenodo.17488258
6. Kempchen TN, … Schmid-Burgk JL, Hölzel M. *Integrated de novo design and high-throughput screening of TCR mimetic minibinders…* (ITOC 2026 abstract P06.04). https://doi.org/10.1136/jitc-2026-itoc.40

**KRAS G12D / A\*11:01 and the campaign target**
7. Poole A, Karuppiah V, … Jakobsen BK. *Therapeutic high affinity T cell receptor targeting a KRAS G12D cancer neoantigen* (JDI TCR; PDB 7OW5/7OW6). Nat Commun (2022). https://www.nature.com/articles/s41467-022-32811-1 — PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC9464187/
8. Zhu J, Chen Z, … Zhao L. *Structure guided analysis of KRAS G12 mutants in HLA-A\*11:01 reveals a length encoded immunogenic advantage in G12D* (PDB 7OW4, 9UV8). Commun Biol (2025). https://www.nature.com/articles/s42003-025-09285-0
9. Han X, Han X, … Shen M. *Identification of novel KRASG12D neoantigen specific TCRs and a strategy to eliminate off-target recognition.* J Transl Med (2025). https://doi.org/10.1186/s12967-025-06094-1
10. Eldaly B, … Baker BM. *Structural insights and immunogenic enhancement of KRAS neoantigen recognition by TCRs* (J Immunol abstract 4724). (2025). https://doi.org/10.1093/jimmun/vkaf283.2359
11. Ng M, … Affini-T Therapeutics. *T cell engagers targeting HLA-A\*11:01 KRAS-G12D and KRAS-G12V mutations* (SITC 2024 #1066). https://jitc.bmj.com/content/12/Suppl_2/A1186
12. Crame K, … Medigene. *Advancing a multi-dimension KRAS mutation-specific TCR library with a 3S TCR targeting G12D* (ESMO 2024 1043P). https://www.annalsofoncology.org/article/S0923-7534(24)02620-6/fulltext
13. DCTY1102 Phase I/II, KRAS/NRAS G12D+ solid tumors. https://clinicaltrials.gov/study/NCT07014878
14. Ahn S, … Jeong B-S. *An integrated in silico–in vitro workflow for discovering high-affinity, selective antibodies to the KRAS(G12D)-MHC I complex* (HLA-C\*08:02). bioRxiv (2025). https://www.biorxiv.org/content/10.1101/2025.08.31.673313v1
15. Wu X, … Kiyotani K. *Engineering T cell-engaging bispecific antibodies targeting KRAS G12V neoantigen across HLA-A\*11:01 and HLA-A\*03:01.* J Immunother Cancer (2026). https://jitc.bmj.com/content/14/10/e016411

**TCR-mimic antibody landscape**
16. *A highly selective TCR-mimic antibody reveals unexpected mechanisms of HBV peptide-MHC recognition…* (MUR35). mAbs (2025). https://doi.org/10.1080/19420862.2025.2562998
17. *Discovery and engineering of bispecific TCR-mimic antibodies targeting peptide–HLA complex* (WT1; X-scan). mAbs (2026). https://doi.org/10.1080/19420862.2026.2731282
18. Yang X, … Garcia KC. *Facile repurposing of peptide–MHC-restricted antibodies for cancer immunotherapy.* Nat Biotechnol (2022). https://www.nature.com/articles/s41587-022-01567-w
19. Hsiue EH, … (p53 R175H TCR-mimic bispecific). Science (2021). https://pure.johnshopkins.edu/en/publications/targeting-a-neoantigen-derived-from-a-common-tp53-mutation/

**Single-point discrimination & prediction**
20. Banerjee A, … *T cell receptor cross-reactivity prediction improved by a comprehensive mutational scan database* (BATMAN/BATCAVE). Cell Systems (2025). https://doi.org/10.1016/j.cels.2025.101345
21. *A biophysical framework to accurately identify antigen single-amino-acid escape variants…* bioRxiv (2026). https://www.biorxiv.org/content/10.64898/2026.02.02.703411v2
22. *Biophysical modeling for accurate T cell specificity prediction of viral and tumor antigens.* Nat Commun (2026). https://www.nature.com/articles/s41467-026-74236-0

**Anthropic × Adaptyv competition & prior competitions**
23. Competition main page. https://proteinbase.com/competitions/anthropic-adaptyv-2026
24. **Challenge 05: KRAS G12D pMHC** (rules, ranking, structures). https://proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/pmhc
25. How designs are selected (Claude selection prompt). https://proteinbase.com/competitions/anthropic-adaptyv-2026/selection
26. EGFR Round 1 results collection. https://proteinbase.com/collections/adaptyv-egfr-competition-round-1
27. Adaptyv. *Protein Optimization 102: Lessons from the protein design competition* (R1 analysis: AF2 hallucination + SolubleMPNN). https://www.adaptyvbio.com/blog/po102
28. Adaptyv. *Protein Design Competition — RESULTS* (R2: 53/378 binders; Cradle, Tihumab, Bustos, Nickel…). https://adaptyvbio.substack.com/p/protein-design-competition-results
29. Adaptyv. *Protein Design Competition: Has binder design been solved?* https://www.adaptyvbio.com/blog/po104
30. Cotet T-S, … *Crowdsourced Protein Design: Lessons From the Adaptyv EGFR Binder Competition* (community paper; BenchBB). bioRxiv (2025). https://www.biorxiv.org/content/10.1101/2025.04.17.648362v2 — blog: https://www.adaptyvbio.com/blog/benchbb/
31. Nipah Competition Results collection (1,196 tested; 111 binders; winners incl. McGibbon, Boyd). https://proteinbase.com/collections/nipah-binder-competition-results
32. UniBio Intelligence. *Computational Design of Nipah Virus Binders: Analysis of the AdaptyvBio Competition Results.* https://unibiointelligence.com/blog/nipah-virus-binder-adaptyv/
33. GEM × Adaptyv RBX1 competition: results collection https://proteinbase.com/collections/gem-x-adaptyv-rbx1-binder-design-competition-results ; participant report (Boltz-2 ipSAE ≈ weak predictor): https://sermare.github.io/data/rbx1_report.pdf
34. Adaptyv. *What does de novo actually mean? Protein novelty in Proteinbase.* https://www.adaptyvbio.com/blog/novelty

**Tools**
35. Watson JL, … Baker D. *De novo design of protein structure and function with RFdiffusion.* Nature (2023). https://www.nature.com/articles/s41586-023-06415-8
36. Bennett NR, … *Improving de novo protein binder design with deep learning* (AF2 initial guess). Nat Commun (2023). https://www.nature.com/articles/s41467-023-38328-5
37. Bennett NR, … Baker D. *Atomically accurate de novo design of antibodies with RFdiffusion* (RFantibody). Nature (2025). https://doi.org/10.1038/s41586-025-09721-5 — preprint https://www.biorxiv.org/content/10.1101/2024.03.14.585103v2
38. Stark H, … *BoltzGen: Toward Universal Binder Design.* (2025). https://boltz.com/boltzgen — code https://github.com/HannesStark/boltzgen
39. Pacesa M, et al. *BindCraft / BindCraft2.* https://github.com/martinpacesa/BindCraft ; https://www.pacesalab.com/bindcraft ; de novo peptide-binder paper https://doi.org/10.1101/2025.07.23.666285

---

*Notes on evidence quality: all quantitative claims above are from the cited sources (peer-reviewed where marked; preprints and conference abstracts as flagged). Paywalled items: Science main texts (abstracts + preprint versions used), JITC/Annals of Oncology abstracts (open), Nature-family papers (open access where noted). The ADAPT tables were extracted from the bioRxiv PDF; the supplementary sequences file (Zenodo) covers only the six successful TCR targets.*
