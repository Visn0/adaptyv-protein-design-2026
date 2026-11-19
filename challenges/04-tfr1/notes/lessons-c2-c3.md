# 04 — what challenges 2 and 3 taught, as rules for this challenge

Written 2026-10-23, before any challenge-4 generation. Each entry names the
source, states the lesson, and states the rule it creates here. Tool-level
versions of some entries also live in the `protein-binder-design` skill.

Challenge 2 ended with **no submission**. Challenge 3 shipped twenty designs.
The difference was not effort. It was that challenge 3 measured the thing it was
selecting on. These rules exist to carry that difference forward.

---

## A. The lessons that decide whether we submit at all

### A1. A docking score is not evidence about a designed interface
Source: `02-tnfa/notes/campaign-close.md`, `x3-strategy.md` section 9.

ipSAE answers "is there an interface here", not "is the interface where the
design put it". In challenge 2 the single passing fold, on which the whole
selection rested, sat 15 to 18 A from its designed groove. Samples that did land
on the groove scored 0.000 to 0.433. Across 90 samples, zero cleared the bar
**and** sat on the designed epitope.

**Rule: every fold is screened for score AND site together. A design with no
at-site contact is discarded whatever it scores.** The screen is
`02-tnfa/handoff/scripts/screen_folds_site.py`, with a site map per epitope set.
Write the challenge-4 site maps for E0, E1 and E2 before the first fold.

### A2. The generator dominates the outcome, not the filter
Source: `02-tnfa/notes/filter-calibration.md`, measured on Anthropic's released
TNF-alpha campaign with real wet-lab outcomes.

| generator | bound of n | win rate |
|---|---|---|
| Genie 3 | 8 of 23 | 34.8 % |
| PXDesign | 4 of 57 | 7.0 % |
| RFdiffusion3 | 1 of 40 | 2.5 % |
| RFdiffusion | 0 of 20 | 0 % |
| BoltzGen | 0 of 8 | 0 % |
| BindCraft | 0 of 2 | 0 % |

Challenge 2 spent its campaign on the 2.5 percent generator.

**Rule: Genie 3 is the primary generator for this challenge.** It is installed at
`~/tools/genie3` with its venv at `~/.venvs/genie3`, it runs at 66 s per design
on this card, and it placed 8 of 8 designs on the specified epitope. RFD4-Proteina
is the co-primary, because it produced 17 of the 20 designs in the challenge-3
submission. RFdiffusion3 is a control arm, not a main arm.

### A3. The score bar is 0.8, not 0.6
Source: same calibration. In that campaign the 0.6 to 0.7 ipSAE band produced 0
binders of 22. The 0.8 and above band bound at 25.7 percent against a base rate
of 8.7 percent.

**Rule: pre-register ipSAE >= 0.8 at the designed site as the submission line,
and 0.6 as the do-not-discard line.** Keep one or two metric outliers by hand:
one real binder in that dataset, at KD 2.1 nM and mouse cross-reactive, scored
0.06.

### A4. A high score is not binding
Source: same calibration, verification folds. Three never-bound designs scored
0.894 to 0.910 through our own pipeline, above every real winner. Their pDockQ2
(0.49 to 0.57) sat far above every winner's (0.07 to 0.28).

**Rule: never describe a saturated score as a promise. Report the whole
five-sample spread of a design, never its best sample.** pDockQ2 is recorded and
not used as a gate, because it was non-discriminative in the calibration.

### A5. A screen can only discard; it cannot add a feature
Source: `03-glp1r/notes/likeness-finding-2026-10-22.md`.

Challenge 3 built a harsh agonist-likeness metric and found the pool ceiling was
6 of 19 contacts. Filtering harder could not raise it. The upside was in aiming
generation at the feature.

**Rule: the pH switch must be built into generation and sequence design, not
hoped for and then filtered. Challenge 2's switch retrofit was listed as "a new
design experiment, not started" and that is why its objective 1 was empty.**

---

## B. The lessons about sequences

### B1. CA-only ProteinMPNN was the chief error of challenge 2
Source: `02-tnfa/notes/genie3-round2-family.md`.

The same Genie 3 backbone capped at ipSAE 0.248 under CA-only sequencing. Under
full-backbone ProteinMPNN it produced 18 members at 0.63 to 0.85, every sequence
with all five folds at the designed site, and a champion whose five independent
folds read 0.832 to 0.852. The released real binders score 0.86 to 0.91 in the
same protocol.

**Rule: full-backbone ProteinMPNN only. Never CA-only.**

### B2. The working protocol, in order
Source: same note, "Protocol now (carry forward)".

