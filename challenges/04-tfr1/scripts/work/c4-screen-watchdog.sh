#!/usr/bin/env bash
# Watchdog for the chai restrained screen (systemd unit chai-screen).
# - every 60 s: if the unit FAILED without an end marker, reset + restart it
#   (the batch runner skips finished designs, so restarts resume cleanly).
#   A manual stop (state 'inactive') is respected - no restart.
# - on CHAI_SCREEN_END: run the aggregator and the registered decision rule,
#   write both to logs/chai-restrained-aggregate.log, then exit (Hermes is
#   notified on exit).
set -u
LOG=$HOME/c4-work/logs/chai-screen.log
AGG=$HOME/c4-work/logs/chai-restrained-aggregate.log
while true; do
  # a deliberate pause must not be fought: the pause flag suspends restarts
  if [ -f $HOME/c4-work/chai/PAUSE ]; then sleep 60; continue; fi
  if grep -q "CHAI_SCREEN_END" "$LOG" 2>/dev/null; then
    echo "watchdog: screen ended - aggregating"
    PY=$HOME/.venvs/chai/bin/python  # needs numpy - system python lacks it
    $PY $HOME/c4-work/bin/chai-restrained-scores.py > "$AGG" 2>&1
    echo "---- decision ----" >> "$AGG"
    $PY $HOME/c4-work/bin/decide-sets-restrained.py >> "$AGG" 2>&1
    tail -14 "$AGG"
    break
  fi
  state=$(systemctl --user is-active chai-screen 2>/dev/null)
  if [ "$state" = "failed" ]; then
    echo "watchdog: unit failed without an end marker - resuming $(date +%H:%M:%S)"
    systemctl --user reset-failed chai-screen 2>/dev/null
    systemctl --user start --no-block chai-screen
  fi
  sleep 60
done
