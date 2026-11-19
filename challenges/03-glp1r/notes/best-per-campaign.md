# Challenge 3: the best designs per campaign (standing ledger)

## Activation geometry (added 2026-10-20, the agonism scorer)

The activation-geometry gate (`notes/agonism-geometry-2026-10-20.md`) scores
six pharmacophore contacts plus insertion depth. Perfect (6/6) designs:

| design | features | depth (A) | pose agreement | note |
|---|---|---|---|---|
| c3-j3-run14 | 6/6 | 23.1 | 5/5 | strongest: full pharmacophore, unanimous |
| c2-run1-b206 | 6/6 | 20.6 | 4/5 | the EvoBind peptide, GLP-1's exact depth |
| c3-j3-run21 | 6/6 | 20.0 | 5/5 | unanimous |
| c3-j3-run3 | 6/6 | 19.8 | 2/5 | weaker agreement |
| c3-j2-run6 | 6/6 | 18.5 | 5/5 | unanimous |
| e1b2-r0065 | 6/6 | 17.4 | 3/5 | the 65-aa miniprotein |

The c3 junction config produced 4 of these 6 - the reason campaign 8 repeats it
at scale.

**Campaign 8 (the scale-up) added three more 6/6 designs:**

| design | features | depth (A) | pose agreement | note |
|---|---|---|---|---|
| c8-run41 | 6/6 | 21.0 | 5/5 | unanimous |
| c8-run13 | 6/6 | 17.6 | 4/5 | **also a two-domain HIT** — the strongest both-lens design |
| c8-run20 | 6/6 | 18.1 | 1/5 | weak agreement, flagged |

The challenge pool now holds nine 6/6 designs and 63+ two-domain HITs. Depths above ~30 A mean a wrapping pose, not insertion; those designs
are flagged, not trusted.

Policy (2026-10-20, from the user):

- **Keep the best designs of every campaign.** The submission file is decided
  later in the week; nothing is dropped from the pool before then.
- **When the campaigns finish, re-check each one for a rerun** in the light of
  new tools and learnings — a finished campaign is re-opened only when a new
  tool or a measured lesson changes its odds.
- The keep-set means: the fold directories of every design listed here are
  never deleted; the full pools stay in the campaign tables (`c3-candidates.csv`
  and the submission CSVs).

## Campaign 1 — `c1-two-domain` (RFdiffusion3 mini-proteins) — complete

| design | sample | ipSAE | composite | note |
|---|---|---|---|---|
| e1b2-r0036 | 0 | 0.888 | 19.80 | best of the campaign |
| e1-r0014 | 0 | 0.857 | 17.80 | |
| e1b-r0059 | 1 | 0.901 | 16.87 | highest ipSAE of the family |

## Campaign 2 — `c2-peptide-agonists` (EvoBind) — complete

| design | sequence | ipSAE | composite | note |
|---|---|---|---|---|
| c2-run1-b206 | MLIRYFVNQQRNYNP | 0.873 | 17.03 | 15 aa, linear |
| c2-run2-i299 | ALAWCVNFIEDRAPS | 0.832 | 14.79 | 15 aa, cyclic run |
| c2-run1-b297 | MGIRYFVGQQRNYNK | 0.898 | 11.39 | high ipSAE, weaker reach |

## Campaign 3 — `c3-boltzgen-cyclic` (BoltzGen, incl. the c4 scale batch) — complete

| design | sequence | ipSAE | composite | note |
|---|---|---|---|---|
| c3-j2-run12 | GKLDPETFKPLS | 0.821 | 17.47 | deep reach (tm 4, ecl3 6) |
| c3-j2-run6 | TFSFEFEGFTYTVG | 0.794 | 16.45 | deep reach |
| c3-jun-run1 | TVSLTNLETGFTITVG | 0.797 | 15.76 | 5/5 samples consistent |
| c3-j3-run13 | TFSFTNSDGFTITVG | 0.843 | 15.65 | campaign-4 batch |
| c3-jun-run6 | TVFEYRGFTIKVM | 0.846 | 15.03 | two-domain HIT |

Seven two-domain HITs total across the c3/c4 batches; the full table is
`campaigns/c3-boltzgen-cyclic/c3-candidates.csv`.

## Campaign 5 — `c5-bindcraft2-junction` (BindCraft2) — complete

50 trajectories, 15-18 aa peptides, junction site. **BindCraft2 accepted 0
of 50** by its own gate — yet its raw designs, screened on our pipeline,
include the campaign's best design:

| design | sequence | ipSAE | grv/tm/ecl3 | note |
|---|---|---|---|---|
| c5-bc2-l18_bfe509d11b1b8f27 | LAYVIERITYHETCHLWN | 0.861 | 2/2/4 | **HIT** — best of the challenge so far |
| c5-bc2-l17_fd59af85e29c407c | LPWYPPKITRNGYWHMP | 0.835 | 3/4/5 | deep reach |
| c5-bc2-l17_e67aad821d1278cd | PTQPHPPNPMIWRQERE | 0.788 | 3/2/4 | |
| c5-bc2-l16_de8486c1c9805cbe | EVVWPPPDRNAYPHMM | 0.763 | 4/4/7 | deepest ecl3 reach |

**The decisive lesson, again:** a generator's own gate is not a filter —
BindCraft2's 0/50 would have discarded the challenge's best candidate. Every
generator's raw output must reach the independent screen.

## The rerun-check list (apply when the campaigns finish)

