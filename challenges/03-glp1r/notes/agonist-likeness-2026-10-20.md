# Agonist-likeness: how close each design is to the real GLP-1 contact pattern

Method: the activating peptide itself is the reference. From 6X18 (GLP-1,
chain P, on the receptor chain R) the script collects the receptor residues
the real agonist touches at each of the four sub-sites, then measures how many
of those same residues each design's fold sample touches (4.5 A heavy-atom
contact). Score = fraction of the 19-residue reference pattern reproduced.

The reference (GLP-1) touches **all** of:

| sub-site | residues touched by GLP-1 |
|---|---|
| groove | 67, 69, 88, 91, 121, 128 (6/6) |
| junction | 197, 210, 221, 234 (4/4) |
| TM pocket | 298, 300, 309, 313 (4/4) |
| ECL3 | 380, 384, 387, 388, 391 (5/8) |

That is a full agonist: the peptide sits in the groove AND threads the
junction AND fills the TM pocket AND reaches ECL3.

## Results (146 designs scored, ~/c3-work/agonist-likeness.csv)

| design | likeness | groove | junction | tm | ecl3 |
|---|---|---|---|---|---|
| e1-r0005 | 0.32 | 2/6 | 1/4 | 3/4 | 0/5 |
| e1-r0016 | 0.32 | 2/6 | 1/4 | 1/4 | 2/5 |
| e3-e1b-r0023-v2 | 0.32 | 1/6 | 1/4 | 2/4 | 2/5 |
| e1-r0034 | 0.26 | 3/6 | 1/4 | 0/4 | 1/5 |
| e1b-r0021 | 0.26 | 2/6 | 1/4 | 1/4 | 1/5 |

## What this says (and does not say)

- **No design is agonist-like in absolute terms.** The best reproduce about a
  third of the reference pattern; a full agonist touches all 19 residues. The
  metric is harsh on purpose: it measures the activation pattern, not binding.
- **The ranking differs from the composite score.** The likeness leaders are
  campaign-1 mini-proteins (e1-r0005, e1-r0016) that sit mid-table on ipSAE.
  The composite's favourites (the c3/c5 peptides) have sparser patterns.
- **Implication for the submission**: if the agonism objective is weighted as
  the challenge says, a likeness leader deserves a slot next to the
  affinity leaders. This is a selection input, not a verdict — the wet-lab
  cAMP assay decides.
- Not a trained predictor: it is a structural proxy against one reference
  agonist (6X18); a different agonist pose would shift the numbers.
