# Tool audit and 2026 landscape

## Target verification (done)

The challenge's three parts against our local structure (7OW6, chains A-C, TCR
removed — the challenge's own reference):

- beta2-microglobulin: exact match (99 aa).
- G12D peptide VVVGADGVGK: exact match.
- HLA-A*11:01 heavy chain: 99.1% identity; the only difference is the disordered
  C-terminal tail (LSSQT, 5 residues) unresolved in the crystal and far from the
  binding groove. Construct numbering 25-305 maps cleanly onto our chain.

Verdict: the target is correct. Scripts: `scripts/verify_target.py`,
`scripts/align_hla.py`.

## Installed tools and versions

| tool | version / commit | status |
|---|---|---|
| boltz | 2.2.1 (latest on PyPI) | current |
| chai-lab | 0.6.1 | current family (Chai-1 line) |
| openfold3 | 0.5.1 | current-ish |
| BindCraft2 | 2026-10-19 | current (Pacesa lab, UZH) |
| bioemu2 | 2026-10-20 | current |
| RFD4-Proteina | 2026-10-21 | current (our new generator) |
| genie3 | 2026-05-10 | this year |
| IPSAE | 2026-01-03 | this year |
| LigandMPNN | 2025-02-06 | maybe stale upstream |
| ProteinMPNN | 2023-06-27 | frozen upstream; LigandMPNN is the successor to use |

Torch stacks: cu128-cu132 builds across the venvs, all Blackwell-capable.

## 2026 landscape findings

1. **Boltz-2 affinity does NOT cover protein-protein binding.** The affinity
   head is small-molecule only. So no direct Kd estimate for our binder from
   boltz. We keep our own E-score and the interface metrics as the specificity
   instruments, and the wet-lab tables (ATLAS/SKEMPI) for calibration.

2. **Chai-2 (Chai Discovery)**: 16% antibody hit rate, and the Nov 2025 update
   reports a **peptide-MHC target among its validated cases**. It is not
   downloadable (access-gated product), so it stays in the watch list, but it
   confirms pMHC binder design is now routine for frontier models.

3. **The open binder-design models to evaluate** (all released after our NIM
   campaigns started):
   - **BoltzGen** (MIT, Oct 2025) — all-atom generative binder design;
     miniproteins, VHH, cyclic peptides.
   - **PXDesign** (ByteDance, Aug 2025, Apache 2.0) — diffusion generator plus
     dual-filter (Protenix + AF2-IG) selection; 17-82% nanomolar wet-lab hit
     rates across seven targets.
   - **Protenix-v2** (Apr 2026) — structure prediction that beats AF3 on some
     benchmarks, plus target-conditioned binder design.
4. **OpenDDE v1** (already installed) is the strongest open co-folder on the
   antibody-antigen benchmarks (76.1% DockQ success vs AF3's 47.9%). It should
   be our second co-folding opinion and part of the ensemble filter.
5. The Adaptyv-style closed loop (design + in-silico filter + wet lab) is now a
   published pattern, including an AI-agent run of Boltz-2 that produced a
   nanomolar binder — the same loop structure we are building.

## Recommended upgrades, in priority order

1. **BoltzGen** — MIT-licensed generative binder design, direct alternative to
   the RFD4 backbone stage. Evaluate on our target; if it matches the campaign
   funnel, it joins or replaces the generator stage in the custom-model loop.
2. **PXDesign / Protenix-v2** — ByteDance's open stack; consider as the second
   generator and as the ensemble filter for candidate selection.
3. **OpenDDE as the second co-folder** — already installed, benchmark-leading.
4. **LigandMPNN re-check + retire ProteinMPNN** from new work.
5. Watch list: Chai-2 access, Chai-1 updates.

The custom-model project's target architecture is unchanged: an in-house
generator, our calibrated scores inside the loop, and the co-folding as the
reward. These new models are the candidate pool for the generator slot.
