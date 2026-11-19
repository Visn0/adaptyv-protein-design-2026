# Design method — as entered on the submission page

Method name: **Epitope-triaged pH-switch miniprotein ensemble**

## Description (general pipeline / reasoning)

De-novo binders of the human transferrin receptor (TfR1) that engage a
conserved, exposed face of the apical domain and carry a designed pH switch on
the binder side. The submission ranks its designs by switch evidence first,
then by mouse cross-reactivity, then by binding strength.

The epitope decision drives everything. The organizers recommend the patch
around Tyr211, but all six of its named residues are substituted in mouse TfR1
or fall in an indel, so a binder there is selected for human specificity and
works against the challenge's second objective (mouse cross-reactivity). We
measured that patch first, defined three epitope sets (E0 the named tip, E1
north, E2 south), and triaged them on restrained co-folds: E0, E1 and E2 all
closed negative — 0 of 48 engaged their designed site on the re-screen — while
the conserved E12 pair (K344/K374) advanced. The same face carries a second
anchor set (R208/Y211 plus K344/K374), and the surviving families bind either
or both.

The target carries no histidine at this epitope, so the pH switch must live on
the binder. The switch is built from engineered histidines placed to engage
the conserved cations K344 and K374: at neutral pH the histidine is unprotonated
and the interface holds; on acidification the histidine protonates, the
interaction breaks and the binder releases. Switch evidence is measured, not
assumed: every variant is folded under the same restraints and its per-site
pKa is computed with PROPKA, so a variant counts only when the pKa shift is
real and points in the forward direction.

## Configuration (workflow, parameters, settings)

Generators: hosted RFD4-Proteina (NVIDIA GPU pool, medium and high thinking,
8 designs per request, seed 42 onward) produced the backbone pool in two
generator arms — one conditioned on the E12 anchor pair, one on the hybrid
anchor set — in the 60-110 aa band, across six campaigns (epitope triage,
binding families, switch layer, mouse cross-fold, multi-chain units,
selection). ProteinMPNN re-sequenced interface-pinned backbones where a
switch layer or a liability repair required it; Proton-PottsMPNN (explicit
protonation states) ran as a pH-conditioned redesign arm and closed at parity
with its parent.

Folds and reads: Chai-1 co-folds under pocket restraints on the designed
anchors, 5 samples per design, seed 42 — the primary instrument. A restrained
read counts only when the worst-anchor minimum distance is at most 8 A and at
least one binder residue sits at the designed site (off-site poses can read
~0.70 without this gate; the gate is mandatory since 2026-10-27). Second
reads per design: unrestrained Chai co-fold (pose shift), mouse cross-fold
against mouse TfR1 under the identical protocol, Boltz-2 restrained folds with
ipSAE and pDockQ2 (Chai writes no PAE), PRODIGY, DockQ on the champion
(0.897, iRMSD 0.55 A), PROPKA for the switch direction, US-align against
known TfR1-binding structures (0 hits above TM 0.5 over 70 % coverage), and a
sequence-liability pass (N-glycosylation sequons, deamidation motifs,
methionine load, free cysteines) with repair variants folded wherever a flag
appeared.

Ranking: row order is the ranking, by the composite
`total = 2.0*S + 1.5*X + 1.5*B + 1.0*E` (max 30, normalised to 100), where S
is switch evidence (measured pKa shift in the forward direction, 0-5), X is
mouse cross-reactivity (0-5 bands), B is binding (engagement-gated restrained
ipTM bands, 0-5) and E is expression risk (mean of a pLDDT band and a
hydropathy band). Hard floors before ranking: pLDDT, sequence complexity and
the engagement gate itself. No two designs exceed 0.90 sequence identity, and
near-duplicates are removed during selection; the twenty sit on twenty distinct
backbones across seven families. Ties break on switch evidence first, then
binding, then family representation. The final run scored 293 designs; 129
failed the floors; 20 were selected.
