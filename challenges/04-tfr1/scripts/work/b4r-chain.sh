#!/usr/bin/env bash
# Starts the b4r (RFdiffusion arm) fold screen when the GPU is free.
# Serializes behind the other queues: waits while no chai-lab process runs,
# holds back if the b4 (RFD4) screen still has designs pending or running,
# and starts b4r once its own list exists and everything ahead of it is done.
set -u
B4LIST=$HOME/c4-work/chai/b4-screen-list.txt
B4LOG=$HOME/c4-work/logs/b4-screen.log
B4RLIST=$HOME/c4-work/chai/b4r-screen-list.txt
while true; do
  if ! pgrep -f "chai-lab" >/dev/null; then
    if [ -s "$B4LIST" ] && ! grep -q "CHAI_SCREEN_END" "$B4LOG" 2>/dev/null; then
      : # b4 is ready or running and goes first; keep waiting
    elif [ -s "$B4RLIST" ]; then
      echo "chain: GPU free, b4 done/absent, b4r designs present - starting $(date -Is)"
      break
    fi
  fi
  sleep 60
done
systemctl --user reset-failed chai-b4r-screen 2>/dev/null
systemctl --user start --no-block chai-b4r-screen
exec /bin/bash $HOME/c4-work/bin/b4r-screen-watchdog.sh
