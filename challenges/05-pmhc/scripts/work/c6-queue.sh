#!/usr/bin/env bash
# C6 step 3: fold the 80 children against G12D, then score.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/c6/queue.log
echo "C6_QUEUE_START $(date -Is)" >> "$LOG"

while pgrep -f "^bash .*c0-probe-fold" >/dev/null; do
    sleep 60
done
echo "GPU free, folding children $(date -Is)" >> "$LOG"

MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/c6 \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1

echo "children folded, scoring $(date -Is)" >> "$LOG"
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work $HOME/c5-work/c6 --jobs 3 >> "$LOG" 2>&1

echo "C6_QUEUE_END $(date -Is)" >> "$LOG"
