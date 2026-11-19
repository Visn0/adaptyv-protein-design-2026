"""Worker process: execute ONE experiment spec into ONE run directory.

Normally launched by the runner, not by hand:

    python -m tools.experiments.worker challenges/<c>/experiments/<spec>.yaml <run_dir>

Writes into the run directory:
    run.log             full transcript (stage logging + subprocess output)
    status.json         state machine + timing + host/device provenance
    summary.json        the pipeline's structured result (drives reports)
    spec.resolved.yaml  copy of the spec actually executed
    artifacts/          every output file the pipeline produced
"""
from __future__ import annotations

import os
import sys
import time
import traceback
from pathlib import Path

from tools import common
from tools.experiments import devices
from tools.experiments.spec import load_spec
from tools.pipelines import PIPELINES


def acquire_gpu_lock(run_dir: Path):
    """Serialize GPU experiments across processes (best effort, POSIX only)."""
    try:
        import fcntl
    except ImportError:
        return None
    lock_dir = run_dir.parents[2] / ".locks"  # challenges/.locks
    lock_dir.mkdir(parents=True, exist_ok=True)
    fh = open(lock_dir / "gpu.lock", "w")
    fcntl.flock(fh, fcntl.LOCK_EX)
    return fh


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print(__doc__)
        return 2
    spec_path, run_dir = Path(argv[0]), Path(argv[1])
    spec = load_spec(spec_path)

    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "run.log"

    device_info = devices.detect()
    device_info["plan"] = devices.plan_for(spec.resources)
    ctx = common.RunContext(
        spec={
            "name": spec.name,
            "challenge": spec.challenge,
            "pipeline": spec.pipeline,
            "description": spec.description,
            "resources": spec.resources,
            "reference": spec.reference,
            "requires_network": spec.requires_network,
            "stages": spec.stages,
        },
        run_dir=run_dir,
        challenge_dir=spec.challenge_dir,
        log_path=log_path,
        artifacts_dir=artifacts_dir,
        params=spec.params,
        device=device_info,
    )

    (run_dir / "spec.resolved.yaml").write_text(spec_path.read_text())

    status = {
        "name": spec.name,
        "challenge": spec.challenge,
        "pipeline": spec.pipeline,
        "state": "running",
        "started_utc": common.utc_now(),
        "finished_utc": None,
        "duration_s": None,
        "run_dir": str(run_dir),
        "spec_path": str(spec_path),
        "params": spec.params,
        "stages": spec.stages,
        "resources": spec.resources,
        "device": ctx.device,
        "python": ctx.device.get("python"),
        "git": common.git_rev(),
        "pid": os.getpid(),
    }
    common.write_json(run_dir / "status.json", status)

    gpu_plan = (ctx.device.get("plan") or {})
    if gpu_plan.get("fallback"):
        ctx.log(f"device: {gpu_plan.get('reason', 'gpu fallback')}")
    gpu_lock = acquire_gpu_lock(run_dir) if gpu_plan.get("resolved") == "cuda" else None
    t0 = time.time()
    summary: dict = {}
    error = None
    try:
        pipeline = PIPELINES.get(spec.pipeline)
        if pipeline is None:
            raise KeyError(f"unknown pipeline '{spec.pipeline}' (have: {sorted(PIPELINES)})")
        ctx.log(
            f"experiment '{spec.name}' ({spec.challenge}) "
            f"pipeline={spec.pipeline} stages={spec.stages or 'default'} "
            f"workers={common.default_workers()} python={ctx.device.get('python')}"
        )
        summary = pipeline(ctx) or {}
        state = "done"
    except common.WaitingInputsError as exc:
        state = "waiting_inputs"
        summary = {"waiting_for": str(exc)}
        ctx.log(f"waiting for inputs: {exc}")
    except Exception:
        state = "failed"
        tb = traceback.format_exc()
        error = tb.strip().splitlines()[-1]
        with open(log_path, "a") as fh:
            fh.write(tb + "\n")
        ctx.log(f"FAILED: {error}")
    finally:
        status.update(
            state=state,
            finished_utc=common.utc_now(),
            duration_s=round(time.time() - t0, 2),
            error=error,
            summary=summary,
        )
        common.write_json(run_dir / "status.json", status)
        common.write_json(run_dir / "summary.json", summary)

    try:
        from tools.report import html as report_html

        report_html.render_run_report(run_dir, run_dir / "report.html")
    except Exception as exc:  # a broken report must never fail the run
        ctx.log(f"report generation failed: {type(exc).__name__}: {exc}")

    return 0 if state in ("done", "waiting_inputs") else 1


if __name__ == "__main__":
    raise SystemExit(main())
