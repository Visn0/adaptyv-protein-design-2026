# C3 — the natural reader's pattern

**Strategy**: nature already solved this problem. The molecules that evolved
to read this exact target are T-cell receptors. Measure exactly where the
natural reader touches the peptide (from the real 7OW6 crystal), then
condition the generator on those atoms instead of our own guess.

**Tools**: gemmi crystal analysis (7OW6 full complex), the hosted RFD4 NIM
with the new NATURAL hotspot set, the standard screens.

**Measured pattern** (peptide atoms within 4.5 A of the JDI TCR): P4 CA;
P5 CB, O; P6 C, O; P7 N, CA, C, O; P8 N, CA, C, CB, CG1, CG2; P9 N, CA —
17 atoms, backbone-dominated. P7 backbone is the anchor; P6 is read via
its carbonyl, not the mutant side chain (the mutation acts as a field).

**Pipeline**: 160 designs generating now (nat-wave1) -> s0 pose screen ->
G12D folds -> tri-state for the winners.

**Results** (2026-11-01/02): 32 designs folded, 9 JDI-like, **4 strict gate passers (28%)** — the best yield of the variant campaigns. nat-wave1 run-011 design_0004 (ipTM 0.966, i_pDAE 0.862) and nat-wave1 run-004 design_0001 (0.959 / 0.845) are submission entries 19 and 17.

**Why it may work**: this is the only conditioning set with experimental
provenance — it produced a real, functional reader of this exact target.
