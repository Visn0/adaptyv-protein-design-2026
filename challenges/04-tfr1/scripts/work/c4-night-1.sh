#!/usr/bin/env bash
# Challenge 4 campaign 1, stages after generation:
#   geometry screen -> MPNN sequences -> fold yamls -> fold chain -> fold screen.
# One GPU job at a time (the fold chain enforces it), CPU stages overlap folds.
set -u
WORK=$HOME/c4-work
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
PY="$REPO/.venv/bin/python"
TARGET=${TARGET:-full}
cd "$WORK" || exit 1

# wait for generation to finish (sentinel in the gen log, or no genie3 running)
while pgrep -f "genie3 generate" >/dev/null 2>&1; do sleep 60; done
sleep 30
echo "### stage 1: geometry screen $(date -Is)"
"$PY" "$WORK/bin/screen-gen-geometry.py" | tee "$WORK/logs/geometry.log"

echo "### stage 2: MPNN sequences $(date -Is)"
bash "$WORK/bin/mpnn-c4.sh" | tee "$WORK/logs/mpnn.log"

echo "### stage 3: fold yamls (target=$TARGET) $(date -Is)"
"$PY" "$WORK/bin/build-c4-fold-yamls.py" --target "$TARGET" | tee "$WORK/logs/build-fold-yamls.log"

echo "### stage 4: fold chain $(date -Is)"
bash "$WORK/bin/run-c4-folds.sh" | tee "$WORK/logs/folds-chain.log"

echo "### stage 5: fold screen (target=$TARGET) $(date -Is)"
"$PY" "$REPO/challenges/04-tfr1/scripts/screen_folds_c4.py" \
    "$WORK/folds" --target "$TARGET" > "$WORK/logs/folds-screen.log" 2>&1
echo "### stage 5 end: $(tail -2 "$WORK/logs/folds-screen.log" | head -1)"
echo "C4_NIGHT1_DONE $(date -Is)"
