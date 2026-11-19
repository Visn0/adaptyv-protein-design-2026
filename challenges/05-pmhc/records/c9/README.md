# C9 — genie3 alternative-generator wave (negative result)

**Question:** can genie3 (all-atom SE(3) diffusion, the third architecture) produce
pMHC binders for this target via the same downstream pipeline?

**Pipeline built and verified:** problem JSON (hotspots C4-C8, chains A1-276/B1-99/C1-10,
binder 60-110) -> generate (100 backbones, ~1 h on the 5070) -> chain-remap converter
(genie3 emits A=binder/B=HLA/C=b2m/D=peptide) -> ProteinMPNN CA-only (the genie3 output
is a CA trace, 2 seqs/backbone, 100/100 done) -> CA-trace pose screen -> top 30 folded
-> scored.

**Result: 0/70.** Best ipTM 0.661 (c9-g3_0), peptide reads 0.00-0.04, no
JDI-like folds. The fold ranking does not correlate with the CA-screen share
(best fold had share 0.013; screen-top g3_2 fold ranks mid-pack). The bounded
retry (backbones 31-70) reproduced the first slice exactly (best raw pair
read 0.63 vs 0.69 in slice 1) - the negative is not sampling noise.

**Diagnosis:** the workstation pinpoints the failure - the CA-trace screen is
sidechain-blind. With all-atom generator output (the NIM campaigns) the pose
screen selected ~20-30% passers whose folds largely held up; on CA traces the
same geometry metrics carry no information about interface quality, so the
folded backbones were effectively a random sample. The CA-only MPNN
sequence assignment (no sidechain context) compounds this.

**Consequence:** genie3 via this pipeline does not produce competitive
binders for this target. A future attempt would need a full-atom
reconstruction step between generation and screening (e.g. re-fold each
backbone with the designed sequence first, screen the folded structures,
then filter) - i.e. the fold step itself remains the only reliable filter,
consistent with C0 and with the competition's own finding that no single
in-silico metric predicts success.

**Files:** `~/c5-work/c9/` (genie3 output, mpnn, screen.csv, s1-summary),
scripts `c9-*.py`, `c9-mpnn.sh`, `c9-queue.sh`, `c9b-queue.sh`, `c9c-queue.sh`.
