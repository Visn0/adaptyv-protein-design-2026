#!/usr/bin/env bash
# Wave4 queue: fold the 39 wave4 passers (G12D), score, then the 3 apo
# top-ups. Waits for a free GPU (anchored guard + VRAM check).
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/s1w4-queue.log
echo "W4_QUEUE_START $(date -Is)" >> "$LOG"

while [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ] \
      || pgrep -f "^bash .*c0-probe-fold" >/dev/null; do
    sleep 60
done
echo "GPU free, folding wave4 passers $(date -Is)" >> "$LOG"
MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/s1w4 \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work $HOME/c5-work/s1w4 --jobs 3 >> "$LOG" 2>&1

echo "wave4 scored, apo top-up $(date -Is)" >> "$LOG"
MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/apo2 \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1
echo "W4_QUEUE_END $(date -Is)" >> "$LOG"
