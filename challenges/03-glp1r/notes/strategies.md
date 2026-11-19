# 03 — GLP1R agonist · strategies (written 2026-10-18, before any generation)

## What the research says (condensed; full citations in `research-brief.md`)

- **Activation is two-domain.** GLP-1's C-terminal helix sits in the ECD groove;
  its N-terminus engages the TM bundle (top of TMs + ECLs). Activation needs the
  ECD to stand up (18–28 Å from the apo-closed state) and the TM6 kink.
- **ECD-groove-only binders are antagonists.** The only published de-novo
  GLP1R-ECD miniproteins (RFdiffusion+MetaGen, Nature 2026) are antagonists;
  of 13 anti-GLP1R antibodies, the single agonist needed a GLP-1 peptide fusion.
  Groove occupancy alone has never produced agonism.
- **Non-peptide agonists** (orforglipron, danuglipron, TT-OAD2) bind TMD-adjacent
  pockets; danuglipron overlaps the GLP-1 site and mimics GLP-1 pharmacology.
- **Two in-silico agonist proxies exist in public:** Ryan Shea's pocket-reach
  heuristic (activators reach deep into the groove pocket, blockers do not) and
  the two-domain contact pattern (groove + TM pocket + ECL2/ECL3).
- **Competition facts:** novelty ≥3/4 is a hard gate (a public prescreen replica
  exists); two public challenge-3 repos both did ECD-groove binders and both
  state they do not expect activation; no released pipeline produces de-novo
  GLP1R agonists (EvoBind/RareFoldGPCR are the only cAMP-validated agonist
  routes, both peptide design tools).

## The strategies, prioritized

### S1 — Two-domain de-novo binder ("mini-GLP-1 mode") — CAMPAIGN 1
Generate de-novo binders at the orthosteric site that (a) dock the ECD groove
and (b) extend into the TM pocket, mimicking GLP-1's two-domain engagement —
the one contact pattern correlated with agonism. Score with ipSAE at the groove
+ a **pocket-reach screen** (contacts to the TM-pocket residues + groove depth,
our version of the public heuristic) + render review of the pose.
- Tools: RFdiffusion3 (primary — receptor-target standard) → full-backbone
  ProteinMPNN → Boltz-2 (full receptor 24–432) → IPSAE → reach screen → Mol*.
- Why first: it is the only route with a mechanistic agonism rationale that our
  stack can attempt; the two public challenge-3 attempts skipped it.
- Discard rule (pre-registered): if after ≥3 generation batches (≥150
  backbones), full MPNN expansion and folds of every at-site design, no design
  reaches the calibrated binding band (ipSAE ≥ 0.8 at the designed site) **and**
  deep pocket reach, the strategy is discarded and S2 starts.

### S2 — ECD-groove mini-binder (the brief's literal reading) — fallback
De-novo binders into the groove only. Expect binding, expect NO activation
(the published outcome). Run only if S1 fails, or to bank affinity-objective
designs while a better activation story is built.
- Discard rule: same bands; its results mainly calibrate how much of the groove
  can be covered by a mini-protein.

### S3 — Peptide agonists via validated agonist tools (EvoBind / RareFoldGPCR)
The only cAMP-validated GLP1R agonist design routes (peptide/cyclic, EC50
µM-class). Requires new tooling + license review (RareFoldGPCR weights are
CC-BY-NC); their published sequences are off-limits as submissions (not de novo).

### S4 — TMD-pocket small-binder mimic (danuglipron-type site)
A protein at a shallow GPCR pocket; hardest geometry, lowest odds with current
generators. Keep as a note, not a campaign.

## Campaign 1 = S1, and what "exhausted" means

Experiments (one experiment = first backbone → scored final protein):
1. E1: RFdiffusion3 generation, 100+ backbones → triage → Boltz-2 co-folds of
   the best → ipSAE + two-domain screen.
2. E2: full-backbone re-sequencing of the best folded backbones (the C2 rescue
   move), re-fold, re-screen.
3. E3: fixed-position mutation rounds on the best scorers (the C2 evolution
   move) until the plateau rule fires.
4. Renders of the best 2–3 poses (groove depth, TM reach) for the tie-break.

The campaign closes with a decision table: binding band reached? reach reached?
If both — candidate set; if binding only — S1 gives S2-grade results and the
activation question moves to S3; if neither — S1 discarded with the measured
reason.

### Campaign 1 close (2026-10-18)

| question | answer |
|---|---|
| Binding band (ipSAE ≥ 0.8 at the designed site) | **reached** — 39 of 335 samples; max ipSAE 0.933, max pDockQ2 0.535 |
| Two-domain reach (groove + TM-pocket + ECL3) | **reached** — 21 distinct designs; best e1b2-r0036 (4 TM + 8 ECL3 contacts) |
| Strategy discarded? | **no — validated.** The junction-only setup gave the best two-domain rate (25 % in E1b2) |

