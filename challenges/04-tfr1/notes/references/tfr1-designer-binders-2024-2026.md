# TfR1 (CD71) designed binder landscape — TB14 family + 2024–2026 public binders
Research deliverable for the de novo minibinder campaign vs TfR1 apical domain (K344/K374 face, P02786 numbering).
Reference/instrument-validation use only — do NOT copy any sequence into a submission (competition rules).

Compiled: 2026-10-28. Every claim below verified against primary sources (paper page/PMC, PDB REST/GraphQL, patent text) unless explicitly flagged as inference or unverified.

---

## 1. TB14 family — the paper behind DOI 10.1002/pro.70384  ★ primary answer

- **Paper**: Veetil AA, Sjöström DJ, Iribarren C, Mohlin C, Ambrosetti E, Bjelic S.
  "Targeting the apical domain of the transferrin receptor: Development of a new protein scaffold for cellular delivery."
  *Protein Science* 34(12):e70384, Dec 2025. DOI: 10.1002/pro.70384 | PMID 41254484 | PMC12626770 | Open access (CC-BY).
  Lab: Linnaeus University (Kalmar) + Karolinska Institutet. https://doi.org/10.1002/pro.70384
- **Design method (NOT RFdiffusion/BindCraft)**: computational docking of a small-scaffold library onto the TfR apical domain at the Machupo virus GP1 (MGP1) binding site (superposed on MGP1–TfR, PDB 3KAS), then RosettaScripts interface (re)design (protocol from Sjöström et al. 2022 FEBS J). 12 scaffolds advanced based on interface size 600–1000 Å² + shape complementarity. Best design "TB14" built on scaffold **PDB 2NZC** (TM1266, *Thermotoga maritima*, 86 aa). Then yeast surface display (pETCON2/EBY100) + 2 rounds error-prone PCR directed evolution + SPR.
- **Length**: TB14 designs are **84 aa** (the parent scaffold 2NZC is 86 aa). Note: the "~86 aa" figure circulating refers to the scaffold.
- **Epitope**: apical domain, Machupo GP1 site. Hydrophobic pocket around TfR **Tyr211** (P02786 numbering) formed by TB14 L9/I11/K74/M76; TB14 H41 ~4 Å from TfR L212/V213 backbone; T78I packs near TfR residues labelled "Asn225/Lys248" in the paper — by residue identity these are **P02786 Asn348/Lys371** (paper numbering offset −123; P02786 225=Ala, 248=Thr). Flagged: inference from identity + unique offset; N348/K371 sit inside the MGP1/2DS25 footprint that contains K344/K371/K374.
- **Affinities (SPR)**: TB14.3 (E16K) Kd ≈ 2 µM → TB14.3A (E16K/N45Y) Kd = 320 nM → S4.4 (T78I) Kd = 240 nM (YSD: 305 ± 55 nM); S4.7 (E13V/T78I) similar. TB14.2 only bound detectably at 1 µM (YSD). eGFP–TB14.3 internalizes into HeLa cells (comparable to Tf–FITC; 7× vs 11× background-subtracted).
- **Public sequences**: YES — Supporting Info (pro70384-sup-0001-supinfo.pdf, Fig. S2) gives **DNA sequences** of TB14, TB14.1, TB14.2, TB14.3 (+ eGFP–TB14.3 fusion). Translated protein sequences (below) verified by internal consistency (every stated mutation D32Y/T55V/T59A/P40D/E16K/N45Y/T78I/E13V reproduces exactly).
- **Public structure**: NONE. Data-availability statement: "available from the corresponding author upon reasonable request". No PDB deposition (verified: full-text search "TB14" and all P02786-mapped entries).

