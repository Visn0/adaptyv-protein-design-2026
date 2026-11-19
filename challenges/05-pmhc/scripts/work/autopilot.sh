#!/usr/bin/env bash
# Evo autopilot v2: full cycle per generation - breed, fold, score, tri-state,
# auto-apply winners (with the guardrails inside evo-apply), validation queue.
# Usage: autopilot.sh <first-gen> <last-gen>
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG=$HOME/c5-work/evo/autopilot.log
cd "$REPO" || exit 1
for g in $(seq "$1" "$2"); do
    echo "=== AUTOPILOT gen$g start $(date -Is) ===" >> "$LOG"
    PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/evo.py "$g" >> "$LOG" 2>&1
    PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/evo-tri-auto.py "$g" >> "$LOG" 2>&1
    PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/evo-apply.py "$g" >> "$LOG" 2>&1
    V=$HOME/c5-work/val-gen$g
    if [ -d "$V/designs" ]; then
        bash challenges/05-pmhc/scripts/work/val-run.sh "$V" >> "$LOG" 2>&1
    fi
    echo "=== AUTOPILOT gen$g done $(date -Is) ===" >> "$LOG"
done
echo "=== AUTOPILOT complete $(date -Is) ===" >> "$LOG"
