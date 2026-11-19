#!/usr/bin/env bash
# C9 sequence assignment: ProteinMPNN (CA-only mode, the backbones are CA traces)
# designs chain D only, 2 sequences per backbone, 4-way parallel.
set -u
unset PYTHONPATH
PROT=$HOME/tools/ProteinMPNN
PY=$HOME/.venvs/mpnn/bin/python
C9=$HOME/c5-work/c9
LOG=$C9/mpnn.log
mkdir -p "$C9/mpnn"
echo "C9_MPNN_START $(date -Is)" >> "$LOG"

run_one() {
    pdb="$1"
    name=$(basename "$pdb" .pdb)
    [ -f "$C9/mpnn/$name/seqs/$name.fa" ] && return 0
    cd "$PROT" || return 1
    PYTHONPATH= "$PY" protein_mpnn_run.py \
        --pdb_path "$pdb" --ca_only --pdb_path_chains D \
        --out_folder "$C9/mpnn/$name" \
        --num_seq_per_target 2 --sampling_temp 0.1 --seed 37 \
        --model_name v_48_020 >> "$LOG.dev" 2>&1
    echo "$name rc=$?" >> "$LOG"
}
export -f run_one
export C9 PROT PY

find "$C9/backbones" -name "g3_*.pdb" | sort | xargs -I{} -P 4 bash -c 'run_one "$@"' _ {}
echo "C9_MPNN_END $(date -Is)" >> "$LOG"
