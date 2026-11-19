# Designed / engineered binders against TfR1 and TfR1-adjacent brain-shuttle receptors

Compiled for the TfR1 apical-domain minibinder campaign (mouse cross-reactivity + pH-switch 7.4→6.0).
Epitope residue lists marked **[derived]** were computed here from the deposited coordinates (heavy-atom
contacts < 4.5 Å, scripts in this directory: `contacts.py`, `map_epitopes.py`) and mapped to UniProt
numbering by sequence alignment (`align_check.py`). Everything else is quoted from the cited source.

---

## A. TfR1 / TFRC / CD71 (the target family itself)

| # | Binder | Length / format | Public ID | Epitope | Species notes | Lesson |
|---|--------|-----------------|-----------|---------|---------------|--------|
| A1 | **Denali ATV / "TV"** (engineered Fc CH3 patch, no insertions) | Fc scaffold; 9-aa CH3 stretch randomized + affinity maturation | Sci Transl Med 2020 [1]; **PDB 6W3H** (3.38 Å) [2]; patents US10457717B2, US12162948 | hTfR1 **apical domain** main-loop region, native numbering ~**197–215** [derived]; Fc side = CH3 EU **383–390 + 413–423** [derived]; away from Tf and FcRn sites; key Fc residue **E387** [3] | Binds **human + cyno**, **not mouse** → work done in hTfR knock-in ("TfR mu/hu KI") mice and cyno [1][32] | An apical, non-Tf-competitive site can be built into native IgG architecture; human/cyno-only reactivity forces KI-mouse translation |
| A2 | **3DS18** (parent **2DS25**, matured **2DS25.3/.5**) — Baker lab/IPD de novo miniprotein | **93 aa** (6WRV); β-sheet "extension" designs | PNAS 2021 [10] (PMID 33879614); **PDB 6WRV** (2.47 Å) [11] | hTfR1 apical **197–215** (incl. 207–212), **340–348** (E343/K344/N348 = H-ferritin patch), **371–376** (K374), plus helical-domain contacts **619–651** [derived] | Only human TfR reported; **no mouse data** | First public de novo miniprotein vs TfR1; maturation was essential (µM → ~20 nM); designed β-strand pairing spans two subdomains; does **not** avoid the ferritin patch |
| A3 | **TfRB1G3** — cystine-dense peptide (CDP, 3 disulfides) from *M. brevicollis* cytochrome BC1 subunit 6 | **49 aa** | JMB 2020 [16] (PMID 32304700); **PDB 6OKD** | **Transferrin-competitive** — footprint overlaps the Tf site on the helical/protease-like region (helical groove hotspot) [12][16] | **Murine cross-reactive** (conserved epitope); dosed in WT mice; CNS ≈25% of blood levels | Transferrin-competitive epitopes are conserved → easy mouse cross-reactivity, but Tf competition is the risk (fast k_on vs Tf compensated); 49-aa disulfide scaffolds can reach pM (Kd 216 pM) |
| A4 | **8D3** (rat anti-mouse TfR1 mAb; Fab/chimeric formats; model shuttle) | Fab 2.9 Å cryo-EM; bivalent/monovalent formats | Cryo-EM bioRxiv 2026 [12]; PDB **29GF** (stated, not yet downloadable); Addgene 254690/254707/254710/254711; original mAb Kissel 1998 (PMID 9681691) | mTfR1 apical **main loop 206–212** (N209-G210-N211 motif) + **minor loop 371–373**; VH-dominated (480 Å² vs 200 Å² VL); VH Y103→N209, G33/P99→N211, Y52/Y53→V206/L212 | **Mouse-specific**: N209G or N211L (mouse→human) **ablate** binding; human equivalent motif is G207-R208-L209 (+ steric clash from R208) [12] | **pH lesson**: structure-guided combinatorial His-scanning → graded pH-selectivity; variants binding *better* at endosomal pH 5.5 than 7.4 showed **reduced** brain penetration in vivo — the opposite polarity (bind 7.4, release 5.5) is the supported direction. Also: 8D3 geometry permits only paired cross-linking → no receptor clustering/degradation (valency lever) |
| A5 | **ch128.1** (chimeric mouse/human anti-hTfR1 IgG1/IgG3) | IgG; 5.7 nM | Nat Commun 2022 [13]; **PDB 6WLA** (Fab only; complex is a docking model) | hTfR1 **S324–S368** (apical); overlaps MACV GP1 site and **partially** H-ferritin residues **E343/K344/N348**; does not block Tf/HFE [13] | Human + Old World NHP (rhesus, African green); not guinea pig/mouse → hTfR1 transgenic mice for efficacy [13] | Apical binders overlapping the ferritin patch are tolerated when Tf binding is preserved ("partial" H-Ft inhibition); species scope is set by apical-loop sequence |
| A6 | **h26D3 / WO2024200271A1** anti-TfR1 antibody (non-apical) | IgG/scFv, CDRs published as SEQ ID NOs | WO2024200271A1 [15] | **Protease-like domain**: hTfR1 residues 150, 151, 154, 158, 159, 161, 163, 385 (SEQ ID NO:85 numbering) | Not stated (human-focused) | The only public binder class that explicitly avoids Tf **and** ferritin **and** HFE; patent reviews the class I–IV epitope taxonomy (WO2014/189973: I–III apical, IV non-apical) and the apical-domain safety concerns (reticulocyte drop/acute signs, Couch 2013) [15] |
| A7 | **Cross-species VHH** (camelid) | VHH (~15 kDa), VHH-Fc mono/homodimer | bioRxiv 2025 [22] | **Novel site at the TfR1 dimer interface** | **Cross-reactive: rodent + rhesus + human**; in vivo in WT mice | Efficient transcytosis correlated with **intermediate affinity + fast dissociation**; cross-species binding preserved after engineering — a template for a cross-species TfR1 minibinder |
| A8 | **NewroBus** humanized TfR1 nanobodies | VHH; humanized (AbNatiV) | bioRxiv 2025 [23] | Not mapped; selected for non-interference with Tf binding/iron uptake | Tested in **humanized TfR1 knock-in rats**; no hematological toxicity in chronic dosing | Non-competitive + humanized + KI-rat validation path; TNFα-inhibitor cargo shows functional shuttle readout |
| A9 | **OTV** (oligonucleotide transport vehicle, Denali) | Engineered Fc (TV) + ASO | Sci Transl Med 2024 [32] | TfR1 apical (TV lineage) | TfR mu/hu KI mice + cynomolgus | Systemic TV beats intrathecal ASO on distribution; lower affinity > high-affinity bivalent antibody for delivery |
| A10 | **TRANSPEP / TRANSMAB** (Imnewrun) | "de novo" TfR1-binding peptides, multivalent fusions | Company site only [33] | Claimed "dense receptor cluster" binding | Claimed preserved TfR1 expression/reduced reticulocyte toxicity | Company claim — **no sequence, structure or peer-reviewed ID published**; treat as unverified |

