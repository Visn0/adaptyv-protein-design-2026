# Rosetta desolvation instrument: control FAILED, disqualified (2026-11-03)

The external review suggested a Rosetta Esol-style ΔΔG as the desolvation
upgrade. Built (ros-desolv.py: interface analysis + P6 D->G mutation + fa_sol
decomposition) and tested against the project's standing control discipline:
the JDI fold must read positive (it prefers the mutant peptide).

## Control result

| protocol | dG_wt | dG_mut | ddG | Esol_wt | Esol_mut |
|---|---|---|---|---|---|
| no repack | -28.9 | -28.9 | +0.0 | 2867.0 | 2860.6 |
| interface repack (pack_input=true) | -124.6 | -124.7 | -0.1 | 2867.0 | 2860.6 |

Required: a clear positive ddG. Delivered: zero, then slightly negative.
**Disqualified - do not use for ranking.**

## Why (the interesting part)

The mutation is invisible to contact-based scoring because there are no
contacts to change: the JDI's nearest atom to the aspartate sits 7.5 A away
(verified in the C0 crystal work). Rosetta's ref2015 is a fixed-charge force
field - it cannot see a buried charge's effect through 7.5 A of groove and
solvent. The repack confirms it: absolute energies drop by ~96 REU (packing
finds many more interactions) while the mutation effect stays at zero.

The Wu 2022 precedent (R175H desolvation-dominated discrimination) does not
transfer: their mutated residue sits IN the interface; ours is read through
the field. The solvent-mediated channel needs an explicit continuum-
electrostatics treatment - which is exactly the class the E-score already
implements in crude form (and the community's APBS difference-map approach
does properly).

## Consequence

Three independent instrument classes have now failed their controls on this
target: fold-confidence metrics (C0, sign inversion), contact-based physics
scoring (Rosetta, zero), and shape-based equilibrium ensembles (BioEmu2,
flat contrast). Only direct electrostatics - the E-score - passes. That
exclusivity is the project's core finding, and this negative strengthens it
rather than weakening it.
