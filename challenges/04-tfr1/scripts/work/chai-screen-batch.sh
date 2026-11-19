#!/usr/bin/env bash
# Restrained chai screen over a list of designs: 2 concurrent folds, then a
# serial second pass for any failures. Design dirs must hold in.fasta,
# msa_pqt/, restraints.csv. Skips designs whose scores already exist.
set -u
DIRS=$HOME/c4-work/chai/designs
LIST=${1:-$HOME/c4-work/chai/screen-list.txt}
SEED="${2:-}"   # optional chai --seed override (second-seed replication runs)
PY=/usr/bin/python3
CHAI=$HOME/.venvs/chai/bin/chai-lab
ML=$HOME/c4-work/bin/memlimit.py
FAILED=$HOME/c4-work/chai/failed-list.txt
: > "$FAILED"

run_one() {
  local name=$1 d="$DIRS/$1"
  if [ -f "$d/out/scores.model_idx_0.npz" ]; then echo "### $name skip (done)"; return 0; fi
  echo "### $name start $(date +%H:%M:%S)"
  ( cd "$d" && MEMLIMIT_MB=17000 $PY $ML $CHAI fold in.fasta out \
      --msa-directory msa_pqt --constraint-path restraints.csv \
      --no-use-esm-embeddings ${SEED:+--seed "$SEED"} > fold.log 2>&1 ) </dev/null
  local rc=$?
  if [ $rc -eq 0 ]; then echo "### $name done $(date +%H:%M:%S)";
  else echo "### $name FAILED rc=$rc $(date +%H:%M:%S)"; rm -rf "$d/out"; echo "$name" >> "$FAILED"; fi
}

# Serial: two concurrent chai folds died at CUDA init together (2026-10-24
# 10:37, cause unresolved); the single-job path is proven at ~12 min/design.
# Pause sentinel: `touch chai/PAUSE` stops the batch between designs. Do not
# SIGTERM the unit mid-fold: a chai process killed in its first ~60 s took the
# host down once (0x7E, 2026-10-26 14:14, right after the pause killed a
# just-started fold). Between designs it is always safe.
PAUSE_SENTINEL=$HOME/c4-work/chai/PAUSE
while read -r a; do
  [ -z "$a" ] && continue
  if [ -f "$PAUSE_SENTINEL" ]; then
    echo "### PAUSED via sentinel at $(date +%H:%M:%S); remove $PAUSE_SENTINEL to resume"
    exit 0
  fi
  run_one "$a"
done < "$LIST"

if [ -s "$FAILED" ]; then
  echo "=== serial retry pass for $(wc -l < $FAILED) failed designs ==="
  # Snapshot the list first: run_one appends new failures to $FAILED, and
  # reading it directly made the pass self-extending (night of 2026-10-27:
  # ~2800 futile 8-second retries, the batch never ended).
  RETRY="$FAILED.retry.$$"
  cp "$FAILED" "$RETRY"
  while read -r name; do run_one "$name"; done < "$RETRY"
  rm -f "$RETRY"
fi
echo CHAI_SCREEN_END "$(date +%H:%M:%S)"
