# Site-sync TODO

Open items: do not present these on the site as finished work.

- 2026-11-03 (sync run, refined 2026-11-04): the app renders `summary` and
  chapter `text` / `outcome` on a lineage page. `verdict` is not rendered,
  and `verdict_detail` renders only on the no-submission path
  (`_no_submission_html`). Every new fact from each sync is therefore also
  written into a summary or a chapter. Fix in tools/serve/app.py (render
  verdict + verdict_detail on the lineage page) stays open.

- 2026-11-04 (sync run, refined later 2026-11-04): evolution plateau 2 is
  OPEN and not fixed. The
  breeder cannot read the sequence of the designs the loop itself swapped
  in - each build log from generation 5 on reads "- <winner>: no sequence
  found, skipped" for A16K, E23K and V24K (evo.py parent_seq). With those
  parents skipped and the other parents' shell positions exhausted, only
  the combo operator fired, and it had no duplicate check: generations
  6-12 built the identical 13 children (same fold names, same E table,
  byte for byte). That duplicate check landed after the run (evo.py v4:
  untried pairs of each family's known mutations, combos already on disk
  skipped) and the site now carries it in C16. Of the two gap fixes, one is
  now CLOSED by aa431ec (2026-11-04): the fold and yaml lookups fall back
  to a recursive search over every fold tree, so the designs the loop
  swapped in itself resolve - generation 14's build log no longer skips
  A16K, E23K and V24K, and the site's C16 fix chapter says so. One fix
  stays OPEN: a plateau or convergence stop. The autopilot still stops
  only at the end of the requested generation range, and a further run
  started before that fix landed (see the live-run bullet below).
  Generations 4-12 are on the site (C16); generation 4's three wins are in
  the submission.

- 2026-11-04 (sync run, closed 2026-11-04): the generation-4 apply left
  three challenge outputs uncommitted - challenges/05-pmhc/records/final2/
  submission-top20.fasta, records/selection-scores-05-pmhc.csv and
  submission/submission-05-pmhc.csv (the three gen-4 entries with their
  parents dropped). The site sync did not commit them: they are the
  loop's own outputs, and another agent shares this repo. The site reads
  the working tree, so the pages already show the new set. Closed: the other
  agent has since committed all three (3ba9b65 - the champions in the
  submission deliverables; c30b2a5 - the selection scores).

- 2026-11-04 (sync run, superseded 2026-11-04): the generator project is on
  the site as C17. The first version carried only the local RFD4-Proteina
  smoke, the 7OW6 A-C target check, the ATLAS/SKEMPI download and the tool
  audit. All of that has since run further and the site now carries the
  results: the 32-design baseline batch (6 of 32 JDI-like, 19 percent),
  the BoltzGen head-to-head (not adopted), the E_int scope test against
  ATLAS (r -0.08) and the fine-tune's 12 GB memory wall. Still OPEN and not
  presented as results: the composite is not calibrated against the
  ATLAS/SKEMPI dDeltaG (only the E_int scope test ran), no LoRA tuning
  cycle has completed, and the second co-folding opinion has no result yet
  (OpenDDE is running - see its own bullet; PXDesign and Protenix-v2 have
  not run).

- 2026-11-04 (sync run, refined later 2026-11-04): the fine-tune is blocked
  on this machine and the site says so. The first LoRA attempt (official
  diffusers example, 8 batch1 complexes) ran out of memory at the
  ~490-residue complexes on the 12 GB card: rank 32 and rank 8 both failed,
  a 4-bit NF4 base loads in 1.2 GB but training still needs about 26 GiB of
  activations, and a six-attempt fork reached the same wall. The later
  truncation test (620 to 520 tokens, 449 to 379 residues) moved the peak
  by 0.5 percent, so input shaping does not reach it; the site's C17 now
  carries that chapter. OPEN and awaiting the user's decision: the choice
  of fallback - train on shorter class I complexes from ATLAS (cheapest,
  untested), quantized base with LoRA, a bigger card (24 GB and up), or
  tune a different component (inverse-folding or the scoring side). No
  tuning cycle has completed.

- 2026-11-04 (sync run): two research notes are plans, not results
  (notes/finetune-research.md, notes/pipeline-integration-options.md). The
  site carries the chosen strategy (the RAFT-style LoRA loop) as the plan
  inside C17, marked as not run; no campaign was invented for them.

- 2026-11-04 (sync run, closed 2026-11-04): two custom-model scripts were
  uncommitted during the first sync (custom-model/scripts/
  cif_to_boltz_yaml.py and gen_batch.py). The other agent has since
  committed them; the site's C17 batch and BoltzGen chapters depend on
  them and both are tracked now.

