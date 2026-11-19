#!/usr/bin/env bash
# C9 fold+score: fold the 30 built genie3 designs, then score.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
C9=$HOME/c5-work/c9
LOG=$C9/fold.log
echo "C9C_START $(date -Is)" >> "$LOG"

while [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ]; do
    sleep 60
done
echo "GPU free, folding 30 c9 designs $(date -Is)" >> "$LOG"
MEMLIMIT_MB=12000 C0_WORK="$C9" \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work "$C9" --jobs 3 >> "$LOG" 2>&1
echo "C9C_END $(date -Is)" >> "$LOG"
