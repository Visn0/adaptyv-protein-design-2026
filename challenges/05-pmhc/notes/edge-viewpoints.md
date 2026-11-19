# Edge viewpoints: dissenting, critical and non-mainstream takes on de novo pMHC binder design, TCR-mimic specificity, and KRAS G12D/HLA-A*11:01 as a design target

Compiled 2026-10-30 for Anthropic × Adaptyv Challenge 5 (KRAS G12D pMHC, submissions close Nov 8, 2026, 23:59 AoE).
Method: web searches + direct page fetches; public APIs (X syndication, Hacker News Algolia, Europe PMC fullTextXML); PDF text extraction; no logins. Every finding carries a URL. Claims are labelled **[DATA]** (measured/reported result), **[OPINION]** (commentary/interpretation), or **[COULD NOT VERIFY]**.

Access limits up front: X/Twitter search requires login (only individual known tweet IDs could be fetched via the syndication endpoint; Nitter mirrors are dead); LinkedIn pages are login-walled (only search-engine snippets); Reddit's own search API is blocked from this environment (only search-engine snippets + some thread pages via a reader proxy); the Proteinbase Slack channel (the official Challenge 5 discussion venue, per the FAQ: https://join.slack.com/t/proteinbase/shared_invite/zt-4ds9ggmk4-ZfBhjp6TTeBY99cwkA_h4A) was not accessed — joining requires an account. Science (AAAS) pages sit behind a bot wall, so two paywalled Science items are quoted only from abstract-level records.

---

## 1. Critiques and limits of structure-prediction-driven pMHC design

**1.1 AlphaFold3 does not predict TCR:pMHC specificity well enough to skip experiments — by the authors' own numbers.** [DATA]
"Characterising AlphaFold 3's ability to predict T cell antigen specificity" (bioRxiv, v2 posted July 2026) states:
> "While AF3 has shown great promise at solving the unseen epitope challenge, the problem is still a long way from being solved. The ROC-AUC performance of AF3 reached a maximum of ≈ 0.6. Although this is better than previous models, which have near-random performance (ROC-AUC ≈ 0.5), it does not achieve good enough discrimination of binders and non-binders to remove the need for experimental validation or to be considered for use in clinical settings. Performance would need to be upwards of ROC-AUC ≈ 0.9 to match the ability of current experimental assays."
URL: https://www.biorxiv.org/content/10.64898/2026.07.08.737208v2.full.pdf

**1.2 The same paper's most subversive finding for this challenge: AF3's discrimination is geometric, not chemical.** [DATA]
> "We investigated the underlying correlates of AlphaFold-derived binding scores and found that the model's predictive power is related to the positioning of TCRs over the pMHC and not chemical interactions."
If true, confidence scores rank *docking pose plausibility*, not *chemical readout of a single mutated side chain* — directly relevant to distinguishing Asp6 from Gly6. URL: https://www.biorxiv.org/content/10.64898/2026.07.08.737208v2.full.pdf

**1.3 RFdiffusion "Exhibits Low Success Rate" paper — a direct counterexample to the 'design is solved' narrative.** [DATA]
Independent evaluation (bioRxiv, Feb 2025) of RFdiffusion for six detection targets:
> "Binders for the other targets failed due to low expression, nonspecific binding, or undetectable affinity. Despite generating structurally diverse candidates, RFdiffusion's success rate was limited by low-affinity designs and inconsistent recombinant expression. These results underscore the need for further optimization of AI-driven protein design tools for practical biochemical applications."
URL: https://www.biorxiv.org/content/10.1101/2025.02.07.636769v1

**1.4 Large-scale meta-analysis of 3,766 experimentally characterised binders: in-silico features barely generalise.** [DATA]
> "These results suggest that incorporating features from other models seems to only introduce noise rather than add complementary information across targets." … "only a small number of features are consistently informative for identifying true binders across targets."
(Overath et al., bioRxiv 2025; includes two pMHC targets in the corpus.) URL: https://www.biorxiv.org/content/10.1101/2025.08.14.670059v2.full-text

**1.5 The iPAE metric that the whole field (and the earlier Adaptyv competitions) thresholded on correlates only weakly with real affinity.** [OPINION, with data]
Boolean Biotech's postmortem of the 2024 Adaptyv EGFR competition:
> "I don't know that I really expected iPAE to correlate strongly with Kd, but it's pretty weak." … "So, it's probably optimistic to think that a few RFdiffusion-derived binders will show strong binding, even if you can somehow get a decent iPAE."
And on metric gaming: "Unfortunately, though the spirit of the competition was to find novel binders, the way iPAE works means that the best scores are very likely to come from EGF-like sequences (or other sequences in AlphaFold's training set)."
URL: https://blog.booleanbiotech.com/adaptyv-binder-design-competition

