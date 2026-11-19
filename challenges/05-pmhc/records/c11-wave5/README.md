# Wave 5 (PEPRIM, 200 designs) - negative, no swaps (2026-11-02)

Generation: `rfd4-batch.sh PEPRIM 25 8 wave5-peprim`, 25 calls x 8 designs,
all completed with zero validation errors (~22 min). Pose screen: 200
designs, 30 pass all three rules (arcs, peptide-first, C3 charge shell).

30 passers folded (Boltz-2, 5 samples). Best reads:

| design | ipTM | i_pDAE | E |
|---|---|---|---|
| wave5-peprim run-014 d0002 | 0.973 | 0.871 | +1.38 |
| wave5-peprim run-021 d0006 | 0.965 | 0.817 | +0.20 |
| wave5-peprim run-024 d0000 | 0.964 | 0.749 | -0.10 |
| wave5-peprim run-021 d0003 | 0.801 | 0.176 | -1.82 |

The affinity-strong designs read POSITIVE E (wrong electrostatics for this
target); the one strongly negative design has a weak interface (i_pDAE 0.18).
Composite estimate for the best (with an assumed mid dfree): ~57, below the
current set's 20th place (60.9). **No swaps; the final 20 stand.**

Lesson for the record: the PEPRIM conditioning favors interface quality, not
the electrostatic reading. The E-sign is only visible after a fold (the pose
screen cannot see it), so the cheapest correct policy is unchanged: fold the
screen passers, then let the composite decide - but expect ~1 in 30, not 1 in
5, to be an E-passing candidate from this campaign.
