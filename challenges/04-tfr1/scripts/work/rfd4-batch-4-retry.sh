#!/usr/bin/env bash
# Retry the batch-4 generation until the hosted endpoint recovers.
# The service began returning server-side CUDA 500s at ~10:17 on 2026-10-27;
# every call fails fast. Cadence via env: SLEEP seconds between rounds
# (default 600), ROUNDS total (default 12). Failed output dirs are cleaned
# before each retry (the client refuses existing dirs).
set -u
SLEEP="${SLEEP:-600}"
ROUNDS="${ROUNDS:-12}"
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
CLIENT=$HOME/tools/bionemo-agent-toolkit/skills/bionemo-agent-toolkit/skills/rfd4-proteina-nim/scripts/design.py
WORK=$HOME/c4-work/rfd4/B4
cd "$REPO" || exit 1
set -a; . ./.env; set +a
declare -A JOBS=(
  ["E12L/run-1"]=request_tfr1_E12L_r8.json
  ["E12L/run-2"]=request_tfr1_E12L_r8.json
  ["E0L/run-1"]=request_tfr1_E0L_r8.json
  ["E0L/run-2"]=request_tfr1_E0L_r8.json
  ["H/run-1"]=request_tfr1_H_r8.json
)
for round in $(seq 1 "$ROUNDS"); do
  pending=0
  for out in "${!JOBS[@]}"; do
    [ -f "$WORK/$out/summary.json" ] && continue
    pending=$((pending + 1))
    rm -rf "$WORK/$out"
    echo "### round $round: $out $(date +%H:%M:%S)"
    if /usr/bin/python3 "$CLIENT" --mode hosted \
         --request "$REPO/challenges/04-tfr1/nim/${JOBS[$out]}" \
         --output-dir "$WORK/$out" 2>&1 | tail -1 | grep -q '"status": "completed"'; then
      echo "    ok"
    else
      echo "    still failing"
    fi
    sleep 8
  done
  if [ "$pending" -eq 0 ]; then break; fi
  echo "--- round $round done; sleeping $SLEEP ---"
  sleep "$SLEEP"
done
echo "RFD4_BATCH4_RETRY_END $(date +%H:%M:%S)"
