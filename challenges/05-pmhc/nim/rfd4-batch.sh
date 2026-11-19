#!/usr/bin/env bash
# C1 hosted generation batch: N calls x R replicates against the RFD4 NIM.
# Network-only (no local GPU). Idempotent: existing run dirs are skipped.
#
# Usage: bash rfd4-batch.sh <set> <calls> <replicates> <prefix>
#   set        PEP | PEPRIM  (request variants from build_request.py)
#   calls      number of NIM calls
#   replicates designs per call
#   prefix     subdirectory under ~/c5-work/c1 for this batch
set -u
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
CLIENT=$HOME/tools/bionemo-agent-toolkit/skills/bionemo-agent-toolkit/skills/rfd4-proteina-nim/scripts/design.py
BASE=$HOME/c5-work/c1
SET=$1; CALLS=$2; REPLICATES=$3; PREFIX=$4

cd "$REPO" || exit 1
set -a; . ./.env; set +a
if [ -z "${NVIDIA_API_KEY:-}" ]; then echo "NVIDIA_API_KEY missing" >&2; exit 1; fi

.venv/bin/python challenges/05-pmhc/nim/build_request.py \
    --set "$SET" --replicates "$REPLICATES" > /dev/null || exit 1
REQ="challenges/05-pmhc/nim/request_pmhc_${SET}_r${REPLICATES}.json"
[ -f "$REQ" ] || REQ="challenges/05-pmhc/nim/request_pmhc_${SET}.json"

for i in $(seq 1 "$CALLS"); do
  OUT="$BASE/$PREFIX/run-$(printf '%03d' "$i")"
  if [ -d "$OUT" ]; then echo "skip $OUT"; continue; fi
  echo "### call $i/$CALLS start $(date +%H:%M:%S)"
  /usr/bin/python3 "$CLIENT" --request "$REQ" --output-dir "$OUT" --timeout 560 2>&1 | tail -1
  sleep 2
done
echo "### batch $PREFIX done $(date +%H:%M:%S)"
