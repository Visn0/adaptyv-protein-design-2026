# Campaign 1 — results (executed record)

Status: **complete** 2026-10-23 21:00 → 2026-10-25 01:35. **Decision: E12
advances to campaign 2; E0 does not** (one design short of the line). Findings
live here; the deep records stay in `notes/`.

## What ran

| stage | tool | scope | result | artifacts |
|---|---|---|---|---|
| generation | genie3 (local GPU) | 4 sets x 24 = 96 designs, E0/E1/E2/E12 | all pass geometry | `~/c4-work/genie3/runs/` |
| sequencing | ProteinMPNN (CA-only, CPU) | 96 sequences | banked | `~/c4-work/seqs/` |
| folds | Boltz-2, 5 samples, full 639-res protomer | 96 designs + 3 controls | 480 models, 0 HIT | `~/c4-work/folds/` |
| fold screen v2 | `scripts/screen_folds_c4.py` | 495 samples | 0 clean at-site anywhere; 69 clash; rest floaters | `~/c4-work/logs/folds-screen-v2.csv` |
| generation arm B | RFD4-Proteina (hosted NIM) | 97 designs, 4 sets | all clean; E0 best obeyed (24/24, 0.86) | `~/c4-work/rfd4/`, `notes/rfd4-arm.md` |
| restrained screen | Chai-1, pocket restraints, 5 samples | 48 designs (24 E0 + 24 E12), 240 samples | **E12: 8/24 >= 0.45 (top 0.752); E0: 5/24 (top 0.556)** | `~/c4-work/chai/designs/`, `logs/chai-restrained.csv` |

## Key findings

1. **The unrestrained co-fold read is fold-limited on this target.** Boltz-2
   and Chai-1 both float the native VP1u RBD 42–55 A from the verified apical
   footprint (ipTM 0.19 unrestrained), while the C2 champion control
   reproduces at ipSAE 0.84–0.90 through the same pipeline. Recorded as
   "cannot decide", not an epitope verdict (`notes/c1-triage.md`).
2. **A directed read works**: Chai-1 with pocket restraints docks designs at
   their designed patch and ranks them (calibration 0.21–0.75; native
   reference 0.42–0.48; stable +-0.02 per design). Caveat: directed poses —
   a consistency read, not independent binding evidence
   (`notes/screen-predictor-options.md`).
3. **Equal-bars confound falsified**: E0 designs at 2 restraints read
   0.412/0.405 — no jump toward E12's 0.655/0.752, so the E12-vs-E0 gap is
   not a restraint-count artifact.
4. **v1 screen numbers were too generous** (site-only clash test); v2 takes
   the minimum over all target atoms — 12 "clean" samples were off-site jams.
5. The native footprint was re-verified from 11RN.cif: TfR1 auth contacts
   202–212 + 348, 371.

## Decisions

- Original fold-based advance rule: **cannot decide** (recorded).
- Amended rule (registered before the full screen): a set advances when
  >= 25 % of its screened designs (>= 6 of 24) score mean restrained
  ipTM >= 0.45 (level with the native reference).
- Final: **E12 advances** — 8 of 24 at or above 0.45 (top: e12_18 0.752,
  e12_9 0.655, e12_6 0.639). **E0 does not** — 5 of 24, one short; its top is
  0.556 (e0_22). Honest margin (review accepted, 2026-10-25): **E0 is not
  eliminated.** Counting any-sample >= 0.45 would give E0 6/24 = 25 % (it
  would advance); Fisher's exact on 5/24 vs 8/24 is p = 0.52 — the sets are
  indistinguishable on the deciding metric, and E0's median is higher (0.388
  vs 0.324). E12's win rides its upper tail. A second-seed rerun of the four
  near-line designs (e0_2, e0_5, e0_7, e12_19) settled it: pooled means
  0.433/0.441/0.430/0.436 — all under 0.45, E0 stands at 5/24 on both seeds.
- Scope: the deciding screen covered **E0 and E12 only**. E1 and E2 were
  never screened under restraints (their only read was the unrestrained one).
  Their screen was **deferred by decision 2026-10-25** — the metric cannot
  rank sets at the needed precision (p = 0.52); the GPU hours moved to
  campaign 2. Full reasoning in `notes/c1-triage.md`, Scope. **Resolved
  2026-10-27: the deferred screen ran (see below) — 0/48 engaged; both sets
  closed negative.**

## E1/E2 re-screen (deferred item, executed 2026-10-27)

The deferred E1/E2 restrained screen ran as the fallback task during the RFD4
outage: all 48 C1-era designs folded under the current instrument (5 samples
each). Result: **0/48 engaged their designed site.** E1: 2/24 above the 0.45
bar (best e1_13 0.491) — both migrated, zero binder residues within 5 A of any
anchor across all five samples (worst-anchor distance 26–59 A). E2: 5/24 above
the bar (best e2_16 0.696) — all five migrated the same way; e2_16's pose sits
at auth 629–760, ~55 A from the designed epitope. Both sets closed negative.

**Instrument lesson (applied since):** a restrained-ipTM read only counts when
gated by engagement — worst-anchor min distance <= 8 A and binder residues at
site > 0. Off-site poses can read ~0.70, so the bar alone would promote a
migrated design. The E0 near-line designs pass the gate (3–5 A, 10–17 residues
at site), so the settled E0 read stands as honest.

## Diagrams

- `diagram/pipeline-per-design@2x.png` — every step of one design, with time
  and resource cost (which steps dominate: the two folds, 80 %).
- `diagram/strategy-comparison@2x.png` — the genie3 path against the hosted
  RFD4 path per design (the speed of each generation strategy).

## Pointers

- Deep records: `notes/c1-triage.md`, `notes/screen-predictor-options.md`,
  `notes/rfd4-arm.md`, `notes/review-2026-10-23.md`.
- Reproduction: `scripts/work/` (23 scripts + README), `nim/` (requests),
  `scripts/screen_folds_c4.py`.