**1.6 The Johansen et al. (Science 2025) paper contains its own strongest critique of ML-guided binder design.** [DATA]
> "Protein design guided by machine learning can result in a high rate of false positives when predicted binders fail during experimental testing. Thus, identifying properties and features that can decrease the false-positive rate is crucial."
Their second, structure-unknown campaign succeeded at "a success rate of ~2%". URL: https://www.science.org/doi/10.1126/science.adv0422 (open PDF copy used: https://bookcafe.yuntsg.com/ueditor/jsp/upload/file/20250822/1755828132710085362.pdf)

**1.7 A flagship 'peptide-centric' binder actually leans on MHC contacts.** [DATA]
In Johansen et al., the MD analysis of the star binder NY1-B04 reports:
> "Residues E11, E96, T133, R139, and E140 of NY1-B04 formed long-lasting interactions with HLA-A*02:01, and residues Y107, E115, and Q119 interacted with the peptide."
Five MHC residues vs three peptide residues among long-lived interactions — i.e., the experimentally validated interface is substantially MHC-facing, exactly the failure mode Challenge 5's no-peptide and WT counter-screens are designed to catch. URL: https://www.science.org/doi/10.1126/science.adv0422

**1.8 Liu et al.'s (Science 2025) own framing shows the problem is not solved: it is 'should become possible'.** [DATA]
> "A central challenge in targeting pMHCI complexes is achieving high specificity."
They screened "between 200 and 12,000 designs" per target to identify specific binders for 11 pMHCs — but "upon incorporation into chimeric antigen receptors, designs for eight targets conferred peptide-specific T cell activation" (i.e. 8/11 in the functional format), and the future-work section is conditional:
> "as deep learning-based structure prediction, design, and model ranking methods improve, it should become possible to find designs with suitable affinities and specificities in testing dozens of candidates."
URL: https://www.science.org/doi/10.1126/science.adv0185 (open PDF: https://www.bakerlab.org/wp-content/uploads/2025/08/science.adv0185.pdf)

**1.9 The ESK1 postmortem: a clinically advanced TCR-mimic that bound its peptide through a single side chain and still hit healthy tissue.** [DATA]
> "ESK1, a well characterized TCR-like T cell bispecific antibody, which is known to unselectively target peptide RMFPNAPYL derived from the intracellular oncoprotein WT1 (WT1 126-134) presented on HLA-A*02:01."
> "direct chemical interactions between ESK1 and the RMFPNAPYL peptide are only occurring with the arginine residue on position 1."
The interactome assay then identified "ESK1 cross-reactive peptides in healthy liver tissue" and off-target killing in lung and colon 3D models. URL: https://www.nature.com/articles/s41467-024-47062-5

**1.10 Antibodies/TCRms engage pMHC differently from TCRs — structurally 'not evolved for it'.** [DATA]
Raybould et al. (Frontiers in Immunology 2023):
> "antibody CDRL2 loops lie unburied in over 50% of general antigen complexes while TCR CDRA2 loops are buried in the pMHC interface to a much greater extent."
> "pMHC complexes offer an unusually broad binding surface that is engaged differently by TCR and TCRm CDRs."
URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC9868621 (also https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2022.1080596/full)

**1.11 Affinity-centric evaluation systematically overstates readiness.** [DATA]
Bits to Binders competition analysis (12,000 designs, CAR-T context):
> "However, most evaluations emphasize binding affinity rather than higher-order biological function." … "4,985 of the designs (42%) dropped out of the population, indicating that some sequences or proteins interfered with cell viability."
URL: https://link.springer.com/article/10.1038/s44320-026-00246-1

