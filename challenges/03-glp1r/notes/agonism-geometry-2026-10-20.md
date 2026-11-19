# Agonism geometry: the first validated activation scorer, and what it says about our designs

Date: 2026-10-20. Status of the challenge: C3 deadline Sunday 25 October.

## Why this exists

No released tool predicts whether a design activates GLP1R. The published record
(A. Muratspahic et al., Nature 2026) says confidence metrics do not separate
agonists from antagonists. A community scout found an unmerged, openly readable
scorer that measures the activating geometry directly:
`charleneleong-ai/ai4science` PR #98, `scripts/activation_geometry.py`.

It measures six pharmacophore contacts of the GLP-1 message region, each ranked
by the mutational cost of losing it, plus the insertion depth of the ligand
below the vestibule rim (the ECL residues 205-221 and 298-380). Cutoffs are
declared before any design exists. All numbering is UniProt P43220.

## Calibration: reproduced, not trusted

We ran the scorer on four experimental structures. It reproduces the paper's
numbers exactly, including the known quirks:

| structure | ligand | features | depth (A) | tier | quirk |
|---|---|---|---|---|---|
| 6X18 | GLP-1 (full agonist) | 6/6 | 20.59 | deep | - |
| 6B3J | exendin-P5 (full agonist) | 4/6 | 23.57 | deep | misses R190 anion (5.03 A) - it is the known G-protein-biased agonist |
| 7LLL | exendin-4 (full agonist) | 4/6 | 18.92 | deep | misses Q234 bond (4.93 A) |
| 9IVG | GLP-1(9-36) (weak partial) | 1/6 | 14.15 | shelf | - |

The groove-only control of the source (GLP-1 16-36) scores 0/6 at depth 7.3.

**Tiers**: deep = depth >= 16 A and >= 3 features; shelf = depth >= 10 A;
wrong_face = more intracellular contacts than ECD or TMD; else groove.

## The rescore: all 213 of our designs

Our folds already use the full 409-residue construct (UniProt 24-432) as chain
B, so every feature and the whole pocket exist in our outputs. We rescored every
design in every campaign: 1065 samples, 5 per design. Samples per design give
the pose-agreement check that the scorer's own documentation says is the
mitigation for its main limitation (it scores the pose it is given, not whether
the design would adopt it).

| campaign | designs | deep | shelf | groove | wrong face | 6/6 | 5/6 |
|---|---|---|---|---|---|---|---|
| c1 (RFdiffusion3) | 67 | 53 | 13 | 0 | 1 | 1 | 28 |
| c2 (EvoBind) | 15 | 9 | 1 | 0 | 5 | 1 | 4 |
| c3 (BoltzGen junction) | 55 | 34 | 14 | 2 | 5 | **4** | 10 |
| c5 (BindCraft2) | 18 | 13 | 3 | 0 | 2 | 0 | 8 |
| c6 (SolubleMPNN) | 40 | 30 | 10 | 0 | 0 | 0 | 15 |
| c7 (long peptides) | 18 | 10 | 6 | 1 | 1 | 0 | 3 |

### The perfect (6/6) designs

| design | features | depth (A) | deep/shelf samples | notes |
|---|---|---|---|---|
| **c3-j3-run14** | **6/6** | 23.1 | 5/5 | the strongest result: full pharmacophore with unanimous pose agreement |
| **c2-run1-b206** | **6/6** | 20.6 | 4/5 | the EvoBind peptide, at the exact depth of GLP-1 in 6X18 (20.59) |
| **c3-j3-run21** | **6/6** | 20.0 | 5/5 | unanimous |
| **c3-j3-run3** | **6/6** | 19.8 | 2/5 | weaker pose agreement |
| **c3-j2-run6** | **6/6** | 18.5 | 5/5 | unanimous |
| **e1b2-r0065** | **6/6** | 17.4 | 3/5 | the c1 miniprotein (65 aa) |

A further tier of 5/6 designs exists (e.g. `c2-run2-i299` at 22.7 A, 5/5;
`c6-e1b-r0057-s5` at 55.0 A - see the caution below).

## Honest caveats

1. **The depth number alone is generous for large binders.** Forty of the deep
   designs show depth 40-68 A, which is a binder wrapping past the membrane
   rather than a pocket insertion. The feature count is the discriminating
   metric; depth is secondary. The 5/6- or 6/6 designs with depths above ~30 A
   are flagged, not trusted.
2. **The scorer scores the pose it is given.** Pose agreement across our five
   Boltz samples (the 5/5 column) is the mitigation, not a solution.
3. **This is still in-silico.** The wet-lab cAMP reporter decides. These
   designs are now better-justified bets, not validated agonists.

## Where the results live

- `~/c3-work/c8-agonism/scorers/activation_geometry.py` - the scorer (verbatim).
- `~/c3-work/c8-agonism/calibration-reproduced.csv` - the four structures.
- `~/c3-work/c8-agonism/rescore-rows.csv` - every sample of every design.
- `~/c3-work/c8-agonism/rescore-summary.csv` - one row per design, ranked.

## Consequence

The c3 junction-only config produced the most complete activation geometries.
Campaign 8 scales that exact configuration to 60 further designs.
