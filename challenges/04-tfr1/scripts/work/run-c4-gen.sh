#!/usr/bin/env bash
# Genie 3 generation, challenge 4 campaign 1: four epitope sets x 24 designs.
# GPU-serial: waits for any running boltz fold, resumable per set.
set -u
cd $HOME/tools/genie3 || exit 1
LOGS=$HOME/c4-work/logs
RUNS=$HOME/c4-work/genie3/runs
while pgrep -f "boltz predict" >/dev/null 2>&1; do sleep 30; done
for key in 11qc_e0 11qc_e1 11qc_e2 11qc_e12; do
    yaml=$HOME/c4-work/genie3/$key.yaml
    have=$(ls "$RUNS/$key/pdbs/"*.pdb 2>/dev/null | wc -l)
    echo "### GEN $key have=$have $(date -Is)"
    if [ "$have" -ge 24 ]; then
        echo "### GEN $key skip (complete)"
        continue
    fi
    MEMLIMIT_MB=8000 /usr/bin/python3 $HOME/c4-work/bin/memlimit.py \
        $HOME/.venvs/genie3/bin/genie3 generate -c "$yaml" \
        > "$LOGS/gen-$key.log" 2>&1
    rc=$?
    n=$(ls "$RUNS/$key/pdbs/"*.pdb 2>/dev/null | wc -l)
    echo "### GEN $key rc=$rc designs=$n $(date -Is)"
done
echo "C4_GEN_END $(date -Is)"