### Sequences (84 aa; translated from SI DNA — reference only, do not reuse)
```
TB14      MEKRFYVLLIIVEDREKAYRQVNELLHNFSEDILLRMGQPHRERNQSTIALVLKTDNDTIGALSGKLGQISGVKVMTTPEKRGS
TB14.1    MEKRFYVLLIIVEDREKAYRQVNELLHNFSEYILLRMGQPHRERNQSTIALVLKVDNDAIGALSGKLGQISGVKVMTTPEKRGS   (D32Y,T55V,T59A)
TB14.2    MEKRFYVLLIIVEDREKAYRQVNELLHNFSEYILLRMGQDHRERNQSTIALVLKVDNDAIGALSGKLGQISGVKVMTTPEKRGS   (+P40D)
TB14.3    MEKRFYVLLIIVEDRKKAYRQVNELLHNFSEYILLRMGQDHRERNQSTIALVLKVDNDAIGALSGKLGQISGVKVMTTPEKRGS   (+E16K)
TB14.3A   MEKRFYVLLIIVEDRKKAYRQVNELLHNFSEYILLRMGQDHRERYQSTIALVLKVDNDAIGALSGKLGQISGVKVMTTPEKRGS   (+N45Y)
S4.4      MEKRFYVLLIIVEDRKKAYRQVNELLHNFSEYILLRMGQDHRERYQSTIALVLKVDNDAIGALSGKLGQISGVKVMTIPEKRGS   (+T78I)
S4.7      MEKRFYVLLIIVVDRKKAYRQVNELLHNFSEYILLRMGQDHRERYQSTIALVLKVDNDAIGALSGKLGQISGVKVMTIPEKRGS   (+E13V,T78I)
scaffold  GHMEKRFYILTIVVEDREKAYRQVNELLHNFSEDILLRVGYPVREENMAIIFLVLKTDNDTIGALSGKLGQISGVRVKTVPLKRGS   (2NZC, 86 aa)
```
- **Why it matters**: the closest public design to this campaign's target face (same apical-domain site as MGP1/2DS25, i.e., the K344/K374 neighbourhood); a non-RFdiffusion (docking + Rosetta) baseline that needed display maturation from µM to ~240 nM — calibrates affinity expectations, validates YSD/SPR/internalization instrument chains, and confirms the site is tractable but hard.
- Same lab, related public structures: **6Y76** (AP01 redesigned apical domain, Sjöström 2020) and **8P0Z** (AP01-S2.3, affinity-matured, 2023 JMB) — useful as TfR-apical-domain calibration reagents (AP01 was used as competitor in the TB14 paper).
- Earlier related design from same lab: **TB08** (FEBS J 2022, DOI 10.1111/febs.16311) — helical-domain binder, Kd ≈ 1 µM; different epitope.

---

## 2. BCY17901 / BCY15466 — Bicycle peptide (2025, public co-crystal structure)

- **Paper**: Østergaard ME et al. "Conjugation to a transferrin receptor 1-binding Bicycle peptide enhances ASO and siRNA potency in skeletal and cardiac muscles." *Nucleic Acids Research* 53(7):gkaf270, Apr 2025. DOI 10.1093/nar/gkaf270 | PMID 40207629 | PMC11983102. (Ionis + Bicycle Therapeutics.)
- **Structure**: **PDB 9GH7** (X-ray, 2.3 Å; released 2025-04-30) — human His6-TfR1 (C89–F760) + **BCY15466**, peptide sequence **ACPPDAHLGCISWCA** (C-terminal amide; 15 aa + tricyclic TATB scaffold; ~2 kDa). Sequence is public in PDB entity 2 and in the paper SI.
- **Method**: phage display of bicyclic peptide libraries + medicinal chemistry / affinity maturation (non-natural AAs: Aib, Aze, HyP, tBuAla, Cba, tBuGly, EPA, 2Nal, 1Nal). NOT computational de novo design.
- **Epitope**: pocket **between the apical and protease-like domains** (SI text; verified by my contact analysis of 9GH7: TfR residues 150–161 incl. K161 salt bridge to peptide Asp3 and S159; 190–195; Y219; 382–384; W412–G413 with scaffold; F458; T569). **Non-competitive with transferrin** (SPR + superposition with Tf–TfR structure 3S9L; my computed Tf footprint on TfR = 121–125 + 619–758). Distinct from the K344/K374 face.
- **Affinity**: unconjugated BCY17901 = single-digit nM on human TfR1 (SPR; SI Table S5); Bicycle–ASO conjugates Ki 89–2 nM (BRET); ~10× weaker on cyno TfR1; lead for muscle LICA (ED50 improvements 5–8× vs unconjugated ASO).
- **Why it matters**: public, high-affinity, non-antibody TfR1 binder with atomic structure — excellent positive control for binding/internalization assays and for specificity counterscreens; demonstrates a second druggable pocket distinct from both the Tf site and the campaign's K344/K374 face.
- Caveat: BCY17901 is NOT in NCBI Protein (the "BCY17901" protein accession there is an unrelated bacterial protein); the optimized lead contains non-natural residues — use PDB 9GH7 / SI for the parent peptide structure.

---

## 3. Eli Lilly patent WO2025042711A1 (2025) — engineered TfR-binding peptides

