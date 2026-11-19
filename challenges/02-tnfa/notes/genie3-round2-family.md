# Round 2: the d7 family — first designs in the winners' zone

Date: 2026-10-16/17. Working artifacts: `~/c2-work/genie3/` (not in git).
Evidence tables: `genie3/family.csv`, `genie3/genie3-all-scores.csv`.

## The comparison that found the mistakes

Diffing our designs against the 13 released binders (sequences, family structure,
folded interface size — same pipeline):

| group | charged % | GRAVY | largest AA % | internal identity | folded interface |
|---|---|---|---|---|---|
| winners (13) | 41.2 | −0.56 | 22.2 | 32.6 % | 307–370 atom pairs |
| our RFD3 campaign | 9.8 | +0.84 | 37.3 | 17.7 % | — |
| batch-01 (CA-only) | 45.1 | −0.67 | 23.7 | 14.3 % | 133–185 pairs |

Three findings: (1) the campaign's sequences were greasy, alanine-heavy and 4×
less charged than any real binder — a class that does not bind; (2) the winners
are ONE backbone family (8 of 13 near-duplicates) plus four singletons — success
converges; our batches were diverse singletons; (3) our folded interfaces were
half the winners' size.

## The fix and the family

**CA-only ProteinMPNN sequences were the chief error.** Re-sequencing the SAME
folded backbone with full-backbone ProteinMPNN (vanilla weights, chain A,
`CUDA_VISIBLE_DEVICES=""`) and re-folding:

- Backbone d7 (from batch-01, a 64-res binder): CA-only sequences capped at
  0.248. Full-backbone sequences: **18 members, best ipSAE 0.63–0.85, every
  sequence's 5 folds at the designed site** (cross-protomer contacts to fold
  positions 108 and 68, the problem's B102/D62).
- Fresh sampling (T=0.1 and T=0.3, new seeds): 9 of 10 sequences landed
  0.75–0.85 at the site — the family reproduces, it is not one lucky sample.
- Champion `d7x-t3-3`: five independent folds read 0.832 / 0.837 / 0.840 /
  0.842 / **0.852** — the first entries in the winners' grade (released
  binders score 0.86–0.91 through this same protocol).
- Control backbone d6 stayed ≤0.19 under identical treatment — backbone
  choice dominates; pick backbones by their folded sample spreads first.

The earlier batch-02 backbones under CA-only sequencing topped out at 0.406
(at-site, b2-d4). After the same full-backbone treatment:

- **d12 — a second family**: 0.62–0.83, every sequence 5/5 at the designed
  site, and pDockQ2 0.20–0.30 — four of five members pass the OLD 0.23 pose
  leg as well; d12-2 buries 311 atom pairs (winner size) and d12-3 (0.833)
  passes the calibrated line.
- d15: interfaces of 373–551 atom pairs (beyond the winners' range) at
  0.47–0.69 — more contact is not more confidence.
- d4: 0.25–0.48.

Full table: `genie3/family.csv` — **33 members total** (18 on d7, 15 across
d4/d12/d15), each with sequence, MPNN score, fold spread and interface size.

## The RBS epitope: the fix does not transfer

The same protocol was pointed at our campaign's own epitope (the RBS junction:
1TNF file 84-89 + 143-148 = their B73-78 + D132-137 — a custom problem JSON
reusing the released target files). Genie 3 placed three of twelve designs on
BOTH junction halves with winner-scale contact counts, but all twelve CA-only
folds read 0.000–0.438, and full-backbone redesigns of the three best backbones
(18 more folds) stayed at 0.000–0.653 — with the high scorers moved OFF the
junction. The RBS negative now holds under the fixed protocol too: the junction
surface resists the interface confidence that the benchmark's groove-adjacent
surface yields immediately. Epitope difficulty gates the fix — read the
backbone's at-site fold spread before sequencing anything.

## What this establishes, and what it does not

- Established: our pipeline can produce, robustly and repeatedly, **two
  converging designed families** (d7, d12) whose members sit on the designed
  epitope with interface confidence in the top calibrated band (best 0.852;
  the released binders score 0.86–0.91 in this same protocol); and the two
  errors (CA-only sequencing, singleton sampling) are measured, not guessed.
- Not established: any wet-lab binding. Per the released-campaign calibration,
  the ≥0.8 band bound about 26 % of the time — promising, not a hit.
- pDockQ2: the d7 family reads 0.08–0.16 (under the old 0.23 pose leg) while
  the d12 family reaches 0.20–0.30 — four of its members pass both legs of the
  old bar. The pose leg stays reported, not used as a gate (non-discriminative
  in the calibration).

## Protocol now (carry forward)

1. Generate diverse backbones (Genie 3, ~65 s per design; 16-64 designs).
2. Fold all, then pick backbones by folded spread (majority of samples at the
   designed site, top scores).
3. Re-sequence the picks with FULL-BACKBONE ProteinMPNN; fold 8-16 sequences.
4. Keep only families that reproduce across independent folds; report the
   champion's whole spread, never a single sample.
