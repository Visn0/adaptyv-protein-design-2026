#!/usr/bin/env bash
# Full-backbone ProteinMPNN (vanilla weights, N/CA/C/O) for campaign-2
# re-sequencing. CPU-only, safe next to GPU jobs. One list file of design
# names per invocation (e.g. 11qc_e12_18, one per line).
# Per backbone: 8 sequences at T=0.1 and 8 at T=0.3, seed 91.
# Output: $WORK/seqs-fullbb/<design>/all.fa (samples only, headers tagged).
set -u
WORK=$HOME/c4-work
PY=$HOME/.venvs/mpnn/bin/python
MPNN=$HOME/tools/ProteinMPNN/protein_mpnn_run.py
LIST=${1:?usage: mpnn-fullbb.sh <list-file>}
export OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 OPENBLAS_NUM_THREADS=3
OUT=$WORK/seqs-fullbb

combine() {  # $1 = design dir, $2 = design name
    "$PY" - "$1" "$2" <<'EOF'
import pathlib, sys
d, name = pathlib.Path(sys.argv[1]), sys.argv[2]
recs = []
for t in ("t0.1", "t0.3"):
    fa = d / t / "seqs" / f"{name}.fa"
    if not fa.exists():
        continue
    cur = []
    for line in fa.read_text().splitlines():
        if line.startswith(">"):
            if cur:
                recs.append("".join(cur))
            cur = []
        else:
            cur.append(line.strip())
    if cur:
        recs.append("".join(cur))
# drop the first record of each temperature block (the native sequence)
out, kept = [], []
for i, s in enumerate(recs):
    kept.append(s)
native = {recs[0], recs[9]} if len(recs) >= 18 else set()
with (d / "all.fa").open("w") as fh:
    n = 0
    for s in kept:
        if s in native and len(kept) > 10:
            continue
        n += 1
        fh.write(f">{name}_fullbb_{n:02d}\n{s}\n")
print(f"{name}: {n} sequences in all.fa")
EOF
}

while read -r design; do
    [ -z "$design" ] && continue
    key="${design%_*}"
    pdb="$WORK/genie3/runs/$key/pdbs/$design.pdb"
    if [ ! -f "$pdb" ]; then echo "MISSING $pdb"; continue; fi
    d="$OUT/$design"; mkdir -p "$d"
    if [ -f "$d/all.fa" ]; then echo "skip $design (all.fa exists)"; continue; fi
    echo "### fullbb $design $(date -Is)"
    for t in 0.1 0.3; do
        CUDA_VISIBLE_DEVICES="" "$PY" "$MPNN" \
            --pdb_path "$pdb" --pdb_path_chains A \
            --path_to_model_weights $HOME/tools/ProteinMPNN/vanilla_model_weights \
            --model_name v_48_020 --num_seq_per_target 8 --sampling_temp "$t" \
            --seed 91 --out_folder "$d/t$t" > "$d/t$t.log" 2>&1 \
            || echo "FAILED $design T=$t"
    done
    combine "$d" "$design"
done < "$LIST"
echo "MPNN_FULLBB_END $(date +%H:%M:%S)"
