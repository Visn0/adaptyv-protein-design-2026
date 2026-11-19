#!/usr/bin/env bash
# C6 follow-up queue: after c7, fold (a) the best children vs WT+free (20 arms)
# and (b) the apo stability set (20 arms), scoring each.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/c6t-queue.log
echo "C6T_QUEUE_START $(date -Is)" >> "$LOG"

while pgrep -f "^bash .*c0-probe-fold" >/dev/null; do
    sleep 60
done
echo "GPU free, folding children tri-state $(date -Is)" >> "$LOG"
MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/c6t \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1

echo "tri-state done, folding apo set $(date -Is)" >> "$LOG"
MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/apo \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1

echo "folds done, scoring $(date -Is)" >> "$LOG"
cd "$REPO" || exit 1
for w in c6t apo; do
    PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
        --work $HOME/c5-work/$w --jobs 3 >> "$LOG" 2>&1
done
echo "C6T_QUEUE_END $(date -Is)" >> "$LOG"
