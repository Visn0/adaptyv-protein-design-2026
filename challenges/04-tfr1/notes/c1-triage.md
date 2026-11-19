# 04 — campaign 1 triage (live record, started 2026-10-23)

This file records the campaign-1 run as it happens. The plan it follows is
`campaigns/c1-epitope-triage/README.md`, with the review changes in
`notes/review-2026-10-23.md` (four sets: E0, E1, E2, E12; the 11RN assertion).

## Setup, completed 2026-10-23

### The generation target

The apical block 180-400 of 11QC chain A, cut from the surviving residues
(221, contiguous). The block PDB is written with chain B and renumbered 1-221
into the Genie 3 dataset (`11qc_apical`, four problems: `11qc_e0`, `11qc_e1`,
`11qc_e2`, `11qc_e12`).

**Renumbering rule: block number = author number - 179.** It is valid because
the block is contiguous. The hotspot letters after the shift are asserted and
all agree:

| set | block hotspots | letters |
|---|---|---|
| E0 | B25, B29, B31, B32, B169, B192 | D, R, V, Y, N, K |
| E1 | B27, B28, B30, B195 | N, G, L, K |
| E2 | B164, B165, B168, B171, B172 | E, K, G, E, G |
| E12 | B165, B195 | K, K |

### The fold target, measured

The full-protomer fold was the one unmeasured risk. Probe: a 92-residue binder
(the C2 b2-d12 sequence) against the 639-residue protomer, Boltz-2, 5 samples,
seed 42, receptor MSA depth-capped at 1024 rows, binder `msa: empty`.

| measurement | value |
|---|---|
| peak job RSS | 15.61 GiB (cap 17 GiB) |
| peak GPU | 11.29 GiB of the 12.2 GB card |
| wall time | ~2.5 min for 5 samples |
| failed examples | 0 |

**Decision: the fold target is the full protomer.** Fold numbering for the
screen is `fold = author - 121`. No block-fold fallback is needed.

### MSAs

`inputs/msa/`, depth 1024, from the ColabFold server, one file per sequence:
human protomer `18b357b72434`, block `5a2246a6d920`, mouse `5f2d464a5da3`.

### Geometry screen

`~/c4-work/bin/screen-gen-geometry.py`, pre-registered pass rule: min binder-
target CA distance >= 3.0 Å AND at least 3 target CAs within 8 Å AND a designed
hotspot within 12 Å (block numbering). First design verified against the block
fasta (all hotspot letters agree).

## Generation and sequencing, completed 2026-10-23

| set | designs | pass geometry | sequences |
|---|---|---|---|
| E0 | 24 | 24 | 24 |
| E1 | 24 | 24 | 24 |
| E2 | 24 | 24 | 24 |
| E12 | 24 | 24 | 24 |

All 96 designs pass the geometry screen, and every one sits on its designed
patch in the generator output (hotspot CA-CA 4.3-6.4 Å for E0). Binder lengths
61-110. Sequences: CA-only ProteinMPNN, one per design (T = 0.1, seed 37),
run in parallel with the generation on CPU.

## The fold read is fold-limited (measured, with controls)

The first fold placed the binder 35-52 Å away from the designed patch, so four
controls were measured before the batch could be read. Raw records:
`~/c4-work/logs/diag-notes.log` and `~/c4-work/diag/`.

| control | result |
|---|---|
| C2 champion (wm-rank05) + TNF trimer through this exact yaml/MSA pipeline | ipSAE 0.841-0.902, pDockQ2 0.56-0.67 (its C2 record: 0.886) |
| 11RN VP1u RBD + 11QC protomer (the native apical binder) | 0 of 5 samples at the footprint, 44-47 Å, ipSAE 0.000 |
| the same, with the VP1u's own MSA | same, 42-50 Å |
| the same, 10 samples | 0 of 10 docked |
| the same, 25 samples (re-run after the host restart) | stopped: the post-reboot run stayed in kernel compilation for 24 min with no output. The 5- and 10-sample results stand |
| the same, against the 221-residue apical block | iptm up to 0.53, but the pose sits on a different patch (author 303-328, the dimer interface), footprint 33-38 Å away |

**Conclusion.** The pipeline is validated (the TNF champion reproduces). Under
this protocol Boltz-2 does not dock any binder, the native VP1u included, to
the TfR1 apical tip. It floats the binder or commits to the dimer-interface
patch. The 96-design fold batch therefore reads as a fold-limited screen, not
a verdict on the designs, and the pre-registered advance rule cannot decide
from it. boltz1 cannot run on this box (peak above 20 GiB for the same
complex).

The batch completed 2026-10-24 04:30 (93 folds in one pass; 96 designs, 480
model files). The box restarted at ~04:40; every artifact was verified intact
afterwards. Screen v2 over all 495 samples (`~/c4-work/logs/folds-screen-v2.csv`):

| set | designs | clean at-site samples (of 120) | clash samples | floaters | best at-site ipSAE |
|---|---|---|---|---|---|
| E0 | 24 | 0 | 16 | 104 | 0.000 |
| E1 | 24 | 0 | 25 | 95 | 0.000 |
| E2 | 24 | 0 | 4 | 116 | 0.000 |
| E12 | 24 | 0 | 24 | 96 | 0.000 |

Corrections in v2 (review accepted, 2026-10-24): the clash test now takes the
minimum over ALL target atoms, not only the designed residues. All 12 samples
that v1 called "clean at-site" carry an off-site heavy-atom collision
(1.6-2.6 A), so v1's clean counts and clash column were too generous; the v1
CSV is superseded. v2 also reports a common bar that is identical for every
set (>= 2 hotspot residues contacted) beside the pre-registered per-set rule -
under the common bar no set has any clean sample either. Per-set rule or
common bar, the unrestrained read stays "cannot decide".

