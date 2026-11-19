# PC handoff (RTX 5070 Ti / WSL2)

The self-contained guide and data package live in
[`../handoff/`](../handoff/): read `handoff/README.md` first.

Package contents: the 8 clean X2 candidates (sequences, PDBs, ready Boltz-2
YAML files), the human and mouse target constructs, both triage CSVs, the fold
metrics, all job records, the full notes, and the two original result zips.
`handoff/SHA256SUMS` verifies the files after the transfer.

Quick start on the PC: unpack, verify with `shasum -a 256 -c SHA256SUMS`,
then follow `README.md` W0 → W1 → W2 (setup, reproduce the known fold, fold
the shortlist). The archived copy: `handoff/c2-handoff.tar.gz`.

Archive record: 45 files, built and verified on 15 Oct 2026 (extracted copy,
all checksums OK). The sha256 of the delivered archive is quoted in the
session chat.
