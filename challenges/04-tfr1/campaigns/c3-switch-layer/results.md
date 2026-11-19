# Campaign 3 — results (executed record)

Status: **complete** 2026-10-26 01:37 → 05:20. **Decision: 13 variants carry
into campaign 4 — binding kept (gate 1) plus a working per-site mechanism (the
engineered histidines register the predicted bound-state pKa depression at the
anchor lysines). The registered sign gate is reported as a consistency check,
not relied on (review finding 1, accepted). The fallback path (objectives 2–3
only) is not taken.** Deep record: `notes/c3-switch.md`.

## What ran

| stage | tool | scope | result | artifacts |
|---|---|---|---|---|
| position pick | `scripts/work/c3-pick-positions.py` (vendored switch geometry + rSASA filter) | 20 designs, both anchors | exposed cation-facing positions on every qualifier | `campaigns/c3-switch-layer/positions.jsonl` |
| variant build | `scripts/work/c3-build-designs.py` | 29 variants (7 doubles, 19 singles, 3 ladder) | identical fold treatment to parents | `~/c4-work/chai/designs/c3_*` |
| folds | chai, restrained K223/K253, 5 samples | 29 variants, 145 samples | 29/29 | `logs/c3-screen.log` |
| gate 1 | `scripts/work/c3-restrained-scores.py` | at-site read vs parent | 21/29 keep (within 0.10) | `logs/c3-restrained.csv` |
| gate 2 (registered) | `tools/switch/linkage_score.py` (PROPKA + Wyman, pH 6.0–7.4) | 29 variants + 10 parents | 26/29 move positive vs parent; parent null 10/81 (~12 %) — consistency only | `logs/c3-linkage.csv` |
| per-site mechanism | `scripts/work/c3-histidine-pka.py` | engineered His, 2 families + 4 controls | engaging sites -0.5..-2.8; far sites flat; one wrong-direction site | `pka-per-site.txt` |

## Key findings

1. **The retrofit holds on the top family.** `e12rfd4_r5d1` (parent 0.779)
   reads 0.782 / 0.781 / 0.748 on the 1/2/3-histidine ladder. Eight of 29
   variants lose binding (worst -0.521); the picked positions on those designs
   were load-bearing. Gate-1 limitation recorded: the read does not price the
   Asp→His contact change (parent carboxylate at 1.78/2.83 A to the anchor NZ
   vs variant imidazole at 3.62/3.88 A).
2. **The per-site mechanism is the substance**: engineered histidines facing
   the anchor lysines show bound-state pKa depressions up to -2.8; far
   picks (8.0–8.4 A) read flat (-0.05, -0.15) and their totals go negative; a
   wrong-direction site (+0.48) drags its total negative. The instrument
   separates engaging from non-engaging sites **at the strong end only**: its
   error on experimental benchmarks is ~0.8 pH units, larger than the 0.4–0.5
   gap of the weakest class, so the -0.53 and -0.63 sites are recorded as
   **unresolved**, not engaging (reviewer finding 2, 2026-10-27). Tuning
   guidance recorded: the 7.4→6.0 window is exercised hardest by free pKas
   near 6.8–7.0; the current set clusters at 5.9–6.4 (reviewer finding 3).
3. **Magnitudes are not quotable.** The totals carry null-level scatter on
   this 639-res target; the raw top is an unmodified parent (extreme tail of
   the null). Recorded statement: direction + engineered site count (1–3) +
   per-site shifts; never a fold-change (gate 3).

## Gate-1 discards (8)

`c3_e12rfd4_r3d4_s1` (-0.158) · `c3_e12rfd4_r4d5_s2` (-0.188) ·
`c3_e12rfd4_r3d4_s2` (-0.251) · `c3_e12rfd4_r4d3_d2` (-0.322) ·
`c3_e12rfd4_r6d5_s1` (-0.347) · `c3_e12rfd4_r4d3_s2` (-0.407) ·
`c3_e12rfd4_r6d5_d2` (-0.424) · `c3_e12b2_8_s1` (-0.521).

## Carry-forward (13 variants, into campaign 4)

`c3_e12rfd4_r5d1`: d2, l1, l2, l3, s1, s2 · `c3_e12rfd4_r5d7_d2` ·
`c3_e12rfd4_r4d5_d2` · `c3_e12rfd4_r3d4_d2` · `c3_e12rfd4_r4d3_s1` ·
`c3_e12b2_20`: d2, s1, s2.

The ladder (parent -> l1 -> l2 -> l3) ships as the declared mechanism control
(the organizers allow such a control to replace a submission's last pick).

## Caveats

- The same directed-read caveat as campaigns 1–2: restrained poses are a
  consistency read.
- The linkage scorer's own calibration note stands: about two orders
  conservative against its FcRn reference — it ranks, it does not predict.
- Review response: findings accepted and corrections recorded in
  `notes/c3-switch.md` ("Review corrections"); the per-site pKa measurement
  was added the same day.

## Pointers

- `notes/c3-switch.md` (chosen positions with geometry, per-site pKa table,
  sign table, review corrections).
- CSVs in this folder: `positions.jsonl`, `variants.csv`, `fold-queue.txt`,
  `linkage.csv`, `restrained.csv`, `best-models.json`, `pka-per-site.txt`.
- Reproduction: `scripts/work/c3-*.{py,sh}`, `tools/switch/` (vendored).
