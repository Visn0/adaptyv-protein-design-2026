#!/usr/bin/env bash
# Watchdog for the multi-chain screen (unit chai-c5-screen).
set -u
LOG=$HOME/c4-work/logs/c5-screen.log
START_LINES=$(wc -l < "$LOG" 2>/dev/null || echo 0)
while true; do
  if tail -n +$((START_LINES + 1)) "$LOG" 2>/dev/null | grep -q "CHAI_SCREEN_END"; then
    echo "watchdog: c5 screen ended $(date -Is)"
    tail -25 "$LOG"
    break
  fi
  state=$(systemctl --user is-active chai-c5-screen 2>/dev/null)
  if [ "$state" = "failed" ]; then
    echo "watchdog: chai-c5-screen failed without an end marker - resuming $(date +%H:%M:%S)"
    systemctl --user reset-failed chai-c5-screen 2>/dev/null
    systemctl --user start --no-block chai-c5-screen
  fi
  sleep 60
done
