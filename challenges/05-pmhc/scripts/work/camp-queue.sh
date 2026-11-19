#!/usr/bin/env bash
# Campaign queue (2026-11-01): after the c2 folds finish, fold the 94
# passers of the three new campaigns (nat/tight/mini), then score them.
# Lean: one GPU job at a time; scorer at reduced parallelism.
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/camp-queue.log
C2LOG=$HOME/c5-work/c2p/logs/probe.log
echo "CAMP_QUEUE_START $(date -Is)" >> "$LOG"

# Wait until NO fold runner and NO boltz is alive. A log-marker wait is not
# safe here: an earlier failed cascade already wrote "ALL ARMS DONE" into the
# c2 log, and the queue started a second concurrent GPU job off that stale
# marker. Process state cannot go stale.
while pgrep -f "c0-probe-fold|boltz predict" >/dev/null; do
    sleep 60
done
echo "GPU free, starting campaign folds $(date -Is)" >> "$LOG"

MEMLIMIT_MB=12000 C0_WORK=$HOME/c5-work/camp \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1

echo "campaign folds done, scoring $(date -Is)" >> "$LOG"
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work $HOME/c5-work/camp --jobs 3 >> "$LOG" 2>&1

echo "CAMP_QUEUE_END $(date -Is)" >> "$LOG"
