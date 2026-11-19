#!/usr/bin/env bash
# Campaign-2 continuation: after campaign 1 closes, apply the pre-registered
# advance rule and, for every advancing epitope set, generate batch 2 (32 more
# backbones), screen, sequence, fold and fold-screen. A negative C1 stops here.
set -u
WORK=$HOME/c4-work
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
PY="$REPO/.venv/bin/python"
LOGS="$WORK/logs"

while ! grep -q "C4_MAIN_DONE" "$LOGS/main-chain.log" 2>/dev/null; do sleep 120; done
sleep 30
echo "### C1 closed, deciding sets $(date -Is)"
"$PY" "$WORK/bin/decide-c1.py" | tee "$LOGS/c1-decision.log"
sets=$(tr '\n' ' ' < "$WORK/state/advancing-sets.txt" 2>/dev/null || true)
sets=${sets% }
if [ -z "$sets" ]; then
    echo "### NO SET ADVANCES. Campaign 1 records the negative. C2 does not start."
    echo "C4_C2_STOP_NEGATIVE $(date -Is)"
    exit 0
fi
echo "### advancing sets: $sets"

cd $HOME/tools/genie3 || exit 1
for key in $sets; do
    yaml="$WORK/genie3/${key}b2.yaml"
    have=$(ls "$WORK/genie3/runs/${key}b2/pdbs/"*.pdb 2>/dev/null | wc -l)
    echo "### GEN ${key}b2 have=$have $(date -Is)"
    if [ "$have" -ge 32 ]; then
        echo "### GEN ${key}b2 skip (complete)"
        continue
    fi
    while pgrep -f "boltz predict" >/dev/null 2>&1; do sleep 30; done
    MEMLIMIT_MB=8000 /usr/bin/python3 "$WORK/bin/memlimit.py" \
        $HOME/.venvs/genie3/bin/genie3 generate -c "$yaml" \
        > "$LOGS/gen-${key}b2.log" 2>&1
    rc=$?
    n=$(ls "$WORK/genie3/runs/${key}b2/pdbs/"*.pdb 2>/dev/null | wc -l)
    echo "### GEN ${key}b2 rc=$rc designs=$n $(date -Is)"
done

echo "### b2 geometry + sequences $(date -Is)"
"$PY" "$WORK/bin/screen-gen-geometry.py" > "$LOGS/geometry-b2.log" 2>&1
bash "$WORK/bin/mpnn-c4.sh" > "$LOGS/mpnn-b2.log" 2>&1
"$PY" "$WORK/bin/build-c4-fold-yamls.py" --target full > "$LOGS/build-yamls-b2.log" 2>&1
echo "### b2 folds $(date -Is)"
bash "$WORK/bin/run-c4-folds.sh" > "$LOGS/folds-chain-b2.log" 2>&1
echo "### full re-screen $(date -Is)"
"$PY" "$REPO/challenges/04-tfr1/scripts/screen_folds_c4.py" "$WORK/folds" --target full \
    > "$LOGS/folds-screen-c2.log" 2>&1
echo "### re-screen done, $(tail -2 "$LOGS/folds-screen-c2.log" | head -1)"
"$PY" "$WORK/bin/decide-c1.py" > "$LOGS/c2-decision.log" 2>&1 || true
echo "C4_C2_DONE $(date -Is)"
