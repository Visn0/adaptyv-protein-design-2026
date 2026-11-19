#!/usr/bin/env bash
# Watchdog for the E1/E2 screen (unit chai-e1e2-screen).
set -u
LOG=$HOME/c4-work/logs/e1e2-screen.log
START_LINES=$(wc -l < "$LOG" 2>/dev/null || echo 0)
while true; do
  if tail -n +$((START_LINES + 1)) "$LOG" 2>/dev/null | grep -q "CHAI_SCREEN_END"; then
    echo "watchdog: e1e2 screen ended $(date -Is)"
    tail -25 "$LOG"
    break
  fi
  state=$(systemctl --user is-active chai-e1e2-screen 2>/dev/null)
  if [ "$state" = "failed" ]; then
    echo "watchdog: chai-e1e2-screen failed without an end marker - resuming $(date +%H:%M:%S)"
    systemctl --user reset-failed chai-e1e2-screen 2>/dev/null
    systemctl --user start --no-block chai-e1e2-screen
  fi
  sleep 60
done
