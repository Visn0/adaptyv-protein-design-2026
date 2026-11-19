# Campaign 8: deep-junction scale-up (activation geometry)

Started 2026-10-20 22:31. This campaign exists because of one measurement.

## Why

The community scan found the first usable activation scorer
(`activation_geometry.py`, see `notes/agonism-geometry-2026-10-20.md`). We
reproduced its calibration on four experimental structures, then rescored every
design from every campaign. Result: the **c3 junction-only config produced 4 of
the 6 perfect (6/6) activation geometries** - more than any other generator.

The best designs so far reach depth 23.1 A below the vestibule rim with all six
pharmacophore contacts and unanimous pose agreement across samples. For
comparison, the experimental full agonists span 18.9-23.6 A.

So campaign 8 repeats the exact configuration that produced those designs, at
scale: 60 further single-design runs.

## Configuration

- Spec: `campaigns/c3-boltzgen-cyclic/scripts/spec-glp1r-cyclic-junction.yaml`
  (junction-only hotspots, cyclic peptide 12-18 aa) - unchanged.
- Runner: `~/c3-work/c8-deep-junction.sh`, one design per run, fresh output
  directory per design, `MEMLIMIT_MB=12500`.
- Output: `~/c3-work/c8-deep-junction/runN/`.

## Plan

1. Generate 60 designs overnight.
2. Fold each against the full 409-residue construct (chain B, offset 24) with
   Boltz, 5 samples.
3. Screen with both scorers: the binding screen (ipSAE etc.) and the
   activation-geometry gate.
4. Keep designs that are both binding HITs and deep-tier with high feature
   counts and pose agreement. Those become the agonism-justified submission
   candidates.

## Status

Generation running. Results and the updated champion table follow when the
folds land.
