# Methods (final, for the submission form)

**Target:** KRAS G12D peptide `VVVGADGVGK` (residues 7-16) presented by
HLA-A*11:01 + beta-2-microglobulin. Objective: bind the mutant complex,
discriminate the wild-type peptide (single D->G change at P6) and avoid the
peptide-free MHC.

**Design generation.** Peptide-centric de novo backbones from the hosted
RFdiffusion4 NIM, conditioned on the peptide ridge (hotspots P4-P8): five
sampling waves plus three targeted campaigns (charge-first, minibinder length
priors, natural-reader priors), 2,264 backbones collected (2,247 unique).
Every backbone went through a geometry screen before sequence assignment; the
passers (~20% per wave) continued. The screen requires the binder to arc over
the peptide ridge and to place a basic nitrogen in the 6-8 A shell above
P6/P7 - the electrostatic reading of the mutant side chain that the published
JDI TCR uses to gain its >4000x mutant/WT window. Near the end, the model was
re-hosted locally (RFD4-Proteina, BSD-3): 32 fresh designs reproduced the
hosted funnel's hit rate exactly (19% vs ~15% interface-class), confirming the
pipeline no longer depends on any hosted service.

**Sequence assignment.** ProteinMPNN on screened backbones; a LigandMPNN pass
naturalized children of the best designs; two charge-directed repair rounds
(basic substitutions in the P6 shell) contributed one strict win each (L58K,
then a second round feeding the evolution below).

**Folding and scoring.** Boltz-2, five diffusion samples per design; reads:
ipTM, ipSAE, i_pDAE. Every candidate was folded in a three-state panel -
mutant, wild-type, peptide-free. The panel was calibrated first: fold-score
deltas alone cannot rank G12D vs WT specificity (controls invert), so
specificity rides on explicit electrostatics, not confidence scores.

**The E-score** is the specificity instrument: the Coulomb interaction between
binder charged groups and the P6 aspartate carboxylate (distance-dependent
dielectric) plus the count of charged atoms within 8 A. It is the only
instrument that passes its control - the known JDI binder reads the correct
sign (-0.67, the published indirect read). A scope caveat was found and
tested: a naive whole-interface Coulomb sum does not predict
measured affinity (r = -0.08 against 1,174 ATLAS wet-lab entries); the
site-specific form is the validated one. Sixteen of the twenty submitted
designs read negative (best -3.75); four older entries read neutral to
positive (+0.14 to +1.47) and are retained on their other validated axes
(`escores.csv`).

**Evolution loop.** A mutation-selection loop (breed the current top parents,
fold, score against the composite, promote winners) ran in generations, the
final one automated with the guardrails built in: a strict margin (+1.0
composite over the parent), one winner per parent family, hard fold gates.
Six promotions in total reshaped the top of the set; the three final champions
are single basic substitutions that each turned a marginal parent into a
top-5 design (best composite 90.5). Everything is reproducible from the
records directory.

**Orthogonal and stability checks.** Chai-1 with MSAs as the second instrument
(only fold model with the correct sign on the controls; supporting only);
three-seed Boltz-2 stability (spread <= 0.006 for the champions); binder-alone
folds (the champions at pLDDT 0.96-0.97); BioEmu2 contact-conditioned
ensembles confirm the charge reading persists under thermal motion (K58-D6 at
7.4 +- 0.8 A across 16 frames - the JDI's geometry class).

**Selection.** Composite ranking (v3): i_pDAE 30%, ipTM 20%, peptide-free
dependence 20%, E-score 20%, WT discrimination 10%. Gates: de-novo eligibility
(any SwissProt hit >= 90% identity excludes); diversity cap of two per
generation run; no design whose WT/free reads exceed its mutant read;
charge-clash screen (clean, max 2 pairs); liability screen (all flagged items
minor and recorded).

**The 20 submitted designs** mix eight campaign parents with twelve
evolution/repair children. Sixteen clear the organizer's ipSAE gate
(peptide_read >= 0.61). The set's best reads: dWT +0.747 (L58K-Q15K) and
the E-score -3.75 (A16K). All are 64-98 aa and homology-screened; binder-alone
folds read pLDDT 0.93-0.97 where measured.
