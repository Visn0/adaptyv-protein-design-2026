#!/usr/bin/env bash
# Watchdog for the b4r screen (unit chai-b4r-screen).
set -u
LOG=$HOME/c4-work/logs/b4r-screen.log
START_LINES=$(wc -l < "$LOG" 2>/dev/null || echo 0)
while true; do
  if tail -n +$((START_LINES + 1)) "$LOG" 2>/dev/null | grep -q "CHAI_SCREEN_END"; then
    echo "watchdog: b4r screen ended $(date -Is)"
    tail -25 "$LOG"
    break
  fi
  state=$(systemctl --user is-active chai-b4r-screen 2>/dev/null)
  if [ "$state" = "failed" ]; then
    echo "watchdog: chai-b4r-screen failed without an end marker - resuming $(date +%H:%M:%S)"
    systemctl --user reset-failed chai-b4r-screen 2>/dev/null
    systemctl --user start --no-block chai-b4r-screen
  fi
  sleep 60
done
