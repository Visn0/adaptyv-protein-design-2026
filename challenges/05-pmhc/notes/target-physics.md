# C5 target physics — the measured physical/chemical reading (2026-10-30)

Why this file exists: challenge 3 shipped a pipeline blind to the physical
context of its target (the membrane), caught after the fact. This file measures
the physical and chemical context of the KRAS G12D pMHC target before any
design work. Every number here is measured on the committed files.

Reproduce with:

    .venv/bin/python challenges/05-pmhc/scripts/target_physics.py

Outputs: `notes/target-physics.csv` (per-residue table),
`notes/references/target-physics.json` (all metrics).

## The files, and what they are

- The three organizer files are direct derivations of the RCSB entries with
  parts deleted: the G12D file equals 7OW6 minus the TCR (heavy-chain CA RMSD
  0.0, identical B-factors), the WT file equals 7OW5 minus the TCR, and the
  peptide-free file equals the G12D file minus the peptide. **The peptide-free
  file is a deletion model: it encodes no conformational change of the empty
  groove.** The real empty-MHC species is a separate question (literature
  pass in the scout reports).
- Numbering: the heavy chain runs 1–276 in these files; the challenge page's
  "Arg114 and Gln70" use this numbering. This file uses it too.

## The peptide: what a binder can read, and what it cannot

| pos | aa | exposure | HLA contacts | note |
|----|----|----------|--------------|------|
| P1 | V | 0.6% | 40 | buried anchor |
| P2 | V | 1.5% | 23 | buried anchor (B pocket) |
| P3 | V | 4.6% | 17 | buried |
| P4 | G | 58% | 1 | readable |
| P5 | A | 27% | 9 | partly readable |
| P6 | D | 18% (sidechain 10%) | 19 | the mutation; sidechain buried |
| P7 | G | 84% | 2 | most readable |
| P8 | V | 38% | 6 | readable |
| P9 | G | 28% | 9 | partly readable |
| P10 | K | 2.6% | 42 | buried anchor (F pocket) |

(Exposure = residue SASA in the complex ÷ SASA of the same residue alone;
contacts = heavy-atom pairs under 4.0 Å with the heavy chain and β2m.)

- The readable ridge is P4–P8; the two ends are anchor positions that a
  binder cannot use.
- The JDI TCR reads exactly this ridge: 275 contacts under 4.5 Å, 20% of them
  on the peptide, concentrated on P7 (32), then P8 (9), P6 (5), P5 (4),
  P4 (2); the rest spread over both HLA helices. The TCR footprint is the
  template for a peptide-first binder footprint.

## The buried aspartate (reproduces the published numbers)

- P6 sidechain exposure: **8.8 Å² (10.4% of free)** — the carboxylate is
  ~90% buried. This independently reproduces the public measurement
  (rpinho, 2026-10-27: SASA 8.8 Å²).
- OD2–R114 NH2: **2.95 Å** (salt bridge). OD2–Q70 NE2: **3.08 Å** (hydrogen
  bond). R114 NE–D116 OD1: **2.81 Å** (second shell — D116 holds R114 in
  place). Matches Poole et al. 2022 and the challenge page's note.
- The closest JDI TCR atom to the D6 carboxylate sits **7.51 Å** away
  (reproduces the public 7.5 Å number). The mutation is read through the
  field it creates, not by contact.
- B-factors in the bound complex: peptide residues 73.5–89.0, mean ≈ 79,
  against a heavy-chain mean of 96.1. P6 is the LOWEST (73.5) — in the
  TCR-bound state the mutated position is the most ordered part of the
  peptide. Mobility lives in the unbound state (next section).

## The peptide moves — design against the bound (closed) state

- In the receptor-free G12D crystal (7OW4), residues P5 and P6 have **no
  coordinates at all**, and the modeled residues shift after HLA
  superposition: P7 by 3.15 Å, P8 by 1.71 Å, P4 by 1.42 Å (HLA CA RMSD
  between the two crystal forms 0.9 Å).
- The central and right half of the peptide is the flexible part. The assays
  and the reference binder (the TCR) see the bound conformation — design and
  screen against it (the provided G12D file).
- The WT complex with the same TCR docks almost identically (279 contacts,
  same peptide positions). The G12D/WT difference is not a large
  conformational read; it is fine energetics. Consistent with the AF2
  control result (ipTM 0.84 on both states) and with Poole et al. 2022.

## The peptide-free target: what the deletion exposes (objective 2)

- Deleting the peptide exposes **678 Å²** of new HLA surface: the groove
  floor and the helix rims. Top contributors (heavy-chain numbering):
  155, 147, 66, 159, 77, 70, 146, 73, 63, 9, 99, 114, 150, 156, 163.
- Design rule: a binder that grabs any of these surfaces binds all three
  targets (it fails objective 2). The footprint must sit ON the peptide
  ridge and must NOT reach down the groove walls.
- Caveat: the real peptide-free sample is metastable (empty MHC-I is
  unstable); the deletion model cannot prove non-binding. Treat
  "peptide-first footprint" as the design constraint, and read the
  literature before trusting any claim about the empty state.

## Electrostatics: the only G12D-specific signal

- The mutant adds one negative charge (the D6 carboxylate, ~90% buried).
  The WT peptide carries no equivalent.
- Debye–Hückel estimate of that charge's field above the groove (the
  G12D-minus-WT difference field; distances from the D6 CG atom, along the
  axis from the peptide toward the TCR):

