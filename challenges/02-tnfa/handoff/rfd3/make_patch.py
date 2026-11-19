#!/usr/bin/env python3
"""Build an RFdiffusion3 input for one hotspot set on the TNF trimer.

Why this exists
---------------
The full trimer (456 residues, ~3600 atoms) costs ~300 s per design and pushes a
12 GB card to its ceiling. A target trimmed to the neighbourhood of the hotspot
set costs ~50 s per design (measured, 6x) at the same peak RSS.

Two building blocks:

* the trimmed PDB keeps every residue within `--radius` of the hotspot centroid,
  on all three chains — the third protomer keeps the residues that block the
  site, so a design cannot be placed where that protomer sits;
* the contig lists the residue *blocks* that survive the trim, because the trim
  leaves gaps and RFdiffusion3 rejects a range that skips a residue
  ("Residue A20 not found in atom array").

Usage:
    python make_patch.py --name x3a-rbs --hotspots A83,A87,A89,B147 --length 70-95
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

C2 = Path(__file__).resolve().parents[2]          # challenges/02-tnfa
SOURCE = C2 / "data/epitope-analysis/1TNF.pdb"
OUT = C2 / "handoff/rfd3"


def parse_ca(path: Path) -> dict[tuple[str, int], tuple[float, float, float]]:
    ca = {}
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")) and line[12:16].strip() == "CA":
            ca[(line[21], int(line[22:26]))] = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
    return ca


def blocks(numbers: list[int]) -> list[str]:
    """['6-23', '25-43', ...] — contiguous runs, so the contig matches the file."""
    runs, start, prev = [], numbers[0], numbers[0]
    for value in numbers[1:]:
        if value != prev + 1:
            runs.append((start, prev))
            start = value
        prev = value
    runs.append((start, prev))
    return [f"{a}" if a == b else f"{a}-{b}" for a, b in runs]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="input key and file stem, e.g. x3a-rbs")
    parser.add_argument("--hotspots", required=True, help="1TNF selections, e.g. A83,A87,B147")
    parser.add_argument("--length", default="70-95", help="binder length range")
    parser.add_argument("--radius", type=float, default=28.0, help="trim radius, A")
    args = parser.parse_args()

    hotspots = []
    for token in args.hotspots.split(","):
        hotspots.append((token[0], int(token[1:])))
    ca = parse_ca(SOURCE)
    missing = [h for h in hotspots if h not in ca]
    if missing:
        raise SystemExit(f"hotspots not in {SOURCE.name}: {missing}")

    centre = tuple(sum(ca[h][i] for h in hotspots) / len(hotspots) for i in range(3))
    keep: dict[str, set[int]] = defaultdict(set)
    for (chain, resi), xyz in ca.items():
        if math.dist(xyz, centre) <= args.radius:
            keep[chain].add(resi)

    source_lines = SOURCE.read_text().splitlines()
    kept = [line for line in source_lines
            if line.startswith(("ATOM", "HETATM"))
            and int(line[22:26]) in keep.get(line[21], set())]
    patch = OUT / f"target-{args.name}.pdb"
    patch.write_text("\n".join(kept) + "\nEND\n")

    contig_target = ",".join(f"{chain}{block}"
                             for chain in sorted(keep)
                             for block in blocks(sorted(keep[chain])))
    spec = {
        args.name: {
            "input": str(patch.resolve()),
            "contig": f"{args.length},/0,{contig_target}",
            "select_hotspots": args.hotspots,
            # Without this the origin token comes from the input structure's centre
            # of mass, and the diffused chain is placed INSIDE the target: measured
            # on the first X3-A batch, every design had its binder centroid within
            # 5 A of the target's centroid, with 24-61 atoms closer than 2 A (the
            # Tamarind X2 designs, the baseline, have none under 2 A). With
            # "hotspots" the origin sits 10 A outward from the hotspot centroid.
            "infer_ori_strategy": "hotspots",
            "is_non_loopy": True,
        }
    }
    spec_path = OUT / f"{args.name}.json"
    spec_path.write_text(json.dumps(spec, indent=2) + "\n")

    residues = sum(len(v) for v in keep.values())
    atoms = sum(1 for line in kept if line.startswith("ATOM"))
    print(f"{args.name}: {residues} residues / {atoms} atoms kept "
          f"({ {c: len(r) for c, r in sorted(keep.items())} })")
    print(f"  target  {patch.relative_to(C2.parent.parent)}")
    print(f"  spec    {spec_path.relative_to(C2.parent.parent)}")
    print(f"  contig  {spec[args.name]['contig'][:150]}")


if __name__ == "__main__":
    main()
