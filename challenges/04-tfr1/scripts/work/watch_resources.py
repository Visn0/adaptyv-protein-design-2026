#!/usr/bin/env python3
"""Sample system memory, a job's RSS and the GPU while the job runs; write a CSV.

Usage: watch_resources.py <pgid> <csv-path> [interval-s] [duration-s]

The point: the host crashed twice from memory pressure, so every GPU job runs
with a live record of what it used. Sampling stops when the job's group is gone
or the duration ends.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

PAGE = os.sysconf("SC_PAGE_SIZE")


def group_rss(pgid: int) -> int:
    total = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat", "rb") as fh:
                fields = fh.read().rsplit(b")", 1)[1].split()
            if int(fields[2]) != pgid:
                continue
            with open(f"/proc/{entry}/statm", "rb") as fh:
                total += int(fh.read().split()[1]) * PAGE
        except (OSError, ValueError, IndexError):
            continue
    return total


def meminfo() -> dict[str, int]:
    info = {}
    for line in open("/proc/meminfo"):
        key, _, rest = line.partition(":")
        info[key] = int(rest.split()[0]) * 1024
    return info


def gpu() -> tuple[int, int]:
    try:
        out = subprocess.run(["/usr/lib/wsl/lib/nvidia-smi",
                              "--query-gpu=utilization.gpu,memory.used",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        util, used = (part.strip() for part in out.split(","))
        return int(util), int(used)
    except Exception:
        return -1, -1


def find_pgid(pattern: str) -> int:
    """Process group of the job whose command line carries `pattern`.

    The job's own group, not the launcher's: memlimit.py starts the child in a
    new session, so watching the launcher measures a few megabytes and nothing
    else (that mistake hid the real usage in the first attempt).
    """
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/cmdline", "rb") as fh:
                cmd = fh.read().decode("utf-8", "replace").replace("\0", " ").strip()
        except OSError:
            continue
        if pattern not in cmd or "watch_resources" in cmd or "memlimit.py" in cmd:
            continue
        try:
            with open(f"/proc/{entry}/stat", "rb") as fh:
                fields = fh.read().rsplit(b")", 1)[1].split()
            return int(fields[2])
        except (OSError, ValueError, IndexError):
            continue
    return 0


def main() -> int:
    pattern = sys.argv[1]
    path = sys.argv[2]
    interval = float(sys.argv[3]) if len(sys.argv) > 3 else 15.0
    duration = float(sys.argv[4]) if len(sys.argv) > 4 else 3600.0
    deadline = time.time() + duration
    peak_rss = peak_gpu = 0
    with open(path, "w") as fh:
        fh.write("time,mem_used_mib,mem_avail_mib,swap_used_mib,job_rss_mib,gpu_util,gpu_mem_mib\n")
        fh.flush()
        seen = False
        while time.time() < deadline:
            pgid = find_pgid(pattern)
            if pgid == 0:
                if seen:
                    break   # the job finished: stop watching, do not spin
                time.sleep(interval)
                continue
            seen = True
            info = meminfo()
            rss = group_rss(pgid)
            util, gpu_mem = gpu()
            if rss == 0:
                break
            peak_rss = max(peak_rss, rss)
            peak_gpu = max(peak_gpu, gpu_mem)
            fh.write(f"{time.strftime('%H:%M:%S')},"
                     f"{(info['MemTotal'] - info['MemFree'] - info.get('Buffers', 0) - info.get('Cached', 0)) / 2**20:.0f},"
                     f"{info['MemAvailable'] / 2**20:.0f},"
                     f"{(info['SwapTotal'] - info['SwapFree']) / 2**20:.0f},"
                     f"{rss / 2**20:.0f},{util},{gpu_mem}\n")
            fh.flush()
            time.sleep(interval)
    print(f"watch: peak job RSS {peak_rss / 2**30:.2f} GiB, peak GPU {peak_gpu} MiB -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
