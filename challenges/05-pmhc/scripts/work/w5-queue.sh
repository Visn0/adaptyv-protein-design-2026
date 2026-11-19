#!/usr/bin/env bash
# Wave5 chain: wait for generation, collect, pose-screen, build folds,
# wait for a free GPU, fold, score, E-score.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
S=$HOME/c5-work/s1w5
LOG=$S/queue.log
mkdir -p "$S"
echo "W5_CHAIN_START $(date -Is)" >> "$LOG"

# 1. wait for the 25th generation call
while [ ! -f $HOME/c5-work/c1/wave5-peprim/run-025/summary.json ]; do
    sleep 60
done
echo "generation complete $(date -Is)" >> "$LOG"
cd "$REPO" || exit 1

# 2. collect + pose screen
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/c1-collect.py >> "$LOG" 2>&1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s0-pose-screen.py \
    --dir $HOME/c5-work/c1/wave5-peprim --out "$S/screen.csv" >> "$LOG" 2>&1
echo "screen: $(tail -1 "$S/screen.csv" 2>/dev/null)" >> "$LOG"

# 3. fold yamls for the passers
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-build-fold-yamls.py \
    --screen "$S/screen.csv" --designs $HOME/c5-work/c1/wave5-peprim \
    --out "$S/folds" --state g12d >> "$LOG" 2>&1
echo "yamls: $(ls "$S/folds"/*.yaml 2>/dev/null | wc -l)" >> "$LOG"

# 4. wait for a free GPU (serialized), then fold + score
while [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ] \
      || pgrep -f "^bash .*c0-probe-fold" >/dev/null \
      || pgrep -f "^bash .*run-ensemble" >/dev/null; do
    sleep 60
done
echo "GPU free, folding $(date -Is)" >> "$LOG"
MEMLIMIT_MB=12000 C0_WORK="$S" \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py \
    --work "$S" --jobs 3 >> "$LOG" 2>&1
PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/escore.py \
    "$S"/folds/*/boltz_results_*/predictions/*/*_model_0.cif >> "$LOG" 2>&1
echo "W5_CHAIN_END $(date -Is)" >> "$LOG"