## B. CD98hc / SLC3A2 / 4F2

| # | Binder | Length / format | Public ID | Epitope | Species notes | Lesson |
|---|--------|-----------------|-----------|---------|---------------|--------|
| B1 | **Denali TV6 family (TV6, TV6.6, TV6.8)** — engineered Fc CH3 β-sheet surface (11-aa patch) | Fc; Kd 20 nM–2.1 µM (human), 205 nM–6 µM (cyno) | Nat Commun 2023 [4]; **PDB 8G0M** (TV6.6–hCD98hc ECD, 2.25 Å) [5] | CD98hc **structured loop adjacent to the α/β barrel**, native numbering ~**375–401** (+ contacts 128–135) [derived]; Fc side CH3 ~**380–387 + 422–440** [derived] | **Human + cyno only**; mouse ECD 71.9% identity → CD98hc mu/hu knock-in mice [4] | Slower uptake, much longer brain retention than TfR; lower parenchymal engagement (specificity); loop-based Fc libraries failed first — β-sheet surface worked |
| B2 | **Genentech/UCSF CD98hc bispecific shuttles** (2×1 scFv-on-IgG) | scFv + knob-into-hole IgG | Cell Chem Biol 2023 [6]; GenBank **OR253073–OR253075** (public sequences) | **Unknown** (stated by authors) | Anti-**mouse** CD98hc (rat mAb) → WT mouse studies | Public sequence enabled reproduction; monovalent/low-affinity shuttle + bivalent cargo; brain retention far longer than TfR shuttles; CD98hc transcytosis mechanism still unclear |
| B3 | **Active-learning evolved anti-CD98hc antibodies (e.g. D4-4, 3.5D19, 3.5D5)** | IgG; start = fully human anti-hu/cyno clone, no mouse binding | Nat Biomed Eng 2026 [9] | Similar epitopes across evolved clones | **Mouse + cyno + human at similar affinities** — eliminates KI mice and surrogate clones; validated in humanized-CD98hc mice | The canonical cross-species engineering precedent: single-His scan of HCDR3 → 10 permissive sites → soft-randomization + HCDR1/2 and LCDR1/3 libraries → shuffle + co-select on both orthologues. No structure required; HCDR3 alone was insufficient |
| B4 | de novo designed miniproteins vs CD98hc | — | — | — | — | **Gap: none published** (searches of literature + PDB 2023–2026 found only Fc-engineered TVs and antibodies) |

