#!/usr/bin/env bash
# Build Boltz-2 restrained folds for the finalist designs (the ipSAE pass).
# Motivation (2026-10-27): ipSAE needs a PAE matrix; chai's CLI does not write
# one, but Boltz-2 does. This pass gives the finalists a third independent fold
# (Boltz-2 + pocket constraints) plus ipSAE / pDockQ / asymmetric ipTM via
# DunbrackLab/IPSAE. CPU-only; runs later on the GPU when it frees.
set -eu
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
WORK="$HOME/c4-work/boltz-finalists"
CHAI="$HOME/c4-work/chai/designs"
MSA="$REPO/challenges/04-tfr1/inputs/msa/18b357b72434-d1024.a3m"
mkdir -p "$WORK"

# design -> pocket contact residues (target sequence numbering, E12 set)
build() {
  local name="$1"; local contacts="$2"
  local fa="$CHAI/$name/in.fasta"
  [ -f "$fa" ] || { echo "missing $fa"; return 1; }
  /usr/bin/python3 - "$name" "$fa" "$WORK" "$MSA" "$contacts" <<'PY'
import pathlib, re, sys
name, fa, work, msa, contacts = sys.argv[1:6]
seqs = re.findall(r'^>.*\n([A-Z]+)', pathlib.Path(fa).read_text(), re.M)
assert len(seqs) >= 2, f'{fa}: need 2 chains'
target, binder = seqs[0], seqs[1]   # chai in.fasta: A=target (639), B=binder
assert len(target) > len(binder), f'{fa}: expected target first, got {len(target)} vs {len(binder)}'
pairs = ', '.join(f'[B, {c}]' for c in contacts.split(','))
yaml = f"""version: 1
sequences:
  - protein:
      id: A
      sequence: {binder}
      msa: empty
  - protein:
      id: B
      sequence: {target}
      msa: {msa}
constraints:
  - pocket:
      binder: A
      contacts: [{pairs}]
      max_distance: 6
"""
out = pathlib.Path(work) / f'{name}.yaml'
out.write_text(yaml)
print(f'wrote {out.name} ({len(binder)} + {len(target)} aa, contacts {contacts})')
PY
}

build e12rfd4_r5d1  223,253
build b3_E12_r90003 223,253
build e12rfd4_r4d5  223,253
build b3_E12_r110007 223,253
build c3_e12rfd4_r5d1_l2 223,253
echo "--- queue:"
ls "$WORK"/*.yaml
