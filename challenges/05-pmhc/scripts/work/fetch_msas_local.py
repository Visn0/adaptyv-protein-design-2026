#!/usr/bin/env python3
"""Fetch a depth-capped a3m from the LOCAL SwissProt mmseqs DB.

Fallback for fetch_msas.py (the ColabFold API was unreachable from this
network on 2026-10-30). Uses the mmseqs database already on disk for the
binder-prescreen setup (`~/prescreen-dbs/swissprot/swissprot`) and the mmseqs
binary at `~/tools/mmseqs/bin/mmseqs`.

Output files use the same naming contract as fetch_msas.py
(`<sha1(seq)[:12]>-d<cap>.a3m`), so the fold-yaml builders pick them up
identically. Provenance (which source each file came from) is recorded in
`msa-provenance.json` next to the a3m files.

Usage:
    python fetch_msas_local.py --fasta seqs.fa --out-dir challenges/05-pmhc/inputs/msa
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile
import time

MMSEQS = pathlib.Path.home() / "tools" / "mmseqs" / "bin" / "mmseqs"
DBS = [
    pathlib.Path.home() / "prescreen-dbs" / "swissprot" / "swissprot",
    pathlib.Path.home() / "prescreen-dbs" / "pdb" / "pdb",
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _rows(text: str) -> list[tuple[str, str]]:
    lines = [line for line in text.splitlines() if line.strip()]
    rows = []
    for i in range(0, len(lines) - 1, 2):
        rows.append((lines[i], lines[i + 1]))
    return rows


def fetch_a3m(seq: str, cap: int) -> str:
    merged: list[tuple[str, str]] = []
    seen: set[str] = set()
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        query = tmp / "q.fa"
        query.write_text(f">query\n{seq}\n")
        qdb = tmp / "qdb"
        run([str(MMSEQS), "createdb", str(query), str(qdb)])
        for n, db in enumerate(DBS):
            res, msa = tmp / f"res{n}", tmp / f"msa{n}.a3m"
            run([str(MMSEQS), "search", str(qdb), str(db), str(res), str(tmp / f"tmp{n}"),
                 "-s", "7.5", "--max-seqs", str(cap), "-e", "1e-3"])
            run([str(MMSEQS), "result2msa", str(qdb), str(db), str(res), str(msa),
                 "--msa-format-mode", "6"])
            for header, row in _rows(msa.read_text()):
                if row not in seen:
                    seen.add(row)
                    merged.append((header, row))
    kept = merged[:cap]
    return "\n".join(f"{h}\n{s}" for h, s in kept) + "\n"


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
    ap.add_argument("sequences", nargs="*")
    ap.add_argument("--fasta", type=pathlib.Path)
    ap.add_argument("--cap", type=int, default=1024)
    ap.add_argument("--out-dir", type=pathlib.Path, required=True)
    args = ap.parse_args()

    if not MMSEQS.exists():
        raise SystemExit(f"mmseqs not found at {MMSEQS}")
    for db in DBS:
        if not pathlib.Path(str(db) + ".dbtype").exists():
            raise SystemExit(f"mmseqs DB not found at {db}")

    seqs = list(args.sequences)
    if args.fasta:
        seqs.extend(_fasta_sequences(args.fasta))
    if not seqs:
        raise SystemExit("no sequences given")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    prov_path = args.out_dir / "msa-provenance.json"
    prov = json.loads(prov_path.read_text()) if prov_path.exists() else {}
    for seq in seqs:
        tag = hashlib.sha1(seq.encode()).hexdigest()[:12]
        out = args.out_dir / f"{tag}-d{args.cap}.a3m"
        if out.exists():
            print(f"cached: {out}")
        else:
            t0 = time.time()
            out.write_text(fetch_a3m(seq, args.cap))
            print(f"wrote {out} in {time.time() - t0:.1f}s")
        rows = sum(1 for line in out.read_text().splitlines() if line.startswith(">"))
        prov[out.name] = {"source": "mmseqs-swissprot+pdb", "rows": rows,
                          "fetched": time.strftime("%Y-%m-%d")}
        print(f"  {out.name}: {rows} rows")
    prov_path.write_text(json.dumps(prov, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
