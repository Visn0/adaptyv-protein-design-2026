#!/usr/bin/env bash
# C7 queue (2026-11-01): after the c6 children finish, fold the 8 rule-scored
# candidates against WT + peptide-free (16 arms), then score.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/c7-queue.log
echo "C7_QUEUE_START $(date -Is)" >> "$LOG"

while pgrep -f "^bash .*c0-probe-fold" >/dev/null; do
    sleep 60
done
echo "GPU free, folding c7 tri-state $(date -Is)" >> "$LOG"

MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/c7 \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1

echo "c7 folds done, scoring $(date -Is)" >> "$LOG"
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work $HOME/c5-work/c7 --jobs 3 >> "$LOG" 2>&1

echo "C7_QUEUE_END $(date -Is)" >> "$LOG"
