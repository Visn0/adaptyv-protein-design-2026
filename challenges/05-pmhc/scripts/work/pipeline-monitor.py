#!/usr/bin/env python3
"""C5 pipeline monitor — run by a Hermes cron job (no_agent mode).

Silent when healthy (empty stdout = nothing delivered). Prints an alert only
when a pipeline is STUCK, DEAD, or COMPLETE. Safe actions only:
  - STUCK  (runner alive, zero progress, idle GPU): kill that runner's pids
    (it cannot be folding); the next tick relaunches.
  - DEAD   (no runner, work left, idle GPU): relaunch the fold runner
    detached (idempotent — it skips finished arms).
Never relaunches while a queue script is alive (the queue owns the launch;
a monitor relaunch would double-fold).

Targets are discovered generically: every ~/c5-work/<pipeline>/folds with
yaml arms; done = *_model_0.cif count.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import signal
import subprocess
import sys

HOME = pathlib.Path.home()
WORK = HOME / "c5-work"
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
RUNNER = REPO / "challenges" / "05-pmhc" / "scripts" / "work" / "c0-probe-fold.sh"
STATE = WORK / "monitor-state.json"
IDLE_MIB = 2500      # GPU below this = no fold running
STUCK_TICKS = 2      # consecutive no-progress ticks before a stall is called
# Deliberately abandoned sets: never relaunch these (the full-size C0 folds
# crash this host; the Fv trim replaced them).
SKIP_PARENTS = {"c0"}


def gpu_used() -> int:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:
        return -1


def proc_table() -> tuple[dict[int, str], bool]:
    """(pid -> C0_WORK for fold runners, any_queue_alive)."""
    runners: dict[int, str] = {}
    queue_alive = False
    for p in pathlib.Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode(
                errors="ignore")
        except Exception:
            continue
        if "queue" in cmd and cmd.endswith(".sh ") or "-queue" in cmd:
            queue_alive = True
        if "c0-probe-fold.sh" not in cmd:
            continue
        try:
            env = (p / "environ").read_bytes().decode(errors="ignore")
        except Exception:
            env = ""
        m = re.search(r"C0_WORK=([^\x00\n]+)", env)
        if m:
            runners[int(p.name)] = m.group(1)
    return runners, queue_alive


def targets() -> dict[str, dict]:
    out = {}
    for d in sorted(WORK.glob("*/folds")):
        if d.parent.name in SKIP_PARENTS:
            continue
        n_yaml = len(list(d.glob("*.yaml")))
        if n_yaml == 0:
            continue
        done = sum(1 for _ in d.glob(
            "*/boltz_results_*/predictions/*/*_model_0.cif"))
        out[str(d)] = {"target": n_yaml, "done": done}
    return out


def main() -> int:
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    gpu = gpu_used()
    runners, queue_alive = proc_table()
    alerts: list[str] = []
    idle = 0 <= gpu < IDLE_MIB

    for d, t in targets().items():
        st = state.setdefault(d, {"last": t["done"], "stuck": 0,
                                  "complete": False})
        if t["done"] > st["last"]:
            st["stuck"] = 0
        else:
            st["stuck"] += 1
        st["last"] = t["done"]

        if t["done"] >= t["target"]:
            if not st["complete"]:
                st["complete"] = True
                alerts.append(f"c5 monitor: {d} COMPLETE "
                              f"{t['done']}/{t['target']} (scoring next)")
            continue
        st["complete"] = False

        # the runner's C0_WORK is the pipeline dir; targets() keys are the
        # folds subdir - compare against the parent.
        pids = [p for p, w in runners.items()
                if w == str(pathlib.Path(d).parent)]
        if pids and idle and st["stuck"] >= STUCK_TICKS:
            for p in pids:
                try:
                    os.kill(p, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            alerts.append(f"c5 monitor: {d} STUCK {t['done']}/{t['target']} "
                          f"(no progress {st['stuck']} ticks, GPU idle) — "
                          f"killed runner pids {pids}; relaunch next tick")
            st["stuck"] = 0
        elif not pids and idle and not queue_alive:
            log = pathlib.Path(d) / "logs" / "monitor-relaunch.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(
                ["setsid", "bash", str(RUNNER), "all"],
                env={**os.environ, "C0_WORK": d, "MEMLIMIT_MB": "12000",
                     "PYTHONPATH": ""},
                stdout=open(log, "a"), stderr=subprocess.STDOUT,
                start_new_session=True)
            alerts.append(f"c5 monitor: {d} DEAD {t['done']}/{t['target']} "
                          f"(GPU idle) — relaunched")
            st["stuck"] = 0
        elif not pids and idle and queue_alive:
            alerts.append(f"c5 monitor: {d} idle {t['done']}/{t['target']} "
                          f"but a queue script is alive — not touching it")

    STATE.write_text(json.dumps(state, indent=1))
    if alerts:
        print("\n".join(alerts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
