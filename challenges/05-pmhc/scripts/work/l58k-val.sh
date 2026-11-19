#!/usr/bin/env bash
# L58K validation: 3 boltz seeds + chai-MSA + apo fold (the swap's R6 round).
set -u
unset PYTHONPATH
V=$HOME/c5-work/l58k-val
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
BIN=$HOME/c5-work/bin
BOLTZ=$HOME/.venvs/boltz/bin/boltz
LOG=$V/logs/chain.log
mkdir -p "$V/logs" "$V/apo"
[ -f "$V/folds/l58k-apo.yaml" ] && mv "$V/folds/l58k-apo.yaml" "$V/apo/l58k-apo.yaml"
echo "L58K_VAL_START $(date -Is)" >> "$LOG"

bash "$REPO/challenges/05-pmhc/scripts/work/s3-multiseed.sh" "$V" >> "$LOG" 2>&1
bash "$REPO/challenges/05-pmhc/scripts/work/s3-chai.sh" "$V" >> "$LOG" 2>&1

while pgrep -f "boltz predict|chai-lab fold" >/dev/null; do
    sleep 60
done
echo "apo fold start $(date -Is)" >> "$LOG"
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False \
MEMLIMIT_MB=12000 timeout 1200 /usr/bin/python3 "$BIN/memlimit.py" \
    "$BOLTZ" predict "$V/apo/l58k-apo.yaml" --out_dir "$V/apo/l58k-apo" \
    --diffusion_samples 5 --output_format mmcif >> "$LOG" 2>&1
echo "L58K_VAL_END $(date -Is)" >> "$LOG"
