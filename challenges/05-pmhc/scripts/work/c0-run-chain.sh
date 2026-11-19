#!/usr/bin/env bash
# C0 instrument-calibration chain: boltz folds -> chai folds -> metric.
# Serial, one GPU job at a time (hard rule). Idempotent: done arms are skipped.
# Do not SIGTERM chai in its first ~60 s (host-crash lesson, 2026-10-26).
#
# Launch (from anywhere):
#   bash challenges/05-pmhc/scripts/work/c0-run-chain.sh
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
STAGE=${STAGE:-all}   # all | boltz | chai | metric
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
WORK=${C0_WORK:-$HOME/c5-work/c0}
BIN=$HOME/c5-work/bin
BOLTZ=$HOME/.venvs/boltz/bin/boltz
CHAI=$HOME/.venvs/chai/bin/chai-lab
PY="$REPO/.venv/bin/python"
LOG="$WORK/logs/chain.log"

mkdir -p "$WORK/logs" "$BIN"
[ -f "$BIN/memlimit.py" ] || cp $HOME/c4-work/bin/memlimit.py "$BIN/memlimit.py"
# Keep output on the launcher's stdout (a silent pipe gets the job killed —
# observed 2026-10-30: a run that redirected all output away died SIGTERM at
# ~3.5 min) while also appending to the log. A 60 s heartbeat keeps the pipe
# active during quiet phases (weight loading, folds).
exec > >(tee -a "$LOG") 2>&1
trap 'rc=$?; echo "### CHAIN EXIT rc=$rc stage=$STAGE $(date +%H:%M:%S)"; [ -n "${HB:-}" ] && kill "$HB" 2>/dev/null' EXIT
( while :; do echo "[hb $(date +%H:%M:%S)]"; sleep 60; done ) & HB=$!

echo "=== CHAIN START stage=$STAGE $(date +%H:%M:%S) ==="

if [ "$STAGE" = "all" ] || [ "$STAGE" = "boltz" ]; then
echo "=== BOLTZ ==="
for y in "$WORK"/folds/*.yaml; do
  name=$(basename "$y" .yaml)
  out="$WORK/folds/$name"
  if compgen -G "$out/boltz_results_*/predictions/*/*_model_0.cif" > /dev/null; then
    echo "skip $name (done)"; continue
  fi
  echo "### boltz $name start $(date +%H:%M:%S)"
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False \
  /usr/bin/python3 "$BIN/memlimit.py" "$BOLTZ" predict "$y" --out_dir "$out" \
    --seed 42 --diffusion_samples 5 --output_format mmcif \
    && echo "### boltz $name done $(date +%H:%M:%S)" \
    || echo "### boltz $name FAILED $(date +%H:%M:%S)"
done
fi

if [ "$STAGE" = "all" ] || [ "$STAGE" = "chai" ]; then
echo "=== CHAI ==="
# Shared-GPU protocol: wait for any running boltz fold before chai starts.
while pgrep -f "boltz predict" >/dev/null; do
  echo "### chai waiting for a running fold to finish $(date +%H:%M:%S)"
  sleep 60
done
for arm in pos-g12d pos-wt neg-peptidefree neg-shuffled; do
  d="$WORK/chai/designs/$arm"
  if [ -f "$d/out/scores.model_idx_0.npz" ]; then
    echo "skip $arm (done)"; continue
  fi
  for attempt in 1 2; do
    echo "### chai $arm attempt $attempt start $(date +%H:%M:%S)"
    ( cd "$d" && MEMLIMIT_MB=17000 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False \
        /usr/bin/python3 "$BIN/memlimit.py" "$CHAI" \
        fold in.fasta out --constraint-path restraints.csv \
        --no-use-esm-embeddings > fold.log 2>&1 ) </dev/null
    rc=$?
    if [ $rc -eq 0 ]; then
      echo "### chai $arm done $(date +%H:%M:%S)"
      break
    fi
    echo "### chai $arm attempt $attempt FAILED rc=$rc $(date +%H:%M:%S)"
    rm -rf "$d/out"
    sleep 20
  done
done
fi

if [ "$STAGE" = "all" ] || [ "$STAGE" = "metric" ]; then
echo "=== METRIC ==="
"$PY" "$REPO/challenges/05-pmhc/scripts/work/c0-tri-state-metric.py"
fi
echo "=== CHAIN END $(date +%H:%M:%S) ==="
