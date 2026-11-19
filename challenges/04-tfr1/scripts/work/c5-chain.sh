#!/usr/bin/env bash
# Waits for the b3 screen to finish, then starts the c5 (multi-chain) screen
# and watches it to completion (notifies via the watchdog's exit output).
set -u
B3LOG=$HOME/c4-work/logs/b3-screen.log
while ! grep -q "CHAI_SCREEN_END" "$B3LOG" 2>/dev/null; do sleep 60; done
echo "chain: b3 finished $(date -Is) - starting c5 screen"
systemctl --user reset-failed chai-c5-screen 2>/dev/null
systemctl --user start --no-block chai-c5-screen
exec /bin/bash $HOME/c4-work/bin/c5-screen-watchdog.sh
