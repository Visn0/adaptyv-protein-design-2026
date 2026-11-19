# Multi-chain binders — references and evaluation tooling (2026-10-26)

Research pass requested after the c5 pilot (see `README.md`). Scope: what
the field knows about binders at our epitope, what is special about multi-chain
design, and which tools genuinely evaluate a two-chain unit better than a single
ipTM number.

## 1. Known binders at the apical patch

**The virus (the challenge's native control).** The TfR1-VP1u complex was solved
by cryo-EM at 2.4 A; the VP1u receptor-binding domain contacts the apical domain
mainly through the betaII-1-betaII-2 loop and betaII-2 strand (residues
208-212), plus I202, K371 and N348, and **two VP1u RBDs bind, one to each
apical domain of the receptor dimer**.[18] Measured affinities: 128 nM (VP1u,
BLI) and 86 nM (RBD); the paper's PRODIGY prediction is about 1 uM.[18] The
organizers' recommended patch - "around Tyr211 (residues 202-215, 348 and
371)" - matches this interface, and the challenge page confirms the receptor is
supplied as a homodimer, so **each target presents two copies of the
epitope**.[10]

**Antibodies and natural ligands.** OKT9-class antibodies block VP1u binding
and uptake.[18] Human ferritin, a natural TfR1 ligand, binds the apical domain
and blocks VP1u as well.[17] Transferrin itself binds the helical domain
(residues 619-670) and only grazes the apical domain of the partner
subunit.[10]

**Designed binders - the closest published relatives of our campaign.**
Sahtoe et al. 2021 designed small proteins against the exposed beta-sheet edge
of the hTfR apical domain by "sheet extension" (PDB 6WRV/6WRW/6WRX); the lead
design **2DS25 binds at 20 nM, is hyperstable, and crosses an in vitro
blood-brain-barrier model**.[22][23][24] The challenge page itself cites "the
designed binders of 6WRV" as landing on the same patch.[10] Our E0 set (204,
208, 210, 211, 348, 371) overlaps this exact region; E12 (344, 374) is the
adjacent dual-lysine anchor.

**Antibody shuttles (engineering lessons).** The Brain Shuttle work established
that **monovalent binding to TfR1 transcytoses more efficiently** than bivalent
engagement, which clusters receptors.[16] Trontinemab carries a TfR1 module in
a "2+1" format precisely to keep TfR1 binding monovalent while the cargo arm
stays bivalent.[3][6] Pabinafusp alfa (JR-141) is an anti-TfR IgG-enzyme fusion
that deliberately does not disrupt transferrin binding.[15] A 2025 study
nuances the monovalent rule (bivalent can be effective in some profiles) and
shows serotransferrin supplementation boosts uptake.[19][20]

**Mouse.** The apical patch differs between human and mouse at six of nine
positions (D204, R208, V210, Y211, N348, K371 become Q207, N211, D213, P214,
K350, Q373), which is why TfR1 binders are so often species-specific.[10] This
is the known mechanism behind the C4 cross-fold result.

## 2. What is genuinely different about multi-chain design

**The generator can do it.** RFdiffusion3 - the model family behind the hosted
RFD4 route - designs "protein monomers, assemblies, and protein-binding
proteins", so multi-chain generation is a supported mode, not a hack.[7][8][9]

**Pairing is a designed property, and we have not designed it.** The antibody
engineering literature treats interface specificity as a multistate problem:
the heterodimer must beat both homodimers (negative design; negative-state
repertoires; combYSelect IgG heterodimers).[13][14] The c5 chains were
generated jointly so the B-C interface should be complementary, but
**nothing penalised B-B or C-C pairing**: a co-expressed two-chain unit in
which one chain can homodimerise loses active unit to a competing species.
That is a real, checkable risk we have not measured.

**Submission format is a constraint we must plan around.** The competition
accepts single-chain proteins, nanobodies, scFv and Fab formats, with a 250 aa
cap for single-chain entries and design caps of 40 (Track 1) / 20 (Tracks 2-3)
per challenge.[10] A de novo two-chain unit fits none of these cleanly, so an
c5 submission (if it ever happens) would need a **linker fusion** joining B
and C into one chain (B+C+linker stays well under 250 aa). The fold currently
validates the unlinked unit.

