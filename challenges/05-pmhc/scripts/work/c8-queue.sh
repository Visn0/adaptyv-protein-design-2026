#!/usr/bin/env bash
# C8 queue: cross-panning folds (9-mer / G12V / G12C) for 14 designs.
# Waits for BOTH the GPU and the c7 queue to fully exit (serialization: two
# waiters waking together must never start two GPU jobs - that crashed the host).
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/c8-queue.log
echo "C8_QUEUE_START $(date -Is)" >> "$LOG"

while pgrep -f "^bash .*c0-probe-fold" >/dev/null \
      || pgrep -f "^bash .*c7-queue.sh" >/dev/null; do
    sleep 60
done
echo "GPU free and c7 exited, folding cross-panning $(date -Is)" >> "$LOG"

MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/c8 \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1

echo "c8 folds done, scoring $(date -Is)" >> "$LOG"
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work $HOME/c5-work/c8 --jobs 3 >> "$LOG" 2>&1

echo "C8_QUEUE_END $(date -Is)" >> "$LOG"
