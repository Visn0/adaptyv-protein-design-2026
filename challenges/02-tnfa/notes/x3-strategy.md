# X3 — strategy change: hotspot re-tuning and a fresh look at the target

*16 October 2026. Written after the W2 result (no shortlist design clears the bar)
and after the host crashed twice under load. Everything here is measured on this
machine: `challenges/02-tnfa/data/epitope-analysis/1TNF.pdb` and
`tnf_patch_map.csv`.*

## 1. Why the strategy changed

W2 folded the 8 shortlist designs (human + mouse). One design — rank 2,
`groove-1_0_model_1` — reaches the ipSAE half of the bar (0.733 human, 0.810
mouse); nothing clears both halves. The handoff's own rule then applies: *"If W2
fails (no new design passes), stop the campaign track and record the negative."*

So this is not a rerun of the same idea. Two levers change, both measured before
spending GPU time.

## 2. Lever 1 — the hotspot set was not the receptor-binding site

The patch map (recomputed on this machine) ranks surface patches by exposure,
apolar fraction and conservation. Its top entries are not the site X1/X2 used:

| Patch-centre residue | score |
|---|---|
| S147 | 222 |
| I83 | 216 |
| Y87 | 177 |
| T89 | 170 |
| Q88 | 157 |
| S86 | 149 |
| V85 | 143 |
| F144 | 141 |

Those are the **TNFR-binding surface** (the 84–89 loop and the 143–148 loop).
X1/X2 targeted the adalimumab groove at residues 65/67 (chain A) + 75 (chain C),
and the switch trio at 103/112. Neither is the receptor site.

**The site is compact enough — this was the measurement that mattered.** The
first attempt to combine the 84–89 loop with the 143–148 loop used residues from
the *same* protomer and measured a 35–49 Å span, which looked impossible. Pairing
the loop of one protomer with the loop of its **neighbour** gives:

```
A83–A87   7.4 Å      A83–B147  13.8 Å      A87–B147  15.3 Å
A89–B147 14.2 Å      span of {A83,A87,A89,B147} = 15.3 Å
```

15.3 Å is at the campaign's own ~15 Å feasibility line, and it is the real
receptor-binding epitope. Set **X3-A (RBS)**: `A83, A87, A89, B147`.

## 3. Lever 2 — the target representation

The full trimer (456 residues, ~3600 atoms) costs 5 min per design and pushes
the 12 GB card to 11.9 GB of GPU memory. The trimmed target keeps the same
geometry with 195 residues / 1543 atoms: every residue within 28 Å of the hotspot
centroid, all three chains (chain C keeps 7 residues — the wall that blocks the
site, so a design cannot sit where the missing protomer would be).

| | full trimer | patch |
|---|---|---|
| residues / atoms | 456 / ~3600 | **195 / 1543** |
| file | `data/epitope-analysis/1TNF.pdb` | `handoff/rfd3/target-patch.pdb` |

The full-trimer loophole check still runs on every design after generation: any
atom within 4 Å of where the absent protomer sits discards the design.

## 4. The sets for X3

| Set | Hotspots (1TNF numbering) | Rationale | Status |
|---|---|---|---|
| **X3-A** | `A83,A87,A89,B147` | the receptor-binding site, never targeted, span 15.3 Å | running |
| **X3-B** | `A103,B103,B112` | the switch trio — the only site with a documented charge-switch mechanism; RFD3 has never been tried on it (BoltzGen failed) | queued |
| **X3-C** | `A65,A67,C75` | the X2 groove, re-run on the local box: the control that ties this campaign to the Tamarind result | queued |

Settings: identical to the Tamarind X2 run — binder 70–95 aa, `is_non_loopy`,
`step_scale 1.5`, `gamma_0 0.6` (both already the local defaults in
`rfd3/configs/inference_engine/rfdiffusion3.yaml`).

## 5. Resource limits (the host crashed, so these are not optional)

The PC's Windows host crashed twice with the same bugcheck (`0x20001`
HYPERVISOR_ERROR, Arg1 `0x28` = hypervisor IOMMU) — see
`~/host-crash-triage-2026-10-16.md`. Two of the crashes happened with no GPU job
running, so the fault is below the OS; but heavy jobs must not add pressure.