## C. INSR (insulin receptor)

| # | Binder | Length / format | Public ID | Epitope | Species notes | Lesson |
|---|--------|-----------------|-----------|---------|---------------|--------|
| C1 | **InsulinR_mb** — de novo miniprotein (HHHH topology), antagonises insulin site | ~65 aa; SC50 800 nM → Kd **210 ± 39 nM** after 10 mutations | Nature 2022 [17]; sequences in ESM Table 1 [18] | **L1 domain**, native insulin-binding site (design started from 4OGA/4ZXB) | Human ECD used | Even a "good" target gave only ~200 nM after maturation; useful as a site-1 module rather than a drug |
| C2 | **S2B** (F1/FnIII-1 site-2 binder) + fusions **S2-F1-S1, RF-405, RF-409** | 65 aa (9DNN chains E/F); Kd 1.9 nM (S2B), 0.37 / 1.3 / 8.1 nM (fusions); stable to 95 °C | Mol Cell 2025 [19]; bioRxiv [20]; **PDB 9DNN, 9DN6, 9DNI** [21] | IR **FnIII-1 (F1) ~503–581** + L1 C-terminal contacts ~178–181 [derived]; fusions link F1' + L1 to fix active-state geometry | Cryo-EM with human and **mouse IR (94% identity)**; in vivo glucose lowering in mice; fusions do **not** bind IGF1R | Two-site binder **fusions** are the design variable that converts binding into signalling (super-agonist / partial agonist / antagonist by linker rigidity); receptor conformational dynamics, not just affinity, is the design target |
| C3 | **RFdiffusion InsR campaign** | 50–100 aa binders | Nature 2023 (RFdiffusion, PMC10468394) | Insulin receptor, unspecified surface | Not reported | ~19% experimental success across 5 targets, nanomolar affinities **without** optimisation — the modern baseline success rate for de novo miniprotein campaigns |
| C4 | **Protein CREATE** (LLM + phage display) | designed binders | PMC11722223 [34] | Multiple contact modes found on IR | Not reported | Closed-loop LLM design-build-test; iPTM pre-screening is imperfect (neither guarantees nor excludes binding) |

## D. IGF1R

| # | Binder | Length / format | Public ID | Epitope | Species notes | Lesson |
|---|--------|-----------------|-----------|---------|---------------|--------|
| D1 | **IGF1R_mb** — de novo miniprotein (HHH topology), targets IGF1 site | ~62 aa; library SC50 **10 µM** → Kd **860 ± 270 nM** after 11 mutations | Nature 2022 [17]; sequences in ESM Table 1 [18] | IGF1-binding site (design started from 5U8R) | Human ECD | Hardest of the 13 Cao targets — shallow surface, only nM-μM after maturation. Set expectations for any IGF1R-adjacent campaign |
| D2 | **Grabody-B** (ABL Bio) — anti-IGF1R scFv shuttle fused to therapeutic IgG | scFv + engineered Fc (plasma stability) | Cell Rep Methods 2022 [35]; Alzforum 2025 [36]; ABL301 Phase 1 (Sanofi); GSK licence 2025 | Not published | **Broad cross-species reactivity**; does not interfere with IGF1R signalling | Different transcytosis route (clathrin + caveolin + FEME; internalisation in ~30 s vs 30–120 min for TfR/CD98hc shuttles) and stable brain penetration in aged mice — a reminder that route, not only affinity, sets delivery |

## E. LRP1 (no de novo designed binders; peptide/nanobody level)

