#!/usr/bin/env bash
# ArcRefine batch: refine the top designs serially (strict one-GPU-job rule).
# Waits for the champion's test run, then processes every config in order.
set -u
ARC=$HOME/tools/ArcRefine
C5=$HOME/c5-work/arcrefine
LOG=$C5/batch.log
RUNNER='^$HOME/tools/ArcRefine/.venv/bin/python .*structural-carryover'
echo "ARC_BATCH_START $(date -Is)" >> "$LOG"

while pgrep -f "$RUNNER" >/dev/null; do
    sleep 60
done
for cfg in "$C5"/*.json; do
    name=$(basename "$cfg" .json)
    [ "$name" = "champion" ] && continue
    [ -d "$C5/$name-run" ] && { echo "skip $name (done)" >> "$LOG"; continue; }
    while pgrep -f "$RUNNER" >/dev/null \
          || [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ]; do
        sleep 60
    done
    echo "### $name start $(date -Is)" >> "$LOG"
    ( cd "$ARC" && .venv/bin/structural-carryover "$cfg" --output "$C5/$name-run" ) >> "$LOG" 2>&1
    echo "### $name done rc=$? $(date -Is)" >> "$LOG"
done
echo "ARC_BATCH_END $(date -Is)" >> "$LOG"
