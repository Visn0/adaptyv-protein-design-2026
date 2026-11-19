# 04 — TfR1 conditional binder · strategies (written 2026-10-23, before any generation)

Companion documents: `brief.md` (the task), `epitope-analysis.md` (the
measurements this plan rests on), `lessons-c2-c3.md` (the rules carried forward).
Campaign plans are in `../campaigns/`.

Window: **2026-10-19 to 2026-11-01, 23:59 AoE**. Nine working days remain.

## 1. The problem, restated

Three objectives, hardest first.

| # | objective | what it needs |
|---|---|---|
| 1 | pH switch | a measurable KD against human TfR1 at pH 7.4 and no detectable binding at pH 6.0 |
| 2 | mouse cross-reactivity | a mouse-to-human KD ratio near 1, with human KD below 1 uM |
| 3 | affinity | the lowest human KD at pH 7.4, at a named functional epitope |

Objective 1 is the same direction as challenge 2: hold at 7.4, release at 6.0.
Challenge 2 produced no submission at all, and its switch work was never started.
Objective 1 is therefore the part of this challenge with no prior art in this
repo.

## 2. What the measurements changed

Four findings from `epitope-analysis.md` drive every decision below.

1. **The recommended patch is the least cross-reactive surface on the protein.**
   All six named residues (204, 208, 210, 211, 348, 371) are either substituted
   in mouse or fall in an indel. Zero are conserved. Designing there optimises
   for human specificity, which is the opposite of objective 2.
2. **A conserved, exposed face sits next to it.** Ten residues in the same
   neighbourhood are identical in mouse and solvent exposed. They sit 5.7 to
   21.7 A from Tyr211 and all fall inside the apical domain, so they still
   satisfy the organizers' apical-domain hint.
3. **The target has no histidine at this epitope.** The entire pH switch must be
   built on the binder. The conserved exposed cations 344 K and 374 K are the
   anchors that give the asked direction. The conserved glutamates 343 E and
   350 E would invert it.
4. **The N251 glycan is conserved and adjacent.** It eliminates 231 K from the
   usable set and requires a footprint screen.

## 3. The central hypothesis

> A binder placed on the **conserved, glycan-clear face of the apical domain**,
> carrying **two or three histidines facing a conserved target lysine**, can
> serve objectives 1 and 2 with the same interface: the epitope is identical in
> both species, so cross-reactivity follows from the epitope choice, and the
> switch follows from like-charge repulsion that appears as the histidines
> protonate near pH 6.

This is falsifiable at three points, and each has a pre-registered discard rule
in the campaign plans: the conserved face may not dock at all (campaign 1), the
histidines may destroy binding (campaign 3), and the linkage sign may come out
negative as it did in challenge 2 (campaign 3).

## 4. The epitope sets

| set | residues (human 11QC numbering) | span | conserved in mouse | glycan clearance | serves |
|---|---|---|---|---|---|
| **E0** named tip | 204, 208, 210, 211, 348, 371 | 15.7 A | 0 of 6 | 11.2 A | objective 3 |
| **E1** north | 206, 207, 209, 374 | 11.8 A | 4 of 4 | 13.9 A | objectives 1, 2, 3 |
| **E2** south | 343, 344, 347, 350, 351 | 14.9 A | 5 of 5 | 16.2 A | objectives 1, 2, 3 |

E1 carries the conserved cation 374 K. E2 carries 344 K and is furthest from the
glycan. E0 is the organizers' literal hint and the set most likely to dock,
because it is the surface their own structure reference shows being bound.

## 5. The strategies, prioritised

### S1 — Conserved-face binder with an engineered histidine switch · PRIMARY
*Campaigns 2 and 3.*

Generate de-novo miniproteins on E1 and E2. Establish binding first, then
install histidines facing 374 K or 344 K and keep only designs whose binding
survives and whose linkage sign is positive.

- Tools: Genie 3 as primary generator, RFD4-Proteina as co-primary,
  full-backbone ProteinMPNN and SolubleMPNN for sequences, Boltz-2 for folds,
  IPSAE for interface scores, `tools/switch/linkage_score.py` for the switch.
- Why first: it is the only route where one interface serves the two hardest
  objectives at once, and the epitope choice is measured rather than assumed.
- Why Genie 3: on Anthropic's released TNF-alpha campaign, with real wet-lab
  outcomes, Genie 3 bound 8 of 23 against RFdiffusion3's 1 of 40. It is
  installed and it placed 8 of 8 designs on a specified epitope on this box.
