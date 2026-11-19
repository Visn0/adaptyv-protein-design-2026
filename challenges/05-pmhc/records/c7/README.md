# C7 — data-mined rules as a tri-state predictor

**Question:** do the 5 design rules mined from the 40 tri-stated designs
(`notes/research-2026-11-01/data-mining-design-rules.md`) predict WT
discrimination in designs never tri-stated?

**Method:** rule-score >= 4/5, G12D ipTM >= 0.85, not yet tri-stated -> 8
candidates -> fold vs WT + peptide-free (`c7-queue.sh`), 16 arms.

**Results (8 candidates):**

| design | g12d ipTM | wt ipTM | dWT | dfree | verdict |
|---|---|---|---|---|---|
| nim-wave3 run-021 d0001 | 0.922 | 0.465 | **+0.457** | +0.603 | **DUAL (new pool best dWT)** |
| wave2-pep run-024 d0001 | 0.891 | 0.704 | +0.187 | +0.547 | **DUAL** |
| nim-wave3 run-010 d0002 | 0.889 | 0.737 | +0.152 | **+0.749** | **DUAL** |
| wave1-pep run-019 d0004 | 0.904 | 0.767 | +0.137 | +0.442 | dfree only |
| wave1-pep run-054 d0005 | 0.895 | 0.809 | +0.086 | +0.398 | dfree only |
| wave1-pep run-028 d0003 | 0.924 | 0.859 | +0.065 | +0.340 | dfree only |
| wave2-pep run-037 d0003 | 0.857 | 0.765 | +0.092 | +0.663 | dfree only |
| wave1-pep run-001 d0006 | 0.905 | 0.850 | +0.055 | +0.196 | flat |

**Verdict:** 3/8 dual-signal (38%) vs the pre-existing pool baseline (6/40 =
15%) — the rules lift the dual-signal rate ~2.5x. All 8 are at least
peptide-dependent (no vetoes). Caveat: rules were mined in-sample on n=7;
this is their first out-of-sample test and they passed.

**Pool after c7 (see `records/c7/tri-state-all.csv`):** 58 tri-stated designs,
11 dual-signal. New top discriminators: nim-wave3 run-021 d0001 (+0.457),
wave1-pep run-033 d0003 (+0.359), wave1-pep run-007 d0000 (+0.335) and its
child c6 (+0.349).
