#!/usr/bin/env bash
# RFD4-Proteina hosted batch: 3 calls x 8 replicates per set, sequential.
# The key is sourced from the repo .env; it is never echoed or logged.
set -u
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
CLIENT=$HOME/tools/bionemo-agent-toolkit/skills/bionemo-agent-toolkit/skills/rfd4-proteina-nim/scripts/design.py
WORK=$HOME/c4-work/rfd4
cd "$REPO" || exit 1
set -a; . ./.env; set +a
if [ -z "${NVIDIA_API_KEY:-}" ]; then echo "REFUSING: no key in env"; exit 1; fi

run() {  # set, runno
  local set=$1 n=$2 out="$WORK/$1/run-$2"
  if [ -f "$out/summary.json" ]; then echo "skip $set run-$n (exists)"; return 0; fi
  echo "### $set run-$n $(date +%H:%M:%S)"
  /usr/bin/python3 "$CLIENT" --mode hosted \
    --request "$REPO/challenges/04-tfr1/nim/request_tfr1_${set}_r8.json" \
    --output-dir "$out" || echo "!!! $set run-$n failed (exit $?)"
  sleep 10
}

# E12 already has the 1-design pilot in run-2; add 3 calls (24 more).
for n in 3 4 5; do run E12 $n; done
for set in E0 E1 E2; do
  for n in 1 2 3; do run "$set" $n; done
done
echo "RFD4_BATCH_END $(date +%H:%M:%S)"
