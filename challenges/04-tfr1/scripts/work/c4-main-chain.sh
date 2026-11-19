#!/usr/bin/env bash
# Master chain for the C4 night: wait for generation to finish, take the fold
# target from the probe result, then run the geometry -> MPNN -> yamls ->
# folds -> screen chain. Safe to start before generation begins.
set -u
WORK=$HOME/c4-work

while pgrep -f "run-c4-ge[n].sh" >/dev/null 2>&1; do sleep 60; done
echo "### gen chain gone $(date -Is)"
verbose=$(grep -c "C4_GEN_END" "$WORK/logs/gen-chain.log" 2>/dev/null || true)
[ "${verbose:-0}" -ge 1 ] || echo "WARNING: no C4_GEN_END sentinel in gen-chain.log"
for key in 11qc_e0 11qc_e1 11qc_e2 11qc_e12; do
    n=$(ls "$WORK/genie3/runs/$key/pdbs/"*.pdb 2>/dev/null | wc -l)
    echo "### gen $key: $n designs"
done

probe=$(ls "$WORK"/folds/probe-100aa/boltz_results_*/predictions/*/*_model_*.cif 2>/dev/null | wc -l)
if [ "$probe" -ge 1 ]; then TARGET=full; else TARGET=block; fi
echo "### fold target from probe: $TARGET (probe models=$probe) $(date -Is)"

TARGET="$TARGET" bash "$WORK/bin/c4-night-1.sh"
echo "C4_MAIN_DONE $(date -Is)"
