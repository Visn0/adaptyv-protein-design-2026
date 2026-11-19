#!/usr/bin/env bash
# Fine-tuned-model funnel: boltz tri-state folds for the RFD4-Proteina
# epoch-99 designs. Same hardening as c0-probe-fold.sh (allocator override,
# memlimit, VRAM watchdog) plus the shared-GPU serialization guard.
#
# Usage: bash ft-funnel.sh [design ...]     (default: all designs in folds/)
#        bash ft-funnel.sh ft-000           (single design probe)
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
WORK=${FT_WORK:-$HOME/c5-work/ft-batch}
BIN=$HOME/c5-work/bin
BOLTZ=$HOME/.venvs/boltz/bin/boltz
LOG=$WORK/logs/fold.log
mkdir -p "$WORK/logs"
exec > >(tee -a "$LOG") 2>&1

DESIGNS=${*:-}
if [ -z "$DESIGNS" ]; then
  DESIGNS=$(cd "$WORK/folds" 2>/dev/null && ls *.yaml 2>/dev/null | sed 's/\.yaml$//')
fi

# shared-GPU protocol: never start while another fold is running, and hold an
# exclusive lock so two queued runners can never fold at the same time (each
# runner checks the GPU once, so without the lock two can wake together). The
# lock is global, not per work dir: two different batches still share one GPU.
exec 9>"/tmp/hermes-fold.lock"
flock 9
while pgrep -f "boltz predict|chai-lab fold|rfd4-generate" >/dev/null; do
  echo "### waiting for the GPU to free $(date +%H:%M:%S)"
  sleep 60
done

for D in $DESIGNS; do
  YAML=$WORK/folds/$D.yaml
  OUT=$WORK/folds/$D
  [ -f "$YAML" ] || { echo "no yaml for $D"; continue; }
  if compgen -G "$OUT/boltz_results_*/predictions/*/*_model_0.cif" > /dev/null; then
    echo "skip $D (done)"
    continue
  fi
  echo "### $D start $(date +%H:%M:%S)"
  START=$(date +%s)
  SEED_ARG=""
  case "$D" in
    *__s*) SEED_ARG="--seed ${D##*__s}" ;;
  esac
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False \
  MEMLIMIT_MB=16000 timeout 2400 /usr/bin/python3 "$BIN/memlimit.py" \
      "$BOLTZ" predict "$YAML" --out_dir "$OUT" $SEED_ARG --diffusion_samples 5 \
      --output_format mmcif
  RC=$?
  echo "### $D rc=$RC elapsed=$(( $(date +%s) - START ))s $(date +%H:%M:%S)"
done
echo "FT_FUNNEL_END $(date -Is)"
