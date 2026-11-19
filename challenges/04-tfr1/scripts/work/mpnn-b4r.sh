#!/usr/bin/env bash
# ProteinMPNN sequencing for the RFdiffusion arm (b4r backbones).
# Mirrors mpnn-fullbb.sh: vanilla weights, redesign chain A (the binder),
# 8 seqs at T=0.1 and 8 at T=0.3, seed 91, CPU-only (safe next to GPU jobs).
# Input:  ~/c4-work/rfdiffusion/B4R/<tag>/design_<i>.pdb  (chain B = target)
# Output: ~/c4-work/seqs-b4r/<tag>_<i>/all.fa
set -u
WORK=$HOME/c4-work
PY=$HOME/.venvs/mpnn/bin/python
MPNN=$HOME/tools/ProteinMPNN/protein_mpnn_run.py
OUT=$WORK/seqs-b4r
export OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 OPENBLAS_NUM_THREADS=3

for pdb in "$WORK"/rfdiffusion/B4R/*/design_*.pdb; do
    [ -f "$pdb" ] || continue
    tag=$(basename "$(dirname "$pdb")")
    idx=$(basename "$pdb" .pdb | sed 's/design_//')
    name="${tag}_${idx}"
    d="$OUT/$name"
    if [ -f "$d/all.fa" ]; then echo "skip $name (all.fa exists)"; continue; fi
    mkdir -p "$d"
    echo "### $name $(date +%H:%M:%S)"
    for t in 0.1 0.3; do
        CUDA_VISIBLE_DEVICES="" "$PY" "$MPNN" \
            --pdb_path "$pdb" --pdb_path_chains A \
            --path_to_model_weights $HOME/tools/ProteinMPNN/vanilla_model_weights \
            --model_name v_48_020 --num_seq_per_target 8 --sampling_temp "$t" \
            --seed 91 --out_folder "$d/t$t" > "$d/t$t.log" 2>&1 \
            || echo "FAILED $name T=$t"
    done
    "$PY" - "$d" "$name" <<'EOF'
import pathlib, sys
d, name = pathlib.Path(sys.argv[1]), sys.argv[2]
recs = []
for t in ("t0.1", "t0.3"):
    fa = d / t / "seqs" / "seqs.fa"
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
native = {recs[0], recs[9]} if len(recs) >= 18 else set()
kept = [s for s in recs if len(recs) <= 10 or s not in native]
with (d / "all.fa").open("w") as fh:
    for n, s in enumerate(kept, start=1):
        fh.write(f">{name}_{n:02d}\n{s}\n")
print(f"{name}: {len(kept)} sequences")
EOF
done
echo "MPNN_B4R_END $(date +%H:%M:%S)"
