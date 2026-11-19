#!/usr/bin/env bash
# C9 downstream chain: wait for the genie3 generation, then convert ->
# ProteinMPNN (CPU) -> CA screen -> fold top 30 -> score.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
C9="$HOME/c5-work/c9"
LOG=$C9/downstream.log
V="$REPO/.venv/bin/python"
echo "C9B_START $(date -Is)" >> "$LOG"

while pgrep -f "^/usr/bin/python3 $HOME/c5-work/bin/memlimit.py" >/dev/null; do
    sleep 120
done
echo "genie3 done, converting $(date -Is)" >> "$LOG"

cd "$REPO" || exit 1
PYTHONPATH= "$V" challenges/05-pmhc/scripts/work/c9-convert.py >> "$LOG" 2>&1
bash challenges/05-pmhc/scripts/work/c9-mpnn.sh >> "$LOG" 2>&1
PYTHONPATH= "$V" challenges/05-pmhc/scripts/work/c9-screen.py \
    --dir "$C9/backbones" --out "$C9/screen.csv" >> "$LOG" 2>&1
PYTHONPATH= "$V" challenges/05-pmhc/scripts/work/c9-fold-build.py --top 30 >> "$LOG" 2>&1

echo "folding c9 top 30 $(date -Is)" >> "$LOG"
while [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ]; do
    sleep 60
done
MEMLIMIT_MB=12000 C0_WORK="$C9" \
    bash "$REPO/challenges/05-pmhc/scripts/work/c0-probe-fold.sh" all >> "$LOG" 2>&1
PYTHONPATH= "$V" challenges/05-pmhc/scripts/work/s1-score.py \
    --work "$C9" --jobs 3 >> "$LOG" 2>&1
echo "C9B_END $(date -Is)" >> "$LOG"
