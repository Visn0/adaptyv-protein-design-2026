# Evolution gen 1: children of the top-8 (2026-11-03)

First generation of the automated evolutionary loop (evo.py): for each of
the current top-8 parents, basic swaps at up to 6 unsampled shell positions
(5-13 A from the P6 aspartate) plus combo mutants stacking known repair hits.
52 variants folded, scored, E-scored.

## Result: 11 qualifying (ipTM >= 0.93, i_pDAE >= 0.60, E gain >= 0.3)

Three swaps earned entry on the full composite (WT + peptide-free arms
folded for 8 candidates):

| parent (old) | child | E before -> after | new score |
|---|---|---|---|
| L58K, rank 1 (83.1) | **Q15K** | -1.78 -> **-3.65** | **90.5** |
| peprim-001 (78.1) | **W57K** | -1.22 -> -2.09 | **84.3** |
| A58K (80.1) | **F50K** | -1.77 -> -2.55 | **81.8** |

Rejected despite qualifying: peprim-001's T53K sibling (84.4 vs the W57K's
84.3, a dead heat decided by the validated instrument: the W57K's E is
-2.09 vs -1.64 and its dWT is +0.252 vs +0.011); nim-001 c7's two children
(A64K 82.5 and V59K 80.5, both just under their parent's 82.8 - the A64K
does carry the project's best interface quality, i_pDAE 0.853, and stays in
the records as a future candidate); wave2-024's V15K (79.7 vs 79.1, inside
the anti-churn threshold).

## Notes

- The Q15K's dWT (+0.747) is a project record, with dfree +0.766 and E
  -3.65 all simultaneously - the first design that is strong on every axis.
- The W57K was produced in the round-1 repair but never tri-stated then; the
  loop recovered it as a full entrant, i.e. the loop already pays for itself.
- The gen-1 combo operator was buggy (built from variant templates, so the
  combo yamls repeated a variant's sequence); fixed in evo.py before gen 2
  (parent-yaml templates + duplicate-position exclusion + cap 8).
- Economics: 52 folds + 16 tri-state arms ~ 2.5 h per generation; ~10-15
  generations fit the remaining window.
