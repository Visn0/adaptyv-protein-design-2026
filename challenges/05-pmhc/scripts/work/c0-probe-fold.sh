#!/usr/bin/env bash
# C0 hardened fold runner: one or more arms, sequentially. Each arm gets the
# allocator override, a VRAM watchdog with abort, and a dxg error trace.
# Written 2026-10-30 after two host crashes at fold start (0x20001 IOMMU
# family); the first run under this hardening (pos-g12d) completed clean
# (2:33 prediction, 10.1 GB VRAM peak, host stable).
#   - PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False (documented override)
#   - VRAM watchdog: abort when >92% VRAM is sustained >=60 s, fold past
#     minute 3 (the chai lesson: never kill in the first minute)
#   - dxg error-rate trace per arm (the documented pre-crash signal)
#
# Usage: bash c0-probe-fold.sh [arm ...]      (default: pos-g12d)
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
WORK=${C0_WORK:-$HOME/c5-work/c0}
BIN=$HOME/c5-work/bin
BOLTZ=$HOME/.venvs/boltz/bin/boltz
LOG=$WORK/logs/probe.log
MON=$WORK/logs/probe-monitor.log
ARMS=${*:-pos-g12d}
if [ "$ARMS" = "all" ]; then
  ARMS=$(cd "$WORK/folds" 2>/dev/null && ls *.yaml 2>/dev/null | sed 's/\.yaml$//')
fi

mkdir -p "$WORK/logs"
exec > >(tee -a "$LOG") 2>&1

# shared-GPU protocol: never start while chai is folding
while pgrep -f "chai-lab fold" >/dev/null; do
  echo "### waiting for chai to finish $(date +%H:%M:%S)"
  sleep 60
done

for ARM in $ARMS; do
  OUT=$WORK/folds/$ARM
  if compgen -G "$OUT/boltz_results_*/predictions/*/*_model_0.cif" > /dev/null; then
    echo "skip $ARM (done)"
    continue
  fi
  START=$(date +%s)
  echo "=== PROBE $ARM start $(date +%H:%M:%S) ==="
  echo "dxg errors before: $(dmesg 2>/dev/null | grep -c dxgk)"

  (
    sleep 20
    over=0
    while :; do
      now=$(date +%s); elapsed=$((now - START))
      used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
      dxg=$(dmesg 2>/dev/null | grep -c dxgk)
      echo "$(date +%H:%M:%S) $ARM t=${elapsed}s vram=${used}MiB dxg=${dxg}" >> "$MON"
      if [ "${used:-0}" -gt 11250 ]; then over=$((over + 1)); else over=0; fi
      if [ "$over" -ge 4 ] && [ "$elapsed" -gt 180 ]; then
        echo "WATCHDOG ABORT $ARM: vram ${used}MiB sustained >92% at t=${elapsed}s"
        pkill -TERM -f "boltz predict" 2>/dev/null
        sleep 10
        pkill -KILL -f "boltz predict" 2>/dev/null
        break
      fi
      sleep 15
    done
  ) & WD=$!

  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False \
  timeout 1200 /usr/bin/python3 "$BIN/memlimit.py" "$BOLTZ" predict "$WORK/folds/$ARM.yaml" \
    --out_dir "$OUT" --seed 42 --diffusion_samples 5 --output_format mmcif
  rc=$?
  kill "$WD" 2>/dev/null
  echo "=== PROBE $ARM exit rc=$rc $(date +%H:%M:%S); dxg now $(dmesg 2>/dev/null | grep -c dxgk) ==="
done
echo "=== ALL ARMS DONE $(date +%H:%M:%S) ==="
