#!/usr/bin/env bash
# Night queue (2026-10-31): after the stage-2 tri-state folds finish, fold the
# 40 wave3/probe-nim passers (G12D), then score them with the full scorer.
# Waits on the stage-2 runner's log marker (not a pid - no reuse hazard).
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/night-queue.log
S2LOG=$HOME/c5-work/s2/logs/probe.log
echo "QUEUE_START $(date -Is)" >> "$LOG"

while ! grep -q "ALL ARMS DONE" "$S2LOG" 2>/dev/null; do
    sleep 60
done
echo "stage-2 done, starting wave3 folds $(date -Is)" >> "$LOG"

MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/s1w3 \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1

echo "wave3 folds done, scoring $(date -Is)" >> "$LOG"
cd "$REPO" || exit 1
.venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work $HOME/c5-work/s1w3 --jobs 6 >> "$LOG" 2>&1

echo "QUEUE_END $(date -Is)" >> "$LOG"
