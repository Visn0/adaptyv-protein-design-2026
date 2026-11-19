# Design method — as entered on the submission page

Method name: **Peptide-ridge de novo minibinders with an electrostatic
specificity rule**

## Description (general pipeline / reasoning)

The target is a peptide–MHC complex: the KRAS G12D peptide VVVGADGVGK
presented by HLA-A*11:01 + β2-microglobulin. The mutated aspartate at P6 is
buried in the groove (about 10% exposed), salt-bridged to HLA R114 and
hydrogen-bonded to Q70 — a single extra negative charge that changes the
electrostatic field above the peptide ridge without changing the peptide's
shape. The published JDI TCR gains its >4000× mutant/WT window by reading
that field indirectly, not by touching the aspartate, and this project
follows the same principle: every design must arc over the peptide ridge
(P4–P8) and place a basic nitrogen in the 6–8 Å shell above P6/P7, so the
mutant's field is read through electrostatics rather than shape.

Designs come from the hosted RFdiffusion4 NIM, conditioned on the peptide
ridge, across multiple sampling waves and targeted campaigns (peptide-only
mining, natural-reader hotspots measured from the real JDI TCR crystal,
charge-first and minibinder length variants) — plus, near the end, the same
model re-hosted locally (RFD4-Proteina, BSD-3) at confirmed parity. Every
backbone passes a geometry screen before sequence assignment, is sequenced
with ProteinMPNN (with a LigandMPNN surface-redesign pass on the finalists),
folded with Boltz-2 (five models per design) and scored with ipTM, ipSAE and
i_pDAE. The final champions additionally passed through a guided evolution
loop (charge-directed repair rounds plus automated mutation generations,
promoting only variants that clear a strict composite margin with intact
fold quality).

Specificity is then measured, not assumed: every candidate is folded in a
three-state panel — mutant complex, wild-type complex, peptide-free MHC —
and ranked on wild-type discrimination and free-state dependence, with
vetoes for designs that read better on the wrong state. The panel was
calibrated against the organizers' own crystal structures and a known-good
control (the JDI TCR) before any design was ranked; fold-score deltas alone
cannot separate the single-point mutation, so the electrostatic interaction
rules and the three-state panel carry the specificity signal. Finalists get
three-seed stability folds (spread ≤ 0.04), Chai-1 MSA cross-checks,
binder-alone folds (pLDDT ≥ 0.93) and a de-novo eligibility screen against
SwissProt (any hit ≥ 90% identity excludes the design).

The submitted nineteen mix eight campaign parents with eleven
evolution/repair children (charge-directed single-point swaps and the
automated mutation loop). Sixteen of the nineteen clear the organizer's ipSAE
gate (peptide_read >= 0.61); the three below it are kept on measured
specificity, and the one entry that failed both the gate and the wild-type
read was dropped on 2026-11-08
(`../records/final-cut-2026-11-08.md`). The strongest reads: wild-type
separation up to 0.67 (N71K), mutant-preference dWT up to +0.747 and
peptide-free dependence dfree up to +0.766 (the L58K-Q15K champion). All
are 64–98 aa, homology-screened, and fifteen carry a negative E-score;
four entries are retained on their other validated axes.
