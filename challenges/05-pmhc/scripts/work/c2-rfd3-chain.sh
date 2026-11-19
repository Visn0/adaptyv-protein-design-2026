#!/bin/bash
# C2: local RFdiffusion3 hedge - per-design out_dir chain.
#
# The C3 lessons drive the shape:
#  1. RFD3 keeps per-out_dir run state; a fresh out_dir per design yields
#     exactly one new design per round (a shared out_dir exits in seconds).
#  2. A rare nondeterministic slow path (10+ min, CPU-bound) hits some
#     designs, so every round runs under `timeout` and the chain moves on.
#  Target: the organizer G12D pMHC (A=HLA 1-276, B=b2m 1-99, C=peptide
#  1-10), hotspots on the peptide P4-P8 ridge (10-mer register: the Asp is
#  P6), binder 60-110 matching C1.
#  Shared-GPU protocol: yield to any fold already running before the loop.
#
# Usage: bash c2-rfd3-chain.sh [target_designs] [round_timeout_s]
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
WORK=$HOME/c5-work/c2
BIN=$HOME/c5-work/bin
OUT=$WORK/rfd3-e1
IN=$REPO/challenges/05-pmhc/inputs/rfd3-c2.json
LOG=$WORK/logs/c2-gen.log
TARGET=${1:-200}
ROUND_TIMEOUT=${2:-420}

mkdir -p "$OUT" "$WORK/logs"
echo "C2_RFD3_CHAIN_START $(date -Is)" | tee -a "$LOG"

# Shared-GPU protocol: yield while ANY fold is running (boltz/chai by name,
# and any other GPU job by memory watermark - the other session's rescue
# chain fires the moment my folds stop, so a name-only guard is not enough).
# Note: "rfd3 design" (not "rfd3") - a bare pattern matches this script's
# own command line and self-locks the guard.
while pgrep -f "chai-lab fold|boltz predict|rfd3 design" >/dev/null \
      || [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 3000 ]; do
    echo "### waiting for the GPU (fold or >3GB in use) $(date -Is)"
    sleep 60
done

for round in $(seq 1 2000); do
    n=$(ls "$OUT"/*/*.cif.gz 2>/dev/null | wc -l)
    echo "### round $round: have $n designs $(date -Is)"
    if [ "$n" -ge "$TARGET" ]; then break; fi
    RD=$(printf "%s/r%04d" "$OUT" "$round")
    mkdir -p "$RD"
    timeout "$ROUND_TIMEOUT" /usr/bin/python3 "$BIN/memlimit.py" \
        $HOME/.venvs/rfd3/bin/rfd3 design \
        out_dir="$RD" inputs="$IN" \
        diffusion_batch_size=1 n_batches=1 low_memory_mode=False >> "$LOG" 2>&1
    rc=$?
    n2=$(ls "$OUT"/*/*.cif.gz 2>/dev/null | wc -l)
    echo "### round $round done rc=$rc designs=$n2 $(date -Is)"
    sleep 20
done
echo "C2_RFD3_END $(date -Is)"
