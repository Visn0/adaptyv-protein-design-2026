# 05 — KRAS G12D pMHC binder · brief (captured 2026-10-30)

Source: the challenge page
(proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/pmhc) + the hub.
Full page text: `references/proteinbase-pmhc-capture-2026-10-30.md`.
Target payload (sequences, structure files): `references/pmhc-targets-2026-10-30.json`.

## The task

Design a **mutation-specific pMHC binder**. Bind the KRAS G12D peptide
VVVGADGVGK (KRAS residues 7–16) presented in the groove of HLA-A*11:01 with
β2-microglobulin. Do not bind the wild-type peptide complex (VVVGAGGVGK — one
position different) and do not bind the peptide-free MHC. Submissions close
**Sunday, November 8, 23:59 AoE** (window Oct 26 – Nov 8).

## Target information

| field | value |
|---|---|
| Target | KRAS G12D peptide on HLA-A*11:01, with β2-microglobulin — a three-chain complex |
| Heavy chain | HLA-A*11:01, UniProt Q5S3G3, residues 25–305 |
| β2-microglobulin | UniProt P61769, residues 21–119 |
| G12D peptide | VVVGADGVGK · KRAS (P01116) residues 7–16 · position 6 = Asp (KRAS residue 12) |
| Wild-type peptide | VVVGAGGVGK · position 6 = Gly |
| Allele | A*11:01:01:01 · IPD-IMGT/HLA HLA00043 |
| Assay construct | complex of the three chains · tags not shown |
| Recommended epitope | the peptide and the groove around it (the surface a T-cell receptor reads) |
| Structure reference | 7OW6 (G12D + TCR) · 7OW5 (wild type + TCR; Poole et al., Nat Commun 2022) · 7OW4 (G12D, no TCR) |
| Conditions | all three targets, same conditions · design immobilised, target in solution |

The organizers provide prepared PDB files for the three states; they are in
`inputs/`. The heavy chain in them is renumbered 1–276 (map before choosing
hotspots), and the peptide carries full sidechains — including the position-6
aspartate. The two peptides differ at exactly one position of ten, and that
position sits in the mobile middle of the peptide.

## How designs are ranked

1. **Mutation specificity** — a measurable KD against the G12D complex and no
   detectable binding to the wild-type complex. Designs that bind both rank
   after these, by the KD ratio (wild type / G12D), largest first.
2. **Peptide-dependent binding** — a measurable KD against the G12D complex and
   no detectable binding to the peptide-free MHC. Designs that bind it rank
   after these, by the KD ratio (peptide-free / G12D), largest first.
3. **Affinity** — lowest KD against the G12D complex. Naming the targeted
   surface and linking the evidence counts in the design's favour.

A design counts as binding a target when its sensorgram gives a fittable curve
and a KD, or — where the curve cannot be fitted — when the association shift
clears 300% over the negative control. The winner clears all three steps.
Each step also awards an honourable mention.

## Sequence constraints

De novo only. 10–250 aa per chain. Single-chain protein, nanobody, scFv, or
Fab. Up to 20 designs for Tracks 2 and 3 (up to 40 for Track 1).

## What this means for the design (first notes)

- The target is **soluble** (no membrane in the construct): neither the
  insertion-depth metric nor the membrane-space check applies (the day-1
  decision, `../README.md`).
- Single-residue discrimination is the whole problem: the two peptide
  complexes differ only at peptide position 6, and the MHC surface is
  identical in all three states. A binder that reads the HLA or the
  β2-microglobulin framework fails by construction.
- The counter-targets are built in: every candidate can be folded against all
  three states and compared — interface scores plus contacts at position 6.
- The provided files carry the position-6 aspartate with full sidechain
  coordinates; 7OW4 (the receptor-free crystal) does not. Fold against the
  provided files, not the bare RCSB entry.
