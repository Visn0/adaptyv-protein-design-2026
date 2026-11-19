#!/usr/bin/env bash
# E-score every folded design (the surrogate's labels) into one TSV.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
W=$HOME/c5-work
OUT=$W/ml/escores-all.tsv
mkdir -p "$W/ml"
echo "ES_ALL_START $(date -Is)" > "$W/ml/es-all.log"
: > "$OUT"
for s in s1 s1w3 camp c2p c6 s1w4 repair repair2 s1w5 s1w6; do
    for d in "$W/$s/folds"/*/; do
        name=$(basename "$d")
        cif=$(ls "$d"/boltz_results_*/predictions/*/*_model_0.cif 2>/dev/null | head -1)
        [ -z "$cif" ] && continue
        line=$(cd "$REPO" && .venv/bin/python challenges/05-pmhc/scripts/work/escore.py "$cif" 2>/dev/null | tail -1)
        [ -n "$line" ] && printf '%s\t%s\n' "$name" "$line" >> "$OUT"
    done
    echo "$s done: $(wc -l < "$OUT") rows $(date -Is)" >> "$W/ml/es-all.log"
done
echo "ES_ALL_END $(date -Is) total $(wc -l < "$OUT")" >> "$W/ml/es-all.log"
