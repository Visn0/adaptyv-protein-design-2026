#!/usr/bin/env bash
# Watchdog for the campaign-4 mouse cross-fold screen (unit chai-c4mn-screen).
set -u
LOG=$HOME/c4-work/logs/c4-screen.log
while true; do
  if grep -q "CHAI_SCREEN_END" "$LOG" 2>/dev/null; then
    echo "watchdog: c4 mouse screen ended $(date -Is)"
    tail -20 "$LOG"
    break
  fi
  state=$(systemctl --user is-active chai-c4mn-screen 2>/dev/null)
  if [ "$state" = "failed" ]; then
    echo "watchdog: chai-c4mn-screen failed without an end marker - resuming $(date +%H:%M:%S)"
    systemctl --user reset-failed chai-c4mn-screen 2>/dev/null
    systemctl --user start --no-block chai-c4mn-screen
  fi
  sleep 60
done
