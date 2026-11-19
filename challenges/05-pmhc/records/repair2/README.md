# Repair round 2: fixing the weak-E entries (2026-11-03)

Target: the nine submitted designs whose E-score read neutral or positive
(the composite's identified drag; avg E-term 1.9/20). Method: the proven
charge-directed variant recipe - basic substitutions at the D6 shell
positions (5-13 A), 4 variants per design, fold, keep only fold-clean
E-improvers.

## Result: 36 variants, 9 qualify (ipTM >= 0.93, i_pDAE >= 0.55, E gain >= 0.3)

Three beat their parents on the full composite (after their WT + peptide-free
arms were folded):

| parent (old score) | variant | E before -> after | new score |
|---|---|---|---|
| wave4-pep run-007 d0002 (62.5) | A58K | -0.46 -> -1.77 | **80.1** |
| nat-wave1 run-011 d0000, rank 20 (60.9) | H27K | +0.09 -> -0.97 | **77.1** |
| nat-wave1 run-011 d0004 (63.4) | N71K | +0.10 -> -0.78 | **76.3** |
| peprim-wave1 run-013 c1 (65.7) | A22K | +0.85 -> -0.24 | 51.5 - REJECTED (dfree collapsed 0.665 -> 0.063) |
| nat-wave1 run-011 d0000 | Q24K | +0.09 -> -1.57 | 76.9 (sibling; H27K won on interface) |

Notes:

- **H27K mutates the native-like shell histidine itself into a lysine** -
  the external review's observation (the native JDI reader is a His100 at
  7.5 A; our score was blind to it) converted into a design fix: the neutral
  ring replaced by a real charge. It lifts the design from rank 20 to the
  top five.
- **N71K** fixes the residue that sits closest to the carboxylate in its
  design (Asn71 ND2 at 7.52 A, a neutral amide -> now a charge); it also
  carries the best dWT of the three (+0.287).
- **A58K** gives the biggest composite jump (+17.6) with the interface
  quality improving (i_pDAE 0.78).
- Five entries resisted repair: their variants either broke the fold
  (wave1-033, nim-013) or gained nothing usable (wave2-054, nat-004,
  mini-011). Honest negative, recorded.

## The set after the swaps (v4)

Top eight: L58K 83.1 | nim-001 c7 82.8 | A58K 80.1 | wave2-024 c5 79.1 |
peprim-001 78.1 | H27K 77.1 | N71K 76.3 | nim-021 68.3. Four entries above
76 (previously two). All three new variants are in their seeds + chai + apo
validation round (the same coverage as every other entry).
