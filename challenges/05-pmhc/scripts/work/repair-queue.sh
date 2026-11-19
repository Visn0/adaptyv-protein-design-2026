#!/usr/bin/env bash
# R2 repair round: fold the 24 charge-directed variants, score, E-score them.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
R=$HOME/c5-work/repair
LOG=$R/queue.log
echo "REPAIR_START $(date -Is)" >> "$LOG"
while [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ]; do
    sleep 60
done
echo "GPU free, folding 24 repair variants $(date -Is)" >> "$LOG"
MEMLIMIT_MB=12000 C0_WORK="$R" \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1
cd "$REPO" || exit 1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work "$R" --jobs 3 >> "$LOG" 2>&1
# E-score the variants (the fold paths)
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/escore.py \
    "$R"/folds/*/boltz_results_*/predictions/*/*_model_0.cif >> "$LOG" 2>&1
echo "REPAIR_END $(date -Is)" >> "$LOG"
