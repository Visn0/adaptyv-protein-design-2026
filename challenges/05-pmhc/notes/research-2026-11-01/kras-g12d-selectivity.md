# How the field achieves KRAS G12D-over-WT selectivity — and what a de novo binder can steal from it

*Scope: mutant Asp12 vs wild-type Gly12. Two contexts are treated separately because they behave differently: (i) free KRAS (drug/inhibitor and monobody recognition), and (ii) the KRAS G12D decamer VVVGADGVGK presented by HLA-A*11:01 vs the WT VVVGAGGVGK (TCR / TCR-mimic recognition). All claims are referenced; contested points are flagged explicitly.*

---

## 1. Covalent and non-covalent G12D-selective inhibitors: exact interactions with Asp12 and reported selectivity

### 1.1 The scaffold logic

KRAS G12D lacks the reactive cysteine of G12C, so the warhead chemistry of the G12C field was replaced by a *non-covalent electrostatic readout* of the aspartate: a protonated amine positioned to form an ion pair with the Asp12 carboxylate inside the switch-II (S-II) pocket — a cryptic, inhibitor-induced pocket between switch II, the α3 helix and the P-loop. The Mirati team states the design premise directly: a "protonated piperazine could interact productively with the mutant Asp12 side chain" ([1], J Med Chem 2022).

### 1.2 MRTX1133 (non-covalent, clinical-stage)

**Interactions (from co-crystal structures and SAR, [1]):**
- The protonated piperazinyl/bicyclic-amine nitrogen forms an **ion pair with the Asp12 carboxylate**, additionally stabilized by a **hydrogen bond to the Gly60 backbone carbonyl** — a "bifurcated" interaction pattern (Asp12 + Gly60). N-methylation of the amine (cmpd 8) or O-substitution (cmpd 9) abolished both potency and selectivity (KD 6.2 and 0.56 μM vs WT), which is the cleanest SAR proof that the ion pair is the selectivity determinant.
- In the earliest hit series (pyrido[4,3-d]pyrimidine, cmpd 5B, KD 3.5 μM) the Asp12 ion pair alone gave only **~10-fold selectivity over WT**; rigidification of the amine (cmpd 15, KD 0.8 nM) gave **>200-fold**; the fully optimized MRTX1133 reaches an estimated **KD ≈ 0.2 pM on GDP-loaded G12D**.
- Additional contacts: H-bond from the 6-position N to Arg68; 8-F in a small hydrophobic pocket near Gly10; C7-naphthol in a deep hydrophobic pocket; H95 (see below).
- Binds both GDP- and GMPPCP-loaded G12D; co-crystals 7RPZ (GDP) and 7T47 (GMPPCP).

**Reported selectivity — and where the numbers disagree (contested):**
- Mirati's own figures ([2], Nat Med 2022; preprint version gives the underlying numbers): SPR **KD = ~0.2 pM (G12D) vs 140 nM (WT)**, quoted in the abstract as **"~700-fold"**. *The two KD values themselves correspond to ~7×10⁵-fold*, so the headline "700-fold" is not arithmetically consistent with its own KDs — a discrepancy that has propagated through the secondary literature.
- The same paper's own biochemical panel shows how assay-dependent the number is (Fig. 1B of [2]): HTRF competition IC50 **<2 nM (G12D) vs 2.4 nM (WT)** — essentially no equilibrium selectivity; HTRF RAF-RBD active-state assay **9 nM vs 112 nM (~12×)**; SPR **0.2 pM vs 140 nM**. The huge SPR window therefore reflects slow dissociation kinetics (long residence time) rather than a large equilibrium advantage at the S-II site. Cellular window: pERK median IC50 ~6 nM in G12D lines vs >3000 nM in non-G12D lines; viability IC50 ~5 nM vs ~573 nM (~100×).
- Independent isogenic-cell-line work ([3], Cancer Res 2023) found that MRTX1133 has **"significant activity against several other KRAS mutants as well as wild-type KRAS protein"** in cells, while showing no activity on HRAS/NRAS (WT or G12D). The cause mapped to **His95**, a residue not conserved in HRAS/NRAS: reciprocal H95 swaps between paralogs reciprocally swap sensitivity. So part of MRTX1133's "selectivity" is *paralog* selectivity (KRAS vs NRAS/HRAS) rather than strictly G12D vs G12.
- Mechanism is also contested: whether MRTX1133 acts by direct steric occlusion of the RBD or by allostery on switch I was debated; a 2025 NMR/BLI/ITC study ([4]) reports that MRTX1133 binds KRAS **regardless of nucleotide state**, freezes switch dynamics, blocks hydrolysis and exchange, but that RBD binding can restore hydrolysis — i.e., more complex than "locks the inactive state".

### 1.3 Non-covalent successors (structures or clinical data)

