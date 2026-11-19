#!/usr/bin/env python3
"""Fetch a depth-capped MSA (a3m) from the ColabFold server and cache it.

Why this exists: `boltz predict --use_msa_server` on a homolog-rich target
(e.g. a 409-aa human GPCR construct) inflates host RAM to ~14.7 GiB and the
memory watchdog kills every fold at ~100 s. Precomputing the target's MSA here
with a depth cap keeps folds inside the cap (measured: 88 s per 489-res
complex, peak 11.71 GiB at depth 1024). Reference the file from the fold YAML:

    sequences:
      - protein:
          id: A
          sequence: <de-novo binder>      # no homologs: no server call needed
          msa: empty
      - protein:
          id: B
          sequence: <target>
          msa: /abs/path/to/<hash>-d1024.a3m

Usage:
    python fetch_msas.py SEQ [SEQ ...] [--depth 1024] [--out-dir DIR]
    python fetch_msas.py --fasta seqs.fa [--depth 1024] [--out-dir DIR]

Writes one a3m per unique sequence, cached by sha1(seq)-depth (re-runs free).
Stdlib only; runs under any python3.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import tarfile
import time
import urllib.parse
import urllib.request

BASE = "https://api.colabfold.com"
DEFAULT_DEPTH = 1024


def fetch_a3m(sequence: str, depth: int) -> str:
    """Return an a3m for one sequence, truncated to `depth` query/hit pairs."""
    body = urllib.parse.urlencode({"q": f">101\n{sequence}", "mode": "all"}).encode()
    req = urllib.request.Request(
        f"{BASE}/ticket/msa", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    ticket = json.loads(urllib.request.urlopen(req, timeout=60).read())["id"]
    status = {"status": "UNKNOWN"}
    for _ in range(120):
        status = json.loads(urllib.request.urlopen(f"{BASE}/ticket/{ticket}", timeout=60).read())
        if status["status"] in ("COMPLETE", "ERROR"):
            break
        time.sleep(5)
    if status["status"] != "COMPLETE":
        raise SystemExit(f"MSA server returned {status['status']}")
    blob = urllib.request.urlopen(f"{BASE}/result/download/{ticket}", timeout=300).read()
    tar = tarfile.open(fileobj=io.BytesIO(blob))
    names = [n for n in tar.getnames() if n.endswith(".a3m")]
    if not names:
        raise SystemExit("no a3m in the archive")
    member = tar.extractfile(names[0])
    if member is None:
        raise SystemExit("a3m member unreadable")
    lines = [line for line in member.read().decode().splitlines() if line.strip()]
    kept, count = [], 0
    for i in range(0, len(lines) - 1, 2):  # a3m rows are query/hit pairs
        if count >= depth:
            break
        kept.extend(lines[i:i + 2])
        count += 1
    return "\n".join(kept) + "\n"


def _fasta_sequences(path: pathlib.Path) -> list[str]:
    seqs, buf = [], []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if buf:
                seqs.append("".join(buf))
            buf = []
        else:
            buf.append(line.strip())
    if buf:
        seqs.append("".join(buf))
    return seqs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sequences", nargs="*", help="raw sequences (name=SEQ also accepted)")
    ap.add_argument("--fasta", type=pathlib.Path, help="FASTA file; one a3m per record")
    ap.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    ap.add_argument("--out-dir", type=pathlib.Path, default=pathlib.Path("msa"))
    args = ap.parse_args()

    seqs = [s.split("=", 1)[-1] for s in args.sequences]
    if args.fasta:
        seqs.extend(_fasta_sequences(args.fasta))
    if not seqs:
        raise SystemExit("no sequences given")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for seq in seqs:
        tag = hashlib.sha1(seq.encode()).hexdigest()[:12]
        out = args.out_dir / f"{tag}-d{args.depth}.a3m"
        if out.exists():
            print(f"cached: {out}")
        else:
            print(f"fetching {len(seq)} aa (depth {args.depth}) ...")
            for attempt in range(1, 4):
                try:
                    out.write_text(fetch_a3m(seq, args.depth))
                    break
                except Exception as exc:  # noqa: BLE001 - the shared server is flaky
                    print(f"  attempt {attempt} failed: {exc}")
                    if attempt == 3:
                        raise
                    time.sleep(20 * attempt)
            print(f"wrote {out}")
        rows = sum(1 for line in out.read_text().splitlines() if line.startswith(">"))
        print(f"  {out.name}: {rows} rows")


if __name__ == "__main__":
    main()
