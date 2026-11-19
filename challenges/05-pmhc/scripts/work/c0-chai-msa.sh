#!/usr/bin/env bash
# C0 chai MSA re-run: the four arms with their msa_pqt directories - the real
# second instrument. The single-sequence pass (out/) is the documented
# contrast read (~0.14 ipTM on the positive). Writes out-msa/.
set -u
unset PYTHONPATH  # Hermes restarts can leak a py3.14 site-packages here; breaks venv numpy
WORK=${C0_WORK:-$HOME/c5-work/c0t}
BIN=$HOME/c5-work/bin
CHAI=$HOME/.venvs/chai/bin/chai-lab
LOG=$WORK/logs/chai-msa.log
mkdir -p "$WORK/logs"
exec > >(tee -a "$LOG") 2>&1
( while :; do echo "[hb $(date +%H:%M:%S)]"; sleep 60; done ) & HB=$!
trap 'rc=$?; echo "### CHAI-MSA EXIT rc=$rc $(date +%H:%M:%S)"; kill "$HB" 2>/dev/null' EXIT

echo "=== CHAI-MSA START $(date +%H:%M:%S) ==="
# shared-GPU protocol: wait until no fold (boltz or chai) is running
while pgrep -f "boltz predict|chai-lab fold" >/dev/null; do
  echo "### chai-msa waiting for the GPU $(date +%H:%M:%S)"
  sleep 60
done

for arm in pos-g12d pos-wt neg-peptidefree neg-shuffled; do
  d="$WORK/chai/designs/$arm"
  if [ -f "$d/out-msa/scores.model_idx_0.npz" ]; then
    echo "skip $arm (done)"
    continue
  fi
  for attempt in 1 2; do
    echo "### chai-msa $arm attempt $attempt start $(date +%H:%M:%S)"
    ( cd "$d" && MEMLIMIT_MB=17000 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False \
        /usr/bin/python3 "$BIN/memlimit.py" "$CHAI" \
        fold in.fasta out-msa --msa-directory msa_pqt \
        --constraint-path restraints.csv \
        --no-use-esm-embeddings > fold-msa.log 2>&1 ) </dev/null
    rc=$?
    if [ $rc -eq 0 ]; then
      echo "### chai-msa $arm done $(date +%H:%M:%S)"
      break
    fi
    echo "### chai-msa $arm attempt $attempt FAILED rc=$rc $(date +%H:%M:%S)"
    rm -rf "$d/out-msa"
    sleep 20
  done
done
echo "=== CHAI-MSA END $(date +%H:%M:%S) ==="
