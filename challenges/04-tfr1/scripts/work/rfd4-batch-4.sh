#!/usr/bin/env bash
# Batch 4 generation wave (2026-10-27): long-length sweep (E12, E0 at 110-140),
# hybrid epitope H = {R208, Y211, K344, K374}. Same request, separate runs =
# different samples. The thinking_high probe was dropped (server-side 500).
set -u
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
CLIENT=$HOME/tools/bionemo-agent-toolkit/skills/bionemo-agent-toolkit/skills/rfd4-proteina-nim/scripts/design.py
WORK=$HOME/c4-work/rfd4/B4
cd "$REPO" || exit 1
set -a; . ./.env; set +a
if [ -z "${NVIDIA_API_KEY:-}" ]; then echo "REFUSING: no key in env"; exit 1; fi
run() {  # request, outdir
  local req=$1 out=$2
  if [ -f "$out/summary.json" ]; then echo "skip $out (exists)"; return 0; fi
  echo "### $out $(date +%H:%M:%S)"
  /usr/bin/python3 "$CLIENT" --mode hosted \
    --request "$REPO/challenges/04-tfr1/nim/$req" --output-dir "$out" \
    || echo "!!! $out failed"
  sleep 5
}
run request_tfr1_E12L_r8.json "$WORK/E12L/run-1"
run request_tfr1_E12L_r8.json "$WORK/E12L/run-2"
run request_tfr1_E0L_r8.json "$WORK/E0L/run-1"
run request_tfr1_E0L_r8.json "$WORK/E0L/run-2"
run request_tfr1_H_r8.json "$WORK/H/run-1"
echo "RFD4_BATCH4_END $(date +%H:%M:%S)"
