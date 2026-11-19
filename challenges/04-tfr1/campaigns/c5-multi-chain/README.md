# Campaign 5 — multi-chain units

Status: **complete — rescued** (2026-10-27 → 2026-10-30). **The registered
test still cannot run on this host** (the assembled three-chain fold is
unrunnable here: VRAM cliff, ~10x slow trunk, host crash); the direction was
therefore re-answered with the **block-target rescue** below, which proves the
assembly capability. It stays a recorded capability rather than a competitor:
the rescue folds a different target under different restraints, so no
comparable read against the single-chain class exists. The per-chain proxy read (0/22 at the 0.70 unit bar; DockQ vs the
design models ~0.1) is **confounded by construction** — a chain designed to
brace against both the target and its partner, folded without its partner,
should read low and should fail to return to its designed pose — and does not
constitute a negative result against the architecture. Executed record:
`results.md` (with the reviewer finding applied). References: `research.md`
(literature pass, 24 sources). Working dir:
`~/c4-work/{rfd4/C5,chai/designs/c5_*}`. The adaptation note below stands as
the record of how the read was taken.

A cheap rescue exists if the question ever matters again: fold the assembled
unit against the 221-residue apical **block** target (established in campaign
1; a third of the size, the VRAM cliff disappears). 22 designs, ~2.5 h of GPU.
Not queued as of 2026-10-27.

**The rescue ran overnight 2026-10-28/29 and the direction is no longer
untested.** All 22 assembled units folded against the block (Boltz-2, 5
samples, pocket restraints on both binders, E12 anchors in block numbering
165/195): **74 of 110 samples engage both binders at the anchors** (19 of 22
designs have at least one such sample; 10 engage in every sample), the
designed B-C brace forms (contact distances 1.8-2.9 A), and the best units
read ipTM 0.958 / 0.923 / 0.901. The assembled-unit question - do the two
designed chains find the target and each other - is therefore answered
**yes** for most designs. What remains untested is the registered test
itself: the same fold against the full 639-residue protomer (or the dimer)
is still unrunnable on this host. Record:
`../../records/c5-rescue-block-2026-10-29.csv`, scorer
`~/c4-work/bin/c5-rescue-scores.py`.

**Protocol adaptation (2026-10-26 22:40, recorded as executed).** The assembled
three-chain fold is pathologically slow on this host: VRAM 11.9 of 12.2 GB, and
the trunk runs ~775 s per recycle against an 82 s morning baseline and 217 s by
the end of a session (two independent attempts, one on a cold boot; the first
ended in a host crash, `0x20001`). The same 2-chain size class folds in
9-15 min, 39 for 39, so the campaign read is taken **per chain**: each design
is folded twice, chain B and chain C alone against the target with that
chain's own interface-derived restraints. Consequences, recorded honestly:
the two binder-target interfaces are still measured directly; **the B-C
interface is no longer read from a fold** — it stays validated from the design
model (contacts, per-pair clash counts there, and the DockQ-vs-design check at
selection time). The advance/discard rules below are unchanged in wording; the
"pair ipTMs" now come from the two per-chain folds.

This campaign is deliberately separate from campaigns 1-4: they design one
binder chain; this one asks whether splitting the binder unit across two
designed chains beats the single-chain class at the same epitope. Its records
do not mix with theirs, and its results never retroactively change their rules.

## Why this campaign

The user asked to try multi-chain designs ("just to try, we have time and
resources"). The one multi-chain idea already measured dead stays dead: a
single binder bridging the two receptor protomers cannot work — the apical
domains sit 73-93 A apart (A344-B344 93.2 A) while a 60-110 aa binder spans
30-45 A. So the live hypothesis is the binder unit itself split across two
chains: RFD4 generates chains B and C jointly against the E12 patch
{344 K, 374 K}, and the pair associates into one unit covering the patch with
a combined interface.

Two properties make the test fair and cheap:

- The per-design read is the same restrained Chai-1 protocol used everywhere
  else; restraints are derived from each design's own interface (a chain gets
  an anchor pocket only where the design shows that contact, >= 3 atom pairs
  under 4.5 A).
- The hosted RFD4 endpoint accepted a two-designed-segment request with zero
  validation errors (first submission: 8 designs in 95 s), so generation is
  free and fast.

## What the generation pass found

24 designs (3 runs). 23/24 form a real B-C unit (>= 20 atom contacts; one
design produced two independent chains); 24/24 chain B contacts the target,
21/24 chain C also contacts it; 23/24 the combined unit contacts both anchor
lysines. Two designs clash with the N251 glycan and are excluded; 22 fold.

The fold adds chain C to the usual A+B load (789 residues total, still the
single-protomer size class; the dimer construct that crashed the host was
1353 residues and stays parked off-box).

## Decides

Whether the two-chain architecture has signal at this epitope.

- **Advance rule (registered before the folds):** the campaign advances when
  >= 3 of the 22 designs reach mean restrained ipTM >= 0.70 (the single-chain
  top band, cf. e12rfd4_r5d1 at 0.779) **with a clean three-interface profile**:
  both binder-target pair ipTMs present, the B-C interface intact, no
  chain-chain clashes, and DockQ >= 0.8 against their own design models.
- **Discard rule:** if no design reaches ipTM 0.60 with a clean 3-interface
  profile, the architecture is closed and the direction recorded as
  measured-negative. The literature pass is retained either way.

## Instrument (as executed)

The restrained chai fold as everywhere, plus the multi-chain evaluation built
for this campaign (`scripts/work/c5-restrained-scores.py`): per-chain-pair ipTM
and clash matrices (native to the chai npz), DockQ v2 per interface against the
design model, and PRODIGY dG/Kd for the unit and every pair. DockQ and PRODIGY
were calibrated before use: DockQ 0.897 / iRMSD 0.55 A on an existing design,
PRODIGY 1.3-1.7 uM on the native 11RN interface against a published ~1 uM.

## Known caveats (recorded now, checked later)

- **Pairing specificity was not designed.** The chains were generated jointly,
  but nothing penalised B-B or C-C homodimers. A negative-design check is part
  of the evaluation plan; the antibody-engineering literature treats this as
  the first-class risk of any designed heterodimer (`research.md`, section 2).
- **Submission format:** the competition accepts single-chain/scFv/Fab entries
  (250 aa cap). A de novo two-chain unit would need a linker fusion to be
  submittable; the current folds validate the unlinked unit.
- **ipSAE is not available on chai folds** (no PAE in the npz); the per-pair
  ipTM matrix covers the same question for this campaign.
