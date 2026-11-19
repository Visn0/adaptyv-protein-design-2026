#!/bin/bash
# Campaign 3 sampling loop: N single-design BoltzGen runs, each into a fresh
# output dir (accumulating state in one dir re-generates all prior designs and
# crosses the RAM cap). Collects sequences + metrics into a CSV at the end.
set -u
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)}"
C3="$HOME/c3-work"
cd "$C3/boltzgen" || exit 1
export MEMLIMIT_MB=12500 MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=4
SPEC="$REPO/challenges/03-glp1r/campaigns/c3-boltzgen-cyclic/scripts/spec-glp1r-cyclic-junction.yaml"
N=${1:-6}
for i in $(seq 1 "$N"); do
    OUT="$C3/c8-deep-junction/run$i"
    echo "### run $i $(date -Is)"
    timeout 3600 /usr/bin/python3 "$C3/memlimit.py" \
        "$C3/boltzgen-env/bin/boltzgen" run "$SPEC" \
        --output "$OUT" --protocol protein-anything \
        --num_designs 1 --diffusion_batch_size 1 --num_workers 1 \
        --use_kernels false > "$C3/logs/c8-deep-junction-$i.log" 2>&1
    echo "### run $i exit=$? $(date -Is)"
done
echo "C8_SAMPLES_DONE $(date -Is)"

"$C3/boltzgen-env/bin/python" - <<'EOF'
import numpy as np, pathlib, csv
base = pathlib.Path.home() / "c3-work/c8-deep-junction"
rows = []
for run in sorted(base.glob("run*")):
    fr = run / "final_ranked_designs"
    if not fr.exists():
        continue
    for f in sorted(fr.glob("all_designs_metrics.csv")):
        with open(f) as fh:
            for r in csv.DictReader(fh):
                rows.append((run.name, r.get("designed_sequence", ""),
                             r.get("design_to_target_iptm", ""),
                             r.get("min_design_to_target_pae", ""),
                             r.get("design_ptm", ""),
                             r.get("designfolding-filter_rmsd", "")))
out = pathlib.Path.home() / "c3-work/c8-deep-junction.csv"
with open(out, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["run", "sequence", "iptm", "min_pae", "ptm", "designfolding_rmsd"])
    w.writerows(rows)
print(f"collected {len(rows)} designs -> {out}")
for r in rows:
    print(r)
EOF
