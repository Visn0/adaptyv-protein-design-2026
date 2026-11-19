# Campaign 1 — feasibility and epitope triage

Status: **executed** 2026-10-23 21:00 → 2026-10-24. Results:
[`results.md`](results.md) · diagrams: [`diagram/`](diagram/) · deep records:
`notes/c1-triage.md`, `notes/screen-predictor-options.md`, `notes/rfd4-arm.md`.

## Why this campaign

Two questions block every other campaign, and both are cheap to answer.

1. **Which epitope set docks?** Challenge 2's hardest lesson was that epitope
   difficulty gates everything: the same protocol that produced two good design
   families on an easy surface produced nothing at all on a hard junction
   epitope, across 18 folded designs and 90 samples. Spending the week on a
   surface that resists docking is exactly how challenge 2 ended with no
   submission.
2. **Which fold target fits on this card?** The TfR1 dimer is 1278 residues. A
   single protomer is 639. Challenge 2's 456-residue complex needed 11.3 GiB.
   Nothing downstream can be planned until this is measured.

This campaign answers both and submits nothing.

## Configuration

**Targets.**

| use | file | residues |
|---|---|---|
| generation | apical block 180-400 of 11QC chain A, to be cut | 221 |
| fold, first choice | 11QC chain A, full protomer | 639 |
| fold, fallback | the same apical block, domain complete | 221 |
| clash check | 11QC chains A and B | 1278 |

Generation uses one protomer only. The two apical domains are 90.1 A apart, so
no binder can span them.

**Epitope sets** (from `notes/epitope-analysis.md`):

| set | hotspots | role |
|---|---|---|
| E0 | 204, 208, 210, 211, 348, 371 | the organizers' hint, human specific |
| E1 | 206, 207, 209, 374 | conserved, carries 374 K |
| E2 | 343, 344, 347, 350, 351 | conserved, carries 344 K, furthest from the glycan |

**Generation.** Genie 3 from `~/.venvs/genie3`, 24 designs per set, binder length
60 to 110. About 66 s per design, so 72 designs is about 80 minutes.

**Sequences.** Full-backbone ProteinMPNN, never CA-only. CA-only sequencing was
the chief error of challenge 2: it capped a good backbone at ipSAE 0.248 that
later reached 0.852 under full-backbone sequencing.

**Folds.** Boltz-2, 5 samples, seed 42, binder as chain A, receptor MSA
depth-capped at 1024 rows, `msa: empty` for the binder chain.

## Tasks, in order

1. **Measure the fold.** Build one dummy complex of a 100-residue binder against
   the 639-residue protomer. Run it under `memlimit.py` with
   `watch_resources.py`. Record peak RSS, peak GPU and wall time. Decide the
   fold target from the measurement, not from an estimate.
2. **Cut the targets.** Build the apical generation block from surviving residue
   blocks, never as a plain range: a contig that skips a residue stops
   RFdiffusion-class tools outright. Reuse the shape of
   `02-tnfa/handoff/rfd3/make_patch.py`.
3. **Write the site maps.** One site rule per epitope set for
   `02-tnfa/handoff/scripts/screen_folds_site.py`. Then assert a known-good count
   against a hand-checked design. A site check keyed wrongly silently passes
   everything and reports "no contact" for every fold, which happened in
   challenge 2.
4. **Fetch the calibration structures.** 11RN, the apical complex named in the
   brief, and 1SUV, the transferrin complex. Measure a real apical interface's
   contact count and buried area, and verify the brief's claim that this epitope
   leaves the transferrin site free.
5. **Generate.** 24 designs per set on E0, E1 and E2.
6. **Screen the geometry before spending fold time.** Count binder heavy atoms
   within 2 A of the target. Zero to two is a docked design. Dozens means the
   binder was placed inside the target, which is what an unset origin strategy
   produces. Also check every design against the full dimer for atoms inside the
   second protomer, and against the N251 glycan position.
7. **Fold everything that passes geometry.** Then read the at-site spread per
   backbone, not the best single sample.

## Pre-registered decision rule

Written before any data.

- An epitope set **advances** to campaign 2 if at least two of its backbones have
  a majority of their five samples at the designed site, with a best at-site
  ipSAE of 0.60 or higher.
- A set is **parked** if it places designs on the site geometrically but every
  at-site fold scores below 0.60. Challenge 2 called this pattern "touching, not
  docking", and it is the signature of a hard epitope.
- If **no** set advances, the campaign stops and records the negative, exactly as
  challenge 2's stop rule required. No further GPU time is spent on this target.
- If E1 and E2 are both parked but E0 advances, the submission competes on
  objective 3 and says so plainly.

## What this campaign records

`notes/c1-triage.md`: the memory measurement, the per-set geometry counts, the
per-backbone at-site fold spread, the calibration numbers from 11RN and 1SUV,
and the decision the rule produced.
