#!/usr/bin/env bash
# Repair tri-state: fold the 4 best variants vs WT + peptide-free, score.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
R=$HOME/c5-work/repair
LOG=$R/tristate/queue.log
echo "RT_START $(date -Is)" >> "$LOG"
while [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ]; do
    sleep 60
done
MEMLIMIT_MB=12000 C0_WORK="$R/tristate" \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work "$R/tristate" --jobs 3 >> "$LOG" 2>&1
echo "RT_END $(date -Is)" >> "$LOG"