| # | Binder | Length / format | Public ID | Epitope | Species notes | Lesson |
|---|--------|-----------------|-----------|---------|---------------|--------|
| E1 | **Angiopep-2** | 19-mer peptide (TFFYGGSRGKRNNFKTEEY), aprotinin Kunitz-derived | Demeule 2008 [37]; reviews [28] | LRP1 (competes with activated α2-macroglobulin) | Works across bovine/rat/mouse/human models; ANG1005 Phase II | Sequence-level shuttle, not structure-designed; the benchmark for LRP1 |
| E2 | **KS-487** | 15-mer cyclic peptide | BB Reports 2022 [30] | LRP1 **cluster IV** (EC50 10.5 nM) | Rat + monkey BBB models; stable in mouse plasma | Outperformed Angiopep-2 and L57 in permeability — cyclic, protease-stable formats win on LRP1 |
| E3 | **dAb D11** | single-domain antibody (Kd 183 nM) | J Drug Target 2024 [31] | LRP1 (phage display, in vitro BBB model) | Mouse biodistribution | First LRP1 dAb with BBB permeability; weak affinity still delivered |
| E4 | — | — | — | — | — | **Gap: no de novo designed miniprotein vs LRP1 published**; LRP1 mid-avidity lesson (polymersomes, STTT 2025) — mid-avidity favours PACSIN2 transcytosis and preserves receptor; high avidity drives lysosomal degradation and receptor downregulation |

## F. Cross-cutting pH-switch precedents (directly relevant to the 7.4→6.0 objective)

| # | Binder | Format | Public ID | Result | Lesson |
|---|--------|--------|-----------|--------|--------|
| F1 | **F06 (YU904-F06)** | bivalent anti-TfR IgG | mAbs 2025 [24] | Strong pH sensitivity: binds at 7.4, binding "strikingly reduced" at 5.2, none at 4.0; efficient transcytosis in two in vitro BBB models; Roche Brainshuttle much less pH-sensitive | Strongest antibody evidence that **release at acidic endosomal pH** rescues the lysosomal-degradation penalty of a high-affinity bivalent binder |
| F2 | **M1 nanobody variants (R56H/P96H/Y102H)** | mTfR-binding nanobody + cargo | Fluids Barriers CNS 2023 [25] | ~3× greater unbinding at pH 5.5 vs 7.4; >8 °C neurotensin hypothermia; 3.5% ID/g brain; saturation-limited | Closest **minibinder-scale** in vivo pH-switch precedent; His-cluster engineering is the practical route |
| F3 | **M16 scFv** | anti-TfR scFv, His-saturated CDRH1 | PLOS One 2016 [26] | 2.6× more internalised; effect abolished by bafilomycin (acidification-dependent) | Early proof that pH-dependent unbinding changes trafficking, not just affinity |
| F4 | **8D3 His-scan variants** | IgG variants | bioRxiv 2026 [12] | Variants preferring pH 5.5 over 7.4 had **reduced** brain penetration; paper supports the 7.4-preferring polarity but could not test it; could **not** reproduce pH-sensitivity of two previously published "pH-selective" anti-TfR antibodies | **Polarity matters**: only the bind-at-7.4 / release-at-5.5–6.0 direction is supported. Re-validate published pH claims in-house |

## G. Reviews / comparative sources on shuttle strategy

- Choi & Shusta, *Expert Opin Drug Deliv* 2023 [27] — antibody discovery/engineering/validation for BBB RMT (incl. emerging targets).
- WO2024200271A1 [15] — explicit apical vs protease-like-domain rationale; class I–IV epitope taxonomy; ferritin/Tf interference arguments.
- 8D3 bioRxiv 2026 [12] — the two-hotspot framing of all known hTfR1 complexes: **helical groove** (HFE, Tf, DNA aptamer, cystine-dense peptide shuttle) vs **apical domain** (MACV GP1, *P. vivax*, 3DS18, Denali Fc, parvovirus B19).
- Pharmaceutics 2022 review [38] — kinetics of TfRMAb transport; apical domain = TfRMAb site, holo-Tf binds protease-like + helical.
- Fluids Barriers CNS 2025 [29] — dose, valency and affinity effects on TfR-mediated delivery in vivo.
- Cell Reports 2025 [7] and 2025 biodistribution paper [8] — dual TfR+CD98hc TVs and organ/parenchymal-level comparison of the two platforms.

## H. Verified sequence-level facts for the campaign

