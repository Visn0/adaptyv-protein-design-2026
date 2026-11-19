#!/usr/bin/env bash
# Stage-3 chai-MSA second instrument for the 10 finalists (unconstrained folds
# of binder + G12D pMHC; msa_pqt route). Adapted from c0-chai-msa.sh.
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
WORK=${1:-$HOME/c5-work/s3}
BIN=$HOME/c5-work/bin
CHAI=$HOME/.venvs/chai/bin/chai-lab
LOG=$WORK/logs/chai.log
mkdir -p "$WORK/logs"
exec > >(tee -a "$LOG") 2>&1
( while :; do echo "[hb $(date +%H:%M:%S)]"; sleep 60; done ) & HB=$!
trap 'rc=$?; echo "### CHAI EXIT rc=$rc $(date +%H:%M:%S)"; kill "$HB" 2>/dev/null' EXIT

echo "=== CHAI START $(date +%H:%M:%S) ==="
while pgrep -f "boltz predict|chai-lab fold|opendde pred" >/dev/null; do
  echo "### chai waiting for the GPU $(date +%H:%M:%S)"
  sleep 60
done

for d in "$WORK"/designs/*/; do
  name=$(basename "$d")
  if [ -f "$d/out-msa/scores.model_idx_0.npz" ]; then
    echo "skip $name (done)"
    continue
  fi
  for attempt in 1 2; do
    echo "### chai $name attempt $attempt start $(date +%H:%M:%S)"
    ( cd "$d" && MEMLIMIT_MB=17000 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False \
        /usr/bin/python3 "$BIN/memlimit.py" "$CHAI" \
        fold in.fasta out-msa --msa-directory msa_pqt \
        --no-use-esm-embeddings > fold.log 2>&1 ) </dev/null
    rc=$?
    if [ $rc -eq 0 ]; then
      echo "### chai $name done $(date +%H:%M:%S)"
      break
    fi
    echo "### chai $name attempt $attempt FAILED rc=$rc $(date +%H:%M:%S)"
    rm -rf "$d/out-msa"
    sleep 20
  done
done
echo "=== CHAI DONE $(date +%H:%M:%S) ==="