- **WO2025042711A1** "Engineered transferrin receptor binding peptides as well as methods of making and using the same"; Eli Lilly and Co; priority 2023-08-18, filed 2024-08-16, published 2025-02-27; inventors S. Afshar, H. Eissa, C. J. Rito. https://patents.google.com/patent/WO2025042711A1/en
- **Content**: 46 SEQ ID NOs — TfR-binding peptides of **14–20 aa** (2–3 Cys, disulfide-constrained), plus consensus "Formula I" (SEQ 17: X1X2X3CRSFYPX10X11YCX14AM). Representative sequences: SEQ 18 = `FWDCRSFYPFDYCEAM` ("Peptide 15", lead, 16 aa); parent SEQ 10 = `QSWEACRSFYPQDYCVAMKN`.
- **Affinity/data**: Peptide 15 SPR KD 25 nM (hTfR) / 160 nM (cyno), cell EC50 17 nM; internalizes (hCMEC/D3, EFO-21); siRNA conjugates active (IC50 6–9 nM); no mouse TfR binding.
- **Epitope**: stated to be "distinct from the transferrin (Tf) binding site" (HDX-MS epitope mapping, FIG 4B — image only, exact residues not readable → unverified).
- **Why it matters**: large public sequence trove of small internalizing TfR1 binders; useful as peptide-scale benchmark and for prior-art/FTO awareness.

---

## 4. 2DS25/3DS18 sheet-extension miniproteins (2021) — verified PDB mapping (correction)

- Paper: "Transferrin receptor targeting by de novo sheet extension", PNAS 2021, DOI 10.1073/pnas.2021569118.
- **Verified PDB ↔ variant mapping (RCSB titles)**: **6WRX = 2DS25.1**, **6WRW = 2DS25.5**, **6WRV = 3DS18** (the commonly cited order 6WRV=2DS25.1 is wrong).
- 10 kDa, hyperstable (Tm > 95 °C); Kd 20–400 nM across variants (2DS25.5 = 20 nM); β-sheet-extension binding mode; competes with Machupo GP1; crosses an in-vitro BBB chip.
- **Epitope (computed from 6WRV=3DS18)**: TfR 199–215 (incl. Y211, L212, N215) + 340–376 (incl. E343, **K344**, N348, **K371, K374**, T376) — i.e., exactly the K344/K374 face this campaign targets, overlapping the TB14 site.
- **Why it matters**: the reference "same-epitope, de novo, RFdiffusion-era-preceding" designs with public sequences + structures; the natural yardstick for designs against this face.

---

## 5. Adjacent / non-de-novo TfR1 binders (context; sequence availability flagged)

| Agent | Type | Source (verified) | Notes |
|---|---|---|---|
| NewroBus nanobodies (TfR1b-Nbs) | camelid VHH, humanized (AbNatiV) | Cell Commun Signal 2025; DOI 10.1186/s12964-025-02605-1; PMID 41462276; bioRxiv 10.1101/2025.04.20.649139 | pM KD; non-competitive with Tf; BBB transcytosis; NO PDB for TfR–nanobody complexes 2024+ (verified); sequence availability not checked → unverified |
| Anti-TfR nanobody papers 2025 | VHH | PMID 40089126 (Protein Expr Purif 2025); PMID 40824762 (eLife 2025) | immunization/display-derived; sequences unverified |
| Type-II VNAR anti-TfR1 | shark VNAR | US Patent 12187805 | patent sequences; not independently verified |
| TfR-binding cystine-dense peptide (TfRB1G3 lineage) | 49 aa CDP (PDB construct = GS + 49 aa: `GSREGCASRCMKYNDELEKCEARMMSMSNTEEDCEQELEDLLYCLDHCHSQ`) | J Mol Biol 2020, DOI 10.1016/j.jmb.2020.04.002, PMID 32304700; **PDB 6OKD** (TfR complex) & **6OKE** (apo) | Kd 216 pM (TfRB1G3); Tf-competitive; mouse cross-reactive; native-CDP library + maturation (not de novo) |
| Antibody agents (Trontinemab, Pabinafusp, Delpacibart, Zeleciment) | mAb/fusion | (known to project) | — |

---

## 6. Verification notes / negative results

- **PDB search for TB14**: no entry. Full P02786 (human TfR1) entry list = 24 entries total; the only 2024–2026 releases are **9GH7** (Bicycle, 2025-04-30), **11RN** (B19V VP1u RBD complex, 2026-05-27) and **11QC** (apo TfR ectodomain, 2026-05-27). No new designed-miniprotein–TfR1 complexes in PDB 2024–2026 beyond the above.
- No 2024–2026 bioRxiv/Europe-PMC preprint found on de novo miniprotein binders vs TfR1 other than the items above (searches: Europe PMC preprints, PubMed, web).
- TB14 "Asn225/Lys248" labels: P02786 numbering gives Ala225/Thr248; the unique identity-consistent mapping is Asn348/Lys371 (offset −123). Treat as inference (paper itself does not state P02786 numbering for these two).
- TB14.1/2/3 protein sequences are translations of the SI DNA (SI shows DNA + an image alignment figure); reconstructed TB14.3A/S4.4/S4.7 follow from the mutations stated in the paper — all cross-checked.
- Machine-readable copy of the sequences: `~/.hermes/cache/scratch/tb14_family.json`.
