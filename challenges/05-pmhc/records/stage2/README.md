# Stage 2 record — tri-state specificity reads (23 designs)

Run: 2026-10-31/11-01, boltz-2 5 models per state; G12D from stage 1,
WT + peptide-free folded fresh. Table: `stage2-table.csv`.

## Amendment (recorded)

The pre-registered free-state veto referenced `iptm_pep(free)`. The free
structure has no peptide chain, so that read cannot exist. The free-state
preference read is the binder-HLA interface confidence (`iptm_hla`) — the
only interface present — compared against the same read in the G12D state.
Scorer fix: the binder is the LAST chain in every fold (4-chain G12D/WT:
index 3; 3-chain free: index 2).

## Verdicts

- **0 vetoes.** No design prefers WT over G12D (worst dWT: -0.002 = noise),
  and none prefers the empty MHC (all free-HLA reads sit below their G12D
  counterparts).
- **6 designs prefer G12D by > 0.1 ipTM** (the C0 noise floor is ~0.05-0.1;
  these deltas are 2-6x larger).
- **The peptide-dependence physics is clean and correlates with the
  preference**: designs that engage the MHC equally with and without the
  peptide (free-HLA ~0.95, delta ~0) hold the HLA helices only. Designs
  whose engagement collapses without the peptide (free-HLA 0.28-0.60,
  delta +0.38..+0.68) are holding the peptide itself.

## Tiers

**Tier 1 — both specificity signals strong (peptide-dependent + G12D-
preferring):**

| design | G12D ipTM | dWT | free-HLA | dfree |
| --- | --- | --- | --- | --- |
| wave2-pep__run-054__design_0005 | 0.948 | +0.308 | 0.285 | +0.682 |
| wave2-pep__run-024__design_0007 | 0.941 | +0.173 | 0.292 | +0.672 |
| wave1-pep__run-007__design_0000 | 0.951 | +0.335 | 0.585 | +0.381 |
| peprim-wave1__run-012__design_0006 | 0.934 | +0.232 | 0.564 | +0.396 |
| wave2-pep__run-009__design_0007 | 0.950 | +0.174 | 0.535 | +0.430 |

**Tier 2 — affinity-strong, specificity flat** (high ipTM, free-HLA ~0.95:
cross-reactive profile, like the JDI control): run-001 d0002, run-008 d0005,
run-026 d0003, run-016 d0003, run-003 d0006, run-040 d0000, run-029 d0004.

**Tier 3 — peptide-dependent, preference flat:** the remaining designs
(free-HLA 0.3-0.77, dWT ~0).

**Flagged:** wave2-pep__run-049__design_0002 reads dWT +0.181 but free-HLA
0.952 (delta +0.027) — it engages the empty MHC as strongly as the loaded
one. Peptide-independent despite the WT preference; recorded, second tier.

## Next

Wave3 folds + scoring land ~01:50 (night queue). Then stage 3: multi-seed
boltz + chai-MSA on the tier-1 set and the best tier-2 designs, plus the
OpenDDE JDI acceptance test. The final 20 comes from that pass.

## Wave3 addendum (2026-11-01 08:07)

The 200-design NIM wave (nim-wave3 + probe-nim) produced 40 s0 passers; 40
G12D folds gave 4 tri-state candidates (band rule: ipTM >= 0.93 and
i_pDAE >= 0.5; the gate passer was already in the band). Tri-state reads:

| design | G12D ipTM | dWT | free-HLA | dfree |
| --- | --- | --- | --- | --- |
| nim-wave3__run-013__design_0003 | 0.960 | +0.026 | 0.295 | +0.682 |
| nim-wave3__run-001__design_0004 | 0.969 | +0.013 | 0.367 | +0.617 |
| nim-wave3__run-021__design_0002 | 0.951 | +0.005 | 0.455 | +0.519 |
| nim-wave3__run-008__design_0004 | 0.942 | +0.010 | 0.720 | +0.254 |

All four are peptide-dependent (dfree +0.25..+0.68) with flat WT preference
(no vetoes). None matches the dual tier-1 profile of the C1 five; run-013
d0003 and run-001 d0004 rank with the strong set on affinity + dependence.
Combined candidate pool: 27 designs with full tri-state reads.