1. Generate diverse backbones, 16 to 64 per set.
2. Fold them all. Pick backbones by their folded spread, which means the
   majority of samples at the designed site.
3. Re-sequence only the picks with full-backbone ProteinMPNN, 8 to 16 sequences
   each, at temperature 0.1 and 0.3.
4. Keep only families that reproduce across independent folds.

**Rule: this is the challenge-4 protocol. Read the at-site fold spread before
sequencing anything, because epitope difficulty gates the whole fix.** In
challenge 2 the same protocol that produced two good families on a
benchmark-adjacent surface produced nothing on the hard junction epitope.

### B3. There is a measured composition target
Source: same note, the comparison against the 13 released wet-lab winners.

| group | charged % | GRAVY | largest single residue % |
|---|---|---|---|
| real winners, n=13 | 41.2 | -0.56 | 22.2 |
| our failed RFD3 campaign | 9.8 | +0.84 | 37.3 |
| our Genie 3 batch | 45.1 | -0.67 | 23.7 |

The failed campaign's sequences were greasy, alanine-heavy and four times less
charged than any real binder.

**Rule: screen every candidate on charged fraction, GRAVY and largest-residue
share, against the winner bands above.** This also catches the failure mode in
C3 rule C4 below.

### B4. RFdiffusion backbones collapse to poly-alanine under plain MPNN
Source: `03-glp1r/campaigns/c1-two-domain/LEARNINGS.md`, item 5. Plain
ProteinMPNN gave 47 percent alanine; SolubleMPNN gave 28 percent on the same
backbones.

**Rule: use SolubleMPNN for re-sequencing, and pin the co-folded interface
contacts while redesigning the periphery at temperature 0.3.**

---

## C. The lessons about selection and records

### C1. Quality floors must be in the selector, not in the prose
Source: this repo, challenge-3 selection, 2026-10-23.

The challenge-3 methodology promised pLDDT, pDockQ2 and complexity floors that
no code applied. The selector returned a 24-residue design that was 64 percent
alanine with 2.14 bits of sequence entropy, ranked 20th at a score of 88.4.

**Rule: the floors live in the selector. For challenge 4 they are pLDDT >= 63,
pDockQ2 >= 0.18, sequence entropy >= 2.5 bits, no residue above 45 percent of
the chain, and no homopolymer run of 6 or more.** Reuse
`03-glp1r/campaigns/c8-deep-junction/scripts/select-top20.py` as the base.

### C2. Verify that a gate actually ran on every design
Source: same session.

Challenge 3's activation gate had never been run on the 482 RFD4 designs. Because
that gate carried the heaviest weight, those designs capped at 56.5 against an
83.9 cutoff while holding the best binding in the pool. A full rescore moved 416
of 482 into the top tier and 17 of the final 20 came from that generator.

**Rule: before any selection, assert that every design has a row in every screen.
Print the count of ungated designs and require it to be zero.**

### C3. One writer per derived number
Source: same session. Challenge 3's selection logic was duplicated in the
submission builder and silently produced a different twenty.

**Rule: one script owns the ranking. Everything else attaches data to its
output.**

### C4. Keep one design per backbone family
Source: `03-glp1r/campaigns/c1-two-domain/LEARNINGS.md`, item 6; and the
organizers' prompt, which caps a method family at 25 percent of the selected
designs and relaxes that cap only to fill the quota.

There is a real tension here. The challenge-2 calibration found that the real
winners **converge**: 8 of 13 were near-duplicates of one backbone family. Our
batches were diverse singletons. Success looks like a family, and the submission
rules want diversity.

**Rule: sample families deeply to find the good one, then submit the family's
best member plus genuinely different designs. Hold over-cap members back as the
top-up pool rather than dropping them.**

### C5. The switch scorer is rank-grade, and the sign is the result
Source: `02-tnfa/notes/linkage-check.md`.

The vendored PROPKA linkage scorer (`tools/switch/linkage_score.py`) was about
two orders conservative against the FcRn reference. Its magnitudes are
indicative. Its sign is informative, and in challenge 2 every design's sign was
wrong.

**Rule: require `delta_log_Ka > 0` as a gate, and never quote its magnitude as a
predicted fold-change.** State the physical ceiling instead: one titratable site
changes affinity at most tenfold per pH unit, and the assay window is 1.4 pH
units. The organizers' own prompt applies exactly that sanity check.

### C6. Claim the ratio, not the absence of binding
Source: the organizers' selection prompt, via
`docs/competition-notes/08-organizer-selection-prompt.md`.

