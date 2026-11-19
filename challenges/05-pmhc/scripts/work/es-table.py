#!/usr/bin/env python3
"""Corrected E-score table for the submitted 20 (v2/His-aware + closest contact).

Usage: PYTHONPATH= .venv/bin/python es-table.py <foldlist.txt>
"""

from __future__ import annotations

import pathlib
import sys

import gemmi

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from escore2 import score  # noqa: E402


def main() -> int:
    folds = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    print(f"{'design':48s} {'E_v2':>6s} {'his':>4s} {'minD6':>6s} {'closest atom':>16s}")
    for f in folds:
        p = pathlib.Path(f)
        r2 = score(p)
        if not r2:
            print(f"{p.name[:48]:48s}   ---")
            continue
        st = gemmi.read_structure(str(p))[0]
        b = st.find_chain("D")
        pep = st.find_chain("C")
        d6 = [a for rr in pep if rr.seqid.num == 6 for a in rr
              if a.name in ("OD1", "OD2")]
        best = (999.0, "?")
        for rr in b:
            for a in rr:
                d = min(a.pos.dist(x.pos) for x in d6)
                if d < best[0]:
                    best = (d, f"{rr.name}{rr.seqid.num}:{a.name}")
        name = p.name.replace("_model_0.cif", "")
        print(f"{name[:48]:48s} {r2['E_D6']:>6.2f} {r2['n_his_shell']:>4d} "
              f"{best[0]:>6.2f} {best[1]:>16s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
