#!/usr/bin/env bash
# Wave3 tri-state queue (2026-11-01): after the OpenDDE JDI test releases the
# GPU, fold the 4 wave3 winners against WT + peptide-free, then score.
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/night-queue-w3b.log
echo "QUEUE_START $(date -Is)" >> "$LOG"

while pgrep -f "opendde pred" >/dev/null || kill -0 40349 2>/dev/null; do
    sleep 30
done
echo "opendde test done, starting wave3 tri-state folds $(date -Is)" >> "$LOG"

MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/s2w3 \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1

echo "folds done, scoring $(date -Is)" >> "$LOG"
cd "$REPO" || exit 1
.venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work $HOME/c5-work/s2w3 --jobs 6 >> "$LOG" 2>&1

echo "QUEUE_END $(date -Is)" >> "$LOG"