- 2026-11-04 (sync run): the second co-folding opinion runs, with no result
  yet. A new helper appeared uncommitted (custom-model/scripts/
  collect_submitted_cifs.py): it copies the mutant-complex fold of each of
  the 20 submitted designs into ~/c5-work/opendde-20/cifs for OpenDDE
  scoring. It collected 20 cifs at 16:11, the first fold pass reached 3 of
  20 by 16:26 and stopped, and a second pass started at 17:48 on 18 jsons
  (one process on the 12 GB card, its log stops at 17:51). No fold is
  scored, so there is no comparison against boltz or chai. The site stays
  unchanged for this item: the C17 audit chapter still says OpenDDE "earns
  a second co-folding opinion", which remains true. The helper is another
  agent's file, so the site names no script.

- 2026-11-04 (sync run, superseded 2026-11-05 - see the two bullets at
  the end of this file): the loop is running again past the range the site
  records, with no result yet. Generation 13 folded 52 children at 09:41
  (no score summary written) and was left incomplete; an overnight run
  then took generation 14 (22:27) and generation 15 (started 23:11, still
  folding its 60 children at 23:52). Generation 14 bred from the v4 gate
  top, sent 14 qualifiers to the tri-state panel and promoted nothing (its
  autopilot log: "no winners above margin"); generation 15 has no score
  yet. Nothing is promoted and nothing is validated, so the site stays
  unchanged for this item: C16 still describes generations 4-12 and the
  stop at the end of that range, and its fix chapter names the closed
  parent-lookup gap and the live selection change. Update C16 only when a
  generation promotes a swap or the run ends.

- 2026-11-04 (sync run): the submission's score column now holds two
  formulas. records/selection-scores-05-pmhc.csv carries the v2 selector's
  0-100 scores for the fourteen original entries (90.5 down to 61.5) and
  the v4 composite's scores for the six epitope-gate additions (58.9 down
  to 54.7). Both are nominally 0-100, so they read as one scale but are
  not comparable, and the highest v4 score of the whole generation-4 pool
  is 58.9. OPEN: a single comparable score for the twenty is not defined -
  the choice (recompute the twenty on one formula, or keep two labelled
  columns) needs the author. The site says the two scales plainly: the
  submission section of the challenge page and the "selection score"
  legend in tools/insights.py now name both formulas, and the C10 chapter
  "E - the epitope-gate re-cut" carries both ranges.

- 2026-11-04 (sync run): the swap script's stated criterion is not
  reproducible from the records. custom-model/scripts/swap_stars.py says
  it removed "the six weakest entries on the organizers' epitope criterion
  (peptide_read <= 0.098)", but the six designs it removed read 0.441 to
  0.665 in their own fold summaries (nim-wave3 run-021 design_0001 0.441,
  H27K 0.537, A58K-F50K 0.527, mini-wave1 run-011 design_0001 c5 0.644,
  N71K 0.641, W57K 0.665), and several entries that stayed read lower
  (peprim-wave1 run-012 design_0006 c3 0.443, peprim-wave1 run-007
  design_0004 0.489). No file in the repo or in ~/c5-work holds a
  re-measurement with those six at or below 0.098. OPEN: the removed set
  and the threshold need the author's confirmation. The site reports the
  swap, the six that left and the reads of the six that entered, and does
  not repeat the 0.098 threshold.

