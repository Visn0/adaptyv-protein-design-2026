# Instrument audit, 2026-11-03 (external review + fixes)

## The review's claims, verified

1. **The E-score is blind to histidine.** True: the v1 charge model carried
   Asp/Glu/Lys/Arg only. The native JDI discriminator reads the mutant
   carboxylate with TCRbeta His100 at 7.5 A (three places in
   deep-campaigns.md). 7 of the 20 submissions contain a His; two place a
   ring nitrogen in the 6-8 A shell.
2. **The two flagged designs, measured independently:** peprim-wave1
   run-013 d0007 c1: HIS50 NE2 to D6 = 6.88 A. nat-wave1 run-011 d0000:
   HIS27 NE2 to D6 = 6.10 A. (The reviewer's numbers, exact.) Both were
   ranked low: E +0.85 (demoted) and entry 20.
3. **The desolvation gap.** True and documented in our own notes
   (deep-physics.md): the groove water network is decisive and Wu et al.
   2022 (p53 R175H) settled single-residue discrimination with a Rosetta
   Esol-style dG where desolvation was the dominant term. The E-score's
   desolvation half is a buried-SASA proxy only.
4. **The peptide-MHC specificity classifier** (the Science pipeline's
   filter) has never been run. Availability caveat (deep-campaigns.md
   169): the original fine-tuned parameters were never cleanly released;
   reachable derivatives are the pMHCI screening repo (77forest,
   Zenodo 10.5281/zenodo.15169815) and ADAPT (Zenodo 10.5281/zenodo.17488258).
5. **A second co-folding opinion** is available locally and unused:
   NVIDIA Complexa (six skills in bionemo-agent-toolkit, never used), plus
   complexa-evaluate-pdbs which re-folds through RF3/AF2/ESMfold. Protenix
   (open AF3) is the other candidate (12 GB unverified).
6. **Format diversity** (nanobody/scFv): agreed as the one structural hedge
   never attempted; too large for the remaining window.

## The fix built today

- `escore2.py` - PROPKA-aware E-score. For each folded complex, PROPKA
  gives every binder His a pKa; the fraction f = 1/(1+10^(7.4-pKa)); ring
  nitrogens carry +0.5*f. Calibration matched to v1 exactly (sum over both
  carboxylate oxygens, each -0.5, 83*q1*q2/r^2).
- PROPKA install note: Python >= 3.14 breaks it; the venv is 3.12
  (`uv venv --python 3.12`), at ~/.venvs/propka.

## The corrected table (all 20, E_v2 and closest atom to the D6)

**Every shell His reads 0% protonated** (the HLA R114 +1 field disfavours
protonation there), so E_v2 equals v1 for the whole set. No charged His
exists anywhere in the set's shells.

The closest binder atom to the carboxylate, per design:

| design | E | closest atom | d (A) |
|---|---|---|---|
| repair-wave2-016 d0005 L58K | -1.78 | VAL57:CG1 | 7.36 |
| nim-wave3 run-001 d0004 c7 | -1.13 | SER62:OG | 7.17 |
| wave2-pep run-024 d0007 c5 | -0.87 | ARG76:NH2 | 5.49 |
| peprim-wave1 run-001 d0002 | -1.22 | ARG32:NH2 | 6.93 |
| nim-wave3 run-021 d0001 | -0.37 | GLN51:NE2 | 7.03 |
| mini-wave1 run-014 d0005 | -1.77 | TYR19:OH | 6.59 |
| nat-wave1 run-004 d0001 | +0.14 | ARG31:NH1 | 5.19 |
| peprim-wave1 run-013 d0007 c1 | +0.85 | HIS50:CE1 (NE2 6.88) | 6.66 |
| mini-wave1 run-011 d0001 c5 | +1.62 | SER44:OG | 6.99 |
| wave2-pep run-049 d0002 | -1.92 | TYR21:OH | 7.03 |
| wave1-pep run-016 d0003 | -1.69 | LEU25:CD1 | 7.91 |
| nim-wave3 run-013 d0003 | -0.07 | SER42:O | 7.22 |
| wave2-pep run-026 d0003 | -0.93 | ARG30:NH1 | 7.34 |
| peprim-wave1 run-012 d0006 c3 | -0.65 | GLN8:NE2 | 7.11 |
| nat-wave1 run-011 d0004 | +0.10 | ASN71:ND2 | 7.52 |
| wave1-pep run-033 d0003 | +0.22 | VAL52:CG2 | 7.50 |
| wave4-pep run-007 d0002 | -0.46 | THR18:CG2 | 6.27 |
| peprim-wave1 run-007 d0004 | -1.51 | GLN16:OE1 | 6.21 |
| wave2-pep run-054 d0005 | +1.47 | GLN32:NE2 | 7.39 |
| nat-wave1 run-011 d0000 | +0.09 | HIS27:NE2 | 6.10 |

## The finding that matters

The set's shell readers are overwhelmingly POLAR groups (Ser/Thr/Tyr/Asn/
Gln/His) at 6-7 A, plus compensated charge pairs (e.g. nat-wave1 run-004:
ARG31 at 5.19 A but E +0.14 - a nearby negative cancels it). That is a
dipolar, field-sensing read - the same class as the native His100. **A
charge-Coulomb score systematically undercounts this class.** A low E on a
polar-shell design is an instrument-class mismatch, not a bad design.

## Open items (next steps, in priority order)

1. Desolvation/polar-read instrument: Rosetta Esol-style dG (PyRosetta is
   pip-installable, free for non-commercial use - awaiting the user's
   licensing decision).
2. The classifier attempt (pMHCI repo / ADAPT Zenodo).
3. The second co-folding opinion (Complexa / complexa-evaluate-pdbs).
