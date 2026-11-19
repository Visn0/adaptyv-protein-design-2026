# Evaluation protocol — the final 20 (pre-registered 2026-10-31)

The competition ranks three objectives: (1) specificity, G12D vs WT;
(2) peptide-dependence, no binding to peptide-free MHC; (3) affinity.
The metric benchmark of 2026-10-30 (ProteinBase, 400 measured designs) says:
i_pDAE ranks real interfaces best and consistently (72.5-80% top-decile PPV),
ipTM is strong and model-dependent (45-80%), ipSAE is the weakest (52.5-72.5%).
This protocol uses the strong metrics for the quality axis and keeps ipSAE as
the organizer-aligned record.

## What each stage produces

**Stage 1 — fold confidence (running).** Gate (organizer-aligned, unchanged):
mean peptide ipSAE >= 0.61 over the 5 models. Companion reads, recorded per
design: `iptm_pep` (JDI calibration: the known 425 nM binder reads 0.95;
"JDI-like" means >= 0.8), `ipdae_pep`, `ipdae_hla`, `peptide_share`,
`p6_min_dist`.

**Stage 2 — specificity, tri-state.** The pre-built yamls fold each stage-1
passer against WT pMHC and against peptide-free MHC.
Amendment (2026-10-31, after the stage-1 numbers landed): the gate alone
(9 designs) cannot fill a 20-design submission, so the stage-2 set is the
ipSAE gate passers UNION the JDI band (iptm_pep >= 0.93 AND ipdae_pep >= 0.5)
= 23 designs. The band contains all 9 gate passers.
```
for s in wt free; do
  mkdir -p ~/c5-work/s2-$s/folds
  cp ~/c5-work/s1/folds-$s/*.yaml ~/c5-work/s2-$s/folds/   # passers only
  C0_WORK=~/c5-work/s2-$s MEMLIMIT_MB=12000 \
    bash challenges/05-pmhc/scripts/work/c0-probe-fold.sh all
done
```
The same scorer runs per state (`s1-score.py --work ~/c5-work/s2-wt`), so
every metric above exists for G12D, WT, and free states.

**Stage 3 — finalists.** Multi-seed boltz (3 seeds) + chai-MSA on the top set.
OpenDDE joins only after the JDI acceptance test passes. A design must keep
its rank across seeds to stay in the pick.

## Selection rules for the 20 (in order)

1. **Gates.** Stage-1 gate passed; the fold places the binder on the peptide
   (not on HLA alone): `peptide_share` >= 0.20 or the C3 rule holds.
2. **Vetoes** (C0 says fold-score deltas do not rank — the JDI control read
   the wrong sign — so deltas veto, they do not rank):
   - strong WT preference: `iptm_pep(WT) > iptm_pep(G12D) + 0.05` = drop;
   - strong free-MHC preference: `iptm_pep(free) > iptm_pep(G12D) + 0.05` = drop.
3. **Specificity rank** (objective 1): the C3 electrostatic rule (basic
   nitrogen in a 6-8 A shell over P6-P7) plus peptide-first footprint plus
   ridge engagement (P4-P8 contacts). These are the signals C0 left standing.
4. **Affinity rank** (objective 3): `iptm_pep(G12D)` first, then
   `ipdae_pep(G12D)`, then `peptide_read` (ipSAE). No ensembles or votes —
   the benchmark shows consensus adds nothing, and C0 agrees.
5. **Diversity cap** for the submission: at most 2-3 designs per generation
   family (wave/run group), and pairwise sequence identity below ~70% inside
   the final 20. The submission needs 20 distinct designs, not 20 siblings.
6. **Sequence checks, recorded per design:** length inside 10-250 (ours are
   60-110); de novo by construction, confirmed with a quick mmseqs screen
   against SwissProt; liability motifs recorded (free cysteines, N-glyc
   sequons NxS/T, long homopolymer runs).

## The record

`s1-scores.csv` + `s1-summary.csv` per stage hold every read. The campaign
record (`campaigns/`) keeps the pre-registration, the amendments, and the
final pick with its full read table for the write-up.
