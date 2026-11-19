#!/usr/bin/env bash
# Run the finalist Boltz-2 folds (serial, one at a time, under memlimit) then
# score every model with ipsae.py. Launch ONLY when no chai-lab / boltz process
# runs (one GPU job at a time - hard rule).
set -eu
REPO="${PDT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
WORK="$HOME/c4-work/boltz-finalists"
BOLTZ="$HOME/.venvs/boltz/bin/boltz"
MEMLIMIT="$HOME/c4-work/bin/memlimit.py"
IPSAE="$HOME/tools/IPSAE/ipsae.py"
PY="$REPO/.venv/bin/python"
LOG="$HOME/c4-work/logs/boltz-finalists.log"
mkdir -p "$LOG.d" 2>/dev/null || true
exec >> "$LOG" 2>&1

for y in "$WORK"/*.yaml; do
  name=$(basename "$y" .yaml)
  out="$WORK/$name"
  if compgen -G "$out/boltz_results_*/predictions/*/*model_0.cif" > /dev/null; then
    echo "skip $name (done)"; continue
  fi
  echo "### $name start $(date +%H:%M:%S)"
  /usr/bin/python3 "$MEMLIMIT" "$BOLTZ" predict "$y" --out_dir "$out" \
      --seed 42 --diffusion_samples 5 --output_format cif \
      && echo "### $name done $(date +%H:%M:%S)" || echo "### $name FAILED $(date +%H:%M:%S)"
done

echo "=== ipSAE scoring ==="
for d in "$WORK"/*/boltz_results_*/predictions/*/; do
  for m in "$d"*_model_*.cif; do
    [ -f "$m" ] || continue
    npz="${m/.cif/.npz}"; npz=$(dirname "$m")/"pae_$(basename "$m" .cif).npz"
    [ -f "$npz" ] && $PY "$IPSAE" "$npz" "$m" 10 10 >/dev/null 2>&1 || echo "ipsae skip $m"
  done
done
echo "BOLTZ_FINALISTS_END $(date +%H:%M:%S)"
