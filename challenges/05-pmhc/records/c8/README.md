# C8 — multi-state cross-panning (9-mer register + G12V + G12C)

**Question:** can Boltz-2 fold reads separate the G12D epitope from the 9-mer
register (VVGADGVGK) and the G12V/G12C single-point variants — the
Johansen/Liu-style cross-panning filter?

**Method:** top 12 of the clean-20 + the 2 best children x 3 states = 42 folds
(`c8-build.py`, `c8-queue.sh`).

**Results (peptide ipTM, G12D minus state):**

| delta | range | reading |
|---|---|---|
| d9mer | +0.005 .. +0.046 | 9-mer register reads lower in **14/14** — consistent, weak |
| dG12V | +0.000 .. +0.068 | flat — instrument blind to P6 |
| dG12C | -0.002 .. +0.094 | flat |

**Verdict: the cross-panning filter is not usable with this instrument.** The
fold reads cannot resolve single-point peptide differences — exactly what C0
established for G12D vs WT (ipTM delta -0.043, wrong sign); here it is
confirmed for G12V/G12C too. No design shows cross-reactivity above its G12D
read (no red flags), but no discrimination evidence either, so C8 adds no
ranking signal. The consistent 9-mer penalty (+0.005..+0.046, all 14) is a
genuine but weak register preference — noted, not used as a gate.

**Consequence:** specificity ranking stays on the tri-state reads (dWT/dfree)
plus the interaction rules; the P6-variant discrimination can only be settled
in the wet lab, which is what the competition measures.
