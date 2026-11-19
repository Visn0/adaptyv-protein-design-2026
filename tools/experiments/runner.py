"""Launch experiments (optionally several at once) and read the run ledger.

`pdt exp run` resolves specs, spawns one worker process per experiment (up to
`-j` at a time) and reports each outcome. Every experiment gets an isolated
run directory, so parallel runs never share state. The per-experiment
`workers` knob (PDT_WORKERS) is set here so that N concurrent experiments
together use roughly the machine's cores, not N x all cores.
"""
from __future__ import annotations

import concurrent.futures
import os
import subprocess
import sys
import time
from pathlib import Path

from tools import common
from tools.experiments.spec import Spec, discover, load_spec  # noqa: F401 (re-export)


def _make_run_dir(spec: Spec) -> Path:
    runs_root = spec.runs_root
    runs_root.mkdir(parents=True, exist_ok=True)
    base = runs_root / f"{common.utc_stamp()}-{spec.name}"
    candidate, n = base, 1
    while candidate.exists():
        n += 1
        candidate = Path(f"{base}-{n}")
    candidate.mkdir(parents=True)
    return candidate


def _run_blocking(spec: Spec, workers_per: int) -> dict:
    run_dir = _make_run_dir(spec)
    env = os.environ.copy()
    env["PDT_WORKERS"] = str(max(1, workers_per))
    cmd = [sys.executable, "-m", "tools.experiments.worker", str(spec.path), str(run_dir)]
    proc = subprocess.run(cmd, env=env)
    status_path = run_dir / "status.json"
    status = common.read_json(status_path) if status_path.exists() else {}
    return {
        "name": spec.name,
        "challenge": spec.challenge,
        "pipeline": spec.pipeline,
        "run_dir": str(run_dir),
        "state": status.get("state", f"exit-{proc.returncode}"),
        "duration_s": status.get("duration_s"),
        "summary": status.get("summary"),
    }


def run_specs(specs: list[Spec], jobs: int = 2, dry_run: bool = False) -> list[dict]:
    if dry_run:
        for spec in specs:
            print(
                f"[dry-run] {spec.challenge}/{spec.name}: pipeline={spec.pipeline} "
                f"stages={spec.stages or 'default'} resources={spec.resources}"
                + ("  (requires network)" if spec.requires_network else "")
            )
        return []
    if not specs:
        print("no experiments matched")
        return []

    workers_per = max(1, (os.cpu_count() or 4) // max(1, jobs))
    print(f"launching {len(specs)} experiment(s), {jobs} at a time, {workers_per} workers each\n")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {}
        for spec in specs:
            futures[pool.submit(_run_blocking, spec, workers_per)] = spec
            time.sleep(0.25)  # stagger so run-directory timestamps stay distinct
        for future in concurrent.futures.as_completed(futures):
            spec = futures[future]
            try:
                record = future.result()
            except Exception as exc:
                record = {
                    "name": spec.name, "challenge": spec.challenge, "pipeline": spec.pipeline,
                    "run_dir": None, "state": "launch-failed", "duration_s": None,
                    "summary": {"error": str(exc)},
                }
                print(f"!! {spec.name}: launch failed: {exc}")
            results.append(record)
            dur = f" in {record['duration_s']}s" if record.get("duration_s") else ""
            print(f"[{record['state']:>14}] {record['challenge']}/{record['name']}{dur}"
                  f"  -> {record['run_dir']}")
    return results


def status_rows(challenge: str | None = None, recent: int = 15) -> list[dict]:
    pattern = f"{challenge}/runs/*/status.json" if challenge else "*/runs/*/status.json"
    rows = []
    for path in common.CHALLENGES_DIR.glob(pattern):
        try:
            row = common.read_json(path)
        except Exception:
            continue
        row.setdefault("run_dir", str(path.parent))
        rows.append(row)
    rows.sort(key=lambda r: r.get("started_utc") or "", reverse=True)
    return rows[:recent]


def print_status(challenge: str | None = None, recent: int = 15) -> None:
    rows = status_rows(challenge=challenge, recent=recent)
    if not rows:
        print("no runs yet — try: pdt exp run --all")
        return
    print(f"{'state':<15}{'challenge':<9} {'name':<28}{'started (UTC)':<22}{'dur':>7}  run_dir")
    for row in rows:
        dur = f"{row.get('duration_s')}s" if row.get("duration_s") is not None else "-"
        print(f"{row.get('state', '?'):<15}{row.get('challenge', '?'):<9} "
              f"{row.get('name', '?'):<28}{row.get('started_utc', '?'):<22}{dur:>7}  "
              f"{row.get('run_dir', '?')}")
