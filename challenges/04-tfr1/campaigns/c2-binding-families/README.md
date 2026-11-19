# Campaign 2 — binding families on the surviving epitopes

Status: **complete** 2026-10-26 01:35 — 20 designs cleared the line and
carry into campaign 3; the executed record with all numbers is in
`results.md`. Days 2 to 3.

## Why this campaign

Nothing in this challenge is reachable without a binder. Objective 1 needs an
interface to put a switch into, and objective 2 needs an interface to test on a
second species. Campaign 2 produces the interfaces.

It follows the one protocol in this repo that has ever reached the released
winners' score band. In challenge 2, Genie 3 backbones re-sequenced with
full-backbone ProteinMPNN produced two converging families: 18 members on one
backbone at ipSAE 0.63 to 0.85, and a champion whose five independent folds read
0.832, 0.837, 0.840, 0.842 and 0.852. Real wet-lab binders score 0.86 to 0.91
through the same pipeline.

## Configuration

**Arms.** Two generators run in parallel, because the challenge-2 calibration
showed the generator choice dominates the outcome far more than filter tuning.

| arm | generator | why |
|---|---|---|
| A | Genie 3 | bound 8 of 23 on Anthropic's released TNF-alpha campaign, against RFdiffusion3's 1 of 40; installed and measured on this box at 66 s per design |
| B | RFD4-Proteina, NVIDIA hosted pool | produced 17 of the 20 designs in the challenge-3 submission; the hosted pool is free until 2026-11-04, which covers this window; the request builder exists at `nim/build_request.py` |
| C | RFdiffusion3, local | control arm only, for continuity with the challenge-2 record |

Arm B needs its annotated CIF rebuilt per epitope set. `nim/build_request.py`
currently hard-codes the E0 patch in `APICAL_PATCH`; it must take the set as an
argument before this campaign runs.

**Epitope sets.** Whichever advanced in campaign 1, in that priority order.

**Binder length.** 60 to 110 residues. The challenge-3 submission's winning band
and the Genie 3 feasibility band agree on this range.

**Sequences.** Full-backbone ProteinMPNN at temperature 0.1 and 0.3, 8 to 16
sequences per picked backbone. SolubleMPNN for any backbone whose plain
ProteinMPNN output comes back alanine-rich: measured 28 percent alanine against
47 percent on the same backbones in challenge 3.

**Folds.** Boltz-2, 5 samples, seed 42, the fold target campaign 1 chose.

## The protocol, in order

This order is the lesson, not a preference.

1. Generate diverse backbones, 48 to 64 per advancing set.
2. Screen geometry: binder atoms within 2 A of the target, dimer clash, glycan
   footprint.
3. **Fold them all.** Do not pre-select by any sequence metric.
4. **Pick backbones by their folded spread**, meaning the majority of five
   samples at the designed site and the top at-site scores. Backbone choice
   dominates: in challenge 2 one control backbone stayed at or below 0.19 under
   identical treatment while its sibling reached 0.852.
5. Re-sequence only the picks, with full-backbone ProteinMPNN, 8 to 16 sequences
   each at two temperatures and fresh seeds.
6. Fold every new sequence. Keep only families that reproduce across independent
   folds.
7. Report each champion's whole five-sample spread. Never a single sample.

## Screens recorded per design

The three the organizers require, plus the ones this repo learned to need.

| screen | source | gate |
|---|---|---|
| ipSAE at the designed site | IPSAE on Boltz-2 output | 0.80 to submit, 0.60 to keep |
| at-site contact | `screen_folds_site.py` with the campaign-1 site map | required |
| pLDDT | Boltz-2 | 63 floor |
| mean Kyte-Doolittle hydropathy | sequence | recorded, banded |
| pDockQ2 | IPSAE | 0.18 floor, not a ranking gate |
| charged fraction, GRAVY, largest residue share | sequence | flagged against the winners' bands: 41.2 percent charged, GRAVY -0.56, largest residue 22.2 percent |
| interface atom pairs | fold | recorded; the winners sat at 307 to 370 pairs, and more contact was not more confidence |

## Pre-registered discard rule

If, after at least three generation batches per advancing set, folds of every
at-site design, and full-backbone re-sequencing of every picked backbone, no
family reaches **ipSAE 0.80 at the designed site with a majority of samples at
the site**, then strategies S1 and S2 are both dead. The campaign records the
negative and no switch work begins.

If families reach 0.60 to 0.80 only, they pass to campaign 3 as "possible" and
the methodology reports them in that band without claiming the submission line.

## Known traps for this campaign

Taken from `notes/lessons-c2-c3.md`, section D.

- One fresh output directory per design, `n_batches=1`, wrapped in a timeout. A
  shared directory makes later runs exit in seconds doing nothing.
- Copy Boltz outputs under their original names. Renaming makes IPSAE read no
  pLDDT file and report pDockQ2 at a floor value while ipSAE stays correct.
- After killing any fold runner, check the process list and kill orphaned Boltz
  children by PID. They hold about 11 GB and starve the next batch.
- A memory kill, exit 137, can still leave usable models. Check the output
  directory before retrying.
- Kill by PID, never with a `pkill -f` pattern that matches the calling shell.

## What this campaign records

`notes/c2-families.md`: per-arm and per-set design counts, the geometry screen
table, the per-backbone folded spread that drove the picks, the family tables
with every member's sequence and fold spread, and the champion spreads.
