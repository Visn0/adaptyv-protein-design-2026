# 03 — GLP1R agonist · research brief (2026-10-18)

Condensed from a three-way research pass (mechanism/prior art; competition
intel; tooling). Every claim carries its source; the full lists live in the
delegation transcripts of 2026-10-18.

## 1. Mechanism — what a designed agonist must engage

- **Two-domain binding.** The peptide's C-terminal helix docks in the ECD
  groove; its N-terminus engages the TM bundle (top of TMs + ECLs).
  [10.1016/j.cell.2016.05.023; 10.1074/jbc.M109.033829]
- **State change on activation.** The apo receptor has a closed ECD lying on
  the TMD (928 Å² interface); the peptide-bound active state stands the ECD up
  along the peptide (interface ~350 Å², ECD tip moves 18–28 Å) and needs the
  TM6 kink to accept Gs. [10.1038/s41467-020-14934-5; 10.1038/nature22394]
- **Non-peptide agonists.** Orforglipron (LY3502970) binds the upper bundle
  contacting the ECD Trp33 lid + ECL2 + TM1/2/3/7 (partial, Gs-biased);
  danuglipron (PF-06882961) overlaps the GLP-1 site and mimics GLP-1
  pharmacology; TT-OAD2 sits at the ECL3/TM6–7 rim (partial, slow).
  [10.1073/pnas.2014879117; 10.1016/j.molcel.2020.09.020; 10.1038/s41586-019-1902-z]
- **ECD-groove occupancy alone = antagonist.** The only published de-novo
  GLP1R-ECD miniproteins (dGl1_024 IC50 61 nM, mGl1_008 IC50 39 nM;
  RFdiffusion + MetaGen, yeast display ~17k designs) are antagonists;
  GLP1R/GIPR/GCGR/CGRPR all yielded antagonists (agonists were achieved for
  MRGPRX1). Of 13 anti-GLP1R antibodies, the single agonist was a GLP-1
  peptide fusion — ECD binding alone did not agonize.
  [10.1101/2025.03.23.644666; s41586-026-10656-8; 10.1080/19420862.2021.1893425]
- **Agonist-likeness in-silico.** The only public attempt: a participant's
  pocket-reach heuristic — activators (exendin-4) reach deep into the groove
  pocket (anchors Q234/W306/E387 in his numbering), blockers (exendin 9–39)
  do not; calibrated with 24 AF2 predictions.
  [x.com/ryaneshea/status/2110741411465179368]

## 2. 6X18 and its neighbours (our computed map: `groove-contacts.md`)

- 6X18: GLP-1 + GLP1R–Gs, 2.1 Å [10.1016/j.molcel.2020.09.020]. Chain R =
  receptor (aligned identity 0.969 vs the challenge segment, UniProt
  numbering), chain P = GLP-1 (30-mer), A/B/G/N = Gs + nanobody.
- Our 6X18 contact map: 56 receptor residues within 4.5 Å of the peptide —
  ECD groove (30–145), ECD/TM junction (148–241), TM pocket (297–392).
  Hotspot CSV: `inputs/groove-hotspots.csv`.
- ECD-groove GLP-1 contacts (from 3IOL): C-terminal helix Ala24–Val33; the
  hydrophobic face (Leu25/Phe28/Ile29/Leu32/Val33) packs the groove; Val33
  H-bonds Arg121, contacts Tyr69/Leu123; Lys26–Glu128; scaffold
  Asp67/Trp72/Pro86/Gly108/Trp110. [10.1074/jbc.M109.033829]
- Active-state neighbours: 6B3J (exendin-P5, biased), 5NX2 (active-like),
  6LN2 (peptide-free, closed ECD), 6XOX/6X1A/6X19 (small-molecule complexes),
  6ORV (TT-OAD2). [rcsb.org/structure/<ID>]

## 3. Competition intel (challenge 3)

- Novelty ≥3/4 is a hard gate; a public replica of the screen exists
  (github.com/adaptyvbio/binder-prescreen) — run the shortlist through it.
- Two public challenge-3 repos, both ECD/groove-focused, both state activation
  is not engineered and ECD-groove binders probably will not activate
  (github.com/Abdulrahman-Neamah/glp1r-agonist-binder-design;
  github.com/jianurr/glp1r-binder-design). One of them: ECD-only targets make
  binders clash into the omitted TM helix bundle — give the designer the full
  receptor.
- Adaptyv's own skills/toolkit: github.com/adaptyvbio/protein-design-skills
  (24 skills), binder-prescreen, competition_metrics (iPTM/ipAE/ESM-PLL
  rank-average), plus the Anthropic binder-design protocol + dataset
  (huggingface.co/datasets/Anthropic/claude-protein-binder-design).
- Generator hit rates (organizer-published, target-dependent): Mosaic 89 %
  (Nipah), MPNN-hybrid 25 %, RFdiffusion 22 %, BindCraft 7 %, BoltzGen 3 %.
- Agonist-capable tools (peptide/cyclic, cAMP-validated): EvoBind
  (github.com/patrickbryant1/EvoBind; dual GCGR/GLP1R cyclic agonist
  EC50 32 nM), RareFoldGPCR (github.com/patrickbryant1/RareFoldGPCR; GLP1R
  peptide agonists EC50 1.2–7.3 µM). No released pipeline produces de-novo
  protein agonists.

## 4. Reusable configs

- BoltzGen GLP1R yaml (3IOL chain A, hotspots 32,39,68,69,91, peptide 21–31):
  supercomputer.sh/docs/examples/boltzgen.
- RFdiffusion flexible-peptide example on GLP-1 (3IOL, contigs
  `[B10-35/0 70-100]`, hotspots B28,B29): RFdiffusion/examples/design_ppi_flexible_peptide.sh.
- BindCraft GPCR recipe (split TMs at the membrane axis, keep local context):
  the BindCraft wiki.
- Peptide potency models: amp91/PeptideModels (GCGR/GLP-1R CNN ensemble).
