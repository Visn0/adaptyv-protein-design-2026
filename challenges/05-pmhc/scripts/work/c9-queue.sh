#!/usr/bin/env bash
# C9 queue: genie3 alternative-generator campaign. Waits for the whole GPU
# chain (folds + c7 + c8 queues), probes with 2 samples, then generates 100.
set -u
unset PYTHONPATH
C9=$HOME/c5-work/c9
LOG=$C9/queue.log
GENIE=$HOME/tools/genie3
mkdir -p "$C9"
echo "C9_QUEUE_START $(date -Is)" >> "$LOG"

while pgrep -f "^bash .*c0-probe-fold" >/dev/null \
      || pgrep -f "^bash .*c7-queue.sh" >/dev/null \
      || pgrep -f "^bash .*c8-queue.sh" >/dev/null \
      || [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 2500 ]; do
    sleep 60
done
echo "GPU free, genie3 probe $(date -Is)" >> "$LOG"

cd "$GENIE" || exit 1
sed -e 's/n_sample: 100/n_sample: 2/' -e 's/pmhc_g12d_wave1/pmhc_g12d_test/' \
    "$C9/experiment-pmhc_g12d.yaml" > "$C9/experiment-test.yaml"
MEMLIMIT_MB=12000 /usr/bin/python3 $HOME/c5-work/bin/memlimit.py \
    $HOME/.venvs/genie3/bin/genie3 generate -c "$C9/experiment-test.yaml" >> "$LOG" 2>&1

n=$(find "$C9/genie3" -name "*.pdb" 2>/dev/null | wc -l)
echo "probe produced $n pdbs $(date -Is)" >> "$LOG"
if [ "$n" -ge 1 ]; then
    echo "running full generation (100 samples) $(date -Is)" >> "$LOG"
    MEMLIMIT_MB=12000 /usr/bin/python3 $HOME/c5-work/bin/memlimit.py \
        $HOME/.venvs/genie3/bin/genie3 generate -c "$C9/experiment-pmhc_g12d.yaml" >> "$LOG" 2>&1
fi
echo "C9_QUEUE_END $(date -Is)" >> "$LOG"
