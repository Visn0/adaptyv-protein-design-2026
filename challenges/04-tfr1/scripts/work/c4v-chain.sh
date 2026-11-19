#!/usr/bin/env bash
# Campaign-4 chain: after the main mouse screen (20 designs) ends, start the
# campaign-3 survivor screen against the same mouse target, watch it, then run
# the c4 scorer so the paired human/mouse table is ready. One GPU job at a
# time; resumes the variant unit on failure.
set -u
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
LOG="$HOME/c4-work/logs/c4-screen.log"
VLOG="$HOME/c4-work/logs/c4v-screen.log"
while ! grep -q "CHAI_SCREEN_END" "$LOG" 2>/dev/null; do sleep 60; done
echo "main mouse screen ended $(date -Is); starting variant screen"
systemctl --user start --no-block chai-c4mnv-screen
while true; do
  if grep -q "CHAI_SCREEN_END" "$VLOG" 2>/dev/null; then
    echo "variant mouse screen ended $(date -Is)"
    "$REPO/.venv/bin/python" \
      "$HOME/c4-work/bin/c4-restrained-scores.py"
    break
  fi
  state=$(systemctl --user is-active chai-c4mnv-screen 2>/dev/null)
  if [ "$state" = "failed" ]; then
    echo "variant unit failed without an end marker - resuming $(date +%H:%M:%S)"
    systemctl --user reset-failed chai-c4mnv-screen 2>/dev/null
    systemctl --user start --no-block chai-c4mnv-screen
  fi
  sleep 60
done