**1.12 On 'designs that grip MHC not peptide' as a named failure mode.** [COULD NOT VERIFY]
I found no 2025–2026 paper that explicitly studies, at scale, the fraction of de novo pMHC binders whose binding is MHC-dominated. The closest evidence is indirect: (i) Liu et al. state the design requirement as "avoidance of extensive contacts with ubiquitously expressed MHC" (https://www.science.org/doi/10.1126/science.adv0185); (ii) the Garcia-lab TCRm preprint notes scaffolds with different orientations, "with some anticipated to make more MHC versus peptide contacts than others" (https://pmc.ncbi.nlm.nih.gov/articles/PMC11702606); (iii) Challenge 5's own ranking text formalises the failure: "A binder that reads the HLA or the β2-microglobulin instead of the peptide binds all three targets and ranks there" (https://proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/pmhc).

**1.13 Formal rebuttals/technical comments against Liu 2025 or Johansen 2025.** [COULD NOT VERIFY]
No published rebuttal, matters-arising, or technical comment against either Science paper (adv0185, adv0422) was found in PubMed/Europe PMC/web searches. Science's eLetter facility was inaccessible from this environment (bot wall). The closest 'rebuttal-grade' material is (a) the 2026 AF3 specificity benchmark (1.1–1.2) showing structure-based specificity prediction remains near-unusable, and (b) the ESK1 interactome paper (1.9) showing the failure mode in a sibling TCRm modality. Treat 'no rebuttals exist' as unresolved rather than proven.

---

## 2. Expert commentary and predictions — 'what is still hard'

**2.1 The official Science perspective for the Liu/Johansen papers is optimistically hedged.** [OPINION]
Hickok & Stromnes, "Beyond the native repertoire," Science 389(6758):349-351 (2025). Abstract (full text paywalled/bot-walled): "Design of T cell receptors by artificial intelligence is poised to accelerate cancer immunotherapy." [COULD NOT VERIFY full-text caveats.]
URLs: https://www.science.org/doi/10.1126/science.adz6423 ; https://pubmed.ncbi.nlm.nih.gov/40705900

**2.2 Baker lab's own accessibility caveat on pMHC binders.** [OPINION]
Cancer Grand Challenges news piece on the MATCHMAKERS team (24 July 2025):
> "would still need testing to first identify their HLA type, in order to find the right binder therapy for them. However, the lab aspires to design against non-polymorphic alleles in the future."
URL: https://www.cancergrandchallenges.org/news/designing-accessible-immunotherapies-with-ai

**2.3 Baker on hype vs. reality.** [OPINION, title-level]
GEN's video interview is literally titled "AI in Protein Design: Hype vs. Reality Explained by David Baker" (Oct 20, 2025). Transcript not retrievable (video page, JS). URL: https://www.genengnews.com/topics/artificial-intelligence/ai-in-protein-design-hype-vs-reality-explained-by-david-baker/

**2.4 Adaptyv's own CEO (Julian Englert) publicly tempers the AI-binder narrative.** [OPINION]
Hacker News thread (Aug 2026): "So can AI now solve all diseases? Well no, not yet. This case study shows that Claude is at least expert-level at orchestrating protein design tools." And in Adaptyv's write-up: "Of course, those proteins that we tested here are not real therapeutics. They completed only the first step of the process: demonstrating that they can function as binders."
URLs: https://news.ycombinator.com/item?id=49354929 ; https://www.adaptyvbio.com/blog/anthropic-1

**2.5 The loudest public skeptic of the Claude protein-design campaign.** [OPINION]
Martin Shkreli called Claude's AI-designed binders "not impressive work," saying they "offered little advantage over existing antibodies," and "cited low affinities and the binders' inability to target proteins inside cells."
URLs: https://newsable.asianetnews.com/markets/-pharma-bro-martin-shkreli-slams-anthropic-s-claude-drug-discovery-claims-this-is-not-impressive-work-articleshow-ikcgu3u ; https://stocktwits.com/news-articles/markets/equity/martin-shkreli-anthropic-claude-drug-discovery-claims/cZYdE2tRJkJ

**2.6 Immunocore's CEO: 'ambition with caution'.** [OPINION]
FierceBiotech (Feb 13, 2026): "After R&D head exits, Immunocore CEO pairs ambition with caution for growing cancer portfolio" — "an abundance of caution doesn't mean a lack of ambition."
URL: https://www.fiercebiotech.com/biotech/immunocore-ceo-eyes-careful-growth-centered-cancer-hiv-cure-side

**2.7 The definitional fight over 'de novo' itself.** [OPINION]
Kresten Lindorff-Larsen (X, Aug 2026): "Broke: De novo / Woke: From scratch / [and neither have a clear definition]". Adaptyv's own blog concedes: "The term is frequently used in the literature but is rarely defined exactly and has evolved over the years with the capability of new design methods."
URLs: https://x.com/LindorffLarsen/status/2090704385894424770 ; https://www.adaptyvbio.com/blog/novelty

**2.8 'Just starting to crack' — a community framing from 2024 that still reads as the honest state.** [OPINION]
David K. Yang (X, Nov 2024) on the de novo pMHC binder papers: "pMHC-1 is a key target class that we're just starting to crack."
URL: https://x.com/davidkmyang/status/1863006329545376211

**2.9 Two independent review verdicts on the TCR-agent field being immature.** [DATA/OPINION]
> "The soluble TCR-based protein biologic field has gained significant momentum but is in its early stages. Key challenges still need to be overcome, including toxicity, immunosuppression, and drug resistance." (Review, 2025; PMC13664799) URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC13664799
> "Recent development of methods to discover and engineer therapeutic TCRs or antibody mimics of TCRs, and to understand their immunology and pharmacology, lag two decades behind therapeutic antibodies." (Immunol Rev 2023; PMC11141734) URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC11141734

---

## 3. Debates specific to this epitope (KRAS G12D / HLA-A*11:01)

**3.1 The 9-mer vs 10-mer register debate is now data, not speculation — and it cuts both ways.** [DATA]
Zhu et al., Commun Biol 2025 (the 'Zhu 2025' register paper):
> "G12D peptides adopt two registers, a 9-mer and a 10-mer, that diverge sharply in structure and immunogenicity. The 10-mer forms a compact, stable pMHC with a TCR-accessible surface, while the 9-mer adopts a bent conformation incompatible with recognition."
> "These shifts generate structurally non-overlapping epitopes and explain why a TCR selected against the 10-mer fails to recognize the 9-mer, despite near-identical sequences."
> "HLA-A*11:01 is one of the most prevalent HLA alleles in East Asian populations."
URL: https://www.nature.com/articles/s42003-025-09285-0 (PMC copy: https://pmc.ncbi.nlm.nih.gov/articles/PMC12774912; PubMed: https://pubmed.ncbi.nlm.nih.gov/41339521). Crystal structures exist for both: 9-mer PDB 9UV8 (https://www.rcsb.org/structure/9UV8); G12S 10-mer 9WVF (https://www.rcsb.org/structure/9WVF).
**The disagreement this creates:** whether an A*11:01 binder/TCR selected against the 10-mer will see the same epitope in vivo (the 9-mer register is also presented — both were quantified by MS in 2023 work), and whether the challenge's choice of the 10-mer VVVGADGVGK biases designs toward a register that some tumour cells may not dominant-present.

**3.2 The very residue being targeted is disordered in the receptor-free crystal.** [DATA]
Challenge 5 FAQ, verbatim:
> "Position 6, where the two peptides differ, sits in the mobile middle of the peptide. 7OW4, the G12D crystal without a T-cell receptor, has no coordinates for positions 5 and 6. With a receptor bound (7OW6), the aspartate is tucked against Arg114 and Gln70 of the HLA (PDB numbering)."
URL: https://proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/pmhc
This is the concrete form of the 'static models miss dynamics' critique for this epitope: the design target's discriminating atom is not visible in the apo structure and is only defined when a TCR clamps it.

**3.3 Can a non-TCR scaffold 'read' a buried mutation? The literature says: often indirectly.** [DATA]
Mariuzza-lab review of neoantigen recognition:
> "in some cases, the mutation is detected by direct interactions with TCR, or by energetically driven or other indirect strategies not requiring direct TCR contacts with the mutation."
> "this physiochemical similarity presents a challenge to the immune system and probably explains, at least in part, the low frequency of T cells able to recognize neoantigens."
URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC10693334
Combined with 1.2 (AF3 scores track pose, not chemistry) and 1.7 (validated binder contacts dominated by MHC residues), the non-mainstream position is: a generic minibinder is more likely to lock a *conformation* of the Asp6-containing 10-mer than to make a direct Asp6 salt bridge — and that may be sufficient for specificity (conformational readout) or may fail the WT counter-screen (which differs by the same conformational shift). The field has no settled answer. [OPINION]

**3.4 There IS a TCRm program against exactly this pMHC — but only preclinical, and as an ADC.** [DATA]
AACR 2026 abstract 6929: "NDV-ADC01-exatecan, which targets the KRAS G12D/HLA-A*11 pMHC complex, mediated specific antitumor activity in vitro and in vivo without obvious toxicity in xenograft models of lung, pancreatic, and colorectal cancer."
URL: https://aacrjournals.org/cancerres/article-split/86/7_Supplement/6929/780899/Abstract-6929-Targeting-intracellular-KRASG12D-HLA
So the 'can an antibody-like scaffold target G12D/A*11 at all' question is being answered affirmatively — in mice, by a company, with a payload — not yet in patients.

**3.5 HLA-C*08:02 vs A*11:01: an actual documented expert disagreement about which allele matters.** [DATA/OPINION]
The NEJM correspondence on Tran et al.'s KRAS G12D/C*08:02 T-cell case is a rare, citable researcher-vs-researcher exchange:
- Rech & Vonderheide: "we identified 151 patients with KRAS G12D mutations out of 6125 patients in the Cancer Genome Atlas. Of these, only 4 had the HLA-C*08:02 allele… Immunotherapy targeting KRAS G12D in patients with the HLA-C*08:02 allele appears to be an important but rare opportunity."
- Maoz, Rennert & Gruber: "HLA typing available for 3734 patients shows that 687 (18.4%) have at least one copy of HLA-C*08:02. We found that 85 of 3734 patients (2.3%) with colorectal cancer share the same HLA type and KRAS mutation as described by Tran et al."
- Tran et al. reply: "The data cited by Rech and Vonderheide in their letter are not consistent with the frequency of HLA-C*08:02 and of the KRAS G12D mutation in the U.S. population."
URLs: https://www.nejm.org/doi/full/10.1056/NEJMoa1609279 (correspondence; open PDF copy: https://www.med.upenn.edu/pici/assets/user-content/PICI@Penn%20Publications/Rech%20NEJM%202017.pdf)
For A*11:01 the case is different — the KRAS G12V/A*11:01 TCR-T (NW-301V) reported a "significant response rate" at ESMO 2025, with the commentator's caveats being cost/manufacturing and that "the specificity of NW-301V for the G12V mutation alone could also be restrictive." URL: https://dailyreporter.esmo.org/news-insights/all-news/first-in-human-trial-of-a-tcr-t-therapy-targeting-kras-g12v-reports-a-significant-response-rate

**3.6 How confidently do we know the peptide is presented at useful density?** [DATA, with an edge]
The 2023 neoepitope-HLA platform paper (which quantified A*11:01 KRAS 9-mer/10-mer presentation) cautions: "only a fraction of those found here were evaluated by HLA-IP-MS using cells that natively express the neoantigens and HLAs." URL: https://www.nature.com/articles/s41587-023-01945-y. The edge position: design contests test binding to refolded/synthetic pMHC, which brackets out presentation biology (processing, competition, density) that determines whether any of it matters clinically.

---

## 4. Negative results and postmortems

**4.1 Adaptyv's own published hit-rate curve (the community's baseline expectation for Challenge 5).** [DATA]
> "Context on the Adaptyv Protein Design Competition hit-rates over time: EGFR R1 (2024) = 2.5%, R2 = 13.2%, Nipah (Jan 2026) = 9.6%, TREM2 now = 37% in a single day. The bar gets pushed up every 6 months, and agents are riding that curve alongside humans now." (Adaptyv, X, May 2026)
URL: https://x.com/adaptyvbio/status/2054607923318268189
Note: none of those targets had a one-residue specificity requirement against a near-identical decoy plus a peptide-free decoy. The nearest published analog for pMHC hit rates is the JITC abstract: "Of the top 30 AI-designed binders, 6 showed strong, peptide-specific binding" (20% at the top of the funnel; https://jitc.bmj.com/content/13/Suppl_2/A1131).

**4.2 In-silico #1 ≠ wet-lab binder — an explicit, named postmortem.** [DATA/OPINION]
Adaptyv's Nipah recap: "Andrés Torrubia learned firsthand that aggressively optimizing leaderboard metrics does not necessarily translate into experimental success: although his designs ranked #1 in silico in the EGFR competition, they ultimately failed in the wet lab."
URL: https://adaptyvbio.substack.com/p/what-happened-in-the-nipah-protein

**4.3 The EGFR competition write-up's list of what didn't work.** [DATA]
> "it also exposed key challenges, such as the lack of standardized benchmarks, experimental design targets, and robust c[omparison]."
URL: https://www.biorxiv.org/content/10.1101/2025.04.17.648362v2.full

**4.4 Design-stage failures in Bits to Binders.** [DATA]
> "The combination of DNA GC content and Shannon entropy separates out 55 designs that failed to synthesize as DNA." … "Almost all of the designs that failed to be recovered were created with ProteinMPNN or SolubleMPNN."
URL: https://link.springer.com/article/10.1038/s44320-026-00246-1

**4.5 The classic fatal TCR off-target precedent (still the field's cautionary tale).** [DATA]
"Cancer regression and neurological toxicity following anti-MAGE-A3 TCR gene therapy" — cross-reactivity with a Titin epitope caused fatal cardiotoxicity. URL: https://pubmed.ncbi.nlm.nih.gov/23377668
Also relevant: the KITE-718 (MAGE-A3/A6) engineered-T-cell study record — URL: https://clinicaltrials.gov/study/NCT03139370 (status not verified here).

**4.6 ESK1 (WT1 TCRm) as the TCRm-specific negative result.** [DATA]
Off-target interactome and tissue killing as in 1.9. URL: https://www.nature.com/articles/s41467-024-47062-5

**4.7 The ~2% unknown-structure success rate in the flagship de novo pMHC paper.** [DATA]
As quoted in 1.6. URL: https://www.science.org/doi/10.1126/science.adv0422

**4.8 A field-level negative: no generalisable prioritisation metric.** [DATA]
The 3,766-binder meta-analysis (1.4) and the RFdiffusion detection-binder failure study (1.3). URLs: https://www.biorxiv.org/content/10.1101/2025.08.14.670059v2.full-text ; https://www.biorxiv.org/content/10.1101/2025.02.07.636769v1

---

## 5. Community debates about Challenge 5 itself

**Access-limits summary (read this before the rest):** No X search without login; no LinkedIn; Reddit search API blocked (snippets only); Proteinbase Slack not joined; Manifold market pages not fetched. Everything below is what could actually be fetched or is quoted from search-result snippets (labelled).

**5.1 The official announcement (verbatim, fetched via X syndication).** [DATA]
Adaptyv (Oct 26, 2026, 91 likes): "Our last challenge in the Anthropic x Adaptyv Protein Design Competition is about immunotherapy, one of the most important ways of treating cancer. Immunotherapy helps the immune system attack cancer cells, but distinguishing them from healthy cells isn't always easy."
URL: https://x.com/adaptyvbio/status/2114826922173833569
A separate "Submit now" post: https://x.com/adaptyvbio/status/2114827339083456725
**[COULD NOT VERIFY]** any public replies/debate under these posts (X reply threads require login).

**5.2 What the challenge itself concedes about difficulty.** [DATA]
From the official challenge page/FAQ (fetched in full):
- "Position 6, where the two peptides differ, sits in the mobile middle of the peptide. 7OW4, the G12D crystal without a T-cell receptor, has no coordinates for positions 5 and 6."
- "We recommend targeting the peptide and the groove around it… The rest of the complex is the same for both peptides, and the same again with no peptide, so a binder that sits there cannot tell them apart."
- Ranking: "A measurable KD against the KRAS G12D complex and no detectable binding to the wild-type KRAS complex… A binder that reads the HLA or the β2-microglobulin instead of the peptide binds all three targets and ranks there."
- "Every measurement, including the failures, is on Proteinbase with sequences and methods."
- Scale: "Per problem we expect to screen ~1500 designs (50% for Track 1, 25% for Track 2, and 25% for Track 3)"; up to 40 designs per Track 1 participant.
- Selection: "Anthropic and Adaptyv select designs for synthesis using a Claude-based workflow, published after the competition."
URL: https://proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/pmhc

**5.3 'Has binder design been solved?' — Adaptyv's own framing, and the number they later posted.** [DATA/OPINION]
Dec 2024: "Has protein binder design been solved? We analyze the results of our protein design competition where 130 designers created binders for EGFR. With a 5x improvement in success rates and some designs outperforming clinical antibodies, we explore what worked, what didn't…" URL: https://x.com/adaptyvbio/status/1871693290325598234 (article version: https://adaptyvbio.substack.com/p/protein-design-competition-has-binder)
By May 2026 the cumulative curve was 2.5% → 13.2% → 9.6% → 37% (5.1-adjacent tweet, 4.1). The implicit community expectation for a one-residue discrimination target should be set well below the 37% general-target figure — no organiser has published a pMHC-specific expectation. [OPINION]

**5.4 Prediction markets as the community's expectations channel.** [DATA]
Adaptyv, Nipah recap (Jan 2026): "we opened a prediction market on Manifold for this competition so you can bet on hit rates, best performing models, and more."
URL: https://adaptyvbio.substack.com/p/what-happened-in-the-nipah-protein
**[COULD NOT VERIFY]** whether a Manifold market exists for Challenge 5 specifically.

**5.5 Hacker News: almost no engagement.** [DATA]
The Adaptyv/Anthropic wet-lab case study thread (Aug 2026) has 4 points and exactly 1 comment (by Adaptyv's CEO). URL: https://news.ycombinator.com/item?id=49354929. HN search for "adaptyv" surfaces no Challenge-5 discussion at all (Algolia: https://hn.algolia.com/api/v1/search?query=adaptyv).

**5.6 Reddit: enthusiasm about Claude's results, no Challenge-5-specific critique found.** [DATA, snippet-level]
- r/singularity thread (1.9k-upvote range; fetched partially) quotes Anthropic: "Designing a binder is an easier process than designing a drug, but it's a useful proxy. The typical success rate in the field today is between 10% and 15%." URL: https://www.reddit.com/r/singularity/comments/1vs6f13/anthropic_working_on_claude_autonomously/
- Snippet-level (search results, not opened in-page): r/AIGuild: "Anthropic says Claude designed successful protein binders for 14 of 15 targets — with up to 35% hit rates vs 10–15% typical" (https://www.reddit.com/r/AIGuild/comments/1vs7bw9/); r/AIdaily_news: "Against RBX1, it achieved a 40% hit rate compared with 3.7% among participants in an Adaptyv Bio protein design competition" (https://www.reddit.com/r/AIdaily_news/comments/1vslop2/).
**[COULD NOT VERIFY]** any Reddit thread debating Challenge 5's fairness, the WT counter-screen, or expected hit rates.

**5.7 The 'this is impossible / not impressive' genre.** [OPINION]
The Shkreli episode (2.5) is the most-visible skeptic take on the broader Anthropic protein-design campaign. For the specific 'TCR mimic is very hard' genre, the field's own framing is the strongest: "pMHC-1 is a key target class that we're just starting to crack" (2.8) and the ~2% unknown-structure success rate (1.6). No one found in this search publicly declared Challenge 5 itself impossible. [COULD NOT VERIFY]

**5.8 Precedent for a pMHC binder competition: the Bits to Binders model (2026).** [DATA]
A global competition on de novo binders as CAR domains ("12,000 designs", "team hit rates from 0.6% to 38.4%") shows organisers now report hit-rate distributions openly — and shows the spread you should expect for Challenge 5. URL: https://link.springer.com/article/10.1038/s44320-026-00246-1

---

## Table: viewpoint | who | evidence | URL

| # | Viewpoint | Who | Evidence (label) | URL |
|---|-----------|-----|------------------|-----|
| 1 | AF3 cannot yet discriminate TCR binders from non-binders; ROC-AUC ≈ 0.6, needs ≈ 0.9 to replace assays | AF3 specificity benchmark authors (bioRxiv 2026) | Verbatim quote [DATA] | https://www.biorxiv.org/content/10.64898/2026.07.08.737208v2.full.pdf |
| 2 | AF3's pMHC binding signal tracks TCR positioning, "not chemical interactions" | Same | Verbatim quote [DATA] | https://www.biorxiv.org/content/10.64898/2026.07.08.737208v2.full.pdf |
| 3 | RFdiffusion low real-world success; failures = expression, nonspecificity, undetectable affinity | Jiang et al. bioRxiv 2025 | Verbatim quote [DATA] | https://www.biorxiv.org/content/10.1101/2025.02.07.636769v1 |
| 4 | In-silico interface features don't generalise across targets (3,766 binders) | Overath et al. bioRxiv 2025 | Verbatim quote [DATA] | https://www.biorxiv.org/content/10.1101/2025.08.14.670059v2.full-text |
| 5 | iPAE–Kd correlation "pretty weak"; iPAE rewards training-set lookalikes | Boolean Biotech (Brian Naughton) | Verbatim quote [OPINION] | https://blog.booleanbiotech.com/adaptyv-binder-design-competition |
| 6 | ML-guided binder design has a high false-positive rate by the authors' own admission | Johansen et al., Science 2025 | Verbatim quote [DATA] | https://www.science.org/doi/10.1126/science.adv0422 |
| 7 | Flagship "peptide-centric" binder's long-lived contacts are mostly to MHC | Johansen et al. (MD analysis) | Verbatim quote [DATA] | https://www.science.org/doi/10.1126/science.adv0422 |
| 8 | 11 pMHC binders found, only 8 worked as CARs; 200–12,000 designs screened per target | Liu et al., Science 2025 | Verbatim quotes [DATA] | https://www.science.org/doi/10.1126/science.adv0185 |
| 9 | TCR-mimic ESK1: peptide contact via one side chain; off-targets in healthy liver/lung/colon | Nature Comms 2024 interactome study | Verbatim quotes [DATA] | https://www.nature.com/articles/s41467-024-47062-5 |
| 10 | TCRm CDR usage differs from TCRs; pMHC is "an unusually broad binding surface" | Raybould et al. 2023 | Verbatim quote [DATA] | https://pmc.ncbi.nlm.nih.gov/articles/PMC9868621 |
| 11 | Field verdict: soluble TCR biologics "in its early stages"; TCR methods "lag two decades behind therapeutic antibodies" | Two 2023–2025 reviews | Verbatim quotes [DATA/OPINION] | https://pmc.ncbi.nlm.nih.gov/articles/PMC13664799 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC11141734 |
| 12 | "Broke: De novo. Woke: From scratch. [neither has a clear definition]" | Kresten Lindorff-Larsen (X) | Verbatim quote [OPINION] | https://x.com/LindorffLarsen/status/2090704385894424770 |
| 13 | Claude's designs "are not real therapeutics"; "So can AI now solve all diseases? Well no, not yet" | Julian Englert, Adaptyv CEO | Verbatim quote [OPINION] | https://news.ycombinator.com/item?id=49354929 |
| 14 | Claude's binders are "not impressive work", little advantage over antibodies, low affinities, can't hit intracellular targets | Martin Shkreli (via news reports) | Paraphrase+quote [OPINION] | https://newsable.asianetnews.com/markets/-pharma-bro-martin-shkreli-slams-anthropic-s-claude-drug-discovery-claims-this-is-not-impressive-work-articleshow-ikcgu3u |
| 15 | G12D presents as 9-mer and 10-mer; 9-mer "bent… incompatible with recognition"; TCR vs 10-mer fails on 9-mer | Zhu et al., Commun Biol 2025 | Verbatim quotes [DATA] | https://www.nature.com/articles/s42003-025-09285-0 |
| 16 | The discriminating residue is invisible in the apo crystal ("no coordinates for positions 5 and 6") | Challenge 5 FAQ (Proteinbase) | Verbatim quote [DATA] | https://proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/pmhc |
| 17 | Buried neoantigen mutations are often read indirectly, without direct TCR contacts | Mariuzza-lab review | Verbatim quote [DATA] | https://pmc.ncbi.nlm.nih.gov/articles/PMC10693334 |
| 18 | HLA-C*08:02 "important but rare opportunity" (4/151 patients) vs 2.3% of CRC patients — with authors' reply disputing | Rech/Vonderheide; Maoz et al.; Tran reply (NEJM) | Verbatim quotes [DATA/OPINION] | https://www.nejm.org/doi/full/10.1056/NEJMoa1609279 |
| 19 | A TCRm-ADC against KRAS G12D/HLA-A*11 works in mice, not yet in patients | AACR 2026 abstract 6929 | Verbatim quote [DATA] | https://aacrjournals.org/cancerres/article-split/86/7_Supplement/6929/780899/Abstract-6929-Targeting-intracellular-KRASG12D-HLA |
| 20 | Hit-rate history: 2.5% → 13.2% → 9.6% → 37%; "the bar gets pushed up every 6 months" | Adaptyv (X, May 2026) | Verbatim quote [DATA] | https://x.com/adaptyvbio/status/2054607923318268189 |
| 21 | pMHC binder platform benchmark: 6/30 top AI designs bound peptide-specifically | JITC 2025 abstract 1002 | Verbatim quote [DATA] | https://jitc.bmj.com/content/13/Suppl_2/A1131 |
| 22 | "pMHC-1 is a key target class that we're just starting to crack" | David K. Yang (X, 2024) | Verbatim quote [OPINION] | https://x.com/davidkmyang/status/1863006329545376211 |

---

## Gaps (what this search could not establish)

1. **No formal rebuttals of Liu 2025 / Johansen 2025 were found** (no matters-arising/technical comments in PubMed, Europe PMC, or web search). Science eLetters were inaccessible (bot wall). Absence is unproven.
2. **No full text of the Hickok & Stromnes Science perspective** ("Beyond the native repertoire") — only its abstract; its caveats/limitations statements could not be verified.
3. **X/Twitter replies and quote-tweets under the Challenge 5 announcement could not be read** (login wall; Nitter mirrors dead). Any real-time community skepticism about Challenge 5 may exist there unmeasured. Same for LinkedIn.
4. **No Challenge-5-specific hit-rate expectation or fairness debate found** in any accessible public venue (HN: near-zero engagement; Reddit: only generic enthusiasm/skepticism about the Anthropic campaign). The Proteinbase Slack is the likely venue and was not joined.
5. **No public negative result from any completed de novo pMHC design campaign against KRAS G12D/A*11:01** — the closest is the preclinical AACR TCRm-ADC abstract. If a company tried and failed, it is not public.
6. **No Manifold prediction market found for Challenge 5** (one existed for Nipah); whether one exists could not be verified.
7. **Quantitative allele-frequency sourcing for A*11:01 vs C*08:02** relies on the Zhu 2025 statement ("one of the most prevalent HLA alleles in East Asian populations") and the NEJM exchange; allelefrequencies.net was not queried for exact per-population numbers.
8. **The GEN "Hype vs. Reality" David Baker interview transcript was not retrievable** (video/JS); its content is unverified beyond the headline framing.
