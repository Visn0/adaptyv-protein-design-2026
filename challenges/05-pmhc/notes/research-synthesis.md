# Challenge 5 — deep research synthesis (2026-10-30)

Three scout reports sit next to this file: `research-mechanism.md` (literature
and prior art), `research-community.md` (public participant and organizer
signals), `research-tooling.md` (software mapped to this box). Every finding
in them carries a source URL. This file reads the three together.

## The one fact that decides the strategy

Asp6 of the G12D peptide is ~90% buried and salt-bridged to HLA Arg114
(measured by rpinho, 2026-10-27; matching Poole et al. 2022: D6–R114 salt
bridge, stabilised by D116, plus a Q70 hydrogen bond). The JDI TCR makes no
direct contact with the mutation — its nearest atom sits 7.5 Å from the Asp
carboxylate. Discrimination is an **electrostatic field perturbation above
the groove**, not a direct Asp contact. The APBS difference map measured
8.4 kT/e at 6–8 Å, negative sign, epicentre at peptide positions 6–7.

## The second fact: static folds cannot see the difference

Measured control (rpinho, 2026-10-27): ColabFold AF2-Multimer gives the known
JDI TCR the **same ipTM 0.84** on the G12D and the wild-type complex. Mean
ipTM: 0.818 / 0.772 / 0.710 for G12D / WT / peptide-free. A screen that ranks
on raw ipTM is blind to the objective. This is the sharpest instance yet of
our own rule that a fold score is not site evidence.

## What is proven to work (literature)

- Liu et al., Science 2025 (10.1126/science.adv0185): RFdiffusion backbones
  that "arc above" the groove, hotspots on outward-facing peptide residues,
  ProteinMPNN, AF2 plus a fine-tuned specificity filter (Motmaen 2023).
  11 pMHC targets, single- to double-digit nM binders, peptide-specific CAR
  activation. Failure mode: cross-reactivity with proteome peptides sharing
  outward-facing residues.
- Johansen et al., Science 2025 (10.1126/science.adv0422): minibinder
  NY1-B04 against NY-ESO-1/HLA-A*02:01, KD 6.9 nM, cryo-EM 3.8 Å, kills
  cells in a CAR format. 44 filtered designs yielded 1 binder (~2%).
- TCRm precedents (same idea, protein formats): the engineered JDI TCR
  reaches 64 pM (parent 63 µM) with a >6000× wild-type window; tebentafusp
  (24 pM, approved); a KRAS G12D/C*08:02 TCRm antibody reached low nM
  (Mol Ther 2026).
- No published de novo binder exists for this exact pMHC. The prescreen's
  `kras-pmhc` reference set is TCR-only and says so. The competition is new
  territory.

## The two live public strategies (as of Oct 30)

