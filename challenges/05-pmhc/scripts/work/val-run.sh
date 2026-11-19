#!/usr/bin/env bash
# v4 validation: 3 seeds + chai + apo for the three swapped designs.
set -u
unset PYTHONPATH
V=${1:-$HOME/c5-work/val-run}
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
BIN=$HOME/c5-work/bin
BOLTZ=$HOME/.venvs/boltz/bin/boltz
LOG=$V/logs/chain.log
mkdir -p "$V/logs"
echo "VAL_RUN_START $(date -Is)" >> "$LOG"
bash "$REPO/challenges/05-pmhc/scripts/work/s3-multiseed.sh" "$V" >> "$LOG" 2>&1
bash "$REPO/challenges/05-pmhc/scripts/work/s3-chai.sh" "$V" >> "$LOG" 2>&1
while pgrep -f "boltz predict|chai-lab fold" >/dev/null; do sleep 60; done
for a in "$V"/apo/*.yaml; do
    n=$(basename "$a" .yaml)
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False \
    MEMLIMIT_MB=12000 timeout 1200 /usr/bin/python3 "$BIN/memlimit.py" \
        "$BOLTZ" predict "$a" --out_dir "$V/apo/$n" --diffusion_samples 5 \
        --output_format mmcif >> "$LOG" 2>&1
done
echo "VAL_RUN_END $(date -Is)" >> "$LOG"
