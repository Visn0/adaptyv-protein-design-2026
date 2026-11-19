#!/usr/bin/env bash
# s3b: final validation of the 6 new leaders - multi-seed boltz + chai-MSA.
set -u
unset PYTHONPATH
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
W=${1:-$HOME/c5-work/s3b}
LOG=$W/queue.log
echo "S3B_START $(date -Is)" >> "$LOG"
while [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ]; do
    sleep 60
done
bash "$REPO/challenges/05-pmhc/scripts/work/s3-multiseed.sh" "$W" >> "$LOG" 2>&1
if [ -d "$W/designs" ]; then
    bash "$REPO/challenges/05-pmhc/scripts/work/s3-chai.sh" "$W" >> "$LOG" 2>&1
else
    echo "no designs dir for chai - skipped" >> "$LOG"
fi
echo "S3B_END $(date -Is)" >> "$LOG"