Formal decision (`~/c4-work/bin/decide-c1.py`): **no set advances** (zero
qualifying backbones; the rule needs two per set). This is recorded as
**cannot decide**, not as an epitope verdict: the fold-limited read above is
the cause, and the generator-side evidence (all 96 designs placed on their
designed patch by construction) stands unchanged.

Fold numbering for the screen is `fold = author - 121`
(`scripts/screen_folds_c4.py --target full`).

## Amended advance rule (registered 2026-10-24; revised same day, before the screen)

The original fold-based rule stays recorded as "cannot decide" (above). The
operative screen is now the restrained chai read (`screen-predictor-options.md`).
The amended rule:

**A set advances to campaign 2 when at least 25 percent of its screened
designs (>= 6 of 24) score mean restrained ipTM >= 0.45.**

Rationale: the native VP1u reference (a binder known to work) scores 0.42-0.48
under the same protocol; 0.45 sits inside that range, so the line means "level
with the native reference". Revision (review accepted, 2026-10-24): the first
draft used 0.50 and described it as "at or above the native reference", but
0.50 is above the entire reference range, so the wording did not match the
number. The line is now 0.45 and the wording states what it means.

The pilot (4 designs per set) cannot support the threshold - with n=4 one
design moves a set across any 25 percent line. It is recorded as calibration
only; the rule is judged on the full 24 designs per set. Applied by
`scripts/work/decide-sets-restrained.py`; per-design numbers land in
`~/c4-work/logs/chai-restrained.csv`.

Known confound under test (review item, 2026-10-24): sets carry different
numbers of hotspot residues (E0 6, E2 5, E1 4, E12 2), so a design in a small
set has fewer restraints to satisfy. A falsification run re-scores two E0
designs with only 2 restraints; if their scores jump toward the E12 range,
the set comparison must move to an equal-restraint protocol before any set
advances. Resolved 2026-10-24: two E0 designs re-run with only 2 restraints
score 0.412 and 0.405 (vs 0.400 and 0.437 at 6) - no jump toward the E12 range
(0.655, 0.752), so the confound is falsified and the per-set protocol stands.
The full screen was resumed right after; completed designs skip on resume.

FINAL RESULT (2026-10-25 01:35, 48 designs, 240 samples; the watchdog's first
aggregation pass ran with the wrong python and a stale CSV - re-run corrected):

| set | n | mean ipTM >= 0.45 | >= 0.5 | median | top three |
|---|---|---|---|---|---|
| E0 | 24 | 5 (21%) | 4 | 0.388 | e0_22 0.556, e0_21 0.543, e0_19 0.520 |
| E12 | 24 | 8 (33%) | 7 | 0.324 | e12_18 0.752, e12_9 0.655, e12_6 0.639 |

**E12 advances to campaign 2** (33% >= the 25% line); E0 does not - one
design short (5 of the 6 needed). Margin recorded honestly: E0's median is
higher than E12's (0.388 vs 0.324); E12's win is carried by a stronger upper
tail (7 designs at 0.5+ against E0's 4; top 0.752 against 0.556).

Statistic choice matters at this margin (review accepted, 2026-10-25):
counting designs with ANY sample >= 0.45 gives E0 exactly 6 of 24 = 25%,
which would advance. The two decisive designs are e0_2 (mean 0.437, max
0.447) and e0_5 (mean 0.428, max 0.454). Fisher's exact on 5/24 vs 8/24 is
p = 0.52 - the sets are statistically indistinguishable on the deciding
metric. The pre-registered verdict stands (E12 clears the bar), but it is
recorded for what it is: **E0 is not eliminated**. A second-seed rerun of
the four near-line designs (e0_2, e0_5, e0_7, e12_19) is running to settle
whether E0 is at 5 or 6 (unit `chai-c1-finish`).

Reseed verdict (2026-10-25 09:30, second seed, pooled means = the pre-stated
comparison): e0_2 0.437+0.429 -> 0.433 pooled; e0_5 0.428+0.454 -> 0.441;
e0_7 0.428+0.433 -> 0.430; e12_19 0.441+0.432 -> 0.436. All stay under 0.45;
**E0 stands at 5 of 24 on both seeds** - the margin is stable and the
registered verdict holds (e0_5 crossed 0.45 on the second seed alone, which
is exactly the single-seed wobble pooling removes). E0 remains carried as a
secondary arm.

Scope (review accepted, 2026-10-25): **the deciding screen covered E0 and E12
only.** E1 and E2 were never put through any restrained screen - their only
measurement was the unrestrained read that returned "cannot decide" for
everything. Decision, same day: the E1/E2 screen is **deferred** - the metric
cannot rank sets at the precision this would need (p = 0.52 between the two
measured sets), so 9 GPU-hours buy completeness prose, not decisions, and the
hours move to campaign 2. The scope is recorded here and in
`campaigns/c1-epitope-triage/results.md`, which was the review's accepted
alternative. Revisit only if campaign 2 stalls with idle GPU. The equal-bars
caveat still applies to any future E1/E2 run (4 and 5 restraints).

## Morning decision menu

1. **RFD4-Proteina arm** (the plan's co-primary generator): ready to submit;
   all four request files build clean (`nim/build_request.py --set E0|E1|E2|E12`,
   verified letters and 10-31 hotspot atoms). Needs the NVIDIA API key or one
   HF Space sign-in. Note: it fixes the backbone class, not the fold screen.
2. **A second fold predictor** (Protenix, Chai-1, openfold): hours of setup,
   and the only route to a working co-fold screen for this target.
3. **Re-read campaign 1 from generation-side evidence only** (placement
   geometry, interface size): weak evidence, against the C2 lessons.
4. The submitted-file work (campaign 5) is unaffected.
