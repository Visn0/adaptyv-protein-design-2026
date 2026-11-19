#!/usr/bin/env bash
# Wave4 tri-state: fold the 7 wave4 leaders vs WT + free, score.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/s1w4t-queue.log
echo "W4T_START $(date -Is)" >> "$LOG"
while [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ]; do
    sleep 60
done
echo "GPU free, folding wave4 tri-state $(date -Is)" >> "$LOG"
MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/s1w4t \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work $HOME/c5-work/s1w4t --jobs 3 >> "$LOG" 2>&1
echo "W4T_END $(date -Is)" >> "$LOG"
