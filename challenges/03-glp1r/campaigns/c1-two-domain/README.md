# Campaign 1 — two-domain mini-binders (strategy S1)

## The bet

GLP-1 activates GLP1R with a two-domain grip: its C-terminal helix sits in the
ECD peptide-binding groove, its N-terminus threads toward the transmembrane
pocket. The published designed GLP1R binders (miniproteins, antibodies) all
bind the groove only — and all are antagonists. Campaign 1 bet that a de-novo
binder whose contact map reproduces the GLP-1 path (groove → junction →
TM-top → ECL3) has the best available shot at agonism.

## What ran

| experiment | setup | backbones | two-domain pre-fold |
|---|---|---|---|
| E1 | RFdiffusion3, groove + junction hotspots | 43 | 6 |
| E1b | RFdiffusion3, junction-only hotspots | 60 | 10 |
| E1b2 | E1b repeated (the productive setup) | 80 | 20 |
| E3 | fixed-interface MPNN refinement of the leaders | 32×5 variants | (10 folded) |

Every at-site design was co-folded against the full 24–432 construct
(Boltz-2, 5 samples, depth-capped cached MSA) and screened for ipSAE ≥ 0.8,
groove + TM-pocket contacts, zero clashes, and the ECL3/TM6–7 reach.

## Result

- **39 of 335 samples** are two-domain hits across **21 distinct designs**.
- Leaders: `e1b2-r0036` (4 TM + 8 ECL3 contacts, no liabilities), `e1-r0025`
  (ipSAE 0.933, the full path including E387), `e1b-r0023` (0.925),
  `e1b-r0059` (0.901, pDockQ2 0.514), `e1-r0033` (0.873). Poses
  render-verified (`viewers/`): elongated helices threading the receptor's
  cleft along the GLP-1 path, on an active-state receptor.
- **Decision: keep the strategy.** Binding and two-domain reach are
  demonstrated in-silico; activation is the assay's call.

## Output

- `submission/` — the 20-design competition file (top 20 of 21 families by
  `tm*3 + ecl3*1.5 + ipSAE`, one per family, prescreen-passed), the candidate
  table, the methodology, the prescreen report.
- `scripts/` — the full pipeline (target prep, RFD3 chains, triage, fold-YAML
  builders, the two-domain screen, candidate ranking, submission builder).
- `viewers/` — Mol* renders + explorers for the four leaders.
