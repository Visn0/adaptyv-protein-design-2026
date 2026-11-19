#!/usr/bin/env bash
# CA-only ProteinMPNN, one sequence per passing design (the C2 triage protocol).
# CPU-only (runs safely next to GPU jobs). 3 designs in parallel with bounded
# threads: 4 unbounded workers thrash (measured 7.5+ min per design vs 2 min
# serial). flock-guarded so only one instance of this script writes at a time.
set -u
WORK=$HOME/c4-work
PY=$HOME/.venvs/mpnn/bin/python
MPNN=$HOME/tools/ProteinMPNN/protein_mpnn_run.py
export WORK PY MPNN
export OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 OPENBLAS_NUM_THREADS=3
mkdir -p "$WORK/seqs" "$WORK/state"
exec 9>"$WORK/state/mpnn.lock"
flock -w 7200 9   # one writer; a second caller waits for the first

process_one() {
    design="$1"
    if [ -f "$WORK/seqs/$design.fa" ]; then
        echo "skip $design (sequence exists)"
        return 0
    fi
    key="${design%_*}"
    pdb="$WORK/genie3/runs/$key/pdbs/$design.pdb"
    if [ ! -f "$pdb" ]; then
        echo "MISSING $pdb"
        return 0
    fi
    out="$WORK/seqs/$design"
    mkdir -p "$out"
    echo "### mpnn $design $(date -Is)"
    CUDA_VISIBLE_DEVICES="" "$PY" "$MPNN" --ca_only --pdb_path "$pdb" \
        --pdb_path_chains A \
        --path_to_model_weights $HOME/tools/ProteinMPNN/ca_model_weights \
        --model_name v_48_020 --num_seq_per_target 1 --sampling_temp 0.1 \
        --seed 37 --out_folder "$out" > "$out/mpnn.log" 2>&1
    fa="$out/seqs/$design.fa"
    if [ ! -f "$fa" ]; then
        echo "### mpnn FAILED $design"
        return 0
    fi
    /usr/bin/python3 - "$fa" "$WORK/seqs/$design.fa" "$design" <<'EOF'
import sys
src, dst, name = sys.argv[1], sys.argv[2], sys.argv[3]
recs, cur = [], []
for line in open(src):
    if line.startswith(">"):
        if cur:
            recs.append("".join(cur))
        cur = []
    else:
        cur.append(line.strip())
if cur:
    recs.append("".join(cur))
if len(recs) < 2:
    raise SystemExit(f"{src}: only {len(recs)} records")
seq = "".join(c for c in recs[1] if c in "ACDEFGHIKLMNPQRSTVWY")
with open(dst, "w") as fh:
    fh.write(f">{name}\n{seq}\n")
print(f"sequence {name}: {len(seq)} aa")
EOF
}
export -f process_one

grep -v '^[[:space:]]*$' "$WORK/state/pass-gen.txt" \
    | xargs -r -P 3 -I{} bash -c 'process_one "$@"' _ {}
echo "C4_MPNN_END $(date -Is)"
