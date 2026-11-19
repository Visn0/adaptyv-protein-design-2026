# Method — Challenge 3 (GLP1R agonist)

The designs are de-novo binders of the human GLP-1 receptor. They were selected
to engage the receptor the way GLP-1 does: at the peptide-binding groove of the
extracellular domain, along the path from that groove toward the transmembrane
bundle, and — for the designs ranked first — with the full pharmacophore of the
GLP-1 message region at the depth the experimental agonists reach.

The file is ranked. Row order is the ranking: activation evidence first (the
six-contact pharmacophore at depth, with pose agreement), then binding strength.

## 1. Target

Human GLP1R (UniProt P43220-1), the challenge segment 24-432, as supplied in
detergent. The reference pose is the active-state complex 6X18 (chain R).

## 2. Backbone generation

Several independent generators were used, each a method family of its own:
RFdiffusion3 mini-proteins (hotspots on the groove and the ECD–TMD junction —
junction-only runs repeated), EvoBind cyclic peptides from sequence alone
(15-residue class), BoltzGen cyclic peptides designed against the junction, and
BindCraft2 peptides with forced targeting. A final family re-sequenced the
strongest backbones with SolubleMPNN, interface pinned.

## 3. Activation-geometry gate (the method)

A published activation scorer (`activation_geometry.py`, charleneleong-ai/
ai4science PR #98) measures the GLP-1 message-region pharmacophore explicitly:
six contacts — an anion to R190, an aromatic at Y148, a small group at W306, an
H-bond to Q234, a hydrophobe at E387, and ECL3 contact — plus the insertion
depth of the ligand below the vestibule rim (residues 205-221, 298-380),
projected on the rim-to-floor axis.

Cutoffs are fixed in the tool, not fitted. We reproduced the tool's calibration
on four experimental structures before trusting it: 6X18 GLP-1 6/6 at 20.6 A;
6B3J exendin-P5 4/6 at 23.6 A (it misses R190 — the known G-protein-biased
agonist); 7LLL exendin-4 4/6 at 18.9 A (misses Q234); 9IVG GLP-1(9-36) weak
partial agonist 1/6 at 14.2 A. The tiers: deep = depth >= 16 A with >= 3
features; shelf = depth >= 10 A.

Every design was scored in all five fold samples. Pose agreement across samples
is reported because the gate scores the pose it is given.

## 4. Validation

Every backbone was re-folded with the full receptor construct (Boltz-2, five
samples, receptor MSA depth-capped). Each sample was scored with ipSAE and
pDockQ2, checked for clashes, and screened for the contact pattern: groove AND
the transmembrane-side path. The three screens recorded for the selectors:
pLDDT (fold), ipSAE (interface), and mean Kyte-Doolittle hydropathy (from the
sequence). Designs docking only the groove, or clashing into the omitted
detergent-facing surface, were discarded.

## 5. Selection

Ranked by activation evidence first (6/6 pharmacophore with unanimous pose
agreement, then depth), then binding strength. Exact sequences are in the
submission CSV. Sequence-level prior art was screened with the organizers'
public prescreen tool against the curated GLP-1R reference set: no design
matches a known binder; peptides below 25 residues return the tool's
`no_reference_signal` (its documented short-sequence blind spot).

## 6. Honest limits

Activation cannot be predicted from a co-fold. The gate scores the pose it is
given, not whether a design adopts it; pose agreement across samples is the
mitigation, not a proof. Depths above ~30 A indicate a wrapping pose rather
than pocket insertion and are flagged, not trusted. Binding affinities are for
the assay to determine.
