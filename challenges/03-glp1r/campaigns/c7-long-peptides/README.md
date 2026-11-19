# Campaign 7: extended-length BoltzGen peptides (20-24 aa)

## Why

Campaign 3 settled the 12-18 aa range at the junction (four two-domain HITs),
and campaign 5 added the challenge's best design in the 15-18 aa band. The
20-24 aa range is the one untried length class for this generator. Longer
peptides can span more of the activation path (the agonist-likeness reference
touches groove + junction + TM + ECL3), at the risk that the extra length
dangles without contacts.

## Configuration

- **Target**: the junction-only configuration, unchanged from campaign 3's
  best (`binding_types` R 163,176,187,200 in fragment numbering).
- **Designed entity**: one cyclic peptide, length range **20..24** (the only
  variable versus campaign 3's 12-18).
- **Validation**: the standard pipeline - Boltz-2 co-fold against the full
  409-residue receptor, the contact screen, and the agonist-likeness score.

## Result: viable, not superior

30 designs sampled (~5 min each), all folded against the full receptor and
screened. **5 two-domain HITs** - the same success rate as the 12-18 aa
campaign, so the extended range is a viable class:

| design | ipSAE | groove | tm | ecl3 |
|---|---|---|---|---|
| c7-run9 | 0.834 | 5/6 | 1/4 | 2/5 |
| c7-run24 | 0.832 | 2/6 | 1/4 | 5/5 |
| c7-run22 | 0.819 | 5/6 | 2/4 | 5/5 |
| c7-run1 | 0.819 | 6/6 | 2/4 | 5/5 |
| c7-run11 | 0.812 | 6/6 | 2/4 | 7/8 |

**Verdict on the length question**: longer peptides cover MORE of the groove
(two designs touch all six groove residues) but do not beat the 15-18 aa band
on affinity (best 0.834 versus campaign 6's 0.934). The 15-18 aa range stands
as the recommended length; 20-24 aa is a viable backup class.
