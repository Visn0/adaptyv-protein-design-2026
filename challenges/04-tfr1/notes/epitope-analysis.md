# 04 — TfR1 epitope analysis (measured 2026-10-23, before any generation)

Every number here comes from `scripts/epitope_analysis.py`, which runs on the two
structures in `inputs/`. Re-run it with:

    .venv/bin/python challenges/04-tfr1/scripts/epitope_analysis.py

It writes `notes/epitope-analysis.csv`, one row per neighbourhood residue.

## Why this analysis exists

The challenge ranks three objectives: (1) a pH switch, (2) mouse
cross-reactivity, (3) affinity. The challenge page recommends the apical domain
"around Tyr211". Challenge 2 taught us that a recommended patch is not
automatically the right patch (`02-tnfa/notes/x3-strategy.md`, lever 1). So the
patch was measured before any compute was spent.

## The constructs

| item | value |
|---|---|
| human, 11QC chain A | 639 amino acids, author numbering 122-760 |
| mouse, AF-Q62351-F1 | 641 amino acids, author numbering 123-763 |
| sequence identity | 498 of 638 aligned columns = **78.1 percent** |
| glycans in the model | NAG on N251, N317 and N727 of each chain |
| homodimer | chains A and B, 1278 residues in total |

The 78.1 percent figure confirms the brief. It only appears when the two chains
are aligned.

### Finding 0 — the species numbering offset is not constant

Mouse author number minus human author number is **+3 for 359 positions and +2
for 279 positions**. There is an indel between the two constructs.

A fixed offset therefore mis-maps the epitope. This is the same class of error as
AGENT.md mistake 21 (a wrong RFdiffusion3 offset gave a confident, wrong 0 of
72). A first pass of this analysis joined the two chains on author numbering and
reported 5.5 percent identity, which is impossible against a stated 78 percent.
That wrong number is what exposed the indel.

**Rule for every campaign: map human to mouse through the alignment in
`epitope_analysis.py`, never through an offset.**

## Finding 1 — the recommended patch is the least cross-reactive surface

The patch named on the challenge page and used by `nim/build_request.py` is
D204, R208, V210, Y211, N348, K371.

| human | mouse | relative exposure | species |
|---|---|---|---|
| 204 D | 207 Q | 24.4 % | substituted |
| 208 R | 211 N | 55.3 % | substituted |
| 210 V | — | 46.5 % | indel, no counterpart |
| 211 Y | 213 D | 27.2 % | substituted |
| 348 N | 350 K | 12.2 % | substituted |
| 371 K | 373 Q | 26.8 % | substituted |

**Five of six residues are substituted and the sixth falls in an indel. Not one
is conserved.** Two of the six (204 and 348) are also below the exposure line, so
the usable patch is really four residues.

The maximum CA-CA span of the named six is 15.7 A, just past the 15 A
feasibility line in AGENT.md rule 19. The 208-348 pair carries that span.

Consequence: a binder aimed at the named patch is selected for human
specificity. It can serve objective 3, which is human affinity. It argues
against objective 2.

## Finding 2 — there is a conserved and exposed face next to it

The neighbourhood is every chain-A residue with a heavy atom within 10 A of a
named-patch side chain: 44 residues. Of those, 27 are conserved in mouse, and 10
are both conserved and solvent exposed in the assembled dimer.

| human residue | exposure | charge | distance to the N251 glycan |
|---|---|---|---|
| 206 N | 65.8 % | neutral | 15.0 A |
| 207 G | 43.3 % | neutral | 15.2 A |
| 209 L | 57.9 % | neutral | 19.9 A |
| 231 K | 33.0 % | cation | **6.4 A** |
| 343 E | 39.4 % | anion | 22.8 A |
| 344 K | 28.9 % | cation | 20.7 A |
| 347 G | 57.5 % | neutral | 20.6 A |
| 350 E | 49.0 % | anion | 16.2 A |
| 351 G | 25.4 % | neutral | 17.8 A |
| 374 K | 28.2 % | cation | 13.9 A |

These residues sit 5.7 A to 21.7 A from Y211 and all fall inside the apical
domain, which spans roughly residues 189 to 382. The challenge calls the apical
domain a hint and not a rule, and names Tyr211 only as a landmark. This face
satisfies the hint and is cross-reactive by construction.

The whole face spans 23.7 A, which is wider than one hotspot set can cover. It
splits into two.

## Finding 3 — the target carries no titratable site at this epitope

| chemistry | in the neighbourhood | conserved and exposed |
|---|---|---|
| histidine | **0** | 0 |
| arginine or lysine | 7 | 231 K, 344 K, 374 K |
| aspartate or glutamate | 5 | 343 E, 350 E |