- Why RFD4 alongside: it produced 17 of the 20 designs in the challenge-3
  submission. NVIDIA's hosted pool is free until 2026-11-04, which covers this
  whole window, and the request builder already exists at `nim/build_request.py`.

### S2 — Named-tip affinity binder · INSURANCE
*Campaign 2, second arm.*

The same pipeline on E0. Human-specific by construction, so it serves objective 3
only.

- Why keep it: challenge 2's hardest lesson was that epitope difficulty gates
  everything. The same protocol that produced two good families on an easy
  surface produced nothing on a hard junction. E0 is the surface the organizers
  point at, so it is the most likely to dock. If E1 and E2 both resist, E0 is the
  difference between a submission and another recorded negative.
- It also gives the submission an internal contrast: a human-only tight binder
  beside cross-reactive ones.

### S3 — Histidine-biased sequence design · PARALLEL TO S1
*Campaign 3.*

Rather than only retrofitting histidines onto finished sequences, bias the
inverse-folding step toward histidine at interface positions facing the target
cation, using ProteinMPNN's per-residue amino-acid bias.

- Why: challenge 3's clearest methodological finding was that a screen can only
  discard, never supply a feature the generator never produced. The switch is
  such a feature.
- Risk: biasing a buried or structurally important position costs binding. The
  bias is therefore applied only to positions whose side chain points at the
  anchor lysine in the co-folded pose, and every biased sequence is re-folded.

### S4 — A declared charge ladder on one validated backbone · THE MECHANISM CONTROL
*Campaign 3.*

Take the single best binding backbone and submit a ladder on it: the parent with
no interface histidine, then variants with one, two and three histidines at
cation-facing positions.

- Why: the organizers' prompt states that "a declared control that truly tests
  the mechanism may be one" of a submission's picks, replacing the last. A ladder
  is the strongest available evidence that the switch is designed rather than
  hoped for, because the series isolates the variable.
- It is also the honest form of the claim. We can predict a direction and a
  rough ceiling, never an absolute KD.

### S5 — Calibrate on real apical-domain binders · DO FIRST, COSTS ALMOST NOTHING
*Campaign 1.*

The apical domain has known binders: arenavirus GP1, parvovirus B19 VP1u and
brain-shuttle antibodies. The organizers' rules are explicit that designs must
be de novo and not built from an existing binder, but that "training or
calibrating on known binders is fine".

- Use them only as a calibration reference: what interface area, contact count
  and residue composition a real apical-domain interface has. Challenge 2's
  single most useful artifact was exactly this kind of calibration, which moved
  the submission bar from 0.6 to 0.8 and exposed the composition error.
- Fetch 11RN (the apical complex named in the brief) and 1SUV (the
  transferrin complex, to verify the claim that this epitope leaves the
  transferrin site free). Neither is on disk yet.
- **No sequence or backbone from these structures enters a design.**

### S6 — Nanobody or scFv class entry · STRETCH, ONLY IF S1 LANDS EARLY
The organizers reward class diversity across nine classes and ask for new
methods, "even untested, at least about a tenth" of the selection. A nanobody
with histidines in CDR3 facing 344 K would be class-diverse and mechanistically
identical to S1. The `germinal` skill covers de-novo nanobody design.

Not a campaign. A nine-day window with one GPU does not have room for a new
toolchain before S1 is proven.

### S7 — Short peptide switch · NOTE ONLY
EvoBind peptides carried part of the challenge-3 submission. For a switch they
are a poor fit: few positions to tune, and the organizers' novelty prescreen
returns no signal below 25 residues, which forfeits the novelty read. Recorded
and not pursued.

## 6. The campaign map

| campaign | what it decides | days | discard rule |
|---|---|---|---|
| **C1** feasibility and epitope triage | which epitope sets carry the work, and which fold target is affordable | 1-2 | if no set reaches 2 backbones with a majority of samples at the designed site, stop and record the negative |
| **C2** binding families | the binding backbones | 2-5 | if no family reaches ipSAE 0.8 at the designed site after full-backbone re-sequencing, S1 and S2 are both dead and the campaign records a negative |
| **C3** switch layer | the pH evidence | 4-7 | if no histidine variant keeps its binding and shows a positive linkage sign, the submission competes on objectives 2 and 3 only, and says so |
| **C4** mouse cross-fold | the cross-reactivity evidence | 6-8 | none; this campaign measures and does not gate |
| **C5** selection and submission | the file | 8-9 | the validator and the prescreen must both pass before upload |

Campaigns overlap because folding is the bottleneck and generation is cheap.

