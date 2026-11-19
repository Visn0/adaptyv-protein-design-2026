#!/usr/bin/env python3
"""Kill processes whose command line contains a substring, safely.

Shell alternatives (pkill -f, pgrep -f, even bracket-guarded patterns)
match the calling shell's own command line whenever the target string
appears anywhere in the call, which SIGTERMs the tool call itself. This
script reads /proc/*/cmdline instead and skips its own PID and all of its
ancestors, so the pattern can live on the command line safely.

Usage:
    python3 kill_by_cmdline.py <substring> [--signal TERM]

Prints the killed PIDs, one per line. Exits 0 even when nothing matched.
"""
import os
import pathlib
import signal
import sys


def ancestors(pid: int) -> set:
    out = set()
    for _ in range(20):
        try:
            stat = pathlib.Path(f"/proc/{pid}/stat").read_text().split()
            pid = int(stat[3])
        except Exception:
            break
        if pid <= 0:
            break
        out.add(pid)
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    pattern = sys.argv[1]
    sig = signal.SIGTERM
    if len(sys.argv) > 3 and sys.argv[2] == "--signal":
        sig = getattr(signal, f"SIG{sys.argv[3].upper()}", signal.SIGTERM)

    me = os.getpid()
    skip = {me} | ancestors(me)
    killed = []
    for entry in pathlib.Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid in skip:
            continue
        try:
            cmd = (entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode(errors="replace")
        except Exception:
            continue
        if pattern in cmd:
            try:
                os.kill(pid, sig)
                killed.append(pid)
            except Exception:
                pass
    for pid in killed:
        print(pid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
