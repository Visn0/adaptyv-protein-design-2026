# The agonist-likeness finding (2026-10-22)

**What was measured.** Every folded design (644, all campaigns) was scored by how much of
the natural hormone's own contact pattern it reproduces — GLP-1 in 6X18 touches all six
groove residues, all four junction residues, all four TM-pocket residues and five of eight
ECL3 residues (19 in total). The metric is deliberately harsh; no design in the pool is
agonist-like in absolute terms, and the pool ceiling is 6 of 19.

**The finding.** The likeness ranking disagrees with the affinity ranking, and the
disagreement is informative:

- Our highest-ranked designs (the full-geometry RFD4 champions) reproduce 3 to 5 of 19
  contacts. The activation-geometry gate and the pattern metric measure different things:
  the gate checks the six message-region pharmacophore contacts at depth; the pattern
  metric checks how much of the hormone's whole footprint is reproduced.
- Four designs outside the top-20 hit the pool ceiling (6 of 19) — and the depth check
  disqualified three of them immediately. Their apparent TM-pocket reach came from
  **wrapping poses** (insertion depths 57-74 A, the flagged wrapping class), not from
  pocket insertion. Their "pattern" was an artifact of contact-counting a binder that
  lies across the receptor.
- Exactly one design survived both lenses: `c12-mpnn-b13-d01-v3` — full 6/6 geometry at a
  trusted depth of 23.9 A with 5/5 pose agreement, likeness at the pool ceiling, ipSAE
  0.855. It replaced the lowest-likeness slot in the submission twenty.

**Why this matters for method choice.** A screen can only discard; it cannot supply a
feature the generator never produced. The likeness dead-end says the pool already
contains what groove/junction conditioning can reach — the remaining upside is in aiming
generation at the pattern itself (the reward-guided lever), not in filtering the existing
pool harder.

**Caveats.** The metric is a structural proxy against one reference agonist pose; it is
not a trained predictor; the wet-lab cAMP assay decides. The wrap-pose disqualification
uses our declared 30 A depth threshold.