Campaign totals: 183 backbones generated (E1 43, E1b 60, E1b2 80); **77 of 77
folded** (5 samples each; 8 folds lost to memory kills were recovered in a retry
pass); 335 samples screened. Output: a 20-design submission file (top 20 of 21
distinct-family candidates by the reach-weighted composite
`tm*3 + ecl3*1.5 + ipSAE`, one per backbone family, prescreen-passed) plus 5 E3
refinement variants as alternates. Activation remains for the wet-lab assay;
every claim here is in-silico.

### E1/E1b results (2026-10-18) — the S1 strategy works in-silico

- Generation: 43 backbones (E1, groove+junction hotspots) + 60 (E1b, junction-only
  hotspots). 37 designs co-folded against the full 24–432 construct with cached,
  depth-capped MSAs (1024 rows; the uncapped server MSA needed 14.65 GiB and was
  killed — see `working/fetch_msas.py`).
- Screen (ipSAE ≥ 0.8 + groove contacts + TM-pocket contacts + 0 clashes):
  **13 of 140 samples are two-domain HITs, across 9 designs.**
- Best: **e1-r0025 sample 0** — ipSAE 0.933, pDockQ2 0.493, a 66-aa binder whose
  4.5 Å contact map covers 17 groove residues (D67/E68/Y69/Y88/P90/W91/R121/
  E128 …), 17 junction residues (K197/Q210/Q211/W214/F230/M233/Q234 …),
  5 TM-top residues (W297/T298/R299/N300/W306) and 7 ECL3/TM6–7 residues
  (R376–T391, including E387) — the GLP-1 path through the orthosteric site, on
  an active-state receptor (fold vs 6X18 CA distances agree within 2–4 Å at
  67/91/121–300/234).
- Second tier: e1-r0007 s0 (0.926, 4 TM contacts), e1b-r0037 s0 (0.826,
  pDockQ2 0.527 — the best interface quality score of the set).
- Verdict: binding + two-domain reach demonstrated in-silico; agonism remains a
  wet-lab question. Campaign 1 proceeds to E2 (full-backbone re-sequencing of
  the best backbones) to raise margins.

### E2 findings (2026-10-18)

- **ProteinMPNN re-sequencing does not transfer to these backbones.** RFD3's
  binders are already alanine-rich helices (e.g. e1-r0007 chain A is ~45 % A),
  and MPNN at temp 0.1 on such low-complexity backbones collapses to poly-A
  (`AAAAAAALAAAAAAAAAL…`) — not usable. The C2 "full-backbone resequencing
  rescue" applied to diverse backbones; here the sequence step must stay with
  the generator. E2 was therefore redefined: a second generation batch of the
  productive setup (E1b junction-only hotspots, 80 more backbones).
- **Operational lesson:** after killing a fold runner, its boltz children can
  survive as orphans holding ~11 GB RAM and the GPU. They starved the next
  fold batch (memlimit kills at 13.5 GiB). Always verify `ps` after killing a
  runner — and give each runner generation a unique out_dir for the same
  reason the RFD3 chain needed it.

### E1 execution notes (2026-10-18, measured on this box)

- The generation target: 6X18 chain R **residues 29–241** — the ECD groove plus
  the ECD–TMD junction/ECL region. Hotspots: groove
  `R67,R69,R88,R91,R121,R128` + junction `R197,R210,R221,R234`. Rationale: the
  activation-compatible pose needs the groove AND the ECD–TMD interface (the
  active ECD "stands up"; the interface reorganises), and the junction lies on
  the GLP-1 N-terminal path toward the TM pocket.
- Target-size finding: the full receptor (384 resolved / 409 construct) made
  RFD3 either pathologically slow (`low_memory_mode=True`: 14+ min with no
  output, CPU-bound) or GPU-OOM-prone (fast but OOM after 1–2 designs per
  process). The 213-resolved ECD+junction target runs at **33 s per design,
  peak 6.9 GiB** with `n_batches=2` per process, chained (fresh VRAM per
  round). Generation config: `inputs/rfd3-e1.json`.
- The ECD-only target was rejected as a generation target because the public
  challenge-3 repos hit exactly that trap (binders clash into the omitted TM
  bundle); our safeguard is that the CO-FOLD uses the full 409-res construct
  and the screen flags clashes.
- Screen metrics (pre-registered): ipSAE ≥ 0.8 (the C2-calibrated line) AND
  two-domain contacts (≥1 groove residue + ≥1 junction/TM residue within
  4.5 Å) AND zero clash pairs < 2.0 Å.
