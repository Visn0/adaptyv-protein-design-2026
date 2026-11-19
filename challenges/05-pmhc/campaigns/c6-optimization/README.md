# C6 — the optimization loop (children)

**Strategy**: after every campaign reports, take the best designs across
all of them and generate CHILDREN: sequence variants that keep the binding
interface but change the rest of the surface (stability, expression,
charge balance). Re-fold the children, keep the ones that improve.

**Tools**: ProteinMPNN (installed at ~/.venvs/mpnn) for sequence design on
the fixed complex, boltz for re-folding, the standard scorer, plus an
apo-fold check (fold each binder ALONE — a well-folded apo chain is the
cheapest available stability signal).

**Pipeline**:
1. Parents: the top designs across C1-C5 (per-campaign leaders + the
   dual-signal designs).
2. Children: MPNN sequence design with the interface held fixed ->
   4-8 children per parent.
3. Test: fold each child against G12D (and WT/free for the best) + the
   apo-fold stability check.
4. Keep children that beat their parent on the composite (confidence,
   specificity reads, stability) -> final selection.

**Results** (2026-11-02): 80 children folded against G12D; 6/10 parents got children equal-or-better (best gain +0.08 i_pDAE). All 20 apo folds read pLDDT 0.93-0.97 (children consistently at or above their parents) — the stability goal is met. But WT discrimination collapsed in 8/10 children: a frozen interface is not enough. Two children kept the dual signal (wave1-pep run-007 design_0000 c6 and wave2-pep run-009 design_0007 c2 — submission entries 3 and 4); several improved the dependence axis (dfree up to +0.752). Selection rule: parents stay the specificity carriers; children are the stability/expressibility hedge.

**Why it may work**: the parents were designed by one pass of one
generator. Sequence-level polish around a proven interface is the
cheapest source of real improvement left in the budget.
