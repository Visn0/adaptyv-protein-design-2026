#!/usr/bin/env bash
# Stage-3 multi-seed boltz folds for the 10 finalists (3 seeds each = 30 arms).
# Seed is read from the arm name suffix __s<N>. Skip-done + GPU guard + memlimit.
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
WORK=${1:-$HOME/c5-work/s3}
BIN=$HOME/c5-work/bin
BOLTZ=$HOME/.venvs/boltz/bin/boltz
LOG=$WORK/logs/multiseed.log
mkdir -p "$WORK/logs"
exec > >(tee -a "$LOG") 2>&1
( while :; do echo "[hb $(date +%H:%M:%S)]"; sleep 60; done ) & HB=$!
trap 'rc=$?; echo "### MULTISEED EXIT rc=$rc $(date +%H:%M:%S)"; kill "$HB" 2>/dev/null' EXIT

echo "=== MULTISEED START $(date +%H:%M:%S) ==="
while pgrep -f "boltz predict|chai-lab fold|opendde pred" >/dev/null; do
  echo "### waiting for the GPU $(date +%H:%M:%S)"
  sleep 60
done

for y in "$WORK"/folds/*.yaml; do
  arm=$(basename "$y" .yaml)
  seed=${arm##*__s}
  OUT=$WORK/folds/$arm
  if compgen -G "$OUT/boltz_results_*/predictions/*/*_model_0.cif" >/dev/null; then
    echo "skip $arm (done)"
    continue
  fi
  echo "=== PROBE $arm start $(date +%H:%M:%S) seed=$seed ==="
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False \
  MEMLIMIT_MB=12000 timeout 1200 /usr/bin/python3 "$BIN/memlimit.py" \
    "$BOLTZ" predict "$y" --out_dir "$OUT" --seed "$seed" \
    --diffusion_samples 5 --output_format mmcif
  echo "=== PROBE $arm exit rc=$? $(date +%H:%M:%S) ==="
done
echo "=== MULTISEED DONE $(date +%H:%M:%S) ==="
