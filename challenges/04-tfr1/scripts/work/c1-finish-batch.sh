#!/usr/bin/env bash
# Campaign-1 close-out + campaign-2 kick:
#   1. second-seed reruns of the four near-line designs (seed 7) - settles
#      whether E0 is at 5 or 6 on the deciding metric
#   2. campaign-2 E12 generation top-up: genie3 11qc_e12b2, 24 more backbones
# The E1/E2 restrained screen is DEFERRED by decision 2026-10-25 (the metric
# cannot rank sets at p=0.52; the GPU hours move to campaign 2; the scope gap
# is recorded in notes/c1-triage.md instead).
set -u
BIN=$HOME/c4-work/bin
echo "=== reseeds, seed 7 $(date +%F' '%H:%M:%S) ==="
bash "$BIN/chai-screen-batch.sh" $HOME/c4-work/chai/reseed-list.txt 7

echo "=== c2 kick: genie3 11qc_e12b2 $(date +%F' '%H:%M:%S) ==="
if ! cd $HOME/tools/genie3; then exit 1; fi
RUNS=$HOME/c4-work/genie3/runs
have=$(ls "$RUNS/11qc_e12b2/pdbs/"*.pdb 2>/dev/null | wc -l)
if [ "$have" -lt 24 ]; then
  MEMLIMIT_MB=8000 /usr/bin/python3 "$BIN/memlimit.py" \
      $HOME/.venvs/genie3/bin/genie3 generate \
      -c $HOME/c4-work/genie3/11qc_e12b2.yaml \
      > $HOME/c4-work/logs/gen-11qc_e12b2.log 2>&1
  rc=$?
  n=$(ls "$RUNS/11qc_e12b2/pdbs/"*.pdb 2>/dev/null | wc -l)
  echo "### GEN 11qc_e12b2 rc=$rc designs=$n"
else
  echo "### GEN 11qc_e12b2 skip (complete, have=$have)"
fi
echo "C1_FINISH_END $(date +%H:%M:%S)"
