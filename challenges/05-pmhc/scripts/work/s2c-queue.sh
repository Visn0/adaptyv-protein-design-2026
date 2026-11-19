#!/usr/bin/env bash
# Tri-state queue for the new campaigns' winners (2026-11-01): fold the 13
# designs against WT + peptide-free (26 arms), then score.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/s2c-queue.log
echo "S2C_QUEUE_START $(date -Is)" >> "$LOG"

while pgrep -f "c0-probe-fold|boltz predict" >/dev/null; do
    sleep 60
done
echo "GPU free, folding tri-state $(date -Is)" >> "$LOG"

MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/s2c \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1

echo "folds done, scoring $(date -Is)" >> "$LOG"
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work $HOME/c5-work/s2c --jobs 3 >> "$LOG" 2>&1

echo "S2C_QUEUE_END $(date -Is)" >> "$LOG"
