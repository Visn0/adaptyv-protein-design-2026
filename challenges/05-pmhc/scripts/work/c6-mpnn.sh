#!/usr/bin/env bash
# C6 step 1: LigandMPNN children for the 10 parents (interface fixed, surface
# redesigned). CPU-only. 8 children per parent, T=0.1.
set -u
unset PYTHONPATH
MPNN=$HOME/tools/LigandMPNN
PY=$HOME/.venvs/mpnn/bin/python
C6=$HOME/c5-work/c6
LOG=$C6/mpnn.log
mkdir -p "$C6"
echo "C6_MPNN_START $(date -Is)" >> "$LOG"

for pdb in "$C6"/*.pdb; do
    name=$(basename "$pdb" .pdb)
    fixed_file=$C6/$name.fixed.txt
    [ -f "$fixed_file" ] || { echo "no fixed list for $name" >> "$LOG"; continue; }
    out=$C6/mpnn/$name
    if [ -f "$out/seqs/$name.fa" ]; then
        echo "skip $name (done)" >> "$LOG"
        continue
    fi
    echo "### $name $(date +%H:%M:%S)" >> "$LOG"
    ( cd "$MPNN" && PYTHONPATH= "$PY" run.py \
        --model_type protein_mpnn \
        --pdb_path "$pdb" \
        --out_folder "$out" \
        --chains_to_design D \
        --fixed_residues "$(cat "$fixed_file")" \
        --number_of_batches 8 --temperature 0.1 --seed 7 \
        >> "$LOG" 2>&1 )
done
echo "C6_MPNN_END $(date -Is)" >> "$LOG"