1. **Electrostatic placement** (rpinho's panel, measured): place a cation
   (Arg/Lys/His) 7–8 Å above peptide positions 6–7, where the G12D-minus-WT
   potential difference is strongest.
2. **Liu-style peptide-hotspot diffusion plus specificity filters** (the
   ElainW campaign, June 2026, same neoantigen but the 9-mer register):
   1,000 backbones → 7,472 sequences → 914 AF2-tested → 4 pass (0.4%).
   Its filters: peptide-specific ipSAE, delta-PAE specificity, p5-contact
   reads. Caution: ElainW used the 9-mer VVGADGVGK (PDB 9UV8), not our
   10-mer VVVGADGVGK (7OW6) — do not copy its hotspot numbering.

## Tooling verdict for this box (12 GB RTX 5070)

- RFdiffusion v1: proven on pMHC (Science 2025); peptide hotspots on
  outward-facing residues (P4–P8), never the buried groove floor.
- RFdiffusion3: mechanically supported; third-party pMHC configs exist
  (BinderGeneration: chains A,B,C, hotspots on peptide residues 3,4,5,7,8;
  pepbench-tcr). No official example; hotspot numbering is on us.
- BindCraft (v1/2): officially multi-chain, but the only public pMHC run
  failed (0 of 100+ accepted overnight; fixed only after moving hotspots to
  the groove rim plus exposed peptide). BindCraft2's `bindcraft score`
  (Hotspot_Contact_Fraction, Off_Epitope_Contact_Fraction, coldspots) is a
  usable QC layer regardless.
- BoltzGen: a public NY-ESO-1 exercise marks HLA and β2-microglobulin as
  non-binding regions; heavy, not local.
- ADAPT (Motmaen/Jude/Baker/Garcia, Nov 2025): purpose-built for pMHC
  (TCRs and antibodies); WIP repo — watch it.
- ipSAE: the chain-pair table fits our scorer (binder–peptide vs binder–HLA
  vs binder–β2-microglobulin rows); organizers' thresholds: ipSAE_min > 0.61
  standard, > 0.70 stringent.
- binder-prescreen ships a `kras-pmhc` target set (144 TCR references,
  22 confirmed binders) — the novelty gate is ready for this challenge.

## Organizer signals

The Tracks 2/3 selection prompt lists the hardest objective first (no WT
binding, no peptide-free binding, then G12D affinity) and says: model the
whole complex, not the peptide alone. The organizers' in-silico metric set
carries no mutation-specificity term — specificity is an experimental
readout, so in-silico specificity evidence is a design-quality lever, not a
leaderboard one.

## Implications for the strategy step (feeds `strategies.md`)

1. Run the JDI positive control (7OW6 chains) through OUR stack on all three
   states before generating anything. If our instruments cannot separate
   G12D from WT for a known binder, fix the instruments first (the C4
   restrained-screen pattern).
2. Design against the receptor-bound (closed) peptide conformation; arc
   above the groove; hotspots on outward-facing peptide residues plus the
   groove rim.
3. Multi-state screen: fold every candidate against G12D, WT and
   peptide-free; read contacts at position 6 and interface scores per chain
   pair; require the binder–HLA and binder–β2-microglobulin rows to stay
   weak; add an electrostatic term (APBS or a charge-placement heuristic)
   for the P6–P7 zone.
4. nM affinity is enough. Do not trade specificity for picomolar affinity.
5. Expect a low yield: published pMHC campaigns pass ~0.4–2% of filtered
   designs. Plan hundreds to thousands of backbones per campaign.

## Second pass — the deep dive (same day)

Full reports: `deep-physics.md`, `deep-similar-targets.md`,
`deep-campaigns.md`; the design factors are consolidated in
`target-physics.md`. What changed:

- The JDI thermodynamics are measured: ΔH −20.3 vs −9.6 kcal/mol (G12D vs
  WT), TΔS −8.1 vs −1.8 — enthalpy-driven with a real entropy cost. The
  mutation is read as indirect electrostatics ("the difference in binding
  energy is primarily driven by changes in electrostatic potential in
  pHLA").
- The single-residue desolvation precedent is the p53 R175H TCR 6-11 (Wu
  2022 JBC), not the H2 antibody — H2 reads its mutation by direct contacts.
- The peptide flips on engagement (induced fit): the bulge is mobile and
  P5–P6 are invisible without a binder; both peptides order on TCR binding.
  The 9-mer register is a decoy (flattened; its Asp does not reach R114).
- Empty MHC-I is not a clean protein: unlocked/partially collapsed,
  heterogeneous, peptide-scavenging. Read the peptide-free arm with that in
  mind.
- Published binder campaigns all "arc above the groove" with peptide-first
  footprints, but Johansen's cryo-EM hit still makes more MHC contacts than
  peptide contacts (46 vs 21 pairs) and reaches both helices; its
  specificity lives in a hydrophobic pocket over P4–P5. Odin-Multi's
  counter-selection doubles the specific-design rate (6.0% → 14.2%).
- The C8K10D programme shows the classic failure: mid-affinity clones bind
  unpulsed (peptide-free) cells; negative selection on unpulsed cells fixed
  it. Counter-select against the peptide-free state from the first round.
- Operational warning: the public 9-mer repos used 9UV8 (VVGADGVGK, Asp at
  P5). Our target is the 10-mer VVVGADGVGK (Asp at P6). Never copy their
  hotspot numbering.

## Third pass — edges and reuse (same day)

Reports: `edge-viewpoints.md`, `edge-modalities.md`, `edge-resources.md`,
`reuse-audit.md`. What changes:

- The honest field verdict: structure-based specificity prediction is NOT
  solved (AF3 ROC-AUC ≈ 0.6, "would need ≈ 0.9"; its discrimination tracks
  TCR pose placement, not chemistry). A meta-analysis of 3,766 measured
  binders finds few generalisable in-silico features. Reviews place TCR-agent
  methods "two decades behind therapeutic antibodies". Expect our screen, not
  a published score, to be the instrument.
- Calibrated expectations: "6 of 30 top AI designs bound peptide-specifically"
  (JITC 2025 benchmark); Liu 8/11 CAR-functional; Johansen ~2%; Odin-Multi
  enrichment 11/166 → 3/167 with counter-selection; Adaptyv hit-rate history
  2.5 → 13.2 → 9.6 → 37% across targets. Plan for a low yield.
- The WT counter-target is real and stable — unlike HLA-C*08:02, where the WT
  peptide does not stabilise the allele at all. On A*11:01 the WT complex is
  MS-detected and G12D actually destabilises the complex (fastest-degrading
  mutant in the chase assay). Discrimination must come from the binder; the
  JDI TCR proves a >6000× window is achievable.
- Both registers are presented in vivo (9-mer and 10-mer); the challenge's
  10-mer is the TCR-accessible one. A 10-mer binder may not see the 9-mer —
  relevant when reading the literature, not for our target choice.
- The realistic winner shape: Householder's designed mini-TCRm docks
  diagonally at ~40°, buries 1216 Å², 31% from the peptide; but even
  NY1-B04's long-lived contacts lean MHC (5 residues vs 3). Peptide-first,
  not peptide-only, is the practical bar.
- Modalities: no small molecule or macrocycle discriminating a mutant pMHC
  exists (white space); the only working modality family is protein binders.
  Clinical G12D/A*11:01 is TCR-T only (AZD0240 recruiting); every protein
  binder is preclinical. Nabla's VHH-from-sequence design with a 0.93 Å
  cryo-EM match on KRAS G12V shows industrial zero-shot design now works.
- Reuse (see `reuse-audit.md`): the C4 selector/validator/builder adapt
  directly; the Chai-1 restrained screen is the instrument-test vehicle; the
  novelty prescreen is fully provisioned locally (`~/prescreen-dbs`, 113 GB,
  all eight arms; `kras-pmhc` slug; mmseqs binary present); a new `c5`
  pipeline owns the tri-state specificity scoring.

## Open unknowns

- Whether Boltz-2 or Chai-1 separate the G12D/WT complexes better than AF2 —
  untested anywhere public.
- RFdiffusion3's pMHC hotspot choice (open unanswered issue in the foundry
  repo).
- Peptide-free HLA stability for this allele is unmeasured.
- The 9-mer vs 10-mer register difference across the public KRAS work.
