#!/usr/bin/env python3
"""Run a command under a hard memory limit — kill it before it can take the host down.

The limit applies to the RSS of the command's whole process group, sampled every
two seconds. The command is killed with SIGKILL the moment the group exceeds the
limit, so a runaway pre-processing step costs a job, not the machine.

Usage:  MEMLIMIT_MB=8000 python3 memlimit.py <command> [args...]
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

PAGE = os.sysconf("SC_PAGE_SIZE")


def group_rss(pgid: int) -> int:
    """Resident bytes of every process in the group (WSL /proc is the truth here)."""
    total = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat", "rb") as fh:
                fields = fh.read().rsplit(b")", 1)[1].split()
            if int(fields[2]) != pgid:  # fields[2] = process group (after comm)
                continue
            with open(f"/proc/{entry}/statm", "rb") as fh:
                total += int(fh.read().split()[1]) * PAGE
        except (OSError, ValueError, IndexError):
            continue
    return total


def main() -> int:
    limit_mb = int(os.environ.get("MEMLIMIT_MB", "8000"))
    if not sys.argv[1:]:
        print(__doc__)
        return 2
    proc = subprocess.Popen(sys.argv[1:], preexec_fn=os.setsid)
    pgid = os.getpgid(proc.pid)
    peak = 0
    while proc.poll() is None:
        rss = group_rss(pgid)
        peak = max(peak, rss)
        if rss > limit_mb * 1024 * 1024:
            os.killpg(pgid, signal.SIGKILL)
            proc.wait()
            print(f"memlimit: KILLED at {rss / 2**30:.2f} GiB (limit {limit_mb} MiB); "
                  f"peak {peak / 2**30:.2f} GiB", file=sys.stderr)
            return 137
        time.sleep(2)
    print(f"memlimit: peak {peak / 2**30:.2f} GiB of {limit_mb} MiB limit, "
          f"exit {proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
