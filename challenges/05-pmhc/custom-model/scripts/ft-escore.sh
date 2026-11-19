#!/usr/bin/env bash
# E-score the fine-tuned funnel folds with the v2 (histidine-aware) instrument,
# one row per design, using the best model of each fold. Same shape as es-all.sh.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
W=${FT_WORK:-$HOME/c5-work/ft-batch}
OUT=$W/escores-v2.tsv
LOG=$W/logs/escore.log
mkdir -p "$W/logs"
echo "FT_ESCORE_START $(date -Is)" >> "$LOG"
: > "$OUT"
for d in "$W"/folds/*/; do
    name=$(basename "$d")
    case "$name" in *__*) continue ;; esac
    cif=$(ls "$d"/boltz_results_*/predictions/*/*_model_0.cif 2>/dev/null | head -1)
    [ -z "$cif" ] && continue
    line=$(cd "$REPO" && PYTHONPATH= .venv/bin/python \
        challenges/05-pmhc/scripts/work/escore2.py "$cif" 2>/dev/null | tail -1)
    [ -n "$line" ] && printf '%s\t%s\n' "$name" "$line" >> "$OUT"
done
echo "FT_ESCORE_END $(date -Is) rows $(wc -l < "$OUT")" >> "$LOG"
