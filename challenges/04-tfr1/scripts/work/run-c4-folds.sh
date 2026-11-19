#!/usr/bin/env bash
# Boltz-2 co-fold chain for challenge 4 campaign 1 (5 samples, seed 42).
# Re-globs the yaml folder between passes, so yamls built while the chain runs
# are picked up. Resumable: a fold with models in its output dir is skipped.
# One fold at a time; waits for the card to be quiet first.
set -u
WORK=$HOME/c4-work
LIMIT=${MEMLIMIT_MB:-17000}
cd "$WORK" || exit 1
for pass in 1 2 3 4; do
    echo "=== fold pass $pass $(date -Is) ==="
    todo=0
    for yaml in "$WORK"/folds/*.yaml; do
        name=$(basename "$yaml" .yaml)
        out="$WORK/folds/$name"
        if ls "$out"/boltz_results_*/predictions/*/*_model_*.cif >/dev/null 2>&1; then
            continue
        fi
        todo=$((todo + 1))
        echo "### $name $(date -Is)"
        while pgrep -f "boltz predict" >/dev/null 2>&1; do sleep 30; done
        sleep 20   # settle: no new fold starts under us
        mkdir -p "$out"
        MEMLIMIT_MB=$LIMIT /usr/bin/python3 "$WORK/bin/memlimit.py" \
            $HOME/.venvs/boltz/bin/boltz predict "$yaml" --out_dir "$out" \
            --seed 42 --diffusion_samples 5 > "$out/fold.log" 2>&1 &
        job=$!
        /usr/bin/python3 "$WORK/bin/watch_resources.py" "$name" \
            "$WORK/logs/folds-$name-resources.csv" 15 10800 > "$out/watch.log" 2>&1 &
        watcher=$!
        wait "$job"
        rc=$?
        kill "$watcher" 2>/dev/null
        models=$(ls "$out"/boltz_results_*/predictions/*/*_model_*.cif 2>/dev/null | wc -l)
        echo "### $name exit=$rc models=$models $(date -Is)"
    done
    echo "=== fold pass $pass: $todo folded this pass ==="
    [ "$todo" -eq 0 ] && break
done
echo "C4_FOLDS_END $(date -Is)"
