# 03 — GLP1R agonist · brief (captured 2026-10-18)

Source: the competition hub + the challenge page
(proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/glp1r).

## The task

Design a **GLP1R agonist**: it must bind human GLP1R **and activate it**.
A binder that does not activate does not count. Submissions close
**Sunday, Oct 25, 23:59 AoE** (~7 days from capture).

## Target information

| field | value |
|---|---|
| Target | Human GLP1R, UniProt P43220-1 |
| Segment | residues 24–432 (409 aa): ECD + 7 TM helices + start of the tail |
| Supply | receptor in DDM/CHS detergent (assay: 13944-H18H-DD, N-FLAG / C-His, proprietary thermostabilising mutations not listed — the public sequence is wild-type) |
| Recommended epitope | the **peptide-binding groove of the extracellular domain** — where GLP-1, exendin-4 and semaglutide dock |
| Structure reference | PDB 6X18, chain R |
| Conditions | none — no species, no pH (unlike challenge 2) |

## How designs are ranked

1. **Affinity** against human GLP1R (binding measured on the detergent receptor).
2. **Activation** — confirmed agonist in a cell-based reporter assay (cAMP →
   secreted alkaline phosphatase → luminescence, compared with untreated cells
   and a reference agonist).

## What this means for the design (first notes)

- The objective is **functional**, not a plain binder. The natural agonist
  mechanism is the ECD closing around the peptide — a miniprotein that docks
  into the peptide-binding groove the way GLP-1 does is the obvious route.
  A pure groove-blocker risks binding without activating.
- The C2 lessons carry over unchanged: full-backbone ProteinMPNN re-sequencing,
  hundreds of backbones not dozens, selection at the designed site, and the
  0.8-line calibration discipline.
- Folding in-silico: the full 409-aa receptor is foldable (Boltz-2, no membrane
  needed); the ECD alone (residues ~24–140 + loops) is the cheaper screen.
- Agonism has no direct in-silico readout in our pipeline — the proxy is
  docking into the peptide groove with the ECD in the closed state. Plan for a
  peptide-mimic scaffold rather than an arbitrary mini-binder.

## Open decisions (before generating anything)

- [ ] modality + scaffold strategy (peptide-mimetic miniprotein vs binder
      scaffold designed into the groove)
- [ ] target construct for screening (full 24–432 vs ECD-only)
- [ ] generation budget + which generator (Genie 3 remains the working one)
- [ ] how to score "activates" in-silico (ECD-closure pose? GLP-1 contact mimicry?)