| local dielectric | 6 Å | 7 Å | 8 Å |
|---|---|---|---|
| ε = 10 | −4.3 | −3.3 | −2.6 kT/e |
| ε = 20 | −2.2 | −1.7 | −1.3 kT/e |
| ε = 40 | −1.1 | −0.8 | −0.7 kT/e |
| ε = 80 | −0.5 | −0.4 | −0.3 kT/e |

  A 7×7 Å lateral sweep at 7 Å above P6–P7 with ε = 20 reads −0.8 to
  −1.7 kT/e depending on position.
- Direction: negative — **a cation (Arg/Lys/His) placed 6–8 Å above P6–P7
  gains a favorable interaction in the G12D state only.** The public APBS
  analysis measured the same difference map at up to 8.4 kT/e; the numbers
  differ because this estimate uses a uniform dielectric and point charges,
  but the sign and the location (epicentre P6–P7) agree.
- Caveat: this is an order-of-magnitude estimate, not a free-energy
  calculation. The salt bridge to R114 reduces the free charge, and the
  local dielectric is unknown. Use it for placement decisions, not ranking.

## Waters and desolvation

- 7OW6 models only 18 waters, none within 7 Å of the peptide (minimum
  6.97 Å). This is a deposition choice, not evidence about hydration. The
  other KRAS structures model more solvent: 7OW4 has 10 waters within 4 Å of
  the peptide (of 1009 modelled), 9UV8 has 23 (of 326). The real interface is
  solvated.
- The deep dive documents the physics: the groove carries a conserved water
  network (63 conserved clusters across 12 high-resolution MHC-I structures;
  Ogata & Wodak 2002); MD finds 14 long-lived waters at the HLA-A2/peptide
  interface that enhance affinity without adding specificity (Petrone &
  Garcia 2004); the central peptide of an HLA-A1 complex is loosely bound and
  stabilized by water-mediated contacts (JBC 2020). For single-residue
  discrimination the published energetic analysis is the p53 R175H TCR 6-11
  case: 1.5 of 1.6 REU of the WT-vs-mutant difference came from desolvating
  the P8 side chain, with no direct contacts to the mutation (Wu, Gowthaman,
  Pierce, Mariuzza, JBC 2022). The TCR-mimic antibody H2 in the same system
  is the counter-example: it reads its mutation by direct contacts (6W51).
- Design consequence: score candidates with an explicit desolvation term and
  treat water as part of the interface. No ordered water is available as an
  anchor in the provided files.

## Assay physics (the context the binder meets)

- The design is immobilised through a C-terminal Twin-Strep capture tag and
  the target is in solution. Keep the C-terminus away from the interface.
- The complexes carry His and Avi tags (not shown in the files); binding to
  a tag does not count. The binder must not grip tag regions.
- All three targets are measured in the same conditions; binding = a
  fittable KD or a 300% association shift over the negative control.

## The physical/chemical checklist for our designs (the C3 lesson applied)

Measured here:

1. Readable surface = the P4–P8 ridge. Never design against the anchors
   (P1–P3, P9–P10). [measured]
2. The G12D signal is electrostatic: a buried charge and its field. The
   shape difference (Asp vs Gly) is one methylene-sized group. [measured]
3. Design and screen against the receptor-bound peptide conformation; the
   unbound middle is disordered. [measured]
4. Footprint discipline: contacts must be peptide-first; no groove-floor or
   helix contacts that would survive the peptide's absence. [measured]
5. A positive charge above P6–P7 is the cheap specificity handle.
   [measured estimate]
6. The counter-targets are cheap: fold every candidate against all three
   states (same files). [method]

Added by the deep dive (2026-10-30; full detail in `deep-physics.md`):

7. Expect induced fit and pay for entropy: binding rigidifies the mobile
   bulge (measured TΔS −8.1 vs −1.8 kcal/mol for G12D vs WT with the
   matured JDI). Design to stabilize the preferred bulge or to exploit a
   rigid segment. [Poole 2022]
8. Never target the 9-mer register (VVGADGVGK — Asp at P5, flattened and
   non-productive; its Asp never reaches R114, 7.1 Å). Our target is the
   10-mer (Asp at P6, bulged). Do not copy hotspot numbers from the public
   9-mer work. [Zhu 2025; measured]
9. Score desolvation explicitly and treat water as interface: the groove
   water network is conserved and affinity-enhancing, and the best-studied
   single-residue discrimination case (p53 R175H, TCR 6-11) is decided by a
   desolvation penalty, not by contacts. [Wu 2022; Ogata & Wodak 2002;
   Petrone & Garcia 2004]
10. The peptide-free target is metastable, heterogeneous and
    peptide-scavenging (empty MHC-I is unlocked/partially collapsed; RMA-S
    "empty" molecules carry low-affinity peptides). Prefer designs whose
    binding REQUIRES the peptide atoms, and read any peptide-free binding
    cautiously. [Zacharias & Springer 2004; Anjanappa 2020; De Silva 1999;
    2026 cryo-EM]
11. The N86 glycan is off-footprint: its attachment point sits ~15 Å from
    the peptide axis and 18.6 Å from the nearest JDI atom, and the KRAS
    reagents are E. coli-refolded (aglycosylated). A JDI-like footprint
    over P4–P7 is physically compatible. [measured + Zhu 2025]
12. Do not rely on anchor differences: the N-/C-terminal anchor networks are
    identical between mutant and WT. All discrimination lives in the middle
    of the peptide. [Chujoh 1998; Zhu 2025]
13. nM affinity suffices; the KD(WT)/KD(G12D) window matters more than
    absolute affinity. Maturation with WT-depletion widened the JDI window
    (98× → >6000×); mid-affinity TCRm clones commonly pick up peptide-free
    binding — counter-select against it from the first round. [Poole 2022;
    Ahn 2026 (C8K10D); Robertson 2024]