- 2026-11-04 (sync run): the v4 ranking rests on a pasted table.
  custom-model/scripts/rerank_v4.py carries the E-scores of the
  generation-4 pool in an in-file dict (E_TABLE, 18 entries, "paste of the
  measured values") instead of reading them from the fold trees, so a
  re-run of the ranking depends on a manual copy. OPEN: read the E table
  from the records. The site presents the v4 composite and its 18 gate
  passers without claiming the table is generated.

- 2026-11-04 (sync run, done 2026-11-04): the site now carries the
  2026-11-04 evening work. C10 gained the chapter "E - the epitope-gate
  re-cut" (six gate passers in, six entries out, 20/20/20 verified) and
  its proteins now come from the live submission file, so the submission
  table and the campaign page show the twenty with the six additions. C16's
  fix chapter records the closed parent-lookup gap and the move to the v4
  selection. C17 gained two chapters: the truncated-complex test (the peak
  moves 0.5 percent for a 16 percent cut) and the composite v4 gate term
  (18 passers in the generation-4 pool). The multiview viewer
  submission.html was regenerated and now renders the six new designs.

- 2026-11-05 (sync run, superseded 2026-11-05 by the two bullets at the
  end of this file): generations 13-17 ran with no promotion. Generation 13
  built 52
  children and was left incomplete; generation 14 (67 children in two
  runs) sent 14 qualifiers to the tri-state panel and promoted nothing;
  generations 15, 16 and 17 bred 60 children each and all 60 are
  byte-identical across the three. Generation 17 is still folding its
  children (started 04:22). The site now carries this: C16's title spans
  generations 4-17, its summary and the new chapter "G13-17 - the
  plateau holds" record the five barren generations, and the fix chapter
  no longer claims the repeated child set cannot recur. Nothing is
  promoted and nothing is validated.

- 2026-11-05 (sync run, OPEN, not fixed, belongs in evo.py): the v4
  combo dedupe does not prevent repetition across generations. evo.py
  skips a combo only when the file exists in the generation's own folds
  directory, which is empty at build time, so generations 15, 16 and 17
  wrote the same 60 children byte for byte and the same folds were paid
  for three times at about 2.5 h each. The site states this in C16
  (chapter G13-17). Related: three of the breeder's sixteen parents
  carry a v4 score of -1 because their E column in evo/gen4/
  rerank-v4.csv is empty (ranks 14-16), and the breeder still breeds
  from them.

- 2026-11-05 (sync run, superseded 2026-11-05 by the bullet that
  follows): generations 18 and 19 ran and promoted nothing, so the
  plateau then spanned generations 13-19. Generations 15, 16, 17, 18 and 19 bred 60
  children each and all five child sets are byte-identical: the same 60
  fold names, the same fold file contents and the same E table, and
  generations 15-18 also wrote the same 24-arm tri-state score table.
  Generations 15-18 sent 12 qualifiers each and no winner cleared the
  margin. Generation 19 bred the same 60 children; its tri-state panel
  (12 qualifiers, 24 arms) was still folding when the site was built, so
  its result is not recorded anywhere. The autopilot run is requested for
  generations 14-20 (autopilot.sh 14 20), so generation 20 is the last
  and the stop is the end of the requested range, not a convergence rule
  - still OPEN, and the site's fix chapter says so. The site carries this:
  C16's title now spans generations 4-19, its summary names the five
  identical child sets and the 12 qualifiers generations 15-18 sent, and
  the chapter is renamed "G13-19 - the plateau holds". Nothing is
  promoted and nothing is validated.

- 2026-11-05 (sync run, supersedes the generations 13-19 bullet): the
  autopilot run of generations 14-20 ended at 14:55 on 2026-11-05
  ("AUTOPILOT complete"), so the loop is idle now. Generation 19's
  tri-state panel finished after the last sync and cleared no margin: 12
  qualifiers, 24 arms, no winner. Generation 20 built the same 60
  children again, and its s1 read is identical to generations 15-19 (4
  children at the organizer's peptide gate, 27 JDI-like interfaces), so
  six generations (15-20) paid about 2.5 h each for the same folds and
  the plateau now spans generations 13-20. The run stopped at the end of
  the requested range, so the convergence stop is still OPEN and belongs
  in evo.py. The site carries this: C16 spans generations 4-20, its
  verdict and goal_extra count sixteen barren generations, and the
  chapter is renamed "G13-20 - the plateau holds". Two file types inside
  a repeated generation are NOT byte-identical: Boltz's own .pml and
  .txt output embed the generation path (600 of each), so the site now
  says "the same structures and the same E table" instead of "byte for
  byte".

- 2026-11-05 (sync run): the OpenDDE item still has no result.
  ~/c5-work/opendde-20/preds and pred2.log have not changed since
  2026-11-04 17:51 and no submitted design is scored, so the C17 audit
  chapter stays as it is.

- 2026-11-05 (sync run, note for the next run): the change digest watches
  repo paths only. The generation work runs in ~/c5-work/evo, outside
  every path step 1 of the playbook checks, so new generations appear in
  the digest only when a note or a record changes. Step 1 now also checks
  ~/c5-work/evo for a generation newer than lineage.json. A further trap
  from this run: the digest and step 1 both flag this playbook and this
  TODO file as changed after every sync, because the sync itself edits
  them - a run whose only digest entries are notes/site-sync-playbook.md
  and notes/site-sync-todo.md must still check ~/c5-work/evo for new
  generation work before it reports "nothing to do".

- 2026-11-08 (sync run, SKIPPED for a concurrent edit): the site was left
  unchanged and nothing but this note was committed. The digest flagged
  three records, records/deep-review-2026-11-08.md and records/final2/
  {METHODS.md,README.md}, all committed at 12:26 in e8b3906. They are
  submission-facing texts, not site facts, and the two submission texts
  and the two final2 documents they correct are records the site does not
  render. The real blocker is other agent work in flight: build-lineage.py
  (12:11), lineage.json (12:14) and the multiview folder (12:11-12:14)
  carry an uncommitted, staged restructure that merges 18 campaigns into
  13 (c7+c13, c9+c17+c18+c19, c11+c12, c14+c15+c16), and HEAD moved twice
  during this run (e8b3906 at 12:26, 40893ea at 12:27). Any rebuild or
  commit here would have carried that restructure under this run's commit
  and could have overwritten it, so the sync stood down. The site is NOT
  behind on the 2026-11-08 panel work: 48804e4 and d748414 already put the
  two-for-two swap (N71K in, W57K in, gate compliance 14 of 20 to 16 of
  20) on C10 and C18.

- 2026-11-08 (sync run, CLOSED 2026-11-09 - applied, see the 2026-11-09
  bullet): the "audit" chapter
  of the generator campaign said OpenDDE "earns a second co-folding
  opinion". The committed deep review says the opposite: OpenDDE is
  shelved after two host reboots, its retry pass collected 20 complex
  files and produced no scores, and it is a binder-versus-nonbinder
  instrument, not a G12D-versus-WT one. Apply this only when
  build-lineage.py is clean, because the pending restructure rewrites that
  chapter (c17 is folded into c9-generator-hunt). The same review adds
  tool verdicts the site does not carry: APBS is not installed and is an
  optional post-deadline addition, PXDesign/Protenix-v2 was never run
  (backup generator), Complexa and OpenFold3 were available and unused,
  and no all-atom MD or FEP run was made (the BioEmu2 ensembles cover
  thermal stability). The rival-archive panel (~/c5-work/rival-panel, 64
  designs from another participant) stays out of the site until after the
  deadline, and the W57K score-cell inconsistency (site 84.3, score file
  empty) belongs to the other agent's restructure, not to this sync.

- 2026-11-08 (second sync run, CLOSED 2026-11-09 - applied, see the
  2026-11-09 bullet): the submitted set is NINETEEN designs, not twenty
  (records/final-cut-2026-11-08.md: the organizer ipSAE gate left 16 of 20,
  three below-gate entries were restored after audit, one was dropped; the
  deliverables are submission/submission-05-pmhc.csv, records/selection-
  scores-05-pmhc.csv and records/final2/submission-final.fasta, all 19
  rows). The site is HALF updated. The submission section already reads
  nineteen because it renders submission/methodology.md, which the other
  agent updated at 18:19 ("Fifteen of the nineteen submitted designs", "the
  final 19 designs"). The C10 campaign text in build-lineage.py still reads
  "Every one of the twenty then got the full instrument set" in its summary,
  and its goal, goal_extra, verdict_detail and chapter texts still say "the
  twenty". The live C10 lineage page shows it (HTTP 200 at
  http://127.0.0.1:8737/lineage/05-pmhc/c10-final-selection, text "Every one
  of the twenty"). Apply this only when build-lineage.py is clean: it still
  holds another agent's uncommitted, staged restructure (18 campaigns merged
  into 13, 168 added lines, staged index at 109 files), HEAD moved to
  f4fdc3d at 18:31, and ATTRIBUTION.md and EXPERIMENTS.md were written at
  18:35 during this run. A rebuild or commit here would have carried that
  restructure under this run's commit, so the sync stood down again. Also
  noted: the challenge route is now /ch/05-pmhc (the old /challenges/05-pmhc
  path 404s after the restructure); ~/c5-work/evo has no generation newer
  than lineage.json (gen20, autopilot complete 2026-11-05).

- 2026-11-09 (sync run, applied the two pending items; the concurrent
  restructure landed as 33f8592, so build-lineage.py is clean now): the site
  carries the nineteen-design final cut. C10's verdict, summary, goal,
  goal_extra and verdict_detail now end on the 2026-11-08 cut (the
  organizers' ipSAE gate, peptide_read >= 0.61, applied to the twenty:
  sixteen passed, three of the four below it were restored on their
  wild-type separation, one (E23K) left), and C10 gained the chapter
  "F - the final cut to nineteen". The C10 proteins list is the live
  submission file, now 19 rows, and the submission table reads "the final 19
  designs". The generator campaign's audit chapter now carries the shelved
  OpenDDE verdict (two host reboots, a 20-file retry pass with no scores, a
  binder-versus-nonbinder instrument) and the other tool verdicts from the
  deep review (PXDesign/Protenix-v2 never run, APBS not installed, Complexa
  and OpenFold3 unused, no all-atom MD or FEP). The new metrics record
  records/submitted-19-metrics-2026-11-08.csv is named in the C10 summary.
  NOT on the site, deliberately: the challenge-5 video reel under
  challenges/05-pmhc/videos/ (the ten top-ranked designs, 2026-11-08). The
  app renders no videos and the challenge-3 and challenge-4 reels are not on
  the site either, so this is house convention, not a lag. Still OPEN and
  unchanged: the rival-archive panel (post-deadline), the W57K score-cell
  inconsistency (the other agent's restructure), verdict/verdict_detail not
  rendering on lineage pages, the evolution convergence stop, the rerank_v4
  pasted E table and the two-scale score column.