There is no target histidine anywhere in the epitope. **The whole pH switch must
be built on the binder.** No amount of epitope selection will supply it.

### The direction rule

The challenge asks the binder to hold at pH 7.4 and release at pH 6.0, so
affinity must fall as pH falls. A histidine gains a positive charge near pH 6.

- A binder histidine facing a target **cation** is neutral at 7.4 and positive at
  6.0. The new like-charge repulsion weakens binding as the pH falls. **This is
  the asked direction.**
- A binder histidine facing a target **anion** gains an attraction as the pH
  falls. This strengthens binding and **inverts the objective**.

Challenge 2 measured exactly that inversion on its own lineage: every design
scored a negative `delta_log_Ka`, meaning tighter at pH 6.0
(`02-tnfa/notes/linkage-check.md`). The sign was the informative result there,
and it is the thing to design for here.

So the switch anchors are the conserved exposed cations **344 K and 374 K**, and
the conserved glutamates 343 E and 350 E are positions to keep a binder histidine
away from.

## Finding 4 — the N251 glycan is adjacent, and it is conserved

NAG761 is N-linked to N251 by a 1.44 A glycosidic bond. It sits 11.2 A from the
named patch and **6.4 A from the conserved face**. The N-G-S sequon at human
251-253 is conserved in mouse at 253-255, so the glycan is present in both
species.

The model holds only the first sugar. A real N-glycan extends 10 A to 20 A
further, and no co-folding model in this stack represents it. Of the conserved
face, only **231 K is glycan adjacent at 6.4 A**. Every other conserved residue
is 13.9 A or further.

Consequence: drop 231 K from the hotspot sets, and screen every design for a
footprint that reaches across N251.

## The three epitope sets this produces

| set | residues | span | conserved | glycan clearance | serves |
|---|---|---|---|---|---|
| **E0 named tip** | 204, 208, 210, 211, 348, 371 | 15.7 A | no, 0 of 6 | 11.2 A | objective 3 |
| **E1 north** | 206, 207, 209, 374 | 11.8 A | yes, 4 of 4 | 13.9 A | objectives 1 and 2 |
| **E2 south** | 343, 344, 347, 350, 351 | 14.9 A | yes, 5 of 5 | 16.2 A | objectives 1 and 2 |

E1 carries one switch anchor (374 K). E2 carries one switch anchor (344 K) and is
the furthest from the glycan. E0 is the organizers' literal hint and the only set
that cannot serve cross-reactivity.

Glycan clearance in this table is the shortest distance from any atom of the set
to the N251 sugar, so the set figure is lower than some of its members' own
distances in the table above: E1 is set by 374 K at 13.9 A and E2 by 350 E at
16.2 A.

## Finding 5 — no cross-protomer binder is possible

Y211 of chain A to Y211 of chain B is **90.1 A**. The two apical domains sit at
opposite tips of the dimer.

This reverses a challenge-2 lesson. There, every wet-lab winner's interface
crossed two or three protomers, and the junction class was the productive one
(`02-tnfa/notes/filter-calibration.md`, finding 3). Here a 70 to 120 residue
binder cannot span 90 A, so **every design is single-protomer**, and generation
should use one protomer.

The dimer still matters in two ways. It presents two copies of the epitope, so a
target in solution can bind two immobilised designs at once. That avidity can
flatter the sensorgram and complicate the KD fit. And the full dimer remains the
right structure for the clash check.

## Compute feasibility, measured on this box

| target | residues | note |
|---|---|---|
| C2 TNF trimer, folded at 11.3 GiB | 456 | the measured reference point |
| C4 apical block 189-382 | 194 | matches C2's proven 195-residue patch target |
| C4 apical block 180-400 | 221 | the generation target |
| **C4 single protomer** | **639** | the wanted fold target, memory unmeasured |
| C4 full dimer | 1278 | out of reach, do not attempt |

Host memory is now 23 GiB total with 21 GiB available, not the 16 GiB the older
notes assume. A 639-residue fold is plausible but it is **not yet measured**.
Campaign 1 measures it before anything depends on it.

## What stays unverified

- The claim that the apical domain leaves the transferrin site free comes from
  the brief. It is not measured here, because no transferrin complex is on disk.
  Fetch 1SUV and measure it before the methodology repeats the claim.
- The exposure numbers use a theoretical maximum SASA table (Tien et al. 2013)
  and the deposited coordinates. They rank residues, they are not absolute.
- The glycan tree is absent from the model, so glycan clearance is a distance to
  the first sugar only.
