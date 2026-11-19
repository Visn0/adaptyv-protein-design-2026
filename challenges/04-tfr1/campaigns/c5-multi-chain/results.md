# Campaign 5 — multi-chain units: results

Status: **complete — rescued** (2026-10-27 → 2026-10-30). Verdict: **the
registered test (assembled three-chain fold) could not run on this host; the
direction was re-answered on the block target overnight 2026-10-28/29 and is
no longer untested.** 110 samples across 22 units: 74 engage both binders at
the anchors, 9 of 22 in all five samples, best unit ipTM 0.962 - recorded as
capability, not pursued as a submission class (different target and
restraints; no comparable read against the single-chain designs). The per-chain proxy below is confounded by construction (partner
context removed) and is recorded as inconclusive, not as a negative result.
Reviewer finding 1 (2026-10-27) applied. Plan in `README.md`, literature in
`research.md`.

## What ran

24 two-chain designs generated (hosted RFD4, two designed segments); 2 excluded
by the glycan screen; 22 designs folded. The assembled three-chain fold proved
unrunnable on this host (VRAM 11.9 of 12.2 GB, trunk ~10x slow, one host crash
`0x20001`), so the registered read was taken per chain: each design folded
twice (chain B and chain C alone against the target, each with its own
interface-derived restraints) — 44 folds, 44/44 complete. The B-C interface
stays validated from the design models (contacts 27-425 atom pairs, zero
clashes in all 22).

## The numbers (logs/c5-restrained.csv, 220 samples)

| read | result | single-chain E12 reference |
|---|---|---|
| unit read — **minimum** of the two chain folds (the honest aggregation for a unit where both chains must bind) | best **0.356** (`c5_r3d4`) | best 0.779 |
| unit read — mean of the two chain folds | best 0.502 (`c5_r3d6`), median ~0.27 | the 0.70 bar was calibrated on whole single binders, so this juxtaposition compares unlike quantities |
| designs at unit ipTM >= 0.70, either aggregation | **0** | 3+ |
| DockQ vs the design model | 0.00-0.19 for almost all (two 0.65-0.68 outliers) | 0.89-0.90 for single-chain controls |
| restrained chains sitting far from their restraint | 0 of 44 after the numbering fix | - |

The mean lets one good chain carry a flat partner — exactly `c5_r3d6`
(B 0.702, C 0.303). The minimum is the number a unit bar should be read
against; both aggregations fail it for every design, but the minimum is what
the record should compare.

**Numbering incident (found and fixed before the verdict was signed).** The
first pass of the 9 fallback-restraint files fed auth numbering from the
design models into restraint files that need sequence numbering (off by 121),
so those nine folds were conditioned on the wrong site and all read 39-48 A
from their intended residues. The fix (sequence position, letter re-read from
the target sequence) was applied and the nine re-folded; every corrected fold
now sits 3.4-9.5 A from its restraining residue. Corrected reads moved by
-0.17 to +0.13 ipTM and change no conclusion: best unit remains 0.502
(`c5_r3d6`), and the two designs whose mis-conditioned folds had accidentally
flattered them (`r2d1` B 0.438 -> 0.269; `r2d2` C 0.466 -> 0.355) now join the
floor class.

## Reading (both reads are confounded; recorded as inconclusive)

1. **The per-chain floor is the expected result of removing the partner.** The
   restrained read of an unrelated binder on this target calibrates at
   0.29-0.30, and most c5 chains read 0.21-0.33 — but a chain designed to
   brace against both the target and its partner, folded without its partner,
   should read low. `c5_r3d6`'s B chain (0.702, one chain behaving like an
   ordinary E12 binder) is the one data point that is not obviously an
   artifact of the adaptation.
2. **DockQ ~0.1 is also the expected result of removing the partner.** A
   constrained interface whose second half is deleted should not return to its
   designed pose in a free fold. The 0.89-0.90 single-chain controls do not
   make a fair comparison: their interfaces never depended on a third party.

Recorded limitation, carried from before the review: the per-chain adaptation
removes the B-C context. The registered discard rule fires mechanically, but
its profile conditions (B-C intact, clashes) were only ever measurable on the
assembled fold, so the rule fired on criteria it could not evaluate — this is
why the verdict is "untested", not "negative".

## Decision

The assembled test **could not run on this host** (the three-chain fold is
unrunnable: VRAM cliff, ~10x slow trunk, host crash; see crash 6). The
direction is **tested, positive as a capability read, not pursued as a submission class** - with four days to the
deadline and single-chain as the lead class, the compute is better spent
elsewhere. If the question matters again, the cheap rescue is recorded in
`README.md`: the same 22 units folded against the 221-residue apical **block**
target (~2.5 h GPU). The literature pass (`research.md`), the tooling
(per-pair matrices, DockQ and PRODIGY integration, `scripts/work/
c5b-restrained-scores.py`) and the generation recipe stay on record. E12
single-chain designs remain the challenge's lead class (campaigns 2, 6).

## Pointers

- Folds: `~/c4-work/chai/designs/c5[BC]_*` (44). Scores: `logs/c5-restrained.csv`.
- Generation: `~/c4-work/rfd4/C5/run-{1,2,3}`; request builder in `nim/`.
- Host crash during the assembled attempt: crash 6 in `~/windows-crash-prevention-plan.md`.