| Agent | Chemistry | Key Asp12 interaction | Reported G12D/WT selectivity |
|---|---|---|---|
| **MRTX1133** | non-covalent pyrido[4,3-d]pyrimidine | ion pair + H-bond to Gly60 CO (bifurcated) | KD 0.2 pM vs 140 nM (SPR); assay-dependent (see above) [1,2] |
| **TH-Z816/827/835** (Cell Discov. 2022, [5]) | non-covalent piperazine series | crystallographically confirmed **salt bridge**: ionic bond + H-bond, **2.7 Å, 166.7°**; binds GDP *and* GMPPNP states (PDB 7EWA, 7EWB) | no measurable binding to WT or G12C (ITC); but cellular effects were **not fully KRAS-mutation-dependent** — off-target inhibition of other small GTPases was reported by the authors |
| **HRS-4642** (Cancer Cell 2024, [6]) | non-covalent, liposomal, long-acting | structure **not disclosed**; design rationale = protonated amine near Asp12, as MRTX1133 | KD 0.083 nM; only **21× vs G12C, 17× vs WT** (SPR); SOS1 IC50 0.72 vs 14.98 nM; RAF1 IC50 5.9 vs 171.8 nM; cellular 0.55–66 nM (G12D lines) vs 249 to >10,000 nM |
| **INCB161734** ([7]), **GFH375/VS-7375** ([8]) | non-covalent "ON/OFF" | not disclosed | clinical stage; no peer-reviewed Asp12 structure |

The pattern across the table: **only scaffolds that reach the Asp12 carboxylate with a well-fixed ion pair achieve large (≥100×) binding selectivity**; HRS-4642, whose pharmacophore reasoning is the same but for which no structure has been shown, reports only ~17–21× in SPR. And the discrimination achieved by *equilibrium binding* (0.2 pM vs 140 nM aside) is smaller than cellular/therapeutic windows because cells add paralog-specific (H95) and pathway-amplification effects.

### 1.4 Covalent and degrader successors

- **Zoldonrasib / RMC-9805 (RAS(ON), covalent, clinical)** — Science 2025 ([9]). Mechanism: the compound binds **cyclophilin A (CypA)** and *creates a neomorphic CYP-A–RAS interface*, positioning an **aziridine** warhead against Asp12 inside the induced pocket. This "privileged environment" produces **enzyme-like rate enhancement**: the warhead has **no intrinsic reactivity toward a model aspartate** and is stable in GSH/whole blood, yet reaches 86% crosslinking at 6 h with **kinact/KI ≈ 102 M⁻¹s⁻¹** (pERK EC50 23 nM in AsPC-1; tri-complex structure PDB 9CTB, 1.29 Å). Covalency, not affinity, provides the selectivity and durability: non-covalent activity is low-potency against WT and non-G12D RAS, and zoldonrasib is described as RAS(ON) G12D-selective because CypA–RAS only forms on active RAS. Preclinical analog RMC-9945. The stated design lesson: *position the reactive group precisely (Colocalize + exclude water + tune the electrostatic environment) and specificity comes from the protein interface, not the warhead's intrinsic reactivity.*
- **Carbodiimide warheads** (JACS 2025, [10]) — an Asp-selective electrophile class reported to covalently label KRAS G12D with an X-ray structure of the covalent adduct and selectivity over other KRAS alleles. Distinguishes itself from earlier "Asp-reactive" chemistry that also hit Cys.
- **Oxirane electrophiles** (JACS 2023, [11]) — the first compound that covalently engages **both G12D and G12C**; useful cautionary example: Asp-directed electrophiles can be **cross-reactive with cysteine**, so "Asp warhead" ≠ mutant specificity.
- **ASP3082 (degrader, clinical)** ([12]) — a KRAS(G12D)-binding ligand linked to a VHL ligand; ternary complex KRAS G12D/ASP3082/VCB at **KD 0.95 nM, DC50 38 nM**; degrades G12D with selectivity over >9,000 proteins and over other RAS variants in the order **12D ≫ 12C, 12V > 13D ≫ 12R, WT**; ternary structure PDB 9L6F. The G12D-binding warhead of the degrader has not been structurally disclosed, but the selectivity hierarchy shows the same trend as the inhibitors: an Asp12-contacting binder discriminates far better than binders that read only the pocket.

### 1.5 What the inhibitor field establishes about Asp vs Gly

