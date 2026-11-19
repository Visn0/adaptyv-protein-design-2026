# Design method — as entered on the submission page

Method name: **Activation-geometry-gated de-novo binder ensemble**

## Description (general pipeline / reasoning)

De-novo binders of human GLP1R, selected to engage the receptor the way GLP-1
does. The submission ranks its designs by activation evidence first, then by
binding strength. The activation evidence comes from our activation-geometry
gate: six pharmacophore contacts of the GLP-1 message region — an anion to
R190, an aromatic at Y148, a small group at W306, an H-bond to Q234, a
hydrophobe at E387, and ECL3 contact — plus the insertion depth of the ligand
below the vestibule rim. We calibrated the gate on four experimental structures
before trusting it: 6X18 GLP-1 scores 6/6 at 20.6 A; exendin-P5 (6B3J) 4/6 at
23.6 A, missing R190, which is the known biased agonist; exendin-4 (7LLL) 4/6
at 18.9 A; the weak metabolite GLP-1(9-36) (9IVG) 1/6 at 14.2 A. A second lens scores each design by how much of the
hormone's whole 19-contact footprint it reproduces; it disqualified apparent
pattern leaders whose reach came from wrapping around the receptor (depths of 57
to 74 A) rather than inserting. Designs with the full 6/6 pattern at depth lead
the file; everything is also screened for classic binding (ipSAE, pDockQ2) and
expression risk (pLDDT, hydropathy). 

## Configuration (workflow, parameters, settings)

Generators (all targeting the 6X18 active-state geometry of the challenge
construct 24-432; junction-only hotspots dominated): RFdiffusion3 mini-proteins
(60-110 aa), EvoBind peptides from sequence alone (15-aa class), BoltzGen
peptides against the ECD-TMD junction (12-24 aa), BindCraft2 peptides (15-18
aa, relaxed gates so raw output survives our independent screen), and
RFD4-Proteina (NVIDIA hosted GPU pool, medium and high thinking, 8 designs per
request, seed 42 and onward) in three rounds: 60-100 aa conditioned on the
TM-pocket and ECL3 message region (256 designs), the same length band
conditioned on the ECD-TMD junction block K197/Q210/Q221/Q234 (73), and a
shorter 40-70 aa band against the deep region (72). Interface-pinned SolubleMPNN
re-sequencing of full-geometry backbones (interface residues within 4 A pinned,
periphery redesigned at temperature 0.3, top three variants per backbone
folded), in three passes of 40, 33 and 81 variants.

Folds: Boltz-2 2.2.1, 5 diffusion samples per design, seed 42, binder as chain
A, the full 409-residue construct as chain B, receptor MSA depth-capped at 1024
rows. Screens per design: ipSAE and pDockQ2 (interface), pLDDT (fold), mean
Kyte-Doolittle hydropathy (sequence), the activation-geometry gate, and the
agonist-pattern likeness score. The gate reports two separate figures — the
contact count from the best of the five samples, and the number of samples that
insert within the declared 30 A threshold, written as `6/6 d19.2 5/5`.

Ranking: row order is the ranking, by the composite
`total = 2·A + 1.5·B + 1·E + 0.5·R` where A is activation evidence (6/6 with
strong insertion agreement = 5, 5/6 = 3.5, wrapping pose beyond 30 A costs 1),
B is binding (ipSAE bands, +0.5 for pDockQ2 >= 0.30), E is expression risk (mean
of a pLDDT band and a hydropathy band) and R is reach (groove, TM-pocket and
ECL3 contact fractions). Ties break on insertion agreement, then depth. The selector applies a hard
quality gate before ranking: minimum 63 pLDDT, minimum 0.18 pDockQ2, and no
low-complexity sequence (entropy below 2.5 bits, one residue above 45 % of the
chain, or a homopolymer run of 6 or more). It removes 486 of the 800 scored
designs. No two designs exceed 90 %
sequence identity; near-duplicates are removed during selection. Seventeen of
the twenty carry the full 6/6 activation pattern and three carry 5/6: the
composite weights binding and expression alongside activation, so a 5/6 design
that binds hard and is likely to express outranks a 6/6 design that does
neither. ipSAE across the file runs 0.840 to 0.933 and the normalized score 87.8
to 95.4.
