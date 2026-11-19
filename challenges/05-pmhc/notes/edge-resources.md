# Challenge 5 edge resources - HLA-A*11:01 decoys, WT-vs-G12D presentation, community sweep

Prepared 2026-10-30 ~14:15 CET. All items verified live on 2026-10-30 unless marked; read-only; no logins. Scratch artifacts: ~/.hermes/cache/scratch/c5/.

## 1. Decoy-panel data resources for HLA-A*11:01

### 1.1 HLA Ligand Atlas (benign-tissue immunopeptidome, MS)
- What it is: 90,428 HLA-I and 142,625 HLA-II naturally presented peptides across 29 tissues (release 2020.12; Marcu et al., J Immunother Cancer 2021).
- HLA-A*11:01 counts (computed 2026-10-30 from the release tables): 40,827 distinct HLA-I peptide sequences across 6 A*11:01 donors (AUT01-DN02 6,475; AUT01-DN03 10,019; AUT01-DN05 11,274; AUT01-DN12 18,124; AUT01-DN13 12,987; OVA01-DN281 4,661) and 72,627 distinct HLA-II peptides. The sample_hits table has 967,449 rows.
- URL: https://hla-ligand-atlas.org/ ; downloads: https://hla-ligand-atlas.org/downloads ; machine-readable tables: https://hla-ligand-atlas.org/rel/2020.12/sample_hits.tsv.gz (also peptides.tsv.gz, donors.tsv.gz).
- License: CC-BY 4.0 (https://hla-ligand-atlas.org/license).
- Local artifact: a11_ligands_hla_ligand_atlas.tsv = the 40,827 A*11:01 HLA-I sequences, ready as a decoy base list.
- 2025 extension: HLA Ligand Atlas DIA (higher-sensitivity DIA runs; 28 DIA runs) - https://doi.org/10.1136/jitc-2025-012083 (PMID 40887106; data also at PRIDE PXD024837, PXD024809, PXD020186).

### 1.2 IEDB (curated MHC ligand assays)
- Export page (CC-BY 4.0): https://www.iedb.org/database_export_v3.php
- HLA-A*11:01 counts (computed 2026-10-30 from the mhc_ligand_full TSV export; 6,275,428 rows in the whole file): 54,889 assay rows with MHC restriction exactly HLA-A*11:01; 46,967 positive (incl. 1,648 high, 1,294 intermediate, 1,245 low) and 3,735 negative; 18,256 distinct epitope sequences overall (12,231 with at least one positive assay); 11,551 distinct sequences seen by MS-based methods (11,548 positive); 3,000 distinct sequences with at least one negative assay (useful decoys).
- File URL: https://www.iedb.org/downloader.php?file_name=doc/mhc_ligand_full_tsv.zip (309 MB; also mhc_ligand_full.xlsx 1 GB, mhc_ligand_full_single_file.zip, mhc_ligand_full_json.zip 548 MB).
- Note: the older mhc_ligand_full.csv.zip name is no longer served (probe 2026-10-30 returned an HTML page, 0 bytes).
- Bonus tool: hitlist (PyPI) builds allele-resolved IEDB+CEDAR peptide lists, e.g. hitlist export binding --mhc-allele HLA-A*11:01 - https://pypi.org/project/hitlist/ (merged totals: 2,672,046 observations; 748,386 unique peptides; 579,096 mono-allelic observations across 119 alleles).

### 1.3 SysteMHC Atlas v2.0
- New home (old systemhcatlas.org is retired): https://systemhc.sjtu.edu.cn/ ; statistics: https://systemhc.sjtu.edu.cn/stats
- Counts (statistics page v.231201, retrieved 2026-10-30 via indexed snapshot; direct fetch was intermittent): human MHC-I - 1,785 unique samples, 1,354,052 unique peptides, 449,731 binders, 149 unique alleles. Update V2024-0601 added 1,192 raw files (41.9M MS/MS spectra) with 280,126 peptides. Paper: NAR 2024, doi 10.1093/nar/gkad1068 (7,190 MS files, 303 allotypes).
- HLA-A*11:01-specific slice: available through the site allele-stats/search UI; NOT extracted here (JS UI and intermittent reachability) - marked unverified.

### 1.4 PRIDE / ProteomeXchange datasets (best 5 for A*11:01)
- PXD028985 - influenza A/B immunopeptidome of C1R-A*11:01; 7 datasets (3 uninfected, 2 IAV, 2 IBV) - https://www.ebi.ac.uk/pride/archive/projects/PXD028985 (Habel et al. 2022, PLoS Pathog; PMC8929706).
- PXD051538 - EBV peptides from HLA-A*11:01/A*02:01 NPC cell lines; median 3,422 peptides per sample (range 1,106-5,830) - https://www.ebi.ac.uk/pride/archive/projects/PXD051538 (Wang et al. 2024, Viruses 16:669).
- PXD019643 + PXD020186 - raw MS behind the HLA Ligand Atlas (includes the 6 A*11:01 donors) - https://www.ebi.ac.uk/pride/archive/projects/PXD019643 (Marcu et al. 2021).
- PXD024837 - Ligand Atlas DIA extension (28 DIA runs) - https://www.ebi.ac.uk/pride/archive/projects/PXD024837
- PXD074199 - 2026 ultra-sensitive targeted immunopeptidomics workflow - https://www.ebi.ac.uk/pride/archive/projects/PXD074199 (Forster et al. 2026, Mol Cell Proteomics 25:101634).
- Also seen: PXD033407 (vaccinia surface/immunopeptidome resource incl. A*11:01), PXD055544 (neoantigen/TCR cohort).

### 1.5 Presentation predictors with A*11:01 coverage
- NetMHCpan-4.2 (current; 4.1b still downloadable): web server https://services.healthtech.dtu.dk/services/NetMHCpan-4.2/ ; A*11:01 is in the allele list on the page. Academic license + download form, e.g. Linux 4.2e: https://services.healthtech.dtu.dk/cgi-bin/sw_request?software=netMHCpan&version=4.2&packageversion=4.2e&platform=Linux (also 4.2estatic Linux; NetMHCpan-4.1b Linux via packageversion=4.1b).
- MHCflurry 2.3.16 (released 2026-10-20): affinity + processing + presentation - https://github.com/openvax/mhcflurry ; install: pip install mhcflurry>=2.3,<2.4 ; then: mhcflurry downloads fetch models_class1_presentation ; A*11:01 is present in the class-1 allele sets (verify locally with mhcflurry --list-supported-alleles).
- Alternatives: PRIME https://github.com/GfellerLab/PRIME ; MixMHCpred https://github.com/GfellerLab/MixMHCpred ; BigMHC https://github.com/KarchinLab/bigmhc

### 1.6 Pre-built A*11:01 peptidome lists
- Computed here (ready to use): 40,827 HLA-I A*11:01 sequences from the Ligand Atlas (a11_ligands_hla_ligand_atlas.tsv in the scratch dir).
- IEDB: 18,256 distinct A*11:01 epitopes (12,231 positive; 11,551 MS-observed) - extract from the TSV export (Epitope Name column; MHC Restriction Name = HLA-A*11:01).
- SysteMHC: allele-resolved lists via web UI (not extracted here).
- hitlist: per-allele exports (see 1.2).

### Resource table (section 1)

| resource | what it gives | URL | notes |
| --- | --- | --- | --- |
| HLA Ligand Atlas | 40,827 A*11:01 HLA-I + 72,627 HLA-II ligand sequences (computed from release 2020.12) | https://hla-ligand-atlas.org/downloads | CC-BY 4.0; tables under /rel/2020.12/; A*11:01 HLA-I list saved locally |
| HLA Ligand Atlas DIA | higher-sensitivity DIA runs (28) + JY dilution data | https://doi.org/10.1136/jitc-2025-012083 | JITC 2025; PRIDE PXD024837 / PXD024809 / PXD020186 |
| IEDB mhc_ligand_full | 54,889 A*11:01 assay rows; 18,256 distinct epitopes (12,231 positive; 3,000 with negative assays) | https://www.iedb.org/downloader.php?file_name=doc/mhc_ligand_full_tsv.zip | 309 MB TSV; 6,275,428 rows total; CC-BY 4.0; counts computed 2026-10-30 |
| SysteMHC Atlas v2.0 | human MHC-I: 1,354,052 unique peptides (449,731 binders; 149 alleles) | https://systemhc.sjtu.edu.cn/stats | allele-level A*11:01 counts via UI; site intermittent on 2026-10-30 |
| PRIDE PXD028985 | A*11:01 immunopeptidome in influenza infection (C1R-A*11:01); 7 datasets | https://www.ebi.ac.uk/pride/archive/projects/PXD028985 | Habel 2022 PLoS Pathog; small mono-allelic set |
| PRIDE PXD051538 | EBV A*11:01/A*02:01 peptides; median 3,422 peptides per sample | https://www.ebi.ac.uk/pride/archive/projects/PXD051538 | Wang 2024 Viruses 16:669 |
| PRIDE PXD019643 / PXD020186 | raw MS of the HLA Ligand Atlas (DDA) | https://www.ebi.ac.uk/pride/archive/projects/PXD019643 | includes the 6 A*11:01 donors |
| PRIDE PXD074199 | 2026 targeted immunopeptidomics workflow (optiPRM+) | https://www.ebi.ac.uk/pride/archive/projects/PXD074199 | Forster 2026 Mol Cell Proteomics |
| NetMHCpan-4.2 | A*11:01 binding/presentation predictor | https://services.healthtech.dtu.dk/services/NetMHCpan-4.2/ | academic license; sw_request packages 4.2e/4.2estatic Linux; 4.1b also available |
| MHCflurry 2.3.16 | affinity + processing + presentation (A*11:01 supported) | https://github.com/openvax/mhcflurry | pip install; fetch models_class1_presentation; release 2026-10-20 |
| hitlist | builds per-allele IEDB+CEDAR peptide lists for decoys/training | https://pypi.org/project/hitlist/ | 748,386 unique peptides merged; per-allele export filter |
| Computed A*11:01 list (local) | 40,827 sequences ready as decoy panel | https://hla-ligand-atlas.org/rel/2020.12/sample_hits.tsv.gz | derived from this table + peptides table; file in scratch dir |

## 2. WT vs G12D presentation biology on HLA-A*11:01 (and the C*08:02 contrast)

### 2.1 Zhu et al. 2025 (Commun Biol 9:26; doi 10.1038/s42003-025-09285-0; PMID 41339521; PMC12774912)
- URL: https://www.nature.com/articles/s42003-025-09285-0
- G12D uniquely destabilizes the HLA-A*11:01 complex through the buried aspartate side chain (NMR chemical-shift mapping across G12C/R/V/D/A/S; G12D induced the most pronounced changes).
- G12D presents in two registers: 9-mer VVGADGVGK (bent, TCR-incompatible) vs 10-mer VVVGADGVGK (compact, stable, TCR-accessible; the challenge target).
- Quantitative (read from the published figures 2026-10-30): MM/GBSA binding free energy ~ -122.5 kcal/mol (10-mer) vs ~ -108.1 kcal/mol (9-mer), Fig 5B; TCR binding 92.9% vs 1.89% positive cells, Fig 4A/B; CHX chase (Fig 3G/H): the G12D complex degrades fastest - ~50% remaining at ~12 h and ~15-20% at 48-60 h (****), vs ~45-75% at 60 h for G12C/R/V/A/S. No WT lane in that assay; WT comparison comes from NMR/MD.
- New PDB structures: 9UV8 (A*11:01 + G12D 9-mer); 7OW4 (G12D 10-mer, previously determined); 8K4T/8K4V/8K50 (G12C/G12R/G12V); 9WVE/9WVF (G12A/G12S 10-mers).
- Paper framing: G12D is a challenging target on A*11:01 with suboptimal antigen presentation and reduced MHC-I complex stability.

### 2.2 The discriminating-binder precedent: JDI TCR (Nat Commun 13:5333, 2022; PMID 36088370; PMC9464187)
- URL: https://www.nature.com/articles/s41467-022-32811-1
- Affinity-enhanced TCR against VVVGADGVGK/HLA-A*11:01: KD 64 +/- 10 pM for G12D vs 425 +/- 15 nM for WT - a >6,000-fold specificity window; IFN-gamma release only with the G12D decamer; crystal structures show few direct TCR-pMHC contact differences, with specificity driven by indirect electrostatic interactions/MD.
- This is the strongest public evidence that G12D-vs-WT discrimination on A*11:01 is achievable (with a TCR scaffold).

### 2.3 HLA-C*08:02 contrast (Tran 2016 NEJM; Sim et al. 2020 PNAS; eLife 2022)
- URLs: https://www.pnas.org/doi/10.1073/pnas.1921964117 and https://pmc.ncbi.nlm.nih.gov/articles/PMC9177145
- On C*08:02, only the mutant G12D peptides (9-/10-mer) stabilize the allele, via the p3 Asp anchor salt bridge to HLA-C; the WT peptide (Gly at p3) does not stabilize the allele and is effectively not presented. Mutant-only presentation there is solved by allele biology, not by binder discrimination.
- Quantitative anchors: WT-KRAS peptides gave no C*08:02 stabilization (flow cytometry and recombinant refolds); G12D 9-mer stabilizes C*08 but not C*05 while the 10-mer stabilizes both; TCR9a/TCR10 affinities nM to low microM; an A18L nonamer variant improved stabilization and TCR9a EC50 ~20-fold.
- Zhu et al. discussion: C*08:02 places Asp12 at p3 as an anchor; in A*11:01 the same Asp shifts to p6 and is buried - a different structural situation.

### 2.4 G12D presentation on A*11:01 is real; WT is a genuine counter-target
- Choi et al. 2021 (PMC9017224): targeted MS detected the G12D 10-mer VVVGADGVGK on HLA-A*11:01 (Table 1, MS-observed, per the cited Wang et al. record); TCRs were isolated for KRAS G12V and G12D on A*11:01; epitopes bind with strong affinity (most <500 nM) and are more stable on A*11:01 (Table S3). WT VVVGAGGVGK was MS-detected on A*03:01 in that table.
- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC9017224
- Implication for the WT counter-target: unlike C*08:02, the WT complex on A*11:01 is a real, high-affinity pMHC and is expected to be at least as stable as G12D (G12D destabilizes). Discrimination must be engineered into the binder; the mutation site is mostly buried (Asp6 SASA ~8.8 A^2, ~90% buried; the challenge page recommends: the peptide and the groove around it), and generic co-folding scores do not separate the states (see rpinho control FAIL, section 3). The JDI TCR shows a >6,000-fold window is achievable with a TCR scaffold.
- Adjacent new paper: T-cell-engaging bispecifics against KRAS G12V on HLA-A*11:01 and A*03:01 (2026-10-18; PMID 42896875; PMC13691759).

## 3. Community sweep (as of 2026-10-30 ~14:15 CET)

### 3.1 GitHub (push dates verified via API)
- rpinho/adaptyv-challenges - pushed 2026-10-29 01:15 UTC. New C5 material: c5_prep/ docs dated 10-27/28 (BindCraft overnight campaign report; scoring-strategy panel; control-validation results; positive control; templates) and targets/c5_pmhc/ (state1_g12d_complex.pdb, state2_wt_complex.pdb, state3_peptide_free.pdb, control TCR). Highlights: BindCraft run on the G12D pMHC (chains A+B+C, 385 residues; hotspots A69, A155, C7, C8); ColabFold AF2-Multimer positive control FAILED to discriminate binder vs non-binder (ipTM 0.84 for both states); the review panel measured Asp6 SASA at 8.8 A^2 (~90% buried). URL: https://github.com/rpinho/adaptyv-challenges
- ElainW - no pushes since 2026-08-27 (STCRpy). pmhc_binder_kras (2026-06-26; de novo minibinder design, 100k sequences, 49 high-confidence candidates) and agent_pmhc_kras_binder_2 (2026-06-27) are unchanged. URL: https://github.com/ElainW/pmhc_binder_kras
- adaptyvbio/binder-prescreen - pushed 2026-10-27; kras-pmhc target set: 144 prior-art references (51 TCRs; 22 confirmed binders). URL: https://github.com/adaptyvbio/binder-prescreen
- New/updated repos pushed 2026-10-26 to 10-30 (API search): Jaycee871/pH-Switchable-TfR1-Binder-Design-Challenge (Oct 30; C4), DamienLegros/prot-competition-guide (Oct 30; aggregator), pirl-unc/presto (Oct 30; T-cell:pMHC prediction model), xanthine-adenine/anthropic-x-adaptyv-competition-2026 (Oct 29), wwwtalalahmed98-collab/ph-switch-binders (Oct 29), Mohsen-graphyy/DSM-bind-TCR-pMHC (Oct 29), hpaalv/proteinpaint (Oct 29; pMHC-interface design visualizer), guillemares/adaptyv-interface-frustation (Oct 28), wkh1267/pmhcii-af3-prereg (Oct 28), Charliserein/MHC-alphafold (Oct 27), antigenomics/tcren (Oct 26).
- Closest pMHC binder-design repo (not KRAS): balintvarga-bio/pMHC-HLA-I-binder-design- (Oct 20/21; BoltzGen binders to HLA-I presenting NY-ESO-1). KRAS G12D protein-level (not pMHC): precisionmatics/kras-g12d-nanobody-scripts (Oct 18; paper deposit with 30k designs). URL: https://github.com/balintvarga-bio/pMHC-HLA-I-binder-design-
- No public repo explicitly targeting KRAS G12D pMHC / Challenge 5 found yet.

### 3.2 Organizer posts and pages
- X @adaptyvbio 2026-10-26: Challenge 5 announcement (15.6K views) + submit link (712 views) - https://x.com/adaptyvbio/status/2114826922173833569
- LinkedIn Adaptyv company page 2026-10-26: same announcement (82 likes) - https://www.linkedin.com/company/adaptyvbio (walls limit deeper browsing).
- Proteinbase challenge page: submissions open until Sunday, November 8, 23:59 AoE; the challenge asks for three things - bind the G12D complex, do not bind the wild-type one, and do not bind the same HLA with no peptide in it. Provided structures: target = PDB 7OW6 chains A-C with TCR removed; wild-type offtarget = PDB 7OW5 (TCR removed); peptide-free = A*11:01 heavy chain, UniProt Q5S3G3, residues 25-305. Recommended epitope: the peptide and the groove around it. URL: https://proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/pmhc
- No public Slack; no Adaptyv blog post on C5; Substack latest post = 2026-08-19 (nothing on this competition).

### 3.3 Prediction markets
- None found for Challenge 5: Manifold searches (adaptyv, kras, proteinbase, pmhc, binder design, challenge 5) return only the three Nipah markets by Proteinbase, created 2026-01-05 and resolved; Polymarket has nothing. Precedent (Nipah) documented at https://adaptyvbio.substack.com/p/what-happened-in-the-nipah-protein

### 3.4 Participant posts / community
- No Challenge-5-specific participant posts found via search (X/LinkedIn largely walled; indexed posts only). Examples of the genre: @JohnsonThomasMD Challenge 1 write-up (Oct 8); Crane Bioworks studies incl. a KRAS G12D binder study (Feb 2026; protein-level) - https://cranebioworks.com/stories/kras-g12d-binder-design
- Aggregator with stale schedule text (says final closes Nov 1; official is Nov 8): https://phage.directory/items/anthropic-adaptyv-protein-design-competition-five-autumn-challenges-be85169c62725fe79d091408e909bd05

### 3.5 New papers/preprints (late Oct 2026)
- BenchMHC: reproducible framework for peptide-MHC presentation prediction (2026-10-27, preprint PPR1351550) - https://europepmc.org/article/PPR/PPR1351550
- EMBER: TCR-pMHC binding without a docked complex (arXiv, 2026-10-19) - http://arxiv.org/abs/2610.27334
- Beyond Better Models: barriers in generalisable TCR-antigen specificity prediction (2026-10-18, PPR1344516) - https://europepmc.org/article/PPR/PPR1344516
- KRAS G12D-targeted therapy sensitivity depends on interferon signaling (2026-10-29; PMID 42956743) - therapy, not design.
- Earlier September: specificity-driven protein binder design with Odin-Multi (2026-09-09, PPR1316904); interpretable peptide-HLA model learns binding energetics (2026-09-14, PPR1320080).

## Gaps and caveats
- SysteMHC HLA-A*11:01-specific counts were not extracted (JS UI; site intermittently unreachable on 2026-10-30).
- No head-to-head WT-vs-G12D Tm/KD on A*11:01 was found. Closest quantitative data: Zhu Fig 3H (mutants only), NMR titrations, MM/GBSA (9-mer vs 10-mer), and the JDI TCR affinities (binder side). WT stability >= G12D is an inference, not a measurement.
- No public C5 submission counts or leaderboard; no C5 prediction market; participant-post coverage limited by X/LinkedIn walls.
- IEDB counts are computed here from the 309 MB TSV export (one row per assay; distinct-epitope counts use the Epitope Name field; graded positives counted as positive).
- New since today (2026-10-30): only three GitHub pushes dated Oct 30 (Jaycee871, DamienLegros, pirl-unc/presto); no other same-day public items found.