| new tool / learning | what it re-opens |
|---|---|
| SolubleMPNN (28% vs 47% alanine) | re-sequence the c1 champion backbones; a fresh sequence family per backbone |
| reactifpTM | already run on the current top designs (all >= 0.975); re-run after every new batch |
| BindCraft2 modalities (VHH, scFv, large_binder) | c5 covers the peptide class; the other modalities are untried |
| The junction-only lesson | any rerun of c1 (mini-proteins) should use junction-only hotspots |
| The metric-divergence lesson | every new generator's designs go through our screen, never its own gate |
| BoltzGen `main` (SolubleMPNN default, 105 commits) | a medium-risk upgrade that could lift the c3 generator itself |

## Campaign 6 — `c6-solublemnn-resequencing` — complete, the strongest campaign

Interface-pinned SolubleMPNN re-sequencing of campaign 1's five champion
backbones (40 designs). 20 samples cleared the two-domain bar.

| design | sequence | ipSAE | grv/tm/ecl3 | note |
|---|---|---|---|---|
| c6-e1-r0025-s2 | MSEDEANAQTATLTAAAACACDDTFPQAAVEIARAACRDASGRECLQAALAALALASLINTLAEHL | 0.934 | 6/2/5 | **challenge-best ipSAE; full groove** |
| c6-e1b-r0059-s5 | SSNASLQSAFTIVAARDLLALIALATASLVHPANGVILDACSSIEEAAALLAEAQALGTASPEEAVRRALEETVALLRAVLDAVAAFAAVSAALAAL | 0.870 | 5/4/8 | **composite leader 19.42 — deepest reach** |
| c6-e1-r0025-s3 | see c6-e1-r0025 family | 0.911 | 6/2/6 | |
| c6-e1-r0025-s7 | | 0.909 | 5/2/7 | |
| c6-e1b-r0037-s3 | | 0.905 | 5/2/7 | |

## Campaign 7 — `c7-long-peptides` — complete

30 designs at 20-24 aa (the one untried length class). 5 two-domain HITs;
best `c7-run11` (0.812, groove 6/6, ecl3 7/8). Verdict: viable, not superior
to 15-18 aa. Two designs cover all six groove residues.

## Campaign 8 — `c8-deep-junction` (BoltzGen, deep conditioning) — complete

60 designs conditioned on the TM-pocket/ECL3 message region. 3 full 6/6
geometries, 12 two-domain HITs, 105/300 samples deep. `c8-run13` led the board
until the hosted RFD4 rounds (22.51).

## Campaign 9 — `c9-solublemnn-resequenced` (SolubleMPNN on c3 champions) — complete

33 variants of the c3 full-geometry backbones. 5 full 6/6, 13 two-domain HITs.
Re-sequencing raises the 6/6 rate; `c9-e1b2-r0065-s4` (21.94) entered the
submission twenty.

## Campaign 12 — `c12-rfd4-proteina` (RFD4-Proteina, NVIDIA's hosted pool) — complete

256 designs (medium + high thinking) from the deep conditioning. **27 full 6/6
geometries, 68 two-domain HITs**, 769/1280 samples deep — the best generator
this target has seen, and the first hosted free-compute campaign.

## Campaign 12b — `c12-mpnn-variants` (SolubleMPNN on c12 champions) — complete

81 interface-pinned variants of the 27 c12 champions. **25 full 6/6 (31 %)** —
the best re-sequencing yield of the challenge; five entered the submission
twenty.

## Campaign 13 — `c13-junction` (RFD4 conditioned on the ECD–TMD junction) — complete

73 designs where only the junction block (K197/Q210/Q221/Q234) steered
generation. **15 full 6/6 (21 %) — the strongest configuration of the
challenge** — 27 two-domain HITs, 285/365 samples deep (78 %). Produced the
overall best design, `c13-junction-b43-d02` (23.85, 6/6 at 19.2 A, 5/5 poses,
ipSAE 0.918, two-domain HIT).

## Campaign 14 — `c14-short-band` (RFD4, 40-70 aa) — complete

72 designs: the deep conditioning at the c1-proven short length band. 6 full
6/6, 13 two-domain HITs — the best two-domain rate of any round — and two
designs in the top five (`c14-short-b46-d02`, `c14-short-b47-d08`, both 23.06).

## The current leaders (2026-10-23)

| # | design | total | activation | note |
|---|---|---|---|---|
| 1 | c13-junction-b43-d02 | **23.85** | 6/6 @19.2 A, 5/5 poses | the overall best; two-domain HIT |
| 2 | c13-junction-b36-d07 | 23.45 | 6/6 @21.6 A, 5/5 | |
| 3 | c13-junction-b41-d04 | 23.39 | 6/6 @24.6 A, 5/5 | |
| 4 | c14-short-b46-d02 | 23.06 | 6/6 @29.3 A, 4/5 | short band |
| 5 | c14-short-b47-d08 | 23.06 | 6/6 @21.6 A, 5/5 | short band; two-domain HIT |
| 6 | c12-b3-d01 | 22.92 | 6/6 @22.0 A, 5/5 | deep campaign leader |
| 7 | c12-b21-d08 | 22.90 | 6/6 | |
| 8 | c12-mpnn-b21-d08-v1 | 22.79 | 6/6 | re-sequenced |
| 9 | c12-mpnn-b10-d07-v2 | 22.78 | 6/6 | re-sequenced |
| 10 | c2-run1-b206 | 22.51 | 6/6 @20.6 A | EvoBind peptide — the only non-RFD4-family design this high |

The complete ranking with every score sits in
`~/c3-work/c8-agonism/selection-all.csv`; the submission twenty in
`submission/competition-submission-rubric-2026-10-23.csv`.
