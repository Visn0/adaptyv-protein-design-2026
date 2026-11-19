# Stage 1 record — fold confidence over the 239-design shortlist

Run: 2026-10-31, boltz-2, 5 models per design, `~/c5-work/s1`.
Files: `stage1-shortlist.csv` (all 239, joined with the pose screen),
`stage1-stage2-set.csv` (the 23 that move to stage 2).

## Numbers

- 239/239 designs folded (the marathon paused at 118, resumed after the
  19:18 host reboot; the 18 pre-pause memory-cap kills were all re-folded at
  the raised 12 GB cap, zero new kills).
- 9 designs pass the pre-registered organizer-aligned gate
  (mean peptide ipSAE >= 0.61).
- 59 designs are JDI-like (mean peptide ipTM >= 0.8; the JDI control, a real
  425 nM binder, reads 0.95); 38 read >= 0.9.

## Stage-2 set (amendment, recorded)

The gate alone (9) cannot fill a 20-design submission. Documented widening:
**stage-2 set = ipSAE gate passers UNION (iptm_pep >= 0.93 AND
ipdae_pep >= 0.5)**. Result: 23 designs, ipTM 0.931-0.975. The band already
contains all 9 gate passers, so the set is exactly the band.

## The convergence finding

All 23 stage-2 designs are flagged `c3=True` AND `peptide_first=True` in the
s0 generator-pose screen. Two independent evidence streams — generator-pose
geometry (C3 electrostatic rule + footprint) and folded-interface confidence
(i_pDAE + ipTM, benchmark-validated) — agree on this set with no exceptions.
This is the strongest cross-instrument agreement the campaign has produced.

## Next

Stage 2: fold the 23 against WT pMHC and peptide-free MHC (46 folds, ~1.5 h),
score with the same scorer, then apply the pre-registered selection rules
(`notes/evaluation-protocol.md`) including the delta vetoes.
