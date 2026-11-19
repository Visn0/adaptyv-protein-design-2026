#!/bin/bash
# Two concurrent OpenMM MD runs (C2 promises) + pack, around 1.5 h total.
set -e
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
cd "$REPO"
PY=.venv/bin/python
B=$HOME/c2-work/md-anim/build_md.py
F=$HOME/c2-work/genie3/folds
R=$HOME/c2-work/md-anim/runs
L=$HOME/c2-work/md-anim

nice -n 10 $PY $B prep --design d7x-t3-3 \
  --cif "$F/d7x-t3-3/boltz_results_d7x-t3-3/predictions/d7x-t3-3/d7x-t3-3_model_0.cif" \
  --run-dir "$R/d7x-t3-3" > "$L/d7_prep.log" 2>&1

nice -n 10 $PY $B prep --design b2x-d12-2 \
  --cif "$F/b2x-d12-2/boltz_results_b2x-d12-2/predictions/b2x-d12-2/b2x-d12-2_model_2.cif" \
  --run-dir "$R/b2x-d12-2" > "$L/d12_prep.log" 2>&1

nice -n 10 $PY $B run --design d7x-t3-3 --run-dir "$R/d7x-t3-3" \
  --length-ps 120 --equil-ps 12 --save-every-ps 2 > "$L/d7_md.log" 2>&1 &
P1=$!
nice -n 10 $PY $B run --design b2x-d12-2 --run-dir "$R/b2x-d12-2" \
  --length-ps 120 --equil-ps 12 --save-every-ps 2 > "$L/d12_md.log" 2>&1 &
P2=$!
wait $P1 $P2

$PY $B pack --design d7x-t3-3 --run-dir "$R/d7x-t3-3" --movie-frames 60 > "$L/d7_pack.log" 2>&1
$PY $B pack --design b2x-d12-2 --run-dir "$R/b2x-d12-2" --movie-frames 60 > "$L/d12_pack.log" 2>&1
echo ALL_MD_DONE
