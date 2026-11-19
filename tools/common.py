"""Shared helpers: paths, run context, subprocess + logging plumbing."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHALLENGES_DIR = PROJECT_ROOT / "challenges"

# Sibling study clones used by `pdt fetch-data` (override via env vars).
SOURCE_REPOS = {
    "baseline": Path(os.environ.get(
        "PDT_BASELINE_REPO",
        "~/Projects/Protein-design-competition-Anthropic-X-adaptyv")).expanduser(),
    "bindcraft": Path(os.environ.get(
        "PDT_BINDCRAFT_REPO",
        "~/Projects/egfr-conditional-binder")).expanduser(),
}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text())


def write_json(path: Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n")


def default_workers() -> int:
    """Workers for intra-experiment parallelism.

    The runner sets PDT_WORKERS per experiment so that `-j` concurrent
    experiments do not oversubscribe the CPU cores together.
    """
    env = os.environ.get("PDT_WORKERS", "")
    if env.strip().isdigit() and int(env) > 0:
        return int(env)
    return max(1, (os.cpu_count() or 4) // 2)


class WaitingInputsError(RuntimeError):
    """A stage needs external artifacts that are not present yet (not a failure)."""


@dataclass
class RunContext:
    """Everything a pipeline stage needs, plus logging into the run's log file."""

    spec: dict
    run_dir: Path
    challenge_dir: Path
    log_path: Path
    artifacts_dir: Path
    params: dict = field(default_factory=dict)
    device: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        return str(self.spec.get("name", "unnamed"))

    def param(self, key: str, default: Any = None) -> Any:
        return self.params.get(key, default)

    def resolve(self, value: str | os.PathLike) -> Path:
        """Resolve a param path against the challenge dir unless it is absolute."""
        path = Path(str(value)).expanduser()
        return path if path.is_absolute() else (self.challenge_dir / path)

    def artifact(self, name: str) -> Path:
        path = self.artifacts_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def log(self, message: str) -> None:
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        print(line, flush=True)
        with open(self.log_path, "a") as fh:
            fh.write(line + "\n")


def run_cmd(
    ctx: RunContext,
    cmd: list,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a subprocess, transcripting command + output into the run log."""
    ctx.log("$ " + " ".join(str(part) for part in cmd))
    completed = subprocess.run(
        [str(part) for part in cmd],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    with open(ctx.log_path, "a") as fh:
        if completed.stdout:
            fh.write(completed.stdout)
        if completed.stderr:
            fh.write(completed.stderr)
    if check and completed.returncode != 0:
        tail = "\n".join(completed.stderr.strip().splitlines()[-12:])
        raise RuntimeError(
            f"command failed (exit {completed.returncode}): "
            f"{' '.join(str(p) for p in cmd)}\n{tail}"
        )
    return completed


def git_rev() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
        )
        return out.stdout.strip() or None
    except Exception:
        return None
