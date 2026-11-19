#!/usr/bin/env python3
"""Fetch a depth-capped MSA for a sequence and cache it as an a3m.

Why this exists: boltz with --use_msa_server on the full 409-res GLP1R
construct inflated RAM to 14.65 GiB and the memory watchdog killed every fold.
The receptor MSA is the driver (thousands of homologs), so it is computed once
here, capped, and referenced from the fold YAMLs. De-novo binders have no
homologs and use `msa: empty` directly.

    .venv/bin/python challenges/03-glp1r/campaigns/c1-two-domain/scripts/fetch_msas.py [depth]
"""
from __future__ import annotations

import hashlib
import io
import pathlib
import sys
import tarfile
import time
import urllib.parse
import urllib.request

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


OUT_DIR = _repo_root() / "challenges/03-glp1r/inputs/msa"
BASE = "https://api.colabfold.com"
DEFAULT_DEPTH = 1024

RECEPTOR = ("RPQGATVSLWETVQKWREYRRQCQRSLTEDPPPATDLFCNRTFDEYACWPDGEPGSFVNVSCPWYLPWASSVPQGHVYRFCTAEGLWL"
            "QKDNSSLPWRDLSECEESKRGERSSPEEQLLFLYIIYTVGYALSFSALVIASAILLGFRHLHCTRNYIHLNLFASFILRALSVFIKD"
            "AALKWMYSTAAQQHQWDGLLSYQDSLSCRLVFLLMQYCVAANYYWLLVEGVYLYTLLAFSVLSEQWIFRLYVSIGWGVPLLFVVPW"
            "GIVKYLYEDEGCWTRNSNMNYWLIIRLPILFAIGVNFLIFVRVICIVVSKLKANLMCKTDIKCRLAKSTLTLIPLLGTHEVIFAFV"
            "MDEHARGTLRFIKLFTELSFTSFQGLMVAILYCFVNNEVQLEFRKSWERWRLEHLHIQRDSS")


def _post(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    import json
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def fetch_a3m(sequence: str, depth: int) -> str:
    ticket = _post(f"{BASE}/ticket/msa", {"q": f">101\n{sequence}", "mode": "all"})["id"]
    import json
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
    text = tar.extractfile(names[0]).read().decode()
    lines = [line for line in text.splitlines() if line.strip()]
    kept = []
    count = 0
    for i in range(0, len(lines), 2):
        if count >= depth:
            break
        kept.extend(lines[i:i + 2])
        count += 1
    return "\n".join(kept) + "\n"


def main() -> None:
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DEPTH
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = hashlib.sha1(RECEPTOR.encode()).hexdigest()[:12]
    out = OUT_DIR / f"receptor-{tag}-d{depth}.a3m"
    if out.exists():
        print(f"cached: {out}")
    else:
        print(f"fetching receptor MSA (depth {depth}) ...")
        a3m = fetch_a3m(RECEPTOR, depth)
        out.write_text(a3m)
        print(f"wrote {out}")
    rows = sum(1 for line in out.read_text().splitlines() if line.startswith(">"))
    print(f"rows: {rows}; first line: {out.read_text().splitlines()[0][:80]}")


if __name__ == "__main__":
    main()
