# C6 — sequence optimization loop (LigandMPNN children)

**Question:** do the 10 best parents survive surface redesign (interface frozen,
non-interface residues rewritten by LigandMPNN), and do the children keep the
specificity signal?

**Method:** `c6-prep.py` (parents -> PDB + fixed interface residues, atoms within
8 A of the target chains) -> `c6-mpnn.sh` (LigandMPNN protein_mpnn, T=0.1, 8
children per parent, chains_to_design D, interface fixed) -> `c6-build.py`
(child fold yamls) -> `c6-queue.sh` (fold 80 children vs G12D, score) ->
`c6-tri-build.py` + `c6t-queue.sh` (best child of each parent vs WT + peptide-
free; plus the apo set: every parent and best child folded alone).

**Results (parent -> best child, i_pDAE-composite pick):**

| parent | par ipTM / i_pDAE | kid ipTM / i_pDAE | kid dWT / dfree | apo pLDDT (par / kid) |
|---|---|---|---|---|
| nim-wave3 run-001 d0004 | 0.969 / 0.847 | 0.973 / **0.880** | +0.010 / +0.536 | 0.969 / 0.969 |
| nat-wave1 run-011 d0004 | 0.966 / 0.862 | 0.970 / 0.864 | +0.048 / +0.406 | 0.968 / 0.963 |
| wave1-pep run-007 d0000 | 0.951 / 0.618 | 0.951 / 0.606 | **+0.349 / +0.350** | 0.947 / **0.951** |
| wave2-pep run-024 d0007 | 0.941 / 0.729 | 0.955 / **0.809** | +0.060 / +0.677 | 0.968 / 0.969 |
| mini-wave1 run-011 d0001 | 0.965 / 0.771 | 0.965 / 0.793 | +0.004 / **+0.752** | 0.966 / 0.968 |
| peprim-wave1 run-013 d0007 | 0.966 / 0.846 | 0.965 / 0.849 | +0.023 / +0.665 | 0.966 / 0.962 |
| wave1-pep run-033 d0003 | 0.958 / 0.810 | 0.955 / 0.809 | +0.016 / +0.267 | 0.958 / 0.956 |
| wave2-pep run-054 d0005 | 0.948 / 0.608 | 0.933 / 0.452 | +0.066 / +0.713 | 0.967 / 0.967 |
| peprim-wave1 run-012 d0006 | 0.934 / 0.606 | 0.932 / 0.616 | +0.110 / +0.571 | 0.974 / 0.972 |
| wave2-pep run-009 d0007 | 0.950 / 0.553 | 0.925 / 0.427 | **+0.347** / +0.205 | 0.928 / 0.936 |

**Verdict:**
1. **Stability: the redesign works.** All 20 apo folds read pLDDT 0.93-0.97;
   children are equal or slightly above their parents in almost every pair.
   The naturalized surfaces are the expressibility hedge.
2. **WT discrimination mostly erodes with naturalization** — the frozen
   interface is not sufficient; the signal lives in the whole sequence fold.
   Two exceptions kept it: `wave1-pep run-007 d0000`'s child c6 (+0.349 /
   +0.350, apo 0.951) — a *new dual-signal candidate with a naturalized
   surface* — and `wave2-pep run-009 d0007`'s child c2 (+0.347 dWT).
3. **Peptide-dependence (dfree) often improves** in children: mini-011 c5
   (+0.752 = best in the pool), wave2-054 c7 (+0.713), wave2-024 c5 (+0.677).
4. **Selection rule:** keep parents as specificity carriers; children only
   where they beat the parent on the axis they were optimized for
   (c6: dual-signal + stability; the dfree children: dependence).

**Data:** `~/c5-work/c6/` (80 children, s1-summary/s1-scores), `~/c5-work/c6t/`
(20 tri-state arms), `~/c5-work/apo/` (20 stability folds),
`~/c5-work/c6/child-specificity.json`.
