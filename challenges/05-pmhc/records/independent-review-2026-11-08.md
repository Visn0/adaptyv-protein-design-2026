# Independent review of the submission set, verified — 2026-11-08

An external reviewer audited the 20-design submission on deadline day. This
record states what I verified, what I refuted, and where the reviewer's own
recommendation does not hold.

## Verified

**1. Six of twenty sit below the organizer gate (peptide_read >= 0.61).**
Recomputed independently from the fold summaries. My readings:

| design | read | reviewer |
|---|---|---|
| peprim-wave1 run-012 design_0006 c3 | 0.443 | 0.443 |
| peprim-wave1 run-007 design_0004 | 0.489 | 0.489 |
| wave2-pep run-054 design_0005 | 0.546 | 0.520 |
| wave2-pep run-049 design_0002 | 0.565 | 0.565 |
| L58K-Q15K (rank 1, composite 90.5) | 0.574 | 0.574 |
| E23K | 0.600 | 0.600 |

One entry differs by 0.026 (wave2-pep-054). The count of six holds.

**2. The swap's documented criterion is false.** `swap_stars.py` stated it
removed "the six weakest entries on the organizers' epitope criterion
(peptide_read <= 0.098)". The six removed entries actually read:

    W57K 0.665 | N71K 0.641 | c5 0.644 | H27K 0.537 | A58K-F50K 0.527 |
    nim-wave3-021 0.441

Nothing in the repo or in `~/c5-work` supports 0.098. The 0.0 readings behind
that number belong to a **descendant** design (`W57K-combo285357`), not to any
removed entry — the lookup joined the wrong generation of the same family.
The header now carries the correction.

**3. Three removed entries outread fourteen of the twenty that stayed.**
W57K 0.665, c5 0.644 and N71K 0.641 all clear 0.61. Confirmed.

**4. Diversity collapsed.** 20 entries, **14 unique backbones**.
`mini-wave1__run-014__design_0005` contributes **4** (A16K, Q48K, L23K, A47K)
— 20 percent of the set from one scaffold. The original ranking capped each
run at two entries; the hand-written swap bypassed that cap. Confirmed.

**5. The score column mixes two formulas.** The first 14 entries carry v2
scores (90.5 down to 61.5) and the last 6 carry v4 scores (58.9 down to 54.7).
The two are nominally 0-100 and are not comparable. Confirmed.

## Refuted

**6. "The repo's own validator no longer gates this file."** False. Running
the current validator on the submission:

```
$ PYTHONPATH= .venv/bin/python tools/analysis/validate_submission.py \
      challenges/05-pmhc/submission/submission-05-pmhc.csv
20 design(s) checked
OK - ready to upload          (exit 0)
```

`single_chain` is in the validator's allowed class set, and the run produced
no rejection and no histidine warnings. The file is gated and it passes.

## Where the reviewer's recommendation does not hold

The proposal was a three-for-three swap: bring back W57K, mini-011 c5 and
N71K, dropping the three lowest gate readers. Gate compliance would rise from
14/20 to 17/20. **One of the three proposed additions is not specific.**

| proposed IN | G12D | WT | separation |
|---|---|---|---|
| N71K | 0.641 | 0.018 | **0.623** |
| W57K | 0.665 | 0.194 | 0.471 |
| **mini-011 c5** | 0.644 | **0.580** | **0.064** |

`mini-011 c5` binds the WT peptide at 0.580 against G12D 0.644. Its E-score is
**+1.62** — the wrong sign. It is the same defect that disqualified the raw
generation candidate pr-089 in C19. The reviewer applied the correct principle
("the gate measures pose confidence, not specificity") to protect rank 1, then
did not apply it to their own additions.

The other two additions are sound and materially better than what they would
replace. The reviewer also did not report a finding that this analysis turned
up: the entry `peprim-wave1 run-007 design_0004` has a G12D read of 0.489 and
a **WT read of 0.479 — a separation of 0.010**. It is itself non-specific, and
it is the weakest entry on that criterion regardless of the gate.

## Outcome, 2026-11-08 — the clean panel settled it

The clean two-state panel ran: nine designs, each folded twice from one
sequence source in one batch (six entries below the gate, three proposed
restorations). Result:

| design | G12D | WT | separation | outcome |
|---|---|---|---|---|
| N71K | 0.676 | 0.006 | 0.670 | restored |
| W57K | 0.641 | 0.223 | 0.418 | restored |
| mini-011 c5 | 0.635 | 0.519 | 0.116 | **not restored** |
| wave2-pep-049 | 0.596 | 0.053 | 0.543 | kept (below gate) |
| L58K-Q15K | 0.554 | 0.000 | 0.554 | kept (rank 1) |
| E23K | 0.545 | 0.313 | 0.232 | kept (below gate) |
| peprim-007 | 0.486 | 0.429 | 0.057 | **removed** |
| wave2-pep-054 | 0.463 | 0.019 | 0.444 | kept (below gate) |
| peprim-012-c3 | 0.411 | 0.113 | 0.298 | **removed** |

The six entries' reads reproduced their recorded values within about 0.05, so
the earlier readings were sound. The reviewer's restore list was right about
two designs and wrong about one. `mini-011 c5` passes the gate but its
wild-type read is 0.519 — cross-reactive, exactly the defect predicted above.
It was excluded.

The swap was made **two-for-two**: N71K and W57K in, `peprim-007` (separation
0.057) and `peprim-012-c3` out. Both swaps are strict improvements on both
criteria, and gate compliance rises from 14 of 20 to **16 of 20**.

An error of my own surfaced here and is worth recording: the first panel folded
three candidate sequences truncated to 60 residues, because a display-truncated
string was copied into the builder. Those arms read near zero, which is what
exposed the mistake. Corrected lengths were 98, 86 and 100 residues. **Never
build an input from a printed preview of a sequence — read the source value.**

## Caveat, resolved

The earlier readings came from several fold batches and crossed the `evo`
prefix, which is why they were not trusted. The panel above removes both
problems: one sequence source per design, one fold batch, full names matched
including the prefix. Only three arms were affected by the truncation bug, and
they were re-folded.

The score column in `selection-scores-05-pmhc.csv` is left empty for the two
restored designs: that column already mixes two formulas, and inventing a third
would make it worse.
