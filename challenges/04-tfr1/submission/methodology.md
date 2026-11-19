# Methodology — challenge 04 (TfR1 conditional binder)

## The target and the epitope decision

The assay construct is the human TfR1 ectodomain homodimer (UniProt P02786,
residues 121-760), 639 residues per chain. The organizers recommend the apical
domain around Tyr211. We measured that patch first: all six of its named
residues are substituted in mouse TfR1 or fall in an indel, so a binder there
is selected for human specificity and works against objective 2 (mouse
cross-reactivity). A conserved, exposed face sits in the same neighbourhood.
Three epitope sets were defined and triaged: E0 (the named tip), E1 (north),
E2 (south), plus the E12 pair (K344/K374) that survived triage.

The target carries no histidine at this epitope, so the pH switch must be
built on the binder. The conserved cations K344 and K374 are the switch
anchors; the engineered histidines are placed to engage them.

## The read: a restrained co-fold with an engagement gate

The primary instrument is a Chai-1 co-fold under pocket restraints on the
designed anchors (5 samples per design). A read counts only when the worst
anchor distance is at most 8 A and at least one binder residue sits at the
designed site — off-site poses can read ~0.70 without this gate.

Second reads, all recorded per design: mouse cross-fold (the same protocol
against the mouse receptor, with its own superposition frame), Boltz-2
restrained folds with ipSAE and pDockQ2 (Chai writes no PAE, so the
cross-validation needs a second folder), PRODIGY, DockQ on the champion
(0.897, iRMSD 0.55 A), and PROPKA for the switch direction.

## The campaigns

1. **Epitope triage (C1)** — 217 designs over four patches; the E12 pair
   advanced, E0/E1/E2 closed negative (E1/E2: 0 of 48 engaged their designed
   site on the re-screen).
2. **Binding families (C2)** — batch generation with two generator arms
   (Genie 3 and hosted RFD4-Proteina); 20 of 81 cleared the restrained line;
   a third wave added the hybrid anchor set (R208/Y211 + K344/K374).
3. **Switch layer (C3)** — 29 histidine variants retrofitted onto the top 10
   families (singles, doubles, a 0-to-3 ladder); 21 kept their binding, 13
   carried forward; a pH-conditioned redesign arm (Proton-PottsMPNN, explicit
   protonation states) closed at parity with its parent.
4. **Mouse cross-fold (C4)** — every carry-forward design folded against
   mouse TfR1 under the identical protocol; the champion's mouse read is
   0.688 against 0.782 human.
5. **Multi-chain units (C5)** — rescued on the block target (74 of 110 samples
engage both binders; recorded as capability, not a submission class): the assembled
   three-chain fold is unrunnable on this host (VRAM cliff, host crash). The
   per-chain proxy read is recorded as confounded by construction, not as a
   negative result.
6. **Selection (C6)** — one script owns the ranking
   (`campaigns/c6-selection/scripts/select-top20.py`): rubric S (switch
   evidence) x2.0 + X (mouse) x1.5 + B (binding, engagement-gated) x1.5 +
   E (expression: pLDDT + hydropathy) x1.0, floors on pLDDT, complexity and
   engagement. Final run: 293 designs scored, 129 fail the floors, 20
   selected.

## Selection principles

- **Diversity per backbone, enforced at 0.90.** The 20 sit on 20 distinct
  backbones, and at most one design per 0.90-identity cluster enters the
  file (stricter than the prescreen's 0.95 within-batch rule); near-neighbours
  form the ranked reserve. Twenty sequences threaded onto two backbones carry
  two structural identities; a single fold resembling something known removes
  every design built on it. Ties in the composite break on switch evidence
  first, then binding, then family representation.
- **Prescreen first.** All 20 pass the organizers' binder-prescreen (v0.5,
  tfr1 arm, 6,695 references) with no prior-art or known-binder flags; the
  swapped final list was re-screened on 2026-10-30 (20/20 again).
- **The dimer context is checked, not assumed.** Every folded binder was
  placed in the 11QC dimer frame: the minimum binder-atom distance to the
  second protomer is 20.3 A and to the N251 glycan 5.1 A, so the
  single-protomer screen is safe at this epitope (the apexes sit 93 A apart).