1. A **direct charged H-bond/ion pair to the Asp12 carboxylate is the single most effective selectivity handle** (MRTX1133, TH-Z: 2.7 Å salt bridge; monobody 12D1: backbone NH donor, [13]).
2. Selectivity does **not** scale with affinity alone; large affinity windows in SPR can be kinetic (koff). Reported "fold-selectivity" numbers must be read with the assay in mind.
3. Residues **outside position 12** (H95 — KRAS paralog; Gly60; the pocket's plasticity) contribute materially to which protein the drug actually inhibits; the pocket itself is cryptic and induced, so "reading" Asp12 is inseparable from matching a conformational state.

---

## 2. Biophysics of discriminating aspartate from glycine

### 2.1 What actually changes

- **Charge.** At pH 7.4, Asp carries a **−1 carboxylate** (model pKa ~3.7–4.0); Gly has no ionizable group. Burying that charge costs solvation free energy unless it is paired; when paired, it buys a strong, directional Coulomb interaction and up to two charged H-bonds.
- **Size and shape.** Asp replaces the Gly Cα hydrogens with a **Cβ–CγO₂** group (side-chain addition ~50–60 Å³; standard residue volumes: Gly ≈ 60 Å³, Asp ≈ 110 Å³ [14]). In a Gly12 pocket, WT leaves a small, water-filled cavity; the mutant fills it. A binder selected against that cavity is automatically disfavored by WT.
- **Backbone.** Gly is the only residue routinely sampling **φ > 0**; it is a conformational hinge and contributes backbone entropy. Experimental demonstration: inserting **flanking glycines** into staphylococcal nuclease lets a buried Lys66 side chain reach bulk water via helix overwinding — i.e., Gly controls whether buried side chains can hydrate ([15]). The Gly→Asp substitution therefore also changes peptide/side-chain conformational ensembles, not just chemistry.

### 2.2 The desolvation arithmetic (numbers from experiment/theory)

- Continuum electrostatics on 21 protein salt bridges: **17/21 electrostatically destabilizing**, average **3.5 kcal/mol** relative to hydrophobic isosteres; the penalty is a desolvation term of **3.3–23.8 kcal/mol** only partly compensated by the bridge interaction, with effective dielectric dropping from ~45 (exposed) to ~10 (most buried) ([16], Hendsch & Tidor).
- Measured inside a protein: **dielectric ~10–12** ([17]); a buried Lys66 titrates with **pKa 5.7** (vs ~10.4 exposed) ([15]); an engineered buried **Glu–Lys pair interacts for ~5 kcal/mol** yet still destabilizes the protein, because the recovered Coulomb interaction offsets dehydration of only one of the two charges ([18], Robinson et al.).
- At real interfaces: isolated salt bridges moved to a reference environment are **neutral or repulsive**, but the same bridges **inside their native network contribute 1–1.5 kcal/mol each**, with **cooperative triads** ([19], TEM-1/BLIP). Computed desolvation costs of interfacial salt bridges span **~10 to ~210 kcal/mol** depending on burial ([20]).
- **Design implication feeding the KRAS case:** a buried, unpaired Asp is very expensive; a buried, paired Asp is affordable and highly directional. MRTX1133's design explicitly assumed the deprotonated Asp12. Conversely, the free energy *difference* between mutant and WT binding is the only thing that matters — competition between the partner's contact and solvent/water, not the absolute bridge strength.

### 2.3 The pMHC twist: in HLA-A*11:01, the mutant Asp is largely an MHC anchor

- In the crystal structure of the G12D decamer bound to HLA-A*11:01 (PDB 7OW4), **Asp6 (KRAS D12) is buried in the groove**, forming a **salt bridge to HLA R114** (itself stabilized by D116) and an **H-bond to Q70** ([21], Nat Commun 2022). The WT Gly cannot make these. Note the register: in this 10-mer, the mutation sits at peptide position **P6**, and in A*11:01 the center of the groove is the part of the peptide the TCR sees.
- A 2025 structural survey of G12 variants in A*11:01 ([22], Commun Biol) shows **allele-specific burial**: G12C and G12R side chains point outward into solvent; G12A, G12S, G12V and **G12D point inward**, with G12D inserting deeply and forming intramolecular contacts with HLA (R114). In A*03:01 the same G12V is *solvent-exposed* — the same mutation is "visible" or "masked" depending on the allele.
- **Length/register matters**: the G12D 9-mer (VVGADGVGK) binds HLA-A*11:01 in a **bent conformation with the Asp solvent-exposed**, while the 10-mer is compact, more stable (NMR titration; MD) and presents a TCR-accessible surface. A TCR specific for the 10-mer bound the 9-mer at <2% of the 10-mer signal ([22]).
- The JDI TCR structure shows the Asp is **not pre-organized into the groove in the free pMHC**: binding involves **induced fit**, with D6 forming its HLA-A*11 network *upon* TCR engagement ([21]).

**Contested:** [21] describes the D6–R114/Q70 network as stabilizing (formed on TCR binding), while [22] argues G12D "uniquely destabilizes" the complex through a buried charged side chain. Both agree on the key design-relevant fact: in the A*11:01 10-mer, the mutant side chain is **sequestered from solvent and turned toward the groove**, so a reader should not expect a simple surface-exposed Asp to H-bond.

---

## 3. Single-point-mutation specificity in protein–protein recognition: designed, evolved and natural binders

### 3.1 An evolved binder that reads Asp12 directly: monobody 12D1

Koide lab monobodies selected from naive phage/yeast libraries against KRAS(G12D)·GTPγS with **negative selection against KRAS(WT)·GDP** ([13], PNAS 2023). Crystal structure (PDB 8EZG): the monobody binds the S-II pocket and **H-bonds the Asp12 side chain with the backbone NH of Gly81** — an exact mimic of MRTX1133's nitrogen. It also reads **H95** (KRAS paralog handle) via Thr49 (H-bond) and Phe31 (π–π). Affinity-matured 12D1–12D4 reach low-nM KD with **up to 180-fold G12D/WT affinity difference** (~3.1 kcal/mol), ~9-fold preference for GTPγS over GDP state, and no binding to other KRAS mutants or to HRAS/NRAS G12D. Deep mutational scanning of the monobody mapped functional vs non-functional interface residues.
**Key contrast:** the KRAS(G12D)-directed *peptides* (KRpep-2d, KD2) bind the same S-II pocket but show only **moderate selectivity and make no direct contact with Asp12** ([13, 23]). Direct readout of the mutant side chain, again, is what buys high selectivity.

### 3.2 TCR-mimic antibodies against KRAS G12D pMHC

- **C8K10D5-1** (anti-KRAS G12D₁₀/HLA-C*08:02 Fab; Molecular Therapy 2026, [24]): built by an in-silico-then-library workflow; Fab KD ≈ **1.36 μM**; 4.5 Å co-crystal shows a **diagonal, peptide-centric docking mode** — CDR-H3, CDR-L1 and CDR-L3 cover essentially the whole peptide, with only auxiliary contacts over the HLA α1/α2 helices. Alanine scanning: peptide positions **P3, P7, P10 are essential**; no binding to G12V/G12C/G12R variants or to p53 R175H/HLA-A*02:01. Critically, **the mutant Asp (P3 of the 9-mer) does not contact the Fab at all** — it lies below the peptide plane as an anchor salt-bridge partner of HLA-C R156 — yet the antibody is fully mutant-specific because the whole composite epitope differs.
- Panels of TCR-mimic (TCRm) antibodies against KRAS G12V/G12D-HLA were also raised in "RenTCR-mimic" mice ([25], AACR abstract) — showing the epitope class is antibody-addressable, but no structures or selectivity numbers are public. TCRm–pMHC complexes (~45 structures) are catalogued in TCR3d.

### 3.3 Computational and selection-based approaches to single-residue specificity

- **Negative design / second-site suppressors.** The Rosetta-era protocol identifies specificity switches (knob-in-hole, hydrophobic→H-bond, polar→non-polar) by *designing against* the unwanted partner, not just for the wanted one ([26], [27]). Explicit negative design is the standard tool when the off-target differs by one residue.
- **Designed repeat proteins benchmark** ([28]): designed armadillo-repeat pockets discriminated single peptide-position changes across **1–1000 nM** affinity; three physics-based methods (Rosetta flex ddG, Osprey BBK*, PocketOptimizer) each show **residue-class biases** (aromatic vs charged), so per-method errors (~1 kcal/mol, the size of the whole effect) remain a real risk; ensembling helps.
- **Deep-learning specificity.** Fine-tuning AlphaFold on peptide–MHC binder/non-binder data (10,340 examples) reaches **AUROC 0.97 (class I) / 0.93 (class II)**, competitive with NetMHCpan, and generalizes to SH3/PDZ ([29]). But default AlphaFold "tends to dock non-binding peptides in the groove" — it needs explicit negative examples. AlphaFold *competition* experiments can rank single-residue variants, but only statistically over ~100 models per comparison ([30]); single-residue ΔΔG prediction remains unreliable.
- **Conformational-shift design.** Binding specificity can be changed by shifting the **populations of binding-competent states** through remote (core) mutations rather than by touching the interface — demonstrated on ubiquitin open/closed substates ([31]). Relevant because the KRAS S-II pocket and the G12D pMHC register are both conformational-ensemble problems.
- **Natural systems** use the same two strategies: paralog-differentiating residues outside the "hot" position (H95 for MRTX1133 and 12D1), and anchor-driven ligand stabilization (KRAS G12D/HLA-C needs D3 to form the R156 salt bridge to be presented at all — the WT peptide fails to stabilize HLA-C*08:02, so TCRs see no ligand rather than a similar ligand) ([32]).

---

## 4. How TCRs read a one-residue peptide difference: published structural rules

### 4.1 The general rules (and their limits)

- **Docking**: TCRs bind pMHC roughly diagonally; germline CDR1/CDR2 loops sit over the MHC α-helices, hypervariable CDR3 loops over the peptide center (e.g. CDR3s converge over **P5** in class II). Crossing angles vary widely (e.g. 15° vs 63° for two TCRs on the same HLA-C complex); "role assignment" is a simplification — germline loops contact peptide and hypervariable loops contact MHC routinely ("the rules are more like guidelines"; [33], [34]).
- **Which peptide positions are read** depends on register. For a canonical 9-mer: **P1/P2/P3/P6 face down** (MHC anchors; randomized down-facing library = MHC-contact set) and **P4/P5/P7/P8 face up** (TCR-contact set) ([35], 42F3/QL9 system; anchor positions P2/P9). For class II, the "immunogenic triad" is P3/P5/P8 ([36]). MHC helices set and constrain the register, and allele-specific helix residues (e.g. **R65** and **E58** of HLA-A2/A*11 α1; **R156** of HLA-C α2; **R114** of A*11 α2) are recurrent TCR-binding hotspots — the helices both dock the TCR and organize the mutation readout ([33], [21], [32]).
- **Backbone vs side chain.** TCRs make many **conserved polar contacts to peptide backbone C=O/NH** — peptide backbone methylene scans reduce binding, and backbone H-bonds are partly conserved ([37]). Side-chain readout is by shape complementarity and by a small number of **high-quality H-bonds/salt bridges placed where desolvation is affordable**. The A6/Tax case is the textbook demonstration: exquisite specificity for **Gly at P4** arises *indirectly* — only Gly leaves room for CDR3α to pack against the HLA-A2 α1 helix and reach R65; specificity for **Tyr at P8** comes from one nearly optimal, solvent-exposed H-bond whose *limited desolvation penalty* makes it unusually strong ([33]).

### 4.2 The mechanistic taxonomy for single-residue neoantigen discrimination

From the tabulated survey of TCR–neoantigen structures ([32]):
- **Direct TCR contacts with the mutation** (TPI T28I; p53 R175H; **KRAS G12V/A*11:01**).
- **Stabilization of the pMHC ligand by the mutant anchor** (KRAS G12D/HLA-C*08:02 — the WT peptide does not stabilize HLA-C; PIK3CA H1047L).
- **Conformational pre-organization** of the pMHC by the mutation (HHAT p8F).
- **Indirect, energetic mechanisms**: e.g. the 6-11 TCR binds p53 R175H 60× better than WT p53 **with no contact to the mutation**, because engaging WT costs more desolvation; and the JDI TCR reads KRAS G12D through **new electrostatic interactions** with no direct mutation contacts ([32], [21]).

### 4.3 The two KRAS G12D systems in detail

**(a) HLA-C*08:02 nonamer/decamer (clinical TIL case; [38], PNAS 2020; 6ULI/6ULK/6ULN/6ULR/6UON):**
- Mutant **D3 forms a salt bridge with HLA-C R156**; WT Gly cannot, so WT pMHC is not stabilized/presented — specificity is partly at the *presentation* level.
- TCR9a–9d (nonamer-specific) share CDR2β/CDR3α contacts: **P7 Lys H-bonds CDR2β Y48 and salt-bridges CDR2β E49**; CDR3α Q98 H-bonds the P5 carbonyl and HLA-C Q155/R156.
- TCR10 (decamer-specific) reads a **different, TCR-induced peptide conformation** (bulge shifts from P7 to P4–P6; salt bridge CDR3β D95↔P7 K; backbone H-bonds to P4 and P5 carbonyls); alanine substitution of P4–P6 abolishes activation.
- Affinities 16 nM–6.7 μM; **inverse correlation between affinity and in vivo persistence**.

**(b) HLA-A*11:01 decamer VVVGADGVGK (JDI TCR; [21], Nat Commun 2022; 7OW3–7OW6, 7PB2):**
- Parent JDI KD ≈ 63 μM; affinity maturation to **KD 743 pM** (2nd gen; WT 3.0 μM → **>4,000× window**) and 63.7 pM (3rd gen; WT 425 nM → >6,000×).
- Free pMHC and complex structures are nearly superimposable in TCR contacts (RMSD of TCR V domains 0.29 Å; identical 50° crossing angle). **The mutation is not read by a canonical direct contact**: in the complexes, D6 is buried and forms its HLA network (R114 salt bridge, Q70 H-bond) — and the peptide **undergoes induced fit upon TCR binding**.
- Mechanism from thermodynamics + MD ([21]): binding to G12D gains **net electrostatic enthalpy** — the D6-built salt bridge shifts the **surface electrostatic potential of the pMHC around the TCR footprint toward more negative**, which better complements the largely **positively charged TCR residues** (CDR2α W53, which does contact D6; P52α; CDR3β K94). The cost is **entropic** (TΔS = −8.1 vs −1.8 kcal/mol for WT), i.e. rigidification.
- CDR contacts are mostly to the **C-terminal half and backbone** of the peptide (Y33α→A5; N101β/H100β→G7; G98β→G9) and to the α1 helix (R28α–E58, D29α–R65 salt bridges); energy decomposition singles out **R28α** as the only residue contributing significantly to the mutant/WT difference (its side-chain density is weak in the mutant complex — a "frustrated", flexible contact).
- **Register matters**: a TCR specific for the 10-mer recognized the 9-mer at <2% ([22]). And in the same HLA-A*11:01, TCRs against the **G12V** nonamer (VVGAVGVGK) read **P5 Val directly** (CDR3β- or CDR3α-dominated contacts; P4–P5 shift downward vs WT), yet discriminate only **~9×** (14 vs 131 μM) and **~1.5×** (28 vs 42 μM) ([39], 8I5C/8I5D/8I5E; [32]). Direct side-chain contact alone does not guarantee large selectivity if the WT complex can relax to accommodate.

---

## 5. Contested points (read these before designing)

1. **MRTX1133 selectivity figures.** "~700×" (abstract) vs its own KD ratio (~7×10⁵) vs near-equal HTRF competition IC50s vs near-equal WT activity in isogenic cells. Selectivity is assay- and kinetics-dependent; H95 makes part of it paralog-level ([1–3]).
2. **Whether MRTX1133's mechanism is steric or allosteric**, and whether it truly binds only GDP-bound KRAS (2025 NMR/BLI/ITC says it binds both states and freezes dynamics) ([4]).
3. **How the JDI TCR "reads" D6.** Same structures are described as "no direct TCR contacts with the mutation" (review table [32]) and as containing a CDR2α W53–D6 contact (primary paper [21]); the dominant mechanism is indirect electrostatics + induced fit, not a direct H-bond.
4. **G12D stabilizing vs destabilizing in A*11:01** ([21] vs [22]); and whether the 10-mer's D6 should be considered "TCR-accessible" or "masked" — the two papers emphasize different conformations/registers.
5. **"Covalent Asp targeting" specificity.** Oxirane electrophiles cross-react with G12C [11]; carbodiimide warheads claim Asp-selective chemistry ([10]); zoldonrasib needs CYP-A's interface to react at all ([9]) — no general solution yet.
6. **Computational single-mutation design** is not solved: AF2/3-based ΔΔG and docking still mis-rank charge/H-bond swaps at the ~1 kcal/mol level that equals the entire effect ([28–30]).

---

## 6. Transferable principles for a de novo binder (testable design rules)

*Target reference frame: binder must discriminate KRAS G12D (Asp at peptide P6 / protein position 12) from the Gly variant. Conversion used throughout: selectivity S corresponds to ΔΔG = 0.59·ln S kcal/mol at 25 °C (180× = 3.1; 700× = 3.9; 4,000× = 4.9 kcal/mol).*

**P1 — If the mutant carboxylate is solvent-accessible, read it directly with a fixed, bidentate charged H-bond; make the readout networked, not single.**
Place a protonated amine (or Arg/Lys/backbone NH) in a rigidified scaffold so the donor sits at salt-bridge geometry to the Asp12 carboxylate, plus a second H-bond to a **fixed backbone partner (Gly60-CO analog)** — the MRTX1133/12D1 motif. Network/bury the pair so desolvation is compensated (isolated interfacial salt bridges are neutral or repulsive; networked ones contribute 1–1.5 kcal/mol each; [16,19,20]).
*Test:* Asp12→Asn/Ala/Gly single substitutions and neutralization of the binder donor → expect loss of ≥2 kcal/mol binding to the mutant and no gain on WT; verify a 2.5–3.0 Å N···Oδ distance and ≥150° angle in the model/co-crystal; target ≥100× (ΔΔG ≥ 2.7 kcal/mol).

**P2 — If the mutant side chain is buried toward a partner (as in A*11:01 pMHC), do not design a direct Asp pocket — design a positive surface that reads the mutant-induced electrostatic potential and register.**
JDI's >4,000× window came with the Asp buried (salt-bridged to HLA R114/Q70) and *not* H-bonded to the TCR; the discriminating terms were the mutant-dependent shift of pMHC surface potential and contacts from positively charged CDR residues (W53/P52/K94-like) plus backbone H-bonds to the peptide (A5, G7, G9 positions).
*Test:* compute the Δ(electrostatic potential) between G12D and WT pMHC surfaces in the binder footprint; place Lys/Arg residues at the biggest mutant-favorable spots; test WT-side charge-reversal controls. Binding should be lost on the **9-mer register** (bent, Asp exposed) and preserved on the **10-mer**; require ≥2-fold preference for the 10-mer over the 9-mer as a register check ([21,22]).

**P3 — Buy specificity with desolvation asymmetry: put the key H-bonds where the mutant can afford them and the WT cannot (or must pay more).**
Precedents: the A6 TCR's Tyr8 H-bond is strong precisely because it is peripheral/water-exposed (low desolvation penalty); the 6-11 TCR gains 60× on p53 R175H with no mutation contact, purely because desolvating WT Arg175 costs more ([32,33]). Gly12 in KRAS (and Gly6 in the peptide) leaves a hydrated cavity that an Asp-reading binder cannot match; conversely a design that buries an unsatisfied polar group will kill the WT complex first.
*Test:* per-contact solvent-accessible surface area and Poisson–Boltzmann desolvation terms for mutant vs WT complexes (target: mutant-favorable Δ in the desolvation term); ITC should show ΔΔH favoring the mutant; explicitly model the WT Gly cavity and verify the binder cannot seal it (no compensating buried hydrophobic rescue when Asp→Gly).

**P4 — Require two mutation-coupled determinants (composite epitope), so WT must fail twice.**
Examples: Asp12 ion pair **plus** H95 (12D1/MRTX1133 read KRAS-vs-NRAS/HRAS); mutant side chain **plus** peptide register/length (9-mer vs 10-mer are distinct epitopes; TCRs are register-specific [22,39]); mutant **plus** nucleotide/activation state (monobodies prefer GTPγS ~9-fold [13]; zoldonrasib crosslinks only RAS(ON) [9]).
*Test:* binding panels must include G12D vs G12V/C/R/S/A, HRAS/NRAS-G12D, 9-mer vs 10-mer pMHC, GDP vs GTPγS-loaded KRAS. Design rule of thumb: WT must fail at least two independent checks; if it fails only one, expect the ~10-fold class of selectivity (MRTX1133 intermediate series [1]; HRS-4642 [6]; G12V TCRs [39]).

**P5 — Use negative design, selection and deep mutational scanning to enforce specificity; treat equilibrium ΔΔG predictions as noise until proven.**
Explicitly design *against* the WT/Gly surface (second-site-suppressor and negative-design logic [26,27]); mature with yeast/phage display against G12D with WT counter-selection (the 12D1 workflow: positive on G12D·GTPγS, negative on WT·GDP [13]); then map the interface by site-saturation mutagenesis (as done for de novo binders and 12D1) and re-test every affinity-enhancing variant against WT. Physics-based specificities (Rosetta flex ddG, BBK*, PocketOptimizer) carry residue-class biases of order 1 kcal/mol [28]; AlphaFold alone will not rank single mutants reliably [29,30].
*Test:* a design is "done" only when a DMS/SSM map shows that interface positions contributing positively to G12D binding contribute neutrally-or-negatively to WT binding, and when the mutant/WT ΔΔG measured by ITC/SPR agrees with the design model within ~1 kcal/mol.

**P6 — Engineer the kinetic/conformational dimension: match the state the mutant populates and exploit residence time (or irreversibility).**
The S-II pocket is cryptic and induced; the JDI epitope requires an **induced-fit** peptide conformation; MRTX1133's enormous SPR window is dominated by slow dissociation rather than equilibrium binding ([1,2,4,21]). Select binders against the mutant-stabilized state (open S-II pocket; compact 10-mer; GTP-bound RAS), and score by **koff/residence time**, not KD alone.
*Test:* SPR/kinetic analysis must report koff(mutant)/koff(WT) and residence times; MD/ensemble analysis should show the binder engages a conformation populated only (or preferentially) by the mutant; for peptide-MHC targets, test the alternative register and unliganded pMHC to prove state dependence. If the design is covalent, require a demonstrated rate enhancement at the interface (enzyme-like microenvironment) rather than intrinsic warhead reactivity ([9]).

---

## 7. References

1. Wang X. et al. *Identification of MRTX1133, a noncovalent, potent, and selective KRAS^G12D inhibitor.* **J Med Chem** 65:3123–3133 (2022). DOI 10.1021/acs.jmedchem.1c01688; PMID 34889605. (PDB 7RPZ, 7T47)
2. Wang X. et al. *Anti-tumor efficacy of a potent and selective non-covalent KRAS^G12D inhibitor.* **Nat Med** 28:2171–2182 (2022). DOI 10.1038/s41591-022-02007-7; PMID 36216931.
3. Keats M.A. et al. *A nonconserved histidine residue on KRAS drives paralog selectivity of the KRAS^G12D inhibitor MRTX1133.* **Cancer Res** 83:2816–2823 (2023). DOI 10.1158/0008-5472.CAN-23-0592; PMID 37339170.
4. Kim H.N. et al. *Switch II pocket inhibitor allosterically freezes KRAS^G12D nucleotide-binding site and arrests the GTPase cycle.* **J Mol Biol** 437:169162 (2025). DOI 10.1016/j.jmb.2025.169162.
5. Mao Z. et al. *KRAS(G12D) can be targeted by potent inhibitors via formation of salt bridge.* **Cell Discov** 8:5 (2022). DOI 10.1038/s41421-021-00368-w; PMID 35075146. (PDB 7EWA, 7EWB)
6. Zhou C. et al. *Anti-tumor efficacy of HRS-4642 and its potential combination with proteasome inhibition in KRAS G12D-mutant cancer.* **Cancer Cell** (2024). DOI 10.1016/j.ccell.2024.06.001; PMID 38942026.
7. *INCB161734, a novel oral KRAS G12D inhibitor: phase I.* **Ann Oncol** 2025 (ESMO 916O), NCT06179160.
8. *GFH375 (VS-7375), oral KRAS G12D (ON/OFF) inhibitor.* **J Clin Oncol** 43:3013 (2025); ESMO 2025 LBA; AACR 2025 abstract 4394.
9. Weller C. et al. *A neomorphic protein interface catalyzes covalent inhibition of RAS^G12D aspartic acid in tumors.* **Science** (2025). DOI 10.1126/science.ads0239; PMID 40705880. (PDB 9CTB)
10. Sirocchi L.S. et al. *Discovery of carbodiimide warheads to selectively and covalently target aspartic acid in KRAS^G12D.* **J Am Chem Soc** 147:15787–15795 (2025). DOI 10.1021/jacs.5c03562.
11. Yu Z. et al. *Simultaneous covalent modification of K-Ras(G12D) and K-Ras(G12C) with tunable oxirane electrophiles.* **J Am Chem Soc** 145:20403–20411 (2023). DOI 10.1021/jacs.3c05899.
12. *Discovery of KRAS(G12D) selective degrader ASP3082.* **Commun Chem** 8:254 (2025). DOI 10.1038/s42004-025-01662-4; PMID 40849515. (PDB 9L6F)
13. Akkapeddi P. et al. *Exploring switch II pocket conformation of KRAS(G12D) with mutant-selective monobody inhibitors.* **PNAS** 120:e2302485120 (2023). DOI 10.1073/pnas.2302485120; PMID 37399416. (PDB 8EZG)
14. Amino-acid residue volumes (Zamyatnin 1972; Perkins 1986 compilation), BioNumbers BNID 112196.
15. Peck M.T. et al. *Local backbone flexibility as a determinant of the apparent pKa values of buried ionizable groups.* **Biochemistry** 56:5338–5346 (2017). DOI 10.1021/acs.biochem.7b00678; PMID 28952715.
16. Hendsch Z.S., Tidor B. *Do salt bridges stabilize proteins? A continuum electrostatic analysis.* **Protein Sci** 3:211–226 (1994). DOI 10.1002/pro.5560030206; PMID 8003958.
17. García-Moreno B. et al. *Experimental measurement of the effective dielectric in the hydrophobic core of a protein.* **Biophys Chem** 64:211–224 (1997). PMID 9127946.
18. Robinson A.C. et al. *Structural and thermodynamic consequences of burial of an artificial ion pair in the hydrophobic interior of a protein.* **PNAS** 111:11685–11690 (2014). DOI 10.1073/pnas.1402900111; PMID 25074910.
19. Albeck S., Schreiber G. *Evaluation of direct and cooperative contributions towards the strength of buried hydrogen bonds and salt bridges.* **J Mol Biol** 298:503–520 (2000). DOI 10.1006/jmbi.2000.3656; PMID 10772866.
20. *Desolvation costs of salt bridges across protein binding interfaces: implicit vs explicit solvent.* **J Phys Chem Lett** 1:2844 (2010).
21. Poole A. et al. *Therapeutic high affinity T cell receptor targeting a KRAS^G12D cancer neoantigen.* **Nat Commun** 13:5333 (2022). DOI 10.1038/s41467-022-32811-1; PMID 36088370. (PDB 7OW3, 7OW4, 7OW5, 7OW6, 7PB2)
22. Zhu J. et al. *Structure-guided analysis of KRAS G12 mutants in HLA-A*11:01 reveals a length-encoded immunogenic advantage in G12D.* **Commun Biol** 9:26 (2025). DOI 10.1038/s42003-025-09285-0; PMID 41339521. (PDB 8K4T, 8K4V, 8K50, 9UV8, 9WVE, 9WVF)
23. Sakamoto K. et al. *K-Ras(G12D)-selective inhibitory peptides / crystal structure with GDP.* **ACS Med Chem Lett** 8:733–737 (2017). DOI 10.1021/acsmedchemlett.7b00128; PMID 28740607. (KD2: DOI 10.1080/07391102.2023.2192298)
24. Ahn S. et al. *Discovery of TCR-like antibodies to the KRAS G12D neoantigen via an in silico–in vitro workflow.* **Mol Ther** 34:5157–5174 (2026). DOI 10.1016/j.ymthe.2026.05.032.
25. Du J. et al. *Targeting mutant KRAS proteins with novel TCR-mimic fully human antibodies.* **AACR 2024**, abstract 6717. DOI 10.1158/1538-7445.AM2024-6717.
26. Kortemme T., Baker D. *A simple physical model for binding energy hot spots in protein–protein complexes.* **PNAS** 99:14116–14121 (2002). DOI 10.1073/pnas.202485799. (Second-site-suppressor design: Sammond D.W. et al. **Proteins** 78:1055–1065 (2010). DOI 10.1002/prot.22631.)
27. Havranek J.J. *Specificity in computational protein design.* **J Biol Chem** 285:31095–31099 (2010). DOI 10.1074/jbc.R110.157685.
28. Ayyildiz M. et al. *Evaluation of physics-based protein design methods for predicting single residue effects on peptide binding specificities.* **J Comput Chem** 46:e70160 (2025). DOI 10.1002/jcc.70160.
29. Motmaen A. et al. *Peptide-binding specificity prediction using fine-tuned protein structure prediction networks.* **PNAS** 120:e2216697120 (2023). DOI 10.1073/pnas.2216697120; PMID 36802421.
30. *AlphaFold ensemble / competition experiments on ubiquitin–UIM single-residue variants.* PMC11494501.
31. *A designed conformational shift to control protein binding specificity.* **Angew Chem** (2014). DOI 10.1002/ange.201403102.
32. *Structural basis for T cell recognition of cancer neoantigens and implications for predicting neoepitope immunogenicity.* **Front Immunol** 14:1303304 (2023). DOI 10.3389/fimmu.2023.1303304; PMID 38045695.
33. *The evolving T cell receptor recognition code: the rules are more like guidelines.* **Immunol Rev** 329:e13439 (2025). DOI 10.1111/imr.13439; PMID 39804137.
34. *Structural and biophysical determinants of αβ T-cell antigen recognition.* **Immunology** (2012). PMC3246648.
35. *T cell receptor signaling is limited by docking geometry to peptide–MHC.* **Immunity** (2011). PMC3253265. (up/down-facing position analysis; 42F3/QL9)
36. *A simplified amino acid alphabet to unveil TCR antigens: a computational perspective.* **Front Immunol** (2021). PMC7947793.
37. Calbo S. et al. *Role of peptide backbone in T cell recognition.* **J Immunol** 162:4657–4662 (1999). PMID 10202005.
38. Sim M.J.W. et al. *High-affinity oligoclonal TCRs define effective adoptive T cell therapy targeting mutant KRAS-G12D.* **PNAS** 117:12826–12835 (2020). DOI 10.1073/pnas.1921964117; PMID 32461371. (PDB 6ULI, 6ULK, 6ULN, 6ULR, 6UON)
39. Lu D. et al. *KRAS G12V neoantigen specific T cell receptor for adoptive T cell therapy against tumors.* **Nat Commun** 14:6389 (2023). DOI 10.1038/s41467-023-42010-1. (PDB 8I5C, 8I5D, 8I5E)
40. Tran E. et al. *T-cell transfer therapy targeting mutant KRAS in cancer.* **N Engl J Med** 375:2255–2262 (2016). DOI 10.1056/NEJMoa1609279. (clinical validation of the HLA-C*08:02 G12D TIL case)