"A weak but clearly pH-sensitive binder beats a strong, insensitive one." The
prompt also checks that the mechanism is physically possible.

**Rule: the methodology states a predicted KD ratio between pH 6.0 and 7.4 and
the number of titratable sites that produce it. It never claims "no detectable
binding at pH 6.0", which is a wet-lab observation we cannot predict.**

### C7. Mouse cross-reactivity arrived only with tight designs
Source: `02-tnfa/notes/filter-calibration.md`, finding 4. The three mouse
binders had human KD of 2.1, 4.2 and 18.9 nM. Nothing weaker than 19 nM bound
mouse at all.

**Rule: do not treat cross-reactivity as a separate design goal to trade against
affinity. Design for tightness on a conserved epitope and test both species.**

---

## D. The operational traps, with their fixes

From `02-tnfa/notes/campaign-close.md`, `x3-strategy.md`,
`03-glp1r/campaigns/c1-two-domain/LEARNINGS.md` and AGENT.md.

| # | trap | fix |
|---|---|---|
| D1 | `infer_ori_strategy` unset places the binder **inside** the target. 12 designs had 24 to 61 atoms under 2 A. | Set `"infer_ori_strategy": "hotspots"`. Then count binder atoms within 2 A of the target: 0 to 2 is docked, dozens means buried. Screen every batch. |
| D2 | IPSAE finds its companion files by renaming the PAE path. Renamed Boltz outputs make pDockQ2 collapse to a floor while ipSAE stays right. | Copy Boltz outputs under their original names. Symptom: ipSAE matches a reference exactly but pDockQ2 does not. |
| D3 | A contig range that skips a residue stops RFD3 with "Residue A20 not found". | Build the contig from surviving blocks, as `02-tnfa/handoff/rfd3/make_patch.py` does. |
| D4 | A site check keyed by set name against per-design folders silently passes everything. Every fold scored against an empty site map and reported "no contact". | Assert a known-good count after any triage change. A silent zero throws no exception. |
| D5 | A shared RFD3 `out_dir` makes every later run exit in seconds doing nothing. | One fresh `out_dir` per design, `n_batches=1`, wrapped in `timeout 420`. |
| D6 | `low_memory_mode=True` on a big target is pathologically slow and produces nothing. Without it, batch >= 2 runs out of GPU memory. | Batch 1 plus chaining. |
| D7 | A large receptor's server MSA is a RAM bomb at 14.65 GiB. | Fetch once, cap depth to 1024 rows, reference it from the YAML. Use `msa: empty` for the de-novo binder chain. |
| D8 | Killing a fold runner orphans its Boltz children, which hold about 11 GB and starve the next batch. | Always check the process list after killing a runner and kill leftovers by PID. |
| D9 | A memory kill, exit 137, can still leave usable models. | Check the output directory before retrying. A retry pass recovered 8 of 8 folds once. |
| D10 | `pkill -f` and `pgrep -f` match the invoking shell's own command line. This killed the working shell three times in challenge 2 and twice again in this session. | Kill by PID, found from `ss -lptn` or the process list. |
| D11 | Trusting a downscaled screenshot. In this session a non-existent layout overflow was "fixed" three times before measurement showed the page had never overflowed. | Measure. Do not infer a number from an image. |
| D12 | Detaching a long job with `&` instead of tracking it. In this session that produced two overlapping writers on the same output files. | Run long jobs in the background through the harness so completion is reported, one writer per file. |
| D13 | Declaring a capability missing without checking. In this session the novelty prescreen was reported as unrunnable while the tool sat at `~/tools/binder-prescreen` and only needed `mmseqs` on PATH. | Check the filesystem before saying a tool is unavailable. `mmseqs` is at `~/tools/mmseqs/bin`. |

---

## E. The two challenge-3 lessons that do NOT transfer

Recorded so nobody applies them by habit.

1. **Cross-protomer interfaces.** In challenge 2 every wet-lab winner's interface
   spanned two or three protomers, and that was the productive class. In
   challenge 4 the two apical domains are **90.1 A apart**
   (`notes/epitope-analysis.md`, finding 5), so a miniprotein cannot span them.
   Every challenge-4 design is single-protomer.

2. **Fold against the full construct.** Challenge 3's rule was to generate
   against a fragment and fold against the full 409-residue receptor, because an
   ECD-only fold hid a clash. Challenge 4's dimer is 1278 residues and will not
   fold on this card. The challenge-4 split is: generate against the apical
   block, fold against **one full protomer** if memory allows, and run the clash
   check against the full dimer separately. Campaign 1 measures which fold target
   is affordable before anything depends on it.
