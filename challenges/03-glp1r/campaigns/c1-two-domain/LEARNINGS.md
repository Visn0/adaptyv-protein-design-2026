# Campaign 1 — learnings (recorded 2026-10-18)

Everything learned running campaign 1, kept for the next campaigns. Tool-level
versions of the operational items also live in the `protein-binder-design`
skill (`references/rfd3-boltz-ops.md`).

## Science

1. **The two-domain signature is achievable but rare at 60–100 aa.** 39 of 335
   folded samples (~12 %; 21 of 77 designs) touch both the groove and the
   TM-side path with a clean interface. Junction-only hotspot sets raise the
   rate (14 % → 25 % across batches) — targeting the interface directly beats
   asking one binder to span two distant sites.
2. **Generating against the fragment and folding against the full construct is
   the right split.** The generation target must stay ≤ ~250 residues for RFD3
   to run; the fold must be the full 409-residue receptor or the ECD-only
   clash trap stays invisible. Our screen's clash column caught designs the
   public challenge-3 repos submitted blind.
3. **Reach must be measured in the active conformation.** Verify the fold's
   receptor state (intra-receptor CA distances vs 6X18) before trusting any
   contact-depth metric — a closed/auto-inhibited receptor makes unrelated
   contacts look like reach. Boltz folded the receptor active with the
   depth-capped MSA; check every time.
4. **The groove alone is the antagonist trap.** Designs that dock only the
   groove (many of ours) are exactly the published antagonist outcome; they
   bank affinity at best. The ECL3/TM6–7 reach (residues 376–391, anchor E387)
   is the distinguishing feature worth ranking on.
5. **RFD3's binders are alanine-rich helices.** Plain ProteinMPNN
   re-sequencing collapses to poly-A; the working refinement is
   fixed-interface MPNN (pin the co-folded contact set, redesign the periphery
   at temp 0.3). Even then the variants stay same-family — good as alternates,
   not as new submissions.
6. **One design per family for the competition.** The prescreen flags
   same-backbone variants as batch duplicates; the diversity filter is real.

## Operations (the hard-won bits)

7. **RFD3 keeps per-out_dir run state.** A shared out_dir makes every later
   invocation exit in seconds doing nothing; one fresh out_dir per design with
   `n_batches=1`, wrapped in `timeout 420`, is the resumable, crash-proof
   shape. A rare slow path (10+ min, CPU-bound) hits ~1 in 10 designs — the
   timeout skips it.
8. **`low_memory_mode=True` is a trap for big targets** (pathologically slow,
   no output); without it, batch ≥ 2 GPU-OOMs. Batch 1 + chaining is the
   stable point (~33 s/design at 213 residues).
9. **A big human receptor's server MSA is a RAM bomb** (14.65 GiB, watchdog
   kills). Fetch once, depth-cap to 1024 rows, reference from the YAML;
   `msa: empty` for de-novo binder chains. Folds then run ~90 s at ~11.7 GiB.
10. **Killing a fold runner orphans its Boltz children** (~11 GB RAM + GPU
    held). They starve the next batch into memlimit kills. Always `ps` after
    killing a runner; kill leftovers by PID.
11. **A memlimit kill (exit 137) can still leave usable models.** Check the
    output directory before retrying; the retry pass recovered 8 of 8 lost
    folds.
12. **`pkill -f`/`pgrep -f` patterns match the invoking shell's own command
    line** — this killed the working shell three times and made two watchers
    immortal. Use the bracket trick (`"name[.]sh"`) or explicit PIDs.

## What we would do differently

- Start with the junction-only hotspot set (E1b/E1b2), not the two-site set.
- Fold every design with the depth-capped MSA from the very first batch.
- Rank by the reach composite from the start instead of re-screening.
- For agonism specifically: the next campaigns should try modalities whose
  designs have actually activated GLP1R in published cAMP assays (campaign 2).