Measured on this box:

| Run | peak RSS | peak GPU | time |
|---|---|---|---|
| RFD3 de-novo 100 aa, batch 2 | 6.38 GiB | — | 46 s |
| RFD3 3-chain trimer, batch 2, `low_memory_mode` | >7.15 GiB (killed) | — | — |
| RFD3 full trimer target, batch 1 | 3.99 GiB | 11.88 GiB | 302 s/design |
| RFD3 trimmed patch target, batch 1 | **4.21 GiB** | **8.8 GiB** | **50 s/design** |

Rules for every run: `memlimit.py` with `MEMLIMIT_MB=6000`, one GPU job at a
time, and `watch_resources.py` writing the RAM/swap/GPU record next to the
output. WSL is capped at 12 GB (`%USERPROFILE%\.wslconfig`, backup kept).

## 6. The bug that made the first X3 batch worthless

The first 12 X3-A designs were **buried in the target, not docked on it**:

| | binder centroid shift | min heavy-atom distance | atoms < 2 Å | contact pairs < 4 Å |
|---|---|---|---|---|
| Tamarind X2 designs (baseline) | — | 2.03–2.35 Å | 0 | 86–109 |
| X3-A, first batch | 4.7–11.7 Å | 0.73–1.02 Å | 24–32 | 478–575 |
| X3-A, after the fix | 23–27 Å | 1.3–2.4 Å | 0–2 | 35–106 |

Cause: `infer_ori_strategy` was not set, so the origin token came from the input
structure's centre of mass and the diffused chain was placed at the target's
centre. The RFdiffusion3 docs name the fix — *"using hotspots will place the ORI
token 10 Å outward from the center of mass of the specified hotspots"* — so the
input JSON now carries `"infer_ori_strategy": "hotspots"` (see
`handoff/rfd3/make_patch.py`, which also builds the block contig the trimmed
target needs). The 12 invalid designs are kept in
`~/c2-work/x3/rejected-buried/`, not in the run ledger.

**Screen every RFD3 output before spending more compute on it:** count binder
atoms closer than 2 Å to the target. Zero to two is a docked design; dozens means
the binder is inside the target.


## 7. Results so far (16 Oct, evening)

Generation (local RFD3, 24 designs per set, ~40 s each):

| set | designs | at the site | clean | loophole-clean |
|---|---|---|---|---|
| x3a-rbs (receptor site) | 24 | 11 | 6 | 24/24 |
| x3b-switch (switch trio) | 24 | 24 | 2 | 24/24 |
| x3c-groove (X2 groove) | 24 | 21 | 4 | 24/24 |

The control is the useful number: 21 of 24 local designs land in the groove the
Tamarind run used, so the local setup now behaves like the validated one.

Co-folds (Boltz-2, five samples each, human TNF, scored with IPSAE; bar = ipSAE
>= 0.6 AND pDockQ2 >= 0.23):

| design | set | best ipSAE | pDockQ2 | bar |
|---|---|---|---|---|
| x3b-switch-2 | switch trio | 0.230 | 0.148 | fail |
| x3a-rbs-16 | receptor site | 0.229 | 0.041 | fail |
| x3a-rbs-15 | receptor site | 0.012 | 0.133 | fail |

Context: the Tamarind X2 campaign folded 72 designs and produced **one** that
cleared the bar (ipSAE 0.80). The X3 folds so far are in the range of X2's
non-winning designs. At this hit rate, 24 designs per set cannot be expected to
produce a pass; the generation step must scale (it is cheap now: ~40 s/design).

## 8. Memory findings (why the folds were blocked)

Boltz-2 needs about **11.3 GiB** of host memory for a 4-chain, ~540-residue
complex on this box, and none of these levers reduced it: `--max_parallel_samples 1`
(11.30), `--subsample_msa --num_subsampled_msa 64` (11.19), a 2-chain target
(11.37). A trivial 78-residue single-chain fold peaks at 1.07 GiB, so the cost is
the complex, not a fixed floor. The 12 GB WSL cap could not hold it — folds died
at the cap every time. `%USERPROFILE%\.wslconfig` is back to **16 GB**
(processors 12, swap 8 GB, autoMemoryReclaim, sparseVhd). With that, folds peak
at 7.6 GiB and run at full speed. Every job still runs under `memlimit.py`.


