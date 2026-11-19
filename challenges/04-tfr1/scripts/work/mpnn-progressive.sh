#!/usr/bin/env bash
# Front-load the CPU work: while Genie 3 generation runs on the GPU, keep
# screening new designs and turning them into sequences. Exits after
# generation stops and one final pass ran clean.
set -u
WORK=$HOME/c4-work
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
PY="$REPO/.venv/bin/python"
while true; do
    "$PY" "$WORK/bin/screen-gen-geometry.py" > "$WORK/logs/geometry.log" 2>&1
    bash "$WORK/bin/mpnn-c4.sh" > "$WORK/logs/mpnn.log" 2>&1
    if ! pgrep -f "genie3 generat[e]" >/dev/null 2>&1; then
        sleep 30
        if ! pgrep -f "genie3 generat[e]" >/dev/null 2>&1; then break; fi
    fi
    sleep 90
done
echo "MPNN_PROGRESSIVE_DONE $(date -Is)"
