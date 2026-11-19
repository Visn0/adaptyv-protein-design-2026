#!/usr/bin/env bash
# Starts the batch-4 fold screen when the GPU is free and the designs exist.
# Waits until no chai-lab process is running AND b4-screen-list.txt is non-empty
# (the list only exists after the generation wave lands). Covers every order of
# arrival: generation first, another screen first, or both already done.
set -u
LIST=$HOME/c4-work/chai/b4-screen-list.txt
while true; do
  if ! pgrep -f "chai-lab" >/dev/null && [ -s "$LIST" ]; then
    echo "chain: GPU free and b4 designs present ($(wc -l < "$LIST") designs) - starting $(date -Is)"
    break
  fi
  sleep 60
done
systemctl --user reset-failed chai-b4-screen 2>/dev/null
systemctl --user start --no-block chai-b4-screen
exec /bin/bash $HOME/c4-work/bin/b4-screen-watchdog.sh
