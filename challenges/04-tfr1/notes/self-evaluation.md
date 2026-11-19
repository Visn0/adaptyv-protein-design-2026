# Self-evaluation — our submission read against the organizers' prompt

Run 2026-10-30, before upload. Method: the challenge-4 instance of the
organizers' published selection prompt (captured from the competition hub;
the repo copy was removed with the `docs/` folder on 2026-11-08)
read against our own submission as if we were the graders. This is our own
run of their rules, not their verdict.

## Hard rules

| rule | our state |
|---|---|
| Class: protein scaffold, 10-250 aa per chain | miniproteins, **60-108 aa per chain** (11 of 20 above 79 aa), single chain, no tags or linkers. Declared `molecule_class: single_chain` - the template's own vocabulary and the widest-agreeing value in the prescreen's declared-class map; the prescreen confirms `declared_class_match: agree` on all 20 |
| Diversity: no duplicates; first 20 in order | exactly 20 rows in composite order; **at most one design per 0.90-identity cluster** (stricter than the prescreen's 0.95 rule; near-neighbours held for the reserve); 20 distinct backbones. The one 0.947 pair the first pass carried (the champion and its Proton-PottsMPNN interface redesign) was moved to the reserve after review |
| Novelty level >= 3 enforced | our proxy: **all 20 pass binder-prescreen v0.5 (tfr1 arm, 6,695 references)** with no prior-art or known-binder flags; sequence similarity to the closest reference <= 0.28. Structural arm (US-align vs the known binder structures we hold, coverage-aware): **0 of 20 hit TM > 0.5 across > 70% of the design** (max TM 0.49) - `records/structural-novelty-2026-10-29.csv`. The platform's own level is theirs to compute |
| De novo, zero-shot | RFdiffusion3 (hosted RFD4-Proteina) and Genie 3 backbones generated from scratch on the target structure; no existing binder was used as a starting point at any stage |
| Row order is the ranking | yes - the CSV is written in composite-score order |

## The three screens per design (required)

1. **pLDDT** - binder chain, from the co-fold (recorded per design in
   `records/selection-scores-2026-10-30.csv`).
2. **ipSAE with the target** - Boltz-2 restrained folds, 5 models, mean
   (`records/ipsae-pool-2026-10-28.csv` plus the fill passes; the final
   entrants' folds completed the screen on 2026-10-29; the two
   2026-10-30 liability repairs carry theirs in the 10-30 selection record).
3. **Mean Kyte-Doolittle hydropathy** - recorded per design (the E component
   of the rubric).

No single metric decides: the design with the top chai ipTM (0.802) is not the
selection's top pick, and the most cross-validated design (b3_E12_r90003:
chai 0.776, Boltz ipTM 0.808, ipSAE 0.50, pDockQ2 0.43) sits at rank 13
because its switch evidence is thin (S1). The rubric weighs the switch
hardest, per the prompt's own ordering.

## What the prompt says to select for, against our file

- **A real chance to express and bind.** pLDDT 78-90 across the 20; hydropathy
  in the +0.05 to +0.30 band; all folds engaged their designed site under the
  engagement gate (worst-anchor <= 8 A, binder residues at site > 0). The
  stronger test - **unrestrained re-folds** (no pocket constraints, 5 samples
  each, run 2026-10-28/29): **11 of 20 designs find the designed site on
  their own**, 5 of them in every sample: `c3_b4_H_r1d0000_53h` 0.771, the
  champion `c3_e12rfd4_r4d5_d2` at 0.725, `e12_9` 0.688,
  `c3_e12rfd4_r5d1_d2` 0.681, `c3_e12_18_21h` 0.667. The
  other 9 read high only under restraints and are restraint-dependent -
  recorded, not hidden (`records/unrestrained-engagement-2026-10-29.csv`).
- **The hardest goal first - the pH switch.** 5 of the 20 carry the S5 switch
  class (two engineered sites, direction verified); the rest carry S1-S4. The
  selector now enforces the direction gate its own docstring always
  described: a linkage moving the wrong way caps S, which moved two
  high-fold-ipTM designs (r6d2_s1, b2_26_s1) out of the S5 class on
  2026-10-29. The
  mechanism is the asked direction (release on acidification). The per-site
  measurement (PROPKA bound vs free, `campaigns/c3-switch-layer/pka-per-site.txt`)
  now covers the file's S5 set - `r4d5_d2`, `r5d1_d2`, `53h`, `r5d7_d2`,
  `b2_20_s2_n10q`: **four of the five carry at least one site outside
  PROPKA's ~0.8-unit error** - the champion's site 28 reads **-2.82**, `53h`
  -2.14, `b2_20_s2_n10q` -2.16 (inherited from its parent's measured site;
  the engineered histidine is unchanged), `r5d1_d2` -1.35 - while `r5d7_d2`
  (-0.76) reads within noise and rests on site count and direction alone.
  The two demoted designs (`r6d2_s1` -1.47, `b2_26_s1` -0.48) scored
  S = 2 on the direction gate and are absent from the file. The champion's rank-1 switch is
  measurement-backed, not only class-awarded. The selection still never ranks
  on quotable magnitudes, per the prompt's "weak but clearly pH-sensitive"
  language.