## 3. Evaluation tooling: what a two-chain unit needs that ipTM cannot give

Single ipTM conflates every interface in the complex. The literature-native
answers:

| Tool | Read | Status for us |
|---|---|---|
| chai `per_chain_pair_iptm` + `chain_chain_clashes` (npz) | per-pair interface confidence + steric clashes | **native** - already produced by every restrained fold; now extracted per pair |
| DockQ v2 | per-interface quality vs the design model (f_nat, iRMSD, LRMSD; automatic chain mapping for multimers) | **installed and verified**: e12rfd4_r4d5 fold vs its design model scored 0.897 total, iRMSD 0.55 A |
| PRODIGY | dG / Kd per interface group; multi-chain groups supported (e.g. interactor "B,C") | **installed and calibrated**: on the native 11RN interface it predicts 1.3-1.7 uM, matching the published PRODIGY value of about 1 uM |
| ipSAE (per chain pair, directional) | PAE-based interface score | needs a PAE source; chai's npz carries no PAE, so per-pair ipSAE requires a secondary Boltz-2 fold of the shortlist |
| Boltz-2 affinity head | - | **not applicable**: it only scores small-molecule ligands, not protein-protein pairs |

DockQ v2 is a pure-Python rewrite that scores every interface of a multimer
with automatic chain mapping.[1][2] PRODIGY predicts dG and Kd from
intermolecular contacts and accepts multi-chain interactor groups.[11][12] The
per-chain-pair readings of ipSAE are directional by design and are the
recommended multi-interface read where PAE exists.[4][5] Boltz-2's affinity
module cannot contribute here because it only covers small-molecule
ligands.[21]

The calibration points matter: PRODIGY reproduced the published number on 11RN
within a factor of ~1.7,[18] and DockQ against the design model quantifies
exactly the question "did the fold reproduce the designed interface".

## 4. What was built from this research

`scripts/work/c5-restrained-scores.py`: for every fold sample it
records global ipTM, the full per-chain-pair ipTM matrix, per-pair clash counts,
PRODIGY dG/Kd for the unit and for each pair, DockQ vs the design model, and
anchor-contact counts per chain. It runs the moment the c5 folds land.

## 5. Takeaways

- Three known binder families sit at our patch: the virus (VP1u), antibodies,
  and the 2021 designed `2DS25` family; the natural binder's "multivalency" is
  the receptor dimer presenting two epitope copies, not a two-chain unit.[10][18][23]
- A designed two-chain unit at this target is not a published format; the risk
  it adds is chain pairing, which the field handles with negative design.[13][14]
- The evaluation upgrade is real and mostly free: per-pair ipTM and clashes
  already exist in every chai fold; DockQ and PRODIGY close the remaining gap.

[^1]: https://academic.oup.com/bioinformatics/article/40/10/btae586/7796530 — DockQ v2 (Mirabello & Wallner, Bioinformatics 2024)
[^2]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11467047 — DockQ v2 full text (PMC)
[^3]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10572082 — Trontinemab Brainshuttle delivery (PMC)
[^4]: https://github.com/dunbracklab/IPSAE — DunbrackLab ipSAE (GitHub)
[^5]: https://www.biorxiv.org/content/10.1101/2025.02.10.637595v2.full — Res ipSAE loquuntur (bioRxiv 2025)
[^6]: https://clinicaltrials.gov/study/NCT04639050 — Brainshuttle AD trial (NCT04639050)
[^7]: https://www.biorxiv.org/content/10.1101/2025.09.18.676967v2 — RFdiffusion3 (bioRxiv 2025)
[^8]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12458353 — RFD3 PMC full text
[^9]: https://www.ipd.uw.edu/2025/12/rfdiffusion3-now-available — IPD: RFdiffusion3 release
[^10]: https://proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/tfr1 — Proteinbase Challenge 04 TfR1 page
[^11]: https://wenmr.science.uu.nl/prodigy/manual — PRODIGY manual (Bonvin lab)
[^12]: https://github.com/haddocking/prodigy — PRODIGY standalone (GitHub)
[^13]: https://www.cell.com/structure/fulltext/S0969-2126(16)00072-1 — Bispecific antibodies via negative state repertoires (Structure 2016)
[^14]: https://doi.org/10.1126/sciadv.adk8157 — combYSelect IgG heterodimers (Sci Adv)
[^15]: https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(20)30496-2 — Pabinafusp alfa phase 2/3 (Mol Ther 2020)
[^16]: https://www.cell.com/neuron/fulltext/S0896-6273(13)01035-0 — Monovalent Brain Shuttle (Neuron 2013)
[^17]: https://journals.asm.org/doi/10.1128/mbio.01482-26 — hTfR as B19V co-receptor (mBio)
[^18]: https://www.nature.com/articles/s41467-026-74283-7 — TfR1 binds B19V VP1u (Nat Commun 2026)
[^19]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12952256 — Anti-TfR1 antibody balance (mAbs 2025)
[^20]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12350589 — Serotransferrin enhances TfR uptake
[^21]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12262699 — Boltz-2 affinity (PMC)
[^22]: https://www.rcsb.org/structure/6wrv — PDB 6WRV (3DS18-hTfR complex)
[^23]: https://www.pnas.org/doi/full/10.1073/pnas.2021569118 — Sahtoe PNAS 2021 sheet extension
[^24]: https://pmc.ncbi.nlm.nih.gov/articles/PMC8092486 — Sahtoe PNAS full text (PMC)