- **Species numbering anchor (verified by UniProt alignment, `align_check.py`):** hTfR1 **K344 ↔ mTfR1 K346** and hTfR1 **K374 ↔ mTfR1 K376** (mouse = human + 2 in this region). Both are lysines in both species → a conserved anchor patch.
- The 8D3 "minor loop" region: mouse 373–375 (Q-N-V) aligns to human 371–373 (K-N-V); human K374 = mouse K376.
- **Fc numbering** in 6W3H/8G0M is EU-like; 6W3H additionally carries **YTE (M252Y/S254T/T256E)**; 6W3H chains A and B are sequence-identical.
- **Denali TV patch (6W3H) vs WT Fc (4W4O)**: N384Y, Q386T, P387E, E388W, N389S, N390S, D413T, R416E, N421F (plus the YTE set) — consistent with "nine amino acids randomized in CH3, affinity-matured; key residue E387" [3].
- **CD98hc TV6.6 patch (8G0M) vs WT Fc**: 380L, 382N, 384R, 385F, 386V, 387L, 422I, 424A, 426N, 428Y, 438F, 440N, 442A — the β-sheet surface described in [4].
- **Cao 2022 sequences (public, ESM Table 1 [18]):**
  - InsulinR_mb optimized (65 aa): `DEELMELVYEAVEKNDPELLFEAWMELASLLDETGDPKIEEALGLLQQVDGGNPDAGRRIKELFK`
  - IGF1R_mb optimized (62 aa): `STRNAEFIMLLLELCVKSKNDPQVQEYVKKVKKQVERLVGNGDEKKAEEVARKALEYCADG`

## I. Transferable lessons for a TfR1 apical-domain minibinder (mouse cross-reactivity + pH switch)

1. **Epitope choice sets cross-species reach.** The immunodominant apical main loop (mouse 206–212) is *not* conserved (mouse N-G-N vs human G-R-L; N209G/N211L ablate 8D3 [12]). The conserved apical anchors are the lysine patches **K344/K346** and **K374/K376** — the same region 3DS18 and the Denali Fc both contact [derived].
2. **But K344 sits in the H-ferritin patch** (E343/K344/N348, ch128.1 [13]) — expect partial H-Ft inhibition; that was tolerated in vivo.
3. **pH polarity: bind 7.4, release 5.5–6.0** is the supported direction [12][24][25]; the reverse polarity loses brain penetration. Validate pH-sensitivity with your own assay (published pH claims failed to replicate in [12]).
4. **Affinity window:** low-digit nM + bivalency → lysosomal sorting; intermediate affinity/fast off-rate correlates with better transcytosis [12][22]. For a monovalent minibinder the pH switch, not avidity, is the main trafficking lever.
5. **Cross-species strategies, in order of published success:** (a) evolve cross-reactivity directly (Tessier active learning on CD98hc [9]; Grabody-B IGF1R [35]); (b) target conserved surfaces (CDP/Tf-competitive [16]; cross-species VHH at the dimer interface [22]); (c) two-clone/species-panel (OX26/8D3/R17-217 tradition) or KI-mouse + human/cyno binder (Denali TfR [1] and CD98hc [4]).
6. **Scaffold options with precedent:** Fc-CH3 patch (no new fold, native IgG [1][4]); 93-aa de novo β-sheet-extension miniprotein needing maturation to ~20 nM [10]; 49-aa disulfide-dense peptide reaching pM on a conserved epitope [16].
7. **Do not expect the receptor to tolerate clustering:** 8D3 geometry supports only paired cross-linking without degradation [12]; bivalent high-affinity TfR binders are degraded (8D3 paper refs) — keep the minibinder monovalent.

---

## Sources