- **Mouse cross-reactivity.** The champion reads 0.688 against 0.782 human.
  Coverage, stated plainly: **4 of 20 read mouse >= 0.60** (0.688, 0.615,
  0.605, 0.603), 7 of 20 clear 0.50, the median across the twenty is
  **0.465**, and 20 of 20 carry a mouse cross-fold under the identical
  protocol (the two liability repairs' folds, joined by the 10-30 fix to the
  mouse record). Objective 2 is the
  champion's strength, not the file's average.
- **Binding at a functional epitope.** The E12 pair (K344/K374) sits inside
  the VP1u-verified footprint (auth 200-216 + 341-377, including K344/K372/
  K375), i.e. the region known binders actually use, not a sterile patch.
- **Diversity.** 20 distinct backbones, 7 method families, 3 generator arms
  (hosted RFdiffusion3, Genie 3, hybrid anchor sets). Structural diversity,
  measured (US-align, all 20 pairwise): median pairwise TM 0.38, max 0.57 -
  **no near-identical fold pair at all**, 8 clusters at TM >= 0.5 (all
  singletons at TM >= 0.6). The near-neighbour pairs the earlier passes
  carried (the champion's Proton-PottsMPNN sibling; each hybrid parent beside
  its switch variant) are held in the **reserve** - exactly the shape the
  no-duplicates rule protects against.
- **Dimer context.** Every folded binder was placed in the 11QC dimer frame:
  minimum distance to the second protomer 20.3 A, to the N251 glycan 5.1 A.
  The single-protomer screen is safe at this epitope (apexes 93 A apart).

## Expressability and sequence-liability QC (2026-10-29)

Prompted by the Pythia Labs preprint's approach of constraining sequence
liabilities at design time, the final twenty were screened for the standard
liability motifs: N-glycosylation sequons, deamidation motifs
(NG/NS/DG/DS/QG), methionine load and free cysteines
(`records/developability-qc-2026-10-29.csv`). Result: **zero N-glycosylation
sequons** anywhere - the critical one for cell-free expression; 12 designs
carry a deamidation motif (mostly the moderate DS/DG class; three NG sites:
`b2_20_s2`, `r6d2_s1`, `e12_9`); one design (`r4d6`) carries an odd cysteine
(a free thiol). Nine of the twenty designs carry a flagged position **at or next to the
binding interface** (checked against each fold's contact map; the record
carries the positions) - a deamidation there could erode binding over time,
so this is a real, recorded risk rather than a hidden one.

**The round was then run, not just recorded.** Conservative repair variants
(N to Q at each NG site, the classic motif-removing swap with no charge
change; C to S at the free thiol) were built, folded restrained, unrestrained
and against the mouse, and screened by the organizers' prescreen
(`records/liability-round-2026-10-30.csv`). Two variants replaced their
parents **at no measured cost**: `b2_20_s2_n10q` (interface NG removed; chai
parity, unrestrained and ipSAE slightly better) and `r6d2_s1_n30q` (NG
removed; equal or better on every comparable read). Three parents stayed with
their costs recorded: `e12_9` (repair regresses unrestrained site-finding by
0.083), `r4d3_s1` (restrained -0.065) and `r4d6` (thiol removal costs 0.15 -
a free cysteine is the lesser liability). The swapped final list re-passes
the prescreen 20/20.

## Flags we would self-report

None. No prompt-injection content in the submission; no derivation from a
known binder (prescreen clean, de novo generation); no tag-aimed designs (the
constructs are tag-free and the epitope is the apical domain); no
near-identical designs across accounts (single account); no simulated data
presented as experimental (every number is an in-silico read, labelled).

## Honest limitations

- The switch magnitudes are modest and their per-site scatter is real; the
  wet lab decides whether the direction is enough.
- The assembled multi-chain direction (campaign 5) is tested on the block-target
  rescue - 74 of 110 samples engage both binders, the B-C brace forms, best
  unit 0.962 - and stays a recorded capability rather than a submission
  class (different target and restraints; no comparable read against the
  single-chain designs); the
  single-chain class carries the submission.
- The folds are single-protomer by host necessity; the dimer question is
  answered geometrically, not by a dimer fold.
- ipSAE is low for the top chai reads (cross-metric disagreement): recorded,
  not hidden - the prompt's "no single in-silico metric decides" is exactly
  this situation.

**Tie-break and reserve.** Within an equal-composite group the order is
switch evidence first (S - the challenge's hardest goal), then binding (B),
then the least-represented family. Held-back designs form the ranked
reserve: first the near-neighbour cluster around rank 1 (the
Proton-PottsMPNN redesigns), then the score order.

## Expected verdict (our own read)

Rule-compliant on every hard rule; competitive on the switch (5 of 20 carry
S5 - the new hybrid variant `53h` keeps its parent's 5/5 unrestrained
binding), the mouse objective (champion 0.688; 4 of 20 at or above 0.60) and
novelty (0 structural hits; 8 fold clusters); the risk is switch magnitude,
which no in-silico read can settle. Worth the wet-lab slots: yes - the
submission's strongest case is the one design carrying all three objectives
(`c3_e12rfd4_r4d5_d2`) plus five family-diverse switch partners.
