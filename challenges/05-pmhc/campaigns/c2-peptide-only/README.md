# C2 — peptide-only readers

**Strategy**: a design that touches mostly the peptide has fewer chances to
hold on to the healthy frame. The main funnel produced groove-floor
binders; this campaign selects for the opposite shape: minimal contact
with HLA, most contact on the 10-mer.

**Tools**: no new generation — the existing 1,121 unfolded designs are
mined from the pose screen by peptide contact share. Then boltz folding,
the standard scorer, and the tri-state.

**Pipeline**: 1,121 unfolded designs -> 45 with peptide share >= 0.45 and
ridge contacts >= 10 (top share: 0.96 — a near-pure peptide reader) ->
G12D folds (running) -> score -> tri-state for the winners.

**Results** (2026-11-01 12:45): 44/45 folded (one design lost to a crash-truncated
cache; queued for retry). **1 gate-passer, 6 JDI-like** — a modest yield vs the
main funnel's 25%, but the family's signature is real:

| design | ipSAE | ipTM | i_pDAE | fold peptide share |
| --- | --- | --- | --- | --- |
| wave1-pep__run-033__design_0003 | 0.675 | 0.958 | 0.810 | 0.42 |
| wave1-pep__run-026__design_0000 | 0.347 | 0.914 | 0.460 | 0.16 |
| wave2-pep__run-024__design_0001 | 0.367 | 0.891 | 0.537 | 0.42 |
| nim-wave3__run-010__design_0002 | 0.259 | 0.889 | 0.412 | 0.67 |
| wave1-pep__run-001__design_0003 | 0.164 | 0.817 | 0.138 | 0.43 |
| wave2-pep__run-001__design_0002 | 0.085 | 0.814 | 0.091 | 0.26 |

The leader (run-033 d0003) clears the organizer gate AND folds JDI-like AND
keeps a peptide-heavy interface (0.42) — a dual-qualified candidate for the
final set. nim-wave3 d0002 is the most peptide-focused fold (0.67 share).
Note: the fold's share can differ from the generator pose's share — the fold
rearranges contacts.

**Why it may work**: peptide-only geometry concentrates the interface on
the mutated 10-mer; a change at P6 perturbs a larger share of the contact
surface than it does for a groove-floor binder.
