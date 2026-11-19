#!/usr/bin/env bash
# Watchdog for the campaign-3 switch-variant screen (unit chai-c3-screen).
# Keeps the car: resumes on state 'failed'; on CHAI_SCREEN_END it prints the
# tail and exits so Hermes is notified.
set -u
LOG=$HOME/c4-work/logs/c3-screen.log
while true; do
  if grep -q "CHAI_SCREEN_END" "$LOG" 2>/dev/null; then
    echo "watchdog: c3 screen ended $(date -Is)"
    tail -20 "$LOG"
    break
  fi
  state=$(systemctl --user is-active chai-c3-screen 2>/dev/null)
  if [ "$state" = "failed" ]; then
    echo "watchdog: chai-c3-screen failed without an end marker - resuming $(date +%H:%M:%S)"
    systemctl --user reset-failed chai-c3-screen 2>/dev/null
    systemctl --user start --no-block chai-c3-screen
  fi
  sleep 60
done
