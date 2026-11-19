#!/usr/bin/env bash
# Watchdog for the campaign-2 restrained screen (unit chai-c2-screen).
# - resumes the unit on crash (state 'failed'), respects the PAUSE flag
# - on CHAI_SCREEN_END: runs both scorers (C1 set table + C2 arm table) and
#   exits, so Hermes is notified with the results in the output.
set -u
LOG=$HOME/c4-work/logs/c2-screen.log
AGG=$HOME/c4-work/logs/c2-restrained-aggregate.log
PY=$HOME/.venvs/chai/bin/python
while true; do
  if [ -f $HOME/c4-work/chai/PAUSE ]; then sleep 60; continue; fi
  if grep -q "CHAI_SCREEN_END" "$LOG" 2>/dev/null; then
    echo "watchdog: c2 screen ended - aggregating"
    $PY $HOME/c4-work/bin/c2-restrained-scores.py > "$AGG" 2>&1
    echo "---- c1 set table (unaffected sets only) ----" >> "$AGG"
    $PY $HOME/c4-work/bin/chai-restrained-scores.py >> "$AGG" 2>&1
    $PY $HOME/c4-work/bin/decide-sets-restrained.py >> "$AGG" 2>&1
    tail -20 "$AGG"
    break
  fi
  state=$(systemctl --user is-active chai-c2-screen 2>/dev/null)
  if [ "$state" = "failed" ]; then
    echo "watchdog: chai-c2-screen failed without an end marker - resuming $(date +%H:%M:%S)"
    systemctl --user reset-failed chai-c2-screen 2>/dev/null
    systemctl --user start --no-block chai-c2-screen
  fi
  sleep 60
done
