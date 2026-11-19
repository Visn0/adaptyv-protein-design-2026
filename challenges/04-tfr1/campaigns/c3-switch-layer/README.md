# Campaign 3 — the pH switch layer

Status: **complete** 2026-10-26 → 2026-10-28 — input: the 20 campaign-2
designs clearing the at-site line. 29 histidine variants folded; 21 kept
their binding; **13 carry forward**, headed by `c3_e12rfd4_r4d5_d2` (0.782,
mouse-competent) and `c3_e12b2_20_s2` (0.802). The pH-conditioned redesign
arm (Proton-PottsMPNN, 6 folds) closed at parity with its parent. Full
read: `results.md` (separation claim limited to the strong end; the weak
class is recorded as unresolved).

**The switch-transfer round (c3b, 2026-10-29).** Ten histidine variants on
the three strongest-binding S1 parents; the winner `c3_b4_H_r1d0000_53h`
(restrained 0.768, unrestrained 0.771 at 5/5, per-site pKa -2.14) replaced its
parent in the twenty. Per-site pKa values for all S5 families:
`pka-per-site.txt`.

## Why this campaign

This is objective 1, the hardest goal and the one the organizers weight above
everything else: "a weak but clearly pH-sensitive binder beats a strong,
insensitive one."

It is also the campaign challenge 2 never ran. Its switch retrofit was recorded
as "a new design experiment, not started", and that is the direct reason its
submission could not claim objective 1.

Two measured facts shape the whole campaign:

1. **The target has no histidine at this epitope.** Zero, across all 44
   neighbourhood residues. The switch cannot come from the target.
2. **Challenge 2's lineage had the wrong sign.** Every one of its five complexes
   scored a negative `delta_log_Ka`, meaning tighter at pH 6.0, which is the
   opposite of the objective. The sign is the result that matters.

## The mechanism, and the direction rule

The challenge asks the binder to hold at pH 7.4 and release at pH 6.0, so
affinity must fall as the pH falls. A histidine side chain is near-neutral at
7.4 and largely protonated near 6.0.

- A binder histidine facing a target **cation** gains a like-charge repulsion as
  the pH falls. Binding weakens. **This is the asked direction.**
- A binder histidine facing a target **anion** gains an attraction as the pH
  falls. Binding strengthens. This inverts the objective.

The anchors are therefore the conserved, exposed, glycan-clear cations
**344 K** on epitope set E2 and **374 K** on set E1. The conserved glutamates
343 E and 350 E are positions to keep histidine away from.

Because both anchors are conserved in mouse, the switch chemistry is identical
in both species. Objectives 1 and 2 are served by the same interface.

## The physical ceiling, stated up front

One titratable site changes affinity by at most tenfold per pH unit. The assay
window is 1.4 pH units. So one histidine buys at most about 25-fold in theory
and far less in practice, and two or three coupled sites are needed for a large
swing. The organizers' prompt applies exactly this sanity check.

The methodology will therefore state a predicted **direction and ratio** with the
number of titratable sites that produce it. It will never claim "no detectable
binding at pH 6.0", which is a wet-lab observation.

## Configuration

**Input.** Every family champion and family member from campaign 2 that clears
the at-site line.

**Three arms.**

| arm | method | purpose |
|---|---|---|
| **R** retrofit | pick interface positions whose side chain points at the anchor lysine in the co-folded pose, mutate to histidine, re-fold | the main arm, applied to every family |
| **B** biased design | re-run full-backbone ProteinMPNN with a per-position histidine bias at those same positions | aims generation at the feature instead of filtering for it, which was challenge 3's clearest methodological finding |
| **L** ladder | one validated backbone, four variants: 0, 1, 2 and 3 interface histidines | the declared mechanism control; the organizers allow such a control to replace a submission's last pick |

**Position selection for arms R and B.** From the co-folded pose, keep binder
positions whose side-chain centroid lies within 8 A of the anchor lysine's
terminal nitrogen and whose own side chain is solvent exposed. Never pick a
buried position: a buried histidine changes the fold rather than the interface.

**Scoring.** `tools/switch/linkage_score.py`, which runs PROPKA on the bound and
free states and integrates the Wyman linkage relation across pH 6.0 to 7.4.
Keep the venv on Python 3.12: PROPKA 3.5.1 breaks on 3.14.

## Pre-registered gates

1. **Binding must survive.** A histidine variant is discarded if its at-site
   ipSAE falls below 0.60, or by more than 0.10 from its parent. A switch on a
   design that no longer binds is worthless.
2. **The sign must be positive.** `delta_log_Ka > 0`. This is the gate that
   challenge 2's lineage failed on all five complexes.
3. **The magnitude is never quoted as a fold-change.** The scorer was about two
   orders conservative against its FcRn reference. It ranks; it does not predict.
4. **Two or more cation-facing histidines** earns the top switch band in the
   rubric. One earns the middle band.

## Discard rule

If no histidine variant of any family keeps its binding and shows a positive
linkage sign, then the submission competes on objectives 2 and 3 only and states
that plainly in the methodology. The parent designs still ship, and the
campaign's negative result is recorded with its numbers.

This is the explicit fallback. It is better than challenge 2's outcome, which was
no submission at all.

## What this campaign records

`notes/c3-switch.md`: the chosen positions per family with the geometric reason,
the full linkage table with signs for every variant and its parent, the
before-and-after at-site ipSAE for every variant, the ladder series, and the
predicted ratio with its site count.
