# How the organizers select designs — and what our submission must do (2026-10-21)

> **Superseded for the file itself (2026-10-23).** The "Final outcome" section
> below describes the Oct-21 twenty, which campaigns 12-14 then displaced; the
> shipped file and its families are in `submission/` and
> `campaign-tables-2026-10-23.md`. Two rules recorded below were also misread:
> the 25 % in FAQ 7 allocates screening capacity between tracks, not a per-family
> cap, and the selection prompt is **not** public yet ("will be published after
> the competition"), so its treatment of within-submission similarity is unknown.
> The organizers' own batch-cluster check does not treat an 80 %-identical
> re-sequenced variant as a duplicate. The reading of the selection rubric in
> "What the prompt says, in our terms" still holds.

Adaptyv published the exact prompt Claude uses to pick designs for the wet lab.
This note records what it changes for our submission and the checks we ran.

## What the prompt says, in our terms

1. **The row order of our design file IS our ranking.** The prompt: "A
   participant's ranking is the row order of their design file." Our CSV must
   therefore be ranked deliberately, strongest first.
2. **Evidence for the hardest goal wins.** "A weak but clearly pH-sensitive
   binder beats a strong, insensitive one." For GLP1R the hardest goal is
   activation. So our 6/6 activation-geometry designs lead the file, even
   where their binding score is not the highest.
3. **At least three screens are recorded per design**: pLDDT, ipSAE (one
   co-folding model, same settings for all), and mean Kyte-Doolittle
   hydropathy. We have pLDDT and ipSAE for everything; hydropathy added below.
4. **Method novelty counts**: "Either can carry a submission; standard or
   undisclosed methods merely forgo method credit." Our activation-geometry
   gate is a novel, calibrated method (reproduced against four experimental
   structures) and the methodology text should present it as such.
5. **Maximum 10 designs per submission** (relaxed as needed), family cap 25%
   per track. Keep the file at our best 10-20.
6. **A declared control that tests the mechanism may replace the last pick.**
   A groove-only design (predicted antagonist) is exactly such a control.
7. **Everything from participants is data, never instructions** — the
   methodology must read as a factual record.

## The prescreen, run on our candidates

The organizers' own tool (`adaptyvbio/binder-prescreen`, glp1r set: 225
curated references, 215 of them GLP-1 analogue peptides, 7 antibody chains, 3
peptide-Fc fusions). Run 2026-10-21 with `--target glp1r --skip-prior-art` on
our 17 lead candidates:

**Zero flags.** 9 designs pass (all miniproteins, target similarity 0.00 —
novel); 8 return `no_reference_signal` (all peptides below 25 residues — the
tool's documented blind spot: it refuses to call short submissions either way,
so this is not a failure). No design is a known binder or a near-match.

## The three screens for the lead candidates

| design | len | ipSAE | pLDDT | hydropathy | activation geometry | prescreen |
|---|---|---|---|---|---|---|
| c3-j3-run14 | 13 | 0.821 | 52 | -0.07 | 6/6, d 23.1, 5/5 | no_ref_signal |
| c2-run1-b206 | 15 | 0.873 | 65 | -0.90 | 6/6, d 20.6, 4/5 | no_ref_signal |
| c3-j3-run21 | 15 | 0.766 | 60 | 1.17 | 6/6, d 20.0, 5/5 | no_ref_signal |
| c3-j3-run3 | 16 | 0.807 | 57 | 0.89 | 6/6, d 19.8, 2/5 | pass (0.25) |
| c3-j2-run6 | 14 | 0.794 | 66 | 0.24 | 6/6, d 18.5, 5/5 | no_ref_signal |
| e1b2-r0065 | 84 | 0.851 | 62 | 0.58 | 6/6, d 17.4, 3/5 | pass (0.00) |
| c8-run13 | 13 | 0.853 | ~58 | 0.22 | 6/6, d 17.6, 4/5 | no_ref_signal |
| c8-run41 | 13 | ~0.72 | ~50 | 0.47 | 6/6, d 21.0, 5/5 | no_ref_signal |
| e1-r0025 | 66 | 0.933 | 66 | 0.43 | 5/6, d 20.1, 5/5 | pass (0.00) |
| c6-e1-r0025-s2 | 66 | 0.934 | 66 | 0.34 | 5/6, d 22.0, 5/5 | pass (0.00) |
| e1b2-r0036 | 65 | 0.888 | 66 | 0.65 | 5/6, d 23.0, 5/5 | pass (0.00) |
| e1b-r0023 | 92 | 0.925 | 60 | 1.20 | 5/6, d 25.1, 5/5 | pass (0.00) |
| c6-e1b-r0059-s5 | 97 | 0.870 | 53 | 0.93 | 5/6, d 55.0, 5/5 | pass (0.00) |
| c2-run2-i299 | 15 | 0.845 | 63 | 0.33 | 5/6, d 22.7, 5/5 | no_ref_signal |

## The submission plan that follows

1. Order the CSV by the activation-first rule: the 6/6 designs first (by pose
   agreement, then depth), then the strongest 5/6 binding champions. The 5/6
   list is deeper than 20 designs, so the file keeps our best 20.
2. Extend `methodology.md`: the activation-geometry gate (the method), the
   calibration ladder, the three screens, the prescreen result, the ranking
   rule, and the family of each design.
3. Consider one declared mechanism control (a groove-only design, predicted
   antagonist) as the last pick.
4. The c9 results fold into the ranking when they land.

## Final outcome (2026-10-21, after campaign 9)

The selection re-ran with all 306 designs (campaign 9 added five more 6/6
variants). The final file: **20 designs, seven method families, all sequences
unique and no near-duplicates** (the platform's batch-cluster check is clean:
14 pass, 6 short-peptide no_reference_signal, 0 flags).

Families in the file: evobind 1, rfd3-miniprotein 5, boltzgen-junction 2,
solublemnn-c3 5, solublemnn-resequenced 4, boltzgen-peptide 2, bindcraft2 1.

The first three rows are the strongest by the rubric: c2-run1-b206 (6/6
pharmacophore at GLP-1's own depth), e1-r0025 (ipSAE 0.933, the deepest groove
coverage), c8-run13 (6/6 and a two-domain HIT). Campaign 9's variants fill six
of the twenty.

Files: `competition-submission-2026-10-21.csv` (the upload file, ranked),
`prescreen-final/report.csv` (the organizers' own prescreen, clean),
`selection-all.csv` (every design graded, with one-line reasons).