## Sources

[1] https://academic.oup.com/bioinformatics/article/40/10/btae586/7796530 — DockQ v2 (Mirabello & Wallner, Bioinformatics 2024)
[2] https://pmc.ncbi.nlm.nih.gov/articles/PMC11467047 — DockQ v2 full text (PMC)
[3] https://pmc.ncbi.nlm.nih.gov/articles/PMC10572082 — Trontinemab Brainshuttle delivery (PMC)
[4] https://github.com/dunbracklab/IPSAE — DunbrackLab ipSAE (GitHub)
[5] https://www.biorxiv.org/content/10.1101/2025.02.10.637595v2.full — Res ipSAE loquuntur (bioRxiv 2025)
[6] https://clinicaltrials.gov/study/NCT04639050 — Brainshuttle AD trial (NCT04639050)
[7] https://www.biorxiv.org/content/10.1101/2025.09.18.676967v2 — RFdiffusion3 (bioRxiv 2025)
[8] https://pmc.ncbi.nlm.nih.gov/articles/PMC12458353 — RFD3 PMC full text
[9] https://www.ipd.uw.edu/2025/12/rfdiffusion3-now-available — IPD: RFdiffusion3 release
[10] https://proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/tfr1 — Proteinbase Challenge 04 TfR1 page
[11] https://wenmr.science.uu.nl/prodigy/manual — PRODIGY manual (Bonvin lab)
[12] https://github.com/haddocking/prodigy — PRODIGY standalone (GitHub)
[13] https://www.cell.com/structure/fulltext/S0969-2126(16)00072-1 — Bispecific antibodies via negative state repertoires (Structure 2016)
[14] https://doi.org/10.1126/sciadv.adk8157 — combYSelect IgG heterodimers (Sci Adv)
[15] https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(20)30496-2 — Pabinafusp alfa phase 2/3 (Mol Ther 2020)
[16] https://www.cell.com/neuron/fulltext/S0896-6273(13)01035-0 — Monovalent Brain Shuttle (Neuron 2013)
[17] https://journals.asm.org/doi/10.1128/mbio.01482-26 — hTfR as B19V co-receptor (mBio)
[18] https://www.nature.com/articles/s41467-026-74283-7 — TfR1 binds B19V VP1u (Nat Commun 2026)
[19] https://pmc.ncbi.nlm.nih.gov/articles/PMC12952256 — Anti-TfR1 antibody balance (mAbs 2025)
[20] https://pmc.ncbi.nlm.nih.gov/articles/PMC12350589 — Serotransferrin enhances TfR uptake
[21] https://pmc.ncbi.nlm.nih.gov/articles/PMC12262699 — Boltz-2 affinity (PMC)
[22] https://www.rcsb.org/structure/6wrv — PDB 6WRV (3DS18-hTfR complex)
[23] https://www.pnas.org/doi/full/10.1073/pnas.2021569118 — Sahtoe PNAS 2021 sheet extension
[24] https://pmc.ncbi.nlm.nih.gov/articles/PMC8092486 — Sahtoe PNAS full text (PMC)