## 7. Pre-registered bars

Set now, before any data, so they cannot be tuned to the result.

**Binding.** ipSAE >= 0.80 at the designed site is the submission line.
ipSAE >= 0.60 is the do-not-discard line. Both are measured on the best of five
Boltz-2 samples, and the whole five-sample spread is reported with every design.
pDockQ2 is recorded, not gated, because the challenge-2 calibration found it
non-discriminative.

**Site.** A design must have at-site contacts to its designed hotspot residues.
Score without site is discarded whatever the number.

**Switch.** `delta_log_Ka > 0` from `tools/switch/linkage_score.py`, integrated
across pH 6.0 to 7.4. The sign is the gate. The magnitude is never quoted as a
predicted fold-change.

**Quality floors, applied inside the selector.** pLDDT >= 63. pDockQ2 >= 0.18.
Sequence entropy >= 2.5 bits. No residue above 45 percent of the chain. No
homopolymer run of 6 or more.

**Composition, against the released winners' bands.** Charged fraction near
41 percent, GRAVY near -0.56, largest single residue below about 23 percent.
Flag anything that looks like the failed challenge-2 class (9.8 percent charged,
GRAVY +0.84, 37 percent largest residue).

**The three screens the judges require, recorded per design.** pLDDT, ipSAE
against the target, and mean Kyte-Doolittle hydropathy.

**Novelty.** Level 3 or higher is enforced at submission and level 4 is
preferred. Screen with `~/tools/binder-prescreen`, which needs `mmseqs` from
`~/tools/mmseqs/bin` on PATH.

## 8. The scoring rubric

One normalised score per design, no verdict labels, modelled on the
challenge-3 selector and reordered for this challenge's objectives.

    total = 2.0 * S + 1.5 * X + 1.5 * B + 1.0 * E
    normalised = 100 * total / 30

| component | meaning | 5 | 3.5 | 2 | 0 |
|---|---|---|---|---|---|
| **S** switch | linkage sign and designed histidines | positive sign, 2 or more cation-facing histidines, binding retained | positive sign, 1 histidine | positive sign, no designed histidine | sign zero or negative |
| **X** cross-reactivity | mouse fold at the same site | at site in both species, ipSAE within 0.05 | within 0.15 | mouse at site but clearly weaker | human only |
| **B** binding | ipSAE at the designed site | >= 0.90 | >= 0.85 is 4, >= 0.80 is 3 | >= 0.75 | below 0.60 |
| **E** expression | mean of the pLDDT band, the hydropathy band and the composition band | — | — | — | — |

S carries the heaviest weight because the pH switch is objective 1. Ties break on
the five-sample at-site agreement, then on ipSAE.

The row order of the submission file is the ranking. Only the first 20 designs
count. The method-family cap is 25 percent of the file, relaxed to fill the
quota, with over-cap designs held back as the top-up pool rather than dropped.

## 9. Compute plan and the one unmeasured risk

One RTX 5070 with 12 GB. Host memory is 23 GiB with 21 GiB available, which is
larger than the 16 GiB the older notes assume.

| target | residues | status |
|---|---|---|
| generation target, apical block 180-400 | 221 | matches challenge 2's proven 195-residue patch target, which ran at 8.8 GiB GPU and 50 s per design |
| fold target, one full protomer | 639 | **wanted but unmeasured** |
| full dimer | 1278 | out of reach, never attempt |

The reference point is challenge 2's 456-residue, four-chain complex at
11.3 GiB. A 639-residue protomer plus a binder is about 1.4 times that in
tokens.

**This is the single largest unknown in the plan, and campaign 1 measures it
first.** If a protomer fold does not fit, the fallback is a domain-complete
apical block as the fold target plus a separate clash check against the full
dimer, which is the pattern challenge 2 used for its trimmed target.

Rough budget: generation is about 66 s per design, so a 400-design pool costs
about 7.5 hours. Folding dominates. At five samples per design and an estimated
5 to 8 minutes per design, the plan affords roughly 250 to 400 folded designs
across the whole window, one GPU job at a time.

## 10. What this plan does not claim

- No in-silico method predicts a KD, and none predicts "no detectable binding".
  The switch evidence is a direction and a ranked linkage score, and the
  methodology will say so.
- The linkage scorer is rank-grade and was about two orders conservative against
  its FcRn reference.
- A high interface score is not binding. In the released campaign three
  never-bound designs scored 0.894 to 0.910 through this same pipeline, above
  every real winner.
- The glycan is represented by one sugar, so glycan clearance is a distance and
  not a steric calculation.
