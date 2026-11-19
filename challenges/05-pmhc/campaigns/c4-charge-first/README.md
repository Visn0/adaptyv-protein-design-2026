# C4 — charge first

**Strategy**: the mutation is one extra negative charge. Instead of hoping
a design lands near it, condition the generator on the mutation's
neighbourhood only (P5-P7) so every design must solve the charge problem
locally, and let the C3 electrostatic rule act as the core gate rather
than a filter.

**Tools**: the hosted RFD4 NIM with the new TIGHT hotspot set (P5-P7
ridge, 6 atoms), the C3 electrostatic filter, the standard screens.

**Pipeline**: 160 designs generating now (tight-wave1) -> s0 pose screen
with the C3 rule as the primary criterion -> G12D folds -> tri-state.

**Results** (2026-11-01/02): 25 designs folded, 4 JDI-like, **0 strict passers**, none tri-stated. The 6-atom window produces designs that engage P5-P7 but lack the broader anchor contacts the gate requires — the interface starves. Negative with a clear cause.

**Why it may work**: the main funnel spread contacts over the whole ridge;
a tighter focus should raise the share of designs whose reading of the
peptide is decided by the P6 region.