[1] https://doi.org/10.1126/scitranslmed.aay1359 — Kariolis 2020 Sci Transl Med - ATV Fc BBB transport vehicle (6W3H)
[2] https://www.rcsb.org/structure/6W3H — PDB 6W3H - ATV Fc + hTfR apical domain
[3] https://doi.org/10.1016/j.cell.2020.06.041 — Cell preview 2020 - Therapeutic TVs for Crossing Barriers in the Brain
[4] https://www.nature.com/articles/s41467-023-40681-4 — Nat Commun 2023 - CD98hc is a target for brain delivery (TV CD98hc, 8G0M)
[5] https://www.rcsb.org/structure/8G0M — PDB 8G0M - TV6.6 Fc + CD98hc ECD
[6] https://doi.org/10.1016/j.chembiol.2023.09.008 — Cell Chem Biol 2023 - bispecific CD98hc shuttles (GenBank OR253073-75)
[7] https://doi.org/10.1016/j.celrep.2025.116038 — Cell Reports 2025 - dual TfR+CD98hc transport vehicle
[8] https://pmc.ncbi.nlm.nih.gov/articles/PMC11842567 — 2025 - ATV TfR vs ATV CD98hc biodistribution
[9] https://www.nature.com/articles/s41551-026-01718-3 — Nat Biomed Eng 2026 - CD98hc shuttles with broad cross-species reactivity (Tessier)
[10] https://doi.org/10.1073/pnas.2021569118 — Sahtoe 2021 PNAS - TfR targeting by de novo sheet extension (2DS25/3DS18)
[11] https://www.rcsb.org/structure/6WRV — PDB 6WRV - 3DS18 + hTfR ectodomain
[12] https://www.biorxiv.org/content/10.64898/2026.06.30.735565v1.full — 2026 bioRxiv - molecular mechanism of action of 8D3 (mTfR1 cryo-EM, PDB 29GF)
[13] https://www.nature.com/articles/s41467-021-27949-3 — Nat Commun 2022 - ch128.1 apical-domain docking, 6WLA
[15] https://patents.google.com/patent/WO2024200271A1/en — WO2024200271A1 - anti-TfR1 protease-like domain binder
[16] https://doi.org/10.1016/j.jmb.2020.04.002 — JMB 2020 - TfR-binding cystine-dense peptide TfRB1G3 (PDB 6OKD)
[17] https://www.nature.com/articles/s41586-022-04654-9 — Cao 2022 Nature - miniprotein binders incl. InsulinR_mb, IGF1R_mb
[18] https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-022-04654-9/MediaObjects/41586_2022_4654_MOESM1_ESM.pdf — Cao 2022 ESM Table 1 - binder sequences
[19] https://doi.org/10.1016/j.molcel.2025.09.020 — Wang 2025 Mol Cell - de novo designed insulin receptor agonists (S1B/S2B)
[20] https://doi.org/10.1101/2024.10.07.617068 — Wang 2024 bioRxiv - Tuning insulin receptor signaling (preprint)
[21] https://www.rcsb.org/structure/9DNN — PDB 9DNN - IR + insulin + S2B
[22] https://www.biorxiv.org/content/10.1101/2025.05.23.649291v3 — 2025 bioRxiv - cross-species TfR1 VHH (dimer-interface epitope)
[23] https://www.biorxiv.org/content/10.1101/2025.04.20.649139 — 2025 bioRxiv - NewroBus humanized TfR1 nanobodies
[24] https://doi.org/10.1080/19420862.2025.2563758 — mAbs 2025 - pH-sensitive bivalent anti-TfR antibody F06
[25] https://pmc.ncbi.nlm.nih.gov/articles/PMC10463325 — Fluids Barriers CNS 2023 - pH-sensitive mTfR nanobody M1 R56H/P96H/Y102H
[26] https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0145820 — PLOS One 2016 - anti-TfR scFv M16 pH-sensitive engineering
[27] https://pmc.ncbi.nlm.nih.gov/articles/PMC10842915 — Choi & Shusta 2023 - review: antibody strategies for BBB RMT
[28] https://www.mdpi.com/1999-4923/14/9/1874 — Pharmaceutics 2022 - Peptide shuttles for BBB drug delivery
[29] https://doi.org/10.1186/s12987-025-00643-y — Fluids Barriers CNS 2025 - dose, valency, affinity effects on TfR delivery
[30] https://doi.org/10.1016/j.bbrep.2022.101367 — BB Reports 2022 - KS-487 LRP1-binding cyclic peptide
[31] https://pubmed.ncbi.nlm.nih.gov/39618311 — J Drug Target 2024 - LRP1-binding dAb D11
[32] https://www.science.org/doi/10.1126/scitranslmed.adi2245 — Sci Transl Med 2024 - TfR1 oligonucleotide transport vehicle (OTV)
[33] https://www.imnewrun.com/science — Imnewrun TRANSPEP/TRANSMAB de novo TfR1 peptide binders (company claim)
[34] https://pmc.ncbi.nlm.nih.gov/articles/PMC11722223 — Protein CREATE - LLM-designed binders to IL-7Ra and insulin receptor
[35] https://doi.org/10.1016/j.crmeth.2022.100338 — Shin 2022 Cell Rep Methods - Grabody B IGF1R-based shuttle
[36] https://www.alzforum.org/news/conference-coverage/tfr-no-longer-lone-star-new-shuttles-use-other-keys-unlock-brain — Alzforum 2025 - shuttles beyond TfR (Grabody B, CD98hc)
[37] https://doi.org/10.1111/j.1471-4159.2008.05492.x — Demeule 2008 - Angiopep-2 LRP1 transcytosis
[38] https://www.mdpi.com/1424-8247/15/1/3 — Pharmaceutics 2022 - kinetics of BBB transport of monoclonal antibodies