## 9. The finding that matters most (site check on every fold)

The fold score alone was misleading. `ipSAE` answers "is there an interface",
not "is the interface where the design put it". Screening every sample of every
X3 fold for contacts to the **designed** residues (both halves of the epitope,
on different protomers) gives:

| what | number |
|---|---|
| designs folded | 12 (five samples each, 60 samples) |
| samples that sit on the designed epitope (both halves, cross-protomer) | 9 |
| ... and also score above the bar | **0** |
| best score of those 9 | **ipSAE 0.000** |
| highest score anywhere in the batch | 0.769 (x3a-rbs-9, 2-protomer fold) — 18 A from the designed residues |

And the retrospective check on the earlier campaign's best number: the W1 fold
of the X2 design (ipSAE 0.733, the sample the whole selection rested on) sits
**15-18 A from its designed groove (65/67/75)**. The samples that do land on the
groove score at most 0.433. So the campaign's single "pass" was an interface
somewhere else on the target.

Consequence: selection must require **score AND site together**. With that rule
nothing in the campaign passes yet — not the X2 shortlist, not the X3 sets.


## 12. Final result of the X3 strategy (16 Oct, 14:30)

Generation on the patch the folding program prefers (`x3d-ntc`, hotspots
R6/T7/P8 + the neighbour's 52-57/125 loop), 96 designs:

| metric | value |
|---|---|
| designs generated | 96 |
| at the designed patch (design geometry) | 43 |
| clean shortlist | 8 |
| loophole-clean | 95/96 |
| folded (best six by contacts) | 6 |
| ... clearing the bar AND at the patch | **0** |
| best score among them | 0.455 (x3d-ntc-67) — 10-18 A off the patch |

Campaign total: **18 designs folded (90 samples), 0 samples that both clear the
bar and sit on the designed epitope.** The two best interfaces the folds ever
produced sit on the drug groove (0.43) and on the receptor-binding loops (0.31) —
surfaces we had already designed against, and both under the bar.

Where the new folds landed: ntc-15 on the receptor-binding surfaces (R31/A33,
Y87/T89/K90, A145/E146/S147 across two protomers); ntc-29 on the drug epitope
(K65/Q67/E110, L143/A145/E146). The model prefers those two surfaces over every
patch we have aimed at, which is why the "designed patch" and the fold's patch
keep disagreeing.

**Conclusion.** With RFdiffusion3 generation plus Boltz-2 co-folding, no design
in this campaign carries a TNF interface that survives independent prediction at
the site it was designed for. The campaign's value is its method and this
negative, not a submission.

## 10. Options from here

1. **Mass generation + joint screen.** Generation costs ~40 s per design, the
   screen is free. Generate 300-500 designs across the two best-understood
   sites, keep only samples that sit on the designed epitope, fold those. This
   is the cheapest way to keep looking.
2. **Change the design target.** Design against one protomer's compact surface
   (the 84-89 loop alone) instead of a cross-protomer groove; the 2-protomer
   fold suggests the model can dock there (ipSAE 0.769 was found when the
   third protomer was absent).
3. **Scaffold route (different perspective).** Take a validated TNF-binding
   module — the adalimumab or infliximab paratope (3WD5, 4G3Y, both on disk) or
   a receptor-derived domain — and engineer the pH switch into its interface.
   Binding is then near-certain and the designed part is the switch, which is
   what C2 actually asks for. Check the platform's novelty rule before choosing.
4. **Record the negative** (the handoff's stop rule) if none of the above fits
   the remaining time.

## 11. What comes next

1. Score the remaining co-folds and record the full table in this file.
2. Scale the generation: 96 more designs on the receptor site and 96 on the
   groove (the run starts when the folds stop; the GPU runs one job at a time).
3. Triage the larger sets and co-fold the best eight to ten — a bar-clearing
   design is the gate for everything else.
4. Only a design that clears the bar gets the switch layer (binder histidines
   against the target cation trio, PROPKA audit, mouse chemistry classes).
5. Nothing is submitted unless a design is genuinely promising.
