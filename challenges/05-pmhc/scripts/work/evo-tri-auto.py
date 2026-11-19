#!/usr/bin/env python3
"""Auto tri-state for an evolution generation: fold the WT + peptide-free arms
of every qualifying variant, then print the composite comparison table.

Usage: PYTHONPATH= .venv/bin/python evo-tri-auto.py <gen>
"""

from __future__ import annotations

import csv
import pathlib
import re
import subprocess
import sys

import yaml

HOME = pathlib.Path.home()
def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
W = HOME / "c5-work"
GEN = int(sys.argv[1])
G = W / "evo" / f"gen{GEN}"
WT = "VVVGAGGVGK"
GATE_IPTM, GATE_IPDAE, GATE_E = 0.93, 0.60, -0.5


def main() -> int:
    es = {}
    for line in (G / "escores.txt").read_text().splitlines():
        m = re.match(r"\s*(-?[0-9.]+)\s+\d+\s+\d+\s+(\S+)$", line)
        if m:
            es[m.group(2)] = float(m.group(1))
    rows = list(csv.DictReader((G / "s1-summary.csv").open()))
    qual = []
    for r in rows:
        d = r["design"]
        e = es.get(d)
        try:
            iptm = float(r.get("iptm_pep") or 0)
            ipdae = float(r.get("ipdae_pep") or 0)
        except ValueError:
            continue
        if iptm >= GATE_IPTM and ipdae >= GATE_IPDAE and e is not None and e <= GATE_E:
            qual.append(d)
    out = G / "tristate" / "folds"
    out.mkdir(parents=True, exist_ok=True)
    made = 0
    for d in qual:
        src = G / "folds" / f"{d}.yaml"
        if not src.exists():
            continue
        text = src.read_text()
        (out / f"{d}__wt.yaml").write_text(
            re.sub(r"sequence: VVVGADGVGK", f"sequence: {WT}", text, count=1))
        blocks = re.split(r"(?=  - protein:)", text)
        (out / f"{d}__free.yaml").write_text(
            "".join(b for b in blocks if "id: C" not in b))
        made += 2
    print(f"gen{GEN}: {len(qual)} qualifiers -> {made} tri-state arms")
    if made:
        subprocess.run(["bash", "-c",
                        f"while [ \"$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)\" -gt 2500 ]; "
                        f"do sleep 60; done; cd {REPO} && MEMLIMIT_MB=12000 "
                        f"C0_WORK={G}/tristate bash challenges/05-pmhc/scripts/work/c0-probe-fold.sh all "
                        f">> {G}/tristate/queue.log 2>&1 && "
                        f"PYTHONPATH= .venv/bin/python challenges/05-pmhc/scripts/work/s1-score.py "
                        f"--work {G}/tristate --jobs 3 >> {G}/tristate/queue.log 2>&1"],
                       check=False)
        print(f"gen{GEN}: tri-state folded + scored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
