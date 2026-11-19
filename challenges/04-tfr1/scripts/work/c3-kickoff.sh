#!/usr/bin/env bash
# Campaign-3 step 1, run at campaign-2 completion: read the final C2 restrained
# scores, pick His positions on the qualifying designs, build the variants.
# Then the operator starts the chai-c3-screen unit + c3-screen-watchdog.
set -u
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
WORK="$HOME/c4-work"
PY="$REPO/.venv/bin/python"

echo "### c3 pick $(date -Is)"
"$PY" "$WORK/bin/c3-pick-positions.py"
echo "### c3 build $(date -Is)"
"$PY" "$WORK/bin/c3-build-designs.py" --max-designs 10 --ladder
echo "### queue:"
cat "$WORK/chai/c3-screen-list.txt"
echo "C3_KICKOFF_DONE $(date -Is)"
